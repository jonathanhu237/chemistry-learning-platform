from __future__ import annotations

from typing import Any

from server.app.domains.textbook_ingestion.contracts import IngestionStage


def _job_actions(status: str) -> list[str]:
    actions: list[str] = []
    if status in {
        IngestionStage.UPLOADED.value,
        IngestionStage.EXTRACTING.value,
        IngestionStage.AWAITING_OCR.value,
        IngestionStage.OCR.value,
        IngestionStage.STRUCTURING.value,
        IngestionStage.CHUNKING.value,
        IngestionStage.EMBEDDING.value,
        IngestionStage.INDEXING.value,
        IngestionStage.REVIEW_READY.value,
        IngestionStage.FAILED.value,
    }:
        actions.append("cancel")
    if status in {
        IngestionStage.FAILED.value,
        IngestionStage.CANCELLED.value,
        IngestionStage.AWAITING_OCR.value,
        IngestionStage.REVIEW_READY.value,
    }:
        actions.append("retry")
    return actions


def public_job(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    config = row.get("config_snapshot") if isinstance(row.get("config_snapshot"), dict) else {}
    ocr = config.get("ocr") if isinstance(config.get("ocr"), dict) else {}
    return {
        "id": str(row.get("id") or ""),
        "document_id": str(row.get("document_id") or ""),
        "status": str(row.get("status") or IngestionStage.UPLOADED.value),
        "progress": int(row.get("progress") or 0),
        "attempts": int(row.get("attempts") or 0),
        "max_attempts": int(row.get("max_attempts") or 1),
        "total_pages": int(row.get("total_pages") or 0),
        "processed_pages": int(row.get("processed_pages") or 0),
        "ocr_pages": int(row.get("ocr_pages") or 0),
        "total_chunks": int(row.get("total_chunks") or 0),
        "embedded_chunks": int(row.get("embedded_chunks") or 0),
        "indexed_chunks": int(row.get("indexed_chunks") or 0),
        "error_code": row.get("error_code"),
        "error_message": row.get("error_message"),
        "stage_metrics": dict(row.get("stage_metrics") or {}),
        "quality_report": dict(row.get("quality_report") or {}),
        "outputs": dict(row.get("outputs") or {}),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
        "started_at": row.get("started_at"),
        "finished_at": row.get("finished_at"),
        "allowed_actions": _job_actions(str(row.get("status") or "")),
        "ocr": {
            "provider": ocr.get("provider"),
            "model": ocr.get("model"),
            "enabled": bool(ocr.get("enabled")),
            "credential_configured": bool(ocr.get("credential_configured")),
            "credential_fingerprint": ocr.get("credential_fingerprint"),
        },
    }


def public_document(row: dict[str, Any]) -> dict[str, Any]:
    latest_job = public_job(row.get("latest_job") if isinstance(row.get("latest_job"), dict) else None)
    publication_status = str(row.get("publication_status") or "draft")
    job_status = str((latest_job or {}).get("status") or "")
    quality_report = (latest_job or {}).get("quality_report") or {}
    outputs = (latest_job or {}).get("outputs") or {}
    document_kind = str(row.get("document_kind") or "")
    is_seed = document_kind == "canonical_textbook"
    blockers = [str(item) for item in quality_report.get("blocking_issues") or []]
    rollback_candidate = publication_status == "inactive"
    expected_job_statuses = (
        {IngestionStage.READY.value, IngestionStage.REVIEW_READY.value}
        if rollback_candidate
        else {IngestionStage.REVIEW_READY.value}
    )
    if not (rollback_candidate and is_seed):
        if job_status not in expected_job_statuses:
            blockers.append("ingestion_not_review_ready")
        if not bool(quality_report.get("publishable")):
            blockers.append("quality_not_publishable")
        if not bool(outputs.get("index_verified")):
            blockers.append("index_not_verified")
        total_chunks = int((latest_job or {}).get("total_chunks") or 0)
        if (
            total_chunks <= 0
            or int((latest_job or {}).get("embedded_chunks") or 0) != total_chunks
            or int((latest_job or {}).get("indexed_chunks") or 0) != total_chunks
            or int(outputs.get("indexed_chunks") or 0) != total_chunks
        ):
            blockers.append("index_count_mismatch")
    blockers = list(dict.fromkeys(blockers))
    can_publish = publication_status in {"review_ready", "inactive"} and not blockers
    actions = list((latest_job or {}).get("allowed_actions") or [])
    if can_publish:
        actions.append("publish")
        if rollback_candidate:
            actions.append("rollback")
    if publication_status == "published":
        actions.append("deactivate")
    active_job_statuses = {
        IngestionStage.UPLOADED.value,
        IngestionStage.EXTRACTING.value,
        IngestionStage.AWAITING_OCR.value,
        IngestionStage.OCR.value,
        IngestionStage.STRUCTURING.value,
        IngestionStage.CHUNKING.value,
        IngestionStage.EMBEDDING.value,
        IngestionStage.INDEXING.value,
    }
    if (
        not is_seed
        and publication_status not in {"published", "deleted"}
        and job_status not in active_job_statuses
    ):
        actions.append("delete")
    return {
        "id": str(row.get("id") or ""),
        "logical_textbook_key": str(row.get("logical_textbook_key") or row.get("id") or ""),
        "version_number": int(row.get("version_number") or 1),
        "version_label": row.get("version_label"),
        "title": str(row.get("title") or row.get("file_name") or ""),
        "file_name": str(row.get("file_name") or ""),
        "size_bytes": row.get("size_bytes"),
        "checksum_sha256": row.get("checksum_sha256"),
        "publication_status": publication_status,
        "quality_summary": dict(row.get("quality_summary") or {}),
        "metadata": dict(row.get("metadata") or {}),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
        "published_at": row.get("published_at"),
        "deactivated_at": row.get("deactivated_at"),
        "deleted_at": row.get("deleted_at"),
        "corpus_revision": row.get("corpus_revision"),
        "latest_job": latest_job,
        "allowed_actions": list(dict.fromkeys(actions)),
        "can_publish": can_publish,
        "publish_blockers": blockers,
        "ocr": dict((latest_job or {}).get("ocr") or {}),
    }


def public_page(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "document_id": str(row.get("document_id") or ""),
        "page_number": int(row.get("page_number") or 0),
        "extraction_method": row.get("extraction_method"),
        "text": str(row.get("text") or ""),
        "markdown": str(row.get("markdown") or ""),
        "blocks": list(row.get("blocks") or []),
        "content_hash": row.get("content_hash"),
        "quality_score": float(row.get("quality_score") or 0),
        "quality_flags": list(row.get("quality_flags") or []),
        "needs_ocr": bool(row.get("needs_ocr")),
        "ocr_provider": row.get("ocr_provider"),
        "ocr_model": row.get("ocr_model"),
        "diagnostics": dict(row.get("diagnostics") or {}),
        "updated_at": row.get("updated_at"),
    }


def public_chunk(row: dict[str, Any]) -> dict[str, Any]:
    allowed = {
        "id",
        "document_id",
        "document_version",
        "chunk_index",
        "text",
        "markdown",
        "page_start",
        "page_end",
        "section_title",
        "section_path",
        "content_type",
        "content_hash",
        "parent_chunk_id",
        "previous_chunk_id",
        "next_chunk_id",
        "extraction_method",
        "quality_flags",
        "review_required",
        "content_status",
        "metadata",
        "updated_at",
    }
    return {key: value for key, value in row.items() if key in allowed}
