from __future__ import annotations

import re
from typing import Any

from server.app.domains.assistant.policy import _is_platform_resource_request
from server.app.domains.assistant.runtime import (
    AgentRunContext,
    RETRIEVAL_DECISION_MODES,
    RETRIEVAL_DECISION_SOURCES,
    StudentAIPolicyDecision,
    StudentAIRetrievalDecision,
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
