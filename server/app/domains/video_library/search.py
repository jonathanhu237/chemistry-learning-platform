from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol

from sqlalchemy import text

from server.app.chemistry_search import chemistry_terms_for_document, normalize_search_query
from server.app.infrastructure.settings import get_settings
from server.app.infrastructure.database import db_session
from server.app.domains.student_learning.point_detail import _learning_profiles, _student_id
from server.app.student_video_library_schemas import (
    StudentVideoLibraryBrowseChip,
    StudentVideoLibraryBrowseState,
    StudentVideoLibraryResultGroup,
    StudentVideoLibraryResultItem,
    StudentVideoLibraryRouteTarget,
    StudentVideoLibrarySearchResponse,
)


@dataclass(frozen=True)
class VideoLibraryDocument:
    id: str
    result_type: str
    title: str
    subtitle: str
    snippet: str
    search_text: str
    score_boost: float
    target: StudentVideoLibraryRouteTarget | None
    badges: tuple[str, ...] = ()
    index_source: dict[str, Any] | None = None


class VideoLibrarySearchAdapter(Protocol):
    backend: str

    def search(self, query: str, documents: list[VideoLibraryDocument], limit: int) -> list[VideoLibraryDocument]:
        ...


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _unique(values: list[str]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = value.strip()
        if text and text not in seen:
            result.append(text)
            seen.add(text)
    return result


def _contains_any(text_value: str, query: str) -> bool:
    normalized_text = text_value.lower()
    normalized_query = normalize_search_query(query).strip().lower()
    if not normalized_query:
        return True
    tokens = [token for token in normalized_query.replace("，", " ").replace(",", " ").split() if token]
    if not tokens:
        tokens = [normalized_query]
    return all(token in normalized_text for token in tokens)


def _local_score(document: VideoLibraryDocument, query: str) -> float:
    normalized_query = normalize_search_query(query).strip().lower()
    if not normalized_query:
        return document.score_boost
    fields = [
        (document.title.lower(), 6.0),
        (document.subtitle.lower(), 3.0),
        (document.snippet.lower(), 2.0),
        (document.search_text.lower(), 1.0),
    ]
    score = document.score_boost
    tokens = [token for token in normalized_query.replace("，", " ").replace(",", " ").split() if token] or [normalized_query]
    for token in tokens:
        for field, weight in fields:
            if token in field:
                score += weight
    return score


def _profile_context_for_chapter(chapter_id: str, profiles: list[dict[str, Any]]) -> dict[str, Any] | None:
    return next(
        (
            profile
            for profile in profiles
            if profile.get("enabled", True) and _clean_text(profile.get("chapter_id")) == chapter_id
        ),
        None,
    )


def _chapter_target(profile: dict[str, Any] | None) -> StudentVideoLibraryRouteTarget | None:
    if not profile:
        return None
    profile_id = _clean_text(profile.get("profile_id"))
    if not profile_id:
        return None
    return StudentVideoLibraryRouteTarget(
        kind="chapter_detail",
        route=f"/chapter/{profile_id}",
        profile_id=profile_id,
        chapter_id=_clean_text(profile.get("chapter_id")) or None,
        element_symbol=_clean_text(profile.get("default_element_symbol")) if profile.get("default_element_symbol") else None,
        context_title=_clean_text(profile.get("title")),
        context_summary=_clean_text(profile.get("subtitle")) or _clean_text(profile.get("family_name")),
    )


def _ai_target(query: str, title: str, summary: str) -> StudentVideoLibraryRouteTarget:
    prompt = f"请结合实验视频解释：{query or title}"
    return StudentVideoLibraryRouteTarget(
        kind="ai_chat",
        route="/ai/chat",
        context_title=title,
        context_summary=summary,
        prompt=prompt,
    )


def _document_search_text(*parts: Any) -> str:
    flattened: list[str] = []
    for part in parts:
        if isinstance(part, (list, tuple, set)):
            flattened.extend(_clean_text(item) for item in part)
        else:
            flattened.append(_clean_text(part))
    return " ".join(item for item in flattened if item)


def _load_published_point_rows(session: Any) -> list[dict[str, Any]]:
    if not hasattr(session, "execute"):
        return []
    rows = (
        session.execute(
            text(
                """
                SELECT
                  n.id AS node_id,
                  n.chapter_id,
                  c.chapter_title,
                  n.title AS node_title,
                  n.summary,
                  n.display_order,
                  n.updated_at AS node_updated_at,
                  pc.point_title,
                  pc.principle_mode,
                  pc.principle_equation,
                  pc.principle_text,
                  pc.phenomenon_explanation,
                  pc.safety_note,
                  pc.updated_at AS content_updated_at,
                  COALESCE((
                    WITH RECURSIVE path AS (
                      SELECT id, parent_id, title, 0 AS depth
                      FROM experiment_catalog_nodes
                      WHERE id = n.id
                      UNION ALL
                      SELECT parent.id, parent.parent_id, parent.title, path.depth + 1
                      FROM experiment_catalog_nodes parent
                      JOIN path ON path.parent_id = parent.id
                    )
                    SELECT jsonb_agg(title ORDER BY depth DESC)
                    FROM path
                  ), '[]'::jsonb) AS catalog_path,
                  jsonb_build_array(
                    jsonb_build_object(
                      'chapter_id', n.chapter_id,
                      'chapter_title', c.chapter_title,
                      'coverage_type', 'primary',
                      'sort_order', 0
                    )
                  ) AS chapter_bindings,
                  COALESCE((
                    SELECT jsonb_agg(
                      jsonb_build_object(
                        'media_id', ma.id,
                        'title', COALESCE(mb.title, ma.title, ma.original_file_name),
                        'upload_status', ma.upload_status,
                        'binding_status', mb.binding_status,
                        'has_thumbnail', ma.thumbnail_relative_path IS NOT NULL
                      )
                      ORDER BY mb.display_order, mb.created_at
                    )
                    FROM experiment_catalog_point_media_bindings mb
                    JOIN media_assets ma ON ma.id = mb.media_asset_id
                    WHERE mb.node_id = n.id
                      AND ma.upload_status = 'ready'
                      AND mb.binding_status = 'published'
                  ), '[]'::jsonb) AS videos,
                  COALESCE((
                    SELECT jsonb_agg(
                      jsonb_build_object(
                        'node_id', target.id,
                        'title', COALESCE(l.label, target.title),
                        'relation_type', l.relation_type
                      )
                      ORDER BY l.sort_order, l.created_at
                    )
                    FROM experiment_catalog_point_related_links l
                    JOIN experiment_catalog_nodes target ON target.id = l.target_node_id
                    WHERE l.source_node_id = n.id
                      AND l.hidden = false
                      AND target.status = 'published'
                  ), '[]'::jsonb) AS related_links
                FROM experiment_catalog_nodes n
                JOIN chapters c ON c.id = n.chapter_id
                JOIN experiment_catalog_point_content pc ON pc.node_id = n.id
                WHERE n.node_kind IN ('point', 'hybrid')
                  AND n.status = 'published'
                  AND pc.content_status = 'published'
                ORDER BY c.chapter_number NULLS LAST, n.display_order, n.id
                """
            )
        )
        .mappings()
        .all()
    )
    return [dict(row) for row in rows]


def _point_document(row: dict[str, Any], profiles: list[dict[str, Any]]) -> VideoLibraryDocument | None:
    node_id = _clean_text(row.get("node_id"))
    chapter_id = _clean_text(row.get("chapter_id"))
    profile = _profile_context_for_chapter(chapter_id, profiles)
    point_title = _clean_text(row.get("point_title"))
    principle = _clean_text(row.get("principle_equation") if row.get("principle_mode") == "equation" else row.get("principle_text"))
    phenomenon = _clean_text(row.get("phenomenon_explanation"))
    safety = _clean_text(row.get("safety_note"))
    videos = row.get("videos") if isinstance(row.get("videos"), list) else []
    related_links = row.get("related_links") if isinstance(row.get("related_links"), list) else []
    catalog_path = [str(item) for item in row.get("catalog_path") or [] if str(item).strip()]
    chapter_title = _clean_text(row.get("chapter_title"))
    chemistry = chemistry_terms_for_document(point_title, principle, phenomenon, safety)
    if not node_id:
        return None
    target = StudentVideoLibraryRouteTarget(
        kind="point_detail",
        route=f"/point/{node_id}",
        node_id=node_id,
        profile_id=_clean_text(profile.get("profile_id")) if profile else None,
        chapter_id=chapter_id or None,
        catalog_path=catalog_path,
        point_title=point_title,
        context_title=point_title,
        context_summary=phenomenon or principle,
    )
    search_text = _document_search_text(
        row.get("chapter_title"),
        catalog_path,
        point_title,
        principle,
        phenomenon,
        safety,
        [item.get("title") for item in related_links if isinstance(item, dict)],
        [item.get("title") for item in videos if isinstance(item, dict)],
        chemistry["formulae"],
        chemistry["aliases"],
        chemistry["reaction_features"],
        profile.get("title") if profile else "",
        profile.get("family_name") if profile else "",
        profile.get("element_symbols") if profile else [],
    )
    document_id = node_id
    index_source = {
        "id": document_id,
        "result_type": "video_point",
        "node_id": node_id,
        "chapter_id": row.get("chapter_id"),
        "chapter_ids": [row.get("chapter_id")],
        "catalog_path": catalog_path,
        "title": point_title,
        "subtitle": " / ".join(catalog_path),
        "snippet": phenomenon or principle,
        "search_text": search_text,
        "principle": principle,
        "phenomenon_explanation": phenomenon,
        "safety_note": safety,
        "related_text": [item.get("title") for item in related_links if isinstance(item, dict) and item.get("title")],
        "formulae": chemistry["formulae"],
        "aliases": chemistry["aliases"],
        "reaction_features": chemistry["reaction_features"],
        "has_video": bool(videos),
        "video_count": len(videos),
        "badges": _unique([chapter_title, *chemistry["reaction_features"]]),
        "target": target.model_dump(),
        "updated_at": row.get("content_updated_at"),
    }
    return VideoLibraryDocument(
        id=document_id,
        result_type="video_point",
        title=point_title,
        subtitle=" / ".join(catalog_path),
        snippet=phenomenon or principle,
        search_text=search_text,
        score_boost=6.0 + len(videos),
        target=target,
        badges=tuple(_unique([chapter_title, "实验点位", *chemistry["formulae"][:2]])),
        index_source=index_source,
    )


def _build_point_documents(
    profiles: list[dict[str, Any]],
    point_rows: list[dict[str, Any]],
) -> list[VideoLibraryDocument]:
    documents = [_point_document(row, profiles) for row in point_rows]
    return [document for document in documents if document is not None]


def _build_documents(
    experiments: list[dict[str, Any]],
    profiles: list[dict[str, Any]],
    point_rows: list[dict[str, Any]] | None = None,
) -> list[VideoLibraryDocument]:
    _ = experiments
    return _build_point_documents(profiles, point_rows or [])


def _result_item(document: VideoLibraryDocument, score: float | None = None) -> StudentVideoLibraryResultItem | None:
    if not document.target:
        return None
    action_labels = {
        "video_point": "看点位",
        "experiment": "进实验",
        "chapter_experiment": "看章节",
        "knowledge_point": "看知识",
        "ai_prompt": "问 AI",
    }
    return StudentVideoLibraryResultItem(
        id=document.id,
        type=document.result_type,  # type: ignore[arg-type]
        title=document.title,
        subtitle=document.subtitle,
        snippet=document.snippet,
        score=float(score if score is not None else document.score_boost),
        badges=list(document.badges),
        action_label=action_labels.get(document.result_type, "打开"),
        target=document.target,
    )


class LocalVideoLibrarySearchAdapter:
    backend = "local"

    def search(self, query: str, documents: list[VideoLibraryDocument], limit: int) -> list[VideoLibraryDocument]:
        if not query.strip():
            return sorted(documents, key=lambda item: item.score_boost, reverse=True)[:limit]
        matches = [document for document in documents if _contains_any(document.search_text, query)]
        return sorted(matches, key=lambda item: _local_score(item, query), reverse=True)[:limit]


class ElasticsearchVideoLibrarySearchAdapter:
    backend = "elasticsearch"

    def __init__(self, *, base_url: str, index: str, timeout: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.index = index
        self.timeout = timeout

    def search(self, query: str, documents: list[VideoLibraryDocument], limit: int) -> list[VideoLibraryDocument]:
        if not query.strip():
            return LocalVideoLibrarySearchAdapter().search(query, documents, limit)
        normalized_query = normalize_search_query(query)
        payload = {
            "size": limit,
            "query": {
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": normalized_query,
                                "fields": [
                                    "title^5",
                                    "subtitle^2",
                                    "snippet^3",
                                    "principle^4",
                                    "phenomenon_explanation^4",
                                    "search_text",
                                    "aliases^4",
                                ],
                                "type": "best_fields",
                            }
                        },
                        {"terms": {"formulae": [token.upper() for token in normalized_query.split()]}},
                        {"terms": {"reaction_features": normalized_query.split()}},
                    ],
                    "minimum_should_match": 1,
                }
            },
        }
        request = urllib.request.Request(
            f"{self.base_url}/{self.index}/_search",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            raw = json.loads(response.read().decode("utf-8"))
        source_ids = [
            str(hit.get("_source", {}).get("id") or hit.get("_id") or "")
            for hit in raw.get("hits", {}).get("hits", [])
            if isinstance(hit, dict)
        ]
        by_id = {document.id: document for document in documents}
        return [by_id[source_id] for source_id in source_ids if source_id in by_id][:limit]


def _adapter() -> VideoLibrarySearchAdapter | None:
    settings = get_settings()
    if not settings.video_library_search_enabled or settings.video_library_search_backend == "disabled":
        return None
    if settings.video_library_search_backend == "elasticsearch" and settings.video_library_search_url:
        return ElasticsearchVideoLibrarySearchAdapter(
            base_url=settings.video_library_search_url,
            index=settings.video_library_search_index,
            timeout=settings.video_library_search_timeout_seconds,
        )
    return LocalVideoLibrarySearchAdapter()


def _browse_chips(documents: list[VideoLibraryDocument], profiles: list[dict[str, Any]]) -> list[StudentVideoLibraryBrowseChip]:
    chips: list[StudentVideoLibraryBrowseChip] = []
    phenomenon_terms = ["颜色变化", "沉淀", "气体", "分层", "褪色", "火焰", "放热"]
    reagent_terms = ["氯水", "溴水", "碘水", "高锰酸钾", "硫代硫酸钠", "CCl4"]
    search_corpus = " ".join(document.search_text for document in documents)
    for term in phenomenon_terms:
        if term in search_corpus or len(chips) < 4:
            chips.append(StudentVideoLibraryBrowseChip(kind="phenomenon", label=term, query=term))
    for term in reagent_terms:
        if term in search_corpus:
            chips.append(StudentVideoLibraryBrowseChip(kind="reagent", label=term, query=term))
    for profile in profiles[:6]:
        if not profile.get("enabled", True):
            continue
        title = _clean_text(profile.get("family_name")) or _clean_text(profile.get("title"))
        if title:
            chips.append(
                StudentVideoLibraryBrowseChip(
                    kind="element_family",
                    label=title,
                    query=title,
                    profile_id=_clean_text(profile.get("profile_id")) or None,
                    chapter_id=_clean_text(profile.get("chapter_id")) or None,
                    element_symbol=_clean_text(profile.get("default_element_symbol")) or None,
                )
            )
    return chips[:14]


def _browse_state(documents: list[VideoLibraryDocument], profiles: list[dict[str, Any]]) -> StudentVideoLibraryBrowseState:
    recommended_docs = sorted(
        [document for document in documents if document.result_type in {"video_point", "experiment"}],
        key=lambda item: item.score_boost,
        reverse=True,
    )[:6]
    return StudentVideoLibraryBrowseState(
        recommended=[item for item in (_result_item(document) for document in recommended_docs) if item],
        recent=[],
        chips=_browse_chips(documents, profiles),
    )


def _group_results(items: list[StudentVideoLibraryResultItem]) -> list[StudentVideoLibraryResultGroup]:
    group_meta = {
        "video_point": ("video_points", "实验观察点", "直接进入视频点位和实验观察。"),
        "experiment": ("experiments", "实验视频", "进入完整实验视频或实验详情。"),
        "chapter_experiment": ("chapters", "章节与知识", "回到关联章节继续学习。"),
        "knowledge_point": ("knowledge", "知识点", "从知识点回到学习页。"),
        "ai_prompt": ("ai", "AI 解释", "带着实验现象向 AI 提问。"),
    }
    buckets: dict[str, list[StudentVideoLibraryResultItem]] = {}
    for item in items:
        buckets.setdefault(item.type, []).append(item)
    groups: list[StudentVideoLibraryResultGroup] = []
    for result_type in ["video_point", "experiment", "chapter_experiment", "knowledge_point", "ai_prompt"]:
        group_items = buckets.get(result_type, [])
        if not group_items:
            continue
        key, title, summary = group_meta[result_type]
        groups.append(StudentVideoLibraryResultGroup(key=key, title=title, summary=summary, items=group_items))
    return groups


def _ai_prompt_item(query: str, documents: list[VideoLibraryDocument]) -> StudentVideoLibraryResultItem | None:
    if not query.strip():
        return None
    first = documents[0] if documents else None
    title = f"解释“{query.strip()}”相关实验现象"
    summary = first.snippet if first else "结合实验视频、试剂和现象生成解释。"
    target = _ai_target(query, title, summary)
    return StudentVideoLibraryResultItem(
        id=f"ai_prompt:{query.strip()}",
        type="ai_prompt",
        title=title,
        subtitle="AI 学习助手",
        snippet=summary,
        score=0.5,
        badges=["AI"],
        action_label="问 AI",
        target=target,
    )


def search_student_video_library(user: Any, *, query: str = "", limit: int = 24) -> StudentVideoLibrarySearchResponse:
    settings = get_settings()
    with db_session() as session:
        point_rows = _load_published_point_rows(session)
    profiles = _learning_profiles()
    documents = _build_documents([], profiles, point_rows=point_rows)
    browse = _browse_state(documents, profiles)

    adapter = _adapter()
    if adapter is None:
        return StudentVideoLibrarySearchResponse(
            query=query,
            status="disabled",
            backend="disabled",
            message="实验视频库搜索暂未启用。",
            total=0,
            groups=[],
            browse=browse,
        )

    try:
        matched_documents = adapter.search(query, documents, limit)
        backend = adapter.backend  # type: ignore[assignment]
        status = "ok"
        message = ""
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError):
        if not settings.video_library_search_local_fallback:
            return StudentVideoLibrarySearchResponse(
                query=query,
                status="error",
                backend="elasticsearch",
                message="实验视频库搜索服务暂时不可用。",
                total=0,
                groups=[],
                browse=browse,
            )
        matched_documents = LocalVideoLibrarySearchAdapter().search(query, documents, limit)
        backend = "local"
        status = "fallback"
        message = "搜索服务暂时不可用，已使用本地实验元数据结果。"

    items = [item for item in (_result_item(document, _local_score(document, query)) for document in matched_documents) if item]
    ai_item = _ai_prompt_item(query, matched_documents)
    if ai_item:
        items.append(ai_item)

    if query.strip() and not matched_documents:
        status = "empty" if status == "ok" else status
        message = message or "没有找到匹配的实验视频结果。"

    return StudentVideoLibrarySearchResponse(
        query=query,
        status=status,  # type: ignore[arg-type]
        backend=backend,  # type: ignore[arg-type]
        message=message,
        total=len(items),
        groups=_group_results(items),
        browse=browse,
    )


def video_library_index_preview(user: Any) -> dict[str, Any]:
    with db_session() as session:
        point_rows = _load_published_point_rows(session)
    profiles = _learning_profiles()
    documents = _build_documents([], profiles, point_rows=point_rows)
    return {
        "student_id": _student_id(user),
        "document_count": len(documents),
        "point_count": len({_clean_text(row.get("node_id")) for row in point_rows}),
        "hidden_document_count": len([document for document in documents if not document.target]),
    }
