from __future__ import annotations

import csv
import hashlib
import io
import json
import os
import re
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, Path, Query, Response, UploadFile, status
from pydantic import BaseModel, Field
from sqlalchemy import text

from server.app import data_loader
from server.app.auth import AuthUser, require_roles
from server.app.config import get_settings
from server.app.database import db_session
from server.app.media import create_media_asset, create_media_binding
from server.app.platform_settings import ai_feature_enabled, effective_ai_settings
from server.app.retrieval import keyword_score

admin_router = APIRouter(prefix="/api/admin", tags=["experiment-admin"])
student_router = APIRouter(prefix="/api", tags=["experiment-learning"])

OBJECTIVE_TYPES = {"single_choice", "true_false", "fill_blank"}
QUESTION_STATUSES = {"draft", "published", "disabled", "archived"}


class ExperimentChapterBinding(BaseModel):
    chapter_id: str = Field(min_length=1)
    coverage_type: str = Field(default="primary", pattern="^(primary|partial|supporting)$")
    notes: str | None = None
    sort_order: int = 0


class ExperimentCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    summary: str | None = None
    status: str = Field(default="draft", pattern="^(draft|published|archived)$")
    chapter_ids: list[str] = Field(default_factory=list)


class ExperimentUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    summary: str | None = None
    status: str | None = Field(default=None, pattern="^(draft|published|archived)$")
    chapter_ids: list[str] | None = None
    chapter_bindings: list[ExperimentChapterBinding] | None = None


class QuestionRequest(BaseModel):
    experiment_id: str = Field(min_length=1)
    question_type: str = Field(pattern="^(single_choice|true_false|fill_blank)$")
    stem: str = Field(min_length=1)
    options: list[Any] = Field(default_factory=list)
    answer: Any
    explanation: str | None = None
    difficulty: str | None = "basic"
    related_chapter_ids: list[str] = Field(default_factory=list)
    related_knowledge_point_ids: list[str] = Field(default_factory=list)
    source_chunk_ids: list[str] = Field(default_factory=list)
    source_refs: list[dict[str, Any]] = Field(default_factory=list)
    status: str = Field(default="draft", pattern="^(draft|published|disabled|archived)$")
    bank_kind: str = Field(default="manual", pattern="^(default|generated|manual)$")


class QuestionUpdateRequest(BaseModel):
    stem: str | None = Field(default=None, min_length=1)
    options: list[Any] | None = None
    answer: Any | None = None
    explanation: str | None = None
    difficulty: str | None = None
    related_chapter_ids: list[str] | None = None
    related_knowledge_point_ids: list[str] | None = None
    source_chunk_ids: list[str] | None = None
    source_refs: list[dict[str, Any]] | None = None
    status: str | None = Field(default=None, pattern="^(draft|published|disabled|archived)$")


class GenerationRequest(BaseModel):
    experiment_id: str = Field(min_length=1)
    prompt: str = Field(min_length=1, max_length=2000)
    question_types: list[str] = Field(default_factory=lambda: ["single_choice", "true_false", "fill_blank"])
    count: int = Field(default=5, ge=1, le=20)
    difficulty: str | None = "basic"
    chapter_ids: list[str] = Field(default_factory=list)
    knowledge_point_ids: list[str] = Field(default_factory=list)


class QuestionBankAssistantRequest(BaseModel):
    intent: str = Field(default="add_questions", pattern="^(add_questions|repair_question|coverage_check|disable_question)$")
    prompt: str = Field(min_length=1, max_length=2000)
    chapter_id: str | None = None
    experiment_id: str | None = None
    question_id: str | None = None
    question_types: list[str] = Field(default_factory=lambda: ["single_choice", "true_false", "fill_blank"])
    count: int = Field(default=5, ge=1, le=20)
    difficulty: str | None = "basic"


class DraftUpdateRequest(BaseModel):
    payload: dict[str, Any] = Field(default_factory=dict)
    status: str | None = Field(default=None, pattern="^(draft|published|rejected)$")


class ExperimentAnswer(BaseModel):
    question_id: str = Field(min_length=1)
    answer: Any


class ExperimentQuestionSubmitRequest(BaseModel):
    student_id: str = Field(min_length=1)
    experiment_id: str = Field(min_length=1)
    attempt_kind: str = "practice"
    answers: list[ExperimentAnswer]


class ExperimentExistingVideoBindRequest(BaseModel):
    media_asset_id: str = Field(min_length=1)
    title: str | None = None
    status: str = Field(default="draft", pattern="^(draft|published)$")
    point_key: str | None = None
    point_title: str | None = None


class ExperimentVideoPointResourceRequest(BaseModel):
    media_asset_id: str = Field(min_length=1)
    title: str | None = None
    status: str = Field(default="draft", pattern="^(draft|published)$")


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False)


def _json_array(value: Any) -> str:
    return json.dumps(value if value is not None else [], ensure_ascii=False)


def _dump(model: BaseModel) -> dict[str, Any]:
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()


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
    filters = ["mb.target_type = 'experiment'"]
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
                           ma.mime_type, ma.file_size_bytes, ma.upload_status, ma.error_reason,
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
                  source_chunk_ids, source_refs, status, created_by, published_by, published_at, updated_at
                )
                VALUES (
                  CAST(:bank_id AS uuid), :experiment_id, CAST(:generation_id AS uuid),
                  :question_type, :stem, CAST(:options AS jsonb), CAST(:answer AS jsonb),
                  :explanation, :difficulty, :related_chapter_ids, :related_knowledge_point_ids,
                  :source_chunk_ids, CAST(:source_refs AS jsonb), :status,
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
}
GENERAL_RESOURCE_AREA_ID = "general"
GENERAL_RESOURCE_AREA_NAME = "通识资源"


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


def _count_questions_by_chapter_and_experiment(
    questions: list[dict[str, Any]],
    bindings_by_experiment: dict[str, list[str]],
) -> tuple[dict[str, int], dict[str, int], int]:
    by_chapter_sets: dict[str, set[str]] = defaultdict(set)
    by_experiment_sets: dict[str, set[str]] = defaultdict(set)
    all_question_ids: set[str] = set()
    for question in questions:
        status_value = str(question.get("status") or "")
        if status_value and status_value != "published":
            continue
        if not status_value and question.get("student_visible") is False:
            continue
        question_id = _question_row_id(question)
        if not question_id:
            continue
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
        elif chapter_ids:
            all_question_ids.add(question_id)
        else:
            continue
        if experiment_ids and not chapter_ids:
            chapter_ids = sorted({chapter_id for experiment_id in experiment_ids for chapter_id in bindings_by_experiment.get(experiment_id, [])})
        for chapter_id in chapter_ids:
            by_chapter_sets[chapter_id].add(question_id)
    return (
        {chapter_id: len(question_ids) for chapter_id, question_ids in by_chapter_sets.items()},
        {experiment_id: len(question_ids) for experiment_id, question_ids in by_experiment_sets.items()},
        len(all_question_ids),
    )


def _build_learning_resource_overview(
    *,
    chapters: list[dict[str, Any]],
    units: list[dict[str, Any]],
    knowledge_points: list[dict[str, Any]],
    experiments: list[dict[str, Any]],
    questions: list[dict[str, Any]],
    bindings_by_experiment: dict[str, list[str]],
) -> dict[str, Any]:
    question_counts_by_chapter, question_counts_by_experiment, total_published_questions = _count_questions_by_chapter_and_experiment(
        questions, bindings_by_experiment
    )

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
            "media_count": 0,
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
        for index, media_resource in enumerate(media_resources):
            if isinstance(media_resource, dict):
                media_id = str(
                    media_resource.get("media_id")
                    or media_resource.get("binding_id")
                    or media_resource.get("id")
                    or f"{experiment_id}:{index}"
                )
            else:
                media_id = f"{experiment_id}:{index}"
            all_media_ids.add(media_id)
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
                    "question_count": int(question_counts_by_experiment.get(experiment_id, 0)),
                }
            )
            group["experiment_count"] += 1
            group["media_count"] += experiment_media_count

    area_order = ["p", "s", "ds", "d", "f", GENERAL_RESOURCE_AREA_ID, "other"]
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
                },
            },
        )
        area["group_ids"].append(group["id"])
        area["metrics"]["group_count"] += 1
        for key in ("knowledge_unit_count", "knowledge_point_count", "experiment_count", "question_count", "media_count"):
            area["metrics"][key] += int(group.get(key) or 0)

    areas = sorted(area_by_id.values(), key=lambda item: (area_order.index(item["area_id"]) if item["area_id"] in area_order else 99, item["area_name"]))
    metrics = {
        "knowledge_unit_count": sum(int(group.get("knowledge_unit_count") or 0) for group in groups),
        "knowledge_point_count": sum(int(group.get("knowledge_point_count") or 0) for group in groups),
        "experiment_count": len(all_experiment_ids),
        "media_resource_count": len(all_media_ids),
        "question_count": total_published_questions,
    }
    return {"metrics": metrics, "areas": areas, "groups": groups}


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


def _json_learning_resource_overview() -> dict[str, Any]:
    experiments: list[dict[str, Any]] = []
    bindings_by_experiment: dict[str, list[str]] = {}
    experiment_ids: set[str] = set()
    for experiment in data_loader.experiments():
        experiment_id = str(experiment.get("id") or experiment.get("experiment_id") or "")
        chapter_id = str(experiment.get("normalized_chapter_id") or experiment.get("chapter_id") or "")
        if not experiment_id or not chapter_id:
            continue
        experiment_ids.add(experiment_id)
        media_resources = []
        if experiment.get("video_url") and str(experiment.get("media_status") or "") in {"ready", "published"}:
            media_resources.append(
                {
                    "media_id": experiment_id,
                    "title": experiment.get("name") or experiment_id,
                }
            )
        experiments.append(
            {
                "id": experiment_id,
                "code": experiment.get("code") or "",
                "title": experiment.get("name") or experiment.get("normalized_name") or experiment_id,
                "status": "published" if experiment.get("student_visible", True) else "draft",
                "display_order": experiment.get("display_order"),
                "chapter_bindings": [{"chapter_id": chapter_id}],
                "media_resources": media_resources,
            }
        )
        bindings_by_experiment[experiment_id] = [chapter_id]

    experiment_questions: list[dict[str, Any]] = []
    for question in data_loader.questions():
        related_experiment_ids = [
            str(experiment_id)
            for experiment_id in question.get("related_experiment_ids") or []
            if str(experiment_id) in experiment_ids
        ]
        if not related_experiment_ids and str(question.get("experiment_id") or "") not in experiment_ids:
            continue
        item = dict(question)
        item["related_experiment_ids"] = related_experiment_ids
        experiment_questions.append(item)

    return _build_learning_resource_overview(
        chapters=data_loader.chapters(),
        units=data_loader.units(),
        knowledge_points=data_loader.knowledge_points(),
        experiments=experiments,
        questions=experiment_questions,
        bindings_by_experiment=bindings_by_experiment,
    )


@admin_router.get("/learning-resources/overview")
async def admin_learning_resources_overview(
    user: AuthUser = Depends(require_roles("admin", "teacher")),
) -> dict[str, Any]:
    if get_settings().data_backend == "json":
        return _json_learning_resource_overview()

    with db_session() as session:
        chapters = _list_learning_resource_chapters(session)
        units = _list_learning_resource_units(session)
        knowledge_points = _list_learning_resource_kps(session)
        experiments = _list_learning_resource_experiments(session)
        bindings_by_experiment = _question_bank_bindings_by_experiment(session)
        questions = _list_question_bank_question_rows(session)
    return _build_learning_resource_overview(
        chapters=chapters,
        units=units,
        knowledge_points=knowledge_points,
        experiments=experiments,
        questions=questions,
        bindings_by_experiment=bindings_by_experiment,
    )


def _load_chapter_source_refs(session: Any, *, chapter_id: str | None, prompt: str, limit: int = 6) -> list[dict[str, Any]]:
    if not chapter_id:
        return []
    rows = [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT sc.id AS chunk_id, sc.text, sc.markdown, sc.chapter_id, sc.page_number,
                       sc.section_title, sd.file_name AS source_file
                FROM source_chunks sc
                LEFT JOIN source_documents sd ON sd.id = sc.document_id
                WHERE sc.chapter_id = :chapter_id
                  AND COALESCE(sc.content_status, 'published') = 'published'
                ORDER BY sc.document_id, sc.chunk_index
                LIMIT 120
                """
            ),
            {"chapter_id": chapter_id},
        )
        .mappings()
        .all()
    ]
    rows.sort(
        key=lambda row: keyword_score(prompt, {"text": row.get("text") or row.get("markdown") or ""}, chapter_id=row.get("chapter_id")),
        reverse=True,
    )
    return [
        {
            "chunk_id": row.get("chunk_id"),
            "source_file": row.get("source_file"),
            "chapter_id": row.get("chapter_id"),
            "page_number": row.get("page_number"),
            "section_title": row.get("section_title"),
            "text_preview": " ".join((row.get("text") or row.get("markdown") or "").split())[:360],
        }
        for row in rows[:limit]
    ]


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
                           COUNT(q.id) FILTER (WHERE q.status = 'draft') AS draft_count
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
    filters = ["COALESCE(sc.content_status, 'published') = 'published'"]
    params: dict[str, Any] = {}
    if chapter_ids:
        filters.append("sc.chapter_id = ANY(:chapter_ids)")
        params["chapter_ids"] = chapter_ids
    if knowledge_point_ids:
        filters.append("sc.related_knowledge_point_ids && :knowledge_point_ids")
        params["knowledge_point_ids"] = knowledge_point_ids
    rows = [
        dict(row)
        for row in session.execute(
            text(
                f"""
                SELECT sc.id AS chunk_id, sc.text, sc.markdown, sc.chapter_id, sc.page_number,
                       sc.section_title, sc.related_knowledge_point_ids, sc.related_experiment_ids,
                       sd.file_name AS source_file
                FROM source_chunks sc
                LEFT JOIN source_documents sd ON sd.id = sc.document_id
                WHERE {" AND ".join(filters)}
                ORDER BY sc.document_id, sc.chunk_index
                LIMIT 200
                """
            ),
            params,
        )
        .mappings()
        .all()
    ]
    query = " ".join([prompt, experiment.get("title") or "", experiment.get("summary") or ""])
    rows.sort(key=lambda row: keyword_score(query, {"text": row.get("text") or row.get("markdown") or ""}, chapter_id=row.get("chapter_id")), reverse=True)
    return [
        {
            "chunk_id": row.get("chunk_id"),
            "source_file": row.get("source_file"),
            "chapter_id": row.get("chapter_id"),
            "page_number": row.get("page_number"),
            "section_title": row.get("section_title"),
            "text_preview": " ".join((row.get("text") or row.get("markdown") or "").split())[:360],
        }
        for row in rows[:limit]
    ]


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
    with db_session() as session:
        experiment = _ensure_experiment(session, payload.experiment_id)
        source_refs = _load_generation_sources(
            session,
            experiment=experiment,
            prompt=payload.prompt,
            chapter_ids=payload.chapter_ids,
            knowledge_point_ids=payload.knowledge_point_ids,
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
                    "metadata": _json({"chapter_ids": payload.chapter_ids, "knowledge_point_ids": payload.knowledge_point_ids}),
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
    return {"generation_id": generation_id, "mode": mode, "warning": warning, "source_refs": source_refs, "drafts": drafts}


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


def _grade_answer(question_type: str, expected: dict[str, Any], submitted: Any) -> bool:
    if question_type == "single_choice":
        return str(submitted).strip().lower() == str(expected.get("value") or "").strip().lower()
    if question_type == "true_false":
        try:
            submitted_norm = _normalize_answer("true_false", submitted)["value"]
        except ValueError:
            return False
        return bool(submitted_norm) is bool(expected.get("value"))
    if question_type == "fill_blank":
        submitted_text = str(submitted).strip().lower()
        return submitted_text in {str(item).strip().lower() for item in expected.get("accepted_answers") or []}
    return False


@student_router.post("/experiment-questions/submit")
async def submit_experiment_questions(payload: ExperimentQuestionSubmitRequest) -> dict[str, Any]:
    answer_lookup = {answer.question_id: answer.answer for answer in payload.answers}
    with db_session() as session:
        student = (
            session.execute(
                text(
                    """
                    SELECT sp.student_id, sp.student_name, sp.class_id, sp.user_id, c.class_name
                    FROM student_profiles sp
                    LEFT JOIN classes c ON c.id = sp.class_id
                    WHERE sp.student_id = :student_id
                    UNION
                    SELECT re.student_id, re.student_name, re.class_id, NULL::uuid AS user_id, c.class_name
                    FROM roster_entries re
                    LEFT JOIN classes c ON c.id = re.class_id
                    WHERE re.student_id = :student_id
                      AND re.status <> 'disabled'
                    ORDER BY class_id NULLS LAST
                    LIMIT 1
                    """
                ),
                {"student_id": payload.student_id},
            )
            .mappings()
            .first()
        )
        class_id = student["class_id"] if student else None
        session.execute(
            text(
                """
                INSERT INTO students (
                  id, display_name, class_name, user_id, student_id, class_id, status, updated_at
                )
                VALUES (
                  :student_id, :display_name, :class_name, CAST(:user_id AS uuid),
                  :student_id, :class_id, 'active', now()
                )
                ON CONFLICT (id) DO UPDATE SET
                  display_name = COALESCE(EXCLUDED.display_name, students.display_name),
                  class_name = COALESCE(EXCLUDED.class_name, students.class_name),
                  user_id = COALESCE(EXCLUDED.user_id, students.user_id),
                  student_id = COALESCE(EXCLUDED.student_id, students.student_id),
                  class_id = COALESCE(EXCLUDED.class_id, students.class_id),
                  status = 'active',
                  updated_at = now()
                """
            ),
            {
                "student_id": payload.student_id,
                "display_name": student["student_name"] if student else payload.student_id,
                "class_name": student["class_name"] if student else None,
                "user_id": str(student["user_id"]) if student and student.get("user_id") else None,
                "class_id": class_id,
            },
        )
        questions = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT *
                    FROM experiment_questions
                    WHERE experiment_id = :experiment_id
                      AND status = 'published'
                      AND id = ANY(:question_ids)
                    """
                ),
                {"experiment_id": payload.experiment_id, "question_ids": list(answer_lookup.keys())},
            )
            .mappings()
            .all()
        ]
        correct_count = 0
        for question in questions:
            submitted = answer_lookup.get(str(question["id"]))
            correct = _grade_answer(question["question_type"], question["answer"], submitted)
            correct_count += 1 if correct else 0
            session.execute(
                text(
                    """
                    INSERT INTO experiment_question_attempts (
                      student_id, class_id, experiment_id, question_id, question_type,
                      submitted_answer, correct, score, attempt_kind, metadata
                    )
                    VALUES (
                      :student_id, :class_id, :experiment_id, CAST(:question_id AS uuid), :question_type,
                      CAST(:submitted_answer AS jsonb), :correct, :score, :attempt_kind, '{}'::jsonb
                    )
                    """
                ),
                {
                    "student_id": payload.student_id,
                    "class_id": class_id,
                    "experiment_id": payload.experiment_id,
                    "question_id": str(question["id"]),
                    "question_type": question["question_type"],
                    "submitted_answer": _json({"value": submitted}),
                    "correct": correct,
                    "score": 1 if correct else 0,
                    "attempt_kind": payload.attempt_kind,
                },
            )
        total = len(questions)
        score = round(100 * correct_count / total, 2) if total else 0
        status_value = "completed" if total and score >= 60 else ("needs_attention" if total else "in_progress")
        session.execute(
            text(
                """
                INSERT INTO student_experiment_progress (
                  student_id, class_id, experiment_id, status, completion_percent,
                  best_score, last_activity_at, completed_at, metadata, updated_at
                )
                VALUES (
                  :student_id, :class_id, :experiment_id, :status, :completion_percent,
                  :score, now(), CASE WHEN :status = 'completed' THEN now() ELSE NULL END,
                  CAST(:metadata AS jsonb), now()
                )
                ON CONFLICT (student_id, experiment_id) DO UPDATE SET
                  class_id = EXCLUDED.class_id,
                  status = EXCLUDED.status,
                  completion_percent = GREATEST(student_experiment_progress.completion_percent, EXCLUDED.completion_percent),
                  best_score = GREATEST(COALESCE(student_experiment_progress.best_score, 0), COALESCE(EXCLUDED.best_score, 0)),
                  last_activity_at = now(),
                  completed_at = COALESCE(student_experiment_progress.completed_at, EXCLUDED.completed_at),
                  metadata = EXCLUDED.metadata,
                  updated_at = now()
                """
            ),
            {
                "student_id": payload.student_id,
                "class_id": class_id,
                "experiment_id": payload.experiment_id,
                "status": status_value,
                "completion_percent": 100 if total else 20,
                "score": score,
                "metadata": _json({"correct_count": correct_count, "total_count": total, "attempt_kind": payload.attempt_kind}),
            },
        )
        primary_chapter = session.execute(
            text(
                """
                SELECT chapter_id
                FROM experiment_chapter_bindings
                WHERE experiment_id = :experiment_id
                ORDER BY CASE coverage_type WHEN 'primary' THEN 0 WHEN 'partial' THEN 1 ELSE 2 END, sort_order
                LIMIT 1
                """
            ),
            {"experiment_id": payload.experiment_id},
        ).scalar()
        session.execute(
            text(
                """
                INSERT INTO student_events (
                  student_id, event_type, chapter_id, experiment_id, difficulty,
                  correct, metadata, created_at
                )
                VALUES (
                  :student_id, 'experiment_question_submit', :chapter_id, :experiment_id,
                  'basic', :correct, CAST(:metadata AS jsonb), now()
                )
                """
            ),
            {
                "student_id": payload.student_id,
                "chapter_id": primary_chapter,
                "experiment_id": payload.experiment_id,
                "correct": score >= 60 if total else None,
                "metadata": _json({"score": score, "correct_count": correct_count, "total_count": total}),
            },
        )
    return {"score": score, "correct_count": correct_count, "total_count": total}


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
                    SELECT a.*, q.stem, q.related_knowledge_point_ids, fe.code AS experiment_code, fe.title AS experiment_title
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
    for attempt in attempts:
        if attempt.get("correct") is True:
            continue
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
    return {"items": items, "total": len(items)}


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
