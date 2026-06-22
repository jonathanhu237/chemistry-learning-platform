from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.app.domains.catalog_tree.teacher_search import (
    TEACHER_CATALOG_SEARCH_INDEX_MAPPING_VERSION,
    teacher_catalog_search_index_mapping,
)
from server.app.domains.video_library.index_client import video_library_analyzer_assets
from server.app.infrastructure.settings import get_settings


def main() -> None:
    mapping = teacher_catalog_search_index_mapping(analyzer=get_settings().teacher_catalog_search_analyzer)
    properties = mapping["mappings"]["properties"]
    required_fields = [
        "node_kind",
        "teacher_note",
        "point_teacher_note",
        "legacy_text",
        "formulae",
        "title_formula_pairs",
        "aliases",
        "reactants",
        "products",
        "participants",
        "equation_formula_pairs",
        "equation_rows",
        "reagent_aliases",
        "condition_tags",
        "phenomenon_tags",
        "property_tags",
        "primary_state",
        "missing_field_keys",
    ]
    assets = video_library_analyzer_assets()
    missing_fields = [field for field in required_fields if field not in properties]
    ok = not missing_fields and bool(assets.get("ok")) and mapping["mappings"]["_meta"]["mapping_version"] == TEACHER_CATALOG_SEARCH_INDEX_MAPPING_VERSION
    payload = {
        "ok": ok,
        "mapping_version": mapping["mappings"]["_meta"]["mapping_version"],
        "index": get_settings().teacher_catalog_search_index,
        "missing_fields": missing_fields,
        "analyzer_assets": assets,
    }
    sys.stdout.buffer.write((json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n").encode("utf-8"))
    if not ok:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
