from __future__ import annotations

from typing import Any

from server.app.domains.assistant import orchestrator as _orchestrator
from server.app.domains.assistant.runtime_facade import AgentRuntime, AgentRuntimeOptions, run_agent, run_agent_stream

# Compatibility exports for existing tests and callers while runtime consumers migrate
# to the facade/adapters.
AgentPolicy = _orchestrator.AgentPolicy
AgentRunContext = _orchestrator.AgentRunContext
StudentAIPolicyDecision = _orchestrator.StudentAIPolicyDecision
StudentAIRetrievalDecision = _orchestrator.StudentAIRetrievalDecision
AgentStreamCancelled = _orchestrator.AgentStreamCancelled
classify_agent_request = _orchestrator.classify_agent_request
load_agent_policy = _orchestrator.load_agent_policy
_apply_policy_decision_to_classification = _orchestrator._apply_policy_decision_to_classification
_local_policy_decision_from_classification = _orchestrator._local_policy_decision_from_classification
_normalize_assistant_formula_output = _orchestrator._normalize_assistant_formula_output
_sanitize_visible_thinking_message = _orchestrator._sanitize_visible_thinking_message


def __getattr__(name: str) -> Any:
    return getattr(_orchestrator, name)
