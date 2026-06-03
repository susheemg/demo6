"""
Central LLM configuration — the ONE place to wire AI providers.

Reads API keys from environment variables, lazily builds the relevant SDK
client, and exposes a single `complete()` the rest of the app calls. If no key
is set, `is_enabled()` is False and every feature falls back to its tested
deterministic-local path — so the app always runs, with or without AI.

ENVIRONMENT VARIABLES (set these to enable AI):
    BRO_LLM_PROVIDER   "claude" (default) or "openai" — which provider to use
    ANTHROPIC_API_KEY  your Claude API key            (for provider=claude)
    OPENAI_API_KEY     your OpenAI / ChatGPT API key  (for provider=openai)
    BRO_LLM_MODEL      optional model override
                       (default claude-sonnet-4-20250514 / gpt-4o)

Examples:
    export ANTHROPIC_API_KEY=sk-ant-...           # Claude
    export BRO_LLM_PROVIDER=openai
    export OPENAI_API_KEY=sk-...                   # ChatGPT

Nothing here is committed; keys live only in the environment / your secrets store.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from .provider import LLMRequest, Provider
from .adapters import ClaudeAdapter, OpenAIAdapter


def configured_provider() -> Optional[str]:
    """Return the provider to use based on env, or None if no key is set."""
    pref = (os.environ.get("BRO_LLM_PROVIDER") or "").lower().strip()
    has_claude = bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("BRO_LLM_KEY"))
    has_openai = bool(os.environ.get("OPENAI_API_KEY"))

    if pref == "openai" and has_openai:
        return "openai"
    if pref == "claude" and has_claude:
        return "claude"
    # no explicit preference: prefer whichever key is present (Claude first)
    if has_claude:
        return "claude"
    if has_openai:
        return "openai"
    return None


def is_enabled() -> bool:
    """True if any provider key is configured. Features check this to decide
    whether to use AI or their deterministic-local fallback."""
    return configured_provider() is not None


def status() -> dict:
    """Human-readable status for an admin/settings screen — never leaks the key."""
    prov = configured_provider()
    return {
        "enabled": prov is not None,
        "provider": prov,
        "claude_key_present": bool(os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("BRO_LLM_KEY")),
        "openai_key_present": bool(os.environ.get("OPENAI_API_KEY")),
        "model": _model_for(prov) if prov else None,
    }


def _model_for(provider: str) -> str:
    override = os.environ.get("BRO_LLM_MODEL")
    if override:
        return override
    return "claude-sonnet-4-20250514" if provider == "claude" else "gpt-4o"


@lru_cache(maxsize=2)
def _adapter(provider: str):
    """Build (and cache) the adapter + SDK client for a provider. Imported lazily
    so the app runs without the SDKs installed when AI is disabled."""
    model = _model_for(provider)
    if provider == "claude":
        import anthropic  # pip install anthropic
        key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("BRO_LLM_KEY")
        client = anthropic.Anthropic(api_key=key)
        return ClaudeAdapter(client, model=model)
    if provider == "openai":
        import openai  # pip install openai
        client = openai.OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
        return OpenAIAdapter(client, model=model)
    raise ValueError(f"unknown provider: {provider}")


def complete(system_prompt: str, user_content: str,
             domain: str = "general") -> Optional[str]:
    """Single entry point the features call. Returns the model's text, or None
    if AI is disabled or the call fails (caller then uses its local fallback)."""
    provider = configured_provider()
    if provider is None:
        return None
    try:
        adapter = _adapter(provider)
        resp = adapter.complete(LLMRequest(
            system_prompt=system_prompt, user_content=user_content, domain=domain))
        return resp.text
    except Exception:
        return None  # fail safe to deterministic-local
