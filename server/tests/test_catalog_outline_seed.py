from __future__ import annotations

from typing import Any

import pytest

from server.app.domains.questions import bank as question_bank_domain
from server.app.domains.catalog_tree.catalog_seed import (
    load_catalog_seed,
    load_point_content_examples,
    reset_legacy_experiment_seed_data,
    validate_catalog_seed,
)
from server.app.domains.questions.generation import _catalog_node_evidence_ready
from server.app.domains.video_library.search import _build_documents
from scripts.generate_experiment_catalog_seed import ExampleMapping, _build_semantic_mapping_report


def test_catalog_outline_seed_matches_required_counts_and_corrected_siblings() -> None:
    nodes = load_catalog_seed()
    examples = load_point_content_examples()

    result = validate_catalog_seed(nodes, examples)

    assert result["ok"] is True
    assert result["counts"]["total_nodes"] == 569
    assert result["counts"]["directory_nodes"] == 176
    assert result["counts"]["point_nodes"] == 393
    assert result["counts"]["chapter_21_nodes"] == 0
    assert result["counts"]["point_content_examples"] == 30
    assert result["counts"]["unique_target_seed_keys"] == 30
    assert result["counts"]["semantic_mapped_examples"] == 30
    assert result["counts"]["corrected_wording_examples"] == 1
    assert result["corrected_hypochlorite_points"] == ["NaClO + MnSO₄", "NaClO + 品红溶液"]
    assert result["corrected_sample_wording"] == "NaClO + 品红溶液"
    assert all(example.get("semantic_mapping", {}).get("top_candidates") for example in examples)
    corrected = next(example for example in examples if example["example_number"] == 21)
    assert corrected["semantic_mapping"]["wording_correction"]["corrected"] == "NaClO + 品红溶液"


def test_catalog_seed_validation_rejects_legacy_identity_and_missing_mapping_report() -> None:
    nodes = load_catalog_seed()
    examples = load_point_content_examples()
    broken = dict(examples[0])
    broken.pop("semantic_mapping", None)
    broken["experiment_id"] = "EXP_LEGACY"
    broken["point_key"] = "legacy-point"

    result = validate_catalog_seed(nodes, [broken, *examples[1:]])

    assert result["ok"] is False
    assert any("legacy identity keys are not allowed" in error for error in result["errors"])
    assert any("semantic_mapping report is required" in error for error in result["errors"])


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
        "source_refs": [{"chunk_id": "chunk-1"}],
        "target_point_node_ids": ["cat-outline-point-1"],
    }

    assert _catalog_node_evidence_ready(legacy_package, target_point_node_ids=["cat-outline-point-1"]) is False
    assert _catalog_node_evidence_ready(catalog_package, target_point_node_ids=["cat-outline-point-2"]) is False
    assert _catalog_node_evidence_ready(catalog_package, target_point_node_ids=["cat-outline-point-1"]) is True


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


def test_thirty_seed_examples_build_search_documents_without_legacy_ai_evidence() -> None:
    nodes = {node["seed_key"]: node for node in load_catalog_seed()}
    examples = load_point_content_examples()
    point_rows = []
    for example in examples:
        target = nodes[example["target_seed_key"]]
        path_titles = list(example["target_path_titles"])
        point_rows.append(
            {
                "node_id": example["target_seed_key"],
                "chapter_id": target["chapter_id"],
                "chapter_title": path_titles[0],
                "node_title": path_titles[-1],
                "catalog_path": path_titles,
                "point_title": path_titles[-1],
                "principle_mode": "text",
                "principle_text": example["principle_text"],
                "principle_equation": None,
                "phenomenon_explanation": example["phenomenon_explanation"],
                "safety_note": example["safety_note"],
                "directory_context": [{"title": title} for title in path_titles[:-1]],
                "videos": [],
                "related_links": [],
                "content_updated_at": None,
            }
        )

    documents = _build_documents([], [], point_rows=point_rows)
    search_text = "\n".join(document.search_text for document in documents)

    assert len(documents) == 30
    assert all(document.target and document.target.node_id for document in documents)
    assert "source_chunks" not in search_text
    assert "experiment_video_point_evidence" not in search_text
    assert any("焰色反应" in document.search_text for document in documents)
