"""Tests for the pure enrichment step (no LLM)."""
from __future__ import annotations

from app.schemas.extraction import RawCandidate, RawJob, RawJobSkill, RawSkill
from app.services.extraction import enrich_candidate, enrich_job


def test_enrich_candidate_normalizes_and_dedupes():
    raw = RawCandidate(
        name="Ada Lovelace",
        skills=[
            RawSkill(name="Python", confidence=0.9),
            RawSkill(name="py", confidence=0.4),  # duplicate of python via alias
            RawSkill(name="React.js", confidence=0.8),
            RawSkill(name="JS", confidence=0.7),
            RawSkill(name="Quantum Tea Brewing", confidence=0.5),  # unmatched, kept
        ],
    )
    profile = enrich_candidate(raw)
    ids = profile.canonical_skill_ids()
    assert "python" in ids
    assert "react" in ids
    assert "javascript" in ids
    # python should appear once (deduped), keeping the higher-confidence entry.
    pythons = [s for s in profile.skills if s.canonical_id == "python"]
    assert len(pythons) == 1
    assert pythons[0].confidence == 0.9
    # Unmatched skill is preserved (not silently dropped).
    assert any(s.canonical_id is None and "Quantum" in s.name for s in profile.skills)


def test_enrich_job_normalizes_alternatives():
    raw = RawJob(
        title="Frontend Engineer",
        required_skills=[
            RawJobSkill(
                name="React", importance="required", alternatives=["Vue.js", "Angular"]
            ),
        ],
    )
    profile = enrich_job(raw)
    req = profile.requirements[0]
    assert req.canonical_id == "react"
    assert set(req.alternatives) == {"vue", "angular"}


def test_enrich_job_assigns_weights():
    raw = RawJob(
        title="Backend Engineer",
        required_skills=[
            RawJobSkill(name="Python", importance="required"),
            RawJobSkill(name="Docker", importance="preferred"),
            RawJobSkill(name="Kubernetes", importance="nice_to_have"),
        ],
    )
    profile = enrich_job(raw)
    weights = {r.canonical_id: r.weight for r in profile.requirements}
    assert weights["python"] == 1.0
    assert weights["docker"] == 0.6
    assert weights["kubernetes"] == 0.3
