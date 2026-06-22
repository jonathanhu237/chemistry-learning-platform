from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.app.infrastructure.database import db_session
from server.app.domains.video_library.search import (
    _build_documents,
    _learning_profiles,
    _load_published_point_rows,
)
from server.app.domains.video_library.index_client import (
    configured_index_client,
    document_hash,
    forbidden_video_library_document_violations,
    mark_index_sync_failure,
    mark_index_sync_success,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild the student video-library Elasticsearch index from published point content.")
    parser.add_argument("--recreate", action="store_true", help="Delete and recreate the index before indexing.")
    parser.add_argument("--dry-run", action="store_true", help="Print document count and sample ids without writing to ES.")
    args = parser.parse_args()

    with db_session() as session:
        point_rows = _load_published_point_rows(session)
    documents = _build_documents([], _learning_profiles(), point_rows=point_rows)
    payloads = [document.index_source for document in documents if document.index_source]
    purity_violations = [
        {"id": payload.get("id"), "violations": forbidden_video_library_document_violations(payload)}
        for payload in payloads
        if forbidden_video_library_document_violations(payload)
    ]
    if purity_violations:
        sys.stdout.buffer.write(
            (
                json.dumps(
                    {
                        "ok": False,
                        "error": "video_library_document_purity_failed",
                        "violations": purity_violations[:20],
                    },
                    ensure_ascii=False,
                    indent=2,
                    default=str,
                )
                + "\n"
            ).encode("utf-8")
        )
        raise SystemExit(1)

    if args.dry_run:
        sys.stdout.buffer.write(
            (
                json.dumps(
                    {
                        "document_count": len(payloads),
                        "sample_ids": [payload["id"] for payload in payloads[:10]],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n"
            ).encode("utf-8")
        )
        return

    client = configured_index_client()
    if client is None:
        raise SystemExit("VIDEO_LIBRARY_SEARCH_BACKEND=elasticsearch and VIDEO_LIBRARY_SEARCH_URL are required")
    client.ensure_index(recreate=args.recreate)

    ok = 0
    failed = 0
    for payload in payloads:
        node_id = str(payload["node_id"])
        try:
            client.upsert_document(payload)
            mark_index_sync_success(
                node_id=node_id,
                document_id=str(payload["id"]),
                payload_hash=document_hash(payload),
            )
            ok += 1
        except Exception as exc:  # noqa: BLE001 - maintenance command records per-document failures.
            mark_index_sync_failure(
                node_id=node_id,
                document_id=str(payload["id"]),
                action="upsert",
                error=str(exc),
            )
            failed += 1
    sys.stdout.buffer.write((json.dumps({"indexed": ok, "failed": failed}, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
