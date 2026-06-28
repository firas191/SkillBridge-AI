"""Tests for the Interview Simulator (mocked LLM, deterministic)."""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

import app.services.interview.interviewer as interviewer
from app.main import app
from app.schemas.interview import InterviewPlanIn, InterviewReportIn, TranscriptTurn
from app.services.interview import evaluate_interview, generate_interview_plan

PLAN_JSON = json.dumps(
    {
        "intro": "Thanks for joining — let's dive in.",
        "questions": [
            {
                "question": "Walk me through how you deployed a local LLM with Flask.",
                "focus": "Technical — LLMs",
                "type": "technical",
                "what_good_looks_like": "Concrete architecture, trade-offs, metrics.",
            },
            {
                "question": "Tell me about a time you shipped under ambiguity.",
                "focus": "Behavioral",
                "type": "behavioral",
                "what_good_looks_like": "Ownership, decision-making, outcome.",
            },
            {
                "question": "You haven't used n8n — how would you ramp up?",
                "focus": "Gap — n8n",
                "type": "gap",
                "what_good_looks_like": "Learning approach, transfer from known tools.",
            },
        ],
    }
)

REPORT_JSON = json.dumps(
    {
        "summary": "Strong technical depth, behavioral answers a bit thin.",
        "assessments": [
            {
                "question": "Walk me through how you deployed a local LLM with Flask.",
                "score": 5,
                "feedback": "Excellent, specific and metric-backed.",
                "strong_answer_points": ["Architecture", "Trade-offs"],
            },
            {
                "question": "Tell me about a time you shipped under ambiguity.",
                "score": 3,
                "feedback": "Solid but generic — add a concrete outcome.",
                "strong_answer_points": ["Specific situation", "Measurable result"],
            },
            {
                "question": "You haven't used n8n — how would you ramp up?",
                "score": 4,
                "feedback": "Good learning plan and transfer reasoning.",
                "strong_answer_points": ["Concrete plan"],
            },
        ],
        "strengths": ["Hands-on LLM experience"],
        "improvements": ["Use the STAR structure for behavioral answers"],
        "next_steps": ["Practice 3 behavioral stories"],
    }
)


def plan_completer(_prompt: str) -> str:
    return PLAN_JSON


def report_completer(_prompt: str) -> str:
    return REPORT_JSON


def test_generate_plan_normalizes_ids():
    plan = generate_interview_plan(
        InterviewPlanIn(
            candidate_name="Firas",
            job_title="AI Engineer",
            strengths=["LLMs", "Python"],
            gaps=["n8n"],
            num_questions=3,
        ),
        completer=plan_completer,
    )
    assert len(plan.questions) == 3
    assert [q.id for q in plan.questions] == [1, 2, 3]
    assert plan.questions[2].type == "gap"


def test_evaluate_computes_overall_score():
    report = evaluate_interview(
        InterviewReportIn(
            candidate_name="Firas",
            job_title="AI Engineer",
            transcript=[
                TranscriptTurn(question="Q1", answer="..."),
                TranscriptTurn(question="Q2", answer="..."),
                TranscriptTurn(question="Q3", answer="..."),
            ],
        ),
        completer=report_completer,
    )
    # scores 5,3,4 -> 12/15 = 80
    assert report.overall_score == 80
    assert report.verdict == "Interview-ready"
    assert len(report.assessments) == 3


def test_interview_endpoints(monkeypatch):
    monkeypatch.setattr(interviewer, "_default_completer", plan_completer)
    with TestClient(app) as client:
        start = client.post(
            "/interview/start",
            json={
                "candidate_name": "Firas",
                "job_title": "AI Engineer",
                "strengths": ["LLMs"],
                "gaps": ["n8n"],
                "num_questions": 3,
            },
        )
    assert start.status_code == 200
    assert len(start.json()["questions"]) == 3

    monkeypatch.setattr(interviewer, "_default_completer", report_completer)
    with TestClient(app) as client:
        rep = client.post(
            "/interview/report",
            json={
                "candidate_name": "Firas",
                "job_title": "AI Engineer",
                "transcript": [
                    {"question": "Q1", "answer": "a"},
                    {"question": "Q2", "answer": "b"},
                    {"question": "Q3", "answer": "c"},
                ],
            },
        )
    assert rep.status_code == 200
    assert rep.json()["overall_score"] == 80
