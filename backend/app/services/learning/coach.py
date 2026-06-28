"""Adaptive Learning Coach: turn match gaps into a sequenced learning plan."""
from __future__ import annotations

from typing import Optional

from app.core.logging import get_logger
from app.schemas.learning import LearningPlan, LearningPlanIn
from app.services.extraction.chains import Completer, _complete_structured, _default_completer
from app.services.learning import prompts
from app.services.learning.resources import resources_for
from app.services.taxonomy import get_normalizer

log = get_logger(__name__)


def _format_gaps(req: LearningPlanIn) -> str:
    if not req.gaps:
        return "- (no hard gaps — focus on deepening evidence and interview readiness)"
    return "\n".join(f"- {g.skill} ({g.importance})" for g in req.gaps)


def _enrich_resources(plan: LearningPlan) -> None:
    """Merge curated/verified resources with the model's suggestions per module."""
    norm = get_normalizer()
    for module in plan.modules:
        cid = module.canonical_id or norm.normalize(module.skill).canonical_id
        module.canonical_id = cid
        curated = resources_for(module.skill, cid, limit=3)
        seen: set[str] = set()
        merged = []
        for res in [*curated, *module.resources]:
            key = (res.url or res.title).strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            merged.append(res)
        module.resources = merged[:5]


def generate_learning_plan(
    req: LearningPlanIn, completer: Optional[Completer] = None
) -> LearningPlan:
    user = prompts.COACH_TEMPLATE.format(
        role=req.job_title,
        name=req.candidate_name,
        weekly_hours=req.weekly_hours,
        strengths=", ".join(req.strengths) if req.strengths else "(none listed)",
        gaps=_format_gaps(req),
    )
    plan = _complete_structured(
        prompts.COACH_SYSTEM, user, LearningPlan, completer or _default_completer
    )

    # Fill authoritative fields from the request and enrich resources.
    plan.candidate_name = req.candidate_name
    plan.job_title = req.job_title
    plan.weekly_hours = req.weekly_hours
    _enrich_resources(plan)
    if not plan.total_weeks:
        plan.total_weeks = len(plan.weekly_missions) or max(1, len(plan.modules))
    return plan
