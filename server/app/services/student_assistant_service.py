from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, AsyncIterator

from fastapi import HTTPException, status
from sqlalchemy import text

from server.app.agent import run_agent, run_agent_stream
from server.app.auth import AuthUser
from server.app.config import get_settings
from server.app.database import db_session
from server.app.platform_settings import (
    effective_ai_settings,
    get_ai_configuration_response,
    get_learning_behavior_settings,
)
from server.app.schemas import AgentAskRequest
from server.app.student_assistant_schemas import (
    StudentAssistantAskRequest,
    StudentAssistantGeneratedResponse,
)


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=str)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _student_id(user: AuthUser) -> str:
    return str(user.student_id or user.username).strip().upper()


def _ai_enabled() -> tuple[bool, bool]:
    learning_settings = get_learning_behavior_settings()
    ai_config = get_ai_configuration_response(can_edit=False, auto_check=False)
    if not learning_settings.learning_features.ai_assistant_enabled:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="学生端 AI 学习助手入口已关闭")
    if not ai_config.enabled_features.student_ai_assistant:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="学生 AI 学习助手功能已关闭")
    return True, bool(ai_config.enabled_features.rag_access_enabled)


def _effective_settings_ready() -> bool:
    settings = effective_ai_settings(get_settings())
    return bool(
        settings.agent_llm_provider in {"openai", "openai_compatible"}
        and settings.agent_llm_api_key
        and settings.agent_llm_model
    )


def _contextual_question(payload: StudentAssistantAskRequest) -> str:
    context_lines = [
        f"当前页面：{payload.context_title or payload.context_type}",
        f"页面类型：{payload.context_type}",
    ]
    if payload.context_summary:
        context_lines.append(f"页面上下文：{payload.context_summary}")
    return "\n".join([*context_lines, f"学生问题：{payload.question}"])


def _agent_request_for_chat(user: AuthUser, payload: StudentAssistantAskRequest, *, allow_rag_lookup: bool) -> AgentAskRequest:
    return AgentAskRequest(
        student_id=_student_id(user),
        user_id=user.id,
        user_role="student",
        question=_contextual_question(payload),
        chapter_id=payload.chapter_id or None,
        experiment_id=payload.experiment_id or None,
        point_key=payload.point_key or None,
        knowledge_point_ids=payload.knowledge_point_ids,
        allow_progress_lookup=True,
        allow_rag_lookup=allow_rag_lookup,
        conversation_history=payload.conversation_history,
        max_answer_chars=1200,
    )


async def stream_student_assistant_answer(user: AuthUser, payload: StudentAssistantAskRequest) -> AsyncIterator[dict[str, Any]]:
    _, rag_enabled = _ai_enabled()
    request = _agent_request_for_chat(user, payload, allow_rag_lookup=rag_enabled)
    async for item in run_agent_stream(request, settings=effective_ai_settings(get_settings())):
        yield item


def _metadata(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("metadata")
    return value if isinstance(value, dict) else {}


def _load_posttest_session(session: Any, *, student_id: str, session_id: str) -> dict[str, Any]:
    row = (
        session.execute(
            text(
                """
                SELECT *
                FROM student_posttest_sessions
                WHERE id = CAST(:session_id AS uuid)
                  AND student_id = :student_id
                  AND status = 'completed'
                """
            ),
            {"student_id": student_id, "session_id": session_id},
        )
        .mappings()
        .first()
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Posttest report not found")
    return dict(row)


def _load_posttest_experiments(session: Any, experiment_ids: list[str]) -> list[dict[str, Any]]:
    if not experiment_ids:
        return []
    return [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT id, code, title
                FROM formal_experiments
                WHERE id = ANY(:experiment_ids)
                ORDER BY array_position(:experiment_ids, id), display_order, code
                """
            ),
            {"experiment_ids": experiment_ids},
        )
        .mappings()
        .all()
    ]


def _load_posttest_attempts(session: Any, *, student_id: str, session_id: str) -> list[dict[str, Any]]:
    return [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT a.question_id::text AS question_id,
                       a.correct,
                       a.submitted_answer,
                       q.experiment_id,
                       fe.title AS experiment_title,
                       q.question_type,
                       q.stem,
                       q.options,
                       q.answer,
                       q.explanation,
                       q.difficulty,
                       q.related_chapter_ids,
                       q.related_knowledge_point_ids
                FROM experiment_question_attempts a
                JOIN experiment_questions q ON q.id = a.question_id
                JOIN formal_experiments fe ON fe.id = q.experiment_id
                WHERE a.student_id = :student_id
                  AND a.metadata->>'posttest_session_id' = :session_id
                ORDER BY a.created_at, a.id
                """
            ),
            {"student_id": student_id, "session_id": session_id},
        )
        .mappings()
        .all()
    ]


def _experiment_ids(row: dict[str, Any]) -> list[str]:
    return [str(item) for item in _as_list(row.get("experiment_ids")) if str(item).strip()]


def _answer_value(value: Any) -> Any:
    if isinstance(value, dict) and "value" in value:
        return value.get("value")
    return value


def _correct_answer(row: dict[str, Any]) -> Any:
    answer = row.get("answer") if isinstance(row.get("answer"), dict) else {}
    question_type = str(row.get("question_type") or "")
    if question_type in {"single_choice", "true_false"}:
        return answer.get("value")
    if question_type == "fill_blank":
        return answer.get("accepted_answers") or []
    return answer


def _score_line(row: dict[str, Any]) -> str:
    correct_rate = float(row.get("score") or 0)
    return f"{int(row.get('correct_count') or 0)}/{int(row.get('total_count') or 0)} 题，得分 {correct_rate:.1f}"


def _mastery_average(snapshot: dict[str, Any]) -> float | None:
    scores = [
        float(item.get("mastery_score"))
        for item in snapshot.values()
        if isinstance(item, dict) and item.get("mastery_score") is not None
    ]
    if not scores:
        return None
    return round(sum(scores) / len(scores), 2)


def _fallback_summary(row: dict[str, Any], experiments: list[dict[str, Any]], wrong_count: int) -> str:
    names = "、".join(str(item.get("title") or item.get("id")) for item in experiments) or "本轮实验"
    before = _mastery_average(row.get("mastery_before") if isinstance(row.get("mastery_before"), dict) else {})
    after = _mastery_average(row.get("mastery_after") if isinstance(row.get("mastery_after"), dict) else {})
    mastery_part = ""
    if before is not None and after is not None:
        mastery_part = f"相关实验平均掌握度由 {before:.1f} 变为 {after:.1f}。"
    if wrong_count:
        advice = "建议先复盘错题对应的实验现象、反应方程式和判断依据，再进入下一组实验。"
    else:
        advice = "本轮没有错题，可以继续选择下一组实验学习。"
    return f"本轮完成了 {names} 的学习，课后摸底结果为 {_score_line(row)}。{mastery_part}{advice}"


def _fallback_mistake_explanation(attempts: list[dict[str, Any]]) -> str:
    wrong = [item for item in attempts if not item.get("correct")]
    if not wrong:
        return "这次后测没有错题。"
    lines = ["本轮错题可以这样复盘："]
    for index, item in enumerate(wrong, start=1):
        submitted = _answer_value((item.get("submitted_answer") or {}).get("value") if isinstance(item.get("submitted_answer"), dict) else item.get("submitted_answer"))
        lines.append(
            f"{index}. {item.get('stem')} 你的作答是 {submitted or '未作答'}，参考项是 {_correct_answer(item)}。"
            f"{' ' + str(item.get('explanation')) if item.get('explanation') else ''}"
        )
    lines.append("下一步先回到对应实验现象，再把现象、方程式和元素性质判断连起来。")
    return "\n".join(lines)


def _posttest_context(session_row: dict[str, Any], experiments: list[dict[str, Any]], attempts: list[dict[str, Any]]) -> dict[str, Any]:
    wrong = [item for item in attempts if not item.get("correct")]
    return {
        "score": _score_line(session_row),
        "experiments": [{"id": item.get("id"), "code": item.get("code"), "title": item.get("title")} for item in experiments],
        "wrong_count": len(wrong),
        "mastery_before_average": _mastery_average(session_row.get("mastery_before") if isinstance(session_row.get("mastery_before"), dict) else {}),
        "mastery_after_average": _mastery_average(session_row.get("mastery_after") if isinstance(session_row.get("mastery_after"), dict) else {}),
        "wrong_questions": [
            {
                "stem": item.get("stem"),
                "student_answer": _answer_value((item.get("submitted_answer") or {}).get("value") if isinstance(item.get("submitted_answer"), dict) else item.get("submitted_answer")),
                "correct_answer": _correct_answer(item),
                "explanation": item.get("explanation"),
                "experiment_title": item.get("experiment_title"),
                "related_knowledge_point_ids": _as_list(item.get("related_knowledge_point_ids")),
            }
            for item in wrong
        ],
    }


async def _generate_with_agent(
    *,
    user: AuthUser,
    question: str,
    context: dict[str, Any],
    attempts: list[dict[str, Any]],
    allow_rag_lookup: bool,
    fallback_text: str,
) -> tuple[str, str, str]:
    if not _effective_settings_ready():
        return fallback_text, "fallback", "local_fallback"
    chapter_ids = [
        str(chapter_id)
        for item in attempts
        for chapter_id in _as_list(item.get("related_chapter_ids"))
        if str(chapter_id).strip()
    ]
    kp_ids = sorted(
        {
            str(kp_id)
            for item in attempts
            for kp_id in _as_list(item.get("related_knowledge_point_ids"))
            if str(kp_id).strip()
        }
    )
    experiment_id = str(attempts[0].get("experiment_id")) if attempts else None
    request = AgentAskRequest(
        student_id=_student_id(user),
        user_id=user.id,
        user_role="student",
        question=json.dumps({"task": question, "posttest_context": context}, ensure_ascii=False),
        chapter_id=chapter_ids[0] if chapter_ids else None,
        experiment_id=experiment_id,
        knowledge_point_ids=kp_ids,
        allow_progress_lookup=True,
        allow_rag_lookup=allow_rag_lookup,
        assessment_review=True,
        max_answer_chars=1600,
    )
    try:
        response = await run_agent(request, settings=effective_ai_settings(get_settings()))
    except Exception:
        return fallback_text, "fallback", "agent_error_fallback"
    if not response.answer or response.mode in {"guardrail_refusal", "guardrail_hint"}:
        return fallback_text, "fallback", response.mode or "agent_guardrail_fallback"
    return response.answer, "ai", response.mode


def _cached_response(cached: Any) -> StudentAssistantGeneratedResponse | None:
    if not isinstance(cached, dict) or not cached.get("text"):
        return None
    return StudentAssistantGeneratedResponse(
        text=str(cached["text"]),
        source="ai" if cached.get("source") == "ai" else "fallback",
        mode=str(cached.get("mode") or "cached"),
        cached=True,
    )


def _store_cache(session: Any, row: dict[str, Any], key: str, *, text_value: str, source: str, mode: str) -> None:
    metadata = _metadata(row)
    metadata[key] = {
        "text": text_value,
        "source": source,
        "mode": mode,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    session.execute(
        text(
            """
            UPDATE student_posttest_sessions
            SET metadata = CAST(:metadata AS jsonb),
                updated_at = now()
            WHERE id = CAST(:id AS uuid)
            """
        ),
        {"id": str(row["id"]), "metadata": _json(metadata)},
    )


async def generate_posttest_ai_summary(user: AuthUser, session_id: str) -> StudentAssistantGeneratedResponse:
    _, rag_enabled = _ai_enabled()
    student_id = _student_id(user)
    with db_session() as session:
        row = _load_posttest_session(session, student_id=student_id, session_id=session_id)
        cached = _cached_response(_metadata(row).get("ai_summary"))
        if cached:
            return cached
        experiments = _load_posttest_experiments(session, _experiment_ids(row))
        attempts = _load_posttest_attempts(session, student_id=student_id, session_id=session_id)
        context = _posttest_context(row, experiments, attempts)
        fallback = _fallback_summary(row, experiments, int(context["wrong_count"]))
    text_value, source, mode = await _generate_with_agent(
        user=user,
        question="请为学生生成一段课后学习总结，包含本轮学习内容、后测表现、实验掌握度变化和下一步建议。不要超过 220 字。只输出纯文本，不要使用 Markdown、标题符号、LaTeX 或项目列表。",
        context=context,
        attempts=attempts,
        allow_rag_lookup=rag_enabled,
        fallback_text=fallback,
    )
    with db_session() as session:
        row = _load_posttest_session(session, student_id=student_id, session_id=session_id)
        _store_cache(session, row, "ai_summary", text_value=text_value, source=source, mode=mode)
    return StudentAssistantGeneratedResponse(text=text_value, source=source, mode=mode, cached=False)


async def generate_posttest_mistake_explanation(user: AuthUser, session_id: str) -> StudentAssistantGeneratedResponse:
    _, rag_enabled = _ai_enabled()
    student_id = _student_id(user)
    with db_session() as session:
        row = _load_posttest_session(session, student_id=student_id, session_id=session_id)
        cached = _cached_response(_metadata(row).get("ai_mistake_explanation"))
        if cached:
            return cached
        experiments = _load_posttest_experiments(session, _experiment_ids(row))
        attempts = _load_posttest_attempts(session, student_id=student_id, session_id=session_id)
        wrong = [item for item in attempts if not item.get("correct")]
        if not wrong:
            return StudentAssistantGeneratedResponse(text="这次后测没有错题。", source="fallback", mode="no_wrong_answers")
        context = _posttest_context(row, experiments, attempts)
        fallback = _fallback_mistake_explanation(attempts)
    text_value, source, mode = await _generate_with_agent(
        user=user,
        question="请解释学生已提交后测中的全部错题。先概括共同错因，再按题号说明正确思路和复习抓手。可以引用题目给出的参考项，但不要用于未提交测验作答。",
        context=context,
        attempts=attempts,
        allow_rag_lookup=rag_enabled,
        fallback_text=fallback,
    )
    with db_session() as session:
        row = _load_posttest_session(session, student_id=student_id, session_id=session_id)
        _store_cache(session, row, "ai_mistake_explanation", text_value=text_value, source=source, mode=mode)
    return StudentAssistantGeneratedResponse(text=text_value, source=source, mode=mode, cached=False)
