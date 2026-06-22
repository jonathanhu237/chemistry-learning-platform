from __future__ import annotations

import urllib.error
from typing import Any

from sqlalchemy import text

from server.app.chemistry_search import chemistry_query_terms, chemistry_terms_for_document, formula_pair_terms
from server.app.domains.catalog_tree.common import (
    MISSING_LEARNING_FIELD_KEYS,
    breadcrumbs,
    catalog_node_status_summary,
    catalog_path_titles_with_chapter,
    clean,
    get_content,
    get_node,
    node_card,
    node_select,
    point_capable,
    row_dict,
    validate_node_payload,
)
from server.app.domains.catalog_tree.equations import reaction_derived_terms, reaction_principle_text
from server.app.domains.video_library.index_client import (
    VideoLibraryIndexClient,
    document_hash,
    video_library_analyzer_assets,
)
from server.app.infrastructure.database import db_session
from server.app.infrastructure.settings import get_settings


TEACHER_CATALOG_SEARCH_INDEX_MAPPING_VERSION = "teacher-catalog-admin-v1"
TEACHER_SEARCH_DOCUMENT_HASH_IGNORED_FIELDS = {"updated_at"}
TEACHER_SEARCH_STATUS_FILTERS = {
    "all",
    "actionable",
    "blocked",
    "needs_content",
    "missing_principle",
    "missing_phenomenon",
    "missing_safety",
    "needs_video",
    "unpublished",
    "published",
    "sync_attention",
}


def _unique(values: list[Any]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        text_value = clean(value)
        if not text_value or text_value in seen:
            continue
        seen.add(text_value)
        result.append(text_value)
    return result


def _text_field(*, search_analyzer: str) -> dict[str, Any]:
    return {"type": "text", "analyzer": "chemistry_ik", "search_analyzer": search_analyzer}


def _keyword_field() -> dict[str, Any]:
    return {"type": "keyword", "normalizer": "chemistry_keyword"}


def teacher_catalog_search_index_mapping(
    *,
    analyzer: str = "ik_max_word",
    search_tokenizer: str = "ik_smart",
    search_analyzer: str = "chemistry_ik_search",
) -> dict[str, Any]:
    text_field = _text_field(search_analyzer=search_analyzer)
    keyword_field = _keyword_field()
    return {
        "settings": {
            "analysis": {
                "filter": {
                    "chemistry_stop": {
                        "type": "stop",
                        "ignore_case": True,
                        "stopwords_path": "analysis/chemistry_stopwords.txt",
                    },
                    "chemistry_synonyms": {
                        "type": "synonym_graph",
                        "lenient": True,
                        "synonyms_path": "analysis/chemistry_synonyms.txt",
                        "updateable": True,
                    },
                },
                "analyzer": {
                    "chemistry_ik": {
                        "type": "custom",
                        "tokenizer": analyzer,
                        "filter": ["lowercase", "chemistry_stop"],
                    },
                    "chemistry_ik_search": {
                        "type": "custom",
                        "tokenizer": search_tokenizer,
                        "filter": ["lowercase", "chemistry_synonyms", "chemistry_stop"],
                    },
                },
                "normalizer": {
                    "chemistry_keyword": {
                        "type": "custom",
                        "filter": ["lowercase"],
                    }
                },
            }
        },
        "mappings": {
            "_meta": {
                "mapping_version": TEACHER_CATALOG_SEARCH_INDEX_MAPPING_VERSION,
                "retrieval_model": "teacher-catalog-admin-authoring-context",
                "student_index_boundary": "separate-index-no-student-documents",
            },
            "dynamic": "false",
            "properties": {
                "id": {"type": "keyword"},
                "result_type": {"type": "keyword"},
                "node_id": {"type": "keyword"},
                "node_kind": {"type": "keyword"},
                "placement_node_id": {"type": "keyword"},
                "canonical_point_id": {"type": "keyword"},
                "chapter_id": {"type": "keyword"},
                "parent_id": {"type": "keyword"},
                "status": {"type": "keyword"},
                "content_status": {"type": "keyword"},
                "primary_state": {"type": "keyword"},
                "missing_field_keys": {"type": "keyword"},
                "legacy_experiment_ids": {"type": "keyword"},
                "legacy_point_keys": {"type": "keyword"},
                "title": text_field,
                "point_title": text_field,
                "summary": text_field,
                "teacher_note": text_field,
                "point_teacher_note": text_field,
                "catalog_path": text_field,
                "breadcrumb_text": text_field,
                "legacy_text": text_field,
                "search_text": text_field,
                "principle": text_field,
                "phenomenon_explanation": text_field,
                "safety_note": text_field,
                "equation_rows": text_field,
                "formulae": keyword_field,
                "title_formulae": keyword_field,
                "title_formula_pairs": keyword_field,
                "aliases": {
                    "type": "text",
                    "analyzer": "chemistry_ik",
                    "search_analyzer": search_analyzer,
                    "fields": {"keyword": keyword_field},
                },
                "strict_aliases": keyword_field,
                "reactants": keyword_field,
                "products": keyword_field,
                "participants": keyword_field,
                "equation_formula_pairs": keyword_field,
                "annotation_formulae": keyword_field,
                "annotation_aliases": keyword_field,
                "reagent_aliases": {
                    "type": "text",
                    "analyzer": "chemistry_ik",
                    "search_analyzer": search_analyzer,
                    "fields": {"keyword": keyword_field},
                },
                "reaction_features": {"type": "keyword"},
                "condition_tags": keyword_field,
                "phenomenon_tags": keyword_field,
                "property_tags": keyword_field,
                "node_status": {"type": "object", "enabled": True},
                "target": {"type": "object", "enabled": True},
                "updated_at": {"type": "date"},
            },
        },
    }


class TeacherCatalogSearchIndexClient(VideoLibraryIndexClient):
    def ensure_index(self, *, recreate: bool = False, analyzer: str = "ik_max_word") -> None:
        if recreate:
            try:
                self.request("DELETE", f"/{self.index}")
            except urllib.error.HTTPError as exc:
                if exc.code != 404:
                    raise
        try:
            self.request("HEAD", f"/{self.index}")
            return
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
        self.request("PUT", f"/{self.index}", teacher_catalog_search_index_mapping(analyzer=analyzer))


def configured_teacher_search_client() -> TeacherCatalogSearchIndexClient | None:
    settings = get_settings()
    if not settings.teacher_catalog_search_enabled:
        return None
    if settings.teacher_catalog_search_backend != "elasticsearch" or not settings.teacher_catalog_search_url:
        return None
    return TeacherCatalogSearchIndexClient(
        base_url=settings.teacher_catalog_search_url,
        index=settings.teacher_catalog_search_index,
        timeout=settings.teacher_catalog_search_timeout_seconds,
    )


def teacher_search_document_sync_hash(document: dict[str, Any]) -> str:
    stable_document = {key: value for key, value in document.items() if key not in TEACHER_SEARCH_DOCUMENT_HASH_IGNORED_FIELDS}
    return document_hash(stable_document)


def _legacy_identity_values(session: Any, node_id: str) -> dict[str, list[str]]:
    rows = (
        session.execute(
            text(
                """
                SELECT legacy_experiment_id, legacy_point_key, legacy_identity
                FROM experiment_catalog_legacy_identity_map
                WHERE catalog_node_id = :node_id
                ORDER BY legacy_kind, legacy_experiment_id, legacy_point_key
                """
            ),
            {"node_id": node_id},
        )
        .mappings()
        .all()
    )
    return {
        "legacy_experiment_ids": _unique([row.get("legacy_experiment_id") for row in rows]),
        "legacy_point_keys": _unique([row.get("legacy_point_key") for row in rows]),
        "legacy_identities": _unique([row.get("legacy_identity") for row in rows]),
    }


def _content_status(content: dict[str, Any] | None) -> str:
    return clean((content or {}).get("content_status")) or ("draft" if content else "missing")


def _status_facets(node: dict[str, Any], content: dict[str, Any] | None) -> dict[str, Any]:
    validation = validate_node_payload(node, content if content else None)
    status_summary = catalog_node_status_summary(node, content=content, validation=validation)
    core = status_summary.get("core_readiness") if isinstance(status_summary.get("core_readiness"), dict) else {}
    return {
        "node_status": status_summary,
        "primary_state": clean(status_summary.get("primary_state")) or clean(node.get("status")) or "draft",
        "missing_field_keys": [clean(item) for item in core.get("missing_field_keys", []) if clean(item)],
    }


def _chemistry_fields(content: dict[str, Any] | None, title: str, node_summary: str, teacher_notes: list[str]) -> dict[str, Any]:
    content = content or {}
    if content.get("principle_mode") == "equation":
        principle = reaction_principle_text(content)
        core_principle = reaction_principle_text(content, include_annotations=False)
    else:
        principle = clean(content.get("principle_text"))
        core_principle = principle
    phenomenon = clean(content.get("phenomenon_explanation"))
    safety = clean(content.get("safety_note"))
    chemistry = chemistry_terms_for_document(title, core_principle, phenomenon, safety, node_summary, *teacher_notes)
    title_chemistry = chemistry_terms_for_document(title)
    equation_terms = reaction_derived_terms(content)
    formulae = sorted(set([*chemistry["formulae"], *equation_terms["formulae"]]))
    title_formulae = sorted(set(title_chemistry["formulae"]))
    reactants = sorted(set(equation_terms.get("reactants") or []))
    products = sorted(set(equation_terms.get("products") or []))
    participants = sorted(set([*reactants, *products, *(equation_terms.get("participants") or [])]))
    aliases = sorted(set([*chemistry["aliases"], *equation_terms["aliases"]]))
    return {
        "principle": principle,
        "phenomenon_explanation": phenomenon,
        "safety_note": safety,
        "formulae": formulae,
        "title_formulae": title_formulae,
        "title_formula_pairs": formula_pair_terms(title_formulae),
        "aliases": aliases,
        "strict_aliases": sorted(set([*(chemistry.get("strict_aliases") or []), *aliases])),
        "reactants": reactants,
        "products": products,
        "participants": participants,
        "equation_formula_pairs": sorted(set(equation_terms.get("equation_formula_pairs") or [])),
        "equation_rows": sorted(set(equation_terms.get("equation_rows") or [])),
        "reaction_features": sorted(set([*chemistry["reaction_features"], *equation_terms["reaction_features"]])),
        "annotation_formulae": sorted(set(equation_terms.get("annotation_formulae") or [])),
        "annotation_aliases": sorted(set(equation_terms.get("annotation_aliases") or [])),
        "reagent_aliases": sorted(set(chemistry.get("reagent_aliases") or [])),
        "condition_tags": sorted(set([*(chemistry.get("condition_tags") or []), *(equation_terms.get("condition_tags") or [])])),
        "phenomenon_tags": sorted(set(chemistry.get("phenomenon_tags") or [])),
        "property_tags": sorted(set(chemistry.get("property_tags") or [])),
    }


def teacher_search_document_for_node(session: Any, *, node_id: str) -> dict[str, Any] | None:
    node = get_node(session, node_id, include_archived=True)
    if clean(node.get("status")) == "archived":
        return None

    content = get_content(session, node["node_id"]) if point_capable(node) else None
    path = breadcrumbs(session, node["node_id"])
    path_titles = catalog_path_titles_with_chapter(node, path)
    path_text = " / ".join(path_titles)
    legacy = _legacy_identity_values(session, node["node_id"])
    status_facets = _status_facets(node, content)
    title = clean((content or {}).get("point_title")) or clean(node.get("title"))
    summary = clean(node.get("summary"))
    node_teacher_note = clean(node.get("teacher_note"))
    point_teacher_note = clean((content or {}).get("teacher_note"))
    chemistry = _chemistry_fields(content, title, summary, [node_teacher_note, point_teacher_note]) if point_capable(node) else {
        "principle": "",
        "phenomenon_explanation": "",
        "safety_note": "",
        "formulae": [],
        "title_formulae": [],
        "title_formula_pairs": [],
        "aliases": [],
        "strict_aliases": [],
        "reactants": [],
        "products": [],
        "participants": [],
        "equation_formula_pairs": [],
        "equation_rows": [],
        "reaction_features": [],
        "annotation_formulae": [],
        "annotation_aliases": [],
        "reagent_aliases": [],
        "condition_tags": [],
        "phenomenon_tags": [],
        "property_tags": [],
    }
    search_text = " ".join(
        item
        for item in [
            path_text,
            title,
            summary,
            node_teacher_note,
            point_teacher_note,
            chemistry["principle"],
            chemistry["phenomenon_explanation"],
            chemistry["safety_note"],
            " ".join(legacy["legacy_experiment_ids"]),
            " ".join(legacy["legacy_point_keys"]),
            " ".join(legacy["legacy_identities"]),
            " ".join(chemistry["formulae"]),
            " ".join(chemistry["title_formulae"]),
            " ".join(chemistry["title_formula_pairs"]),
            " ".join(chemistry["aliases"]),
            " ".join(chemistry["reactants"]),
            " ".join(chemistry["products"]),
            " ".join(chemistry["participants"]),
            " ".join(chemistry["equation_formula_pairs"]),
            " ".join(chemistry["equation_rows"]),
            " ".join(chemistry["reagent_aliases"]),
            " ".join(chemistry["condition_tags"]),
            " ".join(chemistry["phenomenon_tags"]),
            " ".join(chemistry["property_tags"]),
        ]
        if item
    )
    return {
        "id": node["node_id"],
        "result_type": "teacher_catalog_node",
        "node_id": node["node_id"],
        "node_kind": clean(node.get("node_kind")) or "directory",
        "placement_node_id": node["node_id"] if point_capable(node) else None,
        "canonical_point_id": node.get("canonical_point_id") if point_capable(node) else None,
        "chapter_id": node["chapter_id"],
        "parent_id": node.get("parent_id"),
        "status": clean(node.get("status")) or "draft",
        "content_status": _content_status(content) if point_capable(node) else "not_applicable",
        "title": title,
        "point_title": clean((content or {}).get("point_title")),
        "summary": summary,
        "teacher_note": node_teacher_note,
        "point_teacher_note": point_teacher_note,
        "catalog_path": path_titles,
        "breadcrumb_text": path_text,
        "legacy_text": " ".join([*legacy["legacy_experiment_ids"], *legacy["legacy_point_keys"], *legacy["legacy_identities"]]),
        "legacy_experiment_ids": legacy["legacy_experiment_ids"],
        "legacy_point_keys": legacy["legacy_point_keys"],
        "search_text": search_text,
        "target": {
            "kind": "catalog_node",
            "route": f"/admin/catalog?node={node['node_id']}",
            "node_id": node["node_id"],
            "node_kind": clean(node.get("node_kind")) or "directory",
            "chapter_id": node["chapter_id"],
            "breadcrumb_node_ids": [str(item["node_id"]) for item in path],
        },
        "updated_at": (content or {}).get("updated_at") or node.get("updated_at"),
        **status_facets,
        **chemistry,
    }


def queue_teacher_index_state(
    session: Any,
    *,
    node_id: str,
    action: str = "upsert",
    last_error: str | None = None,
    trigger_source: str = "automatic",
    soft: bool = False,
) -> None:
    desired_action = "delete" if action == "delete" else "upsert"
    row = (
        session.execute(
            text(
                """
                SELECT canonical_point_id
                FROM experiment_catalog_nodes
                WHERE id = :node_id
                """
            ),
            {"node_id": node_id},
        )
        .mappings()
        .first()
    )
    canonical_point_id = str(row["canonical_point_id"]) if row and row.get("canonical_point_id") else None
    session.execute(
        text(
            """
            INSERT INTO experiment_catalog_teacher_search_index_state (
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
    from server.app.domains.catalog_tree.jobs import queue_teacher_search_sync_job

    queue_teacher_search_sync_job(session, node_id=node_id, action=desired_action, trigger_source=trigger_source, soft=soft)


def queue_subtree_teacher_indexes(
    session: Any,
    *,
    node_id: str,
    action: str = "upsert",
    trigger_source: str = "automatic",
    soft: bool = False,
) -> None:
    rows = (
        session.execute(
            text(
                """
                WITH RECURSIVE subtree AS (
                  SELECT id
                  FROM experiment_catalog_nodes
                  WHERE id = :node_id
                  UNION ALL
                  SELECT child.id
                  FROM experiment_catalog_nodes child
                  JOIN subtree ON child.parent_id = subtree.id
                )
                SELECT id
                FROM subtree
                """
            ),
            {"node_id": node_id},
        )
        .scalars()
        .all()
    )
    for current_node_id in rows:
        queue_teacher_index_state(session, node_id=str(current_node_id), action=action, trigger_source=trigger_source, soft=soft)


def mark_teacher_search_state_success(
    *,
    node_id: str,
    action: str,
    document_hash: str,
    indexed: bool = True,
    analyzer_version: str | None = None,
) -> None:
    with db_session() as session:
        row = (
            session.execute(
                text("SELECT canonical_point_id FROM experiment_catalog_nodes WHERE id = :node_id"),
                {"node_id": node_id},
            )
            .mappings()
            .first()
        )
        canonical_point_id = str(row["canonical_point_id"]) if row and row.get("canonical_point_id") else None
        session.execute(
            text(
                """
                INSERT INTO experiment_catalog_teacher_search_index_state (
                  node_id, placement_node_id, canonical_point_id, document_id, desired_action, sync_status, attempts,
                  document_hash, last_error, indexed_at, last_attempted_at, analyzer_version, updated_at
                )
                VALUES (
                  :node_id, :node_id, :canonical_point_id, :node_id, :action, 'synced', 1,
                  :document_hash, NULL, now(), now(), :analyzer_version, now()
                )
                ON CONFLICT (node_id) DO UPDATE SET
                  placement_node_id = EXCLUDED.placement_node_id,
                  canonical_point_id = EXCLUDED.canonical_point_id,
                  document_id = EXCLUDED.document_id,
                  desired_action = EXCLUDED.desired_action,
                  sync_status = 'synced',
                  attempts = experiment_catalog_teacher_search_index_state.attempts + 1,
                  document_hash = EXCLUDED.document_hash,
                  last_error = NULL,
                  indexed_at = CASE WHEN :indexed THEN now() ELSE experiment_catalog_teacher_search_index_state.indexed_at END,
                  last_attempted_at = now(),
                  analyzer_version = COALESCE(EXCLUDED.analyzer_version, experiment_catalog_teacher_search_index_state.analyzer_version),
                  updated_at = now()
                """
            ),
            {
                "node_id": node_id,
                "canonical_point_id": canonical_point_id,
                "action": action,
                "document_hash": document_hash,
                "indexed": bool(indexed),
                "analyzer_version": analyzer_version,
            },
        )


def mark_teacher_search_state_failure(*, node_id: str, action: str, error: str, status_value: str = "failed") -> None:
    with db_session() as session:
        row = (
            session.execute(
                text("SELECT canonical_point_id FROM experiment_catalog_nodes WHERE id = :node_id"),
                {"node_id": node_id},
            )
            .mappings()
            .first()
        )
        canonical_point_id = str(row["canonical_point_id"]) if row and row.get("canonical_point_id") else None
        session.execute(
            text(
                """
                INSERT INTO experiment_catalog_teacher_search_index_state (
                  node_id, placement_node_id, canonical_point_id, document_id, desired_action, sync_status, attempts,
                  last_error, last_attempted_at, updated_at
                )
                VALUES (
                  :node_id, :node_id, :canonical_point_id, :node_id, :action, :sync_status, 1,
                  :error, now(), now()
                )
                ON CONFLICT (node_id) DO UPDATE SET
                  placement_node_id = EXCLUDED.placement_node_id,
                  canonical_point_id = EXCLUDED.canonical_point_id,
                  desired_action = EXCLUDED.desired_action,
                  sync_status = EXCLUDED.sync_status,
                  attempts = experiment_catalog_teacher_search_index_state.attempts + 1,
                  last_error = EXCLUDED.last_error,
                  last_attempted_at = now(),
                  updated_at = now()
                """
            ),
            {
                "node_id": node_id,
                "canonical_point_id": canonical_point_id,
                "action": action,
                "sync_status": status_value,
                "error": error[:1000],
            },
        )


def _missing_field_for_filter(status_filter: str) -> str | None:
    mapping = {
        "missing_principle": "principle",
        "missing_phenomenon": "phenomenon",
        "missing_safety": "safety",
    }
    return mapping.get(status_filter)


def teacher_node_matches_status_filter(node: dict[str, Any], status_filter: str) -> bool:
    if status_filter not in TEACHER_SEARCH_STATUS_FILTERS or status_filter == "all":
        return True
    status = node.get("node_status") if isinstance(node.get("node_status"), dict) else {}
    core = status.get("core_readiness") if isinstance(status.get("core_readiness"), dict) else {}
    counts = core.get("descendant_status_counts") if isinstance(core.get("descendant_status_counts"), dict) else {}
    missing_counts = core.get("descendant_missing_field_counts") if isinstance(core.get("descendant_missing_field_counts"), dict) else {}
    state = clean(status.get("primary_state")) or clean(node.get("status")) or "draft"
    missing_field = _missing_field_for_filter(status_filter)
    if missing_field:
        if clean(node.get("node_kind")) == "directory":
            return int(missing_counts.get(missing_field) or counts.get(f"missing_{missing_field}") or 0) > 0
        missing_keys = core.get("missing_field_keys") if isinstance(core.get("missing_field_keys"), list) else []
        return state == "needs_content" and missing_field in missing_keys
    if clean(node.get("node_kind")) == "directory":
        if status_filter == "published":
            return int(counts.get("published") or 0) > 0
        if status_filter == "blocked":
            return int(counts.get("blocked") or 0) > 0
        if status_filter == "unpublished":
            return int(counts.get("draft") or 0) > 0 or int(counts.get("ready") or 0) > 0
        if status_filter == "needs_content":
            return int(counts.get("needs_content") or 0) > 0
        if status_filter == "needs_video":
            return int(counts.get("needs_video") or 0) > 0
        if status_filter == "sync_attention":
            return int(counts.get("sync_attention") or 0) > 0
        return any(int(counts.get(key) or 0) > 0 for key in ("blocked", "needs_content", "needs_video", "ready", "draft", "sync_attention"))
    if status_filter == "published":
        return state == "published"
    if status_filter == "blocked":
        return state == "blocked"
    if status_filter == "unpublished":
        return state in {"draft", "ready"}
    if status_filter == "needs_content":
        return state == "needs_content"
    if status_filter == "needs_video":
        return state == "needs_video"
    if status_filter == "sync_attention":
        return state == "sync_attention"
    return state in {"blocked", "needs_content", "needs_video", "draft", "ready", "sync_attention"}


def _status_filter_clause(status_filter: str) -> list[dict[str, Any]]:
    if status_filter == "all" or status_filter not in TEACHER_SEARCH_STATUS_FILTERS:
        return []

    def primary_or_descendant(states: list[str]) -> dict[str, Any]:
        should: list[dict[str, Any]] = [{"terms": {"primary_state": states}}]
        should.extend(
            {"range": {f"node_status.core_readiness.descendant_status_counts.{state}": {"gt": 0}}}
            for state in states
        )
        return {"bool": {"should": should, "minimum_should_match": 1}}

    missing_field = _missing_field_for_filter(status_filter)
    if missing_field:
        return [
            {
                "bool": {
                    "should": [
                        {"term": {"missing_field_keys": missing_field}},
                        {"range": {f"node_status.core_readiness.descendant_missing_field_counts.{missing_field}": {"gt": 0}}},
                    ],
                    "minimum_should_match": 1,
                }
            }
        ]
    if status_filter == "unpublished":
        return [primary_or_descendant(["draft", "ready"])]
    if status_filter == "actionable":
        return [primary_or_descendant(["blocked", "needs_content", "needs_video", "draft", "ready", "sync_attention"])]
    return [primary_or_descendant([status_filter])]


def build_teacher_catalog_search_payload(
    *,
    query: str,
    chapter_id: str | None = None,
    exclude_chapter_id: str | None = None,
    status_filter: str = "all",
    limit: int = 80,
) -> dict[str, Any]:
    normalized_limit = max(1, min(int(limit or 80), 200))
    query_terms = chemistry_query_terms(query)
    filters: list[dict[str, Any]] = [{"bool": {"must_not": [{"term": {"status": "archived"}}]}}]
    if chapter_id:
        filters.append({"term": {"chapter_id": chapter_id}})
    if exclude_chapter_id:
        filters.append({"bool": {"must_not": [{"term": {"chapter_id": exclude_chapter_id}}]}})
    filters.extend(_status_filter_clause(status_filter))
    should: list[dict[str, Any]] = [
        {
            "multi_match": {
                "query": clean(query),
                "fields": [
                    "title^9",
                    "point_title^9",
                    "catalog_path^5",
                    "breadcrumb_text^4",
                    "legacy_text^7",
                    "summary^3",
                    "teacher_note^3",
                    "point_teacher_note^3",
                    "principle^3",
                    "phenomenon_explanation^2",
                    "safety_note^2",
                    "equation_rows^4",
                    "search_text",
                ],
                "type": "best_fields",
                "_name": "text",
            }
        },
        {
            "multi_match": {
                "query": query_terms["normalized_query"],
                "fields": [
                    "title^6",
                    "point_title^6",
                    "catalog_path^4",
                    "breadcrumb_text^3",
                    "principle^3",
                    "equation_rows^4",
                    "aliases^4",
                    "reagent_aliases^3",
                    "search_text",
                ],
                "type": "most_fields",
                "_name": "chemistry_synonym_text",
            }
        },
    ]
    structured_terms = _unique(
        [
            *query_terms.get("formulae", []),
            *query_terms.get("strict_aliases", []),
            *query_terms.get("reagent_aliases", []),
            *query_terms.get("condition_tags", []),
            *query_terms.get("phenomenon_tags", []),
            *query_terms.get("property_tags", []),
        ]
    )
    for field in [
        "formulae",
        "title_formulae",
        "strict_aliases",
        "reactants",
        "products",
        "participants",
        "equation_formula_pairs",
        "annotation_formulae",
        "condition_tags",
        "phenomenon_tags",
        "property_tags",
    ]:
        if structured_terms:
            should.append({"terms": {field: structured_terms, "boost": 5, "_name": f"structured_{field}"}})
    return {
        "size": normalized_limit,
        "track_total_hits": True,
        "query": {
            "bool": {
                "filter": filters,
                "should": should,
                "minimum_should_match": 1,
            }
        },
        "_source": [
            "node_id",
            "node_kind",
            "chapter_id",
            "catalog_path",
            "breadcrumb_text",
            "primary_state",
            "target",
        ],
    }


def _matched_field_label(hit: dict[str, Any]) -> str | None:
    matched = hit.get("matched_queries") if isinstance(hit.get("matched_queries"), list) else []
    if any(str(item).startswith("structured_") for item in matched):
        return "化学结构匹配"
    if "chemistry_synonym_text" in matched:
        return "同义词/化学词匹配"
    if "text" in matched:
        return "文本匹配"
    return None


def _cards_for_node_ids(session: Any, node_ids: list[str], hit_context: dict[str, dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    if not node_ids:
        return []
    rows = (
        session.execute(
            text(
                node_select(
                    """
                    WHERE n.id = ANY(:node_ids)
                      AND n.status <> 'archived'
                    """
                )
            ),
            {"node_ids": node_ids},
        )
        .mappings()
        .all()
    )
    cards_by_id = {str(row["node_id"]): node_card(row_dict(row), include_teacher_note=True) for row in rows}
    results: list[dict[str, Any]] = []
    for node_id in node_ids:
        card = cards_by_id.get(node_id)
        if not card:
            continue
        path = breadcrumbs(session, node_id)
        context = (hit_context or {}).get(node_id, {})
        results.append(
            {
                **card,
                "breadcrumbs": path,
                "breadcrumb_path": " / ".join(catalog_path_titles_with_chapter(card, path)),
                "search_scope": context.get("search_scope"),
                "search_match": context or None,
                "stale_safe": True,
            }
        )
    return results


def _search_scope_for_chapter(node_chapter_id: str | None, chapter_id: str | None) -> str:
    if not chapter_id:
        return "all"
    return "current_chapter" if clean(node_chapter_id) == clean(chapter_id) else "other_chapter"


def _search_scope_counts(items: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for item in items:
        scope = clean(item.get("search_scope")) or "all"
        counts[scope] = counts.get(scope, 0) + 1
    return counts


def _total_hits_value(response: dict[str, Any] | None) -> int:
    total_payload = ((response or {}).get("hits") or {}).get("total") if isinstance(response, dict) else None
    if isinstance(total_payload, dict):
        return int(total_payload.get("value") or 0)
    if isinstance(total_payload, int):
        return total_payload
    return 0


def _teacher_es_hits_for_scope(
    *,
    client: VideoLibraryIndexClient,
    query: str,
    chapter_id: str | None = None,
    exclude_chapter_id: str | None = None,
    status_filter: str,
    limit: int,
    scope: str,
) -> tuple[list[str], dict[str, dict[str, Any]], int]:
    payload = build_teacher_catalog_search_payload(
        query=query,
        chapter_id=chapter_id,
        exclude_chapter_id=exclude_chapter_id,
        status_filter=status_filter,
        limit=limit,
    )
    response = client.request("GET", f"/{client.index}/_search", payload)
    hits = (((response or {}).get("hits") or {}).get("hits") or []) if isinstance(response, dict) else []
    hit_node_ids: list[str] = []
    hit_context: dict[str, dict[str, Any]] = {}
    for hit in hits:
        source = hit.get("_source") if isinstance(hit, dict) else {}
        node_id = clean((source or {}).get("node_id"))
        if not node_id or node_id in hit_context:
            continue
        hit_node_ids.append(node_id)
        hit_context[node_id] = {
            "score": hit.get("_score"),
            "field_label": _matched_field_label(hit),
            "backend": "elasticsearch",
            "catalog_path": (source or {}).get("catalog_path") or [],
            "primary_state": (source or {}).get("primary_state"),
            "search_scope": scope,
        }
    return hit_node_ids, hit_context, _total_hits_value(response)


def _postgres_fallback_search(
    *,
    query: str,
    chapter_id: str | None,
    status_filter: str,
    limit: int,
    fallback_reason: str,
) -> dict[str, Any]:
    term = f"%{clean(query)}%"
    fetch_limit = max(1, min(int(limit or 80) * 5, 500))
    filters = ["n.status <> 'archived'"]
    params: dict[str, Any] = {"term": term, "limit": fetch_limit, "chapter_id": chapter_id}
    where = " AND ".join(filters)
    with db_session() as session:
        rows = (
            session.execute(
                text(
                    node_select(
                        f"""
                        LEFT JOIN experiment_catalog_point_content pc ON pc.node_id = n.id
                          OR (n.canonical_point_id IS NOT NULL AND pc.canonical_point_id = n.canonical_point_id)
                        LEFT JOIN experiment_catalog_legacy_identity_map legacy ON legacy.catalog_node_id = n.id
                        WHERE {where}
                          AND (
                            n.title ILIKE :term
                            OR n.summary ILIKE :term
                            OR n.teacher_note ILIKE :term
                            OR pc.point_title ILIKE :term
                            OR pc.principle_equation ILIKE :term
                            OR pc.principle_text ILIKE :term
                            OR pc.phenomenon_explanation ILIKE :term
                            OR pc.safety_note ILIKE :term
                            OR pc.teacher_note ILIKE :term
                            OR legacy.legacy_experiment_id ILIKE :term
                            OR legacy.legacy_point_key ILIKE :term
                          )
                        ORDER BY
                          CASE WHEN :chapter_id IS NOT NULL AND n.chapter_id = :chapter_id THEN 0 ELSE 1 END,
                          n.updated_at DESC
                        LIMIT :limit
                        """
                    )
                ),
                params,
            )
            .mappings()
            .all()
        )
        cards = [
            {
                **node_card(row_dict(row), include_teacher_note=True),
                "breadcrumbs": breadcrumbs(session, str(row["node_id"])),
                "search_match": {"field_label": "本地文本匹配"},
                "stale_safe": True,
            }
            for row in rows
        ]
        for card in cards:
            path = card.get("breadcrumbs") or []
            scope = _search_scope_for_chapter(card.get("chapter_id"), chapter_id)
            card["breadcrumb_path"] = " / ".join(catalog_path_titles_with_chapter(card, path))
            card["search_scope"] = scope
            search_match = card.get("search_match")
            if isinstance(search_match, dict):
                search_match["search_scope"] = scope
    filtered = [card for card in cards if teacher_node_matches_status_filter(card, status_filter)]
    limited = filtered[: max(1, min(int(limit or 80), 200))]
    scope_counts = _search_scope_counts(limited)
    scope_totals = _search_scope_counts(filtered)
    return {
        "query": query,
        "items": limited,
        "meta": {
            "backend": "postgres_fallback",
            "fallback_reason": fallback_reason,
            "index": None,
            "mapping_version": None,
            "synonyms_active": False,
            "chemistry_recall_active": False,
            "status_filter": status_filter,
            "chapter_id": chapter_id,
            "total": len(filtered),
            "returned": len(limited),
            "limited": len(filtered) > len(limited),
            "scope_counts": scope_counts,
            "scope_totals": scope_totals,
            "cross_chapter_enabled": bool(chapter_id),
        },
    }


def search_teacher_catalog_nodes(
    *,
    query: str,
    chapter_id: str | None = None,
    limit: int = 80,
    status_filter: str = "all",
) -> dict[str, Any]:
    normalized_filter = status_filter if status_filter in TEACHER_SEARCH_STATUS_FILTERS else "all"
    if not clean(query):
        return {
            "query": query,
            "items": [],
            "meta": {
                "backend": "none",
                "fallback_reason": "empty_query",
                "index": None,
                "mapping_version": None,
                "synonyms_active": False,
                "chemistry_recall_active": False,
                "status_filter": normalized_filter,
                "chapter_id": chapter_id,
                "total": 0,
                "returned": 0,
                "limited": False,
            },
        }
    settings = get_settings()
    if not settings.teacher_catalog_search_enabled or settings.teacher_catalog_search_backend != "elasticsearch":
        return _postgres_fallback_search(
            query=query,
            chapter_id=chapter_id,
            status_filter=normalized_filter,
            limit=limit,
            fallback_reason="teacher_search_disabled",
        )
    client = configured_teacher_search_client()
    if client is None:
        if settings.teacher_catalog_search_local_fallback:
            return _postgres_fallback_search(
                query=query,
                chapter_id=chapter_id,
                status_filter=normalized_filter,
                limit=limit,
                fallback_reason="elasticsearch_not_configured",
            )
        return {"query": query, "items": [], "meta": {"backend": "unavailable", "fallback_reason": "elasticsearch_not_configured"}}
    normalized_limit = max(1, min(int(limit or 80), 200))
    try:
        if chapter_id:
            current_node_ids, current_context, current_total = _teacher_es_hits_for_scope(
                client=client,
                query=query,
                chapter_id=chapter_id,
                status_filter=normalized_filter,
                limit=normalized_limit,
                scope="current_chapter",
            )
            other_node_ids, other_context, other_total = _teacher_es_hits_for_scope(
                client=client,
                query=query,
                exclude_chapter_id=chapter_id,
                status_filter=normalized_filter,
                limit=normalized_limit,
                scope="other_chapter",
            )
            scope_totals = {"current_chapter": current_total, "other_chapter": other_total}
            scoped_hits = [(current_node_ids, current_context), (other_node_ids, other_context)]
        else:
            all_node_ids, all_context, all_total = _teacher_es_hits_for_scope(
                client=client,
                query=query,
                status_filter=normalized_filter,
                limit=normalized_limit,
                scope="all",
            )
            scope_totals = {"all": all_total}
            scoped_hits = [(all_node_ids, all_context)]
    except Exception as exc:  # noqa: BLE001 - search endpoint degrades to Postgres with explicit metadata.
        if settings.teacher_catalog_search_local_fallback:
            return _postgres_fallback_search(
                query=query,
                chapter_id=chapter_id,
                status_filter=normalized_filter,
                limit=limit,
                fallback_reason=f"elasticsearch_error:{exc.__class__.__name__}",
            )
        raise
    hit_node_ids: list[str] = []
    hit_context: dict[str, dict[str, Any]] = {}
    for scoped_node_ids, scoped_context in scoped_hits:
        for node_id in scoped_node_ids:
            if node_id in hit_context:
                continue
            hit_node_ids.append(node_id)
            hit_context[node_id] = scoped_context[node_id]
    with db_session() as session:
        items = _cards_for_node_ids(session, hit_node_ids, hit_context)
    total = sum(scope_totals.values())
    scope_counts = _search_scope_counts(items)
    return {
        "query": query,
        "items": items,
        "meta": {
            "backend": "elasticsearch",
            "fallback_reason": None,
            "index": client.index,
            "mapping_version": TEACHER_CATALOG_SEARCH_INDEX_MAPPING_VERSION,
            "synonyms_active": True,
            "chemistry_recall_active": True,
            "status_filter": normalized_filter,
            "chapter_id": chapter_id,
            "total": total,
            "returned": len(items),
            "stale_hit_count": max(len(hit_node_ids) - len(items), 0),
            "limited": total > len(items),
            "scope_counts": scope_counts,
            "scope_totals": scope_totals,
            "cross_chapter_enabled": bool(chapter_id),
        },
    }


def teacher_catalog_search_documents(session: Any, *, chapter_id: str | None = None) -> list[dict[str, Any]]:
    filters = ["n.status <> 'archived'"]
    params: dict[str, Any] = {}
    if chapter_id:
        filters.append("n.chapter_id = :chapter_id")
        params["chapter_id"] = chapter_id
    node_ids = (
        session.execute(
            text(
                f"""
                SELECT n.id
                FROM experiment_catalog_nodes n
                WHERE {" AND ".join(filters)}
                ORDER BY n.chapter_id, n.parent_id NULLS FIRST, n.display_order, n.id
                """
            ),
            params,
        )
        .scalars()
        .all()
    )
    documents: list[dict[str, Any]] = []
    for node_id in node_ids:
        document = teacher_search_document_for_node(session, node_id=str(node_id))
        if document:
            documents.append(document)
    return documents


def teacher_catalog_search_index_diagnostics() -> dict[str, Any]:
    settings = get_settings()
    status_rows: list[dict[str, Any]] = []
    failed_rows: list[dict[str, Any]] = []
    active_node_count = 0
    migration_available = True
    postgres_error: str | None = None
    with db_session() as session:
        active_node_count = int(
            session.execute(text("SELECT COUNT(*) FROM experiment_catalog_nodes WHERE status <> 'archived'")).scalar_one() or 0
        )
        try:
            status_rows = [
                dict(row)
                for row in session.execute(
                    text(
                        """
                        SELECT sync_status, COUNT(*) AS count
                        FROM experiment_catalog_teacher_search_index_state
                        GROUP BY sync_status
                        """
                    )
                )
                .mappings()
                .all()
            ]
            failed_rows = [
                dict(row)
                for row in session.execute(
                    text(
                        """
                        SELECT node_id, document_id, desired_action, sync_status,
                               attempts, last_error, updated_at
                        FROM experiment_catalog_teacher_search_index_state
                        WHERE sync_status IN ('failed', 'pending', 'unavailable')
                        ORDER BY updated_at DESC
                        LIMIT 20
                        """
                    )
                )
                .mappings()
                .all()
            ]
        except Exception as exc:  # noqa: BLE001 - diagnostics should report missing migrations instead of crashing.
            migration_available = False
            postgres_error = str(exc)
    client = configured_teacher_search_client()
    es: dict[str, Any] = {"configured": client is not None}
    if client is not None:
        try:
            es["health"] = client.health()
            es["document_count"] = client.request("GET", f"/{client.index}/_count").get("count")
            mapping_payload = client.request("GET", f"/{client.index}/_mapping")
            mapping = mapping_payload.get(client.index, {}).get("mappings", {})
            properties = mapping.get("properties", {})
            es["mapping"] = {
                "version": (mapping.get("_meta") or {}).get("mapping_version"),
                "desired_version": TEACHER_CATALOG_SEARCH_INDEX_MAPPING_VERSION,
                "field_count": len(properties),
                "chemistry_fields_present": {
                    field: field in properties
                    for field in [
                        "formulae",
                        "title_formulae",
                        "title_formula_pairs",
                        "aliases",
                        "reactants",
                        "products",
                        "participants",
                        "equation_formula_pairs",
                        "equation_rows",
                        "reagent_aliases",
                        "condition_tags",
                        "phenomenon_tags",
                        "property_tags",
                    ]
                },
            }
        except Exception as exc:  # noqa: BLE001 - diagnostics are best-effort.
            es["error"] = str(exc)
    return {
        "settings": {
            "enabled": settings.teacher_catalog_search_enabled,
            "backend": settings.teacher_catalog_search_backend,
            "index": settings.teacher_catalog_search_index,
            "desired_mapping_version": TEACHER_CATALOG_SEARCH_INDEX_MAPPING_VERSION,
            "analyzer": settings.teacher_catalog_search_analyzer,
            "local_fallback": settings.teacher_catalog_search_local_fallback,
            "analyzer_assets": video_library_analyzer_assets(),
        },
        "postgres": {
            "migration_available": migration_available,
            "error": postgres_error,
            "active_catalog_node_count": active_node_count,
            "sync_status_counts": {str(row["sync_status"]): int(row["count"]) for row in status_rows},
            "retryable_rows": failed_rows,
        },
        "elasticsearch": es,
    }
