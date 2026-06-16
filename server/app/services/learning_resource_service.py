from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from sqlalchemy import text

from server.app.database import db_session
from server.app.experiment_framework import build_experiment_framework_overview

QUESTION_STATUSES = {"draft", "published", "disabled", "archived"}

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

def get_learning_resource_overview() -> dict[str, Any]:
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


def get_experiment_knowledge_framework_overview() -> dict[str, Any]:
    with db_session() as session:
        return build_experiment_framework_overview(session)
