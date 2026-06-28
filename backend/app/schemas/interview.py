"""Schemas for the Interview Simulator."""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field

QuestionType = Literal["technical", "behavioral", "gap", "motivation"]


# ---- start ----
class InterviewPlanIn(BaseModel):
    candidate_name: str = "Candidate"
    job_title: str = "the role"
    summary: Optional[str] = None
    strengths: List[str] = Field(default_factory=list)
    gaps: List[str] = Field(default_factory=list)
    num_questions: int = Field(default=5, ge=3, le=8)


class InterviewQuestion(BaseModel):
    id: int = 0
    question: str
    focus: str = ""
    type: QuestionType = "technical"
    what_good_looks_like: str = ""


class InterviewPlan(BaseModel):
    intro: str = ""
    questions: List[InterviewQuestion] = Field(default_factory=list)


# ---- report ----
class TranscriptTurn(BaseModel):
    question: str
    focus: str = ""
    what_good_looks_like: str = ""
    answer: str = ""


class InterviewReportIn(BaseModel):
    candidate_name: str = "Candidate"
    job_title: str = "the role"
    transcript: List[TranscriptTurn] = Field(default_factory=list)


class AnswerAssessment(BaseModel):
    question: str
    score: int = 0  # 0-5
    feedback: str = ""
    strong_answer_points: List[str] = Field(default_factory=list)


class InterviewReport(BaseModel):
    candidate_name: str = "Candidate"
    job_title: str = "the role"
    overall_score: int = 0  # 0-100 (computed from per-answer scores)
    verdict: str = ""
    summary: str = ""
    assessments: List[AnswerAssessment] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    improvements: List[str] = Field(default_factory=list)
    next_steps: List[str] = Field(default_factory=list)
