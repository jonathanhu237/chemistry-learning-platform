from __future__ import annotations

from typing import Any

from server.app.schemas import AgentAskRequest
from server.app.student_assistant_schemas import StudentAssistantAskRequest


def student_id_for_runtime(user: Any) -> str:
    return str(user.student_id or user.username).strip().upper()


def contextual_student_question(payload: StudentAssistantAskRequest) -> str:
    context_lines = [
        f"当前页面：{payload.context_title or payload.context_type}",
        f"页面类型：{payload.context_type}",
    ]
    if payload.context_summary:
        context_lines.append(f"页面上下文：{payload.context_summary}")
    return "\n".join([*context_lines, f"学生问题：{payload.question}"])


def build_student_agent_request(
    user: Any,
    payload: StudentAssistantAskRequest,
    *,
    allow_rag_lookup: bool,
) -> AgentAskRequest:
    return AgentAskRequest(
        student_id=student_id_for_runtime(user),
        user_id=user.id,
        user_role="student",
        question=contextual_student_question(payload),
        chapter_id=payload.chapter_id or None,
        experiment_id=payload.experiment_id or None,
        point_key=payload.point_key or None,
        point_node_id=payload.point_node_id or None,
        source_node_id=payload.source_node_id or None,
        catalog_path=payload.catalog_path,
        knowledge_point_ids=payload.knowledge_point_ids,
        allow_progress_lookup=True,
        allow_rag_lookup=allow_rag_lookup,
        conversation_history=payload.conversation_history,
        max_answer_chars=0,
    )
