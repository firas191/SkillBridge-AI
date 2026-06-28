"""Tests for taxonomy loading and skill normalization."""
from __future__ import annotations

from app.services.taxonomy import get_normalizer, get_taxonomy
from app.services.taxonomy.store import normalize_text


def test_taxonomy_loads():
    store = get_taxonomy()
    assert len(store) > 100
    assert store.get("python") is not None
    assert store.get("python").name == "Python"


def test_normalize_text_preserves_tech_tokens():
    assert normalize_text("C++") == "c++"
    assert normalize_text("C#") == "c#"
    assert normalize_text("Node.JS") == "node.js"
    assert normalize_text("  React   JS ") == "react js"


def test_exact_and_alias_matches():
    n = get_normalizer()
    assert n.normalize("Python").canonical_id == "python"
    assert n.normalize("py").canonical_id == "python"  # alias
    assert n.normalize("JS").canonical_id == "javascript"  # alias
    assert n.normalize("PostgreSQL").canonical_id == "postgresql"


def test_fuzzy_matches_surface_variants():
    n = get_normalizer()
    assert n.normalize("React.js").canonical_id == "react"
    assert n.normalize("react js").canonical_id == "react"
    assert n.normalize("Node js").canonical_id == "node-js"


def test_unknown_skill_is_unmatched():
    n = get_normalizer()
    res = n.normalize("Underwater Basket Weaving")
    assert res.matched is False
    assert res.canonical_id is None


def test_related_skills_lookup():
    store = get_taxonomy()
    # python and fastapi reference each other as related in the seed.
    assert store.are_related("fastapi", "python") is True
    assert store.are_related("python", "kubernetes") is False
