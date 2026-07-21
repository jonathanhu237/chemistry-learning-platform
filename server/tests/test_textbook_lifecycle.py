from __future__ import annotations

from typing import Any

import pytest

from server.app.domains.textbook_ingestion import lifecycle
from server.app.domains.textbook_ingestion.lifecycle import publication_blockers
from server.app.domains.textbook_ingestion.views import public_document
from server.app.domains.textbook_rag.clients import embedding_profile_fingerprint
from server.app.infrastructure.settings import Settings


EMBEDDING_PROFILE = embedding_profile_fingerprint(
    provider="openai_compatible",
    protocol="openai_embeddings",
    base_url="",
    endpoint="",
    model="embedding-v1",
    dimensions=3,
    send_dimensions=True,
)


def _online_document(status: str = "review_ready") -> dict[str, object]:
    return {
        "id": "tbk_1",
        "document_kind": "textbook",
        "publication_status": status,
        "active_projection_run_id": "run-1",
    }


def _verified_job(status: str = "review_ready") -> dict[str, object]:
    return {
        "id": "job-1",
        "status": status,
        "total_chunks": 2,
        "embedded_chunks": 2,
        "indexed_chunks": 2,
        "quality_report": {"publishable": True, "blocking_issues": []},
        "outputs": {
            "index_verified": True,
            "indexed_chunks": 2,
            "projection_run_id": "run-1",
        },
    }


def test_publication_gate_requires_quality_embedding_and_index_count_consistency() -> None:
    assert publication_blockers(_online_document(), _verified_job(), chunk_count=2) == []

    job = _verified_job()
    job["quality_report"] = {"publishable": False, "blocking_issues": ["empty_pages"]}
    job["indexed_chunks"] = 1
    job["outputs"] = {"index_verified": False, "indexed_chunks": 1}

    blockers = publication_blockers(_online_document(), job, chunk_count=2)

    assert "empty_pages" in blockers
    assert "quality_not_publishable" in blockers
    assert "index_not_verified" in blockers
    assert "index_count_mismatch" in blockers


def test_inactive_verified_online_version_and_seed_are_rollback_candidates() -> None:
    assert publication_blockers(
        _online_document("inactive"),
        _verified_job("ready"),
        chunk_count=2,
    ) == []
    assert publication_blockers(
        {"document_kind": "canonical_textbook", "publication_status": "inactive"},
        None,
        chunk_count=10,
    ) == []


def test_public_document_only_advertises_safe_lifecycle_actions() -> None:
    review_ready = public_document(
        {
            **_online_document(),
            "logical_textbook_key": "chemistry",
            "version_number": 2,
            "title": "Chemistry",
            "file_name": "chemistry.pdf",
            "latest_job": _verified_job(),
        }
    )
    assert review_ready["can_publish"] is True
    assert "publish" in review_ready["allowed_actions"]
    assert "delete" in review_ready["allowed_actions"]

    processing = public_document(
        {
            **_online_document("processing"),
            "logical_textbook_key": "chemistry",
            "version_number": 2,
            "title": "Chemistry",
            "file_name": "chemistry.pdf",
            "latest_job": {**_verified_job("embedding"), "allowed_actions": ["cancel"]},
        }
    )
    assert "cancel" in processing["allowed_actions"]
    assert "delete" not in processing["allowed_actions"]

    rollback = public_document(
        {
            "id": "canonical-1",
            "document_kind": "canonical_textbook",
            "publication_status": "inactive",
            "logical_textbook_key": "chemistry",
            "version_number": 1,
            "title": "Chemistry seed",
            "file_name": "seed.jsonl",
            "latest_job": None,
        }
    )
    assert {"publish", "rollback"}.issubset(rollback["allowed_actions"])
    assert "delete" not in rollback["allowed_actions"]


class _FakeElasticsearch:
    index = "shared-textbooks"

    def __init__(self, *, document_count: int = 2, contract_count: int = 2) -> None:
        self.document_count = document_count
        self.contract_count = contract_count
        self.requests: list[tuple[str, str, Any]] = []

    def request(self, method: str, path: str, payload: Any | None = None) -> dict[str, Any]:
        self.requests.append((method, path, payload))
        if path.endswith("/_mapping"):
            return {
                self.index: {
                    "mappings": {
                        "_meta": {
                            "embedding_model": "embedding-v1",
                            "embedding_dimension": 3,
                            "embedding_profile_fingerprint": EMBEDDING_PROFILE,
                        },
                        "properties": {"embedding": {"type": "dense_vector", "dims": 3}},
                    }
                }
            }
        if isinstance(payload, dict) and "bool" in dict(payload.get("query") or {}):
            return {"count": self.contract_count}
        return {"count": self.document_count}


def test_live_projection_verifies_mapping_count_and_online_fingerprint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        lifecycle,
        "effective_ingestion_settings",
        lambda: Settings(
            textbook_rag_embedding_model="embedding-v1",
            textbook_rag_embedding_dimension=3,
        ),
    )
    client = _FakeElasticsearch()
    result = lifecycle.verify_live_elasticsearch_projection(
        {
            "id": "tbk-online",
            "document_kind": "textbook",
            "publication_status": "review_ready",
            "processing_fingerprint": "fingerprint-v1",
            "active_projection_run_id": "run-1",
            "metadata": {},
        },
        _verified_job(),
        2,
        client=client,
    )

    assert result["verified"] is True
    assert result["actual_chunk_count"] == 2
    contract_query = client.requests[-1][2]
    filters = contract_query["query"]["bool"]["filter"]
    assert {"term": {"document_id": "tbk-online"}} in filters
    assert {"term": {"processing_fingerprint": "fingerprint-v1"}} in filters
    assert {"term": {"embedding_model": "embedding-v1"}} in filters
    assert {"term": {"embedding_dimension": 3}} in filters
    assert {"term": {"embedding_profile_fingerprint": EMBEDDING_PROFILE}} in filters
    assert {"term": {"projection_run_id": "run-1"}} in filters


def test_live_projection_rejects_stale_or_partial_document_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        lifecycle,
        "effective_ingestion_settings",
        lambda: Settings(
            textbook_rag_embedding_model="embedding-v1",
            textbook_rag_embedding_dimension=3,
        ),
    )
    result = lifecycle.verify_live_elasticsearch_projection(
        {
            "id": "tbk-online",
            "document_kind": "textbook",
            "publication_status": "review_ready",
            "processing_fingerprint": "fingerprint-v1",
            "active_projection_run_id": "run-1",
            "metadata": {},
        },
        _verified_job(),
        2,
        client=_FakeElasticsearch(document_count=2, contract_count=1),
    )

    assert result["verified"] is False
    assert result["blockers"] == ["live_active_projection_count_mismatch"]


def test_live_projection_rejects_extra_es_orphans_for_same_document(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        lifecycle,
        "effective_ingestion_settings",
        lambda: Settings(
            textbook_rag_embedding_model="embedding-v1",
            textbook_rag_embedding_dimension=3,
        ),
    )
    result = lifecycle.verify_live_elasticsearch_projection(
        {
            "id": "tbk-online",
            "document_kind": "textbook",
            "publication_status": "review_ready",
            "processing_fingerprint": "fingerprint-v1",
            "active_projection_run_id": "run-1",
            "metadata": {},
        },
        _verified_job(),
        2,
        client=_FakeElasticsearch(document_count=3, contract_count=2),
    )

    assert result["verified"] is True
    assert result["blockers"] == []
    assert result["stale_projection_chunk_count"] == 1


def test_live_projection_rejects_job_and_document_run_conflict(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        lifecycle,
        "effective_ingestion_settings",
        lambda: Settings(
            textbook_rag_embedding_model="embedding-v1",
            textbook_rag_embedding_dimension=3,
        ),
    )
    result = lifecycle.verify_live_elasticsearch_projection(
        {
            "id": "tbk-online",
            "document_kind": "textbook",
            "publication_status": "inactive",
            "processing_fingerprint": "fingerprint-v1",
            "active_projection_run_id": "run-2",
            "metadata": {},
        },
        _verified_job(),
        2,
        client=_FakeElasticsearch(),
    )

    assert result["verified"] is False
    assert "projection_run_id_mismatch" in result["blockers"]


def test_inactive_rollback_uses_document_run_when_job_output_lacks_legacy_run(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        lifecycle,
        "effective_ingestion_settings",
        lambda: Settings(
            textbook_rag_embedding_model="embedding-v1",
            textbook_rag_embedding_dimension=3,
        ),
    )
    job = _verified_job("ready")
    job["outputs"] = {"index_verified": True, "indexed_chunks": 2}
    result = lifecycle.verify_live_elasticsearch_projection(
        {
            "id": "tbk-online",
            "document_kind": "textbook",
            "publication_status": "inactive",
            "processing_fingerprint": "fingerprint-v1",
            "active_projection_run_id": "run-2",
            "metadata": {},
        },
        job,
        2,
        client=_FakeElasticsearch(),
    )

    assert result["verified"] is True
    assert result["active_projection_run_id"] == "run-2"
    assert result["job_projection_run_id"] is None


def test_live_seed_projection_uses_registered_es_doc_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        lifecycle,
        "effective_ingestion_settings",
        lambda: Settings(
            textbook_rag_embedding_model="embedding-v1",
            textbook_rag_embedding_dimension=3,
        ),
    )
    client = _FakeElasticsearch()
    result = lifecycle.verify_live_elasticsearch_projection(
        {
            "id": "DOC_SEED",
            "document_kind": "canonical_textbook",
            "metadata": {"index_document_id": "seed-es-doc"},
        },
        None,
        2,
        client=client,
    )

    assert result["verified"] is True
    assert result["identity_field"] == "doc_id"
    assert result["identity_value"] == "seed-es-doc"
    filters = client.requests[-1][2]["query"]["bool"]["filter"]
    assert {"term": {"doc_id": "seed-es-doc"}} in filters
    assert not any("processing_fingerprint" in item.get("term", {}) for item in filters)


@pytest.mark.parametrize("partial_stage", ["delete", "count"])
def test_elasticsearch_cleanup_rejects_partial_success(
    partial_stage: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        lifecycle,
        "effective_ingestion_settings",
        lambda: Settings(
            textbook_rag_elasticsearch_url="http://elasticsearch.test:9200",
            textbook_rag_elasticsearch_index="shared-textbooks",
        ),
    )

    class _PartialCleanupElasticsearch:
        index = "shared-textbooks"

        def request(
            self,
            _method: str,
            path: str,
            _payload: Any | None = None,
        ) -> dict[str, Any]:
            response = {
                "_shards": {
                    "total": 2,
                    "successful": 1,
                    "skipped": 0,
                    "failed": 0,
                }
            }
            if "_delete_by_query" in path:
                return {"deleted": 2, **(response if partial_stage == "delete" else {})}
            return {"count": 0, **(response if partial_stage == "count" else {})}

    monkeypatch.setattr(
        lifecycle,
        "TextbookElasticsearchClient",
        lambda **_kwargs: _PartialCleanupElasticsearch(),
    )

    with pytest.raises(lifecycle.TextbookIngestionError) as raised:
        lifecycle._delete_elasticsearch_projection("tbk-online")

    assert raised.value.reason == "elasticsearch_cleanup_incomplete"
    assert "shards_incomplete" in (
        raised.value.details[f"{partial_stage}_issues"]
    )
