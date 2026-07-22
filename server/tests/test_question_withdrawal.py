from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any, Callable

import pytest

from server.app.domains.errors import DomainHTTPException
from server.app.domains.questions import bank, drafts
from server.app.experiment_admin_schemas import DraftUpdateRequest


ACTOR_ID = "00000000-0000-0000-0000-000000000001"
QUESTION_ID = "00000000-0000-0000-0000-000000000010"
GENERATION_ID = "00000000-0000-0000-0000-000000000020"
DRAFT_ID = "00000000-0000-0000-0000-000000000030"
OTHER_QUESTION_ID = "00000000-0000-0000-0000-000000000040"
REVOKED_AT = "2026-07-22T08:00:00+00:00"


class _FakeResult:
    def __init__(self, rows: list[dict[str, Any]] | None = None, *, scalar: Any = None) -> None:
        self._rows = rows or []
        self._scalar = scalar

    def mappings(self) -> _FakeResult:
        return self

    def all(self) -> list[dict[str, Any]]:
        return self._rows

    def one(self) -> dict[str, Any]:
        return self._rows[0]

    def first(self) -> dict[str, Any] | None:
        return self._rows[0] if self._rows else None

    def scalar_one_or_none(self) -> Any:
        return self._scalar


ResultFactory = Callable[[str, dict[str, Any]], _FakeResult]


class _FakeSession:
    def __init__(self, results: list[_FakeResult | ResultFactory]) -> None:
        self.results = list(results)
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def execute(self, statement: Any, params: dict[str, Any] | None = None) -> _FakeResult:
        sql = str(statement)
        clean_params = params or {}
        self.calls.append((sql, clean_params))
        if not self.results:
            raise AssertionError(f"Unexpected SQL: {sql}")
        result = self.results.pop(0)
        return result(sql, clean_params) if callable(result) else result


@contextmanager
def _fake_db_session(session: _FakeSession):
    yield session


def _evidence_metadata() -> dict[str, Any]:
    return {
        "source_audit": {
            "evidence_contract": "catalog_node_evidence",
            "evidence_source": "catalog_node_evidence",
            "target_point_node_ids": ["point-1"],
        }
    }


def _question_row(*, status: str = "published", stem: str = "原题干") -> dict[str, Any]:
    return {
        "id": QUESTION_ID,
        "bank_id": "00000000-0000-0000-0000-000000000050",
        "experiment_id": "EXP-1",
        "generation_id": None,
        "question_type": "single_choice",
        "stem": stem,
        "options": ["A. 正确", "B. 错误"],
        "answer": {"value": "A"},
        "explanation": "原解析",
        "difficulty": "basic",
        "related_chapter_ids": ["CH13"],
        "related_knowledge_point_ids": [],
        "source_chunk_ids": ["chunk-1"],
        "source_refs": [{"chunk_id": "chunk-1"}],
        "primary_point_node_ids": ["point-1"],
        "primary_canonical_point_ids": ["canonical-1"],
        "source_placement_node_ids": ["point-1"],
        "status": status,
        "metadata": _evidence_metadata(),
        "created_by": ACTOR_ID,
        "published_by": ACTOR_ID,
        "published_at": datetime(2026, 7, 20, tzinfo=timezone.utc),
    }


def _payload(*, stem: str = "修改后的题干", metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "question_type": "single_choice",
        "stem": stem,
        "options": ["A. 正确", "B. 错误"],
        "answer": {"value": "B"},
        "explanation": "修改后的解析",
        "difficulty": "basic",
        "related_chapter_ids": ["CH13"],
        "related_knowledge_point_ids": [],
        "source_chunk_ids": ["chunk-1"],
        "source_refs": [{"chunk_id": "chunk-1"}],
        "primary_point_node_ids": ["point-1"],
        "primary_canonical_point_ids": ["canonical-1"],
        "source_placement_node_ids": ["point-1"],
        "metadata": metadata if metadata is not None else _evidence_metadata(),
        "status": "draft",
    }


def _generation_row(*, legacy: bool = False) -> dict[str, Any]:
    metadata: dict[str, Any] = {"revoked_from_question_id": QUESTION_ID}
    if not legacy:
        metadata.update(
            {
                "operation": bank.QUESTION_WITHDRAWAL_OPERATION,
                "revoked_by_user_id": ACTOR_ID,
                "revoked_at": REVOKED_AT,
            }
        )
    return {
        "generation_mode": bank.LEGACY_QUESTION_WITHDRAWAL_MODE if legacy else bank.QUESTION_WITHDRAWAL_MODE,
        "generation_metadata": metadata,
        "generation_created_by": ACTOR_ID,
        "generation_created_at": datetime(2026, 7, 22, 8, tzinfo=timezone.utc),
    }


def _draft_row(*, status: str = "draft", legacy: bool = False, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "id": DRAFT_ID,
        "generation_id": GENERATION_ID,
        "experiment_id": "EXP-1",
        "payload": payload or _payload(),
        "validation_errors": [],
        "status": status,
        **_generation_row(legacy=legacy),
    }


def _install_draft_validation_fakes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(drafts, "normalize_question_point_identity", lambda _session, payload: payload)
    monkeypatch.setattr(drafts, "question_payload_has_catalog_evidence_lineage", lambda payload: True)

    def attach(_session: Any, *, payload: dict[str, Any], **_kwargs: Any) -> dict[str, Any]:
        metadata = dict(payload.get("metadata") or {})
        metadata["duplicate_risk"] = {"has_risk": False, "blocking": False}
        return {**payload, "metadata": metadata}

    monkeypatch.setattr(drafts, "attach_duplicate_risk_for_payload", attach)


def test_withdraw_published_question_locks_source_and_creates_authoritative_draft(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    generation = {"id": GENERATION_ID, **_generation_row()}
    draft = _draft_row()
    session = _FakeSession(
        [
            _FakeResult([_question_row()]),
            _FakeResult(scalar=None),
            _FakeResult([generation]),
            _FakeResult([draft]),
            _FakeResult(),
        ]
    )
    monkeypatch.setattr(bank, "db_session", lambda: _fake_db_session(session))

    result = bank.revoke_question_to_draft(
        question_id=QUESTION_ID,
        user=SimpleNamespace(id=ACTOR_ID),
    )

    assert result["id"] == DRAFT_ID
    assert result["revoked_from_question_id"] == QUESTION_ID
    assert result["withdrawal"] == {
        "revoked_from_question_id": QUESTION_ID,
        "revoked_by_user_id": ACTOR_ID,
        "revoked_at": REVOKED_AT,
    }
    assert "FOR UPDATE" in session.calls[0][0]
    generation_params = session.calls[2][1]
    generation_metadata = json.loads(generation_params["metadata"])
    assert generation_metadata["operation"] == bank.QUESTION_WITHDRAWAL_OPERATION
    assert generation_metadata["revoked_from_question_id"] == QUESTION_ID
    editable_payload = json.loads(session.calls[3][1]["payload"])
    assert "revoked_from_question_id" not in editable_payload
    assert "revoked_from_question_id" not in editable_payload["metadata"]
    source_update = session.calls[4][0]
    assert "SET status = 'disabled'" in source_update
    assert "published_by" not in source_update
    assert "published_at" not in source_update


def test_withdraw_rejects_non_published_source_before_creating_generation(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeSession([_FakeResult([_question_row(status="disabled")])])
    monkeypatch.setattr(bank, "db_session", lambda: _fake_db_session(session))

    with pytest.raises(DomainHTTPException) as exc_info:
        bank.revoke_question_to_draft(question_id=QUESTION_ID, user=SimpleNamespace(id=ACTOR_ID))

    assert exc_info.value.status_code == 400
    assert len(session.calls) == 1


def test_active_withdrawal_draft_prevents_a_second_draft_even_if_source_was_republished(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    session = _FakeSession([_FakeResult([_question_row()]), _FakeResult(scalar=DRAFT_ID)])
    monkeypatch.setattr(bank, "db_session", lambda: _fake_db_session(session))

    with pytest.raises(DomainHTTPException) as exc_info:
        bank.revoke_question_to_draft(question_id=QUESTION_ID, user=SimpleNamespace(id=ACTOR_ID))

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["draft_id"] == DRAFT_ID
    assert all("INSERT INTO experiment_question_generations" not in sql for sql, _params in session.calls)


def test_direct_publish_is_blocked_while_withdrawal_draft_is_active(monkeypatch: pytest.MonkeyPatch) -> None:
    session = _FakeSession([_FakeResult([_question_row(status="disabled")]), _FakeResult(scalar=DRAFT_ID)])
    monkeypatch.setattr(bank, "db_session", lambda: _fake_db_session(session))

    with pytest.raises(DomainHTTPException) as exc_info:
        bank.publish_question(question_id=QUESTION_ID, user=SimpleNamespace(id=ACTOR_ID))

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["draft_id"] == DRAFT_ID
    assert all("SET status = 'published'" not in sql for sql, _params in session.calls)


def test_disable_remains_a_single_independent_question_update(monkeypatch: pytest.MonkeyPatch) -> None:
    disabled = _question_row(status="disabled")
    session = _FakeSession([_FakeResult([disabled])])
    monkeypatch.setattr(bank, "db_session", lambda: _fake_db_session(session))

    result = bank.disable_question(question_id=QUESTION_ID, user=SimpleNamespace(id=ACTOR_ID))

    assert result["status"] == "disabled"
    assert len(session.calls) == 1
    assert "SET status = 'disabled'" in session.calls[0][0]
    assert "experiment_question_drafts" not in session.calls[0][0]


def test_draft_listing_is_active_only_and_exposes_read_only_withdrawal_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    listed = {
        **_draft_row(),
        "prompt": "撤回修订",
        "mode": bank.QUESTION_WITHDRAWAL_MODE,
        "warning": None,
        "experiment_code": "EXP-1",
        "experiment_title": "实验一",
    }
    session = _FakeSession([_FakeResult([listed])])
    monkeypatch.setattr(drafts, "db_session", lambda: _fake_db_session(session))

    result = drafts.list_question_drafts(point_node_id="point-1")

    assert result["total"] == 1
    assert result["items"][0]["revoked_from_question_id"] == QUESTION_ID
    assert "generation_metadata" not in result["items"][0]
    assert "d.status = 'draft'" in session.calls[0][0]


def test_update_withdrawal_draft_strips_spoofed_provenance_and_revalidates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_draft_validation_fakes(monkeypatch)
    malicious_metadata = {
        **_evidence_metadata(),
        "revoked_from_question_id": OTHER_QUESTION_ID,
        "revoked_by_user_id": OTHER_QUESTION_ID,
        "revoked_at": "2099-01-01T00:00:00Z",
    }

    def updated_row(_sql: str, params: dict[str, Any]) -> _FakeResult:
        return _FakeResult(
            [
                {
                    **_draft_row(),
                    "payload": json.loads(params["payload"]),
                    "validation_errors": json.loads(params["errors"]),
                }
            ]
        )

    session = _FakeSession([_FakeResult([_draft_row()]), updated_row])
    monkeypatch.setattr(drafts, "db_session", lambda: _fake_db_session(session))

    result = drafts.update_question_draft(
        draft_id=DRAFT_ID,
        payload=DraftUpdateRequest(payload=_payload(metadata=malicious_metadata), status="draft"),
    )

    saved_payload = json.loads(session.calls[1][1]["payload"])
    assert "FOR UPDATE OF d" in session.calls[0][0]
    assert "revoked_from_question_id" not in saved_payload["metadata"]
    assert "revoked_by_user_id" not in saved_payload["metadata"]
    assert saved_payload["metadata"]["duplicate_risk"]["has_risk"] is False
    assert result["revoked_from_question_id"] == QUESTION_ID
    assert result["revoked_by_user_id"] == ACTOR_ID


def test_draft_patch_cannot_bypass_publish_action() -> None:
    with pytest.raises(DomainHTTPException) as exc_info:
        drafts.update_question_draft(
            draft_id=DRAFT_ID,
            payload=DraftUpdateRequest(payload=_payload(), status="published"),
        )

    assert exc_info.value.status_code == 400


def test_publish_withdrawal_draft_locks_source_and_updates_original_question_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_draft_validation_fakes(monkeypatch)
    updated_question = {**_question_row(status="published", stem="修改后的题干"), "generation_id": GENERATION_ID}
    session = _FakeSession(
        [
            _FakeResult([_draft_row()]),
            _FakeResult([_question_row(status="disabled")]),
            _FakeResult([updated_question]),
            _FakeResult(),
        ]
    )
    monkeypatch.setattr(drafts, "db_session", lambda: _fake_db_session(session))
    monkeypatch.setattr(
        drafts,
        "_insert_question",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("withdrawal must not insert a new question")),
    )

    result = drafts.publish_question_draft(draft_id=DRAFT_ID, user=SimpleNamespace(id=ACTOR_ID))

    assert result["id"] == QUESTION_ID
    assert result["generation_id"] == GENERATION_ID
    assert "FOR UPDATE OF d, g" in session.calls[0][0]
    assert "FOR UPDATE" in session.calls[1][0]
    question_sql, question_params = session.calls[2]
    assert "UPDATE experiment_questions" in question_sql
    assert "status = 'published'" in question_sql
    assert question_params["id"] == QUESTION_ID
    assert question_params["source_status"] == "disabled"
    assert question_params["stem"] == "修改后的题干"
    stored_metadata = json.loads(question_params["metadata"])
    assert "revoked_from_question_id" not in stored_metadata
    assert stored_metadata["duplicate_risk"]["has_risk"] is False
    assert "status = 'published'" in session.calls[3][0]


def test_publish_withdrawal_draft_rejects_source_that_left_withdrawn_state(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_draft_validation_fakes(monkeypatch)
    session = _FakeSession([_FakeResult([_draft_row()]), _FakeResult([_question_row(status="published")])])
    monkeypatch.setattr(drafts, "db_session", lambda: _fake_db_session(session))

    with pytest.raises(DomainHTTPException) as exc_info:
        drafts.publish_question_draft(draft_id=DRAFT_ID, user=SimpleNamespace(id=ACTOR_ID))

    assert exc_info.value.status_code == 409
    assert len(session.calls) == 2


def test_publish_withdrawal_draft_keeps_current_evidence_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_draft_validation_fakes(monkeypatch)
    monkeypatch.setattr(drafts, "question_payload_has_catalog_evidence_lineage", lambda payload: False)
    session = _FakeSession([_FakeResult([_draft_row()])])
    monkeypatch.setattr(drafts, "db_session", lambda: _fake_db_session(session))

    with pytest.raises(DomainHTTPException) as exc_info:
        drafts.publish_question_draft(draft_id=DRAFT_ID, user=SimpleNamespace(id=ACTOR_ID))

    assert exc_info.value.status_code == 400
    assert "evidence lineage" in exc_info.value.detail["errors"][0]
    assert len(session.calls) == 1


def test_legacy_withdrawal_generation_uses_server_owned_generation_actor_and_time() -> None:
    provenance = bank._question_withdrawal_provenance(_generation_row(legacy=True))

    assert provenance == {
        "revoked_from_question_id": QUESTION_ID,
        "revoked_by_user_id": ACTOR_ID,
        "revoked_at": "2026-07-22T08:00:00+00:00",
        "source_status": "draft_or_disabled",
    }
