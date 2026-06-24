from __future__ import annotations

import os
import json
import re
from typing import Any, AsyncIterator, Callable

from server.app.domains.experiment_points.canonical_points import candidate_point_key as _candidate_point_key
from server.app.infrastructure.settings import ROOT, Settings, get_settings
from server.app.hybrid_rag import retrieve_hybrid_context
from server.app.repositories import RepositoryProvider, get_repositories
from server.app.retrieval import keyword_score
from server.app.schemas import AgentAskRequest, AgentAskResponse, RagSource
from server.app.domains.assistant.output_normalization import (
    CHEM_MATH_OUTPUT_CONTRACT,
    normalize_assistant_formula_output as _normalize_assistant_formula_output,
)
from server.app.domains.assistant.policy import (
    POLICY_DECISION_MODES,
    AgentPolicy,
    _is_platform_resource_request,
    _is_rag_source_asset_request,
    classify_agent_request,
    load_agent_policy,
)
from server.app.domains.assistant.evidence_shaping import (
    build_figure_evidence_items as _figure_evidence_items,
    merge_sources as _merge_sources,
    rag_trace_payload as _rag_trace_payload,
)
from server.app.domains.assistant.output_guardrails import (
    has_resource_tool_result as _has_resource_tool_result,
    normalize_formula_answer,
)
from server.app.domains.assistant.retrieval import (
    agent_to_rag_request,
    generate_retrieval_queries as _generate_retrieval_queries,
    rag_to_agent_request,
    retrieve_context as _retrieve_context,
)
from server.app.domains.assistant.runtime import (
    AgentRunContext,
    RETRIEVAL_DECISION_MODES,
    RETRIEVAL_DECISION_SOURCES,
    StudentAIRetrievalDecision,
    StudentAIPolicyDecision,
    build_agent_response,
    chunk_stream_text as _chunk_stream_text,
    create_agent_context,
    dump_agent_response as _dump_agent_response,
)
from server.app.domains.assistant.rag_sources import (
    _source_asset_markdown,
    _source_evidence_payload,
    _source_from_chunk,
    source_to_dict,
)
from server.app.domains.catalog_tree.ai_context import (
    catalog_point_static_evidence_package,
    hydrate_static_evidence_sources,
)

VISIBLE_THINKING_MAX_CHARS = 40
_THINKING_SOURCE_VALUES = {"reasoning_summary", "agent_trace"}
_AGENT_TRACE_COPY: dict[str, tuple[str, str]] = {
    "retrieval_decision": ("retrieval_decision", "\u6b63\u5728\u5224\u65ad\u662f\u5426\u9700\u8981\u8bfe\u7a0b\u8d44\u6599"),
    "retrieval_skip": ("retrieval_skip", "\u65e0\u9700\u68c0\u7d22\uff0c\u6b63\u5728\u7ec4\u7ec7\u89e3\u91ca"),
    "fixed_evidence": ("fixed_evidence", "\u6b63\u5728\u8bfb\u53d6\u5f53\u524d\u8bfe\u7a0b\u4e0a\u4e0b\u6587"),
    "evidence_quality": ("evidence_quality", "\u6b63\u5728\u68c0\u67e5\u8d44\u6599\u76f8\u5173\u6027"),
    "policy": ("policy", "正在判断问题范围"),
    "context": ("context", "正在整理课程上下文"),
    "retrieval": ("retrieval", "正在检索课程资料"),
    "knowledge": ("generation", "正在根据课程知识组织回答"),
    "generation": ("generation", "正在组织回答"),
    "fallback": ("fallback", "正在使用本地兜底生成回答"),
}
_THINKING_UNSAFE_TERMS = (
    "chain-of-thought",
    "chain of thought",
    "reasoning_text",
    "raw reasoning",
    "system prompt",
    "developer message",
    "tool_calls",
    "tool call",
    "tool arguments",
    "function_call",
    "rag_trace",
    "guardrail",
    "policy_decision",
    "classification",
    "chunk_id",
    "source_node_id",
    "stack trace",
    "traceback",
    "exception",
    "openai",
    "provider",
    "model=",
    "思维链",
    "系统提示",
    "开发者消息",
    "工具参数",
    "策略码",
    "策略标签",
    "诊断",
    "异常",
    "堆栈",
    "原始",
    "教师端",
    "管理端",
)
_CJK_TEXT_RE = re.compile(r"[\u3400-\u9fff]")
_JSON_LIKE_RE = re.compile(r"[{}\[\]]")


def _experiment_title(experiment: dict[str, Any] | None) -> str:
    if not experiment:
        return ""
    return str(
        experiment.get("title")
        or experiment.get("name")
        or experiment.get("normalized_name")
        or experiment.get("code")
        or experiment.get("experiment_id")
        or ""
    ).strip()


def _experiment_video_points(experiment: dict[str, Any] | None) -> list[dict[str, str]]:
    if not experiment:
        return []
    raw_candidates = experiment.get("video_candidates")
    if not isinstance(raw_candidates, list):
        metadata = experiment.get("metadata") if isinstance(experiment.get("metadata"), dict) else {}
        raw_candidates = metadata.get("video_candidates") if isinstance(metadata, dict) else []
    if not isinstance(raw_candidates, list):
        return []
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, raw_title in enumerate(raw_candidates):
        title = str(raw_title or "").strip()
        if not title or title in seen:
            continue
        seen.add(title)
        result.append({"point_key": _candidate_point_key(index, title), "point_title": title})
    return result


def _resolve_point_context(context: AgentRunContext) -> dict[str, Any]:
    requested_point_key = str(context.request.point_key or "").strip()
    experiment_id = str(context.request.experiment_id or "").strip()
    if not requested_point_key or not experiment_id:
        return {}
    experiment = context.repositories.content.get_experiment(experiment_id)
    points = _experiment_video_points(experiment)
    selected = next(
        (
            point
            for point in points
            if requested_point_key in {point.get("point_key"), point.get("point_title")}
        ),
        None,
    )
    resolved_point_key = selected.get("point_key") if selected else requested_point_key
    return {
        "requested_point_key": requested_point_key,
        "point_key": resolved_point_key,
        "point_title": (selected or {}).get("point_title") or requested_point_key,
        "experiment_id": experiment_id,
        "experiment_code": (experiment or {}).get("code"),
        "experiment_title": _experiment_title(experiment),
        "chapter_id": context.request.chapter_id or (experiment or {}).get("chapter_id"),
        "available_point_count": len(points),
        "resolved": bool(selected),
    }


def _unique_texts(values: list[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def _first_safe_thinking_segment(text: str) -> str:
    for separator in ("。", "；", ";", "\n", "，", ",", "！", "!", "？", "?"):
        if separator in text:
            segment = text.split(separator, 1)[0].strip()
            if 2 <= len(segment) <= VISIBLE_THINKING_MAX_CHARS:
                return segment
    return text


def _sanitize_visible_thinking_message(message: Any) -> str:
    text = " ".join(str(message or "").strip().split())
    if not text:
        return ""
    text = re.sub(r"^```.*?```$", "", text, flags=re.S).strip()
    text = re.sub(r"^[#>*\-\d\.\s]+", "", text).strip()
    text = text.strip("`'\" ")
    if not text or not _CJK_TEXT_RE.search(text):
        return ""
    lowered = text.lower()
    if any(term in lowered or term in text for term in _THINKING_UNSAFE_TERMS):
        return ""
    if _JSON_LIKE_RE.search(text):
        return ""
    text = _first_safe_thinking_segment(text)
    text = text.strip("：:，,。；; ")
    if not (2 <= len(text) <= VISIBLE_THINKING_MAX_CHARS):
        return ""
    return text


def _thinking_event(
    *,
    source: str,
    message: Any,
    phase: str | None = None,
    sequence: int | None = None,
) -> dict[str, Any] | None:
    if source not in _THINKING_SOURCE_VALUES:
        return None
    safe_message = _sanitize_visible_thinking_message(message)
    if not safe_message:
        return None
    event: dict[str, Any] = {
        "event": "thinking",
        "source": source,
        "message": safe_message,
    }
    if phase:
        event["phase"] = phase
    if sequence is not None:
        event["sequence"] = sequence
    return event


def _agent_trace_event(key: str, *, sequence: int | None = None) -> dict[str, Any] | None:
    phase_message = _AGENT_TRACE_COPY.get(key)
    if not phase_message:
        return None
    phase, message = phase_message
    return _thinking_event(source="agent_trace", message=message, phase=phase, sequence=sequence)


def _response_event_type(event: Any) -> str:
    if isinstance(event, dict):
        return str(event.get("type") or "")
    return str(getattr(event, "type", "") or "")


def _response_event_text(event: Any, key: str) -> str:
    if isinstance(event, dict):
        return str(event.get(key) or "")
    return str(getattr(event, key, "") or "")


def _response_event_sequence(event: Any) -> int | None:
    value = event.get("sequence_number") if isinstance(event, dict) else getattr(event, "sequence_number", None)
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _sources_for_chunk_ids(context: AgentRunContext, chunk_ids: list[str]) -> tuple[list[RagSource], list[str]]:
    if not chunk_ids:
        return [], []
    source_chunks = context.repositories.content.source_chunks()
    chunks_by_id = {
        str(chunk.get("chunk_id") or chunk.get("id")): chunk
        for chunk in source_chunks
        if str(chunk.get("chunk_id") or chunk.get("id") or "").strip()
    }
    fixed_chunks = [chunks_by_id[chunk_id] for chunk_id in chunk_ids if chunk_id in chunks_by_id]
    missing_chunk_ids = [chunk_id for chunk_id in chunk_ids if chunk_id not in chunks_by_id]
    return [_source_from_chunk(chunk) for chunk in fixed_chunks], missing_chunk_ids


def _point_source_payloads(
    sources: list[RagSource],
    experiment_chunk_ids: list[str],
    theory_chunk_ids: list[str],
) -> list[dict[str, Any]]:
    role_by_chunk_id = {chunk_id: "experiment" for chunk_id in experiment_chunk_ids}
    role_by_chunk_id.update({chunk_id: "theory" for chunk_id in theory_chunk_ids if chunk_id not in role_by_chunk_id})
    payloads: list[dict[str, Any]] = []
    for source in sources:
        payload = _source_evidence_payload(source)
        payload["evidence_kind"] = role_by_chunk_id.get(source.chunk_id, "point")
        payloads.append(payload)
    return payloads


def _catalog_node_source_payloads(sources: list[RagSource], role_by_chunk_id: dict[str, str]) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for source in sources:
        payload = _source_evidence_payload(source)
        payload["evidence_kind"] = role_by_chunk_id.get(source.chunk_id, "supplemental")
        payload["source_boundary"] = "catalog_node_static_evidence"
        payloads.append(payload)
    return payloads


def _build_catalog_node_evidence_package(context: AgentRunContext) -> bool:
    point_node_id = str(context.request.point_node_id or "").strip()
    if not point_node_id:
        return False
    try:
        package = catalog_point_static_evidence_package(point_node_id=point_node_id)
    except Exception as exc:
        package = {
            "enabled": True,
            "evidence_source": "catalog_node_static_evidence",
            "static_evidence_role": "fallback_or_supplemental",
            "point_node_id": point_node_id,
            "chunk_ids": [],
            "chunk_roles": {},
            "static_fallback_missing": True,
            "static_evidence_status": "missing_fallback_evidence",
            "source_count": 0,
            "bindings": [],
            "dynamic_rag_available": bool(context.request.allow_rag_lookup),
            "message": "Static catalog-node evidence lookup failed; dynamic RAG may still run when allowed.",
            "lookup_error": f"{exc.__class__.__name__}: {str(exc)[:240]}",
        }
    if not package:
        context.point_evidence = {
            "enabled": True,
            "evidence_source": "catalog_node_static_evidence",
            "static_evidence_role": "fallback_or_supplemental",
            "point_node_id": point_node_id,
            "chunk_ids": [],
            "sources": [],
            "source_count": 0,
            "static_fallback_missing": True,
            "static_evidence_status": "missing_fallback_evidence",
            "dynamic_rag_available": bool(context.request.allow_rag_lookup),
        }
        return True

    chunk_ids = _unique_texts(list(package.get("chunk_ids") or []))
    role_by_chunk_id = {
        str(key): str(value or "supplemental")
        for key, value in (package.get("chunk_roles") or {}).items()
    }
    fixed_sources, missing_chunk_ids = hydrate_static_evidence_sources(context.repositories, chunk_ids=chunk_ids)
    if fixed_sources:
        context.sources = _merge_sources(fixed_sources, context.sources)
    source_payloads = _catalog_node_source_payloads(fixed_sources[:10], role_by_chunk_id)
    context.point_evidence = {
        **package,
        "chunk_ids": chunk_ids,
        "missing_chunk_ids": missing_chunk_ids,
        "sources": source_payloads,
        "source_count": len(fixed_sources),
        "static_source_count": len(fixed_sources),
        "supplemental_dynamic_rag_allowed": bool(context.request.allow_rag_lookup),
    }
    if package.get("static_fallback_missing"):
        context.add_guardrail(
            "catalog_node_static_evidence_missing",
            "use_dynamic_rag_when_available",
            "catalog-node static fallback evidence is absent; keep structured point context and allow supplemental dynamic RAG when policy permits",
        )
    elif fixed_sources:
        context.add_guardrail(
            "catalog_node_static_evidence_loaded",
            "use_static_then_dynamic",
            "catalog-node static evidence loaded as fallback or supplemental evidence",
        )
    else:
        context.add_guardrail(
            "catalog_node_static_evidence_unhydrated",
            "use_dynamic_rag_when_available",
            "catalog-node evidence bindings exist but source_chunks did not hydrate any static evidence",
        )
    return True


def _build_point_evidence_package(context: AgentRunContext) -> None:
    if _build_catalog_node_evidence_package(context):
        return

    point_context = _resolve_point_context(context)
    if not point_context:
        context.point_evidence = {}
        return

    experiment_id = point_context["experiment_id"]
    point_key = point_context["point_key"]
    reviewed = context.repositories.content.point_reviewed_evidence(experiment_id, point_key)
    if not reviewed:
        context.point_evidence = {
            **point_context,
            "enabled": True,
            "evidence_source": "manual_reviewed_point_evidence",
            "manual_reviewed": False,
            "review_grade": None,
            "experiment_chunk_ids": [],
            "theory_chunk_ids": [],
            "chunk_ids": [],
            "experiment_source_count": 0,
            "theory_source_count": 0,
            "source_count": 0,
            "sources": [],
            "missing_binding": True,
        }
        context.add_guardrail(
            "point_context_missing_reviewed_evidence",
            "answer_from_model_knowledge",
            "manual reviewed point evidence binding not found; keeping structured point context only",
        )
        return

    experiment_chunk_ids = _unique_texts(list(reviewed.get("experiment_chunk_ids") or []))
    theory_chunk_ids = _unique_texts(list(reviewed.get("theory_chunk_ids") or []))
    chunk_ids = _unique_texts([*experiment_chunk_ids, *theory_chunk_ids])
    fixed_sources, missing_chunk_ids = _sources_for_chunk_ids(context, chunk_ids)
    if fixed_sources:
        context.sources = _merge_sources(fixed_sources, context.sources)
    source_payloads = _point_source_payloads(fixed_sources[:10], experiment_chunk_ids, theory_chunk_ids)
    found_chunk_ids = {source.chunk_id for source in fixed_sources}

    context.point_evidence = {
        **point_context,
        "enabled": True,
        "evidence_source": "manual_reviewed_point_evidence",
        "manual_reviewed": bool(reviewed.get("manual_reviewed")),
        "review_grade": reviewed.get("review_grade"),
        "source_label": reviewed.get("source_label"),
        "experiment_chunk_ids": experiment_chunk_ids,
        "theory_chunk_ids": theory_chunk_ids,
        "chunk_ids": chunk_ids,
        "missing_chunk_ids": missing_chunk_ids,
        "experiment_source_count": len([chunk_id for chunk_id in experiment_chunk_ids if chunk_id in found_chunk_ids]),
        "theory_source_count": len([chunk_id for chunk_id in theory_chunk_ids if chunk_id in found_chunk_ids]),
        "source_count": len(fixed_sources),
        "sources": source_payloads,
    }
    if fixed_sources:
        context.add_guardrail("point_context_fixed", "use_fixed_evidence", "manual reviewed point evidence loaded")
    else:
        context.add_guardrail(
            "point_context_empty",
            "answer_from_model_knowledge",
            "manual reviewed point binding exists, but source_chunks did not hydrate any evidence",
        )

async def _policy_gate_decision(context: AgentRunContext, settings: Settings) -> StudentAIPolicyDecision:
    if not _sdk_enabled(settings):
        decision = _local_policy_decision_from_classification(context.classification)
        decision.raw.setdefault("source", "local_fallback")
        return decision
    try:
        decision = await _run_openai_policy_gate(context, settings)
    except Exception as exc:
        context.add_guardrail(
            "policy_gate_fallback",
            "continue_with_local_policy",
            f"policy gate unavailable: {exc.__class__.__name__}",
        )
        decision = _local_policy_decision_from_classification(context.classification)
        decision.raw.setdefault("source", "local_fallback")
        return decision
    if not decision.valid:
        context.add_guardrail(
            "policy_decision_invalid",
            "continue_with_local_policy",
            decision.reason or "invalid structured policy decision",
        )
        decision = _local_policy_decision_from_classification(context.classification)
        decision.raw.setdefault("source", "local_fallback")
        return decision
    return decision


def _policy_conversation_payload(context: AgentRunContext) -> list[dict[str, str]]:
    payload: list[dict[str, str]] = []
    for item in context.request.conversation_history[-6:]:
        data = item.model_dump() if hasattr(item, "model_dump") else item.dict()
        payload.append(
            {
                "role": str(data.get("role") or ""),
                "content": " ".join(str(data.get("content") or "").split())[:600],
            }
        )
    return payload


def _resolved_policy_question(context: AgentRunContext) -> str:
    question = context.request.question.strip()
    history = _policy_conversation_payload(context)
    if not history:
        return question
    short_followup = len(question) <= 12 or question in {"为什么", "为啥", "怎么理解", "继续", "展开讲讲", "这是什么意思"}
    if not short_followup:
        return question
    last_user = next((item["content"] for item in reversed(history) if item["role"] == "user"), "")
    last_assistant = next((item["content"] for item in reversed(history) if item["role"] == "assistant"), "")
    parts = [part for part in [f"上一轮学生问题：{last_user}" if last_user else "", f"上一轮助手回答摘要：{last_assistant}" if last_assistant else "", f"当前追问：{question}"] if part]
    return "；".join(parts) or question


async def _run_openai_policy_gate(context: AgentRunContext, settings: Settings) -> StudentAIPolicyDecision:
    from openai import OpenAI

    client = OpenAI(
        api_key=settings.agent_llm_api_key or os.getenv("OPENAI_API_KEY"),
        base_url=settings.agent_llm_base_url or None,
        timeout=12.0,
    )
    response = client.chat.completions.create(
        model=settings.agent_llm_model,
        temperature=0,
        response_format={"type": "json_object"},
        messages=[
            {
                "role": "system",
                "content": (
                    "You are the policy gate for a student inorganic chemistry learning assistant. "
                    "Classify the request with the compact policy below and return JSON only.\n\n"
                    f"{context.policy.compact_rail}\n\n"
                    "Allowed mode values: normal_answer, refuse_out_of_scope, safe_experiment_guidance, "
                    "assessment_hint, needs_platform_evidence.\n"
                    "Use needs_platform_evidence only for platform-specific resource/material availability claims. "
                    "Do not classify a short follow-up as out of scope when resolved_question or conversation_history "
                    "shows it continues an inorganic chemistry explanation. "
                    "Requests for textbook figures, source images, Frost/F-Z diagrams, Latimer diagrams, or evidence images "
                    "should use normal_answer with rag_search instead of published_resource_lookup. "
                    "Requests to explain a video point or experiment observation are normal_answer, not platform resource requests. "
                    "For ordinary inorganic chemistry factual questions, use normal_answer and treat RAG as optional support.\n"
                    "Retrieval modes: skip, fixed_evidence, dynamic_rag, resource_lookup, strict_evidence. "
                    "Use skip for ordinary concept explanations, mechanisms, equation derivations, and short follow-ups "
                    "that do not ask for platform evidence. Use dynamic_rag or strict_evidence for citations, source images, "
                    "textbook wording, figures, or answers explicitly according to course materials. Use resource_lookup only "
                    "for platform resource/video/file/link availability. "
                    "Return keys: mode, reason, evidence_required, student_guidance, allowed_tools, retrieval_mode, "
                    "retrieval_reason, retrieval_confidence, strict_evidence. "
                    "allowed_tools may include rag_search, curriculum_lookup, published_resource_lookup, "
                    "own_student_progress_lookup."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "question": context.request.question,
                        "resolved_question": _resolved_policy_question(context),
                        "conversation_history": _policy_conversation_payload(context),
                        "chapter_id": context.request.chapter_id,
                        "experiment_id": context.request.experiment_id,
                        "point_key": context.request.point_key,
                        "point_context": context.point_evidence,
                        "knowledge_point_ids": context.request.knowledge_point_ids,
                        "student_id_present": bool(context.request.student_id),
                        "allow_rag_lookup": context.request.allow_rag_lookup,
                    },
                    ensure_ascii=False,
                ),
            },
        ],
    )
    content = response.choices[0].message.content if response.choices else ""
    try:
        payload = json.loads(content or "{}")
    except json.JSONDecodeError:
        return _invalid_policy_decision("policy decision was not valid JSON", {"content": str(content)[:400]})
    return _parse_policy_decision_payload(payload)


def _parse_retrieval_confidence(value: Any) -> float | None:
    if value is None:
        return None
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        return None
    if confidence < 0:
        return 0.0
    if confidence > 1:
        return 1.0
    return confidence


def _parse_policy_decision_payload(payload: Any) -> StudentAIPolicyDecision:
    if not isinstance(payload, dict):
        return _invalid_policy_decision("policy decision payload is not an object", {"payload": str(payload)[:400]})
    mode = str(payload.get("mode") or "").strip()
    if mode not in POLICY_DECISION_MODES:
        return _invalid_policy_decision(f"unknown policy decision mode: {mode or '<empty>'}", dict(payload))
    retrieval_mode = str(payload.get("retrieval_mode") or "").strip()
    if retrieval_mode and retrieval_mode not in RETRIEVAL_DECISION_MODES:
        return _invalid_policy_decision(f"unknown retrieval decision mode: {retrieval_mode}", dict(payload))
    allowed_tools = tuple(
        str(item).strip()
        for item in (payload.get("allowed_tools") or [])
        if isinstance(item, str) and item.strip()
    )
    return StudentAIPolicyDecision(
        mode=mode,
        reason=str(payload.get("reason") or "")[:300],
        evidence_required=bool(payload.get("evidence_required")) or mode == "needs_platform_evidence",
        student_guidance=str(payload.get("student_guidance") or "")[:300],
        allowed_tools=allowed_tools,
        retrieval_mode=retrieval_mode,
        retrieval_reason=str(payload.get("retrieval_reason") or "")[:300],
        retrieval_confidence=_parse_retrieval_confidence(payload.get("retrieval_confidence")),
        strict_evidence=bool(payload.get("strict_evidence")) or bool(payload.get("evidence_required")) or mode == "needs_platform_evidence",
        valid=True,
        raw=dict(payload),
    )


def _invalid_policy_decision(reason: str, raw: dict[str, Any] | None = None) -> StudentAIPolicyDecision:
    return StudentAIPolicyDecision(
        mode="normal_answer",
        reason=reason,
        evidence_required=False,
        student_guidance="",
        allowed_tools=(),
        valid=False,
        raw=raw or {},
    )


def _local_policy_decision_from_classification(classification: dict[str, Any]) -> StudentAIPolicyDecision:
    if not classification.get("in_course_scope", True):
        return StudentAIPolicyDecision(
            mode="refuse_out_of_scope",
            reason="local fallback classified the request as outside course scope",
            retrieval_mode="skip",
            retrieval_reason="safety refusal does not need retrieval",
        )
    if classification.get("experiment_safety"):
        return StudentAIPolicyDecision(
            mode="safe_experiment_guidance",
            reason="local fallback identified unsafe experiment details",
            retrieval_mode="skip",
            retrieval_reason="unsafe experiment request should not run retrieval for operation steps",
        )
    if classification.get("assessment_leakage"):
        return StudentAIPolicyDecision(
            mode="assessment_hint",
            reason="local fallback identified direct assessment-answer request",
            retrieval_mode="skip",
            retrieval_reason="assessment hint should not retrieve a direct answer",
        )
    if classification.get("resource_request"):
        return StudentAIPolicyDecision(
            mode="needs_platform_evidence",
            reason="local fallback identified platform resource request",
            evidence_required=True,
            allowed_tools=("published_resource_lookup", "rag_search", "curriculum_lookup"),
            retrieval_mode="resource_lookup",
            retrieval_reason="platform resource availability requires published resource lookup",
            strict_evidence=True,
        )
    if classification.get("source_asset_request"):
        return StudentAIPolicyDecision(
            mode="normal_answer",
            reason="local fallback identified a source or evidence asset request",
            evidence_required=True,
            allowed_tools=("rag_search", "curriculum_lookup"),
            retrieval_mode="strict_evidence",
            retrieval_reason="source figure or evidence request requires course evidence",
            strict_evidence=True,
        )
    if classification.get("rag_preferred"):
        return StudentAIPolicyDecision(
            mode="normal_answer",
            reason="local fallback allows normal course answer from chemistry knowledge",
            evidence_required=False,
            allowed_tools=("curriculum_lookup",),
            retrieval_mode="skip",
            retrieval_reason="ordinary course explanation does not require supplemental RAG",
        )
    return StudentAIPolicyDecision(
        mode="normal_answer",
        reason="local fallback allows normal course answer",
        retrieval_mode="skip",
        retrieval_reason="normal answer does not require supplemental RAG",
    )


def _apply_policy_decision_to_classification(context: AgentRunContext) -> None:
    decision = context.policy_decision
    classification = context.classification
    mode = decision.mode if decision.mode in POLICY_DECISION_MODES else "normal_answer"
    source_asset_request = _is_rag_source_asset_request(context.request.question)
    deterministic_platform_resource_request = (not source_asset_request) and _is_platform_resource_request(context.request.question)
    if source_asset_request and mode in {"needs_platform_evidence", "refuse_out_of_scope"}:
        context.add_guardrail(
            "policy_resource_veto",
            "treat_as_learning_answer",
            "Policy gate classified a source figure or evidence image request as resource availability/refusal; keeping it on the learning evidence rail.",
        )
        mode = "normal_answer"
        decision.evidence_required = False
    if mode == "needs_platform_evidence" and not deterministic_platform_resource_request:
        context.add_guardrail(
            "policy_resource_veto",
            "treat_as_learning_answer",
            "Policy gate classified the turn as platform-resource availability, but deterministic resource-boundary checks identify it as a learning/explanation request.",
        )
        mode = "normal_answer"
        decision.evidence_required = False
    if not deterministic_platform_resource_request:
        decision.allowed_tools = tuple(
            tool for tool in decision.allowed_tools if tool != "published_resource_lookup"
        )
        if mode == "normal_answer" and not decision.allowed_tools:
            decision.allowed_tools = ("rag_search", "curriculum_lookup")
    resource_tool_allowed = "published_resource_lookup" in decision.allowed_tools
    platform_resource_request = bool(
        deterministic_platform_resource_request
        and resource_tool_allowed
        and mode == "needs_platform_evidence"
    )
    if not decision.valid:
        classification.update(
            {
                "intent": "policy_fallback_normal",
                "in_course_scope": True,
                "requires_evidence": False,
                "resource_request": False,
                "source_asset_request": source_asset_request,
                "experiment_safety": False,
                "assessment_leakage": False,
            }
        )
    else:
        classification.update(
            {
                "intent": mode,
                "in_course_scope": True if source_asset_request else mode != "refuse_out_of_scope",
                "requires_evidence": bool(platform_resource_request and (decision.evidence_required or mode == "needs_platform_evidence")),
                "resource_request": platform_resource_request,
                "source_asset_request": source_asset_request,
                "experiment_safety": mode == "safe_experiment_guidance",
                "assessment_leakage": mode == "assessment_hint",
            }
        )
    classification.update(
        {
            "policy_version": context.policy.version,
            "policy_decision_mode": mode,
            "policy_decision_valid": decision.valid,
            "policy_evidence_required": decision.evidence_required,
        }
    )


def _fixed_point_evidence_available(context: AgentRunContext) -> bool:
    if not context.point_evidence:
        return False
    try:
        if int(context.point_evidence.get("source_count") or 0) > 0:
            return True
    except (TypeError, ValueError):
        pass
    sources = context.point_evidence.get("sources")
    return isinstance(sources, list) and bool(sources)


def _is_explicit_evidence_request(question: str) -> bool:
    text = question.strip()
    if not text:
        return False
    lowered = text.lower()
    english_terms = (
        "cite",
        "citation",
        "source",
        "textbook",
        "according to the material",
        "according to course material",
        "page",
        "figure",
        "evidence",
    )
    if any(term in lowered for term in english_terms):
        return True
    chinese_terms = (
        "\u5f15\u7528",
        "\u51fa\u5904",
        "\u6765\u6e90",
        "\u8bfe\u672c",
        "\u6559\u6750",
        "\u8bfe\u7a0b\u8d44\u6599",
        "\u5e73\u53f0\u8d44\u6599",
        "\u6839\u636e\u8d44\u6599",
        "\u6839\u636e\u8bfe\u7a0b",
        "\u7b2c\u51e0\u9875",
        "\u9875\u7801",
        "\u56fe",
        "\u56fe\u7247",
        "\u8bc1\u636e",
    )
    return any(term in text for term in chinese_terms)


def _is_ordinary_learning_explanation(question: str) -> bool:
    text = question.strip()
    if not text:
        return False
    lowered = text.lower()
    english_terms = (
        "why",
        "how",
        "explain",
        "mechanism",
        "principle",
        "derive",
        "relationship",
        "what is",
    )
    if any(term in lowered for term in english_terms):
        return True
    chinese_terms = (
        "\u4e3a\u4ec0\u4e48",
        "\u4e3a\u4f55",
        "\u600e\u4e48",
        "\u5982\u4f55",
        "\u600e\u6837",
        "\u89e3\u91ca",
        "\u539f\u7406",
        "\u673a\u5236",
        "\u63a8\u5bfc",
        "\u7406\u89e3",
        "\u5173\u7cfb",
        "\u533a\u522b",
        "\u662f\u4ec0\u4e48",
        "\u4ec0\u4e48\u662f",
    )
    return any(term in text for term in chinese_terms)


def _retrieval_action_for_mode(mode: str) -> str:
    return {
        "skip": "skip_rag",
        "fixed_evidence": "use_fixed_evidence",
        "dynamic_rag": "use_dynamic_rag",
        "resource_lookup": "use_resource_lookup",
        "strict_evidence": "require_evidence",
    }.get(mode, "skip_rag")


def _student_retrieval_reason(mode: str) -> str:
    return {
        "skip": "\u65e0\u9700\u68c0\u7d22\uff0c\u6b63\u5728\u7ec4\u7ec7\u89e3\u91ca",
        "fixed_evidence": "\u6b63\u5728\u8bfb\u53d6\u5f53\u524d\u8bfe\u7a0b\u4e0a\u4e0b\u6587",
        "dynamic_rag": "\u6b63\u5728\u68c0\u7d22\u8bfe\u7a0b\u8d44\u6599",
        "resource_lookup": "\u6b63\u5728\u67e5\u627e\u5e73\u53f0\u8d44\u6e90",
        "strict_evidence": "\u6b63\u5728\u6838\u5bf9\u8bfe\u7a0b\u8bc1\u636e",
    }.get(mode, "\u6b63\u5728\u7ec4\u7ec7\u56de\u7b54")


def _normalize_allowed_tools(tools: tuple[str, ...] | list[str] | set[str]) -> tuple[str, ...]:
    allowed: list[str] = []
    seen: set[str] = set()
    for tool in tools:
        name = str(tool or "").strip()
        if name and name not in seen:
            seen.add(name)
            allowed.append(name)
    return tuple(allowed)


def _retrieval_decision_from_policy(context: AgentRunContext) -> StudentAIRetrievalDecision:
    decision = context.policy_decision
    classification = context.classification
    local_decision = _local_policy_decision_from_classification(classification)
    mode = decision.retrieval_mode if decision.valid and decision.retrieval_mode in RETRIEVAL_DECISION_MODES else ""
    decision_is_local = decision.raw.get("source") == "local_fallback" or decision.reason.startswith("local fallback")
    source = "llm_policy" if mode and not decision_is_local else "local_fallback"
    if not mode:
        mode = local_decision.retrieval_mode if local_decision.retrieval_mode in RETRIEVAL_DECISION_MODES else "skip"
    reason = decision.retrieval_reason or decision.reason or local_decision.retrieval_reason or local_decision.reason
    confidence = decision.retrieval_confidence
    strict_evidence = bool(decision.strict_evidence or decision.evidence_required or local_decision.strict_evidence)
    allowed_tools = _normalize_allowed_tools(decision.allowed_tools or local_decision.allowed_tools)

    fixed_available = _fixed_point_evidence_available(context)
    source_asset_request = bool(classification.get("source_asset_request"))
    explicit_evidence_request = source_asset_request or _is_explicit_evidence_request(context.request.question)
    ordinary_learning_explanation = (
        not explicit_evidence_request
        and _is_ordinary_learning_explanation(context.request.question)
    )
    resource_request = bool(classification.get("resource_request"))
    allow_rag = bool(classification.get("allow_rag_lookup", True))
    override_reason = ""

    if classification.get("experiment_safety") or classification.get("assessment_leakage") or not classification.get("in_course_scope", True):
        mode = "skip"
        source = "hard_rule"
        strict_evidence = False
        allowed_tools = ()
        override_reason = "safety_or_scope_guardrail"
    elif resource_request:
        if mode not in {"resource_lookup", "strict_evidence"}:
            override_reason = "deterministic_platform_resource_request"
        mode = "resource_lookup"
        source = "hard_rule"
        strict_evidence = True
        allowed_tools = _normalize_allowed_tools((*allowed_tools, "published_resource_lookup"))
    elif explicit_evidence_request:
        if mode not in {"dynamic_rag", "fixed_evidence", "strict_evidence"}:
            override_reason = "deterministic_explicit_evidence_request"
        mode = "strict_evidence" if allow_rag or not fixed_available else "fixed_evidence"
        source = "hard_rule"
        strict_evidence = True
        allowed_tools = _normalize_allowed_tools((*allowed_tools, "rag_search", "curriculum_lookup"))
    elif ordinary_learning_explanation and mode in {"dynamic_rag", "strict_evidence", "resource_lookup"}:
        override_reason = "deterministic_ordinary_learning_skip"
        mode = "fixed_evidence" if fixed_available else "skip"
        source = "hard_rule"
        strict_evidence = False
        allowed_tools = _normalize_allowed_tools(tool for tool in allowed_tools if tool != "rag_search" and tool != "published_resource_lookup")
    elif fixed_available and mode == "skip":
        mode = "fixed_evidence"
        source = "hard_rule" if source == "local_fallback" else source
        reason = reason or "fixed point evidence is available for this turn"
    elif mode == "fixed_evidence" and not fixed_available:
        mode = "skip"
        override_reason = "fixed_evidence_unavailable"

    if not allow_rag and mode in {"dynamic_rag", "strict_evidence"} and not resource_request:
        source = "feature_disabled"
        override_reason = override_reason or "rag_feature_disabled"
        if fixed_available:
            mode = "fixed_evidence"
        elif explicit_evidence_request:
            mode = "strict_evidence"
        else:
            mode = "skip"

    should_call_resource_lookup = resource_request and mode in {"resource_lookup", "strict_evidence"}
    should_call_rag = bool(allow_rag and mode in {"dynamic_rag", "strict_evidence"} and not should_call_resource_lookup)
    should_use_fixed = fixed_available and mode in {"fixed_evidence", "skip", "dynamic_rag", "strict_evidence"}
    if should_call_rag:
        allowed_tools = _normalize_allowed_tools((*allowed_tools, "rag_search", "curriculum_lookup"))
    if should_call_resource_lookup:
        allowed_tools = _normalize_allowed_tools((*allowed_tools, "published_resource_lookup"))
    if mode in {"skip", "fixed_evidence"}:
        allowed_tools = tuple(tool for tool in allowed_tools if tool != "rag_search")

    return StudentAIRetrievalDecision(
        mode=mode if mode in RETRIEVAL_DECISION_MODES else "skip",
        source=source if source in RETRIEVAL_DECISION_SOURCES else "local_fallback",
        reason=reason[:300],
        student_reason=_student_retrieval_reason(mode),
        confidence=confidence,
        strict_evidence=strict_evidence,
        allowed_tools=allowed_tools,
        should_call_rag=should_call_rag,
        should_call_resource_lookup=should_call_resource_lookup,
        should_use_fixed_point_evidence=should_use_fixed,
        override_reason=override_reason,
    )


def _apply_retrieval_decision(context: AgentRunContext) -> None:
    context.retrieval_decision = _retrieval_decision_from_policy(context)
    decision = context.retrieval_decision
    if decision.strict_evidence and decision.mode in {"dynamic_rag", "fixed_evidence", "strict_evidence"}:
        context.classification["requires_evidence"] = True
    if (
        decision.mode == "skip"
        and not decision.should_call_rag
        and not decision.should_call_resource_lookup
        and not decision.should_use_fixed_point_evidence
    ):
        context.sources = []
    context.classification.update(
        {
            "retrieval_decision": decision.as_dict(),
            "retrieval_mode": decision.mode,
            "retrieval_decision_source": decision.source,
            "retrieval_strict_evidence": decision.strict_evidence,
            "retrieval_should_call_rag": decision.should_call_rag,
            "retrieval_should_call_resource_lookup": decision.should_call_resource_lookup,
            "retrieval_should_use_fixed_point_evidence": decision.should_use_fixed_point_evidence,
            "retrieval_override_reason": decision.override_reason,
        }
    )
    context.add_guardrail("retrieval_decision", _retrieval_action_for_mode(decision.mode), decision.reason or decision.student_reason)
    if decision.override_reason:
        context.add_guardrail("retrieval_decision_override", decision.override_reason, decision.reason or decision.student_reason)


def approved_tool_registry(context: AgentRunContext) -> dict[str, Callable[..., Any]]:
    return {
        "rag_search": lambda query: rag_search_tool(context, query),
        "curriculum_lookup": lambda query: curriculum_lookup_tool(context, query),
        "published_resource_lookup": lambda target_type=None, target_id=None: published_resource_lookup_tool(
            context, target_type, target_id
        ),
        "own_student_progress_lookup": lambda: own_student_progress_lookup_tool(context),
    }


async def run_agent(
    request: AgentAskRequest,
    repositories: RepositoryProvider | None = None,
    settings: Settings | None = None,
    policy: AgentPolicy | None = None,
) -> AgentAskResponse:
    repositories = repositories or get_repositories()
    settings = settings or get_settings()
    context = create_agent_context(
        request=request,
        repositories=repositories,
        policy=policy or load_agent_policy(),
        classification=classify_agent_request(request),
        settings=settings,
    )

    try:
        _build_point_evidence_package(context)
        context.policy_decision = await _policy_gate_decision(context, settings)
        _apply_policy_decision_to_classification(context)
        _apply_retrieval_decision(context)
        answer = _preflight_response(context)
        if answer is None:
            answer = await _run_with_optional_sdk(context, settings)
        answer = _apply_output_guardrails(context, answer)
        response = build_agent_response(context, answer)
        _persist_agent_log(context, response)
        return response
    except Exception as exc:
        _persist_agent_error_log(context, exc)
        raise


async def run_agent_stream(
    request: AgentAskRequest,
    repositories: RepositoryProvider | None = None,
    settings: Settings | None = None,
    policy: AgentPolicy | None = None,
) -> AsyncIterator[dict[str, Any]]:
    repositories = repositories or get_repositories()
    settings = settings or get_settings()
    context = create_agent_context(
        request=request,
        repositories=repositories,
        policy=policy or load_agent_policy(),
        classification=classify_agent_request(request),
        settings=settings,
    )

    try:
        thinking_sequence = 0

        def next_trace_event(key: str) -> dict[str, Any] | None:
            nonlocal thinking_sequence
            thinking_sequence += 1
            return _agent_trace_event(key, sequence=thinking_sequence)

        _build_point_evidence_package(context)
        trace = next_trace_event("policy")
        if trace:
            yield trace
        yield {"event": "status", "message": "正在判断问题类型与安全策略"}
        context.policy_decision = await _policy_gate_decision(context, settings)
        _apply_policy_decision_to_classification(context)
        trace = next_trace_event("retrieval_decision")
        if trace:
            yield trace
        _apply_retrieval_decision(context)
        answer = _preflight_response(context)

        if answer is None:
            answer_parts: list[str] = []
            if _sdk_enabled(settings):
                trace_keys = ["context"]
                if context.retrieval_decision.should_use_fixed_point_evidence:
                    trace_keys.append("fixed_evidence")
                if context.retrieval_decision.should_call_rag or context.retrieval_decision.should_call_resource_lookup:
                    trace_keys.extend(["retrieval", "evidence_quality"])
                else:
                    trace_keys.append("retrieval_skip")
                for trace_key in trace_keys:
                    trace = next_trace_event(trace_key)
                    if trace:
                        yield trace
                yield {"event": "status", "message": "正在连接模型，开始流式生成"}
                try:
                    if _reasoning_summary_enabled(settings):
                        trace = next_trace_event("generation")
                        if trace:
                            yield trace
                        async for item in _run_openai_responses_stream(context, settings):
                            if item.get("event") == "delta" and isinstance(item.get("delta"), str):
                                answer_parts.append(item["delta"])
                            yield item
                    else:
                        trace = next_trace_event("generation")
                        if trace:
                            yield trace
                        async for delta in _run_openai_chat_completion_stream(context, settings):
                            if not delta:
                                continue
                            answer_parts.append(delta)
                            yield {"event": "delta", "delta": delta}
                    answer = "".join(answer_parts).strip()
                except Exception as exc:
                    context.add_guardrail(
                        "responses_reasoning_stream_fallback" if _reasoning_summary_enabled(settings) else "chat_completion_stream_fallback",
                        "fallback_to_local",
                        f"流式模型调用失败：{exc.__class__.__name__}",
                    )
                    yield {"event": "status", "message": "模型流式调用失败，已切换到本地兜底"}
                    trace = next_trace_event("fallback")
                    if trace:
                        yield trace
                    context.mode = "local"
                    answer_parts = []
                    answer = _run_local_agent(context)
                    for delta in _chunk_stream_text(answer):
                        yield {"event": "delta", "delta": delta}
            else:
                yield {"event": "status", "message": "未配置可用模型，使用本地兜底回答"}
                trace = next_trace_event("fallback")
                if trace:
                    yield trace
                context.mode = "local"
                answer = _run_local_agent(context)
                for delta in _chunk_stream_text(answer):
                    yield {"event": "delta", "delta": delta}
        else:
            trace = next_trace_event("generation")
            if trace:
                yield trace
            for delta in _chunk_stream_text(answer):
                yield {"event": "delta", "delta": delta}

        guarded_answer = _apply_output_guardrails(context, answer)
        if guarded_answer != answer:
            answer = guarded_answer
            yield {"event": "replace", "answer": answer}

        response = build_agent_response(context, answer)
        _persist_agent_log(context, response)
        yield {"event": "final", "response": _dump_agent_response(response)}
    except Exception as exc:
        _persist_agent_error_log(context, exc)
        yield {"event": "error", "message": str(exc) or exc.__class__.__name__}


def rag_search_tool(context: AgentRunContext, query: str) -> dict[str, Any]:
    if not context.classification.get("allow_rag_lookup", True):
        result = {"evidence": [], "disabled": True}
        context.add_guardrail("rag_lookup_disabled", "skip_rag_lookup", "学生侧 AI RAG 接入已关闭。")
        context.record_tool("rag_search", {"query": query}, result["evidence"])
        return result
    settings = context.settings or get_settings()
    legacy_retrieve = lambda lookup_query, lookup_limit: _retrieve_context(
        context.repositories,
        lookup_query,
        context.request,
        limit=lookup_limit,
    )
    hybrid_result = retrieve_hybrid_context(
        repositories=context.repositories,
        question=query,
        request=context.request,
        settings=settings,
        legacy_retrieve=legacy_retrieve,
        query_generator=lambda lookup_query: _generate_retrieval_queries(context, settings, lookup_query),
        limit=max(1, settings.rag_final_top_k),
    )
    chunks = hybrid_result.chunks
    context.rag_traces.append(hybrid_result.trace)
    sources = [_source_from_chunk(chunk) for chunk in chunks]
    context.sources = _merge_sources(context.sources, sources)
    evidence = [_source_evidence_payload(source) for source in sources]
    result = {
        "evidence": evidence,
        "trace": hybrid_result.trace,
    }
    context.record_tool(
        "rag_search",
        {
            "query": query,
            "mode": hybrid_result.trace.get("mode"),
            "generated_queries": hybrid_result.trace.get("generated_queries") or [],
        },
        result["evidence"],
    )
    return result


def curriculum_lookup_tool(context: AgentRunContext, query: str) -> dict[str, Any]:
    request = context.request
    chapters = context.repositories.content.chapters()
    units = context.repositories.content.units()
    points = context.repositories.content.knowledge_points()
    if request.chapter_id:
        chapters = [item for item in chapters if item.get("chapter_id") == request.chapter_id]
        units = [item for item in units if item.get("chapter_id") == request.chapter_id]
        points = [item for item in points if item.get("chapter_id") == request.chapter_id]
    if request.knowledge_point_ids:
        wanted = set(request.knowledge_point_ids)
        points = [item for item in points if item.get("knowledge_point_id") in wanted or item.get("id") in wanted]
    scored_points = sorted(
        points,
        key=lambda item: keyword_score(query, {"text": item.get("content") or item.get("unit_title") or ""}, chapter_id=request.chapter_id),
        reverse=True,
    )[:8]
    result = {"chapters": chapters[:5], "units": units[:8], "knowledge_points": scored_points}
    context.record_tool("curriculum_lookup", {"query": query}, result)
    return result


def published_resource_lookup_tool(
    context: AgentRunContext,
    target_type: str | None = None,
    target_id: str | None = None,
) -> dict[str, Any]:
    request = context.request
    lookups: list[tuple[str, str]] = []
    if target_type and target_id:
        lookups.append((target_type, target_id))
    if request.experiment_id:
        lookups.append(("experiment", request.experiment_id))
    for kp_id in request.knowledge_point_ids:
        lookups.append(("knowledge_point", kp_id))
    if request.chapter_id:
        lookups.append(("chapter", request.chapter_id))

    resources: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item_type, item_id in lookups:
        for resource in context.repositories.media.list_ready_bindings(item_type, item_id):
            resource_id = str(resource.get("binding_id") or resource.get("media_id") or resource)
            if resource_id not in seen:
                seen.add(resource_id)
                resources.append(resource)

    result = {"resources": resources}
    context.record_tool("published_resource_lookup", {"targets": lookups}, resources)
    return result


def own_student_progress_lookup_tool(context: AgentRunContext) -> dict[str, Any]:
    if not context.request.student_id or not context.classification.get("allow_progress_lookup"):
        result = {"allowed": False, "reason": "student_context_required"}
        context.record_tool("own_student_progress_lookup", {}, result)
        return result
    mastery = context.repositories.learning.load_mastery().get(context.request.student_id, {})
    weak_points = [
        {"knowledge_point_id": kp_id, "mastery_score": state.get("mastery_score", 0)}
        for kp_id, state in mastery.items()
        if float(state.get("mastery_score", 0)) < 60
    ][:8]
    result = {"allowed": True, "weak_knowledge_points": weak_points}
    context.record_tool("own_student_progress_lookup", {"student_id": context.request.student_id}, result)
    return result


def _preflight_response(context: AgentRunContext) -> str | None:
    classification = context.classification
    if classification["simple_greeting"]:
        context.add_guardrail("simple_greeting", "allow_without_tools", "简单问候不需要检索。")
        context.mode = "local"
        return "你好，我可以帮你复习无机化学实验、知识点、现象解释和已发布资料。"
    if not classification["in_course_scope"]:
        context.add_guardrail("course_scope", "refuse", "问题超出无机化学实验学习平台范围。")
        context.mode = "guardrail_refusal"
        return "这个问题超出了当前无机化学实验学习范围。我可以帮你看课程知识点、实验现象、方程式、资料或复习建议。"
    if classification["experiment_safety"]:
        context.add_guardrail("experiment_safety", "refuse_unsafe_detail", "请求包含不安全实验操作细节。")
        context.mode = "guardrail_refusal"
        return "这个请求涉及不安全的实验操作细节，我不能提供私下操作步骤、剂量或危险条件。请只在教师指导和实验室规范下进行实验；我可以改为解释相关原理、现象和安全注意事项。"
    if classification["assessment_leakage"]:
        context.add_guardrail("assessment_answer_leakage", "provide_hint", "学生疑似索要测验或考试直接答案。")
        context.mode = "guardrail_hint"
        return "我不能直接给出测验答案。你可以先判断题目考的是哪个知识点、相关反应现象或方程式；把你的思路发来，我可以帮你检查推理并给提示。"
    return None


async def _run_with_optional_sdk(context: AgentRunContext, settings: Settings) -> str:
    if _sdk_enabled(settings):
        try:
            return await _run_openai_agents_sdk(context, settings)
        except Exception as exc:
            context.add_guardrail("agent_sdk_fallback", "fallback_to_local", f"SDK不可用或调用失败：{exc.__class__.__name__}")
            if not context.classification.get("resource_request"):
                try:
                    return await _run_openai_chat_completion(context, settings)
                except Exception as chat_exc:
                    context.add_guardrail(
                        "chat_completion_fallback",
                        "fallback_to_local",
                        f"普通模型兜底失败：{chat_exc.__class__.__name__}",
                    )
    context.mode = "local"
    return _run_local_agent(context)


async def _run_openai_agents_sdk(context: AgentRunContext, settings: Settings) -> str:
    from agents import Agent, Runner, function_tool

    os.environ.setdefault("OPENAI_API_KEY", settings.agent_llm_api_key)
    os.environ.setdefault("OPENAI_AGENTS_DISABLE_TRACING", "1")
    if settings.agent_llm_base_url:
        os.environ.setdefault("OPENAI_BASE_URL", settings.agent_llm_base_url)

    tools = approved_tool_registry(context)

    @function_tool
    def rag_search(query: str) -> dict[str, Any]:
        """Search approved course evidence and return source-grounded snippets."""
        return tools["rag_search"](query)

    @function_tool
    def curriculum_lookup(query: str) -> dict[str, Any]:
        """Look up published curriculum chapters, knowledge units, and knowledge points."""
        return tools["curriculum_lookup"](query)

    @function_tool
    def published_resource_lookup(target_type: str | None = None, target_id: str | None = None) -> dict[str, Any]:
        """Find ready and published videos or media resources for course entities."""
        return tools["published_resource_lookup"](target_type, target_id)

    @function_tool
    def own_student_progress_lookup() -> dict[str, Any]:
        """Look up only the current student's own mastery summary."""
        return tools["own_student_progress_lookup"]()

    allowed_tool_names = set(context.retrieval_decision.allowed_tools or context.policy_decision.allowed_tools)
    if context.policy_decision.mode == "needs_platform_evidence" and not allowed_tool_names:
        allowed_tool_names = {"rag_search", "curriculum_lookup"}
    if not allowed_tool_names:
        allowed_tool_names = {"curriculum_lookup"}

    agent = Agent(
        name="Inorganic Chemistry Learning Agent",
        model=settings.agent_llm_model,
        instructions=_agent_instructions(context),
        tools=[
            *([rag_search] if context.retrieval_decision.should_call_rag and "rag_search" in allowed_tool_names else []),
            *([curriculum_lookup] if "curriculum_lookup" in allowed_tool_names else []),
            *([published_resource_lookup] if context.retrieval_decision.should_call_resource_lookup and "published_resource_lookup" in allowed_tool_names else []),
            *([own_student_progress_lookup] if "own_student_progress_lookup" in allowed_tool_names else []),
        ],
    )
    kwargs: dict[str, Any] = {}
    try:
        from agents import RunConfig

        kwargs["run_config"] = RunConfig(tracing_disabled=True)
    except Exception:
        pass
    result = await Runner.run(agent, _agent_user_input(context), **kwargs)
    context.mode = "openai_agents_sdk"
    return str(result.final_output).strip()


def _source_asset_answer(figure_evidence_items: list[dict[str, Any]]) -> str:
    if not figure_evidence_items:
        return "当前这轮检索还没有找到可直接展示的教材图。你可以把图名、页码或相关概念说得更具体一些，我会继续按教材证据检索。"
    lines = [
        "可以。本轮检索已经找到对应的教材图，右侧“来源证据”里会展示可预览的图像。",
        "",
        "已命中的图像证据：",
    ]
    for index, item in enumerate(figure_evidence_items[:3], start=1):
        caption = item.get("caption") or item.get("source_file") or "教材图"
        page = f"p.{item.get('page_number')}" if item.get("page_number") else ""
        asset_count = item.get("asset_count") or 0
        suffix = f"（{page}，{asset_count} 个图像资产）" if page else f"（{asset_count} 个图像资产）"
        lines.append(f"{index}. {caption}{suffix}")
        image_asset = next(
            (
                asset
                for asset in item.get("asset_files", [])
                if isinstance(asset, dict) and asset.get("path") and asset.get("kind") != "page"
            ),
            None,
        ) or next(
            (
                asset
                for asset in item.get("asset_files", [])
                if isinstance(asset, dict) and asset.get("path")
            ),
            None,
        )
        if image_asset:
            markdown = image_asset.get("markdown") or _source_asset_markdown(image_asset, caption)
            if markdown:
                lines.append(f"   {markdown}")
    lines.extend([
        "",
        "你可以在右侧来源卡片中查看原图；我也可以继续按这张图解释稳定区、氧化态和氧化性关系。",
    ])
    return "\n".join(lines)


def _has_usable_evidence(evidence: list[dict[str, Any]]) -> bool:
    for item in evidence:
        if not isinstance(item, dict):
            continue
        if item.get("text_preview") or item.get("caption") or item.get("source_file"):
            return True
        assets = item.get("assets")
        if isinstance(assets, list) and assets:
            return True
    return False


def _answer_evidence_items(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "source_file": item.get("source_file"),
            "page_number": item.get("page_number"),
            "text_preview": item.get("text_preview"),
            "caption": item.get("caption"),
            "content_type": item.get("content_type"),
            "asset_count": len(item.get("assets") or []),
            "markdown_images": item.get("markdown_images") or [],
        }
        for item in evidence[:5]
    ]


def _collect_retrieval_context_for_answer(context: AgentRunContext) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    decision = context.retrieval_decision
    evidence: list[dict[str, Any]] = []
    platform_resources: list[dict[str, Any]] = []
    if decision.should_call_resource_lookup:
        platform_resources = published_resource_lookup_tool(context).get("resources") or []
        if not platform_resources:
            context.add_guardrail("no_fabricated_resource", "state_unavailable", "No ready + published platform resource matched this request.")
    if decision.should_call_rag:
        evidence = rag_search_tool(context, context.request.question).get("evidence") or []
        if not _has_usable_evidence(evidence):
            context.add_guardrail("rag_no_match", "answer_from_model_knowledge", "RAG did not return usable selected evidence for this turn.")
            if decision.strict_evidence:
                context.add_guardrail("retrieval_no_usable_evidence", "strict_evidence_missing", "Strict evidence was requested but no usable RAG evidence was selected.")
    elif not context.classification.get("allow_rag_lookup", True) and not decision.should_call_resource_lookup:
        context.add_guardrail("rag_lookup_disabled", "answer_without_rag", "Student RAG lookup is disabled for this turn.")
    return evidence, platform_resources


async def _legacy_run_openai_chat_completion_always_rag(context: AgentRunContext, settings: Settings) -> str:
    from openai import OpenAI

    curriculum = curriculum_lookup_tool(context, context.request.question)
    evidence: list[dict[str, Any]] = []
    if context.classification.get("allow_rag_lookup", True):
        evidence = rag_search_tool(context, context.request.question).get("evidence") or []
        if not evidence:
            context.add_guardrail("rag_no_match", "answer_from_model_knowledge", "RAG 未命中可用课程证据，改用模型化学常识回答。")
    else:
        context.add_guardrail("rag_lookup_disabled", "answer_from_model_knowledge", "本次未开启 RAG 检索，改用模型化学常识回答。")

    point_titles = [
        point.get("content")
        for point in curriculum.get("knowledge_points", [])
        if point.get("content")
    ][:5]
    fixed_point_evidence = context.point_evidence.get("sources", []) if context.point_evidence else []
    evidence_items = [
        {
            "source_file": item.get("source_file"),
            "page_number": item.get("page_number"),
            "text_preview": item.get("text_preview"),
            "caption": item.get("caption"),
            "content_type": item.get("content_type"),
            "asset_count": len(item.get("assets") or []),
            "markdown_images": item.get("markdown_images") or [],
        }
        for item in evidence[:5]
    ]
    figure_evidence_items = _figure_evidence_items(context, evidence)
    if context.classification.get("source_asset_request"):
        context.mode = "source_asset_evidence"
        return _source_asset_answer(figure_evidence_items)
    client = OpenAI(
        api_key=settings.agent_llm_api_key or os.getenv("OPENAI_API_KEY"),
        base_url=settings.agent_llm_base_url or None,
        timeout=20.0,
    )
    response = client.chat.completions.create(
        model=settings.agent_llm_model,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是无机化学实验学习助手。请用中文回答学生的课程问题。"
                    "RAG/课程证据只是辅助：如果提供了证据，优先参考证据并避免和证据冲突；"
                    "如果没有证据或本次未开启 RAG，就用你可靠的无机化学常识回答。"
                    "不要声称平台存在某个视频、资源或教材出处，除非证据中明确提供。"
                    "fixed_point_evidence is trusted evidence for the selected experiment video point and remains available even when supplemental RAG is disabled. "
                    "Use it before supplemental rag_evidence when answering point explanations. "
                    "If rag_figure_evidence is not empty or any rag_evidence item has asset_count > 0, tell the student the source figure is available in the evidence panel and summarize what it shows; do not say the figure is unavailable."
                    "When a source figure helps answer the question, include one provided Markdown image reference exactly as-is from markdown_images or rag_figure_evidence.asset_files[].markdown."
                    "If source_figures_available is true, you must not say the system has no image files or asset_count is zero."
                    f"{CHEM_MATH_OUTPUT_CONTRACT}"
                    "不要提供危险实验的私下操作步骤，也不要直接给测验答案。"
                    "回答要适合学生阅读，简洁、分点、可复习。"
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "question": context.request.question,
                        "chapter_id": context.request.chapter_id,
                        "experiment_id": context.request.experiment_id,
                        "knowledge_point_ids": context.request.knowledge_point_ids,
                        "conversation_history": _conversation_history_payload(context),
                        "related_knowledge_points": point_titles,
                        "point_context": context.point_evidence,
                        "fixed_point_evidence": fixed_point_evidence,
                        "rag_evidence": evidence_items,
                        "rag_figure_evidence": figure_evidence_items,
                        "source_figures_available": bool(figure_evidence_items),
                        "source_figure_count": len(figure_evidence_items),
                    },
                    ensure_ascii=False,
                ),
            },
        ],
    )
    context.mode = "openai_chat_fallback"
    content = response.choices[0].message.content if response.choices else ""
    return str(content or "").strip()


def _legacy_openai_answer_context_payload_always_rag(context: AgentRunContext) -> tuple[dict[str, Any], str | None]:
    curriculum = curriculum_lookup_tool(context, context.request.question)
    evidence: list[dict[str, Any]] = []
    if context.classification.get("allow_rag_lookup", True):
        evidence = rag_search_tool(context, context.request.question).get("evidence") or []
        if not evidence:
            context.add_guardrail("rag_no_match", "answer_from_model_knowledge", "RAG did not return usable student evidence; answer from model chemistry knowledge.")
    else:
        context.add_guardrail("rag_lookup_disabled", "answer_from_model_knowledge", "Student RAG lookup was disabled for this turn.")

    figure_evidence_items = _figure_evidence_items(context, evidence)
    if context.classification.get("source_asset_request"):
        context.mode = "source_asset_evidence"
        return {}, _source_asset_answer(figure_evidence_items)

    point_titles = [
        point.get("content")
        for point in curriculum.get("knowledge_points", [])
        if point.get("content")
    ][:5]
    fixed_point_evidence = context.point_evidence.get("sources", []) if context.point_evidence else []
    evidence_items = [
        {
            "source_file": item.get("source_file"),
            "page_number": item.get("page_number"),
            "text_preview": item.get("text_preview"),
            "caption": item.get("caption"),
            "content_type": item.get("content_type"),
            "asset_count": len(item.get("assets") or []),
            "markdown_images": item.get("markdown_images") or [],
        }
        for item in evidence[:5]
    ]
    return {
        "question": context.request.question,
        "chapter_id": context.request.chapter_id,
        "experiment_id": context.request.experiment_id,
        "knowledge_point_ids": context.request.knowledge_point_ids,
        "conversation_history": _conversation_history_payload(context),
        "related_knowledge_points": point_titles,
        "point_context": context.point_evidence,
        "fixed_point_evidence": fixed_point_evidence,
        "rag_evidence": evidence_items,
        "rag_figure_evidence": figure_evidence_items,
        "source_figures_available": bool(figure_evidence_items),
        "source_figure_count": len(figure_evidence_items),
        "policy_decision": context.policy_decision.as_dict(),
    }, None


async def _run_openai_responses_stream(context: AgentRunContext, settings: Settings) -> AsyncIterator[dict[str, Any]]:
    payload, direct_answer = _openai_answer_context_payload(context)
    if direct_answer is not None:
        for delta in _chunk_stream_text(direct_answer):
            yield {"event": "delta", "delta": delta}
        return

    client = _openai_client(settings, timeout=30.0)
    summary_buffer = ""
    last_summary = ""
    context.mode = "openai_responses_stream"
    with client.responses.stream(
        model=settings.agent_llm_model,
        instructions=(
            f"{_agent_instructions(context)}\n"
            "Follow retrieval_decision: use provided evidence for evidence-bound claims, and use reliable chemistry knowledge when retrieval was skipped. "
            "Do not claim platform resources, pages, figures, or uploaded materials exist unless they are present in the payload. "
            "Answer the student in concise Chinese. "
            "If reasoning summaries are produced, keep them high-level and student-safe."
        ),
        input=json.dumps(payload, ensure_ascii=False),
        reasoning={
            "summary": _reasoning_summary_mode(settings),
            "effort": _reasoning_effort(settings),
        },
        temperature=0.2,
    ) as stream:
        for event in stream:
            event_type = _response_event_type(event)
            if event_type == "response.output_text.delta":
                delta = _response_event_text(event, "delta")
                if delta:
                    yield {"event": "delta", "delta": delta}
                continue
            if event_type == "response.reasoning_summary_text.delta":
                summary_buffer += _response_event_text(event, "delta")
                thinking = _thinking_event(
                    source="reasoning_summary",
                    message=summary_buffer,
                    phase="reasoning",
                    sequence=_response_event_sequence(event),
                )
                if thinking and thinking["message"] != last_summary:
                    last_summary = str(thinking["message"])
                    yield thinking
                continue
            if event_type == "response.reasoning_summary_text.done":
                summary_text = _response_event_text(event, "text") or summary_buffer
                thinking = _thinking_event(
                    source="reasoning_summary",
                    message=summary_text,
                    phase="reasoning",
                    sequence=_response_event_sequence(event),
                )
                if thinking and thinking["message"] != last_summary:
                    last_summary = str(thinking["message"])
                    yield thinking
                continue
            if event_type in {"response.reasoning_text.delta", "response.reasoning_text.done"}:
                continue
            if event_type in {"response.error", "response.failed", "response.incomplete"}:
                raise RuntimeError("responses stream failed")


async def _legacy_run_openai_chat_completion_stream_always_rag(context: AgentRunContext, settings: Settings) -> AsyncIterator[str]:
    from openai import OpenAI

    curriculum = curriculum_lookup_tool(context, context.request.question)
    evidence: list[dict[str, Any]] = []
    if context.classification.get("allow_rag_lookup", True):
        evidence = rag_search_tool(context, context.request.question).get("evidence") or []
        if not evidence:
            context.add_guardrail("rag_no_match", "answer_from_model_knowledge", "RAG 未命中可用课程证据，改用模型课程知识回答。")
    else:
        context.add_guardrail("rag_lookup_disabled", "answer_from_model_knowledge", "本次未启用 RAG 检索，使用模型课程知识回答。")

    point_titles = [
        point.get("content")
        for point in curriculum.get("knowledge_points", [])
        if point.get("content")
    ][:5]
    fixed_point_evidence = context.point_evidence.get("sources", []) if context.point_evidence else []
    evidence_items = [
        {
            "source_file": item.get("source_file"),
            "page_number": item.get("page_number"),
            "text_preview": item.get("text_preview"),
            "caption": item.get("caption"),
            "content_type": item.get("content_type"),
            "asset_count": len(item.get("assets") or []),
            "markdown_images": item.get("markdown_images") or [],
        }
        for item in evidence[:5]
    ]
    figure_evidence_items = _figure_evidence_items(context, evidence)
    if context.classification.get("source_asset_request"):
        context.mode = "source_asset_evidence"
        answer = _source_asset_answer(figure_evidence_items)
        for delta in _chunk_stream_text(answer):
            yield delta
        return
    client = OpenAI(
        api_key=settings.agent_llm_api_key or os.getenv("OPENAI_API_KEY"),
        base_url=settings.agent_llm_base_url or None,
        timeout=30.0,
    )
    stream = client.chat.completions.create(
        model=settings.agent_llm_model,
        temperature=0.2,
        stream=True,
        messages=[
            {
                "role": "system",
                "content": (
                    "你是无机化学实验学习助手。请用中文、面向学生、简洁回答。"
                    "优先基于给定课程证据和实验上下文回答；没有证据时要说明平台暂未找到可靠来源。"
                    "fixed_point_evidence is trusted evidence for the selected experiment video point and remains available even when supplemental RAG is disabled. "
                    "Use it before supplemental rag_evidence when answering point explanations. "
                    "If rag_figure_evidence is not empty or any rag_evidence item has asset_count > 0, tell the student the source figure is available in the evidence panel and summarize what it shows; do not say the figure is unavailable."
                    "When a source figure helps answer the question, include one provided Markdown image reference exactly as-is from markdown_images or rag_figure_evidence.asset_files[].markdown."
                    "If source_figures_available is true, you must not say the system has no image files or asset_count is zero."
                    f"{CHEM_MATH_OUTPUT_CONTRACT}"
                    "不要提供危险家庭实验步骤，不要直接泄露测验答案，只给思路和概念提示。"
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "question": context.request.question,
                        "chapter_id": context.request.chapter_id,
                        "experiment_id": context.request.experiment_id,
                        "knowledge_point_ids": context.request.knowledge_point_ids,
                        "conversation_history": _conversation_history_payload(context),
                        "related_knowledge_points": point_titles,
                        "point_context": context.point_evidence,
                        "fixed_point_evidence": fixed_point_evidence,
                        "rag_evidence": evidence_items,
                        "rag_figure_evidence": figure_evidence_items,
                        "source_figures_available": bool(figure_evidence_items),
                        "source_figure_count": len(figure_evidence_items),
                        "policy_decision": context.policy_decision.as_dict(),
                    },
                    ensure_ascii=False,
                ),
            },
        ],
    )
    context.mode = "openai_chat_stream"
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content or ""
        if delta:
            yield str(delta)


async def _run_openai_chat_completion(context: AgentRunContext, settings: Settings) -> str:
    from openai import OpenAI

    payload, direct_answer = _openai_answer_context_payload(context)
    if direct_answer is not None:
        return direct_answer
    client = OpenAI(
        api_key=settings.agent_llm_api_key or os.getenv("OPENAI_API_KEY"),
        base_url=settings.agent_llm_base_url or None,
        timeout=20.0,
    )
    response = client.chat.completions.create(
        model=settings.agent_llm_model,
        temperature=0.2,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are Atom, a student-facing inorganic chemistry learning assistant. "
                    "Answer in concise Chinese. Use fixed_point_evidence first when it is present. "
                    "Use rag_evidence only when retrieval_decision says supplemental retrieval ran. "
                    "Platform resources, citations, source images, textbook/material references, and answers explicitly "
                    "according to course material must be grounded in provided evidence or platform_resources. "
                    "Ordinary concept explanations, mechanisms, equations, and follow-ups may use reliable chemistry "
                    "knowledge when retrieval was skipped or unavailable. Do not claim platform evidence, pages, figures, "
                    "or uploaded resources exist unless they are present in the payload. "
                    "If source_figures_available is true, summarize what the figure evidence shows and include one "
                    "provided Markdown image reference exactly as-is when useful. "
                    f"{CHEM_MATH_OUTPUT_CONTRACT}"
                ),
            },
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
    )
    context.mode = "openai_chat_fallback"
    content = response.choices[0].message.content if response.choices else ""
    return str(content or "").strip()


def _openai_answer_context_payload(context: AgentRunContext) -> tuple[dict[str, Any], str | None]:
    curriculum = curriculum_lookup_tool(context, context.request.question)
    evidence, platform_resources = _collect_retrieval_context_for_answer(context)
    figure_evidence_items = _figure_evidence_items(context, evidence)
    if context.classification.get("source_asset_request"):
        context.mode = "source_asset_evidence"
        return {}, _source_asset_answer(figure_evidence_items)

    point_titles = [
        point.get("content")
        for point in curriculum.get("knowledge_points", [])
        if point.get("content")
    ][:5]
    fixed_point_evidence = context.point_evidence.get("sources", []) if context.point_evidence else []
    return {
        "question": context.request.question,
        "chapter_id": context.request.chapter_id,
        "experiment_id": context.request.experiment_id,
        "knowledge_point_ids": context.request.knowledge_point_ids,
        "conversation_history": _conversation_history_payload(context),
        "related_knowledge_points": point_titles,
        "point_context": context.point_evidence,
        "fixed_point_evidence": fixed_point_evidence,
        "rag_evidence": _answer_evidence_items(evidence),
        "rag_figure_evidence": figure_evidence_items,
        "platform_resources": platform_resources[:5],
        "source_figures_available": bool(figure_evidence_items),
        "source_figure_count": len(figure_evidence_items),
        "policy_decision": context.policy_decision.as_dict(),
        "retrieval_decision": context.retrieval_decision.as_dict(),
    }, None


async def _run_openai_chat_completion_stream(context: AgentRunContext, settings: Settings) -> AsyncIterator[str]:
    from openai import OpenAI

    payload, direct_answer = _openai_answer_context_payload(context)
    if direct_answer is not None:
        for delta in _chunk_stream_text(direct_answer):
            yield delta
        return
    client = OpenAI(
        api_key=settings.agent_llm_api_key or os.getenv("OPENAI_API_KEY"),
        base_url=settings.agent_llm_base_url or None,
        timeout=30.0,
    )
    stream = client.chat.completions.create(
        model=settings.agent_llm_model,
        temperature=0.2,
        stream=True,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are Atom, a student-facing inorganic chemistry learning assistant. "
                    "Answer in concise Chinese. Use fixed_point_evidence first when it is present. "
                    "Use rag_evidence only when retrieval_decision says supplemental retrieval ran. "
                    "Platform resources, citations, source images, textbook/material references, and answers explicitly "
                    "according to course material must be grounded in provided evidence or platform_resources. "
                    "Ordinary concept explanations, mechanisms, equations, and follow-ups may use reliable chemistry "
                    "knowledge when retrieval was skipped or unavailable. Do not claim platform evidence, pages, figures, "
                    "or uploaded resources exist unless they are present in the payload. "
                    "If source_figures_available is true, summarize what the figure evidence shows and include one "
                    "provided Markdown image reference exactly as-is when useful. "
                    f"{CHEM_MATH_OUTPUT_CONTRACT}"
                ),
            },
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
    )
    context.mode = "openai_chat_stream"
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta.content or ""
        if delta:
            yield str(delta)


def _legacy_run_local_agent_always_rag(context: AgentRunContext) -> str:
    tools = approved_tool_registry(context)
    if context.classification["resource_request"]:
        resources = tools["published_resource_lookup"]().get("resources") or []
        if not resources:
            context.add_guardrail("no_fabricated_resource", "state_unavailable", "没有查到 ready + published 的视频或资料。")
            return "当前平台还没有查到已发布且可播放的相关视频或资料。老师后续上传并发布后，这里会显示。"
        titles = [resource.get("title") or resource.get("original_file_name") or "已发布资料" for resource in resources[:3]]
        return "已找到这些已发布资源：" + "；".join(titles)

    curriculum = tools["curriculum_lookup"](context.request.question)
    fixed_sources = context.point_evidence.get("sources", []) if context.point_evidence else []
    if fixed_sources:
        previews = [
            str(item.get("text_preview") or item.get("caption") or "").strip()
            for item in fixed_sources[:3]
            if isinstance(item, dict) and str(item.get("text_preview") or item.get("caption") or "").strip()
        ]
        if previews:
            context.mode = "point_context_local"
            return "根据当前视频点位已绑定的实验教材证据，可以先这样理解：\n" + "\n".join(
                f"{index}. {preview}" for index, preview in enumerate(previews, start=1)
            )
    if not context.classification.get("allow_rag_lookup", True):
        context.add_guardrail("rag_lookup_disabled", "answer_without_rag", "学生侧 AI RAG 接入已关闭。")
        point_titles = [
            point.get("content")
            for point in curriculum.get("knowledge_points", [])
            if point.get("content")
        ][:3]
        if point_titles:
            return "当前未开启 RAG 资料检索。可以先围绕这些相关知识点复习：" + "、".join(point_titles)
        return "当前未开启 RAG 资料检索。可以先回到章节内容复习，再向老师确认需要补充的资料。"
    evidence = tools["rag_search"](context.request.question).get("evidence") or []
    if not evidence:
        context.add_guardrail("missing_evidence", "no_evidence_fallback", "检索不到可支撑回答的已发布课程证据。")
        return "当前平台没有找到足够可靠的已发布课程材料来回答这个问题。你可以换成具体章节、知识点或实验现象再问。"

    point_titles = [
        point.get("content")
        for point in curriculum.get("knowledge_points", [])
        if point.get("content")
    ][:2]
    evidence_text = " ".join(item["text_preview"] for item in evidence[:2])
    answer = "根据已发布课程材料，" + evidence_text[:360]
    if point_titles:
        answer += "\n相关知识点：" + "；".join(point_titles)
    return answer


def _run_local_agent(context: AgentRunContext) -> str:
    tools = approved_tool_registry(context)
    decision = context.retrieval_decision
    if context.classification["resource_request"] or decision.should_call_resource_lookup:
        resources = tools["published_resource_lookup"]().get("resources") or []
        if not resources:
            context.add_guardrail("no_fabricated_resource", "state_unavailable", "No ready + published platform resource matched this request.")
            return "\u5f53\u524d\u5e73\u53f0\u6ca1\u6709\u67e5\u5230\u5df2\u53d1\u5e03\u4e14\u53ef\u7528\u7684\u76f8\u5173\u8d44\u6e90\u3002"
        titles = [resource.get("title") or resource.get("original_file_name") or "\u5df2\u53d1\u5e03\u8d44\u6e90" for resource in resources[:3]]
        return "\u5df2\u627e\u5230\u76f8\u5173\u5e73\u53f0\u8d44\u6e90\uff1a" + "\u3001".join(str(title) for title in titles)

    curriculum = tools["curriculum_lookup"](context.request.question)
    fixed_sources = context.point_evidence.get("sources", []) if context.point_evidence else []
    if decision.should_use_fixed_point_evidence and fixed_sources:
        previews = [
            str(item.get("text_preview") or item.get("caption") or "").strip()
            for item in fixed_sources[:3]
            if isinstance(item, dict) and str(item.get("text_preview") or item.get("caption") or "").strip()
        ]
        if previews:
            context.mode = "point_context_local"
            return "\u6839\u636e\u5f53\u524d\u8bfe\u7a0b\u4e0a\u4e0b\u6587\uff0c\u53ef\u4ee5\u5148\u8fd9\u6837\u7406\u89e3\uff1a\n" + "\n".join(
                f"{index}. {preview}" for index, preview in enumerate(previews, start=1)
            )

    if decision.should_call_rag:
        evidence = tools["rag_search"](context.request.question).get("evidence") or []
        if not _has_usable_evidence(evidence):
            context.add_guardrail("missing_evidence", "no_evidence_fallback", "No usable selected evidence was found.")
            if decision.strict_evidence:
                return "\u5f53\u524d\u6ca1\u6709\u627e\u5230\u8db3\u591f\u53ef\u9760\u7684\u8bfe\u7a0b\u8bc1\u636e\u6765\u652f\u6491\u8fd9\u4e2a\u8bf7\u6c42\u3002"
            return "\u6682\u65f6\u6ca1\u6709\u68c0\u7d22\u5230\u53ef\u7528\u8bc1\u636e\uff0c\u6211\u5148\u7528\u8bfe\u7a0b\u77e5\u8bc6\u5e2e\u4f60\u68b3\u7406\u3002"
        evidence_text = " ".join(str(item.get("text_preview") or item.get("caption") or "") for item in evidence[:2])
        answer = "\u6839\u636e\u5df2\u627e\u5230\u7684\u8bfe\u7a0b\u8bc1\u636e\uff1a" + evidence_text[:360]
        point_titles = [
            point.get("content")
            for point in curriculum.get("knowledge_points", [])
            if point.get("content")
        ][:2]
        if point_titles:
            answer += "\n\u76f8\u5173\u77e5\u8bc6\u70b9\uff1a" + "\u3001".join(str(title) for title in point_titles)
        return answer

    if not context.classification.get("allow_rag_lookup", True):
        context.add_guardrail("rag_lookup_disabled", "answer_without_rag", "Student RAG lookup is disabled for this turn.")
    point_titles = [
        point.get("content")
        for point in curriculum.get("knowledge_points", [])
        if point.get("content")
    ][:3]
    if point_titles:
        return "\u65e0\u9700\u989d\u5916\u68c0\u7d22\uff0c\u53ef\u4ee5\u5148\u56f4\u7ed5\u8fd9\u4e9b\u77e5\u8bc6\u70b9\u7406\u89e3\uff1a" + "\u3001".join(str(title) for title in point_titles)
    return "\u8fd9\u662f\u4e00\u4e2a\u8bfe\u7a0b\u5b66\u4e60\u95ee\u9898\uff0c\u53ef\u4ee5\u5148\u4ece\u6982\u5ff5\u3001\u73b0\u8c61\u548c\u53cd\u5e94\u903b\u8f91\u4e09\u4e2a\u89d2\u5ea6\u68b3\u7406\u3002"


def _apply_output_guardrails(context: AgentRunContext, answer: str) -> str:
    evidence_required = bool(context.classification["requires_evidence"])
    if evidence_required and not context.classification["resource_request"] and not context.sources and "没有找到" not in answer:
        context.add_guardrail("source_grounding", "override_no_evidence", "事实性课程回答缺少来源。")
        answer = "当前平台没有找到足够可靠的已发布课程材料来回答这个问题。你可以换成具体章节、知识点或实验现象再问。"
    if context.classification["resource_request"] and not _has_resource_tool_result(context) and "没有" not in answer:
        context.add_guardrail("no_fabricated_resource", "override_unavailable_resource", "资源请求没有已发布资源支撑。")
        answer = "当前平台还没有查到已发布且可播放的相关视频或资料。老师后续上传并发布后，这里会显示。"
    max_answer_chars = context.policy.max_answer_chars if context.request.max_answer_chars is None else context.request.max_answer_chars
    if max_answer_chars and len(answer) > max_answer_chars:
        context.add_guardrail("mobile_length", "trim", "回答超过小程序端建议长度。")
        answer = answer[:max_answer_chars].rstrip() + "..."
    normalized_answer, raw_latex_leak = normalize_formula_answer(answer)
    if normalized_answer != answer:
        if raw_latex_leak:
            context.add_guardrail("chem_latex_format", "normalize_formula_output", "normalized chemistry/math LaTeX formatting")
        answer = normalized_answer
    return answer


def _persist_agent_log(context: AgentRunContext, response: AgentAskResponse) -> None:
    try:
        context.repositories.agent_logs.append_log(
            {
                "user_id": context.request.user_id,
                "student_id": context.request.student_id,
                "user_role": context.request.user_role,
                "question": context.request.question,
                "classification": response.classification,
                "tool_calls": response.tool_calls,
                "source_refs": [source_to_dict(source) for source in response.sources],
                "guardrail_decisions": response.guardrail_decisions,
                "response_text": response.answer,
                "response_metadata": {
                    "status": "success",
                    "mode": response.mode,
                    "review_required": response.review_required,
                    "policy_version": context.policy.version,
                    "policy_decision": context.policy_decision.as_dict(),
                    "retrieval_decision": context.retrieval_decision.as_dict(),
                    "final_mode": response.mode,
                    "source_count": len(response.sources),
                    "rag_trace": response.rag_trace,
                },
            }
        )
    except Exception:
        pass


def _persist_agent_error_log(context: AgentRunContext, error: Exception) -> None:
    try:
        context.repositories.agent_logs.append_log(
            {
                "user_id": context.request.user_id,
                "student_id": context.request.student_id,
                "user_role": context.request.user_role,
                "question": context.request.question,
                "classification": context.classification,
                "tool_calls": context.tool_calls,
                "source_refs": [source_to_dict(source) for source in context.sources],
                "guardrail_decisions": context.guardrail_decisions,
                "response_text": None,
                "response_metadata": {
                    "status": "error",
                    "mode": context.mode,
                    "policy_version": context.policy.version,
                    "policy_decision": context.policy_decision.as_dict(),
                    "retrieval_decision": context.retrieval_decision.as_dict(),
                    "final_mode": context.mode,
                    "source_count": len(context.sources),
                    "rag_trace": _rag_trace_payload(context),
                    "error_type": type(error).__name__,
                    "error_message": str(error)[:240],
                },
            }
        )
    except Exception:
        pass


def _conversation_history_payload(context: AgentRunContext) -> list[dict[str, str]]:
    return [
        item.model_dump() if hasattr(item, "model_dump") else item.dict()
        for item in context.request.conversation_history[-10:]
    ]


def _agent_user_input(context: AgentRunContext) -> str:
    if not context.request.conversation_history and not context.point_evidence:
        return context.request.question
    return json.dumps(
        {
            "conversation_history": _conversation_history_payload(context),
            "current_question": context.request.question,
            "point_context": context.point_evidence,
        },
        ensure_ascii=False,
    )


def _sdk_enabled(settings: Settings) -> bool:
    return (
        settings.agent_llm_provider in {"openai", "openai_compatible"}
        and bool(settings.agent_llm_api_key or os.getenv("OPENAI_API_KEY"))
        and bool(settings.agent_llm_model)
    )


def _reasoning_summary_enabled(settings: Settings) -> bool:
    if not _sdk_enabled(settings) or not bool(getattr(settings, "agent_reasoning_summary_enabled", False)):
        return False
    mode = str(getattr(settings, "agent_reasoning_summary_mode", "auto") or "auto").lower()
    if mode in {"off", "none", "disabled", "false"}:
        return False
    provider = str(settings.agent_llm_provider or "").lower()
    base_url = str(getattr(settings, "agent_llm_base_url", "") or "").strip()
    if provider == "openai" and not base_url:
        return True
    return mode in {"force", "forced", "responses", "compatible"}


def _reasoning_summary_mode(settings: Settings) -> str:
    mode = str(getattr(settings, "agent_reasoning_summary_mode", "auto") or "auto").lower()
    return mode if mode in {"auto", "concise", "detailed"} else "auto"


def _reasoning_effort(settings: Settings) -> str:
    effort = str(getattr(settings, "agent_reasoning_effort", "low") or "low").lower()
    return effort if effort in {"minimal", "low", "medium", "high"} else "low"


def _openai_client(settings: Settings, *, timeout: float):
    from openai import OpenAI

    return OpenAI(
        api_key=settings.agent_llm_api_key or os.getenv("OPENAI_API_KEY"),
        base_url=settings.agent_llm_base_url or None,
        timeout=timeout,
    )


def _agent_instructions(context: AgentRunContext) -> str:
    return (
        "你是无机化学实验学习平台的受控学习 agent。"
        "只回答课程范围内的问题；事实、实验现象、方程式、资料推荐必须先调用工具取得证据。"
        "不能编造课程材料、视频或资料；没有证据时明确说明平台未找到可靠材料。"
        "遇到测验或考试直接答案请求，只给提示和概念引导。"
        "遇到危险实验操作请求，拒绝提供步骤、剂量和危险条件，转为安全说明。"
        "回答要短，适合手机端。"
        f"\n分类结果：{context.classification}"
        f"\n学生 AI 安全策略版本：{context.policy.version}"
        f"\n学生 AI 安全策略：{context.policy.compact_rail}"
        f"\n本次策略判定：{context.policy_decision.as_dict()}"
        f"\n课程限制提示摘录：{context.policy.source_excerpt}"
        f"\nRetrieval decision: {context.retrieval_decision.as_dict()}"
        "\nUse platform evidence only for citations, source images, textbook/material references, and platform resource claims. "
        "For ordinary explanations, mechanisms, equations, and follow-ups, answer from reliable chemistry knowledge when retrieval was skipped. "
        "Never claim a platform source, page, figure, or uploaded resource exists unless provided in the tool evidence."
        f"{CHEM_MATH_OUTPUT_CONTRACT}"
    )
