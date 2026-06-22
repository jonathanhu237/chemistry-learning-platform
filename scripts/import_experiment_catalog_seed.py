from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.app.domains.catalog_tree.catalog_seed import import_catalog_seed
from server.app.infrastructure.database import apply_migrations, db_session

DEFAULT_IMPORT_REPORT = ROOT / "data" / "seed" / "import_reports" / "catalog_outline_seed_import_report.json"


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Reset retired experiment seed data and import the canonical catalog outline seed. "
            "Canonical RAG chunks, embeddings, analyzer dictionaries, users, roles, courses, and media assets are preserved."
        )
    )
    parser.add_argument("--skip-migrations", action="store_true")
    parser.add_argument("--no-reset", action="store_true", help="Import without clearing retired legacy seed-derived rows.")
    parser.add_argument("--dry-run", action="store_true", help="Validate only; do not write database rows.")
    parser.add_argument("--report", type=Path, default=DEFAULT_IMPORT_REPORT)
    args = parser.parse_args()

    if args.dry_run:
        from server.app.domains.catalog_tree.catalog_seed import validate_catalog_seed_files

        result = validate_catalog_seed_files()
        sys.stdout.buffer.write((json.dumps({"dry_run": True, **result}, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        if not result["ok"]:
            raise SystemExit(1)
        return

    if not args.skip_migrations:
        apply_migrations()

    with db_session() as session:
        result = import_catalog_seed(session, reset=not args.no_reset)

    payload = {
        "report_type": "catalog_outline_seed_import_report",
        "created_at": datetime.now(timezone.utc).isoformat(),
        **result,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sys.stdout.buffer.write((json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
