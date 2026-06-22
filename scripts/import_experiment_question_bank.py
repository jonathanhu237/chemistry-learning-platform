from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.app.infrastructure.database import apply_migrations, db_session
from server.app.canonical_evidence import missing_canonical_chunk_ids, resolve_source_refs
from server.app.domains.questions.bank import _validate_question_payload

LEGACY_BANK_PATH = Path(r"E:\chemistry-rag\data\generated\experiment_question_bank_v1\experiment_question_bank_v1.json")
FORBIDDEN_ALIAS_NAME = "experiment_question_bank_v1_with_ascii_aliases.json"
EXPECTED_SHA256 = "09648686fa90998c4e0965b1cdd7b18b6246f91ebc5617b998cfaa8b3b2b88bd"
EXPECTED_TOTAL = 2310
EXPECTED_EXPERIMENT_COUNT = 77
EXPECTED_PER_EXPERIMENT = 30
EXPECTED_PER_TYPE = 10
QUESTION_TYPES = ("single_choice", "true_false", "fill_blank")


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False)


def _json_array(value: Any) -> str:
    return json.dumps(value if value is not None else [], ensure_ascii=False)


def load_question_bank(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]], str]:
    if path.name == FORBIDDEN_ALIAS_NAME:
        raise ValueError(f"Refusing to import forbidden backup file: {path}")
    raw = path.read_bytes()
    sha256 = hashlib.sha256(raw).hexdigest()
    if sha256 != EXPECTED_SHA256:
        raise ValueError(f"Question bank SHA256 mismatch: expected {EXPECTED_SHA256}, got {sha256}")
    payload = json.loads(raw.decode("utf-8-sig"))
    rows = payload.get("questions") if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError("Question bank JSON must be a list or an object with a questions list")
    return payload if isinstance(payload, dict) else {}, rows, sha256


def formal_experiments_by_id(session: Any) -> dict[str, dict[str, Any]]:
    rows = session.execute(
        text(
            """
            SELECT fe.id,
                   fe.code,
                   fe.title,
                   COALESCE(
                     array_agg(ecb.chapter_id ORDER BY ecb.sort_order, ecb.chapter_id)
                       FILTER (WHERE ecb.chapter_id IS NOT NULL),
                     '{}'
                   ) AS chapter_ids
            FROM formal_experiments fe
            LEFT JOIN experiment_chapter_bindings ecb ON ecb.experiment_id = fe.id
            WHERE fe.status <> 'archived'
            GROUP BY fe.id, fe.code, fe.title, fe.display_order
            ORDER BY fe.display_order, fe.code
            """
        )
    ).mappings()
    return {str(row["id"]): dict(row) for row in rows}


def validate_rows(rows: list[dict[str, Any]], formal_by_id: dict[str, dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    errors: list[str] = []
    normalized_rows: list[dict[str, Any]] = []
    by_experiment: Counter[str] = Counter()
    by_experiment_type: dict[str, Counter[str]] = defaultdict(Counter)
    title_mismatches: dict[str, dict[str, Any]] = {}
    chapter_mismatches: dict[str, dict[str, Any]] = {}
    answer_distribution: dict[str, Counter[Any]] = {
        "single_choice": Counter(),
        "true_false": Counter(),
        "fill_blank": Counter(),
    }

    if len(rows) != EXPECTED_TOTAL:
        errors.append(f"Expected {EXPECTED_TOTAL} questions, got {len(rows)}")

    formal_ids = set(formal_by_id)
    seen_experiment_ids: set[str] = set()
    for index, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            errors.append(f"row {index}: row must be an object")
            continue
        experiment_id = str(row.get("experiment_id") or "")
        seen_experiment_ids.add(experiment_id)
        formal = formal_by_id.get(experiment_id)
        if not formal:
            errors.append(f"row {index}: unknown experiment_id {experiment_id}")
            continue
        if row.get("experiment_code") != formal["code"]:
            errors.append(f"row {index}: experiment_code mismatch for {experiment_id}")
        if row.get("experiment_title") != formal["title"]:
            mismatch = title_mismatches.setdefault(
                experiment_id,
                {
                    "experiment_code": formal["code"],
                    "question_bank_title": row.get("experiment_title"),
                    "formal_title": formal["title"],
                    "question_count": 0,
                },
            )
            mismatch["question_count"] += 1
        if row.get("status") != "draft":
            errors.append(f"row {index}: status must be draft")
        if row.get("bank_kind") != "default":
            errors.append(f"row {index}: bank_kind must be default")
        if row.get("difficulty") != "basic":
            errors.append(f"row {index}: difficulty must be basic")
        if row.get("related_knowledge_point_ids") not in ([], None):
            errors.append(f"row {index}: related_knowledge_point_ids must stay empty")
        chapter_ids = list(row.get("related_chapter_ids") or [])
        if chapter_ids and not set(chapter_ids).issubset(set(formal.get("chapter_ids") or [])):
            mismatch = chapter_mismatches.setdefault(
                experiment_id,
                {
                    "experiment_code": formal["code"],
                    "question_bank_chapter_ids": chapter_ids,
                    "formal_chapter_ids": list(formal.get("chapter_ids") or []),
                    "question_count": 0,
                },
            )
            mismatch["question_count"] += 1

        normalized, validation_errors = _validate_question_payload(row)
        if validation_errors or normalized is None:
            errors.append(f"row {index}: {'; '.join(validation_errors)}")
            continue
        normalized["related_chapter_ids"] = list(formal.get("chapter_ids") or chapter_ids)

        question_type = normalized["question_type"]
        by_experiment[experiment_id] += 1
        by_experiment_type[experiment_id][question_type] += 1
        answer = normalized["answer"]
        if question_type == "single_choice":
            answer_distribution[question_type][answer.get("value")] += 1
        elif question_type == "true_false":
            answer_distribution[question_type][answer.get("value")] += 1
        else:
            answer_distribution[question_type]["items"] += 1

        normalized_rows.append(
            {
                "experiment_id": experiment_id,
                "experiment_code": row.get("experiment_code"),
                "experiment_title": row.get("experiment_title"),
                "bank_kind": row.get("bank_kind") or "default",
                **normalized,
                "metadata": {
                    "source_experiment_code": row.get("experiment_code"),
                    "source_experiment_title": row.get("experiment_title"),
                    "source_related_chapter_ids": chapter_ids,
                    "import_version": "experiment_question_bank_v1",
                },
            }
        )

    missing = sorted(formal_ids - seen_experiment_ids)
    extra = sorted(seen_experiment_ids - formal_ids)
    if len(seen_experiment_ids) != EXPECTED_EXPERIMENT_COUNT:
        errors.append(f"Expected {EXPECTED_EXPERIMENT_COUNT} covered experiments, got {len(seen_experiment_ids)}")
    if missing:
        errors.append(f"Missing formal experiments: {missing[:10]}")
    if extra:
        errors.append(f"Extra experiment ids: {extra[:10]}")
    for experiment_id in sorted(formal_ids):
        total = by_experiment[experiment_id]
        if total != EXPECTED_PER_EXPERIMENT:
            errors.append(f"{experiment_id}: expected {EXPECTED_PER_EXPERIMENT} questions, got {total}")
        for question_type in QUESTION_TYPES:
            type_count = by_experiment_type[experiment_id][question_type]
            if type_count != EXPECTED_PER_TYPE:
                errors.append(f"{experiment_id}: expected {EXPECTED_PER_TYPE} {question_type}, got {type_count}")

    if errors:
        raise ValueError("Question bank validation failed:\n" + "\n".join(errors[:80]))

    report = {
        "question_count": len(normalized_rows),
        "experiment_count": len(seen_experiment_ids),
        "type_counts": dict(Counter(row["question_type"] for row in normalized_rows)),
        "answer_distribution": {
            key: {str(k): v for k, v in counter.items()}
            for key, counter in answer_distribution.items()
        },
        "title_mismatch_count": len(title_mismatches),
        "title_mismatches": list(title_mismatches.values()),
        "chapter_mismatch_count": len(chapter_mismatches),
        "chapter_mismatches": list(chapter_mismatches.values()),
    }
    return normalized_rows, report


def replace_default_bank_questions(
    session: Any,
    rows: list[dict[str, Any]],
    *,
    source_file: Path,
    source_sha256: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    experiment_ids = sorted({row["experiment_id"] for row in rows})
    import_id = str(
        session.execute(
            text(
                """
                INSERT INTO experiment_question_imports (
                  source_file, status, total_rows, valid_rows, invalid_rows, errors, metadata
                )
                VALUES (:source_file, 'validating', :total_rows, 0, 0, '[]'::jsonb, CAST(:metadata AS jsonb))
                RETURNING id
                """
            ),
            {
                "source_file": str(source_file),
                "total_rows": len(rows),
                "metadata": _json(
                    {
                        "source_sha256": source_sha256,
                        "source_metadata": metadata,
                        "replace_default_bank": True,
                    }
                ),
            },
        ).scalar_one()
    )

    bank_ids: dict[str, str] = {}
    for experiment_id in experiment_ids:
        bank_id = str(
            session.execute(
                text(
                    """
                    INSERT INTO experiment_question_banks (
                      experiment_id, bank_kind, title, status, source_label, metadata, updated_at
                    )
                    VALUES (
                      :experiment_id, 'default', '默认离线题库', 'draft',
                      'experiment_question_bank_v1', CAST(:metadata AS jsonb), now()
                    )
                    ON CONFLICT (experiment_id, bank_kind) DO UPDATE SET
                      title = EXCLUDED.title,
                      status = 'draft',
                      source_label = EXCLUDED.source_label,
                      metadata = EXCLUDED.metadata,
                      updated_at = now()
                    RETURNING id
                    """
                ),
                {
                    "experiment_id": experiment_id,
                    "metadata": _json({"source_sha256": source_sha256, "import_id": import_id}),
                },
            ).scalar_one()
        )
        bank_ids[experiment_id] = bank_id

    deleted = session.execute(
        text(
            """
            DELETE FROM experiment_questions q
            USING experiment_question_banks b
            WHERE q.bank_id = b.id
              AND b.bank_kind = 'default'
              AND b.experiment_id = ANY(:experiment_ids)
            """
        ),
        {"experiment_ids": experiment_ids},
    ).rowcount

    for row in rows:
        session.execute(
            text(
                """
                INSERT INTO experiment_questions (
                  bank_id, experiment_id, question_type, stem, options, answer,
                  explanation, difficulty, related_chapter_ids, related_knowledge_point_ids,
                  source_chunk_ids, source_refs, status, metadata, updated_at
                )
                VALUES (
                  CAST(:bank_id AS uuid), :experiment_id, :question_type, :stem,
                  CAST(:options AS jsonb), CAST(:answer AS jsonb), :explanation,
                  :difficulty, :related_chapter_ids, :related_knowledge_point_ids,
                  :source_chunk_ids, CAST(:source_refs AS jsonb), :status,
                  CAST(:metadata AS jsonb), now()
                )
                """
            ),
            {
                "bank_id": bank_ids[row["experiment_id"]],
                "experiment_id": row["experiment_id"],
                "question_type": row["question_type"],
                "stem": row["stem"],
                "options": _json_array(row["options"]),
                "answer": _json(row["answer"]),
                "explanation": row["explanation"],
                "difficulty": row["difficulty"],
                "related_chapter_ids": row["related_chapter_ids"],
                "related_knowledge_point_ids": row["related_knowledge_point_ids"],
                "source_chunk_ids": row["source_chunk_ids"],
                "source_refs": _json_array(row["source_refs"]),
                "status": row["status"],
                "metadata": _json(row["metadata"]),
            },
        )

    session.execute(
        text(
            """
            UPDATE experiment_question_imports
            SET status = 'succeeded',
                valid_rows = :valid_rows,
                invalid_rows = 0,
                errors = '[]'::jsonb,
                updated_at = now()
            WHERE id = CAST(:import_id AS uuid)
            """
        ),
        {"import_id": import_id, "valid_rows": len(rows)},
    )
    return {
        "import_id": import_id,
        "deleted_existing_questions": max(int(deleted or 0), 0),
        "inserted_questions": len(rows),
        "bank_count": len(bank_ids),
    }


def attach_canonical_source_refs(session: Any, rows: list[dict[str, Any]]) -> dict[str, Any]:
    all_chunk_ids = sorted({chunk_id for row in rows for chunk_id in row.get("source_chunk_ids") or []})
    missing = missing_canonical_chunk_ids(session, all_chunk_ids)
    if missing:
        raise ValueError(
            "Question bank references missing canonical source chunks:\n"
            + "\n".join(missing[:80])
        )
    refs_by_id = {str(ref["chunk_id"]): ref for ref in resolve_source_refs(session, all_chunk_ids)}
    rows_with_refs = 0
    for row in rows:
        source_chunk_ids = [str(chunk_id) for chunk_id in row.get("source_chunk_ids") or []]
        row["source_refs"] = [refs_by_id[chunk_id] for chunk_id in source_chunk_ids if chunk_id in refs_by_id]
        if row["source_refs"]:
            rows_with_refs += 1
    return {
        "referenced_chunk_count": len(all_chunk_ids),
        "rows_with_source_refs": rows_with_refs,
    }


def update_experiment_evidence_coverage(session: Any, rows: list[dict[str, Any]]) -> dict[str, Any]:
    experiments_by_chunk: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        experiment_id = str(row.get("experiment_id") or "")
        if not experiment_id:
            continue
        for chunk_id in row.get("source_chunk_ids") or []:
            experiments_by_chunk[str(chunk_id)].add(experiment_id)

    updated = 0
    for chunk_id, experiment_ids in experiments_by_chunk.items():
        existing = (
            session.execute(
                text("SELECT related_experiment_ids FROM source_chunks WHERE id = :chunk_id"),
                {"chunk_id": chunk_id},
            )
            .scalar_one_or_none()
            or []
        )
        merged = sorted(set(existing).union(experiment_ids))
        session.execute(
            text(
                """
                UPDATE source_chunks
                SET related_experiment_ids = :experiment_ids,
                    updated_at = now()
                WHERE id = :chunk_id
                """
            ),
            {"chunk_id": chunk_id, "experiment_ids": merged},
        )
        updated += 1
    return {
        "experiment_evidence_chunk_count": updated,
        "experiment_evidence_link_count": sum(len(value) for value in experiments_by_chunk.values()),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Import the legacy flat offline experiment question bank. "
            "The current catalog-outline baseline intentionally keeps experiment question banks empty "
            "until fresh catalog-node evidence is generated."
        )
    )
    parser.add_argument("--file", type=Path)
    parser.add_argument("--skip-migrations", action="store_true")
    args = parser.parse_args()

    if args.file is None:
        raise SystemExit(
            "This legacy importer no longer has a default file. "
            "Pass --file explicitly only for historical recovery. "
            "The production seed bank is currently empty until catalog-node evidence is regenerated. "
            f"Previous legacy path was: {LEGACY_BANK_PATH}"
        )

    if not args.skip_migrations:
        apply_migrations()

    payload, raw_rows, sha256 = load_question_bank(args.file)
    with db_session() as session:
        formal_by_id = formal_experiments_by_id(session)
        normalized_rows, validation_report = validate_rows(raw_rows, formal_by_id)
        source_ref_report = attach_canonical_source_refs(session, normalized_rows)
        evidence_coverage_report = update_experiment_evidence_coverage(session, normalized_rows)
        import_report = replace_default_bank_questions(
            session,
            normalized_rows,
            source_file=args.file,
            source_sha256=sha256,
            metadata=payload.get("metadata") if isinstance(payload, dict) else {},
        )

    result = {
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "source_file": str(args.file),
        "source_sha256": sha256,
        **validation_report,
        **source_ref_report,
        **evidence_coverage_report,
        **import_report,
    }
    sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
