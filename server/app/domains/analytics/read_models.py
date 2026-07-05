from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from typing import Any

from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from sqlalchemy import text

from server.app.domains.platform.roles import is_teacher_role
from server.app.domains.preview.student_device_preview import TEACHER_PREVIEW_ACCOUNT_PURPOSE, TEACHER_PREVIEW_CLASS_PURPOSE
from server.app.infrastructure.database import db_session
from server.app.mastery import DEFAULT_EXPERIMENT_MASTERY_SCORE

ELEMENT_FAMILY_TITLE_BY_CHAPTER = {
    "CH13": "卤族元素",
    "CH14": "氧族元素",
    "CH15": "氮族元素",
    "CH16": "碳族元素",
    "CH17": "硼族元素",
    "CH18": "碱金属和碱土金属",
    "CH19": "铜锌副族元素",
    "CH20": "d 区过渡金属元素",
    "CH21": "镧系和锕系元素",
    "CH22": "氢和稀有气体",
}


@dataclass(frozen=True)
class CsvExport:
    content: str
    media_type: str
    filename: str


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _metadata(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("metadata")
    return value if isinstance(value, dict) else {}


def _answer_value(value: Any) -> Any:
    if isinstance(value, dict) and "value" in value:
        return value.get("value")
    return value


def _submitted_answer_value(value: Any) -> Any:
    if isinstance(value, dict):
        return _answer_value(value.get("value", value))
    return value


def _correct_answer(row: dict[str, Any]) -> Any:
    answer = row.get("answer") if isinstance(row.get("answer"), dict) else {}
    question_type = str(row.get("question_type") or "")
    if question_type in {"single_choice", "true_false"}:
        return answer.get("value")
    if question_type == "fill_blank":
        return answer.get("accepted_answers") or []
    return answer


def _cached_ai_response(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict) or not value.get("text"):
        return None
    return {
        "text": str(value.get("text") or ""),
        "source": "ai" if value.get("source") == "ai" else "fallback",
        "mode": str(value.get("mode") or "cached"),
        "generated_at": value.get("generated_at"),
    }


def _clean_experiment_group_title(value: Any) -> str:
    title = str(value or "").strip()
    chapter_id = _chapter_id_from_text(title)
    if chapter_id and chapter_id in ELEMENT_FAMILY_TITLE_BY_CHAPTER:
        return ELEMENT_FAMILY_TITLE_BY_CHAPTER[chapter_id]
    title = re.sub(r"^实验\s*\d+\s*-\s*\d+\s*", "", title).strip()
    title = re.sub(r"^（[^）]+）\s*", "", title).strip()
    title = re.sub(r"^第\s*\d+\s*章\s*", "", title).strip()
    title = re.sub(r"^CH\d{2}\s*[-_—:：]?\s*", "", title, flags=re.IGNORECASE).strip()
    return title


def _chapter_id_from_text(value: Any) -> str:
    text_value = str(value or "").strip()
    match = re.search(r"\bCH\s*([0-9]{2})\b", text_value, flags=re.IGNORECASE)
    if match:
        return f"CH{match.group(1)}"
    match = re.search(r"第\s*([0-9]{1,2})\s*章", text_value)
    if match:
        return f"CH{int(match.group(1)):02d}"
    return ""


def _primary_chapter_binding(experiment: dict[str, Any]) -> dict[str, Any] | None:
    bindings = experiment.get("chapter_bindings") or []
    if not isinstance(bindings, list):
        return None
    for binding in bindings:
        if isinstance(binding, dict) and str(binding.get("chapter_id") or "").strip():
            return binding
    return None


def _experiment_group_info(experiment: dict[str, Any]) -> dict[str, str]:
    metadata = _metadata(experiment)
    catalog_chapter_id = str(metadata.get("catalog_chapter_id") or "").strip()
    if catalog_chapter_id and catalog_chapter_id in ELEMENT_FAMILY_TITLE_BY_CHAPTER:
        return {
            "id": catalog_chapter_id,
            "code": catalog_chapter_id,
            "title": ELEMENT_FAMILY_TITLE_BY_CHAPTER[catalog_chapter_id],
            "raw_title": str(metadata.get("catalog_root_title") or metadata.get("catalog_chapter_title") or catalog_chapter_id),
        }
    chapter_binding = _primary_chapter_binding(experiment)
    if chapter_binding:
        chapter_id = str(chapter_binding.get("chapter_id") or "").strip()
        chapter_title = _clean_experiment_group_title(chapter_binding.get("chapter_title"))
        title = chapter_title or ELEMENT_FAMILY_TITLE_BY_CHAPTER.get(chapter_id) or chapter_id
        return {"id": chapter_id, "code": chapter_id, "title": title, "raw_title": str(chapter_binding.get("chapter_title") or "")}
    parent_code = str(metadata.get("parent_code") or "").strip()
    raw_title = (
        metadata.get("parent_title")
        or metadata.get("outline_group")
        or metadata.get("module_display_title")
        or metadata.get("module_title")
        or ""
    )
    chapter_id = _chapter_id_from_text(parent_code) or _chapter_id_from_text(raw_title)
    if chapter_id and chapter_id in ELEMENT_FAMILY_TITLE_BY_CHAPTER:
        return {"id": chapter_id, "code": chapter_id, "title": ELEMENT_FAMILY_TITLE_BY_CHAPTER[chapter_id], "raw_title": str(raw_title or parent_code)}
    title = _clean_experiment_group_title(raw_title)
    if not title:
        title = parent_code or str(experiment.get("code") or experiment.get("id") or "未分组")
    group_id = parent_code or title
    return {"id": group_id, "code": parent_code, "title": title, "raw_title": str(raw_title or "")}


def _attach_experiment_group(experiment: dict[str, Any]) -> dict[str, Any]:
    group = _experiment_group_info(experiment)
    return {
        **experiment,
        "family_id": group["id"],
        "family_code": group["code"],
        "family_title": group["title"],
    }


def _build_experiment_groups(experiments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, dict[str, Any]] = {}
    for experiment in experiments:
        group = _experiment_group_info(experiment)
        item = groups.setdefault(
            group["id"],
            {
                "id": group["id"],
                "code": group["code"],
                "title": group["title"],
                "raw_title": group["raw_title"],
                "experiment_ids": [],
                "experiment_count": 0,
            },
        )
        item["experiment_ids"].append(experiment["id"])
        item["experiment_count"] += 1
    return list(groups.values())


def _catalog_points_by_chapter(chapter_ids: list[str]) -> dict[str, list[dict[str, Any]]]:
    ids = sorted({str(chapter_id).strip() for chapter_id in chapter_ids if str(chapter_id).strip()})
    if not ids:
        return {}
    with db_session() as session:
        rows = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT
                      n.id AS point_node_id,
                      n.chapter_id,
                      n.title AS point_title,
                      n.canonical_point_id,
                      n.display_order,
                      parent.id AS directory_id,
                      parent.title AS directory_title,
                      parent.display_order AS directory_order
                    FROM experiment_catalog_nodes n
                    LEFT JOIN experiment_catalog_nodes parent ON parent.id = n.parent_id
                    WHERE n.chapter_id = ANY(:chapter_ids)
                      AND n.node_kind = 'point'
                      AND n.status <> 'archived'
                    ORDER BY
                      n.chapter_id,
                      parent.display_order NULLS LAST,
                      parent.title NULLS LAST,
                      n.display_order,
                      n.title,
                      n.id
                    """
                ),
                {"chapter_ids": ids},
            )
            .mappings()
            .all()
        ]
    by_chapter: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_chapter.setdefault(str(row["chapter_id"]), []).append(row)
    return by_chapter


def _teacher_can_access_class(user: Any, class_id: str) -> bool:
    if is_teacher_role(user.role):
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

def _is_teacher_preview_class(class_id: str) -> bool:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    SELECT COALESCE(class_purpose, 'instructional') = :preview_purpose AS is_preview
                    FROM classes
                    WHERE id = :class_id
                    """
                ),
                {"class_id": class_id, "preview_purpose": TEACHER_PREVIEW_CLASS_PURPOSE},
            )
            .mappings()
            .first()
        )
    return bool(row and row["is_preview"])

def _require_class_access(class_id: str, user: Any) -> None:
    if _is_teacher_preview_class(class_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
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
              AND COALESCE(ma.lifecycle_status, 'active') = 'active'
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
                AND COALESCE(ma.lifecycle_status, 'active') = 'active'
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
                AND COALESCE(ma.lifecycle_status, 'active') = 'active'
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

def _attempt_primary_points(attempt: dict[str, Any]) -> list[dict[str, Any]]:
    metadata = attempt.get("metadata") if isinstance(attempt.get("metadata"), dict) else {}
    question_metadata = attempt.get("question_metadata") if isinstance(attempt.get("question_metadata"), dict) else {}
    points = metadata.get("primary_points") or question_metadata.get("primary_points") or []
    node_ids = [
        str(node_id)
        for node_id in (metadata.get("primary_point_node_ids") or question_metadata.get("primary_point_node_ids") or [])
        if str(node_id).strip()
    ]
    if not node_ids and attempt.get("point_node_id"):
        node_ids = [str(attempt.get("point_node_id"))]
    if points:
        output: list[dict[str, Any]] = []
        seen_node_ids: set[str] = set()
        for index, item in enumerate(points):
            if not isinstance(item, dict) or not (item.get("point_node_id") or item.get("point_key")):
                continue
            point = dict(item)
            node_id = str(point.get("point_node_id") or "").strip()
            if not node_id and index < len(node_ids):
                node_id = node_ids[index]
                point["point_node_id"] = node_id
            if node_id:
                seen_node_ids.add(node_id)
            output.append(point)
        output.extend(
            {"point_node_id": node_id, "point_title": node_id, "point_key": ""}
            for node_id in node_ids
            if node_id not in seen_node_ids
        )
        if output:
            return output
    if node_ids:
        return [
            {"point_node_id": str(node_id), "point_title": str(node_id), "point_key": ""}
            for node_id in node_ids
            if str(node_id).strip()
        ]
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
                  AND COALESCE(re.entry_purpose, 'instructional') <> :preview_account_purpose
                UNION
                SELECT sp.student_id, sp.student_name, au.status, sp.class_id
                FROM student_profiles sp
                JOIN app_users au ON au.id = sp.user_id
                WHERE sp.class_id = :class_id
                  AND au.status <> 'disabled'
                  AND COALESCE(sp.profile_purpose, 'instructional') <> :preview_account_purpose
                ORDER BY student_id
                """
            ),
            {"class_id": class_id, "preview_account_purpose": TEACHER_PREVIEW_ACCOUNT_PURPOSE},
        )
        .mappings()
        .all()
    ]
    return rows

def get_class_dashboard(
    *,
    class_id: str,
    experiment_id: str | None = None,
    user: Any,
) -> dict[str, Any]:
    _require_class_access(class_id, user)
    with db_session() as session:
        students = _class_students(session, class_id)
        student_ids = [str(student["student_id"]) for student in students]
        experiments = [_attach_experiment_group(item) for item in _list_experiments(status_filter="published")]
        if experiment_id:
            experiments = [item for item in experiments if item["id"] == experiment_id]
        experiment_groups = _build_experiment_groups(experiments)
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
        point_mastery_rows = (
            [
                dict(row)
                for row in session.execute(
                    text(
                        """
                        SELECT student_id, class_id, point_node_id, experiment_id, canonical_point_id,
                               mastery_score, evidence_count, updated_at
                        FROM student_point_mastery
                        WHERE student_id = ANY(:student_ids)
                          AND (class_id = :class_id OR class_id IS NULL)
                        """
                    ),
                    {"student_ids": student_ids, "class_id": class_id},
                )
                .mappings()
                .all()
            ]
            if student_ids
            else []
        )
        experiment_mastery_rows = (
            [
                dict(row)
                for row in session.execute(
                    text(
                        """
                        SELECT student_id, experiment_id, point_node_id, mastery_score, evidence_count, updated_at
                        FROM student_experiment_mastery
                        WHERE student_id = ANY(:student_ids)
                        """
                    ),
                    {"student_ids": student_ids},
                )
                .mappings()
                .all()
            ]
            if student_ids
            else []
        )
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
    mastery_by_experiment_key: dict[tuple[Any, Any], list[dict[str, Any]]] = {}
    for row in experiment_mastery_rows:
        mastery_by_experiment_key.setdefault((row["student_id"], row["experiment_id"]), []).append(row)
    point_titles = _catalog_point_titles([str(row.get("point_node_id") or "") for row in experiment_mastery_rows])
    point_mastery_by_key = {
        (str(row.get("student_id") or ""), str(row.get("point_node_id") or "")): row
        for row in point_mastery_rows
        if str(row.get("student_id") or "").strip() and str(row.get("point_node_id") or "").strip()
    }
    experiments_by_id = {str(experiment["id"]): experiment for experiment in experiments}
    groups_by_id = {group["id"]: group for group in experiment_groups}
    catalog_points_by_chapter = _catalog_points_by_chapter([str(group_id) for group_id in groups_by_id])
    matrix: list[dict[str, Any]] = []
    completed_cells = 0
    scored_cells: list[float] = []
    active_students: set[str] = set()
    for student in students:
        experiment_states: dict[str, Any] = {}
        group_states: dict[str, Any] = {}
        student_scores: list[float] = []
        for experiment in experiments:
            key = (student["student_id"], experiment["id"])
            progress = progress_by_key.get(key)
            attempt = attempts_by_key.get(key)
            mastery_items = mastery_by_experiment_key.get(key, [])
            point_scores = []
            for index, mastery in enumerate(mastery_items):
                point_node_id = str(mastery.get("point_node_id") or "").strip()
                point_score = (
                    float(mastery["mastery_score"])
                    if mastery and mastery.get("mastery_score") is not None
                    else DEFAULT_EXPERIMENT_MASTERY_SCORE
                )
                point_scores.append(
                    {
                        "point_node_id": point_node_id or None,
                        "point_title": point_titles.get(point_node_id) or point_node_id or f"{experiment['title']}点位 {index + 1}",
                        "experiment_id": experiment["id"],
                        "experiment_code": experiment.get("code"),
                        "experiment_title": experiment.get("title"),
                        "mastery_score": point_score,
                        "score": point_score,
                        "evidence_count": int(mastery["evidence_count"]) if mastery and mastery.get("evidence_count") is not None else 0,
                        "updated_at": mastery.get("updated_at"),
                    }
                )
            if progress or attempt or mastery_items:
                active_students.add(student["student_id"])
            status_value = progress.get("status") if progress else "not_started"
            if status_value == "completed":
                completed_cells += 1
            best_score = float(progress["best_score"]) if progress and progress.get("best_score") is not None else None
            mastery_score = (
                round(sum(float(point["mastery_score"]) for point in point_scores) / len(point_scores), 2)
                if point_scores
                else DEFAULT_EXPERIMENT_MASTERY_SCORE
            )
            student_scores.append(mastery_score)
            experiment_states[experiment["id"]] = {
                "status": status_value,
                "completion_percent": float(progress["completion_percent"]) if progress else 0,
                "best_score": best_score,
                "mastery_score": mastery_score,
                "score": mastery_score,
                "has_mastery": bool(mastery_items),
                "evidence_count": sum(int(point["evidence_count"]) for point in point_scores),
                "attempt_count": int(attempt["attempt_count"]) if attempt else 0,
                "points": point_scores,
            }
        student_group_scores: list[float] = []
        for group_id, group in groups_by_id.items():
            experiment_ids = [str(item) for item in group["experiment_ids"]]
            states = [experiment_states[experiment_id] for experiment_id in experiment_ids if experiment_id in experiment_states]
            catalog_points = catalog_points_by_chapter.get(group_id, [])
            points = []
            for point in catalog_points:
                point_node_id = str(point.get("point_node_id") or "")
                mastery = point_mastery_by_key.get((str(student["student_id"]), point_node_id))
                point_score = (
                    float(mastery["mastery_score"])
                    if mastery and mastery.get("mastery_score") is not None
                    else DEFAULT_EXPERIMENT_MASTERY_SCORE
                )
                evidence_value = int(mastery["evidence_count"]) if mastery and mastery.get("evidence_count") is not None else 0
                points.append(
                    {
                        "point_node_id": point_node_id or None,
                        "point_title": point.get("point_title") or point_node_id or "未命名点位",
                        "canonical_point_id": point.get("canonical_point_id"),
                        "directory_id": point.get("directory_id"),
                        "directory_title": point.get("directory_title") or "",
                        "experiment_id": mastery.get("experiment_id") if mastery else None,
                        "experiment_title": point.get("directory_title") or "",
                        "family_id": group_id,
                        "family_title": group["title"],
                        "mastery_score": point_score,
                        "score": point_score,
                        "evidence_count": evidence_value,
                        "updated_at": mastery.get("updated_at") if mastery else None,
                    }
                )
            if not points:
                points = [
                    {
                        **point,
                        "family_id": group_id,
                        "family_title": group["title"],
                        "experiment_title": point.get("experiment_title")
                        or experiments_by_id.get(str(point.get("experiment_id") or ""), {}).get("title"),
                    }
                    for experiment_id in experiment_ids
                    for point in experiment_states.get(experiment_id, {}).get("points", [])
                ]
            scores = [float(point["mastery_score"]) for point in points]
            mastery_score = round(sum(scores) / len(scores), 2) if scores else DEFAULT_EXPERIMENT_MASTERY_SCORE
            evidence_experiment_count = sum(1 for state in states if state["has_mastery"])
            evidence_point_count = sum(1 for point in points if int(point.get("evidence_count") or 0) > 0)
            evidence_count = sum(int(point["evidence_count"]) for point in points)
            if evidence_point_count > 0:
                active_students.add(student["student_id"])
            attempt_count = sum(int(state["attempt_count"]) for state in states)
            lowest_experiment_id = None
            lowest_experiment_score = None
            if states:
                lowest_experiment_id, lowest_state = min(
                    ((experiment_id, experiment_states[experiment_id]) for experiment_id in experiment_ids if experiment_id in experiment_states),
                    key=lambda item: float(item[1]["mastery_score"]),
                )
                lowest_experiment_score = float(lowest_state["mastery_score"])
            group_states[group_id] = {
                "status": "not_started"
                if evidence_experiment_count == 0
                else "needs_attention"
                if mastery_score < 60
                else "completed"
                if points and evidence_point_count == len(points)
                else "in_progress",
                "mastery_score": mastery_score,
                "score": mastery_score,
                "has_mastery": evidence_point_count > 0 or evidence_experiment_count > 0,
                "evidence_experiment_count": evidence_experiment_count,
                "evidence_point_count": evidence_point_count,
                "experiment_count": len(states),
                "evidence_count": evidence_count,
                "attempt_count": attempt_count,
                "lowest_experiment_id": lowest_experiment_id,
                "lowest_experiment_score": lowest_experiment_score,
                "points": points,
            }
            student_group_scores.append(mastery_score)
            scored_cells.append(mastery_score)
        matrix.append(
            {
                **student,
                "average_score": round(sum(student_group_scores) / len(student_group_scores), 2)
                if student_group_scores
                else round(sum(student_scores) / len(student_scores), 2)
                if student_scores
                else 0,
                "experiments": experiment_states,
                "experiment_groups": group_states,
            }
        )
    total_cells = max(1, len(students) * len(experiments))
    missing_students = [row for row in matrix if all(cell["status"] == "not_started" for cell in row["experiments"].values())]
    return {
        "class_id": class_id,
        "metrics": {
            "class_size": len(students),
            "active_students": len(active_students),
            "published_experiments": len(experiments),
            "published_experiment_groups": len(experiment_groups),
            "completion_rate": round(100 * completed_cells / total_cells, 2),
            "average_score": round(sum(scored_cells) / len(scored_cells), 2) if scored_cells else 0,
            "missing_students": len(missing_students),
        },
        "experiments": experiments,
        "experiment_groups": experiment_groups,
        "matrix": matrix,
        "recent_activity": recent,
        "missing_students": missing_students,
    }


def _attempt_kind_label(value: Any) -> str:
    kind = str(value or "")
    if kind == "posttest":
        return "课后测试"
    if kind == "pretest_stage1":
        return "课前摸底 · 粗筛"
    if kind == "pretest_stage2":
        return "课前摸底 · 精诊"
    if kind:
        return kind
    return "未标记"


def _shape_attempt_for_teacher(attempt: dict[str, Any]) -> dict[str, Any]:
    shaped = dict(attempt)
    if shaped.get("id") is not None:
        shaped["id"] = str(shaped["id"])
    if shaped.get("question_id") is not None:
        shaped["question_id"] = str(shaped["question_id"])
    if shaped.get("score") is not None:
        shaped["score"] = float(shaped["score"])
    shaped["submitted_answer_value"] = _submitted_answer_value(shaped.get("submitted_answer"))
    shaped["correct_answer"] = _correct_answer(shaped)
    shaped["attempt_kind_label"] = _attempt_kind_label(shaped.get("attempt_kind"))
    shaped["primary_points"] = _attempt_primary_points(shaped)
    return shaped


def _catalog_point_titles(node_ids: list[str]) -> dict[str, str]:
    ids = sorted({str(node_id) for node_id in node_ids if str(node_id).strip()})
    if not ids:
        return {}
    with db_session() as session:
        return {
            str(row["id"]): str(row.get("title") or row["id"])
            for row in session.execute(
                text("SELECT id, title FROM experiment_catalog_nodes WHERE id = ANY(:node_ids)"),
                {"node_ids": ids},
            ).mappings()
        }


def _enrich_point_titles(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    titles = _catalog_point_titles([str(item.get("point_node_id") or "") for item in items])
    for item in items:
        node_id = str(item.get("point_node_id") or "")
        if node_id and titles.get(node_id):
            item["point_title"] = titles[node_id]
    return items


def _attempt_session_id(attempt: dict[str, Any]) -> str | None:
    metadata = _metadata(attempt)
    value = metadata.get("posttest_session_id")
    return str(value) if value else None


def _build_latest_posttest_report(row: dict[str, Any] | None, attempts: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not row:
        return None
    session_id = str(row["id"])
    session_attempts = [attempt for attempt in attempts if _attempt_session_id(attempt) == session_id]
    session_attempts.sort(key=lambda item: (str(item.get("created_at") or ""), str(item.get("id") or "")))
    experiments: dict[str, dict[str, Any]] = {}
    experiment_ids = [str(item) for item in _as_list(row.get("experiment_ids")) if str(item).strip()]
    for attempt in session_attempts:
        experiment_id = str(attempt.get("experiment_id") or "")
        if not experiment_id:
            continue
        experiments.setdefault(
            experiment_id,
            {
                "id": experiment_id,
                "code": attempt.get("experiment_code"),
                "title": attempt.get("experiment_title"),
            },
        )
    ordered_experiments = [
        experiments[experiment_id]
        for experiment_id in experiment_ids
        if experiment_id in experiments
    ]
    ordered_experiments.extend(
        experiment
        for experiment_id, experiment in experiments.items()
        if experiment_id not in experiment_ids
    )
    metadata = _metadata(row)
    return {
        "session_id": session_id,
        "completed_at": row.get("completed_at"),
        "score": float(row["score"]) if row.get("score") is not None else None,
        "correct_count": int(row.get("correct_count") or 0),
        "total_count": int(row.get("total_count") or 0),
        "experiments": ordered_experiments,
        "attempts": session_attempts,
        "wrong_answers": [attempt for attempt in session_attempts if attempt.get("correct") is False],
        "ai_summary": _cached_ai_response(metadata.get("ai_summary")),
        "ai_mistake_explanation": _cached_ai_response(metadata.get("ai_mistake_explanation")),
    }


def get_student_report(
    *,
    class_id: str,
    student_id: str,
    user: Any,
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
                      AND sp.class_id = :class_id
                      AND COALESCE(sp.profile_purpose, 'instructional') <> :preview_account_purpose
                    UNION
                    SELECT re.student_id, re.student_name, re.class_id, c.class_name
                    FROM roster_entries re
                    LEFT JOIN classes c ON c.id = re.class_id
                    WHERE re.student_id = :student_id
                      AND re.class_id = :class_id
                      AND COALESCE(re.entry_purpose, 'instructional') <> :preview_account_purpose
                    LIMIT 1
                    """
                ),
                {
                    "student_id": student_id,
                    "class_id": class_id,
                    "preview_account_purpose": TEACHER_PREVIEW_ACCOUNT_PURPOSE,
                },
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
                    SELECT a.*,
                           q.stem,
                           q.options,
                           q.answer,
                           q.explanation,
                           q.difficulty,
                           q.related_chapter_ids,
                           q.related_knowledge_point_ids,
                           q.metadata AS question_metadata,
                           fe.code AS experiment_code,
                           fe.title AS experiment_title,
                           fe.metadata AS experiment_metadata
                    FROM experiment_question_attempts a
                    LEFT JOIN experiment_questions q ON q.id = a.question_id
                    LEFT JOIN formal_experiments fe ON fe.id = a.experiment_id
                    WHERE a.student_id = :student_id
                      AND (a.class_id = :class_id OR a.class_id IS NULL)
                    ORDER BY a.created_at DESC
                    LIMIT 1000
                    """
                ),
                {"student_id": student_id, "class_id": class_id},
            )
            .mappings()
            .all()
        ]
        posttest_sessions = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT *
                    FROM student_posttest_sessions
                    WHERE student_id = :student_id
                      AND (class_id = :class_id OR class_id IS NULL)
                      AND status = 'completed'
                    ORDER BY completed_at DESC NULLS LAST, updated_at DESC, created_at DESC
                    LIMIT 50
                    """
                ),
                {"student_id": student_id, "class_id": class_id},
            )
            .mappings()
            .all()
        ]
        experiment_mastery = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT experiment_id, mastery_score, evidence_count, last_evidence_kind, updated_at
                    FROM student_experiment_mastery
                    WHERE student_id = :student_id
                    ORDER BY updated_at DESC
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
    attempts = [_shape_attempt_for_teacher(attempt) for attempt in attempts]
    posttest_reports = [_build_latest_posttest_report(row, attempts) for row in posttest_sessions]
    posttest_reports = [report for report in posttest_reports if report is not None]
    latest_posttest_report = posttest_reports[0] if posttest_reports else None
    weak_points: dict[str, dict[str, Any]] = {}
    weak_video_points: dict[str, dict[str, Any]] = {}
    for attempt in attempts:
        if attempt.get("correct") is True:
            continue
        for point in _attempt_primary_points(attempt):
            point_node_id = str(point.get("point_node_id") or attempt.get("point_node_id") or "").strip()
            point_key = str(point.get("point_key") or point_node_id).strip()
            if not point_key and not point_node_id:
                continue
            weak_video_points.setdefault(
                point_node_id or point_key,
                {
                    "point_node_id": point_node_id or None,
                    "point_key": point_key,
                    "point_title": point.get("point_title") or point_key or point_node_id,
                    "experiment_id": attempt.get("experiment_id"),
                    "experiment_code": attempt.get("experiment_code"),
                    "experiment_title": attempt.get("experiment_title"),
                    "incorrect_count": 0,
                },
            )
            weak_video_points[point_node_id or point_key]["incorrect_count"] += 1
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
        "experiment_mastery": experiment_mastery,
        "attempts": attempts,
        "latest_posttest_report": latest_posttest_report,
        "posttest_reports": posttest_reports,
        "weak_points": sorted(weak_points.values(), key=lambda row: row["incorrect_count"], reverse=True),
        "weak_video_points": _enrich_point_titles(
            sorted(weak_video_points.values(), key=lambda row: row["incorrect_count"], reverse=True)
        ),
        "timeline": timeline,
    }


def get_class_weak_points(
    *,
    class_id: str,
    experiment_id: str | None = None,
    user: Any,
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
                           a.point_node_id,
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
            point_node_id = str(point.get("point_node_id") or attempt.get("point_node_id") or "").strip()
            point_key = str(point.get("point_key") or point_node_id).strip()
            if not point_key and not point_node_id:
                continue
            item = point_items_by_key.setdefault(
                point_node_id or point_key,
                {
                    "point_node_id": point_node_id or None,
                    "point_key": point_key,
                    "point_title": point.get("point_title") or point_key or point_node_id,
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
    point_items = _enrich_point_titles(point_items)
    point_items.sort(key=lambda row: (row["incorrect_count"], row["attempt_count"]), reverse=True)
    return {"items": items, "total": len(items), "point_items": point_items, "point_total": len(point_items)}


def export_class_report_csv(
    *,
    class_id: str,
    user: Any,
) -> CsvExport:
    dashboard = get_class_dashboard(class_id=class_id, user=user)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "record_type",
            "class_id",
            "student_id",
            "student_name",
            "family_id",
            "family_title",
            "family_score",
            "family_evidence_experiments",
            "family_experiment_count",
            "experiment_id",
            "experiment_code",
            "experiment_title",
            "experiment_score",
            "experiment_has_mastery",
            "experiment_evidence_count",
            "experiment_attempt_count",
        ]
    )
    experiments_by_id = {item["id"]: item for item in dashboard["experiments"]}
    groups_by_id = {item["id"]: item for item in dashboard["experiment_groups"]}
    for student in dashboard["matrix"]:
        for group_id, state in student.get("experiment_groups", {}).items():
            group = groups_by_id.get(group_id, {})
            writer.writerow(
                [
                    "family_summary",
                    class_id,
                    student["student_id"],
                    student["student_name"],
                    group_id,
                    group.get("title"),
                    state.get("mastery_score", DEFAULT_EXPERIMENT_MASTERY_SCORE),
                    state.get("evidence_experiment_count", 0),
                    state.get("experiment_count", 0),
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                    "",
                ]
            )
        for experiment_id, state in student["experiments"].items():
            experiment = experiments_by_id.get(experiment_id, {})
            writer.writerow(
                [
                    "experiment_detail",
                    class_id,
                    student["student_id"],
                    student["student_name"],
                    experiment.get("family_id"),
                    experiment.get("family_title"),
                    "",
                    "",
                    "",
                    experiment_id,
                    experiment.get("code"),
                    experiment.get("title"),
                    state.get("mastery_score", DEFAULT_EXPERIMENT_MASTERY_SCORE),
                    state.get("has_mastery", False),
                    state.get("evidence_count", 0),
                    state.get("attempt_count", 0),
                ]
            )
    return CsvExport(
        content="\ufeff" + output.getvalue(),
        media_type="text/csv; charset=utf-8",
        filename=f"class-{class_id}-learning-analytics.csv",
    )
