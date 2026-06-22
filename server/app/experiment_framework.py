from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from sqlalchemy import text

SOURCE_COLLECTION = "textbook_experiment_clean_v1"
DOC_ID = "DOC_CANONICAL_EXPERIMENT_V1"
BOOK_TITLE = "无机化学实验（第四版）"


def _row_dict(row: Any) -> dict[str, Any]:
    return dict(row)


def _zero_metrics() -> dict[str, int]:
    return {
        "node_count": 0,
        "chapter_count": 0,
        "section_count": 0,
        "protocol_count": 0,
        "canonical_chunk_count": 0,
        "linked_chunk_count": 0,
        "formal_experiment_count": 0,
        "formal_link_count": 0,
        "canonical_evidence_link_count": 0,
        "video_count": 0,
        "published_video_count": 0,
        "question_count": 0,
        "published_question_count": 0,
    }


def _load_nodes(session: Any) -> list[dict[str, Any]]:
    return [
        _row_dict(row)
        for row in session.execute(
            text(
                """
                SELECT id, parent_id, source_collection, doc_id, book_title, node_type,
                       title, full_path, depth, display_order, page_start, page_end,
                       metadata, content_status
                FROM experiment_framework_nodes
                WHERE source_collection = :source_collection
                  AND doc_id = :doc_id
                  AND content_status = 'published'
                ORDER BY display_order, title
                """
            ),
            {"source_collection": SOURCE_COLLECTION, "doc_id": DOC_ID},
        )
        .mappings()
        .all()
    ]


def _load_chunk_links(session: Any) -> dict[str, set[str]]:
    links: dict[str, set[str]] = defaultdict(set)
    for row in session.execute(
        text(
            """
            SELECT l.node_id, l.chunk_id
            FROM experiment_framework_chunk_links l
            JOIN experiment_framework_nodes n ON n.id = l.node_id
            WHERE n.source_collection = :source_collection
              AND n.doc_id = :doc_id
            """
        ),
        {"source_collection": SOURCE_COLLECTION, "doc_id": DOC_ID},
    ).mappings():
        links[str(row["node_id"])].add(str(row["chunk_id"]))
    return links


def _load_formal_links(session: Any) -> list[dict[str, Any]]:
    return [
        _row_dict(row)
        for row in session.execute(
            text(
                """
                SELECT l.node_id,
                       l.experiment_id,
                       fe.code AS experiment_code,
                       fe.title AS experiment_title,
                       fe.status AS experiment_status,
                       l.relation_type,
                       l.link_source,
                       l.evidence_chunk_id,
                       sc.section_title AS evidence_section_title,
                       l.confidence,
                       l.sort_order
                FROM experiment_framework_formal_links l
                JOIN experiment_framework_nodes n ON n.id = l.node_id
                JOIN formal_experiments fe ON fe.id = l.experiment_id
                LEFT JOIN source_chunks sc ON sc.id = l.evidence_chunk_id
                WHERE n.source_collection = :source_collection
                  AND n.doc_id = :doc_id
                  AND fe.status <> 'archived'
                ORDER BY n.display_order, l.sort_order, fe.code, l.relation_type
                """
            ),
            {"source_collection": SOURCE_COLLECTION, "doc_id": DOC_ID},
        )
        .mappings()
        .all()
    ]


def _load_formal_stats(session: Any, experiment_ids: set[str]) -> dict[str, dict[str, int]]:
    if not experiment_ids:
        return {}
    rows = session.execute(
        text(
            """
            SELECT fe.id AS experiment_id,
                   CASE WHEN COUNT(DISTINCT mb.id) FILTER (WHERE mb.status <> 'archived') > 0 THEN 1 ELSE 0 END AS video_count,
                   CASE WHEN COUNT(DISTINCT mb.id) FILTER (WHERE mb.status = 'published') > 0 THEN 1 ELSE 0 END AS published_video_count,
                   COUNT(DISTINCT q.id) FILTER (WHERE q.status <> 'archived') AS question_count,
                   COUNT(DISTINCT q.id) FILTER (WHERE q.status = 'published') AS published_question_count
            FROM formal_experiments fe
            LEFT JOIN media_bindings mb
              ON mb.target_type = 'experiment'
             AND mb.target_id = fe.id
            LEFT JOIN experiment_questions q
              ON q.experiment_id = fe.id
            WHERE fe.id = ANY(:experiment_ids)
            GROUP BY fe.id
            """
        ),
        {"experiment_ids": sorted(experiment_ids)},
    ).mappings()
    return {
        str(row["experiment_id"]): {
            "video_count": int(row["video_count"] or 0),
            "published_video_count": int(row["published_video_count"] or 0),
            "question_count": int(row["question_count"] or 0),
            "published_question_count": int(row["published_question_count"] or 0),
        }
        for row in rows
    }


def _count_source_chunks(session: Any) -> int:
    return int(
        session.execute(
            text(
                """
                SELECT COUNT(*)
                FROM source_chunks
                WHERE metadata->>'source_collection' = :source_collection
                  AND COALESCE(content_status, 'published') = 'published'
                """
            ),
            {"source_collection": SOURCE_COLLECTION},
        ).scalar()
        or 0
    )


def _node_sort_key(node: dict[str, Any]) -> tuple[int, int, int, str]:
    title = str(node.get("title") or "")
    if title.startswith("第一部分"):
        return (0, 0, int(node.get("display_order") or 0), title)
    match = re.search(r"第\s*(\d+)\s*章", title)
    if match:
        return (1, int(match.group(1)), int(node.get("display_order") or 0), title)
    return (2, int(node.get("display_order") or 0), int(node.get("depth") or 0), title)


def build_experiment_framework_overview(session: Any) -> dict[str, Any]:
    nodes = _load_nodes(session)
    if not nodes:
        return {
            "available": False,
            "source": {
                "source_collection": SOURCE_COLLECTION,
                "doc_id": DOC_ID,
                "book_title": BOOK_TITLE,
            },
            "metrics": _zero_metrics(),
            "roots": [],
            "nodes": [],
            "formal_links": [],
        }

    children_by_parent: dict[str | None, list[str]] = defaultdict(list)
    node_by_id = {str(node["id"]): node for node in nodes}
    for node in nodes:
        children_by_parent[node.get("parent_id")].append(str(node["id"]))

    direct_chunks = _load_chunk_links(session)
    formal_links = _load_formal_links(session)
    direct_formal_ids: dict[str, set[str]] = defaultdict(set)
    canonical_evidence_link_count = 0
    for link in formal_links:
        node_id = str(link["node_id"])
        experiment_id = str(link["experiment_id"])
        direct_formal_ids[node_id].add(experiment_id)
        if link.get("relation_type") == "canonical_evidence":
            canonical_evidence_link_count += 1

    all_formal_ids = {str(link["experiment_id"]) for link in formal_links}
    formal_stats = _load_formal_stats(session, all_formal_ids)

    aggregate_chunks: dict[str, set[str]] = {}
    aggregate_formals: dict[str, set[str]] = {}

    def collect(node_id: str) -> tuple[set[str], set[str]]:
        chunks = set(direct_chunks.get(node_id, set()))
        formals = set(direct_formal_ids.get(node_id, set()))
        for child_id in children_by_parent.get(node_id, []):
            child_chunks, child_formals = collect(child_id)
            chunks.update(child_chunks)
            formals.update(child_formals)
        aggregate_chunks[node_id] = chunks
        aggregate_formals[node_id] = formals
        return chunks, formals

    roots = [node_id for node_id, node in node_by_id.items() if node.get("parent_id") is None]
    for root_id in roots:
        collect(root_id)

    enriched_nodes: list[dict[str, Any]] = []
    for node in nodes:
        node_id = str(node["id"])
        experiment_ids = aggregate_formals.get(node_id, set())
        video_count = sum(formal_stats.get(experiment_id, {}).get("video_count", 0) for experiment_id in experiment_ids)
        published_video_count = sum(
            formal_stats.get(experiment_id, {}).get("published_video_count", 0) for experiment_id in experiment_ids
        )
        question_count = sum(formal_stats.get(experiment_id, {}).get("question_count", 0) for experiment_id in experiment_ids)
        published_question_count = sum(
            formal_stats.get(experiment_id, {}).get("published_question_count", 0) for experiment_id in experiment_ids
        )
        enriched_nodes.append(
            {
                **node,
                "direct_evidence_count": len(direct_chunks.get(node_id, set())),
                "evidence_count": len(aggregate_chunks.get(node_id, set())),
                "direct_formal_experiment_count": len(direct_formal_ids.get(node_id, set())),
                "formal_experiment_count": len(experiment_ids),
                "child_count": len(children_by_parent.get(node_id, [])),
                "video_count": video_count,
                "published_video_count": published_video_count,
                "question_count": question_count,
                "published_question_count": published_question_count,
            }
        )

    root_ids = {str(node["id"]) for node in nodes if node.get("parent_id") is None}
    top_nodes = sorted((node for node in enriched_nodes if node.get("parent_id") in root_ids), key=_node_sort_key)
    metrics = _zero_metrics()
    metrics.update(
        {
            "node_count": len(nodes),
            "chapter_count": sum(1 for node in nodes if node["node_type"] == "chapter"),
            "section_count": sum(1 for node in nodes if node["node_type"] == "section"),
            "protocol_count": sum(1 for node in nodes if node["node_type"] == "protocol"),
            "canonical_chunk_count": _count_source_chunks(session),
            "linked_chunk_count": len({chunk_id for values in direct_chunks.values() for chunk_id in values}),
            "formal_experiment_count": len(all_formal_ids),
            "formal_link_count": len(formal_links),
            "canonical_evidence_link_count": canonical_evidence_link_count,
            "video_count": sum(formal_stats.get(experiment_id, {}).get("video_count", 0) for experiment_id in all_formal_ids),
            "published_video_count": sum(
                formal_stats.get(experiment_id, {}).get("published_video_count", 0) for experiment_id in all_formal_ids
            ),
            "question_count": sum(formal_stats.get(experiment_id, {}).get("question_count", 0) for experiment_id in all_formal_ids),
            "published_question_count": sum(
                formal_stats.get(experiment_id, {}).get("published_question_count", 0) for experiment_id in all_formal_ids
            ),
        }
    )
    return {
        "available": True,
        "source": {
            "source_collection": SOURCE_COLLECTION,
            "doc_id": DOC_ID,
            "book_title": BOOK_TITLE,
        },
        "metrics": metrics,
        "roots": top_nodes,
        "nodes": enriched_nodes,
        "formal_links": formal_links,
    }
