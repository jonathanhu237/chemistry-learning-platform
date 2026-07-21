from __future__ import annotations

import hashlib
import json
import os
import shutil
import urllib.error
import uuid
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

import pymupdf
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url

import server.app.domains.textbook_ingestion.lifecycle as lifecycle
import server.app.domains.textbook_ingestion.persistence as persistence
import server.app.domains.textbook_ingestion.queue as queue
import server.app.domains.textbook_ingestion.recovery as recovery
import server.app.domains.textbook_ingestion.repository as repository
import server.app.domains.textbook_rag.active_corpus as active_corpus
import server.app.domains.textbook_rag.retrieval as retrieval
import server.app.infrastructure.database as database
import server.app.workers.textbook_ingestion_worker as textbook_worker
from server.app.domains.textbook_ingestion.contracts import IngestionStage
from server.app.domains.textbook_rag.index import (
    TextbookElasticsearchClient,
    chunk_document,
    validate_bulk_index_response,
)
from server.app.infrastructure.settings import Settings


pytestmark = pytest.mark.skipif(
    os.getenv("TEXTBOOK_INGESTION_E2E_TEST") != "1",
    reason=(
        "set TEXTBOOK_INGESTION_E2E_TEST=1 to run with disposable PostgreSQL "
        "and Elasticsearch"
    ),
)

_DEFAULT_DATABASE_URL = (
    "postgresql+psycopg://chemistry:chemistry@127.0.0.1:15432/chemistry_exam"
)
_DEFAULT_ELASTICSEARCH_URL = "http://127.0.0.1:9200"
_EMBEDDING_DIMENSION = 4
_EMBEDDING_MODEL = "deterministic-textbook-e2e-v1"
_QUERY_TEXT = "Zephyrium catalyst stabilizes the violet endpoint during redox titration."


@dataclass(frozen=True)
class _IntegrationContext:
    settings: Settings
    elasticsearch: TextbookElasticsearchClient
    storage_root: Path


class _DeterministicEmbeddingClient:
    """Credential-free embedding double used on both indexing and retrieval paths."""

    def __init__(
        self,
        *,
        model: str,
        dimensions: int | None = None,
        **_: Any,
    ) -> None:
        self.model = model
        self.dimensions = int(dimensions or _EMBEDDING_DIMENSION)
        self.calls: list[list[str]] = []

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.calls.append(list(texts))
        # Keep the vector non-zero for cosine search while making every result
        # completely deterministic and independent of an HTTP provider.
        return [[1.0, 0.5, 0.25, 0.125][: self.dimensions] for _ in texts]


class _DeterministicRerankClient:
    def __init__(self, **_: Any) -> None:
        pass

    def rerank(self, *, query: str, documents: list[str]) -> list[float]:
        query_tokens = set(query.casefold().split())
        return [
            1.0 + len(query_tokens.intersection(document.casefold().split())) / 100.0
            for document in documents
        ]


def _source_database_url() -> URL:
    return make_url(
        os.getenv("TEXTBOOK_INGESTION_E2E_DATABASE_URL")
        or os.getenv("DATABASE_URL")
        or _DEFAULT_DATABASE_URL
    )


def _create_disposable_database() -> tuple[str, str, URL]:
    source_url = _source_database_url()
    maintenance_url = source_url.set(database="postgres")
    database_name = f"chemistry_textbook_e2e_{uuid.uuid4().hex[:12]}"
    target_url = source_url.set(database=database_name)
    engine = create_engine(
        maintenance_url,
        isolation_level="AUTOCOMMIT",
        pool_pre_ping=True,
        future=True,
    )
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            connection.execute(text(f'CREATE DATABASE "{database_name}"'))
    except Exception as exc:  # noqa: BLE001 - optional live dependency probe.
        pytest.skip(
            "textbook ingestion e2e requires PostgreSQL create-database access: "
            f"{exc.__class__.__name__}"
        )
    finally:
        engine.dispose()
    return target_url.render_as_string(hide_password=False), database_name, maintenance_url


def _drop_disposable_database(database_name: str, maintenance_url: URL) -> None:
    engine = create_engine(
        maintenance_url,
        isolation_level="AUTOCOMMIT",
        pool_pre_ping=True,
        future=True,
    )
    try:
        with engine.connect() as connection:
            connection.execute(
                text(
                    """
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = :database_name
                      AND pid <> pg_backend_pid()
                    """
                ),
                {"database_name": database_name},
            )
            connection.execute(text(f'DROP DATABASE IF EXISTS "{database_name}"'))
    finally:
        engine.dispose()


def _elasticsearch_url() -> str:
    return (
        os.getenv("TEXTBOOK_INGESTION_E2E_ELASTICSEARCH_URL")
        or os.getenv("TEXTBOOK_RAG_ELASTICSEARCH_URL")
        or _DEFAULT_ELASTICSEARCH_URL
    ).rstrip("/")


def _delete_index(es: TextbookElasticsearchClient) -> None:
    try:
        es.request("DELETE", f"/{es.index}")
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise


def _dispose_database_caches() -> None:
    if database.get_engine.cache_info().currsize:
        database.get_engine().dispose()
    database.get_session_factory.cache_clear()
    database.get_engine.cache_clear()


@pytest.fixture()
def integration_context(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> _IntegrationContext:
    es_url = _elasticsearch_url()
    probe = TextbookElasticsearchClient(
        base_url=es_url,
        index="unused-textbook-e2e-probe",
        timeout=3,
    )
    try:
        probe.request("GET", "/")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        pytest.skip(
            "textbook ingestion e2e requires Elasticsearch: "
            f"{exc.__class__.__name__}"
        )

    database_url, database_name, maintenance_url = _create_disposable_database()
    index_name = f"textbook-ingestion-e2e-{uuid.uuid4().hex[:12]}"
    storage_root = tmp_path / "textbook-storage"
    settings = Settings(
        data_backend="postgres",
        database_url=database_url,
        textbook_ingestion_enabled=True,
        textbook_storage_root=storage_root,
        textbook_ingestion_lease_seconds=120,
        textbook_chunk_max_chars=420,
        textbook_chunk_overlap_chars=40,
        textbook_native_min_chars=80,
        textbook_ocr_enabled=False,
        textbook_rag_enabled=True,
        textbook_rag_elasticsearch_url=es_url,
        textbook_rag_elasticsearch_index=index_name,
        textbook_rag_embedding_base_url="deterministic://local",
        # Readiness requires a configured secret, but the patched deterministic
        # client never sends this non-secret sentinel over HTTP.
        textbook_rag_embedding_api_key="e2e-sentinel-not-a-credential",
        textbook_rag_embedding_model=_EMBEDDING_MODEL,
        textbook_rag_embedding_dimension=_EMBEDDING_DIMENSION,
        textbook_rag_rerank_base_url="deterministic://local",
        textbook_rag_rerank_model="deterministic-reranker-v1",
        textbook_rag_timeout_seconds=5,
        catalog_point_evidence_auto_refresh=False,
    )
    es = TextbookElasticsearchClient(
        base_url=es_url,
        index=index_name,
        timeout=settings.textbook_rag_timeout_seconds,
    )

    for module in (database, repository, queue, persistence, lifecycle, active_corpus):
        monkeypatch.setattr(module, "get_settings", lambda: settings)
    monkeypatch.setattr(lifecycle, "effective_ingestion_settings", lambda: settings)
    monkeypatch.setattr(textbook_worker, "QwenEmbeddingClient", _DeterministicEmbeddingClient)
    monkeypatch.setattr(recovery, "QwenEmbeddingClient", _DeterministicEmbeddingClient)
    monkeypatch.setattr(retrieval, "QwenEmbeddingClient", _DeterministicEmbeddingClient)
    monkeypatch.setattr(retrieval, "QwenRerankClient", _DeterministicRerankClient)

    _dispose_database_caches()
    try:
        database.apply_migrations()
        yield _IntegrationContext(
            settings=settings,
            elasticsearch=es,
            storage_root=storage_root,
        )
    finally:
        try:
            _delete_index(es)
        finally:
            try:
                _dispose_database_caches()
                _drop_disposable_database(database_name, maintenance_url)
            finally:
                shutil.rmtree(storage_root, ignore_errors=True)


def _synthetic_pdf() -> bytes:
    document = pymupdf.open()
    pages = [
        (
            "1 Zephyrium Redox Chemistry",
            (
                "This synthetic text-native textbook introduces a traceable redox method. "
                "Zephyrium is a fictional catalyst used only by this regression test. "
                "A violet endpoint appears after the oxidant is added slowly to the sample. "
                "The observation is recorded with temperature, concentration, and source page. "
                "Every sentence is real PDF text and therefore must bypass OCR completely."
            ),
        ),
        (
            "1.1 Zephyrium Endpoint Control",
            (
                f"{_QUERY_TEXT} "
                "The sample remains colorless before the catalyst is introduced. "
                "Gentle mixing produces a stable violet endpoint without image recognition. "
                "This second page supplies a distinct source citation and section path. "
                "The deterministic retrieval query should locate this explanation exactly."
            ),
        ),
    ]
    try:
        for heading, body in pages:
            page = document.new_page(width=595, height=842)
            page.insert_text((72, 86), heading, fontsize=20, fontname="helv")
            remaining = page.insert_textbox(
                pymupdf.Rect(72, 130, 523, 700),
                body,
                fontsize=11,
                fontname="helv",
                lineheight=1.4,
            )
            assert remaining >= 0, "synthetic PDF text did not fit on its page"
        return document.tobytes(garbage=4, deflate=True)
    finally:
        document.close()


def _insert_published_seed(
    *,
    logical_key: str,
    seed_document_id: str,
    seed_index_document_id: str,
    seed_chunk_id: str,
) -> None:
    seed_text = (
        f"{_QUERY_TEXT} This canonical seed deliberately shares its collection with the "
        "staged online replacement."
    )
    with database.db_session() as session:
        session.execute(
            text(
                """
                INSERT INTO source_documents (
                  id, title, file_name, path, type, document_kind, size_bytes,
                  processing_status, metadata, logical_textbook_key, version_number,
                  version_label, publication_status, published_at, updated_at
                ) VALUES (
                  :id, :title, 'synthetic-seed.jsonl', 'synthetic-seed.jsonl',
                  'jsonl', 'canonical_textbook', 1, 'imported',
                  CAST(:metadata AS jsonb), :logical_key, 1, 'seed-v1',
                  'published', now(), now()
                )
                """
            ),
            {
                "id": seed_document_id,
                "title": "Synthetic Zephyrium Seed",
                "logical_key": logical_key,
                "metadata": json.dumps(
                    {
                        "source_collection": logical_key,
                        "index_document_id": seed_index_document_id,
                        "source_role": "canonical_textbook",
                    }
                ),
            },
        )
        session.execute(
            text(
                """
                INSERT INTO source_chunks (
                  id, document_id, document_version, page_number, page_end,
                  section_title, section_path, chunk_index, text, markdown,
                  tags, metadata, review_required, content_status, published_at,
                  content_type, content_hash, extraction_method, quality_flags,
                  updated_at
                ) VALUES (
                  :id, :document_id, 1, 7, 7,
                  'Seed reference', ARRAY['Seed reference'], 1, :text, :text,
                  ARRAY[:logical_key], CAST(:metadata AS jsonb), false, 'published', now(),
                  'text', :content_hash, 'seed', '{}'::text[], now()
                )
                """
            ),
            {
                "id": seed_chunk_id,
                "document_id": seed_document_id,
                "logical_key": logical_key,
                "text": seed_text,
                "content_hash": hashlib.sha256(seed_text.encode("utf-8")).hexdigest(),
                "metadata": json.dumps(
                    {
                        "source_collection": logical_key,
                        "doc_id": seed_index_document_id,
                    }
                ),
            },
        )


def _bulk_index(
    es: TextbookElasticsearchClient,
    documents: list[dict[str, Any]],
) -> None:
    operations: list[dict[str, Any]] = []
    expected_ids: list[str] = []
    for document in documents:
        chunk_id = str(document["chunk_id"])
        expected_ids.append(chunk_id)
        operations.extend(
            [
                {"index": {"_index": es.index, "_id": chunk_id}},
                document,
            ]
        )
    response = es.bulk(operations)
    successful_ids, failures = validate_bulk_index_response(
        response,
        expected_ids=expected_ids,
    )
    assert failures == []
    assert successful_ids == expected_ids
    es.request("POST", f"/{es.index}/_refresh")


def _retrieval_settings(context: _IntegrationContext) -> dict[str, Any]:
    return {
        "enabled": True,
        "elasticsearch_url": context.settings.textbook_rag_elasticsearch_url,
        "index_name": context.settings.textbook_rag_elasticsearch_index,
        "embedding": {
            "base_url": "deterministic://local",
            "api_key": "",
            "model": _EMBEDDING_MODEL,
        },
        "rerank": {
            "base_url": "deterministic://local",
            "api_key": "",
            "model": "deterministic-reranker-v1",
        },
        "embedding_dimension": _EMBEDDING_DIMENSION,
        "keyword_top_k": 20,
        "vector_top_k": 20,
        "rerank_top_k": 20,
        "final_top_k": 20,
        "min_rerank_score": 0,
        "timeout_seconds": 5,
    }


def _retrieve(context: _IntegrationContext) -> dict[str, Any]:
    return retrieval.retrieve_textbook_evidence(
        point_context={
            "point_title": "Zephyrium endpoint",
            "chapter": "1.1 Zephyrium Endpoint Control",
            "content": {"principle_text": _QUERY_TEXT},
        },
        settings=_retrieval_settings(context),
    )


def test_text_native_pdf_ingests_publishes_and_retrieves_exact_generation(
    integration_context: _IntegrationContext,
) -> None:
    """Exercise the worker-facing service boundary without HTTP auth or external AI.

    This is intentionally the smallest meaningful online end-to-end boundary:
    durable upload/job creation, the real worker pipeline, PostgreSQL facts, real
    Elasticsearch projection, publication, and the production retrieval service.
    Router authentication is covered separately by route contract tests.
    """

    context = integration_context
    run_id = uuid.uuid4().hex
    logical_key = f"textbook-zephyrium-e2e-{run_id}"
    seed_document_id = f"DOC_E2E_SEED_{run_id}"
    seed_index_document_id = f"seed-zephyrium-{run_id}"
    seed_chunk_id = f"seed-chunk-{run_id}"
    decoy_chunk_id = f"wrong-version-{run_id}"

    _insert_published_seed(
        logical_key=logical_key,
        seed_document_id=seed_document_id,
        seed_index_document_id=seed_index_document_id,
        seed_chunk_id=seed_chunk_id,
    )
    with database.db_session() as session:
        embeddings_before = int(
            session.execute(text("SELECT count(*) FROM chunk_embeddings")).scalar_one()
        )

    uploaded = repository.create_textbook_upload(
        title="Synthetic Zephyrium Online Textbook",
        filename="zephyrium.pdf",
        stream=BytesIO(_synthetic_pdf()),
        content_type="application/pdf",
        uploaded_by=None,
        logical_textbook_key=logical_key,
    )
    document_id = str(uploaded["id"])
    document_version = int(uploaded["version_number"])
    job_id = str(uploaded["latest_job"]["id"])
    assert document_version == 2
    assert uploaded["supersedes_document_id"] == seed_document_id
    assert uploaded["latest_job"]["status"] == IngestionStage.UPLOADED.value
    stored_pdf = context.storage_root / str(uploaded["path"])
    assert stored_pdf.is_file()
    assert stored_pdf.read_bytes().startswith(b"%PDF")

    claimed = queue.claim_next_job(f"textbook-e2e-worker-{run_id}")
    assert claimed is not None
    assert claimed.document_id == document_id

    pipeline = textbook_worker.build_pipeline(context.settings)
    outcome = pipeline.process(claimed)
    assert outcome.status == IngestionStage.REVIEW_READY
    assert outcome.total_pages == 2
    assert outcome.ocr_pages == 0
    assert outcome.total_chunks >= 2

    pages = repository.list_document_pages(document_id)["items"]
    chunks = repository.list_document_chunks(document_id)["items"]
    assert [page["page_number"] for page in pages] == [1, 2]
    assert all(page["extraction_method"] == "native" for page in pages)
    assert all(page["needs_ocr"] is False for page in pages)
    assert {_QUERY_TEXT in page["text"] for page in pages} == {False, True}
    assert len(chunks) == outcome.total_chunks
    assert {page for chunk in chunks for page in range(chunk["page_start"], chunk["page_end"] + 1)} == {1, 2}
    assert all(chunk["document_version"] == document_version for chunk in chunks)
    assert all(chunk["metadata"]["logical_textbook_key"] == logical_key for chunk in chunks)

    seed_source = chunk_document(
        {
            "chunk_id": seed_chunk_id,
            "doc_id": seed_index_document_id,
            "document_id": seed_document_id,
            "logical_textbook_key": logical_key,
            "document_version": 1,
            "processing_fingerprint": "synthetic-seed",
            "source_collection": logical_key,
            "source_role": "canonical_textbook",
            "authority_level": "primary",
            "book_title": "Synthetic Zephyrium Seed",
            "chapter": "Seed reference",
            "content_type": "text",
            "knowledge_unit": "Seed reference",
            "section_path": ["Seed reference"],
            "clean_text_for_embedding": (
                f"{_QUERY_TEXT} This result belongs to the canonical seed generation."
            ),
            "raw_markdown": _QUERY_TEXT,
            "page_start": 7,
            "page_end": 7,
            "use_for_question_generation": True,
            "content_hash": hashlib.sha256(seed_chunk_id.encode("utf-8")).hexdigest(),
        },
        source_file="synthetic-seed.jsonl",
        embedding=[1.0, 0.5, 0.25, 0.125],
        embedding_model=_EMBEDDING_MODEL,
    )
    decoy_source = chunk_document(
        {
            "chunk_id": decoy_chunk_id,
            "doc_id": document_id,
            "document_id": document_id,
            "logical_textbook_key": logical_key,
            "document_version": document_version,
            "processing_fingerprint": claimed.processing_fingerprint,
            "projection_run_id": f"stale-run-{run_id}",
            "source_collection": logical_key,
            "source_role": "canonical_textbook",
            "authority_level": "primary",
            "book_title": "Synthetic Zephyrium Stale Projection",
            "chapter": "Stale projection run",
            "content_type": "text",
            "knowledge_unit": "Stale projection run",
            "section_path": ["Stale projection run"],
            "clean_text_for_embedding": (
                f"{_QUERY_TEXT} This ES-only decoy has the right document and version but a stale run."
            ),
            "raw_markdown": _QUERY_TEXT,
            "page_start": 99,
            "page_end": 99,
            "use_for_question_generation": True,
            "content_hash": hashlib.sha256(decoy_chunk_id.encode("utf-8")).hexdigest(),
        },
        source_file="stale-run-decoy.jsonl",
        embedding=[1.0, 0.5, 0.25, 0.125],
        embedding_model=_EMBEDDING_MODEL,
    )
    _bulk_index(context.elasticsearch, [seed_source, decoy_source])

    shared_collection = context.elasticsearch.request(
        "POST",
        f"/{context.elasticsearch.index}/_search",
        {
            "size": 100,
            "_source": ["doc_id", "document_id", "document_version", "source_collection"],
            "query": {"term": {"source_collection": logical_key}},
        },
    )
    shared_sources = [hit["_source"] for hit in shared_collection["hits"]["hits"]]
    assert {source["doc_id"] for source in shared_sources} == {
        seed_index_document_id,
        document_id,
    }
    assert {int(source["document_version"]) for source in shared_sources} == {1, document_version}

    seed_retrieval = _retrieve(context)
    assert seed_retrieval["ok"] is True
    assert seed_retrieval["source_refs"]
    assert {source["document_id"] for source in seed_retrieval["source_refs"]} == {
        seed_document_id
    }
    assert {source["document_version"] for source in seed_retrieval["source_refs"]} == {1}
    assert {source["source_file"] for source in seed_retrieval["source_refs"]} == {
        "synthetic-seed.jsonl"
    }

    published = lifecycle.publish_textbook(document_id, actor_id=None)
    assert published["publication_status"] == "published"
    assert published["projection_verification"]["stale_projection_chunk_count"] == 1
    assert published["latest_job"]["status"] == IngestionStage.READY.value
    assert published["latest_job"]["outputs"]["index_verified"] is True
    assert published["latest_job"]["outputs"]["indexed_chunks"] == outcome.total_chunks
    assert published["projection_verification"]["stale_projection_chunk_count"] == 1
    assert repository.get_textbook_document(seed_document_id)["publication_status"] == "inactive"
    event_statuses = list(
        dict.fromkeys(
            event["status"]
            for event in repository.list_ingestion_job_events(job_id)["items"]
        )
    )
    assert event_statuses == [
        IngestionStage.UPLOADED.value,
        IngestionStage.EXTRACTING.value,
        IngestionStage.STRUCTURING.value,
        IngestionStage.CHUNKING.value,
        IngestionStage.EMBEDDING.value,
        IngestionStage.INDEXING.value,
        IngestionStage.REVIEW_READY.value,
        IngestionStage.READY.value,
    ]

    online_retrieval = _retrieve(context)
    assert online_retrieval["ok"] is True
    assert online_retrieval["source_refs"]
    assert {source["document_id"] for source in online_retrieval["source_refs"]} == {
        document_id
    }
    assert {source["document_version"] for source in online_retrieval["source_refs"]} == {
        document_version
    }
    assert all(
        source["source_file"] == f"online:{document_id}"
        for source in online_retrieval["source_refs"]
    )
    assert all(
        source["page_start"] in {1, 2} and source["page_end"] in {1, 2}
        for source in online_retrieval["source_refs"]
    )
    assert any(source["section_path"] for source in online_retrieval["source_refs"])
    assert all(source["chunk_id"] != decoy_chunk_id for source in online_retrieval["source_refs"])

    with database.db_session() as session:
        embeddings_after = int(
            session.execute(text("SELECT count(*) FROM chunk_embeddings")).scalar_one()
        )
        persisted = session.execute(
            text(
                """
                SELECT
                  (SELECT count(*) FROM textbook_document_pages WHERE document_id = :document_id) AS pages,
                  (SELECT count(*) FROM source_chunks WHERE document_id = :document_id) AS chunks,
                  (SELECT count(*) FROM textbook_ingestion_jobs WHERE document_id = :document_id) AS jobs
                """
            ),
            {"document_id": document_id},
        ).mappings().one()
    assert embeddings_after == embeddings_before
    assert persisted["pages"] == 2
    assert persisted["chunks"] == outcome.total_chunks
    assert persisted["jobs"] == 1

    active_run_before_loss = repository.get_textbook_document(document_id)[
        "active_projection_run_id"
    ]
    _delete_index(context.elasticsearch)
    recovered = recovery.reproject_configured_online_textbooks(
        settings=context.settings,
        document_ids=[document_id],
    )
    recovered_document = repository.get_textbook_document(document_id)
    assert recovered["documents"] == 1
    assert recovered["chunks"] == outcome.total_chunks
    assert recovered_document["active_projection_run_id"] != active_run_before_loss
    assert recovered_document["latest_job"]["outputs"]["projection_run_id"] == (
        recovered_document["active_projection_run_id"]
    )
    verified_noop = lifecycle.publish_textbook(document_id, actor_id=None)
    assert verified_noop["lifecycle_noop"] is True
    assert verified_noop["projection_verification"]["verified"] is True
    recovered_retrieval = _retrieve(context)
    assert recovered_retrieval["ok"] is True
    assert {
        source["document_id"] for source in recovered_retrieval["source_refs"]
    } == {document_id}
