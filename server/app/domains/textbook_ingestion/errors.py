from __future__ import annotations

from typing import Any


class TextbookIngestionError(Exception):
    def __init__(self, reason: str, message: str, *, status_code: int = 400, **details: Any) -> None:
        super().__init__(message)
        self.reason = reason
        self.message = message
        self.status_code = status_code
        self.details = details

    def detail(self) -> dict[str, Any]:
        return {"reason": self.reason, "message": self.message, **self.details}


class TextbookJobLeaseLostError(RuntimeError):
    """Raised when a reclaimed job is updated by its former worker."""
