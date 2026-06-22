from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from sqlalchemy import text

from server.app.canonical_evidence import load_evidence_source_refs
from server.app.infrastructure.database import db_session
from server.app.experiment_admin_schemas import (
    QuestionBankAssistantRequest,
    QuestionRequest,
    QuestionUpdateRequest,
)
from server.app.domains.platform.settings import ai_feature_enabled
from server.app.domains.catalog.experiments import _ensure_experiment, _list_experiments
from server.app.domains.questions.point_identity import collect_question_point_identity, normalize_question_point_identity

QUESTION_TYPE_ORDER = ("single_choice", "true_false", "fill_blank")
OBJECTIVE_TYPES = set(QUESTION_TYPE_ORDER)
QUESTION_STATUSES = {"draft", "published", "disabled", "archived"}

def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=str)


def _json_array(value: Any) -> str:
    return json.dumps(value if value is not None else [], ensure_ascii=False, default=str)


def _dump(model: Any) -> dict[str, Any]:
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()


CURRENT_BANK_STATUSES = {"draft", "published", "disabled"}


def _unique_strings(*groups: Any) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for group in groups:
        values = group if isinstance(group, list) else [group]
        for item in values:
            text_value = str(item or "").strip()
            if text_value and text_value not in seen:
                seen.add(text_value)
                output.append(text_value)
    return output


def _point_node_ids_from_payload(payload: dict[str, Any], metadata: dict[str, Any]) -> list[str]:
    return collect_question_point_identity(payload, metadata)["placement_node_ids"]


def _canonical_point_ids_from_payload(payload: dict[str, Any], metadata: dict[str, Any]) -> list[str]:
    return collect_question_point_identity(payload, metadata)["canonical_point_ids"]


def _source_placement_node_ids_from_payload(payload: dict[str, Any], metadata: dict[str, Any]) -> list[str]:
    return collect_question_point_identity(payload, metadata)["source_placement_node_ids"]


def _zero_type_counts() -> dict[str, int]:
    return {question_type: 0 for question_type in QUESTION_TYPE_ORDER}


def _inc_count(target: dict[str, int], key: str, amount: int = 1) -> None:
    clean_key = str(key or "unknown").strip() or "unknown"
    target[clean_key] = int(target.get(clean_key) or 0) + amount


def _metadata(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _payload_point_node_ids(payload: dict[str, Any]) -> list[str]:
    return _point_node_ids_from_payload(payload, _metadata(payload.get("metadata")))


def _payload_canonical_point_ids(payload: dict[str, Any]) -> list[str]:
    return _canonical_point_ids_from_payload(payload, _metadata(payload.get("metadata")))


def _question_evidence_source(metadata: dict[str, Any]) -> str:
    source_audit = metadata.get("source_audit") if isinstance(metadata.get("source_audit"), dict) else {}
    lineage = metadata.get("evidence_lineage") if isinstance(metadata.get("evidence_lineage"), dict) else {}
    source = (
        source_audit.get("evidence_source")
        or lineage.get("evidence_source")
        or source_audit.get("evidence_contract")
        or lineage.get("evidence_contract")
        or "unknown"
    )
    return str(source or "unknown").strip() or "unknown"


def _empty_point_audit(point_node_id: str, row: dict[str, Any] | None = None) -> dict[str, Any]:
    row = row or {}
    return {
        "point_node_id": point_node_id,
        "canonical_point_id": row.get("canonical_point_id") or point_node_id,
        "source_placement_node_ids": row.get("source_placement_node_ids") or [],
        "point_title": row.get("point_title") or point_node_id,
        "chapter_id": row.get("chapter_id") or "",
        "directory_id": row.get("directory_id") or "",
        "directory_title": row.get("directory_title") or "",
        "evidence_status": row.get("evidence_status") or "missing",
        "evidence_source_mode": row.get("evidence_source_mode") or "none",
        "question_type_counts": _zero_type_counts(),
        "published_count": 0,
        "draft_count": 0,
        "disabled_count": 0,
        "accepted_draft_count": 0,
        "rejected_draft_count": 0,
        "evidence_source_counts": {},
    }


def _ensure_audit_bucket(
    buckets: dict[str, dict[str, Any]],
    key: str,
    *,
    title: str,
    chapter_id: str = "",
) -> dict[str, Any]:
    clean_key = key or "unassigned"
    if clean_key not in buckets:
        buckets[clean_key] = {
            "id": clean_key,
            "title": title or clean_key,
            "chapter_id": chapter_id,
            "point_count": 0,
            "covered_point_count": 0,
            "unresolved_point_count": 0,
            "question_type_counts": _zero_type_counts(),
            "published_count": 0,
            "draft_count": 0,
            "accepted_draft_count": 0,
            "rejected_draft_count": 0,
            "evidence_source_counts": {},
        }
    return buckets[clean_key]


def _question_generation_audit(session: Any, *, chapter_id: str | None = None) -> dict[str, Any]:
    point_params: dict[str, Any] = {}
    point_filter = ""
    if chapter_id:
        point_filter = "AND n.chapter_id = :chapter_id"
        point_params["chapter_id"] = chapter_id
    point_query = text(
        f"""
        SELECT cp.id AS canonical_point_id,
               (
                 array_agg(n.id ORDER BY n.chapter_id, parent.display_order NULLS FIRST, n.display_order, n.id)
               )[1] AS point_node_id,
               (
                 array_agg(n.chapter_id ORDER BY n.chapter_id, parent.display_order NULLS FIRST, n.display_order, n.id)
               )[1] AS chapter_id,
               COALESCE(cp.title, (
                 array_agg(n.title ORDER BY n.chapter_id, parent.display_order NULLS FIRST, n.display_order, n.id)
               )[1]) AS point_title,
               (
                 array_agg(parent.id ORDER BY n.chapter_id, parent.display_order NULLS FIRST, n.display_order, n.id)
               )[1] AS directory_id,
               (
                 array_agg(parent.title ORDER BY n.chapter_id, parent.display_order NULLS FIRST, n.display_order, n.id)
               )[1] AS directory_title,
               array_agg(n.id ORDER BY n.chapter_id, parent.display_order NULLS FIRST, n.display_order, n.id) AS source_placement_node_ids,
               COALESCE(state.evidence_status, 'missing') AS evidence_status,
               COALESCE(state.source_mode, 'none') AS evidence_source_mode
        FROM experiment_catalog_nodes n
        JOIN experiment_catalog_points cp ON cp.id = n.canonical_point_id
        LEFT JOIN experiment_catalog_nodes parent ON parent.id = n.parent_id
        LEFT JOIN LATERAL (
          SELECT evidence_status, source_mode
          FROM experiment_catalog_point_evidence_state state
          WHERE state.canonical_point_id = cp.id OR state.node_id = n.id
          ORDER BY state.updated_at DESC
          LIMIT 1
        ) state ON true
        WHERE cp.status <> 'archived'
          AND n.node_kind = 'point'
          AND n.status <> 'archived'
          {point_filter}
        GROUP BY cp.id, cp.title, state.evidence_status, state.source_mode
        ORDER BY chapter_id, directory_id NULLS FIRST, point_node_id
        """
    )
    point_result = session.execute(point_query, point_params) if point_params else session.execute(point_query)
    point_rows = [dict(row) for row in point_result.mappings().all()]
    points = {
        str(row.get("canonical_point_id") or row["point_node_id"]): _empty_point_audit(str(row["point_node_id"]), row)
        for row in point_rows
    }
    chapters: dict[str, dict[str, Any]] = {}
    directories: dict[str, dict[str, Any]] = {}
    for point in points.values():
        chapter = _ensure_audit_bucket(
            chapters,
            str(point.get("chapter_id") or "unassigned"),
            title=str(point.get("chapter_id") or "unassigned"),
        )
        directory = _ensure_audit_bucket(
            directories,
            str(point.get("directory_id") or "unassigned"),
            title=str(point.get("directory_title") or "Unassigned directory"),
            chapter_id=str(point.get("chapter_id") or ""),
        )
        chapter["point_count"] += 1
        directory["point_count"] += 1

    question_rows = [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT question_type, status, primary_point_node_ids, primary_canonical_point_ids,
                       source_placement_node_ids, metadata
                FROM experiment_questions
                WHERE status <> 'archived'
                """
            )
        )
        .mappings()
        .all()
    ]
    question_type_counts = _zero_type_counts()
    evidence_source_counts: dict[str, int] = {}
    for row in question_rows:
        q_type = str(row.get("question_type") or "unknown")
        q_status = str(row.get("status") or "unknown")
        metadata = _metadata(row.get("metadata"))
        source = _question_evidence_source(metadata)
        _inc_count(question_type_counts, q_type)
        _inc_count(evidence_source_counts, source)
        payload = {
            "primary_point_node_ids": row.get("primary_point_node_ids") or [],
            "primary_canonical_point_ids": row.get("primary_canonical_point_ids") or [],
            "source_placement_node_ids": row.get("source_placement_node_ids") or [],
            "metadata": metadata,
        }
        for point_id in _payload_canonical_point_ids(payload) or _payload_point_node_ids(payload):
            point = points.setdefault(point_id, _empty_point_audit(point_id))
            _inc_count(point["question_type_counts"], q_type)
            _inc_count(point["evidence_source_counts"], source)
            if q_status == "published":
                point["published_count"] += 1
            elif q_status == "draft":
                point["draft_count"] += 1
            elif q_status == "disabled":
                point["disabled_count"] += 1

    draft_rows = [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT status, payload, validation_errors
                FROM experiment_question_drafts
                """
            )
        )
        .mappings()
        .all()
    ]
    draft_status_counts: dict[str, int] = {}
    draft_question_type_counts = _zero_type_counts()
    for row in draft_rows:
        draft_status = str(row.get("status") or "unknown")
        payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
        q_type = str(payload.get("question_type") or "unknown")
        _inc_count(draft_status_counts, draft_status)
        _inc_count(draft_question_type_counts, q_type)
        for point_id in _payload_canonical_point_ids(payload) or _payload_point_node_ids(payload):
            point = points.setdefault(point_id, _empty_point_audit(point_id))
            if draft_status == "draft":
                point["draft_count"] += 1
            elif draft_status == "published":
                point["accepted_draft_count"] += 1
            elif draft_status == "rejected":
                point["rejected_draft_count"] += 1

    candidate_rows = [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT status, payload, validation_errors
                FROM experiment_question_workbench_candidates
                """
            )
        )
        .mappings()
        .all()
    ]
    candidate_status_counts: dict[str, int] = {}
    for row in candidate_rows:
        _inc_count(candidate_status_counts, str(row.get("status") or "unknown"))

    for point in points.values():
        chapter = _ensure_audit_bucket(
            chapters,
            str(point.get("chapter_id") or "unassigned"),
            title=str(point.get("chapter_id") or "unassigned"),
        )
        directory = _ensure_audit_bucket(
            directories,
            str(point.get("directory_id") or "unassigned"),
            title=str(point.get("directory_title") or "Unassigned directory"),
            chapter_id=str(point.get("chapter_id") or ""),
        )
        for bucket in (chapter, directory):
            bucket["published_count"] += int(point.get("published_count") or 0)
            bucket["draft_count"] += int(point.get("draft_count") or 0)
            bucket["accepted_draft_count"] += int(point.get("accepted_draft_count") or 0)
            bucket["rejected_draft_count"] += int(point.get("rejected_draft_count") or 0)
            if point.get("published_count") or point.get("draft_count") or point.get("accepted_draft_count"):
                bucket["covered_point_count"] += 1
            else:
                bucket["unresolved_point_count"] += 1
            for q_type, count in point.get("question_type_counts", {}).items():
                bucket["question_type_counts"][q_type] = int(bucket["question_type_counts"].get(q_type) or 0) + int(count or 0)
            for source, count in point.get("evidence_source_counts", {}).items():
                _inc_count(bucket["evidence_source_counts"], source, int(count or 0))

    by_point = sorted(points.values(), key=lambda item: (str(item.get("chapter_id") or ""), str(item.get("directory_id") or ""), str(item.get("point_node_id") or "")))
    unresolved_points = [
        {
            "point_node_id": point["point_node_id"],
            "canonical_point_id": point.get("canonical_point_id"),
            "source_placement_node_ids": point.get("source_placement_node_ids") or [],
            "point_title": point.get("point_title"),
            "chapter_id": point.get("chapter_id"),
            "directory_id": point.get("directory_id"),
            "directory_title": point.get("directory_title"),
            "evidence_status": point.get("evidence_status"),
        }
        for point in by_point
        if not point.get("published_count") and not point.get("draft_count") and not point.get("accepted_draft_count")
    ]
    return {
        "catalog_point_count": len(by_point),
        "covered_point_count": len(by_point) - len(unresolved_points),
        "unresolved_point_count": len(unresolved_points),
        "question_type_counts": question_type_counts,
        "draft_question_type_counts": draft_question_type_counts,
        "evidence_source_counts": evidence_source_counts,
        "draft_status_counts": draft_status_counts,
        "workbench_candidate_status_counts": candidate_status_counts,
        "accepted_draft_count": int(draft_status_counts.get("published") or 0) + int(candidate_status_counts.get("published") or 0),
        "rejected_draft_count": int(draft_status_counts.get("rejected") or 0) + int(candidate_status_counts.get("rejected") or 0),
        "by_chapter": sorted(chapters.values(), key=lambda item: str(item.get("id") or "")),
        "by_directory": sorted(directories.values(), key=lambda item: (str(item.get("chapter_id") or ""), str(item.get("id") or ""))),
        "by_point": by_point,
        "unresolved_points": unresolved_points[:100],
    }

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
    metadata = dict(payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {})
    primary_point_node_ids = _point_node_ids_from_payload(payload, metadata)
    primary_canonical_point_ids = _canonical_point_ids_from_payload(payload, metadata)
    source_placement_node_ids = _source_placement_node_ids_from_payload(payload, metadata)
    if primary_point_node_ids:
        metadata["primary_point_node_ids"] = primary_point_node_ids
    if primary_canonical_point_ids:
        metadata["primary_canonical_point_ids"] = primary_canonical_point_ids
    if source_placement_node_ids:
        metadata["source_placement_node_ids"] = source_placement_node_ids
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
        "primary_point_node_ids": primary_point_node_ids,
        "primary_canonical_point_ids": primary_canonical_point_ids,
        "source_placement_node_ids": source_placement_node_ids,
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
    normalized = normalize_question_point_identity(session, normalized)
    bank_id = _ensure_question_bank(session, experiment_id, bank_kind, actor_user_id)
    row = (
        session.execute(
            text(
                """
                INSERT INTO experiment_questions (
                  bank_id, experiment_id, generation_id, question_type, stem, options, answer,
                  explanation, difficulty, related_chapter_ids, related_knowledge_point_ids,
                  source_chunk_ids, source_refs, primary_point_node_ids, primary_canonical_point_ids,
                  source_placement_node_ids, status, metadata,
                  created_by, published_by, published_at, updated_at
                )
                VALUES (
                  CAST(:bank_id AS uuid), :experiment_id, CAST(:generation_id AS uuid),
                  :question_type, :stem, CAST(:options AS jsonb), CAST(:answer AS jsonb),
                  :explanation, :difficulty, :related_chapter_ids, :related_knowledge_point_ids,
                  :source_chunk_ids, CAST(:source_refs AS jsonb), :primary_point_node_ids,
                  :primary_canonical_point_ids, :source_placement_node_ids,
                  :status, CAST(:metadata AS jsonb),
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
                "primary_point_node_ids": normalized["primary_point_node_ids"],
                "primary_canonical_point_ids": normalized["primary_canonical_point_ids"],
                "source_placement_node_ids": normalized["source_placement_node_ids"],
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
                       q.primary_point_node_ids,
                       q.primary_canonical_point_ids,
                       q.source_placement_node_ids,
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

def _load_chapter_source_refs(session: Any, *, chapter_id: str | None, prompt: str, limit: int = 6) -> list[dict[str, Any]]:
    if not chapter_id:
        return []
    return load_evidence_source_refs(session, prompt=prompt, chapter_ids=[chapter_id], limit=limit)

def list_question_bank_chapters_overview() -> dict[str, Any]:
    with db_session() as session:
        chapters = _list_question_bank_chapters(session)
        bindings_by_experiment = _question_bank_bindings_by_experiment(session)
        questions = _list_question_bank_question_rows(session)
    items = _summarize_question_bank_chapters(chapters, questions, bindings_by_experiment)
    return {"items": items, "total": len(items)}


def list_chapter_questions(
    *,
    chapter_id: str,
    question_type: str | None = None,
    status_filter: str | None = None,
    experiment_id: str | None = None,
    search: str | None = None,
    limit: int = 300,
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


def preview_question_bank_assistant(
    *,
    payload: QuestionBankAssistantRequest,
    user: Any,
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


def list_question_banks(
    *,
    experiment_id: str | None = None,
    chapter_id: str | None = None,
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
        regeneration_audit = _question_generation_audit(session, chapter_id=chapter_id)
    banks_by_experiment: dict[str, list[dict[str, Any]]] = {}
    for bank in banks:
        banks_by_experiment.setdefault(bank["experiment_id"], []).append(bank)
    items = [{**experiment, "banks": banks_by_experiment.get(experiment["id"], [])} for experiment in experiments]
    question_count = sum(int(bank.get("question_count") or 0) for bank in banks)
    return {
        "items": items,
        "total": len(items),
        "baseline": {
            "question_bank_empty": question_count == 0,
            "retired_legacy_seed": question_count == 0,
            "message": (
                "旧题库已随新版实验目录重置退休；新题库需等待目录点位证据重新生成后再创建。"
                if question_count == 0
                else ""
            ),
            "requires_catalog_node_evidence": True,
            "regeneration_audit": regeneration_audit,
        },
        "regeneration_audit": regeneration_audit,
    }


def list_questions(
    *,
    experiment_id: str | None = None,
    question_type: str | None = None,
    difficulty: str | None = None,
    status_filter: str | None = None,
    search: str | None = None,
    limit: int = 300,
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


def create_question(
    *,
    payload: QuestionRequest,
    user: Any,
) -> dict[str, Any]:
    data = _dump(payload)
    experiment_id = data.pop("experiment_id")
    bank_kind = data.pop("bank_kind")
    with db_session() as session:
        row = _insert_question(session, experiment_id=experiment_id, payload=data, bank_kind=bank_kind, actor_user_id=user.id)
    return row


def update_question(
    *,
    payload: QuestionUpdateRequest,
    question_id: str,
    user: Any,
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
        normalized = normalize_question_point_identity(session, normalized)
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
                        primary_point_node_ids = :primary_point_node_ids,
                        primary_canonical_point_ids = :primary_canonical_point_ids,
                        source_placement_node_ids = :source_placement_node_ids,
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
                    "primary_point_node_ids": normalized["primary_point_node_ids"],
                    "primary_canonical_point_ids": normalized["primary_canonical_point_ids"],
                    "source_placement_node_ids": normalized["source_placement_node_ids"],
                    "metadata": _json(normalized["metadata"]),
                    "status": normalized["status"],
                    "actor": user.id,
                },
            )
            .mappings()
            .one()
        )
    return dict(row)


def publish_question(
    *,
    question_id: str,
    user: Any,
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


def disable_question(
    *,
    question_id: str,
    user: Any,
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


def import_question_bank(
    *,
    filename: str | None,
    content: bytes,
    publish: bool = False,
    user: Any,
) -> dict[str, Any]:
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
                    "source_file": filename,
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


def export_question_bank(
    *,
    experiment_id: str | None = None,
    status_filter: str | None = "published",
) -> dict[str, Any]:
    questions = list_questions(experiment_id=experiment_id, status_filter=status_filter)
    return {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "items": questions["items"],
        "total": questions["total"],
    }
