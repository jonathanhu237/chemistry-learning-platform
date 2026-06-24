from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from server.app.infrastructure.settings import Settings
from server.app.repositories import RepositoryProvider
from server.app.schemas import AgentAskRequest, AgentAskResponse
from server.app.domains.assistant.evidence_shaping import rag_trace_payload
from server.app.domains.assistant.output_guardrails import count_result, preview_result


RETRIEVAL_DECISION_MODES = {"skip", "fixed_evidence", "dynamic_rag", "resource_lookup", "strict_evidence"}
RETRIEVAL_DECISION_SOURCES = {"llm_policy", "hard_rule", "local_fallback", "feature_disabled"}


@dataclass
class StudentAIRetrievalDecision:
    mode: str = "skip"
    source: str = "local_fallback"
    reason: str = ""
    student_reason: str = ""
    confidence: float | None = None
    strict_evidence: bool = False
    allowed_tools: tuple[str, ...] = field(default_factory=tuple)
    should_call_rag: bool = False
    should_call_resource_lookup: bool = False
    should_use_fixed_point_evidence: bool = False
    override_reason: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "source": self.source,
            "reason": self.reason,
            "student_reason": self.student_reason,
            "confidence": self.confidence,
            "strict_evidence": self.strict_evidence,
            "allowed_tools": list(self.allowed_tools),
            "should_call_rag": self.should_call_rag,
            "should_call_resource_lookup": self.should_call_resource_lookup,
            "should_use_fixed_point_evidence": self.should_use_fixed_point_evidence,
            "override_reason": self.override_reason,
        }


@dataclass
class StudentAIPolicyDecision:
    mode: str = "normal_answer"
    reason: str = ""
    evidence_required: bool = False
    student_guidance: str = ""
    allowed_tools: tuple[str, ...] = field(default_factory=tuple)
    retrieval_mode: str = ""
    retrieval_reason: str = ""
    retrieval_confidence: float | None = None
    strict_evidence: bool = False
    valid: bool = True
    raw: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "reason": self.reason,
            "evidence_required": self.evidence_required,
            "student_guidance": self.student_guidance,
            "allowed_tools": list(self.allowed_tools),
            "retrieval_mode": self.retrieval_mode,
            "retrieval_reason": self.retrieval_reason,
            "retrieval_confidence": self.retrieval_confidence,
            "strict_evidence": self.strict_evidence,
            "valid": self.valid,
        }


@dataclass
class AgentRunContext:
    request: AgentAskRequest
    repositories: RepositoryProvider
    policy: Any
    classification: dict[str, Any]
    settings: Settings | None = None
    policy_decision: StudentAIPolicyDecision = field(default_factory=StudentAIPolicyDecision)
    retrieval_decision: StudentAIRetrievalDecision = field(default_factory=StudentAIRetrievalDecision)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    sources: list[Any] = field(default_factory=list)
    rag_traces: list[dict[str, Any]] = field(default_factory=list)
    point_evidence: dict[str, Any] = field(default_factory=dict)
    guardrail_decisions: list[dict[str, Any]] = field(default_factory=list)
    mode: str = "local"

    def record_tool(self, name: str, arguments: dict[str, Any], result: Any) -> None:
        self.tool_calls.append(
            {
                "name": name,
                "arguments": arguments,
                "result_count": count_result(result),
                "result_preview": preview_result(result),
            }
        )

    def add_guardrail(self, code: str, action: str, reason: str) -> None:
        self.guardrail_decisions.append({"code": code, "action": action, "reason": reason})


def create_agent_context(
    *,
    request: AgentAskRequest,
    repositories: RepositoryProvider,
    policy: Any,
    classification: dict[str, Any],
    settings: Settings | None,
) -> AgentRunContext:
    return AgentRunContext(
        request=request,
        repositories=repositories,
        policy=policy,
        classification=classification,
        settings=settings,
    )


def build_agent_response(context: AgentRunContext, answer: str) -> AgentAskResponse:
    classification = dict(context.classification)
    retrieval_decision = context.retrieval_decision.as_dict()
    classification.update(
        {
            "retrieval_decision": retrieval_decision,
            "retrieval_mode": retrieval_decision["mode"],
            "retrieval_decision_source": retrieval_decision["source"],
            "retrieval_strict_evidence": retrieval_decision["strict_evidence"],
            "retrieval_should_call_rag": retrieval_decision["should_call_rag"],
            "retrieval_should_call_resource_lookup": retrieval_decision["should_call_resource_lookup"],
            "retrieval_should_use_fixed_point_evidence": retrieval_decision["should_use_fixed_point_evidence"],
            "retrieval_override_reason": retrieval_decision["override_reason"],
        }
    )
    return AgentAskResponse(
        answer=answer,
        sources=context.sources,
        mode=context.mode,
        classification=classification,
        tool_calls=context.tool_calls,
        guardrail_decisions=context.guardrail_decisions,
        rag_trace=rag_trace_payload(context),
        review_required=True,
    )


def dump_agent_response(response: AgentAskResponse) -> dict[str, Any]:
    if hasattr(response, "model_dump"):
        return response.model_dump()
    return response.dict()


def chunk_stream_text(text: str, chunk_size: int = 18) -> list[str]:
    if not text:
        return []
    return [text[index : index + chunk_size] for index in range(0, len(text), chunk_size)]
