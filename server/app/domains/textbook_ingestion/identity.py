from __future__ import annotations

import hashlib
import re
import unicodedata

from server.app.domains.textbook_ingestion.errors import TextbookIngestionError


CANONICAL_TEXTBOOK_TITLE_KEYS = {
    "inorganic_lower": "textbook_inorganic_lower_v1",
    "inorganic_experiment": "textbook_experiment_clean_v1",
}


def normalized_title(title: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", title).casefold().split())


def canonical_key_for_title(title: str) -> str | None:
    value = normalized_title(title)
    compact = re.sub(r"\s+", "", value)
    if "无机化学实验" in compact:
        return CANONICAL_TEXTBOOK_TITLE_KEYS["inorganic_experiment"]
    if "无机化学" in compact and ("下册" in compact or "下卷" in compact):
        return CANONICAL_TEXTBOOK_TITLE_KEYS["inorganic_lower"]
    return None


def normalize_logical_textbook_key(title: str, requested_key: str | None = None) -> str:
    title_value = normalized_title(title)
    if not title_value:
        raise TextbookIngestionError("title_required", "Textbook title is required", status_code=422)
    if requested_key:
        key = unicodedata.normalize("NFKC", requested_key).strip().lower()
        if not re.fullmatch(r"[a-z0-9][a-z0-9._:-]{2,127}", key):
            raise TextbookIngestionError(
                "invalid_logical_textbook_key",
                "Logical textbook key must contain 3-128 lowercase letters, numbers, '.', '_', ':' or '-'",
                status_code=422,
            )
        return key
    canonical_key = canonical_key_for_title(title_value)
    if canonical_key:
        return canonical_key
    return f"textbook:{hashlib.sha256(title_value.encode('utf-8')).hexdigest()[:24]}"
