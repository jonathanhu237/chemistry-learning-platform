from __future__ import annotations

import hashlib
import sys
from collections.abc import Callable
from types import SimpleNamespace
from typing import Any

import pytest
from pydantic import ValidationError

from server.app.domains.platform import settings as platform_settings
from server.app.domains.platform.settings import (
    AIConfigurationUpdate,
    TextbookEmbeddingProviderUpdate,
    TextbookOCRProviderUpdate,
    TextbookRAGConfigurationUpdate,
    TextbookRerankProviderUpdate,
    effective_ai_settings,
    effective_textbook_rag_settings,
    save_ai_configuration,
)
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


def test_textbook_provider_configuration_round_trips_and_redacts_secrets(monkeypatch) -> None:
    _reset_memory(monkeypatch)
    _install_fake_openai(monkeypatch, [])
    first = AIConfigurationUpdate(
        provider="openai_compatible",
        base_url="https://chat.example.test/v1",
        model="chat-model",
        api_key="chat-secret",
        textbook_rag=TextbookRAGConfigurationUpdate(
            enabled=True,
            elasticsearch_url="http://elasticsearch.test:9200",
            index_name="textbook-bge-v1",
            ocr=TextbookOCRProviderUpdate(
                enabled=True,
                provider="campus_mineru",
                protocol="openai_chat_completions",
                endpoint="https://ocr.example.test/v1/chat/completions",
                model="mineru-alias",
                api_key="ocr-secret",
                timeout_seconds=120,
                concurrency=3,
                max_retries=4,
                max_output_tokens=8192,
                render_dpi=180,
            ),
            embedding=TextbookEmbeddingProviderUpdate(
                provider="campus_bge",
                protocol="openai_embeddings",
                endpoint="https://embedding.example.test/v1/embeddings",
                model="bge-m3",
                api_key="embedding-secret",
                send_dimensions=False,
                batch_size=32,
            ),
            rerank=TextbookRerankProviderUpdate(
                provider="campus_bge",
                protocol="tei",
                endpoint="https://rerank.example.test/rerank",
                model="bge-reranker-v2-m3",
                api_key="rerank-secret",
            ),
            embedding_dimension=1024,
        ),
    )

    response = save_ai_configuration(first)
    effective = effective_textbook_rag_settings()
    serialized = response.model_dump(mode="json")

    assert response.provider == "openai_compatible"
    assert response.textbook_rag is not None
    assert response.textbook_rag.ocr.provider == "campus_mineru"
    assert response.textbook_rag.ocr.api_key_configured is True
    assert response.textbook_rag.ocr.max_output_tokens == 8192
    assert response.textbook_rag.embedding.protocol == "openai_embeddings"
    assert response.textbook_rag.embedding.send_dimensions is False
    assert response.textbook_rag.embedding.batch_size == 32
    assert response.textbook_rag.rerank.protocol == "tei"
    assert response.textbook_rag.ocr.api_key_fingerprint == hashlib.sha256(
        b"ocr-secret"
    ).hexdigest()[:16]
    assert response.textbook_rag.embedding.api_key_fingerprint == hashlib.sha256(
        b"embedding-secret"
    ).hexdigest()[:16]
    assert response.textbook_rag.rerank.api_key_fingerprint == hashlib.sha256(
        b"rerank-secret"
    ).hexdigest()[:16]
    assert "ocr-secret" not in str(serialized)
    assert "embedding-secret" not in str(serialized)
    assert "rerank-secret" not in str(serialized)
    assert effective["ocr"]["api_key"] == "ocr-secret"
    assert effective["ocr"]["max_output_tokens"] == 8192
    assert effective["embedding"]["api_key"] == "embedding-secret"
    assert effective["embedding"]["batch_size"] == 32
    assert effective["rerank"]["api_key"] == "rerank-secret"


def test_textbook_endpoint_can_be_cleared_without_erasing_secret(monkeypatch) -> None:
    _reset_memory(monkeypatch)
    _install_fake_openai(monkeypatch, [])
    base_payload = _payload().model_copy(
        update={
            "textbook_rag": TextbookRAGConfigurationUpdate(
                embedding=TextbookEmbeddingProviderUpdate(
                    endpoint="https://embedding.example.test/v1/embeddings",
                    model="bge-m3",
                    api_key="embedding-secret",
                )
            )
        }
    )
    save_ai_configuration(base_payload)

    cleared = save_ai_configuration(
        base_payload.model_copy(
            update={
                "textbook_rag": TextbookRAGConfigurationUpdate(
                    embedding=TextbookEmbeddingProviderUpdate(
                        endpoint="",
                        base_url="https://embedding.example.test/v1",
                        model="bge-m3",
                        api_key=None,
                    )
                )
            }
        )
    )
    effective = effective_textbook_rag_settings()

    assert cleared.textbook_rag is not None
    assert cleared.textbook_rag.embedding.endpoint == ""
    assert cleared.textbook_rag.embedding.base_url == "https://embedding.example.test/v1"
    assert cleared.textbook_rag.embedding.api_key_configured is True
    assert effective["embedding"]["api_key"] == "embedding-secret"


def test_legacy_partial_role_update_preserves_new_provider_fields(monkeypatch) -> None:
    _reset_memory(monkeypatch)
    _install_fake_openai(monkeypatch, [])
    save_ai_configuration(
        _payload().model_copy(
            update={
                "textbook_rag": TextbookRAGConfigurationUpdate(
                    ocr=TextbookOCRProviderUpdate(
                        enabled=True,
                        provider="campus_mineru",
                        protocol="openai_chat_completions",
                        base_url="https://ocr.example.test/v1",
                        model="mineru",
                        api_key="ocr-secret",
                        max_output_tokens=12288,
                    ),
                    embedding=TextbookEmbeddingProviderUpdate(
                        provider="campus_bge",
                        protocol="openai_embeddings",
                        base_url="https://embedding.example.test/v1",
                        endpoint="/custom/embeddings",
                        model="bge-m3",
                        api_key="embedding-secret",
                        send_dimensions=False,
                        batch_size=48,
                    )
                )
            }
        )
    )

    partial = AIConfigurationUpdate(
        provider="openai",
        base_url="https://gateway.example.test/v1",
        model="test-model",
        textbook_rag={
            "ocr": {
                "base_url": "https://new-ocr.example.test/v1",
                "model": "mineru",
                "api_key": None,
            },
            "embedding": {
                "base_url": "https://new-embedding.example.test/v1",
                "model": "bge-m3",
                "api_key": None,
            }
        },
    )
    save_ai_configuration(partial)
    effective = effective_textbook_rag_settings()
    ocr = effective["ocr"]
    embedding = effective["embedding"]

    assert ocr["provider"] == "campus_mineru"
    assert ocr["max_output_tokens"] == 12288
    assert ocr["base_url"] == "https://new-ocr.example.test/v1"
    assert ocr["api_key"] == "ocr-secret"
    assert embedding["provider"] == "campus_bge"
    assert embedding["protocol"] == "openai_embeddings"
    assert embedding["endpoint"] == "/custom/embeddings"
    assert embedding["base_url"] == "https://new-embedding.example.test/v1"
    assert embedding["send_dimensions"] is False
    assert embedding["batch_size"] == 48
    assert embedding["api_key"] == "embedding-secret"


def test_legacy_stored_textbook_roles_gain_compatible_defaults_without_secret_leak(monkeypatch) -> None:
    _reset_memory(monkeypatch)
    platform_settings._memory_settings[platform_settings.AI_CONFIGURATION_KEY] = {
        "textbook_rag": {
            "enabled": False,
            "index_name": "canonical-rag-chunks-qwen-v1",
            "embedding": {
                "provider": "openai",
                "base_url": "https://legacy-embedding.example.test/v1",
                "model": "legacy-embedding",
                "api_key": "legacy-embedding-secret",
            },
            "rerank": {
                "provider": "openai",
                "base_url": "https://legacy-rerank.example.test/v1",
                "model": "legacy-rerank",
                "api_key": "legacy-rerank-secret",
            },
        }
    }

    effective = effective_textbook_rag_settings()
    response = platform_settings.get_ai_configuration_response(auto_check=False)
    serialized = response.model_dump(mode="json")

    assert effective["embedding"]["protocol"] == "openai_embeddings"
    assert effective["embedding"]["endpoint"] == ""
    assert effective["embedding"]["api_key"] == "legacy-embedding-secret"
    assert effective["rerank"]["protocol"] == "auto"
    assert effective["rerank"]["endpoint"] == ""
    assert "legacy-embedding-secret" not in str(serialized)
    assert "legacy-rerank-secret" not in str(serialized)


def test_textbook_rag_does_not_fall_back_to_retired_video_search_url(monkeypatch) -> None:
    platform_settings._memory_settings.clear()
    base = Settings(data_backend="json", textbook_rag_elasticsearch_url="")
    object.__setattr__(base, "video_library_search_url", "http://retired-video-search:9200")
    monkeypatch.setattr(platform_settings, "get_settings", lambda: base)

    effective = effective_textbook_rag_settings()

    assert effective["elasticsearch_url"] == ""


@pytest.mark.parametrize(
    "provider_update",
    [
        lambda: TextbookOCRProviderUpdate(max_output_tokens=0),
        lambda: TextbookOCRProviderUpdate(max_output_tokens=32769),
        lambda: TextbookEmbeddingProviderUpdate(batch_size=0),
        lambda: TextbookEmbeddingProviderUpdate(batch_size=257),
    ],
)
def test_textbook_processing_provider_limits_are_validated(
    provider_update: Callable[[], object],
) -> None:
    with pytest.raises(ValidationError):
        provider_update()
