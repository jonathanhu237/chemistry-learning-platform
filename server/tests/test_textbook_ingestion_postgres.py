from __future__ import annotations

import os
import uuid
from io import BytesIO

import pymupdf
import pytest
from sqlalchemy import text

from server.app.domains.textbook_ingestion import lifecycle, queue, recovery, repository
from server.app.domains.textbook_ingestion.contracts import IngestionStage
from server.app.domains.textbook_ingestion.errors import TextbookJobLeaseLostError
from server.app.infrastructure.database import apply_migrations, db_session
from server.app.infrastructure.settings import Settings


pytestmark = pytest.mark.skipif(
    os.getenv("TEXTBOOK_INGESTION_POSTGRES_TEST") != "1",
    reason="requires disposable PostgreSQL on DATABASE_URL",
)


def _pdf_bytes(label: str) -> bytes:
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), label)
    try:
        return document.tobytes()
    finally:
        document.close()


@pytest.fixture()
def ingestion_settings(monkeypatch, tmp_path):
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
    monkeypatch.setattr(lifecycle, "get_settings", lambda: settings)
    monkeypatch.setattr(lifecycle, "effective_ingestion_settings", lambda: settings)
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
                  review_required, content_status, metadata, content_hash,
                  document_version, processing_fingerprint
                ) VALUES (
                  :chunk_id, :document_id, 1, 1, 'synthetic chemistry evidence',
                  'synthetic chemistry evidence', false, 'pending_review',
                  '{}'::jsonb, :content_hash,
                  (SELECT version_number FROM source_documents WHERE id = :document_id),
                  (SELECT processing_fingerprint FROM source_documents WHERE id = :document_id)
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


def _verified_live_projection(
    _document: dict[str, object],
    _latest_job: dict[str, object] | None,
    chunk_count: int,
) -> dict[str, object]:
    return {
        "verified": True,
        "expected_chunk_count": chunk_count,
        "actual_chunk_count": chunk_count,
        "contract_chunk_count": chunk_count,
        "blockers": [],
    }


def test_duplicate_pdf_upload_creates_distinct_version_and_job(ingestion_settings) -> None:
    key = f"test-textbook-{uuid.uuid4().hex}"
    created_ids: list[str] = []
    content = _pdf_bytes("identical-content")
    try:
        first = repository.create_textbook_upload(
            title="Synthetic Chemistry Textbook",
            filename="synthetic.pdf",
            stream=BytesIO(content),
            content_type="application/pdf",
            uploaded_by=None,
            logical_textbook_key=key,
        )
        second = repository.create_textbook_upload(
            title="Synthetic Chemistry Textbook",
            filename="synthetic.pdf",
            stream=BytesIO(content),
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
            stream=BytesIO(_pdf_bytes("lease-test")),
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
            stream=BytesIO(_pdf_bytes("cancel-test")),
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

        with pytest.raises(TextbookJobLeaseLostError):
            queue.fail_job(
                claimed,
                error_code="synthetic_failure_after_cancel",
                error_message="a failure must not overwrite the cancellation request",
            )
        assert repository.get_ingestion_job(claimed.id)["status"] == IngestionStage.EXTRACTING.value

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


def test_unclaimed_cancellation_finishes_immediately(ingestion_settings) -> None:
    document_id = ""
    try:
        document = repository.create_textbook_upload(
            title="Queued Cancellation Textbook",
            filename="queued-cancel.pdf",
            stream=BytesIO(_pdf_bytes("queued-cancel")),
            content_type="application/pdf",
            uploaded_by=None,
            logical_textbook_key=f"queued-cancel-{uuid.uuid4().hex}",
        )
        document_id = document["id"]

        cancelled = queue.request_cancellation(document["latest_job"]["id"], actor_id=None)

        assert cancelled["status"] == IngestionStage.CANCELLED.value
        assert cancelled["worker_id"] is None
        assert repository.get_textbook_document(document_id)["processing_status"] == "cancelled"
    finally:
        _cleanup_documents([document_id] if document_id else [])


def test_reaper_finalizes_dead_cancellation_and_exhausted_final_attempt(ingestion_settings) -> None:
    document_ids: list[str] = []
    try:
        cancelled_document = repository.create_textbook_upload(
            title="Dead Cancellation Textbook",
            filename="dead-cancel.pdf",
            stream=BytesIO(_pdf_bytes("dead-cancel")),
            content_type="application/pdf",
            uploaded_by=None,
            logical_textbook_key=f"dead-cancel-{uuid.uuid4().hex}",
        )
        document_ids.append(cancelled_document["id"])
        cancelled_claim = queue.claim_next_job("dead-cancel-worker", lease_seconds=30)
        assert cancelled_claim is not None
        queue.request_cancellation(cancelled_claim.id, actor_id=None)

        failed_document = repository.create_textbook_upload(
            title="Exhausted Lease Textbook",
            filename="exhausted.pdf",
            stream=BytesIO(_pdf_bytes("exhausted")),
            content_type="application/pdf",
            uploaded_by=None,
            logical_textbook_key=f"exhausted-{uuid.uuid4().hex}",
        )
        document_ids.append(failed_document["id"])
        with db_session() as session:
            session.execute(
                text(
                    """
                    UPDATE textbook_ingestion_jobs
                    SET lease_expires_at = now() - interval '1 second'
                    WHERE id = CAST(:job_id AS uuid)
                    """
                ),
                {"job_id": cancelled_claim.id},
            )
        exhausted_claim = queue.claim_next_job("exhausted-worker", lease_seconds=30)
        assert exhausted_claim is not None
        assert exhausted_claim.document_id == failed_document["id"]
        with db_session() as session:
            session.execute(
                text(
                    """
                    UPDATE textbook_ingestion_jobs
                    SET attempts = max_attempts,
                        lease_expires_at = now() - interval '1 second'
                    WHERE id = CAST(:job_id AS uuid)
                    """
                ),
                {"job_id": exhausted_claim.id},
            )

        reaped = queue.reap_stale_jobs()

        assert reaped == {"cancelled": 0, "failed": 1}
        assert repository.get_ingestion_job(cancelled_claim.id)["status"] == IngestionStage.CANCELLED.value
        failed = repository.get_ingestion_job(exhausted_claim.id)
        assert failed["status"] == IngestionStage.FAILED.value
        assert failed["error_code"] == "attempts_exhausted"
    finally:
        _cleanup_documents(document_ids)


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
            stream=BytesIO(_pdf_bytes("publication-v1")),
            content_type="application/pdf",
            uploaded_by=None,
            logical_textbook_key=key,
        )
        created_ids.append(first["id"])
        _mark_review_ready(first["id"])
        published_first = lifecycle.publish_textbook(
            first["id"],
            actor_id=None,
            projection_verifier=_verified_live_projection,
        )
        assert published_first["publication_status"] == "published"
        assert published_first["latest_job"]["status"] == "ready"

        second = repository.create_textbook_upload(
            title="Publication Textbook",
            filename="publication-v2.pdf",
            stream=BytesIO(_pdf_bytes("publication-v2")),
            content_type="application/pdf",
            uploaded_by=None,
            logical_textbook_key=key,
        )
        created_ids.append(second["id"])
        _mark_review_ready(second["id"])
        lifecycle.publish_textbook(
            second["id"],
            actor_id=None,
            projection_verifier=_verified_live_projection,
        )

        assert repository.get_textbook_document(first["id"])["publication_status"] == "inactive"
        assert repository.get_textbook_document(second["id"])["publication_status"] == "published"

        rolled_back = lifecycle.publish_textbook(
            first["id"],
            actor_id=None,
            projection_verifier=_verified_live_projection,
        )
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
            stream=BytesIO(_pdf_bytes("delete-me")),
            content_type="application/pdf",
            uploaded_by=None,
            logical_textbook_key=key,
        )
        document_id = document["id"]
        _mark_review_ready(document_id)

        def delete_projection(value: str) -> dict[str, int]:
            with db_session() as session:
                durable_status = session.execute(
                    text("SELECT publication_status FROM source_documents WHERE id = :document_id"),
                    {"document_id": value},
                ).scalar_one()
            assert durable_status == "deleted"
            projection_deletes.append(value)
            return {"deleted": 1}

        deleted = lifecycle.delete_textbook(
            document_id,
            actor_id=None,
            projection_cleanup=delete_projection,
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
        assert event["details"]["phase"] == "cleanup_complete"
    finally:
        _cleanup_documents([document_id] if document_id else [])


def test_delete_cleanup_failure_is_durable_and_retryable(ingestion_settings) -> None:
    key = f"test-textbook-{uuid.uuid4().hex}"
    document_id = ""
    projection_attempts: list[str] = []
    blob_deletes: list[str] = []
    try:
        document = repository.create_textbook_upload(
            title="Retry Deleted Textbook",
            filename="delete-retry.pdf",
            stream=BytesIO(_pdf_bytes("delete-retry")),
            content_type="application/pdf",
            uploaded_by=None,
            logical_textbook_key=key,
        )
        document_id = document["id"]
        _mark_review_ready(document_id)

        def fail_projection(value: str) -> dict[str, int]:
            projection_attempts.append(value)
            raise RuntimeError("synthetic ES cleanup failure")

        with pytest.raises(lifecycle.TextbookIngestionError) as raised:
            lifecycle.delete_textbook(
                document_id,
                actor_id=None,
                projection_cleanup=fail_projection,
                blob_cleanup=lambda value: blob_deletes.append(value),
            )
        assert raised.value.reason == "textbook_delete_cleanup_failed"

        failed = repository.get_textbook_document(document_id)
        assert failed["publication_status"] == "deleted"
        assert failed["metadata"]["deletion_cleanup"]["status"] == "failed"
        assert failed["metadata"]["deletion_cleanup"]["projection"]["status"] == "failed"
        assert failed["metadata"]["deletion_cleanup"]["blob"]["status"] == "complete"

        recovered = lifecycle.delete_textbook(
            document_id,
            actor_id=None,
            projection_cleanup=lambda value: projection_attempts.append(value) or {"deleted": 0},
            blob_cleanup=lambda value: blob_deletes.append(f"unexpected:{value}"),
        )
        assert recovered["publication_status"] == "deleted"
        assert recovered["metadata"]["deletion_cleanup"]["status"] == "complete"
        assert recovered["metadata"]["deletion_cleanup"]["attempt"] == 2
        assert projection_attempts == [document_id, document_id]
        assert blob_deletes == [document["path"]]
    finally:
        _cleanup_documents([document_id] if document_id else [])


def test_recovery_loads_retained_online_chunks_without_postgres_vectors(ingestion_settings) -> None:
    document_id = ""
    try:
        document = repository.create_textbook_upload(
            title="Recoverable Textbook",
            filename="recoverable.pdf",
            stream=BytesIO(_pdf_bytes("recoverable")),
            content_type="application/pdf",
            uploaded_by=None,
            logical_textbook_key=f"recoverable-{uuid.uuid4().hex}",
        )
        document_id = document["id"]
        chunk_id = _mark_review_ready(document_id)
        lifecycle.publish_textbook(
            document_id,
            actor_id=None,
            projection_verifier=_verified_live_projection,
        )
        lifecycle.deactivate_textbook(document_id, actor_id=None)

        inventory = recovery.online_textbook_inventory()
        loaded = recovery.load_online_textbooks_for_reprojection(
            document_ids=[document_id],
        )

        assert inventory["by_status"]["inactive"]["documents"] >= 1
        assert len(loaded) == 1
        assert loaded[0].document_id == document_id
        assert loaded[0].publication_status == "inactive"
        assert [chunk.chunk_id for chunk in loaded[0].chunks] == [chunk_id]
        assert loaded[0].expected_embedding_model == ingestion_settings.textbook_rag_embedding_model
        recovery.commit_recovered_projection_run(
            loaded[0],
            "recovery-run-pg-1",
            {
                "index_verified": True,
                "indexed_chunks": 1,
                "projection_run_id": "recovery-run-pg-1",
            },
        )
        recovered_document = repository.get_textbook_document(document_id)
        assert recovered_document["active_projection_run_id"] == "recovery-run-pg-1"
        assert recovered_document["latest_job"]["outputs"]["projection_run_id"] == (
            "recovery-run-pg-1"
        )
        with db_session() as session:
            postgres_vector_rows = int(
                session.execute(
                    text(
                        """
                        SELECT count(*)
                        FROM chunk_embeddings ce
                        JOIN source_chunks sc ON sc.id = ce.chunk_id
                        WHERE sc.document_id = :document_id
                        """
                    ),
                    {"document_id": document_id},
                ).scalar_one()
            )
        assert postgres_vector_rows == 0
    finally:
        _cleanup_documents([document_id] if document_id else [])


def test_older_delete_cleanup_attempt_cannot_overwrite_newer_success(ingestion_settings) -> None:
    document_id = ""
    nested_results: list[dict[str, object]] = []
    try:
        document = repository.create_textbook_upload(
            title="Concurrent Delete Textbook",
            filename="concurrent-delete.pdf",
            stream=BytesIO(_pdf_bytes("concurrent-delete")),
            content_type="application/pdf",
            uploaded_by=None,
            logical_textbook_key=f"concurrent-delete-{uuid.uuid4().hex}",
        )
        document_id = document["id"]
        _mark_review_ready(document_id)

        def outer_projection_cleanup(value: str) -> dict[str, int]:
            nested_results.append(
                lifecycle.delete_textbook(
                    value,
                    actor_id=None,
                    projection_cleanup=lambda _nested: {"deleted": 0},
                    blob_cleanup=lambda _path: None,
                )
            )
            return {"deleted": 0}

        outer = lifecycle.delete_textbook(
            document_id,
            actor_id=None,
            projection_cleanup=outer_projection_cleanup,
            blob_cleanup=lambda _path: None,
        )

        assert outer["cleanup_superseded"] is True
        assert nested_results[0]["metadata"]["deletion_cleanup"]["attempt"] == 2
        durable = repository.get_textbook_document(document_id)
        assert durable["metadata"]["deletion_cleanup"]["attempt"] == 2
        assert durable["metadata"]["deletion_cleanup"]["status"] == "complete"
        with db_session() as session:
            phases = session.execute(
                text(
                    """
                    SELECT details->>'phase'
                    FROM textbook_lifecycle_events
                    WHERE document_id = :document_id AND action = 'delete'
                    ORDER BY created_at
                    """
                ),
                {"document_id": document_id},
            ).scalars().all()
        assert phases == ["cleanup_superseded", "cleanup_complete"]
    finally:
        _cleanup_documents([document_id] if document_id else [])
