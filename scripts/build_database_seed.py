from __future__ import annotations

from collections import defaultdict
from typing import Any

from common import PROCESSED_DIR, SEED_DIR, dump_json, ensure_dirs, load_json, now_iso, tokenize_for_match


def formal_experiment_ids() -> set[str]:
    seed = load_json(SEED_DIR / "formal_experiments.json", {})
    if not isinstance(seed, dict):
        return set()
    return {str(item.get("id")) for item in seed.get("experiments") or [] if item.get("id")}


def keep_current_experiment_ids(items: list[str], formal_ids: set[str]) -> list[str]:
    return [item for item in items if item in formal_ids]


def clean_source_chunks(chunks: list[dict[str, Any]], formal_ids: set[str]) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    for chunk in chunks:
        item = dict(chunk)
        item["related_experiment_ids"] = keep_current_experiment_ids(
            list(item.get("related_experiment_ids") or []),
            formal_ids,
        )
        cleaned.append(item)
    return cleaned


def clean_questions(questions: list[dict[str, Any]], formal_ids: set[str]) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    for question in questions:
        item = dict(question)
        item["related_experiment_ids"] = keep_current_experiment_ids(
            list(item.get("related_experiment_ids") or []),
            formal_ids,
        )
        cleaned.append(item)
    return cleaned


def clean_links(links: list[dict[str, Any]], formal_ids: set[str]) -> list[dict[str, Any]]:
    cleaned: list[dict[str, Any]] = []
    for link in links:
        from_is_experiment = link.get("from_type") == "experiment"
        to_is_experiment = link.get("to_type") == "experiment"
        if from_is_experiment and link.get("from_id") not in formal_ids:
            continue
        if to_is_experiment and link.get("to_id") not in formal_ids:
            continue
        cleaned.append(link)
    return cleaned


def build_keyword_index(chunks: list[dict[str, Any]]) -> dict[str, list[str]]:
    index: dict[str, list[str]] = defaultdict(list)
    for chunk in chunks:
        for token in tokenize_for_match(chunk.get("text", "")):
            if chunk["id"] not in index[token]:
                index[token].append(chunk["id"])
    return dict(index)


def main() -> None:
    ensure_dirs()
    formal_ids = formal_experiment_ids()
    tables = {
        "source_documents": load_json(PROCESSED_DIR / "source_documents.json", []),
        "chapters": load_json(PROCESSED_DIR / "chapters.json", []),
        "knowledge_units": load_json(PROCESSED_DIR / "knowledge_units.json", []),
        "knowledge_points": load_json(PROCESSED_DIR / "knowledge_points.json", []),
        "source_chunks": clean_source_chunks(load_json(PROCESSED_DIR / "source_chunks.json", []), formal_ids),
        "experiments": [],
        "experiment_learning_cards": [],
        "questions": clean_questions(load_json(PROCESSED_DIR / "questions.json", []), formal_ids),
        "links": clean_links(load_json(PROCESSED_DIR / "links.json", []), formal_ids),
    }
    resources = [
        {
            "id": f"RES_{doc['document_id']}",
            "document_id": doc["document_id"],
            "title": doc["file_name"],
            "resource_type": doc["document_kind"],
            "path": doc["path"],
            "review_required": doc["document_kind"] in {"experiment_material", "learning_flow"},
            "created_at": now_iso(),
        }
        for doc in tables["source_documents"]
    ]
    tables["resources"] = resources
    dump_json(PROCESSED_DIR / "resources.json", resources)
    dump_json(SEED_DIR / "database_seed.json", tables)

    chunks = tables["source_chunks"]
    keyword_index = build_keyword_index(chunks)
    dump_json(PROCESSED_DIR / "rag_keyword_index.json", keyword_index)
    manifest = {
        "created_at": now_iso(),
        "chunk_count": len(chunks),
        "keyword_terms": len(keyword_index),
        "vector_enabled": False,
        "embedding": {
            "enabled": False,
            "reason": "No embedding API or local model is configured by default.",
            "dimension_config_env": "EMBEDDING_DIMENSION",
        },
        "retrieval_strategy": [
            "metadata filter: chapter_id, experiment_id, knowledge_point_ids",
            "keyword/BM25-style fallback over source_chunks",
            "full corpus fallback only when scoped retrieval has no result",
        ],
        "files": {
            "chunks": "data/processed/source_chunks.json",
            "keyword_index": "data/processed/rag_keyword_index.json",
        },
    }
    dump_json(PROCESSED_DIR / "rag_index_manifest.json", manifest)
    print("built database seed and RAG keyword index")


if __name__ == "__main__":
    main()
