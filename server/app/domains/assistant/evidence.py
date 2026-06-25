from __future__ import annotations

from typing import Any, Callable

from server.app.domains.assistant.evidence_shaping import (
    build_figure_evidence_items as _figure_evidence_items,
    merge_sources as _merge_sources,
)
from server.app.domains.assistant.rag_sources import (
    _source_asset_markdown,
    _source_evidence_payload,
    _source_from_chunk,
)
from server.app.domains.assistant.runtime import AgentRunContext
from server.app.domains.assistant.streaming import await_tool_result as _await_tool_result
from server.app.domains.assistant.tools import (
    curriculum_lookup_tool,
    published_resource_lookup_tool,
    rag_search_tool,
)
from server.app.domains.catalog_tree.ai_context import (
    catalog_point_static_evidence_package,
    hydrate_static_evidence_sources,
)
from server.app.domains.experiment_points.canonical_points import candidate_point_key as _candidate_point_key
from server.app.schemas import RagSource


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


def _catalog_node_source_payloads(sources: list[RagSource], role_by_chunk_id: dict[str, str]) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for source in sources:
        payload = _source_evidence_payload(source)
        payload["evidence_kind"] = role_by_chunk_id.get(source.chunk_id, "supplemental")
        payload["source_boundary"] = "catalog_node_static_evidence"
        payloads.append(payload)
    return payloads


def _build_catalog_node_evidence_package(context: AgentRunContext) -> bool:
    point_node_id = str(context.request.point_node_id or "").strip()
    if not point_node_id:
        return False
    try:
        package = catalog_point_static_evidence_package(point_node_id=point_node_id)
    except Exception as exc:
        package = {
            "enabled": True,
            "evidence_source": "catalog_node_static_evidence",
            "static_evidence_role": "fallback_or_supplemental",
            "point_node_id": point_node_id,
            "chunk_ids": [],
            "chunk_roles": {},
            "static_fallback_missing": True,
            "static_evidence_status": "missing_fallback_evidence",
            "source_count": 0,
            "bindings": [],
            "dynamic_rag_available": bool(context.request.allow_rag_lookup),
            "message": "Static catalog-node evidence lookup failed; dynamic RAG may still run when allowed.",
            "lookup_error": f"{exc.__class__.__name__}: {str(exc)[:240]}",
        }
    if not package:
        context.point_evidence = {
            "enabled": True,
            "evidence_source": "catalog_node_static_evidence",
            "static_evidence_role": "fallback_or_supplemental",
            "point_node_id": point_node_id,
            "chunk_ids": [],
            "sources": [],
            "source_count": 0,
            "static_fallback_missing": True,
            "static_evidence_status": "missing_fallback_evidence",
            "dynamic_rag_available": bool(context.request.allow_rag_lookup),
        }
        return True

    chunk_ids = _unique_texts(list(package.get("chunk_ids") or []))
    role_by_chunk_id = {
        str(key): str(value or "supplemental")
        for key, value in (package.get("chunk_roles") or {}).items()
    }
    fixed_sources, missing_chunk_ids = hydrate_static_evidence_sources(context.repositories, chunk_ids=chunk_ids)
    if fixed_sources:
        context.sources = _merge_sources(fixed_sources, context.sources)
    source_payloads = _catalog_node_source_payloads(fixed_sources[:10], role_by_chunk_id)
    context.point_evidence = {
        **package,
        "chunk_ids": chunk_ids,
        "missing_chunk_ids": missing_chunk_ids,
        "sources": source_payloads,
        "source_count": len(fixed_sources),
        "static_source_count": len(fixed_sources),
        "supplemental_dynamic_rag_allowed": bool(context.request.allow_rag_lookup),
    }
    if package.get("static_fallback_missing"):
        context.add_guardrail(
            "catalog_node_static_evidence_missing",
            "use_dynamic_rag_when_available",
            "catalog-node static fallback evidence is absent; keep structured point context and allow supplemental dynamic RAG when policy permits",
        )
    elif fixed_sources:
        context.add_guardrail(
            "catalog_node_static_evidence_loaded",
            "use_static_then_dynamic",
            "catalog-node static evidence loaded as fallback or supplemental evidence",
        )
    else:
        context.add_guardrail(
            "catalog_node_static_evidence_unhydrated",
            "use_dynamic_rag_when_available",
            "catalog-node evidence bindings exist but source_chunks did not hydrate any static evidence",
        )
    return True


def build_point_evidence_package(context: AgentRunContext) -> None:
    if _build_catalog_node_evidence_package(context):
        return

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


def _source_asset_answer(figure_evidence_items: list[dict[str, Any]]) -> str:
    if not figure_evidence_items:
        return "当前检索没有找到可直接展示的课程图片证据。可以换一个更具体的图名、页码或实验点位再试。"
    lines = [
        "可以。本轮检索已经找到可展示的课程图片证据：",
        "",
    ]
    for index, item in enumerate(figure_evidence_items[:3], start=1):
        caption = item.get("caption") or item.get("source_file") or "课程图片"
        page = f"p.{item.get('page_number')}" if item.get("page_number") else ""
        asset_count = item.get("asset_count") or 0
        suffix = f"（{page}，{asset_count} 个图片资源）" if page else f"（{asset_count} 个图片资源）"
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
    lines.extend(
        [
            "",
            "你可以在右侧材料中查看这些图片；也可以继续追问这张图说明的稳定性、氧化性或相关反应。",
        ]
    )
    return "\n".join(lines)


def has_usable_evidence(evidence: list[dict[str, Any]]) -> bool:
    for item in evidence:
        if not isinstance(item, dict):
            continue
        if item.get("text_preview") or item.get("caption") or item.get("source_file"):
            return True
        assets = item.get("assets")
        if isinstance(assets, list) and assets:
            return True
    return False


def _answer_evidence_items(evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
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


async def _collect_retrieval_context_for_answer(context: AgentRunContext) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    decision = context.retrieval_decision
    evidence: list[dict[str, Any]] = []
    platform_resources: list[dict[str, Any]] = []
    if decision.should_call_resource_lookup:
        platform_resources = published_resource_lookup_tool(context).get("resources") or []
        if not platform_resources:
            context.add_guardrail("no_fabricated_resource", "state_unavailable", "No ready + published platform resource matched this request.")
    if decision.should_call_rag:
        evidence = (await _await_tool_result(rag_search_tool(context, context.request.question))).get("evidence") or []
        if not has_usable_evidence(evidence):
            context.add_guardrail("rag_no_match", "answer_from_model_knowledge", "RAG did not return usable selected evidence for this turn.")
            if decision.strict_evidence:
                context.add_guardrail("retrieval_no_usable_evidence", "strict_evidence_missing", "Strict evidence was requested but no usable RAG evidence was selected.")
    elif not context.classification.get("allow_rag_lookup", True) and not decision.should_call_resource_lookup:
        context.add_guardrail("rag_lookup_disabled", "answer_without_rag", "Student RAG lookup is disabled for this turn.")
    return evidence, platform_resources


async def openai_answer_context_payload(
    context: AgentRunContext,
    *,
    conversation_history_payload: Callable[[AgentRunContext], list[dict[str, str]]],
) -> tuple[dict[str, Any], str | None]:
    curriculum = curriculum_lookup_tool(context, context.request.question)
    evidence, platform_resources = await _collect_retrieval_context_for_answer(context)
    figure_evidence_items = _figure_evidence_items(context, evidence)
    if context.classification.get("source_asset_request"):
        context.mode = "source_asset_evidence"
        return {}, _source_asset_answer(figure_evidence_items)

    point_titles = [
        point.get("content")
        for point in curriculum.get("knowledge_points", [])
        if point.get("content")
    ][:5]
    fixed_point_evidence = context.point_evidence.get("sources", []) if context.point_evidence else []
    return {
        "question": context.request.question,
        "chapter_id": context.request.chapter_id,
        "experiment_id": context.request.experiment_id,
        "knowledge_point_ids": context.request.knowledge_point_ids,
        "conversation_history": conversation_history_payload(context),
        "related_knowledge_points": point_titles,
        "point_context": context.point_evidence,
        "fixed_point_evidence": fixed_point_evidence,
        "rag_evidence": _answer_evidence_items(evidence),
        "rag_figure_evidence": figure_evidence_items,
        "platform_resources": platform_resources[:5],
        "source_figures_available": bool(figure_evidence_items),
        "source_figure_count": len(figure_evidence_items),
        "policy_decision": context.policy_decision.as_dict(),
        "retrieval_decision": context.retrieval_decision.as_dict(),
    }, None
