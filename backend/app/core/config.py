"""Application configuration.

All settings are loaded from environment variables (and an optional `.env`
file). This keeps secrets out of the codebase and lets the same image run in
development and production with different configuration.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# Repository root = two levels up from this file (backend/app/core/config.py).
BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent


class Settings(BaseSettings):
    """Strongly-typed application settings."""

    model_config = SettingsConfigDict(
        env_file=(BACKEND_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Provider selection ----
    llm_provider: Literal["nvidia", "openai_compatible"] = "nvidia"

    # ---- NVIDIA NIM ----
    nvidia_api_key: str = ""
    nvidia_chat_model: str = "meta/llama-3.1-8b-instruct"
    nvidia_embed_model: str = ""

    # ---- OpenAI-compatible (Ollama / vLLM / OpenAI) ----
    openai_base_url: str = "http://localhost:11434/v1"
    openai_api_key: str = "ollama"
    openai_chat_model: str = "llama3.1:8b"
    openai_embed_model: str = ""

    # ---- LLM behaviour ----
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2048
    llm_request_timeout: int = 60
    llm_max_retries: int = 2
    # Hard ceiling (seconds) for a single extraction call before we give up and
    # return a clean error instead of hanging on a slow/queued provider.
    extraction_timeout: int = 150

    # ---- Skill normalization ----
    skill_match_threshold: int = 82
    taxonomy_path: str = "data/taxonomy/skills_seed.json"
    esco_skills_csv: str = ""
    resources_path: str = "data/resources/learning_resources.json"

    # ---- Application ----
    database_url: str = "sqlite:///./skillbridge.db"
    # Stored as a comma-separated string (avoids pydantic-settings JSON parsing
    # of list-typed env vars); use `cors_origin_list` for the parsed value.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    log_level: str = "INFO"
    app_env: str = "development"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # ---- Derived helpers ----
    @property
    def taxonomy_file(self) -> Path:
        """Resolve the taxonomy path against the repo root if relative."""
        p = Path(self.taxonomy_path)
        return p if p.is_absolute() else (REPO_ROOT / p)

    @property
    def resources_file(self) -> Path:
        p = Path(self.resources_path)
        return p if p.is_absolute() else (REPO_ROOT / p)

    @property
    def esco_file(self) -> Path | None:
        if not self.esco_skills_csv:
            return None
        p = Path(self.esco_skills_csv)
        return p if p.is_absolute() else (REPO_ROOT / p)

    @property
    def embeddings_enabled(self) -> bool:
        if self.llm_provider == "nvidia":
            return bool(self.nvidia_embed_model)
        return bool(self.openai_embed_model)

    @property
    def active_chat_model(self) -> str:
        return (
            self.nvidia_chat_model
            if self.llm_provider == "nvidia"
            else self.openai_chat_model
        )


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor (single instance per process)."""
    return Settings()
