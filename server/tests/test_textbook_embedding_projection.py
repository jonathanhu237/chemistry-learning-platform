from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pytest

from server.app.domains.textbook_ingestion.contracts import ExtractionMethod, StableChunk
from server.app.domains.textbook_ingestion.embedding import BatchTextbookEmbedder
from server.app.domains.textbook_ingestion.projection import (
    OnlineTextbookSearchProjector,
    ProjectionDocument,
    TextbookProjectionError,
)


def _chunk(index: int, *, content_hash: str | None = None, text: str | None = None) -> StableChunk:
    return StableChunk(
        chunk_id=f"chunk-{index}",
        document_id="tbk-1",
        document_version=2,
        chunk_index=index,
        text=text or f"教材正文 {index}",
        page_start=index,
        page_end=index,
        section_title="第一节",
        section_path=["第一章", "第一节"],
        content_type="text",
        content_hash=content_hash or f"hash-{index}",
        extraction_method=ExtractionMethod.NATIVE,
    )


@dataclass
class _FakeEmbeddingClient:
    model: str = "embedding-model"

    def __post_init__(self) -> None:
        self.calls: list[list[str]] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(texts)
        return [[float(len(text)), 1.0] for text in texts]


class _ReuseStore:
    def lookup(self, *_: Any, **__: Any) -> dict[str, list[float]]:
        return {"reused-hash": [9.0, 9.0]}


def test_batch_embedder_reuses_vectors_and_deduplicates_same_content() -> None:
    client = _FakeEmbeddingClient()
    chunks = [
        _chunk(1, content_hash="reused-hash", text="复用正文"),
        _chunk(2, content_hash="new-hash", text="新正文"),
        _chunk(3, content_hash="new-hash", text="新正文"),
    ]

    result = BatchTextbookEmbedder(
        client,
        embedding_dimension=2,
        batch_size=1,
        reuse_store=_ReuseStore(),
    ).embed_chunks(chunks)

    assert result.vectors == [[9.0, 9.0], [3.0, 1.0], [3.0, 1.0]]
    assert result.reused_count == 1
    assert result.computed_count == 2
    assert result.unique_computed_count == 1
    assert client.calls == [["新正文"]]


class _FakeES:
    index = "rag-index"

    def __init__(self, *, reject_second: bool = False) -> None:
        self.reject_second = reject_second
        self.ensure_calls: list[dict[str, Any]] = []
        self.bulk_sources: list[dict[str, Any]] = []
        self.last_bulk_operations: list[dict[str, Any]] = []
        self.requests: list[tuple[str, str, Any]] = []

    def ensure_index(self, **kwargs: Any) -> None:
        self.ensure_calls.append(kwargs)

    def bulk(self, operations: list[dict[str, Any]]) -> dict[str, Any]:
        self.last_bulk_operations = list(operations)
        ids = [operation["index"]["_id"] for operation in operations[::2]]
        self.bulk_sources.extend(operations[1::2])
        items = []
        for index, chunk_id in enumerate(ids):
            if self.reject_second and index == 1:
                items.append({"index": {"_id": chunk_id, "status": 400, "error": {"reason": "bad vector"}}})
            else:
                items.append({"index": {"_id": chunk_id, "status": 201}})
        return {"errors": self.reject_second, "items": items}

    def request(self, method: str, path: str, payload: Any = None) -> dict[str, Any]:
        self.requests.append((method, path, payload))
        if "_delete_by_query" in path:
            filters = (((payload or {}).get("query") or {}).get("bool") or {}).get("filter") or []
            run_ids = [
                str(item["term"]["projection_run_id"])
                for item in filters
                if isinstance(item, dict) and "projection_run_id" in (item.get("term") or {})
            ]
            before = len(self.bulk_sources)
            if run_ids:
                self.bulk_sources = [
                    source for source in self.bulk_sources if source.get("projection_run_id") not in run_ids
                ]
            else:
                self.bulk_sources.clear()
            deleted = before - len(self.bulk_sources)
            return {"deleted": deleted}
        if path.endswith("/_count"):
            filters = (((payload or {}).get("query") or {}).get("bool") or {}).get("filter") or []
            expected_terms = {
                key: value
                for item in filters
                for key, value in (item.get("term") or {}).items()
                if isinstance(item, dict)
            }
            return {
                "count": sum(
                    all(source.get(key) == value for key, value in expected_terms.items())
                    for source in self.bulk_sources
                )
            }
        return {}


def _projector(es: _FakeES) -> OnlineTextbookSearchProjector:
    return OnlineTextbookSearchProjector(
        es=es,  # type: ignore[arg-type]
        document=ProjectionDocument(
            document_id="tbk-1",
            logical_textbook_key="textbook_inorganic_lower_v1",
            document_version=2,
            title="无机化学（下册）（第二版）",
            processing_fingerprint="fingerprint",
            projection_run_id="lease-run-1",
        ),
        embedding_dimension=2,
        batch_size=10,
    )


def test_online_projector_indexes_traceable_fields_and_verifies_count() -> None:
    es = _FakeES()
    chunks = [_chunk(1), _chunk(2)]

    result = _projector(es).project(chunks, [[0.1, 0.2], [0.3, 0.4]], embedding_model="embedding-model")

    assert result["index_verified"] is True
    assert result["indexed_chunks"] == 2
    assert result["projection_run_id"] == "lease-run-1"
    assert es.ensure_calls == [
        {"embedding_model": "embedding-model", "embedding_dimension": 2, "recreate": False}
    ]
    assert [source["document_id"] for source in es.bulk_sources] == ["tbk-1", "tbk-1"]
    assert [source["document_version"] for source in es.bulk_sources] == [2, 2]
    assert [source["projection_run_id"] for source in es.bulk_sources] == ["lease-run-1", "lease-run-1"]
    bulk_ids = [operation["index"]["_id"] for operation in es.last_bulk_operations[::2]]
    assert all(identifier.startswith("lease-run-1:") for identifier in bulk_ids)
    assert all(source["logical_textbook_key"] == "textbook_inorganic_lower_v1" for source in es.bulk_sources)
    assert es.requests[0][1].startswith("/rag-index/_delete_by_query")
    assert any(path.endswith("/_refresh") for _, path, _ in es.requests)
    assert any(path.endswith("/_count") for _, path, _ in es.requests)


def test_online_projector_rejects_partial_bulk_success() -> None:
    es = _FakeES(reject_second=True)

    with pytest.raises(TextbookProjectionError) as error:
        _projector(es).project([_chunk(1), _chunk(2)], [[0.1, 0.2], [0.3, 0.4]], embedding_model="embedding-model")

    assert error.value.reason == "elasticsearch_bulk_failed"
    assert "bad vector" in str(error.value.details)


def test_online_projector_reprocessing_removes_old_document_chunks_first() -> None:
    es = _FakeES()
    projector = _projector(es)
    projector.project(
        [_chunk(1), _chunk(2)],
        [[0.1, 0.2], [0.3, 0.4]],
        embedding_model="embedding-model",
    )

    result = projector.project([_chunk(1)], [[0.5, 0.6]], embedding_model="embedding-model")

    assert result["indexed_chunks"] == 1
    assert result["removed_stale_chunks"] == 2
    assert len(es.bulk_sources) == 1


def test_stale_projection_run_cleanup_cannot_delete_reclaimed_worker_documents() -> None:
    es = _FakeES()
    projector = _projector(es)
    projector.project([_chunk(1)], [[0.1, 0.2]], embedding_model="embedding-model")
    es.bulk_sources[0]["projection_run_id"] = "lease-run-2"

    result = projector.delete_projection_run("tbk-1", "lease-run-1")

    assert result["deleted"] == 0
    assert len(es.bulk_sources) == 1
    assert es.bulk_sources[0]["projection_run_id"] == "lease-run-2"


class _CleanupResponseES(_FakeES):
    def __init__(
        self,
        *,
        delete_response: dict[str, Any] | None = None,
        count_response: dict[str, Any] | None = None,
    ) -> None:
        super().__init__()
        self.delete_response = delete_response or {"deleted": 0}
        self.count_response = count_response or {"count": 0}

    def request(self, method: str, path: str, payload: Any = None) -> dict[str, Any]:
        self.requests.append((method, path, payload))
        if "_delete_by_query" in path:
            return self.delete_response
        if path.endswith("/_count"):
            return self.count_response
        return {}


@pytest.mark.parametrize(
    "delete_response, expected_issue",
    [
        ({"deleted": 0, "timed_out": True}, "timed_out"),
        ({"deleted": 0, "failures": [{"reason": "partial"}]}, "failures_reported"),
        (
            {
                "deleted": 0,
                "_shards": {"total": 2, "successful": 1, "skipped": 0, "failed": 1},
            },
            "shards_failed",
        ),
        (
            {
                "deleted": 0,
                "_shards": {"total": 2, "successful": 1, "skipped": 0, "failed": 0},
            },
            "shards_incomplete",
        ),
    ],
)
def test_projection_run_cleanup_rejects_partial_delete_response(
    delete_response: dict[str, Any],
    expected_issue: str,
) -> None:
    projector = _projector(_CleanupResponseES(delete_response=delete_response))

    with pytest.raises(TextbookProjectionError) as raised:
        projector.delete_projection_run("tbk-1", "lease-run-1")

    assert raised.value.reason == "elasticsearch_delete_incomplete"
    assert expected_issue in raised.value.details["delete_issues"]


@pytest.mark.parametrize(
    "count_response, expected_issue",
    [
        ({"count": 0, "timed_out": True}, "timed_out"),
        ({"count": 0, "failures": [{"reason": "partial"}]}, "failures_reported"),
        (
            {
                "count": 0,
                "_shards": {"total": 2, "successful": 1, "skipped": 0, "failed": 1},
            },
            "shards_failed",
        ),
        (
            {
                "count": 0,
                "_shards": {"total": 2, "successful": 1, "skipped": 0, "failed": 0},
            },
            "shards_incomplete",
        ),
    ],
)
def test_projection_run_cleanup_rejects_partial_count_response(
    count_response: dict[str, Any],
    expected_issue: str,
) -> None:
    projector = _projector(_CleanupResponseES(count_response=count_response))

    with pytest.raises(TextbookProjectionError) as raised:
        projector.delete_projection_run("tbk-1", "lease-run-1")

    assert raised.value.reason == "elasticsearch_delete_incomplete"
    assert expected_issue in raised.value.details["count_issues"]
