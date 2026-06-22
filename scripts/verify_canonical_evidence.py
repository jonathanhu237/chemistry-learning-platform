from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.app.infrastructure.database import db_session

EXPECTED_SOURCE_DOCUMENTS = 2
EXPECTED_SOURCE_CHUNKS = 3637
EXPECTED_EMBEDDINGS = 3637
EXPECTED_BANKS = 0
EXPECTED_EXPERIMENT_QUESTIONS = 0


def _scalar(session: Any, sql: str) -> int:
    return int(session.execute(text(sql)).scalar_one() or 0)


def verify() -> dict[str, Any]:
    with db_session() as session:
        counts = {
            "source_documents": _scalar(session, "SELECT COUNT(*) FROM source_documents"),
            "source_chunks": _scalar(session, "SELECT COUNT(*) FROM source_chunks"),
            "chunk_embeddings": _scalar(session, "SELECT COUNT(*) FROM chunk_embeddings"),
            "legacy_links": _scalar(session, "SELECT COUNT(*) FROM links"),
            "legacy_questions": _scalar(session, "SELECT COUNT(*) FROM questions"),
            "legacy_resources": _scalar(session, "SELECT COUNT(*) FROM resources"),
            "formal_experiments": _scalar(session, "SELECT COUNT(*) FROM formal_experiments WHERE status <> 'archived'"),
            "experiment_question_banks": _scalar(session, "SELECT COUNT(*) FROM experiment_question_banks"),
            "experiment_questions": _scalar(session, "SELECT COUNT(*) FROM experiment_questions"),
        }
        checks = {
            "old_chunk_ids": _scalar(session, "SELECT COUNT(*) FROM source_chunks WHERE id LIKE 'CHK_DOC_%'"),
            "old_courseware_documents": _scalar(session, "SELECT COUNT(*) FROM source_documents WHERE id LIKE 'DOC_CH%'"),
            "canonical_chunks": _scalar(
                session,
                "SELECT COUNT(*) FROM source_chunks WHERE metadata->>'source_role' = 'canonical_textbook'",
            ),
            "questions_without_source_refs": _scalar(
                session,
                """
                SELECT COUNT(*)
                FROM experiment_questions
                WHERE cardinality(source_chunk_ids) > 0
                  AND jsonb_array_length(source_refs) = 0
                """,
            ),
            "questions_with_missing_chunks": _scalar(
                session,
                """
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
                """,
            ),
        }

    errors: list[str] = []
    expected_counts = {
        "source_documents": EXPECTED_SOURCE_DOCUMENTS,
        "source_chunks": EXPECTED_SOURCE_CHUNKS,
        "chunk_embeddings": EXPECTED_EMBEDDINGS,
        "legacy_links": 0,
        "legacy_questions": 0,
        "legacy_resources": 0,
        "experiment_question_banks": EXPECTED_BANKS,
        "experiment_questions": EXPECTED_EXPERIMENT_QUESTIONS,
    }
    for key, expected in expected_counts.items():
        actual = counts.get(key)
        if actual != expected:
            errors.append(f"{key}: expected {expected}, got {actual}")
    for key in ["old_chunk_ids", "old_courseware_documents", "questions_without_source_refs", "questions_with_missing_chunks"]:
        if checks[key] != 0:
            errors.append(f"{key}: expected 0, got {checks[key]}")
    if checks["canonical_chunks"] != EXPECTED_SOURCE_CHUNKS:
        errors.append(f"canonical_chunks: expected {EXPECTED_SOURCE_CHUNKS}, got {checks['canonical_chunks']}")

    return {
        "ok": not errors,
        "errors": errors,
        "counts": counts,
        "checks": checks,
    }


def main() -> None:
    result = verify()
    sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
