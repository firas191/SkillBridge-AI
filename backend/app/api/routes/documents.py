"""Document text-extraction endpoint.

Reads PDF / DOCX / TXT / image uploads into plain text — fully offline, no API
key. The frontend uses this to populate the editable CV / job boxes from a
file, so the user can verify (and fix) the extracted text before matching.
"""
from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.api import DocumentTextOut
from app.services.extraction import OCRUnavailableError, extract_text

router = APIRouter(prefix="/documents", tags=["documents"])

# Reject absurdly large uploads early (10 MB).
_MAX_BYTES = 10 * 1024 * 1024


@router.post("/extract-text", response_model=DocumentTextOut)
async def extract_document_text(file: UploadFile = File(...)) -> DocumentTextOut:
    data = await file.read()
    if not data:
        raise HTTPException(status_code=422, detail="Empty file.")
    if len(data) > _MAX_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB).")

    try:
        parsed = extract_text(data, file.filename or "upload")
    except ValueError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except OCRUnavailableError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if not parsed.text.strip():
        raise HTTPException(
            status_code=422,
            detail="No readable text found. If this is a scanned image, try a clearer scan.",
        )

    return DocumentTextOut(
        filename=parsed.filename,
        text=parsed.text,
        char_count=parsed.char_count,
        method=parsed.method,
    )
