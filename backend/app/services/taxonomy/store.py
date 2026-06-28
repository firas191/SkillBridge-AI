"""Skill taxonomy store.

Loads a canonical skill taxonomy (curated seed JSON, optionally merged with a
full ESCO export) and exposes fast lookup structures used by the normalizer.

The taxonomy is the backbone of explainability: every extracted skill is mapped
to a stable canonical ID, so candidate evidence and job requirements are
compared on the *same* vocabulary rather than on raw, noisy strings.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.logging import get_logger

log = get_logger(__name__)

_SEP_RE = re.compile(r"[\s\-_/\\]+")
_PUNCT_RE = re.compile(r"[^\w+#. ]")
_WS_RE = re.compile(r"\s+")


def normalize_text(value: str) -> str:
    """Normalise a skill string for matching.

    Lower-cases, unifies separators to single spaces and drops stray
    punctuation while *preserving* technical tokens like ``c++``, ``c#`` and
    ``node.js``.
    """
    if not value:
        return ""
    s = value.lower().strip()
    s = _SEP_RE.sub(" ", s)
    s = _PUNCT_RE.sub("", s)
    s = _WS_RE.sub(" ", s).strip()
    return s


class CanonicalSkill(BaseModel):
    id: str
    name: str
    category: str = "General"
    aliases: List[str] = Field(default_factory=list)
    related: List[str] = Field(default_factory=list)

    def all_surface_forms(self) -> List[str]:
        return [self.name, *self.aliases]


class TaxonomyStore:
    """In-memory index over canonical skills."""

    def __init__(self, skills: List[CanonicalSkill]):
        self._by_id: Dict[str, CanonicalSkill] = {s.id: s for s in skills}
        # Map of normalized surface form -> canonical id (exact lookup).
        self._exact: Dict[str, str] = {}
        # Parallel arrays for fuzzy search.
        self._keys: List[str] = []
        self._key_to_id: Dict[str, str] = {}

        for skill in skills:
            for form in skill.all_surface_forms():
                norm = normalize_text(form)
                if not norm:
                    continue
                # First writer wins for exact map; keep canonical name priority.
                self._exact.setdefault(norm, skill.id)
                if norm not in self._key_to_id:
                    self._key_to_id[norm] = skill.id
                    self._keys.append(norm)

    # ---- accessors ----
    def __len__(self) -> int:
        return len(self._by_id)

    def get(self, skill_id: str) -> Optional[CanonicalSkill]:
        return self._by_id.get(skill_id)

    def all_skills(self) -> List[CanonicalSkill]:
        return list(self._by_id.values())

    def categories(self) -> List[str]:
        return sorted({s.category for s in self._by_id.values()})

    def exact_match(self, value: str) -> Optional[str]:
        return self._exact.get(normalize_text(value))

    @property
    def fuzzy_keys(self) -> List[str]:
        return self._keys

    def id_for_key(self, key: str) -> Optional[str]:
        return self._key_to_id.get(key)

    def are_related(self, id_a: str, id_b: str) -> bool:
        """True if two canonical skills list each other as related."""
        a = self._by_id.get(id_a)
        b = self._by_id.get(id_b)
        if not a or not b:
            return False
        return id_b in a.related or id_a in b.related


# ----------------------------------------------------------------------------
# Loading
# ----------------------------------------------------------------------------
def _load_seed(path: Path) -> List[CanonicalSkill]:
    if not path.exists():
        raise FileNotFoundError(
            f"Taxonomy seed not found at {path}. Check TAXONOMY_PATH in your .env."
        )
    data = json.loads(path.read_text(encoding="utf-8"))
    skills = [CanonicalSkill.model_validate(item) for item in data.get("skills", [])]
    log.info("Loaded %d canonical skills from %s", len(skills), path.name)
    return skills


def _merge_esco(skills: List[CanonicalSkill], csv_path: Path) -> List[CanonicalSkill]:
    """Merge an ingested ESCO CSV (id,name,category,aliases) into the seed.

    Seed entries take precedence on ID collisions. See scripts/ingest_esco.py
    for how to produce the CSV from the official ESCO download.
    """
    import csv

    existing = {s.id for s in skills}
    added = 0
    with csv_path.open(encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            skill_id = (row.get("id") or "").strip()
            name = (row.get("name") or "").strip()
            if not skill_id or not name or skill_id in existing:
                continue
            aliases = [a.strip() for a in (row.get("aliases") or "").split("|") if a.strip()]
            skills.append(
                CanonicalSkill(
                    id=skill_id,
                    name=name,
                    category=(row.get("category") or "ESCO").strip(),
                    aliases=aliases,
                )
            )
            existing.add(skill_id)
            added += 1
    log.info("Merged %d additional skills from ESCO export %s", added, csv_path.name)
    return skills


@lru_cache
def get_taxonomy() -> TaxonomyStore:
    """Cached taxonomy singleton built from configuration."""
    settings = get_settings()
    skills = _load_seed(settings.taxonomy_file)
    esco = settings.esco_file
    if esco and esco.exists():
        skills = _merge_esco(skills, esco)
    return TaxonomyStore(skills)
