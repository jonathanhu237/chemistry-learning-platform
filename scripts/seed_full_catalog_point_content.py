from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import bindparam, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.app.domains.catalog_tree.equations import list_reaction_equations, replace_reaction_equations
from server.app.infrastructure.database import apply_migrations, db_session

DEFAULT_SEED_PATH = ROOT / "data" / "seed" / "experiment_catalog" / "full_point_content_seed.json"
SEED_TYPE = "full_catalog_point_content_seed"
SEED_VERSION = 1
EXPECTED_RECORD_COUNT = 393

CONTENT_COLUMNS = [
    "node_id",
    "canonical_point_id",
    "point_title",
    "teacher_note",
    "principle_mode",
    "principle_equation",
    "principle_text",
    "phenomenon_explanation",
    "safety_note",
    "content_status",
    "published_at",
    "metadata",
    "created_at",
    "updated_at",
]


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _json_param(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=_json_default)


def _row_payload(row: Any, columns: list[str]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for column in columns:
        value = row.get(column)
        if isinstance(value, datetime):
            value = value.isoformat()
        elif isinstance(value, date):
            value = value.isoformat()
        elif value is not None and not isinstance(value, (str, int, float, bool, dict, list)):
            value = str(value)
        payload[column] = value
    return payload


def _summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(str(item.get("content_status") or "") for item in records)
    mode_counts = Counter(str(item.get("principle_mode") or "") for item in records)
    return {
        "records": len(records),
        "status_counts": dict(status_counts),
        "principle_mode_counts": dict(mode_counts),
        "published_records": status_counts.get("published", 0),
        "equation_mode_records": mode_counts.get("equation", 0),
        "text_mode_records": mode_counts.get("text", 0),
        "reaction_equation_rows": sum(len(item.get("reaction_equations") or []) for item in records),
        "records_with_principle_text": sum(1 for item in records if item.get("principle_text")),
        "records_with_principle_equation": sum(1 for item in records if item.get("principle_equation")),
        "records_with_phenomenon_explanation": sum(1 for item in records if item.get("phenomenon_explanation")),
        "records_with_safety_note": sum(1 for item in records if item.get("safety_note")),
    }


def export_seed(session: Any) -> dict[str, Any]:
    rows = session.execute(
        text(
            """
            SELECT pc.node_id, pc.canonical_point_id, pc.point_title, pc.teacher_note,
                   pc.principle_mode, pc.principle_equation, pc.principle_text,
                   pc.phenomenon_explanation, pc.safety_note, pc.content_status,
                   pc.published_at, pc.metadata, pc.created_at, pc.updated_at
            FROM experiment_catalog_point_content pc
            JOIN experiment_catalog_nodes n ON n.id = pc.node_id
            WHERE n.node_kind = 'point'
            ORDER BY n.chapter_id, n.parent_id NULLS FIRST, n.display_order, n.id
            """
        )
    ).mappings().all()
    records = []
    for row in rows:
        record = _row_payload(row, CONTENT_COLUMNS)
        record["reaction_equations"] = (
            list_reaction_equations(session, str(row["node_id"]), canonical_point_id=row.get("canonical_point_id"))
            if record.get("principle_mode") == "equation"
            else []
        )
        records.append(record)
    return {
        "seed_type": SEED_TYPE,
        "version": SEED_VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "description": "Full current catalog point three-part content seed for blank-server bootstrap.",
        "expected_counts": {"records": EXPECTED_RECORD_COUNT},
        "summary": _summary(records),
        "records": records,
    }


def write_seed(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default) + "\n", encoding="utf-8")


def load_seed(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    if payload.get("seed_type") != SEED_TYPE:
        raise ValueError(f"{path} seed_type must be {SEED_TYPE!r}")
    if int(payload.get("version") or 0) != SEED_VERSION:
        raise ValueError(f"{path} version must be {SEED_VERSION}")
    if not isinstance(payload.get("records"), list):
        raise ValueError(f"{path} records must be a list")
    return payload


def _existing_ids(session: Any, *, table: str, column: str, ids: set[str]) -> set[str]:
    if not ids:
        return set()
    rows = session.execute(
        text(f"SELECT {column} FROM {table} WHERE {column} IN :ids").bindparams(bindparam("ids", expanding=True)),
        {"ids": sorted(ids)},
    ).all()
    return {str(row[0]) for row in rows}


def validate_seed_references(session: Any, payload: dict[str, Any]) -> dict[str, Any]:
    records = [item for item in payload.get("records") or [] if isinstance(item, dict)]
    node_ids = {str(item.get("node_id") or "").strip() for item in records if str(item.get("node_id") or "").strip()}
    canonical_point_ids = {
        str(item.get("canonical_point_id") or "").strip()
        for item in records
        if str(item.get("canonical_point_id") or "").strip()
    }
    existing_nodes = _existing_ids(session, table="experiment_catalog_nodes", column="id", ids=node_ids)
    existing_points = _existing_ids(
        session,
        table="experiment_catalog_points",
        column="id",
        ids=canonical_point_ids,
    )
    return {
        "node_ids": len(node_ids),
        "canonical_point_ids": len(canonical_point_ids),
        "missing_node_ids": sorted(node_ids - existing_nodes),
        "missing_canonical_point_ids": sorted(canonical_point_ids - existing_points),
    }


def validate_seed_payload(payload: dict[str, Any], *, session: Any | None = None) -> dict[str, Any]:
    records = [item for item in payload.get("records") or [] if isinstance(item, dict)]
    errors: list[str] = []
    if len(records) != EXPECTED_RECORD_COUNT:
        errors.append(f"records: expected {EXPECTED_RECORD_COUNT}, got {len(records)}")
    node_ids: set[str] = set()
    for index, record in enumerate(records, start=1):
        node_id = str(record.get("node_id") or "").strip()
        if not node_id:
            errors.append(f"records[{index}]: node_id is required")
        elif node_id in node_ids:
            errors.append(f"records[{index}]: duplicate node_id {node_id}")
        node_ids.add(node_id)
        if not str(record.get("point_title") or "").strip():
            errors.append(f"records[{index}]: point_title is required")
        if record.get("principle_mode") not in {"equation", "text"}:
            errors.append(f"records[{index}]: principle_mode must be equation or text")
        if record.get("principle_mode") == "equation" and not isinstance(record.get("reaction_equations"), list):
            errors.append(f"records[{index}]: reaction_equations must be a list")
        if not str(record.get("phenomenon_explanation") or "").strip():
            errors.append(f"records[{index}]: phenomenon_explanation is required")
        if not str(record.get("safety_note") or "").strip():
            errors.append(f"records[{index}]: safety_note is required")
    references = None
    if session is not None:
        references = validate_seed_references(session, payload)
        for key in ["missing_node_ids", "missing_canonical_point_ids"]:
            missing = references.get(key) or []
            if missing:
                errors.append(f"{key}: {', '.join(missing[:20])}")
    return {"ok": not errors, "errors": errors, "summary": _summary(records), "references": references}


def import_seed(session: Any, payload: dict[str, Any]) -> dict[str, Any]:
    validation = validate_seed_payload(payload, session=session)
    if not validation["ok"]:
        raise ValueError("Full catalog point-content seed validation failed:\n" + "\n".join(validation["errors"][:80]))
    records = [item for item in payload.get("records") or [] if isinstance(item, dict)]
    imported = 0
    reaction_rows = 0
    for record in records:
        node_id = str(record.get("node_id") or "").strip()
        mode = str(record.get("principle_mode") or "text").strip()
        reaction_equations = record.get("reaction_equations") if isinstance(record.get("reaction_equations"), list) else []
        session.execute(
            text(
                """
                INSERT INTO experiment_catalog_point_content (
                  node_id, canonical_point_id, point_title, teacher_note, principle_mode,
                  principle_equation, principle_text, phenomenon_explanation, safety_note,
                  content_status, published_at, published_by, created_by, updated_by,
                  metadata, created_at, updated_at
                )
                VALUES (
                  :node_id, :canonical_point_id, :point_title, :teacher_note, :principle_mode,
                  :principle_equation, :principle_text, :phenomenon_explanation, :safety_note,
                  :content_status, CAST(:published_at AS timestamptz), NULL, NULL, NULL,
                  CAST(:metadata AS jsonb), COALESCE(CAST(:created_at AS timestamptz), now()),
                  COALESCE(CAST(:updated_at AS timestamptz), now())
                )
                ON CONFLICT (node_id) DO UPDATE SET
                  canonical_point_id = EXCLUDED.canonical_point_id,
                  point_title = EXCLUDED.point_title,
                  teacher_note = EXCLUDED.teacher_note,
                  principle_mode = EXCLUDED.principle_mode,
                  principle_equation = EXCLUDED.principle_equation,
                  principle_text = EXCLUDED.principle_text,
                  phenomenon_explanation = EXCLUDED.phenomenon_explanation,
                  safety_note = EXCLUDED.safety_note,
                  content_status = EXCLUDED.content_status,
                  published_at = COALESCE(EXCLUDED.published_at, experiment_catalog_point_content.published_at, now()),
                  published_by = NULL,
                  created_by = NULL,
                  updated_by = NULL,
                  metadata = EXCLUDED.metadata,
                  updated_at = EXCLUDED.updated_at
                """
            ),
            {
                "node_id": node_id,
                "canonical_point_id": record.get("canonical_point_id"),
                "point_title": record.get("point_title"),
                "teacher_note": record.get("teacher_note") or "",
                "principle_mode": mode,
                "principle_equation": record.get("principle_equation"),
                "principle_text": record.get("principle_text"),
                "phenomenon_explanation": record.get("phenomenon_explanation") or "",
                "safety_note": record.get("safety_note") or "",
                "content_status": record.get("content_status") or "published",
                "published_at": record.get("published_at"),
                "metadata": _json_param(record.get("metadata") or {}),
                "created_at": record.get("created_at"),
                "updated_at": record.get("updated_at"),
            },
        )
        replace_reaction_equations(
            session,
            node_id=node_id,
            canonical_point_id=record.get("canonical_point_id"),
            equations=reaction_equations if mode == "equation" else [],
        )
        imported += 1
        reaction_rows += len(reaction_equations) if mode == "equation" else 0
    return {"records": imported, "reaction_equation_rows": reaction_rows, "validation": validation}


def main() -> None:
    parser = argparse.ArgumentParser(description="Export, import, or validate full catalog point-content seed data.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--path", type=Path, default=DEFAULT_SEED_PATH)
    export_parser.add_argument("--skip-migrations", action="store_true")

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--path", type=Path, default=DEFAULT_SEED_PATH)
    validate_parser.add_argument("--skip-db", action="store_true")

    import_parser = subparsers.add_parser("import")
    import_parser.add_argument("--path", type=Path, default=DEFAULT_SEED_PATH)
    import_parser.add_argument("--skip-migrations", action="store_true")

    args = parser.parse_args()
    if args.command == "export":
        if not args.skip_migrations:
            apply_migrations()
        with db_session() as session:
            payload = export_seed(session)
            validation = validate_seed_payload(payload, session=session)
            if not validation["ok"]:
                raise SystemExit("Exported seed failed validation:\n" + "\n".join(validation["errors"][:80]))
        write_seed(args.path, payload)
        sys.stdout.buffer.write((json.dumps({"path": str(args.path), **validation}, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        return

    payload = load_seed(args.path)
    if args.command == "validate":
        if args.skip_db:
            result = validate_seed_payload(payload)
        else:
            with db_session() as session:
                result = validate_seed_payload(payload, session=session)
        sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        if not result["ok"]:
            raise SystemExit(1)
        return

    if args.command == "import":
        if not args.skip_migrations:
            apply_migrations()
        with db_session() as session:
            result = import_seed(session, payload)
        sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
