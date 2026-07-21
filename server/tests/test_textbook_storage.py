from __future__ import annotations

from io import BytesIO

import pytest

from server.app.domains.textbook_ingestion.storage import LocalTextbookBlobStore, TextbookStorageError


def test_textbook_blob_store_streams_pdf_and_returns_relative_metadata(tmp_path) -> None:
    store = LocalTextbookBlobStore(tmp_path / "textbooks")
    content = b"%PDF-1.7\nsynthetic-test-pdf"

    stored = store.store_pdf(
        document_id="tbk-test",
        filename="textbook.pdf",
        stream=BytesIO(content),
        content_type="application/pdf",
        max_bytes=1024,
    )

    assert stored.relative_path == "originals/tbk-test/source.pdf"
    assert stored.absolute_path.read_bytes() == content
    assert stored.size_bytes == len(content)
    assert len(stored.checksum_sha256) == 64
    assert store.resolve(stored.relative_path) == stored.absolute_path


def test_textbook_blob_store_rejects_invalid_signature_and_cleans_staging(tmp_path) -> None:
    store = LocalTextbookBlobStore(tmp_path / "textbooks")

    with pytest.raises(TextbookStorageError) as exc_info:
        store.store_pdf(
            document_id="tbk-invalid",
            filename="not-really.pdf",
            stream=BytesIO(b"plain text"),
            content_type="application/pdf",
            max_bytes=1024,
        )

    assert exc_info.value.reason == "invalid_pdf_signature"
    assert not list((tmp_path / "textbooks" / ".staging").glob("*.part"))


def test_textbook_blob_store_rejects_oversized_stream_before_publish(tmp_path) -> None:
    store = LocalTextbookBlobStore(tmp_path / "textbooks")

    with pytest.raises(TextbookStorageError) as exc_info:
        store.store_pdf(
            document_id="tbk-large",
            filename="large.pdf",
            stream=BytesIO(b"%PDF-" + b"x" * 20),
            content_type="application/pdf",
            max_bytes=10,
        )

    assert exc_info.value.reason == "file_too_large"
    assert not (tmp_path / "textbooks" / "originals" / "tbk-large" / "source.pdf").exists()


def test_textbook_blob_store_rejects_path_escape(tmp_path) -> None:
    store = LocalTextbookBlobStore(tmp_path / "textbooks")

    with pytest.raises(TextbookStorageError, match="relative"):
        store.resolve("/tmp/escaped.pdf")
    with pytest.raises(TextbookStorageError, match="escapes"):
        store.resolve("../escaped.pdf")
