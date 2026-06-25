from __future__ import annotations

from server.app.domains.assistant.evidence_shaping import rag_trace_payload
from server.app.domains.assistant.rag_sources import source_to_dict
from server.app.domains.assistant.runtime import AgentRunContext
from server.app.schemas import AgentAskResponse


def persist_agent_log(context: AgentRunContext, response: AgentAskResponse) -> None:
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


def persist_agent_error_log(context: AgentRunContext, error: Exception) -> None:
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
                    "rag_trace": rag_trace_payload(context),
                    "error_type": type(error).__name__,
                    "error_message": str(error)[:240],
                },
            }
        )
    except Exception:
        pass
