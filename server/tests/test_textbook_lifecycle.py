from __future__ import annotations

from server.app.domains.textbook_ingestion.lifecycle import publication_blockers
from server.app.domains.textbook_ingestion.views import public_document


def _online_document(status: str = "review_ready") -> dict[str, object]:
    return {
        "id": "tbk_1",
        "document_kind": "textbook",
        "publication_status": status,
    }


def _verified_job(status: str = "review_ready") -> dict[str, object]:
    return {
        "id": "job-1",
        "status": status,
        "total_chunks": 2,
        "embedded_chunks": 2,
        "indexed_chunks": 2,
        "quality_report": {"publishable": True, "blocking_issues": []},
        "outputs": {"index_verified": True, "indexed_chunks": 2},
    }


def test_publication_gate_requires_quality_embedding_and_index_count_consistency() -> None:
    assert publication_blockers(_online_document(), _verified_job(), chunk_count=2) == []

    job = _verified_job()
    job["quality_report"] = {"publishable": False, "blocking_issues": ["empty_pages"]}
    job["indexed_chunks"] = 1
    job["outputs"] = {"index_verified": False, "indexed_chunks": 1}

    blockers = publication_blockers(_online_document(), job, chunk_count=2)

    assert "empty_pages" in blockers
    assert "quality_not_publishable" in blockers
    assert "index_not_verified" in blockers
    assert "index_count_mismatch" in blockers


def test_inactive_verified_online_version_and_seed_are_rollback_candidates() -> None:
    assert publication_blockers(
        _online_document("inactive"),
        _verified_job("ready"),
        chunk_count=2,
    ) == []
    assert publication_blockers(
        {"document_kind": "canonical_textbook", "publication_status": "inactive"},
        None,
        chunk_count=10,
    ) == []


def test_public_document_only_advertises_safe_lifecycle_actions() -> None:
    review_ready = public_document(
        {
            **_online_document(),
            "logical_textbook_key": "chemistry",
            "version_number": 2,
            "title": "Chemistry",
            "file_name": "chemistry.pdf",
            "latest_job": _verified_job(),
        }
    )
    assert review_ready["can_publish"] is True
    assert "publish" in review_ready["allowed_actions"]
    assert "delete" in review_ready["allowed_actions"]

    processing = public_document(
        {
            **_online_document("processing"),
            "logical_textbook_key": "chemistry",
            "version_number": 2,
            "title": "Chemistry",
            "file_name": "chemistry.pdf",
            "latest_job": {**_verified_job("embedding"), "allowed_actions": ["cancel"]},
        }
    )
    assert "cancel" in processing["allowed_actions"]
    assert "delete" not in processing["allowed_actions"]

    rollback = public_document(
        {
            "id": "canonical-1",
            "document_kind": "canonical_textbook",
            "publication_status": "inactive",
            "logical_textbook_key": "chemistry",
            "version_number": 1,
            "title": "Chemistry seed",
            "file_name": "seed.jsonl",
            "latest_job": None,
        }
    )
    assert {"publish", "rollback"}.issubset(rollback["allowed_actions"])
    assert "delete" not in rollback["allowed_actions"]
