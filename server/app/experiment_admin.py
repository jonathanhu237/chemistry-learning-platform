from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import urllib.error
import urllib.request
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, Query, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import text

from server.app.agent import _source_evidence_payload, _source_from_chunk
from server.app.auth import AuthUser, require_roles
from server.app.canonical_evidence import load_evidence_source_refs
from server.app.config import get_settings
from server.app.database import db_session
from server.app.experiment_admin_schemas import (
    DraftUpdateRequest,
    ExperimentChapterBinding,
    ExperimentCreateRequest,
    ExperimentExistingVideoBindRequest,
    ExperimentUpdateRequest,
    ExperimentVideoPointResourceRequest,
    GenerationRequest,
    PointAwareSuggestionRequest,
    QuestionBankAssistantRequest,
    QuestionRequest,
    QuestionUpdateRequest,
    WorkbenchMessageRequest,
    WorkbenchSessionRequest,
)
from server.app.experiment_framework import build_experiment_framework_overview
from server.app.hybrid_rag import retrieve_hybrid_context
from server.app.media import create_media_asset, create_media_binding
from server.app.platform_settings import ai_feature_enabled, effective_ai_settings
from server.app.repositories import RepositoryProvider, get_repositories
from server.app.retrieval import keyword_score
from server.app.schemas import AgentAskRequest

admin_router = APIRouter(prefix="/api/admin", tags=["experiment-admin"])

OBJECTIVE_TYPES = {"single_choice", "true_false", "fill_blank"}
QUESTION_STATUSES = {"draft", "published", "disabled", "archived"}


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=str)


def _json_array(value: Any) -> str:
    return json.dumps(value if value is not None else [], ensure_ascii=False, default=str)


def _dump(model: BaseModel) -> dict[str, Any]:
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()


def _sse_event(event: str, data: dict[str, Any]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


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


def _row_dict(row: Any) -> dict[str, Any]:
    return dict(row) if row else {}


def _ensure_experiment(session: Any, experiment_id: str) -> dict[str, Any]:
    row = (
        session.execute(
            text(
                """
                SELECT id, code, title, title_en, summary, status, display_order, source_refs, metadata
                FROM formal_experiments
                WHERE id = :experiment_id
                """
            ),
            {"experiment_id": experiment_id},
        )
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formal experiment not found")
    return dict(row)


def _candidate_point_key(index: int, title: str) -> str:
    digest = hashlib.sha1(title.strip().encode("utf-8")).hexdigest()[:8]
    return f"candidate-{index + 1}-{digest}"


def _video_candidates(metadata: Any) -> list[str]:
    if not isinstance(metadata, dict):
        return []
    raw_candidates = metadata.get("video_candidates") or []
    if not isinstance(raw_candidates, list):
        return []
    candidates: list[str] = []
    seen: set[str] = set()
    for raw in raw_candidates:
        title = str(raw or "").strip()
        if not title or title in seen:
            continue
        seen.add(title)
        candidates.append(title)
    return candidates


def _experiment_video_points(experiment: dict[str, Any], resources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    by_key: dict[str, dict[str, Any]] = {}
    for index, title in enumerate(_video_candidates(experiment.get("metadata"))):
        point = {
            "point_key": _candidate_point_key(index, title),
            "point_title": title,
            "source": "candidate",
            "resources": [],
            "resource_count": 0,
            "published_count": 0,
        }
        points.append(point)
        by_key[point["point_key"]] = point

    legacy_point: dict[str, Any] | None = None
    for resource in resources:
        point_key = str(resource.get("point_key") or "").strip()
        point_title = str(resource.get("point_title") or "").strip()
        if point_key and point_key not in by_key:
            point = {
                "point_key": point_key,
                "point_title": point_title or str(resource.get("title") or resource.get("media_title") or point_key),
                "source": "stored",
                "resources": [],
                "resource_count": 0,
                "published_count": 0,
            }
            points.append(point)
            by_key[point_key] = point
        elif not point_key:
            if legacy_point is None:
                legacy_point = {
                    "point_key": "legacy-unassigned",
                    "point_title": "Unassigned resources",
                    "source": "legacy",
                    "resources": [],
                    "resource_count": 0,
                    "published_count": 0,
                }
                points.append(legacy_point)
                by_key[legacy_point["point_key"]] = legacy_point
            point_key = legacy_point["point_key"]

        point = by_key.get(point_key)
        if not point:
            continue
        point["resources"].append(resource)
        point["resource_count"] += 1
        if resource.get("binding_status") == "published":
            point["published_count"] += 1

    return points


def _normalize_chapter_ids(chapter_ids: list[Any] | None) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in chapter_ids or []:
        if isinstance(raw, dict):
            chapter_id = str(raw.get("chapter_id") or "").strip()
        else:
            chapter_id = str(raw or "").strip()
        if not chapter_id or chapter_id in seen:
            continue
        seen.add(chapter_id)
        normalized.append(chapter_id)
    return normalized


def _bindings_from_chapter_ids(chapter_ids: list[Any] | None) -> list[ExperimentChapterBinding]:
    return [
        ExperimentChapterBinding(chapter_id=chapter_id, coverage_type="primary", sort_order=index + 1)
        for index, chapter_id in enumerate(_normalize_chapter_ids(chapter_ids))
    ]


def _normalize_binding_payload(
    *,
    chapter_ids: list[Any] | None = None,
    chapter_bindings: list[Any] | None = None,
) -> list[ExperimentChapterBinding]:
    if chapter_ids is not None:
        return _bindings_from_chapter_ids(chapter_ids)
    if chapter_bindings is None:
        return []
    bindings: list[ExperimentChapterBinding] = []
    for index, raw in enumerate(chapter_bindings):
        if isinstance(raw, ExperimentChapterBinding):
            chapter_id = raw.chapter_id
            notes = raw.notes
        elif isinstance(raw, dict):
            chapter_id = str(raw.get("chapter_id") or "").strip()
            notes = raw.get("notes")
        else:
            chapter_id = str(raw or "").strip()
            notes = None
        if not chapter_id:
            continue
        bindings.append(
            ExperimentChapterBinding(
                chapter_id=chapter_id,
                coverage_type="primary",
                notes=notes,
                sort_order=index + 1,
            )
        )
    return _bindings_from_chapter_ids([binding.chapter_id for binding in bindings])


def _new_custom_experiment_identity(session: Any) -> tuple[str, str, int]:
    display_order = int(session.execute(text("SELECT COALESCE(MAX(display_order), 0) + 1 FROM formal_experiments")).scalar_one())
    while True:
        token = uuid.uuid4().hex[:10].upper()
        experiment_id = f"EXP_CUSTOM_{token}"
        code = f"CUSTOM-{token}"
        exists = session.execute(
            text("SELECT 1 FROM formal_experiments WHERE id = :id OR code = :code"),
            {"id": experiment_id, "code": code},
        ).first()
        if not exists:
            return experiment_id, code, display_order


def _teacher_can_access_class(user: AuthUser, class_id: str) -> bool:
    if user.role == "admin":
        return True
    with db_session() as session:
        row = session.execute(
            text(
                """
                SELECT 1
                FROM teacher_classes
                WHERE teacher_user_id = CAST(:teacher_id AS uuid)
                  AND class_id = :class_id
                """
            ),
            {"teacher_id": user.id, "class_id": class_id},
        ).first()
    return row is not None


def _require_class_access(class_id: str, user: AuthUser) -> None:
    if not _teacher_can_access_class(user, class_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No access to this class")


def _experiment_select_sql(where_clause: str = "") -> str:
    return f"""
        SELECT
          fe.id,
          fe.code,
          fe.title,
          fe.title_en,
          fe.summary,
          fe.status,
          fe.display_order,
          fe.source_refs,
          fe.metadata,
          fe.published_at,
          fe.created_at,
          fe.updated_at,
          COALESCE((
            SELECT jsonb_agg(
              jsonb_build_object(
                'chapter_id', ecb.chapter_id,
                'chapter_title', c.chapter_title,
                'chapter_number', c.chapter_number,
                'coverage_type', ecb.coverage_type,
                'notes', ecb.notes,
                'sort_order', ecb.sort_order
              )
              ORDER BY ecb.sort_order, c.chapter_number NULLS LAST, ecb.chapter_id
            )
            FROM experiment_chapter_bindings ecb
            LEFT JOIN chapters c ON c.id = ecb.chapter_id
            WHERE ecb.experiment_id = fe.id
          ), '[]'::jsonb) AS chapter_bindings,
          COALESCE((
            SELECT jsonb_agg(
              jsonb_build_object(
                'binding_id', mb.id,
                'media_id', ma.id,
                'title', COALESCE(mb.title, ma.title),
                'original_file_name', ma.original_file_name,
                'mime_type', ma.mime_type,
                'file_size_bytes', ma.file_size_bytes,
                'thumbnail_relative_path', ma.thumbnail_relative_path,
                'upload_status', ma.upload_status,
                'binding_status', mb.status,
                'point_key', mb.metadata->>'point_key',
                'point_title', mb.metadata->>'point_title',
                'published_at', mb.published_at
              )
              ORDER BY mb.sort_order, mb.created_at
            )
            FROM media_bindings mb
            JOIN media_assets ma ON ma.id = mb.media_asset_id
            WHERE mb.target_type = 'experiment'
              AND mb.target_id = fe.id
              AND mb.status <> 'archived'
          ), '[]'::jsonb) AS media_resources,
          (SELECT COUNT(*) FROM experiment_questions q WHERE q.experiment_id = fe.id AND q.status = 'published') AS published_question_count,
          (SELECT COUNT(*) FROM experiment_questions q WHERE q.experiment_id = fe.id AND q.status = 'draft') AS draft_question_count,
          (SELECT COUNT(*) FROM experiment_question_drafts d WHERE d.experiment_id = fe.id AND d.status = 'draft') AS generated_draft_count
        FROM formal_experiments fe
        {where_clause}
        ORDER BY fe.display_order, fe.code
    """


def _list_experiments(
    *,
    chapter_id: str | None = None,
    status_filter: str | None = None,
    include_archived: bool = False,
    video_status: str | None = None,
    question_status: str | None = None,
) -> list[dict[str, Any]]:
    filters: list[str] = ["COALESCE(fe.metadata->>'archived_by_catalog_seed', 'false') <> 'true'"]
    params: dict[str, Any] = {}
    if chapter_id:
        filters.append(
            """
            EXISTS (
              SELECT 1 FROM experiment_chapter_bindings ecb
              WHERE ecb.experiment_id = fe.id AND ecb.chapter_id = :chapter_id
            )
            """
        )
        params["chapter_id"] = chapter_id
    if status_filter:
        filters.append("fe.status = :status_filter")
        params["status_filter"] = status_filter
    elif not include_archived:
        filters.append("fe.status <> 'archived'")
    if video_status == "none":
        filters.append(
            """
            NOT EXISTS (
              SELECT 1 FROM media_bindings mb
              JOIN media_assets ma ON ma.id = mb.media_asset_id
              WHERE mb.target_type = 'experiment' AND mb.target_id = fe.id AND mb.status <> 'archived'
            )
            """
        )
    elif video_status:
        filters.append(
            """
            EXISTS (
              SELECT 1 FROM media_bindings mb
              JOIN media_assets ma ON ma.id = mb.media_asset_id
              WHERE mb.target_type = 'experiment'
                AND mb.target_id = fe.id
                AND mb.status <> 'archived'
                AND (ma.upload_status = :video_status OR mb.status = :video_status)
            )
            """
        )
        params["video_status"] = video_status
    if question_status == "empty":
        filters.append("NOT EXISTS (SELECT 1 FROM experiment_questions q WHERE q.experiment_id = fe.id)")
    elif question_status:
        filters.append(
            """
            EXISTS (
              SELECT 1 FROM experiment_questions q
              WHERE q.experiment_id = fe.id AND q.status = :question_status
            )
            """
        )
        params["question_status"] = question_status
    where_clause = "WHERE " + " AND ".join(filters) if filters else ""
    with db_session() as session:
        return [dict(row) for row in session.execute(text(_experiment_select_sql(where_clause)), params).mappings().all()]


def _list_experiment_video_resources(experiment_id: str | None = None) -> list[dict[str, Any]]:
    params: dict[str, Any] = {}
    filters = ["mb.target_type = 'experiment'", "mb.status <> 'archived'"]
    if experiment_id:
        filters.append("mb.target_id = :experiment_id")
        params["experiment_id"] = experiment_id
    with db_session() as session:
        rows = [
            dict(row)
            for row in session.execute(
                text(
                    f"""
                    SELECT mb.id AS binding_id, mb.target_id AS experiment_id, fe.code, fe.title AS experiment_title,
                           mb.title AS binding_title, mb.status AS binding_status, mb.published_at,
                           mb.metadata AS binding_metadata,
                           mb.metadata->>'point_key' AS point_key,
                           mb.metadata->>'point_title' AS point_title,
                           ma.id AS media_id, ma.title AS media_title, ma.original_file_name,
                           ma.mime_type, ma.file_size_bytes, ma.thumbnail_relative_path,
                           ma.upload_status, ma.error_reason,
                           ma.created_at, ma.updated_at
                    FROM media_bindings mb
                    JOIN media_assets ma ON ma.id = mb.media_asset_id
                    LEFT JOIN formal_experiments fe ON fe.id = mb.target_id
                    WHERE {" AND ".join(filters)}
                    ORDER BY mb.sort_order, ma.created_at DESC
                    """
                ),
                params,
            )
            .mappings()
            .all()
        ]
    for row in rows:
        row["title"] = row.get("binding_title") or row.get("media_title") or row.get("original_file_name")
        if not isinstance(row.get("binding_metadata"), dict):
            row["binding_metadata"] = {}
    return rows


def _current_experiment_catalog_count() -> int:
    with db_session() as session:
        return int(
            session.execute(
                text("SELECT COUNT(*) FROM formal_experiments WHERE status <> 'archived'")
            ).scalar_one()
            or 0
        )


@admin_router.get("/experiments")
async def admin_list_experiments(
    chapter_id: str | None = None,
    status_filter: str | None = None,
    include_archived: bool = False,
    video_status: str | None = None,
    question_status: str | None = None,
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    items = _list_experiments(
        chapter_id=chapter_id,
        status_filter=status_filter,
        include_archived=include_archived,
        video_status=video_status,
        question_status=question_status,
    )
    return {
        "items": items,
        "total": len(items),
        "formal_count": _current_experiment_catalog_count(),
        "legacy_fragment_warning": "实验管理以精选目录中的具体实验点为主，不再以 19-1 到 20-3 的大实验单元计数。",
    }


@admin_router.post("/experiments")
async def admin_create_experiment(
    payload: ExperimentCreateRequest,
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    bindings = _bindings_from_chapter_ids(payload.chapter_ids)
    if not bindings:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one chapter binding is required")
    with db_session() as session:
        experiment_id, code, display_order = _new_custom_experiment_identity(session)
        session.execute(
            text(
                """
                INSERT INTO formal_experiments (
                  id, code, title, title_en, summary, status, display_order,
                  source_refs, metadata, published_at, updated_at
                )
                VALUES (
                  :id, :code, :title, NULL, :summary, :status, :display_order,
                  '[]'::jsonb, CAST(:metadata AS jsonb),
                  CASE WHEN :status = 'published' THEN now() ELSE NULL END,
                  now()
                )
                """
            ),
            {
                "id": experiment_id,
                "code": code,
                "title": payload.title,
                "summary": payload.summary,
                "status": payload.status,
                "display_order": display_order,
                "metadata": _json({"custom": True, "created_by": user.id}),
            },
        )
        _replace_chapter_bindings(session, experiment_id, bindings)
    return await admin_get_experiment(experiment_id, user)


@admin_router.get("/experiments/{experiment_id}")
async def admin_get_experiment(
    experiment_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    with db_session() as session:
        row = session.execute(text(_experiment_select_sql("WHERE fe.id = :experiment_id")), {"experiment_id": experiment_id}).mappings().first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formal experiment not found")
    return dict(row)


@admin_router.patch("/experiments/{experiment_id}")
async def admin_update_experiment(
    payload: ExperimentUpdateRequest,
    experiment_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    data = _dump(payload)
    with db_session() as session:
        _ensure_experiment(session, experiment_id)
        session.execute(
            text(
                """
                UPDATE formal_experiments
                SET title = COALESCE(:title, title),
                    summary = COALESCE(:summary, summary),
                    status = COALESCE(:status, status),
                    published_at = CASE
                      WHEN :status = 'published' THEN COALESCE(published_at, now())
                      WHEN :status IS NULL THEN published_at
                      ELSE NULL
                    END,
                    updated_at = now()
                WHERE id = :experiment_id
                """
            ),
            {
                "experiment_id": experiment_id,
                "title": data.get("title"),
                "summary": data.get("summary"),
                "status": data.get("status"),
            },
        )
        if payload.chapter_ids is not None or payload.chapter_bindings is not None:
            _replace_chapter_bindings(
                session,
                experiment_id,
                _normalize_binding_payload(chapter_ids=payload.chapter_ids, chapter_bindings=payload.chapter_bindings),
            )
    return await admin_get_experiment(experiment_id, user)


@admin_router.put("/experiments/{experiment_id}/chapter-bindings")
async def admin_replace_chapter_bindings(
    bindings: list[Any],
    experiment_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    with db_session() as session:
        _ensure_experiment(session, experiment_id)
        _replace_chapter_bindings(session, experiment_id, _normalize_binding_payload(chapter_bindings=bindings))
    return await admin_get_experiment(experiment_id, user)


def _replace_chapter_bindings(session: Any, experiment_id: str, bindings: list[ExperimentChapterBinding]) -> None:
    if not bindings:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one chapter binding is required")
    session.execute(text("DELETE FROM experiment_chapter_bindings WHERE experiment_id = :experiment_id"), {"experiment_id": experiment_id})
    for index, binding in enumerate(bindings):
        chapter = session.execute(text("SELECT id FROM chapters WHERE id = :chapter_id"), {"chapter_id": binding.chapter_id}).first()
        if not chapter:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Chapter not found: {binding.chapter_id}")
        session.execute(
            text(
                """
                INSERT INTO experiment_chapter_bindings (
                  experiment_id, chapter_id, coverage_type, notes, sort_order, updated_at
                )
                VALUES (
                  :experiment_id, :chapter_id, :coverage_type, :notes, :sort_order, now()
                )
                """
            ),
            {
                "experiment_id": experiment_id,
                "chapter_id": binding.chapter_id,
                "coverage_type": binding.coverage_type,
                "notes": binding.notes,
                "sort_order": binding.sort_order or index + 1,
            },
        )


@admin_router.post("/experiments/{experiment_id}/videos/upload")
async def admin_upload_experiment_video(
    experiment_id: str = Path(min_length=1),
    title: str = Form(...),
    file: UploadFile = File(...),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    with db_session() as session:
        _ensure_experiment(session, experiment_id)
    content = await file.read()
    asset = create_media_asset(
        title=title,
        filename=file.filename or "upload.mp4",
        content=content,
        content_type=file.content_type,
        uploaded_by=user.id,
    )
    binding = create_media_binding(
        media_asset_id=str(asset["id"]),
        target_type="experiment",
        target_id=experiment_id,
        title=title,
        status="draft",
    )
    return {"asset": asset, "binding": binding}


@admin_router.post("/experiments/{experiment_id}/videos/bind")
async def admin_bind_existing_experiment_video(
    payload: ExperimentExistingVideoBindRequest,
    experiment_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    with db_session() as session:
        _ensure_experiment(session, experiment_id)
    return create_media_binding(
        media_asset_id=payload.media_asset_id,
        target_type="experiment",
        target_id=experiment_id,
        title=payload.title,
        status=payload.status,
        metadata={
            key: value
            for key, value in {
                "point_key": payload.point_key,
                "point_title": payload.point_title,
            }.items()
            if value
        },
    )


@admin_router.get("/experiments/{experiment_id}/video-points")
async def admin_get_experiment_video_points(
    experiment_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    with db_session() as session:
        experiment = _ensure_experiment(session, experiment_id)
    resources = _list_experiment_video_resources(experiment_id)
    points = _experiment_video_points(experiment, resources)
    return {
        "experiment": {
            "id": experiment["id"],
            "code": experiment["code"],
            "title": experiment["title"],
            "status": experiment["status"],
        },
        "points": points,
        "total_points": len(points),
        "total_resources": sum(len(point["resources"]) for point in points),
        "published_resources": sum(point["published_count"] for point in points),
    }


@admin_router.post("/experiments/{experiment_id}/video-points/{point_key}/resources")
async def admin_add_experiment_video_point_resource(
    payload: ExperimentVideoPointResourceRequest,
    experiment_id: str = Path(min_length=1),
    point_key: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    with db_session() as session:
        experiment = _ensure_experiment(session, experiment_id)
    existing_resources = _list_experiment_video_resources(experiment_id)
    points = _experiment_video_points(experiment, existing_resources)
    point = next((item for item in points if item["point_key"] == point_key), None)
    if not point or point["source"] == "legacy":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Video point not found")
    return create_media_binding(
        media_asset_id=payload.media_asset_id,
        target_type="experiment",
        target_id=experiment_id,
        title=payload.title or point["point_title"],
        status=payload.status,
        metadata={
            "point_key": point["point_key"],
            "point_title": point["point_title"],
        },
    )


@admin_router.get("/experiment-videos")
async def admin_list_experiment_videos(
    experiment_id: str | None = None,
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    rows = _list_experiment_video_resources(experiment_id)
    return {"items": rows, "total": len(rows)}


def _normalize_answer(question_type: str, answer: Any) -> dict[str, Any]:
    if question_type == "single_choice":
        value = str(answer.get("value") if isinstance(answer, dict) else answer).strip()
        if not value:
            raise ValueError("single_choice answer is required")
        return {"value": value}
    if question_type == "true_false":
        raw = answer.get("value") if isinstance(answer, dict) else answer
        if isinstance(raw, bool):
            value = raw
        else:
            normalized = str(raw).strip().lower()
            if normalized in {"true", "t", "1", "yes", "y", "正确", "对"}:
                value = True
            elif normalized in {"false", "f", "0", "no", "n", "错误", "错"}:
                value = False
            else:
                raise ValueError("true_false answer must be true or false")
        return {"value": value}
    if question_type == "fill_blank":
        raw = answer.get("accepted_answers") if isinstance(answer, dict) else answer
        values = raw if isinstance(raw, list) else [raw]
        accepted = [str(item).strip() for item in values if str(item).strip()]
        if not accepted:
            raise ValueError("fill_blank accepted_answers are required")
        return {"accepted_answers": accepted, "match": "normalized_exact"}
    raise ValueError("unsupported question_type")


def _validate_question_payload(payload: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    errors: list[str] = []
    question_type = str(payload.get("question_type") or "").strip()
    if question_type not in OBJECTIVE_TYPES:
        errors.append("question_type must be one of single_choice, true_false, fill_blank")
    stem = str(payload.get("stem") or "").strip()
    if not stem:
        errors.append("stem is required")
    options = payload.get("options") or []
    if question_type == "single_choice" and len(options) < 2:
        errors.append("single_choice requires at least 2 options")
    try:
        answer = _normalize_answer(question_type, payload.get("answer"))
    except ValueError as exc:
        errors.append(str(exc))
        answer = {}
    if errors:
        return None, errors
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    normalized = {
        "question_type": question_type,
        "stem": stem,
        "options": options,
        "answer": answer,
        "explanation": payload.get("explanation"),
        "difficulty": payload.get("difficulty") or "basic",
        "related_chapter_ids": list(payload.get("related_chapter_ids") or []),
        "related_knowledge_point_ids": list(payload.get("related_knowledge_point_ids") or []),
        "source_chunk_ids": list(payload.get("source_chunk_ids") or []),
        "source_refs": list(payload.get("source_refs") or []),
        "metadata": metadata,
        "status": payload.get("status") or "draft",
    }
    if normalized["status"] not in QUESTION_STATUSES:
        normalized["status"] = "draft"
    return normalized, []


def _ensure_question_bank(session: Any, experiment_id: str, bank_kind: str, actor_user_id: str | None = None) -> str:
    _ensure_experiment(session, experiment_id)
    row = (
        session.execute(
            text(
                """
                INSERT INTO experiment_question_banks (
                  experiment_id, bank_kind, title, status, imported_by, updated_at
                )
                VALUES (
                  :experiment_id, :bank_kind, :title, 'draft', CAST(:actor AS uuid), now()
                )
                ON CONFLICT (experiment_id, bank_kind) DO UPDATE SET
                  updated_at = now()
                RETURNING id
                """
            ),
            {
                "experiment_id": experiment_id,
                "bank_kind": bank_kind,
                "title": {"default": "默认 AI 题库", "generated": "AI 生成题库", "manual": "教师自建题库"}[bank_kind],
                "actor": actor_user_id,
            },
        )
        .mappings()
        .one()
    )
    return str(row["id"])


def _insert_question(
    session: Any,
    *,
    experiment_id: str,
    payload: dict[str, Any],
    bank_kind: str,
    actor_user_id: str | None,
    generation_id: str | None = None,
) -> dict[str, Any]:
    normalized, errors = _validate_question_payload(payload)
    if errors or normalized is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"errors": errors})
    bank_id = _ensure_question_bank(session, experiment_id, bank_kind, actor_user_id)
    row = (
        session.execute(
            text(
                """
                INSERT INTO experiment_questions (
                  bank_id, experiment_id, generation_id, question_type, stem, options, answer,
                  explanation, difficulty, related_chapter_ids, related_knowledge_point_ids,
                  source_chunk_ids, source_refs, status, metadata, created_by, published_by, published_at, updated_at
                )
                VALUES (
                  CAST(:bank_id AS uuid), :experiment_id, CAST(:generation_id AS uuid),
                  :question_type, :stem, CAST(:options AS jsonb), CAST(:answer AS jsonb),
                  :explanation, :difficulty, :related_chapter_ids, :related_knowledge_point_ids,
                  :source_chunk_ids, CAST(:source_refs AS jsonb), :status, CAST(:metadata AS jsonb),
                  CAST(:created_by AS uuid),
                  CASE WHEN :status = 'published' THEN CAST(:created_by AS uuid) ELSE NULL END,
                  CASE WHEN :status = 'published' THEN now() ELSE NULL END,
                  now()
                )
                RETURNING *
                """
            ),
            {
                "bank_id": bank_id,
                "experiment_id": experiment_id,
                "generation_id": generation_id,
                "question_type": normalized["question_type"],
                "stem": normalized["stem"],
                "options": _json_array(normalized["options"]),
                "answer": _json(normalized["answer"]),
                "explanation": normalized["explanation"],
                "difficulty": normalized["difficulty"],
                "related_chapter_ids": normalized["related_chapter_ids"],
                "related_knowledge_point_ids": normalized["related_knowledge_point_ids"],
                "source_chunk_ids": normalized["source_chunk_ids"],
                "source_refs": _json_array(normalized["source_refs"]),
                "status": normalized["status"],
                "metadata": _json(normalized["metadata"]),
                "created_by": actor_user_id,
            },
        )
        .mappings()
        .one()
    )
    if normalized["status"] == "published":
        session.execute(
            text("UPDATE experiment_question_banks SET status = 'published', updated_at = now() WHERE id = CAST(:bank_id AS uuid)"),
            {"bank_id": bank_id},
        )
    return dict(row)


CURRENT_BANK_STATUSES = {"draft", "published", "disabled"}
PUBLISHED_RESOURCE_STATUSES = {"published", "ready"}
QUESTION_STATUS_ORDER = ("draft", "published", "disabled", "archived")
QUESTION_TYPE_ORDER = ("single_choice", "true_false", "fill_blank")
MEDIA_UPLOAD_STATUS_ORDER = ("ready", "processing", "failed")
MEDIA_BINDING_STATUS_ORDER = ("draft", "published", "archived")
CLASS_STATUS_ORDER = ("active", "archived", "disabled")
ROSTER_STATUS_ORDER = ("pending", "active", "disabled")
THEORY_AREA_BY_CHAPTER = {
    "CH13": ("p", "p 区元素"),
    "CH14": ("p", "p 区元素"),
    "CH15": ("p", "p 区元素"),
    "CH16": ("p", "p 区元素"),
    "CH17": ("p", "p 区元素"),
    "CH18": ("s", "s 区元素"),
    "CH19": ("ds", "ds 区元素"),
    "CH20": ("d", "d 区元素"),
    "CH21": ("f", "f 区元素"),
    "CH22": ("integrated", "氢和稀有气体"),
}
GENERAL_RESOURCE_AREA_ID = "general"
GENERAL_RESOURCE_AREA_NAME = "通识资源"


def _zero_counts(keys: tuple[str, ...] | list[str] | set[str]) -> dict[str, int]:
    return {str(key): 0 for key in keys}


def _counts_from_sets(value_sets: dict[str, set[str]], keys: tuple[str, ...]) -> dict[str, int]:
    counts = _zero_counts(keys)
    for key, values in value_sets.items():
        counts[str(key)] = len(values)
    return counts


def _db_table_exists(session: Any, table_name: str) -> bool:
    row = session.execute(text("SELECT to_regclass(:name) AS table_name"), {"name": f"public.{table_name}"}).mappings().first()
    return bool(row and row.get("table_name"))


def _db_count_rows(session: Any, table_name: str, where_sql: str = "", params: dict[str, Any] | None = None) -> int:
    if not _db_table_exists(session, table_name):
        return 0
    sql = f"SELECT COUNT(*) AS count FROM {table_name}"
    if where_sql:
        sql += f" WHERE {where_sql}"
    row = session.execute(text(sql), params or {}).mappings().first()
    return int(row["count"] if row else 0)


def _db_count_by_column(
    session: Any,
    *,
    table_name: str,
    column_name: str,
    keys: tuple[str, ...],
    where_sql: str = "",
    params: dict[str, Any] | None = None,
) -> dict[str, int]:
    counts = _zero_counts(keys)
    if not _db_table_exists(session, table_name):
        return counts
    sql = f"""
        SELECT COALESCE({column_name}, 'unknown') AS key, COUNT(*) AS count
        FROM {table_name}
    """
    if where_sql:
        sql += f" WHERE {where_sql}"
    sql += " GROUP BY COALESCE({column_name}, 'unknown')".format(column_name=column_name)
    for row in session.execute(text(sql), params or {}).mappings().all():
        counts[str(row["key"])] = int(row["count"])
    return counts


def _load_learning_resource_dashboard_stats(session: Any) -> dict[str, Any]:
    media_asset_status_counts = _db_count_by_column(
        session,
        table_name="media_assets",
        column_name="upload_status",
        keys=MEDIA_UPLOAD_STATUS_ORDER,
    )
    media_binding_status_counts = _db_count_by_column(
        session,
        table_name="media_bindings",
        column_name="status",
        keys=MEDIA_BINDING_STATUS_ORDER,
        where_sql="target_type = 'experiment'",
    )
    class_status_counts = _db_count_by_column(
        session,
        table_name="classes",
        column_name="status",
        keys=CLASS_STATUS_ORDER,
    )
    roster_status_counts = _db_count_by_column(
        session,
        table_name="roster_entries",
        column_name="status",
        keys=ROSTER_STATUS_ORDER,
    )
    student_status_counts = _db_count_by_column(
        session,
        table_name="students",
        column_name="status",
        keys=ROSTER_STATUS_ORDER,
    )
    return {
        "rag": {
            "source_document_count": _db_count_rows(session, "source_documents"),
            "source_chunk_count": _db_count_rows(session, "source_chunks"),
            "embedding_count": _db_count_rows(session, "chunk_embeddings"),
        },
        "media": {
            "asset_count": _db_count_rows(session, "media_assets"),
            "binding_count": _db_count_rows(session, "media_bindings", "target_type = 'experiment'"),
            "asset_status_counts": media_asset_status_counts,
            "binding_status_counts": media_binding_status_counts,
            "ready_asset_count": int(media_asset_status_counts.get("ready", 0)),
            "published_binding_count": int(media_binding_status_counts.get("published", 0)),
        },
        "classes_students": {
            "class_count": _db_count_rows(session, "classes"),
            "class_status_counts": class_status_counts,
            "roster_count": _db_count_rows(session, "roster_entries"),
            "roster_status_counts": roster_status_counts,
            "student_account_count": _db_count_rows(session, "students"),
            "student_status_counts": student_status_counts,
            "active_student_count": int(student_status_counts.get("active", 0)),
        },
    }


def _strip_chapter_number(title: str) -> str:
    return re.sub(r"^第\s*\d+\s*章\s*", "", title).strip()


def _format_numbered_chapter_title(title: str, number: Any = None) -> str:
    clean = str(title or "").strip()
    if not clean:
        return ""
    if re.match(r"^第\s*\d+\s*章\s*", clean):
        return re.sub(r"^第\s*(\d+)\s*章\s*", r"第 \1 章 ", clean)
    if number:
        return f"第 {number} 章 {clean}"
    return clean


def _is_general_learning_resource(chapter: dict[str, Any]) -> bool:
    chapter_id = str(chapter.get("chapter_id") or "")
    if chapter_id == "CH00":
        return True
    text_value = " ".join(str(chapter.get(key) or "") for key in ("chapter_title", "area_id", "source_label"))
    return any(keyword in text_value for keyword in ("无机化学综合", "通识", "跨章节", "未标章节"))


def _learning_resource_group_display(chapter: dict[str, Any]) -> dict[str, Any]:
    chapter_id = str(chapter.get("chapter_id") or chapter.get("id") or "")
    raw_title = str(chapter.get("chapter_title") or chapter_id or "").strip()
    if _is_general_learning_resource({**chapter, "chapter_id": chapter_id}):
        title = _strip_chapter_number(raw_title) or "通识/跨章节"
        return {
            "id": f"general:{chapter_id}",
            "kind": "general",
            "chapter_id": chapter_id,
            "chapter_number": None,
            "title": title,
            "subtitle": GENERAL_RESOURCE_AREA_NAME,
            "area_id": GENERAL_RESOURCE_AREA_ID,
            "area_name": GENERAL_RESOURCE_AREA_NAME,
        }
    area_id, area_name = THEORY_AREA_BY_CHAPTER.get(chapter_id, ("other", str(chapter.get("element_area") or "其他资源")))
    return {
        "id": f"chapter:{chapter_id}",
        "kind": "chapter",
        "chapter_id": chapter_id,
        "chapter_number": chapter.get("chapter_number"),
        "title": _format_numbered_chapter_title(raw_title, chapter.get("chapter_number")) or chapter_id,
        "subtitle": area_name,
        "area_id": area_id,
        "area_name": area_name,
    }


def _chapter_sort_key(chapter: dict[str, Any]) -> tuple[int, int, str]:
    display = _learning_resource_group_display(chapter)
    return (
        1 if display["kind"] == "general" else 0,
        int(display.get("chapter_number") or 999),
        str(display.get("chapter_id") or ""),
    )


def _chapter_display_title(chapter: dict[str, Any]) -> str:
    title = str(chapter.get("chapter_title") or "").strip()
    number = chapter.get("chapter_number")
    if number and not title.startswith("第"):
        return f"第 {number} 章 {title}".strip()
    return title or str(chapter.get("chapter_id") or "")


def _resolve_question_chapter_ids(question: dict[str, Any], bindings_by_experiment: dict[str, list[str]]) -> list[str]:
    direct = [str(item) for item in question.get("related_chapter_ids") or [] if str(item).strip()]
    if direct:
        return direct
    return list(bindings_by_experiment.get(str(question.get("experiment_id") or ""), []))


def _summarize_question_bank_chapters(
    chapters: list[dict[str, Any]],
    questions: list[dict[str, Any]],
    bindings_by_experiment: dict[str, list[str]],
) -> list[dict[str, Any]]:
    summaries: dict[str, dict[str, Any]] = {}
    for chapter in chapters:
        chapter_id = str(chapter.get("chapter_id") or chapter.get("id") or "")
        if not chapter_id:
            continue
        summaries[chapter_id] = {
            "chapter_id": chapter_id,
            "chapter_number": chapter.get("chapter_number"),
            "chapter_title": _chapter_display_title({**chapter, "chapter_id": chapter_id}),
            "element_area": chapter.get("element_area"),
            "total_count": 0,
            "choice_count": 0,
            "true_false_count": 0,
            "fill_blank_count": 0,
            "enabled_count": 0,
            "disabled_count": 0,
            "draft_count": 0,
            "archived_count": 0,
            "linked_experiment_count": 0,
            "linked_experiments": [],
            "updated_at": None,
        }

    experiments_by_chapter: dict[str, dict[str, dict[str, Any]]] = {chapter_id: {} for chapter_id in summaries}
    for experiment_id, chapter_ids in bindings_by_experiment.items():
        for chapter_id in chapter_ids:
            if chapter_id in experiments_by_chapter:
                experiments_by_chapter[chapter_id][experiment_id] = {"id": experiment_id}

    for question in questions:
        q_status = str(question.get("status") or "")
        q_type = str(question.get("question_type") or "")
        for chapter_id in _resolve_question_chapter_ids(question, bindings_by_experiment):
            summary = summaries.get(chapter_id)
            if not summary:
                continue
            if q_status in CURRENT_BANK_STATUSES:
                summary["total_count"] += 1
                if q_type == "single_choice":
                    summary["choice_count"] += 1
                elif q_type == "true_false":
                    summary["true_false_count"] += 1
                elif q_type == "fill_blank":
                    summary["fill_blank_count"] += 1
            if q_status == "published":
                summary["enabled_count"] += 1
            elif q_status == "disabled":
                summary["disabled_count"] += 1
            elif q_status == "draft":
                summary["draft_count"] += 1
            elif q_status == "archived":
                summary["archived_count"] += 1
            updated_at = question.get("updated_at")
            if updated_at and (not summary["updated_at"] or str(updated_at) > str(summary["updated_at"])):
                summary["updated_at"] = updated_at

    for chapter_id, experiments in experiments_by_chapter.items():
        if chapter_id in summaries:
            summaries[chapter_id]["linked_experiment_count"] = len(experiments)
            summaries[chapter_id]["linked_experiments"] = list(experiments.values())

    return sorted(
        summaries.values(),
        key=lambda item: (
            item.get("chapter_number") is None,
            item.get("chapter_number") or 999,
            item.get("chapter_id") or "",
        ),
    )


def _question_row_id(question: dict[str, Any]) -> str:
    return str(question.get("id") or question.get("question_id") or "")


def _summarize_questions_for_overview(
    questions: list[dict[str, Any]],
    bindings_by_experiment: dict[str, list[str]],
) -> dict[str, Any]:
    by_chapter_sets: dict[str, set[str]] = defaultdict(set)
    by_experiment_sets: dict[str, set[str]] = defaultdict(set)
    all_question_ids: set[str] = set()
    status_sets: dict[str, set[str]] = defaultdict(set)
    type_sets: dict[str, set[str]] = defaultdict(set)
    by_chapter_status_sets: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    by_chapter_type_sets: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    by_experiment_status_sets: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    by_experiment_type_sets: dict[str, dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    for question in questions:
        status_value = str(question.get("status") or "")
        if status_value and status_value not in QUESTION_STATUSES:
            continue
        if not status_value and question.get("student_visible") is False:
            continue
        question_id = _question_row_id(question)
        if not question_id:
            continue
        question_type = str(question.get("question_type") or "")
        experiment_ids = [str(item) for item in question.get("related_experiment_ids") or [] if str(item).strip()]
        if question.get("experiment_id"):
            experiment_ids.append(str(question.get("experiment_id")))
        experiment_ids = sorted(set(experiment_ids))
        direct_chapter_ids = [str(item) for item in question.get("related_chapter_ids") or [] if str(item).strip()]
        if question.get("chapter_id"):
            direct_chapter_ids.append(str(question.get("chapter_id")))
        chapter_ids = sorted(set(direct_chapter_ids))
        if experiment_ids:
            all_question_ids.add(question_id)
            for experiment_id in experiment_ids:
                by_experiment_sets[experiment_id].add(question_id)
                if status_value:
                    by_experiment_status_sets[experiment_id][status_value].add(question_id)
                if question_type:
                    by_experiment_type_sets[experiment_id][question_type].add(question_id)
        elif chapter_ids:
            all_question_ids.add(question_id)
        else:
            continue
        if status_value:
            status_sets[status_value].add(question_id)
        if question_type:
            type_sets[question_type].add(question_id)
        if experiment_ids and not chapter_ids:
            chapter_ids = sorted({chapter_id for experiment_id in experiment_ids for chapter_id in bindings_by_experiment.get(experiment_id, [])})
        for chapter_id in chapter_ids:
            by_chapter_sets[chapter_id].add(question_id)
            if status_value:
                by_chapter_status_sets[chapter_id][status_value].add(question_id)
            if question_type:
                by_chapter_type_sets[chapter_id][question_type].add(question_id)
    return {
        "by_chapter_count": {chapter_id: len(question_ids) for chapter_id, question_ids in by_chapter_sets.items()},
        "by_experiment_count": {experiment_id: len(question_ids) for experiment_id, question_ids in by_experiment_sets.items()},
        "total_count": len(all_question_ids),
        "status_counts": _counts_from_sets(status_sets, QUESTION_STATUS_ORDER),
        "type_counts": _counts_from_sets(type_sets, QUESTION_TYPE_ORDER),
        "by_chapter_status_counts": {
            chapter_id: _counts_from_sets(value_sets, QUESTION_STATUS_ORDER)
            for chapter_id, value_sets in by_chapter_status_sets.items()
        },
        "by_chapter_type_counts": {
            chapter_id: _counts_from_sets(value_sets, QUESTION_TYPE_ORDER)
            for chapter_id, value_sets in by_chapter_type_sets.items()
        },
        "by_experiment_status_counts": {
            experiment_id: _counts_from_sets(value_sets, QUESTION_STATUS_ORDER)
            for experiment_id, value_sets in by_experiment_status_sets.items()
        },
        "by_experiment_type_counts": {
            experiment_id: _counts_from_sets(value_sets, QUESTION_TYPE_ORDER)
            for experiment_id, value_sets in by_experiment_type_sets.items()
        },
    }


def _summarize_media_resources_for_overview(media_resources: list[Any]) -> dict[str, Any]:
    asset_ids: set[str] = set()
    asset_status_counts = _zero_counts(MEDIA_UPLOAD_STATUS_ORDER)
    binding_status_counts = _zero_counts(MEDIA_BINDING_STATUS_ORDER)
    for index, media_resource in enumerate(media_resources):
        if isinstance(media_resource, dict):
            media_id = str(
                media_resource.get("media_id")
                or media_resource.get("binding_id")
                or media_resource.get("id")
                or f"media:{index}"
            )
            upload_status = str(media_resource.get("upload_status") or "unknown")
            binding_status = str(media_resource.get("binding_status") or media_resource.get("status") or "unknown")
        else:
            media_id = f"media:{index}"
            upload_status = "unknown"
            binding_status = "unknown"
        asset_ids.add(media_id)
        asset_status_counts[upload_status] = asset_status_counts.get(upload_status, 0) + 1
        binding_status_counts[binding_status] = binding_status_counts.get(binding_status, 0) + 1
    return {
        "media_ids": asset_ids,
        "asset_status_counts": asset_status_counts,
        "binding_status_counts": binding_status_counts,
        "ready_count": int(asset_status_counts.get("ready", 0)),
        "published_count": int(binding_status_counts.get("published", 0)),
        "draft_count": int(binding_status_counts.get("draft", 0)),
    }


def _build_learning_resource_overview(
    *,
    chapters: list[dict[str, Any]],
    units: list[dict[str, Any]],
    knowledge_points: list[dict[str, Any]],
    experiments: list[dict[str, Any]],
    questions: list[dict[str, Any]],
    bindings_by_experiment: dict[str, list[str]],
    dashboard_stats: dict[str, Any] | None = None,
    experiment_framework: dict[str, Any] | None = None,
) -> dict[str, Any]:
    dashboard_stats = dashboard_stats or {}
    question_summary = _summarize_questions_for_overview(questions, bindings_by_experiment)
    question_counts_by_chapter = question_summary["by_chapter_count"]
    question_counts_by_experiment = question_summary["by_experiment_count"]
    total_question_count = int(question_summary["total_count"])

    sorted_chapters = sorted(chapters, key=_chapter_sort_key)
    group_by_chapter: dict[str, dict[str, Any]] = {}
    groups: list[dict[str, Any]] = []
    for chapter in sorted_chapters:
        display = _learning_resource_group_display(chapter)
        chapter_id = display["chapter_id"]
        group = {
            **display,
            "knowledge_unit_count": 0,
            "knowledge_point_count": 0,
            "experiment_count": 0,
            "question_count": int(question_counts_by_chapter.get(chapter_id, 0)),
            "question_status_counts": question_summary["by_chapter_status_counts"].get(chapter_id, _zero_counts(QUESTION_STATUS_ORDER)),
            "question_type_counts": question_summary["by_chapter_type_counts"].get(chapter_id, _zero_counts(QUESTION_TYPE_ORDER)),
            "media_count": 0,
            "media_ready_count": 0,
            "media_published_count": 0,
            "media_asset_status_counts": _zero_counts(MEDIA_UPLOAD_STATUS_ORDER),
            "media_binding_status_counts": _zero_counts(MEDIA_BINDING_STATUS_ORDER),
            "units": [],
            "experiments": [],
        }
        group_by_chapter[chapter_id] = group
        groups.append(group)

    points_by_unit: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for point in knowledge_points:
        kp_id = str(point.get("knowledge_point_id") or point.get("id") or "")
        unit_id = str(point.get("unit_id") or "")
        chapter_id = str(point.get("chapter_id") or "")
        if not kp_id or not unit_id or chapter_id not in group_by_chapter:
            continue
        points_by_unit[unit_id].append(
            {
                "knowledge_point_id": kp_id,
                "content": point.get("content") or kp_id,
            }
        )

    for point_items in points_by_unit.values():
        point_items.sort(key=lambda item: str(item.get("knowledge_point_id") or ""))

    for unit in sorted(units, key=lambda item: (str(item.get("chapter_id") or ""), int(item.get("unit_index") or 999), str(item.get("unit_id") or ""))):
        unit_id = str(unit.get("unit_id") or unit.get("id") or "")
        chapter_id = str(unit.get("chapter_id") or "")
        group = group_by_chapter.get(chapter_id)
        if not unit_id or not group:
            continue
        kp_nodes = points_by_unit.get(unit_id, [])
        group["units"].append(
            {
                "unit_id": unit_id,
                "unit_index": unit.get("unit_index"),
                "unit_title": unit.get("unit_title") or unit_id,
                "knowledge_point_count": len(kp_nodes),
                "knowledge_points": kp_nodes,
            }
        )
        group["knowledge_unit_count"] += 1
        group["knowledge_point_count"] += len(kp_nodes)

    seen_experiments_by_group: dict[str, set[str]] = defaultdict(set)
    all_experiment_ids: set[str] = set()
    all_media_ids: set[str] = set()
    for experiment in experiments:
        experiment_id = str(experiment.get("id") or experiment.get("experiment_id") or "")
        if not experiment_id:
            continue
        all_experiment_ids.add(experiment_id)
        media_resources = experiment.get("media_resources") or []
        experiment_media_count = len(media_resources)
        media_summary = _summarize_media_resources_for_overview(media_resources)
        all_media_ids.update(media_summary["media_ids"])
        chapter_bindings = experiment.get("chapter_bindings") or []
        chapter_ids = [
            str(binding.get("chapter_id") or "")
            for binding in chapter_bindings
            if isinstance(binding, dict) and binding.get("chapter_id")
        ] or bindings_by_experiment.get(experiment_id, [])
        for chapter_id in chapter_ids:
            group = group_by_chapter.get(chapter_id)
            if not group or experiment_id in seen_experiments_by_group[group["id"]]:
                continue
            seen_experiments_by_group[group["id"]].add(experiment_id)
            group["experiments"].append(
                {
                    "id": experiment_id,
                    "code": experiment.get("code") or "",
                    "title": experiment.get("title") or experiment.get("name") or experiment_id,
                    "status": experiment.get("status") or experiment.get("content_status") or "published",
                    "display_order": experiment.get("display_order"),
                    "media_count": experiment_media_count,
                    "media_ready_count": media_summary["ready_count"],
                    "media_published_count": media_summary["published_count"],
                    "media_asset_status_counts": media_summary["asset_status_counts"],
                    "media_binding_status_counts": media_summary["binding_status_counts"],
                    "question_count": int(question_counts_by_experiment.get(experiment_id, 0)),
                    "question_status_counts": question_summary["by_experiment_status_counts"].get(experiment_id, _zero_counts(QUESTION_STATUS_ORDER)),
                    "question_type_counts": question_summary["by_experiment_type_counts"].get(experiment_id, _zero_counts(QUESTION_TYPE_ORDER)),
                }
            )
            group["experiment_count"] += 1
            group["media_count"] += experiment_media_count
            group["media_ready_count"] += media_summary["ready_count"]
            group["media_published_count"] += media_summary["published_count"]
            for key, value in media_summary["asset_status_counts"].items():
                group["media_asset_status_counts"][key] = group["media_asset_status_counts"].get(key, 0) + int(value)
            for key, value in media_summary["binding_status_counts"].items():
                group["media_binding_status_counts"][key] = group["media_binding_status_counts"].get(key, 0) + int(value)

    area_order = ["p", "s", "ds", "d", "f", "integrated", GENERAL_RESOURCE_AREA_ID, "other"]
    area_by_id: dict[str, dict[str, Any]] = {}
    for group in groups:
        area_id = str(group["area_id"])
        area = area_by_id.setdefault(
            area_id,
            {
                "area_id": area_id,
                "area_name": group["area_name"],
                "kind": "general" if area_id == GENERAL_RESOURCE_AREA_ID else "theory",
                "group_ids": [],
                "metrics": {
                    "group_count": 0,
                    "knowledge_unit_count": 0,
                    "knowledge_point_count": 0,
                    "experiment_count": 0,
                    "question_count": 0,
                    "media_count": 0,
                    "media_ready_count": 0,
                    "media_published_count": 0,
                },
            },
        )
        area["group_ids"].append(group["id"])
        area["metrics"]["group_count"] += 1
        for key in (
            "knowledge_unit_count",
            "knowledge_point_count",
            "experiment_count",
            "question_count",
            "media_count",
            "media_ready_count",
            "media_published_count",
        ):
            area["metrics"][key] += int(group.get(key) or 0)

    areas = sorted(area_by_id.values(), key=lambda item: (area_order.index(item["area_id"]) if item["area_id"] in area_order else 99, item["area_name"]))
    experiment_status_counts = _zero_counts(("draft", "published", "archived"))
    for experiment in experiments:
        status_value = str(experiment.get("status") or "published")
        experiment_status_counts[status_value] = experiment_status_counts.get(status_value, 0) + 1
    rag_stats = dashboard_stats.get("rag") or {}
    media_stats = dashboard_stats.get("media") or {}
    class_stats = dashboard_stats.get("classes_students") or {}
    metrics = {
        "knowledge_unit_count": sum(int(group.get("knowledge_unit_count") or 0) for group in groups),
        "knowledge_point_count": sum(int(group.get("knowledge_point_count") or 0) for group in groups),
        "experiment_count": len(all_experiment_ids),
        "media_resource_count": len(all_media_ids),
        "question_count": total_question_count,
        "published_question_count": int(question_summary["status_counts"].get("published", 0)),
        "draft_question_count": int(question_summary["status_counts"].get("draft", 0)),
        "published_video_binding_count": int(media_stats.get("published_binding_count", 0)),
        "video_asset_count": int(media_stats.get("asset_count", 0)),
        "class_count": int(class_stats.get("class_count", 0)),
        "student_count": int(class_stats.get("roster_count", 0)),
    }
    domains = {
        "knowledge": {
            "title": "知识框架 / 检索语料",
            "knowledge_unit_count": metrics["knowledge_unit_count"],
            "knowledge_point_count": metrics["knowledge_point_count"],
            "source_document_count": int(rag_stats.get("source_document_count", 0)),
            "source_chunk_count": int(rag_stats.get("source_chunk_count", 0)),
            "embedding_count": int(rag_stats.get("embedding_count", 0)),
        },
        "experiment_video": {
            "title": "实验与视频",
            "experiment_count": metrics["experiment_count"],
            "experiment_status_counts": experiment_status_counts,
            "video_asset_count": int(media_stats.get("asset_count", 0)),
            "video_binding_count": int(media_stats.get("binding_count", 0)),
            "ready_video_count": int(media_stats.get("ready_asset_count", 0)),
            "published_video_count": int(media_stats.get("published_binding_count", 0)),
            "asset_status_counts": media_stats.get("asset_status_counts") or _zero_counts(MEDIA_UPLOAD_STATUS_ORDER),
            "binding_status_counts": media_stats.get("binding_status_counts") or _zero_counts(MEDIA_BINDING_STATUS_ORDER),
        },
        "question_bank": {
            "title": "题库",
            "question_count": total_question_count,
            "status_counts": question_summary["status_counts"],
            "type_counts": question_summary["type_counts"],
            "published_question_count": int(question_summary["status_counts"].get("published", 0)),
            "draft_question_count": int(question_summary["status_counts"].get("draft", 0)),
        },
        "classes_students": {
            "title": "班级与学生",
            **class_stats,
        },
    }
    return {
        "metrics": metrics,
        "domains": domains,
        "areas": areas,
        "groups": groups,
        "experiment_framework": experiment_framework,
    }


def _filter_questions_for_chapter(
    questions: list[dict[str, Any]],
    bindings_by_experiment: dict[str, list[str]],
    *,
    chapter_id: str,
    question_type: str | None = None,
    status_filter: str | None = None,
    experiment_id: str | None = None,
    search: str | None = None,
) -> list[dict[str, Any]]:
    search_text = (search or "").strip().lower()
    items: list[dict[str, Any]] = []
    for question in questions:
        if chapter_id not in _resolve_question_chapter_ids(question, bindings_by_experiment):
            continue
        if question_type and question.get("question_type") != question_type:
            continue
        if experiment_id and question.get("experiment_id") != experiment_id:
            continue
        status_value = str(question.get("status") or "")
        if status_filter and status_filter != "all":
            if status_value != status_filter:
                continue
        elif status_value not in CURRENT_BANK_STATUSES:
            continue
        if search_text:
            haystack = " ".join([str(question.get("stem") or ""), str(question.get("explanation") or "")]).lower()
            if search_text not in haystack:
                continue
        items.append(question)
    return items


def _assistant_coverage_actions(chapter_summary: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not chapter_summary:
        return []
    gaps: list[str] = []
    if chapter_summary.get("choice_count", 0) <= 0:
        gaps.append("选择题为空")
    if chapter_summary.get("true_false_count", 0) <= 0:
        gaps.append("判断题为空")
    if chapter_summary.get("fill_blank_count", 0) <= 0:
        gaps.append("填空题为空")
    if not gaps:
        gaps.append("当前三类客观题均已有覆盖")
    return [
        {
            "action_type": "coverage_report",
            "title": "章节题型覆盖检查",
            "summary": "；".join(gaps),
            "counts": {
                "total": chapter_summary.get("total_count", 0),
                "single_choice": chapter_summary.get("choice_count", 0),
                "true_false": chapter_summary.get("true_false_count", 0),
                "fill_blank": chapter_summary.get("fill_blank_count", 0),
            },
        }
    ]


def _build_question_bank_assistant_preview(
    *,
    request: QuestionBankAssistantRequest,
    chapter_summary: dict[str, Any] | None,
    target_question: dict[str, Any] | None,
    source_refs: list[dict[str, Any]],
) -> dict[str, Any]:
    target_title = chapter_summary.get("chapter_title") if chapter_summary else request.chapter_id or "当前范围"
    actions: list[dict[str, Any]] = []
    warnings: list[str] = []
    valid_types = [item for item in request.question_types if item in OBJECTIVE_TYPES] or ["single_choice"]
    if not source_refs:
        warnings.append("当前范围未检索到实验资料片段，建议上传或索引实验 PDF 后再生成正式题目。")

    if request.intent == "coverage_check":
        actions = _assistant_coverage_actions(chapter_summary)
        summary = f"已检查 {target_title} 的题型覆盖情况。"
    elif request.intent == "repair_question":
        if not target_question:
            warnings.append("未选择具体题目，暂时只能给出修复流程建议。")
            actions = [
                {
                    "action_type": "repair_question",
                    "title": "选择题目后生成修复建议",
                    "summary": "请选择一题作为修复对象，助手会基于题干、答案、解析和来源依据生成替换建议。",
                }
            ]
        else:
            actions = [
                {
                    "action_type": "repair_question",
                    "question_id": target_question.get("id"),
                    "title": "修复题目建议",
                    "original_stem": target_question.get("stem"),
                    "suggested_stem": target_question.get("stem"),
                    "summary": "建议重新核对答案、解析和来源依据；确认后再替换原题。",
                    "answer": target_question.get("answer"),
                    "explanation": target_question.get("explanation"),
                }
            ]
        summary = "已生成题目修复建议预览。"
    elif request.intent == "disable_question":
        actions = [
            {
                "action_type": "disable_question",
                "question_id": request.question_id,
                "title": "停用题目建议",
                "summary": "确认后可将问题题目标记为已停用，学生端不再使用。",
            }
        ]
        summary = "已生成停用建议预览。"
    else:
        for index in range(request.count):
            q_type = valid_types[index % len(valid_types)]
            if q_type == "single_choice":
                action = {
                    "action_type": "add_question",
                    "question_type": "single_choice",
                    "title": "新增选择题",
                    "stem": f"围绕{target_title}，下列哪一项最适合作为实验学习中的关键判断？",
                    "options": [
                        {"label": "A", "text": "结合实验现象、理论解释和安全要求进行判断"},
                        {"label": "B", "text": "只记忆实验名称即可"},
                        {"label": "C", "text": "忽略反应条件和观察现象"},
                        {"label": "D", "text": "只依据个人经验判断"},
                    ],
                    "answer": {"value": "A"},
                    "explanation": "正式生成时应结合实验 PDF 和理论 RAG 证据进一步细化。",
                }
            elif q_type == "true_false":
                action = {
                    "action_type": "add_question",
                    "question_type": "true_false",
                    "title": "新增判断题",
                    "stem": f"{target_title} 的题目应同时关注实验现象、理论依据和安全注意事项。",
                    "options": [],
                    "answer": {"value": True},
                    "explanation": "该题用于提示 AI 生成方向，确认前需要教师核对来源依据。",
                }
            else:
                action = {
                    "action_type": "add_question",
                    "question_type": "fill_blank",
                    "title": "新增填空题",
                    "stem": f"{target_title} 中需要学生掌握的一个关键实验结论是____。",
                    "options": [],
                    "answer": {"accepted_answers": ["待 AI 依据资料生成"], "match": "normalized_exact"},
                    "explanation": "正式入库前必须替换为可机判的标准答案。",
                }
            actions.append(action)
        summary = f"已为 {target_title} 生成 {len(actions)} 条新增题目建议预览。"

    return {
        "proposal_id": f"preview-{uuid.uuid4()}",
        "intent": request.intent,
        "mode": "local_preview",
        "mutates_bank": False,
        "summary": summary,
        "warnings": warnings,
        "target": {
            "chapter_id": request.chapter_id,
            "chapter_title": target_title,
            "experiment_id": request.experiment_id,
            "question_id": request.question_id,
        },
        "actions": actions,
        "source_refs": source_refs,
    }


def _list_question_bank_chapters(session: Any) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT id AS chapter_id, chapter_number, chapter_title, element_area
                FROM chapters
                WHERE id IN ('CH13', 'CH14', 'CH15', 'CH16', 'CH17', 'CH18', 'CH19', 'CH20', 'CH21', 'CH22')
                ORDER BY chapter_number NULLS LAST, id
                """
            )
        )
        .mappings()
        .all()
    ]


def _question_bank_bindings_by_experiment(session: Any) -> dict[str, list[str]]:
    bindings: dict[str, list[str]] = {}
    for row in session.execute(
        text(
            """
            SELECT experiment_id, chapter_id
            FROM experiment_chapter_bindings
            ORDER BY experiment_id, sort_order, chapter_id
            """
        )
    ).mappings():
        bindings.setdefault(str(row["experiment_id"]), []).append(str(row["chapter_id"]))
    return bindings


def _list_question_bank_question_rows(session: Any) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT q.id::text AS id,
                       q.bank_id::text AS bank_id,
                       q.generation_id::text AS generation_id,
                       q.experiment_id,
                       fe.code AS experiment_code,
                       fe.title AS experiment_title,
                       q.question_type,
                       q.stem,
                       q.options,
                       q.answer,
                       q.explanation,
                       q.difficulty,
                       q.related_chapter_ids,
                       q.related_knowledge_point_ids,
                       q.source_chunk_ids,
                       q.source_refs,
                       q.status,
                       q.metadata,
                       q.created_at,
                       q.updated_at,
                       b.bank_kind,
                       b.title AS bank_title
                FROM experiment_questions q
                JOIN formal_experiments fe ON fe.id = q.experiment_id
                LEFT JOIN experiment_question_banks b ON b.id = q.bank_id
                ORDER BY q.updated_at DESC, q.created_at DESC
                """
            )
        )
        .mappings()
        .all()
    ]


def _list_learning_resource_chapters(session: Any) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT id AS chapter_id, chapter_number, chapter_title, element_area, content_status
                FROM chapters
                WHERE COALESCE(content_status, 'published') = 'published'
                ORDER BY chapter_number NULLS LAST, id
                """
            )
        )
        .mappings()
        .all()
    ]


def _list_learning_resource_units(session: Any) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT id AS unit_id, chapter_id, unit_index, unit_title, content_status
                FROM knowledge_units
                WHERE COALESCE(content_status, 'published') = 'published'
                ORDER BY chapter_id, unit_index, id
                """
            )
        )
        .mappings()
        .all()
    ]


def _list_learning_resource_kps(session: Any) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT id AS knowledge_point_id, chapter_id, unit_id, content, content_status
                FROM knowledge_points
                WHERE COALESCE(content_status, 'published') = 'published'
                ORDER BY chapter_id, unit_id, id
                """
            )
        )
        .mappings()
        .all()
    ]


def _list_learning_resource_experiments(session: Any) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in session.execute(text(_experiment_select_sql("WHERE fe.status <> 'archived'")))
        .mappings()
        .all()
    ]


@admin_router.get("/learning-resources/overview")
async def admin_learning_resources_overview(
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    with db_session() as session:
        chapters = _list_learning_resource_chapters(session)
        units = _list_learning_resource_units(session)
        knowledge_points = _list_learning_resource_kps(session)
        experiments = _list_learning_resource_experiments(session)
        bindings_by_experiment = _question_bank_bindings_by_experiment(session)
        questions = _list_question_bank_question_rows(session)
        dashboard_stats = _load_learning_resource_dashboard_stats(session)
        experiment_framework = build_experiment_framework_overview(session)
    return _build_learning_resource_overview(
        chapters=chapters,
        units=units,
        knowledge_points=knowledge_points,
        experiments=experiments,
        questions=questions,
        bindings_by_experiment=bindings_by_experiment,
        dashboard_stats=dashboard_stats,
        experiment_framework=experiment_framework,
    )


@admin_router.get("/experiment-knowledge-framework/overview")
async def admin_experiment_knowledge_framework_overview(
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    with db_session() as session:
        return build_experiment_framework_overview(session)


def _load_chapter_source_refs(session: Any, *, chapter_id: str | None, prompt: str, limit: int = 6) -> list[dict[str, Any]]:
    if not chapter_id:
        return []
    return load_evidence_source_refs(session, prompt=prompt, chapter_ids=[chapter_id], limit=limit)


@admin_router.get("/question-banks/chapters")
async def admin_list_question_bank_chapters(
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    with db_session() as session:
        chapters = _list_question_bank_chapters(session)
        bindings_by_experiment = _question_bank_bindings_by_experiment(session)
        questions = _list_question_bank_question_rows(session)
    items = _summarize_question_bank_chapters(chapters, questions, bindings_by_experiment)
    return {"items": items, "total": len(items)}


@admin_router.get("/question-banks/chapter-questions")
async def admin_list_chapter_questions(
    chapter_id: str = Query(min_length=1),
    question_type: str | None = None,
    status_filter: str | None = None,
    experiment_id: str | None = None,
    search: str | None = None,
    limit: int = Query(default=300, ge=1, le=1000),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    with db_session() as session:
        chapters = _list_question_bank_chapters(session)
        bindings_by_experiment = _question_bank_bindings_by_experiment(session)
        questions = _list_question_bank_question_rows(session)
    chapter_by_id = {str(chapter["chapter_id"]): chapter for chapter in chapters}
    if chapter_id not in chapter_by_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
    filtered = _filter_questions_for_chapter(
        questions,
        bindings_by_experiment,
        chapter_id=chapter_id,
        question_type=question_type,
        status_filter=status_filter,
        experiment_id=experiment_id,
        search=search,
    )[:limit]
    for question in filtered:
        chapter_ids = _resolve_question_chapter_ids(question, bindings_by_experiment)
        question["chapter_ids"] = chapter_ids
        question["chapter_titles"] = [
            _chapter_display_title(chapter_by_id[item]) for item in chapter_ids if item in chapter_by_id
        ]
    return {"items": filtered, "total": len(filtered)}


@admin_router.post("/question-banks/assistant/preview")
async def admin_question_bank_assistant_preview(
    payload: QuestionBankAssistantRequest,
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    if not ai_feature_enabled("question_bank_assistant"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="题库助手当前未启用。")
    invalid_types = [item for item in payload.question_types if item not in OBJECTIVE_TYPES]
    if invalid_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported question types: {invalid_types}")
    with db_session() as session:
        chapters = _list_question_bank_chapters(session)
        bindings_by_experiment = _question_bank_bindings_by_experiment(session)
        questions = _list_question_bank_question_rows(session)
        summaries = _summarize_question_bank_chapters(chapters, questions, bindings_by_experiment)
        summary_by_id = {str(item["chapter_id"]): item for item in summaries}
        target_question = next((item for item in questions if item.get("id") == payload.question_id), None)
        if payload.question_id and not target_question:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
        target_chapter_id = payload.chapter_id
        if not target_chapter_id and target_question:
            chapter_ids = _resolve_question_chapter_ids(target_question, bindings_by_experiment)
            target_chapter_id = chapter_ids[0] if chapter_ids else None
        if not target_chapter_id and payload.experiment_id:
            target_chapter_id = next(iter(bindings_by_experiment.get(payload.experiment_id, [])), None)
        chapter_summary = summary_by_id.get(target_chapter_id or "")
        if payload.chapter_id and not chapter_summary:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chapter not found")
        source_refs = _load_chapter_source_refs(session, chapter_id=target_chapter_id, prompt=payload.prompt)
    return _build_question_bank_assistant_preview(
        request=payload,
        chapter_summary=chapter_summary,
        target_question=target_question,
        source_refs=source_refs,
    )


@admin_router.get("/question-banks")
async def admin_list_question_banks(
    experiment_id: str | None = None,
    chapter_id: str | None = None,
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    experiments = _list_experiments(chapter_id=chapter_id)
    if experiment_id:
        experiments = [item for item in experiments if item["id"] == experiment_id]
    with db_session() as session:
        banks = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT b.id, b.experiment_id, b.bank_kind, b.title, b.status, b.source_label,
                           b.created_at, b.updated_at,
                           COUNT(q.id) AS question_count,
                           COUNT(q.id) FILTER (WHERE q.status = 'published') AS published_count,
                           COUNT(q.id) FILTER (WHERE q.status = 'draft') AS draft_count,
                           COUNT(q.id) FILTER (WHERE q.question_type = 'single_choice') AS choice_count,
                           COUNT(q.id) FILTER (WHERE q.question_type = 'true_false') AS true_false_count,
                           COUNT(q.id) FILTER (WHERE q.question_type = 'fill_blank') AS fill_blank_count
                    FROM experiment_question_banks b
                    LEFT JOIN experiment_questions q ON q.bank_id = b.id
                    GROUP BY b.id
                    ORDER BY b.experiment_id, b.bank_kind
                    """
                )
            )
            .mappings()
            .all()
        ]
    banks_by_experiment: dict[str, list[dict[str, Any]]] = {}
    for bank in banks:
        banks_by_experiment.setdefault(bank["experiment_id"], []).append(bank)
    items = [{**experiment, "banks": banks_by_experiment.get(experiment["id"], [])} for experiment in experiments]
    return {"items": items, "total": len(items)}


@admin_router.get("/question-banks/questions")
async def admin_list_questions(
    experiment_id: str | None = None,
    question_type: str | None = None,
    difficulty: str | None = None,
    status_filter: str | None = None,
    search: str | None = None,
    limit: int = Query(default=300, ge=1, le=1000),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    filters: list[str] = []
    params: dict[str, Any] = {"limit": limit}
    if experiment_id:
        filters.append("q.experiment_id = :experiment_id")
        params["experiment_id"] = experiment_id
    if question_type:
        filters.append("q.question_type = :question_type")
        params["question_type"] = question_type
    if difficulty:
        filters.append("q.difficulty = :difficulty")
        params["difficulty"] = difficulty
    if status_filter:
        filters.append("q.status = :status_filter")
        params["status_filter"] = status_filter
    if search:
        filters.append("(q.stem ILIKE :search OR q.explanation ILIKE :search)")
        params["search"] = f"%{search}%"
    where_clause = "WHERE " + " AND ".join(filters) if filters else ""
    with db_session() as session:
        rows = [
            dict(row)
            for row in session.execute(
                text(
                    f"""
                    SELECT q.*, fe.code AS experiment_code, fe.title AS experiment_title,
                           b.bank_kind, b.title AS bank_title
                    FROM experiment_questions q
                    JOIN formal_experiments fe ON fe.id = q.experiment_id
                    LEFT JOIN experiment_question_banks b ON b.id = q.bank_id
                    {where_clause}
                    ORDER BY q.updated_at DESC, q.created_at DESC
                    LIMIT :limit
                    """
                ),
                params,
            )
            .mappings()
            .all()
        ]
    return {"items": rows, "total": len(rows)}


@admin_router.post("/question-banks/questions")
async def admin_create_question(
    payload: QuestionRequest,
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    data = _dump(payload)
    experiment_id = data.pop("experiment_id")
    bank_kind = data.pop("bank_kind")
    with db_session() as session:
        row = _insert_question(session, experiment_id=experiment_id, payload=data, bank_kind=bank_kind, actor_user_id=user.id)
    return row


@admin_router.patch("/question-banks/questions/{question_id}")
async def admin_update_question(
    payload: QuestionUpdateRequest,
    question_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    data = {key: value for key, value in _dump(payload).items() if value is not None}
    with db_session() as session:
        current = (
            session.execute(text("SELECT * FROM experiment_questions WHERE id = CAST(:id AS uuid)"), {"id": question_id})
            .mappings()
            .first()
        )
        if not current:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
        merged = {**dict(current), **data}
        normalized, errors = _validate_question_payload(merged)
        if errors or normalized is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"errors": errors})
        row = (
            session.execute(
                text(
                    """
                    UPDATE experiment_questions
                    SET stem = :stem,
                        options = CAST(:options AS jsonb),
                        answer = CAST(:answer AS jsonb),
                        explanation = :explanation,
                        difficulty = :difficulty,
                        related_chapter_ids = :related_chapter_ids,
                        related_knowledge_point_ids = :related_knowledge_point_ids,
                        source_chunk_ids = :source_chunk_ids,
                        source_refs = CAST(:source_refs AS jsonb),
                        metadata = CAST(:metadata AS jsonb),
                        status = :status,
                        published_by = CASE WHEN :status = 'published' THEN CAST(:actor AS uuid) ELSE published_by END,
                        published_at = CASE WHEN :status = 'published' THEN COALESCE(published_at, now()) ELSE published_at END,
                        updated_at = now()
                    WHERE id = CAST(:id AS uuid)
                    RETURNING *
                    """
                ),
                {
                    "id": question_id,
                    "stem": normalized["stem"],
                    "options": _json_array(normalized["options"]),
                    "answer": _json(normalized["answer"]),
                    "explanation": normalized["explanation"],
                    "difficulty": normalized["difficulty"],
                    "related_chapter_ids": normalized["related_chapter_ids"],
                    "related_knowledge_point_ids": normalized["related_knowledge_point_ids"],
                    "source_chunk_ids": normalized["source_chunk_ids"],
                    "source_refs": _json_array(normalized["source_refs"]),
                    "metadata": _json(normalized["metadata"]),
                    "status": normalized["status"],
                    "actor": user.id,
                },
            )
            .mappings()
            .one()
        )
    return dict(row)


@admin_router.post("/question-banks/questions/{question_id}/publish")
async def admin_publish_question(
    question_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    UPDATE experiment_questions
                    SET status = 'published',
                        published_by = CAST(:actor AS uuid),
                        published_at = COALESCE(published_at, now()),
                        updated_at = now()
                    WHERE id = CAST(:id AS uuid)
                    RETURNING *
                    """
                ),
                {"id": question_id, "actor": user.id},
            )
            .mappings()
            .first()
        )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    return dict(row)


@admin_router.post("/question-banks/questions/{question_id}/disable")
async def admin_disable_question(
    question_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    UPDATE experiment_questions
                    SET status = 'disabled', updated_at = now()
                    WHERE id = CAST(:id AS uuid)
                    RETURNING *
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


@admin_router.post("/question-banks/import")
async def admin_import_question_bank(
    file: UploadFile = File(...),
    publish: bool = Form(False),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    content = await file.read()
    try:
        data = json.loads(content.decode("utf-8-sig"))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid JSON: {exc}") from exc
    rows = data.get("questions") if isinstance(data, dict) else data
    if not isinstance(rows, list):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Import JSON must be a list or {questions: []}")
    errors: list[dict[str, Any]] = []
    imported: list[dict[str, Any]] = []
    with db_session() as session:
        import_id = str(
            session.execute(
                text(
                    """
                    INSERT INTO experiment_question_imports (
                      source_file, status, total_rows, imported_by, metadata
                    )
                    VALUES (:source_file, 'validating', :total_rows, CAST(:actor AS uuid), CAST(:metadata AS jsonb))
                    RETURNING id
                    """
                ),
                {
                    "source_file": file.filename,
                    "total_rows": len(rows),
                    "actor": user.id,
                    "metadata": _json({"publish": publish}),
                },
            ).scalar_one()
        )
        code_to_id = {
            row["code"]: row["id"]
            for row in session.execute(text("SELECT id, code FROM formal_experiments")).mappings().all()
        }
        for index, row in enumerate(rows, start=1):
            if not isinstance(row, dict):
                errors.append({"row": index, "errors": ["row must be an object"]})
                continue
            experiment_id = row.get("experiment_id") or code_to_id.get(str(row.get("experiment_code") or ""))
            if not experiment_id:
                errors.append({"row": index, "errors": ["experiment_id or experiment_code is required"]})
                continue
            payload = {**row, "status": "published" if publish else row.get("status", "draft")}
            normalized, validation_errors = _validate_question_payload(payload)
            if validation_errors or normalized is None:
                errors.append({"row": index, "errors": validation_errors})
                continue
            inserted = _insert_question(
                session,
                experiment_id=experiment_id,
                payload=normalized,
                bank_kind="default",
                actor_user_id=user.id,
            )
            imported.append(inserted)
        final_status = "succeeded" if not errors else ("failed" if not imported else "partial")
        session.execute(
            text(
                """
                UPDATE experiment_question_imports
                SET status = :status,
                    valid_rows = :valid_rows,
                    invalid_rows = :invalid_rows,
                    errors = CAST(:errors AS jsonb),
                    updated_at = now()
                WHERE id = CAST(:id AS uuid)
                """
            ),
            {
                "id": import_id,
                "status": final_status,
                "valid_rows": len(imported),
                "invalid_rows": len(errors),
                "errors": _json_array(errors),
            },
        )
    return {
        "import_id": import_id,
        "status": final_status,
        "total_rows": len(rows),
        "valid_rows": len(imported),
        "invalid_rows": len(errors),
        "errors": errors,
        "items": imported,
    }


@admin_router.get("/question-banks/export")
async def admin_export_question_bank(
    experiment_id: str | None = None,
    status_filter: str | None = "published",
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    questions = await admin_list_questions(experiment_id=experiment_id, status_filter=status_filter, user=user)
    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "items": questions["items"],
        "total": questions["total"],
    }


def _load_generation_sources(
    session: Any,
    *,
    experiment: dict[str, Any],
    prompt: str,
    chapter_ids: list[str],
    knowledge_point_ids: list[str],
    limit: int = 6,
) -> list[dict[str, Any]]:
    if not chapter_ids:
        chapter_ids = [
            row["chapter_id"]
            for row in session.execute(
                text("SELECT chapter_id FROM experiment_chapter_bindings WHERE experiment_id = :experiment_id"),
                {"experiment_id": experiment["id"]},
            )
            .mappings()
            .all()
        ]
    return load_evidence_source_refs(
        session,
        prompt=prompt,
        experiment=experiment,
        chapter_ids=chapter_ids,
        knowledge_point_ids=knowledge_point_ids,
        limit=limit,
    )


def _local_generated_questions(
    *,
    experiment: dict[str, Any],
    request: GenerationRequest,
    source_refs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    valid_types = [item for item in request.question_types if item in OBJECTIVE_TYPES] or ["single_choice"]
    questions: list[dict[str, Any]] = []
    for index in range(request.count):
        q_type = valid_types[index % len(valid_types)]
        title = experiment["title"]
        code = experiment["code"]
        common = {
            "difficulty": request.difficulty or "basic",
            "source_refs": source_refs,
            "related_chapter_ids": request.chapter_ids,
            "related_knowledge_point_ids": request.knowledge_point_ids,
            "source_chunk_ids": [item["chunk_id"] for item in source_refs if item.get("chunk_id")],
            "status": "draft",
        }
        if q_type == "single_choice":
            questions.append(
                {
                    **common,
                    "question_type": "single_choice",
                    "stem": f"关于{title}，以下哪一项最适合作为学习关注点？",
                    "options": [
                        {"label": "A", "text": "实验现象、反应结论与安全注意事项"},
                        {"label": "B", "text": "与该实验无关的生活常识"},
                        {"label": "C", "text": "未发布视频的播放地址"},
                        {"label": "D", "text": "学生个人账号密码"},
                    ],
                    "answer": {"value": "A"},
                    "explanation": "题目由本地生成器产生，需教师结合实验资料核验后再发布。",
                }
            )
        elif q_type == "true_false":
            questions.append(
                {
                    **common,
                    "question_type": "true_false",
                    "stem": f"{title}应作为一个具体实验点管理，并可在该实验下绑定多个视频资源。",
                    "options": [],
                    "answer": {"value": True},
                    "explanation": "正式目录以具体实验点为后台实验主实体，教师发布前仍需核验表述。",
                }
            )
        else:
            questions.append(
                {
                    **common,
                    "question_type": "fill_blank",
                    "stem": f"{title}对应的正式实验编号是____。",
                    "options": [],
                    "answer": {"accepted_answers": [code], "match": "normalized_exact"},
                    "explanation": "本题检查实验编号识别，可作为导入后基础题。",
                }
            )
    return questions


def _try_openai_generation(
    *,
    experiment: dict[str, Any],
    request: GenerationRequest,
    source_refs: list[dict[str, Any]],
) -> list[dict[str, Any]] | None:
    settings = effective_ai_settings(get_settings())
    if settings.agent_llm_provider == "disabled":
        return None
    api_key = settings.agent_llm_api_key or os.getenv("OPENAI_API_KEY", "")
    model = settings.agent_llm_model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    if not api_key:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url=settings.agent_llm_base_url or None)
        response = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You generate teacher-reviewed objective chemistry experiment questions. "
                        "Return JSON only: {\"questions\":[...]}. "
                        "Allowed question_type values: single_choice, true_false, fill_blank. "
                        "Do not publish, do not include unsafe operational details beyond classroom-safe theory."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "experiment": {
                                "id": experiment["id"],
                                "code": experiment["code"],
                                "title": experiment["title"],
                                "summary": experiment.get("summary"),
                            },
                            "prompt": request.prompt,
                            "question_types": request.question_types,
                            "count": request.count,
                            "difficulty": request.difficulty,
                            "sources": source_refs,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
        )
        content = response.choices[0].message.content or "{}"
        data = json.loads(content)
        rows = data.get("questions") or []
        return rows if isinstance(rows, list) else None
    except Exception:
        return None


def _question_source_chunk_ids(source_refs: list[dict[str, Any]], source_audit: dict[str, Any] | None = None) -> list[str]:
    seen: set[str] = set()
    values: list[str] = []
    for raw in [
        *((source_audit or {}).get("canonical_chunk_ids") or []),
        *((source_audit or {}).get("supporting_theory_chunk_ids") or []),
        *[item.get("chunk_id") for item in source_refs if isinstance(item, dict)],
    ]:
        value = str(raw or "").strip()
        if value and value not in seen:
            seen.add(value)
            values.append(value)
    return values


def _source_audit_for_suggestion(
    *,
    source_refs: list[dict[str, Any]],
    target_question: dict[str, Any] | None = None,
) -> dict[str, Any]:
    target_metadata = target_question.get("metadata") if isinstance(target_question, dict) else {}
    existing = target_metadata.get("source_audit") if isinstance(target_metadata, dict) else None
    if isinstance(existing, dict) and existing.get("canonical_chunk_ids"):
        return {
            **existing,
            "reviewer_note": existing.get("reviewer_note") or "Inherited from the original point-aware question for AI repair review.",
        }
    chunk_ids = [item.get("chunk_id") for item in source_refs if isinstance(item, dict) and item.get("chunk_id")]
    return {
        "canonical_chunk_ids": [str(item) for item in chunk_ids],
        "supporting_theory_chunk_ids": [],
        "evidence_sufficient": bool(chunk_ids),
        "reviewer_note": "AI suggestion draft; teacher must verify source support before publication.",
    }


def _point_from_metadata(metadata: Any) -> dict[str, str] | None:
    if not isinstance(metadata, dict):
        return None
    points = metadata.get("primary_points") or []
    if isinstance(points, list):
        for point in points:
            if isinstance(point, dict) and (point.get("point_key") or point.get("point_title")):
                return {
                    "point_key": str(point.get("point_key") or "").strip(),
                    "point_title": str(point.get("point_title") or point.get("point_key") or "").strip(),
                }
    keys = metadata.get("primary_point_keys") or []
    if isinstance(keys, list) and keys:
        key = str(keys[0] or "").strip()
        if key:
            return {"point_key": key, "point_title": key}
    return None


def _points_from_metadata(metadata: Any) -> list[dict[str, str]]:
    if not isinstance(metadata, dict):
        return []
    output: list[dict[str, str]] = []
    points = metadata.get("primary_points") or []
    if isinstance(points, list):
        for point in points:
            if not isinstance(point, dict):
                continue
            key = str(point.get("point_key") or "").strip()
            title = str(point.get("point_title") or key).strip()
            if key or title:
                output.append({"point_key": key or title, "point_title": title or key})
    if output:
        return output
    keys = metadata.get("primary_point_keys") or []
    if isinstance(keys, list):
        return [
            {"point_key": key, "point_title": key}
            for key in [str(item or "").strip() for item in keys]
            if key
        ]
    return []


def _unique_point_keys(*groups: Any) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for group in groups:
        values = group if isinstance(group, list) else [group]
        for item in values:
            key = str(item or "").strip()
            if key and key not in seen:
                seen.add(key)
                output.append(key)
    return output


def _select_suggestion_points(
    *,
    points: list[dict[str, Any]],
    point_keys: list[str],
    target_question: dict[str, Any] | None,
) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    by_key = {str(item.get("point_key") or ""): item for item in points if item.get("point_key")}
    for key in _unique_point_keys(point_keys):
        found = by_key.get(key)
        if found:
            selected.append(
                {
                    "point_key": str(found.get("point_key") or ""),
                    "point_title": str(found.get("point_title") or found.get("point_key") or ""),
                }
            )
        else:
            selected.append({"point_key": key, "point_title": key})
    if selected:
        return selected
    if target_question:
        from_question = _points_from_metadata(target_question.get("metadata"))
        if from_question:
            return from_question
    first = next((item for item in points if item.get("point_key") and item.get("source") != "legacy"), None)
    if first:
        return [
            {
                "point_key": str(first.get("point_key") or ""),
                "point_title": str(first.get("point_title") or first.get("point_key") or ""),
            }
        ]
    return []


def _select_suggestion_point(
    *,
    points: list[dict[str, Any]],
    point_key: str | None,
    target_question: dict[str, Any] | None,
) -> dict[str, str] | None:
    return next(
        iter(
            _select_suggestion_points(
                points=points,
                point_keys=_unique_point_keys(point_key),
                target_question=target_question,
            )
        ),
        None,
    )


def _default_option_links(options: list[Any], point: dict[str, str] | None) -> list[dict[str, Any]]:
    links: list[dict[str, Any]] = []
    for index, option in enumerate(options):
        label = option.get("label") if isinstance(option, dict) else None
        label = str(label or chr(65 + index))
        if index == 0:
            links.append(
                {
                    "label": label,
                    "role": "correct_evidence",
                    "point_key": point.get("point_key") if point else None,
                    "point_title": point.get("point_title") if point else None,
                    "diagnostic_note": "Correct option tied to the selected experiment point.",
                }
            )
        else:
            links.append(
                {
                    "label": label,
                    "role": "weak_distractor",
                    "point_key": None,
                    "diagnostic_note": "Draft distractor; teacher should verify diagnostic value.",
                }
            )
    return links


def _with_point_aware_metadata(
    *,
    row: dict[str, Any],
    request: PointAwareSuggestionRequest,
    experiment: dict[str, Any],
    point: dict[str, str] | None,
    source_refs: list[dict[str, Any]],
    target_question: dict[str, Any] | None,
    index: int,
) -> dict[str, Any]:
    existing_metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
    target_metadata = target_question.get("metadata") if isinstance(target_question, dict) and isinstance(target_question.get("metadata"), dict) else {}
    source_audit = row.get("source_audit") if isinstance(row.get("source_audit"), dict) else None
    if source_audit is None:
        source_audit = existing_metadata.get("source_audit") if isinstance(existing_metadata.get("source_audit"), dict) else None
    source_audit = source_audit or _source_audit_for_suggestion(source_refs=source_refs, target_question=target_question)
    primary_point_keys = _unique_point_keys(row.get("primary_point_keys"), existing_metadata.get("primary_point_keys"))
    if not primary_point_keys:
        primary_point_keys = _unique_point_keys(request.point_keys, point.get("point_key") if point else None)
    primary_points = [
        {
            "point_key": point["point_key"],
            "point_title": point.get("point_title") or point["point_key"],
        }
        for point in ([point] if point and point.get("point_key") else [])
    ]
    if not primary_points and isinstance(target_metadata.get("primary_points"), list):
        primary_points = [item for item in target_metadata["primary_points"] if isinstance(item, dict)]
    if not primary_points and primary_point_keys:
        primary_points = [{"point_key": key, "point_title": key} for key in primary_point_keys]
    question_type = str(row.get("question_type") or "")
    options = row.get("options") if isinstance(row.get("options"), list) else []
    option_links = row.get("option_links") if isinstance(row.get("option_links"), list) else None
    if option_links is None:
        option_links = existing_metadata.get("option_links") if isinstance(existing_metadata.get("option_links"), list) else None
    if question_type == "single_choice" and not option_links:
        option_links = _default_option_links(options, point)
    metadata = {
        **existing_metadata,
        "point_aware_question_bank": True,
        "suggestion_intent": request.intent,
        "primary_point_keys": primary_point_keys,
        "primary_points": primary_points,
        "secondary_point_keys": list(row.get("secondary_point_keys") or existing_metadata.get("secondary_point_keys") or []),
        "coverage_tags": list(row.get("coverage_tags") or existing_metadata.get("coverage_tags") or target_metadata.get("coverage_tags") or []),
        "option_links": option_links or [],
        "quality_flags": list(row.get("quality_flags") or existing_metadata.get("quality_flags") or ["ai_suggestion", "needs_teacher_review"]),
        "source_audit": source_audit,
        "review_decision": "rewrite" if request.intent == "repair_question" else "keep",
        "review_lineage": {
            **(existing_metadata.get("review_lineage") if isinstance(existing_metadata.get("review_lineage"), dict) else {}),
            "suggestion_intent": request.intent,
            "suggestion_index": index,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "experiment_id": experiment.get("id"),
            "experiment_code": experiment.get("code"),
            "original_question_id": request.question_id if request.intent == "repair_question" else None,
        },
        "machine_grading": row.get("machine_grading") or existing_metadata.get("machine_grading") or "deterministic",
    }
    return {
        **row,
        "related_chapter_ids": list(row.get("related_chapter_ids") or (target_question or {}).get("related_chapter_ids") or []),
        "related_knowledge_point_ids": list(
            row.get("related_knowledge_point_ids") or (target_question or {}).get("related_knowledge_point_ids") or []
        ),
        "source_refs": row.get("source_refs") or source_refs or (target_question or {}).get("source_refs") or [],
        "source_chunk_ids": _question_source_chunk_ids(source_refs or [], source_audit),
        "metadata": metadata,
    }


def _local_point_aware_suggestions(
    *,
    request: PointAwareSuggestionRequest,
    experiment: dict[str, Any],
    point: dict[str, str] | None,
    target_question: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    valid_types = [item for item in request.question_types if item in OBJECTIVE_TYPES] or ["single_choice"]
    if request.intent == "repair_question" and target_question:
        valid_types = [str(target_question.get("question_type") or valid_types[0])]
    title = str(experiment.get("title") or experiment.get("code") or "experiment")
    point_title = str((point or {}).get("point_title") or "selected experiment point")
    rows: list[dict[str, Any]] = []
    for index in range(request.count):
        question_type = valid_types[index % len(valid_types)]
        if request.intent == "repair_question" and target_question:
            base_stem = str(target_question.get("stem") or "")
            repair_prefix = "修正建议："
            stem = base_stem if base_stem.startswith(repair_prefix) else f"{repair_prefix}{base_stem}"
            explanation = target_question.get("explanation") or "请教师结合来源证据复核本题解析。"
            options = target_question.get("options") or []
            answer = target_question.get("answer") or {}
        elif question_type == "true_false":
            stem = f"在《{title}》中，围绕“{point_title}”的实验现象可以直接支持本题所述结论。"
            options = []
            answer = {"value": True}
            explanation = "该判断题为 AI 草稿，教师需要核对实验来源和点位绑定后再发布。"
        elif question_type == "fill_blank":
            stem = f"《{title}》中与“{point_title}”直接相关的实验点位是____。"
            options = []
            answer = {"accepted_answers": [point_title[:12] or title[:12]], "match": "normalized_exact"}
            explanation = "填空答案使用短词精确匹配，发布前需要确认手机端输入友好。"
        else:
            stem = f"在《{title}》中，哪一项最能诊断学生是否理解“{point_title}”？"
            options = [
                {"label": "A", "text": f"围绕“{point_title}”说明实验操作、现象和结论之间的关系"},
                {"label": "B", "text": "只记住实验名称，不分析现象和结论"},
                {"label": "C", "text": "把相邻实验的现象直接套用到本实验"},
                {"label": "D", "text": "忽略实验条件，仅凭最终结论作答"},
            ]
            answer = {"value": "A"}
            explanation = "正确项要求学生把点位对应的操作、现象和结论连起来；其余选项用于暴露记忆化或混淆相邻实验的问题。"
        rows.append(
            {
                "question_type": question_type,
                "stem": stem,
                "options": options,
                "answer": answer,
                "explanation": explanation,
                "difficulty": request.difficulty or target_question.get("difficulty") if target_question else request.difficulty or "basic",
            }
        )
    return rows


def _try_openai_point_aware_suggestions(
    *,
    request: PointAwareSuggestionRequest,
    experiment: dict[str, Any],
    point: dict[str, str] | None,
    target_question: dict[str, Any] | None,
    source_refs: list[dict[str, Any]],
) -> list[dict[str, Any]] | None:
    settings = effective_ai_settings(get_settings())
    if settings.agent_llm_provider == "disabled":
        return None
    api_key = settings.agent_llm_api_key or os.getenv("OPENAI_API_KEY", "")
    model = settings.agent_llm_model or os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
    if not api_key:
        return None
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key, base_url=settings.agent_llm_base_url or None)
        response = client.chat.completions.create(
            model=model,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Generate teacher-review draft chemistry objective questions for a point-aware experiment question bank. "
                        "Return JSON only: {\"questions\":[...]}. "
                        "Each question must include question_type, stem, options, answer, explanation, primary_point_keys, "
                        "source_audit, and option_links for single_choice. Do not publish."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "intent": request.intent,
                            "prompt": request.prompt,
                            "question_types": request.question_types,
                            "count": request.count,
                            "difficulty": request.difficulty,
                            "experiment": {
                                "id": experiment.get("id"),
                                "code": experiment.get("code"),
                                "title": experiment.get("title"),
                                "summary": experiment.get("summary"),
                            },
                            "selected_point": point,
                            "original_question": target_question,
                            "source_refs": source_refs,
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
        )
        data = json.loads(response.choices[0].message.content or "{}")
        rows = data.get("questions") or []
        return rows if isinstance(rows, list) else None
    except Exception:
        return None


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
) -> dict[str, Any]:
    normalized_points = target_points or ([point] if point else [])
    target_point_keys = [item["point_key"] for item in normalized_points if item.get("point_key")]
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
        "original_question": _question_snapshot(target_question),
        "source_refs": source_refs,
        "rag_gate": rag_gate or {},
        "evidence_package": package,
        "coverage": coverage or {},
    }


def _question_coverage_for_context(session: Any, experiment_id: str, point_key: str | None) -> dict[str, Any]:
    params = {"experiment_id": experiment_id}
    rows = [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT question_type, status, metadata
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
        if point_key and isinstance(point_keys, list) and point_key in point_keys:
            point_question_count += 1
    return {
        "question_count": len(rows),
        "type_counts": type_counts,
        "selected_point_question_count": point_question_count if point_key else None,
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
        strategy = "canonical_evidence"
        fallback_reason = "rag_gate_unhealthy"

    if not source_refs:
        strategy = "canonical_evidence_after_hybrid_fallback" if fallback_reason else "canonical_evidence"
        source_refs = _load_workbench_source_refs(
            session,
            experiment=experiment,
            prompt=evidence_prompt,
            target_question=target_question,
            target_points=target_points,
        )

    return {
        "mode": trace.get("mode") or strategy,
        "source_refs": source_refs,
        "source_count": len(source_refs),
        "diagnostics": {
            "rag_gate": rag_gate or {},
            "rag_trace": trace,
            "source_strategy": strategy,
            "fallback_reason": fallback_reason,
            "chapter_ids": chapter_ids,
            "knowledge_point_ids": knowledge_point_ids,
            "target_point_keys": [point.get("point_key") for point in (target_points or []) if point.get("point_key")],
        },
    }


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
    requested_point_keys = _unique_point_keys(request.point_keys, request.point_key)
    selected_points = _select_suggestion_points(
        points=points,
        point_keys=requested_point_keys,
        target_question=target_question,
    )
    selected_point = selected_points[0] if selected_points else None
    point_key = selected_point.get("point_key") if selected_point else request.point_key
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
    coverage = _question_coverage_for_context(session, request.experiment_id, point_key)
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
    )
    session_id = str(
        session.execute(
            text(
                """
                INSERT INTO experiment_question_workbench_sessions (
                  mode, experiment_id, point_key, question_id, original_question_snapshot,
                  context_snapshot, status, created_by
                )
                VALUES (
                  :mode, :experiment_id, :point_key, CAST(:question_id AS uuid),
                  CAST(:original_question_snapshot AS jsonb),
                  CAST(:context_snapshot AS jsonb), 'open', CAST(:created_by AS uuid)
                )
                RETURNING id
                """
            ),
            {
                **params,
                "point_key": point_key,
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
    point_keys = metadata.get("primary_point_keys") if isinstance(metadata, dict) else []
    if not isinstance(point_keys, list) or not [item for item in point_keys if str(item).strip()]:
        errors.append("primary_point_keys are required")
    source_audit = metadata.get("source_audit") if isinstance(metadata, dict) else None
    if not isinstance(source_audit, dict):
        errors.append("source_audit is required")
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


@admin_router.post("/question-banks/workbench-sessions")
async def admin_create_question_workbench_session(
    payload: WorkbenchSessionRequest,
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    if not ai_feature_enabled("question_bank_assistant"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Question bank assistant is disabled")
    rag_gate = _ensure_question_workbench_rag_ready()
    with db_session() as session:
        session_id = _create_or_reopen_workbench_session(session, request=payload, user_id=user.id, rag_gate=rag_gate)
        return _workbench_session_response(session, session_id)


@admin_router.get("/question-banks/workbench-sessions/{session_id}")
async def admin_get_question_workbench_session(
    session_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    with db_session() as session:
        return _workbench_session_response(session, session_id)


@admin_router.post("/question-banks/workbench-sessions/{session_id}/messages/stream")
async def admin_stream_question_workbench_message(
    payload: WorkbenchMessageRequest,
    session_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> StreamingResponse:
    if not ai_feature_enabled("question_bank_assistant"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Question bank assistant is disabled")
    invalid_types = [item for item in payload.question_types if item not in OBJECTIVE_TYPES]
    if invalid_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported question types: {invalid_types}")

    async def event_stream():
        yield _sse_event("status", {"message": "已收到提示，正在准备题目上下文"})
        yield _sse_event("status", {"message": "正在调用 AI 生成候选题"})
        try:
            result = await admin_send_question_workbench_message(payload=payload, session_id=session_id, user=user)
            yield _sse_event("final", {"session": result})
        except HTTPException as exc:
            yield _sse_event("error", {"message": exc.detail, "status": exc.status_code})
        except Exception as exc:
            yield _sse_event("error", {"message": str(exc) or exc.__class__.__name__})

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@admin_router.post("/question-banks/workbench-sessions/{session_id}/messages")
async def admin_send_question_workbench_message(
    payload: WorkbenchMessageRequest,
    session_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
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
            }
            for point in raw_target_points
            if isinstance(point, dict) and (point.get("point_key") or point.get("point_title"))
        ]
        if not target_points and selected_point:
            target_points = [selected_point]
        target_point_keys = _unique_point_keys(
            context_snapshot.get("target_point_keys"),
            [point.get("point_key") for point in target_points],
            workbench.get("point_key"),
        )
        if not target_points and target_point_keys:
            target_points = [{"point_key": key, "point_title": key} for key in target_point_keys]
        selected_point = selected_point or (target_points[0] if target_points else None)

        user_turn = _insert_workbench_turn(
            session,
            session_id=session_id,
            role="user",
            content=payload.prompt,
            metadata={"question_types": payload.question_types, "count": payload.count, "point_keys": target_point_keys},
        )
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
        if not source_refs:
            source_refs = list(context_snapshot.get("source_refs") or [])
            if source_refs:
                evidence_package = {
                    **evidence_package,
                    "source_refs": source_refs,
                    "source_count": len(source_refs),
                    "diagnostics": {
                        **(evidence_package.get("diagnostics") if isinstance(evidence_package.get("diagnostics"), dict) else {}),
                        "fallback_reason": "previous_context_source_refs",
                    },
                }
        if not source_refs:
            message = "未找到可用的 RAG/来源证据，AI 出题或修题意见已阻止。"
            _insert_workbench_turn(
                session,
                session_id=session_id,
                role="assistant",
                content=message,
                error_state={"type": "EVIDENCE_MISSING", "message": message},
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
                            "rag_gate": rag_gate,
                            "evidence_package": {
                                "mode": evidence_package.get("mode") or "hybrid_bge_rag",
                                "source_refs": [],
                                "source_count": 0,
                                "diagnostics": evidence_package.get("diagnostics") or {"rag_gate": rag_gate},
                            },
                            "last_prompt": payload.prompt,
                        }
                    ),
                },
            )
            return _workbench_session_response(session, session_id)

        context_snapshot = {
            **context_snapshot,
            "selected_point": selected_point,
            "target_points": target_points,
            "target_point_keys": target_point_keys,
            "source_refs": source_refs,
            "rag_gate": rag_gate,
            "evidence_package": evidence_package,
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


@admin_router.post("/question-banks/workbench-candidates/{candidate_id}/reject")
async def admin_reject_question_workbench_candidate(
    candidate_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
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


@admin_router.post("/question-banks/workbench-candidates/{candidate_id}/publish")
async def admin_publish_question_workbench_candidate(
    candidate_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
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


@admin_router.post("/question-banks/point-aware-suggestions")
async def admin_create_point_aware_suggestions(
    payload: PointAwareSuggestionRequest,
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    if not ai_feature_enabled("question_bank_assistant"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Question bank assistant is disabled")
    invalid_types = [item for item in payload.question_types if item not in OBJECTIVE_TYPES]
    if invalid_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported question types: {invalid_types}")
    if payload.intent == "repair_question" and not payload.question_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="question_id is required for repair suggestions")
    rag_gate = _ensure_question_workbench_rag_ready()

    with db_session() as session:
        experiment = _ensure_experiment(session, payload.experiment_id)
        target_question = None
        if payload.question_id:
            target_question = (
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
                    {"id": payload.question_id},
                )
                .mappings()
                .first()
            )
            if not target_question:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
            target_question = dict(target_question)
            if target_question.get("experiment_id") != payload.experiment_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question does not belong to experiment")

        points = _experiment_video_points(experiment, _list_experiment_video_resources(payload.experiment_id))
        selected_points = _select_suggestion_points(
            points=points,
            point_keys=_unique_point_keys(payload.point_keys, payload.point_key),
            target_question=target_question,
        )
        selected_point = selected_points[0] if selected_points else None
        target_point_keys = _unique_point_keys([point.get("point_key") for point in selected_points], payload.point_key)
        evidence_package = _load_workbench_evidence_package(
            session,
            experiment=experiment,
            prompt=payload.prompt,
            target_question=target_question,
            target_points=selected_points,
            rag_gate=rag_gate,
        )
        source_refs = list(evidence_package.get("source_refs") or [])
        if not source_refs:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No usable evidence was found for this experiment and point context; AI question suggestions are blocked.",
            )
        ai_settings = effective_ai_settings(get_settings())
        generated = _try_openai_point_aware_suggestions(
            request=payload,
            experiment=experiment,
            point=selected_point,
            target_question=target_question,
            source_refs=source_refs,
        )
        mode = "openai_sdk" if generated else "local_template"
        if not generated:
            generated = _local_point_aware_suggestions(
                request=payload,
                experiment=experiment,
                point=selected_point,
                target_question=target_question,
            )
        warning = "" if source_refs else "No source refs found; teacher review is required before publication."
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
                    "experiment_id": payload.experiment_id,
                    "prompt": payload.prompt,
                    "question_types": payload.question_types,
                    "difficulty": payload.difficulty,
                    "requested_count": payload.count,
                    "provider": "openai" if mode == "openai_sdk" else "local",
                    "model": ai_settings.agent_llm_model or os.getenv("OPENAI_MODEL", ""),
                    "mode": mode,
                    "rag_sources": _json_array(source_refs),
                    "warning": warning,
                    "created_by": user.id,
                    "metadata": _json(
                        {
                            "point_aware_suggestion": True,
                            "intent": payload.intent,
                            "point_key": selected_point.get("point_key") if selected_point else None,
                            "point_keys": target_point_keys,
                            "question_id": payload.question_id,
                            "rag_gate": rag_gate,
                            "evidence_package": evidence_package,
                        }
                    ),
                },
            ).scalar_one()
        )
        drafts: list[dict[str, Any]] = []
        for index, row in enumerate(generated[: payload.count]):
            row_payload = _with_point_aware_metadata(
                row={**row, "status": "draft", "difficulty": row.get("difficulty") or payload.difficulty or "basic"},
                request=payload,
                experiment=experiment,
                point=selected_point,
                source_refs=source_refs,
                target_question=target_question,
                index=index,
            )
            normalized, errors = _validate_question_payload(row_payload)
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
                        "experiment_id": payload.experiment_id,
                        "payload": _json(normalized or row_payload),
                        "errors": _json_array(errors),
                    },
                )
                .mappings()
                .one()
            )
            drafts.append(draft)

    return {
        "generation_id": generation_id,
        "mode": mode,
        "warning": warning,
        "source_refs": source_refs,
        "evidence_package": evidence_package,
        "drafts": drafts,
        "target": {
            "intent": payload.intent,
            "experiment_id": payload.experiment_id,
            "question_id": payload.question_id,
            "point": selected_point,
            "points": selected_points,
        },
    }


@admin_router.post("/question-banks/generate")
async def admin_generate_questions(
    payload: GenerationRequest,
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    if not ai_feature_enabled("question_bank_assistant"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="题库助手当前未启用。")
    invalid_types = [item for item in payload.question_types if item not in OBJECTIVE_TYPES]
    if invalid_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported question types: {invalid_types}")
    rag_gate = _ensure_question_workbench_rag_ready()
    with db_session() as session:
        experiment = _ensure_experiment(session, payload.experiment_id)
        evidence_package = _load_workbench_evidence_package(
            session,
            experiment=experiment,
            prompt=payload.prompt,
            target_question={
                "related_chapter_ids": payload.chapter_ids,
                "related_knowledge_point_ids": payload.knowledge_point_ids,
            },
            target_points=[],
            rag_gate=rag_gate,
        )
        source_refs = list(evidence_package.get("source_refs") or [])
        if not source_refs:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No usable evidence was found for this experiment context; AI question generation is blocked.",
            )
        warning = "" if source_refs else "当前实验资料尚未充分入库，已使用实验目录与理论章节信息生成草稿，发布前必须人工核验。"
        ai_settings = effective_ai_settings(get_settings())
        generated = _try_openai_generation(experiment=experiment, request=payload, source_refs=source_refs)
        mode = "openai_sdk" if generated else "local_template"
        if not generated:
            generated = _local_generated_questions(experiment=experiment, request=payload, source_refs=source_refs)
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
                    "experiment_id": payload.experiment_id,
                    "prompt": payload.prompt,
                    "question_types": payload.question_types,
                    "difficulty": payload.difficulty,
                    "requested_count": payload.count,
                    "provider": "openai" if mode == "openai_sdk" else "local",
                    "model": ai_settings.agent_llm_model or os.getenv("OPENAI_MODEL", ""),
                    "mode": mode,
                    "rag_sources": _json_array(source_refs),
                    "warning": warning,
                    "created_by": user.id,
                    "metadata": _json(
                        {
                            "chapter_ids": payload.chapter_ids,
                            "knowledge_point_ids": payload.knowledge_point_ids,
                            "rag_gate": rag_gate,
                            "evidence_package": evidence_package,
                        }
                    ),
                },
            ).scalar_one()
        )
        drafts: list[dict[str, Any]] = []
        for row in generated[: payload.count]:
            row_payload = {
                **row,
                "difficulty": row.get("difficulty") or payload.difficulty or "basic",
                "source_refs": row.get("source_refs") or source_refs,
                "status": "draft",
            }
            normalized, errors = _validate_question_payload(row_payload)
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
                        "experiment_id": payload.experiment_id,
                        "payload": _json(normalized or row_payload),
                        "errors": _json_array(errors),
                    },
                )
                .mappings()
                .one()
            )
            drafts.append(draft)
    return {
        "generation_id": generation_id,
        "mode": mode,
        "warning": warning,
        "source_refs": source_refs,
        "evidence_package": evidence_package,
        "drafts": drafts,
    }


@admin_router.get("/question-banks/drafts")
async def admin_list_question_drafts(
    generation_id: str | None = None,
    experiment_id: str | None = None,
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    filters = ["1 = 1"]
    params: dict[str, Any] = {}
    if generation_id:
        filters.append("d.generation_id = CAST(:generation_id AS uuid)")
        params["generation_id"] = generation_id
    if experiment_id:
        filters.append("d.experiment_id = :experiment_id")
        params["experiment_id"] = experiment_id
    with db_session() as session:
        rows = [
            dict(row)
            for row in session.execute(
                text(
                    f"""
                    SELECT d.*, g.prompt, g.mode, g.warning, fe.code AS experiment_code, fe.title AS experiment_title
                    FROM experiment_question_drafts d
                    JOIN experiment_question_generations g ON g.id = d.generation_id
                    JOIN formal_experiments fe ON fe.id = d.experiment_id
                    WHERE {" AND ".join(filters)}
                    ORDER BY d.created_at DESC
                    """
                ),
                params,
            )
            .mappings()
            .all()
        ]
    return {"items": rows, "total": len(rows)}


@admin_router.patch("/question-banks/drafts/{draft_id}")
async def admin_update_question_draft(
    payload: DraftUpdateRequest,
    draft_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    normalized, errors = _validate_question_payload({**payload.payload, "status": "draft"})
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    UPDATE experiment_question_drafts
                    SET payload = CAST(:payload AS jsonb),
                        validation_errors = CAST(:errors AS jsonb),
                        status = COALESCE(:status, status),
                        updated_at = now()
                    WHERE id = CAST(:id AS uuid)
                    RETURNING *
                    """
                ),
                {
                    "id": draft_id,
                    "payload": _json(normalized or payload.payload),
                    "errors": _json_array(errors),
                    "status": payload.status,
                },
            )
            .mappings()
            .first()
        )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    return dict(row)


@admin_router.post("/question-banks/drafts/{draft_id}/publish")
async def admin_publish_question_draft(
    draft_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    with db_session() as session:
        draft = (
            session.execute(text("SELECT * FROM experiment_question_drafts WHERE id = CAST(:id AS uuid)"), {"id": draft_id})
            .mappings()
            .first()
        )
        if not draft:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
        if draft["status"] != "draft":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only draft questions can be published")
        payload = dict(draft["payload"] or {})
        payload["status"] = "published"
        inserted = _insert_question(
            session,
            experiment_id=draft["experiment_id"],
            payload=payload,
            bank_kind="generated",
            actor_user_id=user.id,
            generation_id=str(draft["generation_id"]),
        )
        session.execute(
            text("UPDATE experiment_question_drafts SET status = 'published', updated_at = now() WHERE id = CAST(:id AS uuid)"),
            {"id": draft_id},
        )
    return inserted


@admin_router.post("/question-banks/drafts/{draft_id}/reject")
async def admin_reject_question_draft(
    draft_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    UPDATE experiment_question_drafts
                    SET status = 'rejected', updated_at = now()
                    WHERE id = CAST(:id AS uuid)
                    RETURNING *
                    """
                ),
                {"id": draft_id},
            )
            .mappings()
            .first()
        )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    return dict(row)


def _attempt_primary_points(attempt: dict[str, Any]) -> list[dict[str, Any]]:
    metadata = attempt.get("metadata") if isinstance(attempt.get("metadata"), dict) else {}
    question_metadata = attempt.get("question_metadata") if isinstance(attempt.get("question_metadata"), dict) else {}
    points = metadata.get("primary_points") or question_metadata.get("primary_points") or []
    if points:
        return [item for item in points if isinstance(item, dict) and item.get("point_key")]
    keys = metadata.get("primary_point_keys") or question_metadata.get("primary_point_keys") or []
    return [{"point_key": str(key), "point_title": str(key)} for key in keys if str(key).strip()]


def _class_students(session: Any, class_id: str) -> list[dict[str, Any]]:
    rows = [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT re.student_id, re.student_name, re.status, re.class_id
                FROM roster_entries re
                WHERE re.class_id = :class_id
                  AND re.status <> 'disabled'
                UNION
                SELECT sp.student_id, sp.student_name, au.status, sp.class_id
                FROM student_profiles sp
                JOIN app_users au ON au.id = sp.user_id
                WHERE sp.class_id = :class_id
                  AND au.status <> 'disabled'
                ORDER BY student_id
                """
            ),
            {"class_id": class_id},
        )
        .mappings()
        .all()
    ]
    return rows


@admin_router.get("/analytics/classes/{class_id}/dashboard")
async def admin_class_dashboard(
    class_id: str = Path(min_length=1),
    experiment_id: str | None = None,
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    _require_class_access(class_id, user)
    with db_session() as session:
        students = _class_students(session, class_id)
        experiments = _list_experiments(status_filter="published")
        if experiment_id:
            experiments = [item for item in experiments if item["id"] == experiment_id]
        progress_rows = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT *
                    FROM student_experiment_progress
                    WHERE class_id = :class_id
                    """
                ),
                {"class_id": class_id},
            )
            .mappings()
            .all()
        ]
        attempt_rows = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT student_id, experiment_id, AVG(score) AS average_item_score, COUNT(*) AS attempt_count
                    FROM experiment_question_attempts
                    WHERE class_id = :class_id
                    GROUP BY student_id, experiment_id
                    """
                ),
                {"class_id": class_id},
            )
            .mappings()
            .all()
        ]
        recent = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT se.student_id, COALESCE(sp.student_name, se.student_id) AS student_name,
                           se.event_type, se.chapter_id, se.experiment_id, se.metadata, se.created_at
                    FROM student_events se
                    LEFT JOIN student_profiles sp ON sp.student_id = se.student_id
                    WHERE sp.class_id = :class_id OR se.student_id IN (
                      SELECT student_id FROM roster_entries WHERE class_id = :class_id
                    )
                    ORDER BY se.created_at DESC
                    LIMIT 20
                    """
                ),
                {"class_id": class_id},
            )
            .mappings()
            .all()
        ]
    progress_by_key = {(row["student_id"], row["experiment_id"]): row for row in progress_rows}
    attempts_by_key = {(row["student_id"], row["experiment_id"]): row for row in attempt_rows}
    matrix: list[dict[str, Any]] = []
    completed_cells = 0
    scored_cells: list[float] = []
    active_students: set[str] = set()
    for student in students:
        experiment_states: dict[str, Any] = {}
        for experiment in experiments:
            key = (student["student_id"], experiment["id"])
            progress = progress_by_key.get(key)
            attempt = attempts_by_key.get(key)
            if progress or attempt:
                active_students.add(student["student_id"])
            status_value = progress.get("status") if progress else "not_started"
            if status_value == "completed":
                completed_cells += 1
            score_value = float(progress["best_score"]) if progress and progress.get("best_score") is not None else None
            if score_value is not None:
                scored_cells.append(score_value)
            experiment_states[experiment["id"]] = {
                "status": status_value,
                "completion_percent": float(progress["completion_percent"]) if progress else 0,
                "best_score": score_value,
                "attempt_count": int(attempt["attempt_count"]) if attempt else 0,
            }
        matrix.append({**student, "experiments": experiment_states})
    total_cells = max(1, len(students) * len(experiments))
    missing_students = [row for row in matrix if all(cell["status"] == "not_started" for cell in row["experiments"].values())]
    return {
        "class_id": class_id,
        "metrics": {
            "class_size": len(students),
            "active_students": len(active_students),
            "published_experiments": len(experiments),
            "completion_rate": round(100 * completed_cells / total_cells, 2),
            "average_score": round(sum(scored_cells) / len(scored_cells), 2) if scored_cells else 0,
            "missing_students": len(missing_students),
        },
        "experiments": experiments,
        "matrix": matrix,
        "recent_activity": recent,
        "missing_students": missing_students,
    }


@admin_router.get("/analytics/classes/{class_id}/students/{student_id}")
async def admin_student_report(
    class_id: str = Path(min_length=1),
    student_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    _require_class_access(class_id, user)
    with db_session() as session:
        student = (
            session.execute(
                text(
                    """
                    SELECT sp.student_id, sp.student_name, sp.class_id, c.class_name
                    FROM student_profiles sp
                    LEFT JOIN classes c ON c.id = sp.class_id
                    WHERE sp.student_id = :student_id
                    UNION
                    SELECT re.student_id, re.student_name, re.class_id, c.class_name
                    FROM roster_entries re
                    LEFT JOIN classes c ON c.id = re.class_id
                    WHERE re.student_id = :student_id
                    LIMIT 1
                    """
                ),
                {"student_id": student_id},
            )
            .mappings()
            .first()
        )
        if not student:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
        progress = [
            dict(row)
            for row in session.execute(
                text("SELECT * FROM student_experiment_progress WHERE student_id = :student_id ORDER BY updated_at DESC"),
                {"student_id": student_id},
            )
            .mappings()
            .all()
        ]
        attempts = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT a.*, q.stem, q.related_knowledge_point_ids, q.metadata AS question_metadata,
                           fe.code AS experiment_code, fe.title AS experiment_title
                    FROM experiment_question_attempts a
                    LEFT JOIN experiment_questions q ON q.id = a.question_id
                    LEFT JOIN formal_experiments fe ON fe.id = a.experiment_id
                    WHERE a.student_id = :student_id
                    ORDER BY a.created_at DESC
                    LIMIT 200
                    """
                ),
                {"student_id": student_id},
            )
            .mappings()
            .all()
        ]
        timeline = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT id, event_type, chapter_id, experiment_id, question_id, difficulty, correct, metadata, created_at
                    FROM student_events
                    WHERE student_id = :student_id
                    ORDER BY created_at DESC
                    LIMIT 200
                    """
                ),
                {"student_id": student_id},
            )
            .mappings()
            .all()
        ]
    weak_points: dict[str, dict[str, Any]] = {}
    weak_video_points: dict[str, dict[str, Any]] = {}
    for attempt in attempts:
        if attempt.get("correct") is True:
            continue
        for point in _attempt_primary_points(attempt):
            point_key = str(point.get("point_key") or "")
            if not point_key:
                continue
            weak_video_points.setdefault(
                point_key,
                {
                    "point_key": point_key,
                    "point_title": point.get("point_title") or point_key,
                    "experiment_id": attempt.get("experiment_id"),
                    "experiment_code": attempt.get("experiment_code"),
                    "experiment_title": attempt.get("experiment_title"),
                    "incorrect_count": 0,
                },
            )
            weak_video_points[point_key]["incorrect_count"] += 1
        kp_ids = attempt.get("related_knowledge_point_ids") or []
        if not kp_ids:
            weak_points.setdefault("unmapped", {"knowledge_point_id": None, "title": "未映射理论 KP", "incorrect_count": 0})
            weak_points["unmapped"]["incorrect_count"] += 1
            continue
        for kp_id in kp_ids:
            weak_points.setdefault(kp_id, {"knowledge_point_id": kp_id, "title": kp_id, "incorrect_count": 0})
            weak_points[kp_id]["incorrect_count"] += 1
    return {
        "student": dict(student),
        "progress": progress,
        "attempts": attempts,
        "weak_points": sorted(weak_points.values(), key=lambda row: row["incorrect_count"], reverse=True),
        "weak_video_points": sorted(weak_video_points.values(), key=lambda row: row["incorrect_count"], reverse=True),
        "timeline": timeline,
    }


@admin_router.get("/analytics/classes/{class_id}/weak-points")
async def admin_class_weak_points(
    class_id: str = Path(min_length=1),
    experiment_id: str | None = None,
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    _require_class_access(class_id, user)
    params: dict[str, Any] = {"class_id": class_id}
    filter_sql = "a.class_id = :class_id"
    if experiment_id:
        filter_sql += " AND a.experiment_id = :experiment_id"
        params["experiment_id"] = experiment_id
    with db_session() as session:
        rows = [
            dict(row)
            for row in session.execute(
                text(
                    f"""
                    SELECT a.experiment_id, fe.code AS experiment_code, fe.title AS experiment_title,
                           a.question_id, q.stem, q.related_chapter_ids, q.related_knowledge_point_ids,
                           COUNT(*) AS attempt_count,
                           COUNT(*) FILTER (WHERE a.correct IS FALSE) AS incorrect_count
                    FROM experiment_question_attempts a
                    LEFT JOIN experiment_questions q ON q.id = a.question_id
                    LEFT JOIN formal_experiments fe ON fe.id = a.experiment_id
                    WHERE {filter_sql}
                    GROUP BY a.experiment_id, fe.code, fe.title, a.question_id, q.stem,
                             q.related_chapter_ids, q.related_knowledge_point_ids
                    ORDER BY incorrect_count DESC, attempt_count DESC
                    LIMIT 100
                    """
                ),
                params,
            )
            .mappings()
            .all()
        ]
        point_attempts = [
            dict(row)
            for row in session.execute(
                text(
                    f"""
                    SELECT a.experiment_id,
                           fe.code AS experiment_code,
                           fe.title AS experiment_title,
                           a.question_id,
                           q.stem,
                           a.correct,
                           a.metadata,
                           q.metadata AS question_metadata
                    FROM experiment_question_attempts a
                    LEFT JOIN experiment_questions q ON q.id = a.question_id
                    LEFT JOIN formal_experiments fe ON fe.id = a.experiment_id
                    WHERE {filter_sql}
                    ORDER BY a.created_at DESC
                    LIMIT 1000
                    """
                ),
                params,
            )
            .mappings()
            .all()
        ]
    items: list[dict[str, Any]] = []
    for row in rows:
        kp_ids = row.get("related_knowledge_point_ids") or []
        items.append(
            {
                **row,
                "weak_kp_ids": kp_ids,
                "unmapped": not bool(kp_ids),
                "incorrect_rate": round(100 * int(row["incorrect_count"]) / max(1, int(row["attempt_count"])), 2),
            }
        )
    point_items_by_key: dict[str, dict[str, Any]] = {}
    for attempt in point_attempts:
        points = _attempt_primary_points(attempt)
        if not points:
            continue
        selected_link = None
        metadata = attempt.get("metadata") if isinstance(attempt.get("metadata"), dict) else {}
        if isinstance(metadata.get("selected_option_link"), dict):
            selected_link = metadata["selected_option_link"]
        for point in points:
            point_key = str(point.get("point_key") or "")
            if not point_key:
                continue
            item = point_items_by_key.setdefault(
                point_key,
                {
                    "point_key": point_key,
                    "point_title": point.get("point_title") or point_key,
                    "experiment_id": attempt.get("experiment_id"),
                    "experiment_code": attempt.get("experiment_code"),
                    "experiment_title": attempt.get("experiment_title"),
                    "attempt_count": 0,
                    "incorrect_count": 0,
                    "representative_questions": [],
                    "selected_option_links": [],
                    "kp_unmapped": True,
                },
            )
            item["attempt_count"] += 1
            if attempt.get("correct") is False:
                item["incorrect_count"] += 1
                if attempt.get("stem") and len(item["representative_questions"]) < 3:
                    item["representative_questions"].append(
                        {"question_id": str(attempt.get("question_id") or ""), "stem": attempt.get("stem")}
                    )
                if selected_link and len(item["selected_option_links"]) < 10:
                    item["selected_option_links"].append(selected_link)
    point_items = []
    for item in point_items_by_key.values():
        item["incorrect_rate"] = round(100 * int(item["incorrect_count"]) / max(1, int(item["attempt_count"])), 2)
        point_items.append(item)
    point_items.sort(key=lambda row: (row["incorrect_count"], row["attempt_count"]), reverse=True)
    return {"items": items, "total": len(items), "point_items": point_items, "point_total": len(point_items)}


@admin_router.get("/analytics/classes/{class_id}/export")
async def admin_export_class_report(
    class_id: str = Path(min_length=1),
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> Response:
    dashboard = await admin_class_dashboard(class_id=class_id, user=user)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["class_id", "student_id", "student_name", "experiment_id", "experiment_code", "completion", "score"])
    experiments_by_id = {item["id"]: item for item in dashboard["experiments"]}
    for student in dashboard["matrix"]:
        for experiment_id, state in student["experiments"].items():
            experiment = experiments_by_id.get(experiment_id, {})
            writer.writerow(
                [
                    class_id,
                    student["student_id"],
                    student["student_name"],
                    experiment_id,
                    experiment.get("code"),
                    state["status"],
                    state["best_score"] if state["best_score"] is not None else "",
                ]
            )
    return Response(
        content=output.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="class-{class_id}-experiment-report.csv"'},
    )
