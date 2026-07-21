from __future__ import annotations

import os
import uuid
from io import BytesIO

import pytest
from sqlalchemy import text

from server.app.domains.textbook_ingestion import lifecycle, queue, repository
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
    monkeypatch.setattr(lifecycle, "get_settings", lambda: settings)
    apply_migrations()
    yield settings


def _cleanup_documents(document_ids: list[str]) -> None:
    if not document_ids:
        return
    with db_session() as session:
        session.execute(
            text("DELETE FROM source_chunks WHERE document_id = ANY(CAST(:ids AS text[]))"),
            {"ids": document_ids},
        )
        session.execute(
            text("DELETE FROM source_documents WHERE id = ANY(CAST(:ids AS text[]))"),
            {"ids": document_ids},
        )


def _mark_review_ready(document_id: str) -> str:
    chunk_id = f"chunk-{uuid.uuid4().hex}"
    with db_session() as session:
        session.execute(
            text(
                """
                INSERT INTO source_chunks (
                  id, document_id, page_number, chunk_index, text, markdown,
                  review_required, content_status, metadata, content_hash
                ) VALUES (
                  :chunk_id, :document_id, 1, 1, 'synthetic chemistry evidence',
                  'synthetic chemistry evidence', false, 'pending_review',
                  '{}'::jsonb, :content_hash
                )
                """
            ),
            {"chunk_id": chunk_id, "document_id": document_id, "content_hash": uuid.uuid4().hex},
        )
        session.execute(
            text(
                """
                UPDATE textbook_ingestion_jobs
                SET status = 'review_ready', progress = 100,
                    total_pages = 1, processed_pages = 1,
                    total_chunks = 1, embedded_chunks = 1, indexed_chunks = 1,
                    quality_report = CAST(:quality_report AS jsonb),
                    outputs = CAST(:outputs AS jsonb),
                    worker_id = NULL, lease_token = NULL, lease_expires_at = NULL,
                    updated_at = now()
                WHERE document_id = :document_id
                """
            ),
            {
                "document_id": document_id,
                "quality_report": '{"publishable": true, "blocking_issues": []}',
                "outputs": '{"index_verified": true, "indexed_chunks": 1}',
            },
        )
        session.execute(
            text(
                """
                UPDATE source_documents
                SET publication_status = 'review_ready', processing_status = 'review_ready', updated_at = now()
                WHERE id = :document_id
                """
            ),
            {"document_id": document_id},
        )
    return chunk_id


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


def test_publish_replace_and_rollback_switch_one_active_version_atomically(ingestion_settings) -> None:
    key = f"test-textbook-{uuid.uuid4().hex}"
    created_ids: list[str] = []
    try:
        with db_session() as session:
            initial_revision = int(
                session.execute(
                    text("SELECT revision FROM textbook_corpus_state WHERE singleton_key = 1")
                ).scalar_one()
            )

        first = repository.create_textbook_upload(
            title="Publication Textbook",
            filename="publication-v1.pdf",
            stream=BytesIO(b"%PDF-1.7\npublication-v1"),
            content_type="application/pdf",
            uploaded_by=None,
            logical_textbook_key=key,
        )
        created_ids.append(first["id"])
        _mark_review_ready(first["id"])
        published_first = lifecycle.publish_textbook(first["id"], actor_id=None)
        assert published_first["publication_status"] == "published"
        assert published_first["latest_job"]["status"] == "ready"

        second = repository.create_textbook_upload(
            title="Publication Textbook",
            filename="publication-v2.pdf",
            stream=BytesIO(b"%PDF-1.7\npublication-v2"),
            content_type="application/pdf",
            uploaded_by=None,
            logical_textbook_key=key,
        )
        created_ids.append(second["id"])
        _mark_review_ready(second["id"])
        lifecycle.publish_textbook(second["id"], actor_id=None)

        assert repository.get_textbook_document(first["id"])["publication_status"] == "inactive"
        assert repository.get_textbook_document(second["id"])["publication_status"] == "published"

        rolled_back = lifecycle.publish_textbook(first["id"], actor_id=None)
        assert rolled_back["publication_status"] == "published"
        assert repository.get_textbook_document(second["id"])["publication_status"] == "inactive"

        with db_session() as session:
            active_ids = session.execute(
                text(
                    """
                    SELECT id FROM source_documents
                    WHERE logical_textbook_key = :key AND publication_status = 'published'
                    """
                ),
                {"key": key},
            ).scalars().all()
            revision = int(
                session.execute(
                    text("SELECT revision FROM textbook_corpus_state WHERE singleton_key = 1")
                ).scalar_one()
            )
            actions = session.execute(
                text(
                    """
                    SELECT action FROM textbook_lifecycle_events
                    WHERE document_id = ANY(CAST(:ids AS text[]))
                      AND action IN ('publish', 'rollback')
                    ORDER BY created_at
                    """
                ),
                {"ids": created_ids},
            ).scalars().all()
        assert active_ids == [first["id"]]
        assert revision == initial_revision + 3
        assert actions == ["publish", "publish", "rollback"]
    finally:
        _cleanup_documents(created_ids)


def test_explicit_delete_removes_blob_and_projection_but_retains_audit_tombstone(ingestion_settings) -> None:
    key = f"test-textbook-{uuid.uuid4().hex}"
    document_id = ""
    projection_deletes: list[str] = []
    blob_deletes: list[str] = []
    try:
        document = repository.create_textbook_upload(
            title="Deleted Textbook",
            filename="delete.pdf",
            stream=BytesIO(b"%PDF-1.7\ndelete-me"),
            content_type="application/pdf",
            uploaded_by=None,
            logical_textbook_key=key,
        )
        document_id = document["id"]
        _mark_review_ready(document_id)

        deleted = lifecycle.delete_textbook(
            document_id,
            actor_id=None,
            projection_cleanup=lambda value: projection_deletes.append(value) or {"deleted": 1},
            blob_cleanup=lambda value: blob_deletes.append(value),
        )

        assert deleted["publication_status"] == "deleted"
        assert deleted["metadata"]["original_blob_deleted"] is True
        assert projection_deletes == [document_id]
        assert blob_deletes == [document["path"]]
        with db_session() as session:
            event = (
                session.execute(
                    text(
                        """
                        SELECT action, previous_publication_status, new_publication_status, details
                        FROM textbook_lifecycle_events
                        WHERE document_id = :document_id AND action = 'delete'
                        ORDER BY created_at DESC LIMIT 1
                        """
                    ),
                    {"document_id": document_id},
                )
                .mappings()
                .one()
            )
        assert event["previous_publication_status"] == "review_ready"
        assert event["new_publication_status"] == "deleted"
        assert event["details"]["original_blob_deleted"] is True
    finally:
        _cleanup_documents([document_id] if document_id else [])
