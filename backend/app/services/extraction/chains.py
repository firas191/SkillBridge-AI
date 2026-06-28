"""Extraction chains: text -> structured, taxonomy-normalized profiles.

The LLM call is isolated behind a ``Completer`` callable so that:
  * production uses the configured provider (NVIDIA NIM / Ollama), and
  * tests can inject a deterministic fake completer with no network.

The *enrichment* step (normalising skills onto the taxonomy, de-duplicating,
weighting requirements) is pure and fully unit-testable.
"""
from __future__ import annotations

import hashlib
import re
from collections import OrderedDict
from threading import Lock
from typing import Callable, Optional

from app.core.config import get_settings
from app.core.llm import LLMCallError, get_chat_model, safe_parse
from app.core.logging import get_logger
from app.schemas.extraction import (
    IMPORTANCE_WEIGHT,
    CandidateProfile,
    ExperienceItem,
    JobProfile,
    JobRequirement,
    RawCandidate,
    RawJob,
    SkillEvidence,
)
from app.services.extraction import prompts
from app.services.taxonomy import SkillNormalizer, get_normalizer, get_taxonomy
from app.services.taxonomy.store import normalize_text

log = get_logger(__name__)

# A completer takes a fully-rendered prompt and returns the model's text.
Completer = Callable[[str], str]

# ---------------------------------------------------------------------------
# Extraction cache (content + model addressed).
# Re-running the same CV/job is instant and spends no credits. Keyed by the
# active model so switching 8B<->70B doesn't return stale results. In-memory
# and per-process (cleared on restart); swap for Redis in a multi-worker deploy.
# ---------------------------------------------------------------------------
_CACHE_MAX = 256
_CACHE_LOCK = Lock()
_CANDIDATE_CACHE: "OrderedDict[str, CandidateProfile]" = OrderedDict()
_JOB_CACHE: "OrderedDict[str, JobProfile]" = OrderedDict()


def _cache_key(kind: str, text: str) -> str:
    model = get_settings().active_chat_model
    return hashlib.sha256(f"{kind}\x00{model}\x00{text}".encode("utf-8")).hexdigest()


def _cache_get(cache: OrderedDict, key: str):
    with _CACHE_LOCK:
        item = cache.get(key)
        if item is not None:
            cache.move_to_end(key)
            return item.model_copy(deep=True)  # defensive copy; callers may mutate
    return None


def _cache_put(cache: OrderedDict, key: str, value) -> None:
    with _CACHE_LOCK:
        cache[key] = value.model_copy(deep=True)
        cache.move_to_end(key)
        while len(cache) > _CACHE_MAX:
            cache.popitem(last=False)


class ExtractionError(RuntimeError):
    pass


def _coerce_content(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):  # some providers return content parts
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("text", "")))
        return "".join(parts)
    return str(content)


def _default_completer(prompt: str) -> str:
    # Temperature 0 for extraction: we want faithful, reproducible structure,
    # not creative variation. This removes run-to-run recall fluctuation.
    model = get_chat_model(temperature=0.0)
    try:
        response = model.invoke(prompt)
    except Exception as exc:  # noqa: BLE001 - normalise any provider error
        raise LLMCallError(
            "The AI model call failed. This is usually a temporary provider error "
            "or a free-tier rate limit (e.g. Gemini allows ~15 requests/minute) — "
            "wait a minute and try again, or move to a higher tier / different "
            f"provider in backend/.env. (provider error: {type(exc).__name__})"
        ) from exc
    return _coerce_content(getattr(response, "content", response))


def _complete_structured(system: str, user: str, schema, completer: Completer):
    """Call the model, parse to ``schema``, with one repair retry."""
    full_prompt = f"{system}\n\n{user}"
    raw_text = completer(full_prompt)
    parsed = safe_parse(raw_text, schema)
    if parsed is not None:
        return parsed

    # Repair retry: ask the model to fix its own JSON.
    log.info("First parse failed; attempting JSON repair pass")
    repair_prompt = prompts.REPAIR_TEMPLATE.format(bad=raw_text[:6000])
    repaired = completer(repair_prompt)
    parsed = safe_parse(repaired, schema)
    if parsed is None:
        raise ExtractionError(
            f"Model did not return valid {schema.__name__} JSON after repair."
        )
    return parsed


# ---------------------------------------------------------------------------
# Candidate
# ---------------------------------------------------------------------------
def enrich_candidate(
    raw: RawCandidate, normalizer: Optional[SkillNormalizer] = None
) -> CandidateProfile:
    """Pure: normalise raw skills onto the taxonomy and de-duplicate."""
    norm = normalizer or get_normalizer()
    by_key: dict[str, SkillEvidence] = {}

    for rs in raw.skills:
        if not rs.name or not rs.name.strip():
            continue
        result = norm.normalize(rs.name)
        evidence = SkillEvidence(
            name=rs.name.strip(),
            canonical_id=result.canonical_id,
            canonical_name=result.canonical_name,
            category=result.category,
            evidence=rs.evidence,
            proficiency=rs.proficiency,
            years_experience=rs.years_experience,
            confidence=rs.confidence,
            match_method=result.method,
            match_score=result.score,
        )
        # Dedup key: canonical id if matched, else normalized surface form.
        key = result.canonical_id or f"raw:{rs.name.strip().lower()}"
        existing = by_key.get(key)
        if existing is None or _skill_rank(evidence) > _skill_rank(existing):
            by_key[key] = evidence

    return CandidateProfile(
        name=raw.name or "Unknown",
        headline=raw.headline,
        summary=raw.summary,
        total_years_experience=raw.total_years_experience,
        skills=list(by_key.values()),
        education=raw.education,
        experience=[
            ExperienceItem(
                title=e.title, company=e.company, duration=e.duration, highlights=e.highlights
            )
            for e in raw.experience
        ],
        certifications=raw.certifications,
    )


def _skill_rank(s: SkillEvidence) -> tuple[float, float]:
    return (s.match_score, s.confidence)


def extract_candidate_profile(
    cv_text: str, completer: Optional[Completer] = None
) -> CandidateProfile:
    use_cache = completer is None
    if use_cache:
        key = _cache_key("candidate", cv_text)
        cached = _cache_get(_CANDIDATE_CACHE, key)
        if cached is not None:
            log.info("Candidate extraction cache hit")
            return cached
    user = prompts.CANDIDATE_TEMPLATE.format(cv=cv_text)
    raw = _complete_structured(
        prompts.CANDIDATE_SYSTEM, user, RawCandidate, completer or _default_completer
    )
    profile = enrich_candidate(raw)
    if use_cache:
        _cache_put(_CANDIDATE_CACHE, key, profile)
    return profile


# ---------------------------------------------------------------------------
# Job
# ---------------------------------------------------------------------------
def enrich_job(raw: RawJob, normalizer: Optional[SkillNormalizer] = None) -> JobProfile:
    """Pure: normalise requirements and assign importance weights."""
    norm = normalizer or get_normalizer()
    by_key: dict[str, JobRequirement] = {}

    for rq in raw.required_skills:
        if not rq.name or not rq.name.strip():
            continue
        result = norm.normalize(rq.name)
        # Normalise "at least one of" alternatives to canonical IDs.
        alt_ids: list[str] = []
        for alt in rq.alternatives:
            alt_res = norm.normalize(alt)
            if alt_res.canonical_id and alt_res.canonical_id != result.canonical_id:
                alt_ids.append(alt_res.canonical_id)
        req = JobRequirement(
            name=rq.name.strip(),
            canonical_id=result.canonical_id,
            canonical_name=result.canonical_name,
            category=result.category,
            importance=rq.importance,
            weight=IMPORTANCE_WEIGHT.get(rq.importance, 1.0),
            min_years=rq.min_years,
            match_method=result.method,
            match_score=result.score,
            alternatives=list(dict.fromkeys(alt_ids)),
        )
        key = result.canonical_id or f"raw:{rq.name.strip().lower()}"
        existing = by_key.get(key)
        # Keep the stronger importance (higher weight) on collision.
        if existing is None or req.weight > existing.weight:
            by_key[key] = req

    return JobProfile(
        title=raw.title or "Untitled role",
        company=raw.company,
        seniority=raw.seniority,
        summary=raw.summary,
        requirements=list(by_key.values()),
        responsibilities=raw.responsibilities,
    )


# Words too generic to confirm a skill is genuinely required (a hallucinated
# "iOS Development" must not be kept just because "development" is in the text).
_STOPWORDS = {
    "a", "an", "the", "or", "and", "of", "with", "in", "to", "for", "on", "your",
    "our", "you", "we", "is", "are", "as", "at", "by", "be", "this", "that",
    "etc", "similar", "ideally", "related", "using", "use", "plus", "via", "any",
}
_GENERIC_TOKENS = {
    "development", "developer", "management", "engineering", "engineer",
    "analysis", "analytics", "design", "systems", "system", "data", "software",
    "application", "applications", "experience", "skills", "skill", "proficiency",
    "working", "professional", "knowledge", "ability", "field", "tools", "tool",
    "platform", "platforms", "framework", "frameworks", "modern", "strong",
    "good", "excellent", "years", "year", "key", "performance", "indicators",
    "level", "high", "various", "understanding", "practices", "best",
    "environment", "team", "teams", "small",
}


def _form_in_source(form: str, source_norm: str) -> bool:
    """True if a surface form appears as a whole token in the normalized text.
    Tolerant of trailing punctuation and tech tokens like c++, c#, node.js."""
    fn = normalize_text(form)
    if not fn:
        return False
    pattern = r"(?<![a-z0-9])" + re.escape(fn) + r"(?![a-z0-9])"
    return re.search(pattern, source_norm) is not None


def _content_tokens(name: str) -> list[str]:
    """Specific (non-generic) tokens from a requirement name used as fallback
    grounding evidence — recovers verbose names like 'n8n, Make, Zapier, or
    similar' via 'n8n' while ignoring filler like 'or'/'similar'."""
    tokens = normalize_text(name).split()
    return [
        t for t in tokens
        if len(t) >= 2 and t not in _STOPWORDS and t not in _GENERIC_TOKENS
    ]


def _ground_job_requirements(job: JobProfile, source_text: str) -> JobProfile:
    """Drop requirements whose skill term is absent from the posting text.

    Deterministic anti-hallucination guard: a phantom REQUIRED skill the model
    invented would otherwise unfairly penalise every candidate. A requirement is
    kept if (a) its raw name or any canonical surface form appears in the text,
    or (b) any specific (non-generic) token of its name appears — which recovers
    verbosely-named-but-real requirements while still dropping inventions.
    """
    source_norm = normalize_text(source_text)
    taxonomy = get_taxonomy()
    kept = []
    for req in job.requirements:
        forms = [req.name]
        if req.canonical_id:
            skill = taxonomy.get(req.canonical_id)
            if skill:
                forms.extend(skill.all_surface_forms())
        grounded = any(_form_in_source(f, source_norm) for f in forms)
        if not grounded:
            grounded = any(
                _form_in_source(tok, source_norm) for tok in _content_tokens(req.name)
            )
        if grounded:
            kept.append(req)
        else:
            log.info(
                "Dropping ungrounded job requirement (likely hallucination): %s",
                req.display_name,
            )
    job.requirements = kept
    return job


def extract_job_profile(
    job_text: str, completer: Optional[Completer] = None
) -> JobProfile:
    use_cache = completer is None
    if use_cache:
        key = _cache_key("job", job_text)
        cached = _cache_get(_JOB_CACHE, key)
        if cached is not None:
            log.info("Job extraction cache hit")
            return cached
    user = prompts.JOB_TEMPLATE.format(job=job_text)
    raw = _complete_structured(
        prompts.JOB_SYSTEM, user, RawJob, completer or _default_completer
    )
    profile = _ground_job_requirements(enrich_job(raw), job_text)
    if use_cache:
        _cache_put(_JOB_CACHE, key, profile)
    return profile
