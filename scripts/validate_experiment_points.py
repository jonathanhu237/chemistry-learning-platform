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
                      COUNT(*) FILTER (WHERE n.node_kind IN ('point', 'hybrid')) AS point_node_count,
                      COUNT(*) FILTER (
                        WHERE n.node_kind IN ('point', 'hybrid')
                          AND pc.node_id IS NOT NULL
                      ) AS point_content_count,
                      COUNT(*) FILTER (
                        WHERE n.node_kind IN ('point', 'hybrid')
                          AND pc.content_status = 'published'
                      ) AS published_content_count,
                      COUNT(*) FILTER (
                        WHERE n.node_kind IN ('point', 'hybrid')
                          AND pc.teacher_note IS NOT NULL
                          AND btrim(pc.teacher_note) <> ''
                      ) AS teacher_note_count,
                      COUNT(*) FILTER (
                        WHERE n.node_kind IN ('point', 'hybrid')
                          AND si.node_id IS NOT NULL
                      ) AS search_state_count
                    FROM experiment_catalog_nodes n
                    LEFT JOIN experiment_catalog_point_content pc ON pc.node_id = n.id
                    LEFT JOIN experiment_catalog_point_search_index_state si ON si.node_id = n.id
                    """
                )
            ).mappings().one()
            legacy_row = session.execute(
                text(
                    """
                    SELECT
                      COUNT(*) AS legacy_point_map_count,
                      COUNT(*) FILTER (WHERE n.id IS NULL) AS broken_legacy_maps
                    FROM experiment_catalog_legacy_identity_map lm
                    LEFT JOIN experiment_catalog_nodes n ON n.id = lm.catalog_node_id
                    WHERE lm.legacy_kind = 'point'
                       OR lm.legacy_kind = 'experiment_point'
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

    point_node_count = int(row["point_node_count"] or 0)
    point_content_count = int(row["point_content_count"] or 0)
    legacy_point_map_count = int(legacy_row["legacy_point_map_count"] or 0)
    broken_legacy_maps = int(legacy_row["broken_legacy_maps"] or 0)
    errors: list[str] = []
    if point_node_count <= 0:
        errors.append("no catalog point nodes found")
    if point_content_count < point_node_count:
        errors.append(f"catalog point content missing: {point_node_count - point_content_count}")
    if legacy_point_map_count < point_node_count:
        errors.append(f"legacy-to-catalog point maps missing: {point_node_count - legacy_point_map_count}")
    if broken_legacy_maps:
        errors.append(f"broken legacy catalog maps: {broken_legacy_maps}")
    if duplicate_ids:
        errors.append(f"duplicate catalog node ids: {', '.join(duplicate_ids[:5])}")

    result = {
        "ok": not errors,
        "errors": errors,
        "point_node_count": point_node_count,
        "point_content_count": point_content_count,
        "published_content_count": int(row["published_content_count"] or 0),
        "teacher_note_count": int(row["teacher_note_count"] or 0),
        "search_state_count": int(row["search_state_count"] or 0),
        "legacy_point_map_count": legacy_point_map_count,
        "broken_legacy_maps": broken_legacy_maps,
    }
    sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
