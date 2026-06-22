from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.app.domains.catalog_tree.teacher_search import (
    configured_teacher_search_client,
    mark_teacher_search_state_failure,
    mark_teacher_search_state_success,
    teacher_catalog_search_documents,
    teacher_catalog_search_index_diagnostics,
    teacher_search_document_sync_hash,
)
from server.app.infrastructure.database import db_session
from server.app.infrastructure.settings import get_settings


def main() -> None:
    parser = argparse.ArgumentParser(description="Rebuild the teacher/admin catalog Elasticsearch index from catalog nodes.")
    parser.add_argument("--chapter-id", help="Limit rebuild to one chapter id.")
    parser.add_argument("--recreate", action="store_true", help="Delete and recreate the teacher index before indexing.")
    parser.add_argument("--dry-run", action="store_true", help="Print document count and sample ids without writing to ES.")
    parser.add_argument("--diagnostics", action="store_true", help="Print teacher search diagnostics and exit.")
    args = parser.parse_args()

    if args.diagnostics:
        sys.stdout.buffer.write((json.dumps(teacher_catalog_search_index_diagnostics(), ensure_ascii=False, indent=2, default=str) + "\n").encode("utf-8"))
        return

    with db_session() as session:
        documents = teacher_catalog_search_documents(session, chapter_id=args.chapter_id)

    if args.dry_run:
        sys.stdout.buffer.write(
            (
                json.dumps(
                    {
                        "document_count": len(documents),
                        "sample_ids": [document["id"] for document in documents[:10]],
                        "index": get_settings().teacher_catalog_search_index,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n"
            ).encode("utf-8")
        )
        return

    client = configured_teacher_search_client()
    if client is None:
        raise SystemExit("TEACHER_CATALOG_SEARCH_BACKEND=elasticsearch and TEACHER_CATALOG_SEARCH_URL are required")
    client.ensure_index(recreate=args.recreate, analyzer=get_settings().teacher_catalog_search_analyzer)

    ok = 0
    failed = 0
    for document in documents:
        node_id = str(document["node_id"])
        try:
            client.upsert_document(document)
            mark_teacher_search_state_success(
                node_id=node_id,
                action="upsert",
                document_hash=teacher_search_document_sync_hash(document),
                analyzer_version=get_settings().teacher_catalog_search_analyzer,
            )
            ok += 1
        except Exception as exc:  # noqa: BLE001 - maintenance command records per-document failures.
            mark_teacher_search_state_failure(node_id=node_id, action="upsert", error=str(exc))
            failed += 1

    sys.stdout.buffer.write((json.dumps({"indexed": ok, "failed": failed}, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
