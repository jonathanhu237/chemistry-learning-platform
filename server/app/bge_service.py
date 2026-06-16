from __future__ import annotations

import os
import threading
import time
from functools import lru_cache
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


EMBED_MODEL = os.getenv("BGE_EMBED_MODEL", "BAAI/bge-m3")
RERANK_MODEL = os.getenv("BGE_RERANK_MODEL", "BAAI/bge-reranker-v2-m3")
DEVICE = os.getenv("BGE_DEVICE", "cpu")
USE_FP16 = os.getenv("BGE_USE_FP16", "false").strip().lower() in {"1", "true", "yes", "on"}
RERANK_MAX_LENGTH = int(os.getenv("BGE_RERANK_MAX_LENGTH", "1024"))
BGE_WARMUP_ON_STARTUP = os.getenv("BGE_WARMUP_ON_STARTUP", "false").strip().lower() in {"1", "true", "yes", "on"}
BGE_WARMUP_QUERY = os.getenv("BGE_WARMUP_QUERY", "高锰酸钾 氧化性 原因")
BGE_WARMUP_DOCUMENT = os.getenv(
    "BGE_WARMUP_DOCUMENT",
    "高锰酸钾具有强氧化性，氧化能力和还原产物会随介质酸碱性不同而变化。",
)
SERVICE_STARTED_AT = time.time()
REQUEST_COUNTS = {"embed": 0, "rerank": 0}
MODEL_LOAD_LOCK = threading.RLock()
WARMUP_LOCK = threading.Lock()
WARMUP_STATE: dict[str, Any] = {
    "enabled": BGE_WARMUP_ON_STARTUP,
    "status": "not_started" if BGE_WARMUP_ON_STARTUP else "disabled",
    "trigger": None,
    "started_at": None,
    "finished_at": None,
    "duration_ms": None,
    "error": None,
}

app = FastAPI(title="Chemistry BGE RAG Service")


class EmbedRequest(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=32)


class EmbedResponse(BaseModel):
    model: str
    dimension: int
    embeddings: list[list[float]]


class RerankRequest(BaseModel):
    query: str = Field(min_length=1)
    documents: list[str] = Field(min_length=1, max_length=64)


class RerankResponse(BaseModel):
    model: str
    scores: list[float]


@app.on_event("startup")
def startup_warmup() -> None:
    if BGE_WARMUP_ON_STARTUP:
        _start_warmup("startup")


@lru_cache(maxsize=1)
def _embedder() -> Any:
    try:
        from FlagEmbedding import BGEM3FlagModel
    except Exception as exc:  # pragma: no cover - optional service dependency
        raise RuntimeError("FlagEmbedding is required for the BGE embed service") from exc
    return BGEM3FlagModel(EMBED_MODEL, use_fp16=USE_FP16, device=DEVICE)


@lru_cache(maxsize=1)
def _reranker() -> Any:
    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except Exception as exc:  # pragma: no cover - optional service dependency
        raise RuntimeError("transformers and torch are required for the BGE rerank service") from exc

    device = DEVICE
    dtype = torch.float16 if USE_FP16 and device != "cpu" else torch.float32
    tokenizer = AutoTokenizer.from_pretrained(RERANK_MODEL, local_files_only=_offline_enabled())
    model = AutoModelForSequenceClassification.from_pretrained(
        RERANK_MODEL,
        local_files_only=_offline_enabled(),
        torch_dtype=dtype,
    ).to(device)
    model.eval()
    return _SequenceClassificationReranker(
        tokenizer=tokenizer,
        model=model,
        torch=torch,
        device=device,
        max_length=RERANK_MAX_LENGTH,
    )


def _get_embedder() -> Any:
    with MODEL_LOAD_LOCK:
        return _embedder()


def _get_reranker() -> Any:
    with MODEL_LOAD_LOCK:
        return _reranker()


@app.get("/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "embed_model": EMBED_MODEL,
        "rerank_model": RERANK_MODEL,
        "device": DEVICE,
        "use_fp16": USE_FP16,
        "rerank_backend": "transformers-sequence-classification",
        "rerank_max_length": RERANK_MAX_LENGTH,
        "warmup": _warmup_snapshot(),
    }


@app.get("/metrics")
def metrics() -> dict[str, Any]:
    return {
        "ok": True,
        "service": "bge-rag",
        "config": {
            "embed_model": EMBED_MODEL,
            "rerank_model": RERANK_MODEL,
            "device": DEVICE,
            "use_fp16": USE_FP16,
            "rerank_backend": "transformers-sequence-classification",
            "rerank_max_length": RERANK_MAX_LENGTH,
            "offline": _offline_enabled(),
        },
        "models": {
            "embed_loaded": _cache_loaded(_embedder),
            "rerank_loaded": _cache_loaded(_reranker),
        },
        "requests": dict(REQUEST_COUNTS),
        "process": _process_metrics(),
        "container": _container_metrics(),
        "warmup": _warmup_snapshot(),
    }


@app.post("/warmup")
def warmup() -> dict[str, Any]:
    return _start_warmup("manual")


@app.post("/embed", response_model=EmbedResponse)
def embed(payload: EmbedRequest) -> EmbedResponse:
    REQUEST_COUNTS["embed"] += 1
    texts = [_normalize_text(text) for text in payload.texts]
    if not all(texts):
        raise HTTPException(status_code=400, detail="texts must be non-empty")
    try:
        result = _get_embedder().encode(texts, batch_size=min(8, len(texts)), max_length=8192, return_dense=True)
        dense = result["dense_vecs"] if isinstance(result, dict) else result
        embeddings = [_to_float_list(item) for item in dense]
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"BGE embed failed: {exc.__class__.__name__}") from exc
    dimension = len(embeddings[0]) if embeddings else 0
    return EmbedResponse(model=EMBED_MODEL, dimension=dimension, embeddings=embeddings)


@app.post("/rerank", response_model=RerankResponse)
def rerank(payload: RerankRequest) -> RerankResponse:
    REQUEST_COUNTS["rerank"] += 1
    query = _normalize_text(payload.query)
    documents = [_normalize_text(document) for document in payload.documents]
    if not query or not all(documents):
        raise HTTPException(status_code=400, detail="query and documents must be non-empty")
    pairs = [[query, document] for document in documents]
    try:
        scores = _get_reranker().compute_score(pairs, normalize=True)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"BGE rerank failed: {exc.__class__.__name__}") from exc
    if isinstance(scores, (int, float)):
        score_list = [float(scores)]
    else:
        score_list = [float(score) for score in scores]
    return RerankResponse(model=RERANK_MODEL, scores=score_list)


def _normalize_text(value: str) -> str:
    return " ".join(str(value or "").split())


def _to_float_list(value: Any) -> list[float]:
    if hasattr(value, "tolist"):
        value = value.tolist()
    return [float(item) for item in value]


def _offline_enabled() -> bool:
    return any(
        os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}
        for name in ("HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE")
    )


def _cache_loaded(loader: Any) -> bool:
    cache_info = loader.cache_info()
    return bool(getattr(cache_info, "currsize", 0))


def _start_warmup(trigger: str) -> dict[str, Any]:
    with WARMUP_LOCK:
        if WARMUP_STATE["status"] == "running":
            return _warmup_snapshot_locked()
        WARMUP_STATE.update(
            {
                "enabled": True,
                "status": "running",
                "trigger": trigger,
                "started_at": _iso_now(),
                "finished_at": None,
                "duration_ms": None,
                "error": None,
            }
        )
    thread = threading.Thread(target=_run_warmup, daemon=True, name="bge-warmup")
    thread.start()
    return _warmup_snapshot()


def _run_warmup() -> None:
    started_at = time.perf_counter()
    try:
        _get_embedder().encode([BGE_WARMUP_QUERY], batch_size=1, max_length=8192, return_dense=True)
        _get_reranker().compute_score([[BGE_WARMUP_QUERY, BGE_WARMUP_DOCUMENT]], normalize=True)
    except Exception as exc:  # pragma: no cover - startup/runtime diagnostic
        with WARMUP_LOCK:
            WARMUP_STATE.update(
                {
                    "status": "failed",
                    "finished_at": _iso_now(),
                    "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
                    "error": f"{exc.__class__.__name__}: {str(exc)[:240]}",
                }
            )
        return
    with WARMUP_LOCK:
        WARMUP_STATE.update(
            {
                "status": "succeeded",
                "finished_at": _iso_now(),
                "duration_ms": round((time.perf_counter() - started_at) * 1000, 2),
                "error": None,
            }
        )


def _warmup_snapshot() -> dict[str, Any]:
    with WARMUP_LOCK:
        return _warmup_snapshot_locked()


def _warmup_snapshot_locked() -> dict[str, Any]:
    snapshot = dict(WARMUP_STATE)
    snapshot["models_ready"] = _cache_loaded(_embedder) and _cache_loaded(_reranker)
    return snapshot


def _iso_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _process_metrics() -> dict[str, Any]:
    os_times = os.times()
    metrics: dict[str, Any] = {
        "uptime_seconds": round(time.time() - SERVICE_STARTED_AT, 2),
        "cpu_user_seconds": round(float(os_times.user), 3),
        "cpu_system_seconds": round(float(os_times.system), 3),
        "memory_rss_mb": None,
        "memory_high_water_mb": None,
        "thread_count": None,
    }
    try:
        with open("/proc/self/status", encoding="utf-8") as status_file:
            for line in status_file:
                key, _, value = line.partition(":")
                if key == "VmRSS":
                    metrics["memory_rss_mb"] = _kb_status_to_mb(value)
                elif key == "VmHWM":
                    metrics["memory_high_water_mb"] = _kb_status_to_mb(value)
                elif key == "Threads":
                    metrics["thread_count"] = int(value.strip())
    except (OSError, ValueError):
        pass
    return metrics


def _container_metrics() -> dict[str, Any]:
    return {
        "memory_current_mb": _read_cgroup_bytes_mb("/sys/fs/cgroup/memory.current")
        or _read_cgroup_bytes_mb("/sys/fs/cgroup/memory/memory.usage_in_bytes"),
        "memory_limit_mb": _read_cgroup_limit_mb(),
        **_read_cgroup_cpu_stat(),
    }


def _read_cgroup_bytes_mb(path: str) -> float | None:
    try:
        raw_value = open(path, encoding="utf-8").read().strip()
        if not raw_value or raw_value == "max":
            return None
        return round(float(raw_value) / 1024 / 1024, 1)
    except (OSError, ValueError):
        return None


def _read_cgroup_limit_mb() -> float | None:
    return _read_cgroup_bytes_mb("/sys/fs/cgroup/memory.max") or _read_cgroup_bytes_mb(
        "/sys/fs/cgroup/memory/memory.limit_in_bytes"
    )


def _read_cgroup_cpu_stat() -> dict[str, Any]:
    output: dict[str, Any] = {
        "cpu_usage_seconds": None,
        "cpu_user_seconds": None,
        "cpu_system_seconds": None,
        "cpu_throttled_seconds": None,
    }
    try:
        values: dict[str, float] = {}
        with open("/sys/fs/cgroup/cpu.stat", encoding="utf-8") as cpu_file:
            for line in cpu_file:
                key, _, value = line.partition(" ")
                if key and value.strip():
                    values[key] = float(value.strip())
        if "usage_usec" in values:
            output["cpu_usage_seconds"] = round(values["usage_usec"] / 1_000_000, 3)
        if "user_usec" in values:
            output["cpu_user_seconds"] = round(values["user_usec"] / 1_000_000, 3)
        if "system_usec" in values:
            output["cpu_system_seconds"] = round(values["system_usec"] / 1_000_000, 3)
        if "throttled_usec" in values:
            output["cpu_throttled_seconds"] = round(values["throttled_usec"] / 1_000_000, 3)
    except (OSError, ValueError):
        pass
    if output["cpu_usage_seconds"] is None:
        try:
            usage_ns = float(open("/sys/fs/cgroup/cpuacct/cpuacct.usage", encoding="utf-8").read().strip())
            output["cpu_usage_seconds"] = round(usage_ns / 1_000_000_000, 3)
        except (OSError, ValueError):
            pass
    if output["cpu_user_seconds"] is None or output["cpu_system_seconds"] is None:
        try:
            ticks_per_second = float(os.sysconf("SC_CLK_TCK"))
            values = {}
            with open("/sys/fs/cgroup/cpuacct/cpuacct.stat", encoding="utf-8") as cpu_file:
                for line in cpu_file:
                    key, _, value = line.partition(" ")
                    if key and value.strip():
                        values[key] = float(value.strip())
            if "user" in values:
                output["cpu_user_seconds"] = round(values["user"] / ticks_per_second, 3)
            if "system" in values:
                output["cpu_system_seconds"] = round(values["system"] / ticks_per_second, 3)
        except (OSError, ValueError):
            pass
    return output


def _kb_status_to_mb(value: str) -> float | None:
    parts = value.strip().split()
    if not parts:
        return None
    try:
        return round(float(parts[0]) / 1024, 1)
    except ValueError:
        return None


class _SequenceClassificationReranker:
    def __init__(self, *, tokenizer: Any, model: Any, torch: Any, device: str, max_length: int) -> None:
        self.tokenizer = tokenizer
        self.model = model
        self.torch = torch
        self.device = device
        self.max_length = max_length

    def compute_score(self, pairs: list[list[str]], normalize: bool = True) -> list[float]:
        if not pairs:
            return []
        queries = [pair[0] for pair in pairs]
        documents = [pair[1] for pair in pairs]
        with self.torch.no_grad():
            encoded = self.tokenizer(
                queries,
                documents,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors="pt",
            ).to(self.device)
            logits = self.model(**encoded).logits.reshape(-1).float()
            if normalize:
                logits = self.torch.sigmoid(logits)
            return [float(score) for score in logits.detach().cpu().tolist()]
