from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

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
    "experiment_catalog_point_content_records": 393,
    "experiment_question_banks": 52,
    "experiment_questions": 1785,
    "question_semantic_fingerprints": 1410,
    "source_documents": 2,
    "source_chunks": 3637,
    "published_catalog_point_content_min": 393,
    "catalog_point_related_links_min": 0,
    "point_evidence_bindings_with_node": 0,
    "catalog_point_textbook_evidence_states": 393,
    "catalog_point_textbook_evidence_bindings": 3537,
    "seed_teacher_accounts": 1,
    "seed_classes": 1,
    "seed_students": 30,
    "seed_media_assets": 5,
    "seed_active_point_media_bindings": 357,
    "seed_video_covered_point_nodes": 393,
    "seed_placeholder_video_covered_point_nodes": 388,
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _json(path: Path) -> Any:
    if path.suffix == ".zip":
        with zipfile.ZipFile(path) as archive:
            json_members = [name for name in archive.namelist() if name.endswith(".json")]
            if len(json_members) != 1:
                raise ValueError(f"{path} must contain exactly one JSON file")
            with archive.open(json_members[0]) as handle:
                return json.loads(handle.read().decode("utf-8-sig"))
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


def _full_catalog_point_content_seed_count(path: Path) -> dict[str, int]:
    data = _json(path)
    records = data.get("records") or []
    if not isinstance(records, list):
        raise ValueError(f"{path} records is not a JSON list")
    return {
        "records": len(records),
        "published_records": sum(
            1 for item in records if isinstance(item, dict) and item.get("content_status") == "published"
        ),
        "equation_mode_records": sum(
            1 for item in records if isinstance(item, dict) and item.get("principle_mode") == "equation"
        ),
        "text_mode_records": sum(1 for item in records if isinstance(item, dict) and item.get("principle_mode") == "text"),
        "reaction_equation_rows": sum(
            len(item.get("reaction_equations") or []) for item in records if isinstance(item, dict)
        ),
        "records_with_phenomenon_explanation": sum(
            1 for item in records if isinstance(item, dict) and item.get("phenomenon_explanation")
        ),
        "records_with_safety_note": sum(1 for item in records if isinstance(item, dict) and item.get("safety_note")),
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


def _current_question_bank_seed_count(path: Path) -> dict[str, int]:
    data = _json(path)
    supplemental_experiments = data.get("supplemental_formal_experiments") or []
    generations = data.get("question_generations") or []
    banks = data.get("question_banks") or []
    questions = data.get("questions") or []
    fingerprints = data.get("question_semantic_fingerprints") or []
    if not isinstance(banks, list) or not isinstance(questions, list):
        raise ValueError(f"{path} must contain question_banks and questions lists")
    return {
        "supplemental_formal_experiments": len(supplemental_experiments),
        "question_generations": len(generations),
        "question_banks": len(banks),
        "questions": len(questions),
        "question_semantic_fingerprints": len(fingerprints),
        "published_banks": sum(1 for item in banks if isinstance(item, dict) and item.get("status") == "published"),
        "published_questions": sum(1 for item in questions if isinstance(item, dict) and item.get("status") == "published"),
        "generated_banks": sum(1 for item in banks if isinstance(item, dict) and item.get("bank_kind") == "generated"),
        "questions_with_primary_point_nodes": sum(
            1 for item in questions if isinstance(item, dict) and item.get("primary_point_node_ids")
        ),
        "questions_with_canonical_points": sum(
            1 for item in questions if isinstance(item, dict) and item.get("primary_canonical_point_ids")
        ),
        "questions_with_source_refs": sum(1 for item in questions if isinstance(item, dict) and item.get("source_refs")),
        "questions_with_source_chunks": sum(
            1 for item in questions if isinstance(item, dict) and item.get("source_chunk_ids")
        ),
        "questions_with_point_aware_metadata": sum(
            1
            for item in questions
            if isinstance(item, dict)
            and isinstance(item.get("metadata"), dict)
            and item["metadata"].get("point_aware_question_bank") is True
        ),
    }


def _demo_identity_seed_count(path: Path) -> dict[str, int]:
    data = _json(path)
    students = data.get("students") or []
    expected = data.get("expected_counts") or {}
    if not isinstance(students, list):
        raise ValueError(f"{path} students must be a list")
    return {
        "teachers": 1 if isinstance(data.get("teacher"), dict) else 0,
        "classes": 1 if isinstance(data.get("class"), dict) else 0,
        "students": len(students),
        "expected_students": int(expected.get("students") or 0),
        "shared_password_policy": 1
        if (data.get("registration_settings") or {}).get("default_password_mode") == "shared"
        else 0,
    }


def _video_inventory_count(path: Path) -> dict[str, int]:
    data = _json(path)
    files = data.get("files") or []
    if not isinstance(files, list):
        raise ValueError(f"{path} files must be a list")
    return {
        "files": len(files),
        "real_videos": sum(1 for item in files if isinstance(item, dict) and item.get("kind") == "real_video"),
        "placeholder_videos": sum(
            1 for item in files if isinstance(item, dict) and item.get("kind") == "placeholder_video"
        ),
        "files_with_duration": sum(1 for item in files if isinstance(item, dict) and item.get("duration_seconds")),
    }


def _experiment_video_media_seed_count(path: Path) -> dict[str, int]:
    data = _json(path)
    assets = data.get("assets") or []
    bindings = data.get("bindings") or []
    expected = data.get("expected_counts") or {}
    if not isinstance(assets, list) or not isinstance(bindings, list):
        raise ValueError(f"{path} assets and bindings must be lists")
    return {
        "assets": len(assets),
        "real_video_assets": sum(1 for item in assets if isinstance(item, dict) and item.get("kind") == "real_video"),
        "placeholder_video_assets": sum(
            1 for item in assets if isinstance(item, dict) and item.get("kind") == "placeholder_video"
        ),
        "bindings": len(bindings),
        "real_video_bindings": sum(
            1 for item in bindings if isinstance(item, dict) and item.get("coverage_kind") == "real_video"
        ),
        "placeholder_video_bindings": sum(
            1 for item in bindings if isinstance(item, dict) and item.get("coverage_kind") == "placeholder_video"
        ),
        "covered_point_nodes": int(expected.get("active_catalog_point_nodes") or 0),
        "placeholder_video_covered_point_nodes": int(expected.get("placeholder_video_covered_point_nodes") or 0),
    }


def _textbook_rag_precomputed_manifest_count(path: Path) -> dict[str, int | str]:
    data = _json(path)
    return {
        "es_count": int(data.get("es_count") or 0),
        "exported_docs": int(data.get("exported_docs") or 0),
        "docs_with_embedding": int(data.get("docs_with_embedding") or 0),
        "embedding_model": str(data.get("embedding_model") or ""),
        "embedding_dimension": int(data.get("embedding_dimension") or 0),
    }


def _textbook_rag_precomputed_zip_count(path: Path) -> dict[str, int]:
    with zipfile.ZipFile(path) as archive:
        names = [name for name in archive.namelist() if name.endswith(".jsonl")]
        if len(names) != 1:
            raise ValueError(f"{path} must contain exactly one .jsonl file")
        with archive.open(names[0], "r") as handle:
            return {"documents": sum(1 for line in handle if line.strip())}


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


def _chemistry_vocabulary_count(path: Path) -> dict[str, int]:
    data = _json(path)
    categories = data.get("categories") if isinstance(data, dict) else {}
    if not isinstance(categories, dict):
        raise ValueError(f"{path} categories must be an object")
    strict = categories.get("strict_chemical_synonyms") or {}
    return {
        "categories": len(categories),
        "strict_chemical_synonyms": len(strict) if isinstance(strict, dict) else 0,
        "reagent_aliases": len(categories.get("reagent_aliases") or []),
        "phenomenon_terms": len(categories.get("phenomenon_terms") or []),
        "property_terms": len(categories.get("property_terms") or []),
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
    optional_profile_ids: set[str] = set()
    covered_experiment_ids: set[str] = set()
    multi_profile_experiment_count = 0
    errors: list[str] = []

    for profile in enabled:
        profile_id = str(profile.get("profile_id") or "<missing>")
        if profile.get("coverage_optional") is True:
            optional_profile_ids.add(profile_id)
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
    required_profiles_without_experiments = [
        profile_id for profile_id in profiles_without_experiments if profile_id not in optional_profile_ids
    ]
    optional_profiles_without_experiments = [
        profile_id for profile_id in profiles_without_experiments if profile_id in optional_profile_ids
    ]
    for profile_id in required_profiles_without_experiments:
        errors.append(f"{profile_id}: no formal experiments are bound to this profile chapter")
    if errors:
        raise ValueError("student learning experiment coverage mismatch: " + "; ".join(errors))
    return {
        "published_experiments": len(experiments),
        "covered_experiments": len(covered_experiment_ids),
        "uncovered_experiments": len(experiments) - len(covered_experiment_ids),
        "profiles_without_experiments": len(profiles_without_experiments),
        "required_profiles_without_experiments": len(required_profiles_without_experiments),
        "optional_profiles_without_experiments": len(optional_profiles_without_experiments),
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


CountFn = Callable[[Path], int | dict[str, int | str] | None]

ALLOWED_SEED_DOCS = {
    "data/seed/README.md",
    "data/seed/manifests/core_resources.json",
}

FORBIDDEN_SEED_PATHS = [
    "data/seed/experiment_points",
    "data/seed/point_evidence",
    "data/seed/question_bank",
    "data/seed/canonical_rag/embeddings",
    "data/seed/import_reports",
    "data/seed/manifests/legacy_cleanup_plan.json",
    "data/seed/experiment_catalog/canonical_point_groups.json",
    "data/seed/experiment_catalog/normalized_three_element_candidates.md",
    "data/seed/experiment_catalog/normalized_three_element_node_mapping.json",
    "data/seed/experiment_catalog/normalized_three_element_node_mapping.md",
    "data/seed/experiment_catalog/three_element_chemistry_review.md",
]


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
        "source_path": None,
    },
    {
        "id": "experiment_catalog_full_point_content_seed",
        "role": "Full current catalog point-content seed for blank-server bootstrap",
        "path": "data/seed/experiment_catalog/full_point_content_seed.json",
        "kind": "json",
        "count": _full_catalog_point_content_seed_count,
        "expected_counts": {
            "records": 393,
            "published_records": 393,
            "equation_mode_records": 182,
            "text_mode_records": 211,
            "reaction_equation_rows": 219,
            "records_with_phenomenon_explanation": 393,
            "records_with_safety_note": 393,
        },
        "source_path": "experiment_catalog_point_content + experiment_catalog_point_reaction_equations",
    },
    {
        "id": "experiment_catalog_point_textbook_evidence_seed",
        "role": "Precomputed catalog point textbook evidence bindings for question generation",
        "path": "data/seed/experiment_catalog/point_textbook_evidence_seed.json.zip",
        "kind": "zip",
        "count": _catalog_point_textbook_evidence_seed_count,
        "expected_counts": {"states": 393, "bindings": 3537, "unique_nodes": 393},
        "source_path": "experiment_catalog_point_evidence_state + experiment_catalog_point_evidence_bindings",
    },
    {
        "id": "current_catalog_node_question_bank_seed",
        "role": "Current published catalog-node question bank seed",
        "path": "data/seed/question_banks/current_catalog_node_question_bank_seed_v1.json.zip",
        "kind": "zip",
        "count": _current_question_bank_seed_count,
        "expected_counts": {
            "supplemental_formal_experiments": 52,
            "question_generations": 392,
            "question_banks": 52,
            "questions": 1785,
            "question_semantic_fingerprints": 1410,
            "published_banks": 52,
            "published_questions": 1785,
            "generated_banks": 52,
            "questions_with_primary_point_nodes": 1785,
            "questions_with_canonical_points": 1785,
            "questions_with_source_refs": 1785,
            "questions_with_source_chunks": 1785,
            "questions_with_point_aware_metadata": 0,
        },
        "source_path": "experiment_question_banks + experiment_questions",
    },
    {
        "id": "demo_identity_seed",
        "role": "Default teacher account, demo class, and active student roster/accounts",
        "path": "data/seed/identity/demo_identity_seed_v1.json",
        "kind": "json",
        "count": _demo_identity_seed_count,
        "expected_counts": {
            "teachers": 1,
            "classes": 1,
            "students": 30,
            "expected_students": 30,
            "shared_password_policy": 1,
        },
        "source_path": "demo seed manifest",
    },
    {
        "id": "experiment_video_inventory",
        "role": "Inventory of reviewed experiment video seed files with checksums and durations",
        "path": "data/seed/media/video_inventory_v1.json",
        "kind": "json",
        "count": _video_inventory_count,
        "expected_counts": {"files": 5, "real_videos": 4, "placeholder_videos": 1, "files_with_duration": 5},
        "source_path": "实验视频（新）.rar + generated ffmpeg placeholder",
    },
    {
        "id": "experiment_video_media_seed",
        "role": "Reviewed media asset and point-video binding seed with placeholder coverage",
        "path": "data/seed/media/experiment_video_seed_v1.json",
        "kind": "json",
        "count": _experiment_video_media_seed_count,
        "expected_counts": {
            "assets": 5,
            "real_video_assets": 4,
            "placeholder_video_assets": 1,
            "bindings": 357,
            "real_video_bindings": 5,
            "placeholder_video_bindings": 352,
            "covered_point_nodes": 393,
            "placeholder_video_covered_point_nodes": 388,
        },
        "source_path": "media_assets + experiment_catalog_point_media_bindings",
    },
    {
        "id": "experiment_video_real_nitrite_test",
        "role": "Seed video: 亚硝酸根的检验方法",
        "path": "data/seed/media/experiment-videos-new-v1/real/亚硝酸根的检验方法.mp4",
        "kind": "binary",
        "source_path": "实验视频（新）.rar",
    },
    {
        "id": "experiment_video_real_nitrous_oxidizing",
        "role": "Seed video: 亚硝酸的氧化性",
        "path": "data/seed/media/experiment-videos-new-v1/real/亚硝酸的氧化性.mp4",
        "kind": "binary",
        "source_path": "实验视频（新）.rar",
    },
    {
        "id": "experiment_video_real_nitrous_generation_decomposition",
        "role": "Seed video: 亚硝酸的生成与分解",
        "path": "data/seed/media/experiment-videos-new-v1/real/亚硝酸的生成与分解.mp4",
        "kind": "binary",
        "source_path": "实验视频（新）.rar",
    },
    {
        "id": "experiment_video_real_nitrous_reducing",
        "role": "Seed video: 亚硝酸的还原性",
        "path": "data/seed/media/experiment-videos-new-v1/real/亚硝酸的还原性.mp4",
        "kind": "binary",
        "source_path": "实验视频（新）.rar",
    },
    {
        "id": "experiment_video_placeholder",
        "role": "Generated placeholder video for unfilmed catalog points",
        "path": "data/seed/media/experiment-videos-new-v1/placeholder/no-video-placeholder.mp4",
        "kind": "binary",
        "source_path": "ffmpeg generated placeholder",
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
        "id": "chemical_search_vocabulary",
        "role": "Runtime chemistry search vocabulary and retrieval facets",
        "path": "data/seed/search/chemistry_vocabulary.json",
        "kind": "json",
        "count": _chemistry_vocabulary_count,
        "source_path": "data/seed/search/chemistry_vocabulary.json",
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
        "expected_count": 42,
        "source_path": "data/seed/search/es_ik/analysis/chemistry_synonyms.txt",
    },
    {
        "id": "student_learning_profiles",
        "role": "Student H5 display-facing family and element learning profiles",
        "path": "data/seed/student_learning/element_profiles.json",
        "kind": "json",
        "count": _student_learning_profile_count,
        "expected_counts": {
            "profiles": 10,
            "enabled_profiles": 10,
            "published_experiments": 77,
            "covered_experiments": 77,
            "uncovered_experiments": 0,
            "profiles_without_experiments": 1,
            "required_profiles_without_experiments": 0,
            "optional_profiles_without_experiments": 1,
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
        "id": "textbook_rag_precomputed_manifest",
        "role": "Precomputed Qwen textbook RAG Elasticsearch bundle manifest",
        "path": "data/seed/textbook_rag_precomputed/manifest.json",
        "kind": "json",
        "count": _textbook_rag_precomputed_manifest_count,
        "expected_counts": {
            "es_count": 3637,
            "exported_docs": 3637,
            "docs_with_embedding": 3637,
            "embedding_model": "text-embedding-v4",
            "embedding_dimension": 1024,
        },
        "source_path": "canonical-rag-chunks-qwen-v1",
    },
    {
        "id": "textbook_rag_precomputed_mapping",
        "role": "Precomputed Qwen textbook RAG Elasticsearch mapping",
        "path": "data/seed/textbook_rag_precomputed/canonical-rag-chunks-qwen-v1.mapping.json",
        "kind": "json",
        "source_path": "canonical-rag-chunks-qwen-v1",
    },
    {
        "id": "textbook_rag_precomputed_settings",
        "role": "Precomputed Qwen textbook RAG Elasticsearch settings",
        "path": "data/seed/textbook_rag_precomputed/canonical-rag-chunks-qwen-v1.settings.json",
        "kind": "json",
        "source_path": "canonical-rag-chunks-qwen-v1",
    },
    {
        "id": "textbook_rag_precomputed_documents_zip",
        "role": "Precomputed Qwen textbook RAG Elasticsearch documents with embeddings",
        "path": "data/seed/textbook_rag_precomputed/canonical-rag-chunks-qwen-v1.documents.jsonl.zip",
        "kind": "zip",
        "count": _textbook_rag_precomputed_zip_count,
        "expected_counts": {"documents": 3637},
        "source_path": "canonical-rag-chunks-qwen-v1",
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


def _allowed_seed_files() -> set[str]:
    return {str(spec["path"]) for spec in RESOURCE_SPECS} | ALLOWED_SEED_DOCS


def validate_seed_tree() -> list[str]:
    errors: list[str] = []
    seed_root = ROOT / "data" / "seed"
    for forbidden in FORBIDDEN_SEED_PATHS:
        path = ROOT / forbidden
        if path.exists():
            errors.append(f"{forbidden}: forbidden retired/non-current seed path exists")
    allowed = _allowed_seed_files()
    for path in sorted(seed_root.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT).as_posix()
        if relative not in allowed:
            errors.append(f"{relative}: not in current seed whitelist")
    return errors


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


def validate_manifest(manifest_path: Path = MANIFEST_PATH, *, check_seed_tree: bool = True) -> dict[str, Any]:
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
    if check_seed_tree:
        errors.extend(validate_seed_tree())
    return {
        "ok": not errors,
        "errors": errors,
        "manifest": str(manifest_path),
        "resource_count": len(actual_entries),
        "expected_database_counts": EXPECTED_DATABASE_COUNTS,
        "seed_whitelist_count": len(_allowed_seed_files()),
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
