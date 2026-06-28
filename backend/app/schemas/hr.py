"""Schemas for the HR Agent (tool-using recruiter brief)."""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

Decision = Literal["advance", "interview_with_focus", "hold", "not_yet"]


# ---- request ----
class HRRequest(BaseModel):
    candidate_name: str = "Candidate"
    job_title: str = "the role"
    region: Optional[str] = None
    seniority: Optional[str] = None  # intern|junior|mid|senior|lead
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    overall_score: float = 0.0
    verdict: Optional[str] = None
    summary: Optional[str] = None


# ---- tool outputs ----
class SalaryBenchmark(BaseModel):
    role: str
    seniority: str
    currency: str = "USD"
    min: int = 0
    median: int = 0
    max: int = 0
    source: str = ""
    matched: bool = True


class SkillDemandItem(BaseModel):
    skill: str
    demand: str = "moderate"  # very_high|high|moderate|niche


class ToolInvocation(BaseModel):
    tool: str
    summary: str = ""
    source: str = ""


# ---- recommendation ----
class HRRecommendation(BaseModel):
    candidate_name: str = "Candidate"
    job_title: str = "the role"
    decision: Decision = "interview_with_focus"
    decision_label: str = ""
    headline: str = ""
    rationale: str = ""
    salary_benchmark: Optional[SalaryBenchmark] = None
    skill_demand: List[SkillDemandItem] = Field(default_factory=list)
    market_outlook: str = ""
    interview_focus: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    fairness_notes: List[str] = Field(default_factory=list)
    tool_calls: List[ToolInvocation] = Field(default_factory=list)
    disclaimer: str = (
        "Decision support only — evidence to assist a human recruiter, who makes "
        "the final call. Compare candidates on skills and evidence, not background."
    )
