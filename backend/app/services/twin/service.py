"""Career Twin service: persist activities, aggregate, and brief."""
from __future__ import annotations

from collections import Counter
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Candidate, TwinActivity, TwinBriefingCache
from app.schemas.extraction import CandidateProfile
from app.schemas.twin import (
    CareerTwin,
    TwinActivityOut,
    TwinAggregate,
    TwinBriefing,
    TwinSaveIn,
    TwinSummary,
)
from app.services.extraction.chains import (
    Completer,
    _complete_structured,
    _default_completer,
)
from app.services.twin import prompts


def _upsert_candidate(db: Session, name: str, profile: CandidateProfile) -> Candidate:
    name = name or "Candidate"
    row = db.execute(select(Candidate).where(Candidate.name == name)).scalars().first()
    pdata = profile.model_dump(mode="json")
    if row:
        if profile.skills:  # only refresh when a real profile is supplied
            row.profile = pdata
        db.add(row)
        db.commit()
        db.refresh(row)
        return row
    row = Candidate(name=name, profile=pdata, raw_text="")
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def save_activity(db: Session, payload: TwinSaveIn) -> str:
    candidate = _upsert_candidate(db, payload.candidate_name, payload.profile)
    activity = TwinActivity(
        candidate_id=candidate.id,
        kind=payload.kind,
        title=payload.title or "",
        score=payload.score,
        verdict=payload.verdict,
        detail=payload.detail or {},
    )
    db.add(activity)
    db.commit()
    return candidate.id


def _aggregate(profile: CandidateProfile, activities: List[TwinActivity]) -> TwinAggregate:
    matches = [a for a in activities if a.kind == "match"]
    interviews = [a for a in activities if a.kind == "interview"]
    learnings = [a for a in activities if a.kind == "learning"]
    agg = TwinAggregate()

    agg.roles_explored = len({(m.title or "").strip().lower() for m in matches if m.title})
    scored = [m for m in matches if m.score is not None]
    if scored:
        best = max(scored, key=lambda m: m.score)
        agg.best_fit_role = best.title
        agg.best_fit_score = round(best.score, 1)
        agg.avg_match_score = round(sum(m.score for m in scored) / len(scored), 1)

    agg.interviews_taken = len(interviews)
    iscored = [a.score for a in interviews if a.score is not None]
    if iscored:
        agg.avg_interview_score = round(sum(iscored) / len(iscored), 1)
    agg.learning_plans = len(learnings)

    gaps: list[str] = []
    for m in matches:
        gaps += [g for g in (m.detail or {}).get("gaps", []) if isinstance(g, str)]
    agg.recurring_gaps = [g for g, _ in Counter(gaps).most_common(6)]
    agg.top_skills = [s.display_name for s in profile.skills][:14]
    return agg


def _generate_briefing(
    name: str,
    profile: CandidateProfile,
    agg: TwinAggregate,
    activities: List[TwinActivity],
    completer: Optional[Completer],
) -> TwinBriefing:
    if not activities:
        return TwinBriefing(
            headline=f"{name}'s Career Twin is just getting started.",
            narrative="Run a role match and save it to start building your living profile.",
        )
    timeline = "; ".join(
        f"{a.kind}: {a.title} ({round(a.score) if a.score is not None else '—'})"
        for a in activities[:8]
    )
    user = prompts.BRIEF_TEMPLATE.format(
        name=name,
        summary=profile.summary or "(no summary)",
        top_skills=", ".join(agg.top_skills) or "n/a",
        roles=agg.roles_explored,
        best_role=agg.best_fit_role or "n/a",
        best_score=agg.best_fit_score or 0,
        avg=agg.avg_match_score or 0,
        interviews=agg.interviews_taken,
        iavg=agg.avg_interview_score or 0,
        plans=agg.learning_plans,
        gaps=", ".join(agg.recurring_gaps) or "none recurring",
        timeline=timeline,
    )
    return _complete_structured(
        prompts.BRIEF_SYSTEM, user, TwinBriefing, completer or _default_completer
    )


def _briefing_cached(
    db: Session,
    candidate: Candidate,
    profile: CandidateProfile,
    agg: TwinAggregate,
    activities,
    completer: Optional[Completer],
) -> TwinBriefing:
    """Reuse the stored briefing while the activity set is unchanged; only call
    the LLM when there is new activity to reflect."""
    if not activities:
        return _generate_briefing(candidate.name, profile, agg, activities, completer)

    count = len(activities)
    cache = db.get(TwinBriefingCache, candidate.id)
    if cache and cache.activity_count == count and cache.briefing:
        try:
            return TwinBriefing.model_validate(cache.briefing)
        except Exception:  # pragma: no cover - corrupt cache, regenerate
            pass

    briefing = _generate_briefing(candidate.name, profile, agg, activities, completer)
    payload = briefing.model_dump(mode="json")
    if cache:
        cache.activity_count = count
        cache.briefing = payload
    else:
        cache = TwinBriefingCache(
            candidate_id=candidate.id, activity_count=count, briefing=payload
        )
    db.add(cache)
    db.commit()
    return briefing


def build_twin(db: Session, candidate_id: str, completer: Optional[Completer] = None) -> CareerTwin:
    candidate = db.get(Candidate, candidate_id)
    if not candidate:
        raise ValueError("Career Twin not found")
    activities = (
        db.execute(
            select(TwinActivity)
            .where(TwinActivity.candidate_id == candidate_id)
            .order_by(TwinActivity.created_at.desc())
        )
        .scalars()
        .all()
    )
    profile = CandidateProfile.model_validate(candidate.profile or {})
    agg = _aggregate(profile, activities)
    briefing = _briefing_cached(db, candidate, profile, agg, activities, completer)
    updated = activities[0].created_at if activities else candidate.created_at
    return CareerTwin(
        id=candidate.id,
        name=candidate.name,
        profile=profile,
        aggregate=agg,
        activities=[
            TwinActivityOut(
                id=a.id,
                kind=a.kind,
                title=a.title,
                score=a.score,
                verdict=a.verdict,
                detail=a.detail or {},
                created_at=a.created_at,
            )
            for a in activities
        ],
        briefing=briefing,
        updated_at=updated,
    )


def list_twins(db: Session) -> List[TwinSummary]:
    rows = db.execute(select(Candidate).order_by(Candidate.created_at.desc())).scalars().all()
    out: List[TwinSummary] = []
    for c in rows:
        acts = (
            db.execute(select(TwinActivity).where(TwinActivity.candidate_id == c.id))
            .scalars()
            .all()
        )
        if not acts:
            continue  # only surface candidates that are real twins
        matches = [a for a in acts if a.kind == "match" and a.score is not None]
        out.append(
            TwinSummary(
                id=c.id,
                name=c.name,
                roles_explored=len({(m.title or "").lower() for m in matches if m.title}),
                best_fit_score=round(max((m.score for m in matches), default=0), 1) or None,
                updated_at=max((a.created_at for a in acts), default=c.created_at),
            )
        )
    return out
