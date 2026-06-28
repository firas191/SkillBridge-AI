"""Skill normalization.

Maps free-text skills (as extracted from CVs / job posts) to canonical
taxonomy IDs. Strategy, in order of precedence:

1. **Exact** normalized match against names + aliases  (score 100).
2. **Fuzzy** lexical match via RapidFuzz token-set ratio (handles typos,
   ordering, and surface variants like "React JS" vs "ReactJS").
3. **Semantic** match via embeddings *if configured* (catches paraphrases
   like "building user interfaces" ~ "UI Design"). Optional upgrade.

The lexical path is deterministic and needs no network or model download, so
the system is fully functional offline and the test suite is reproducible.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import BaseModel
from rapidfuzz import fuzz, process

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.taxonomy.store import TaxonomyStore, get_taxonomy, normalize_text

log = get_logger(__name__)


class NormalizationResult(BaseModel):
    input: str
    matched: bool
    canonical_id: Optional[str] = None
    canonical_name: Optional[str] = None
    category: Optional[str] = None
    score: float = 0.0
    method: str = "unmatched"  # exact | fuzzy | semantic | unmatched


class SkillNormalizer:
    def __init__(
        self,
        store: TaxonomyStore,
        threshold: int = 82,
        embeddings=None,
    ):
        self.store = store
        self.threshold = threshold
        self._embeddings = embeddings
        self._embed_matrix = None  # lazily built numpy array
        self._embed_ids: List[str] = []

    # ---- public API ----
    def normalize(self, text: str) -> NormalizationResult:
        cleaned = (text or "").strip()
        if not cleaned:
            return NormalizationResult(input=text or "", matched=False)

        # 1) exact
        exact_id = self.store.exact_match(cleaned)
        if exact_id:
            return self._result(cleaned, exact_id, 100.0, "exact")

        # 2) fuzzy
        norm = normalize_text(cleaned)
        if norm and self.store.fuzzy_keys:
            best = process.extractOne(
                norm,
                self.store.fuzzy_keys,
                scorer=fuzz.token_set_ratio,
            )
            if best is not None:
                key, score, _ = best
                if score >= self.threshold:
                    skill_id = self.store.id_for_key(key)
                    if skill_id:
                        return self._result(cleaned, skill_id, float(score), "fuzzy")

        # 3) semantic (optional)
        semantic = self._semantic_match(cleaned)
        if semantic is not None:
            return semantic

        return NormalizationResult(input=cleaned, matched=False, score=0.0)

    def normalize_many(self, texts: List[str]) -> List[NormalizationResult]:
        return [self.normalize(t) for t in texts]

    # ---- helpers ----
    def _result(self, text: str, skill_id: str, score: float, method: str) -> NormalizationResult:
        skill = self.store.get(skill_id)
        return NormalizationResult(
            input=text,
            matched=True,
            canonical_id=skill_id,
            canonical_name=skill.name if skill else skill_id,
            category=skill.category if skill else None,
            score=score,
            method=method,
        )

    def _ensure_embedding_index(self) -> bool:
        if self._embeddings is None:
            return False
        if self._embed_matrix is not None:
            return True
        try:
            import numpy as np

            skills = self.store.all_skills()
            texts = [s.name for s in skills]
            vectors = self._embeddings.embed_documents(texts)
            mat = np.asarray(vectors, dtype="float32")
            norms = np.linalg.norm(mat, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            self._embed_matrix = mat / norms
            self._embed_ids = [s.id for s in skills]
            log.info("Built semantic skill index: %d vectors", len(self._embed_ids))
            return True
        except Exception as exc:  # pragma: no cover - network/optional path
            log.warning("Semantic index unavailable, using lexical only: %s", exc)
            self._embeddings = None
            return False

    def _semantic_match(self, text: str) -> Optional[NormalizationResult]:
        if not self._ensure_embedding_index():
            return None
        try:  # pragma: no cover - exercised only when embeddings configured
            import numpy as np

            q = np.asarray(self._embeddings.embed_query(text), dtype="float32")
            qn = q / (np.linalg.norm(q) or 1.0)
            sims = self._embed_matrix @ qn
            idx = int(sims.argmax())
            score = float(sims[idx]) * 100.0
            # Semantic threshold is stricter (cosine 0.62 ~ score 62).
            if score >= max(self.threshold - 20, 60):
                return self._result(text, self._embed_ids[idx], score, "semantic")
        except Exception as exc:  # pragma: no cover
            log.warning("Semantic match failed: %s", exc)
        return None


@lru_cache
def get_normalizer() -> SkillNormalizer:
    """Cached normalizer built from configuration.

    Embeddings are wired in only when enabled, so the default path stays
    offline-friendly and deterministic.
    """
    settings = get_settings()
    embeddings = None
    if settings.embeddings_enabled:
        try:
            from app.core.llm import get_embeddings

            embeddings = get_embeddings()
        except Exception as exc:  # pragma: no cover
            log.warning("Could not initialise embeddings: %s", exc)
    return SkillNormalizer(
        store=get_taxonomy(),
        threshold=settings.skill_match_threshold,
        embeddings=embeddings,
    )
