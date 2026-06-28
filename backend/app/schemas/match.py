"""Schemas for explainable matching output."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

MatchStatus = Literal["matched", "partial", "missing"]
Verdict = Literal["strong_fit", "moderate_fit", "weak_fit"]


class SkillMatch(BaseModel):
    requirement: str
    canonical_id: Optional[str] = None
    importance: str = "required"
    weight: float = 1.0
    status: MatchStatus = "missing"
    # Fraction of this requirement's weight that the candidate earns (0..1).
    score: float = 0.0
    candidate_skill: Optional[str] = None
    candidate_evidence: Optional[str] = None
    candidate_proficiency: Optional[str] = None
    candidate_years: Optional[float] = None
    required_min_years: Optional[float] = None
    rationale: str = ""


class Gap(BaseModel):
    skill: str
    canonical_id: Optional[str] = None
    importance: str = "required"
    severity: Literal["high", "medium", "low"] = "medium"
    reason: str = ""
    recommendation: str = ""


class MatchResult(BaseModel):
    overall_score: float = 0.0  # 0..100
    verdict: Verdict = "weak_fit"
    required_coverage: float = 0.0  # 0..1
    preferred_coverage: float = 0.0  # 0..1
    matched_skills: List[SkillMatch] = Field(default_factory=list)
    missing_skills: List[SkillMatch] = Field(default_factory=list)
    extra_skills: List[str] = Field(default_factory=list)
    gaps: List[Gap] = Field(default_factory=list)
    summary: str = ""
    candidate_name: Optional[str] = None
    job_title: Optional[str] = None
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
