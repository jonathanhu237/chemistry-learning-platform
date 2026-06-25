from __future__ import annotations

import os

from server.app.infrastructure.settings import Settings


def sdk_enabled(settings: Settings) -> bool:
    return (
        settings.agent_llm_provider in {"openai", "openai_compatible"}
        and bool(settings.agent_llm_api_key or os.getenv("OPENAI_API_KEY"))
        and bool(settings.agent_llm_model)
    )


def reasoning_summary_enabled(settings: Settings) -> bool:
    if not sdk_enabled(settings) or not bool(getattr(settings, "agent_reasoning_summary_enabled", False)):
        return False
    mode = str(getattr(settings, "agent_reasoning_summary_mode", "auto") or "auto").lower()
    if mode in {"off", "none", "disabled", "false"}:
        return False
    provider = str(settings.agent_llm_provider or "").lower()
    base_url = str(getattr(settings, "agent_llm_base_url", "") or "").strip()
    if provider == "openai" and not base_url:
        return True
    return mode in {"force", "forced", "responses", "compatible"}


def reasoning_summary_mode(settings: Settings) -> str:
    mode = str(getattr(settings, "agent_reasoning_summary_mode", "auto") or "auto").lower()
    return mode if mode in {"auto", "concise", "detailed"} else "auto"


def reasoning_effort(settings: Settings) -> str:
    effort = str(getattr(settings, "agent_reasoning_effort", "low") or "low").lower()
    return effort if effort in {"minimal", "low", "medium", "high"} else "low"


def async_openai_client(settings: Settings, *, timeout: float):
    from openai import AsyncOpenAI

    return AsyncOpenAI(
        api_key=settings.agent_llm_api_key or os.getenv("OPENAI_API_KEY"),
        base_url=settings.agent_llm_base_url or None,
        timeout=timeout,
    )
