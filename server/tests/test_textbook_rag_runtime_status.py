from __future__ import annotations

import json
import urllib.error
from typing import Any

from server.app.domains.platform.settings import _textbook_rag_runtime_status


def _base_config(**overrides: Any) -> dict[str, Any]:
    config = {
        "enabled": True,
        "elasticsearch_url": "http://es.local:9200",
        "index_name": "canonical-rag-chunks-qwen-v1",
        "embedding": {
            "base_url": "https://embedding.test/v1",
            "model": "qwen-embedding",
            "api_key": "embedding-key",
        },
        "rerank": {
            "endpoint": "https://rerank.test/v1/rerank",
            "model": "qwen-rerank",
            "api_key": "rerank-key",
        },
        "embedding_dimension": 1024,
        "timeout_seconds": 1.0,
    }
    config.update(overrides)
    return config


class _JsonResponse:
    def __init__(self, payload: dict[str, Any]) -> None:
        self.payload = payload

    def __enter__(self) -> "_JsonResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


def test_textbook_rag_runtime_status_disabled_when_feature_disabled() -> None:
    status = _textbook_rag_runtime_status(_base_config(), rag_enabled=False)

    assert status["enabled"] is False
    assert status["status"] == "disabled"


def test_textbook_rag_runtime_status_requires_elasticsearch_url() -> None:
    status = _textbook_rag_runtime_status(_base_config(elasticsearch_url=""), rag_enabled=True)

    assert status["status"] == "elasticsearch_not_configured"


def test_textbook_rag_runtime_status_requires_embedding_config() -> None:
    status = _textbook_rag_runtime_status(_base_config(embedding={"model": "", "api_key": ""}), rag_enabled=True)

    assert status["status"] == "embedding_not_configured"


def test_textbook_rag_runtime_status_requires_rerank_config() -> None:
    status = _textbook_rag_runtime_status(_base_config(rerank={"model": "", "api_key": ""}), rag_enabled=True)

    assert status["status"] == "rerank_not_configured"


def test_textbook_rag_runtime_status_rejects_unsupported_provider_protocol() -> None:
    embedding = {**_base_config()["embedding"], "protocol": "unsupported"}

    status = _textbook_rag_runtime_status(
        _base_config(embedding=embedding),
        rag_enabled=True,
    )

    assert status["status"] == "embedding_protocol_unsupported"


def test_textbook_rag_runtime_status_reports_missing_index(monkeypatch) -> None:
    def raise_missing(*_args: Any, **_kwargs: Any) -> None:
        raise urllib.error.HTTPError("http://es.local/index", 404, "missing", hdrs=None, fp=None)

    monkeypatch.setattr("server.app.domains.platform.settings.urllib.request.urlopen", raise_missing)

    status = _textbook_rag_runtime_status(_base_config(), rag_enabled=True)

    assert status["status"] == "index_missing"
    assert status["diagnostics"]["index_exists"] is False


def test_textbook_rag_runtime_status_reports_stale_index(monkeypatch) -> None:
    payload = {
        "canonical-rag-chunks-qwen-v1": {
            "mappings": {"_meta": {"embedding_model": "old-model", "embedding_dimension": 1024}}
        }
    }
    monkeypatch.setattr(
        "server.app.domains.platform.settings.urllib.request.urlopen",
        lambda *_args, **_kwargs: _JsonResponse(payload),
    )

    status = _textbook_rag_runtime_status(_base_config(), rag_enabled=True)

    assert status["status"] == "index_stale"


def test_textbook_rag_runtime_status_healthy(monkeypatch) -> None:
    payload = {
        "canonical-rag-chunks-qwen-v1": {
            "mappings": {"_meta": {"embedding_model": "qwen-embedding", "embedding_dimension": 1024}}
        }
    }
    monkeypatch.setattr(
        "server.app.domains.platform.settings.urllib.request.urlopen",
        lambda *_args, **_kwargs: _JsonResponse(payload),
    )

    status = _textbook_rag_runtime_status(_base_config(), rag_enabled=True)

    assert status["status"] == "healthy"
    assert status["diagnostics"]["index_exists"] is True
