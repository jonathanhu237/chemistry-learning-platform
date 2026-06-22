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
            example_row = session.execute(
                text(
                    """
                    SELECT
                      COUNT(*) AS example_content_count,
                      COUNT(DISTINCT pc.node_id) AS unique_example_node_count,
                      COUNT(*) FILTER (WHERE pc.content_status = 'published') AS published_example_content_count,
                      COUNT(*) FILTER (WHERE si.node_id IS NOT NULL) AS queued_example_search_count
                    FROM experiment_catalog_point_content pc
                    LEFT JOIN experiment_catalog_point_search_index_state si ON si.node_id = pc.node_id
                    WHERE COALESCE(pc.metadata->>'catalog_outline_point_content_seed', 'false') = 'true'
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
                      (SELECT COUNT(*) FROM experiment_question_banks) AS question_bank_count,
                      (SELECT COUNT(*) FROM experiment_questions) AS question_count,
                      (SELECT COUNT(*) FROM experiment_video_point_evidence) AS point_evidence_count,
                      (SELECT COUNT(*) FROM experiment_video_points) AS legacy_video_point_count,
                      (SELECT COUNT(*) FROM experiment_catalog_legacy_identity_map) AS legacy_identity_map_count,
                      (SELECT COUNT(*) FROM source_chunks) AS source_chunk_count,
                      (SELECT COUNT(*) FROM chunk_embeddings) AS chunk_embedding_count
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
    example_content_count = int(example_row["example_content_count"] or 0)
    unique_example_node_count = int(example_row["unique_example_node_count"] or 0)
    published_example_content_count = int(example_row["published_example_content_count"] or 0)
    queued_example_search_count = int(example_row["queued_example_search_count"] or 0)
    canonical_point_count = int(canonical_row["canonical_point_count"] or 0)
    point_without_canonical_count = int(canonical_row["point_without_canonical_count"] or 0)
    directory_with_canonical_count = int(canonical_row["directory_with_canonical_count"] or 0)
    missing_canonical_target_count = int(canonical_row["missing_canonical_target_count"] or 0)
    orphan_canonical_point_count = int(canonical_row["orphan_canonical_point_count"] or 0)
    evidence_state_without_canonical_count = int(evidence_identity_row["evidence_state_without_canonical_count"] or 0)
    evidence_binding_without_canonical_count = int(evidence_identity_row["evidence_binding_without_canonical_count"] or 0)
    corrected_titles = {str(item["title"]) for item in corrected_rows}
    corrected_parent_ids = {str(item["parent_id"]) for item in corrected_rows}
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
    if example_content_count != 30 or unique_example_node_count != 30:
        errors.append(f"catalog point content examples mismatch: {example_content_count} rows / {unique_example_node_count} unique nodes")
    if published_example_content_count != 30:
        errors.append(f"published example content mismatch: expected 30, got {published_example_content_count}")
    if queued_example_search_count != 30:
        errors.append(f"queued example search documents mismatch: expected 30, got {queued_example_search_count}")
    if corrected_titles != {"NaClO + MnSO₄", "NaClO + 品红溶液"} or len(corrected_parent_ids) != 1:
        errors.append("corrected NaClO + MnSO₄ / NaClO + 品红溶液 sibling points are missing or not siblings")
    if int(retired_row["question_bank_count"] or 0):
        errors.append(f"retired question banks still present: {retired_row['question_bank_count']}")
    if int(retired_row["question_count"] or 0):
        errors.append(f"retired questions still present: {retired_row['question_count']}")
    if int(retired_row["point_evidence_count"] or 0):
        errors.append(f"retired point evidence bindings still present: {retired_row['point_evidence_count']}")
    if int(retired_row["legacy_video_point_count"] or 0):
        errors.append(f"legacy video points still present: {retired_row['legacy_video_point_count']}")
    if int(retired_row["legacy_identity_map_count"] or 0):
        errors.append(f"legacy catalog identity maps still present: {retired_row['legacy_identity_map_count']}")
    if int(retired_row["source_chunk_count"] or 0) < 3637:
        errors.append(f"canonical source chunks missing: expected at least 3637, got {retired_row['source_chunk_count']}")
    if int(retired_row["chunk_embedding_count"] or 0) < 3637:
        errors.append(f"canonical chunk embeddings missing: expected at least 3637, got {retired_row['chunk_embedding_count']}")
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
        "example_content_count": example_content_count,
        "unique_example_node_count": unique_example_node_count,
        "queued_example_search_count": queued_example_search_count,
        "published_content_count": int(row["published_content_count"] or 0),
        "teacher_note_count": int(row["teacher_note_count"] or 0),
        "search_state_count": int(row["search_state_count"] or 0),
        "corrected_hypochlorite_titles": sorted(corrected_titles),
        "retired_counts": {key: int(retired_row[key] or 0) for key in retired_row.keys()},
    }
    sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
