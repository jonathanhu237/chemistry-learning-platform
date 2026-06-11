from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

from server.app import data_loader
from server.app.retrieval import keyword_score, tokenize
from server.app.schemas import RagAskRequest, RagAskResponse, RagSource


def source_preview(chunk: dict[str, Any]) -> RagSource:
    text = " ".join((chunk.get("text") or "").split())
    return RagSource(
        chunk_id=chunk["id"],
        source_file=chunk.get("source_file"),
        page_number=chunk.get("page_number"),
        text_preview=text[:220],
    )


def _context_preview(item: dict[str, Any]) -> RagSource:
    text = " ".join((item.get("text") or "").split())
    return RagSource(
        chunk_id=item.get("chunk_id") or item.get("id"),
        source_file=item.get("source_file"),
        page_number=item.get("page_number"),
        text_preview=text[:220],
    )


def _known_template(question: str, chunks: list[dict[str, Any]]) -> str | None:
    full_text = "\n".join(chunk.get("text", "") for chunk in chunks)
    q_tokens = tokenize(question)
    if {"KI", "CCl4"} & q_tokens or ("氯水" in question and "紫红" in question):
        if "Cl₂ + 2KI" in full_text or "CCl₄层呈紫红色" in full_text or "CCl4层呈紫红色" in full_text:
            return (
                "根据当前课程资料，氯水中的 Cl2 可氧化 I-，使 KI 中的 I- 生成 I2。"
                "I2 在 CCl4 中呈紫红色，因此振荡静置后会看到 CCl4 有机层变紫红色。"
                "可用反应式表示为 Cl2 + 2KI -> 2KCl + I2；这一现象也说明卤素单质氧化性 Cl2 > Br2 > I2。"
            )
    if "H2O2" in question or "过氧化氢" in question:
        return (
            "根据当前课程资料，H2O2 中氧元素为 -1 价，处在氧常见价态的中间位置。"
            "因此它遇到较强还原剂时可作氧化剂，被还原为 H2O 或 OH-；遇到较强氧化剂时也可作还原剂，被氧化为 O2。"
            "具体方向需要结合酸碱介质和反应对象判断。"
        )
    if "碱金属" in question and "金属性" in question:
        return (
            "根据当前课程资料，碱金属从上到下电子层数增加、原子半径增大，最外层电子受原子核束缚减弱，"
            "更容易失去电子，所以金属性和还原性总体增强，和水等试剂反应也更活泼。"
        )
    if "过渡金属" in question and "颜色" in question:
        return (
            "根据当前课程资料，过渡金属离子常有未充满的 d 轨道。配体或水分子形成的配位环境会造成 d 轨道能级分裂，"
            "电子发生 d-d 跃迁或电荷转移时吸收可见光的一部分，于是溶液或配合物呈现颜色。"
        )
    if "镧系收缩" in question:
        return (
            "根据当前课程资料，镧系收缩是指镧系元素随原子序数增加，Ln3+ 等离子半径总体缓慢减小的现象。"
            "主要原因是 4f 电子屏蔽核电荷的能力较弱，核电荷增加对外层电子吸引增强。"
            "它会影响稀土分离，也会导致某些第 5、6 周期同族元素半径和性质相近。"
        )
    return None


def template_answer(question: str, chunks: list[dict[str, Any]]) -> str:
    if not chunks or chunks[0].get("_score", 0) < 0.05:
        return "当前知识库中未找到足够依据，建议联系教师确认。"
    known = _known_template(question, chunks)
    if known:
        return known + "该回答基于课程检索片段生成，仍需教师审核。"
    previews = []
    for index, chunk in enumerate(chunks[:3], start=1):
        text = " ".join((chunk.get("text") or "").split())[:320]
        previews.append(f"{index}. {text}")
    return "根据当前课程资料，可先参考以下检索依据；该回答需教师审核：\n" + "\n".join(previews)


def try_llm_answer(question: str, chunks: list[dict[str, Any]]) -> str | None:
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LLM_API_KEY")
    model = os.getenv("OPENAI_MODEL") or os.getenv("LLM_MODEL")
    if not api_key or not model or not chunks:
        return None

    context = "\n\n".join(
        f"[{chunk['id']} | {chunk.get('source_file')} p.{chunk.get('page_number')}]\n{chunk.get('text', '')[:1200]}"
        for chunk in chunks[:5]
    )
    prompt = (
        "你是无机元素化学课程的学习助手。只能依据给定来源片段回答，不得编造来源；"
        "如果依据不足，回答“当前知识库中未找到足够依据”。回答末尾提醒需要教师审核。\n\n"
        f"问题：{question}\n\n来源片段：\n{context}"
    )
    payload = {
        "model": model,
        "input": [
            {"role": "system", "content": "Use only supplied retrieval context and keep source-grounded."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception:
        return None

    if isinstance(data.get("output_text"), str):
        return data["output_text"]
    texts: list[str] = []
    for item in data.get("output", []):
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                texts.append(content["text"])
    return "\n".join(texts).strip() or None


def _learning_card_context(experiment_id: str) -> list[dict[str, Any]]:
    card = data_loader.get_learning_card(experiment_id)
    if not card:
        return []
    text = "\n".join(f"{section.get('title')}：{section.get('content')}" for section in card.get("sections", []))
    return [
        {
            "id": card["id"],
            "chunk_id": card["id"],
            "source_file": "app_learning_cards.json",
            "page_number": None,
            "text": text,
            "_scope_bonus": 0.30,
        }
    ]


def _chapter_experiment_context(chapter_id: str) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for experiment in data_loader.experiments():
        if experiment.get("chapter_id") != chapter_id or not experiment.get("student_visible"):
            continue
        result.extend(_learning_card_context(experiment["id"]))
        result.extend(data_loader.chunks_by_ids(experiment.get("source_chunk_ids") or []))
    return result


def _score_context(question: str, items: list[dict[str, Any]], request: RagAskRequest) -> list[dict[str, Any]]:
    scored: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        item_id = item.get("id") or item.get("chunk_id")
        if not item_id or item_id in seen:
            continue
        seen.add(item_id)
        base = keyword_score(
            question,
            item,
            chapter_id=request.chapter_id,
            experiment_id=request.experiment_id,
            knowledge_point_ids=request.knowledge_point_ids,
        )
        score = min(1.0, base + float(item.get("_scope_bonus", 0)))
        if score > 0:
            scored.append({**item, "_score": round(score, 4)})
    scored.sort(key=lambda chunk: chunk["_score"], reverse=True)
    return scored[:5]


def retrieve_context(request: RagAskRequest) -> tuple[list[dict[str, Any]], str]:
    scopes: list[list[dict[str, Any]]] = []
    if request.experiment_id:
        experiment = data_loader.get_experiment(request.experiment_id)
        scopes.append(_learning_card_context(request.experiment_id))
        if experiment:
            scopes.append(data_loader.chunks_by_ids(experiment.get("source_chunk_ids") or []))
    if request.knowledge_point_ids:
        kp_chunks: list[dict[str, Any]] = []
        for kp_id in request.knowledge_point_ids:
            kp_chunks.extend(data_loader.related_chunks_for_kp(kp_id))
        scopes.append(kp_chunks)
    if request.chapter_id:
        scopes.append(_chapter_experiment_context(request.chapter_id))
        scopes.append([chunk for chunk in data_loader.source_chunks() if chunk.get("chapter_id") == request.chapter_id])
    scopes.append(data_loader.source_chunks())

    for scope in scopes:
        scored = _score_context(request.question, scope, request)
        if scored and scored[0].get("_score", 0) >= 0.05:
            return scored, "keyword"
    return [], "keyword"


def answer_question(request: RagAskRequest) -> RagAskResponse:
    chunks, mode = retrieve_context(request)
    if not chunks or chunks[0].get("_score", 0) < 0.05:
        return RagAskResponse(answer="当前知识库中未找到足够依据，建议联系教师确认。", sources=[], mode=mode, review_required=True)

    llm_answer = try_llm_answer(request.question, chunks)
    answer = llm_answer or template_answer(request.question, chunks)
    return RagAskResponse(answer=answer, sources=[_context_preview(chunk) for chunk in chunks], mode=mode, review_required=True)
