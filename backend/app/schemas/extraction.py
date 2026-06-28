"""Structured-output schemas for extraction.

Two layers of models:

* ``Raw*``  — the exact shape we ask the LLM to return. Kept small and flat so
  even an 8B open model can produce it reliably.
* Enriched ``CandidateProfile`` / ``JobProfile`` — the Raw output *after* skill
  normalization against the canonical taxonomy. These are what the rest of the
  system (matching, storage, API) consumes.
"""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

Importance = Literal["required", "preferred", "nice_to_have"]
Proficiency = Literal["beginner", "intermediate", "advanced", "expert"]

IMPORTANCE_WEIGHT: dict[str, float] = {
    "required": 1.0,
    "preferred": 0.6,
    "nice_to_have": 0.3,
}


# ---------------------------------------------------------------------------
# Raw LLM output shapes
# ---------------------------------------------------------------------------
class RawSkill(BaseModel):
    name: str
    evidence: Optional[str] = Field(
        default=None, description="Short quote/paraphrase from the source supporting this skill"
    )
    proficiency: Optional[Proficiency] = None
    years_experience: Optional[float] = None
    confidence: float = 0.5


class RawExperience(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    duration: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)


class RawCandidate(BaseModel):
    name: str = "Unknown"
    headline: Optional[str] = None
    summary: Optional[str] = None
    total_years_experience: Optional[float] = None
    skills: List[RawSkill] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)
    experience: List[RawExperience] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)

    @field_validator("education", "certifications", mode="before")
    @classmethod
    def _coerce_str_items(cls, value: object) -> object:
        """Capable models often return education/certs as objects
        ({degree, institution, dates}). Flatten any dict/object items into a
        readable string so the schema stays simple and robust."""
        if not isinstance(value, list):
            return value
        out: list[str] = []
        for item in value:
            if isinstance(item, dict):
                parts = [str(v).strip() for v in item.values() if v and str(v).strip()]
                if parts:
                    out.append(" — ".join(parts))
            elif item is not None:
                out.append(str(item))
        return out

    @field_validator("experience", mode="before")
    @classmethod
    def _coerce_experience(cls, value: object) -> object:
        """Tolerate experience items returned as plain strings."""
        if not isinstance(value, list):
            return value
        return [{"title": i} if isinstance(i, str) else i for i in value]


class RawJobSkill(BaseModel):
    name: str
    importance: Importance = "required"
    min_years: Optional[float] = None
    # Other interchangeable skills that also satisfy this requirement
    # (for "at least one of A, B, C" phrasing).
    alternatives: List[str] = Field(default_factory=list)


class RawJob(BaseModel):
    title: str = "Untitled role"
    company: Optional[str] = None
    seniority: Optional[str] = None
    summary: Optional[str] = None
    required_skills: List[RawJobSkill] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Enriched (normalized) shapes
# ---------------------------------------------------------------------------
class SkillEvidence(BaseModel):
    """A candidate skill mapped onto the canonical taxonomy with evidence."""

    name: str  # original surface form from the CV
    canonical_id: Optional[str] = None
    canonical_name: Optional[str] = None
    category: Optional[str] = None
    evidence: Optional[str] = None
    proficiency: Optional[Proficiency] = None
    years_experience: Optional[float] = None
    confidence: float = 0.5
    match_method: str = "unmatched"
    match_score: float = 0.0

    @property
    def display_name(self) -> str:
        return self.canonical_name or self.name


class ExperienceItem(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    duration: Optional[str] = None
    highlights: List[str] = Field(default_factory=list)


class CandidateProfile(BaseModel):
    name: str = "Unknown"
    headline: Optional[str] = None
    summary: Optional[str] = None
    total_years_experience: Optional[float] = None
    skills: List[SkillEvidence] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)
    experience: List[ExperienceItem] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)

    def canonical_skill_ids(self) -> set[str]:
        return {s.canonical_id for s in self.skills if s.canonical_id}


class JobRequirement(BaseModel):
    name: str  # original surface form
    canonical_id: Optional[str] = None
    canonical_name: Optional[str] = None
    category: Optional[str] = None
    importance: Importance = "required"
    weight: float = 1.0
    min_years: Optional[float] = None
    match_method: str = "unmatched"
    match_score: float = 0.0
    # Canonical IDs of interchangeable skills that also satisfy this requirement.
    alternatives: List[str] = Field(default_factory=list)

    @property
    def display_name(self) -> str:
        return self.canonical_name or self.name


class JobProfile(BaseModel):
    title: str = "Untitled role"
    company: Optional[str] = None
    seniority: Optional[str] = None
    summary: Optional[str] = None
    requirements: List[JobRequirement] = Field(default_factory=list)
    responsibilities: List[str] = Field(default_factory=list)
