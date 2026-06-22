from __future__ import annotations

import json
from typing import Any

import pytest

from server.app.domains.questions import bank as question_bank_domain
from server.app.domains.catalog_tree import catalog_seed as catalog_seed_domain
from server.app.domains.catalog_tree.catalog_seed import (
    CANONICAL_POINT_GROUPS_SEED_PATH,
    import_catalog_seed,
    load_catalog_seed,
    load_canonical_point_seed,
    load_point_content_seed,
    reset_legacy_experiment_seed_data,
    validate_catalog_seed,
)
from server.app.domains.questions.generation import _catalog_node_evidence_ready
from server.app.domains.video_library.search import _build_documents
from scripts.generate_experiment_catalog_seed import ExampleMapping, _build_semantic_mapping_report


def test_catalog_outline_seed_matches_required_counts_and_corrected_siblings() -> None:
    nodes = load_catalog_seed()
    point_content = load_point_content_seed()

    result = validate_catalog_seed(nodes, point_content)

    assert result["ok"] is True
    assert result["counts"]["total_nodes"] == 569
    assert result["counts"]["directory_nodes"] == 176
    assert result["counts"]["point_nodes"] == 393
    assert result["counts"]["point_placements"] == 393
    assert result["counts"]["canonical_points"] == 357
    assert result["counts"]["duplicate_group_count"] == 32
    assert result["counts"]["duplicate_placement_surplus"] == 36
    assert result["counts"]["chapter_21_nodes"] == 0
    assert result["counts"]["point_content_records"] == 76
    assert result["counts"]["equation_content_records"] == 71
    assert result["counts"]["text_content_records"] == 5
    assert result["counts"]["reaction_equation_rows"] == 122
    assert result["counts"]["unique_target_seed_keys"] == 76
    assert result["counts"]["unique_target_canonical_point_ids"] == 76
    assert result["counts"]["semantic_mapped_records"] == 76
    assert result["counts"]["user_kept_source_records"] == 3
    assert result["counts"]["researched_update_records"] == 7
    assert result["corrected_hypochlorite_points"] == ["NaClO + MnSO₄", "NaClO + 品红溶液"]
    assert result["corrected_sample_wording"] == "NaClO + 品红溶液"
    assert all(record.get("semantic_mapping", {}).get("mapping_status") == "matched" for record in point_content)
    assert all(record["reaction_equations"] for record in point_content if record["principle_mode"] == "equation")
    assert all(not record["reaction_equations"] for record in point_content if record["principle_mode"] == "text")


def test_catalog_seed_reviewed_duplicate_groups_share_canonical_points() -> None:
    canonical_points = load_canonical_point_seed()
    grouping_seed = json.loads(CANONICAL_POINT_GROUPS_SEED_PATH.read_text(encoding="utf-8-sig"))
    nodes = [node for node in load_catalog_seed() if node["node_kind"] == "point"]
    by_title: dict[str, list[dict[str, Any]]] = {}
    for node in nodes:
        by_title.setdefault(node["title"], []).append(node)

    assert grouping_seed["counts"]["canonical_points"] == 357
    assert grouping_seed["counts"]["duplicate_group_count"] == 32
    assert grouping_seed["counts"]["ambiguous_duplicate_count"] == 0
    assert len(canonical_points) == 357

    reviewed_groups = {group["title"]: group for group in grouping_seed["groups"]}
    assert reviewed_groups["Na2SiO3 + CO2"]["placement_count"] == 2
    assert reviewed_groups["Al2(SO4)3 + NH3·H2O + NaOH"]["placement_count"] == 4
    assert reviewed_groups["BeSO4 + NH3·H2O + NaOH"]["placement_count"] == 4

    for title in ["Na2SiO3 + CO2", "Al2(SO4)3 + NH3·H2O + NaOH", "BeSO4 + NH3·H2O + NaOH"]:
        rows = by_title[title]
        assert len(rows) == reviewed_groups[title]["placement_count"]
        assert {row["canonical_point_id"] for row in rows} == {reviewed_groups[title]["canonical_point_id"]}

    hypochlorite_rows = by_title["NaClO + MnSO₄"] + by_title["NaClO + 品红溶液"]
    assert len(hypochlorite_rows) == 2
    assert len({row["canonical_point_id"] for row in hypochlorite_rows}) == 2


def test_catalog_seed_validation_rejects_legacy_identity_and_missing_mapping_report() -> None:
    nodes = load_catalog_seed()
    point_content = load_point_content_seed()
    broken = dict(point_content[0])
    broken.pop("semantic_mapping", None)
    broken["experiment_id"] = "EXP_LEGACY"
    broken["point_key"] = "legacy-point"

    result = validate_catalog_seed(nodes, [broken, *point_content[1:]])

    assert result["ok"] is False
    assert any("legacy identity keys are not allowed" in error for error in result["errors"])
    assert any("semantic_mapping report is required" in error for error in result["errors"])


def test_import_catalog_seed_preserves_equation_mode_and_writes_reaction_rows(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResult:
        rowcount = 1

    class FakeSession:
        def __init__(self) -> None:
            self.point_content_params: list[dict[str, Any]] = []

        def execute(self, statement: Any, params: dict[str, Any] | None = None) -> FakeResult:
            sql = str(statement)
            if "INSERT INTO experiment_catalog_point_content" in sql and params:
                self.point_content_params.append(dict(params))
            return FakeResult()

    replace_calls: list[dict[str, Any]] = []

    def fake_replace_reaction_equations(
        session: Any,
        *,
        node_id: str,
        canonical_point_id: str | None = None,
        equations: list[dict[str, Any]],
    ) -> None:
        replace_calls.append({"node_id": node_id, "canonical_point_id": canonical_point_id, "equations": equations})

    monkeypatch.setattr(catalog_seed_domain, "replace_reaction_equations", fake_replace_reaction_equations)
    session = FakeSession()

    result = import_catalog_seed(session, reset=False)

    assert result["point_content_records"] == 76
    assert result["reaction_equation_rows"] == 122
    assert len(session.point_content_params) == 76
    assert sum(1 for params in session.point_content_params if params["principle_mode"] == "equation") == 71
    assert sum(1 for params in session.point_content_params if params["principle_mode"] == "text") == 5
    assert all(params["principle_equation"] for params in session.point_content_params if params["principle_mode"] == "equation")
    assert all(params["principle_text"] for params in session.point_content_params if params["principle_mode"] == "text")
    assert len(replace_calls) == 71
    assert sum(len(call["equations"]) for call in replace_calls) == 122


def test_ambiguous_sample_mapping_requires_reviewed_override() -> None:
    nodes = [
        {
            "seed_key": "cat-a",
            "node_kind": "point",
            "title": "NaClO + 品红溶液",
            "path_titles": ["第13章 卤族元素", "次氯酸盐的氧化性", "NaClO + 品红溶液"],
        },
        {
            "seed_key": "cat-b",
            "node_kind": "point",
            "title": "NaClO + 品红溶液",
            "path_titles": ["第13章 卤族元素", "候选复核", "NaClO + 品红溶液"],
        },
    ]
    mapping = ExampleMapping(
        21,
        "NaClO + 品红溶液",
        ("第13章 卤族元素", "次氯酸盐的氧化性", "NaClO + 品红溶液"),
    )
    block = {
        "example_title_from_source": "NaClO + 品红溶液",
        "principle_text": ["NaClO + 品红溶液"],
        "phenomenon_explanation": [],
        "safety_note": [],
    }

    with pytest.raises(ValueError, match="needs a reviewed override"):
        _build_semantic_mapping_report(
            nodes=nodes,
            mapping=mapping,
            block=block,
            target=nodes[0],
            allow_reviewed_override=False,
        )

    report = _build_semantic_mapping_report(
        nodes=nodes,
        mapping=mapping,
        block=block,
        target=nodes[0],
        allow_reviewed_override=True,
    )

    assert report["review_status"] == "reviewed_override"
    assert report["override"]["type"] == "reviewed_target_path"


def test_catalog_outline_reset_deletes_retired_seed_tables_but_preserves_canonical_corpus() -> None:
    class FakeResult:
        rowcount = 0

    class FakeSession:
        def __init__(self) -> None:
            self.sql: list[str] = []

        def execute(self, statement: Any) -> FakeResult:
            self.sql.append(str(statement))
            return FakeResult()

    session = FakeSession()

    reset_legacy_experiment_seed_data(session)

    joined_sql = "\n".join(session.sql)
    assert "experiment_questions" in joined_sql
    assert "experiment_question_banks" in joined_sql
    assert "experiment_video_point_evidence" in joined_sql
    assert "experiment_video_points" in joined_sql
    assert "experiment_catalog_nodes" in joined_sql
    assert "source_chunks" not in joined_sql
    assert "chunk_embeddings" not in joined_sql
    assert "app_users" not in joined_sql
    assert "media_assets" not in joined_sql


def test_question_generation_requires_fresh_catalog_node_evidence() -> None:
    legacy_package = {
        "mode": "hybrid_bge_rag",
        "source_refs": [{"chunk_id": "chunk-1"}],
        "target_point_node_ids": ["cat-outline-point-1"],
    }
    catalog_package = {
        "mode": "catalog_node_evidence",
        "evidence_contract": "catalog_node_evidence",
        "source_mode": "static_catalog_node_evidence",
        "source_refs": [{"chunk_id": "chunk-1"}],
        "target_point_node_ids": ["cat-outline-point-1"],
    }
    dynamic_package = {
        "mode": "catalog_node_evidence",
        "evidence_contract": "catalog_node_evidence",
        "source_mode": "dynamic_rag_catalog_node_evidence",
        "source_refs": [{"chunk_id": "chunk-2"}],
        "target_point_node_ids": ["cat-outline-point-1"],
    }
    stale_package = {
        **catalog_package,
        "freshness_status": "stale",
        "evidence_status": "stale",
    }

    assert _catalog_node_evidence_ready(legacy_package, target_point_node_ids=["cat-outline-point-1"]) is False
    assert _catalog_node_evidence_ready(catalog_package, target_point_node_ids=["cat-outline-point-2"]) is False
    assert _catalog_node_evidence_ready(catalog_package, target_point_node_ids=["cat-outline-point-1"]) is True
    assert _catalog_node_evidence_ready(dynamic_package, target_point_node_ids=["cat-outline-point-1"]) is True
    assert _catalog_node_evidence_ready(stale_package, target_point_node_ids=["cat-outline-point-1"]) is False


def test_question_bank_empty_baseline_response_marks_retired_seed(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeResult:
        def mappings(self) -> FakeResult:
            return self

        def all(self) -> list[dict[str, Any]]:
            return []

    class FakeSession:
        def execute(self, statement: Any) -> FakeResult:
            return FakeResult()

    class FakeDbSession:
        def __enter__(self) -> FakeSession:
            return FakeSession()

        def __exit__(self, *_args: Any) -> None:
            return None

    monkeypatch.setattr(
        question_bank_domain,
        "_list_experiments",
        lambda chapter_id=None: [{"id": "EXP_EMPTY", "code": "E-0", "title": "Empty bank experiment"}],
    )
    monkeypatch.setattr(question_bank_domain, "db_session", lambda: FakeDbSession())

    response = question_bank_domain.list_question_banks()

    assert response["items"][0]["banks"] == []
    assert response["baseline"]["question_bank_empty"] is True
    assert response["baseline"]["retired_legacy_seed"] is True
    assert response["baseline"]["requires_catalog_node_evidence"] is True
    assert response["baseline"]["regeneration_audit"]["catalog_point_count"] == 0
    assert response["regeneration_audit"]["unresolved_point_count"] == 0


def test_question_bank_regeneration_audit_reports_catalog_node_coverage() -> None:
    class FakeResult:
        def __init__(self, rows: list[dict[str, Any]]) -> None:
            self._rows = rows

        def mappings(self) -> FakeResult:
            return self

        def all(self) -> list[dict[str, Any]]:
            return self._rows

    class FakeSession:
        def execute(self, statement: Any, _params: dict[str, Any] | None = None) -> FakeResult:
            sql = str(statement)
            if "FROM experiment_catalog_nodes n" in sql:
                return FakeResult(
                    [
                        {
                            "point_node_id": "cat-point-1",
                            "chapter_id": "CH13",
                            "point_title": "Point 1",
                            "directory_id": "cat-dir-1",
                            "directory_title": "Directory 1",
                            "evidence_status": "succeeded",
                            "evidence_source_mode": "dynamic_rag_catalog_node_evidence",
                        },
                        {
                            "point_node_id": "cat-point-2",
                            "chapter_id": "CH13",
                            "point_title": "Point 2",
                            "directory_id": "cat-dir-1",
                            "directory_title": "Directory 1",
                            "evidence_status": "missing",
                            "evidence_source_mode": "none",
                        },
                    ]
                )
            if "FROM experiment_questions" in sql:
                return FakeResult(
                    [
                        {
                            "question_type": "single_choice",
                            "status": "published",
                            "primary_point_node_ids": ["cat-point-1"],
                            "metadata": {
                                "source_audit": {
                                    "evidence_contract": "catalog_node_evidence",
                                    "evidence_source": "dynamic_rag_catalog_node_evidence",
                                }
                            },
                        }
                    ]
                )
            if "FROM experiment_question_drafts" in sql:
                return FakeResult(
                    [
                        {
                            "status": "rejected",
                            "payload": {
                                "question_type": "true_false",
                                "primary_point_node_ids": ["cat-point-2"],
                                "metadata": {"primary_point_node_ids": ["cat-point-2"]},
                            },
                            "validation_errors": [],
                        }
                    ]
                )
            if "FROM experiment_question_workbench_candidates" in sql:
                return FakeResult([{"status": "published", "payload": {}, "validation_errors": []}])
            return FakeResult([])

    audit = question_bank_domain._question_generation_audit(FakeSession())

    assert audit["catalog_point_count"] == 2
    assert audit["covered_point_count"] == 1
    assert audit["unresolved_point_count"] == 1
    assert audit["question_type_counts"]["single_choice"] == 1
    assert audit["draft_question_type_counts"]["true_false"] == 1
    assert audit["evidence_source_counts"]["dynamic_rag_catalog_node_evidence"] == 1
    assert audit["accepted_draft_count"] == 1
    assert audit["rejected_draft_count"] == 1
    assert audit["by_chapter"][0]["id"] == "CH13"
    assert audit["by_directory"][0]["id"] == "cat-dir-1"
    assert audit["unresolved_points"][0]["point_node_id"] == "cat-point-2"


def test_point_content_seed_builds_search_documents_without_flattening_equations() -> None:
    nodes = {node["seed_key"]: node for node in load_catalog_seed()}
    point_content = load_point_content_seed()
    point_rows = []
    for record in point_content:
        target = nodes[record["target_seed_key"]]
        path_titles = list(record["target_path_titles"])
        principle_equation = "\n".join(row["raw_text"] for row in record["reaction_equations"])
        point_rows.append(
            {
                "node_id": record["target_seed_key"],
                "placement_node_id": record["target_seed_key"],
                "canonical_point_id": record["target_canonical_point_id"],
                "chapter_id": target["chapter_id"],
                "chapter_title": path_titles[0],
                "node_title": path_titles[-1],
                "catalog_path": path_titles,
                "point_title": record["point_title"],
                "principle_mode": record["principle_mode"],
                "principle_text": record["principle_text"],
                "principle_equation": principle_equation if record["principle_mode"] == "equation" else None,
                "phenomenon_explanation": record["phenomenon_explanation"],
                "safety_note": record["safety_note"],
                "directory_context": [{"title": title} for title in path_titles[:-1]],
                "videos": [],
                "related_links": [],
                "content_updated_at": None,
            }
        )

    documents = _build_documents([], [], point_rows=point_rows)
    search_text = "\n".join(document.search_text for document in documents)

    assert len(documents) == 76
    assert all(document.target and document.target.node_id for document in documents)
    assert all(document.target and document.target.placement_node_id for document in documents)
    assert all(document.target and document.target.canonical_point_id for document in documents)
    assert "source_chunks" not in search_text
    assert "experiment_video_point_evidence" not in search_text
    assert any(record["principle_mode"] == "equation" for record in point_content)
    assert any("Cl2 + 2Br-" in document.search_text or "Cl2 + 2 Br-" in document.search_text for document in documents)
    assert any("焰色反应" in document.search_text for document in documents)
