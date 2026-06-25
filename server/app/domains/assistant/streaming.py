from __future__ import annotations

import inspect
import re
from typing import Any, Awaitable, Callable


VISIBLE_THINKING_MAX_CHARS = 40
StreamCancelCheck = Callable[[], bool | Awaitable[bool]]
_THINKING_SOURCE_VALUES = {"reasoning_summary", "agent_trace"}


class AgentStreamCancelled(Exception):
    """Internal control flow for client-abandoned assistant streams."""

    def __init__(self, stage: str) -> None:
        super().__init__(stage)
        self.stage = stage


async def stream_cancelled(should_cancel: StreamCancelCheck | None) -> bool:
    if should_cancel is None:
        return False
    result = should_cancel()
    if inspect.isawaitable(result):
        return bool(await result)
    return bool(result)


async def await_tool_result(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


def first_safe_thinking_segment(text: str) -> str:
    normalized = " ".join(text.strip().split())
    if not normalized:
        return ""
    for separator in ("。", "；", ";", ".", "\n"):
        if separator in normalized:
            normalized = normalized.split(separator, 1)[0]
            break
    return normalized[:VISIBLE_THINKING_MAX_CHARS]


def sanitize_visible_thinking_message(message: Any) -> str:
    raw = str(message or "").strip()
    if not raw:
        return ""
    lowered = raw.lower()
    blocked_terms = (
        "chain-of-thought",
        "hidden reasoning",
        "system prompt",
        "developer message",
        "traceback",
        "exception",
        "raw diagnostics",
        "policy_decision",
        "retrieval_decision",
        "rag_trace",
        "tool_calls",
        "guardrail",
        "chunk_id",
        "source_refs",
        "stack",
        "debug",
        "内部",
        "系统提示",
        "开发者",
        "调试",
    )
    if any(term in lowered for term in blocked_terms):
        return ""
    if raw.startswith("{") or raw.startswith("["):
        return ""
    if re.search(r"\b[A-Za-z_]+Error\b", raw):
        return ""
    return first_safe_thinking_segment(raw)


def thinking_event(
    *,
    source: str,
    message: Any,
    phase: str | None = None,
    sequence: int | None = None,
) -> dict[str, Any] | None:
    if source not in _THINKING_SOURCE_VALUES:
        return None
    safe_message = sanitize_visible_thinking_message(message)
    if not safe_message:
        return None
    event: dict[str, Any] = {"event": "thinking", "source": source, "message": safe_message}
    if phase:
        event["phase"] = phase
    if sequence is not None:
        event["sequence"] = sequence
    return event


def agent_trace_event(key: str, *, sequence: int | None = None) -> dict[str, Any] | None:
    trace_messages = {
        "policy": ("policy", "判断问题类型"),
        "retrieval_decision": ("retrieval_decision", "判断是否需要课程证据"),
        "context": ("context", "整理当前学习上下文"),
        "fixed_evidence": ("fixed_evidence", "读取当前实验点位资料"),
        "retrieval": ("retrieval", "检索课程证据"),
        "retrieval_skip": ("retrieval_skip", "无需额外检索"),
        "evidence_quality": ("evidence_quality", "筛选可用证据"),
        "generation": ("generation", "组织回答"),
        "fallback": ("fallback", "切换本地兜底"),
    }
    phase, message = trace_messages.get(key, (key, key))
    return thinking_event(source="agent_trace", message=message, phase=phase, sequence=sequence)


def response_event_type(event: Any) -> str:
    if isinstance(event, dict):
        return str(event.get("type") or "")
    return str(getattr(event, "type", "") or "")


def response_event_text(event: Any, key: str) -> str:
    if isinstance(event, dict):
        return str(event.get(key) or "")
    return str(getattr(event, key, "") or "")


def response_event_sequence(event: Any) -> int | None:
    if isinstance(event, dict):
        value = event.get("sequence_number")
    else:
        value = getattr(event, "sequence_number", None)
    return value if isinstance(value, int) else None
