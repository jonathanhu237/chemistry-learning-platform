from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.app.domains.catalog_tree.catalog_seed import (
    CATALOG_SEED_VALIDATION_REPORT_PATH,
    CATALOG_TREE_SEED_PATH,
    POINT_CONTENT_SEED_PATH,
    validate_catalog_seed_files,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the committed experiment catalog outline seed.")
    parser.add_argument("--catalog", type=Path, default=CATALOG_TREE_SEED_PATH)
    parser.add_argument("--content", type=Path, default=POINT_CONTENT_SEED_PATH)
    parser.add_argument("--report", type=Path, default=CATALOG_SEED_VALIDATION_REPORT_PATH)
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args()

    result = validate_catalog_seed_files(catalog_path=args.catalog, content_path=args.content)
    if args.write_report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
