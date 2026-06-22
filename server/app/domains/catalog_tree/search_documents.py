from __future__ import annotations

from typing import Any

from sqlalchemy import text

from server.app.chemistry_search import chemistry_terms_for_document, formula_pair_terms
from server.app.domains.catalog_tree.common import (
    breadcrumbs,
    catalog_path_titles_with_chapter,
    clean,
    get_content,
    get_node,
    point_capable,
    published_path_available,
)
from server.app.domains.catalog_tree.equations import reaction_derived_terms, reaction_principle_text

SEARCH_DOCUMENT_HASH_IGNORED_FIELDS = {"updated_at"}


def student_search_document_sync_hash(document: dict[str, Any]) -> str:
    from server.app.domains.video_library.index_client import document_hash

    stable_document = {key: value for key, value in document.items() if key not in SEARCH_DOCUMENT_HASH_IGNORED_FIELDS}
    return document_hash(stable_document)


def queue_index_state(
    session: Any,
    *,
    node_id: str,
    action: str = "upsert",
    last_error: str | None = None,
    trigger_source: str = "automatic",
    soft: bool = False,
) -> None:
    desired_action = "delete" if action == "delete" else "upsert"
    canonical_point_id = None
    row = (
        session.execute(
            text("SELECT canonical_point_id FROM experiment_catalog_nodes WHERE id = :node_id"),
            {"node_id": node_id},
        )
        .mappings()
        .first()
    )
    if row and row.get("canonical_point_id"):
        canonical_point_id = str(row["canonical_point_id"])
    session.execute(
        text(
            """
            INSERT INTO experiment_catalog_point_search_index_state (
              node_id, placement_node_id, canonical_point_id, document_id, desired_action, sync_status, attempts, last_error, updated_at
            )
            VALUES (
              :node_id, :node_id, :canonical_point_id, :node_id, :desired_action, 'pending', 0, :last_error, now()
            )
            ON CONFLICT (node_id) DO UPDATE SET
              placement_node_id = EXCLUDED.placement_node_id,
              canonical_point_id = EXCLUDED.canonical_point_id,
              document_id = EXCLUDED.document_id,
              desired_action = EXCLUDED.desired_action,
              sync_status = 'pending',
              last_error = EXCLUDED.last_error,
              updated_at = now()
            """
        ),
        {"node_id": node_id, "canonical_point_id": canonical_point_id, "desired_action": desired_action, "last_error": last_error},
    )
    from server.app.domains.catalog_tree.jobs import queue_es_sync_job

    queue_es_sync_job(session, node_id=node_id, action=desired_action, trigger_source=trigger_source, soft=soft)


def queue_subtree_point_indexes(session: Any, *, node_id: str, action: str = "upsert", soft: bool = False) -> None:
    rows = (
        session.execute(
            text(
                """
                WITH RECURSIVE subtree AS (
                  SELECT id, node_kind
                  FROM experiment_catalog_nodes
                  WHERE id = :node_id
                  UNION ALL
                  SELECT child.id, child.node_kind
                  FROM experiment_catalog_nodes child
                  JOIN subtree ON child.parent_id = subtree.id
                )
                SELECT id FROM subtree WHERE node_kind = 'point'
                """
            ),
            {"node_id": node_id},
        )
        .scalars()
        .all()
    )
    for point_node_id in rows:
        queue_index_state(session, node_id=str(point_node_id), action=action, soft=soft)


def _ancestor_directory_context(session: Any, node_id: str) -> list[dict[str, Any]]:
    rows = (
        session.execute(
            text(
                """
                WITH RECURSIVE path AS (
                  SELECT id, parent_id, node_kind, title, 0 AS depth
                  FROM experiment_catalog_nodes
                  WHERE id = :node_id
                  UNION ALL
                  SELECT parent.id, parent.parent_id, parent.node_kind, parent.title, path.depth + 1
                  FROM experiment_catalog_nodes parent
                  JOIN path ON path.parent_id = parent.id
                )
                SELECT title
                FROM path
                WHERE node_kind = 'directory'
                ORDER BY depth DESC
                """
            ),
            {"node_id": node_id},
        )
        .mappings()
        .all()
    )
    return [dict(row) for row in rows]


def search_preview_for_node(session: Any, *, node_id: str) -> dict[str, Any] | None:
    node = get_node(session, node_id)
    if not point_capable(node):
        return None
    return student_search_document_for_node(session, node_id=node["node_id"], require_published=False)


def student_search_document_for_node(session: Any, *, node_id: str, require_published: bool = True) -> dict[str, Any] | None:
    node = get_node(session, node_id, include_archived=not require_published)
    if not point_capable(node):
        return None
    content = get_content(session, node["node_id"])
    if require_published:
        if node["status"] != "published":
            return None
        if not published_path_available(session, node["node_id"]):
            return None
    published_content = content if content and content.get("content_status") == "published" else None
    content_for_search = (published_content if require_published else content) or {"point_title": node["title"], "principle_mode": "text"}

    from server.app.domains.catalog_tree.media_bindings import student_video_readiness
    from server.app.domains.catalog_tree.related_links import related_links

    path = breadcrumbs(session, node["node_id"])
    path_titles = catalog_path_titles_with_chapter(node, path)
    path_text = " / ".join(path_titles)
    directory_context = _ancestor_directory_context(session, node["node_id"])
    category_text = " ".join(
        clean(value)
        for directory in directory_context
        for value in (
            directory.get("title"),
        )
        if clean(value)
    )
    related = related_links(session, node["node_id"], include_hidden=False, include_defaults=True)
    video_readiness = student_video_readiness(session, node["node_id"])
    principle = (
        reaction_principle_text(content_for_search)
        if content_for_search.get("principle_mode") == "equation"
        else clean(content_for_search.get("principle_text"))
    )
    core_principle = (
        reaction_principle_text(content_for_search, include_annotations=False)
        if content_for_search.get("principle_mode") == "equation"
        else clean(content_for_search.get("principle_text"))
    )
    phenomenon = clean(content_for_search.get("phenomenon_explanation"))
    safety = clean(content_for_search.get("safety_note"))
    chemistry = chemistry_terms_for_document(content_for_search.get("point_title"), core_principle, phenomenon, safety)
    title_chemistry = chemistry_terms_for_document(content_for_search.get("point_title"))
    equation_terms = reaction_derived_terms(content_for_search)
    formulae = sorted(set([*chemistry["formulae"], *equation_terms["formulae"]]))
    title_formulae = sorted(set(title_chemistry["formulae"]))
    title_formula_pairs = formula_pair_terms(title_formulae)
    aliases = sorted(set([*chemistry["aliases"], *equation_terms["aliases"]]))
    reactants = sorted(set(equation_terms.get("reactants") or []))
    products = sorted(set(equation_terms.get("products") or []))
    participants = sorted(set([*reactants, *products, *(equation_terms.get("participants") or [])]))
    equation_formula_pairs = sorted(set(equation_terms.get("equation_formula_pairs") or []))
    equation_rows = sorted(set(equation_terms.get("equation_rows") or []))
    reaction_features = sorted(set([*chemistry["reaction_features"], *equation_terms["reaction_features"]]))
    annotation_formulae = sorted(set(equation_terms.get("annotation_formulae") or []))
    annotation_aliases = sorted(set(equation_terms.get("annotation_aliases") or []))
    reagent_aliases = sorted(set(chemistry.get("reagent_aliases") or []))
    condition_tags = sorted(set([*(chemistry.get("condition_tags") or []), *(equation_terms.get("condition_tags") or [])]))
    phenomenon_tags = sorted(set(chemistry.get("phenomenon_tags") or []))
    property_tags = sorted(set(chemistry.get("property_tags") or []))
    search_text = " ".join(
        item
        for item in [
            path_text,
            category_text,
            clean(content_for_search.get("point_title")),
            principle,
            phenomenon,
            safety,
            " ".join(clean(link.get("target_title")) for link in related),
            " ".join(formulae),
            " ".join(title_formulae),
            " ".join(title_formula_pairs),
            " ".join(aliases),
            " ".join(reactants),
            " ".join(products),
            " ".join(participants),
            " ".join(equation_formula_pairs),
            " ".join(equation_rows),
            " ".join(reaction_features),
            " ".join(annotation_formulae),
            " ".join(annotation_aliases),
            " ".join(reagent_aliases),
            " ".join(condition_tags),
            " ".join(phenomenon_tags),
            " ".join(property_tags),
        ]
        if item
    )
    return {
        "id": node["node_id"],
        "result_type": "video_point",
        "node_id": node["node_id"],
        "placement_node_id": node["node_id"],
        "canonical_point_id": node.get("canonical_point_id"),
        "chapter_id": node["chapter_id"],
        "chapter_path": [node["chapter_title"]] if node.get("chapter_title") else [node["chapter_id"]],
        "catalog_path": path_titles,
        "category_text": category_text,
        "title": clean(content_for_search.get("point_title")) or node["title"],
        "subtitle": path_text,
        "snippet": phenomenon or principle,
        "search_text": search_text,
        "principle": principle,
        "phenomenon_explanation": phenomenon,
        "safety_note": safety,
        "reaction_equations": content_for_search.get("reaction_equations") if content_for_search.get("principle_mode") == "equation" else [],
        "formulae": formulae,
        "title_formulae": title_formulae,
        "title_formula_pairs": title_formula_pairs,
        "aliases": aliases,
        "strict_aliases": aliases,
        "reactants": reactants,
        "products": products,
        "participants": participants,
        "equation_formula_pairs": equation_formula_pairs,
        "equation_rows": equation_rows,
        "reaction_features": reaction_features,
        "annotation_formulae": annotation_formulae,
        "annotation_aliases": annotation_aliases,
        "reagent_aliases": reagent_aliases,
        "condition_tags": condition_tags,
        "phenomenon_tags": phenomenon_tags,
        "property_tags": property_tags,
        "related_text": [clean(link.get("target_title")) for link in related if clean(link.get("target_title"))],
        "has_video": bool(video_readiness["has_video"]),
        "video_count": int(video_readiness["video_count"]),
        "target": {
            "kind": "point_detail",
            "route": f"/point/{node['node_id']}",
            "node_id": node["node_id"],
            "placement_node_id": node["node_id"],
            "canonical_point_id": node.get("canonical_point_id"),
            "chapter_id": node["chapter_id"],
            "context_title": clean(content_for_search.get("point_title")) or node["title"],
            "context_summary": phenomenon or principle,
        },
        "updated_at": content_for_search.get("updated_at") or node.get("updated_at"),
    }
