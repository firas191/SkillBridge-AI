"""HR Agent endpoint — tool-grounded recruiter brief."""
from __future__ import annotations

from fastapi import APIRouter

from app.schemas.hr import HRRecommendation, HRRequest
from app.services.hr import run_hr_recommendation

router = APIRouter(prefix="/hr", tags=["hr"])


@router.post("/recommendation", response_model=HRRecommendation)
def hr_recommendation(payload: HRRequest) -> HRRecommendation:
    """Generate an advisory, evidence-backed recruiter brief: the agent gathers
    live market evidence via its tools (salary, demand, outlook, fair-hiring
    guidelines), then reasons over it. Decision support only — a human decides.
    """
    return run_hr_recommendation(payload)
