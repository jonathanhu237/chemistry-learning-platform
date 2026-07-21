from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


class TextbookRAGClientError(RuntimeError):
    pass


def _request_json(
    *,
    url: str,
    api_key: str,
    payload: dict[str, Any],
    timeout: float,
) -> dict[str, Any] | list[Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise TextbookRAGClientError(f"request failed: {exc.__class__.__name__}: {str(exc)[:180]}") from exc
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise TextbookRAGClientError("response is not valid JSON") from exc
    if not isinstance(parsed, (dict, list)):
        raise TextbookRAGClientError("response JSON must be an object or array")
    return parsed


def _join_endpoint(base_url: str, default_suffix: str) -> str:
    normalized = base_url.rstrip("/")
    if not normalized:
        return default_suffix
    if normalized.endswith(default_suffix) or normalized.endswith("/embeddings"):
        return normalized
    return f"{normalized}{default_suffix}"


def _resolve_endpoint(base_url: str, endpoint: str, default_suffix: str) -> str:
    explicit = endpoint.strip()
    if explicit.startswith(("http://", "https://")):
        return explicit.rstrip("/")
    if explicit:
        normalized_base = base_url.rstrip("/")
        if not normalized_base:
            return explicit
        return f"{normalized_base}/{explicit.lstrip('/')}"
    return _join_endpoint(base_url, default_suffix)


def endpoint_configured(base_url: str, endpoint: str) -> bool:
    explicit = endpoint.strip()
    return bool(base_url.strip() or explicit.startswith(("http://", "https://")))


def validate_embedding_protocol(protocol: str) -> str:
    normalized = protocol.strip().lower().replace("-", "_")
    if normalized in {"", "auto", "openai", "openai_compatible", "openai_embeddings"}:
        return "openai_embeddings"
    raise TextbookRAGClientError(f"unsupported embedding protocol: {protocol or '<empty>'}")


def validate_rerank_protocol(protocol: str) -> str:
    normalized = protocol.strip().lower().replace("-", "_")
    if normalized in {"", "auto"}:
        return "auto"
    if normalized in {"openai", "openai_compatible", "openai_rerank"}:
        return "openai_rerank"
    if normalized in {"tei", "tei_rerank", "text_embeddings_inference"}:
        return "tei"
    raise TextbookRAGClientError(f"unsupported rerank protocol: {protocol or '<empty>'}")


def _validated_result_index(
    value: Any,
    *,
    expected_count: int,
    response_kind: str,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TextbookRAGClientError(f"{response_kind} result has invalid index")
    if value < 0 or value >= expected_count:
        raise TextbookRAGClientError(f"{response_kind} result index is out of range")
    return value


def embedding_profile_fingerprint(
    *,
    provider: str,
    protocol: str,
    base_url: str,
    endpoint: str,
    model: str,
    dimensions: int | None,
    send_dimensions: bool,
) -> str:
    """Identify one embedding vector space without including credentials.

    A model alias and dimension are insufficient: two gateways can expose the
    same alias while producing incompatible vectors. The resolved endpoint and
    request contract therefore participate in every index/reuse check.
    """

    payload = {
        "schema_version": 1,
        "provider": provider.strip().lower(),
        "protocol": validate_embedding_protocol(protocol),
        "endpoint": _resolve_endpoint(base_url.strip(), endpoint, "/embeddings"),
        "model": model.strip(),
        "dimensions": int(dimensions or 0),
        "send_dimensions": bool(send_dimensions),
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _rerank_endpoint(base_url: str, model: str) -> str:
    normalized = base_url.rstrip("/")
    if not normalized:
        return "/rerank"
    lower = normalized.lower()
    if lower.endswith(("/rerank", "/reranks", "/text-rerank")):
        return normalized
    if "dashscope" in lower and lower.endswith("/api/v1"):
        return f"{normalized}/services/rerank/text-rerank/text-rerank"
    if "compatible-api" in lower or "compatible-mode" in lower:
        return f"{normalized}/reranks" if model == "qwen3-rerank" else f"{normalized}/rerank"
    return f"{normalized}/rerank"


def _rerank_payload(*, endpoint: str, model: str, query: str, documents: list[str]) -> dict[str, Any]:
    lower = endpoint.lower()
    if "/services/rerank/" in lower or lower.endswith("/text-rerank"):
        return {
            "model": model,
            "input": {"query": query, "documents": documents},
            "parameters": {"return_documents": False, "top_n": len(documents)},
        }
    return {
        "model": model,
        "query": query,
        "documents": documents,
        "top_n": len(documents),
    }


@dataclass(frozen=True)
class OpenAICompatibleEmbeddingClient:
    base_url: str
    api_key: str
    model: str
    dimensions: int | None = None
    timeout_seconds: float = 8.0
    provider: str = "openai_compatible"
    protocol: str = "openai_embeddings"
    endpoint: str = ""
    send_dimensions: bool = True

    @property
    def ready(self) -> bool:
        return bool(
            endpoint_configured(self.base_url, self.endpoint)
            and self.api_key
            and self.model
        )

    @property
    def profile_fingerprint(self) -> str:
        return embedding_profile_fingerprint(
            provider=self.provider,
            protocol=self.protocol,
            base_url=self.base_url,
            endpoint=self.endpoint,
            model=self.model,
            dimensions=self.dimensions,
            send_dimensions=self.send_dimensions,
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        if not self.ready:
            raise TextbookRAGClientError("embedding client is not configured")
        if not texts:
            return []
        validate_embedding_protocol(self.protocol)
        payload: dict[str, Any] = {"model": self.model, "input": texts}
        if self.send_dimensions and self.dimensions:
            payload["dimensions"] = int(self.dimensions)
        response = _request_json(
            url=_resolve_endpoint(self.base_url, self.endpoint, "/embeddings"),
            api_key=self.api_key,
            payload=payload,
            timeout=self.timeout_seconds,
        )
        if not isinstance(response, dict):
            raise TextbookRAGClientError("embedding response JSON must be an object")
        data = response.get("data")
        if not isinstance(data, list):
            raise TextbookRAGClientError("embedding response missing data list")
        if len(data) != len(texts):
            raise TextbookRAGClientError("embedding response count does not match input count")
        embeddings: list[tuple[int | None, list[float]]] = []
        indexed_items = 0
        for item in data:
            if not isinstance(item, dict) or not isinstance(item.get("embedding"), list):
                raise TextbookRAGClientError("embedding response item missing embedding")
            embedding = [float(value) for value in item["embedding"]]
            if not embedding:
                raise TextbookRAGClientError("embedding response contained an empty vector")
            result_index = None
            if "index" in item:
                indexed_items += 1
                result_index = _validated_result_index(
                    item["index"],
                    expected_count=len(texts),
                    response_kind="embedding",
                )
            embeddings.append((result_index, embedding))
        if indexed_items == 0:
            return [embedding for _index, embedding in embeddings]
        if indexed_items != len(embeddings):
            raise TextbookRAGClientError(
                "embedding response mixes indexed and sequential items"
            )
        ordered: list[list[float] | None] = [None] * len(texts)
        for result_index, embedding in embeddings:
            if result_index is None:
                raise TextbookRAGClientError("embedding response item is missing index")
            if ordered[result_index] is not None:
                raise TextbookRAGClientError("embedding response contains duplicate index")
            ordered[result_index] = embedding
        if any(embedding is None for embedding in ordered):
            raise TextbookRAGClientError("embedding response is missing indexed items")
        return [embedding for embedding in ordered if embedding is not None]


@dataclass(frozen=True)
class OpenAICompatibleRerankClient:
    base_url: str
    api_key: str
    model: str
    timeout_seconds: float = 8.0
    provider: str = "openai_compatible"
    protocol: str = "auto"
    endpoint: str = ""

    @property
    def ready(self) -> bool:
        return bool(
            endpoint_configured(self.base_url, self.endpoint)
            and self.api_key
            and self.model
        )

    def rerank(self, *, query: str, documents: list[str]) -> list[float]:
        if not self.ready:
            raise TextbookRAGClientError("rerank client is not configured")
        if not documents:
            return []
        protocol = validate_rerank_protocol(self.protocol)
        if protocol == "auto":
            endpoint = (
                _resolve_endpoint(self.base_url, self.endpoint, "/rerank")
                if self.endpoint
                else _rerank_endpoint(self.base_url, self.model)
            )
            payload = _rerank_payload(
                endpoint=endpoint,
                model=self.model,
                query=query,
                documents=documents,
            )
        elif protocol == "openai_rerank":
            endpoint = _resolve_endpoint(self.base_url, self.endpoint, "/rerank")
            payload = {
                "model": self.model,
                "query": query,
                "documents": documents,
                "top_n": len(documents),
            }
        else:
            endpoint = _resolve_endpoint(self.base_url, self.endpoint, "/rerank")
            payload = {"query": query, "texts": documents}
        response = _request_json(
            url=endpoint,
            api_key=self.api_key,
            payload=payload,
            timeout=self.timeout_seconds,
        )
        scores = _extract_rerank_scores(response, len(documents))
        if len(scores) != len(documents):
            raise TextbookRAGClientError("rerank response count does not match document count")
        return scores


def _extract_rerank_scores(
    response: dict[str, Any] | list[Any],
    expected_count: int,
) -> list[float]:
    result_sets: list[Any] = []
    if isinstance(response, list):
        result_sets = response
    elif isinstance(response.get("scores"), list):
        scores = [float(score) for score in response["scores"]]
        if len(scores) != expected_count:
            raise TextbookRAGClientError(
                "rerank response count does not match document count"
            )
        return scores
    elif isinstance(response.get("results"), list):
        result_sets = response["results"]
    elif isinstance(response.get("data"), list):
        result_sets = response["data"]
    elif isinstance(response.get("output"), dict) and isinstance(response["output"].get("results"), list):
        result_sets = response["output"]["results"]
    if not result_sets:
        raise TextbookRAGClientError("rerank response missing scores/results")
    parsed: list[tuple[int | None, float]] = []
    indexed_items = 0
    for item in result_sets:
        if not isinstance(item, dict):
            parsed.append((None, float(item)))
            continue
        score = item.get("relevance_score", item.get("score", item.get("rerank_score")))
        if score is None:
            raise TextbookRAGClientError("rerank result missing score")
        result_index = None
        index_field = "index" if "index" in item else "document_index"
        if index_field in item:
            indexed_items += 1
            result_index = _validated_result_index(
                item[index_field],
                expected_count=expected_count,
                response_kind="rerank",
            )
        parsed.append((result_index, float(score)))
    if indexed_items == 0:
        scores = [score for _index, score in parsed]
        if len(scores) != expected_count:
            raise TextbookRAGClientError(
                "rerank response count does not match document count"
            )
        return scores
    if indexed_items != len(parsed):
        raise TextbookRAGClientError("rerank response mixes indexed and sequential results")
    scores: list[float | None] = [None] * expected_count
    for result_index, score in parsed:
        if result_index is None:
            raise TextbookRAGClientError("rerank result is missing index")
        if scores[result_index] is not None:
            raise TextbookRAGClientError("rerank response contains duplicate index")
        scores[result_index] = score
    if any(score is None for score in scores):
        raise TextbookRAGClientError("rerank response is missing indexed results")
    return [score for score in scores if score is not None]


# Backward-compatible imports for scripts and integrations that still use the
# historical Qwen-specific names. The clients themselves are provider-neutral.
QwenEmbeddingClient = OpenAICompatibleEmbeddingClient
QwenRerankClient = OpenAICompatibleRerankClient
