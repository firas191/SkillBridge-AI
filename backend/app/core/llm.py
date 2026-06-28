"""Provider-agnostic LLM and embeddings access.

The whole application talks to the model through this module only. Two
providers are supported behind one interface:

* ``nvidia``            -> NVIDIA NIM (build.nvidia.com) via ``ChatNVIDIA``.
* ``openai_compatible`` -> any OpenAI-compatible endpoint via ``ChatOpenAI``
                           (local Ollama, vLLM, OpenAI, Together, ...).

Switching providers is a one-line change in ``.env`` — no code changes. This
means you can develop on NVIDIA's free credits and, when they run out, point
``LLM_PROVIDER=openai_compatible`` at a local Ollama running Llama 3.1 for
free, unlimited inference.

Provider SDKs are imported lazily so the rest of the codebase (and the test
suite) can be imported and run without them installed.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Optional, Type, TypeVar

from pydantic import BaseModel, ValidationError

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

log = get_logger(__name__)

TModel = TypeVar("TModel", bound=BaseModel)


class LLMNotConfiguredError(RuntimeError):
    """Raised when the selected provider is missing required credentials."""


class LLMCallError(RuntimeError):
    """Raised when a model call fails or times out at the provider."""


# ----------------------------------------------------------------------------
# Chat model factory
# ----------------------------------------------------------------------------
@lru_cache
def get_chat_model(temperature: Optional[float] = None):
    """Return a configured LangChain chat model for the active provider.

    Cached per (temperature) so repeated calls reuse one client.
    """
    settings = get_settings()
    temp = settings.llm_temperature if temperature is None else temperature

    if settings.llm_provider == "nvidia":
        if not settings.nvidia_api_key:
            raise LLMNotConfiguredError(
                "LLM_PROVIDER=nvidia but NVIDIA_API_KEY is not set. "
                "Get a free key at https://build.nvidia.com."
            )
        from langchain_nvidia_ai_endpoints import ChatNVIDIA

        log.info("Using NVIDIA NIM chat model: %s", settings.nvidia_chat_model)
        return ChatNVIDIA(
            model=settings.nvidia_chat_model,
            api_key=settings.nvidia_api_key,
            temperature=temp,
            max_tokens=settings.llm_max_tokens,
        )

    # openai_compatible
    from langchain_openai import ChatOpenAI

    log.info(
        "Using OpenAI-compatible chat model: %s @ %s",
        settings.openai_chat_model,
        settings.openai_base_url,
    )
    kwargs = dict(
        model=settings.openai_chat_model,
        base_url=settings.openai_base_url,
        api_key=settings.openai_api_key or "not-needed",
        temperature=temp,
        max_tokens=settings.llm_max_tokens,
        timeout=settings.llm_request_timeout,
        max_retries=settings.llm_max_retries,
    )
    # Gemini 2.5 models "think" by default, which can consume the entire output
    # budget and return empty content for structured tasks. Disable thinking via
    # the documented OpenAI-compat field so the answer (our JSON) lands in
    # `content`. Passed as the explicit `extra_body` param (not model_kwargs).
    if "gemini" in settings.openai_chat_model.lower():
        kwargs["extra_body"] = {"reasoning_effort": "none"}
    return ChatOpenAI(**kwargs)


# ----------------------------------------------------------------------------
# Embeddings factory (optional — system works without it)
# ----------------------------------------------------------------------------
@lru_cache
def get_embeddings():
    """Return an embeddings client, or ``None`` if not configured.

    When ``None``, the skill normalizer falls back to a fast lexical matcher,
    so semantic embeddings are a pure upgrade, never a requirement.
    """
    settings = get_settings()
    if not settings.embeddings_enabled:
        return None

    if settings.llm_provider == "nvidia":
        from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings

        return NVIDIAEmbeddings(
            model=settings.nvidia_embed_model,
            api_key=settings.nvidia_api_key,
        )

    from langchain_openai import OpenAIEmbeddings

    return OpenAIEmbeddings(
        model=settings.openai_embed_model,
        base_url=settings.openai_base_url,
        api_key=settings.openai_api_key or "not-needed",
    )


# ----------------------------------------------------------------------------
# Robust structured-output parsing
# ----------------------------------------------------------------------------
_JSON_BLOCK_RE = re.compile(r"\{.*\}", re.DOTALL)


def extract_json(text: str) -> str:
    """Pull the most likely JSON object out of a model response.

    Handles ```json fences, leading prose, and trailing commentary that
    smaller open models sometimes emit around the JSON payload.
    """
    if not text:
        raise ValueError("Empty model response")
    cleaned = text.strip()
    # Strip code fences.
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned).strip()
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3].strip()
    # If it is already a bare object, return as-is.
    if cleaned.startswith("{") and cleaned.endswith("}"):
        return cleaned
    match = _JSON_BLOCK_RE.search(cleaned)
    if match:
        return match.group(0)
    raise ValueError("No JSON object found in model response")


def parse_model_json(text: str, schema: Type[TModel]) -> TModel:
    """Parse and validate a model response into a Pydantic model.

    Raises ``ValidationError``/``ValueError`` if the payload cannot be coerced;
    callers decide whether to repair-retry.
    """
    payload = extract_json(text)
    data = json.loads(payload)
    return schema.model_validate(data)


def safe_parse(text: str, schema: Type[TModel]) -> Optional[TModel]:
    """Best-effort parse that returns ``None`` instead of raising."""
    try:
        return parse_model_json(text, schema)
    except (ValueError, ValidationError, json.JSONDecodeError) as exc:
        log.warning("Structured parse failed: %s", exc)
        return None


def provider_info(settings: Settings | None = None) -> dict:
    """Lightweight, non-calling description of the active provider."""
    s = settings or get_settings()
    return {
        "provider": s.llm_provider,
        "chat_model": s.active_chat_model,
        "embeddings_enabled": s.embeddings_enabled,
        "configured": (
            bool(s.nvidia_api_key)
            if s.llm_provider == "nvidia"
            else bool(s.openai_base_url)
        ),
    }
