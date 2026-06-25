from __future__ import annotations

import inspect
import re
from pathlib import Path

from server.app.domains.assistant import orchestrator as agent_module


ASSISTANT_DOMAIN = Path(__file__).resolve().parents[1] / "app" / "domains" / "assistant"


DISALLOWED_PATTERNS = [
    (
        "sync OpenAI import",
        re.compile(r"from\s+openai\s+import\s+OpenAI\b"),
    ),
    (
        "sync OpenAI constructor",
        re.compile(r"(?<!Async)\bOpenAI\s*\("),
    ),
    (
        "sync stream iteration",
        re.compile(r"(?m)^[ \t]*for\s+chunk\s+in\s+stream\s*:"),
    ),
]


def test_assistant_domain_uses_async_openai_runtime_only() -> None:
    failures: list[str] = []
    for path in sorted(ASSISTANT_DOMAIN.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        for label, pattern in DISALLOWED_PATTERNS:
            for match in pattern.finditer(source):
                line_number = source.count("\n", 0, match.start()) + 1
                failures.append(f"{path.relative_to(ASSISTANT_DOMAIN)}:{line_number}: disallowed {label}")

    assert not failures, "Assistant runtime must not use blocking OpenAI calls:\n" + "\n".join(failures)


def test_run_agent_stream_routes_only_to_async_provider_helpers() -> None:
    source = inspect.getsource(agent_module.run_agent_stream)

    assert "_run_openai_responses_stream" in source
    assert "_run_openai_chat_completion_stream" in source
    assert "_legacy_run_openai_chat_completion" not in source
    assert "_legacy_run_openai_chat_completion_stream_always_rag" not in source
    assert "for chunk in stream" not in source


def test_removed_legacy_sync_helpers_are_not_importable() -> None:
    assert not hasattr(agent_module, "_legacy_run_openai_chat_completion_always_rag")
    assert not hasattr(agent_module, "_legacy_openai_answer_context_payload_always_rag")
    assert not hasattr(agent_module, "_legacy_run_openai_chat_completion_stream_always_rag")
    assert not hasattr(agent_module, "_legacy_run_local_agent_always_rag")
    assert not hasattr(agent_module, "_openai_client")
