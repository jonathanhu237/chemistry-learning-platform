from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DEFAULT_BUNDLE_DIR = ROOT / "data" / "seed" / "textbook_rag_precomputed"
DEFAULT_INDEX = "canonical-rag-chunks-qwen-v1"


OnlineInventoryLoader = Callable[[], dict[str, Any]]
OnlineReprojectionPreflight = Callable[[], dict[str, Any]]
OnlineRebuilder = Callable[[], dict[str, Any]]


@dataclass(frozen=True)
class ElasticsearchTarget:
    base_url: str
    index: str

    @property
    def display_url(self) -> str:
        """Return an operator-safe URL without credentials or query secrets."""

        parsed = urlsplit(self.base_url)
        if parsed.username is None and parsed.password is None:
            netloc = parsed.netloc
        else:
            hostname = parsed.hostname or ""
            if ":" in hostname and not hostname.startswith("["):
                hostname = f"[{hostname}]"
            port = f":{parsed.port}" if parsed.port is not None else ""
            netloc = f"***@{hostname}{port}"
        return urlunsplit((parsed.scheme, netloc, parsed.path, "", ""))


def _effective_ingestion_settings() -> Any:
    from server.app.domains.textbook_ingestion.config import effective_ingestion_settings

    return effective_ingestion_settings()


def resolve_elasticsearch_target(
    *,
    es_url: str | None = None,
    index: str | None = None,
) -> ElasticsearchTarget:
    """Resolve one immutable target, using DB-backed runtime settings by default."""

    effective = None
    if es_url is None or index is None:
        effective = _effective_ingestion_settings()
    resolved_url = (
        es_url
        if es_url is not None
        else str(effective.textbook_rag_elasticsearch_url or "")
    ).strip().rstrip("/")
    resolved_index = (
        index
        if index is not None
        else str(effective.textbook_rag_elasticsearch_index or "")
    ).strip()
    if not resolved_url:
        raise ValueError(
            "Elasticsearch URL is not configured; save the textbook RAG setting or pass --es-url"
        )
    if not resolved_index:
        raise ValueError(
            "Elasticsearch index is not configured; save the textbook RAG setting or pass --index"
        )
    return ElasticsearchTarget(base_url=resolved_url, index=resolved_index)


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
    bundle_index: str,
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
    settings = _index_settings(
        _json(bundle_dir / f"{bundle_index}.settings.json"),
        bundle_index,
        replicas=replicas,
    )
    mappings = _index_mappings(
        _json(bundle_dir / f"{bundle_index}.mapping.json"),
        bundle_index,
    )
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
    preflight_only: bool = False,
    rebuild_online_projections: bool = False,
    online_inventory_loader: OnlineInventoryLoader | None = None,
    online_reprojection_preflight: OnlineReprojectionPreflight | None = None,
    online_rebuilder: OnlineRebuilder | None = None,
) -> dict[str, Any]:
    manifest = _json(bundle_dir / "manifest.json")
    bundle_index = str(manifest.get("index") or DEFAULT_INDEX).strip()
    expected_docs = int(manifest.get("exported_docs") or manifest.get("es_count") or 0)
    expected_model = str(manifest.get("embedding_model") or "")
    expected_dimension = int(manifest.get("embedding_dimension") or 0)
    scanned = 0
    indexed = 0
    failures: list[str] = []
    operations: list[dict[str, Any]] = []
    online_inventory: dict[str, Any] = {"documents": 0, "chunks": 0, "by_status": {}}
    online_reprojection_contract: dict[str, Any] | None = None
    online_reprojection: dict[str, Any] | None = None

    if not expected_model:
        failures.append("seed bundle manifest has no embedding model")
    if expected_dimension <= 0:
        failures.append("seed bundle manifest has no valid embedding dimension")
    if preflight_only and not recreate:
        failures.append("--preflight-only requires --recreate")
    if rebuild_online_projections and not recreate:
        failures.append("--rebuild-online-projections requires --recreate")

    if recreate and (preflight_only or not dry_run) and not failures:
        try:
            if online_inventory_loader is None:
                from server.app.domains.textbook_ingestion.recovery import online_textbook_inventory

                online_inventory_loader = online_textbook_inventory
            online_inventory = online_inventory_loader()
            online_document_count = int(online_inventory.get("documents") or 0)
            if online_document_count and not rebuild_online_projections:
                failures.append(
                    "refusing to recreate the shared textbook index while online textbook documents exist; "
                    "rerun with --rebuild-online-projections after stopping ingestion workers"
                )
            if online_document_count and rebuild_online_projections:
                from server.app.domains.textbook_ingestion.recovery import (
                    RECREATE_SAFE_PUBLICATION_STATUSES,
                )

                by_status = dict(online_inventory.get("by_status") or {})
                unsafe_statuses = sorted(
                    status
                    for status, counts in by_status.items()
                    if int(dict(counts or {}).get("documents") or 0) > 0
                    and status not in RECREATE_SAFE_PUBLICATION_STATUSES
                )
                if unsafe_statuses:
                    failures.append(
                        "refusing to recreate the shared textbook index while online textbooks are in "
                        f"non-rebuildable states: {', '.join(unsafe_statuses)}"
                    )
                elif online_reprojection_preflight is not None:
                    online_reprojection_contract = online_reprojection_preflight()
                else:
                    from server.app.domains.textbook_ingestion.recovery import (
                        preflight_configured_online_reprojection,
                    )

                    online_reprojection_contract = preflight_configured_online_reprojection(
                        elasticsearch_url=base_url,
                        index=index,
                        publication_statuses=RECREATE_SAFE_PUBLICATION_STATUSES,
                    )
                if not failures:
                    configured_model = str(
                        dict(online_reprojection_contract or {}).get("embedding_model") or ""
                    ).strip()
                    configured_dimension = int(
                        dict(online_reprojection_contract or {}).get("embedding_dimension") or 0
                    )
                    if not configured_model or configured_dimension <= 0:
                        failures.append(
                            "online textbook reprojection preflight did not report an embedding contract"
                        )
                    if configured_model and configured_model != expected_model:
                        failures.append(
                            "seed bundle embedding model does not match online recovery contract: "
                            f"bundle={expected_model}, configured={configured_model}"
                        )
                    if configured_dimension > 0 and configured_dimension != expected_dimension:
                        failures.append(
                            "seed bundle embedding dimension does not match online recovery contract: "
                            f"bundle={expected_dimension}, configured={configured_dimension}"
                        )
        except Exception as exc:
            failures.append(
                "online textbook recreation preflight failed: "
                f"{getattr(exc, 'reason', exc.__class__.__name__)}"
            )

    if failures or preflight_only:
        return {
            "ok": not failures,
            "dry_run": dry_run,
            "preflight_only": preflight_only,
            "elasticsearch_url": ElasticsearchTarget(base_url, index).display_url,
            "index": index,
            "bundle_index": bundle_index,
            "bundle_dir": str(bundle_dir),
            "expected_documents": expected_docs,
            "scanned_documents": 0,
            "indexed_documents": 0,
            "embedding_model": expected_model,
            "embedding_dimension": expected_dimension,
            "online_inventory": online_inventory,
            "online_reprojection_contract": online_reprojection_contract,
            "online_reprojection": None,
            "failures": failures,
        }

    if not dry_run:
        _create_index(
            base_url=base_url,
            bundle_dir=bundle_dir,
            index=index,
            bundle_index=bundle_index,
            recreate=recreate,
            replicas=replicas,
            timeout=timeout,
        )

    for item in _iter_documents(bundle_dir, bundle_index):
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
    if (
        not dry_run
        and not failures
        and rebuild_online_projections
        and int(online_inventory.get("documents") or 0) > 0
    ):
        if online_rebuilder is None:
            from server.app.domains.textbook_ingestion.recovery import (
                RECREATE_SAFE_PUBLICATION_STATUSES,
                reproject_configured_online_textbooks,
            )

            online_rebuilder = lambda: reproject_configured_online_textbooks(
                elasticsearch_url=base_url,
                index=index,
                publication_statuses=RECREATE_SAFE_PUBLICATION_STATUSES,
            )
        try:
            online_reprojection = online_rebuilder()
        except Exception as exc:
            failures.append(
                "online textbook reprojection failed after seed import: "
                f"{getattr(exc, 'reason', exc.__class__.__name__)}"
            )
    return {
        "ok": not failures,
        "dry_run": dry_run,
        "preflight_only": preflight_only,
        "elasticsearch_url": ElasticsearchTarget(base_url, index).display_url,
        "index": index,
        "bundle_index": bundle_index,
        "bundle_dir": str(bundle_dir),
        "expected_documents": expected_docs,
        "scanned_documents": scanned,
        "indexed_documents": indexed,
        "embedding_model": expected_model,
        "embedding_dimension": expected_dimension,
        "online_inventory": online_inventory,
        "online_reprojection_contract": online_reprojection_contract,
        "online_reprojection": online_reprojection,
        "failures": failures,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Import precomputed Qwen textbook RAG embeddings into Elasticsearch.")
    parser.add_argument("--bundle-dir", type=Path, default=DEFAULT_BUNDLE_DIR)
    parser.add_argument("--es-url", default=None)
    parser.add_argument("--index", default=None)
    parser.add_argument("--batch-size", type=int, default=200)
    parser.add_argument("--timeout", type=float, default=120.0)
    parser.add_argument("--recreate", action="store_true")
    parser.add_argument(
        "--preflight-only",
        action="store_true",
        help="Validate shared-index recreation safety without mutating Elasticsearch.",
    )
    parser.add_argument(
        "--rebuild-online-projections",
        action="store_true",
        help=(
            "After an explicit shared-index recreate, recompute and restore all retained online "
            "textbook projections from PostgreSQL. Stop ingestion workers before using this workflow."
        ),
    )
    parser.add_argument("--replicas", type=int, default=0)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        target = resolve_elasticsearch_target(es_url=args.es_url, index=args.index)
    except ValueError as exc:
        parser.error(str(exc))
    result = import_precomputed_index(
        base_url=target.base_url,
        bundle_dir=args.bundle_dir,
        index=target.index,
        recreate=bool(args.recreate),
        batch_size=max(1, int(args.batch_size)),
        replicas=args.replicas,
        timeout=max(1.0, float(args.timeout)),
        dry_run=bool(args.dry_run),
        preflight_only=bool(args.preflight_only),
        rebuild_online_projections=bool(args.rebuild_online_projections),
    )
    sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
