from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.app.domains.catalog_tree.catalog_seed import load_catalog_seed
from server.app.infrastructure.settings import get_settings


def _get_json(base_url: str, path: str, timeout: float) -> dict[str, Any]:
    with urllib.request.urlopen(f"{base_url.rstrip('/')}{path}", timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload if isinstance(payload, dict) else {}


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Catalog-node evidence generation stub. It verifies that future GPU/BGE rerank work targets "
            "leaf catalog nodes by catalog node id or seed key, not legacy experiment_id + point_key."
        )
    )
    parser.add_argument("--bge-url", default=None)
    parser.add_argument("--timeout-seconds", type=float, default=5.0)
    parser.add_argument("--skip-bge-health", action="store_true")
    parser.add_argument("--plan-only", action="store_true", help="Print the catalog-node generation plan and exit 0.")
    args = parser.parse_args()

    settings = get_settings()
    bge_url = (args.bge_url or settings.rag_bge_service_url or "").rstrip("/")
    nodes = load_catalog_seed()
    points = [node for node in nodes if node.get("node_kind") == "point"]
    plan = {
        "mode": "catalog_node_evidence_generation_stub",
        "point_count": len(points),
        "identity_contract": ["catalog_node_id", "catalog_seed_key"],
        "query_context": "point title plus full catalog path",
        "legacy_identity_rejected": ["experiment_id", "point_key"],
        "sample_points": [
            {
                "catalog_seed_key": point["seed_key"],
                "catalog_path": point["path_titles"],
                "query": " / ".join(point["path_titles"]),
            }
            for point in points[:5]
        ],
        "bge_url": bge_url,
    }
    if not args.skip_bge_health:
        if not bge_url:
            raise SystemExit("RAG_BGE_SERVICE_URL or --bge-url is required before catalog-node evidence generation.")
        try:
            plan["bge_health"] = _get_json(bge_url, "/health", args.timeout_seconds)
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
            raise SystemExit(f"BGE service health check failed for {bge_url}: {exc}") from exc
    sys.stdout.buffer.write((json.dumps(plan, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    if not args.plan_only:
        raise SystemExit(
            "Catalog-node evidence generation is not implemented in this change. "
            "Run a future GPU/BGE rerank job that writes catalog_node_id or catalog_seed_key bindings."
        )


if __name__ == "__main__":
    main()
