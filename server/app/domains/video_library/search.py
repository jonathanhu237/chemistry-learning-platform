from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Protocol

from sqlalchemy import text

from server.app.chemistry_search import chemistry_query_terms, chemistry_terms_for_document, formula_pair_terms, normalize_search_query
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


def _query_tokens(query: str) -> list[str]:
    normalized_query = normalize_search_query(query).strip().lower()
    if not normalized_query:
        return []
    return [token for token in re.split(r"[\s,，;；+→=]+", normalized_query) if token]


def _contains_any(text_value: str, query: str) -> bool:  # type: ignore[no-redef]
    normalized_text = text_value.lower()
    tokens = _query_tokens(query)
    if not tokens:
        return True
    return any(token in normalized_text for token in tokens)


def _local_score(document: VideoLibraryDocument, query: str) -> float:  # type: ignore[no-redef]
    tokens = _query_tokens(query)
    if not tokens:
        return document.score_boost
    fields = [
        (document.title.lower(), 6.0),
        (document.subtitle.lower(), 3.0),
        (document.snippet.lower(), 2.0),
        (document.search_text.lower(), 1.0),
    ]
    score = document.score_boost
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
                  n.id AS placement_node_id,
                  n.canonical_point_id,
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
                  COALESCE((
                    WITH RECURSIVE path AS (
                      SELECT id, parent_id, node_kind, title, 0 AS depth
                      FROM experiment_catalog_nodes
                      WHERE id = n.id
                      UNION ALL
                      SELECT parent.id, parent.parent_id, parent.node_kind, parent.title, path.depth + 1
                      FROM experiment_catalog_nodes parent
                      JOIN path ON path.parent_id = parent.id
                    )
                    SELECT jsonb_agg(
                      jsonb_build_object(
                        'title', title
                      )
                      ORDER BY depth DESC
                    )
                    FROM path
                    WHERE node_kind = 'directory'
                  ), '[]'::jsonb) AS directory_context,
                  jsonb_build_array(
                    jsonb_build_object(
                      'chapter_id', n.chapter_id,
                      'chapter_title', c.chapter_title,
                      'coverage_type', 'primary',
                      'sort_order', 0
                    )
                  ) AS chapter_bindings,
                  (
                    SELECT COUNT(*)
                    FROM experiment_catalog_point_media_bindings mb
                    JOIN media_assets ma ON ma.id = mb.media_asset_id
                    WHERE ((n.canonical_point_id IS NOT NULL AND mb.canonical_point_id = n.canonical_point_id)
                        OR mb.node_id = n.id)
                      AND ma.upload_status = 'ready'
                      AND COALESCE(ma.lifecycle_status, 'active') = 'active'
                      AND mb.binding_status <> 'archived'
                  ) AS video_count,
                  COALESCE((
                    SELECT jsonb_agg(
                      jsonb_build_object(
                        'node_id', COALESCE(target_placement.id, target.id),
                        'placement_node_id', COALESCE(target_placement.id, target.id),
                        'canonical_point_id', COALESCE(l.target_canonical_point_id, target.canonical_point_id),
                        'title', COALESCE(target_point.title, target_placement.title, target.title),
                        'relation_type', l.relation_type
                      )
                      ORDER BY l.sort_order, l.created_at
                    )
                    FROM experiment_catalog_point_related_links l
                    LEFT JOIN experiment_catalog_nodes target ON target.id = l.target_node_id
                    LEFT JOIN experiment_catalog_points target_point
                      ON target_point.id = COALESCE(l.target_canonical_point_id, target.canonical_point_id)
                    LEFT JOIN LATERAL (
                      SELECT placement.id, placement.title, placement.status
                      FROM experiment_catalog_nodes placement
                      WHERE placement.canonical_point_id = COALESCE(l.target_canonical_point_id, target.canonical_point_id)
                        AND placement.node_kind = 'point'
                        AND placement.status = 'published'
                      ORDER BY CASE WHEN placement.chapter_id = n.chapter_id THEN 0 ELSE 1 END,
                               placement.display_order,
                               placement.id
                      LIMIT 1
                    ) target_placement ON true
                    WHERE (
                        l.source_node_id = n.id
                        OR l.source_placement_node_id = n.id
                        OR (n.canonical_point_id IS NOT NULL AND l.source_canonical_point_id = n.canonical_point_id)
                      )
                      AND l.hidden = false
                      AND COALESCE(target_placement.status, target.status) = 'published'
                  ), '[]'::jsonb) AS related_links
                FROM experiment_catalog_nodes n
                JOIN chapters c ON c.id = n.chapter_id
                JOIN experiment_catalog_points cp ON cp.id = n.canonical_point_id
                JOIN experiment_catalog_point_content pc
                  ON pc.canonical_point_id = n.canonical_point_id
                  OR pc.node_id = n.id
                WHERE n.node_kind = 'point'
                  AND n.status = 'published'
                  AND cp.status = 'published'
                  AND pc.content_status = 'published'
                  AND (
                    WITH RECURSIVE path AS (
                      SELECT id, parent_id, status
                      FROM experiment_catalog_nodes
                      WHERE id = n.id
                      UNION ALL
                      SELECT parent.id, parent.parent_id, parent.status
                      FROM experiment_catalog_nodes parent
                      JOIN path ON path.parent_id = parent.id
                    )
                    SELECT COALESCE(bool_and(status = 'published'), false)
                    FROM path
                  )
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
    placement_node_id = _clean_text(row.get("placement_node_id")) or node_id
    canonical_point_id = _clean_text(row.get("canonical_point_id"))
    chapter_id = _clean_text(row.get("chapter_id"))
    profile = _profile_context_for_chapter(chapter_id, profiles)
    point_title = _clean_text(row.get("point_title"))
    principle = _clean_text(row.get("principle_equation") if row.get("principle_mode") == "equation" else row.get("principle_text"))
    phenomenon = _clean_text(row.get("phenomenon_explanation"))
    safety = _clean_text(row.get("safety_note"))
    video_count = int(row.get("video_count") or 0)
    related_links = row.get("related_links") if isinstance(row.get("related_links"), list) else []
    directory_context = row.get("directory_context") if isinstance(row.get("directory_context"), list) else []
    catalog_path = [str(item) for item in row.get("catalog_path") or [] if str(item).strip()]
    category_text = _document_search_text(
        [
            value
            for directory in directory_context
            if isinstance(directory, dict)
            for value in (
                directory.get("title"),
            )
        ]
    )
    chapter_title = _clean_text(row.get("chapter_title"))
    chemistry = chemistry_terms_for_document(point_title, principle, phenomenon, safety)
    title_chemistry = chemistry_terms_for_document(point_title)
    title_formula_pairs = formula_pair_terms(title_chemistry["formulae"])
    if not node_id:
        return None
    target = StudentVideoLibraryRouteTarget(
        kind="point_detail",
        route=f"/point/{placement_node_id}",
        node_id=placement_node_id,
        placement_node_id=placement_node_id,
        source_node_id=placement_node_id,
        canonical_point_id=canonical_point_id or None,
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
        category_text,
        point_title,
        principle,
        phenomenon,
        safety,
        [item.get("title") for item in related_links if isinstance(item, dict)],
        chemistry["formulae"],
        title_chemistry["formulae"],
        title_formula_pairs,
        chemistry["aliases"],
        chemistry.get("reagent_aliases", []),
        chemistry.get("condition_tags", []),
        chemistry.get("phenomenon_tags", []),
        chemistry.get("property_tags", []),
        chemistry["reaction_features"],
        profile.get("title") if profile else "",
        profile.get("family_name") if profile else "",
        profile.get("element_symbols") if profile else [],
    )
    document_id = node_id
    index_source = {
        "id": document_id,
        "result_type": "video_point",
        "node_id": placement_node_id,
        "placement_node_id": placement_node_id,
        "canonical_point_id": canonical_point_id,
        "chapter_id": row.get("chapter_id"),
        "chapter_ids": [row.get("chapter_id")],
        "catalog_path": catalog_path,
        "category_text": category_text,
        "title": point_title,
        "subtitle": " / ".join(catalog_path),
        "snippet": phenomenon or principle,
        "search_text": search_text,
        "principle": principle,
        "phenomenon_explanation": phenomenon,
        "safety_note": safety,
        "related_text": [item.get("title") for item in related_links if isinstance(item, dict) and item.get("title")],
        "formulae": chemistry["formulae"],
        "title_formulae": title_chemistry["formulae"],
        "title_formula_pairs": title_formula_pairs,
        "aliases": chemistry["aliases"],
        "strict_aliases": chemistry.get("strict_aliases", chemistry["aliases"]),
        "reactants": [],
        "products": [],
        "participants": chemistry["formulae"],
        "equation_formula_pairs": formula_pair_terms(chemistry["formulae"]) if row.get("principle_mode") == "equation" else [],
        "equation_rows": [principle] if row.get("principle_mode") == "equation" and principle else [],
        "annotation_formulae": [],
        "annotation_aliases": [],
        "reagent_aliases": chemistry.get("reagent_aliases", []),
        "condition_tags": chemistry.get("condition_tags", []),
        "phenomenon_tags": chemistry.get("phenomenon_tags", []),
        "property_tags": chemistry.get("property_tags", []),
        "reaction_features": chemistry["reaction_features"],
        "has_video": video_count > 0,
        "video_count": video_count,
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
        score_boost=6.0 + min(video_count, 1),
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


def _keyword_terms(values: list[Any]) -> list[str]:
    return _unique([str(value).strip().lower() for value in values if str(value or "").strip()])


def _add_route(routes: list[dict[str, Any]], *, name: str, label: str, fields: list[str], weight: float) -> None:
    routes.append({"name": name, "label": label, "fields": fields, "weight": weight})


def _build_elasticsearch_search_payload(query: str, *, limit: int) -> tuple[dict[str, Any], dict[str, Any]]:
    terms = chemistry_query_terms(query)
    routes: list[dict[str, Any]] = []
    if not terms["query_text"].strip():
        return {"size": limit, "query": {"match_all": {}}}, {"terms": terms, "routes": routes}

    should: list[dict[str, Any]] = []
    normalized_query = terms["normalized_query"]
    raw_query = terms["query_text"]

    _add_route(routes, name="title_phrase", label="标题短语精确匹配", fields=["title"], weight=9.0)
    should.append({"match_phrase": {"title": {"query": raw_query, "boost": 9.0, "_name": "title_phrase"}}})

    _add_route(
        routes,
        name="core_text",
        label="标题/三要素/摘要全文匹配",
        fields=["title", "snippet", "principle", "phenomenon_explanation", "aliases", "search_text"],
        weight=5.0,
    )
    should.append(
        {
            "multi_match": {
                "query": normalized_query,
                "fields": [
                    "title^6",
                    "snippet^3",
                    "principle^4",
                    "phenomenon_explanation^4",
                    "aliases^4",
                    "reagent_aliases^3",
                    "search_text",
                ],
                "type": "best_fields",
                "_name": "core_text",
            }
        }
    )

    _add_route(
        routes,
        name="directory_context",
        label="目录/章节上下文匹配",
        fields=["catalog_path", "category_text", "subtitle", "chapter_path"],
        weight=2.0,
    )
    should.append(
        {
            "multi_match": {
                "query": raw_query,
                "fields": ["catalog_path^2", "category_text^2", "subtitle^1.5", "chapter_path"],
                "type": "best_fields",
                "_name": "directory_context",
            }
        }
    )

    formula_terms = _keyword_terms(terms.get("formulae") or [])
    if formula_terms:
        formula_pairs = _keyword_terms(formula_pair_terms(terms.get("formulae") or []))
        if formula_pairs:
            _add_route(
                routes,
                name="title_formula_pair",
                label="标题公式组合匹配",
                fields=["title_formula_pairs"],
                weight=260.0,
            )
            should.append({"terms": {"title_formula_pairs": formula_pairs, "boost": 260.0, "_name": "title_formula_pair"}})
        _add_route(routes, name="title_formula_exact", label="标题化学式精确匹配", fields=["title_formulae"], weight=24.0)
        should.append({"terms": {"title_formulae": formula_terms, "boost": 24.0, "_name": "title_formula_exact"}})
        if formula_pairs:
            _add_route(
                routes,
                name="equation_formula_pair",
                label="同一方程式行公式组合匹配",
                fields=["equation_formula_pairs"],
                weight=34.0,
            )
            should.append({"terms": {"equation_formula_pairs": formula_pairs, "boost": 34.0, "_name": "equation_formula_pair"}})
        _add_route(routes, name="formula_exact", label="化学式精确匹配", fields=["formulae"], weight=14.0)
        should.append({"terms": {"formulae": formula_terms, "boost": 14.0, "_name": "formula_exact"}})
        _add_route(
            routes,
            name="participants_exact",
            label="方程式反应物/生成物匹配",
            fields=["participants", "reactants", "products"],
            weight=12.0,
        )
        _add_route(routes, name="reactants_exact", label="方程式反应物匹配", fields=["reactants"], weight=10.0)
        _add_route(routes, name="products_exact", label="方程式生成物匹配", fields=["products"], weight=10.0)
        _add_route(routes, name="annotation_formulae", label="方程式注释化学式匹配", fields=["annotation_formulae"], weight=5.0)
        should.extend(
            [
                {"terms": {"participants": formula_terms, "boost": 12.0, "_name": "participants_exact"}},
                {"terms": {"reactants": formula_terms, "boost": 10.0, "_name": "reactants_exact"}},
                {"terms": {"products": formula_terms, "boost": 10.0, "_name": "products_exact"}},
                {"terms": {"annotation_formulae": formula_terms, "boost": 5.0, "_name": "annotation_formulae"}},
            ]
        )

    strict_alias_terms = _keyword_terms(terms.get("strict_aliases") or [])
    if strict_alias_terms:
        _add_route(routes, name="strict_alias_exact", label="严格化学同义词匹配", fields=["strict_aliases", "aliases.keyword"], weight=9.0)
        should.extend(
            [
                {"terms": {"strict_aliases": strict_alias_terms, "boost": 9.0, "_name": "strict_alias_exact"}},
                {"terms": {"aliases.keyword": strict_alias_terms, "boost": 6.0, "_name": "alias_keyword"}},
            ]
        )

    if normalized_query:
        _add_route(routes, name="equation_text", label="方程式文本匹配", fields=["equation_rows", "principle"], weight=6.0)
        should.append(
            {
                "multi_match": {
                    "query": normalized_query,
                    "fields": ["equation_rows^6", "principle^3"],
                    "type": "best_fields",
                    "_name": "equation_text",
                }
            }
        )

    reagent_terms = _keyword_terms(terms.get("reagent_aliases") or [])
    if reagent_terms:
        _add_route(routes, name="reagent_aliases", label="试剂形态/俗称匹配", fields=["reagent_aliases"], weight=5.0)
        should.extend(
            [
                {"terms": {"reagent_aliases.keyword": reagent_terms, "boost": 5.0, "_name": "reagent_aliases"}},
                {"match": {"reagent_aliases": {"query": " ".join(reagent_terms), "boost": 3.0, "_name": "reagent_alias_text"}}},
            ]
        )

    for route_name, label, field_name, values, boost in [
        ("condition_tags", "条件标签匹配", "condition_tags", terms.get("condition_tags") or [], 4.0),
        ("phenomenon_tags", "实验现象标签匹配", "phenomenon_tags", terms.get("phenomenon_tags") or [], 4.0),
        ("property_tags", "化学性质标签匹配", "property_tags", terms.get("property_tags") or [], 4.0),
        ("reaction_features", "反应特征匹配", "reaction_features", terms.get("reaction_features") or [], 3.0),
    ]:
        field_terms = _keyword_terms(values)
        if not field_terms:
            continue
        _add_route(routes, name=route_name, label=label, fields=[field_name], weight=boost)
        should.append({"terms": {field_name: field_terms, "boost": boost, "_name": route_name}})

    return {
        "size": limit,
        "query": {"bool": {"should": should, "minimum_should_match": 1}},
    }, {"terms": terms, "routes": routes}


def _execute_elasticsearch_search(*, base_url: str, index: str, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/{index}/_search",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


class ElasticsearchVideoLibrarySearchAdapter:
    backend = "elasticsearch"

    def __init__(self, *, base_url: str, index: str, timeout: float) -> None:
        self.base_url = base_url.rstrip("/")
        self.index = index
        self.timeout = timeout

    def search(self, query: str, documents: list[VideoLibraryDocument], limit: int) -> list[VideoLibraryDocument]:
        if not query.strip():
            return LocalVideoLibrarySearchAdapter().search(query, documents, limit)
        payload, _diagnostics = _build_elasticsearch_search_payload(query, limit=limit)
        raw = _execute_elasticsearch_search(base_url=self.base_url, index=self.index, payload=payload, timeout=self.timeout)
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


def _source_route_matches(source: dict[str, Any], query_terms: dict[str, Any]) -> list[str]:
    routes: list[str] = []
    query_text = str(query_terms.get("query_text") or "").lower()
    normalized_query = str(query_terms.get("normalized_query") or "").lower()
    title_text = _document_search_text(source.get("title")).lower()
    core_text = _document_search_text(
        source.get("title"),
        source.get("snippet"),
        source.get("principle"),
        source.get("phenomenon_explanation"),
        source.get("aliases"),
        source.get("reagent_aliases"),
        source.get("search_text"),
    ).lower()
    directory_text = _document_search_text(source.get("catalog_path"), source.get("category_text"), source.get("subtitle")).lower()
    if query_text and query_text in title_text:
        routes.append("title_phrase")
    if any(token and token in core_text for token in re.split(r"[\s,，;；+→=]+", normalized_query)):
        routes.append("core_text")
    if query_text and query_text in directory_text:
        routes.append("directory_context")
    formulae = set(_keyword_terms(query_terms.get("formulae") or []))
    strict_aliases = set(_keyword_terms(query_terms.get("strict_aliases") or []))
    formula_pairs = set(_keyword_terms(formula_pair_terms(query_terms.get("formulae") or [])))
    if formula_pairs & set(_keyword_terms(source.get("title_formula_pairs") or [])):
        routes.append("title_formula_pair")
    if formulae & set(_keyword_terms(source.get("title_formulae") or [])):
        routes.append("title_formula_exact")
    if formula_pairs & set(_keyword_terms(source.get("equation_formula_pairs") or [])):
        routes.append("equation_formula_pair")
    if formulae & set(_keyword_terms(source.get("formulae") or [])):
        routes.append("formula_exact")
    if formulae & set(_keyword_terms(source.get("participants") or [])):
        routes.append("participants_exact")
    if formulae & set(_keyword_terms(source.get("reactants") or [])):
        routes.append("reactants_exact")
    if formulae & set(_keyword_terms(source.get("products") or [])):
        routes.append("products_exact")
    if strict_aliases & set(_keyword_terms(source.get("strict_aliases") or source.get("aliases") or [])):
        routes.append("strict_alias_exact")
    if normalized_query and any(token and token in _document_search_text(source.get("equation_rows"), source.get("principle")).lower() for token in re.split(r"[\s,，;；+→=]+", normalized_query)):
        routes.append("equation_text")
    for route_name, field_name in [
        ("reagent_aliases", "reagent_aliases"),
        ("condition_tags", "condition_tags"),
        ("phenomenon_tags", "phenomenon_tags"),
        ("property_tags", "property_tags"),
        ("reaction_features", "reaction_features"),
    ]:
        if set(_keyword_terms(query_terms.get(field_name) or [])) & set(_keyword_terms(source.get(field_name) or [])):
            routes.append(route_name)
    return _unique(routes)


def _diagnostic_hit_from_source(
    *,
    rank: int,
    score: float,
    source: dict[str, Any],
    matched_routes: list[str],
) -> dict[str, Any]:
    return {
        "rank": rank,
        "score": score,
        "id": _clean_text(source.get("id")),
        "node_id": _clean_text(source.get("node_id")),
        "placement_node_id": _clean_text(source.get("placement_node_id")),
        "canonical_point_id": _clean_text(source.get("canonical_point_id")),
        "title": _clean_text(source.get("title")),
        "subtitle": _clean_text(source.get("subtitle")),
        "catalog_path": source.get("catalog_path") or [],
        "snippet": _clean_text(source.get("snippet")),
        "matched_routes": matched_routes,
        "formulae": source.get("formulae") or [],
        "participants": source.get("participants") or [],
        "reaction_features": source.get("reaction_features") or [],
        "condition_tags": source.get("condition_tags") or [],
        "phenomenon_tags": source.get("phenomenon_tags") or [],
        "property_tags": source.get("property_tags") or [],
    }


def diagnose_video_library_search(*, query: str, limit: int = 10) -> dict[str, Any]:
    settings = get_settings()
    with db_session() as session:
        point_rows = _load_published_point_rows(session)
    profiles = _learning_profiles()
    documents = _build_documents([], profiles, point_rows=point_rows)
    payload, plan = _build_elasticsearch_search_payload(query, limit=limit)
    response: dict[str, Any] = {
        "query": query,
        "status": "ok",
        "backend": settings.video_library_search_backend,
        "index": settings.video_library_search_index,
        "document_count": len(documents),
        "query_plan": plan,
        "payload": payload,
        "results": [],
    }
    if (
        settings.video_library_search_enabled
        and settings.video_library_search_backend == "elasticsearch"
        and settings.video_library_search_url
    ):
        try:
            raw = _execute_elasticsearch_search(
                base_url=settings.video_library_search_url,
                index=settings.video_library_search_index,
                payload=payload,
                timeout=settings.video_library_search_timeout_seconds,
            )
            hits = raw.get("hits", {}).get("hits", [])
            response["total"] = raw.get("hits", {}).get("total")
            response["results"] = [
                _diagnostic_hit_from_source(
                    rank=index + 1,
                    score=float(hit.get("_score") or 0),
                    source=hit.get("_source") or {},
                    matched_routes=[str(route) for route in hit.get("matched_queries") or []],
                )
                for index, hit in enumerate(hits)
                if isinstance(hit, dict)
            ]
            return response
        except Exception as exc:  # noqa: BLE001 - diagnostics should report backend failure.
            response["status"] = "fallback" if settings.video_library_search_local_fallback else "error"
            response["error"] = str(exc)
            if not settings.video_library_search_local_fallback:
                return response

    matched_documents = LocalVideoLibrarySearchAdapter().search(query, documents, limit)
    response["backend"] = "local"
    response["results"] = [
        _diagnostic_hit_from_source(
            rank=index + 1,
            score=_local_score(document, query),
            source=document.index_source or {},
            matched_routes=_source_route_matches(document.index_source or {}, plan["terms"]),
        )
        for index, document in enumerate(matched_documents)
    ]
    response["total"] = {"value": len(matched_documents), "relation": "eq"}
    return response


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
