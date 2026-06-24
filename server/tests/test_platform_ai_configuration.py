from __future__ import annotations

import sys
from types import SimpleNamespace
from typing import Any

from server.app.domains.platform import settings as platform_settings
from server.app.domains.platform.settings import AIConfigurationUpdate, effective_ai_settings, save_ai_configuration
from server.app.infrastructure.settings import Settings


class _FakeStream:
    def __init__(self, events: list[Any]) -> None:
        self._events = events

    def __enter__(self):
        return iter(self._events)

    def __exit__(self, *_args: Any) -> bool:
        return False


class _FakeResponses:
    def __init__(self, events: list[Any] | Exception) -> None:
        self._events = events

    def stream(self, **_kwargs: Any):
        if isinstance(self._events, Exception):
            raise self._events
        return _FakeStream(self._events)


class _FakeChatCompletions:
    def create(self, **_kwargs: Any) -> Any:
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="OK"))])


class _FakeChat:
    completions = _FakeChatCompletions()


class _FakeOpenAIClient:
    chat = _FakeChat()

    def __init__(self, *, events: list[Any] | Exception) -> None:
        self.responses = _FakeResponses(events)


def _install_fake_openai(monkeypatch, events: list[Any] | Exception) -> None:
    monkeypatch.setitem(
        sys.modules,
        "openai",
        SimpleNamespace(OpenAI=lambda **_kwargs: _FakeOpenAIClient(events=events)),
    )


def _reset_memory(monkeypatch) -> None:
    platform_settings._memory_settings.clear()
    monkeypatch.setattr(
        platform_settings,
        "get_settings",
        lambda: Settings(data_backend="json", agent_llm_provider="disabled"),
    )


def _payload() -> AIConfigurationUpdate:
    return AIConfigurationUpdate(
        provider="openai",
        base_url="https://gateway.example.test/v1",
        model="test-model",
        api_key="test-key",
    )


def test_save_ai_configuration_detects_reasoning_summary_and_enables_runtime(monkeypatch) -> None:
    _reset_memory(monkeypatch)
    _install_fake_openai(
        monkeypatch,
        [SimpleNamespace(type="response.reasoning_summary_text.delta", delta="Planning answer")],
    )

    response = save_ai_configuration(_payload(), user_id=None)
    runtime = effective_ai_settings(Settings(data_backend="json", agent_llm_provider="disabled"))

    assert response.status.connectivity_status == "connected"
    assert response.reasoning_summary.enabled is True
    assert response.reasoning_summary.status == "supported"
    assert response.reasoning_summary.source == "reasoning_summary"
    assert runtime.agent_llm_provider == "openai"
    assert runtime.agent_llm_model == "test-model"
    assert runtime.agent_reasoning_summary_enabled is True
    assert runtime.agent_reasoning_summary_mode == "compatible"


def test_save_ai_configuration_disables_summary_when_provider_does_not_emit_events(monkeypatch) -> None:
    _reset_memory(monkeypatch)
    _install_fake_openai(monkeypatch, [SimpleNamespace(type="response.output_text.delta", delta="OK")])

    response = save_ai_configuration(_payload(), user_id=None)
    runtime = effective_ai_settings(Settings(data_backend="json", agent_llm_provider="disabled"))

    assert response.status.connectivity_status == "connected"
    assert response.reasoning_summary.enabled is False
    assert response.reasoning_summary.status == "unsupported"
    assert response.reasoning_summary.source == "agent_trace"
    assert runtime.agent_reasoning_summary_enabled is False
    assert runtime.agent_reasoning_summary_mode == "auto"


def test_save_ai_configuration_keeps_connection_failed_separate_from_summary(monkeypatch) -> None:
    _reset_memory(monkeypatch)

    class _FailingChatCompletions:
        def create(self, **_kwargs: Any) -> Any:
            raise RuntimeError("chat unavailable")

    class _FailingChat:
        completions = _FailingChatCompletions()

    class _FailingClient:
        chat = _FailingChat()
        responses = _FakeResponses([])

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=lambda **_kwargs: _FailingClient()))

    response = save_ai_configuration(_payload(), user_id=None)

    assert response.status.connectivity_status == "failed"
    assert response.reasoning_summary.enabled is False
    assert response.reasoning_summary.status == "failed"
    assert response.reasoning_summary.source == "agent_trace"
