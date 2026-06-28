"""Adaptive Learning Coach endpoint."""
from __future__ import annotations

from fastapi import APIRouter

from app.schemas.learning import LearningPlan, LearningPlanIn
from app.services.learning import generate_learning_plan

router = APIRouter(tags=["learning"])


@router.post("/learning-plan", response_model=LearningPlan)
def create_learning_plan(payload: LearningPlanIn) -> LearningPlan:
    """Turn a candidate's skill gaps (from a match) into a sequenced, resourced
    upskilling plan with weekly missions and portfolio-building practice projects.
    """
    return generate_learning_plan(payload)
