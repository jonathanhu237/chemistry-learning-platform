from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any, Callable

from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from sqlalchemy import text

from server.app.infrastructure.settings import get_settings
from server.app.infrastructure.database import db_session
from server.app.experiment_admin_schemas import PointAwareSuggestionRequest
from server.app.domains.platform.settings import effective_ai_settings
from server.app.domains.catalog.experiments import (
    _ensure_experiment,
    _experiment_video_points,
    _list_experiment_video_resources,
)
from server.app.domains.questions.bank import _json, _json_array, _validate_question_payload
from server.app.domains.questions.point_identity import point_canonical_id, point_placement_id, unique_strings
from server.app.domains.questions.generation import (
    CATALOG_NODE_EVIDENCE_REQUIRED_DETAIL,
    OBJECTIVE_TYPES,
    attach_evidence_to_point_contexts,
    attach_generation_lineage,
    catalog_point_generation_contexts,
    _catalog_node_evidence_ready,
    _question_source_chunk_ids,
)

EvidencePackageLoader = Callable[..., dict[str, Any]]


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _point_node_id(point: dict[str, Any] | None) -> str:
    return point_placement_id(point)


def _canonical_point_id(point: dict[str, Any] | None) -> str:
    return point_canonical_id(point)


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
                    "point_node_id": _point_node_id(point),
                    "source_placement_node_id": _point_node_id(point),
                    "canonical_point_id": _canonical_point_id(point),
                }
    node_ids = metadata.get("primary_point_node_ids") or metadata.get("point_node_ids") or []
    if isinstance(node_ids, list) and node_ids:
        node_id = _clean_text(node_ids[0])
        if node_id:
            return {"point_key": "", "point_title": node_id, "point_node_id": node_id}
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
            node_id = _point_node_id(point)
            if key or title or node_id:
                output.append(
                    {
                        "point_key": key or title,
                        "point_title": title or key or node_id,
                        "point_node_id": node_id,
                        "source_placement_node_id": node_id,
                        "canonical_point_id": _canonical_point_id(point),
                    }
                )
    if output:
        return output
    node_ids = metadata.get("primary_point_node_ids") or metadata.get("point_node_ids") or []
    if isinstance(node_ids, list):
        output = [
            {"point_key": "", "point_title": node_id, "point_node_id": node_id}
            for node_id in [_clean_text(item) for item in node_ids]
            if node_id
        ]
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


def _unique_point_node_ids(*groups: Any) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for group in groups:
        values = group if isinstance(group, list) else [group]
        for item in values:
            node_id = _point_node_id(item) if isinstance(item, dict) else _clean_text(item)
            if node_id and node_id not in seen:
                seen.add(node_id)
                output.append(node_id)
    return output


def _point_payload(point: dict[str, Any]) -> dict[str, str]:
    point_key = _clean_text(point.get("point_key"))
    point_title = _clean_text(point.get("point_title") or point.get("title") or point_key or _point_node_id(point))
    placement_id = _point_node_id(point)
    return {
        "point_key": point_key,
        "point_title": point_title,
        "point_node_id": placement_id,
        "source_placement_node_id": placement_id,
        "canonical_point_id": _canonical_point_id(point),
    }


def _attach_catalog_point_nodes(session: Any, *, experiment_id: str, points: list[dict[str, str]]) -> list[dict[str, str]]:
    if not points or not hasattr(session, "execute"):
        return points
    point_keys = _unique_point_keys([point.get("point_key") for point in points])
    requested_node_ids = _unique_point_node_ids(points)
    legacy_rows = []
    if point_keys:
        legacy_rows = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT lm.legacy_point_key, lm.catalog_node_id, n.canonical_point_id,
                           COALESCE(cp.title, n.title) AS title, n.chapter_id
                    FROM experiment_catalog_legacy_identity_map lm
                    JOIN experiment_catalog_nodes n ON n.id = lm.catalog_node_id
                    LEFT JOIN experiment_catalog_points cp ON cp.id = n.canonical_point_id
                    WHERE lm.legacy_kind = 'point'
                      AND lm.legacy_experiment_id = :experiment_id
                      AND lm.legacy_point_key = ANY(:point_keys)
                    """
                ),
                {"experiment_id": experiment_id, "point_keys": point_keys},
            )
            .mappings()
            .all()
        ]
    node_rows = []
    if requested_node_ids:
        node_rows = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT n.id AS catalog_node_id, n.canonical_point_id,
                           COALESCE(cp.title, n.title) AS title, n.chapter_id
                    FROM experiment_catalog_nodes n
                    LEFT JOIN experiment_catalog_points cp ON cp.id = n.canonical_point_id
                    WHERE n.id = ANY(:node_ids)
                      AND n.node_kind = 'point'
                    """
                ),
                {"node_ids": requested_node_ids},
            )
            .mappings()
            .all()
        ]
    by_key = {str(row["legacy_point_key"]): row for row in legacy_rows}
    by_node = {str(row["catalog_node_id"]): row for row in [*legacy_rows, *node_rows]}
    enriched: list[dict[str, str]] = []
    for point in points:
        node_id = _point_node_id(point)
        mapped = by_node.get(node_id) if node_id else by_key.get(str(point.get("point_key") or ""))
        if mapped:
            node_id = str(mapped.get("catalog_node_id") or node_id)
            enriched.append(
                {
                    **point,
                    "point_node_id": node_id,
                    "point_id": node_id,
                    "source_placement_node_id": node_id,
                    "canonical_point_id": _clean_text(mapped.get("canonical_point_id")),
                    "point_title": _clean_text(point.get("point_title") or mapped.get("title") or node_id),
                    "chapter_id": _clean_text(mapped.get("chapter_id")),
                }
            )
        else:
            enriched.append(point)
    return enriched


def _select_suggestion_points(
    *,
    points: list[dict[str, Any]],
    point_keys: list[str],
    target_question: dict[str, Any] | None,
) -> list[dict[str, str]]:
    selected: list[dict[str, str]] = []
    by_key = {str(item.get("point_key") or ""): item for item in points if item.get("point_key")}
    by_node = {_point_node_id(item): item for item in points if _point_node_id(item)}
    for key in _unique_point_keys(point_keys):
        found = by_key.get(key) or by_node.get(key)
        if found:
            selected.append(_point_payload(found))
        else:
            selected.append(
                {
                    "point_key": "" if key.startswith("cat-") else key,
                    "point_title": key,
                    "point_node_id": key if key.startswith("cat-") else "",
                    "source_placement_node_id": key if key.startswith("cat-") else "",
                    "canonical_point_id": "",
                }
            )
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
                **_point_payload(first),
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
                    "point_node_id": _point_node_id(point),
                    "source_placement_node_id": _point_node_id(point),
                    "canonical_point_id": _canonical_point_id(point),
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
    primary_point_node_ids = _unique_point_node_ids(
        row.get("primary_point_node_ids"),
        existing_metadata.get("primary_point_node_ids"),
        request.point_node_ids,
        request.point_node_id,
        point,
    )
    primary_canonical_point_ids = unique_strings(
        row.get("primary_canonical_point_ids"),
        existing_metadata.get("primary_canonical_point_ids"),
        _canonical_point_id(point),
    )
    source_placement_node_ids = unique_strings(
        row.get("source_placement_node_ids"),
        existing_metadata.get("source_placement_node_ids"),
        primary_point_node_ids,
    )
    primary_points = [
        {
            "point_key": point["point_key"],
            "point_title": point.get("point_title") or point["point_key"],
            "point_node_id": _point_node_id(point),
            "source_placement_node_id": _point_node_id(point),
            "canonical_point_id": _canonical_point_id(point),
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
    if option_links:
        normalized_links: list[dict[str, Any]] = []
        for link in option_links:
            if not isinstance(link, dict):
                continue
            link_payload = dict(link)
            if not link_payload.get("point_node_id") and point:
                link_key = _clean_text(link_payload.get("point_key"))
                if not link_key or link_key == _clean_text(point.get("point_key")):
                    link_payload["point_node_id"] = _point_node_id(point) or None
                    link_payload["source_placement_node_id"] = _point_node_id(point) or None
                    link_payload["canonical_point_id"] = _canonical_point_id(point) or None
            normalized_links.append(link_payload)
        option_links = normalized_links
    metadata = {
        **existing_metadata,
        "point_aware_question_bank": True,
        "suggestion_intent": request.intent,
        "primary_point_keys": primary_point_keys,
        "primary_point_node_ids": primary_point_node_ids,
        "primary_canonical_point_ids": primary_canonical_point_ids,
        "source_placement_node_ids": source_placement_node_ids,
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
                        "Generate teacher-review draft chemistry objective questions for a point-aware experiment question bank. "
                        "Return JSON only: {\"questions\":[...]}. "
                        "Each question must include question_type, stem, options, answer, explanation, primary_point_keys, "
                        "primary_point_node_ids, source_audit, and option_links for single_choice. Do not publish."
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
                            "catalog_point_contexts": point_contexts or [],
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


def _load_question_for_point_aware_suggestion(session: Any, question_id: str) -> dict[str, Any]:
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


def create_point_aware_suggestions(
    *,
    payload: PointAwareSuggestionRequest,
    user: Any,
    rag_gate: dict[str, Any],
    evidence_loader: EvidencePackageLoader,
) -> dict[str, Any]:
    with db_session() as session:
        experiment = _ensure_experiment(session, payload.experiment_id)
        target_question = None
        if payload.question_id:
            target_question = _load_question_for_point_aware_suggestion(session, payload.question_id)
            if target_question.get("experiment_id") != payload.experiment_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Question does not belong to experiment")

        points = _experiment_video_points(experiment, _list_experiment_video_resources(payload.experiment_id))
        selected_points = _select_suggestion_points(
            points=points,
            point_keys=_unique_point_keys(payload.point_keys, payload.point_key, payload.point_node_ids, payload.point_node_id),
            target_question=target_question,
        )
        selected_points = _attach_catalog_point_nodes(session, experiment_id=payload.experiment_id, points=selected_points)
        selected_point = selected_points[0] if selected_points else None
        target_point_keys = _unique_point_keys([point.get("point_key") for point in selected_points], payload.point_key)
        target_point_node_ids = _unique_point_node_ids(selected_points, payload.point_node_ids, payload.point_node_id)
        target_canonical_point_ids = unique_strings([_canonical_point_id(point) for point in selected_points])
        if not target_point_node_ids:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Select a catalog point node before generating point-aware question suggestions.",
            )
        evidence_package = evidence_loader(
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
        if not _catalog_node_evidence_ready(evidence_package, target_point_node_ids=target_point_node_ids):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=CATALOG_NODE_EVIDENCE_REQUIRED_DETAIL,
            )
        point_contexts = attach_evidence_to_point_contexts(
            catalog_point_generation_contexts(session, target_points=selected_points),
            source_refs=source_refs,
        )
        ai_settings = effective_ai_settings(get_settings())
        generated = _try_openai_point_aware_suggestions(
            request=payload,
            experiment=experiment,
            point=selected_point,
            target_question=target_question,
            source_refs=source_refs,
            point_contexts=point_contexts,
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
                            "point_node_id": _point_node_id(selected_point),
                            "point_node_ids": target_point_node_ids,
                            "source_placement_node_ids": target_point_node_ids,
                            "canonical_point_id": _canonical_point_id(selected_point),
                            "primary_canonical_point_ids": target_canonical_point_ids,
                            "catalog_point_contexts": point_contexts,
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
            row_payload = attach_generation_lineage(
                row_payload,
                evidence_package=evidence_package,
                target_points=selected_points,
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
        "target": {
            "intent": payload.intent,
            "experiment_id": payload.experiment_id,
            "question_id": payload.question_id,
            "point": selected_point,
            "points": selected_points,
            "point_node_ids": target_point_node_ids,
            "source_placement_node_ids": target_point_node_ids,
            "primary_canonical_point_ids": target_canonical_point_ids,
        },
    }
