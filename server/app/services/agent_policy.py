from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from server.app.config import ROOT
from server.app.schemas import AgentAskRequest


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
