"""Tests for the AI Career Twin (persistence + aggregation, LLM mocked)."""
from __future__ import annotations

import json
import uuid

from app.db.session import SessionLocal, init_db
from app.schemas.extraction import CandidateProfile, SkillEvidence
from app.schemas.twin import TwinSaveIn
from app.services.twin import build_twin, save_activity

BRIEF_JSON = json.dumps(
    {
        "headline": "You're building real momentum toward AI engineering.",
        "narrative": "Strong AI core across roles; automation tooling is the consistent gap.",
        "momentum": "Trending upward.",
        "recommended_direction": "Lean into applied LLM/agent roles.",
        "next_missions": ["Ship one n8n workflow"],
    }
)


def brief_completer(_prompt: str) -> str:
    return BRIEF_JSON


def _profile() -> CandidateProfile:
    return CandidateProfile(
        name="Firas",
        summary="AI/ML student.",
        skills=[
            SkillEvidence(name="Python", canonical_id="python", canonical_name="Python"),
            SkillEvidence(name="LangChain", canonical_id="langchain", canonical_name="LangChain"),
        ],
    )


def test_twin_accumulates_and_aggregates():
    init_db()
    db = SessionLocal()
    name = f"Twin {uuid.uuid4().hex[:10]}"  # unique so the test is idempotent
    try:
        profile = _profile()
        # Two matches against different roles + one interview.
        id1 = save_activity(db, TwinSaveIn(
            candidate_name=name, profile=profile, kind="match",
            title="AI Engineer", score=70, verdict="moderate_fit",
            detail={"gaps": ["n8n", "Salesforce"]},
        ))
        save_activity(db, TwinSaveIn(
            candidate_name=name, profile=profile, kind="match",
            title="ML Engineer", score=82, verdict="strong_fit",
            detail={"gaps": ["n8n", "Kubernetes"]},
        ))
        save_activity(db, TwinSaveIn(
            candidate_name=name, profile=profile, kind="interview",
            title="AI Engineer", score=75,
        ))
        # Same person -> same twin id.
        id2 = save_activity(db, TwinSaveIn(
            candidate_name=name, profile=profile, kind="learning",
            title="AI Engineer",
        ))
        assert id1 == id2

        twin = build_twin(db, id1, completer=brief_completer)
        assert twin.name == name
        assert twin.aggregate.roles_explored == 2
        assert twin.aggregate.best_fit_score == 82.0
        assert twin.aggregate.best_fit_role == "ML Engineer"
        assert twin.aggregate.interviews_taken == 1
        assert twin.aggregate.avg_interview_score == 75.0
        assert twin.aggregate.learning_plans == 1
        # n8n recurs across both matches -> first recurring gap.
        assert "n8n" in twin.aggregate.recurring_gaps
        assert len(twin.activities) == 4
        assert twin.briefing.next_missions  # LLM briefing attached
    finally:
        db.close()
