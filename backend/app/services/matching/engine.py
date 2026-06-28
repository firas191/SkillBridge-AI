"""Explainable skill-match engine.

Given a normalized ``CandidateProfile`` and ``JobProfile``, produce a
``MatchResult`` that is:

* **Evidence-based** — every requirement is matched on canonical skill IDs, not
  raw keyword overlap, and carries the candidate's supporting evidence.
* **Explainable** — each requirement gets a human-readable rationale and the
  overall score is a transparent weighted average. No black-box number.
* **Deterministic** — no LLM call here, so results are reproducible and unit
  testable. (An optional LLM "narrative" can be layered on top elsewhere.)

Adjacency (related skills in the taxonomy) is rewarded as a *partial* match,
which is what lets the engine surface strong non-traditional candidates that
keyword screens miss.
"""
from __future__ import annotations

from typing import Dict, List, Optional

from rapidfuzz import fuzz

from app.schemas.extraction import CandidateProfile, JobProfile, SkillEvidence
from app.schemas.match import Gap, MatchResult, SkillMatch
from app.services.taxonomy import TaxonomyStore, get_taxonomy

# Status -> fraction of requirement weight earned.
_STATUS_FACTOR = {"matched": 1.0, "partial": 0.5, "missing": 0.0}

# Fuzzy thresholds for requirements that are not in the canonical taxonomy.
# Kept high so terms that merely share a generic word ("Computer Science" vs
# "Computer Vision" ~ 77) do NOT count as a match.
_FUZZY_MATCH = 90
_FUZZY_PARTIAL = 85

_SEVERITY_BY_IMPORTANCE = {"required": "high", "preferred": "medium", "nice_to_have": "low"}


class MatchEngine:
    def __init__(self, taxonomy: Optional[TaxonomyStore] = None):
        self.taxonomy = taxonomy or get_taxonomy()

    # ------------------------------------------------------------------
    def match(self, candidate: CandidateProfile, job: JobProfile) -> MatchResult:
        by_canonical: Dict[str, SkillEvidence] = {
            s.canonical_id: s for s in candidate.skills if s.canonical_id
        }
        matched: List[SkillMatch] = []
        missing: List[SkillMatch] = []

        used_candidate_ids: set[str] = set()

        for req in job.requirements:
            sm = self._evaluate_requirement(req, candidate, by_canonical, used_candidate_ids)
            if sm.status == "missing":
                missing.append(sm)
            else:
                matched.append(sm)

        # ---- scoring ----
        total_weight = sum(r.weight for r in job.requirements) or 1.0
        earned = sum(sm.weight * _STATUS_FACTOR[sm.status] for sm in matched + missing)
        overall = round(100.0 * earned / total_weight, 1)

        required_coverage = self._coverage(matched + missing, "required")
        preferred_coverage = self._coverage(matched + missing, "preferred")

        verdict = self._verdict(overall, required_coverage)
        satisfied_req_ids = {
            sm.canonical_id
            for sm in matched
            if sm.canonical_id and sm.status in ("matched", "partial")
        }
        extra = self._extra_skills(
            candidate, job, used_candidate_ids, satisfied_req_ids
        )
        gaps = self._build_gaps(missing + [m for m in matched if m.status == "partial"])
        summary = self._summary(
            candidate, job, matched, missing, overall, verdict, required_coverage
        )

        # Sort for stable, readable output: by importance weight then status.
        matched.sort(key=lambda s: (-s.weight, s.status != "matched", s.requirement))
        missing.sort(key=lambda s: (-s.weight, s.requirement))

        return MatchResult(
            overall_score=overall,
            verdict=verdict,
            required_coverage=round(required_coverage, 3),
            preferred_coverage=round(preferred_coverage, 3),
            matched_skills=matched,
            missing_skills=missing,
            extra_skills=extra,
            gaps=gaps,
            summary=summary,
            candidate_name=candidate.name,
            job_title=job.title,
        )

    # ------------------------------------------------------------------
    def _evaluate_requirement(
        self,
        req,
        candidate: CandidateProfile,
        by_canonical: Dict[str, SkillEvidence],
        used_candidate_ids: set[str],
    ) -> SkillMatch:
        base = SkillMatch(
            requirement=req.display_name,
            canonical_id=req.canonical_id,
            importance=req.importance,
            weight=req.weight,
            required_min_years=req.min_years,
        )

        # 1) Direct canonical match, or any accepted alternative ("one of A/B/C").
        satisfied_id = None
        if req.canonical_id and req.canonical_id in by_canonical:
            satisfied_id = req.canonical_id
        else:
            for alt in req.alternatives:
                if alt in by_canonical:
                    satisfied_id = alt
                    break
        if satisfied_id is not None:
            cand = by_canonical[satisfied_id]
            used_candidate_ids.add(satisfied_id)
            sm = self._with_candidate(base, req, cand, direct=True)
            if satisfied_id != req.canonical_id:
                evidence_note = f" Evidence: {cand.evidence}" if cand.evidence else ""
                sm.rationale = (
                    f"Satisfies '{req.display_name}' via the accepted alternative "
                    f"'{cand.display_name}'.{evidence_note}"
                )
            return sm

        # 2) Adjacency: candidate has a related canonical skill.
        if req.canonical_id:
            for cand in candidate.skills:
                if cand.canonical_id and self.taxonomy.are_related(
                    req.canonical_id, cand.canonical_id
                ):
                    used_candidate_ids.add(cand.canonical_id)
                    base.status = "partial"
                    base.score = _STATUS_FACTOR["partial"]
                    base.candidate_skill = cand.display_name
                    base.candidate_evidence = cand.evidence
                    base.candidate_proficiency = cand.proficiency
                    base.candidate_years = cand.years_experience
                    base.rationale = (
                        f"No direct '{req.display_name}', but candidate has the "
                        f"closely related skill '{cand.display_name}'."
                    )
                    return base

        # 3) Fuzzy surface match (for requirements outside the taxonomy).
        fuzzy = self._fuzzy_candidate(req.name, candidate)
        if fuzzy is not None:
            cand, score = fuzzy
            if cand.canonical_id:
                used_candidate_ids.add(cand.canonical_id)
            if score >= _FUZZY_MATCH:
                return self._with_candidate(base, req, cand, direct=True)
            if score >= _FUZZY_PARTIAL:
                base.status = "partial"
                base.score = _STATUS_FACTOR["partial"]
                base.candidate_skill = cand.display_name
                base.candidate_evidence = cand.evidence
                base.rationale = (
                    f"Approximate match to candidate skill '{cand.display_name}' "
                    f"(similarity {score:.0f}/100)."
                )
                return base

        # 4) Missing.
        base.status = "missing"
        base.score = 0.0
        base.rationale = f"No evidence of '{req.display_name}' in the candidate profile."
        return base

    def _with_candidate(self, base: SkillMatch, req, cand: SkillEvidence, direct: bool) -> SkillMatch:
        base.candidate_skill = cand.display_name
        base.candidate_evidence = cand.evidence
        base.candidate_proficiency = cand.proficiency
        base.candidate_years = cand.years_experience

        # Experience gate: required minimum years not met -> partial.
        if (
            req.min_years is not None
            and cand.years_experience is not None
            and cand.years_experience < req.min_years
        ):
            base.status = "partial"
            base.score = _STATUS_FACTOR["partial"]
            base.rationale = (
                f"Has '{req.display_name}' but {cand.years_experience:g} yrs "
                f"experience is below the {req.min_years:g} yrs required."
            )
            return base

        base.status = "matched"
        base.score = _STATUS_FACTOR["matched"]
        evidence_note = f" Evidence: {cand.evidence}" if cand.evidence else ""
        base.rationale = f"Candidate demonstrates '{req.display_name}'.{evidence_note}"
        return base

    @staticmethod
    def _fuzzy_candidate(req_name: str, candidate: CandidateProfile):
        best = None
        best_score = 0.0
        for cand in candidate.skills:
            score = fuzz.token_set_ratio(req_name.lower(), cand.display_name.lower())
            if score > best_score:
                best_score = score
                best = cand
        if best is not None and best_score >= _FUZZY_PARTIAL:
            return best, best_score
        return None

    @staticmethod
    def _coverage(all_matches: List[SkillMatch], importance: str) -> float:
        bucket = [m for m in all_matches if m.importance == importance]
        if not bucket:
            return 1.0  # nothing required in this bucket => fully covered
        return sum(_STATUS_FACTOR[m.status] for m in bucket) / len(bucket)

    @staticmethod
    def _verdict(overall: float, required_coverage: float):
        if overall >= 75 and required_coverage >= 0.7:
            return "strong_fit"
        if overall >= 50:
            return "moderate_fit"
        return "weak_fit"

    def _extra_skills(
        self,
        candidate: CandidateProfile,
        job: JobProfile,
        used_ids: set[str],
        satisfied_req_ids: set[str],
        limit: int = 15,
    ) -> List[str]:
        required_ids = {r.canonical_id for r in job.requirements if r.canonical_id}
        job_categories = {r.category for r in job.requirements if r.category}
        extras: List[tuple[int, str]] = []
        for s in candidate.skills:
            cid = s.canonical_id
            if cid and (cid in required_ids or cid in used_ids):
                continue
            # Drop extras that are merely adjacent to a requirement the candidate
            # already earned credit for — keeps "beyond the role" genuinely novel.
            if cid and any(
                self.taxonomy.are_related(cid, rid) for rid in satisfied_req_ids
            ):
                continue
            # Prioritise extras relevant to the role's domains.
            relevance = 0 if (s.category and s.category in job_categories) else 1
            extras.append((relevance, s.display_name))
        extras.sort(key=lambda x: (x[0], x[1]))
        return [name for _, name in extras[:limit]]

    @staticmethod
    def _build_gaps(deficient: List[SkillMatch]) -> List[Gap]:
        gaps: List[Gap] = []
        for sm in deficient:
            severity = _SEVERITY_BY_IMPORTANCE.get(sm.importance, "medium")
            if sm.status == "missing":
                reason = f"'{sm.requirement}' is {sm.importance} but not evidenced."
                rec = f"Build foundational proficiency in {sm.requirement}."
            else:  # partial
                reason = sm.rationale
                if sm.required_min_years and sm.candidate_years is not None:
                    rec = (
                        f"Gain {sm.required_min_years - sm.candidate_years:g} more years / "
                        f"deeper projects in {sm.requirement}."
                    )
                else:
                    rec = f"Strengthen and provide stronger evidence for {sm.requirement}."
            gaps.append(
                Gap(
                    skill=sm.requirement,
                    canonical_id=sm.canonical_id,
                    importance=sm.importance,
                    severity=severity,
                    reason=reason,
                    recommendation=rec,
                )
            )
        # Highest severity first.
        order = {"high": 0, "medium": 1, "low": 2}
        gaps.sort(key=lambda g: order.get(g.severity, 1))
        return gaps

    @staticmethod
    def _summary(
        candidate, job, matched, missing, overall, verdict, required_coverage
    ) -> str:
        required_total = sum(1 for r in job.requirements if r.importance == "required")
        required_met = sum(
            1 for m in matched if m.importance == "required" and m.status == "matched"
        )
        strong = [m.requirement for m in matched if m.status == "matched"][:5]
        missing_required = [m.requirement for m in missing if m.importance == "required"][:5]
        verdict_label = verdict.replace("_", " ")

        parts = [
            f"{candidate.name} is a {verdict_label} for {job.title} "
            f"(overall {overall:.0f}/100).",
            f"Meets {required_met} of {required_total} required skills "
            f"({required_coverage * 100:.0f}% required coverage).",
        ]
        if strong:
            parts.append("Strengths: " + ", ".join(strong) + ".")
        if missing_required:
            parts.append("Key gaps: " + ", ".join(missing_required) + ".")
        return " ".join(parts)


def match_profiles(
    candidate: CandidateProfile,
    job: JobProfile,
    taxonomy: Optional[TaxonomyStore] = None,
) -> MatchResult:
    """Convenience wrapper around :class:`MatchEngine`."""
    return MatchEngine(taxonomy=taxonomy).match(candidate, job)
