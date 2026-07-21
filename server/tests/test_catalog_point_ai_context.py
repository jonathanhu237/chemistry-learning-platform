from __future__ import annotations

from contextlib import contextmanager
from typing import Any

from server.app.domains.catalog_tree import ai_context
from server.app.domains.questions.generation import _source_refs_from_static_payload


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


def test_static_evidence_missing_is_catalog_node_evidence_absence() -> None:
    payload = ai_context.build_static_evidence_payload(_EvidenceSession(), node_id="cat-point-1")

    assert payload["status"] == "missing_catalog_node_evidence"
    assert payload["static_fallback_missing"] is True
    assert payload["ai_consumable_without_static_binding"] is False


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

    assert payload["status"] == "stale_catalog_node_evidence"
    assert payload["selected_chunk_ids"] == []
    assert payload["bindings"] == []
    assert payload["static_fallback_available"] is False
    assert payload["static_fallback_missing"] is True
    assert payload["binding_count"] == 0
    assert payload["diagnostic_binding_count"] == 1
    diagnostic = payload["binding_diagnostics"][0]
    assert diagnostic["chunk_id"] == "chunk-1"
    assert diagnostic["source_title"] == "source.md"
    assert diagnostic["page_number"] == 3
    assert diagnostic["rerank_score"] == 0.91


def test_stale_state_is_authoritative_even_when_binding_was_not_yet_marked_stale() -> None:
    payload = ai_context.build_static_evidence_payload(
        _EvidenceSession(
            state={
                "node_id": "cat-point-1",
                "evidence_status": "stale",
                "diagnostics": {},
                "stale_reason": "textbook_corpus_changed",
            },
            bindings=[
                {
                    "binding_id": "binding-1",
                    "node_id": "cat-point-1",
                    "chunk_id": "chunk-1",
                    "evidence_role": "theory",
                    "selection_status": "selected",
                    "freshness_status": "fresh",
                    "source_metadata": {"source_file": "source.md"},
                }
            ],
        ),
        node_id="cat-point-1",
    )

    assert payload["status"] == "stale_catalog_node_evidence"
    assert payload["bindings"] == []
    assert payload["selected_chunk_ids"] == []
    assert payload["binding_count"] == 0
    assert payload["diagnostic_binding_count"] == 1
    assert payload["catalog_node_evidence_available"] is False
    assert _source_refs_from_static_payload(payload, node_id="cat-point-1") == []


def test_static_evidence_package_never_exposes_stale_chunks_for_assistant_hydration(monkeypatch) -> None:
    session = _EvidenceSession(
        state={"node_id": "cat-point-1", "evidence_status": "stale", "diagnostics": {}},
        bindings=[
            {
                "binding_id": "binding-1",
                "node_id": "cat-point-1",
                "chunk_id": "chunk-1",
                "selection_status": "selected",
                "freshness_status": "fresh",
                "source_metadata": {"source_file": "source.md"},
            }
        ],
    )

    @contextmanager
    def session_scope():
        yield session

    monkeypatch.setattr(ai_context, "db_session", session_scope)
    monkeypatch.setattr(ai_context, "get_node", _point_node)
    monkeypatch.setattr(ai_context, "breadcrumbs", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(ai_context, "catalog_path_titles_with_chapter", lambda *_args, **_kwargs: [])
    monkeypatch.setattr(ai_context, "get_content", lambda *_args, **_kwargs: {})

    package = ai_context.catalog_point_static_evidence_package(point_node_id="cat-point-1")

    assert package["static_evidence_status"] == "stale_catalog_node_evidence"
    assert package["chunk_ids"] == []
    assert package["bindings"] == []
    assert package["source_count"] == 0
    assert package["diagnostic_binding_count"] == 1


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
    monkeypatch.setattr(ai_context, "effective_textbook_rag_settings", lambda: {"enabled": True})
    monkeypatch.setattr(
        ai_context,
        "retrieve_point_textbook_evidence",
        lambda **_kwargs: {
            "mode": "qwen_es_textbook_rag",
            "source_refs": [
                {
                    "chunk_id": "chunk-1",
                    "source_file": "source.md",
                    "page_number": 4,
                    "text_preview": "Chlorine water bleaches colored solution by oxidation.",
                    "rerank_score": 0.96,
                }
            ],
            "candidate_diagnostics": {"principle": [{"chunk_id": "chunk-1"}]},
            "diagnostics": {"sections": {"principle": {"source_count": 1}}},
            "supported_sections": ["principle"],
            "missing_sections": [],
        },
    )

    result = ai_context.catalog_point_rag_probe(node_id="cat-point-1")

    assert result["ok"] is True
    assert result["generated_queries"] == ["chlorine bleaching evidence"]
    assert result["candidate_counts"]["principle"] == 1
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
        lambda: {
            "healthy": False,
            "status": "elasticsearch_not_configured",
            "reason_code": "elasticsearch_not_configured",
            "message": "External textbook RAG Elasticsearch URL is not configured",
        },
    )

    result = ai_context.catalog_point_rag_probe(node_id="cat-point-1")

    assert result["ok"] is False
    assert result["failed_stage"] == "runtime_health"
    assert result["final_evidence"] == []
    assert result["runtime_health"]["reason_code"] == "elasticsearch_not_configured"
