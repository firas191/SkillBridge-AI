"""HR Agent tools — real, deterministic, dataset-backed.

Each tool returns structured market evidence the agent reasons over. They read
from bundled datasets so they work with no API keys; the salary tool can be
upgraded to a live source (Adzuna) when credentials are configured.
"""
from __future__ import annotations

import json
from functools import lru_cache

from rapidfuzz import fuzz, process

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.hr import SalaryBenchmark, SkillDemandItem
from app.services.taxonomy import get_normalizer
from app.services.taxonomy.store import normalize_text

log = get_logger(__name__)

_SENIORITIES = ["intern", "junior", "mid", "senior", "lead"]


@lru_cache
def _roles() -> dict:
    path = get_settings().market_roles_file
    if not path.exists():
        log.warning("Market roles dataset not found at %s", path)
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache
def _demand_map() -> dict:
    path = get_settings().skill_demand_file
    if not path.exists():
        return {"demand": {}, "default": "moderate"}
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache
def _role_index() -> list[tuple[str, str]]:
    """[(searchable_form, role_key)] over role names + aliases."""
    out: list[tuple[str, str]] = []
    for key, entry in _roles().get("roles", {}).items():
        out.append((normalize_text(key), key))
        for alias in entry.get("aliases", []):
            out.append((normalize_text(alias), key))
    return out


def _match_role(role: str) -> str | None:
    norm = normalize_text(role)
    if not norm:
        return None
    index = _role_index()
    # Exact / substring first.
    for form, key in index:
        if form and (form == norm or form in norm or norm in form):
            return key
    forms = [f for f, _ in index]
    best = process.extractOne(norm, forms, scorer=fuzz.token_set_ratio)
    if best and best[1] >= 80:
        # process.extractOne returns (choice, score, index).
        return index[best[2]][1]
    return None


def normalize_seniority(value: str | None, job_title: str = "") -> str:
    text = f"{value or ''} {job_title}".lower()
    if any(w in text for w in ("intern", "internship", "stage", "stagiaire", "trainee")):
        return "intern"
    if any(w in text for w in ("lead", "principal", "staff", "head")):
        return "lead"
    if any(w in text for w in ("senior", "sr.", "sr ")):
        return "senior"
    if any(w in text for w in ("junior", "jr.", "jr ", "entry", "graduate")):
        return "junior"
    if value in _SENIORITIES:
        return value
    return "mid"


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------
def salary_benchmark(role: str, seniority: str, region: str | None = None) -> SalaryBenchmark:
    data = _roles()
    key = _match_role(role)
    src = data.get("source", "bundled market dataset")
    currency = data.get("currency_default", "USD")
    sen = seniority if seniority in _SENIORITIES else "mid"
    if not key:
        return SalaryBenchmark(
            role=role, seniority=sen, currency=currency, source=src, matched=False
        )
    entry = data["roles"][key]
    band = entry.get("salary", {}).get(sen) or entry.get("salary", {}).get("mid")
    lo, med, hi = (band + [0, 0, 0])[:3] if band else (0, 0, 0)
    return SalaryBenchmark(
        role=key, seniority=sen, currency=currency,
        min=int(lo), median=int(med), max=int(hi),
        source=src + (f" (region hint: {region})" if region else ""),
        matched=True,
    )


def skill_demand(skills: list[str]) -> list[SkillDemandItem]:
    norm = get_normalizer()
    table = _demand_map()
    default = table.get("default", "moderate")
    demand = table.get("demand", {})
    by_name = table.get("by_name", {})
    seen: set[str] = set()
    out: list[SkillDemandItem] = []
    for raw in skills:
        if not raw or not raw.strip():
            continue
        res = norm.normalize(raw)
        # Human languages aren't a market-demand signal — leave them out.
        if (res.category or "") == "Languages":
            continue
        cid = res.canonical_id
        label = res.canonical_name or raw.strip()
        dedup = cid or label.lower()
        if dedup in seen:
            continue
        seen.add(dedup)
        if cid and cid in demand:
            tier = demand[cid]
        else:
            # Non-taxonomy tools (n8n, Salesforce, …) — look up by name.
            tier = by_name.get(normalize_text(raw), by_name.get(label.lower(), default))
        out.append(SkillDemandItem(skill=label, demand=tier))
    return out


def market_outlook(role: str) -> str:
    key = _match_role(role)
    if not key:
        return "No bundled market outlook for this exact role."
    e = _roles()["roles"][key]
    return (
        f"Demand: {e.get('demand', 'moderate').replace('_', ' ')}; "
        f"trend: {e.get('trend', 'stable')}; competition for talent: "
        f"{e.get('competition', 'moderate')}. {e.get('note', '')}"
    ).strip()


def hiring_guidelines() -> list[str]:
    return [
        "Assess on skills and evidence — not school name, age, gender, or background.",
        "Treat AI gaps for junior/intern roles as learnable; weigh trajectory and aptitude.",
        "Keep a human in the loop: this brief supports a decision, it does not make one.",
        "Document the skills-based reasons behind advancing or declining a candidate.",
    ]
