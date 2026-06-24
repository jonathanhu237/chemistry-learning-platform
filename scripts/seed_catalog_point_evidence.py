from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from sqlalchemy import bindparam, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.app.infrastructure.database import apply_migrations, db_session

DEFAULT_SEED_PATH = ROOT / "data" / "seed" / "experiment_catalog" / "point_textbook_evidence_seed.json"
SEED_TYPE = "catalog_point_textbook_evidence_seed"
SEED_VERSION = 1
TEXTBOOK_EVIDENCE_ROLES = ("principle", "phenomenon", "safety")

STATE_COLUMNS = [
    "node_id",
    "evidence_status",
    "source_mode",
    "trigger_policy",
    "selected_chunk_ids",
    "source_refs",
    "diagnostics",
    "stale_reason",
    "latest_error",
    "refreshed_at",
    "stale_at",
    "last_attempted_at",
    "canonical_point_id",
    "source_placement_node_id",
    "content_fingerprint",
    "config_fingerprint",
]

BINDING_COLUMNS = [
    "node_id",
    "canonical_point_id",
    "source_placement_node_id",
    "chunk_id",
    "evidence_role",
    "selection_status",
    "freshness_status",
    "rank",
    "score",
    "rerank_score",
    "source_metadata",
    "diagnostics",
    "content_fingerprint",
    "config_fingerprint",
]


def _json_param(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False)


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, UUID):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _row_payload(row: Any, columns: list[str]) -> dict[str, Any]:
    return {column: row.get(column) for column in columns}


def export_catalog_point_evidence_seed(session: Any) -> dict[str, Any]:
    state_rows = session.execute(
        text(
            """
            SELECT state.*
            FROM experiment_catalog_point_evidence_state state
            WHERE EXISTS (
              SELECT 1
              FROM experiment_catalog_point_evidence_bindings binding
              WHERE binding.node_id = state.node_id
                AND binding.evidence_role IN ('principle', 'phenomenon', 'safety')
                AND binding.selection_status = 'selected'
                AND binding.freshness_status = 'fresh'
            )
            ORDER BY state.node_id
            """
        )
    ).mappings().all()
    node_ids = [str(row["node_id"]) for row in state_rows]
    if node_ids:
        binding_rows = session.execute(
            text(
                """
                SELECT binding.*
                FROM experiment_catalog_point_evidence_bindings binding
                WHERE binding.node_id IN :node_ids
                  AND binding.evidence_role IN ('principle', 'phenomenon', 'safety')
                  AND binding.selection_status = 'selected'
                  AND binding.freshness_status = 'fresh'
                ORDER BY binding.node_id, binding.evidence_role, binding.rank, binding.chunk_id
                """
            ).bindparams(bindparam("node_ids", expanding=True)),
            {"node_ids": node_ids},
        ).mappings().all()
    else:
        binding_rows = []

    states = [_row_payload(row, STATE_COLUMNS) for row in state_rows]
    bindings = [_row_payload(row, BINDING_COLUMNS) for row in binding_rows]
    return {
        "seed_type": SEED_TYPE,
        "version": SEED_VERSION,
        "exported_at": _iso_now(),
        "description": (
            "Precomputed catalog point to textbook chunk evidence bindings. "
            "This seed contains no API keys and does not include transient duplicate-question fingerprints."
        ),
        "source_tables": [
            "experiment_catalog_point_evidence_state",
            "experiment_catalog_point_evidence_bindings",
        ],
        "evidence_roles": list(TEXTBOOK_EVIDENCE_ROLES),
        "counts": {
            "states": len(states),
            "bindings": len(bindings),
            "unique_nodes": len({item["node_id"] for item in states}),
            "unique_chunks": len({item["chunk_id"] for item in bindings}),
        },
        "states": states,
        "bindings": bindings,
    }


def write_seed(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default) + "\n", encoding="utf-8")


def load_seed(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    if payload.get("seed_type") != SEED_TYPE:
        raise ValueError(f"{path} seed_type must be {SEED_TYPE!r}")
    if int(payload.get("version") or 0) != SEED_VERSION:
        raise ValueError(f"{path} version must be {SEED_VERSION}")
    if not isinstance(payload.get("states"), list) or not isinstance(payload.get("bindings"), list):
        raise ValueError(f"{path} must contain list fields: states and bindings")
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
    states = payload.get("states") or []
    bindings = payload.get("bindings") or []
    node_ids = {str(item.get("node_id") or "").strip() for item in states if isinstance(item, dict)}
    node_ids.update(str(item.get("node_id") or "").strip() for item in bindings if isinstance(item, dict))
    node_ids.discard("")
    chunk_ids = {str(item.get("chunk_id") or "").strip() for item in bindings if isinstance(item, dict)}
    chunk_ids.discard("")

    existing_nodes = _existing_ids(session, table="experiment_catalog_nodes", column="id", ids=node_ids)
    existing_chunks = _existing_ids(session, table="source_chunks", column="id", ids=chunk_ids)
    missing_nodes = sorted(node_ids - existing_nodes)
    missing_chunks = sorted(chunk_ids - existing_chunks)
    return {
        "node_ids": len(node_ids),
        "chunk_ids": len(chunk_ids),
        "missing_nodes": missing_nodes,
        "missing_chunks": missing_chunks,
    }


def _seed_state_params(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "node_id": str(item.get("node_id") or "").strip(),
        "canonical_point_id": item.get("canonical_point_id"),
        "source_placement_node_id": item.get("source_placement_node_id"),
        "evidence_status": item.get("evidence_status") or "succeeded",
        "source_mode": item.get("source_mode") or "qwen_es_textbook_rag",
        "trigger_policy": item.get("trigger_policy") or "stale_until_manual_refresh",
        "selected_chunk_ids": list(item.get("selected_chunk_ids") or []),
        "source_refs": _json_param(item.get("source_refs") or []),
        "diagnostics": _json_param(item.get("diagnostics") or {}),
        "stale_reason": item.get("stale_reason"),
        "latest_error": item.get("latest_error"),
        "refreshed_at": item.get("refreshed_at") or _iso_now(),
        "stale_at": item.get("stale_at"),
        "last_attempted_at": item.get("last_attempted_at") or _iso_now(),
        "content_fingerprint": item.get("content_fingerprint"),
        "config_fingerprint": item.get("config_fingerprint"),
    }


def _seed_binding_params(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "node_id": str(item.get("node_id") or "").strip(),
        "canonical_point_id": item.get("canonical_point_id"),
        "source_placement_node_id": item.get("source_placement_node_id"),
        "chunk_id": str(item.get("chunk_id") or "").strip(),
        "evidence_role": item.get("evidence_role") or "dynamic_rag",
        "selection_status": item.get("selection_status") or "selected",
        "freshness_status": item.get("freshness_status") or "fresh",
        "rank": int(item.get("rank") or 0),
        "score": item.get("score"),
        "rerank_score": item.get("rerank_score"),
        "source_metadata": _json_param(item.get("source_metadata") or {}),
        "diagnostics": _json_param(item.get("diagnostics") or {}),
        "content_fingerprint": item.get("content_fingerprint"),
        "config_fingerprint": item.get("config_fingerprint"),
    }


def import_catalog_point_evidence_seed(session: Any, payload: dict[str, Any], *, replace: bool = True) -> dict[str, Any]:
    references = validate_seed_references(session, payload)
    if references["missing_nodes"]:
        raise ValueError(
            "Seed references catalog nodes that do not exist. Import the catalog outline seed first: "
            + ", ".join(references["missing_nodes"][:10])
        )
    if references["missing_chunks"]:
        raise ValueError(
            "Seed references source chunks that do not exist. Run scripts/import_canonical_evidence.py first: "
            + ", ".join(references["missing_chunks"][:10])
        )

    states = [item for item in payload.get("states") or [] if isinstance(item, dict)]
    bindings = [item for item in payload.get("bindings") or [] if isinstance(item, dict)]
    node_ids = sorted({str(item.get("node_id") or "").strip() for item in states + bindings if item.get("node_id")})
    if replace and node_ids:
        session.execute(
            text(
                """
                DELETE FROM experiment_catalog_point_evidence_bindings
                WHERE node_id IN :node_ids
                  AND evidence_role IN ('principle', 'phenomenon', 'safety')
                """
            ).bindparams(bindparam("node_ids", expanding=True)),
            {"node_ids": node_ids},
        )

    for item in states:
        params = _seed_state_params(item)
        if not params["node_id"]:
            continue
        session.execute(
            text(
                """
                INSERT INTO experiment_catalog_point_evidence_state (
                  node_id, canonical_point_id, source_placement_node_id, evidence_status, source_mode, trigger_policy,
                  selected_chunk_ids, source_refs, diagnostics, stale_reason, latest_error,
                  refreshed_at, stale_at, last_attempted_at, content_fingerprint, config_fingerprint, updated_at
                )
                VALUES (
                  :node_id, :canonical_point_id, :source_placement_node_id, :evidence_status, :source_mode, :trigger_policy,
                  :selected_chunk_ids, CAST(:source_refs AS jsonb), CAST(:diagnostics AS jsonb),
                  :stale_reason, :latest_error, CAST(:refreshed_at AS timestamptz),
                  CAST(:stale_at AS timestamptz), CAST(:last_attempted_at AS timestamptz),
                  :content_fingerprint, :config_fingerprint, now()
                )
                ON CONFLICT (node_id) DO UPDATE SET
                  canonical_point_id = EXCLUDED.canonical_point_id,
                  source_placement_node_id = EXCLUDED.source_placement_node_id,
                  evidence_status = EXCLUDED.evidence_status,
                  source_mode = EXCLUDED.source_mode,
                  trigger_policy = EXCLUDED.trigger_policy,
                  selected_chunk_ids = EXCLUDED.selected_chunk_ids,
                  source_refs = EXCLUDED.source_refs,
                  diagnostics = EXCLUDED.diagnostics,
                  stale_reason = EXCLUDED.stale_reason,
                  latest_error = EXCLUDED.latest_error,
                  refreshed_at = EXCLUDED.refreshed_at,
                  stale_at = EXCLUDED.stale_at,
                  last_attempted_at = EXCLUDED.last_attempted_at,
                  content_fingerprint = EXCLUDED.content_fingerprint,
                  config_fingerprint = EXCLUDED.config_fingerprint,
                  updated_at = now()
                """
            ),
            params,
        )

    imported_bindings = 0
    for item in bindings:
        params = _seed_binding_params(item)
        if not params["node_id"] or not params["chunk_id"]:
            continue
        session.execute(
            text(
                """
                INSERT INTO experiment_catalog_point_evidence_bindings (
                  node_id, canonical_point_id, source_placement_node_id,
                  chunk_id, evidence_role, selection_status, freshness_status,
                  rank, score, rerank_score, source_metadata, diagnostics,
                  content_fingerprint, config_fingerprint, updated_at
                )
                VALUES (
                  :node_id, :canonical_point_id, :source_placement_node_id,
                  :chunk_id, :evidence_role, :selection_status, :freshness_status,
                  :rank, :score, :rerank_score, CAST(:source_metadata AS jsonb),
                  CAST(:diagnostics AS jsonb), :content_fingerprint, :config_fingerprint, now()
                )
                ON CONFLICT (node_id, chunk_id, evidence_role) DO UPDATE SET
                  canonical_point_id = EXCLUDED.canonical_point_id,
                  source_placement_node_id = EXCLUDED.source_placement_node_id,
                  selection_status = EXCLUDED.selection_status,
                  freshness_status = EXCLUDED.freshness_status,
                  rank = EXCLUDED.rank,
                  score = EXCLUDED.score,
                  rerank_score = EXCLUDED.rerank_score,
                  source_metadata = EXCLUDED.source_metadata,
                  diagnostics = EXCLUDED.diagnostics,
                  content_fingerprint = EXCLUDED.content_fingerprint,
                  config_fingerprint = EXCLUDED.config_fingerprint,
                  updated_at = now()
                """
            ),
            params,
        )
        imported_bindings += 1

    return {
        "states": len(states),
        "bindings": imported_bindings,
        "unique_nodes": len(node_ids),
        "replace": replace,
        "reference_check": references,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Export or import precomputed catalog point textbook evidence bindings.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser("export", help="Export current fresh textbook evidence bindings to a seed JSON file.")
    export_parser.add_argument("--output", type=Path, default=DEFAULT_SEED_PATH)

    import_parser = subparsers.add_parser("import", help="Import textbook evidence bindings from a seed JSON file.")
    import_parser.add_argument("--input", type=Path, default=DEFAULT_SEED_PATH)
    import_parser.add_argument("--skip-migrations", action="store_true")
    import_parser.add_argument("--merge", action="store_true", help="Upsert without first deleting existing textbook evidence rows.")
    import_parser.add_argument("--dry-run", action="store_true", help="Validate seed references without writing rows.")

    args = parser.parse_args()
    if args.command == "export":
        with db_session() as session:
            payload = export_catalog_point_evidence_seed(session)
        write_seed(args.output, payload)
        sys.stdout.buffer.write((json.dumps({"output": str(args.output), "counts": payload["counts"]}, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        return

    if not args.skip_migrations:
        apply_migrations()
    payload = load_seed(args.input)
    with db_session() as session:
        if args.dry_run:
            result = {
                "dry_run": True,
                "counts": payload.get("counts") or {},
                "reference_check": validate_seed_references(session, payload),
            }
        else:
            result = import_catalog_point_evidence_seed(session, payload, replace=not args.merge)
    sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
