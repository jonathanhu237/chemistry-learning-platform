from __future__ import annotations

from typing import Any


PUBLIC_CHUNK_METADATA_FIELDS = frozenset(
    {
        # Shared source identity and structure.
        "parent_id",
        "doc_id",
        "source_collection",
        "source_role",
        "authority_level",
        "book_title",
        "logical_textbook_key",
        "document_version",
        "page_start",
        "page_end",
        "section_path",
        "chapter",
        "content_type",
        "knowledge_unit",
        "content_hash",
        "quality_flags",
        "prev_chunk_id",
        "next_chunk_id",
        # Canonical textbook chemistry and table annotations.
        "formulas",
        "reactions",
        "compounds",
        "elements",
        "units",
        "table_title",
        "table_columns",
        "row_values",
        "relations",
        "has_reaction",
        "has_table",
        "has_figure",
        "use_for_routing",
        "use_for_question_generation",
        "import_version",
        # Online ingestion traceability that contains no filesystem locations.
        "chunking_strategy",
        "processing_fingerprint",
        "structural_locator",
        "source_block_ids",
        "source_page_numbers",
        "overlap_chars",
        "atomic",
        "exclude_from_question_generation",
    }
)


def public_chunk_metadata(value: Any) -> dict[str, Any]:
    """Return the stable, non-path metadata contract exposed outside storage."""

    if not isinstance(value, dict):
        return {}
    return {
        key: item
        for key, item in value.items()
        if key in PUBLIC_CHUNK_METADATA_FIELDS
    }


def public_source_name(value: Any) -> str:
    """Reduce POSIX or Windows source paths to a display-only file name."""

    normalized = str(value or "").strip().replace("\\", "/").rstrip("/")
    return normalized.rsplit("/", 1)[-1] if normalized else ""
