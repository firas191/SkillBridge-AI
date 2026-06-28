"""Schemas for the Adaptive Learning Coach."""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

ResourceType = Literal["docs", "course", "video", "article", "practice", "tool"]


# ---- request ----
class GapItem(BaseModel):
    skill: str
    importance: str = "required"
    severity: str = "medium"


class LearningPlanIn(BaseModel):
    candidate_name: str = "Candidate"
    job_title: str = "the target role"
    gaps: List[GapItem] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    weekly_hours: int = Field(default=8, ge=1, le=40)


# ---- plan ----
class LearningResource(BaseModel):
    title: str
    url: Optional[str] = None
    type: ResourceType = "article"


class SkillModule(BaseModel):
    skill: str
    canonical_id: Optional[str] = None
    importance: str = "required"
    why_it_matters: str = ""
    concepts: List[str] = Field(default_factory=list)
    steps: List[str] = Field(default_factory=list)
    practice_project: str = ""
    estimated_hours: int = 0
    resources: List[LearningResource] = Field(default_factory=list)


class WeeklyMission(BaseModel):
    week: int
    theme: str = ""
    focus_skills: List[str] = Field(default_factory=list)
    tasks: List[str] = Field(default_factory=list)
    deliverable: str = ""


class LearningPlan(BaseModel):
    candidate_name: str = "Candidate"
    job_title: str = "the target role"
    overview: str = ""
    total_weeks: int = 0
    weekly_hours: int = 8
    leverage_strengths: List[str] = Field(default_factory=list)
    priority_order: List[str] = Field(default_factory=list)
    modules: List[SkillModule] = Field(default_factory=list)
    weekly_missions: List[WeeklyMission] = Field(default_factory=list)
    closing_note: str = ""
