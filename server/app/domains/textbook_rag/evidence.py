from __future__ import annotations

import hashlib
import json
from typing import Any

from server.app.domains.textbook_rag.retrieval import retrieve_textbook_evidence


TEXTBOOK_EVIDENCE_SCHEMA_VERSION = 2
TEXTBOOK_EVIDENCE_SECTIONS = ("principle", "phenomenon", "safety")
TEXTBOOK_SECTION_CONTENT_KEYS = {
    "principle": "principle_text",
    "phenomenon": "phenomenon_explanation",
    "safety": "safety_note",
}
DEFAULT_SELECTED_PER_SECTION = 3
DEFAULT_CANDIDATE_PER_SECTION = 20


def _stable_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def _sha256(value: Any) -> str:
    return hashlib.sha256(_stable_json(value).encode("utf-8")).hexdigest()


def textbook_point_context_from_catalog(context: dict[str, Any]) -> dict[str, Any]:
    catalog_path = [str(item) for item in context.get("catalog_path") or [] if str(item or "").strip()]
    principle = str(context.get("principle") or "").strip()
    equations = context.get("normalized_equations") if isinstance(context.get("normalized_equations"), list) else []
    equation_text = "\n".join(
        str(row.get("canonical_display") or row.get("raw_text") or "").strip()
        for row in equations
        if isinstance(row, dict) and str(row.get("canonical_display") or row.get("raw_text") or "").strip()
    )
    if equation_text:
        principle = "\n".join(item for item in [principle, equation_text] if item)
    return {
        "point_title": str(context.get("title") or context.get("point_title") or "").strip(),
        "experiment_title": catalog_path[0] if catalog_path else "",
        "textbook_chapter": str(context.get("chapter_id") or ""),
        "folder_path": " / ".join(catalog_path),
        "content": {
            "principle_text": principle,
            "phenomenon_explanation": str(context.get("phenomenon_explanation") or "").strip(),
            "safety_note": str(context.get("safety_note") or "").strip(),
        },
    }


def sanitized_textbook_rag_config(settings: dict[str, Any]) -> dict[str, Any]:
    embedding = settings.get("embedding") if isinstance(settings.get("embedding"), dict) else {}
    rerank = settings.get("rerank") if isinstance(settings.get("rerank"), dict) else {}
    return {
        "schema_version": TEXTBOOK_EVIDENCE_SCHEMA_VERSION,
        "index_name": str(settings.get("index_name") or ""),
        "embedding": {
            "base_url": str(embedding.get("base_url") or ""),
            "model": str(embedding.get("model") or ""),
        },
        "rerank": {
            "base_url": str(rerank.get("base_url") or ""),
            "model": str(rerank.get("model") or ""),
        },
        "embedding_dimension": int(settings.get("embedding_dimension") or 0),
        "keyword_top_k": int(settings.get("keyword_top_k") or 0),
        "vector_top_k": int(settings.get("vector_top_k") or 0),
        "rerank_top_k": int(settings.get("rerank_top_k") or 0),
        "final_top_k": int(settings.get("final_top_k") or 0),
        "selected_per_section": int(settings.get("selected_per_section") or DEFAULT_SELECTED_PER_SECTION),
        "candidate_per_section": int(settings.get("candidate_per_section") or DEFAULT_CANDIDATE_PER_SECTION),
        "min_rerank_score": float(settings.get("min_rerank_score") or 0.0),
        "corpus_revision": max(0, int(settings.get("corpus_revision") or 0)),
    }


def textbook_evidence_fingerprints(
    *,
    catalog_context: dict[str, Any],
    point_context: dict[str, Any],
    settings: dict[str, Any],
) -> dict[str, str]:
    content_fingerprint = _sha256(
        {
            "schema_version": TEXTBOOK_EVIDENCE_SCHEMA_VERSION,
            "node_id": catalog_context.get("node_id"),
            "canonical_point_id": catalog_context.get("canonical_point_id"),
            "point_context": point_context,
        }
    )
    config_fingerprint = _sha256(sanitized_textbook_rag_config(settings))
    return {
        "content_fingerprint": content_fingerprint,
        "config_fingerprint": config_fingerprint,
    }


def retrieve_point_textbook_evidence(
    *,
    catalog_context: dict[str, Any],
    settings: dict[str, Any],
    selected_per_section: int = DEFAULT_SELECTED_PER_SECTION,
    candidate_per_section: int = DEFAULT_CANDIDATE_PER_SECTION,
) -> dict[str, Any]:
    point_context = textbook_point_context_from_catalog(catalog_context)
    retrieval_settings = {
        **settings,
        "rerank_top_k": max(int(settings.get("rerank_top_k") or 0), candidate_per_section),
        "final_top_k": max(int(settings.get("final_top_k") or 0), candidate_per_section),
        "candidate_top_k": candidate_per_section,
        "selected_per_section": selected_per_section,
        "candidate_per_section": candidate_per_section,
    }
    package = retrieve_textbook_evidence(point_context=point_context, settings=retrieval_settings)
    package_diagnostics = package.get("diagnostics") if isinstance(package.get("diagnostics"), dict) else {}
    fingerprint_settings = {
        **retrieval_settings,
        "corpus_revision": max(0, int(package_diagnostics.get("corpus_revision") or 0)),
    }
    fingerprints = textbook_evidence_fingerprints(
        catalog_context=catalog_context,
        point_context=point_context,
        settings=fingerprint_settings,
    )
    selected_refs: list[dict[str, Any]] = []
    candidate_diagnostics: dict[str, list[dict[str, Any]]] = {}
    sections = package.get("sections") if isinstance(package.get("sections"), dict) else {}
    for section in TEXTBOOK_EVIDENCE_SECTIONS:
        section_package = sections.get(section) if isinstance(sections.get(section), dict) else {}
        sources = [source for source in section_package.get("sources") or [] if isinstance(source, dict)]
        for rank, source in enumerate(sources[:selected_per_section], start=1):
            section_path = source.get("section_path") if isinstance(source.get("section_path"), list) else []
            text_value = " ".join(str(source.get("text") or "").split())
            selected_refs.append(
                {
                    "chunk_id": source.get("chunk_id"),
                    "text": text_value,
                    "text_preview": text_value[:260],
                    "book_title": source.get("book_title"),
                    "chapter": source.get("chapter"),
                    "source_file": source.get("source_file") or source.get("book_title") or "教材 RAG",
                    "page_number": source.get("page_start") or source.get("page_end"),
                    "page_start": source.get("page_start"),
                    "page_end": source.get("page_end"),
                    "section": section,
                    "evidence_role": section,
                    "rank": rank,
                    "section_title": " / ".join(str(item) for item in section_path if str(item or "").strip()),
                    "section_path": section_path,
                    "content_type": source.get("content_type"),
                    "content_hash": source.get("content_hash"),
                    "document_id": source.get("document_id"),
                    "logical_textbook_key": source.get("logical_textbook_key"),
                    "document_version": source.get("document_version"),
                    "source_collection": source.get("source_collection"),
                    "recall_source": source.get("recall_source"),
                    "recall_score": source.get("recall_score"),
                    "rerank_score": source.get("rerank_score"),
                    "source_boundary": "qwen_es_textbook_rag",
                    "index_name": settings.get("index_name"),
                    "metadata": source.get("metadata") if isinstance(source.get("metadata"), dict) else {},
                }
            )
        candidates = [
            candidate
            for candidate in section_package.get("candidates") or []
            if isinstance(candidate, dict)
        ][:candidate_per_section]
        candidate_diagnostics[section] = candidates
    supported_sections = sorted({str(ref.get("section")) for ref in selected_refs if ref.get("section")})
    required_sections = [
        section
        for section in TEXTBOOK_EVIDENCE_SECTIONS
        if str(point_context["content"].get(TEXTBOOK_SECTION_CONTENT_KEYS[section]) or "").strip()
    ]
    missing_sections = [section for section in required_sections if section not in supported_sections]
    status = "succeeded" if required_sections and len(supported_sections) >= len(required_sections) else ("partial" if selected_refs else "missing")
    return {
        "ok": bool(selected_refs),
        "status": status,
        "mode": "qwen_es_textbook_rag",
        "point_context": point_context,
        "source_refs": selected_refs,
        "source_count": len(selected_refs),
        "selected_chunk_ids": [str(ref.get("chunk_id")) for ref in selected_refs if ref.get("chunk_id")],
        "supported_sections": supported_sections,
        "missing_sections": missing_sections,
        "candidate_diagnostics": candidate_diagnostics,
        "diagnostics": {
            **(package.get("diagnostics") if isinstance(package.get("diagnostics"), dict) else {}),
            "retrieval_package_ok": bool(package.get("ok")),
            "retrieval_reason_code": package.get("reason_code"),
            "retrieval_message": package.get("message"),
            "selected_per_section": selected_per_section,
            "candidate_per_section": candidate_per_section,
            "candidate_diagnostics": candidate_diagnostics,
            "supported_sections": supported_sections,
            "missing_sections": missing_sections,
            "content_fingerprint": fingerprints["content_fingerprint"],
            "config_fingerprint": fingerprints["config_fingerprint"],
        },
        **fingerprints,
    }
