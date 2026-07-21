from __future__ import annotations

from collections.abc import Iterator
from uuid import UUID

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from server.app.api.admin import admin_textbooks
from server.app.auth import AuthUser, require_teacher_console_user
from server.app.domains.textbook_ingestion.views import public_chunk


_JOB_ID = UUID("ed44a919-f189-4ce3-b153-48bcecf28cc3")


def _teacher() -> AuthUser:
    return AuthUser(
        id="9b15d768-b7f8-4e1a-b7d0-82595404ae09",
        username="teacher",
        role="teacher",
        display_name="Teacher",
        status="active",
    )


@pytest.fixture
def client() -> Iterator[TestClient]:
    app = FastAPI()
    app.include_router(admin_textbooks.router)
    app.dependency_overrides[require_teacher_console_user] = _teacher
    with TestClient(app) as test_client:
        yield test_client


def _job_row() -> dict[str, object]:
    return {
        "id": str(_JOB_ID),
        "document_id": "textbook-1",
        "status": "failed",
        "progress": 30,
        "attempts": 1,
        "max_attempts": 3,
    }


def test_public_chunk_exposes_only_safe_metadata_fields() -> None:
    row = {
        "id": "chunk-1",
        "text": "氯气与水反应。",
        "metadata": {
            "source_collection": "textbook_inorganic_lower_v1",
            "knowledge_unit": "氯及其化合物",
            "formulas": ["Cl2"],
            "chunking_strategy": "structure-aware-v1",
            "source_page_numbers": [12],
            "import_version": "canonical_base_v1",
            "import_source_file": "/srv/private/canonical/chunks.jsonl",
            "source_md_files": ["/srv/private/pages/12.md"],
            "source_page_images": ["/srv/private/pages/12.png"],
            "asset_paths": ["/srv/private/assets/figure-1.png"],
            "internal_note": "must not cross the API boundary",
        },
    }

    result = public_chunk(row)

    assert result["metadata"] == {
        "source_collection": "textbook_inorganic_lower_v1",
        "knowledge_unit": "氯及其化合物",
        "formulas": ["Cl2"],
        "chunking_strategy": "structure-aware-v1",
        "source_page_numbers": [12],
        "import_version": "canonical_base_v1",
    }


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/admin/textbooks/jobs/not-a-uuid"),
        ("GET", "/api/admin/textbooks/jobs/not-a-uuid/events"),
        ("POST", "/api/admin/textbooks/jobs/not-a-uuid/cancel"),
        ("POST", "/api/admin/textbooks/jobs/not-a-uuid/retry"),
    ],
)
def test_job_routes_reject_malformed_uuid(
    client: TestClient,
    method: str,
    path: str,
) -> None:
    response = client.request(method, path)

    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["path", "job_id"]


def test_job_routes_pass_normalized_uuid_strings_to_domain_calls(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    received: list[tuple[str, str, object]] = []

    def record_get(job_id: str) -> dict[str, object]:
        received.append(("get", job_id, None))
        return _job_row()

    def record_events(job_id: str, *, limit: int) -> dict[str, object]:
        received.append(("events", job_id, limit))
        return {"items": [], "total": 0}

    def record_cancel(job_id: str, *, actor_id: str) -> dict[str, object]:
        received.append(("cancel", job_id, actor_id))
        return _job_row()

    def record_retry(job_id: str, *, actor_id: str) -> dict[str, object]:
        received.append(("retry", job_id, actor_id))
        return _job_row()

    monkeypatch.setattr(admin_textbooks, "get_ingestion_job", record_get)
    monkeypatch.setattr(admin_textbooks, "list_ingestion_job_events", record_events)
    monkeypatch.setattr(admin_textbooks, "request_cancellation", record_cancel)
    monkeypatch.setattr(admin_textbooks, "retry_job", record_retry)

    base = f"/api/admin/textbooks/jobs/{_JOB_ID}"
    assert client.get(base).status_code == 200
    assert client.get(f"{base}/events?limit=17").status_code == 200
    assert client.post(f"{base}/cancel").status_code == 200
    assert client.post(f"{base}/retry").status_code == 200

    assert received == [
        ("get", str(_JOB_ID), None),
        ("events", str(_JOB_ID), 17),
        ("cancel", str(_JOB_ID), _teacher().id),
        ("retry", str(_JOB_ID), _teacher().id),
    ]
