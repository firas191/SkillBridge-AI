"""Tests for the anti-hallucination grounding guard on job extraction."""
from __future__ import annotations

import json

from app.services.extraction import extract_job_profile


def test_grounding_drops_hallucinated_requirement():
    job_text = (
        "Senior Engineer. Required: Python, React, and SQL. "
        "Nice to have: Docker."
    )
    # The model output invents 'iOS Development', which is NOT in the posting.
    payload = {
        "title": "Senior Engineer",
        "required_skills": [
            {"name": "Python", "importance": "required"},
            {"name": "React", "importance": "required"},
            {"name": "SQL", "importance": "required"},
            {"name": "Docker", "importance": "nice_to_have"},
            {"name": "iOS Development", "importance": "required"},
        ],
        "responsibilities": [],
    }
    profile = extract_job_profile(job_text, completer=lambda _p: json.dumps(payload))
    ids = {r.canonical_id for r in profile.requirements}

    assert {"python", "react", "sql", "docker"} <= ids
    # Hallucinated requirement is grounded out.
    assert "ios" not in ids


def test_grounding_keeps_verbose_named_real_requirements():
    """Token fallback recovers real requirements the model named verbosely,
    while still dropping pure inventions."""
    job_text = (
        "You will wire n8n, Make, Zapier workflows. Professional English required."
    )
    payload = {
        "title": "Automation Engineer",
        "required_skills": [
            {"name": "n8n, Make, Zapier, or similar", "importance": "required"},
            {"name": "English (professional working proficiency)", "importance": "required"},
            {"name": "iOS Development", "importance": "required"},  # invented
        ],
        "responsibilities": [],
    }
    profile = extract_job_profile(job_text, completer=lambda _p: json.dumps(payload))
    names = [r.name for r in profile.requirements]

    assert any("n8n" in n for n in names)       # real, verbosely named -> kept
    assert any("English" in n for n in names)   # real, parenthetical -> kept
    assert not any("iOS" in n for n in names)   # invented -> dropped


def test_grounding_keeps_alias_and_tech_token_forms():
    job_text = "We use Node.js and C++. Experience with REST APIs required."
    payload = {
        "title": "Engineer",
        "required_skills": [
            {"name": "Node.js", "importance": "required"},
            {"name": "C++", "importance": "required"},
            {"name": "REST API Design", "importance": "required"},
            {"name": "Kubernetes", "importance": "required"},  # not mentioned
        ],
        "responsibilities": [],
    }
    profile = extract_job_profile(job_text, completer=lambda _p: json.dumps(payload))
    ids = {r.canonical_id for r in profile.requirements}

    assert {"node-js", "cpp", "rest-api"} <= ids  # alias / tech-token grounding
    assert "kubernetes" not in ids
