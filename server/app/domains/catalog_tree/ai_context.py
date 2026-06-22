from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text

from server.app.domains.catalog_tree.common import (
    breadcrumbs,
    catalog_path_titles_with_chapter,
    clean,
    get_content,
    get_node,
    point_capable,
)
from server.app.domains.catalog_tree.jobs import (
    _catalog_point_context as build_catalog_point_context,
    _catalog_point_queries as build_catalog_point_queries,
    _legacy_retrieve_catalog_context as legacy_retrieve_catalog_context,
    _rag_runtime_gate as catalog_rag_runtime_gate,
    _source_refs_from_chunks as source_refs_from_chunks,
    get_point_job_state,
)
from server.app.domains.catalog_tree.media_bindings import student_videos
from server.app.domains.catalog_tree.related_links import related_links
from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from server.app.hybrid_rag import retrieve_hybrid_context
from server.app.infrastructure.database import db_session
from server.app.infrastructure.settings import get_settings
from server.app.repositories import RepositoryProvider, get_repositories
from server.app.schemas import AgentAskRequest


def catalog_point_ai_context(*, node_id: str) -> dict[str, Any]:
    with db_session() as session:
        node = get_node(session, node_id)
        if not point_capable(node):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="AI context is only available for catalog point nodes")
        content = get_content(session, node_id)
        path = breadcrumbs(session, node_id)
        path_titles = catalog_path_titles_with_chapter(node, path)
        videos = student_videos(session, node_id)
        related = related_links(session, node_id, include_hidden=True, include_defaults=True)
        job_state = get_point_job_state(session, node_id=node_id)
        static_evidence = build_static_evidence_payload(session, node_id=node_id, evidence_state=job_state.get("evidence_state"))

    runtime_health = _safe_runtime_health()
    point_title = clean((content or {}).get("point_title")) or clean(node.get("title"))
    return {
        "teacher_only": True,
        "node_id": node_id,
        "placement_node_id": node_id,
        "canonical_point_id": node.get("canonical_point_id") or node_id,
        "point_title": point_title,
        "catalog_path": path,
        "catalog_path_text": " / ".join(path_titles),
        "publication_state": {
            "node_status": node.get("status") or "draft",
            "content_status": (content or {}).get("content_status") or "missing",
            "node_published_at": _string_or_none(node.get("published_at")),
            "content_published_at": _string_or_none((content or {}).get("published_at")),
        },
        "student_facing_content": {
            "principle_mode": (content or {}).get("principle_mode") or "text",
            "principle_text": (content or {}).get("principle_text") or "",
            "principle_equation": (content or {}).get("principle_equation") or "",
            "reaction_equations": (content or {}).get("reaction_equations") or [],
            "phenomenon_explanation": (content or {}).get("phenomenon_explanation") or "",
            "safety_note": (content or {}).get("safety_note") or "",
        },
        "teacher_only_notes": {
            "node_teacher_note": node.get("teacher_note") or "",
            "point_teacher_note": (content or {}).get("teacher_note") or "",
        },
        "related_points": related,
        "videos": videos,
        "content_freshness": {
            "node_updated_at": _string_or_none(node.get("updated_at")),
            "content_updated_at": _string_or_none((content or {}).get("updated_at")),
            "evidence_status": (job_state.get("evidence_state") or {}).get("evidence_status"),
            "evidence_updated_at": (job_state.get("evidence_state") or {}).get("updated_at"),
            "es_status": (job_state.get("es_state") or {}).get("sync_status") if job_state.get("es_state") else None,
            "es_updated_at": (job_state.get("es_state") or {}).get("updated_at") if job_state.get("es_state") else None,
        },
        "static_evidence": static_evidence,
        "dynamic_rag": {
            "primary_path": True,
            "probe_available": bool(runtime_health.get("healthy")),
            "runtime_health": runtime_health,
            "note": "Dynamic RAG can consume structured catalog point context when runtime policy and BGE health allow it.",
        },
        "job_state": job_state,
    }


def catalog_point_rag_probe(*, node_id: str) -> dict[str, Any]:
    with db_session() as session:
        node = get_node(session, node_id)
        if not point_capable(node):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="RAG probe is only available for catalog point nodes")
        try:
            context = build_catalog_point_context(session, node_id=node_id)
        except Exception as exc:
            return _probe_failure(
                node_id=node_id,
                failed_stage="point_context",
                reason=f"{exc.__class__.__name__}: {str(exc)[:240]}",
                runtime_health=_safe_runtime_health(),
            )

    queries, query_trace = build_catalog_point_queries(context)
    query_strategy = _query_strategy_payload(context, queries, query_trace)
    runtime_health = _safe_runtime_health()
    if not runtime_health.get("healthy"):
        return _probe_failure(
            node_id=node_id,
            failed_stage="runtime_health",
            reason=str(runtime_health.get("message") or runtime_health.get("reason_code") or "RAG runtime is unavailable"),
            runtime_health=runtime_health,
            generated_queries=queries,
            query_strategy=query_strategy,
        )
    if not queries:
        return _probe_failure(
            node_id=node_id,
            failed_stage="query_generation",
            reason="No retrieval query could be generated from the current catalog point context.",
            runtime_health=runtime_health,
            query_strategy=query_strategy,
        )

    settings = get_settings()
    repositories = get_repositories()
    prompt = queries[0]

    def query_generator(_question: str) -> tuple[list[str], dict[str, Any]]:
        return queries, query_trace

    request = AgentAskRequest(
        user_role="teacher",
        question=prompt,
        chapter_id=context.get("chapter_id"),
        point_node_id=node_id,
        catalog_path=context.get("catalog_path") or [],
        allow_progress_lookup=False,
        allow_rag_lookup=True,
        max_answer_chars=0,
    )
    try:
        result = retrieve_hybrid_context(
            repositories=repositories,
            question=prompt,
            request=request,
            settings=settings,
            legacy_retrieve=lambda lookup_query, lookup_limit: legacy_retrieve_catalog_context(
                repositories,
                context=context,
                query=lookup_query,
                limit=lookup_limit,
            ),
            query_generator=query_generator,
            limit=max(1, int(settings.rag_final_top_k)),
        )
    except Exception as exc:
        return _probe_failure(
            node_id=node_id,
            failed_stage="rag_recall_or_rerank",
            reason=f"{exc.__class__.__name__}: {str(exc)[:240]}",
            runtime_health=runtime_health,
            generated_queries=queries,
            query_strategy=query_strategy,
        )

    final_evidence = _final_evidence_payload(result.chunks, result.trace)
    if not final_evidence:
        return _probe_failure(
            node_id=node_id,
            failed_stage="recall",
            reason="RAG completed but selected no usable source chunks for this catalog point.",
            runtime_health=runtime_health,
            generated_queries=queries,
            query_strategy=query_strategy,
            trace=result.trace,
        )
    return {
        "ok": True,
        "node_id": node_id,
        "failed_stage": None,
        "reason": None,
        "runtime_health": runtime_health,
        "generated_queries": queries,
        "query_strategy": query_strategy,
        "recall_source": result.trace.get("mode"),
        "candidate_counts": result.trace.get("candidate_counts") or {},
        "final_evidence": final_evidence,
        "rerank_scores": result.trace.get("rerank_scores") or [],
        "fallbacks": result.trace.get("fallbacks") or [],
        "trace": result.trace,
    }


def build_static_evidence_payload(
    session: Any,
    *,
    node_id: str,
    evidence_state: dict[str, Any] | None = None,
) -> dict[str, Any]:
    state = evidence_state or _evidence_state(session, node_id=node_id)
    bindings = [_binding_payload(row) for row in _evidence_binding_rows(session, node_id=node_id)]
    stale = str(state.get("evidence_status") or "") == "stale" or any(item.get("freshness_status") == "stale" for item in bindings)
    if not bindings:
        status_value = "missing_fallback_evidence"
        message = "Static fallback evidence is missing; Dynamic RAG remains the primary AI path when runtime health permits it."
    elif stale:
        status_value = "stale_fallback_evidence"
        message = "Static fallback evidence exists but is stale; refresh RAG evidence before treating it as current."
    else:
        status_value = "available_static_fallback"
        message = "Static evidence is available as fallback or supplemental AI evidence; it is not student body copy."
    return {
        "node_id": node_id,
        "status": status_value,
        "state": state,
        "bindings": bindings,
        "selected_chunk_ids": [item["chunk_id"] for item in bindings if item.get("selection_status") == "selected"],
        "binding_count": len(bindings),
        "static_fallback_available": bool(bindings),
        "static_fallback_missing": not bindings,
        "dynamic_rag_primary": True,
        "ai_consumable_without_static_binding": True,
        "message": message,
    }


def catalog_point_static_evidence_package(*, point_node_id: str) -> dict[str, Any]:
    with db_session() as session:
        node = get_node(session, point_node_id)
        if not point_capable(node):
            return {}
        path = breadcrumbs(session, point_node_id)
        path_titles = catalog_path_titles_with_chapter(node, path)
        content = get_content(session, point_node_id) or {}
        payload = build_static_evidence_payload(session, node_id=point_node_id)
    bindings = payload.get("bindings") or []
    return {
        "enabled": True,
        "evidence_source": "catalog_node_static_evidence",
        "static_evidence_role": "fallback_or_supplemental",
        "point_node_id": point_node_id,
        "placement_node_id": point_node_id,
        "canonical_point_id": node.get("canonical_point_id") or point_node_id,
        "point_title": clean(content.get("point_title")) or clean(node.get("title")),
        "catalog_path": path_titles,
        "chunk_ids": [str(item.get("chunk_id")) for item in bindings if item.get("chunk_id")],
        "chunk_roles": {str(item.get("chunk_id")): item.get("evidence_role") for item in bindings if item.get("chunk_id")},
        "static_fallback_missing": bool(payload.get("static_fallback_missing")),
        "static_evidence_status": payload.get("status"),
        "evidence_state_status": (payload.get("state") or {}).get("evidence_status"),
        "source_count": len(bindings),
        "bindings": bindings,
        "dynamic_rag_available": True,
        "message": payload.get("message"),
    }


def hydrate_static_evidence_sources(repositories: RepositoryProvider, *, chunk_ids: list[str]) -> tuple[list[Any], list[str]]:
    if not chunk_ids:
        return [], []
    chunks_by_id = {
        str(chunk.get("chunk_id") or chunk.get("id")): chunk
        for chunk in repositories.content.source_chunks()
        if str(chunk.get("chunk_id") or chunk.get("id") or "").strip()
    }
    from server.app.domains.assistant.rag_sources import _source_from_chunk

    sources = [_source_from_chunk(chunks_by_id[chunk_id]) for chunk_id in chunk_ids if chunk_id in chunks_by_id]
    missing = [chunk_id for chunk_id in chunk_ids if chunk_id not in chunks_by_id]
    return sources, missing


def _safe_runtime_health() -> dict[str, Any]:
    try:
        return catalog_rag_runtime_gate(get_settings())
    except Exception as exc:
        return {
            "healthy": False,
            "status": "unavailable",
            "reason_code": "runtime_health_check_failed",
            "message": f"{exc.__class__.__name__}: {str(exc)[:240]}",
        }


def _query_strategy_payload(context: dict[str, Any], queries: list[str], query_trace: dict[str, Any]) -> dict[str, Any]:
    status_value = str(query_trace.get("status") or "generated")
    return {
        "status": status_value,
        "provider": query_trace.get("provider") or "catalog_point_context",
        "generated_queries": queries,
        "fields_used": query_trace.get("field_contributors") or context.get("field_contributors") or [],
        "fallback_reason": "deterministic_catalog_context_query" if status_value == "fallback" else None,
        "field_policy": [
            "title",
            "catalog_path",
            "normalized_equations",
            "phenomenon_explanation",
            "safety_note",
            "videos",
            "related_points",
        ],
    }


def _probe_failure(
    *,
    node_id: str,
    failed_stage: str,
    reason: str,
    runtime_health: dict[str, Any],
    generated_queries: list[str] | None = None,
    query_strategy: dict[str, Any] | None = None,
    trace: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "ok": False,
        "node_id": node_id,
        "failed_stage": failed_stage,
        "reason": reason,
        "runtime_health": runtime_health,
        "generated_queries": generated_queries or [],
        "query_strategy": query_strategy or {},
        "recall_source": (trace or {}).get("mode"),
        "candidate_counts": (trace or {}).get("candidate_counts") or {},
        "final_evidence": [],
        "rerank_scores": (trace or {}).get("rerank_scores") or [],
        "fallbacks": (trace or {}).get("fallbacks") or [],
        "trace": trace or {},
    }


def _final_evidence_payload(chunks: list[dict[str, Any]], trace: dict[str, Any]) -> list[dict[str, Any]]:
    trace_by_chunk = {
        str(item.get("chunk_id")): item
        for item in trace.get("final_evidence") or []
        if isinstance(item, dict) and item.get("chunk_id")
    }
    result: list[dict[str, Any]] = []
    for index, ref in enumerate(source_refs_from_chunks(chunks), start=1):
        chunk_id = str(ref.get("chunk_id") or "")
        scored = trace_by_chunk.get(chunk_id, {})
        result.append(
            {
                **ref,
                "rank": scored.get("rank") or index,
                "score": scored.get("score"),
                "rerank_score": scored.get("rerank_score"),
                "recall_source": scored.get("source"),
                "query": scored.get("query"),
            }
        )
    return result


def _evidence_state(session: Any, *, node_id: str) -> dict[str, Any]:
    row = (
        session.execute(
            text(
                """
                WITH source AS (
                  SELECT id, canonical_point_id
                  FROM experiment_catalog_nodes
                  WHERE id = :node_id
                )
                SELECT es.node_id, es.canonical_point_id, es.source_placement_node_id,
                       es.evidence_status, es.source_mode, es.trigger_policy,
                       es.selected_chunk_ids, es.source_refs, es.diagnostics, es.stale_reason,
                       es.latest_error, es.refreshed_at, es.stale_at, es.last_attempted_at, es.updated_at
                FROM experiment_catalog_point_evidence_state es
                JOIN source ON true
                WHERE es.node_id = :node_id
                   OR (source.canonical_point_id IS NOT NULL AND es.canonical_point_id = source.canonical_point_id)
                ORDER BY CASE WHEN es.canonical_point_id = source.canonical_point_id THEN 0 ELSE 1 END,
                         es.updated_at DESC
                LIMIT 1
                """
            ),
            {"node_id": node_id},
        )
        .mappings()
        .first()
    )
    if not row:
        return {
            "node_id": node_id,
            "canonical_point_id": node_id,
            "source_placement_node_id": node_id,
            "evidence_status": "missing",
            "source_mode": "none",
            "trigger_policy": "stale_until_manual_refresh",
            "selected_chunk_ids": [],
            "source_refs": [],
            "diagnostics": {},
            "stale_reason": None,
            "latest_error": None,
            "refreshed_at": None,
            "stale_at": None,
            "last_attempted_at": None,
            "updated_at": None,
        }
    item = dict(row)
    item["selected_chunk_ids"] = list(item.get("selected_chunk_ids") or [])
    item["source_refs"] = _json_value(item.get("source_refs"), [])
    item["diagnostics"] = _json_value(item.get("diagnostics"), {})
    for key in ("refreshed_at", "stale_at", "last_attempted_at", "updated_at"):
        item[key] = _string_or_none(item.get(key))
    return item


def _evidence_binding_rows(session: Any, *, node_id: str) -> list[dict[str, Any]]:
    rows = (
        session.execute(
            text(
                """
                WITH source AS (
                  SELECT id, canonical_point_id
                  FROM experiment_catalog_nodes
                  WHERE id = :node_id
                )
                SELECT b.id::text AS binding_id,
                       b.node_id,
                       b.canonical_point_id,
                       b.source_placement_node_id,
                       b.chunk_id,
                       b.evidence_role,
                       b.selection_status,
                       b.freshness_status,
                       b.rank,
                       b.score,
                       b.rerank_score,
                       b.source_metadata,
                       b.diagnostics,
                       b.created_at,
                       b.updated_at,
                       sc.document_id,
                       sc.page_number,
                       sc.section_title,
                       sc.chunk_index,
                       sc.text,
                       sc.markdown,
                       sc.metadata AS chunk_metadata,
                       sd.file_name AS source_file,
                       sd.path AS source_path,
                       sd.document_kind,
                       sd.type AS document_type,
                       sd.metadata AS document_metadata
                FROM experiment_catalog_point_evidence_bindings b
                JOIN source ON true
                LEFT JOIN source_chunks sc ON sc.id = b.chunk_id
                LEFT JOIN source_documents sd ON sd.id = sc.document_id
                WHERE b.node_id = :node_id
                   OR (source.canonical_point_id IS NOT NULL AND b.canonical_point_id = source.canonical_point_id)
                ORDER BY b.freshness_status = 'fresh' DESC,
                         b.selection_status = 'selected' DESC,
                         b.rank,
                         b.updated_at DESC
                """
            ),
            {"node_id": node_id},
        )
        .mappings()
        .all()
    )
    return [dict(row) for row in rows]


def _binding_payload(row: dict[str, Any]) -> dict[str, Any]:
    source_metadata = _json_value(row.get("source_metadata"), {})
    diagnostics = _json_value(row.get("diagnostics"), {})
    chunk_metadata = _json_value(row.get("chunk_metadata"), {})
    document_metadata = _json_value(row.get("document_metadata"), {})
    source_title = (
        source_metadata.get("source_title")
        or source_metadata.get("source_file")
        or row.get("source_file")
        or document_metadata.get("title")
        or row.get("document_id")
        or row.get("chunk_id")
    )
    return {
        "binding_id": str(row.get("binding_id") or ""),
        "chunk_id": str(row.get("chunk_id") or ""),
        "evidence_role": row.get("evidence_role") or "supplemental",
        "selection_status": row.get("selection_status") or "selected",
        "freshness_status": row.get("freshness_status") or "missing",
        "rank": int(row.get("rank") or 0),
        "score": _float_or_none(row.get("score")),
        "rerank_score": _float_or_none(row.get("rerank_score")),
        "source_title": source_title,
        "source_file": row.get("source_file") or source_metadata.get("source_file"),
        "document_id": row.get("document_id") or source_metadata.get("document_id"),
        "document_kind": row.get("document_kind") or document_metadata.get("document_kind"),
        "document_type": row.get("document_type") or document_metadata.get("type"),
        "page_number": row.get("page_number") or source_metadata.get("page_number"),
        "section_title": row.get("section_title") or source_metadata.get("section_title"),
        "chunk_index": row.get("chunk_index"),
        "text_preview": _text_preview(row, source_metadata),
        "content_type": source_metadata.get("content_type") or chunk_metadata.get("content_type"),
        "source_metadata": source_metadata,
        "diagnostics": diagnostics,
        "updated_at": _string_or_none(row.get("updated_at")),
    }


def _text_preview(row: dict[str, Any], source_metadata: dict[str, Any]) -> str:
    value = source_metadata.get("text_preview") or row.get("text") or row.get("markdown") or ""
    return " ".join(str(value or "").split())[:420]


def _json_value(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = json.loads(value)
        except ValueError:
            return default
        if isinstance(default, dict) and isinstance(parsed, dict):
            return parsed
        if isinstance(default, list) and isinstance(parsed, list):
            return parsed
    return default


def _float_or_none(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _string_or_none(value: Any) -> str | None:
    return str(value) if value is not None else None
