"""Request/response models for the HTTP API."""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.extraction import CandidateProfile, JobProfile
from app.schemas.match import MatchResult


# ---- requests ----
class CandidateTextIn(BaseModel):
    text: str = Field(..., min_length=20, description="Raw CV / resume text")
    name: Optional[str] = None


class JobTextIn(BaseModel):
    text: str = Field(..., min_length=20, description="Raw job description text")


class MatchByIdIn(BaseModel):
    candidate_id: str
    job_id: str


class AdhocMatchIn(BaseModel):
    cv_text: str = Field(..., min_length=20)
    job_text: str = Field(..., min_length=20)


# ---- responses ----
class CandidateOut(BaseModel):
    id: str
    name: str
    profile: CandidateProfile


class CandidateSummary(BaseModel):
    id: str
    name: str
    skill_count: int


class JobOut(BaseModel):
    id: str
    title: str
    profile: JobProfile


class JobSummary(BaseModel):
    id: str
    title: str
    requirement_count: int


class MatchOut(BaseModel):
    id: Optional[str] = None
    candidate_id: Optional[str] = None
    job_id: Optional[str] = None
    result: MatchResult


class AdhocMatchOut(BaseModel):
    candidate: CandidateProfile
    job: JobProfile
    result: MatchResult


class DocumentTextOut(BaseModel):
    filename: str
    text: str
    char_count: int
    method: str  # pdf-text | pdf-ocr | docx | text | image-ocr


class HealthOut(BaseModel):
    status: str
    version: str
    llm: dict
    taxonomy_skills: int
