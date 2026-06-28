"""Job ingestion endpoints."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Job
from app.db.session import get_db
from app.schemas.api import JobOut, JobSummary, JobTextIn
from app.schemas.extraction import JobProfile
from app.services.extraction import extract_job_profile

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/text", response_model=JobOut, status_code=201)
def create_from_text(payload: JobTextIn, db: Session = Depends(get_db)) -> JobOut:
    profile = extract_job_profile(payload.text)
    row = Job(
        title=profile.title or "Untitled role",
        company=profile.company,
        raw_text=payload.text,
        profile=profile.model_dump(mode="json"),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return JobOut(id=row.id, title=row.title, profile=profile)


@router.get("", response_model=List[JobSummary])
def list_jobs(db: Session = Depends(get_db)) -> List[JobSummary]:
    rows = db.execute(select(Job).order_by(Job.created_at.desc())).scalars().all()
    return [
        JobSummary(
            id=r.id,
            title=r.title,
            requirement_count=len((r.profile or {}).get("requirements", [])),
        )
        for r in rows
    ]


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: str, db: Session = Depends(get_db)) -> JobOut:
    row = db.get(Job, job_id)
    if not row:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobOut(id=row.id, title=row.title, profile=JobProfile.model_validate(row.profile))
