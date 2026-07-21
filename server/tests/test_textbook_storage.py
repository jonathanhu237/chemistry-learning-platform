from __future__ import annotations

from io import BytesIO
import os

import pymupdf
import pytest

from server.app.domains.textbook_ingestion.storage import LocalTextbookBlobStore, TextbookStorageError


def _pdf_bytes(*, width: float = 595, height: float = 842) -> bytes:
    document = pymupdf.open()
    document.new_page(width=width, height=height)
    try:
        return document.tobytes()
    finally:
        document.close()


def _limits() -> dict[str, int]:
    return {"max_pages": 10, "render_dpi": 160, "max_render_pixels": 40_000_000}


def test_textbook_blob_store_streams_pdf_and_returns_relative_metadata(tmp_path) -> None:
    store = LocalTextbookBlobStore(tmp_path / "textbooks")
    content = _pdf_bytes()

    stored = store.store_pdf(
        document_id="tbk-test",
        filename="textbook.pdf",
        stream=BytesIO(content),
        content_type="application/pdf",
        max_bytes=1024,
        **_limits(),
    )

    assert stored.relative_path == "originals/tbk-test/source.pdf"
    assert stored.absolute_path.read_bytes() == content
    assert stored.size_bytes == len(content)
    assert len(stored.checksum_sha256) == 64
    assert store.resolve(stored.relative_path) == stored.absolute_path
    assert stored.absolute_path.stat().st_mode & 0o777 == 0o600
    assert stored.absolute_path.parent.stat().st_mode & 0o777 == 0o700
    assert (tmp_path / "textbooks" / ".staging").stat().st_mode & 0o777 == 0o700


def test_textbook_blob_store_rejects_invalid_signature_and_cleans_staging(tmp_path) -> None:
    store = LocalTextbookBlobStore(tmp_path / "textbooks")

    with pytest.raises(TextbookStorageError) as exc_info:
        store.store_pdf(
            document_id="tbk-invalid",
            filename="not-really.pdf",
            stream=BytesIO(b"plain text"),
            content_type="application/pdf",
            max_bytes=1024,
            **_limits(),
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
            **_limits(),
        )

    assert exc_info.value.reason == "file_too_large"
    assert not (tmp_path / "textbooks" / "originals" / "tbk-large" / "source.pdf").exists()


def test_textbook_blob_store_rejects_malformed_pdf_after_magic_header(tmp_path) -> None:
    store = LocalTextbookBlobStore(tmp_path / "textbooks")

    with pytest.raises(TextbookStorageError) as exc_info:
        store.store_pdf(
            document_id="tbk-malformed",
            filename="malformed.pdf",
            stream=BytesIO(b"%PDF-1.7\nnot-a-valid-pdf"),
            content_type="application/pdf",
            max_bytes=1024,
            **_limits(),
        )

    assert exc_info.value.reason == "invalid_pdf"


def test_textbook_blob_store_rejects_page_that_would_render_too_many_pixels(tmp_path) -> None:
    store = LocalTextbookBlobStore(tmp_path / "textbooks")

    with pytest.raises(TextbookStorageError) as exc_info:
        store.store_pdf(
            document_id="tbk-giant-page",
            filename="giant.pdf",
            stream=BytesIO(_pdf_bytes(width=2000, height=2000)),
            content_type="application/pdf",
            max_bytes=1024 * 1024,
            max_pages=10,
            render_dpi=160,
            max_render_pixels=1_000_000,
        )

    assert exc_info.value.reason == "page_render_limit_exceeded"


def test_textbook_blob_store_removes_published_blob_when_finalization_fails(tmp_path, monkeypatch) -> None:
    store = LocalTextbookBlobStore(tmp_path / "textbooks")

    def _fail_chmod(_path, _mode) -> None:
        raise OSError("simulated finalization failure")

    monkeypatch.setattr(os, "chmod", _fail_chmod)

    with pytest.raises(OSError, match="simulated finalization failure"):
        store.store_pdf(
            document_id="tbk-finalization-failure",
            filename="textbook.pdf",
            stream=BytesIO(_pdf_bytes()),
            content_type="application/pdf",
            max_bytes=1024,
            **_limits(),
        )

    assert not (tmp_path / "textbooks" / "originals" / "tbk-finalization-failure" / "source.pdf").exists()


def test_textbook_blob_store_never_overwrites_an_existing_document_blob(tmp_path) -> None:
    store = LocalTextbookBlobStore(tmp_path / "textbooks")
    original = _pdf_bytes(width=595, height=842)
    replacement = _pdf_bytes(width=500, height=700)
    stored = store.store_pdf(
        document_id="tbk-existing",
        filename="original.pdf",
        stream=BytesIO(original),
        content_type="application/pdf",
        max_bytes=1024,
        **_limits(),
    )

    with pytest.raises(TextbookStorageError) as exc_info:
        store.store_pdf(
            document_id="tbk-existing",
            filename="replacement.pdf",
            stream=BytesIO(replacement),
            content_type="application/pdf",
            max_bytes=1024,
            **_limits(),
        )

    assert exc_info.value.reason == "document_blob_exists"
    assert stored.absolute_path.read_bytes() == original
    assert not list((tmp_path / "textbooks" / ".staging").glob("*.part"))


def test_textbook_blob_store_rejects_path_escape(tmp_path) -> None:
    store = LocalTextbookBlobStore(tmp_path / "textbooks")

    with pytest.raises(TextbookStorageError, match="relative"):
        store.resolve("/tmp/escaped.pdf")
    with pytest.raises(TextbookStorageError, match="escapes"):
        store.resolve("../escaped.pdf")
