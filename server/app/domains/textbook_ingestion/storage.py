from __future__ import annotations

import hashlib
import os
import secrets
from pathlib import Path
from typing import BinaryIO

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

        self.root.mkdir(parents=True, exist_ok=True)
        staging_dir = self._contained(self.root / ".staging")
        staging_dir.mkdir(parents=True, exist_ok=True)
        temporary_path = self._contained(staging_dir / f"{secrets.token_hex(16)}.part")
        digest = hashlib.sha256()
        size_bytes = 0
        prefix = bytearray()
        try:
            with temporary_path.open("xb") as output:
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

            relative_path = Path("originals") / document_id / "source.pdf"
            destination = self.resolve(relative_path.as_posix())
            destination.parent.mkdir(parents=True, exist_ok=True)
            if destination.exists():
                raise TextbookStorageError("document_blob_exists", "A source PDF already exists for this document")
            os.replace(temporary_path, destination)
            return StoredTextbookBlob(
                relative_path=relative_path.as_posix(),
                absolute_path=destination,
                checksum_sha256=digest.hexdigest(),
                size_bytes=size_bytes,
                mime_type="application/pdf",
            )
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise

    def delete(self, relative_path: str) -> None:
        path = self.resolve(relative_path)
        path.unlink(missing_ok=True)
