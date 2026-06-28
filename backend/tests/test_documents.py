"""Tests for the /documents/extract-text endpoint (no LLM, no OCR needed)."""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_extract_text_endpoint_txt():
    with TestClient(app) as client:
        resp = client.post(
            "/documents/extract-text",
            files={
                "file": (
                    "cv.txt",
                    b"Senior Python developer with FastAPI and PostgreSQL experience.",
                    "text/plain",
                )
            },
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["method"] == "text"
    assert body["filename"] == "cv.txt"
    assert "Python" in body["text"]
    assert body["char_count"] > 0


def test_extract_text_endpoint_rejects_unknown_type():
    with TestClient(app) as client:
        resp = client.post(
            "/documents/extract-text",
            files={"file": ("weird.xyz", b"data", "application/octet-stream")},
        )
    assert resp.status_code == 415


def test_extract_text_endpoint_rejects_empty():
    with TestClient(app) as client:
        resp = client.post(
            "/documents/extract-text",
            files={"file": ("empty.txt", b"", "text/plain")},
        )
    assert resp.status_code == 422
