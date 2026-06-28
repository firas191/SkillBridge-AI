"""Interview Simulator endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from app.schemas.interview import (
    InterviewPlan,
    InterviewPlanIn,
    InterviewReport,
    InterviewReportIn,
)
from app.services.interview import evaluate_interview, generate_interview_plan

router = APIRouter(prefix="/interview", tags=["interview"])


@router.post("/start", response_model=InterviewPlan)
def start_interview(payload: InterviewPlanIn) -> InterviewPlan:
    """Generate a tailored set of mock-interview questions for the candidate."""
    return generate_interview_plan(payload)


@router.post("/report", response_model=InterviewReport)
def interview_report(payload: InterviewReportIn) -> InterviewReport:
    """Grade an answered interview transcript into a scored report with feedback."""
    return evaluate_interview(payload)
