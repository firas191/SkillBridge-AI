"""Learning-resource lookup.

Primary source is a curated catalog of real, verified resources keyed by
canonical skill id (official docs + reputable free courses). For skills not in
the catalog, we synthesise trusted-platform search links (real, working URLs)
so every module always has somewhere to start. The LLM's own resource
suggestions are merged on top in the coach.
"""
from __future__ import annotations

import json
from functools import lru_cache
from urllib.parse import quote_plus

from app.core.config import get_settings
from app.core.logging import get_logger
from app.schemas.learning import LearningResource
from app.services.taxonomy import get_normalizer

log = get_logger(__name__)


@lru_cache
def _catalog() -> dict:
    path = get_settings().resources_file
    if not path.exists():
        log.warning("Learning resource catalog not found at %s", path)
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("resources", {})


def _fallback_links(skill_name: str) -> list[LearningResource]:
    q = quote_plus(skill_name)
    return [
        LearningResource(
            title=f"YouTube — {skill_name} tutorials",
            url=f"https://www.youtube.com/results?search_query={q}+tutorial",
            type="video",
        ),
        LearningResource(
            title=f"Coursera — {skill_name} courses",
            url=f"https://www.coursera.org/search?query={q}",
            type="course",
        ),
        LearningResource(
            title=f"freeCodeCamp — {skill_name}",
            url=f"https://www.freecodecamp.org/news/search?query={q}",
            type="article",
        ),
    ]


def resources_for(
    skill_name: str, canonical_id: str | None = None, limit: int = 3
) -> list[LearningResource]:
    """Return curated resources for a skill, or trusted-platform fallbacks."""
    cid = canonical_id
    if cid is None and skill_name:
        cid = get_normalizer().normalize(skill_name).canonical_id
    entries = _catalog().get(cid, []) if cid else []
    resources = [LearningResource(**e) for e in entries]
    if not resources:
        resources = _fallback_links(skill_name)
    return resources[:limit]
