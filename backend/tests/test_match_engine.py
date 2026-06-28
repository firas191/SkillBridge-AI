"""Tests for the explainable match engine (deterministic, no LLM)."""
from __future__ import annotations

from app.schemas.extraction import (
    CandidateProfile,
    JobProfile,
    JobRequirement,
    SkillEvidence,
)
from app.services.matching import match_profiles


def skill(cid, name, years=None, prof=None, evidence="seen in CV"):
    return SkillEvidence(
        name=name,
        canonical_id=cid,
        canonical_name=name,
        evidence=evidence,
        years_experience=years,
        proficiency=prof,
        match_method="exact",
        match_score=100.0,
    )


def req(cid, name, importance="required", weight=1.0, min_years=None):
    return JobRequirement(
        name=name,
        canonical_id=cid,
        canonical_name=name,
        importance=importance,
        weight=weight,
        min_years=min_years,
        match_method="exact",
        match_score=100.0,
    )


def test_mixed_match_scoring_and_verdict():
    candidate = CandidateProfile(
        name="Grace Hopper",
        skills=[
            skill("python", "Python", years=5),
            skill("javascript", "JavaScript"),
            skill("docker", "Docker", years=4),
            skill("sql", "SQL"),
        ],
    )
    job = JobProfile(
        title="Full-Stack Engineer",
        requirements=[
            req("python", "Python", "required", 1.0),               # direct match
            req("react", "React", "required", 1.0),                 # adjacency via javascript -> partial
            req("docker", "Docker", "required", 1.0, min_years=6),  # years gate -> partial
            req("tableau", "Tableau", "required", 1.0),             # clean miss (no adjacency)
        ],
    )
    result = match_profiles(candidate, job)

    # earned = 1.0(py) + 0.5(react) + 0.5(docker) + 0(tableau) = 2.0
    # total  = 4.0  -> 50.0
    assert result.overall_score == 50.0
    assert result.verdict == "moderate_fit"
    assert result.required_coverage == 0.5

    statuses = {m.requirement: m.status for m in result.matched_skills}
    assert statuses.get("Python") == "matched"
    assert statuses.get("React") == "partial"   # adjacent skill, not direct
    assert statuses.get("Docker") == "partial"  # insufficient years

    missing_names = {m.requirement for m in result.missing_skills}
    assert "Tableau" in missing_names

    # SQL is a genuine extra strength the role didn't ask for.
    assert "SQL" in result.extra_skills
    # JavaScript was consumed to partially satisfy React, so it is NOT an extra.
    assert "JavaScript" not in result.extra_skills

    # Every gap carries a recommendation (feeds the learning coach).
    assert result.gaps
    assert all(g.recommendation for g in result.gaps)


def test_strong_fit_full_coverage():
    candidate = CandidateProfile(
        name="Strong Candidate",
        skills=[
            skill("python", "Python", years=6),
            skill("react", "React", years=4),
            skill("docker", "Docker", years=4),
        ],
    )
    job = JobProfile(
        title="Engineer",
        requirements=[
            req("python", "Python", "required", 1.0),
            req("react", "React", "required", 1.0),
            req("docker", "Docker", "required", 1.0, min_years=3),
        ],
    )
    result = match_profiles(candidate, job)
    assert result.overall_score == 100.0
    assert result.verdict == "strong_fit"
    assert result.required_coverage == 1.0
    assert not result.missing_skills


def test_min_years_gate_creates_partial():
    candidate = CandidateProfile(
        name="Junior", skills=[skill("python", "Python", years=1)]
    )
    job = JobProfile(
        title="Senior",
        requirements=[req("python", "Python", "required", 1.0, min_years=5)],
    )
    result = match_profiles(candidate, job)
    assert result.matched_skills[0].status == "partial"
    assert result.overall_score == 50.0


def test_alternative_skill_satisfies_one_of_requirement():
    # "At least one of LangChain / OpenAI API / Mistral" — candidate has LangChain.
    candidate = CandidateProfile(
        name="Dev", skills=[skill("langchain", "LangChain")]
    )
    requirement = JobRequirement(
        name="OpenAI API",
        canonical_id=None,  # primary not in taxonomy
        canonical_name="OpenAI API",
        importance="required",
        weight=1.0,
        alternatives=["langchain"],  # any of these satisfies it
    )
    job = JobProfile(title="AI Engineer", requirements=[requirement])
    result = match_profiles(candidate, job)

    assert result.overall_score == 100.0
    assert result.matched_skills[0].status == "matched"
    assert "alternative" in result.matched_skills[0].rationale.lower()


def test_unrelated_terms_do_not_fuzzy_match():
    # "Computer Science" must not match "Computer Vision" just because they
    # share the generic word "computer".
    candidate = CandidateProfile(
        name="Student", skills=[skill("computer-vision", "Computer Vision")]
    )
    requirement = JobRequirement(
        name="Computer Science",
        canonical_id=None,
        canonical_name="Computer Science",
        importance="required",
        weight=1.0,
    )
    job = JobProfile(title="Role", requirements=[requirement])
    result = match_profiles(candidate, job)

    assert not result.matched_skills
    assert result.missing_skills
    assert result.missing_skills[0].requirement == "Computer Science"


def test_evidence_is_carried_through():
    candidate = CandidateProfile(
        name="X",
        skills=[skill("python", "Python", evidence="Built ETL in Python at ACME")],
    )
    job = JobProfile(title="Y", requirements=[req("python", "Python")])
    result = match_profiles(candidate, job)
    assert "ACME" in result.matched_skills[0].candidate_evidence
