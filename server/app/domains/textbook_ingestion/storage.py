from __future__ import annotations

import hashlib
import math
import os
import secrets
from pathlib import Path
from typing import BinaryIO

import pymupdf

from server.app.domains.textbook_ingestion.ports import StoredTextbookBlob


PDF_MAGIC = b"%PDF-"
ALLOWED_PDF_CONTENT_TYPES = frozenset(
    {
        "application/pdf",
        "application/octet-stream",
        "binary/octet-stream",
        "",
    }
)


class TextbookStorageError(ValueError):
    def __init__(self, reason: str, message: str, **details: object) -> None:
        super().__init__(message)
        self.reason = reason
        self.message = message
        self.details = details

    def detail(self) -> dict[str, object]:
        return {"reason": self.reason, "message": self.message, **self.details}


class LocalTextbookBlobStore:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()

    def _contained(self, path: Path) -> Path:
        resolved = path.resolve()
        if resolved != self.root and self.root not in resolved.parents:
            raise TextbookStorageError("invalid_storage_path", "Textbook path escapes the storage root")
        return resolved

    def resolve(self, relative_path: str) -> Path:
        if not relative_path or Path(relative_path).is_absolute():
            raise TextbookStorageError("invalid_storage_path", "Textbook path must be relative")
        return self._contained(self.root / relative_path)

    def store_pdf(
        self,
        *,
        document_id: str,
        filename: str,
        stream: BinaryIO,
        content_type: str | None,
        max_bytes: int,
        max_pages: int,
        render_dpi: int,
        max_render_pixels: int,
    ) -> StoredTextbookBlob:
        if Path(filename).suffix.lower() != ".pdf":
            raise TextbookStorageError("unsupported_file_extension", "Only PDF textbooks are supported")
        normalized_content_type = (content_type or "").split(";", 1)[0].strip().lower()
        if normalized_content_type not in ALLOWED_PDF_CONTENT_TYPES:
            raise TextbookStorageError(
                "unsupported_mime_type",
                "The uploaded file is not declared as a PDF",
                content_type=normalized_content_type,
            )
        if max_bytes <= 0:
            raise ValueError("max_bytes must be positive")
        if max_pages <= 0 or render_dpi <= 0 or max_render_pixels <= 0:
            raise ValueError("PDF structural limits must be positive")

        self.root.mkdir(parents=True, exist_ok=True)
        os.chmod(self.root, 0o700)
        staging_dir = self._contained(self.root / ".staging")
        staging_dir.mkdir(parents=True, exist_ok=True)
        os.chmod(staging_dir, 0o700)
        temporary_path = self._contained(staging_dir / f"{secrets.token_hex(16)}.part")
        published_path: Path | None = None
        digest = hashlib.sha256()
        size_bytes = 0
        prefix = bytearray()
        try:
            descriptor = os.open(
                temporary_path,
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0),
                0o600,
            )
            with os.fdopen(descriptor, "wb") as output:
                while True:
                    chunk = stream.read(1024 * 1024)
                    if not chunk:
                        break
                    if not isinstance(chunk, bytes):
                        raise TextbookStorageError("invalid_upload_stream", "Upload stream must produce bytes")
                    if len(prefix) < len(PDF_MAGIC):
                        prefix.extend(chunk[: len(PDF_MAGIC) - len(prefix)])
                    size_bytes += len(chunk)
                    if size_bytes > max_bytes:
                        raise TextbookStorageError(
                            "file_too_large",
                            "The textbook PDF exceeds the configured upload limit",
                            max_bytes=max_bytes,
                            size_bytes=size_bytes,
                        )
                    digest.update(chunk)
                    output.write(chunk)
                output.flush()
                os.fsync(output.fileno())

            if size_bytes == 0:
                raise TextbookStorageError("empty_file", "The uploaded PDF is empty")
            if bytes(prefix) != PDF_MAGIC:
                raise TextbookStorageError("invalid_pdf_signature", "The uploaded file does not have a PDF signature")
            self._validate_pdf_structure(
                temporary_path,
                max_pages=max_pages,
                render_dpi=render_dpi,
                max_render_pixels=max_render_pixels,
            )

            relative_path = Path("originals") / document_id / "source.pdf"
            destination = self.resolve(relative_path.as_posix())
            originals_dir = self._contained(self.root / "originals")
            originals_dir.mkdir(parents=True, exist_ok=True)
            os.chmod(originals_dir, 0o700)
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.chmod(destination.parent, 0o700)
            try:
                # Hard-link publication is an atomic no-clobber operation on
                # the same textbook filesystem; unlike exists()+replace it
                # cannot overwrite a concurrently-created destination.
                os.link(temporary_path, destination)
            except FileExistsError as exc:
                raise TextbookStorageError(
                    "document_blob_exists",
                    "A source PDF already exists for this document",
                ) from exc
            published_path = destination
            temporary_path.unlink()
            os.chmod(destination, 0o600)
            directory_fd = os.open(destination.parent, os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
            return StoredTextbookBlob(
                relative_path=relative_path.as_posix(),
                absolute_path=destination,
                checksum_sha256=digest.hexdigest(),
                size_bytes=size_bytes,
                mime_type="application/pdf",
            )
        except Exception:
            temporary_path.unlink(missing_ok=True)
            if published_path is not None:
                published_path.unlink(missing_ok=True)
            raise

    @staticmethod
    def _validate_pdf_structure(
        path: Path,
        *,
        max_pages: int,
        render_dpi: int,
        max_render_pixels: int,
    ) -> None:
        document: pymupdf.Document | None = None
        try:
            document = pymupdf.open(path)
            if document.needs_pass:
                raise TextbookStorageError("encrypted_pdf", "Password-protected textbook PDFs are not supported")
            if document.page_count <= 0:
                raise TextbookStorageError("pdf_has_no_pages", "The uploaded textbook PDF has no pages")
            if document.page_count > max_pages:
                raise TextbookStorageError(
                    "page_limit_exceeded",
                    "The textbook PDF exceeds the configured page limit",
                    page_count=document.page_count,
                    max_pages=max_pages,
                )
            scale = render_dpi / 72.0
            for page_index in range(document.page_count):
                rectangle = document.load_page(page_index).rect
                width = float(rectangle.width)
                height = float(rectangle.height)
                if not math.isfinite(width) or not math.isfinite(height) or width <= 0 or height <= 0:
                    raise TextbookStorageError(
                        "invalid_page_geometry",
                        "A textbook PDF page has invalid geometry",
                        page_number=page_index + 1,
                    )
                pixel_count = math.ceil(width * scale) * math.ceil(height * scale)
                if pixel_count > max_render_pixels:
                    raise TextbookStorageError(
                        "page_render_limit_exceeded",
                        "A textbook PDF page would exceed the configured OCR render limit",
                        page_number=page_index + 1,
                        pixel_count=pixel_count,
                        max_render_pixels=max_render_pixels,
                    )
        except TextbookStorageError:
            raise
        except Exception as exc:
            raise TextbookStorageError(
                "invalid_pdf",
                "The uploaded textbook PDF could not be parsed safely",
                error_type=exc.__class__.__name__,
            ) from exc
        finally:
            if document is not None:
                document.close()

    def delete(self, relative_path: str) -> None:
        path = self.resolve(relative_path)
        path.unlink(missing_ok=True)
