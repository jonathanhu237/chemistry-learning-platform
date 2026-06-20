from __future__ import annotations

from contextlib import contextmanager
from types import SimpleNamespace
from typing import Any

from server.app.domains.catalog_tree import ai_context


class _Result:
    def __init__(self, row: dict[str, Any] | None = None, rows: list[dict[str, Any]] | None = None) -> None:
        self.row = row
        self.rows = rows or ([] if row is None else [row])

    def mappings(self) -> "_Result":
        return self

    def first(self) -> dict[str, Any] | None:
        return self.row

    def all(self) -> list[dict[str, Any]]:
        return self.rows


class _EvidenceSession:
    def __init__(self, *, state: dict[str, Any] | None = None, bindings: list[dict[str, Any]] | None = None) -> None:
        self.state = state
        self.bindings = bindings or []

    def execute(self, statement: Any, params: dict[str, Any] | None = None) -> _Result:
        sql = str(statement)
        if "FROM experiment_catalog_point_evidence_state" in sql:
            return _Result(self.state)
        if "FROM experiment_catalog_point_evidence_bindings" in sql:
            return _Result(rows=self.bindings)
        return _Result()


def test_static_evidence_missing_is_fallback_absence_not_ai_block() -> None:
    payload = ai_context.build_static_evidence_payload(_EvidenceSession(), node_id="cat-point-1")

    assert payload["status"] == "missing_fallback_evidence"
    assert payload["static_fallback_missing"] is True
    assert payload["ai_consumable_without_static_binding"] is True
    assert "Dynamic RAG" in payload["message"]


def test_static_evidence_payload_marks_stale_binding_with_chunk_metadata() -> None:
    payload = ai_context.build_static_evidence_payload(
        _EvidenceSession(
            state={
                "node_id": "cat-point-1",
                "evidence_status": "stale",
                "source_mode": "catalog_node_evidence",
                "trigger_policy": "stale_until_manual_refresh",
                "selected_chunk_ids": ["chunk-1"],
                "source_refs": [],
                "diagnostics": {},
                "stale_reason": "point_content_edited",
            },
            bindings=[
                {
                    "binding_id": "binding-1",
                    "node_id": "cat-point-1",
                    "chunk_id": "chunk-1",
                    "evidence_role": "fallback",
                    "selection_status": "selected",
                    "freshness_status": "stale",
                    "rank": 1,
                    "score": 0.72,
                    "rerank_score": 0.91,
                    "source_metadata": {"source_file": "source.md", "text_preview": "reviewed static evidence"},
                    "diagnostics": {"rerank": "ok"},
                    "document_id": "doc-1",
                    "page_number": 3,
                    "section_title": "Halogen evidence",
                    "source_file": "source.md",
                    "text": "fallback text",
                }
            ],
        ),
        node_id="cat-point-1",
    )

    assert payload["status"] == "stale_fallback_evidence"
    assert payload["selected_chunk_ids"] == ["chunk-1"]
    assert payload["bindings"][0]["chunk_id"] == "chunk-1"
    assert payload["bindings"][0]["source_title"] == "source.md"
    assert payload["bindings"][0]["page_number"] == 3
    assert payload["bindings"][0]["rerank_score"] == 0.91


def _point_node(*_args: Any, **_kwargs: Any) -> dict[str, Any]:
    return {"node_id": "cat-point-1", "node_kind": "point", "title": "Chlorine bleaching", "chapter_id": "CH1"}


@contextmanager
def _session_scope():
    yield object()


def test_dynamic_rag_probe_returns_queries_counts_evidence_and_rerank(monkeypatch) -> None:
    monkeypatch.setattr(ai_context, "db_session", _session_scope)
    monkeypatch.setattr(ai_context, "get_node", _point_node)
    monkeypatch.setattr(
        ai_context,
        "build_catalog_point_context",
        lambda _session, node_id: {
            "node_id": node_id,
            "chapter_id": "CH1",
            "title": "Chlorine bleaching",
            "catalog_path": ["Chapter", "Chlorine"],
            "field_contributors": ["title", "catalog_path", "normalized_equations"],
        },
    )
    monkeypatch.setattr(
        ai_context,
        "build_catalog_point_queries",
        lambda context: (["chlorine bleaching evidence"], {"status": "generated", "provider": "test", "field_contributors": context["field_contributors"]}),
    )
    monkeypatch.setattr(ai_context, "_safe_runtime_health", lambda: {"healthy": True, "status": "healthy"})
    monkeypatch.setattr(ai_context, "get_settings", lambda: SimpleNamespace(rag_final_top_k=2))
    monkeypatch.setattr(ai_context, "get_repositories", lambda: object())
    monkeypatch.setattr(
        ai_context,
        "retrieve_hybrid_context",
        lambda **_kwargs: SimpleNamespace(
            chunks=[
                {
                    "chunk_id": "chunk-1",
                    "source_file": "source.md",
                    "page_number": 4,
                    "text": "Chlorine water bleaches colored solution by oxidation.",
                }
            ],
            trace={
                "mode": "hybrid_bge_rerank",
                "candidate_counts": {"keyword": 1, "vector": 1, "merged": 1, "final": 1},
                "final_evidence": [{"chunk_id": "chunk-1", "rank": 1, "score": 0.8, "rerank_score": 0.96, "source": "vector"}],
                "rerank_scores": [{"chunk_id": "chunk-1", "rerank_score": 0.96}],
                "fallbacks": [],
            },
        ),
    )

    result = ai_context.catalog_point_rag_probe(node_id="cat-point-1")

    assert result["ok"] is True
    assert result["generated_queries"] == ["chlorine bleaching evidence"]
    assert result["candidate_counts"]["final"] == 1
    assert result["final_evidence"][0]["chunk_id"] == "chunk-1"
    assert result["final_evidence"][0]["rerank_score"] == 0.96
    assert result["query_strategy"]["fields_used"] == ["title", "catalog_path", "normalized_equations"]


def test_dynamic_rag_probe_failure_reports_stage_without_evidence(monkeypatch) -> None:
    monkeypatch.setattr(ai_context, "db_session", _session_scope)
    monkeypatch.setattr(ai_context, "get_node", _point_node)
    monkeypatch.setattr(
        ai_context,
        "build_catalog_point_context",
        lambda _session, node_id: {"node_id": node_id, "title": "Point", "catalog_path": [], "field_contributors": ["title"]},
    )
    monkeypatch.setattr(ai_context, "build_catalog_point_queries", lambda _context: (["point query"], {"status": "fallback"}))
    monkeypatch.setattr(
        ai_context,
        "_safe_runtime_health",
        lambda: {"healthy": False, "status": "unavailable", "reason_code": "bge_not_configured", "message": "BGE service URL is not configured"},
    )
    monkeypatch.setattr(
        ai_context,
        "retrieve_hybrid_context",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("RAG should not run when runtime is unhealthy")),
    )

    result = ai_context.catalog_point_rag_probe(node_id="cat-point-1")

    assert result["ok"] is False
    assert result["failed_stage"] == "runtime_health"
    assert result["final_evidence"] == []
    assert result["runtime_health"]["reason_code"] == "bge_not_configured"
