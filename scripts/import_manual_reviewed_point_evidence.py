from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.app.infrastructure.database import apply_migrations, db_session
from server.app.domains.experiment_points.canonical_points import candidate_point_key as _candidate_point_key

DEFAULT_EVIDENCE_PATH = ROOT / "data" / "seed" / "point_evidence" / "manual_reviewed_point_evidence.jsonl"

ALLOWED_GRADES = {"pass", "usable", "weak_but_best_available"}


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc
        if not isinstance(row, dict):
            raise ValueError(f"Line {line_number} must be a JSON object")
        rows.append(row)
    return rows


def _formal_points(session: Any) -> dict[tuple[str, str], str]:
    rows = session.execute(
        text(
            """
            SELECT id, metadata
            FROM formal_experiments
            WHERE status <> 'archived'
            """
        )
    ).mappings()
    points: dict[tuple[str, str], str] = {}
    for row in rows:
        experiment_id = str(row["id"])
        metadata = row.get("metadata") if isinstance(row.get("metadata"), dict) else {}
        candidates = metadata.get("video_candidates") if isinstance(metadata, dict) else []
        if not isinstance(candidates, list):
            continue
        seen_titles: set[str] = set()
        for index, raw_title in enumerate(candidates):
            title = str(raw_title or "").strip()
            if not title or title in seen_titles:
                continue
            seen_titles.add(title)
            points[(experiment_id, _candidate_point_key(index, title))] = title
    return points


def _existing_chunk_ids(session: Any, chunk_ids: set[str]) -> set[str]:
    if not chunk_ids:
        return set()
    rows = session.execute(
        text("SELECT id FROM source_chunks WHERE id = ANY(:chunk_ids)"),
        {"chunk_ids": sorted(chunk_ids)},
    ).mappings()
    return {str(row["id"]) for row in rows}


def _normalize_rows(rows: list[dict[str, Any]], formal_points: dict[tuple[str, str], str], existing_chunks: set[str]) -> list[dict[str, Any]]:
    errors: list[str] = []
    normalized: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for index, row in enumerate(rows, start=1):
        experiment_id = str(row.get("experiment_id") or "").strip()
        point_key = str(row.get("point_key") or "").strip()
        key = (experiment_id, point_key)
        if not experiment_id:
            errors.append(f"row {index}: experiment_id is required")
        if not point_key:
            errors.append(f"row {index}: point_key is required")
        if key in seen:
            errors.append(f"row {index}: duplicate point binding {experiment_id}/{point_key}")
        seen.add(key)
        if key not in formal_points:
            errors.append(f"row {index}: point_key does not resolve to formal_experiments metadata: {experiment_id}/{point_key}")

        experiment_chunk_ids = [str(item).strip() for item in row.get("experiment_chunk_ids") or [] if str(item).strip()]
        theory_chunk_ids = [str(item).strip() for item in row.get("theory_chunk_ids") or [] if str(item).strip()]
        if not experiment_chunk_ids:
            errors.append(f"row {index}: experiment_chunk_ids cannot be empty")
        if not theory_chunk_ids:
            errors.append(f"row {index}: theory_chunk_ids cannot be empty")
        for chunk_id in [*experiment_chunk_ids, *theory_chunk_ids]:
            if chunk_id not in existing_chunks:
                errors.append(f"row {index}: missing source chunk {chunk_id}")

        manual_reviewed = row.get("manual_reviewed")
        if manual_reviewed is not True:
            errors.append(f"row {index}: manual_reviewed must be true")
        review_grade = str(row.get("review_grade") or "").strip()
        if review_grade not in ALLOWED_GRADES:
            errors.append(f"row {index}: invalid review_grade {review_grade!r}")

        normalized.append(
            {
                "experiment_id": experiment_id,
                "experiment_code": str(row.get("experiment_code") or "").strip(),
                "point_key": point_key,
                "point_title": str(row.get("point_title") or formal_points.get(key) or point_key).strip(),
                "experiment_chunk_ids": experiment_chunk_ids,
                "theory_chunk_ids": theory_chunk_ids,
                "manual_reviewed": bool(manual_reviewed),
                "review_grade": review_grade,
            }
        )
    if errors:
        preview = "\n".join(errors[:20])
        suffix = f"\n... {len(errors) - 20} more error(s)" if len(errors) > 20 else ""
        raise ValueError(f"Manual reviewed point evidence validation failed:\n{preview}{suffix}")
    return normalized


def import_point_evidence(path: Path, *, skip_migrations: bool = False, source_label: str | None = None) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    if not skip_migrations:
        apply_migrations()
    rows = _load_jsonl(path)
    all_chunk_ids = {
        str(chunk_id)
        for row in rows
        for chunk_id in [*(row.get("experiment_chunk_ids") or []), *(row.get("theory_chunk_ids") or [])]
        if str(chunk_id).strip()
    }
    label = source_label or path.parent.name
    with db_session() as session:
        formal_points = _formal_points(session)
        existing_chunks = _existing_chunk_ids(session, all_chunk_ids)
        normalized = _normalize_rows(rows, formal_points, existing_chunks)
        for row in normalized:
            session.execute(
                text(
                    """
                    INSERT INTO experiment_video_point_evidence (
                      experiment_id, point_key, experiment_code, point_title,
                      experiment_chunk_ids, theory_chunk_ids, manual_reviewed,
                      review_grade, source_label, metadata, updated_at
                    )
                    VALUES (
                      :experiment_id, :point_key, :experiment_code, :point_title,
                      :experiment_chunk_ids, :theory_chunk_ids, :manual_reviewed,
                      :review_grade, :source_label, CAST(:metadata AS jsonb), now()
                    )
                    ON CONFLICT (experiment_id, point_key) DO UPDATE SET
                      experiment_code = EXCLUDED.experiment_code,
                      point_title = EXCLUDED.point_title,
                      experiment_chunk_ids = EXCLUDED.experiment_chunk_ids,
                      theory_chunk_ids = EXCLUDED.theory_chunk_ids,
                      manual_reviewed = EXCLUDED.manual_reviewed,
                      review_grade = EXCLUDED.review_grade,
                      source_label = EXCLUDED.source_label,
                      metadata = EXCLUDED.metadata,
                      updated_at = now()
                    """
                ),
                {
                    **row,
                    "source_label": label,
                    "metadata": _json({"artifact_path": str(path)}),
                },
            )
    grade_counts = Counter(row["review_grade"] for row in normalized)
    return {
        "artifact": str(path),
        "source_label": label,
        "row_count": len(normalized),
        "grade_counts": dict(grade_counts),
        "experiment_count": len({row["experiment_id"] for row in normalized}),
        "chunk_reference_count": len(all_chunk_ids),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Import retired manual-reviewed video point evidence bindings.")
    parser.add_argument("--path", type=Path, default=DEFAULT_EVIDENCE_PATH)
    parser.add_argument("--source-label", default=None)
    parser.add_argument("--skip-migrations", action="store_true")
    parser.add_argument(
        "--allow-retired-legacy-import",
        action="store_true",
        help="Explicitly run the retired experiment_id + point_key importer for historical recovery only.",
    )
    args = parser.parse_args()
    if not args.allow_retired_legacy_import:
        raise SystemExit(
            "This importer is retired for the current catalog-outline seed. "
            "Old experiment_id + point_key evidence bindings are invalid after reset; "
            "generate fresh catalog-node evidence before rebuilding question banks. "
            "Pass --allow-retired-legacy-import only for historical recovery."
        )
    result = import_point_evidence(args.path, skip_migrations=args.skip_migrations, source_label=args.source_label)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
