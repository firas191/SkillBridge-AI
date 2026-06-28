"""Tests for the Adaptive Learning Coach (mocked LLM, deterministic)."""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

import app.services.learning.coach as coach
from app.main import app
from app.schemas.learning import GapItem, LearningPlanIn
from app.services.learning import generate_learning_plan, resources_for

PLAN_JSON = json.dumps(
    {
        "overview": "A focused 6-week sprint to job-readiness.",
        "total_weeks": 6,
        "leverage_strengths": ["Your Python skills accelerate n8n scripting."],
        "priority_order": ["n8n", "Python"],
        "modules": [
            {
                "skill": "n8n",
                "importance": "required",
                "why_it_matters": "Core automation platform for the role.",
                "concepts": ["nodes", "workflows", "webhooks"],
                "steps": ["Install n8n", "Build a webhook workflow"],
                "practice_project": "Build a Slack-to-Sheets automation.",
                "estimated_hours": 12,
                "resources": [{"title": "n8n Docs", "url": "https://docs.n8n.io", "type": "docs"}],
            },
            {
                "skill": "Python",
                "importance": "preferred",
                "why_it_matters": "Underpins custom automation nodes.",
                "concepts": ["functions"],
                "steps": ["Review basics"],
                "practice_project": "Write a small script.",
                "estimated_hours": 5,
                "resources": [],
            },
        ],
        "weekly_missions": [
            {
                "week": 1,
                "theme": "Automation foundations",
                "focus_skills": ["n8n"],
                "tasks": ["Set up n8n locally"],
                "deliverable": "First working workflow",
            }
        ],
        "closing_note": "You're closer than you think.",
    }
)


def fake_completer(_prompt: str) -> str:
    return PLAN_JSON


def test_resources_catalog_and_fallback():
    py = resources_for("Python")
    assert any("python.org" in (r.url or "") for r in py)  # curated catalog hit
    unknown = resources_for("Underwater Basket Weaving")
    assert unknown and all(r.url for r in unknown)  # trusted-platform fallbacks


def test_generate_plan_enriches_resources():
    req = LearningPlanIn(
        candidate_name="Firas",
        job_title="AI & Automation Engineer",
        gaps=[GapItem(skill="n8n", importance="required")],
        strengths=["Python", "LangChain"],
        weekly_hours=10,
    )
    plan = generate_learning_plan(req, completer=fake_completer)

    assert plan.candidate_name == "Firas"
    assert plan.weekly_hours == 10
    assert plan.total_weeks == 6
    assert plan.modules

    py_mod = next(m for m in plan.modules if m.canonical_id == "python")
    # Curated catalog link injected even though the model returned none.
    assert any("python.org" in (r.url or "") for r in py_mod.resources)

    n8n_mod = next(m for m in plan.modules if m.skill == "n8n")
    assert n8n_mod.resources  # model docs + fallback links


def test_learning_endpoint(monkeypatch):
    monkeypatch.setattr(coach, "_default_completer", fake_completer)
    with TestClient(app) as client:
        resp = client.post(
            "/learning-plan",
            json={
                "candidate_name": "Firas",
                "job_title": "AI & Automation Engineer",
                "gaps": [{"skill": "n8n", "importance": "required"}],
                "strengths": ["Python"],
                "weekly_hours": 8,
            },
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_weeks"] == 6
    assert body["modules"]
    assert body["weekly_missions"]
