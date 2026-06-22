from __future__ import annotations

import inspect
from typing import Any

from server.app.domains.catalog_tree import search_documents, teacher_search


def test_teacher_search_mapping_uses_separate_admin_index_contract() -> None:
    mapping = teacher_search.teacher_catalog_search_index_mapping(analyzer="ik_max_word")

    assert mapping["mappings"]["_meta"]["mapping_version"] == teacher_search.TEACHER_CATALOG_SEARCH_INDEX_MAPPING_VERSION
    assert mapping["mappings"]["_meta"]["student_index_boundary"] == "separate-index-no-student-documents"
    filters = mapping["settings"]["analysis"]["filter"]
    assert filters["chemistry_stop"]["stopwords_path"] == "analysis/chemistry_stopwords.txt"
    assert filters["chemistry_synonyms"]["synonyms_path"] == "analysis/chemistry_synonyms.txt"
    properties = mapping["mappings"]["properties"]
    for field in [
        "teacher_note",
        "point_teacher_note",
        "legacy_experiment_ids",
        "legacy_point_keys",
        "formulae",
        "reactants",
        "products",
        "participants",
        "condition_tags",
        "node_status",
    ]:
        assert field in properties


def test_teacher_search_query_plans_chapter_status_and_structured_chemistry_routes() -> None:
    payload = teacher_search.build_teacher_catalog_search_payload(
        query="SO3^2- AgNO3",
        chapter_id="chapter-13",
        status_filter="missing_principle",
        limit=30,
    )

    filters = payload["query"]["bool"]["filter"]
    assert {"term": {"chapter_id": "chapter-13"}} in filters
    assert any(
        "node_status.core_readiness.descendant_missing_field_counts.principle" in str(filter_clause)
        for filter_clause in filters
    )
    should = payload["query"]["bool"]["should"]
    assert any(clause.get("multi_match", {}).get("_name") == "chemistry_synonym_text" for clause in should)
    assert any("structured_formulae" in str(clause) for clause in should)
    assert payload["size"] == 30


def test_teacher_status_filter_matches_directory_descendant_counts() -> None:
    payload = teacher_search.build_teacher_catalog_search_payload(
        query="KI",
        chapter_id=None,
        status_filter="published",
        limit=10,
    )

    filters = payload["query"]["bool"]["filter"]
    assert any("node_status.core_readiness.descendant_status_counts.published" in str(filter_clause) for filter_clause in filters)


def test_teacher_search_query_can_exclude_current_chapter_for_cross_chapter_bucket() -> None:
    payload = teacher_search.build_teacher_catalog_search_payload(
        query="H2O",
        exclude_chapter_id="chapter-13",
        status_filter="all",
        limit=10,
    )

    filters = payload["query"]["bool"]["filter"]
    assert {"term": {"chapter_id": "chapter-13"}} not in filters
    assert any("must_not" in str(filter_clause) and "chapter-13" in str(filter_clause) for filter_clause in filters)


def test_teacher_search_document_includes_teacher_only_draft_and_legacy_fields(monkeypatch) -> None:
    node = {
        "node_id": "cat-point-1",
        "node_kind": "point",
        "chapter_id": "chapter-13",
        "parent_id": "cat-dir-1",
        "status": "draft",
        "title": "NaClO + MnSO4",
        "summary": "teacher summary",
        "teacher_note": "teacher-only node note",
        "canonical_point_id": "canon-1",
        "updated_at": "2026-06-22T00:00:00",
    }
    content = {
        "content_status": "draft",
        "point_title": "NaClO + MnSO4",
        "teacher_note": "teacher-only point note",
        "principle_mode": "equation",
        "principle_equation": "Mn2+ + ClO- + 2OH- -> MnO2 + Cl- + H2O",
        "reaction_equations": [
            {
                "validation_status": "valid",
                "canonical_display": "Mn2+ + ClO- + 2OH- -> MnO2 + Cl- + H2O",
                "raw_text": "Mn2+ + ClO- + 2OH- -> MnO2 + Cl- + H2O",
                "formulae": ["Mn2+", "ClO-", "OH-", "MnO2", "Cl-", "H2O"],
                "reactants": ["Mn2+", "ClO-", "OH-"],
                "products": ["MnO2", "Cl-", "H2O"],
                "participants": {"all": ["Mn2+", "ClO-", "OH-", "MnO2", "Cl-", "H2O"]},
                "aliases": ["次氯酸根", "二氧化锰"],
                "condition_tags": ["碱性"],
                "reaction_features": ["沉淀"],
            }
        ],
        "phenomenon_explanation": "生成黑色 MnO2 沉淀。",
        "safety_note": "NaClO 有腐蚀性。",
        "updated_at": "2026-06-22T01:00:00",
    }
    status_summary = {
        "primary_state": "needs_video",
        "core_readiness": {
            "missing_field_keys": [],
            "descendant_status_counts": {},
            "descendant_missing_field_counts": {},
        },
    }

    monkeypatch.setattr(teacher_search, "get_node", lambda *_args, **_kwargs: node)
    monkeypatch.setattr(teacher_search, "get_content", lambda *_args, **_kwargs: content)
    monkeypatch.setattr(
        teacher_search,
        "breadcrumbs",
        lambda *_args, **_kwargs: [
            {"node_id": "cat-dir-1", "title": "卤素含氧酸盐的氧化性", "node_kind": "directory"},
            {"node_id": "cat-point-1", "title": "NaClO + MnSO4", "node_kind": "point"},
        ],
    )
    monkeypatch.setattr(teacher_search, "catalog_path_titles_with_chapter", lambda *_args, **_kwargs: ["第 13 章 卤族元素", "卤素含氧酸盐的氧化性", "NaClO + MnSO4"])
    monkeypatch.setattr(teacher_search, "catalog_node_status_summary", lambda *_args, **_kwargs: status_summary)
    monkeypatch.setattr(
        teacher_search,
        "_legacy_identity_values",
        lambda *_args, **_kwargs: {
            "legacy_experiment_ids": ["legacy-exp-001"],
            "legacy_point_keys": ["legacy-point-a"],
            "legacy_identities": ["legacy-exp-001", "legacy-point-a"],
        },
    )

    document = teacher_search.teacher_search_document_for_node(object(), node_id="cat-point-1")

    assert document is not None
    assert document["result_type"] == "teacher_catalog_node"
    assert document["content_status"] == "draft"
    assert document["teacher_note"] == "teacher-only node note"
    assert document["point_teacher_note"] == "teacher-only point note"
    assert document["legacy_experiment_ids"] == ["legacy-exp-001"]
    assert document["legacy_point_keys"] == ["legacy-point-a"]
    assert "teacher-only point note" in document["search_text"]
    assert "Mn2+" in document["formulae"]
    assert "ClO-" in document["reactants"]
    assert "MnO2" in document["products"]
    assert document["target"]["route"] == "/admin/catalog?node=cat-point-1"


def test_student_search_document_source_excludes_teacher_only_fields() -> None:
    source = inspect.getsource(search_documents.student_search_document_for_node)

    assert "teacher_note" not in source
    assert "legacy_experiment_ids" not in source
    assert "legacy_point_keys" not in source


def test_teacher_search_falls_back_with_explicit_metadata(monkeypatch) -> None:
    calls: list[dict[str, Any]] = []
    settings = type(
        "Settings",
        (),
        {
            "teacher_catalog_search_enabled": False,
            "teacher_catalog_search_backend": "disabled",
            "teacher_catalog_search_local_fallback": True,
        },
    )()

    def fake_fallback(**kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs)
        return {"items": [], "meta": {"backend": "postgres_fallback", "fallback_reason": kwargs["fallback_reason"]}}

    monkeypatch.setattr(teacher_search, "get_settings", lambda: settings)
    monkeypatch.setattr(teacher_search, "_postgres_fallback_search", fake_fallback)

    result = teacher_search.search_teacher_catalog_nodes(
        query="NaClO",
        chapter_id="chapter-13",
        status_filter="needs_content",
        limit=20,
    )

    assert result["meta"]["backend"] == "postgres_fallback"
    assert result["meta"]["fallback_reason"] == "teacher_search_disabled"
    assert calls == [
        {
            "query": "NaClO",
            "chapter_id": "chapter-13",
            "status_filter": "needs_content",
            "limit": 20,
            "fallback_reason": "teacher_search_disabled",
        }
    ]
