"""Health & metadata endpoints."""
from __future__ import annotations

from fastapi import APIRouter

from app import __version__
from app.core.llm import provider_info
from app.schemas.api import HealthOut
from app.services.taxonomy import get_taxonomy

router = APIRouter(tags=["system"])


@router.get("/health", response_model=HealthOut)
def health() -> HealthOut:
    return HealthOut(
        status="ok",
        version=__version__,
        llm=provider_info(),
        taxonomy_skills=len(get_taxonomy()),
    )
