"""Interview Simulator service.

Two stateless LLM steps:
  1. generate_interview_plan  — tailored questions from strengths + gaps + role.
  2. evaluate_interview       — grade the answered transcript into a report.

The overall score is computed deterministically from the per-answer scores
(mean of 0-5 -> 0-100), so it can't drift from the individual grades.
"""
from __future__ import annotations

from typing import Optional

from app.core.logging import get_logger
from app.schemas.interview import (
    InterviewPlan,
    InterviewPlanIn,
    InterviewReport,
    InterviewReportIn,
)
from app.services.extraction.chains import (
    Completer,
    _complete_structured,
    _default_completer,
)
from app.services.interview import prompts

log = get_logger(__name__)


def generate_interview_plan(
    req: InterviewPlanIn, completer: Optional[Completer] = None
) -> InterviewPlan:
    user = prompts.QUESTION_TEMPLATE.format(
        job_title=req.job_title,
        name=req.candidate_name,
        strengths=", ".join(req.strengths) if req.strengths else "(none listed)",
        gaps=", ".join(req.gaps) if req.gaps else "(none listed)",
        summary=req.summary or "(no extra context)",
        num_questions=req.num_questions,
    )
    plan = _complete_structured(
        prompts.QUESTION_SYSTEM, user, InterviewPlan, completer or _default_completer
    )
    # Normalise ids in case the model omitted/duplicated them.
    for i, q in enumerate(plan.questions, start=1):
        q.id = i
    return plan


def _verdict(score: int) -> str:
    if score >= 75:
        return "Interview-ready"
    if score >= 50:
        return "Promising — with prep"
    return "Needs practice"


def _format_transcript(report_in: InterviewReportIn) -> str:
    blocks = []
    for i, turn in enumerate(report_in.transcript, start=1):
        blocks.append(
            f"Q{i} ({turn.focus}): {turn.question}\n"
            f"Strong answer covers: {turn.what_good_looks_like}\n"
            f"Candidate answered: {turn.answer or '(no answer given)'}"
        )
    return "\n\n".join(blocks)


def evaluate_interview(
    report_in: InterviewReportIn, completer: Optional[Completer] = None
) -> InterviewReport:
    user = prompts.REPORT_TEMPLATE.format(
        job_title=report_in.job_title,
        name=report_in.candidate_name,
        transcript=_format_transcript(report_in),
    )
    report = _complete_structured(
        prompts.REPORT_SYSTEM, user, InterviewReport, completer or _default_completer
    )
    report.candidate_name = report_in.candidate_name
    report.job_title = report_in.job_title

    # Deterministic overall score from per-answer grades (0-5 -> 0-100).
    if report.assessments:
        scores = [max(0, min(5, a.score)) for a in report.assessments]
        report.overall_score = round(sum(scores) / (len(scores) * 5) * 100)
    report.verdict = _verdict(report.overall_score)
    return report
