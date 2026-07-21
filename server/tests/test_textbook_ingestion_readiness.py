from __future__ import annotations

import json
from dataclasses import replace
from io import BytesIO

import pytest

from server.app.domains.textbook_ingestion import repository
from server.app.domains.textbook_ingestion import config as config_module
from server.app.domains.textbook_ingestion.config import (
    effective_ingestion_settings,
    ingestion_processing_readiness,
    processing_config_snapshot,
    processing_fingerprint,
)
from server.app.domains.textbook_ingestion.errors import TextbookIngestionError
from server.app.infrastructure.settings import Settings


def _ready_settings(**overrides: object) -> Settings:
    settings = Settings(
        data_backend="postgres",
        textbook_ingestion_enabled=True,
        textbook_rag_elasticsearch_url="http://elasticsearch.test:9200",
        textbook_rag_elasticsearch_index="textbook-chunks-test",
        textbook_rag_embedding_base_url="http://embedding.test/v1",
        textbook_rag_embedding_api_key="embedding-secret-alpha",
        textbook_rag_embedding_model="embedding-model-test",
        textbook_rag_embedding_dimension=1024,
        textbook_ocr_enabled=True,
        textbook_ocr_api_key="ocr-secret-alpha",
    )
    return replace(settings, **overrides)


@pytest.mark.parametrize(
    ("setting_name", "missing_reason"),
    [
        ("textbook_rag_elasticsearch_url", "elasticsearch_url_missing"),
        ("textbook_rag_elasticsearch_index", "elasticsearch_index_missing"),
        ("textbook_rag_embedding_base_url", "embedding_base_url_missing"),
        ("textbook_rag_embedding_model", "embedding_model_missing"),
        ("textbook_rag_embedding_api_key", "embedding_credential_missing"),
    ],
)
def test_upload_is_rejected_before_blob_storage_when_processing_dependency_is_missing(
    monkeypatch: pytest.MonkeyPatch,
    setting_name: str,
    missing_reason: str,
) -> None:
    settings = replace(_ready_settings(), **{setting_name: ""})
    monkeypatch.setattr(repository, "get_settings", lambda: settings)
    monkeypatch.setattr(
        repository,
        "LocalTextbookBlobStore",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("upload storage must not be touched while processing is not ready")
        ),
    )

    with pytest.raises(TextbookIngestionError) as raised:
        repository.create_textbook_upload(
            title="Readiness test textbook",
            filename="readiness.pdf",
            stream=BytesIO(b"not-read-because-the-gate-must-fail"),
            content_type="application/pdf",
            uploaded_by=None,
        )

    assert raised.value.reason == "textbook_ingestion_not_ready"
    assert raised.value.status_code == 503
    assert raised.value.details == {"missing": [missing_reason]}


def test_processing_readiness_accepts_complete_online_ingestion_configuration() -> None:
    readiness = ingestion_processing_readiness(_ready_settings())

    assert readiness == {
        "ready": True,
        "missing": [],
        "elasticsearch": {
            "configured": True,
            "index": "textbook-chunks-test",
        },
        "embedding": {
            "configured": True,
            "model": "embedding-model-test",
            "dimension": 1024,
        },
    }


def test_effective_ingestion_settings_uses_the_runtime_rag_contract(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    base = _ready_settings(
        textbook_rag_elasticsearch_url="http://environment-es.test:9200",
        textbook_rag_elasticsearch_index="environment-index",
        textbook_rag_embedding_model="environment-model",
    )
    monkeypatch.setattr(config_module, "get_settings", lambda: base)
    monkeypatch.setattr(
        config_module,
        "_load_effective_textbook_rag_settings",
        lambda: {
            "enabled": True,
            "elasticsearch_url": "http://runtime-es.test:9200",
            "index_name": "runtime-index",
            "embedding": {
                "base_url": "http://runtime-embedding.test/v1",
                "api_key": "runtime-secret",
                "model": "runtime-model",
            },
            "rerank": {
                "base_url": "http://runtime-rerank.test/v1",
                "api_key": "runtime-rerank-secret",
                "model": "runtime-rerank-model",
            },
            "embedding_dimension": 1536,
            "keyword_top_k": 20,
            "vector_top_k": 30,
            "rerank_top_k": 10,
            "final_top_k": 6,
            "min_rerank_score": 0.2,
            "timeout_seconds": 12.0,
        },
    )

    effective = effective_ingestion_settings()
    snapshot = processing_config_snapshot()

    assert effective.textbook_rag_elasticsearch_url == "http://runtime-es.test:9200"
    assert effective.textbook_rag_elasticsearch_index == "runtime-index"
    assert effective.textbook_rag_embedding_model == "runtime-model"
    assert effective.textbook_rag_embedding_dimension == 1536
    assert snapshot["embedding"]["model"] == "runtime-model"
    assert snapshot["index"]["name"] == "runtime-index"
    assert "runtime-secret" not in json.dumps(snapshot, sort_keys=True)


def test_dependency_outage_blocks_new_uploads_but_not_existing_document_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = replace(
        _ready_settings(),
        textbook_rag_elasticsearch_url="",
        textbook_rag_embedding_api_key="",
    )
    monkeypatch.setattr(repository, "get_settings", lambda: settings)

    # List/detail/job endpoints still need to expose existing facts and recovery
    # actions while an external provider is unavailable.
    repository._require_postgres_feature()
    with pytest.raises(TextbookIngestionError) as raised:
        repository._require_processing_ready()

    assert raised.value.reason == "textbook_ingestion_not_ready"


@pytest.mark.parametrize(
    ("setting_name", "changed_value"),
    [
        ("textbook_rag_elasticsearch_url", "http://other-elasticsearch.test:9200"),
        ("textbook_rag_elasticsearch_index", "textbook-chunks-v2"),
        ("textbook_rag_embedding_base_url", "http://other-embedding.test/v1"),
        ("textbook_rag_embedding_model", "embedding-model-v2"),
        ("textbook_rag_embedding_dimension", 1536),
        ("textbook_rag_embedding_api_key", "embedding-secret-beta"),
        ("textbook_ocr_model", "mineru-v2"),
        ("textbook_ocr_api_key", "ocr-secret-beta"),
        ("textbook_chunk_max_chars", 1600),
    ],
)
def test_processing_fingerprint_changes_with_material_processing_configuration(
    setting_name: str,
    changed_value: object,
) -> None:
    settings = _ready_settings()
    baseline = processing_fingerprint(processing_config_snapshot(settings))
    changed_settings = replace(settings, **{setting_name: changed_value})

    assert processing_fingerprint(processing_config_snapshot(changed_settings)) != baseline


def test_processing_snapshot_exposes_only_secret_state_and_fingerprints() -> None:
    settings = _ready_settings()
    snapshot = processing_config_snapshot(settings)
    serialized = json.dumps(snapshot, sort_keys=True)

    assert "embedding-secret-alpha" not in serialized
    assert "ocr-secret-alpha" not in serialized
    assert snapshot["embedding"]["credential_configured"] is True
    assert snapshot["embedding"]["credential_fingerprint"]
    assert snapshot["ocr"]["credential_configured"] is True
    assert snapshot["ocr"]["credential_fingerprint"]
    assert snapshot == processing_config_snapshot(settings)
    assert processing_fingerprint(snapshot) == processing_fingerprint(
        processing_config_snapshot(settings)
    )
