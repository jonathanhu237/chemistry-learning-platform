from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy import text

from server.app.auth import AuthUser
from server.app.config import get_settings
from server.app.database import db_session
from server.app.media import is_student_visible_media
from server.app.normalization import CHAPTER_AREA_MAP
from server.app.student_learning_schemas import (
    StudentExperimentDetailResponse,
    StudentExperimentGroupResponse,
    StudentExperimentGroupSummary,
    StudentExperimentPointSummary,
    StudentLearningArea,
    StudentLearningHomeResponse,
    StudentVideoResource,
)

AREA_ORDER = ["p", "s", "ds", "d", "f"]
AREA_NAMES = {
    "p": "p区",
    "s": "s区",
    "ds": "ds区",
    "d": "d区",
    "f": "f区",
}
PRETEST_AREA_IDS = {
    "p区": "p",
    "s区": "s",
    "ds区": "ds",
    "d区": "d",
    "f区": "f",
}
DEFAULT_RECOMMENDED_AREA_ID = "p"


@dataclass(frozen=True)
class ParentGroup:
    parent_code: str
    parent_title: str
    area_id: str
    area_name: str
    chapter_ids: tuple[str, ...]
    display_order: int
    experiments: tuple[dict[str, Any], ...]


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=str)


def _student_id(user: AuthUser) -> str:
    return str(user.student_id or user.username).strip().upper()


def _chapter_area_id(chapter_id: str | None) -> str | None:
    if not chapter_id:
        return None
    chapter = CHAPTER_AREA_MAP.get(str(chapter_id))
    return str(chapter["area_id"]) if chapter else None


def _chapter_area_name(area_id: str) -> str:
    return AREA_NAMES.get(area_id, area_id)


def _metadata(experiment: dict[str, Any]) -> dict[str, Any]:
    value = experiment.get("metadata")
    return value if isinstance(value, dict) else {}


def _chapter_bindings(experiment: dict[str, Any]) -> list[dict[str, Any]]:
    value = experiment.get("chapter_bindings") or []
    return [item for item in value if isinstance(item, dict)]


def _parent_code(experiment: dict[str, Any]) -> str:
    metadata = _metadata(experiment)
    return str(metadata.get("parent_code") or experiment.get("code") or experiment.get("id"))


def _parent_title(experiment: dict[str, Any]) -> str:
    metadata = _metadata(experiment)
    return str(metadata.get("parent_title") or experiment.get("title") or _parent_code(experiment))


def _module_title(experiment: dict[str, Any]) -> str | None:
    metadata = _metadata(experiment)
    value = metadata.get("module_display_title") or metadata.get("module_title")
    return str(value) if value else None


def _video_candidates(experiment: dict[str, Any]) -> list[str]:
    raw = _metadata(experiment).get("video_candidates") or []
    if not isinstance(raw, list):
        return []
    candidates: list[str] = []
    seen: set[str] = set()
    for item in raw:
        title = str(item or "").strip()
        if title and title not in seen:
            candidates.append(title)
            seen.add(title)
    return candidates


def _media_resources(experiment: dict[str, Any], *, visible_only: bool = False) -> list[dict[str, Any]]:
    resources = experiment.get("media_resources") or []
    items = [item for item in resources if isinstance(item, dict)]
    if not visible_only:
        return items
    return [
        item
        for item in items
        if is_student_visible_media(str(item.get("upload_status") or ""), str(item.get("binding_status") or ""))
    ]


def _published_video_count(experiment: dict[str, Any]) -> int:
    return len(_media_resources(experiment, visible_only=True))


def _question_count(experiment: dict[str, Any]) -> int:
    return int(experiment.get("published_question_count") or 0)


def _experiment_chapter_ids(experiment: dict[str, Any]) -> tuple[str, ...]:
    ids: list[str] = []
    seen: set[str] = set()
    for binding in _chapter_bindings(experiment):
        chapter_id = str(binding.get("chapter_id") or "").strip()
        if chapter_id and chapter_id not in seen:
            ids.append(chapter_id)
            seen.add(chapter_id)
    return tuple(ids)


def _experiment_area_id(experiment: dict[str, Any]) -> str | None:
    bindings = sorted(
        _chapter_bindings(experiment),
        key=lambda item: (
            0 if item.get("coverage_type") == "primary" else 1,
            int(item.get("sort_order") or 999),
            str(item.get("chapter_id") or ""),
        ),
    )
    for binding in bindings:
        area_id = _chapter_area_id(str(binding.get("chapter_id") or ""))
        if area_id in AREA_NAMES:
            return area_id
    return None


def _point_summary(experiment: dict[str, Any]) -> StudentExperimentPointSummary:
    return StudentExperimentPointSummary(
        id=str(experiment["id"]),
        code=str(experiment.get("code") or ""),
        title=str(experiment.get("title") or experiment["id"]),
        summary=experiment.get("summary"),
        parent_code=_parent_code(experiment),
        parent_title=_parent_title(experiment),
        module_title=_module_title(experiment),
        chapter_ids=list(_experiment_chapter_ids(experiment)),
        video_candidate_count=len(_video_candidates(experiment)),
        published_video_count=_published_video_count(experiment),
        question_count=_question_count(experiment),
    )


def _group_summary(group: ParentGroup, *, recommended_parent_code: str | None = None) -> StudentExperimentGroupSummary:
    return StudentExperimentGroupSummary(
        parent_code=group.parent_code,
        parent_title=group.parent_title,
        area_id=group.area_id,
        area_name=group.area_name,
        chapter_ids=list(group.chapter_ids),
        experiment_count=len(group.experiments),
        published_video_count=sum(_published_video_count(experiment) for experiment in group.experiments),
        question_count=sum(_question_count(experiment) for experiment in group.experiments),
        recommended=group.parent_code == recommended_parent_code,
    )


def _build_parent_groups(experiments: list[dict[str, Any]]) -> list[ParentGroup]:
    buckets: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for experiment in experiments:
        area_id = _experiment_area_id(experiment)
        if area_id not in AREA_NAMES or area_id == "f":
            continue
        buckets[(area_id, _parent_code(experiment))].append(experiment)

    groups: list[ParentGroup] = []
    for (area_id, parent_code), items in buckets.items():
        ordered_items = sorted(items, key=lambda item: (int(item.get("display_order") or 999), str(item.get("code") or "")))
        chapter_ids: list[str] = []
        seen_chapters: set[str] = set()
        for item in ordered_items:
            for chapter_id in _experiment_chapter_ids(item):
                if chapter_id not in seen_chapters:
                    chapter_ids.append(chapter_id)
                    seen_chapters.add(chapter_id)
        groups.append(
            ParentGroup(
                parent_code=parent_code,
                parent_title=_parent_title(ordered_items[0]),
                area_id=area_id,
                area_name=_chapter_area_name(area_id),
                chapter_ids=tuple(chapter_ids),
                display_order=min(int(item.get("display_order") or 999) for item in ordered_items),
                experiments=tuple(ordered_items),
            )
        )
    area_index = {area_id: index for index, area_id in enumerate(AREA_ORDER)}
    return sorted(groups, key=lambda group: (area_index.get(group.area_id, 99), group.display_order, group.parent_code))


def _student_experiment_sql(where_clause: str = "") -> str:
    return f"""
        SELECT
          fe.id,
          fe.code,
          fe.title,
          fe.summary,
          fe.status,
          fe.display_order,
          fe.metadata,
          COALESCE((
            SELECT jsonb_agg(
              jsonb_build_object(
                'chapter_id', ecb.chapter_id,
                'chapter_title', c.chapter_title,
                'chapter_number', c.chapter_number,
                'coverage_type', ecb.coverage_type,
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
                'media_id', ma.id,
                'title', COALESCE(mb.title, ma.title),
                'mime_type', COALESCE(ma.playback_mime_type, ma.mime_type),
                'upload_status', ma.upload_status,
                'binding_status', mb.status,
                'point_key', mb.metadata->>'point_key',
                'point_title', mb.metadata->>'point_title',
                'has_thumbnail', ma.thumbnail_relative_path IS NOT NULL
              )
              ORDER BY mb.sort_order, mb.created_at
            )
            FROM media_bindings mb
            JOIN media_assets ma ON ma.id = mb.media_asset_id
            WHERE mb.target_type = 'experiment'
              AND mb.target_id = fe.id
              AND mb.status <> 'archived'
          ), '[]'::jsonb) AS media_resources,
          (SELECT COUNT(*) FROM experiment_questions q WHERE q.experiment_id = fe.id AND q.status = 'published') AS published_question_count
        FROM formal_experiments fe
        {where_clause}
        ORDER BY fe.display_order, fe.code
    """


def _load_published_experiments(session: Any) -> list[dict[str, Any]]:
    rows = session.execute(
        text(
            _student_experiment_sql(
                """
                WHERE fe.status = 'published'
                  AND COALESCE(fe.metadata->>'archived_by_catalog_seed', 'false') <> 'true'
                """
            )
        )
    ).mappings()
    return [dict(row) for row in rows]


def _latest_pretest_area_id(session: Any, student_id: str) -> str | None:
    row = (
        session.execute(
            text(
                """
                SELECT weakest_area
                FROM student_pretest_sessions
                WHERE student_id = :student_id
                  AND status = 'completed'
                ORDER BY completed_at DESC NULLS LAST, updated_at DESC, created_at DESC
                LIMIT 1
                """
            ),
            {"student_id": student_id},
        )
        .mappings()
        .first()
    )
    if not row:
        return None
    return PRETEST_AREA_IDS.get(str(row.get("weakest_area") or ""))


def _lowest_mastery_chapter_id(session: Any, *, student_id: str, area_id: str) -> str | None:
    chapter_ids = [chapter_id for chapter_id, chapter in CHAPTER_AREA_MAP.items() if chapter.get("area_id") == area_id]
    if not chapter_ids:
        return None
    row = (
        session.execute(
            text(
                """
                SELECT kp.chapter_id, sm.mastery_score
                FROM student_mastery sm
                JOIN knowledge_points kp ON kp.id = sm.knowledge_point_id
                WHERE sm.student_id = :student_id
                  AND kp.chapter_id = ANY(:chapter_ids)
                ORDER BY sm.mastery_score ASC, kp.chapter_id ASC, kp.id ASC
                LIMIT 1
                """
            ),
            {"student_id": student_id, "chapter_ids": chapter_ids},
        )
        .mappings()
        .first()
    )
    return str(row["chapter_id"]) if row else None


def _choose_recommendation(
    *,
    groups: list[ParentGroup],
    pretest_area_id: str | None,
    mastery_chapter_id: str | None,
) -> tuple[str | None, str | None]:
    groups_by_area: dict[str, list[ParentGroup]] = defaultdict(list)
    for group in groups:
        groups_by_area[group.area_id].append(group)

    area_id = pretest_area_id if pretest_area_id in groups_by_area else DEFAULT_RECOMMENDED_AREA_ID
    if area_id not in groups_by_area:
        first_group = groups[0] if groups else None
        return (first_group.area_id, first_group.parent_code) if first_group else (None, None)

    candidates = groups_by_area[area_id]
    if mastery_chapter_id:
        matched = next((group for group in candidates if mastery_chapter_id in group.chapter_ids), None)
        if matched:
            return matched.area_id, matched.parent_code
    return candidates[0].area_id, candidates[0].parent_code


def _areas_for_groups(groups: list[ParentGroup]) -> list[StudentLearningArea]:
    groups_by_area: dict[str, list[ParentGroup]] = defaultdict(list)
    for group in groups:
        groups_by_area[group.area_id].append(group)

    areas: list[StudentLearningArea] = []
    for area_id in AREA_ORDER:
        area_groups = groups_by_area.get(area_id, [])
        areas.append(
            StudentLearningArea(
                area_id=area_id,
                area_name=_chapter_area_name(area_id),
                enabled=bool(area_groups),
                parent_codes=[group.parent_code for group in area_groups],
                experiment_count=sum(len(group.experiments) for group in area_groups),
                published_video_count=sum(
                    _published_video_count(experiment)
                    for group in area_groups
                    for experiment in group.experiments
                ),
                question_count=sum(_question_count(experiment) for group in area_groups for experiment in group.experiments),
            )
        )
    return areas


def _ensure_student_row(session: Any, user: AuthUser) -> None:
    student_id = _student_id(user)
    session.execute(
        text(
            """
            INSERT INTO students (id, display_name, class_name, user_id, student_id, class_id, status)
            VALUES (
              :student_id, :display_name, :class_name, CAST(:user_id AS uuid),
              :student_id, :class_id, 'active'
            )
            ON CONFLICT (id) DO UPDATE SET
              display_name = COALESCE(EXCLUDED.display_name, students.display_name),
              class_name = COALESCE(EXCLUDED.class_name, students.class_name),
              user_id = COALESCE(EXCLUDED.user_id, students.user_id),
              student_id = EXCLUDED.student_id,
              class_id = COALESCE(EXCLUDED.class_id, students.class_id),
              status = 'active',
              updated_at = now()
            """
        ),
        {
            "student_id": student_id,
            "display_name": user.display_name,
            "class_name": user.class_name,
            "user_id": user.id,
            "class_id": user.class_id,
        },
    )


def _record_learning_event(
    session: Any,
    *,
    user: AuthUser,
    event_type: str,
    parent_code: str | None = None,
    area_id: str | None = None,
    experiment_id: str | None = None,
    chapter_id: str | None = None,
) -> None:
    _ensure_student_row(session, user)
    session.execute(
        text(
            """
            INSERT INTO student_events (
              student_id, event_type, chapter_id, experiment_id, metadata, created_at
            )
            VALUES (
              :student_id,
              :event_type,
              :chapter_id,
              CASE
                WHEN CAST(:experiment_id AS text) IS NOT NULL
                 AND EXISTS (SELECT 1 FROM experiments e WHERE e.id = CAST(:experiment_id AS text))
                THEN CAST(:experiment_id AS text)
                ELSE NULL
              END,
              CAST(:metadata AS jsonb),
              now()
            )
            """
        ),
        {
            "student_id": _student_id(user),
            "event_type": event_type,
            "chapter_id": chapter_id,
            "experiment_id": experiment_id,
            "metadata": _json(
                {
                    "area_id": area_id,
                    "parent_code": parent_code,
                    "experiment_id": experiment_id,
                }
            ),
        },
    )


def get_student_learning_home(user: AuthUser) -> StudentLearningHomeResponse:
    with db_session() as session:
        experiments = _load_published_experiments(session)
        groups = _build_parent_groups(experiments)
        student_id = _student_id(user)
        pretest_area_id = _latest_pretest_area_id(session, student_id)
        mastery_chapter_id = _lowest_mastery_chapter_id(
            session,
            student_id=student_id,
            area_id=pretest_area_id or DEFAULT_RECOMMENDED_AREA_ID,
        )
        recommended_area_id, recommended_parent_code = _choose_recommendation(
            groups=groups,
            pretest_area_id=pretest_area_id,
            mastery_chapter_id=mastery_chapter_id,
        )
    return StudentLearningHomeResponse(
        recommended_area_id=recommended_area_id,
        recommended_parent_code=recommended_parent_code,
        areas=_areas_for_groups(groups),
        groups=[_group_summary(group, recommended_parent_code=recommended_parent_code) for group in groups],
    )


def get_student_experiment_group(user: AuthUser, parent_code: str) -> StudentExperimentGroupResponse:
    with db_session() as session:
        experiments = _load_published_experiments(session)
        groups = _build_parent_groups(experiments)
        group = next((item for item in groups if item.parent_code == parent_code), None)
        if not group:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment group not found")
        _record_learning_event(
            session,
            user=user,
            event_type="learning_group_opened",
            parent_code=group.parent_code,
            area_id=group.area_id,
            chapter_id=group.chapter_ids[0] if group.chapter_ids else None,
        )
    return StudentExperimentGroupResponse(
        parent_code=group.parent_code,
        parent_title=group.parent_title,
        area_id=group.area_id,
        area_name=group.area_name,
        experiments=[_point_summary(experiment) for experiment in group.experiments],
    )


def _student_video_resource(media: dict[str, Any]) -> StudentVideoResource:
    media_id = str(media.get("media_id") or "")
    has_thumbnail = bool(media.get("has_thumbnail"))
    return StudentVideoResource(
        media_id=media_id,
        title=str(media.get("title") or media_id),
        point_key=str(media.get("point_key")) if media.get("point_key") else None,
        point_title=str(media.get("point_title")) if media.get("point_title") else None,
        mime_type=str(media.get("mime_type")) if media.get("mime_type") else None,
        stream_path=f"/api/student/media/assets/{media_id}/stream" if media_id else None,
        thumbnail_path=f"/api/student/media/assets/{media_id}/thumbnail" if media_id and has_thumbnail else None,
    )


def get_student_experiment_detail(user: AuthUser, experiment_id: str) -> StudentExperimentDetailResponse:
    with db_session() as session:
        experiments = _load_published_experiments(session)
        experiment = next((item for item in experiments if str(item["id"]) == experiment_id), None)
        if not experiment or _experiment_area_id(experiment) == "f":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")
        summary = _point_summary(experiment)
        visible_videos = _media_resources(experiment, visible_only=True)
        _record_learning_event(
            session,
            user=user,
            event_type="experiment_detail_opened",
            parent_code=summary.parent_code,
            area_id=_experiment_area_id(experiment),
            experiment_id=summary.id,
            chapter_id=summary.chapter_ids[0] if summary.chapter_ids else None,
        )
    return StudentExperimentDetailResponse(
        **summary.model_dump(),
        video_candidates=_video_candidates(experiment),
        videos=[_student_video_resource(media) for media in visible_videos],
    )


def _published_student_media_row(asset_id: str) -> dict[str, Any]:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    SELECT ma.id,
                           COALESCE(ma.playback_relative_path, ma.relative_path) AS relative_path,
                           COALESCE(ma.playback_mime_type, ma.mime_type) AS mime_type,
                           ma.original_file_name,
                           ma.thumbnail_relative_path
                    FROM media_assets ma
                    JOIN media_bindings mb ON mb.media_asset_id = ma.id
                    JOIN formal_experiments fe ON fe.id = mb.target_id
                    WHERE ma.id = CAST(:asset_id AS uuid)
                      AND ma.upload_status = 'ready'
                      AND mb.target_type = 'experiment'
                      AND mb.status = 'published'
                      AND fe.status = 'published'
                    LIMIT 1
                    """
                ),
                {"asset_id": asset_id},
            )
            .mappings()
            .first()
        )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found")
    return dict(row)


def _safe_media_file(relative_path: str) -> Path:
    root = get_settings().media_root.resolve()
    path = (root / relative_path).resolve()
    if root != path and root not in path.parents:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media asset not found")
    if not path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media file not found")
    return path


def stream_student_media_asset(asset_id: str) -> FileResponse:
    row = _published_student_media_row(asset_id)
    file_path = _safe_media_file(str(row["relative_path"]))
    return FileResponse(
        file_path,
        media_type=row.get("mime_type") or "application/octet-stream",
        filename=row.get("original_file_name") or file_path.name,
    )


def get_student_media_thumbnail(asset_id: str) -> FileResponse:
    row = _published_student_media_row(asset_id)
    thumbnail = row.get("thumbnail_relative_path")
    if not thumbnail:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Media thumbnail not found")
    return FileResponse(_safe_media_file(str(thumbnail)), media_type="image/jpeg", filename=f"{asset_id}.jpg")
