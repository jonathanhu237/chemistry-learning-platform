from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_BUNDLE_DIR = ROOT / "data" / "seed" / "textbook_rag_precomputed"
DEFAULT_INDEX = "canonical-rag-chunks-qwen-v1"
DEFAULT_ES_URL = "http://127.0.0.1:9200"


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _request(base_url: str, method: str, path: str, payload: Any | None = None, *, timeout: float = 60.0) -> Any:
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method=method,
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
    return json.loads(raw) if raw else {}


def _bulk(base_url: str, operations: list[dict[str, Any]], *, timeout: float = 120.0) -> dict[str, Any]:
    body = "\n".join(json.dumps(item, ensure_ascii=False) for item in operations) + "\n"
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/_bulk",
        data=body.encode("utf-8"),
        headers={"Content-Type": "application/x-ndjson"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
    return json.loads(raw) if raw else {}


def _index_settings(settings_export: dict[str, Any], index: str, *, replicas: int | None = None) -> dict[str, Any]:
    raw = (((settings_export.get(index) or {}).get("settings") or {}).get("index") or {})
    settings: dict[str, Any] = {}
    if raw.get("analysis"):
        settings["analysis"] = raw["analysis"]
    settings["number_of_shards"] = int(raw.get("number_of_shards") or 1)
    settings["number_of_replicas"] = int(replicas if replicas is not None else raw.get("number_of_replicas") or 0)
    return settings


def _index_mappings(mapping_export: dict[str, Any], index: str) -> dict[str, Any]:
    mappings = (mapping_export.get(index) or {}).get("mappings")
    if not isinstance(mappings, dict):
        raise ValueError(f"Mapping export does not contain mappings for index {index!r}")
    return mappings


def _iter_jsonl_from_zip(zip_path: Path) -> Iterable[dict[str, Any]]:
    with zipfile.ZipFile(zip_path) as archive:
        names = [name for name in archive.namelist() if name.endswith(".jsonl")]
        if len(names) != 1:
            raise ValueError(f"{zip_path} must contain exactly one .jsonl file, found {len(names)}")
        with archive.open(names[0], "r") as handle:
            for raw in handle:
                line = raw.decode("utf-8").strip()
                if line:
                    yield json.loads(line)


def _iter_documents(bundle_dir: Path, index: str) -> Iterable[dict[str, Any]]:
    zip_path = bundle_dir / f"{index}.documents.jsonl.zip"
    plain_path = bundle_dir / f"{index}.documents.jsonl"
    if zip_path.exists():
        yield from _iter_jsonl_from_zip(zip_path)
        return
    if plain_path.exists():
        with plain_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    yield json.loads(line)
        return
    raise FileNotFoundError(f"Missing {zip_path} or {plain_path}")


def _create_index(
    *,
    base_url: str,
    bundle_dir: Path,
    index: str,
    recreate: bool,
    replicas: int | None,
    timeout: float,
) -> None:
    if recreate:
        try:
            _request(base_url, "DELETE", f"/{index}", timeout=timeout)
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
    try:
        _request(base_url, "HEAD", f"/{index}", timeout=timeout)
        return
    except urllib.error.HTTPError as exc:
        if exc.code != 404:
            raise
    settings = _index_settings(_json(bundle_dir / f"{index}.settings.json"), index, replicas=replicas)
    mappings = _index_mappings(_json(bundle_dir / f"{index}.mapping.json"), index)
    _request(base_url, "PUT", f"/{index}", {"settings": settings, "mappings": mappings}, timeout=timeout)


def import_precomputed_index(
    *,
    base_url: str,
    bundle_dir: Path,
    index: str,
    recreate: bool,
    batch_size: int,
    replicas: int | None,
    timeout: float,
    dry_run: bool,
) -> dict[str, Any]:
    manifest = _json(bundle_dir / "manifest.json")
    expected_docs = int(manifest.get("exported_docs") or manifest.get("es_count") or 0)
    expected_model = str(manifest.get("embedding_model") or "")
    expected_dimension = int(manifest.get("embedding_dimension") or 0)
    scanned = 0
    indexed = 0
    failures: list[str] = []
    operations: list[dict[str, Any]] = []

    if not dry_run:
        _create_index(
            base_url=base_url,
            bundle_dir=bundle_dir,
            index=index,
            recreate=recreate,
            replicas=replicas,
            timeout=timeout,
        )

    for item in _iter_documents(bundle_dir, index):
        scanned += 1
        doc_id = str(item.get("_id") or "")
        source = item.get("_source") if isinstance(item.get("_source"), dict) else {}
        if not doc_id:
            failures.append(f"line {scanned}: missing _id")
            continue
        embedding = source.get("embedding")
        if not isinstance(embedding, list) or len(embedding) != expected_dimension:
            failures.append(f"{doc_id}: embedding dimension mismatch")
            continue
        if source.get("embedding_model") != expected_model:
            failures.append(f"{doc_id}: embedding model mismatch")
            continue
        if dry_run:
            indexed += 1
            continue
        operations.append({"index": {"_index": index, "_id": doc_id}})
        operations.append(source)
        if len(operations) >= batch_size * 2:
            response = _bulk(base_url, operations, timeout=timeout)
            if response.get("errors"):
                failures.append("Elasticsearch bulk request reported item errors")
            indexed += len(operations) // 2
            operations = []
    if operations and not dry_run:
        response = _bulk(base_url, operations, timeout=timeout)
        if response.get("errors"):
            failures.append("Elasticsearch bulk request reported item errors")
        indexed += len(operations) // 2
    if not dry_run:
        _request(base_url, "POST", f"/{index}/_refresh", timeout=timeout)
    if expected_docs and scanned != expected_docs:
        failures.append(f"expected {expected_docs} documents, scanned {scanned}")
    return {
        "ok": not failures,
        "dry_run": dry_run,
        "index": index,
        "bundle_dir": str(bundle_dir),
        "expected_documents": expected_docs,
        "scanned_documents": scanned,
        "indexed_documents": indexed,
        "embedding_model": expected_model,
        "embedding_dimension": expected_dimension,
        "failures": failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Import precomputed Qwen textbook RAG embeddings into Elasticsearch.")
    parser.add_argument("--bundle-dir", type=Path, default=DEFAULT_BUNDLE_DIR)
    parser.add_argument("--es-url", default=os.getenv("TEXTBOOK_RAG_ELASTICSEARCH_URL") or os.getenv("ELASTICSEARCH_URL") or DEFAULT_ES_URL)
    parser.add_argument("--index", default=os.getenv("TEXTBOOK_RAG_ELASTICSEARCH_INDEX") or DEFAULT_INDEX)
    parser.add_argument("--batch-size", type=int, default=200)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--recreate", action="store_true")
    parser.add_argument("--replicas", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = import_precomputed_index(
        base_url=args.es_url,
        bundle_dir=args.bundle_dir,
        index=args.index,
        recreate=bool(args.recreate),
        batch_size=max(1, int(args.batch_size)),
        replicas=args.replicas,
        timeout=max(1.0, float(args.timeout)),
        dry_run=bool(args.dry_run),
    )
    sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
