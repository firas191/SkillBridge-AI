"""AI Career Twin endpoints — the persistent, evolving candidate profile."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.twin import CareerTwin, TwinSaveIn, TwinSaveOut, TwinSummary
from app.services.twin import build_twin, list_twins, save_activity

router = APIRouter(prefix="/twin", tags=["career-twin"])


@router.post("/save", response_model=TwinSaveOut)
def save_to_twin(payload: TwinSaveIn, db: Session = Depends(get_db)) -> TwinSaveOut:
    """Log an activity (match / interview / learning plan) to the candidate's
    Career Twin, creating it on first save."""
    twin_id = save_activity(db, payload)
    return TwinSaveOut(twin_id=twin_id)


@router.get("/list", response_model=List[TwinSummary])
def twins(db: Session = Depends(get_db)) -> List[TwinSummary]:
    return list_twins(db)


@router.get("/{twin_id}", response_model=CareerTwin)
def get_twin(twin_id: str, db: Session = Depends(get_db)) -> CareerTwin:
    """The aggregated Career Twin: profile, activity timeline, stats, and an AI
    briefing on momentum and next missions."""
    try:
        return build_twin(db, twin_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
