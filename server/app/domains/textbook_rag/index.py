from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Iterable

from server.app.domains.textbook_rag.clients import QwenEmbeddingClient


DEFAULT_CHUNK_PATHS = (
    Path("data/seed/canonical_rag/chunks/textbook_experiment_chunks_v1.jsonl"),
    Path("data/seed/canonical_rag/chunks/textbook_inorganic_lower_chunks_v1.jsonl"),
)
TEXTBOOK_RAG_INDEX_SCHEMA = "canonical-rag-chunks-qwen-v2"
ONLINE_MAPPING_PROPERTIES: dict[str, Any] = {
    "document_id": {"type": "keyword"},
    "logical_textbook_key": {"type": "keyword"},
    "document_version": {"type": "integer"},
    "processing_fingerprint": {"type": "keyword"},
    "extraction_method": {"type": "keyword"},
    "quality_flags": {"type": "keyword"},
}


class TextbookElasticsearchClient:
    def __init__(self, *, base_url: str, index: str, timeout: float = 8.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.index = index
        self.timeout = timeout

    def request(self, method: str, path: str, payload: Any | None = None) -> Any:
        data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method=method,
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}

    def ensure_index(self, *, embedding_model: str, embedding_dimension: int, recreate: bool = False) -> None:
        if recreate:
            try:
                self.request("DELETE", f"/{self.index}")
            except urllib.error.HTTPError as exc:
                if exc.code != 404:
                    raise
        try:
            self.request("HEAD", f"/{self.index}")
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
            self.request(
                "PUT",
                f"/{self.index}",
                textbook_chunk_index_mapping(
                    embedding_model=embedding_model,
                    embedding_dimension=embedding_dimension,
                ),
            )
            return
        mapping_response = self.request("GET", f"/{self.index}/_mapping")
        index_mapping = mapping_response.get(self.index, {}) if isinstance(mapping_response, dict) else {}
        mappings = index_mapping.get("mappings", {}) if isinstance(index_mapping, dict) else {}
        metadata = mappings.get("_meta", {}) if isinstance(mappings, dict) else {}
        properties = mappings.get("properties", {}) if isinstance(mappings, dict) else {}
        actual_model = str(metadata.get("embedding_model") or "")
        actual_dimension = int(
            metadata.get("embedding_dimension")
            or ((properties.get("embedding") or {}).get("dims") if isinstance(properties, dict) else 0)
            or 0
        )
        if actual_model and actual_model != embedding_model:
            raise ValueError(
                f"Elasticsearch textbook index embedding model mismatch: expected {embedding_model}, got {actual_model}"
            )
        if actual_dimension and actual_dimension != embedding_dimension:
            raise ValueError(
                "Elasticsearch textbook index embedding dimension mismatch: "
                f"expected {embedding_dimension}, got {actual_dimension}"
            )
        self.request(
            "PUT",
            f"/{self.index}/_mapping",
            {
                "_meta": {
                    **(metadata if isinstance(metadata, dict) else {}),
                    "embedding_model": embedding_model,
                    "embedding_dimension": embedding_dimension,
                    "schema": TEXTBOOK_RAG_INDEX_SCHEMA,
                },
                "properties": ONLINE_MAPPING_PROPERTIES,
            },
        )

    def bulk(self, operations: list[dict[str, Any]]) -> dict[str, Any]:
        body = "\n".join(json.dumps(item, ensure_ascii=False) for item in operations) + "\n"
        request = urllib.request.Request(
            f"{self.base_url}/_bulk",
            data=body.encode("utf-8"),
            headers={"Content-Type": "application/x-ndjson"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            raw = response.read().decode("utf-8")
        return json.loads(raw) if raw else {}


def textbook_chunk_index_mapping(*, embedding_model: str, embedding_dimension: int) -> dict[str, Any]:
    return {
        "settings": {
            "analysis": {
                "analyzer": {
                    "chemistry_ik": {
                        "type": "custom",
                        "tokenizer": "ik_max_word",
                        "filter": ["lowercase"],
                    }
                },
                "normalizer": {
                    "chemistry_keyword": {
                        "type": "custom",
                        "filter": ["lowercase"],
                    }
                },
            }
        },
        "mappings": {
            "dynamic": "false",
            "_meta": {
                "embedding_model": embedding_model,
                "embedding_dimension": embedding_dimension,
                "schema": TEXTBOOK_RAG_INDEX_SCHEMA,
            },
            "properties": {
                "chunk_id": {"type": "keyword"},
                "doc_id": {"type": "keyword"},
                "source_collection": {"type": "keyword"},
                "source_role": {"type": "keyword"},
                "authority_level": {"type": "keyword"},
                "book_title": {"type": "keyword"},
                "chapter": {"type": "keyword"},
                "content_type": {"type": "keyword"},
                "knowledge_unit": {"type": "keyword"},
                "section_path": {"type": "keyword"},
                "text": {"type": "text", "analyzer": "chemistry_ik", "search_analyzer": "ik_smart"},
                "raw_markdown": {"type": "text", "analyzer": "chemistry_ik", "search_analyzer": "ik_smart"},
                "formulas": {"type": "keyword", "normalizer": "chemistry_keyword"},
                "reactions": {"type": "keyword"},
                "compounds": {"type": "keyword", "normalizer": "chemistry_keyword"},
                "elements": {"type": "keyword", "normalizer": "chemistry_keyword"},
                "page_start": {"type": "integer"},
                "page_end": {"type": "integer"},
                "use_for_question_generation": {"type": "boolean"},
                "content_hash": {"type": "keyword"},
                "source_file": {"type": "keyword"},
                "indexed_at": {"type": "date"},
                "embedding_model": {"type": "keyword"},
                "embedding_dimension": {"type": "integer"},
                "embedding": {"type": "dense_vector", "dims": embedding_dimension, "index": True, "similarity": "cosine"},
                "metadata": {"type": "object", "enabled": True},
                **ONLINE_MAPPING_PROPERTIES,
            },
        },
    }


def iter_chunk_rows(paths: Iterable[str | Path]) -> Iterable[tuple[Path, dict[str, Any]]]:
    for raw_path in paths:
        path = Path(raw_path)
        with path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                yield path, json.loads(line)


def chunk_document(row: dict[str, Any], *, source_file: str, embedding: list[float], embedding_model: str) -> dict[str, Any]:
    text = str(row.get("clean_text_for_embedding") or row.get("raw_markdown") or "")
    return {
        "chunk_id": str(row.get("chunk_id") or ""),
        "doc_id": str(row.get("doc_id") or ""),
        "document_id": str(row.get("document_id") or ""),
        "logical_textbook_key": str(row.get("logical_textbook_key") or row.get("source_collection") or ""),
        "document_version": int(row.get("document_version") or 1),
        "processing_fingerprint": str(row.get("processing_fingerprint") or ""),
        "extraction_method": str(row.get("extraction_method") or "seed"),
        "quality_flags": [str(item) for item in row.get("quality_flags") or []],
        "source_collection": str(row.get("source_collection") or ""),
        "source_role": str(row.get("source_role") or ""),
        "authority_level": str(row.get("authority_level") or ""),
        "book_title": str(row.get("book_title") or ""),
        "chapter": str(row.get("chapter") or ""),
        "content_type": str(row.get("content_type") or ""),
        "knowledge_unit": str(row.get("knowledge_unit") or ""),
        "section_path": [str(item) for item in row.get("section_path") or []],
        "text": text,
        "raw_markdown": str(row.get("raw_markdown") or ""),
        "formulas": [str(item) for item in row.get("formulas") or []],
        "reactions": [str(item) for item in row.get("reactions") or []],
        "compounds": [str(item) for item in row.get("compounds") or []],
        "elements": [str(item) for item in row.get("elements") or []],
        "page_start": row.get("page_start"),
        "page_end": row.get("page_end"),
        "use_for_question_generation": bool(row.get("use_for_question_generation")),
        "content_hash": str(row.get("content_hash") or hashlib.md5(text.encode("utf-8")).hexdigest()),
        "source_file": source_file,
        "indexed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "embedding_model": embedding_model,
        "embedding_dimension": len(embedding),
        "embedding": embedding,
        "metadata": {
            key: value
            for key, value in row.items()
            if key
            not in {
                "clean_text_for_embedding",
                "raw_markdown",
                "formulas",
                "reactions",
                "compounds",
                "elements",
            }
        },
    }


def index_textbook_chunks(
    *,
    es: TextbookElasticsearchClient,
    embedding_client: QwenEmbeddingClient,
    chunk_paths: Iterable[str | Path] = DEFAULT_CHUNK_PATHS,
    embedding_dimension: int,
    batch_size: int = 16,
    recreate: bool = False,
) -> dict[str, Any]:
    es.ensure_index(
        embedding_model=embedding_client.model,
        embedding_dimension=embedding_dimension,
        recreate=recreate,
    )
    indexed = 0
    failures: list[str] = []
    pending: list[tuple[Path, dict[str, Any]]] = []
    for item in iter_chunk_rows(chunk_paths):
        pending.append(item)
        if len(pending) >= batch_size:
            indexed += _flush_batch(es, embedding_client, pending, failures)
            pending = []
    if pending:
        indexed += _flush_batch(es, embedding_client, pending, failures)
    return {"indexed": indexed, "failures": failures}


def _flush_batch(
    es: TextbookElasticsearchClient,
    embedding_client: QwenEmbeddingClient,
    batch: list[tuple[Path, dict[str, Any]]],
    failures: list[str],
) -> int:
    texts = [str(row.get("clean_text_for_embedding") or row.get("raw_markdown") or "") for _, row in batch]
    embeddings = embedding_client.embed(texts)
    operations: list[dict[str, Any]] = []
    for (path, row), embedding in zip(batch, embeddings):
        chunk_id = str(row.get("chunk_id") or "")
        if not chunk_id:
            failures.append(f"{path}: missing chunk_id")
            continue
        operations.append({"index": {"_index": es.index, "_id": chunk_id}})
        operations.append(chunk_document(row, source_file=str(path), embedding=embedding, embedding_model=embedding_client.model))
    if not operations:
        return 0
    response = es.bulk(operations)
    expected_ids = [str(operation["index"]["_id"]) for operation in operations[::2]]
    successful_ids, item_failures = validate_bulk_index_response(response, expected_ids=expected_ids)
    failures.extend(item_failures)
    return len(successful_ids)


def validate_bulk_index_response(
    response: dict[str, Any],
    *,
    expected_ids: list[str],
) -> tuple[list[str], list[str]]:
    items = response.get("items") if isinstance(response, dict) else None
    if not isinstance(items, list):
        return [], ["Elasticsearch bulk response is missing item results"]
    successful: list[str] = []
    failures: list[str] = []
    for item in items:
        result = item.get("index") if isinstance(item, dict) else None
        if not isinstance(result, dict):
            failures.append("Elasticsearch bulk response contains an invalid item")
            continue
        chunk_id = str(result.get("_id") or "")
        status = int(result.get("status") or 0)
        if status < 200 or status >= 300 or result.get("error"):
            reason = result.get("error")
            failures.append(f"Elasticsearch rejected chunk {chunk_id or '<unknown>'}: {str(reason)[:240]}")
            continue
        successful.append(chunk_id)
    missing = sorted(set(expected_ids) - set(successful))
    unexpected = sorted(set(successful) - set(expected_ids))
    if missing:
        failures.append(f"Elasticsearch bulk response omitted {len(missing)} expected chunk(s)")
    if unexpected:
        failures.append(f"Elasticsearch bulk response returned {len(unexpected)} unexpected chunk(s)")
    return [chunk_id for chunk_id in expected_ids if chunk_id in set(successful)], failures
