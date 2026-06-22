from __future__ import annotations

import inspect
from contextlib import contextmanager
from typing import Any

from server.app.domains.catalog_tree import jobs
from server.app.domains.catalog_tree.search_documents import student_search_document_sync_hash


class _Result:
    def __init__(self, row: dict[str, Any] | None = None, rows: list[dict[str, Any]] | None = None) -> None:
        self.row = row
        self.rows = rows or ([] if row is None else [row])

    def mappings(self) -> "_Result":
        return self

    def first(self) -> dict[str, Any] | None:
        return self.row

    def all(self) -> list[dict[str, Any]]:
        return self.rows

    def scalars(self) -> "_Result":
        return self


class _FakeSession:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def execute(self, statement: Any, params: dict[str, Any] | None = None) -> _Result:
        self.calls.append({"sql": str(statement), "params": params or {}})
        if "RETURNING id, node_id, job_type" in str(statement):
            return _Result(
                {
                    "id": "00000000-0000-0000-0000-000000000001",
                    "node_id": (params or {}).get("node_id"),
                    "job_type": (params or {}).get("job_type"),
                    "trigger_source": (params or {}).get("trigger_source"),
                    "status": "pending",
                    "attempts": 0,
                    "max_attempts": (params or {}).get("max_attempts", 3),
                    "payload": {},
                    "result": {},
                }
            )
        return _Result()


def _call_with_param(session: _FakeSession, key: str, value: Any) -> dict[str, Any]:
    return next(call for call in session.calls if call["params"].get(key) == value)


def test_enqueue_point_job_is_idempotent_for_open_equivalent_work() -> None:
    session = _FakeSession()

    row = jobs.enqueue_point_job(
        session,
        node_id="cat-point-1",
        job_type="rag_evidence_refresh",
        trigger_source="manual",
        payload={"reason": "manual_refresh"},
    )

    assert row["node_id"] == "cat-point-1"
    assert row["job_type"] == "rag_evidence_refresh"
    insert_call = _call_with_param(session, "job_type", "rag_evidence_refresh")
    assert "ON CONFLICT (idempotency_key) WHERE status IN ('pending', 'running')" in insert_call["sql"]
    assert insert_call["params"]["idempotency_key"].startswith("catalog-point:cat-point-1:rag_evidence_refresh:")
    assert insert_call["params"]["placement_node_id"] == "cat-point-1"
    assert insert_call["params"]["canonical_point_id"] == "cat-point-1"


def test_queue_es_sync_job_records_desired_action_and_catalog_node_identity() -> None:
    session = _FakeSession()

    jobs.queue_es_sync_job(session, node_id="cat-point-1", action="delete", trigger_source="automatic")

    params = _call_with_param(session, "job_type", "es_delete")["params"]
    assert params["node_id"] == "cat-point-1"
    assert params["job_type"] == "es_delete"
    assert params["placement_node_id"] == "cat-point-1"
    assert params["canonical_point_id"] == "cat-point-1"
    assert params["trigger_source"] == "automatic"
    assert '"desired_action": "delete"' in params["payload"]


def test_queue_es_soft_sync_job_coalesces_with_quiet_window_and_max_wait() -> None:
    session = _FakeSession()

    jobs.queue_es_sync_job(session, node_id="cat-point-1", action="upsert", trigger_source="automatic", soft=True)

    call = _call_with_param(session, "job_type", "es_upsert")
    params = call["params"]
    assert "LEAST(" in call["sql"]
    assert "experiment_catalog_point_jobs.created_at + (:max_coalesce_seconds * INTERVAL '1 second')" in call["sql"]
    assert params["idempotency_key"] == "catalog-point:cat-point-1:es_upsert:soft"
    assert params["run_after_seconds"] == jobs.SOFT_ES_SYNC_QUIET_SECONDS == 30
    assert params["max_coalesce_seconds"] == jobs.SOFT_ES_SYNC_MAX_WAIT_SECONDS == 180
    assert params["coalesce_with_open_job"] is True
    assert '"sync_mode": "soft"' in params["payload"]


def test_queue_es_hard_delete_runs_immediately() -> None:
    session = _FakeSession()

    jobs.queue_es_sync_job(session, node_id="cat-point-1", action="delete", trigger_source="manual")

    params = _call_with_param(session, "job_type", "es_delete")["params"]
    assert params["run_after_seconds"] == 0
    assert params["coalesce_with_open_job"] is False


def test_queue_teacher_search_sync_job_uses_independent_target_and_allows_directories() -> None:
    session = _FakeSession()

    row = jobs.queue_teacher_search_sync_job(
        session,
        node_id="cat-dir-1",
        action="upsert",
        trigger_source="automatic",
        soft=True,
    )

    assert row["node_id"] == "cat-dir-1"
    assert row["job_type"] == "teacher_search_upsert"
    params = _call_with_param(session, "job_type", "teacher_search_upsert")["params"]
    assert params["placement_node_id"] == "cat-dir-1"
    assert params["canonical_point_id"] is None
    assert params["idempotency_key"] == "catalog-teacher-search:cat-dir-1:teacher_search_upsert:soft"
    assert '"target_index": "teacher_catalog_search"' in params["payload"]
    assert '"sync_mode": "soft"' in params["payload"]


def test_mark_point_evidence_stale_does_not_block_or_auto_refresh_by_default(monkeypatch) -> None:
    session = _FakeSession()

    monkeypatch.setattr(jobs, "get_settings", lambda: type("Settings", (), {"catalog_point_evidence_auto_refresh": False})())

    jobs.mark_point_evidence_stale(session, node_id="cat-point-1", reason="point_content_edited")

    stale_call = _call_with_param(session, "evidence_status", "stale")["params"]
    assert stale_call["node_id"] == "cat-point-1"
    assert stale_call["canonical_point_id"] == "cat-point-1"
    assert stale_call["source_placement_node_id"] == "cat-point-1"
    assert stale_call["stale_reason"] == "point_content_edited"


def test_worker_claim_uses_database_locking_to_avoid_duplicate_execution() -> None:
    source = inspect.getsource(jobs.claim_next_point_job)

    assert "FOR UPDATE SKIP LOCKED" in source
    assert "status = 'pending'" in source
    assert "attempts < max_attempts" in source


def test_process_point_job_records_bge_unavailable_as_diagnostic_status(monkeypatch) -> None:
    calls: list[dict[str, Any]] = []
    job = jobs.CatalogPointJob(
        id="00000000-0000-0000-0000-000000000002",
        node_id="cat-point-1",
        job_type="rag_evidence_refresh",
        attempts=1,
        payload={},
    )

    def raise_unavailable(_job: jobs.CatalogPointJob) -> dict[str, Any]:
        raise jobs.CatalogPointJobUnavailable("BGE service is unreachable")

    monkeypatch.setattr(jobs, "_process_rag_evidence_refresh", raise_unavailable)
    monkeypatch.setattr(
        jobs,
        "_mark_evidence_failure",
        lambda **kwargs: calls.append({"kind": "evidence_failure", **kwargs}),
    )
    monkeypatch.setattr(
        jobs,
        "fail_point_job",
        lambda failed_job, error, status_value="failed", result=None: calls.append(
            {"kind": "job_failure", "job_id": failed_job.id, "error": error, "status": status_value}
        ),
    )

    jobs.process_point_job(job)

    assert calls[0]["kind"] == "evidence_failure"
    assert calls[0]["node_id"] == "cat-point-1"
    assert calls[0]["evidence_status"] == "unavailable"
    assert calls[1]["kind"] == "job_failure"
    assert calls[1]["status"] == "unavailable"
    assert "BGE service is unreachable" in calls[1]["error"]


def test_teacher_projection_failure_marks_only_teacher_search_state(monkeypatch) -> None:
    calls: list[dict[str, Any]] = []
    job = jobs.CatalogPointJob(
        id="00000000-0000-0000-0000-000000000003",
        node_id="cat-point-1",
        job_type="teacher_search_upsert",
        attempts=1,
        payload={},
    )

    def fail_teacher(_job: jobs.CatalogPointJob) -> dict[str, Any]:
        raise RuntimeError("teacher index is down")

    monkeypatch.setattr(jobs, "_process_teacher_search_job", fail_teacher)
    monkeypatch.setattr(jobs, "_mark_es_state_failure", lambda **kwargs: calls.append({"kind": "student_failure", **kwargs}))
    monkeypatch.setattr(
        "server.app.domains.catalog_tree.teacher_search.mark_teacher_search_state_failure",
        lambda **kwargs: calls.append({"kind": "teacher_failure", **kwargs}),
    )
    monkeypatch.setattr(
        jobs,
        "fail_point_job",
        lambda failed_job, error, status_value="failed", result=None: calls.append(
            {"kind": "job_failure", "job_id": failed_job.id, "error": error, "status": status_value}
        ),
    )

    jobs.process_point_job(job)

    assert [call["kind"] for call in calls] == ["teacher_failure", "job_failure"]
    assert calls[0]["node_id"] == "cat-point-1"
    assert calls[0]["action"] == "upsert"
    assert calls[1]["status"] == "failed"
    assert "teacher index is down" in calls[1]["error"]


def test_student_projection_failure_marks_only_student_search_state(monkeypatch) -> None:
    calls: list[dict[str, Any]] = []
    job = jobs.CatalogPointJob(
        id="00000000-0000-0000-0000-000000000004",
        node_id="cat-point-1",
        job_type="es_upsert",
        attempts=1,
        payload={},
    )

    def fail_student(_job: jobs.CatalogPointJob) -> dict[str, Any]:
        raise RuntimeError("student index is down")

    monkeypatch.setattr(jobs, "_process_es_job", fail_student)
    monkeypatch.setattr(jobs, "_mark_es_state_failure", lambda **kwargs: calls.append({"kind": "student_failure", **kwargs}))
    monkeypatch.setattr(
        "server.app.domains.catalog_tree.teacher_search.mark_teacher_search_state_failure",
        lambda **kwargs: calls.append({"kind": "teacher_failure", **kwargs}),
    )
    monkeypatch.setattr(
        jobs,
        "fail_point_job",
        lambda failed_job, error, status_value="failed", result=None: calls.append(
            {"kind": "job_failure", "job_id": failed_job.id, "error": error, "status": status_value}
        ),
    )

    jobs.process_point_job(job)

    assert [call["kind"] for call in calls] == ["student_failure", "job_failure"]
    assert calls[0]["node_id"] == "cat-point-1"
    assert calls[0]["action"] == "upsert"
    assert calls[1]["status"] == "failed"
    assert "student index is down" in calls[1]["error"]


def test_rag_runtime_gate_requires_configured_hybrid_bge() -> None:
    settings = type(
        "Settings",
        (),
        {
            "rag_hybrid_bge_enabled": False,
            "rag_query_generation_enabled": True,
            "rag_bge_service_url": "",
            "rag_vector_top_k": 24,
            "rag_rerank_top_k": 9,
            "rag_final_top_k": 5,
        },
    )()

    gate = jobs._rag_runtime_gate(settings)

    assert gate["healthy"] is False
    assert gate["status"] == "unavailable"
    assert gate["reason_code"] == "hybrid_bge_disabled"


class _FakeDbSession:
    def __init__(self, document_hash: str | None = None) -> None:
        self.document_hash = document_hash

    def execute(self, statement: Any, params: dict[str, Any] | None = None) -> _Result:
        if "SELECT document_hash FROM experiment_catalog_point_search_index_state" in str(statement):
            return _Result({"document_hash": self.document_hash} if self.document_hash else None)
        return _Result()


@contextmanager
def _fake_db_session(document_hash: str | None = None):
    yield _FakeDbSession(document_hash=document_hash)


class _FakeIndexClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, Any]] = []

    def ensure_index(self, analyzer: str | None = None) -> None:
        self.calls.append(("ensure_index", analyzer))

    def upsert_document(self, document: dict[str, Any]) -> None:
        self.calls.append(("upsert", document))

    def delete_document(self, document_id: str) -> None:
        self.calls.append(("delete", document_id))


def test_process_es_job_skips_upsert_when_document_hash_is_unchanged(monkeypatch) -> None:
    document = {"id": "cat-point-1", "title": "氯水 + KI", "updated_at": "2026-06-22T00:00:00"}
    sync_hash = student_search_document_sync_hash(document)
    client = _FakeIndexClient()
    marks: list[dict[str, Any]] = []

    monkeypatch.setattr(jobs, "db_session", lambda: _fake_db_session(sync_hash))
    monkeypatch.setattr("server.app.domains.catalog_tree.search_documents.student_search_document_for_node", lambda *_args, **_kwargs: document)
    monkeypatch.setattr("server.app.domains.video_library.index_client.configured_index_client", lambda: client)
    monkeypatch.setattr(jobs, "_mark_es_state_success", lambda **kwargs: marks.append(kwargs))

    result = jobs._process_es_job(jobs.CatalogPointJob(id="job-1", node_id="cat-point-1", job_type="es_upsert", attempts=1, payload={}))

    assert result["no_op"] is True
    assert client.calls == []
    assert marks == [{"node_id": "cat-point-1", "action": "upsert", "document_hash": sync_hash, "indexed": False}]


def test_process_es_job_upserts_when_document_hash_changes(monkeypatch) -> None:
    document = {"id": "cat-point-1", "title": "氯水 + KI", "updated_at": "2026-06-22T00:00:00"}
    sync_hash = student_search_document_sync_hash(document)
    client = _FakeIndexClient()
    marks: list[dict[str, Any]] = []
    settings = type("Settings", (), {"video_library_search_analyzer": "ik_max_word"})()

    monkeypatch.setattr(jobs, "db_session", lambda: _fake_db_session("old-hash"))
    monkeypatch.setattr("server.app.domains.catalog_tree.search_documents.student_search_document_for_node", lambda *_args, **_kwargs: document)
    monkeypatch.setattr("server.app.domains.video_library.index_client.configured_index_client", lambda: client)
    monkeypatch.setattr(jobs, "get_settings", lambda: settings)
    monkeypatch.setattr(jobs, "_mark_es_state_success", lambda **kwargs: marks.append(kwargs))

    result = jobs._process_es_job(jobs.CatalogPointJob(id="job-1", node_id="cat-point-1", job_type="es_upsert", attempts=1, payload={}))

    assert result["document_hash"] == sync_hash
    assert client.calls == [("ensure_index", "ik_max_word"), ("upsert", document)]
    assert marks == [{"node_id": "cat-point-1", "action": "upsert", "document_hash": sync_hash, "analyzer_version": "ik_max_word"}]


def test_process_es_job_deletes_when_upsert_target_is_no_longer_searchable(monkeypatch) -> None:
    client = _FakeIndexClient()
    marks: list[dict[str, Any]] = []

    monkeypatch.setattr(jobs, "db_session", lambda: _fake_db_session("old-hash"))
    monkeypatch.setattr("server.app.domains.catalog_tree.search_documents.student_search_document_for_node", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("server.app.domains.video_library.index_client.configured_index_client", lambda: client)
    monkeypatch.setattr(jobs, "_mark_es_state_success", lambda **kwargs: marks.append(kwargs))

    result = jobs._process_es_job(jobs.CatalogPointJob(id="job-1", node_id="cat-point-1", job_type="es_upsert", attempts=1, payload={}))

    assert result["reason"] == "point_not_searchable"
    assert client.calls == [("delete", "cat-point-1")]
    assert marks == [{"node_id": "cat-point-1", "action": "delete", "document_hash": "not_searchable"}]
