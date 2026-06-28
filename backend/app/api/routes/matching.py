"""Matching endpoints."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FuturesTimeout

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Candidate, Job, MatchRecord
from app.db.session import get_db
from app.schemas.api import AdhocMatchIn, AdhocMatchOut, MatchByIdIn, MatchOut
from app.schemas.extraction import CandidateProfile, JobProfile
from app.services.extraction import extract_candidate_profile, extract_job_profile
from app.services.matching import match_profiles

router = APIRouter(prefix="/match", tags=["matching"])


@router.post("", response_model=MatchOut)
def match_by_id(payload: MatchByIdIn, db: Session = Depends(get_db)) -> MatchOut:
    candidate = db.get(Candidate, payload.candidate_id)
    if not candidate:
        raise HTTPException(status_code=404, detail="Candidate not found")
    job = db.get(Job, payload.job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    cand_profile = CandidateProfile.model_validate(candidate.profile)
    job_profile = JobProfile.model_validate(job.profile)
    result = match_profiles(cand_profile, job_profile)

    record = MatchRecord(
        candidate_id=candidate.id,
        job_id=job.id,
        overall_score=result.overall_score,
        verdict=result.verdict,
        result=result.model_dump(mode="json"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return MatchOut(
        id=record.id, candidate_id=candidate.id, job_id=job.id, result=result
    )


@router.post("/adhoc", response_model=AdhocMatchOut)
def match_adhoc(payload: AdhocMatchIn) -> AdhocMatchOut:
    """One-shot match: extract both sides and score, without persistence.

    Ideal for the frontend "try it" flow where the user pastes a CV and a job
    description and wants an instant explainable result.

    The CV and job extractions are independent, so they run concurrently —
    roughly halving wall-clock latency versus calling them in sequence. Each is
    bounded by ``extraction_timeout`` so a slow/queued provider yields a clean
    504 instead of hanging.
    """
    timeout = get_settings().extraction_timeout
    pool = ThreadPoolExecutor(max_workers=2)
    try:
        cand_future = pool.submit(extract_candidate_profile, payload.cv_text)
        job_future = pool.submit(extract_job_profile, payload.job_text)
        candidate = cand_future.result(timeout=timeout)
        job = job_future.result(timeout=timeout)
    except FuturesTimeout as exc:
        raise HTTPException(
            status_code=504,
            detail=(
                f"The model did not respond within {timeout}s. If you're running a "
                "local model, it's likely too large for your GPU and offloading to "
                "CPU — switch to a smaller/faster model (e.g. llama3.2:3b) or lower "
                "num_ctx. If on the NVIDIA free tier, the 70B model is often too slow."
            ),
        ) from exc
    finally:
        # Don't block the response waiting on an orphaned slow call.
        pool.shutdown(wait=False, cancel_futures=True)

    result = match_profiles(candidate, job)
    return AdhocMatchOut(candidate=candidate, job=job, result=result)
