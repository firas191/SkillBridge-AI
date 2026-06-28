"""HR Agent: gather market evidence via tools, then synthesise a recruiter brief.

The agent first calls its tools (real, dataset-backed) to collect live evidence,
then runs one LLM synthesis over that evidence. Tool selection is rule-based and
transparent (every call is reported back), which is more reliable than an
LLM-driven tool loop while still demonstrating evidence-grounded tool use.
"""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from app.core.logging import get_logger
from app.schemas.hr import (
    HRRecommendation,
    HRRequest,
    ToolInvocation,
)
from app.services.extraction.chains import (
    Completer,
    _complete_structured,
    _default_completer,
)
from app.services.hr import prompts, tools

log = get_logger(__name__)


class _RawHRRec(BaseModel):
    decision: str = "interview_with_focus"
    decision_label: str = ""
    headline: str = ""
    rationale: str = ""
    interview_focus: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    fairness_notes: list[str] = Field(default_factory=list)


_DECISIONS = {"advance", "interview_with_focus", "hold", "not_yet"}
_DECISION_LABELS = {
    "advance": "Advance to interview",
    "interview_with_focus": "Interview — with focus areas",
    "hold": "Hold for comparison",
    "not_yet": "Not yet a fit",
}


def run_hr_recommendation(
    req: HRRequest, completer: Optional[Completer] = None
) -> HRRecommendation:
    seniority = tools.normalize_seniority(req.seniority, req.job_title)

    # ---- gather tool evidence ----
    salary = tools.salary_benchmark(req.job_title, seniority, req.region)
    demand = tools.skill_demand([*req.strengths[:6], *req.gaps[:6]])
    outlook = tools.market_outlook(req.job_title)
    guidelines = tools.hiring_guidelines()

    salary_summary = (
        f"{salary.role} ({salary.seniority}): {salary.currency} "
        f"{salary.min:,}–{salary.max:,} (median {salary.median:,})"
        if salary.matched
        else f"No benchmark matched for '{req.job_title}'."
    )
    tool_calls = [
        ToolInvocation(tool="salary_benchmark", summary=salary_summary, source=salary.source),
        ToolInvocation(
            tool="skill_demand",
            summary=", ".join(f"{d.skill}: {d.demand.replace('_', ' ')}" for d in demand)
            or "no skills supplied",
            source="bundled skill-demand dataset",
        ),
        ToolInvocation(tool="market_outlook", summary=outlook, source="bundled market dataset"),
        ToolInvocation(
            tool="hiring_guidelines",
            summary=f"{len(guidelines)} fair-hiring reminders applied",
            source="responsible-AI policy",
        ),
    ]

    # ---- synthesise ----
    user = prompts.HR_TEMPLATE.format(
        candidate_name=req.candidate_name,
        job_title=req.job_title,
        overall_score=round(req.overall_score),
        verdict=req.verdict or "n/a",
        summary=req.summary or "(no summary)",
        strengths=", ".join(req.strengths) if req.strengths else "(none listed)",
        gaps=", ".join(req.gaps) if req.gaps else "(none listed)",
        salary=salary_summary,
        demand="; ".join(f"{d.skill}={d.demand}" for d in demand) or "n/a",
        outlook=outlook,
        guidelines=" | ".join(guidelines),
    )
    raw = _complete_structured(
        prompts.HR_SYSTEM, user, _RawHRRec, completer or _default_completer
    )

    decision = raw.decision if raw.decision in _DECISIONS else "interview_with_focus"
    return HRRecommendation(
        candidate_name=req.candidate_name,
        job_title=req.job_title,
        decision=decision,
        decision_label=raw.decision_label or _DECISION_LABELS[decision],
        headline=raw.headline,
        rationale=raw.rationale,
        salary_benchmark=salary if salary.matched else None,
        skill_demand=demand,
        market_outlook=outlook,
        interview_focus=raw.interview_focus,
        risks=raw.risks,
        fairness_notes=raw.fairness_notes or tools.hiring_guidelines()[:2],
        tool_calls=tool_calls,
    )
