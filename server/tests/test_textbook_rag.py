from __future__ import annotations

from typing import Any

from server.app.domains.textbook_rag.clients import QwenEmbeddingClient, QwenRerankClient, _extract_rerank_scores
import server.app.domains.textbook_rag.clients as client_module
from server.app.domains.textbook_rag.cache import retrieve_textbook_evidence_cached, textbook_evidence_cache_fingerprints
from server.app.domains.textbook_rag.index import textbook_chunk_index_mapping
from server.app.domains.textbook_rag.retrieval import build_section_queries, retrieve_textbook_evidence
import server.app.domains.textbook_rag.retrieval as retrieval_module


def _settings() -> dict[str, Any]:
    return {
        "enabled": True,
        "elasticsearch_url": "http://localhost:9200",
        "index_name": "canonical-rag-chunks-qwen-v1",
        "embedding": {"base_url": "http://qwen.example", "api_key": "key", "model": "embed-model"},
        "rerank": {"base_url": "http://qwen.example", "api_key": "key", "model": "rerank-model"},
        "embedding_dimension": 2,
        "keyword_top_k": 2,
        "vector_top_k": 2,
        "rerank_top_k": 2,
        "final_top_k": 1,
        "min_rerank_score": 0.0,
        "timeout_seconds": 1.0,
    }


def test_extract_rerank_scores_supports_output_results_shape() -> None:
    response = {"output": {"results": [{"index": 1, "relevance_score": 0.2}, {"index": 0, "relevance_score": 0.9}]}}

    assert _extract_rerank_scores(response, 2) == [0.9, 0.2]


def test_qwen_embedding_client_sends_configured_dimensions(monkeypatch: Any) -> None:
    captured: dict[str, Any] = {}

    def fake_request_json(**kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return {"data": [{"embedding": [0.1, 0.2]}]}

    monkeypatch.setattr(client_module, "_request_json", fake_request_json)

    vectors = QwenEmbeddingClient(
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        api_key="key",
        model="text-embedding-v4",
        dimensions=1024,
    ).embed(["氯水置换溴离子"])

    assert vectors == [[0.1, 0.2]]
    assert captured["url"].endswith("/embeddings")
    assert captured["payload"]["dimensions"] == 1024


def test_qwen_rerank_client_supports_dashscope_native_payload(monkeypatch: Any) -> None:
    captured: dict[str, Any] = {}

    def fake_request_json(**kwargs: Any) -> dict[str, Any]:
        captured.update(kwargs)
        return {"output": {"results": [{"index": 0, "relevance_score": 0.7}, {"index": 1, "relevance_score": 0.3}]}}

    monkeypatch.setattr(client_module, "_request_json", fake_request_json)

    scores = QwenRerankClient(
        base_url="https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank",
        api_key="key",
        model="gte-rerank-v2",
    ).rerank(query="卤素氧化性", documents=["Cl2 oxidizes Br-", "unrelated"])

    assert scores == [0.7, 0.3]
    assert captured["url"].endswith("/services/rerank/text-rerank/text-rerank")
    assert captured["payload"]["input"]["query"] == "卤素氧化性"
    assert captured["payload"]["input"]["documents"] == ["Cl2 oxidizes Br-", "unrelated"]
    assert captured["payload"]["parameters"]["top_n"] == 2


def test_textbook_chunk_mapping_records_model_metadata() -> None:
    mapping = textbook_chunk_index_mapping(embedding_model="qwen-embed", embedding_dimension=1024)

    assert mapping["mappings"]["_meta"]["embedding_model"] == "qwen-embed"
    assert mapping["mappings"]["_meta"]["embedding_dimension"] == 1024
    assert mapping["mappings"]["properties"]["embedding"]["dims"] == 1024


def test_textbook_evidence_cache_fingerprint_excludes_api_keys() -> None:
    settings_a = _settings()
    settings_b = {
        **_settings(),
        "embedding": {**_settings()["embedding"], "api_key": "different-embedding-key"},
        "rerank": {**_settings()["rerank"], "api_key": "different-rerank-key"},
    }
    point_context = {
        "point_title": "氯水 + KBr + CCl4",
        "content": {"principle_text": "Cl2氧化Br-。"},
    }

    assert textbook_evidence_cache_fingerprints(
        point_context=point_context,
        settings=settings_a,
        point_node_id="point-1",
        canonical_point_id="canon-1",
    ) == textbook_evidence_cache_fingerprints(
        point_context=point_context,
        settings=settings_b,
        point_node_id="point-1",
        canonical_point_id="canon-1",
    )


def test_cached_textbook_evidence_does_not_call_retriever_on_hit() -> None:
    class FakeResult:
        rowcount = 0

        def __init__(self, row: dict[str, Any] | None) -> None:
            self.row = row

        def mappings(self) -> "FakeResult":
            return self

        def first(self) -> dict[str, Any] | None:
            return self.row

    class FakeSession:
        def execute(self, *_: Any, **__: Any) -> FakeResult:
            return FakeResult(
                {
                    "package": {"ok": True, "source_count": 1, "sections": {}, "diagnostics": {}},
                    "created_at": "2026-06-23T00:00:00Z",
                    "updated_at": "2026-06-23T00:00:00Z",
                }
            )

    def fail_retriever(**_: Any) -> dict[str, Any]:
        raise AssertionError("retriever should not run on cache hit")

    package = retrieve_textbook_evidence_cached(
        FakeSession(),
        point_context={"point_title": "氯水 + KBr + CCl4", "content": {"principle_text": "Cl2氧化Br-。"}},
        settings=_settings(),
        point_node_id="point-1",
        canonical_point_id="canon-1",
        retrieve_fn=fail_retriever,
    )

    assert package["cache"]["hit"] is True
    assert package["ok"] is True


def test_build_section_queries_uses_three_part_content() -> None:
    queries = build_section_queries(
        {
            "point_title": "氯水 + KBr + CCl4",
            "experiment_title": "二、卤素的氧化性",
            "textbook_chapter": "第 13 章 卤族元素",
            "content": {
                "principle_text": "Cl2氧化Br-。",
                "phenomenon_explanation": "CCl4层呈橙红色。",
                "safety_note": "通风橱操作。",
            },
        }
    )

    assert [query.section for query in queries] == ["principle", "phenomenon", "safety"]
    assert "氯水 + KBr + CCl4" in queries[0].query
    assert "实验原理" in queries[0].query


def test_retrieve_textbook_evidence_groups_section_sources(monkeypatch: Any) -> None:
    class FakeEmbeddingClient:
        def __init__(self, **_: Any) -> None:
            pass

        def embed(self, texts: list[str]) -> list[list[float]]:
            return [[0.1, 0.2] for _ in texts]

    class FakeRerankClient:
        def __init__(self, **_: Any) -> None:
            pass

        def rerank(self, *, query: str, documents: list[str]) -> list[float]:
            return [0.8 for _ in documents]

    class FakeES:
        def __init__(self, **_: Any) -> None:
            self.index = "idx"

        def request(self, method: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
            return {
                "hits": {
                    "hits": [
                        {
                            "_id": "chunk-1",
                            "_score": 1.2,
                            "_source": {
                                "chunk_id": "chunk-1",
                                "text": "Cl2 can oxidize Br- to Br2.",
                                "book_title": "无机化学实验",
                                "chapter": "第7章",
                                "section_path": ["第7章", "实验 19-1 卤素"],
                                "content_type": "experiment_protocol",
                                "content_hash": "hash",
                                "source_file": r"E:\\private\\canonical\\chapter-7.md",
                                "use_for_question_generation": True,
                                "metadata": {
                                    "knowledge_unit": "卤素的氧化性",
                                    "formulas": ["Cl2", "Br-"],
                                    "import_source_file": "/srv/private/canonical/chunks.jsonl",
                                    "source_md_files": ["/srv/private/pages/7.md"],
                                    "asset_paths": ["/srv/private/assets/reaction.png"],
                                    "internal_note": "not public",
                                },
                            },
                        }
                    ]
                }
            }

    monkeypatch.setattr(retrieval_module, "QwenEmbeddingClient", FakeEmbeddingClient)
    monkeypatch.setattr(retrieval_module, "QwenRerankClient", FakeRerankClient)
    monkeypatch.setattr(retrieval_module, "TextbookElasticsearchClient", FakeES)

    package = retrieve_textbook_evidence(
        point_context={
            "point_title": "氯水 + KBr + CCl4",
            "experiment_title": "二、卤素的氧化性",
            "content": {"principle_text": "Cl2氧化Br-。"},
        },
        settings=_settings(),
    )

    assert package["ok"] is True
    assert package["supported_sections"] == ["principle"]
    assert package["sections"]["principle"]["sources"][0]["chunk_id"] == "chunk-1"
    assert package["sections"]["principle"]["sources"][0]["rerank_score"] == 0.8
    assert package["sections"]["principle"]["sources"][0]["source_file"] == "chapter-7.md"
    assert package["sections"]["principle"]["candidates"][0]["source_file"] == "chapter-7.md"
    assert package["sections"]["principle"]["sources"][0]["metadata"] == {
        "knowledge_unit": "卤素的氧化性",
        "formulas": ["Cl2", "Br-"],
    }
    assert package["sections"]["principle"]["candidates"][0]["metadata"] == {
        "knowledge_unit": "卤素的氧化性",
        "formulas": ["Cl2", "Br-"],
    }


def test_retrieve_textbook_evidence_fails_when_all_sections_have_no_sources(monkeypatch: Any) -> None:
    class FakeEmbeddingClient:
        def __init__(self, **_: Any) -> None:
            pass

        def embed(self, texts: list[str]) -> list[list[float]]:
            return [[0.1, 0.2] for _ in texts]

    class FakeRerankClient:
        def __init__(self, **_: Any) -> None:
            pass

        def rerank(self, *, query: str, documents: list[str]) -> list[float]:
            return []

    class FakeES:
        def __init__(self, **_: Any) -> None:
            self.index = "idx"

        def request(self, method: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
            return {"hits": {"hits": []}}

    monkeypatch.setattr(retrieval_module, "QwenEmbeddingClient", FakeEmbeddingClient)
    monkeypatch.setattr(retrieval_module, "QwenRerankClient", FakeRerankClient)
    monkeypatch.setattr(retrieval_module, "TextbookElasticsearchClient", FakeES)

    package = retrieve_textbook_evidence(
        point_context={"point_title": "氯水 + KBr + CCl4", "content": {"principle_text": "Cl2氧化Br-。"}},
        settings=_settings(),
    )

    assert package["ok"] is False
    assert package["reason_code"] == "textbook_evidence_missing"
