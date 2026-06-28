"""Tests for the HR Agent (tools deterministic, LLM mocked)."""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

import app.services.hr.agent as agent
from app.main import app
from app.schemas.hr import HRRequest
from app.services.hr import run_hr_recommendation
from app.services.hr import tools

REC_JSON = json.dumps(
    {
        "decision": "interview_with_focus",
        "decision_label": "Interview — with focus areas",
        "headline": "Promising AI background; verify automation tooling.",
        "rationale": "Strong LLM/agent skills in high demand; lacks the specific automation stack.",
        "interview_focus": ["How they'd ramp on n8n"],
        "risks": ["No hands-on workflow-automation experience yet"],
        "fairness_notes": ["Treat the automation gap as learnable for an intern"],
    }
)


def rec_completer(_prompt: str) -> str:
    return REC_JSON


# ---- tools ----
def test_salary_benchmark_matches_role_and_seniority():
    sal = tools.salary_benchmark("AI & Automation Engineer Intern", "intern")
    assert sal.matched
    assert sal.median > 0
    assert sal.seniority == "intern"


def test_seniority_inferred_from_title():
    assert tools.normalize_seniority(None, "AI Engineer Intern") == "intern"
    assert tools.normalize_seniority(None, "Senior Backend Engineer") == "senior"
    assert tools.normalize_seniority(None, "Software Engineer") == "mid"


def test_skill_demand_maps_canonical_skills():
    items = tools.skill_demand(["Large Language Models", "Python", "Underwater Weaving"])
    by = {i.skill: i.demand for i in items}
    assert by.get("Large Language Models") == "very_high"
    assert by.get("Python") == "very_high"
    # unknown skill falls back to the default tier
    assert any(i.demand == "moderate" for i in items)


def test_skill_demand_by_name_and_language_filter():
    items = tools.skill_demand(["n8n", "Salesforce", "English (Language)"])
    by = {i.skill: i.demand for i in items}
    # automation tools get a real signal via the by-name table, not the default
    assert by.get("n8n") == "high"
    assert by.get("Salesforce") == "high"
    # human languages are excluded from demand evidence
    assert not any("Language" in i.skill for i in items)


# ---- agent ----
def test_agent_builds_recommendation_with_tool_evidence():
    rec = run_hr_recommendation(
        HRRequest(
            candidate_name="Firas",
            job_title="AI & Automation Engineer Intern",
            strengths=["Large Language Models", "LangChain", "Python"],
            gaps=["n8n", "Salesforce"],
            overall_score=70,
            verdict="moderate_fit",
            summary="Strong AI core, lacks automation tooling.",
        ),
        completer=rec_completer,
    )
    assert rec.decision == "interview_with_focus"
    assert rec.salary_benchmark is not None and rec.salary_benchmark.median > 0
    assert rec.skill_demand  # tool evidence attached
    assert len(rec.tool_calls) == 4
    assert {t.tool for t in rec.tool_calls} == {
        "salary_benchmark",
        "skill_demand",
        "market_outlook",
        "hiring_guidelines",
    }
    assert rec.disclaimer  # human-in-the-loop note present


def test_hr_endpoint(monkeypatch):
    monkeypatch.setattr(agent, "_default_completer", rec_completer)
    with TestClient(app) as client:
        resp = client.post(
            "/hr/recommendation",
            json={
                "candidate_name": "Firas",
                "job_title": "AI & Automation Engineer Intern",
                "strengths": ["Large Language Models", "Python"],
                "gaps": ["n8n"],
                "overall_score": 70,
                "verdict": "moderate_fit",
                "summary": "Strong AI core.",
            },
        )
    assert resp.status_code == 200
    body = resp.json()
    assert body["decision"] == "interview_with_focus"
    assert len(body["tool_calls"]) == 4
