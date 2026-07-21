from __future__ import annotations

import threading
from types import SimpleNamespace

from server.app.domains.textbook_ingestion.config import (
    processing_config_snapshot,
    processing_fingerprint,
)
from server.app.domains.textbook_ingestion.contracts import IngestionStage
from server.app.domains.textbook_ingestion.errors import TextbookJobLeaseLostError
from server.app.domains.textbook_ingestion.queue import ClaimedIngestionJob
from server.app.infrastructure.settings import Settings
from server.app.workers import textbook_ingestion_worker as worker


def _settings() -> Settings:
    return Settings(
        data_backend="postgres",
        textbook_ingestion_enabled=True,
        textbook_ingestion_lease_seconds=30,
        textbook_rag_elasticsearch_url="http://elasticsearch.test:9200",
        textbook_rag_elasticsearch_index="textbook-test",
        textbook_rag_embedding_base_url="http://embedding.test/v1",
        textbook_rag_embedding_api_key="test-key",
        textbook_rag_embedding_model="test-embedding",
        textbook_rag_embedding_dimension=2,
    )


def _job(settings: Settings, *, current_config: bool = True) -> ClaimedIngestionJob:
    snapshot = processing_config_snapshot(settings) if current_config else {"schema_version": 0}
    return ClaimedIngestionJob(
        id="11111111-1111-4111-8111-111111111111",
        document_id="tbk-worker-test",
        status=IngestionStage.EXTRACTING,
        attempts=1,
        max_attempts=3,
        worker_id="worker-test",
        lease_token="22222222-2222-4222-8222-222222222222",
        processing_fingerprint=processing_fingerprint(snapshot),
        config_snapshot=snapshot,
    )


def test_independent_heartbeat_runs_while_job_code_is_blocked(monkeypatch) -> None:
    called = threading.Event()
    job = _job(_settings())
    monkeypatch.setattr(worker, "heartbeat", lambda *_args, **_kwargs: called.set())
    runner = worker._LeaseHeartbeat(job, lease_seconds=30)
    runner.interval_seconds = 0.01

    with runner:
        assert called.wait(0.5)

    assert runner.error is None


def test_worker_rejects_claim_when_processing_snapshot_changed(monkeypatch) -> None:
    settings = _settings()
    job = _job(settings, current_config=False)
    failures: list[dict[str, str]] = []
    monkeypatch.setattr(worker, "claim_next_job", lambda _worker_id: job)
    monkeypatch.setattr(worker, "fail_job", lambda _job, **kwargs: failures.append(kwargs))
    monkeypatch.setattr(
        worker,
        "build_pipeline",
        lambda _settings: (_ for _ in ()).throw(AssertionError("pipeline must not be built")),
    )

    assert worker.run_once(settings=settings) is True
    assert failures == [
        {
            "error_code": "processing_config_changed",
            "error_message": "Worker processing configuration changed; retry the job to capture the new configuration",
        }
    ]


def test_per_job_lease_loss_does_not_terminate_worker_loop(monkeypatch) -> None:
    settings = _settings()
    job = _job(settings)
    monkeypatch.setattr(worker, "claim_next_job", lambda _worker_id: job)
    monkeypatch.setattr(worker, "heartbeat", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(
        worker,
        "build_pipeline",
        lambda _settings: SimpleNamespace(
            process=lambda _job: (_ for _ in ()).throw(TextbookJobLeaseLostError("lease lost"))
        ),
    )

    assert worker.run_once(settings=settings) is True
