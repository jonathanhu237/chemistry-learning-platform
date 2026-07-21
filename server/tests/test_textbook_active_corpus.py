from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from zipfile import ZipFile

import server.app.domains.textbook_rag.retrieval as retrieval_module
from server.app.domains.textbook_rag.active_corpus import (
    ActiveTextbookCorpus,
    ActiveTextbookDocument,
    active_textbook_filter,
    load_active_textbook_corpus,
)
from server.app.domains.textbook_rag.cache import textbook_evidence_cache_fingerprints
from server.app.domains.textbook_rag.evidence import textbook_evidence_fingerprints
from server.app.domains.textbook_rag.retrieval import (
    _lexical_payload,
    _vector_payload,
    retrieve_textbook_evidence,
)


def _online(document_id: str = "tbk-online") -> ActiveTextbookDocument:
    return ActiveTextbookDocument(
        document_id=document_id,
        logical_textbook_key="inorganic-lower",
        document_version=2,
        document_kind="textbook",
        source_collection="inorganic-lower",
        index_document_id=document_id,
        projection_run_id="run-online-2",
    )


def _legacy() -> ActiveTextbookDocument:
    return ActiveTextbookDocument(
        document_id="seed-inorganic-lower",
        logical_textbook_key="textbook_inorganic_lower_v1",
        document_version=1,
        document_kind="canonical_textbook",
        source_collection="textbook_inorganic_lower_v1",
        index_document_id="inorganic_chemistry_lower_2nd",
    )


def _settings(corpus: ActiveTextbookCorpus) -> dict[str, Any]:
    return {
        "enabled": True,
        "elasticsearch_url": "http://elasticsearch.example",
        "index_name": "textbooks",
        "embedding": {"base_url": "http://embedding.example", "api_key": "secret", "model": "embed"},
        "rerank": {"base_url": "http://rerank.example", "api_key": "secret", "model": "rerank"},
        "embedding_dimension": 2,
        "keyword_top_k": 2,
        "vector_top_k": 2,
        "rerank_top_k": 2,
        "final_top_k": 1,
        "timeout_seconds": 1,
        "_active_textbook_corpus": corpus,
    }


def test_active_filter_distinguishes_online_generation_from_legacy_seed() -> None:
    filter_query = active_textbook_filter([_online(), _legacy()])

    assert filter_query == {
        "bool": {
            "should": [
                {
                    "bool": {
                        "filter": [
                            {"term": {"doc_id": "tbk-online"}},
                            {"term": {"document_version": 2}},
                            {"term": {"projection_run_id": "run-online-2"}},
                        ]
                    }
                },
                {
                    "bool": {
                        "filter": [
                            {"term": {"doc_id": "inorganic_chemistry_lower_2nd"}}
                        ]
                    }
                },
            ],
            "minimum_should_match": 1,
        }
    }
    assert active_textbook_filter([]) == {"match_none": {}}


def test_legacy_seed_without_registered_index_identity_fails_closed() -> None:
    legacy = _legacy()
    unregistered = ActiveTextbookDocument(
        document_id=legacy.document_id,
        logical_textbook_key=legacy.logical_textbook_key,
        document_version=legacy.document_version,
        document_kind=legacy.document_kind,
        source_collection=legacy.source_collection,
    )

    assert active_textbook_filter([unregistered]) == {"match_none": {}}


def test_committed_legacy_seed_bundle_is_activated_by_registered_doc_id() -> None:
    bundle = Path(
        "data/seed/textbook_rag_precomputed/"
        "canonical-rag-chunks-qwen-v1.documents.jsonl.zip"
    )
    with ZipFile(bundle) as archive:
        with archive.open(archive.namelist()[0]) as handle:
            source = json.loads(handle.readline())["_source"]

    assert source["doc_id"] == _legacy().index_document_id
    assert "document_version" not in source
    clause = active_textbook_filter([_legacy()])["bool"]["should"][0]
    assert clause["bool"]["filter"] == [
        {"term": {"doc_id": "inorganic_chemistry_lower_2nd"}}
    ]


def test_lexical_and_vector_recall_share_the_same_active_filter() -> None:
    active_filter = active_textbook_filter([_online()])

    lexical = _lexical_payload(
        "氯气氧化溴离子",
        size=4,
        point_context={},
        active_filter=active_filter,
    )
    vector = _vector_payload([0.1, 0.2], size=4, active_filter=active_filter)

    assert lexical["query"]["bool"]["filter"] == [active_filter]
    assert vector["query"]["script_score"]["query"]["bool"]["filter"] == [active_filter]


def test_active_corpus_loader_uses_published_documents_as_authority() -> None:
    statements: list[str] = []

    class Result:
        def __init__(self, rows: list[dict[str, Any]]) -> None:
            self.rows = rows

        def mappings(self) -> "Result":
            return self

        def all(self) -> list[dict[str, Any]]:
            return self.rows

        def first(self) -> dict[str, Any] | None:
            return self.rows[0] if self.rows else None

    class Session:
        def execute(self, statement: Any) -> Result:
            sql = str(statement)
            statements.append(sql)
            if "LEFT JOIN source_documents" in sql:
                return Result(
                    [
                        {
                            "id": "tbk-online",
                            "logical_textbook_key": "inorganic-lower",
                            "version_number": 2,
                            "document_kind": "textbook",
                            "active_projection_run_id": "run-online-2",
                            "revision": 9,
                            "metadata": {
                                "source_collection": "inorganic-lower",
                                "index_document_id": "ignored-for-online",
                            },
                        }
                    ]
                )
            return Result([])

    corpus = load_active_textbook_corpus(Session())

    assert [document.document_id for document in corpus.documents] == ["tbk-online"]
    assert corpus.documents[0].index_document_id == "tbk-online"
    assert corpus.documents[0].projection_run_id == "run-online-2"
    assert corpus.revision == 9
    assert "sd.publication_status = 'published'" in statements[0]
    assert len(statements) == 1


def test_retrieval_filters_both_paths_and_returns_document_traceability(monkeypatch: Any) -> None:
    payloads: list[dict[str, Any]] = []

    class EmbeddingClient:
        def __init__(self, **_: Any) -> None:
            pass

        def embed(self, texts: list[str]) -> list[list[float]]:
            return [[0.1, 0.2] for _ in texts]

    class RerankClient:
        def __init__(self, **_: Any) -> None:
            pass

        def rerank(self, *, query: str, documents: list[str]) -> list[float]:
            return [0.9 for _ in documents]

    class Elasticsearch:
        def __init__(self, **_: Any) -> None:
            self.index = "textbooks"

        def request(self, method: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
            payloads.append(payload)
            return {
                "hits": {
                    "hits": [
                        {
                            "_id": "chunk-online",
                            "_score": 1.0,
                            "_source": {
                                "chunk_id": "chunk-online",
                                "text": "Cl2 oxidizes Br-.",
                                "book_title": "无机化学（下册）",
                                "document_id": "tbk-online",
                                "logical_textbook_key": "inorganic-lower",
                                "document_version": 2,
                                "source_collection": "inorganic-lower",
                                "source_file": "online:tbk-online",
                            },
                        }
                    ]
                }
            }

    monkeypatch.setattr(retrieval_module, "OpenAICompatibleEmbeddingClient", EmbeddingClient)
    monkeypatch.setattr(retrieval_module, "OpenAICompatibleRerankClient", RerankClient)
    monkeypatch.setattr(retrieval_module, "TextbookElasticsearchClient", Elasticsearch)
    corpus = ActiveTextbookCorpus(documents=(_online(),), revision=12)

    package = retrieve_textbook_evidence(
        point_context={"point_title": "卤素", "content": {"principle_text": "Cl2氧化Br-。"}},
        settings=_settings(corpus),
    )

    active_filter = {
        "bool": {
            "should": [
                {
                    "bool": {
                        "filter": [
                            {"term": {"doc_id": "tbk-online"}},
                            {"term": {"document_version": 2}},
                            {"term": {"projection_run_id": "run-online-2"}},
                        ]
                    }
                }
            ],
            "minimum_should_match": 1,
        }
    }
    assert payloads[0]["query"]["bool"]["filter"] == [active_filter]
    assert payloads[1]["query"]["script_score"]["query"]["bool"]["filter"] == [active_filter]
    assert package["diagnostics"]["corpus_revision"] == 12
    assert package["source_refs"][0]["document_id"] == "tbk-online"
    assert package["source_refs"][0]["logical_textbook_key"] == "inorganic-lower"
    assert package["source_refs"][0]["document_version"] == 2


def test_cache_and_evidence_fingerprints_change_with_corpus_revision() -> None:
    base_settings = _settings(ActiveTextbookCorpus())
    point_context = {"point_title": "卤素", "content": {"principle_text": "Cl2氧化Br-。"}}
    catalog_context = {"node_id": "point-1", "canonical_point_id": "canonical-1"}

    cache_v1 = textbook_evidence_cache_fingerprints(
        point_context=point_context,
        settings={**base_settings, "corpus_revision": 1},
        point_node_id="point-1",
    )
    cache_v2 = textbook_evidence_cache_fingerprints(
        point_context=point_context,
        settings={**base_settings, "corpus_revision": 2},
        point_node_id="point-1",
    )
    evidence_v1 = textbook_evidence_fingerprints(
        catalog_context=catalog_context,
        point_context=point_context,
        settings={**base_settings, "corpus_revision": 1},
    )
    evidence_v2 = textbook_evidence_fingerprints(
        catalog_context=catalog_context,
        point_context=point_context,
        settings={**base_settings, "corpus_revision": 2},
    )

    assert cache_v1["config_fingerprint"] != cache_v2["config_fingerprint"]
    assert evidence_v1["config_fingerprint"] != evidence_v2["config_fingerprint"]


def test_cache_fingerprint_changes_with_active_projection_generation() -> None:
    point_context = {"point_title": "卤素", "content": {"principle_text": "Cl2氧化Br-。"}}
    first = _online()
    second = ActiveTextbookDocument(
        **{**first.__dict__, "projection_run_id": "run-online-3"}
    )

    fingerprint_v2 = textbook_evidence_cache_fingerprints(
        point_context=point_context,
        settings=_settings(ActiveTextbookCorpus(documents=(first,), revision=12)),
        point_node_id="point-1",
    )
    fingerprint_v3 = textbook_evidence_cache_fingerprints(
        point_context=point_context,
        settings=_settings(ActiveTextbookCorpus(documents=(second,), revision=12)),
        point_node_id="point-1",
    )

    assert fingerprint_v2["config_fingerprint"] != fingerprint_v3["config_fingerprint"]
