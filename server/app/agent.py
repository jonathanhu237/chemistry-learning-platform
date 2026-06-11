from __future__ import annotations

import os
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from server.app.config import ROOT, Settings, get_settings
from server.app.repositories import RepositoryProvider, get_repositories
from server.app.retrieval import keyword_score
from server.app.schemas import AgentAskRequest, AgentAskResponse, RagAskRequest, RagSource


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
ASSESSMENT_KEYWORDS = {"考试", "测验", "选择题", "题目", "答案", "选哪个", "直接告诉", "帮我选"}
UNSAFE_KEYWORDS = {"在家", "私下", "自制", "爆炸", "剧毒", "氢氟酸", "氰", "浓硫酸", "明火", "加热到", "剂量", "详细步骤"}
GREETING_RE = re.compile(r"^(你好|您好|hello|hi|嗨|在吗)[!！。.\s]*$", re.IGNORECASE)

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
    policy_decision: StudentAIPolicyDecision = field(default_factory=StudentAIPolicyDecision)
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    sources: list[RagSource] = field(default_factory=list)
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


def classify_agent_request(request: AgentAskRequest) -> dict[str, Any]:
    question = request.question.strip()
    lowered = question.lower()
    has_course_keyword = any(keyword.lower() in lowered for keyword in COURSE_KEYWORDS)
    has_scope_hint = bool(request.chapter_id or request.experiment_id or request.knowledge_point_ids)
    is_greeting = bool(GREETING_RE.match(question))
    is_resource_request = any(keyword in question for keyword in RESOURCE_KEYWORDS) or any(
        keyword in question for keyword in ("视频", "资料", "资源", "课件", "演示")
    )
    is_assessment_leakage = any(keyword in question for keyword in ASSESSMENT_KEYWORDS) and (
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
        "requires_evidence": factual_query and not is_greeting and not is_resource_request,
        "resource_request": is_resource_request,
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
            "continue_with_normal_answer",
            decision.reason or "invalid structured policy decision",
        )
    return decision


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
                        "chapter_id": context.request.chapter_id,
                        "experiment_id": context.request.experiment_id,
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
    if classification.get("requires_evidence"):
        return StudentAIPolicyDecision(
            mode="needs_platform_evidence",
            reason="local fallback identified course factual query requiring evidence",
            evidence_required=True,
            allowed_tools=("rag_search", "curriculum_lookup"),
        )
    return StudentAIPolicyDecision(mode="normal_answer", reason="local fallback allows normal course answer")


def _apply_policy_decision_to_classification(context: AgentRunContext) -> None:
    decision = context.policy_decision
    classification = context.classification
    mode = decision.mode if decision.mode in POLICY_DECISION_MODES else "normal_answer"
    resource_tool_allowed = "published_resource_lookup" in decision.allowed_tools
    if not decision.valid:
        classification.update(
            {
                "intent": "policy_fallback_normal",
                "in_course_scope": True,
                "requires_evidence": False,
                "resource_request": False,
                "experiment_safety": False,
                "assessment_leakage": False,
            }
        )
    else:
        classification.update(
            {
                "intent": mode,
                "in_course_scope": mode != "refuse_out_of_scope",
                "requires_evidence": bool(decision.evidence_required or mode == "needs_platform_evidence"),
                "resource_request": bool(resource_tool_allowed),
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
    )

    try:
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
            review_required=True,
        )
        _persist_agent_log(context, response)
        return response
    except Exception as exc:
        _persist_agent_error_log(context, exc)
        raise


def agent_to_rag_request(request: AgentAskRequest) -> RagAskRequest:
    return RagAskRequest(
        student_id=request.student_id,
        question=request.question,
        chapter_id=request.chapter_id,
        experiment_id=request.experiment_id,
        knowledge_point_ids=request.knowledge_point_ids,
    )


def rag_to_agent_request(request: RagAskRequest) -> AgentAskRequest:
    return AgentAskRequest(
        student_id=request.student_id,
        question=request.question,
        chapter_id=request.chapter_id,
        experiment_id=request.experiment_id,
        knowledge_point_ids=request.knowledge_point_ids,
    )


def rag_search_tool(context: AgentRunContext, query: str) -> dict[str, Any]:
    if not context.classification.get("allow_rag_lookup", True):
        result = {"evidence": [], "disabled": True}
        context.add_guardrail("rag_lookup_disabled", "skip_rag_lookup", "学生侧 AI RAG 接入已关闭。")
        context.record_tool("rag_search", {"query": query}, result["evidence"])
        return result
    chunks = _retrieve_context(context.repositories, query, context.request)
    sources = [_source_from_chunk(chunk) for chunk in chunks]
    context.sources = _merge_sources(context.sources, sources)
    result = {
        "evidence": [
            {
                "chunk_id": source.chunk_id,
                "source_file": source.source_file,
                "page_number": source.page_number,
                "text_preview": source.text_preview,
            }
            for source in sources
        ]
    }
    context.record_tool("rag_search", {"query": query}, result["evidence"])
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
    result = await Runner.run(agent, context.request.question, **kwargs)
    context.mode = "openai_agents_sdk"
    return str(result.final_output).strip()


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
    evidence_required = bool(context.classification["requires_evidence"] or context.policy_decision.evidence_required)
    if evidence_required and not context.classification["resource_request"] and not context.sources and "没有找到" not in answer:
        context.add_guardrail("source_grounding", "override_no_evidence", "事实性课程回答缺少来源。")
        answer = "当前平台没有找到足够可靠的已发布课程材料来回答这个问题。你可以换成具体章节、知识点或实验现象再问。"
    if context.classification["resource_request"] and not _has_resource_tool_result(context) and "没有" not in answer:
        context.add_guardrail("no_fabricated_resource", "override_unavailable_resource", "资源请求没有已发布资源支撑。")
        answer = "当前平台还没有查到已发布且可播放的相关视频或资料。老师后续上传并发布后，这里会显示。"
    if len(answer) > context.policy.max_answer_chars:
        context.add_guardrail("mobile_length", "trim", "回答超过小程序端建议长度。")
        answer = answer[: context.policy.max_answer_chars].rstrip() + "..."
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
                    "error_type": type(error).__name__,
                    "error_message": str(error)[:240],
                },
            }
        )
    except Exception:
        pass


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


def _source_from_chunk(chunk: dict[str, Any]) -> RagSource:
    text = " ".join((chunk.get("text") or chunk.get("markdown") or "").split())
    return RagSource(
        chunk_id=str(chunk.get("chunk_id") or chunk.get("id")),
        source_file=chunk.get("source_file"),
        page_number=chunk.get("page_number"),
        text_preview=text[:220],
    )


def source_to_dict(source: RagSource) -> dict[str, Any]:
    if hasattr(source, "model_dump"):
        return source.model_dump()
    return source.dict()


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
        "遇到危险实验操作请求，拒绝提供步骤、剂量和危险条件，转为安全说明。"
        "回答要短，适合手机端。"
        f"\n分类结果：{context.classification}"
        f"\n学生 AI 安全策略版本：{context.policy.version}"
        f"\n学生 AI 安全策略：{context.policy.compact_rail}"
        f"\n本次策略判定：{context.policy_decision.as_dict()}"
        f"\n课程限制提示摘录：{context.policy.source_excerpt}"
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
