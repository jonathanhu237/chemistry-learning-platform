#!/usr/bin/env python
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.app.domains.platform.settings import effective_textbook_rag_settings
from server.app.domains.textbook_rag.clients import OpenAICompatibleEmbeddingClient
from server.app.domains.textbook_rag.index import (
    DEFAULT_CHUNK_PATHS,
    TextbookElasticsearchClient,
    index_textbook_chunks,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Index canonical textbook chunks with the configured Embedding provider and Elasticsearch target."
    )
    parser.add_argument("--chunk", action="append", dest="chunks", help="JSONL chunk file. Repeatable.")
    parser.add_argument("--batch-size", type=int, default=10)
    parser.add_argument("--recreate", action="store_true")
    args = parser.parse_args()

    config = effective_textbook_rag_settings()
    if not config.get("enabled"):
        raise SystemExit("Textbook RAG is disabled in AI configuration.")
    embedding = config.get("embedding") or {}
    es = TextbookElasticsearchClient(
        base_url=str(config.get("elasticsearch_url") or ""),
        index=str(config.get("index_name") or ""),
        timeout=float(config.get("timeout_seconds") or 8.0),
    )
    embedder = OpenAICompatibleEmbeddingClient(
        base_url=str(embedding.get("base_url") or ""),
        api_key=str(embedding.get("api_key") or ""),
        model=str(embedding.get("model") or ""),
        dimensions=int(config.get("embedding_dimension") or 0) or None,
        timeout_seconds=float(config.get("timeout_seconds") or 8.0),
        provider=str(embedding.get("provider") or "openai_compatible"),
        protocol=str(embedding.get("protocol") or "openai_embeddings"),
        endpoint=str(embedding.get("endpoint") or ""),
        send_dimensions=bool(embedding.get("send_dimensions", True)),
    )
    chunk_paths = [Path(path) for path in args.chunks] if args.chunks else list(DEFAULT_CHUNK_PATHS)
    result = index_textbook_chunks(
        es=es,
        embedding_client=embedder,
        chunk_paths=chunk_paths,
        embedding_dimension=int(config.get("embedding_dimension") or 1024),
        batch_size=max(1, int(args.batch_size)),
        recreate=bool(args.recreate),
    )
    print(result)


if __name__ == "__main__":
    main()
