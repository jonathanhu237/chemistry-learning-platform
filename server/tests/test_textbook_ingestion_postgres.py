from __future__ import annotations

import os
import uuid
from io import BytesIO

import pytest
from sqlalchemy import text

from server.app.domains.textbook_ingestion import queue, repository
from server.app.domains.textbook_ingestion.contracts import IngestionStage
from server.app.domains.textbook_ingestion.errors import TextbookJobLeaseLostError
from server.app.infrastructure.database import apply_migrations, db_session
from server.app.infrastructure.settings import Settings


pytestmark = pytest.mark.skipif(
    os.getenv("TEXTBOOK_INGESTION_POSTGRES_TEST") != "1",
    reason="requires disposable PostgreSQL on DATABASE_URL",
)


@pytest.fixture()
def ingestion_settings(monkeypatch, tmp_path):
    settings = Settings(
        data_backend="postgres",
        textbook_ingestion_enabled=True,
        textbook_storage_root=tmp_path / "textbooks",
        textbook_ingestion_lease_seconds=30,
    )
    monkeypatch.setattr(repository, "get_settings", lambda: settings)
    monkeypatch.setattr(queue, "get_settings", lambda: settings)
    apply_migrations()
    yield settings


def _cleanup_documents(document_ids: list[str]) -> None:
    if not document_ids:
        return
    with db_session() as session:
        session.execute(
            text("DELETE FROM source_documents WHERE id = ANY(CAST(:ids AS text[]))"),
            {"ids": document_ids},
        )


def test_duplicate_pdf_upload_creates_distinct_version_and_job(ingestion_settings) -> None:
    key = f"test-textbook-{uuid.uuid4().hex}"
    created_ids: list[str] = []
    try:
        first = repository.create_textbook_upload(
            title="Synthetic Chemistry Textbook",
            filename="synthetic.pdf",
            stream=BytesIO(b"%PDF-1.7\nidentical-content"),
            content_type="application/pdf",
            uploaded_by=None,
            logical_textbook_key=key,
        )
        second = repository.create_textbook_upload(
            title="Synthetic Chemistry Textbook",
            filename="synthetic.pdf",
            stream=BytesIO(b"%PDF-1.7\nidentical-content"),
            content_type="application/pdf",
            uploaded_by=None,
            logical_textbook_key=key,
        )
        created_ids.extend([first["id"], second["id"]])

        assert first["id"] != second["id"]
        assert first["version_number"] == 1
        assert second["version_number"] == 2
        assert second["metadata"]["duplicate_of_document_id"] == first["id"]
        assert first["latest_job"]["status"] == "uploaded"
        assert second["latest_job"]["status"] == "uploaded"
    finally:
        _cleanup_documents(created_ids)


def test_reclaimed_job_rejects_stale_worker_updates(ingestion_settings) -> None:
    key = f"test-textbook-{uuid.uuid4().hex}"
    document_id = ""
    try:
        document = repository.create_textbook_upload(
            title="Lease Fencing Textbook",
            filename="lease.pdf",
            stream=BytesIO(b"%PDF-1.7\nlease-test"),
            content_type="application/pdf",
            uploaded_by=None,
            logical_textbook_key=key,
        )
        document_id = document["id"]
        first_claim = queue.claim_next_job("worker-a", lease_seconds=30)
        assert first_claim is not None
        assert first_claim.document_id == document_id
        assert first_claim.status == IngestionStage.EXTRACTING

        with db_session() as session:
            session.execute(
                text(
                    """
                    UPDATE textbook_ingestion_jobs
                    SET lease_expires_at = now() - interval '1 second'
                    WHERE id = CAST(:job_id AS uuid)
                    """
                ),
                {"job_id": first_claim.id},
            )

        second_claim = queue.claim_next_job("worker-b", lease_seconds=30)
        assert second_claim is not None
        assert second_claim.id == first_claim.id
        assert second_claim.lease_token != first_claim.lease_token

        with pytest.raises(TextbookJobLeaseLostError):
            queue.advance_job(first_claim, IngestionStage.STRUCTURING, progress=40)

        advanced = queue.advance_job(second_claim, IngestionStage.STRUCTURING, progress=40)
        assert advanced.status == IngestionStage.STRUCTURING
        assert repository.get_ingestion_job(second_claim.id)["status"] == "structuring"
    finally:
        _cleanup_documents([document_id] if document_id else [])


def test_active_cancellation_is_acknowledged_and_retry_is_fenced(ingestion_settings) -> None:
    key = f"test-textbook-{uuid.uuid4().hex}"
    document_id = ""
    try:
        document = repository.create_textbook_upload(
            title="Cancellation Textbook",
            filename="cancel.pdf",
            stream=BytesIO(b"%PDF-1.7\ncancel-test"),
            content_type="application/pdf",
            uploaded_by=None,
            logical_textbook_key=key,
        )
        document_id = document["id"]
        claimed = queue.claim_next_job("cancellation-worker", lease_seconds=30)
        assert claimed is not None

        requested = queue.request_cancellation(claimed.id, actor_id=None)
        assert requested["status"] == IngestionStage.EXTRACTING.value
        assert queue.cancellation_requested(claimed) is True

        queue.acknowledge_cancellation(claimed)
        cancelled = repository.get_ingestion_job(claimed.id)
        assert cancelled["status"] == IngestionStage.CANCELLED.value
        assert cancelled["worker_id"] is None

        retried = queue.retry_job(claimed.id, actor_id=None)
        assert retried["status"] == IngestionStage.UPLOADED.value
        second_claim = queue.claim_next_job("retry-worker", lease_seconds=30)
        assert second_claim is not None
        assert second_claim.id == claimed.id
        assert queue.release_job_for_retry(
            second_claim,
            error_code="temporary_upstream",
            error_message="temporary upstream failure",
            base_delay_seconds=1,
        ) is True
        scheduled = repository.get_ingestion_job(claimed.id)
        assert scheduled["status"] == IngestionStage.UPLOADED.value
        assert scheduled["resume_from_status"] == IngestionStage.EXTRACTING.value
        assert scheduled["worker_id"] is None
    finally:
        _cleanup_documents([document_id] if document_id else [])
