from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.app.domains.textbook_ingestion.recovery import (
    RECREATE_SAFE_PUBLICATION_STATUSES,
    RETAINED_PUBLICATION_STATUSES,
    TextbookRecoveryError,
    load_online_textbooks_for_reprojection,
    reproject_configured_online_textbooks,
)
from scripts.import_precomputed_textbook_rag import resolve_elasticsearch_target


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Recompute embeddings from PostgreSQL textbook chunks and rebuild their "
            "derived projections in the shared Elasticsearch index."
        )
    )
    parser.add_argument(
        "--es-url",
        default=None,
    )
    parser.add_argument(
        "--index",
        default=None,
    )
    parser.add_argument("--document-id", action="append", default=[])
    parser.add_argument(
        "--include-review-ready",
        action="store_true",
        help="Also rebuild review-ready staged projections (used by safe seed index recreation).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Read PostgreSQL facts and print the rebuild plan without calling the provider or ES.",
    )
    args = parser.parse_args()
    try:
        target = resolve_elasticsearch_target(es_url=args.es_url, index=args.index)
    except ValueError as exc:
        parser.error(str(exc))
    statuses = (
        RECREATE_SAFE_PUBLICATION_STATUSES
        if args.include_review_ready
        else RETAINED_PUBLICATION_STATUSES
    )
    try:
        if args.dry_run:
            documents = load_online_textbooks_for_reprojection(
                publication_statuses=statuses,
                document_ids=args.document_id,
            )
            result = {
                "ok": True,
                "dry_run": True,
                "elasticsearch_url": target.display_url,
                "index": target.index,
                "documents": len(documents),
                "chunks": sum(len(document.chunks) for document in documents),
                "items": [
                    {
                        "document_id": document.document_id,
                        "publication_status": document.publication_status,
                        "chunks": len(document.chunks),
                    }
                    for document in documents
                ],
            }
        else:
            result = reproject_configured_online_textbooks(
                elasticsearch_url=target.base_url,
                index=target.index,
                publication_statuses=statuses,
                document_ids=args.document_id,
            )
            result = {
                "elasticsearch_url": target.display_url,
                "index": target.index,
                **result,
            }
    except TextbookRecoveryError as exc:
        result = {
            "ok": False,
            "reason": exc.reason,
            "message": str(exc),
            "elasticsearch_url": target.display_url,
            "index": target.index,
            **exc.details,
        }
        sys.stdout.buffer.write(
            (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        )
        raise SystemExit(1) from exc
    sys.stdout.buffer.write(
        (json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    )


if __name__ == "__main__":
    main()
