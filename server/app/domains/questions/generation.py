from __future__ import annotations

import json
import os
from typing import Any, Callable

from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from sqlalchemy import text

from server.app.canonical_evidence import load_evidence_source_refs
from server.app.domains.catalog_tree.ai_context import build_static_evidence_payload
from server.app.domains.catalog_tree.jobs import _catalog_point_context as build_catalog_point_context
from server.app.infrastructure.settings import get_settings
from server.app.infrastructure.database import db_session
from server.app.experiment_admin_schemas import GenerationRequest
from server.app.domains.platform.settings import effective_ai_settings
from server.app.domains.catalog.experiments import _ensure_experiment
from server.app.domains.questions.bank import _json, _json_array, _validate_question_payload
from server.app.domains.questions.point_identity import point_canonical_id, point_placement_id, string_list, unique_strings

OBJECTIVE_TYPES = {"single_choice", "true_false", "fill_blank"}


def _normalize_option_rows(options: Any) -> list[Any]:
    if not isinstance(options, list):
        return []
    normalized: list[Any] = []
    for index, option in enumerate(options):
        fallback_label = chr(ord("A") + index)
        if isinstance(option, dict):
            label = str(option.get("label") or option.get("key") or option.get("option") or fallback_label).strip()
            text_value = option.get("text") or option.get("content") or option.get("value") or option.get("label") or ""
            normalized.append({"label": label[:1].upper() or fallback_label, "text": str(text_value).strip()})
            continue
        raw = str(option or "").strip()
        label = fallback_label
        text_value = raw
        if len(raw) >= 2 and raw[0].isalpha() and raw[1] in {".", "、", "．", ")", "）", ":"}:
            label = raw[0].upper()
            text_value = raw[2:].strip()
        normalized.append({"label": label, "text": text_value})
    return normalized


def _choice_answer_value(raw_answer: Any, options: list[Any]) -> str:
    if isinstance(raw_answer, dict):
        raw_answer = (
            raw_answer.get("value")
            or raw_answer.get("label")
            or raw_answer.get("option")
            or raw_answer.get("answer")
            or raw_answer.get("text")
        )
    raw = str(raw_answer or "").strip()
    if not raw:
        return ""
    if len(raw) == 1 and raw.isalpha():
        return raw.upper()
    if len(raw) >= 2 and raw[0].isalpha() and raw[1] in {".", "、", "．", ")", "）", ":"}:
        return raw[0].upper()
    for option in options:
        if not isinstance(option, dict):
            continue
        label = str(option.get("label") or "").strip()
        text_value = str(option.get("text") or "").strip()
        if raw == label or raw == text_value or raw in text_value:
            return label or raw
    return raw


def _normalize_llm_question_row(row: Any) -> dict[str, Any]:
    if not isinstance(row, dict):
        return {}
    question_type = str(row.get("question_type") or row.get("type") or "").strip()
    options = _normalize_option_rows(row.get("options") or row.get("choices") or row.get("choice_options") or [])
    raw_answer = (
        row.get("answer")
        if row.get("answer") is not None
        else row.get("correct_answer")
        if row.get("correct_answer") is not None
        else row.get("correctAnswer")
        if row.get("correctAnswer") is not None
        else row.get("correct_option")
        if row.get("correct_option") is not None
        else row.get("correctOption")
        if row.get("correctOption") is not None
        else row.get("fill_blank_answer")
    )
    if question_type == "single_choice":
        answer: Any = {"value": _choice_answer_value(raw_answer, options)}
    elif question_type == "true_false":
        if isinstance(raw_answer, dict):
            raw_answer = raw_answer.get("value") if raw_answer.get("value") is not None else raw_answer.get("answer")
        answer = {"value": raw_answer}
    elif question_type == "fill_blank":
        if isinstance(raw_answer, dict):
            answer = raw_answer
        elif isinstance(raw_answer, list):
            answer = {"accepted_answers": raw_answer, "match": "normalized_exact"}
        else:
            answer = {"accepted_answers": [raw_answer] if raw_answer is not None else [], "match": "normalized_exact"}
    else:
        answer = raw_answer
    return {
        **row,
        "question_type": question_type,
        "stem": str(row.get("stem") or row.get("question_text") or row.get("question") or row.get("title") or "").strip(),
        "options": options,
        "answer": answer,
        "explanation": row.get("explanation") or row.get("analysis") or row.get("rationale"),
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
                    "stem": f"{title}应作为一个具体视频点位管理，并唯一对应一个视频资源。",
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
    point_contexts: list[dict[str, Any]] | None = None,
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
                            "required_schema": {
                                "question_type": "single_choice | true_false | fill_blank",
                                "stem": "question text",
                                "options": [{"label": "A", "text": "option text"}],
                                "answer": {"value": "A for single_choice, true/false for true_false"},
                                "fill_blank_answer": {"accepted_answers": ["answer"], "match": "normalized_exact"},
                                "explanation": "brief evidence-based explanation",
                            },
                            "target_point_node_ids": request.target_point_node_ids,
                            "catalog_point_contexts": point_contexts or [],
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
        return [_normalize_llm_question_row(row) for row in rows] if isinstance(rows, list) else None
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


EvidencePackageLoader = Callable[..., dict[str, Any]]

CATALOG_NODE_EVIDENCE_REQUIRED_DETAIL = (
    "Fresh catalog-node evidence is required for AI question generation. "
    "Legacy experiment_id/point_key evidence and generic canonical RAG refs are not valid after the catalog reset."
)


def _as_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item or "").strip()]


def _catalog_node_evidence_ready(
    evidence_package: dict[str, Any] | None,
    *,
    target_point_node_ids: list[str] | None = None,
) -> bool:
    if not isinstance(evidence_package, dict):
        return False
    mode = str(evidence_package.get("mode") or "").strip()
    contract = str(evidence_package.get("evidence_contract") or "").strip()
    diagnostics = evidence_package.get("diagnostics") if isinstance(evidence_package.get("diagnostics"), dict) else {}
    strategy = str(diagnostics.get("source_strategy") or "").strip()
    if "catalog_node_evidence" not in {mode, contract, strategy}:
        return False
    source_mode = str(evidence_package.get("source_mode") or diagnostics.get("source_mode") or "").strip()
    if any("legacy" in item for item in (mode, contract, strategy, source_mode)):
        return False
    freshness_status = str(evidence_package.get("freshness_status") or diagnostics.get("freshness_status") or "").strip()
    evidence_status = str(evidence_package.get("evidence_status") or diagnostics.get("evidence_status") or "").strip()
    if freshness_status in {"stale", "missing", "legacy_keyed", "incompatible"}:
        return False
    if evidence_status in {"stale", "missing", "failed", "unavailable", "legacy_keyed", "incompatible"}:
        return False

    package_node_ids = {
        *_as_string_list(evidence_package.get("target_point_node_ids")),
        *_as_string_list(evidence_package.get("catalog_node_ids")),
        *_as_string_list(evidence_package.get("point_node_ids")),
        *_as_string_list(diagnostics.get("target_point_node_ids")),
        *_as_string_list(diagnostics.get("catalog_node_ids")),
    }
    requested_node_ids = set(_as_string_list(target_point_node_ids or []))
    if requested_node_ids and not requested_node_ids.issubset(package_node_ids):
        return False
    if not package_node_ids:
        return False
    source_refs = evidence_package.get("source_refs")
    return isinstance(source_refs, list) and bool(source_refs)


def _target_points_from_catalog_nodes(session: Any, node_ids: list[str]) -> list[dict[str, str]]:
    node_ids = _as_string_list(node_ids)
    if not node_ids:
        return []
    rows = [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT n.id AS point_node_id,
                       n.canonical_point_id,
                       n.title AS point_title,
                       n.chapter_id,
                       COALESCE(c.point_title, cp.title) AS authored_point_title
                FROM experiment_catalog_nodes n
                LEFT JOIN experiment_catalog_points cp ON cp.id = n.canonical_point_id
                LEFT JOIN experiment_catalog_point_content c
                  ON c.canonical_point_id = n.canonical_point_id OR c.node_id = n.id
                WHERE n.id = ANY(:node_ids)
                  AND n.node_kind = 'point'
                  AND n.status <> 'archived'
                """
            ),
            {"node_ids": node_ids},
        )
        .mappings()
        .all()
    ]
    by_id = {str(row["point_node_id"]): row for row in rows}
    missing = [node_id for node_id in node_ids if node_id not in by_id]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"message": "Question generation targets must be active catalog point nodes.", "missing_point_node_ids": missing},
        )
    return [
        {
            "point_node_id": node_id,
            "point_id": node_id,
            "source_placement_node_id": node_id,
            "canonical_point_id": str(by_id[node_id].get("canonical_point_id") or ""),
            "point_key": "",
            "point_title": str(by_id[node_id].get("authored_point_title") or by_id[node_id].get("point_title") or node_id),
            "chapter_id": str(by_id[node_id].get("chapter_id") or ""),
        }
        for node_id in node_ids
    ]


def _target_point_node_ids(target_points: list[dict[str, Any]] | None) -> list[str]:
    return _as_string_list([point_placement_id(point) for point in (target_points or []) if isinstance(point, dict)])


def _target_canonical_point_ids(target_points: list[dict[str, Any]] | None) -> list[str]:
    return unique_strings([point_canonical_id(point) for point in (target_points or []) if isinstance(point, dict)])


def catalog_point_generation_contexts(session: Any, *, target_points: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    contexts: list[dict[str, Any]] = []
    for point in target_points or []:
        node_id = str(point.get("point_node_id") or point.get("point_id") or point.get("node_id") or "").strip()
        if not node_id:
            continue
        try:
            context = build_catalog_point_context(session, node_id=node_id)
        except Exception as exc:
            context = {
                "node_id": node_id,
                "chapter_id": point.get("chapter_id"),
                "title": point.get("point_title") or point.get("title") or node_id,
                "catalog_path": [],
                "principle": "",
                "normalized_equations": [],
                "phenomenon_explanation": "",
                "safety_note": "",
                "videos": [],
                "related_points": [],
                "field_contributors": ["title"],
                "context_status": "partial",
                "missing_reason": f"{exc.__class__.__name__}: {str(exc)[:240]}",
            }
        contexts.append(
            {
                "catalog_node_id": node_id,
                "placement_node_id": node_id,
                "source_placement_node_id": node_id,
                "canonical_point_id": point_canonical_id(point),
                "chapter_id": context.get("chapter_id"),
                "point_title": context.get("title") or point.get("point_title") or node_id,
                "catalog_path": context.get("catalog_path") or [],
                "principle": context.get("principle") or "",
                "normalized_equations": context.get("normalized_equations") or [],
                "phenomenon_explanation": context.get("phenomenon_explanation") or "",
                "safety_note": context.get("safety_note") or "",
                "videos": context.get("videos") or [],
                "related_points": context.get("related_points") or [],
                "field_contributors": context.get("field_contributors") or [],
                "context_status": context.get("context_status") or "available",
                "missing_reason": context.get("missing_reason"),
            }
        )
    return contexts


def attach_evidence_to_point_contexts(
    point_contexts: list[dict[str, Any]],
    *,
    source_refs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not point_contexts:
        return []
    output: list[dict[str, Any]] = []
    for context in point_contexts:
        node_id = str(context.get("catalog_node_id") or context.get("node_id") or "").strip()
        refs = [
            ref
            for ref in source_refs
            if isinstance(ref, dict)
            and (
                str(ref.get("point_node_id") or "").strip() == node_id
                or node_id in _as_string_list(ref.get("point_node_ids") or [])
            )
        ]
        if not refs and len(point_contexts) == 1:
            refs = source_refs
        output.append({**context, "evidence_sources": refs})
    return output


def _catalog_node_evidence_package(
    *,
    source_refs: list[dict[str, Any]],
    target_points: list[dict[str, Any]] | None,
    source_mode: str,
    freshness_status: str | None = None,
    diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    node_ids = _target_point_node_ids(target_points)
    normalized_source_refs: list[dict[str, Any]] = []
    for ref in source_refs:
        if not isinstance(ref, dict):
            continue
        item = dict(ref)
        if node_ids and not item.get("point_node_id") and not item.get("point_node_ids"):
            item["point_node_ids"] = node_ids
        canonical_ids = _target_canonical_point_ids(target_points)
        if canonical_ids and not item.get("canonical_point_id") and not item.get("canonical_point_ids"):
            item["canonical_point_ids"] = canonical_ids
        normalized_source_refs.append(item)
    diagnostics_payload = {
        "source_strategy": "catalog_node_evidence",
        "source_mode": source_mode,
        "target_point_node_ids": node_ids,
        "target_canonical_point_ids": _target_canonical_point_ids(target_points),
        "catalog_node_ids": node_ids,
        **(diagnostics or {}),
    }
    freshness = freshness_status or str(diagnostics_payload.get("freshness_status") or ("fresh" if normalized_source_refs else "missing"))
    evidence_status = str(diagnostics_payload.get("evidence_status") or ("fresh" if normalized_source_refs else "missing"))
    return {
        "mode": "catalog_node_evidence",
        "evidence_contract": "catalog_node_evidence",
        "source_mode": source_mode,
        "freshness_status": freshness,
        "evidence_status": evidence_status,
        "target_point_node_ids": node_ids,
        "target_canonical_point_ids": _target_canonical_point_ids(target_points),
        "catalog_node_ids": node_ids,
        "source_refs": normalized_source_refs,
        "source_count": len(normalized_source_refs),
        "diagnostics": diagnostics_payload,
    }


def _source_refs_from_static_payload(payload: dict[str, Any], *, node_id: str) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for binding in payload.get("bindings") or []:
        if not isinstance(binding, dict):
            continue
        if binding.get("selection_status") != "selected" or binding.get("freshness_status") != "fresh":
            continue
        chunk_id = str(binding.get("chunk_id") or "").strip()
        if not chunk_id:
            continue
        refs.append(
            {
                "chunk_id": chunk_id,
                "source_file": binding.get("source_file") or binding.get("source_title"),
                "page_number": binding.get("page_number"),
                "page_start": binding.get("page_start"),
                "page_end": binding.get("page_end"),
                "section_title": binding.get("section_title"),
                "section_path": binding.get("section_path") or [],
                "section": binding.get("section") or binding.get("evidence_role"),
                "text": binding.get("text"),
                "text_preview": binding.get("text_preview"),
                "content_type": binding.get("content_type"),
                "content_hash": binding.get("content_hash"),
                "evidence_role": binding.get("evidence_role"),
                "source_boundary": binding.get("source_boundary") or "catalog_node_static_evidence",
                "index_name": binding.get("index_name"),
                "point_node_id": node_id,
                "freshness_status": binding.get("freshness_status"),
                "selection_status": binding.get("selection_status"),
                "rank": binding.get("rank"),
                "score": binding.get("score"),
                "rerank_score": binding.get("rerank_score"),
            }
        )
    return refs


def _static_catalog_node_evidence_package(session: Any, *, target_points: list[dict[str, Any]] | None) -> dict[str, Any]:
    node_ids = _target_point_node_ids(target_points)
    if not node_ids:
        return _catalog_node_evidence_package(
            source_refs=[],
            target_points=target_points,
            source_mode="missing_target_points",
            diagnostics={
                "evidence_status": "missing",
                "freshness_status": "missing",
                "missing_reason": "target_point_node_ids_required",
            },
        )
    source_refs: list[dict[str, Any]] = []
    per_point: list[dict[str, Any]] = []
    stale_points: list[str] = []
    missing_points: list[str] = []
    for node_id in node_ids:
        payload = build_static_evidence_payload(session, node_id=node_id)
        refs = _source_refs_from_static_payload(payload, node_id=node_id)
        point_status = str(payload.get("status") or "")
        per_point.append(
            {
                "point_node_id": node_id,
                "status": point_status,
                "binding_count": payload.get("binding_count") or 0,
                "fresh_source_count": len(refs),
                "state_status": (payload.get("state") or {}).get("evidence_status"),
                "candidate_diagnostics": payload.get("candidate_diagnostics") or {},
            }
        )
        if point_status == "stale_catalog_node_evidence":
            stale_points.append(node_id)
        elif not refs:
            missing_points.append(node_id)
        source_refs.extend(refs)
    if stale_points:
        return _catalog_node_evidence_package(
            source_refs=[],
            target_points=target_points,
            source_mode="static_catalog_node_evidence",
            diagnostics={
                "evidence_status": "stale",
                "freshness_status": "stale",
                "stale_point_node_ids": stale_points,
                "per_point": per_point,
            },
        )
    if missing_points:
        return _catalog_node_evidence_package(
            source_refs=[],
            target_points=target_points,
            source_mode="static_catalog_node_evidence",
            diagnostics={
                "evidence_status": "missing",
                "freshness_status": "missing",
                "missing_point_node_ids": missing_points,
                "per_point": per_point,
            },
        )
    return _catalog_node_evidence_package(
        source_refs=source_refs,
        target_points=target_points,
        source_mode="static_catalog_node_evidence",
        freshness_status="fresh",
        diagnostics={"evidence_status": "fresh", "freshness_status": "fresh", "per_point": per_point},
    )


def _source_audit_for_generation(
    *,
    source_refs: list[dict[str, Any]],
    evidence_package: dict[str, Any],
    target_point_node_ids: list[str],
    target_canonical_point_ids: list[str] | None = None,
) -> dict[str, Any]:
    chunk_ids = _question_source_chunk_ids(source_refs)
    return {
        "canonical_chunk_ids": chunk_ids,
        "supporting_theory_chunk_ids": [],
        "evidence_sufficient": bool(chunk_ids),
        "evidence_contract": "catalog_node_evidence",
        "evidence_source": evidence_package.get("source_mode") or "catalog_node_evidence",
        "target_point_node_ids": target_point_node_ids,
        "target_canonical_point_ids": target_canonical_point_ids or [],
        "source_placement_node_ids": target_point_node_ids,
        "reviewer_note": "Generated draft; teacher must verify catalog-node evidence before publication.",
    }


def question_payload_has_catalog_evidence_lineage(
    payload: dict[str, Any],
    *,
    target_point_node_ids: list[str] | None = None,
) -> bool:
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    source_audit = metadata.get("source_audit") if isinstance(metadata.get("source_audit"), dict) else {}
    lineage = metadata.get("evidence_lineage") if isinstance(metadata.get("evidence_lineage"), dict) else {}
    evidence_contract = str(source_audit.get("evidence_contract") or lineage.get("evidence_contract") or "").strip()
    evidence_source = str(source_audit.get("evidence_source") or lineage.get("evidence_source") or "").strip()
    if evidence_contract != "catalog_node_evidence":
        return False
    if "legacy" in evidence_source:
        return False
    payload_node_ids = set(
        _as_string_list(
            payload.get("primary_point_node_ids")
            or metadata.get("primary_point_node_ids")
            or metadata.get("target_point_node_ids")
            or source_audit.get("target_point_node_ids")
            or lineage.get("target_point_node_ids")
            or []
        )
    )
    payload_canonical_ids = set(
        _as_string_list(
            payload.get("primary_canonical_point_ids")
            or metadata.get("primary_canonical_point_ids")
            or metadata.get("target_canonical_point_ids")
            or source_audit.get("target_canonical_point_ids")
            or lineage.get("target_canonical_point_ids")
            or []
        )
    )
    requested = set(_as_string_list(target_point_node_ids or []))
    if requested and not requested.issubset(payload_node_ids):
        return False
    if not payload_node_ids and not payload_canonical_ids:
        return False
    return bool(source_audit.get("canonical_chunk_ids") or payload.get("source_refs") or lineage.get("source_refs"))


def attach_generation_lineage(
    payload: dict[str, Any],
    *,
    evidence_package: dict[str, Any],
    target_points: list[dict[str, Any]] | None,
    generation_id: str | None = None,
) -> dict[str, Any]:
    target_node_ids = _target_point_node_ids(target_points)
    target_canonical_ids = _target_canonical_point_ids(target_points)
    source_refs = list(evidence_package.get("source_refs") or payload.get("source_refs") or [])
    metadata = dict(payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {})
    metadata["primary_point_node_ids"] = _as_string_list(metadata.get("primary_point_node_ids") or target_node_ids)
    metadata["source_placement_node_ids"] = _as_string_list(metadata.get("source_placement_node_ids") or target_node_ids)
    metadata["primary_canonical_point_ids"] = _as_string_list(metadata.get("primary_canonical_point_ids") or target_canonical_ids)
    if target_points:
        metadata["primary_points"] = [
            {
                "point_node_id": point_placement_id(point),
                "source_placement_node_id": point_placement_id(point),
                "canonical_point_id": point_canonical_id(point),
                "point_key": point.get("point_key") or "",
                "point_title": point.get("point_title") or point.get("title") or point.get("point_node_id"),
            }
            for point in target_points
        ]
    source_audit = dict(metadata.get("source_audit") if isinstance(metadata.get("source_audit"), dict) else {})
    if source_audit.get("reviewer_note"):
        source_audit["model_reviewer_note"] = source_audit.get("reviewer_note")
    source_audit = {
        **source_audit,
        **_source_audit_for_generation(
            source_refs=source_refs,
            evidence_package=evidence_package,
            target_point_node_ids=target_node_ids,
            target_canonical_point_ids=target_canonical_ids,
        ),
    }
    metadata["source_audit"] = source_audit
    metadata["evidence_lineage"] = {
        "generation_id": generation_id,
        "evidence_contract": "catalog_node_evidence",
        "evidence_source": evidence_package.get("source_mode") or "catalog_node_evidence",
        "target_point_node_ids": target_node_ids,
        "target_canonical_point_ids": target_canonical_ids,
        "source_placement_node_ids": target_node_ids,
        "source_ref_count": len(source_refs),
    }
    return {
        **payload,
        "primary_point_node_ids": _as_string_list(payload.get("primary_point_node_ids") or target_node_ids),
        "source_placement_node_ids": _as_string_list(payload.get("source_placement_node_ids") or target_node_ids),
        "primary_canonical_point_ids": _as_string_list(payload.get("primary_canonical_point_ids") or target_canonical_ids),
        "source_refs": source_refs,
        "source_chunk_ids": _question_source_chunk_ids(source_refs, source_audit),
        "metadata": metadata,
    }


def generate_question_drafts(
    *,
    payload: GenerationRequest,
    user: Any,
    rag_gate: dict[str, Any],
    evidence_loader: EvidencePackageLoader,
) -> dict[str, Any]:
    with db_session() as session:
        experiment = _ensure_experiment(session, payload.experiment_id)
        target_points = _target_points_from_catalog_nodes(session, payload.target_point_node_ids)
        if not target_points:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="AI question generation requires target catalog point node ids after the catalog reset.",
            )
        evidence_package = evidence_loader(
            session,
            experiment=experiment,
            prompt=payload.prompt,
            target_question={
                "related_chapter_ids": payload.chapter_ids,
                "related_knowledge_point_ids": payload.knowledge_point_ids,
            },
            target_points=target_points,
            rag_gate=rag_gate,
        )
        source_refs = list(evidence_package.get("source_refs") or [])
        if not source_refs:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="No usable evidence was found for this experiment context; AI question generation is blocked.",
            )
        if not _catalog_node_evidence_ready(evidence_package):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=CATALOG_NODE_EVIDENCE_REQUIRED_DETAIL,
            )
        target_point_node_ids = _target_point_node_ids(target_points)
        point_contexts = attach_evidence_to_point_contexts(
            catalog_point_generation_contexts(session, target_points=target_points),
            source_refs=source_refs,
        )
        warning = "" if source_refs else "当前实验资料尚未充分入库，已使用实验目录与理论章节信息生成草稿，发布前必须人工核验。"
        ai_settings = effective_ai_settings(get_settings())
        generated = _try_openai_generation(
            experiment=experiment,
            request=payload,
            source_refs=source_refs,
            point_contexts=point_contexts,
        )
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
                            "target_point_node_ids": target_point_node_ids,
                            "target_points": target_points,
                            "catalog_point_contexts": point_contexts,
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
                "primary_point_node_ids": row.get("primary_point_node_ids") or target_point_node_ids,
                "status": "draft",
            }
            row_payload = attach_generation_lineage(
                row_payload,
                evidence_package=evidence_package,
                target_points=target_points,
                generation_id=generation_id,
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
    }
