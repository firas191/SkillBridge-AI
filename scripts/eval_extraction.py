#!/usr/bin/env python3
"""Extraction-quality evaluation harness.

Measures how well the live LLM extractor recovers the skills a human would
expect from a CV. Runs the *real* extraction pipeline (so it needs a configured
provider and network / credits), normalises to canonical taxonomy IDs, and
reports recall against a hand-labelled gold set.

Use it to quantify prompt changes:
    # before editing prompts
    python scripts/eval_extraction.py            > before.txt
    # after editing prompts
    python scripts/eval_extraction.py            > after.txt
    # compare the macro recall lines

Run from the repo root with the backend venv active and backend/.env configured:
    python scripts/eval_extraction.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make the backend package importable when run from the repo root.
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.services.extraction import extract_candidate_profile  # noqa: E402

# ---------------------------------------------------------------------------
# Gold set: realistic CVs with the canonical skill IDs a recruiter would expect.
# Expected IDs intentionally include skills that are only IMPLIED by experience
# (e.g. leadership/teamwork/agile from "mentored ... led ceremonies"), which is
# exactly what the improved prompt is meant to recover.
# ---------------------------------------------------------------------------
GOLD: list[dict] = [
    {
        "name": "Maria Chen — Full-Stack Engineer",
        "cv": """Maria Chen
Software Engineer — Berlin

SUMMARY
Backend-leaning full-stack engineer with 4 years building data-intensive web
applications.

EXPERIENCE
Senior Software Engineer, FinFlow (2022-present)
- Built and operated REST APIs in Python (FastAPI) serving 2M requests/day.
- Designed PostgreSQL schemas and optimized slow queries (-60% p95 latency).
- Containerized services with Docker and deployed to AWS ECS.
- Mentored two junior engineers; led agile ceremonies.

Software Engineer, Bright Apps (2020-2022)
- Developed React + TypeScript dashboards used by 500+ business customers.
- Wrote ETL jobs in Python to sync data into the warehouse.

SKILLS
Python, FastAPI, PostgreSQL, JavaScript, React, TypeScript, Docker, AWS, Git.

EDUCATION
BSc Computer Science, TU Munich.""",
        "expected": {
            "python", "fastapi", "postgresql", "react", "typescript",
            "docker", "aws", "rest-api", "git", "etl",
            "leadership", "agile",
        },
    },
    {
        "name": "Sam Okafor — Data Analyst",
        "cv": """Sam Okafor
Data Analyst — Remote

SUMMARY
Data analyst with 3 years turning messy data into decisions.

EXPERIENCE
Data Analyst, RetailIQ (2021-present)
- Wrote complex SQL to model sales across 12 markets.
- Built Tableau dashboards used weekly by the leadership team.
- Automated reporting in Python with pandas, cutting manual work by 8 hrs/week.
- Ran A/B tests and presented statistical findings to stakeholders.

SKILLS
SQL, Python, pandas, Tableau, Excel, statistics, data visualization.""",
        "expected": {
            "sql", "python", "pandas", "tableau", "excel",
            "statistics", "data-visualization", "data-analysis",
        },
    },
]


def evaluate() -> int:
    recalls: list[float] = []
    print("=" * 72)
    print("SkillBridge AI — extraction recall evaluation")
    print("=" * 72)

    for case in GOLD:
        expected: set[str] = case["expected"]
        try:
            profile = extract_candidate_profile(case["cv"])
        except Exception as exc:  # noqa: BLE001
            print(f"\n[{case['name']}] FAILED: {exc}")
            print("Is backend/.env configured with a working provider?")
            return 1

        predicted = profile.canonical_skill_ids()
        hit = expected & predicted
        missed = expected - predicted
        recall = len(hit) / len(expected) if expected else 1.0
        recalls.append(recall)

        print(f"\n[{case['name']}]")
        print(f"  expected   : {len(expected)} skills")
        print(f"  extracted  : {len(predicted)} canonical skills total")
        print(f"  recall     : {recall * 100:5.1f}%  ({len(hit)}/{len(expected)})")
        if missed:
            print(f"  MISSED     : {', '.join(sorted(missed))}")
        # Show a couple of evidence samples to eyeball quality.
        samples = [s for s in profile.skills if s.canonical_id in hit][:3]
        for s in samples:
            ev = (s.evidence or "").strip().replace("\n", " ")
            print(f"    - {s.display_name}: \"{ev[:90]}\"")

    macro = sum(recalls) / len(recalls) if recalls else 0.0
    print("\n" + "-" * 72)
    print(f"MACRO RECALL: {macro * 100:.1f}%  across {len(recalls)} CVs")
    print("-" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(evaluate())
