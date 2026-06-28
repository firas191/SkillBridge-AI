"""Candidate ingestion endpoints."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Candidate
from app.db.session import get_db
from app.schemas.api import CandidateOut, CandidateSummary, CandidateTextIn
from app.schemas.extraction import CandidateProfile
from app.services.extraction import extract_candidate_profile, extract_text

router = APIRouter(prefix="/candidates", tags=["candidates"])


def _persist(db: Session, profile: CandidateProfile, raw_text: str, filename: str | None) -> Candidate:
    row = Candidate(
        name=profile.name or "Unknown",
        source_filename=filename,
        raw_text=raw_text,
        profile=profile.model_dump(mode="json"),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.post("/text", response_model=CandidateOut, status_code=201)
def create_from_text(payload: CandidateTextIn, db: Session = Depends(get_db)) -> CandidateOut:
    profile = extract_candidate_profile(payload.text)
    if payload.name:
        profile.name = payload.name
    row = _persist(db, profile, payload.text, None)
    return CandidateOut(id=row.id, name=row.name, profile=profile)


@router.post("/upload", response_model=CandidateOut, status_code=201)
async def create_from_upload(
    file: UploadFile = File(...), db: Session = Depends(get_db)
) -> CandidateOut:
    data = await file.read()
    try:
        parsed = extract_text(data, file.filename or "upload")
    except ValueError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    if not parsed.text.strip():
        raise HTTPException(status_code=422, detail="No extractable text in document.")
    profile = extract_candidate_profile(parsed.text)
    row = _persist(db, profile, parsed.text, parsed.filename)
    return CandidateOut(id=row.id, name=row.name, profile=profile)


@router.get("", response_model=List[CandidateSummary])
def list_candidates(db: Session = Depends(get_db)) -> List[CandidateSummary]:
    rows = db.execute(select(Candidate).order_by(Candidate.created_at.desc())).scalars().all()
    return [
        CandidateSummary(
            id=r.id, name=r.name, skill_count=len((r.profile or {}).get("skills", []))
        )
        for r in rows
    ]


@router.get("/{candidate_id}", response_model=CandidateOut)
def get_candidate(candidate_id: str, db: Session = Depends(get_db)) -> CandidateOut:
    row = db.get(Candidate, candidate_id)
    if not row:
        raise HTTPException(status_code=404, detail="Candidate not found")
    return CandidateOut(
        id=row.id, name=row.name, profile=CandidateProfile.model_validate(row.profile)
    )
