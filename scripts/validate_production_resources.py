from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_PATH = ROOT / "data" / "seed" / "manifests" / "core_resources.json"

EXPECTED_DATABASE_COUNTS = {
    "formal_experiments_active": 77,
    "chapters": 11,
    "knowledge_units": 133,
    "knowledge_points": 385,
    "experiment_catalog_nodes": 569,
    "experiment_catalog_directory_nodes": 176,
    "experiment_catalog_point_nodes": 393,
    "experiment_catalog_point_content_records": 76,
    "experiment_question_banks": 0,
    "experiment_questions": 0,
    "source_documents": 2,
    "source_chunks": 3637,
    "chunk_embeddings": 3637,
    "published_catalog_point_content_min": 76,
    "catalog_point_related_links_min": 0,
    "point_evidence_bindings_with_node": 0,
    "catalog_point_textbook_evidence_states": 1,
    "catalog_point_textbook_evidence_bindings": 9,
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _jsonl_count(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig") as handle:
        return sum(1 for line in handle if line.strip())


def _text_line_count(path: Path) -> int:
    return sum(1 for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip())


def _formal_experiment_count(path: Path) -> int:
    return len(_json(path).get("experiments") or [])


def _json_list_count(path: Path) -> int:
    data = _json(path)
    if not isinstance(data, list):
        raise ValueError(f"{path} is not a JSON list")
    return len(data)


def _reviewed_curriculum_count(path: Path) -> dict[str, int]:
    data = _json(path)
    return {
        "chapters": len(data.get("chapters") or []),
        "knowledge_units": len(data.get("knowledge_units") or []),
        "knowledge_points": len(data.get("knowledge_points") or []),
    }


def _point_inventory_count(path: Path) -> dict[str, int]:
    data = _json(path)
    summary = data.get("summary") or {}
    return {
        "experiments": int(summary.get("experiment_count") or len(data.get("experiments") or [])),
        "points": int(summary.get("total_video_points") or 0),
    }


def _catalog_tree_count(path: Path) -> dict[str, int]:
    data = _json(path)
    nodes = data.get("nodes") or []
    if not isinstance(nodes, list):
        raise ValueError(f"{path} nodes is not a JSON list")
    return {
        "total_nodes": len(nodes),
        "directory_nodes": sum(1 for node in nodes if isinstance(node, dict) and node.get("node_kind") == "directory"),
        "point_nodes": sum(1 for node in nodes if isinstance(node, dict) and node.get("node_kind") == "point"),
        "chapter_21_nodes": sum(1 for node in nodes if isinstance(node, dict) and int(node.get("chapter_number") or 0) == 21),
    }


def _catalog_point_content_seed_count(path: Path) -> dict[str, int]:
    data = _json(path)
    records = data.get("records") or []
    if not isinstance(records, list):
        raise ValueError(f"{path} records is not a JSON list")
    return {
        "records": len(records),
        "equation_mode_records": sum(1 for item in records if isinstance(item, dict) and item.get("principle_mode") == "equation"),
        "text_mode_records": sum(1 for item in records if isinstance(item, dict) and item.get("principle_mode") == "text"),
        "reaction_equation_rows": sum(
            len(item.get("reaction_equations") or []) for item in records if isinstance(item, dict)
        ),
        "unique_target_seed_keys": len({str(item.get("target_seed_key") or "") for item in records if isinstance(item, dict)}),
        "semantic_mapped_records": sum(
            1 for item in records if isinstance(item, dict) and isinstance(item.get("semantic_mapping"), dict)
        ),
    }


def _catalog_point_textbook_evidence_seed_count(path: Path) -> dict[str, int]:
    data = _json(path)
    states = data.get("states") or []
    bindings = data.get("bindings") or []
    if not isinstance(states, list) or not isinstance(bindings, list):
        raise ValueError(f"{path} must contain states and bindings lists")
    return {
        "states": len(states),
        "bindings": len(bindings),
        "unique_nodes": len({str(item.get("node_id") or "") for item in states if isinstance(item, dict)}),
        "unique_chunks": len({str(item.get("chunk_id") or "") for item in bindings if isinstance(item, dict)}),
    }


def _catalog_validation_report_count(path: Path) -> dict[str, int | bool]:
    data = _json(path)
    counts = data.get("counts") or {}
    return {
        "ok": bool(data.get("ok")),
        "total_nodes": int(counts.get("total_nodes") or 0),
        "directory_nodes": int(counts.get("directory_nodes") or 0),
        "point_nodes": int(counts.get("point_nodes") or 0),
        "point_content_records": int(counts.get("point_content_records") or 0),
        "equation_content_records": int(counts.get("equation_content_records") or 0),
        "text_content_records": int(counts.get("text_content_records") or 0),
        "reaction_equation_rows": int(counts.get("reaction_equation_rows") or 0),
        "semantic_mapped_records": int(counts.get("semantic_mapped_records") or 0),
    }


def _question_bank_count(path: Path) -> dict[str, int]:
    data = _json(path)
    experiments = data.get("experiments") or []
    return {
        "experiments": len(experiments),
        "questions": sum(len(experiment.get("questions") or []) for experiment in experiments),
    }


def _seed_experiment_chapter_ids(experiment: dict[str, Any]) -> list[str]:
    chapter_ids: list[str] = []
    seen: set[str] = set()
    for binding in experiment.get("chapter_bindings") or []:
        if not isinstance(binding, dict):
            continue
        chapter_id = str(binding.get("chapter_id") or "").strip()
        if chapter_id and chapter_id not in seen:
            chapter_ids.append(chapter_id)
            seen.add(chapter_id)
    return chapter_ids


def _student_learning_experiment_coverage_counts(profiles: list[dict[str, Any]]) -> dict[str, int]:
    formal_experiments = _json(ROOT / "data" / "seed" / "formal_experiments.json").get("experiments") or []
    experiments = [
        experiment
        for experiment in formal_experiments
        if isinstance(experiment, dict) and str(experiment.get("status") or "published") == "published"
    ]
    enabled = [profile for profile in profiles if isinstance(profile, dict) and profile.get("enabled", True)]
    chapter_to_profile: dict[str, str] = {}
    profile_counts: dict[str, int] = defaultdict(int)
    covered_experiment_ids: set[str] = set()
    multi_profile_experiment_count = 0
    errors: list[str] = []

    for profile in enabled:
        profile_id = str(profile.get("profile_id") or "<missing>")
        chapter_id = str(profile.get("chapter_id") or "").strip()
        if not chapter_id:
            errors.append(f"{profile_id}: missing chapter_id")
            continue
        if chapter_id in chapter_to_profile:
            errors.append(f"{profile_id}: duplicate chapter_id {chapter_id}")
        chapter_to_profile[chapter_id] = profile_id
        profile_counts.setdefault(profile_id, 0)

    for experiment in experiments:
        experiment_id = str(experiment.get("id") or experiment.get("code") or "<missing>")
        profile_ids = [
            chapter_to_profile[chapter_id]
            for chapter_id in _seed_experiment_chapter_ids(experiment)
            if chapter_id in chapter_to_profile
        ]
        if not profile_ids:
            errors.append(f"{experiment_id}: no student learning profile covers its chapter bindings")
            continue
        covered_experiment_ids.add(experiment_id)
        if len(set(profile_ids)) > 1:
            multi_profile_experiment_count += 1
        for profile_id in set(profile_ids):
            profile_counts[profile_id] += 1

    profiles_without_experiments = sorted(profile_id for profile_id, count in profile_counts.items() if count == 0)
    for profile_id in profiles_without_experiments:
        errors.append(f"{profile_id}: no formal experiments are bound to this profile chapter")
    if errors:
        raise ValueError("student learning experiment coverage mismatch: " + "; ".join(errors))
    return {
        "published_experiments": len(experiments),
        "covered_experiments": len(covered_experiment_ids),
        "uncovered_experiments": len(experiments) - len(covered_experiment_ids),
        "profiles_without_experiments": len(profiles_without_experiments),
        "multi_profile_experiments": multi_profile_experiment_count,
    }


def _student_learning_profile_count(path: Path) -> dict[str, int]:
    required_cards = {
        "atomic_number",
        "electron_configuration",
        "group",
        "common_valence",
        "elemental_state",
        "redox",
    }
    required_element_facts = {
        "atomic_number",
        "electron_configuration",
        "group_label",
        "common_valence",
        "state",
        "redox_tendency",
    }
    required_element_card_fields = {
        "card_focus",
        "card_relevance",
        "card_tags",
    }
    required_reference_media = {
        "id",
        "usage",
        "asset_type",
        "source_url",
        "license",
        "attribution",
        "alt_text",
    }
    data = _json(path)
    profiles = data.get("profiles") or []
    if not isinstance(profiles, list):
        raise ValueError(f"{path} profiles is not a JSON list")
    enabled = [profile for profile in profiles if isinstance(profile, dict) and profile.get("enabled", True)]
    for profile in enabled:
        profile_id = profile.get("profile_id") or "<missing>"
        for key in [
            "chapter_id",
            "title",
            "hero",
            "elements",
            "property_cards",
            "family_common_properties",
            "property_sections",
        ]:
            if not profile.get(key):
                raise ValueError(f"{path} profile {profile_id} missing {key}")
        card_keys = {
            str(card.get("key") or "")
            for card in profile.get("property_cards") or []
            if isinstance(card, dict)
        }
        missing = sorted(required_cards - card_keys)
        if missing:
            raise ValueError(f"{path} profile {profile_id} missing property cards: {', '.join(missing)}")
        for element in profile.get("elements") or []:
            if not isinstance(element, dict):
                raise ValueError(f"{path} profile {profile_id} has a non-object element")
            symbol = element.get("symbol") or "<missing>"
            missing_facts = sorted(key for key in required_element_facts if element.get(key) in (None, ""))
            if missing_facts:
                raise ValueError(f"{path} profile {profile_id} element {symbol} missing facts: {', '.join(missing_facts)}")
            missing_card_fields = sorted(
                key for key in required_element_card_fields if element.get(key) in (None, "", [])
            )
            if missing_card_fields:
                raise ValueError(
                    f"{path} profile {profile_id} element {symbol} missing card copy: {', '.join(missing_card_fields)}"
                )
        for media in profile.get("reference_media") or []:
            if not isinstance(media, dict):
                raise ValueError(f"{path} profile {profile_id} has a non-object reference media entry")
            missing_media = sorted(key for key in required_reference_media if not media.get(key))
            if missing_media:
                raise ValueError(f"{path} profile {profile_id} reference media missing: {', '.join(missing_media)}")
    return {
        "profiles": len(profiles),
        "enabled_profiles": len(enabled),
        **_student_learning_experiment_coverage_counts(profiles),
    }


def _embedding_dense_count(path: Path) -> dict[str, int]:
    dense = np.load(path, mmap_mode="r")
    if len(dense.shape) != 2:
        raise ValueError(f"{path} is not a two-dimensional dense embedding matrix")
    return {"rows": int(dense.shape[0]), "dimensions": int(dense.shape[1])}


CountFn = Callable[[Path], int | dict[str, int] | None]


RESOURCE_SPECS: list[dict[str, Any]] = [
    {
        "id": "formal_experiments",
        "role": "Published formal experiment catalog",
        "path": "data/seed/formal_experiments.json",
        "kind": "json",
        "count": _formal_experiment_count,
        "expected_count": 77,
    },
    {
        "id": "knowledge_framework_chapters",
        "role": "Knowledge framework chapter fallback data",
        "path": "data/seed/knowledge_framework/chapters.json",
        "kind": "json",
        "count": _json_list_count,
        "expected_count": 11,
        "source_path": "data/processed/chapters.json",
    },
    {
        "id": "knowledge_framework_units",
        "role": "Knowledge framework unit fallback data",
        "path": "data/seed/knowledge_framework/knowledge_units.json",
        "kind": "json",
        "count": _json_list_count,
        "expected_count": 133,
        "source_path": "data/processed/knowledge_units.json",
    },
    {
        "id": "knowledge_framework_points",
        "role": "Knowledge framework point fallback data",
        "path": "data/seed/knowledge_framework/knowledge_points.json",
        "kind": "json",
        "count": _json_list_count,
        "expected_count": 385,
        "source_path": "data/processed/knowledge_points.json",
    },
    {
        "id": "reviewed_curriculum",
        "role": "Reviewed curriculum source used to publish framework fallback JSON",
        "path": "data/seed/knowledge_framework/reviewed_curriculum.json",
        "kind": "json",
        "count": _reviewed_curriculum_count,
        "expected_counts": {"chapters": 11, "knowledge_units": 133, "knowledge_points": 385},
        "source_path": "data/processed/reviewed_curriculum.json",
    },
    {
        "id": "experiment_catalog_tree",
        "role": "Canonical outline-backed experiment catalog tree seed",
        "path": "data/seed/experiment_catalog/catalog_tree.json",
        "kind": "json",
        "count": _catalog_tree_count,
        "expected_counts": {"total_nodes": 569, "directory_nodes": 176, "point_nodes": 393, "chapter_21_nodes": 0},
        "source_path": "docs/实验目录_整理版.md",
    },
    {
        "id": "experiment_catalog_point_content_seed",
        "role": "Reviewed catalog point-content seed with structured reaction equations for ES/search tests",
        "path": "data/seed/experiment_catalog/point_content_seed.json",
        "kind": "json",
        "count": _catalog_point_content_seed_count,
        "expected_counts": {
            "records": 76,
            "equation_mode_records": 71,
            "text_mode_records": 5,
            "reaction_equation_rows": 122,
            "unique_target_seed_keys": 76,
            "semantic_mapped_records": 76,
        },
        "source_path": "data/seed/experiment_catalog/normalized_three_element_candidates.md",
    },
    {
        "id": "experiment_catalog_point_textbook_evidence_seed",
        "role": "Precomputed catalog point textbook evidence bindings for question generation",
        "path": "data/seed/experiment_catalog/point_textbook_evidence_seed.json",
        "kind": "json",
        "count": _catalog_point_textbook_evidence_seed_count,
        "expected_counts": {"states": 1, "bindings": 9, "unique_nodes": 1, "unique_chunks": 5},
        "source_path": "experiment_catalog_point_evidence_state + experiment_catalog_point_evidence_bindings",
    },
    {
        "id": "chemical_search_aliases",
        "role": "Chemistry-aware video-library search formula alias dictionary",
        "path": "data/seed/search/chemical_aliases.json",
        "kind": "json",
        "source_path": "data/seed/search/chemical_aliases.json",
    },
    {
        "id": "chemical_search_stopwords",
        "role": "Chemistry-aware video-library search domain stopword list",
        "path": "data/seed/search/chemical_stopwords.txt",
        "kind": "text",
        "source_path": "data/seed/search/chemical_stopwords.txt",
    },
    {
        "id": "es_ik_chemistry_manifest",
        "role": "Versioned ES/IK chemistry analyzer asset manifest",
        "path": "data/seed/search/es_ik/manifest.json",
        "kind": "json",
        "source_path": "data/seed/search/es_ik/manifest.json",
    },
    {
        "id": "es_ik_analyzer_config",
        "role": "ES/IK analyzer external dictionary configuration",
        "path": "data/seed/search/es_ik/analysis-ik/IKAnalyzer.cfg.xml",
        "kind": "text",
        "count": _text_line_count,
        "expected_count": 7,
        "source_path": "data/seed/search/es_ik/analysis-ik/IKAnalyzer.cfg.xml",
    },
    {
        "id": "es_ik_hit_stopwords",
        "role": "Harbin Institute of Technology stopword baseline for IK",
        "path": "data/seed/search/es_ik/analysis-ik/custom/hit_stopwords.dic",
        "kind": "text",
        "count": _text_line_count,
        "expected_count": 59,
        "source_path": "data/seed/search/es_ik/analysis-ik/custom/hit_stopwords.dic",
    },
    {
        "id": "es_ik_project_chemistry_stopwords",
        "role": "Project chemistry stopwords for IK",
        "path": "data/seed/search/es_ik/analysis-ik/custom/project_chemistry_stopwords.dic",
        "kind": "text",
        "count": _text_line_count,
        "expected_count": 22,
        "source_path": "data/seed/search/es_ik/analysis-ik/custom/project_chemistry_stopwords.dic",
    },
    {
        "id": "es_ik_chemistry_custom_dictionary",
        "role": "Chemistry custom IK dictionary",
        "path": "data/seed/search/es_ik/analysis-ik/custom/chemistry_custom.dic",
        "kind": "text",
        "count": _text_line_count,
        "expected_count": 66,
        "source_path": "data/seed/search/es_ik/analysis-ik/custom/chemistry_custom.dic",
    },
    {
        "id": "es_ik_chemistry_stopwords_filter",
        "role": "Elasticsearch chemistry analyzer stopword filter list",
        "path": "data/seed/search/es_ik/analysis/chemistry_stopwords.txt",
        "kind": "text",
        "count": _text_line_count,
        "expected_count": 81,
        "source_path": "data/seed/search/es_ik/analysis/chemistry_stopwords.txt",
    },
    {
        "id": "es_ik_chemistry_synonyms",
        "role": "Elasticsearch chemistry synonym graph filter list",
        "path": "data/seed/search/es_ik/analysis/chemistry_synonyms.txt",
        "kind": "text",
        "count": _text_line_count,
        "expected_count": 29,
        "source_path": "data/seed/search/es_ik/analysis/chemistry_synonyms.txt",
    },
    {
        "id": "student_learning_profiles",
        "role": "Student H5 display-facing family and element learning profiles",
        "path": "data/seed/student_learning/element_profiles.json",
        "kind": "json",
        "count": _student_learning_profile_count,
        "expected_counts": {
            "profiles": 9,
            "enabled_profiles": 9,
            "published_experiments": 77,
            "covered_experiments": 77,
            "uncovered_experiments": 0,
            "profiles_without_experiments": 0,
        },
    },
    {
        "id": "canonical_chunks_inorganic_lower",
        "role": "Canonical inorganic textbook chunks",
        "path": "data/seed/canonical_rag/chunks/textbook_inorganic_lower_chunks_v1.jsonl",
        "kind": "jsonl",
        "count": _jsonl_count,
        "expected_count": 3288,
        "source_path": "E:/chemistry-rag/data/rag_ready/chunks/textbook_inorganic_lower_chunks_v1.jsonl",
    },
    {
        "id": "canonical_chunks_experiment",
        "role": "Canonical experiment textbook chunks",
        "path": "data/seed/canonical_rag/chunks/textbook_experiment_chunks_v1.jsonl",
        "kind": "jsonl",
        "count": _jsonl_count,
        "expected_count": 349,
        "source_path": "E:/chemistry-rag/data/rag_ready/chunks/textbook_experiment_chunks_v1.jsonl",
    },
    {
        "id": "canonical_embedding_row_map",
        "role": "Canonical BGE embedding row map",
        "path": "data/seed/canonical_rag/embeddings/canonical_base_v1/chunk_id_to_row.jsonl",
        "kind": "jsonl",
        "count": _jsonl_count,
        "expected_count": 3637,
        "source_path": "E:/chemistry-rag/data/rag_ready/embeddings/canonical_base_v1/chunk_id_to_row.jsonl",
    },
    {
        "id": "canonical_embedding_dense",
        "role": "Canonical BGE dense embeddings",
        "path": "data/seed/canonical_rag/embeddings/canonical_base_v1/dense.float32.npy",
        "kind": "npy",
        "count": _embedding_dense_count,
        "expected_counts": {"rows": 3637, "dimensions": 1024},
        "source_path": "E:/chemistry-rag/data/rag_ready/embeddings/canonical_base_v1/dense.float32.npy",
    },
    {
        "id": "canonical_embedding_sparse",
        "role": "Canonical sparse embedding sidecar",
        "path": "data/seed/canonical_rag/embeddings/canonical_base_v1/sparse.jsonl",
        "kind": "jsonl",
        "count": _jsonl_count,
        "expected_count": 3637,
        "source_path": "E:/chemistry-rag/data/rag_ready/embeddings/canonical_base_v1/sparse.jsonl",
    },
    {
        "id": "canonical_embedding_manifest",
        "role": "Canonical embedding generation manifest",
        "path": "data/seed/canonical_rag/embeddings/canonical_base_v1/embedding_manifest.json",
        "kind": "json",
        "source_path": "E:/chemistry-rag/data/rag_ready/embeddings/canonical_base_v1/embedding_manifest.json",
    },
    {
        "id": "knowledge_framework_import_report",
        "role": "Current experiment knowledge framework import report",
        "path": "data/seed/import_reports/experiment_knowledge_framework_import_report.json",
        "kind": "json",
        "source_path": "artifacts/experiment_knowledge_framework_import_report.json",
    },
    {
        "id": "catalog_outline_seed_validation_report",
        "role": "Current catalog outline seed validation report",
        "path": "data/seed/import_reports/catalog_outline_seed_validation_report.json",
        "kind": "json",
        "count": _catalog_validation_report_count,
        "expected_counts": {
            "ok": True,
            "total_nodes": 569,
            "directory_nodes": 176,
            "point_nodes": 393,
            "point_content_records": 76,
            "equation_content_records": 71,
            "text_content_records": 5,
            "reaction_equation_rows": 122,
            "semantic_mapped_records": 76,
        },
        "source_path": "data/seed/experiment_catalog/catalog_tree.json",
    },
]


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _resource_entry(spec: dict[str, Any]) -> dict[str, Any]:
    path = ROOT / spec["path"]
    if not path.exists():
        raise FileNotFoundError(path)
    count_fn: CountFn | None = spec.get("count")
    count_value = count_fn(path) if count_fn else None
    entry = {
        "id": spec["id"],
        "role": spec["role"],
        "path": _relative(path),
        "source_path": spec.get("source_path"),
        "required": True,
        "kind": spec["kind"],
        "size_bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }
    if count_value is not None:
        entry["count"] = count_value
    if "expected_count" in spec:
        entry["expected_count"] = spec["expected_count"]
    if "expected_counts" in spec:
        entry["expected_counts"] = spec["expected_counts"]
    return entry


def build_manifest() -> dict[str, Any]:
    return {
        "version": "production-core-resources-v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "policy": (
            "These files are the protected current system resources. Destructive cleanup "
            "must validate this manifest before deleting or moving historical artifacts."
        ),
        "external_sources_mirrored": True,
        "expected_database_counts": EXPECTED_DATABASE_COUNTS,
        "resources": [_resource_entry(spec) for spec in RESOURCE_SPECS],
    }


def _compare_count(entry: dict[str, Any], actual: Any, errors: list[str]) -> None:
    if "expected_count" in entry and actual != entry["expected_count"]:
        errors.append(f"{entry['id']}: expected count {entry['expected_count']}, got {actual}")
    expected_counts = entry.get("expected_counts")
    if expected_counts:
        if not isinstance(actual, dict):
            errors.append(f"{entry['id']}: expected structured counts {expected_counts}, got {actual}")
            return
        for key, expected in expected_counts.items():
            if actual.get(key) != expected:
                errors.append(f"{entry['id']}.{key}: expected {expected}, got {actual.get(key)}")


def validate_manifest(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    if not manifest_path.exists():
        raise FileNotFoundError(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    expected_by_id = {entry["id"]: entry for entry in manifest.get("resources") or []}
    errors: list[str] = []
    actual_entries: list[dict[str, Any]] = []
    for spec in RESOURCE_SPECS:
        try:
            actual = _resource_entry(spec)
        except Exception as exc:  # noqa: BLE001 - validation should aggregate resource failures.
            errors.append(f"{spec['id']}: {exc}")
            continue
        actual_entries.append(actual)
        expected = expected_by_id.get(spec["id"])
        if expected is None:
            errors.append(f"{spec['id']}: missing from manifest")
            continue
        for key in ["path", "kind", "size_bytes", "sha256"]:
            if actual.get(key) != expected.get(key):
                errors.append(f"{spec['id']}.{key}: expected {expected.get(key)!r}, got {actual.get(key)!r}")
        _compare_count(actual, actual.get("count"), errors)
    extra = sorted(set(expected_by_id) - {spec["id"] for spec in RESOURCE_SPECS})
    for resource_id in extra:
        errors.append(f"{resource_id}: unknown resource remains in manifest")
    return {
        "ok": not errors,
        "errors": errors,
        "manifest": str(manifest_path),
        "resource_count": len(actual_entries),
        "expected_database_counts": EXPECTED_DATABASE_COUNTS,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate protected production seed resources.")
    parser.add_argument("--write-manifest", action="store_true", help="Regenerate the core resource manifest.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    args = parser.parse_args()

    if args.write_manifest:
        manifest = build_manifest()
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = validate_manifest(args.manifest)
    sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
