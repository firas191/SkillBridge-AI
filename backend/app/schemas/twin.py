"""Schemas for the AI Career Twin — a persistent, evolving candidate profile."""
from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.extraction import CandidateProfile

ActivityKind = Literal["match", "interview", "learning"]


# ---- save ----
class TwinSaveIn(BaseModel):
    candidate_name: str = "Candidate"
    profile: CandidateProfile = Field(default_factory=CandidateProfile)
    kind: ActivityKind = "match"
    title: str = ""  # role title / interview focus / plan target
    score: Optional[float] = None
    verdict: Optional[str] = None
    detail: dict = Field(default_factory=dict)


class TwinSaveOut(BaseModel):
    twin_id: str
    saved: bool = True


# ---- read ----
class TwinActivityOut(BaseModel):
    id: str
    kind: str
    title: str
    score: Optional[float] = None
    verdict: Optional[str] = None
    detail: dict = Field(default_factory=dict)
    created_at: datetime


class TwinAggregate(BaseModel):
    roles_explored: int = 0
    best_fit_role: Optional[str] = None
    best_fit_score: Optional[float] = None
    avg_match_score: Optional[float] = None
    interviews_taken: int = 0
    avg_interview_score: Optional[float] = None
    learning_plans: int = 0
    recurring_gaps: List[str] = Field(default_factory=list)
    top_skills: List[str] = Field(default_factory=list)


class TwinBriefing(BaseModel):
    headline: str = ""
    narrative: str = ""
    momentum: str = ""
    recommended_direction: str = ""
    next_missions: List[str] = Field(default_factory=list)


class CareerTwin(BaseModel):
    id: str
    name: str
    profile: CandidateProfile
    aggregate: TwinAggregate
    activities: List[TwinActivityOut] = Field(default_factory=list)
    briefing: TwinBriefing = Field(default_factory=TwinBriefing)
    updated_at: datetime


class TwinSummary(BaseModel):
    id: str
    name: str
    roles_explored: int = 0
    best_fit_score: Optional[float] = None
    updated_at: datetime
