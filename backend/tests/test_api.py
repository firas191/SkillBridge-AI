"""API smoke tests using a fake LLM completer (no network)."""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
import app.services.extraction.chains as chains

CANDIDATE_JSON = json.dumps(
    {
        "name": "Ada Lovelace",
        "headline": "Software Engineer",
        "summary": "Backend engineer.",
        "skills": [
            {"name": "Python", "evidence": "Built APIs in Python", "confidence": 0.95},
            {"name": "React", "evidence": "Built dashboards", "confidence": 0.8},
        ],
        "education": ["BSc Computer Science"],
        "experience": [],
        "certifications": [],
    }
)

JOB_JSON = json.dumps(
    {
        "title": "Full-Stack Engineer",
        "company": "ACME",
        "seniority": "mid",
        "summary": "Build product features.",
        "required_skills": [
            {"name": "Python", "importance": "required"},
            {"name": "React", "importance": "required"},
            {"name": "Kubernetes", "importance": "nice_to_have"},
        ],
        "responsibilities": ["Ship features"],
    }
)


def fake_completer(prompt: str) -> str:
    if "JOB POSTING:" in prompt:
        return JOB_JSON
    return CANDIDATE_JSON


@pytest.fixture(autouse=True)
def _patch_llm(monkeypatch):
    monkeypatch.setattr(chains, "_default_completer", fake_completer)


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["taxonomy_skills"] > 100
    assert body["llm"]["provider"] in {"nvidia", "openai_compatible"}


def test_adhoc_match(client):
    resp = client.post(
        "/match/adhoc",
        json={
            "cv_text": "Ada is a backend engineer with Python and React experience.",
            "job_text": "We need a Full-Stack Engineer with Python, React, and Kubernetes.",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert {s["canonical_id"] for s in data["candidate"]["skills"]} >= {"python", "react"}
    result = data["result"]
    assert result["verdict"] == "strong_fit"
    assert result["overall_score"] >= 80
    # Kubernetes was a nice-to-have the candidate lacks -> appears as a gap.
    assert any("Kubernetes" in g["skill"] for g in result["gaps"])


def test_persisted_match_flow(client):
    c_resp = client.post(
        "/candidates/text",
        json={"text": "Ada Lovelace, backend engineer skilled in Python and React."},
    )
    assert c_resp.status_code == 201
    candidate_id = c_resp.json()["id"]

    j_resp = client.post(
        "/jobs/text",
        json={"text": "Full-Stack Engineer needed with Python, React, and Kubernetes skills."},
    )
    assert j_resp.status_code == 201
    job_id = j_resp.json()["id"]

    m_resp = client.post(
        "/match", json={"candidate_id": candidate_id, "job_id": job_id}
    )
    assert m_resp.status_code == 200
    match = m_resp.json()
    assert match["id"]
    assert match["result"]["overall_score"] >= 80
