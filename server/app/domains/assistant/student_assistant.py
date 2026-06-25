from __future__ import annotations

import json
import os
import re
import inspect
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Awaitable, Callable

from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from sqlalchemy import text

from server.app.domains.assistant.adapters.student import (
    build_student_agent_request,
    contextual_student_question,
    student_id_for_runtime,
)
from server.app.domains.assistant.adapters.posttest import run_posttest_agent
from server.app.domains.assistant.runtime_facade import run_agent_stream
from server.app.infrastructure.settings import get_settings
from server.app.infrastructure.database import db_session
from server.app.domains.platform.settings import (
    effective_ai_settings,
    get_ai_configuration_response,
    get_learning_behavior_settings,
)

StreamCancelCheck = Callable[[], bool | Awaitable[bool]]


async def _stream_cancelled(should_cancel: StreamCancelCheck | None) -> bool:
    if should_cancel is None:
        return False
    result = should_cancel()
    if inspect.isawaitable(result):
        return bool(await result)
    return bool(result)
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


def _student_id(user: Any) -> str:
    return student_id_for_runtime(user)


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


_FOLLOWUP_MIN_VISIBLE_CHARS = 8
_FOLLOWUP_MAX_VISIBLE_CHARS = 24
_FOLLOWUP_MAX_COUNT = 5
_TITLE_MIN_VISIBLE_CHARS = 4
_TITLE_MAX_VISIBLE_CHARS = 18
_STUDENT_FINAL_RESPONSE_KEYS = {
    "answer",
    "mode",
    "review_required",
    "sources",
    "source_count",
    "text",
}
_MODEL_SUCCESS_MODES = {
    "openai_chat",
    "openai_chat_stream",
    "openai_chat_fallback",
    "source_asset_evidence",
}
_MODEL_SKIP_MODES = {
    "local",
    "guardrail_refusal",
    "guardrail_hint",
    "assessment_hint",
    "needs_platform_evidence",
}
_FOLLOWUP_SYSTEM_PROMPT = (
    "You generate next-turn chips for Atom, a student inorganic chemistry learning assistant. "
    "The chips are shown to the student and, when tapped, are sent verbatim as the student's next message to Atom. "
    "Return JSON only: an array of 3 to 5 concise Chinese questions written in the student's voice. "
    "Each item must be 8 to 24 visible characters. "
    "Use direct askable wording, for example 'Ellingham图怎么判读？' or 'Frost图怎么分析？'. "
    "Do not write Atom's offer/choice wording such as '想了解...？', '需要解析...？', '要不要...？', '是否需要...？', or '我来...'. "
    "Base the questions only on the current student context, latest question, completed answer, and recent history. "
    "Do not include markdown, numbering, explanations, diagnostics, RAG/chunk/internal terms, unsafe private experiment operations, "
    "direct live-assessment answers, or off-course topics."
)
_DIAGNOSTIC_PROMPT_TERMS = (
    "rag",
    "chunk",
    "trace",
    "json",
    "token",
    "debug",
    "log",
    "guardrail",
    "policy",
    "\u8c03\u8bd5",
    "\u8bca\u65ad",
    "\u65e5\u5fd7",
    "\u540e\u53f0",
    "\u7ba1\u7406\u5458",
    "\u6559\u5e08\u7aef",
)
_UNSAFE_PROMPT_TERMS = (
    "home lab",
    "at home",
    "private experiment",
    "dose",
    "\u5728\u5bb6",
    "\u79c1\u4e0b",
    "\u79c1\u81ea",
    "\u5177\u4f53\u6b65\u9aa4",
    "\u64cd\u4f5c\u6b65\u9aa4",
    "\u52a0\u70ed\u591a\u4e45",
    "\u600e\u4e48\u5236\u5907\u6c2f\u6c14",
    "\u7206\u70b8",
)
_ASSESSMENT_ANSWER_PROMPT_TERMS = (
    "answer choice",
    "correct answer",
    "tell me the answer",
    "\u6b63\u786e\u7b54\u6848",
    "\u7b54\u6848\u9009",
    "\u9009\u54ea\u4e2a",
    "\u586b\u4ec0\u4e48",
    "\u76f4\u63a5\u544a\u8bc9\u7b54\u6848",
    "\u6d4b\u8bc4\u7b54\u6848",
    "\u8003\u8bd5\u7b54\u6848",
)
_OFF_SCOPE_PROMPT_TERMS = (
    "stock",
    "movie",
    "game",
    "\u80a1\u7968",
    "\u7406\u8d22",
    "\u7535\u5f71",
    "\u604b\u7231",
    "\u661f\u5ea7",
)
_ASSISTANT_OFFER_PROMPT_PATTERNS = tuple(
    re.compile(pattern)
    for pattern in (
        r"^(?:想了解|想知道|想看|还想了解|继续了解)",
        r"^需要(?:解析|分析|讲解|说明|了解|复习|我|帮你)",
        r"^(?:是否需要|要不要|要继续|还需要)",
        r"^(?:我来|让我|可以继续|可以再)",
    )
)
_TITLE_REJECT_TERMS = (
    "markdown",
    "json",
    "atom",
    "assistant",
    "prompt",
    "conversation",
    "history",
    "admin",
    "teacher",
    *_DIAGNOSTIC_PROMPT_TERMS,
    *_UNSAFE_PROMPT_TERMS,
    *_ASSESSMENT_ANSWER_PROMPT_TERMS,
    *_OFF_SCOPE_PROMPT_TERMS,
    "\u6211\u6b63\u5728\u5b66\u4e60",
    "\u8bf7\u89e3\u91ca",
    "\u8bf7\u7528",
    "\u73b0\u4ee3",
    "\u56de\u7b54",
    "\u8fd9\u4e2a\u5185\u5bb9\u4e3b\u8981",
    "\u9009\u62e9\u5b9e\u9a8c",
    "\u9009\u62e9\u70b9\u4f4d",
    "\u5b66\u751f\u7aef",
    "\u6559\u5e08",
    "\u540e\u53f0",
)

_FOLLOWUP_SYSTEM_PROMPT = (
    "You generate final UI metadata for Atom, a student inorganic chemistry learning assistant. "
    "Return JSON only: {\"suggested_prompts\":[...],\"conversation_title\":\"...\"}. "
    "suggested_prompts must be 3 to 5 concise Chinese questions written in the student's voice; "
    "each prompt must be 8 to 24 visible characters and can be sent verbatim as the student's next message. "
    "If request_conversation_title is true, also return one concise Chinese learning-topic title, 4 to 18 visible characters. "
    "If request_conversation_title is false, omit conversation_title or set it to null. "
    "Preserve meaningful chemistry formulas such as KI, Cl2, and CCl4. "
    "Use direct askable prompt wording. "
    "Do not write Atom's offer/choice wording. "
    "Base all metadata only on the current student context, latest question, completed answer, and recent history. "
    "Do not include markdown, numbering, explanations, diagnostics, RAG/chunk/internal terms, unsafe private experiment operations, "
    "direct live-assessment answers, teacher/admin terms, or off-course topics."
)


def _followup_model_ready(settings: Any) -> bool:
    return bool(
        settings.agent_llm_provider in {"openai", "openai_compatible"}
        and (settings.agent_llm_api_key or os.getenv("OPENAI_API_KEY"))
        and settings.agent_llm_model
    )


def _conversation_history_for_followups(payload: StudentAssistantAskRequest) -> list[dict[str, str]]:
    history: list[dict[str, str]] = []
    for item in payload.conversation_history[-6:]:
        data = item.model_dump() if hasattr(item, "model_dump") else item.dict()
        history.append(
            {
                "role": str(data.get("role") or ""),
                "content": " ".join(str(data.get("content") or "").split())[:700],
            }
        )
    return history


def _should_request_conversation_title(payload: StudentAssistantAskRequest) -> bool:
    return not payload.conversation_history


def _followup_generation_payload(payload: StudentAssistantAskRequest, answer: str) -> dict[str, Any]:
    return {
        "context_type": payload.context_type,
        "context_title": payload.context_title,
        "context_summary": payload.context_summary,
        "chapter_id": payload.chapter_id,
        "experiment_id": payload.experiment_id,
        "point_key": payload.point_key,
        "point_node_id": payload.point_node_id,
        "source_node_id": payload.source_node_id,
        "catalog_path": payload.catalog_path,
        "knowledge_point_ids": payload.knowledge_point_ids,
        "latest_student_question": payload.question,
        "completed_answer": answer[:2200],
        "recent_conversation_history": _conversation_history_for_followups(payload),
        "request_conversation_title": _should_request_conversation_title(payload),
    }


def _json_payload_from_model_text(text: str) -> Any:
    content = text.strip()
    if content.startswith("```"):
        lines = [line for line in content.splitlines() if not line.strip().startswith("```")]
        content = "\n".join(lines).strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        for pattern in (r"\{[\s\S]*\}", r"\[[\s\S]*\]"):
            match = re.search(pattern, content)
            if not match:
                continue
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                continue
        return []


def _parse_followup_metadata_payload(value: Any) -> dict[str, Any]:
    payload = _json_payload_from_model_text(value) if isinstance(value, str) else value
    if isinstance(payload, dict):
        return payload
    if isinstance(payload, list):
        return {"suggested_prompts": payload}
    return {}


def _parse_suggested_prompt_payload(value: Any) -> list[Any]:
    payload = value
    if isinstance(value, str):
        payload = _json_payload_from_model_text(value)
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("suggested_prompts", "suggestions", "followups", "follow_up_questions"):
            items = payload.get(key)
            if isinstance(items, list):
                return items
    return []


def _visible_char_count(text: str) -> int:
    return len(re.sub(r"\s+", "", text))


def _prompt_has_guardrail_issue(text: str) -> bool:
    normalized = re.sub(r"\s+", " ", text).casefold()
    compact = re.sub(r"\s+", "", text).casefold()
    for term in (
        *_DIAGNOSTIC_PROMPT_TERMS,
        *_UNSAFE_PROMPT_TERMS,
        *_ASSESSMENT_ANSWER_PROMPT_TERMS,
        *_OFF_SCOPE_PROMPT_TERMS,
    ):
        term_text = str(term).casefold()
        if term_text and (term_text in normalized or term_text in compact):
            return True
    return False


def _prompt_uses_assistant_offer_voice(text: str) -> bool:
    compact = re.sub(r"\s+", "", text)
    return any(pattern.search(compact) for pattern in _ASSISTANT_OFFER_PROMPT_PATTERNS)


def _sanitize_followup_prompts(value: Any) -> list[str]:
    raw_items = _parse_suggested_prompt_payload(value)
    suggestions: list[str] = []
    seen: set[str] = set()
    for raw in raw_items:
        if not isinstance(raw, str):
            continue
        text_value = re.sub(r"\s+", " ", raw).strip()
        text_value = re.sub(r"^(?:[-*]|\d+[.)])\s*", "", text_value).strip()
        if not text_value:
            continue
        visible_length = _visible_char_count(text_value)
        if visible_length < _FOLLOWUP_MIN_VISIBLE_CHARS or visible_length > _FOLLOWUP_MAX_VISIBLE_CHARS:
            continue
        dedupe_key = re.sub(r"\s+", "", text_value).casefold()
        if dedupe_key in seen:
            continue
        if _prompt_has_guardrail_issue(text_value):
            continue
        if _prompt_uses_assistant_offer_voice(text_value):
            continue
        seen.add(dedupe_key)
        suggestions.append(text_value)
        if len(suggestions) >= _FOLLOWUP_MAX_COUNT:
            break
    return suggestions


def _title_has_rejected_term(text: str) -> bool:
    normalized = re.sub(r"\s+", " ", text).casefold()
    compact = re.sub(r"\s+", "", text).casefold()
    for term in _TITLE_REJECT_TERMS:
        term_text = str(term).casefold()
        if term_text and (term_text in normalized or term_text in compact):
            return True
    return False


def _sanitize_conversation_title(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    raw = value.strip()
    if not raw or "\n" in raw or "\r" in raw:
        return ""
    if raw.startswith("```") or re.search(r"[{}\[\]<>`#*|]", raw):
        return ""
    text_value = re.sub(r"\s+", " ", raw).strip()
    text_value = re.sub(r"^(?:[-*]|\d+[.)])\s*", "", text_value).strip()
    text_value = text_value.strip(" \"'`_*#-:：,，.。;；!?！？()（）[]【】{}<>《》")
    if not text_value:
        return ""
    visible_length = _visible_char_count(text_value)
    if visible_length < _TITLE_MIN_VISIBLE_CHARS or visible_length > _TITLE_MAX_VISIBLE_CHARS:
        return ""
    if _title_has_rejected_term(text_value):
        return ""
    if _prompt_uses_assistant_offer_voice(text_value):
        return ""
    return text_value


def _sanitize_followup_metadata(value: Any, *, include_title: bool) -> dict[str, Any]:
    payload = _parse_followup_metadata_payload(value)
    metadata: dict[str, Any] = {
        "suggested_prompts": _sanitize_followup_prompts(payload),
    }
    if include_title:
        title = _sanitize_conversation_title(
            payload.get("conversation_title")
            or payload.get("title")
            or payload.get("chat_title")
            or payload.get("history_title")
        )
        if title:
            metadata["conversation_title"] = title
    return metadata


def _should_generate_followups(response: dict[str, Any], answer: str) -> bool:
    if not answer.strip():
        return False
    mode = str(response.get("mode") or "").strip()
    if not mode:
        return True
    if mode in _MODEL_SKIP_MODES:
        return False
    return mode in _MODEL_SUCCESS_MODES or mode.startswith("openai")


async def _generate_followup_metadata(
    payload: StudentAssistantAskRequest,
    answer: str,
    settings: Any,
) -> dict[str, Any]:
    if not _followup_model_ready(settings):
        return {"suggested_prompts": []}

    from openai import AsyncOpenAI

    include_title = _should_request_conversation_title(payload)
    client = AsyncOpenAI(
        api_key=settings.agent_llm_api_key or os.getenv("OPENAI_API_KEY"),
        base_url=settings.agent_llm_base_url or None,
        timeout=10.0,
    )
    response = await client.chat.completions.create(
        model=settings.agent_llm_model,
        temperature=0.35,
        max_tokens=320,
        messages=[
            {
                "role": "system",
                "content": _FOLLOWUP_SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": json.dumps(_followup_generation_payload(payload, answer), ensure_ascii=False),
            },
        ],
    )
    content = response.choices[0].message.content if response.choices else ""
    return _sanitize_followup_metadata(content or "", include_title=include_title)


async def _generate_followup_prompts(
    payload: StudentAssistantAskRequest,
    answer: str,
    settings: Any,
) -> list[str]:
    metadata = await _generate_followup_metadata(payload, answer, settings)
    return _sanitize_followup_prompts(metadata)


def _answer_from_final_response(response: dict[str, Any]) -> str:
    value = response.get("answer")
    if value is None:
        value = response.get("text")
    return str(value or "")


async def _student_final_response_with_followups(
    response: dict[str, Any],
    payload: StudentAssistantAskRequest,
    settings: Any,
    *,
    should_cancel: StreamCancelCheck | None = None,
) -> dict[str, Any]:
    next_response = {key: response[key] for key in _STUDENT_FINAL_RESPONSE_KEYS if key in response}
    answer = _answer_from_final_response(next_response)
    metadata: dict[str, Any] = {"suggested_prompts": []}
    if _should_generate_followups(next_response, answer) and not await _stream_cancelled(should_cancel):
        try:
            raw_metadata = await _generate_followup_metadata(payload, answer, settings)
            if await _stream_cancelled(should_cancel):
                return next_response
            metadata = raw_metadata if isinstance(raw_metadata, dict) else {"suggested_prompts": raw_metadata}
        except Exception:
            metadata = {"suggested_prompts": []}
    next_response["suggested_prompts"] = _sanitize_followup_prompts(metadata)
    title = _sanitize_conversation_title(metadata.get("conversation_title")) if _should_request_conversation_title(payload) else ""
    if title:
        next_response["conversation_title"] = title
    return next_response


def _contextual_question(payload: StudentAssistantAskRequest) -> str:
    return contextual_student_question(payload)


def _agent_request_for_chat(user: Any, payload: StudentAssistantAskRequest, *, allow_rag_lookup: bool) -> AgentAskRequest:
    return build_student_agent_request(user, payload, allow_rag_lookup=allow_rag_lookup)


async def stream_student_assistant_answer(
    user: Any,
    payload: StudentAssistantAskRequest,
    *,
    should_cancel: StreamCancelCheck | None = None,
) -> AsyncIterator[dict[str, Any]]:
    _, rag_enabled = _ai_enabled()
    settings = effective_ai_settings(get_settings())
    request = _agent_request_for_chat(user, payload, allow_rag_lookup=rag_enabled)
    async for item in run_agent_stream(request, settings=settings, should_cancel=should_cancel):
        if await _stream_cancelled(should_cancel):
            return
        if item.get("event") == "final" and isinstance(item.get("response"), dict):
            if await _stream_cancelled(should_cancel):
                return
            yield {
                **item,
                "response": await _student_final_response_with_followups(item["response"], payload, settings, should_cancel=should_cancel),
            }
            continue
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
    user: Any,
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
        response = await run_posttest_agent(request, settings=effective_ai_settings(get_settings()))
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


async def generate_posttest_ai_summary(user: Any, session_id: str) -> StudentAssistantGeneratedResponse:
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


async def generate_posttest_mistake_explanation(user: Any, session_id: str) -> StudentAssistantGeneratedResponse:
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
