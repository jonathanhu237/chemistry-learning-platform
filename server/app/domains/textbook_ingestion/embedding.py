from __future__ import annotations

import urllib.error
from dataclasses import dataclass
from typing import Callable, Protocol, Sequence

from server.app.domains.textbook_ingestion.contracts import StableChunk
from server.app.domains.textbook_rag.index import TextbookElasticsearchClient


class TextbookEmbeddingError(RuntimeError):
    def __init__(self, reason: str, message: str) -> None:
        super().__init__(message)
        self.reason = reason


class EmbeddingClient(Protocol):
    @property
    def model(self) -> str: ...

    def embed(self, texts: list[str]) -> list[list[float]]: ...


class EmbeddingReuseStore(Protocol):
    def lookup(
        self,
        content_hashes: Sequence[str],
        *,
        embedding_model: str,
        embedding_dimension: int,
    ) -> dict[str, list[float]]: ...


@dataclass(frozen=True)
class BatchEmbeddingResult:
    vectors: list[list[float]]
    reused_count: int
    computed_count: int
    unique_computed_count: int


class ElasticsearchEmbeddingReuseStore:
    def __init__(self, es: TextbookElasticsearchClient, *, batch_size: int = 500) -> None:
        self.es = es
        self.batch_size = max(1, batch_size)

    def lookup(
        self,
        content_hashes: Sequence[str],
        *,
        embedding_model: str,
        embedding_dimension: int,
    ) -> dict[str, list[float]]:
        hashes = [value for value in dict.fromkeys(str(item) for item in content_hashes) if value]
        results: dict[str, list[float]] = {}
        for start in range(0, len(hashes), self.batch_size):
            batch = hashes[start : start + self.batch_size]
            try:
                response = self.es.request(
                    "POST",
                    f"/{self.es.index}/_search",
                    {
                        "size": len(batch),
                        "_source": ["content_hash", "embedding", "embedding_model", "embedding_dimension"],
                        "query": {
                            "bool": {
                                "filter": [
                                    {"terms": {"content_hash": batch}},
                                    {"term": {"embedding_model": embedding_model}},
                                    {"term": {"embedding_dimension": embedding_dimension}},
                                ]
                            }
                        },
                    },
                )
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    return {}
                raise
            hits = response.get("hits", {}).get("hits", []) if isinstance(response, dict) else []
            for hit in hits if isinstance(hits, list) else []:
                source = hit.get("_source") if isinstance(hit, dict) and isinstance(hit.get("_source"), dict) else {}
                content_hash = str(source.get("content_hash") or "")
                raw_vector = source.get("embedding")
                if content_hash and isinstance(raw_vector, list) and len(raw_vector) == embedding_dimension:
                    results.setdefault(content_hash, [float(value) for value in raw_vector])
        return results


class BatchTextbookEmbedder:
    def __init__(
        self,
        client: EmbeddingClient,
        *,
        embedding_dimension: int,
        batch_size: int = 16,
        reuse_store: EmbeddingReuseStore | None = None,
    ) -> None:
        if embedding_dimension <= 0:
            raise ValueError("embedding_dimension must be positive")
        self.client = client
        self.embedding_dimension = embedding_dimension
        self.batch_size = max(1, batch_size)
        self.reuse_store = reuse_store

    @property
    def model(self) -> str:
        return self.client.model

    def embed_chunks(
        self,
        chunks: Sequence[StableChunk],
        *,
        on_batch: Callable[[int, int], None] | None = None,
    ) -> BatchEmbeddingResult:
        if not chunks:
            return BatchEmbeddingResult(vectors=[], reused_count=0, computed_count=0, unique_computed_count=0)
        content_by_hash: dict[str, str] = {}
        for chunk in chunks:
            if not chunk.content_hash:
                raise TextbookEmbeddingError("content_hash_missing", f"Chunk {chunk.chunk_id} has no content hash")
            previous_text = content_by_hash.setdefault(chunk.content_hash, chunk.text)
            if previous_text != chunk.text:
                raise TextbookEmbeddingError(
                    "content_hash_collision",
                    f"Chunks with content hash {chunk.content_hash} contain different text",
                )

        reused: dict[str, list[float]] = {}
        if self.reuse_store is not None:
            reused = self.reuse_store.lookup(
                list(content_by_hash),
                embedding_model=self.model,
                embedding_dimension=self.embedding_dimension,
            )
        for content_hash, vector in reused.items():
            if len(vector) != self.embedding_dimension:
                raise TextbookEmbeddingError(
                    "reused_embedding_dimension_mismatch",
                    f"Reused embedding for {content_hash} has dimension {len(vector)}",
                )

        computed: dict[str, list[float]] = {}
        missing_hashes = [content_hash for content_hash in content_by_hash if content_hash not in reused]
        for start in range(0, len(missing_hashes), self.batch_size):
            batch_hashes = missing_hashes[start : start + self.batch_size]
            vectors = self.client.embed([content_by_hash[content_hash] for content_hash in batch_hashes])
            if len(vectors) != len(batch_hashes):
                raise TextbookEmbeddingError(
                    "embedding_count_mismatch",
                    "Embedding provider returned a different vector count than requested",
                )
            for content_hash, vector in zip(batch_hashes, vectors):
                if len(vector) != self.embedding_dimension:
                    raise TextbookEmbeddingError(
                        "embedding_dimension_mismatch",
                        f"Embedding provider returned dimension {len(vector)}; expected {self.embedding_dimension}",
                    )
                computed[content_hash] = [float(value) for value in vector]
            if on_batch is not None:
                on_batch(min(start + len(batch_hashes), len(missing_hashes)), len(missing_hashes))

        vector_by_hash = {**reused, **computed}
        vectors = [vector_by_hash[chunk.content_hash] for chunk in chunks]
        reused_count = sum(1 for chunk in chunks if chunk.content_hash in reused)
        return BatchEmbeddingResult(
            vectors=vectors,
            reused_count=reused_count,
            computed_count=len(chunks) - reused_count,
            unique_computed_count=len(computed),
        )
