from __future__ import annotations

import json
import os
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from io import BytesIO
from pathlib import Path
from typing import Any, Iterator

import pytest
import pymupdf
from sqlalchemy import text

from server.app.domains.textbook_ingestion import persistence, queue, repository
from server.app.domains.textbook_ingestion.contracts import (
    ExtractionMethod,
    IngestionStage,
    NormalizedBlock,
    NormalizedPage,
    PageQuality,
    StableChunk,
)
from server.app.domains.textbook_ingestion.errors import (
    TextbookIngestionError,
    TextbookJobLeaseLostError,
)
from server.app.domains.textbook_ingestion.queue import ClaimedIngestionJob
from server.app.infrastructure.database import apply_migrations, db_session
from server.app.infrastructure.settings import Settings


def _pdf_bytes(label: str) -> bytes:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), label)
    try:
        return document.tobytes()
    finally:
        document.close()


class _FakeResult:
    def __init__(self, row: dict[str, Any] | None = None) -> None:
        self.row = row

    def mappings(self) -> _FakeResult:
        return self

    def first(self) -> dict[str, Any] | None:
        return self.row


class _FakeSession:
    def __init__(self, lease_row: dict[str, Any] | None) -> None:
        self.lease_row = lease_row
        self.calls: list[tuple[str, Any]] = []

    def execute(self, statement: Any, parameters: Any = None) -> _FakeResult:
        sql = str(statement)
        self.calls.append((sql, parameters))
        if "FROM textbook_ingestion_jobs tij" in sql:
            return _FakeResult(self.lease_row)
        return _FakeResult()


def _claimed_job(*, document_id: str = "tbk_test") -> ClaimedIngestionJob:
    return ClaimedIngestionJob(
        id="11111111-1111-4111-8111-111111111111",
        document_id=document_id,
        status=IngestionStage.STRUCTURING,
        attempts=1,
        max_attempts=3,
        worker_id="worker-a",
        lease_token="22222222-2222-4222-8222-222222222222",
        processing_fingerprint="job-fingerprint",
        config_snapshot={"chunk_size": 900},
    )


def _lease_row(*, document_id: str = "tbk_test", version: int = 3) -> dict[str, Any]:
    return {
        "document_id": document_id,
        "logical_textbook_key": "chemistry-lower",
        "version_number": version,
        "title": "无机化学（下册）",
        "file_name": "无机化学.pdf",
        "path": f"originals/{document_id}/source.pdf",
        "mime_type": "application/pdf",
        "checksum_sha256": "a" * 64,
        "metadata": {"source_origin": "online_upload"},
        "processing_fingerprint": "database-fingerprint",
        "config_snapshot": {"native_extraction": True},
    }


def _install_fake_session(
    monkeypatch: pytest.MonkeyPatch,
    lease_row: dict[str, Any] | None,
) -> _FakeSession:
    session = _FakeSession(lease_row)

    @contextmanager
    def fake_db_session() -> Iterator[_FakeSession]:
        yield session

    monkeypatch.setattr(persistence, "db_session", fake_db_session)
    return session


def _page() -> NormalizedPage:
    return NormalizedPage(
        page_number=4,
        width_points=595,
        height_points=842,
        text="氯气的实验室制法",
        markdown="## 氯气的实验室制法",
        blocks=[
            NormalizedBlock(
                block_id="p4-b1",
                block_type="section_header",
                text="氯气的实验室制法",
                metadata={"observed_at": datetime(2026, 7, 22, tzinfo=UTC)},
            )
        ],
        quality=PageQuality(score=0.94, needs_ocr=False, flags=["native_text"]),
        diagnostics={"render_path": Path("page-4.png")},
    )


def _chunk(*, document_id: str = "tbk_test", version: int = 3) -> StableChunk:
    return StableChunk(
        chunk_id=f"{document_id}:v{version}:c0001",
        document_id=document_id,
        document_version=version,
        chunk_index=1,
        text="氯气可由二氧化锰与浓盐酸加热制备。",
        markdown="氯气可由二氧化锰与浓盐酸加热制备。",
        page_start=4,
        page_end=5,
        section_title="氯气",
        section_path=["第十六章", "氯气"],
        content_hash="b" * 64,
        metadata={"observed_at": datetime(2026, 7, 22, tzinfo=UTC)},
    )


def test_load_processing_input_validates_lease_and_storage_containment(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    job = _claimed_job()
    row = _lease_row()
    source_path = tmp_path / row["path"]
    source_path.parent.mkdir(parents=True)
    source_path.write_bytes(b"%PDF-1.7\ncontent")
    session = _install_fake_session(monkeypatch, row)

    result = persistence.load_processing_input(job, storage_root=tmp_path)

    assert result.document_version == 3
    assert result.source_path == source_path.resolve()
    assert result.metadata == {"source_origin": "online_upload"}
    assert result.processing_fingerprint == "database-fingerprint"
    lease_sql, lease_params = session.calls[0]
    assert "FOR UPDATE OF tij, sd" in lease_sql
    assert "tij.cancellation_requested_at IS NULL" in lease_sql
    assert "tij.lease_expires_at > now()" in lease_sql
    assert lease_params == {
        "job_id": job.id,
        "document_id": job.document_id,
        "worker_id": job.worker_id,
        "lease_token": job.lease_token,
        "status": job.status.value,
    }


def test_load_processing_input_rejects_path_escape(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    row = _lease_row()
    row["path"] = "../outside.pdf"
    _install_fake_session(monkeypatch, row)

    with pytest.raises(TextbookIngestionError) as raised:
        persistence.load_processing_input(_claimed_job(), storage_root=tmp_path)

    assert raised.value.reason == "invalid_storage_path"


def test_page_upsert_is_batched_and_pydantic_json_safe(monkeypatch: pytest.MonkeyPatch) -> None:
    job = _claimed_job()
    session = _install_fake_session(monkeypatch, _lease_row())

    assert persistence.upsert_normalized_pages(job, [_page()]) == 1

    assert len(session.calls) == 2
    write_sql, parameters = session.calls[1]
    assert "ON CONFLICT (document_id, page_number) DO UPDATE" in write_sql
    assert "CAST(:blocks AS jsonb)" in write_sql
    assert isinstance(parameters, list)
    page_parameters = parameters[0]
    assert page_parameters["document_id"] == job.document_id
    assert page_parameters["processing_fingerprint"] == job.processing_fingerprint
    assert len(page_parameters["content_hash"]) == 64
    assert json.loads(page_parameters["blocks"])[0]["metadata"]["observed_at"].endswith("Z")
    assert json.loads(page_parameters["diagnostics"])["render_path"] == "page-4.png"


def test_writes_stop_before_mutation_when_lease_is_lost(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _install_fake_session(monkeypatch, None)

    with pytest.raises(TextbookJobLeaseLostError):
        persistence.upsert_normalized_pages(_claimed_job(), [_page()])

    assert len(session.calls) == 1


def test_chunk_replace_derives_parent_version_and_keeps_draft_pending_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    job = _claimed_job()
    session = _install_fake_session(monkeypatch, _lease_row(version=3))

    assert persistence.replace_document_chunks(job, [_chunk()]) == 1

    assert len(session.calls) == 3
    delete_sql, delete_parameters = session.calls[1]
    insert_sql, insert_parameters = session.calls[2]
    assert "DELETE FROM source_chunks WHERE document_id = :document_id" in delete_sql
    assert delete_parameters == {"document_id": job.document_id}
    assert "true, 'pending_review', NULL" in insert_sql
    assert isinstance(insert_parameters, list)
    chunk_parameters = insert_parameters[0]
    assert chunk_parameters["document_version"] == 3
    assert chunk_parameters["processing_fingerprint"] == "database-fingerprint"
    metadata = json.loads(chunk_parameters["metadata"])
    assert metadata["document_version"] == 3
    assert metadata["observed_at"].endswith("Z")


def test_chunk_replace_rejects_version_mismatch_before_delete(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _install_fake_session(monkeypatch, _lease_row(version=4))

    with pytest.raises(ValueError, match="expected 4"):
        persistence.replace_document_chunks(_claimed_job(), [_chunk(version=3)])

    assert len(session.calls) == 1


def test_empty_chunk_collection_still_fences_then_atomically_clears(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _install_fake_session(monkeypatch, _lease_row())

    assert persistence.replace_document_chunks(_claimed_job(), []) == 0

    assert len(session.calls) == 2
    assert "FOR UPDATE OF tij, sd" in session.calls[0][0]
    assert "DELETE FROM source_chunks" in session.calls[1][0]


@pytest.mark.skipif(
    os.getenv("TEXTBOOK_INGESTION_POSTGRES_TEST") != "1",
    reason="requires disposable PostgreSQL on DATABASE_URL",
)
def test_persistence_round_trip_with_postgres(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    settings = Settings(
        data_backend="postgres",
        textbook_ingestion_enabled=True,
        textbook_storage_root=tmp_path / "textbooks",
        textbook_ingestion_lease_seconds=30,
        textbook_rag_elasticsearch_url="http://elasticsearch.test:9200",
        textbook_rag_embedding_base_url="http://embedding.test/v1",
        textbook_rag_embedding_api_key="test-key",
        textbook_rag_embedding_model="test-embedding",
        textbook_rag_embedding_dimension=2,
    )
    monkeypatch.setattr(repository, "get_settings", lambda: settings)
    monkeypatch.setattr(queue, "get_settings", lambda: settings)
    monkeypatch.setattr(persistence, "get_settings", lambda: settings)
    apply_migrations()
    document_id = ""
    try:
        document = repository.create_textbook_upload(
            title="Persistence Integration Textbook",
            filename="persistence.pdf",
            stream=BytesIO(_pdf_bytes("persistence-test")),
            content_type="application/pdf",
            uploaded_by=None,
            logical_textbook_key=f"persistence-{uuid.uuid4().hex}",
        )
        document_id = document["id"]
        job = queue.claim_next_job(f"persistence-worker-{uuid.uuid4().hex}")
        assert job is not None
        assert job.document_id == document_id

        processing_input = persistence.load_processing_input(job)
        page = _page()
        ocr_page = page.model_copy(
            update={
                "extraction_method": ExtractionMethod.MINERU,
                "quality": PageQuality(score=0.98, needs_ocr=False, flags=["ocr_complete"]),
                "ocr_provider": "mineru",
                "ocr_model": "integration-test-model",
            }
        )
        chunk = _chunk(document_id=document_id, version=processing_input.document_version)
        assert persistence.upsert_normalized_pages(job, [ocr_page]) == 1
        reusable_pages = persistence.load_reusable_ocr_pages(job)
        assert list(reusable_pages) == [ocr_page.page_number]
        assert reusable_pages[ocr_page.page_number].text == ocr_page.text
        assert reusable_pages[ocr_page.page_number].extraction_method == ExtractionMethod.MINERU
        assert reusable_pages[ocr_page.page_number].ocr_model == "integration-test-model"
        assert persistence.replace_document_chunks(job, [chunk]) == 1

        with db_session() as session:
            stored_page = session.execute(
                text(
                    "SELECT last_job_id, content_hash FROM textbook_document_pages "
                    "WHERE document_id = :document_id"
                ),
                {"document_id": document_id},
            ).mappings().one()
            stored_chunk = session.execute(
                text(
                    "SELECT document_version, content_status, review_required "
                    "FROM source_chunks WHERE document_id = :document_id"
                ),
                {"document_id": document_id},
            ).mappings().one()
        assert str(stored_page["last_job_id"]) == job.id
        assert len(stored_page["content_hash"]) == 64
        assert stored_chunk["document_version"] == processing_input.document_version
        assert stored_chunk["content_status"] == "pending_review"
        assert stored_chunk["review_required"] is True

        assert persistence.replace_document_chunks(job, []) == 0
        with db_session() as session:
            remaining = session.execute(
                text("SELECT count(*) FROM source_chunks WHERE document_id = :document_id"),
                {"document_id": document_id},
            ).scalar_one()
        assert remaining == 0
    finally:
        if document_id:
            with db_session() as session:
                session.execute(
                    text("DELETE FROM source_documents WHERE id = :document_id"),
                    {"document_id": document_id},
                )
