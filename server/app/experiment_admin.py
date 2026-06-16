from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Path, status
from fastapi.responses import StreamingResponse
from sqlalchemy import text

from server.app.agent import _source_evidence_payload, _source_from_chunk
from server.app.auth import AuthUser, require_roles
from server.app.config import get_settings
from server.app.database import db_session
from server.app.experiment_admin_schemas import (
    GenerationRequest,
    PointAwareSuggestionRequest,
    WorkbenchMessageRequest,
    WorkbenchSessionRequest,
)
from server.app.experiment_framework import build_experiment_framework_overview
from server.app.hybrid_rag import retrieve_hybrid_context
from server.app.platform_settings import ai_feature_enabled, effective_ai_settings
from server.app.repositories import RepositoryProvider, get_repositories
from server.app.retrieval import keyword_score
from server.app.services.experiment_catalog_service import (
    _ensure_experiment,
    _experiment_video_points,
    _list_experiment_video_resources,
    _list_experiments,
)
from server.app.services.question_bank_service import (
    _insert_question,
    _validate_question_payload,
)
from server.app.services.question_generation_service import (
    _load_generation_sources,
    _local_generated_questions,
    _question_source_chunk_ids,
    _try_openai_generation,
)
from server.app.schemas import AgentAskRequest

admin_router = APIRouter(prefix="/api/admin", tags=["experiment-admin"])

OBJECTIVE_TYPES = {"single_choice", "true_false", "fill_blank"}
QUESTION_STATUSES = {"draft", "published", "disabled", "archived"}


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=str)


def _json_array(value: Any) -> str:
    return json.dumps(value if value is not None else [], ensure_ascii=False, default=str)


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
