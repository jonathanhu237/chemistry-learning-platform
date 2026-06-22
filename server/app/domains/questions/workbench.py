from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from typing import Any

from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from sqlalchemy import text

from server.app.domains.catalog_tree.equations import list_reaction_equations, reaction_principle_text
from server.app.infrastructure.settings import get_settings
from server.app.infrastructure.database import db_session
from server.app.experiment_admin_schemas import (
    PointAwareSuggestionRequest,
    WorkbenchMessageRequest,
    WorkbenchSessionRequest,
)
from server.app.hybrid_rag import retrieve_hybrid_context
from server.app.domains.platform.settings import ai_feature_enabled, effective_ai_settings
from server.app.repositories import RepositoryProvider, get_repositories
from server.app.retrieval import keyword_score
from server.app.domains.catalog.experiments import (
    _ensure_experiment,
    _experiment_video_points,
    _list_experiment_video_resources,
)
from server.app.domains.questions.point_aware import (
    _attach_catalog_point_nodes,
    _canonical_point_id,
    _local_point_aware_suggestions,
    _point_node_id,
    _select_suggestion_points,
    _try_openai_point_aware_suggestions,
    _unique_point_keys,
    _unique_point_node_ids,
    _with_point_aware_metadata,
)
from server.app.domains.questions.bank import (
    _insert_question,
    _validate_question_payload,
)
from server.app.domains.questions.generation import (
    CATALOG_NODE_EVIDENCE_REQUIRED_DETAIL,
    attach_evidence_to_point_contexts,
    attach_generation_lineage,
    catalog_point_generation_contexts,
    question_payload_has_catalog_evidence_lineage,
    _catalog_node_evidence_package,
    _catalog_node_evidence_ready,
    _load_generation_sources,
    _static_catalog_node_evidence_package,
)
from server.app.domains.assistant.rag_sources import _source_evidence_payload, _source_from_chunk
from server.app.schemas import AgentAskRequest

OBJECTIVE_TYPES = {"single_choice", "true_false", "fill_blank"}


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=str)


def _json_array(value: Any) -> str:
    return json.dumps(value if value is not None else [], ensure_ascii=False, default=str)


def _question_workbench_rag_gate() -> dict[str, Any]:
    settings = get_settings()
    rag_enabled = ai_feature_enabled("rag_access_enabled")
    runtime = {
        "rag_enabled": rag_enabled,
        "hybrid_bge_enabled": bool(settings.rag_hybrid_bge_enabled),
        "query_generation_enabled": bool(settings.rag_query_generation_enabled),
        "bge_service_required": bool(rag_enabled and settings.rag_hybrid_bge_enabled),
        "bge_service_url": settings.rag_bge_service_url,
        "vector_top_k": int(settings.rag_vector_top_k),
        "rerank_top_k": int(settings.rag_rerank_top_k),
        "final_top_k": int(settings.rag_final_top_k),
    }

    def blocked(reason_code: str, message: str, *, bge_status: str = "not_required", bge_error: str | None = None) -> dict[str, Any]:
        return {
            "healthy": False,
            "status": "blocked",
            "reason_code": reason_code,
            "message": message,
            "rag_runtime": runtime,
            "bge_status": bge_status,
            "bge_error": bge_error,
            "bge_metrics": None,
        }

    if not rag_enabled:
        return blocked("rag_disabled", "RAG access is disabled; AI question workbench requires healthy RAG evidence.")
    if not settings.rag_hybrid_bge_enabled:
        return blocked("hybrid_bge_disabled", "Hybrid BGE RAG is disabled; AI question workbench requires reranked evidence.")
    if not settings.rag_query_generation_enabled:
        return blocked("query_generation_disabled", "RAG query generation is disabled; enable it before using AI question workbench.")
    if not settings.rag_bge_service_url:
        return blocked("bge_not_configured", "BGE service URL is not configured.", bge_status="not_configured")

    try:
        with urllib.request.urlopen(
            f"{settings.rag_bge_service_url.rstrip('/')}/metrics",
            timeout=min(max(1.0, float(settings.rag_bge_timeout_seconds)), 2.0),
        ) as response:
            metrics = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        return blocked(
            "bge_unreachable",
            "BGE service is unreachable; AI question workbench requires healthy rerank service.",
            bge_status="unreachable",
            bge_error=f"{exc.__class__.__name__}: {str(exc)[:160]}",
        )

    if not isinstance(metrics, dict) or not metrics.get("ok"):
        return {
            "healthy": False,
            "status": "blocked",
            "reason_code": "bge_degraded",
            "message": "BGE service responded but is not healthy; AI question workbench is blocked.",
            "rag_runtime": runtime,
            "bge_status": "degraded",
            "bge_error": None,
            "bge_metrics": metrics if isinstance(metrics, dict) else None,
        }

    return {
        "healthy": True,
        "status": "healthy",
        "reason_code": "",
        "message": "Hybrid BGE RAG is healthy; AI question workbench can use grounded evidence.",
        "rag_runtime": runtime,
        "bge_status": "healthy",
        "bge_error": None,
        "bge_metrics": metrics,
    }


def _ensure_question_workbench_rag_ready() -> dict[str, Any]:
    gate = _question_workbench_rag_gate()
    if not gate.get("healthy"):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(gate.get("message") or "RAG is not ready"))
    return gate


def _load_question_for_workbench(session: Any, question_id: str) -> dict[str, Any]:
    row = (
        session.execute(
            text(
                """
                SELECT q.*, fe.code AS experiment_code, fe.title AS experiment_title,
                       b.bank_kind, b.title AS bank_title
                FROM experiment_questions q
                JOIN formal_experiments fe ON fe.id = q.experiment_id
                LEFT JOIN experiment_question_banks b ON b.id = q.bank_id
                WHERE q.id = CAST(:id AS uuid)
                """
            ),
            {"id": question_id},
        )
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    return dict(row)


def _question_snapshot(question: dict[str, Any] | None) -> dict[str, Any]:
    if not question:
        return {}
    keys = [
        "id",
        "experiment_id",
        "experiment_code",
        "experiment_title",
        "bank_kind",
        "question_type",
        "stem",
        "options",
        "answer",
        "explanation",
        "difficulty",
        "status",
        "related_chapter_ids",
        "related_knowledge_point_ids",
        "source_chunk_ids",
        "source_refs",
        "metadata",
        "created_at",
        "updated_at",
    ]
    return {key: question.get(key) for key in keys if key in question}


def _workbench_context(
    *,
    mode: str,
    experiment: dict[str, Any],
    point: dict[str, str] | None,
    target_question: dict[str, Any] | None,
    source_refs: list[dict[str, Any]],
    target_points: list[dict[str, str]] | None = None,
    rag_gate: dict[str, Any] | None = None,
    evidence_package: dict[str, Any] | None = None,
    coverage: dict[str, Any] | None = None,
    teacher_point_content: dict[str, Any] | None = None,
) -> dict[str, Any]:
    normalized_points = target_points or ([point] if point else [])
    target_point_keys = [item["point_key"] for item in normalized_points if item.get("point_key")]
    target_point_node_ids = _unique_point_node_ids(normalized_points)
    target_canonical_point_ids = [
        item
        for item in dict.fromkeys(_canonical_point_id(item) for item in normalized_points).keys()
        if item
    ]
    package = evidence_package or {
        "mode": "canonical_evidence",
        "source_refs": source_refs,
        "source_count": len(source_refs),
        "diagnostics": {
            "rag_gate": rag_gate or {},
            "source_strategy": "canonical_evidence",
        },
    }
    return {
        "mode": mode,
        "experiment": {
            "id": experiment.get("id"),
            "code": experiment.get("code"),
            "title": experiment.get("title"),
            "summary": experiment.get("summary"),
        },
        "selected_point": point,
        "target_points": normalized_points,
        "target_point_keys": target_point_keys,
        "target_point_node_ids": target_point_node_ids,
        "source_placement_node_ids": target_point_node_ids,
        "target_canonical_point_ids": target_canonical_point_ids,
        "original_question": _question_snapshot(target_question),
        "source_refs": source_refs,
        "rag_gate": rag_gate or {},
        "evidence_package": package,
        "teacher_point_content": teacher_point_content or {},
        "source_boundaries": {
            "teacher_point_content": "student_page_context_only",
            "catalog_node_evidence": "required_fresh_catalog_node_evidence",
            "supplemental_rag_evidence": package.get("mode") or "canonical_evidence",
        },
        "coverage": coverage or {},
    }


def _teacher_point_content_context(
    session: Any,
    experiment_id: str,
    point_key: str | None,
    point_node_id: str | None = None,
) -> dict[str, Any]:
    point_node_id = str(point_node_id or "").strip()
    if point_node_id:
        row = (
            session.execute(
                text(
                    """
                    SELECT point_title, principle_mode, principle_equation, principle_text,
                           phenomenon_explanation, safety_note, content_status, updated_at
                    FROM experiment_catalog_nodes n
                    JOIN experiment_catalog_point_content pc
                      ON (
                        n.canonical_point_id IS NOT NULL
                        AND pc.canonical_point_id = n.canonical_point_id
                      )
                      OR pc.node_id = n.id
                    WHERE n.id = :node_id
                    ORDER BY
                      CASE WHEN pc.canonical_point_id = n.canonical_point_id THEN 0 ELSE 1 END,
                      pc.updated_at DESC
                    LIMIT 1
                    """
                ),
                {"node_id": point_node_id},
            )
            .mappings()
            .first()
        )
        if not row:
            return {"available": False, "content_status": "missing", "source_role": "student_page_context_only"}
        data = dict(row)
        data["reaction_equations"] = list_reaction_equations(session, point_node_id) if data.get("principle_mode") == "equation" else []
        return {
            "available": data.get("content_status") == "published",
            "point_node_id": point_node_id,
            "point_title": data.get("point_title"),
            "content_status": data.get("content_status"),
            "principle_mode": data.get("principle_mode"),
            "principle_preview": reaction_principle_text(data) if data.get("principle_mode") == "equation" else data.get("principle_text"),
            "normalized_equations": data["reaction_equations"] if data.get("principle_mode") == "equation" else [],
            "phenomenon_preview": data.get("phenomenon_explanation"),
            "safety_preview": data.get("safety_note"),
            "updated_at": data.get("updated_at"),
            "source_role": "student_page_context_only",
        }
    if not point_key:
        return {}
    return {
        "available": False,
        "content_status": "missing_node_id",
        "source_role": "student_page_context_only",
    }


def _question_coverage_for_context(
    session: Any,
    experiment_id: str,
    point_key: str | None,
    point_node_id: str | None = None,
) -> dict[str, Any]:
    params = {"experiment_id": experiment_id}
    rows = [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT question_type, status, metadata, primary_point_node_ids,
                       primary_canonical_point_ids, source_placement_node_ids
                FROM experiment_questions
                WHERE experiment_id = :experiment_id
                """
            ),
            params,
        )
        .mappings()
        .all()
    ]
    type_counts: dict[str, int] = {}
    point_question_count = 0
    for row in rows:
        type_counts[str(row.get("question_type") or "")] = type_counts.get(str(row.get("question_type") or ""), 0) + 1
        metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        point_keys = metadata.get("primary_point_keys") if isinstance(metadata, dict) else []
        point_node_ids = (
            row.get("source_placement_node_ids")
            or row.get("primary_point_node_ids")
            or metadata.get("source_placement_node_ids")
            or metadata.get("primary_point_node_ids")
            or []
        )
        if point_node_id and isinstance(point_node_ids, list) and point_node_id in point_node_ids:
            point_question_count += 1
            continue
        if point_key and isinstance(point_keys, list) and point_key in point_keys:
            point_question_count += 1
    return {
        "question_count": len(rows),
        "type_counts": type_counts,
        "selected_point_question_count": point_question_count if (point_key or point_node_id) else None,
    }


def _load_workbench_source_refs(
    session: Any,
    *,
    experiment: dict[str, Any],
    prompt: str,
    target_question: dict[str, Any] | None,
    target_points: list[dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    prompt_parts = [
        prompt,
        str(target_question.get("stem")) if target_question else "",
        " ".join(str(point.get("point_title") or point.get("point_key") or "") for point in (target_points or [])),
    ]
    source_refs = _load_generation_sources(
        session,
        experiment=experiment,
        prompt=" ".join(item for item in prompt_parts if item),
        chapter_ids=list((target_question or {}).get("related_chapter_ids") or []),
        knowledge_point_ids=list((target_question or {}).get("related_knowledge_point_ids") or []),
    )
    if not source_refs and target_question:
        source_refs = list(target_question.get("source_refs") or [])
    return source_refs


def _workbench_chapter_ids(session: Any, experiment: dict[str, Any], target_question: dict[str, Any] | None) -> list[str]:
    question_chapters = list((target_question or {}).get("related_chapter_ids") or [])
    if question_chapters:
        return [str(item) for item in question_chapters if str(item).strip()]
    return [
        str(row["chapter_id"])
        for row in session.execute(
            text("SELECT chapter_id FROM experiment_chapter_bindings WHERE experiment_id = :experiment_id"),
            {"experiment_id": experiment["id"]},
        )
        .mappings()
        .all()
        if str(row.get("chapter_id") or "").strip()
    ]


def _workbench_evidence_prompt(
    *,
    experiment: dict[str, Any],
    prompt: str,
    target_question: dict[str, Any] | None,
    target_points: list[dict[str, str]] | None,
) -> str:
    parts = [
        prompt,
        str(experiment.get("code") or ""),
        str(experiment.get("title") or ""),
        str(experiment.get("summary") or ""),
        str(target_question.get("stem")) if target_question else "",
        " ".join(str(point.get("point_title") or point.get("point_key") or "") for point in (target_points or [])),
    ]
    return " ".join(item for item in parts if item).strip()


def _workbench_query_generator(
    *,
    experiment: dict[str, Any],
    target_points: list[dict[str, str]] | None,
) -> Any:
    point_text = " ".join(str(point.get("point_title") or point.get("point_key") or "") for point in (target_points or [])).strip()
    experiment_text = " ".join(str(experiment.get(key) or "") for key in ("code", "title")).strip()

    def generate(question: str) -> tuple[list[str], dict[str, Any]]:
        queries = _unique_point_keys(
            question,
            f"{experiment_text} {point_text} {question}".strip(),
            f"{experiment_text} {point_text} 实验现象 原理 误区".strip(),
        )[:3]
        return queries or [question], {
            "status": "generated" if len(queries) > 1 else "fallback",
            "provider": "question_workbench",
            "queries": queries,
            "point_count": len(target_points or []),
        }

    return generate


def _retrieve_workbench_context(
    repositories: RepositoryProvider,
    question: str,
    request: AgentAskRequest,
    limit: int,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(item: dict[str, Any]) -> None:
        item_id = str(item.get("id") or item.get("chunk_id") or "")
        if item_id and item_id not in seen:
            seen.add(item_id)
            candidates.append(item)

    for kp_id in request.knowledge_point_ids:
        for chunk in repositories.content.related_chunks_for_kp(kp_id, limit=limit):
            add(chunk)
    source_chunks = repositories.content.source_chunks()
    if request.experiment_id:
        experiment = repositories.content.get_experiment(request.experiment_id)
        chunk_ids = set((experiment or {}).get("source_chunk_ids") or [])
        for chunk in source_chunks:
            if chunk.get("id") in chunk_ids or chunk.get("chunk_id") in chunk_ids:
                add(chunk)
    if request.chapter_id:
        for chunk in source_chunks:
            if chunk.get("chapter_id") == request.chapter_id:
                add(chunk)
    for chunk in source_chunks:
        add(chunk)

    scored: list[dict[str, Any]] = []
    for item in candidates:
        score = keyword_score(
            question,
            item,
            chapter_id=request.chapter_id,
            experiment_id=request.experiment_id,
            knowledge_point_ids=request.knowledge_point_ids,
        )
        if score > 0.04:
            scored.append({**item, "_score": score})
    scored.sort(key=lambda item: item["_score"], reverse=True)
    return scored[:limit]


def _source_refs_from_hybrid_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for chunk in chunks:
        chunk_id = str(chunk.get("chunk_id") or chunk.get("id") or "").strip()
        if chunk_id and chunk_id in seen:
            continue
        if chunk_id:
            seen.add(chunk_id)
        try:
            refs.append(_source_evidence_payload(_source_from_chunk(chunk)))
        except Exception:
            refs.append(
                {
                    "chunk_id": chunk_id,
                    "source_file": chunk.get("source_file"),
                    "page_number": chunk.get("page_number"),
                    "text_preview": " ".join(str(chunk.get("text") or chunk.get("markdown") or chunk.get("caption") or "").split())[:220],
                    "content_type": chunk.get("content_type"),
                    "caption": chunk.get("caption") or chunk.get("title"),
                    "section_path": chunk.get("section_path") if isinstance(chunk.get("section_path"), list) else [],
                }
            )
    return refs


def _load_workbench_evidence_package(
    session: Any,
    *,
    experiment: dict[str, Any],
    prompt: str,
    target_question: dict[str, Any] | None,
    target_points: list[dict[str, str]] | None,
    rag_gate: dict[str, Any] | None,
) -> dict[str, Any]:
    chapter_ids = _workbench_chapter_ids(session, experiment, target_question)
    knowledge_point_ids = list((target_question or {}).get("related_knowledge_point_ids") or [])
    static_package = _static_catalog_node_evidence_package(session, target_points=target_points)
    if _catalog_node_evidence_ready(static_package, target_point_node_ids=_unique_point_node_ids(target_points or [])):
        return static_package
    static_diagnostics = static_package.get("diagnostics") if isinstance(static_package.get("diagnostics"), dict) else {}
    if static_diagnostics.get("freshness_status") == "stale":
        return static_package
    evidence_prompt = _workbench_evidence_prompt(
        experiment=experiment,
        prompt=prompt,
        target_question=target_question,
        target_points=target_points,
    )
    source_refs: list[dict[str, Any]] = []
    trace: dict[str, Any] = {}
    strategy = "hybrid_bge_rag"
    fallback_reason = ""
    if rag_gate and rag_gate.get("healthy"):
        try:
            settings = get_settings()
            repositories = get_repositories()
            request = AgentAskRequest(
                user_role="teacher",
                question=evidence_prompt,
                chapter_id=chapter_ids[0] if chapter_ids else None,
                experiment_id=str(experiment.get("id") or ""),
                point_key=str((target_points or [{}])[0].get("point_key") or "") or None,
                point_node_id=_point_node_id((target_points or [{}])[0]),
                knowledge_point_ids=[str(item) for item in knowledge_point_ids if str(item).strip()],
                allow_progress_lookup=False,
                allow_rag_lookup=True,
                max_answer_chars=0,
            )
            hybrid_result = retrieve_hybrid_context(
                repositories=repositories,
                question=evidence_prompt,
                request=request,
                settings=settings,
                legacy_retrieve=lambda lookup_query, lookup_limit: _retrieve_workbench_context(
                    repositories,
                    lookup_query,
                    request,
                    limit=lookup_limit,
                ),
                query_generator=_workbench_query_generator(experiment=experiment, target_points=target_points),
                limit=max(1, settings.rag_final_top_k),
            )
            trace = hybrid_result.trace
            source_refs = _source_refs_from_hybrid_chunks(hybrid_result.chunks)
            if not source_refs:
                fallback_reason = "hybrid_empty"
        except Exception as exc:
            fallback_reason = f"{exc.__class__.__name__}: {str(exc)[:160]}"
    else:
        strategy = "dynamic_rag_unavailable"
        fallback_reason = "rag_gate_unhealthy"

    return _catalog_node_evidence_package(
        source_refs=source_refs,
        target_points=target_points,
        source_mode="dynamic_rag_catalog_node_evidence" if source_refs else strategy,
        freshness_status="fresh" if source_refs else "missing",
        diagnostics={
            "rag_gate": rag_gate or {},
            "rag_trace": trace,
            "source_strategy": "catalog_node_evidence",
            "dynamic_source_strategy": trace.get("mode") or strategy,
            "fallback_reason": fallback_reason,
            "requires_catalog_node_evidence": True,
            "catalog_node_evidence_ready": bool(source_refs),
            "chapter_ids": chapter_ids,
            "knowledge_point_ids": knowledge_point_ids,
            "target_point_keys": [point.get("point_key") for point in (target_points or []) if point.get("point_key")],
            "target_point_node_ids": _unique_point_node_ids(target_points or []),
            "static_evidence_diagnostics": static_diagnostics,
            "evidence_status": "fresh" if source_refs else "missing",
            "freshness_status": "fresh" if source_refs else "missing",
        },
    )


def _create_or_reopen_workbench_session(
    session: Any,
    *,
    request: WorkbenchSessionRequest,
    user_id: str,
    rag_gate: dict[str, Any],
) -> str:
    experiment = _ensure_experiment(session, request.experiment_id)
    target_question = None
    if request.mode == "repair":
        if not request.question_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="question_id is required for repair workbench")
        target_question = _load_question_for_workbench(session, request.question_id)
        if target_question.get("experiment_id") != request.experiment_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question does not belong to experiment")

    points = _experiment_video_points(experiment, _list_experiment_video_resources(request.experiment_id))
    requested_point_keys = _unique_point_keys(request.point_keys, request.point_key, request.point_node_ids, request.point_node_id)
    selected_points = _select_suggestion_points(
        points=points,
        point_keys=requested_point_keys,
        target_question=target_question,
    )
    selected_points = _attach_catalog_point_nodes(session, experiment_id=request.experiment_id, points=selected_points)
    selected_point = selected_points[0] if selected_points else None
    point_key = selected_point.get("point_key") if selected_point else request.point_key
    point_node_id = _point_node_id(selected_point) or str(request.point_node_id or "").strip()
    target_point_node_ids = _unique_point_node_ids(selected_points, point_node_id)
    target_canonical_point_ids = [
        item
        for item in dict.fromkeys(_canonical_point_id(point) for point in selected_points).keys()
        if item
    ]
    if not target_point_node_ids:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Select a catalog point node before opening the AI question workbench.",
        )
    params = {
        "mode": request.mode,
        "experiment_id": request.experiment_id,
        "question_id": request.question_id,
        "point_key": point_key or "",
        "created_by": user_id,
    }
    if request.mode == "repair":
        existing = (
            session.execute(
                text(
                    """
                    SELECT id
                    FROM experiment_question_workbench_sessions
                    WHERE mode = 'repair'
                      AND question_id = CAST(:question_id AS uuid)
                      AND status = 'open'
                      AND created_by = CAST(:created_by AS uuid)
                    ORDER BY updated_at DESC
                    LIMIT 1
                    """
                ),
                params,
            )
            .mappings()
            .first()
        )
    else:
        existing = (
            session.execute(
                text(
                    """
                    SELECT id
                    FROM experiment_question_workbench_sessions
                    WHERE mode = 'create'
                      AND experiment_id = :experiment_id
                      AND COALESCE(point_key, '') = :point_key
                      AND status = 'open'
                      AND created_by = CAST(:created_by AS uuid)
                    ORDER BY updated_at DESC
                    LIMIT 1
                    """
                ),
                params,
            )
            .mappings()
            .first()
        )
    if existing:
        return str(existing["id"])

    initial_prompt = str(target_question.get("stem") or "") if target_question else str(experiment.get("title") or "")
    evidence_package = _load_workbench_evidence_package(
        session,
        experiment=experiment,
        prompt=initial_prompt,
        target_question=target_question,
        target_points=selected_points,
        rag_gate=rag_gate,
    )
    source_refs = list(evidence_package.get("source_refs") or [])
    if not source_refs:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="No usable evidence was found for this experiment and point context; AI question workbench is blocked.",
        )
    if not _catalog_node_evidence_ready(evidence_package, target_point_node_ids=target_point_node_ids):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=CATALOG_NODE_EVIDENCE_REQUIRED_DETAIL,
        )
    coverage = _question_coverage_for_context(session, request.experiment_id, point_key, point_node_id)
    teacher_point_content = _teacher_point_content_context(session, request.experiment_id, point_key, point_node_id)
    context = _workbench_context(
        mode=request.mode,
        experiment=experiment,
        point=selected_point,
        target_question=target_question,
        source_refs=source_refs,
        target_points=selected_points,
        rag_gate=rag_gate,
        evidence_package=evidence_package,
        coverage=coverage,
        teacher_point_content=teacher_point_content,
    )
    session_id = str(
        session.execute(
            text(
                """
                INSERT INTO experiment_question_workbench_sessions (
                  mode, experiment_id, point_key, question_id, original_question_snapshot,
                  context_snapshot, point_node_ids, status, created_by
                )
                VALUES (
                  :mode, :experiment_id, :point_key, CAST(:question_id AS uuid),
                  CAST(:original_question_snapshot AS jsonb),
                  CAST(:context_snapshot AS jsonb), CAST(:point_node_ids AS jsonb), 'open', CAST(:created_by AS uuid)
                )
                RETURNING id
                """
            ),
            {
                **params,
                "point_key": point_key,
                "point_node_ids": _json_array(target_point_node_ids),
                "original_question_snapshot": _json(_question_snapshot(target_question)),
                "context_snapshot": _json(context),
            },
        ).scalar_one()
    )
    return session_id


def _insert_workbench_turn(
    session: Any,
    *,
    session_id: str,
    role: str,
    content: str,
    provider: str | None = None,
    model: str | None = None,
    error_state: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return dict(
        session.execute(
            text(
                """
                INSERT INTO experiment_question_workbench_turns (
                  session_id, role, content, provider, model, error_state, metadata
                )
                VALUES (
                  CAST(:session_id AS uuid), :role, :content, :provider, :model,
                  CAST(:error_state AS jsonb), CAST(:metadata AS jsonb)
                )
                RETURNING *
                """
            ),
            {
                "session_id": session_id,
                "role": role,
                "content": content,
                "provider": provider,
                "model": model,
                "error_state": _json(error_state) if error_state is not None else None,
                "metadata": _json(metadata or {}),
            },
        )
        .mappings()
        .one()
    )


def _workbench_candidate_validation_errors(
    payload: dict[str, Any],
    *,
    session_id: str,
    turn_id: str,
) -> list[str]:
    errors: list[str] = []
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    point_node_ids = (
        payload.get("source_placement_node_ids")
        or payload.get("primary_point_node_ids")
        or metadata.get("source_placement_node_ids")
        or metadata.get("primary_point_node_ids")
        or []
    )
    canonical_point_ids = (
        payload.get("primary_canonical_point_ids")
        or metadata.get("primary_canonical_point_ids")
        or []
    )
    normalized_point_node_ids = _unique_point_node_ids(point_node_ids)
    if not normalized_point_node_ids and not canonical_point_ids:
        errors.append("canonical point ids or source placement node ids are required")
    source_audit = metadata.get("source_audit") if isinstance(metadata, dict) else None
    if not isinstance(source_audit, dict):
        errors.append("source_audit is required")
    elif not question_payload_has_catalog_evidence_lineage(payload, target_point_node_ids=normalized_point_node_ids):
        errors.append("catalog-node evidence lineage is required")
    if payload.get("question_type") == "single_choice":
        option_links = metadata.get("option_links") if isinstance(metadata, dict) else []
        if not isinstance(option_links, list) or not option_links:
            errors.append("single_choice option_links are required")
    lineage = metadata.get("review_lineage") if isinstance(metadata, dict) else None
    if not isinstance(lineage, dict) or lineage.get("workbench_session_id") != session_id or lineage.get("workbench_turn_id") != turn_id:
        errors.append("workbench lineage is required")
    return errors


def _record_workbench_generation_failure(
    session: Any,
    *,
    session_id: str,
    user_turn: dict[str, Any],
    exc: Exception,
) -> dict[str, Any]:
    assistant_turn = _insert_workbench_turn(
        session,
        session_id=session_id,
        role="assistant",
        content="AI 建议生成失败，已保留本轮提示。请调整提示或稍后重试。",
        error_state={"message": str(exc), "type": exc.__class__.__name__},
        metadata={"user_turn_id": str(user_turn["id"])},
    )
    session.execute(
        text("UPDATE experiment_question_workbench_sessions SET updated_at = now() WHERE id = CAST(:id AS uuid)"),
        {"id": session_id},
    )
    return assistant_turn


def _workbench_session_response(session: Any, session_id: str) -> dict[str, Any]:
    row = (
        session.execute(
            text(
                """
                SELECT s.*, fe.code AS experiment_code, fe.title AS experiment_title
                FROM experiment_question_workbench_sessions s
                JOIN formal_experiments fe ON fe.id = s.experiment_id
                WHERE s.id = CAST(:id AS uuid)
                """
            ),
            {"id": session_id},
        )
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workbench session not found")
    turns = [
        dict(turn)
        for turn in session.execute(
            text(
                """
                SELECT *
                FROM experiment_question_workbench_turns
                WHERE session_id = CAST(:id AS uuid)
                ORDER BY created_at ASC
                """
            ),
            {"id": session_id},
        )
        .mappings()
        .all()
    ]
    candidates = [
        dict(candidate)
        for candidate in session.execute(
            text(
                """
                SELECT c.*, d.status AS draft_status, d.validation_errors AS draft_validation_errors
                FROM experiment_question_workbench_candidates c
                LEFT JOIN experiment_question_drafts d ON d.id = c.draft_id
                WHERE c.session_id = CAST(:id AS uuid)
                ORDER BY c.created_at DESC
                """
            ),
            {"id": session_id},
        )
        .mappings()
        .all()
    ]
    response = dict(row)
    response["turns"] = turns
    response["candidates"] = candidates
    return response


def create_question_workbench_session(*, payload: WorkbenchSessionRequest, user: Any) -> dict[str, Any]:
    if not ai_feature_enabled("question_bank_assistant"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Question bank assistant is disabled")
    rag_gate = _ensure_question_workbench_rag_ready()
    with db_session() as session:
        session_id = _create_or_reopen_workbench_session(session, request=payload, user_id=user.id, rag_gate=rag_gate)
        return _workbench_session_response(session, session_id)


def get_question_workbench_session(*, session_id: str) -> dict[str, Any]:
    with db_session() as session:
        return _workbench_session_response(session, session_id)


def send_question_workbench_message(*, payload: WorkbenchMessageRequest, session_id: str, user: Any) -> dict[str, Any]:
    if not ai_feature_enabled("question_bank_assistant"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Question bank assistant is disabled")
    invalid_types = [item for item in payload.question_types if item not in OBJECTIVE_TYPES]
    if invalid_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported question types: {invalid_types}")

    with db_session() as session:
        workbench = (
            session.execute(
                text("SELECT * FROM experiment_question_workbench_sessions WHERE id = CAST(:id AS uuid)"),
                {"id": session_id},
            )
            .mappings()
            .first()
        )
        if not workbench:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workbench session not found")
        if workbench["status"] != "open":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workbench session is not open")

        workbench = dict(workbench)
        experiment = _ensure_experiment(session, workbench["experiment_id"])
        context_snapshot = workbench.get("context_snapshot") if isinstance(workbench.get("context_snapshot"), dict) else {}
        target_question = (
            dict(workbench.get("original_question_snapshot") or {})
            if workbench.get("mode") == "repair"
            else None
        )
        selected_point = context_snapshot.get("selected_point") if isinstance(context_snapshot.get("selected_point"), dict) else None
        raw_target_points = context_snapshot.get("target_points") if isinstance(context_snapshot.get("target_points"), list) else []
        target_points = [
            {
                "point_key": str(point.get("point_key") or "").strip(),
                "point_title": str(point.get("point_title") or point.get("point_key") or "").strip(),
                "point_node_id": str(point.get("point_node_id") or point.get("point_id") or point.get("node_id") or "").strip(),
                "source_placement_node_id": str(
                    point.get("source_placement_node_id")
                    or point.get("placement_node_id")
                    or point.get("point_node_id")
                    or point.get("point_id")
                    or point.get("node_id")
                    or ""
                ).strip(),
                "canonical_point_id": str(point.get("canonical_point_id") or "").strip(),
            }
            for point in raw_target_points
            if isinstance(point, dict) and (point.get("point_key") or point.get("point_title") or point.get("point_node_id"))
        ]
        if not target_points and selected_point:
            target_points = [selected_point]
        target_point_keys = _unique_point_keys(
            context_snapshot.get("target_point_keys"),
            [point.get("point_key") for point in target_points],
            workbench.get("point_key"),
        )
        target_point_node_ids = _unique_point_node_ids(
            context_snapshot.get("target_point_node_ids"),
            context_snapshot.get("source_placement_node_ids"),
            workbench.get("point_node_ids") if isinstance(workbench.get("point_node_ids"), list) else [],
            target_points,
        )
        if not target_points and target_point_keys:
            target_points = [{"point_key": key, "point_title": key} for key in target_point_keys]
        if target_points:
            target_points = _attach_catalog_point_nodes(session, experiment_id=str(workbench["experiment_id"]), points=target_points)
            target_point_node_ids = _unique_point_node_ids(target_point_node_ids, target_points)
        target_canonical_point_ids = [
            item
            for item in dict.fromkeys(
                [
                    *(context_snapshot.get("target_canonical_point_ids") or []),
                    *[_canonical_point_id(point) for point in target_points],
                ]
            ).keys()
            if item
        ]
        selected_point = selected_point or (target_points[0] if target_points else None)

        user_turn = _insert_workbench_turn(
            session,
            session_id=session_id,
            role="user",
            content=payload.prompt,
            metadata={
                "question_types": payload.question_types,
                "count": payload.count,
                "point_keys": target_point_keys,
                "point_node_ids": target_point_node_ids,
                "source_placement_node_ids": target_point_node_ids,
                "canonical_point_ids": target_canonical_point_ids,
            },
        )
        if not target_point_node_ids:
            message = "未选择新版目录点位，AI 出题或修题意见已阻止。"
            _insert_workbench_turn(
                session,
                session_id=session_id,
                role="assistant",
                content=message,
                error_state={"type": "CATALOG_POINT_MISSING", "message": message},
                metadata={"user_turn_id": str(user_turn["id"])},
            )
            session.execute(
                text(
                    """
                    UPDATE experiment_question_workbench_sessions
                    SET context_snapshot = CAST(:context_snapshot AS jsonb), updated_at = now()
                    WHERE id = CAST(:id AS uuid)
                    """
                ),
                {
                    "id": session_id,
                    "context_snapshot": _json(
                        {
                            **context_snapshot,
                            "target_points": target_points,
                            "target_point_keys": target_point_keys,
                            "target_point_node_ids": [],
                            "source_placement_node_ids": [],
                            "target_canonical_point_ids": target_canonical_point_ids,
                            "last_prompt": payload.prompt,
                        }
                    ),
                },
            )
            return _workbench_session_response(session, session_id)

        rag_gate = _question_workbench_rag_gate()
        if not rag_gate.get("healthy"):
            _insert_workbench_turn(
                session,
                session_id=session_id,
                role="assistant",
                content=str(rag_gate.get("message") or "RAG runtime is not ready; generation is blocked."),
                error_state={
                    "type": "RAG_GATE_BLOCKED",
                    "message": str(rag_gate.get("message") or ""),
                    "reason_code": str(rag_gate.get("reason_code") or ""),
                },
                metadata={"user_turn_id": str(user_turn["id"]), "rag_gate": rag_gate},
            )
            session.execute(
                text(
                    """
                    UPDATE experiment_question_workbench_sessions
                    SET context_snapshot = CAST(:context_snapshot AS jsonb), updated_at = now()
                    WHERE id = CAST(:id AS uuid)
                    """
                ),
                {
                    "id": session_id,
                    "context_snapshot": _json({**context_snapshot, "rag_gate": rag_gate, "last_prompt": payload.prompt}),
                },
            )
            return _workbench_session_response(session, session_id)

        evidence_package = _load_workbench_evidence_package(
            session,
            experiment=experiment,
            prompt=payload.prompt,
            target_question=target_question,
            target_points=target_points,
            rag_gate=rag_gate,
        )
        source_refs = list(evidence_package.get("source_refs") or [])
        if not source_refs or not _catalog_node_evidence_ready(evidence_package, target_point_node_ids=target_point_node_ids):
            message = "缺少重新生成的目录点位证据，AI 出题或修题意见已阻止。"
            _insert_workbench_turn(
                session,
                session_id=session_id,
                role="assistant",
                content=message,
                error_state={"type": "CATALOG_NODE_EVIDENCE_MISSING", "message": message},
                metadata={"user_turn_id": str(user_turn["id"]), "rag_gate": rag_gate},
            )
            session.execute(
                text(
                    """
                    UPDATE experiment_question_workbench_sessions
                    SET context_snapshot = CAST(:context_snapshot AS jsonb), updated_at = now()
                    WHERE id = CAST(:id AS uuid)
                    """
                ),
                {
                    "id": session_id,
                    "context_snapshot": _json(
                        {
                            **context_snapshot,
                            "target_points": target_points,
                            "target_point_keys": target_point_keys,
                            "target_point_node_ids": target_point_node_ids,
                            "source_placement_node_ids": target_point_node_ids,
                            "target_canonical_point_ids": target_canonical_point_ids,
                            "rag_gate": rag_gate,
                            "evidence_package": {
                                "mode": evidence_package.get("mode") or "hybrid_bge_rag",
                                "source_refs": source_refs,
                                "source_count": len(source_refs),
                                "diagnostics": evidence_package.get("diagnostics") or {"rag_gate": rag_gate},
                            },
                            "last_prompt": payload.prompt,
                        }
                    ),
                },
            )
            return _workbench_session_response(session, session_id)

        point_contexts = attach_evidence_to_point_contexts(
            catalog_point_generation_contexts(session, target_points=target_points),
            source_refs=source_refs,
        )
        context_snapshot = {
            **context_snapshot,
            "selected_point": selected_point,
            "target_points": target_points,
            "target_point_keys": target_point_keys,
            "target_point_node_ids": target_point_node_ids,
            "source_placement_node_ids": target_point_node_ids,
            "target_canonical_point_ids": target_canonical_point_ids,
            "source_refs": source_refs,
            "rag_gate": rag_gate,
            "evidence_package": evidence_package,
            "catalog_point_contexts": point_contexts,
            "teacher_point_content": _teacher_point_content_context(
                session,
                str(experiment.get("id") or context_snapshot.get("experiment", {}).get("id") or ""),
                target_point_keys[0] if target_point_keys else None,
                target_point_node_ids[0] if target_point_node_ids else None,
            ),
            "source_boundaries": {
                "teacher_point_content": "student_page_context_only",
                "catalog_node_evidence": "required_fresh_catalog_node_evidence",
                "supplemental_rag_evidence": evidence_package.get("mode") or "hybrid_bge_rag",
            },
            "last_prompt": payload.prompt,
        }
        session.execute(
            text(
                """
                UPDATE experiment_question_workbench_sessions
                SET context_snapshot = CAST(:context_snapshot AS jsonb), updated_at = now()
                WHERE id = CAST(:id AS uuid)
                """
            ),
            {"id": session_id, "context_snapshot": _json(context_snapshot)},
        )
        ai_settings = effective_ai_settings(get_settings())
        suggestion_request = PointAwareSuggestionRequest(
            intent="repair_question" if workbench["mode"] == "repair" else "add_questions",
            experiment_id=workbench["experiment_id"],
            prompt=payload.prompt,
            question_id=str(workbench.get("question_id")) if workbench.get("question_id") else None,
            point_key=str(workbench.get("point_key") or "") or None,
            point_keys=target_point_keys,
            point_node_id=target_point_node_ids[0] if target_point_node_ids else None,
            point_node_ids=target_point_node_ids,
            question_types=payload.question_types,
            count=payload.count,
            difficulty=payload.difficulty,
        )
        try:
            generated = _try_openai_point_aware_suggestions(
                request=suggestion_request,
                experiment=experiment,
                point=selected_point,
                target_question=target_question,
                source_refs=source_refs,
                point_contexts=point_contexts,
            )
            mode = "openai_sdk" if generated else "local_template"
            if not generated:
                generated = _local_point_aware_suggestions(
                    request=suggestion_request,
                    experiment=experiment,
                    point=selected_point,
                    target_question=target_question,
                )
            assistant_turn = _insert_workbench_turn(
                session,
                session_id=session_id,
                role="assistant",
                content=f"已生成 {min(len(generated), payload.count)} 条候选，可继续追问或发布通过校验的版本。",
                provider="openai" if mode == "openai_sdk" else "local",
                model=ai_settings.agent_llm_model or os.getenv("OPENAI_MODEL", ""),
                metadata={"mode": mode, "source_ref_count": len(source_refs), "user_turn_id": str(user_turn["id"])},
            )
            generation_id = str(
                session.execute(
                    text(
                        """
                        INSERT INTO experiment_question_generations (
                          experiment_id, prompt, question_types, difficulty, requested_count,
                          provider, model, mode, rag_sources, warning, status, created_by, metadata
                        )
                        VALUES (
                          :experiment_id, :prompt, :question_types, :difficulty, :requested_count,
                          :provider, :model, :mode, CAST(:rag_sources AS jsonb),
                          :warning, 'draft', CAST(:created_by AS uuid), CAST(:metadata AS jsonb)
                        )
                        RETURNING id
                        """
                    ),
                    {
                        "experiment_id": workbench["experiment_id"],
                        "prompt": payload.prompt,
                        "question_types": payload.question_types,
                        "difficulty": payload.difficulty,
                        "requested_count": payload.count,
                        "provider": "openai" if mode == "openai_sdk" else "local",
                        "model": ai_settings.agent_llm_model or os.getenv("OPENAI_MODEL", ""),
                        "mode": mode,
                        "rag_sources": _json_array(source_refs),
                        "warning": "" if source_refs else "No source refs found; teacher review is required before publication.",
                        "created_by": user.id,
                        "metadata": _json(
                            {
                                "workbench_session_id": session_id,
                                "workbench_user_turn_id": str(user_turn["id"]),
                                "workbench_assistant_turn_id": str(assistant_turn["id"]),
                                "intent": suggestion_request.intent,
                                "point_key": selected_point.get("point_key") if selected_point else None,
                                "point_keys": target_point_keys,
                                "point_node_id": _point_node_id(selected_point),
                                "point_node_ids": target_point_node_ids,
                                "source_placement_node_ids": target_point_node_ids,
                                "canonical_point_id": _canonical_point_id(selected_point),
                                "primary_canonical_point_ids": target_canonical_point_ids,
                                "catalog_point_contexts": point_contexts,
                                "question_id": suggestion_request.question_id,
                                "rag_gate": rag_gate,
                            }
                        ),
                    },
                ).scalar_one()
            )
            for index, row in enumerate(generated[: payload.count]):
                row_payload = _with_point_aware_metadata(
                    row={**row, "status": "draft", "difficulty": row.get("difficulty") or payload.difficulty or "basic"},
                    request=suggestion_request,
                    experiment=experiment,
                    point=selected_point,
                    source_refs=source_refs,
                    target_question=target_question,
                    index=index,
                )
                row_payload = attach_generation_lineage(
                    row_payload,
                    evidence_package=evidence_package,
                    target_points=target_points,
                    generation_id=generation_id,
                )
                metadata = row_payload.get("metadata") if isinstance(row_payload.get("metadata"), dict) else {}
                lineage = metadata.get("review_lineage") if isinstance(metadata.get("review_lineage"), dict) else {}
                metadata["review_lineage"] = {
                    **lineage,
                    "workbench_session_id": session_id,
                    "workbench_user_turn_id": str(user_turn["id"]),
                    "workbench_turn_id": str(assistant_turn["id"]),
                }
                row_payload["metadata"] = metadata
                normalized, errors = _validate_question_payload(row_payload)
                candidate_payload = normalized or row_payload
                errors = [*errors, *_workbench_candidate_validation_errors(candidate_payload, session_id=session_id, turn_id=str(assistant_turn["id"]))]
                draft = dict(
                    session.execute(
                        text(
                            """
                            INSERT INTO experiment_question_drafts (
                              generation_id, experiment_id, payload, validation_errors, status
                            )
                            VALUES (
                              CAST(:generation_id AS uuid), :experiment_id,
                              CAST(:payload AS jsonb), CAST(:errors AS jsonb), 'draft'
                            )
                            RETURNING *
                            """
                        ),
                        {
                            "generation_id": generation_id,
                            "experiment_id": workbench["experiment_id"],
                            "payload": _json(candidate_payload),
                            "errors": _json_array(errors),
                        },
                    )
                    .mappings()
                    .one()
                )
                session.execute(
                    text(
                        """
                        INSERT INTO experiment_question_workbench_candidates (
                          session_id, turn_id, draft_id, payload, validation_errors, status, lineage
                        )
                        VALUES (
                          CAST(:session_id AS uuid), CAST(:turn_id AS uuid), CAST(:draft_id AS uuid),
                          CAST(:payload AS jsonb), CAST(:errors AS jsonb), 'draft', CAST(:lineage AS jsonb)
                        )
                        """
                    ),
                    {
                        "session_id": session_id,
                        "turn_id": str(assistant_turn["id"]),
                        "draft_id": str(draft["id"]),
                        "payload": _json(candidate_payload),
                        "errors": _json_array(errors),
                        "lineage": _json(metadata.get("review_lineage") or {}),
                    },
                )
            session.execute(
                text(
                    """
                    UPDATE experiment_question_workbench_sessions
                    SET context_snapshot = CAST(:context_snapshot AS jsonb), updated_at = now()
                    WHERE id = CAST(:id AS uuid)
                    """
                ),
                {
                    "id": session_id,
                    "context_snapshot": _json(
                        {
                            **context_snapshot,
                            "source_refs": source_refs,
                            "last_prompt": payload.prompt,
                        }
                    ),
                },
            )
        except Exception as exc:
            _record_workbench_generation_failure(
                session,
                session_id=session_id,
                user_turn=user_turn,
                exc=exc,
            )
        return _workbench_session_response(session, session_id)


def reject_question_workbench_candidate(*, candidate_id: str) -> dict[str, Any]:
    with db_session() as session:
        candidate = (
            session.execute(
                text("SELECT * FROM experiment_question_workbench_candidates WHERE id = CAST(:id AS uuid)"),
                {"id": candidate_id},
            )
            .mappings()
            .first()
        )
        if not candidate:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
        candidate = dict(candidate)
        if candidate.get("draft_id"):
            session.execute(
                text("UPDATE experiment_question_drafts SET status = 'rejected', updated_at = now() WHERE id = CAST(:id AS uuid)"),
                {"id": str(candidate["draft_id"])},
            )
        row = (
            session.execute(
                text(
                    """
                    UPDATE experiment_question_workbench_candidates
                    SET status = 'rejected', updated_at = now()
                    WHERE id = CAST(:id AS uuid)
                    RETURNING *
                    """
                ),
                {"id": candidate_id},
            )
            .mappings()
            .one()
        )
    return dict(row)


def publish_question_workbench_candidate(*, candidate_id: str, user: Any) -> dict[str, Any]:
    with db_session() as session:
        candidate = (
            session.execute(
                text(
                    """
                    SELECT c.*, s.experiment_id, s.question_id, d.generation_id
                    FROM experiment_question_workbench_candidates c
                    JOIN experiment_question_workbench_sessions s ON s.id = c.session_id
                    LEFT JOIN experiment_question_drafts d ON d.id = c.draft_id
                    WHERE c.id = CAST(:id AS uuid)
                    """
                ),
                {"id": candidate_id},
            )
            .mappings()
            .first()
        )
        if not candidate:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
        candidate = dict(candidate)
        if candidate["status"] != "draft":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft candidates can be published")
        validation_errors = candidate.get("validation_errors") or []
        if validation_errors:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"errors": validation_errors})
        payload_data = dict(candidate.get("payload") or {})
        metadata = payload_data.get("metadata") if isinstance(payload_data.get("metadata"), dict) else {}
        lineage = metadata.get("review_lineage") if isinstance(metadata.get("review_lineage"), dict) else {}
        metadata["review_lineage"] = {
            **lineage,
            "workbench_candidate_id": candidate_id,
            "published_from_workbench_at": datetime.now(timezone.utc).isoformat(),
        }
        payload_data["metadata"] = metadata
        if not question_payload_has_catalog_evidence_lineage(payload_data):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"errors": ["catalog-node evidence lineage is required before publication"]},
            )
        payload_data["status"] = "published"
        inserted = _insert_question(
            session,
            experiment_id=candidate["experiment_id"],
            payload=payload_data,
            bank_kind="generated",
            actor_user_id=user.id,
            generation_id=str(candidate["generation_id"]) if candidate.get("generation_id") else None,
        )
        if candidate.get("draft_id"):
            session.execute(
                text("UPDATE experiment_question_drafts SET status = 'published', updated_at = now() WHERE id = CAST(:id AS uuid)"),
                {"id": str(candidate["draft_id"])},
            )
        session.execute(
            text(
                """
                UPDATE experiment_question_workbench_candidates
                SET status = 'published',
                    lineage = lineage || CAST(:lineage AS jsonb),
                    updated_at = now()
                WHERE id = CAST(:id AS uuid)
                """
            ),
            {
                "id": candidate_id,
                "lineage": _json({"published_question_id": str(inserted["id"])}),
            },
        )
    return inserted
