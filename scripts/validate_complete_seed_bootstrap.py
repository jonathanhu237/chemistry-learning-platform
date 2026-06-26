from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.seed_demo_identities import DEFAULT_SEED_PATH as IDENTITY_SEED_PATH
from scripts.seed_demo_identities import load_seed as load_identity_seed
from scripts.seed_demo_identities import validate_database as validate_identity_database
from scripts.seed_experiment_videos import DEFAULT_MANIFEST_PATH as MEDIA_SEED_PATH
from scripts.seed_experiment_videos import load_manifest as load_media_seed
from scripts.seed_experiment_videos import validate_database as validate_media_database
from scripts.validate_production_resources import EXPECTED_DATABASE_COUNTS, validate_manifest
from server.app.infrastructure.database import db_session
from server.app.infrastructure.settings import get_settings


def _db_count_row() -> dict[str, int]:
    with db_session() as session:
        row = session.execute(
            text(
                """
                SELECT
                  (
                    SELECT count(*)
                    FROM formal_experiments
                    WHERE status = 'published'
                      AND metadata->>'formal_catalog' = 'true'
                  ) AS formal_experiments_active,
                  (
                    SELECT count(*)
                    FROM formal_experiments
                    WHERE status = 'published'
                      AND COALESCE(metadata->>'formal_catalog', 'false') <> 'true'
                  ) AS non_seed_published_formal_experiments,
                  (SELECT count(*) FROM chapters) AS chapters,
                  (SELECT count(*) FROM knowledge_units) AS knowledge_units,
                  (SELECT count(*) FROM knowledge_points) AS knowledge_points,
                  (SELECT count(*) FROM experiment_catalog_nodes) AS experiment_catalog_nodes,
                  (SELECT count(*) FROM experiment_catalog_nodes WHERE node_kind = 'directory') AS experiment_catalog_directory_nodes,
                  (SELECT count(*) FROM experiment_catalog_nodes WHERE node_kind = 'point') AS experiment_catalog_point_nodes,
                  (SELECT count(*) FROM experiment_catalog_point_content) AS experiment_catalog_point_content_records,
                  (
                    SELECT count(*)
                    FROM experiment_catalog_point_content
                    WHERE content_status = 'published'
                  ) AS published_catalog_point_content,
                  (SELECT count(*) FROM source_documents) AS source_documents,
                  (SELECT count(*) FROM source_chunks) AS source_chunks,
                  (
                    SELECT count(*)
                    FROM source_chunks
                    WHERE metadata->>'source_role' = 'canonical_textbook'
                  ) AS canonical_textbook_source_chunks,
                  (SELECT count(*) FROM experiment_catalog_point_evidence_state) AS catalog_point_textbook_evidence_states,
                  (
                    SELECT count(*)
                    FROM experiment_catalog_point_evidence_bindings
                    WHERE selection_status = 'selected'
                      AND freshness_status = 'fresh'
                  ) AS catalog_point_textbook_evidence_bindings,
                  (
                    SELECT count(*)
                    FROM experiment_question_banks
                    WHERE status = 'published'
                      AND bank_kind = 'generated'
                  ) AS experiment_question_banks,
                  (
                    SELECT count(*)
                    FROM experiment_question_banks
                    WHERE status = 'published'
                  ) AS published_experiment_question_banks,
                  (
                    SELECT count(*)
                    FROM experiment_questions q
                    JOIN experiment_question_banks b ON b.id = q.bank_id
                    WHERE q.status = 'published'
                      AND b.status = 'published'
                      AND b.bank_kind = 'generated'
                  ) AS experiment_questions,
                  (
                    SELECT count(*)
                    FROM experiment_questions
                    WHERE status = 'published'
                  ) AS published_experiment_questions,
                  (
                    SELECT count(*)
                    FROM question_semantic_fingerprints fingerprint
                    WHERE fingerprint.owner_kind = 'question'
                      AND EXISTS (
                        SELECT 1
                        FROM experiment_questions q
                        JOIN experiment_question_banks b ON b.id = q.bank_id
                        WHERE q.id::text = fingerprint.owner_id::text
                          AND q.status = 'published'
                          AND b.status = 'published'
                          AND b.bank_kind = 'generated'
                      )
                  ) AS question_semantic_fingerprints,
                  (
                    SELECT count(*)
                    FROM question_semantic_fingerprints
                    WHERE owner_kind <> 'question'
                  ) AS non_question_semantic_fingerprints,
                  (
                    SELECT count(*)
                    FROM experiment_questions
                    WHERE status = 'published'
                      AND question_type NOT IN ('single_choice', 'true_false', 'fill_blank')
                  ) AS unsupported_question_types,
                  (
                    SELECT count(*)
                    FROM experiment_questions
                    WHERE status = 'published'
                      AND (
                        experiment_id IS NULL
                        OR bank_id IS NULL
                        OR cardinality(source_chunk_ids) = 0
                        OR jsonb_array_length(COALESCE(source_refs, '[]'::jsonb)) = 0
                      )
                  ) AS malformed_published_questions,
                  (
                    SELECT count(*)
                    FROM experiment_questions
                    WHERE status = 'published'
                      AND (
                        lower(COALESCE(metadata::text, '') || ' ' || COALESCE(stem, '') || ' ' || COALESCE(explanation, '')) LIKE '%mock%'
                      OR lower(COALESCE(metadata::text, '') || ' ' || COALESCE(stem, '') || ' ' || COALESCE(explanation, '')) LIKE '%fake%'
                      OR COALESCE(metadata->>'mock', 'false') = 'true'
                      OR COALESCE(metadata->>'fake', 'false') = 'true'
                      )
                  ) AS mock_or_fake_question_markers
                """
            )
        ).mappings().one()
    return {key: int(row[key] or 0) for key in row.keys()}


def _compare_counts(counts: dict[str, int]) -> list[str]:
    errors: list[str] = []
    exact_keys = [
        "formal_experiments_active",
        "chapters",
        "knowledge_units",
        "knowledge_points",
        "experiment_catalog_nodes",
        "experiment_catalog_directory_nodes",
        "experiment_catalog_point_nodes",
        "experiment_catalog_point_content_records",
        "experiment_question_banks",
        "experiment_questions",
        "question_semantic_fingerprints",
        "source_documents",
        "source_chunks",
        "catalog_point_textbook_evidence_states",
        "catalog_point_textbook_evidence_bindings",
    ]
    for key in exact_keys:
        expected = EXPECTED_DATABASE_COUNTS.get(key)
        if expected is not None and counts.get(key) != expected:
            errors.append(f"{key}: expected {expected}, got {counts.get(key)}")
    min_published = int(EXPECTED_DATABASE_COUNTS["published_catalog_point_content_min"])
    if counts.get("published_catalog_point_content", 0) < min_published:
        errors.append(
            f"published_catalog_point_content: expected at least {min_published}, got {counts.get('published_catalog_point_content')}"
        )
    if counts.get("published_experiment_question_banks") != EXPECTED_DATABASE_COUNTS["experiment_question_banks"]:
        errors.append(
            "published_experiment_question_banks: "
            f"expected {EXPECTED_DATABASE_COUNTS['experiment_question_banks']}, got {counts.get('published_experiment_question_banks')}"
        )
    if counts.get("published_experiment_questions") != EXPECTED_DATABASE_COUNTS["experiment_questions"]:
        errors.append(
            "published_experiment_questions: "
            f"expected {EXPECTED_DATABASE_COUNTS['experiment_questions']}, got {counts.get('published_experiment_questions')}"
        )
    for zero_key in ["unsupported_question_types", "malformed_published_questions", "mock_or_fake_question_markers"]:
        if counts.get(zero_key) != 0:
            errors.append(f"{zero_key}: expected 0, got {counts.get(zero_key)}")
    return errors


def _runtime_config_status() -> dict[str, Any]:
    settings = get_settings()
    return {
        "agent_llm_provider": settings.agent_llm_provider or "disabled",
        "agent_llm_configured": bool(
            settings.agent_llm_provider
            and settings.agent_llm_provider != "disabled"
            and settings.agent_llm_api_key
            and settings.agent_llm_model
        ),
        "textbook_rag_enabled": settings.textbook_rag_enabled,
        "textbook_rag_es_configured": bool(settings.textbook_rag_elasticsearch_url),
        "textbook_rag_embedding_configured": bool(
            settings.textbook_rag_embedding_base_url
            and settings.textbook_rag_embedding_api_key
            and settings.textbook_rag_embedding_model
        ),
        "textbook_rag_rerank_configured": bool(
            settings.textbook_rag_rerank_base_url
            and settings.textbook_rag_rerank_api_key
            and settings.textbook_rag_rerank_model
        ),
        "video_library_search_backend": settings.video_library_search_backend,
        "teacher_catalog_search_backend": settings.teacher_catalog_search_backend,
        "configuration_pending_is_seed_failure": False,
    }


def validate_complete_seed(
    *,
    check_files: bool = True,
    media_root: Path | None = None,
    teacher_username: str | None = None,
    class_id: str | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    sections: dict[str, Any] = {}
    if check_files:
        resource_result = validate_manifest()
        sections["resources"] = resource_result
        errors.extend(f"resources: {item}" for item in resource_result.get("errors") or [])
    identity_payload = load_identity_seed(IDENTITY_SEED_PATH)
    identity_result = validate_identity_database(identity_payload, teacher_username=teacher_username, class_id=class_id)
    sections["identity"] = identity_result
    errors.extend(f"identity: {item}" for item in identity_result.get("errors") or [])
    media_payload = load_media_seed(MEDIA_SEED_PATH)
    media_result = validate_media_database(media_payload, media_root=media_root)
    sections["media"] = media_result
    errors.extend(f"media: {item}" for item in media_result.get("errors") or [])
    counts = _db_count_row()
    count_errors = _compare_counts(counts)
    sections["database_counts"] = {"ok": not count_errors, "errors": count_errors, "summary": counts}
    errors.extend(f"database_counts: {item}" for item in count_errors)
    sections["runtime_config"] = _runtime_config_status()
    return {"ok": not errors, "errors": errors, "sections": sections}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the complete production seed after bootstrap.")
    parser.add_argument("--skip-file-validation", action="store_true")
    parser.add_argument("--media-root", type=Path)
    parser.add_argument("--teacher-username")
    parser.add_argument("--class-id")
    args = parser.parse_args()
    result = validate_complete_seed(
        check_files=not args.skip_file_validation,
        media_root=args.media_root,
        teacher_username=args.teacher_username,
        class_id=args.class_id,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
