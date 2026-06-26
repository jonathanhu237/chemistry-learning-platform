from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("PGCONNECT_TIMEOUT", "5")

from server.app.infrastructure.database import db_session


EXPECTED_CATALOG_POINT_CONTENT_COUNT = 393


def main() -> None:
    try:
        with db_session() as session:
            row = session.execute(
                text(
                    """
                    SELECT
                      COUNT(*) AS catalog_node_count,
                      COUNT(*) FILTER (WHERE n.node_kind = 'directory') AS directory_node_count,
                      COUNT(*) FILTER (WHERE n.node_kind = 'point') AS point_node_count,
                      COUNT(*) FILTER (WHERE n.chapter_id = 'CH21') AS chapter_21_node_count,
                      COUNT(*) FILTER (
                        WHERE n.node_kind = 'point'
                          AND pc.node_id IS NOT NULL
                      ) AS point_content_count,
                      COUNT(*) FILTER (
                        WHERE n.node_kind = 'point'
                          AND pc.content_status = 'published'
                      ) AS published_content_count,
                      COUNT(*) FILTER (
                        WHERE n.node_kind = 'point'
                          AND pc.teacher_note IS NOT NULL
                          AND btrim(pc.teacher_note) <> ''
                      ) AS teacher_note_count,
                      COUNT(*) FILTER (
                        WHERE n.node_kind = 'point'
                          AND si.node_id IS NOT NULL
                      ) AS search_state_count
                    FROM experiment_catalog_nodes n
                    LEFT JOIN experiment_catalog_point_content pc ON pc.node_id = n.id
                    LEFT JOIN experiment_catalog_point_search_index_state si ON si.node_id = n.id
                    """
                )
            ).mappings().one()
            point_children = int(
                session.execute(
                    text(
                        """
                        SELECT COUNT(*)
                        FROM experiment_catalog_nodes point
                        JOIN experiment_catalog_nodes child ON child.parent_id = point.id
                        WHERE point.node_kind = 'point'
                        """
                    )
                ).scalar_one()
                or 0
            )
            full_content_row = session.execute(
                text(
                    """
                    SELECT
                      COUNT(*) AS full_content_count,
                      COUNT(DISTINCT pc.node_id) AS unique_full_content_node_count,
                      COUNT(*) FILTER (WHERE pc.content_status = 'published') AS published_full_content_count,
                      COUNT(*) FILTER (WHERE si.node_id IS NOT NULL) AS indexed_full_content_count
                    FROM experiment_catalog_point_content pc
                    JOIN experiment_catalog_nodes n ON n.id = pc.node_id AND n.node_kind = 'point'
                    LEFT JOIN experiment_catalog_point_search_index_state si ON si.node_id = pc.node_id
                    """
                )
            ).mappings().one()
            canonical_row = session.execute(
                text(
                    """
                    SELECT
                      (SELECT COUNT(*) FROM experiment_catalog_points WHERE status <> 'archived') AS canonical_point_count,
                      COUNT(*) FILTER (
                        WHERE n.status <> 'archived'
                          AND n.node_kind = 'point'
                          AND n.canonical_point_id IS NULL
                      ) AS point_without_canonical_count,
                      COUNT(*) FILTER (
                        WHERE n.status <> 'archived'
                          AND n.node_kind = 'directory'
                          AND n.canonical_point_id IS NOT NULL
                      ) AS directory_with_canonical_count,
                      COUNT(*) FILTER (
                        WHERE n.status <> 'archived'
                          AND n.node_kind = 'point'
                          AND n.canonical_point_id IS NOT NULL
                          AND cp.id IS NULL
                      ) AS missing_canonical_target_count,
                      (
                        SELECT COUNT(*)
                        FROM experiment_catalog_points canon
                        WHERE canon.status <> 'archived'
                          AND NOT EXISTS (
                            SELECT 1
                            FROM experiment_catalog_nodes placement
                            WHERE placement.canonical_point_id = canon.id
                              AND placement.node_kind = 'point'
                              AND placement.status <> 'archived'
                          )
                      ) AS orphan_canonical_point_count
                    FROM experiment_catalog_nodes n
                    LEFT JOIN experiment_catalog_points cp ON cp.id = n.canonical_point_id
                    """
                )
            ).mappings().one()
            evidence_identity_row = session.execute(
                text(
                    """
                    SELECT
                      (SELECT COUNT(*) FROM experiment_catalog_point_evidence_state WHERE canonical_point_id IS NULL) AS evidence_state_without_canonical_count,
                      (SELECT COUNT(*) FROM experiment_catalog_point_evidence_bindings WHERE canonical_point_id IS NULL) AS evidence_binding_without_canonical_count
                    """
                )
            ).mappings().one()
            corrected_rows = [
                dict(item)
                for item in session.execute(
                    text(
                        """
                        SELECT child.title, child.parent_id
                        FROM experiment_catalog_nodes parent
                        JOIN experiment_catalog_nodes child ON child.parent_id = parent.id
                        WHERE parent.chapter_id = 'CH13'
                          AND parent.title = '次氯酸盐的氧化性'
                          AND child.node_kind = 'point'
                          AND child.title IN ('NaClO + MnSO₄', 'NaClO + 品红溶液')
                        """
                    )
                )
                .mappings()
                .all()
            ]
            retired_row = session.execute(
                text(
                    """
                    SELECT
                      (SELECT COUNT(*) FROM experiment_video_point_evidence) AS point_evidence_count,
                      (SELECT COUNT(*) FROM experiment_video_points) AS legacy_video_point_count,
                      (SELECT COUNT(*) FROM experiment_catalog_legacy_identity_map) AS legacy_identity_map_count,
                      (SELECT COUNT(*) FROM source_chunks) AS source_chunk_count,
                      (SELECT COUNT(*) FROM chunk_embeddings) AS optional_chunk_embedding_count
                    """
                )
            ).mappings().one()
            question_identity_row = session.execute(
                text(
                    """
                    WITH point_refs AS (
                      SELECT q.id AS question_id, unnest(q.primary_point_node_ids) AS node_id
                      FROM experiment_questions q
                      WHERE q.primary_point_node_ids IS NOT NULL
                    ),
                    canonical_refs AS (
                      SELECT q.id AS question_id, unnest(q.primary_canonical_point_ids) AS canonical_point_id
                      FROM experiment_questions q
                      WHERE q.primary_canonical_point_ids IS NOT NULL
                    )
                    SELECT
                      (SELECT COUNT(*) FROM experiment_question_banks) AS question_bank_count,
                      (SELECT COUNT(*) FROM experiment_question_banks WHERE status = 'published') AS published_question_bank_count,
                      (
                        SELECT COUNT(*)
                        FROM experiment_question_banks
                        WHERE experiment_id IS NULL OR btrim(experiment_id) = ''
                      ) AS question_bank_without_experiment_count,
                      (SELECT COUNT(*) FROM experiment_questions) AS question_count,
                      (SELECT COUNT(*) FROM experiment_questions WHERE status = 'published') AS published_question_count,
                      (
                        SELECT COUNT(*)
                        FROM experiment_questions
                        WHERE experiment_id IS NULL OR btrim(experiment_id) = ''
                      ) AS question_without_experiment_count,
                      (
                        SELECT COUNT(*)
                        FROM experiment_questions q
                        WHERE q.bank_id IS NULL
                          OR NOT EXISTS (
                            SELECT 1
                            FROM experiment_question_banks b
                            WHERE b.id = q.bank_id
                          )
                      ) AS question_without_bank_count,
                      (
                        SELECT COUNT(*)
                        FROM experiment_questions
                        WHERE COALESCE(array_length(primary_point_node_ids, 1), 0) = 0
                      ) AS question_without_point_nodes_count,
                      (
                        SELECT COUNT(*)
                        FROM experiment_questions
                        WHERE COALESCE(array_length(primary_point_node_ids, 1), 0) = 0
                          AND metadata->>'point_aware_question_bank' = 'true'
                          AND cardinality(source_chunk_ids) > 0
                          AND jsonb_array_length(COALESCE(source_refs, '[]'::jsonb)) > 0
                      ) AS legacy_point_aware_question_without_point_nodes_count,
                      (
                        SELECT COUNT(*)
                        FROM experiment_questions
                        WHERE COALESCE(array_length(primary_canonical_point_ids, 1), 0) = 0
                      ) AS question_without_canonical_points_count,
                      (
                        SELECT COUNT(*)
                        FROM experiment_questions
                        WHERE COALESCE(array_length(primary_canonical_point_ids, 1), 0) = 0
                          AND metadata->>'point_aware_question_bank' = 'true'
                          AND cardinality(source_chunk_ids) > 0
                          AND jsonb_array_length(COALESCE(source_refs, '[]'::jsonb)) > 0
                      ) AS legacy_point_aware_question_without_canonical_points_count,
                      (
                        SELECT COUNT(*)
                        FROM point_refs refs
                        LEFT JOIN experiment_catalog_nodes n ON n.id = refs.node_id
                        WHERE n.id IS NULL
                      ) AS missing_question_point_refs_count,
                      (
                        SELECT COUNT(*)
                        FROM canonical_refs refs
                        LEFT JOIN experiment_catalog_points p ON p.id = refs.canonical_point_id
                        WHERE p.id IS NULL
                      ) AS missing_question_canonical_refs_count,
                      (
                        SELECT COUNT(*)
                        FROM experiment_questions
                        WHERE source_refs IS NOT NULL
                          AND jsonb_typeof(source_refs) <> 'array'
                      ) AS question_source_refs_not_array_count,
                      (
                        SELECT COUNT(*)
                        FROM experiment_questions
                        WHERE cardinality(source_chunk_ids) > 0
                          AND jsonb_array_length(COALESCE(source_refs, '[]'::jsonb)) = 0
                      ) AS question_source_chunks_without_refs_count,
                      (
                        SELECT COUNT(*)
                        FROM experiment_questions q
                        WHERE EXISTS (
                          SELECT 1
                          FROM unnest(q.source_chunk_ids) AS cid
                          WHERE NOT EXISTS (
                            SELECT 1
                            FROM source_chunks sc
                            WHERE sc.id = cid
                              AND sc.metadata->>'source_role' = 'canonical_textbook'
                          )
                        )
                      ) AS question_missing_canonical_chunks_count
                    """
                )
            ).mappings().one()
            duplicate_ids = [
                str(item["id"])
                for item in session.execute(
                    text(
                        """
                        SELECT id
                        FROM experiment_catalog_nodes
                        GROUP BY id
                        HAVING COUNT(*) > 1
                        """
                    )
                ).mappings().all()
            ]
    except SQLAlchemyError as exc:
        result = {
            "ok": False,
            "errors": [f"database unavailable for catalog point validation: {exc}"],
        }
        sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        raise SystemExit(1) from exc

    catalog_node_count = int(row["catalog_node_count"] or 0)
    directory_node_count = int(row["directory_node_count"] or 0)
    point_node_count = int(row["point_node_count"] or 0)
    point_content_count = int(row["point_content_count"] or 0)
    chapter_21_node_count = int(row["chapter_21_node_count"] or 0)
    full_content_count = int(full_content_row["full_content_count"] or 0)
    unique_full_content_node_count = int(full_content_row["unique_full_content_node_count"] or 0)
    published_full_content_count = int(full_content_row["published_full_content_count"] or 0)
    indexed_full_content_count = int(full_content_row["indexed_full_content_count"] or 0)
    canonical_point_count = int(canonical_row["canonical_point_count"] or 0)
    point_without_canonical_count = int(canonical_row["point_without_canonical_count"] or 0)
    directory_with_canonical_count = int(canonical_row["directory_with_canonical_count"] or 0)
    missing_canonical_target_count = int(canonical_row["missing_canonical_target_count"] or 0)
    orphan_canonical_point_count = int(canonical_row["orphan_canonical_point_count"] or 0)
    evidence_state_without_canonical_count = int(evidence_identity_row["evidence_state_without_canonical_count"] or 0)
    evidence_binding_without_canonical_count = int(evidence_identity_row["evidence_binding_without_canonical_count"] or 0)
    corrected_titles = {str(item["title"]) for item in corrected_rows}
    corrected_parent_ids = {str(item["parent_id"]) for item in corrected_rows}
    question_identity_counts = {key: int(question_identity_row[key] or 0) for key in question_identity_row.keys()}
    errors: list[str] = []
    if catalog_node_count != 569:
        errors.append(f"catalog node count mismatch: expected 569, got {catalog_node_count}")
    if directory_node_count != 176:
        errors.append(f"directory node count mismatch: expected 176, got {directory_node_count}")
    if point_node_count != 393:
        errors.append(f"point node count mismatch: expected 393, got {point_node_count}")
    if canonical_point_count != 357:
        errors.append(f"canonical point count mismatch: expected 357, got {canonical_point_count}")
    if point_without_canonical_count:
        errors.append(f"point placements without canonical point: {point_without_canonical_count}")
    if directory_with_canonical_count:
        errors.append(f"directory nodes with canonical point: {directory_with_canonical_count}")
    if missing_canonical_target_count:
        errors.append(f"point placements targeting missing canonical point: {missing_canonical_target_count}")
    if orphan_canonical_point_count:
        errors.append(f"active canonical points without active placements: {orphan_canonical_point_count}")
    if evidence_state_without_canonical_count:
        errors.append(f"evidence state rows without canonical point: {evidence_state_without_canonical_count}")
    if evidence_binding_without_canonical_count:
        errors.append(f"evidence binding rows without canonical point: {evidence_binding_without_canonical_count}")
    if chapter_21_node_count:
        errors.append(f"chapter 21 should be empty, got {chapter_21_node_count} node(s)")
    if point_children:
        errors.append(f"point nodes with children: {point_children}")
    if full_content_count != EXPECTED_CATALOG_POINT_CONTENT_COUNT or unique_full_content_node_count != EXPECTED_CATALOG_POINT_CONTENT_COUNT:
        errors.append(
            "catalog point content mismatch: "
            f"{full_content_count} rows / {unique_full_content_node_count} unique nodes"
        )
    if published_full_content_count != EXPECTED_CATALOG_POINT_CONTENT_COUNT:
        errors.append(
            "published catalog point content mismatch: "
            f"expected {EXPECTED_CATALOG_POINT_CONTENT_COUNT}, got {published_full_content_count}"
        )
    if indexed_full_content_count != EXPECTED_CATALOG_POINT_CONTENT_COUNT:
        errors.append(
            "indexed catalog point content mismatch: "
            f"expected {EXPECTED_CATALOG_POINT_CONTENT_COUNT}, got {indexed_full_content_count}"
        )
    unresolved_question_without_point_nodes = max(
        0,
        question_identity_counts["question_without_point_nodes_count"]
        - question_identity_counts["legacy_point_aware_question_without_point_nodes_count"],
    )
    unresolved_question_without_canonical_points = max(
        0,
        question_identity_counts["question_without_canonical_points_count"]
        - question_identity_counts["legacy_point_aware_question_without_canonical_points_count"],
    )
    for key, label in [
        ("question_bank_without_experiment_count", "question banks without experiment ids"),
        ("question_without_experiment_count", "questions without experiment ids"),
        ("question_without_bank_count", "questions without current banks"),
        ("missing_question_point_refs_count", "question catalog point references targeting missing nodes"),
        ("missing_question_canonical_refs_count", "question canonical point references targeting missing points"),
        ("question_source_refs_not_array_count", "questions with non-array source_refs"),
        ("question_source_chunks_without_refs_count", "questions with source chunks but no source refs"),
        ("question_missing_canonical_chunks_count", "questions referencing missing canonical chunks"),
    ]:
        if question_identity_counts[key]:
            errors.append(f"{label}: {question_identity_counts[key]}")
    if unresolved_question_without_point_nodes:
        errors.append(f"questions without catalog point placements: {unresolved_question_without_point_nodes}")
    if unresolved_question_without_canonical_points:
        errors.append(f"questions without canonical points: {unresolved_question_without_canonical_points}")
    if int(retired_row["point_evidence_count"] or 0):
        errors.append(f"retired point evidence bindings still present: {retired_row['point_evidence_count']}")
    if int(retired_row["legacy_video_point_count"] or 0):
        errors.append(f"legacy video points still present: {retired_row['legacy_video_point_count']}")
    if int(retired_row["legacy_identity_map_count"] or 0):
        errors.append(f"legacy catalog identity maps still present: {retired_row['legacy_identity_map_count']}")
    if int(retired_row["source_chunk_count"] or 0) < 3637:
        errors.append(f"canonical source chunks missing: expected at least 3637, got {retired_row['source_chunk_count']}")
    if duplicate_ids:
        errors.append(f"duplicate catalog node ids: {', '.join(duplicate_ids[:5])}")

    result = {
        "ok": not errors,
        "errors": errors,
        "catalog_node_count": catalog_node_count,
        "directory_node_count": directory_node_count,
        "point_node_count": point_node_count,
        "canonical_point_count": canonical_point_count,
        "point_without_canonical_count": point_without_canonical_count,
        "directory_with_canonical_count": directory_with_canonical_count,
        "missing_canonical_target_count": missing_canonical_target_count,
        "orphan_canonical_point_count": orphan_canonical_point_count,
        "evidence_state_without_canonical_count": evidence_state_without_canonical_count,
        "evidence_binding_without_canonical_count": evidence_binding_without_canonical_count,
        "point_content_count": point_content_count,
        "chapter_21_node_count": chapter_21_node_count,
        "point_children": point_children,
        "full_content_count": full_content_count,
        "unique_full_content_node_count": unique_full_content_node_count,
        "indexed_full_content_count": indexed_full_content_count,
        "unresolved_question_without_point_nodes": unresolved_question_without_point_nodes,
        "unresolved_question_without_canonical_points": unresolved_question_without_canonical_points,
        "published_content_count": int(row["published_content_count"] or 0),
        "teacher_note_count": int(row["teacher_note_count"] or 0),
        "search_state_count": int(row["search_state_count"] or 0),
        "corrected_hypochlorite_titles": sorted(corrected_titles),
        "current_question_bank_counts": question_identity_counts,
        "retired_counts": {key: int(retired_row[key] or 0) for key in retired_row.keys()},
    }
    sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
