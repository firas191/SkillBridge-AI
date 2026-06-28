"""SQLAlchemy ORM models.

Structured LLM outputs (skill profiles, match results) are stored as JSON
columns. This keeps the schema stable while the structured-output shapes
evolve, and mirrors how document/feature stores are used in production ML
systems. Relational columns are kept for the fields we query/sort on.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import JSON


def _uuid() -> str:
    return uuid.uuid4().hex


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(255), default="Unknown")
    source_filename: Mapped[str | None] = mapped_column(String(512), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, default="")
    # Full CandidateProfile (pydantic) serialised to JSON.
    profile: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    matches: Mapped[list["MatchRecord"]] = relationship(
        back_populates="candidate", cascade="all, delete-orphan"
    )


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(255), default="Untitled role")
    company: Mapped[str | None] = mapped_column(String(255), nullable=True)
    raw_text: Mapped[str] = mapped_column(Text, default="")
    # Full JobProfile (pydantic) serialised to JSON.
    profile: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    matches: Mapped[list["MatchRecord"]] = relationship(
        back_populates="job", cascade="all, delete-orphan"
    )


class MatchRecord(Base):
    __tablename__ = "matches"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=_uuid)
    candidate_id: Mapped[str] = mapped_column(ForeignKey("candidates.id"))
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"))
    overall_score: Mapped[float] = mapped_column(Float, default=0.0)
    verdict: Mapped[str] = mapped_column(String(32), default="weak_fit")
    # Full MatchResult (pydantic) serialised to JSON.
    result: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    candidate: Mapped[Candidate] = relationship(back_populates="matches")
    job: Mapped[Job] = relationship(back_populates="matches")
