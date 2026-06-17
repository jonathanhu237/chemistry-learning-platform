from __future__ import annotations

import os
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, AsyncIterator, Callable

from server.app.config import ROOT, Settings, get_settings
from server.app.hybrid_rag import retrieve_hybrid_context
from server.app.repositories import RepositoryProvider, get_repositories
from server.app.retrieval import keyword_score
from server.app.schemas import AgentAskRequest, AgentAskResponse, RagAskRequest, RagSource
from server.app.services.agent_output_normalization import (
    CHEM_MATH_OUTPUT_CONTRACT,
    has_raw_latex_leak,
    normalize_assistant_formula_output as _normalize_assistant_formula_output,
)
from server.app.services.rag_source_service import (
    _asset_url,
    _source_asset_markdown,
    _source_evidence_payload,
    _source_from_chunk,
    source_to_dict,
)


COURSE_KEYWORDS = {
    "化学",
    "无机",
    "元素",
    "实验",
    "反应",
    "方程",
    "离子",
    "氧化",
    "还原",
    "酸",
    "碱",
    "沉淀",
    "配位",
    "金属",
    "卤素",
    "氯",
    "溴",
    "碘",
    "硫",
    "氮",
    "过氧化氢",
    "试剂",
    "现象",
    "知识点",
    "章节",
    "视频",
    "资料",
    "KC",
    "KP",
}

OUT_OF_SCOPE_KEYWORDS = {
    "股票",
    "投资",
    "天气",
    "新闻",
    "电影",
    "游戏",
    "写代码",
    "编程",
    "小说",
    "历史人物",
    "政治",
}

RESOURCE_KEYWORDS = {"视频", "资料", "资源", "课件", "演示", "哪里看", "在哪看"}
PLATFORM_RESOURCE_KEYWORDS = {"视频", "资料", "资源", "课件", "演示", "播放", "可播放", "上传", "发布", "下载", "文件", "链接", "哪里看", "在哪看"}
RAG_SOURCE_ASSET_KEYWORDS = {
    "教材图",
    "原图",
    "截图",
    "图像",
    "图表",
    "插图",
    "示意图",
    "电势图",
    "F-Z",
    "FZ图",
    "Frost",
    "frost",
    "拉蒂默",
    "Latimer",
    "来源图",
    "证据图",
}
ASSESSMENT_KEYWORDS = {"考试", "测验", "选择题", "题目", "答案", "选哪个", "直接告诉", "帮我选"}
UNSAFE_KEYWORDS = {"在家", "私下", "自制", "爆炸", "剧毒", "氢氟酸", "氰", "浓硫酸", "明火", "加热到", "剂量", "详细步骤"}
GREETING_RE = re.compile(r"^(你好|您好|hello|hi|嗨|在吗)[!！。.\s]*$", re.IGNORECASE)


def _is_rag_source_asset_request(question: str) -> bool:
    text = question.strip()
    if not text:
        return False
    lowered = text.lower()
    literal_keywords = {
        "教材图",
        "教材图片",
        "来源图",
        "来源图片",
        "证据图",
        "证据图片",
        "原图",
        "插图",
        "图像证据",
        "图片证据",
        "F-Z图",
        "f-z图",
        "Frost图",
        "frost图",
        "拉蒂默图",
        "Latimer图",
        "latimer图",
    }
    if any(keyword.lower() in lowered for keyword in literal_keywords):
        return True
    if "图" in text and any(hint.lower() in lowered for hint in ("教材", "来源", "证据", "图片", "插图", "F-Z", "Frost", "Latimer", "拉蒂默", "电势")):
        return True
    if "图" in text and any(verb in text for verb in ("给我", "发我", "展示", "看看", "看一下", "引用", "返回")):
        return True
    if any(keyword in text for keyword in RAG_SOURCE_ASSET_KEYWORDS):
        return True
    return bool(re.search(r"(教材|课本|来源|证据).{0,8}图|图.{0,8}(教材|课本|来源|证据)", text, re.IGNORECASE))


def _is_platform_resource_request(question: str) -> bool:
    if _is_rag_source_asset_request(question):
        return False
    text = question.strip()
    if not text:
        return False
    resource_terms = [
        "视频",
        "资料",
        "资源",
        "课件",
        "演示",
        "播放",
        "链接",
        "下载",
        *PLATFORM_RESOURCE_KEYWORDS,
    ]
    availability_terms = [
        "有没有",
        "是否有",
        "有吗",
        "能不能看",
        "可以看",
        "可播放",
        "在哪里",
        "在哪",
        "哪里",
        "发布",
        "上传",
        "下载",
        "链接",
        "播放",
        "打开",
        "查看资源",
    ]
    explanation_terms = ["解释", "为什么", "原理", "现象", "说明什么", "怎么理解", "这个点位", "实验点位"]
    has_resource_term = any(keyword in text for keyword in resource_terms)
    has_availability_term = any(keyword in text for keyword in availability_terms)
    if not (has_resource_term and has_availability_term):
        return False
    if any(keyword in text for keyword in explanation_terms) and not any(
        keyword in text for keyword in ("有没有", "是否有", "有吗", "在哪里", "在哪", "哪里", "下载", "链接", "播放")
    ):
        return False
    return True

STUDENT_AI_POLICY_VERSION = "student-ai-policy-v1"
POLICY_DECISION_MODES = {
    "normal_answer",
    "refuse_out_of_scope",
    "safe_experiment_guidance",
    "assessment_hint",
    "needs_platform_evidence",
}
COMPACT_STUDENT_AI_POLICY_RAIL = """
学生 AI 学习助手只服务本课程学习。
1. 课程外请求：礼貌拒答，并引导回无机化学课程学习。
2. 危险实验请求：不得提供家庭、自制、绕过安全条件的实验步骤、剂量或操作细节；只解释安全原则、风险原因和课堂/实验室规范。
3. 索要测验、作业、考试直接答案：不得直接给答案；只给思路、概念提示、检查路径或分步引导。
4. 涉及实验现象、视频、课程资料、平台资源或需要核验的课程事实：必须依赖平台检索证据；找不到证据就说明平台未找到可靠资料，不编造。
5. 普通课程问题：可以回答，但应保持简洁、适合手机端阅读，并优先结合课程术语和学生当前章节上下文。
""".strip()


@dataclass(frozen=True)
class AgentPolicy:
    source_path: str | None
    source_excerpt: str
    course_scope: tuple[str, ...]
    compact_rail: str = COMPACT_STUDENT_AI_POLICY_RAIL
    version: str = STUDENT_AI_POLICY_VERSION
    max_answer_chars: int = 520


@dataclass
class StudentAIPolicyDecision:
    mode: str = "normal_answer"
    reason: str = ""
    evidence_required: bool = False
    student_guidance: str = ""
    allowed_tools: tuple[str, ...] = field(default_factory=tuple)
    valid: bool = True
    raw: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "reason": self.reason,
            "evidence_required": self.evidence_required,
            "student_guidance": self.student_guidance,
            "allowed_tools": list(self.allowed_tools),
            "valid": self.valid,
        }


@dataclass
class AgentRunContext:
    request: AgentAskRequest
    repositories: RepositoryProvider
    policy: AgentPolicy
    classification: dict[str, Any]
    settings: Settings | None = None
    policy_decision: StudentAIPolicyDecision = field(default_factory=StudentAIPolicyDecision)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    sources: list[RagSource] = field(default_factory=list)
    rag_traces: list[dict[str, Any]] = field(default_factory=list)
    point_evidence: dict[str, Any] = field(default_factory=dict)
    guardrail_decisions: list[dict[str, Any]] = field(default_factory=list)
    mode: str = "local"

    def record_tool(self, name: str, arguments: dict[str, Any], result: Any) -> None:
        self.tool_calls.append(
            {
                "name": name,
                "arguments": arguments,
                "result_count": _count_result(result),
                "result_preview": _preview_result(result),
            }
        )

    def add_guardrail(self, code: str, action: str, reason: str) -> None:
        self.guardrail_decisions.append({"code": code, "action": action, "reason": reason})


def load_agent_policy(policy_path: Path | None = None) -> AgentPolicy:
    path = policy_path or ROOT / "docs" / "students" / "Ai限制 提示词.md"
    text = ""
    source_path: str | None = None
    if path.exists():
        text = path.read_text(encoding="utf-8", errors="ignore")
        source_path = str(path)
    return AgentPolicy(
        source_path=source_path,
        source_excerpt=" ".join(text.split())[:1200],
        course_scope=tuple(sorted(COURSE_KEYWORDS)),
    )


def _candidate_point_key(index: int, title: str) -> str:
    digest = hashlib.sha1(title.strip().encode("utf-8")).hexdigest()[:8]
    return f"candidate-{index + 1}-{digest}"


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


def _build_point_evidence_package(context: AgentRunContext) -> None:
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

def classify_agent_request(request: AgentAskRequest) -> dict[str, Any]:
    question = request.question.strip()
    lowered = question.lower()
    has_course_keyword = any(keyword.lower() in lowered for keyword in COURSE_KEYWORDS)
    has_scope_hint = bool(request.chapter_id or request.experiment_id or request.point_key or request.knowledge_point_ids)
    is_greeting = bool(GREETING_RE.match(question))
    is_source_asset_request = _is_rag_source_asset_request(question)
    is_resource_request = (not is_source_asset_request) and (
        _is_platform_resource_request(question)
        or any(keyword in question for keyword in ("视频", "资料", "资源", "课件", "演示"))
    )
    is_resource_request = (not is_source_asset_request) and _is_platform_resource_request(question)
    is_assessment_leakage = (not request.assessment_review) and any(keyword in question for keyword in ASSESSMENT_KEYWORDS) and (
        "答案" in question or "选" in question or "直接" in question
    )
    is_experiment_request = "实验" in question or bool(request.experiment_id)
    is_unsafe_experiment = is_experiment_request and any(keyword in question for keyword in UNSAFE_KEYWORDS)
    is_out_of_scope = not (has_course_keyword or has_scope_hint or is_greeting) and any(
        keyword in question for keyword in OUT_OF_SCOPE_KEYWORDS
    )
    factual_query = not is_greeting and not is_out_of_scope and not is_assessment_leakage and not is_unsafe_experiment
    return {
        "intent": _intent_name(
            is_greeting=is_greeting,
            is_out_of_scope=is_out_of_scope,
            is_unsafe_experiment=is_unsafe_experiment,
            is_assessment_leakage=is_assessment_leakage,
            is_resource_request=is_resource_request,
            factual_query=factual_query,
        ),
        "in_course_scope": not is_out_of_scope,
        "requires_evidence": False,
        "rag_preferred": factual_query and not is_greeting and not is_resource_request,
        "resource_request": is_resource_request,
        "source_asset_request": is_source_asset_request,
        "experiment_safety": is_unsafe_experiment,
        "assessment_leakage": is_assessment_leakage,
        "simple_greeting": is_greeting,
        "allow_progress_lookup": bool(request.allow_progress_lookup and request.student_id),
        "allow_rag_lookup": bool(request.allow_rag_lookup),
    }


async def _policy_gate_decision(context: AgentRunContext, settings: Settings) -> StudentAIPolicyDecision:
    if not _sdk_enabled(settings):
        return _local_policy_decision_from_classification(context.classification)
    try:
        decision = await _run_openai_policy_gate(context, settings)
    except Exception as exc:
        context.add_guardrail(
            "policy_gate_fallback",
            "continue_with_local_policy",
            f"policy gate unavailable: {exc.__class__.__name__}",
        )
        return _local_policy_decision_from_classification(context.classification)
    if not decision.valid:
        context.add_guardrail(
            "policy_decision_invalid",
            "continue_with_local_policy",
            decision.reason or "invalid structured policy decision",
        )
        return _local_policy_decision_from_classification(context.classification)
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
                    "Return keys: mode, reason, evidence_required, student_guidance, allowed_tools. "
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
                        "assessment_review": context.request.assessment_review,
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


def _parse_policy_decision_payload(payload: Any) -> StudentAIPolicyDecision:
    if not isinstance(payload, dict):
        return _invalid_policy_decision("policy decision payload is not an object", {"payload": str(payload)[:400]})
    mode = str(payload.get("mode") or "").strip()
    if mode not in POLICY_DECISION_MODES:
        return _invalid_policy_decision(f"unknown policy decision mode: {mode or '<empty>'}", dict(payload))
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
        )
    if classification.get("experiment_safety"):
        return StudentAIPolicyDecision(
            mode="safe_experiment_guidance",
            reason="local fallback identified unsafe experiment details",
        )
    if classification.get("assessment_leakage"):
        return StudentAIPolicyDecision(
            mode="assessment_hint",
            reason="local fallback identified direct assessment-answer request",
        )
    if classification.get("resource_request"):
        return StudentAIPolicyDecision(
            mode="needs_platform_evidence",
            reason="local fallback identified platform resource request",
            evidence_required=True,
            allowed_tools=("published_resource_lookup", "rag_search", "curriculum_lookup"),
        )
    if classification.get("rag_preferred"):
        return StudentAIPolicyDecision(
            mode="normal_answer",
            reason="local fallback allows normal course answer with optional RAG support",
            evidence_required=False,
            allowed_tools=("rag_search", "curriculum_lookup"),
        )
    return StudentAIPolicyDecision(mode="normal_answer", reason="local fallback allows normal course answer")


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
    context = AgentRunContext(
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
        answer = _preflight_response(context)
        if answer is None:
            answer = await _run_with_optional_sdk(context, settings)
        answer = _apply_output_guardrails(context, answer)
        response = AgentAskResponse(
            answer=answer,
            sources=context.sources,
            mode=context.mode,
            classification=context.classification,
            tool_calls=context.tool_calls,
            guardrail_decisions=context.guardrail_decisions,
            rag_trace=_rag_trace_payload(context),
            review_required=True,
        )
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
    context = AgentRunContext(
        request=request,
        repositories=repositories,
        policy=policy or load_agent_policy(),
        classification=classify_agent_request(request),
        settings=settings,
    )

    try:
        _build_point_evidence_package(context)
        yield {"event": "status", "message": "正在判断问题类型与安全策略"}
        context.policy_decision = await _policy_gate_decision(context, settings)
        _apply_policy_decision_to_classification(context)
        answer = _preflight_response(context)

        if answer is None:
            answer_parts: list[str] = []
            if _sdk_enabled(settings):
                yield {"event": "status", "message": "正在连接模型，开始流式生成"}
                try:
                    async for delta in _run_openai_chat_completion_stream(context, settings):
                        if not delta:
                            continue
                        answer_parts.append(delta)
                        yield {"event": "delta", "delta": delta}
                    answer = "".join(answer_parts).strip()
                except Exception as exc:
                    context.add_guardrail(
                        "chat_completion_stream_fallback",
                        "fallback_to_local",
                        f"流式模型调用失败：{exc.__class__.__name__}",
                    )
                    yield {"event": "status", "message": "模型流式调用失败，已切换到本地兜底"}
                    context.mode = "local"
                    answer = _run_local_agent(context)
                    for delta in _chunk_stream_text(answer):
                        yield {"event": "delta", "delta": delta}
            else:
                yield {"event": "status", "message": "未配置可用模型，使用本地兜底回答"}
                context.mode = "local"
                answer = _run_local_agent(context)
                for delta in _chunk_stream_text(answer):
                    yield {"event": "delta", "delta": delta}
        else:
            for delta in _chunk_stream_text(answer):
                yield {"event": "delta", "delta": delta}

        guarded_answer = _apply_output_guardrails(context, answer)
        if guarded_answer != answer:
            answer = guarded_answer
            yield {"event": "replace", "answer": answer}

        response = AgentAskResponse(
            answer=answer,
            sources=context.sources,
            mode=context.mode,
            classification=context.classification,
            tool_calls=context.tool_calls,
            guardrail_decisions=context.guardrail_decisions,
            rag_trace=_rag_trace_payload(context),
            review_required=True,
        )
        _persist_agent_log(context, response)
        yield {"event": "final", "response": _dump_agent_response(response)}
    except Exception as exc:
        _persist_agent_error_log(context, exc)
        yield {"event": "error", "message": str(exc) or exc.__class__.__name__}


def agent_to_rag_request(request: AgentAskRequest) -> RagAskRequest:
    return RagAskRequest(
        student_id=request.student_id,
        question=request.question,
        chapter_id=request.chapter_id,
        experiment_id=request.experiment_id,
        point_key=request.point_key,
        knowledge_point_ids=request.knowledge_point_ids,
    )


def rag_to_agent_request(request: RagAskRequest) -> AgentAskRequest:
    return AgentAskRequest(
        student_id=request.student_id,
        question=request.question,
        chapter_id=request.chapter_id,
        experiment_id=request.experiment_id,
        point_key=request.point_key,
        knowledge_point_ids=request.knowledge_point_ids,
    )


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

    allowed_tool_names = set(context.policy_decision.allowed_tools)
    if context.policy_decision.mode == "needs_platform_evidence" and not allowed_tool_names:
        allowed_tool_names = {"rag_search", "curriculum_lookup"}
    if not allowed_tool_names:
        allowed_tool_names = {
            "rag_search",
            "curriculum_lookup",
            "published_resource_lookup",
            "own_student_progress_lookup",
        }

    agent = Agent(
        name="Inorganic Chemistry Learning Agent",
        model=settings.agent_llm_model,
        instructions=_agent_instructions(context),
        tools=[
            *([rag_search] if context.classification.get("allow_rag_lookup", True) and "rag_search" in allowed_tool_names else []),
            *([curriculum_lookup] if "curriculum_lookup" in allowed_tool_names else []),
            *([published_resource_lookup] if "published_resource_lookup" in allowed_tool_names else []),
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


def _figure_evidence_items(context: AgentRunContext, evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = [*evidence, *[source_to_dict(source) for source in context.sources]]
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in candidates:
        assets = item.get("assets") or []
        if not assets:
            continue
        chunk_id = str(item.get("chunk_id") or item.get("id") or item.get("caption") or len(result))
        if chunk_id in seen:
            continue
        seen.add(chunk_id)
        result.append(
            {
                "source_file": item.get("source_file"),
                "page_number": item.get("page_number"),
                "caption": item.get("caption") or item.get("text_preview"),
                "content_type": item.get("content_type"),
                "asset_count": len(assets),
                "asset_files": [
                    {
                        "file_name": asset.get("file_name"),
                        "kind": asset.get("kind"),
                        "path": asset.get("path"),
                        "url": _asset_url(asset.get("path")),
                        "markdown": _source_asset_markdown(asset, item.get("caption") or item.get("text_preview")),
                    }
                    for asset in assets[:3]
                    if isinstance(asset, dict) and asset.get("path")
                ],
            }
        )
    return result[:3]


async def _run_openai_chat_completion(context: AgentRunContext, settings: Settings) -> str:
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


async def _run_openai_chat_completion_stream(context: AgentRunContext, settings: Settings) -> AsyncIterator[str]:
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


def _run_local_agent(context: AgentRunContext) -> str:
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
    normalized_answer = _normalize_assistant_formula_output(answer)
    if normalized_answer != answer:
        if has_raw_latex_leak(answer):
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


def _generate_retrieval_queries(
    context: AgentRunContext,
    settings: Settings,
    question: str,
) -> tuple[list[str], dict[str, Any]]:
    trace: dict[str, Any] = {"status": "skipped", "reason": "", "provider": settings.agent_llm_provider}
    if not settings.rag_query_generation_enabled:
        trace["reason"] = "disabled"
        return [question], trace
    if not _sdk_enabled(settings):
        trace["reason"] = "llm_not_configured"
        return [question], trace
    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=settings.agent_llm_api_key or os.getenv("OPENAI_API_KEY"),
            base_url=settings.agent_llm_base_url or None,
            timeout=10.0,
        )
        response = client.chat.completions.create(
            model=settings.agent_llm_model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You rewrite an inorganic chemistry student question into concise retrieval queries. "
                        "Return JSON only with key queries as an array of 1 to 3 Chinese search queries. "
                        "Keep reagent names, experiment numbers, and chemistry terms exact. Do not answer the question."
                    ),
                },
                {
                    "role": "user",
                    "content": json.dumps(
                        {
                            "question": question,
                            "chapter_id": context.request.chapter_id,
                            "experiment_id": context.request.experiment_id,
                            "knowledge_point_ids": context.request.knowledge_point_ids,
                            "conversation_history": [
                                item.model_dump() if hasattr(item, "model_dump") else item.dict()
                                for item in context.request.conversation_history[-6:]
                            ],
                        },
                        ensure_ascii=False,
                    ),
                },
            ],
        )
        content = response.choices[0].message.content if response.choices else ""
        payload = json.loads(content or "{}")
        raw_queries = payload.get("queries") if isinstance(payload, dict) else []
        queries = [
            " ".join(str(item or "").split())
            for item in raw_queries
            if isinstance(item, str) and str(item or "").strip()
        ][:3]
        if not queries:
            trace.update({"status": "fallback", "reason": "empty_queries"})
            return [question], trace
        trace.update({"status": "generated", "reason": "", "queries": queries})
        return queries, trace
    except Exception as exc:
        trace.update({"status": "fallback", "reason": f"{exc.__class__.__name__}: {str(exc)[:160]}"})
        return [question], trace


def _rag_trace_payload(context: AgentRunContext) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if context.rag_traces:
        payload.update({"runs": context.rag_traces, "latest": context.rag_traces[-1]})
    if context.point_evidence:
        payload["point_context"] = context.point_evidence
    return payload


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


def _retrieve_context(
    repositories: RepositoryProvider,
    question: str,
    request: AgentAskRequest,
    limit: int = 5,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()

    def add(item: dict[str, Any]) -> None:
        item_id = str(item.get("id") or item.get("chunk_id") or "")
        if item_id and item_id not in seen:
            seen.add(item_id)
            candidates.append(item)

    if request.knowledge_point_ids:
        for kp_id in request.knowledge_point_ids:
            for chunk in repositories.content.related_chunks_for_kp(kp_id, limit=limit):
                add(chunk)
    source_chunks = repositories.content.source_chunks()
    if request.experiment_id:
        experiment = repositories.content.get_experiment(request.experiment_id)
        chunk_ids = set((experiment or {}).get("source_chunk_ids") or [])
        for chunk in source_chunks:
            if chunk.get("id") in chunk_ids or chunk.get("chunk_id") in chunk_ids:
                add(chunk)
    if request.chapter_id:
        for chunk in source_chunks:
            if chunk.get("chapter_id") == request.chapter_id:
                add(chunk)
    for chunk in source_chunks:
        add(chunk)

    scored: list[dict[str, Any]] = []
    for item in candidates:
        score = keyword_score(
            question,
            item,
            chapter_id=request.chapter_id,
            experiment_id=request.experiment_id,
            knowledge_point_ids=request.knowledge_point_ids,
        )
        if score > 0.04:
            scored.append({**item, "_score": score})
    scored.sort(key=lambda item: item["_score"], reverse=True)
    return scored[:limit]


def _dump_agent_response(response: AgentAskResponse) -> dict[str, Any]:
    if hasattr(response, "model_dump"):
        return response.model_dump()
    return response.dict()


def _chunk_stream_text(text: str, chunk_size: int = 18) -> list[str]:
    if not text:
        return []
    return [text[index : index + chunk_size] for index in range(0, len(text), chunk_size)]


def _merge_sources(existing: list[RagSource], incoming: list[RagSource]) -> list[RagSource]:
    result = list(existing)
    seen = {source.chunk_id for source in result}
    for source in incoming:
        if source.chunk_id not in seen:
            seen.add(source.chunk_id)
            result.append(source)
    return result[:8]


def _intent_name(**flags: bool) -> str:
    if flags["is_greeting"]:
        return "greeting"
    if flags["is_out_of_scope"]:
        return "out_of_scope"
    if flags["is_unsafe_experiment"]:
        return "unsafe_experiment"
    if flags["is_assessment_leakage"]:
        return "assessment_guidance"
    if flags["is_resource_request"]:
        return "resource_request"
    if flags["factual_query"]:
        return "course_factual_query"
    return "general_navigation"


def _sdk_enabled(settings: Settings) -> bool:
    return (
        settings.agent_llm_provider in {"openai", "openai_compatible"}
        and bool(settings.agent_llm_api_key or os.getenv("OPENAI_API_KEY"))
        and bool(settings.agent_llm_model)
    )


def _agent_instructions(context: AgentRunContext) -> str:
    return (
        "你是无机化学实验学习平台的受控学习 agent。"
        "只回答课程范围内的问题；事实、实验现象、方程式、资料推荐必须先调用工具取得证据。"
        "不能编造课程材料、视频或资料；没有证据时明确说明平台未找到可靠材料。"
        "遇到测验或考试直接答案请求，只给提示和概念引导。"
        "如果 assessment_review 为 true，说明学生已提交后测，允许解释已完成题目的错因和复习方法，但不要帮助作答未提交的测验。"
        "遇到危险实验操作请求，拒绝提供步骤、剂量和危险条件，转为安全说明。"
        "回答要短，适合手机端。"
        f"\n分类结果：{context.classification}"
        f"\n学生 AI 安全策略版本：{context.policy.version}"
        f"\n学生 AI 安全策略：{context.policy.compact_rail}"
        f"\n本次策略判定：{context.policy_decision.as_dict()}"
        f"\n课程限制提示摘录：{context.policy.source_excerpt}"
        f"{CHEM_MATH_OUTPUT_CONTRACT}"
    )


def _has_resource_tool_result(context: AgentRunContext) -> bool:
    for call in context.tool_calls:
        if call.get("name") == "published_resource_lookup" and call.get("result_count", 0) > 0:
            return True
    return False


def _count_result(result: Any) -> int:
    if isinstance(result, list):
        return len(result)
    if isinstance(result, dict):
        if "resources" in result and isinstance(result["resources"], list):
            return len(result["resources"])
        if "evidence" in result and isinstance(result["evidence"], list):
            return len(result["evidence"])
        return len(result)
    return 1 if result else 0


def _preview_result(result: Any) -> str:
    text = str(result)
    return text[:240]
