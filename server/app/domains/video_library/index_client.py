from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from datetime import date, datetime
from typing import Any

from sqlalchemy import text

from server.app.chemistry_search import chemistry_vocabulary_metadata
from server.app.infrastructure.settings import ROOT, get_settings
from server.app.infrastructure.database import db_session


VIDEO_LIBRARY_INDEX_MAPPING_VERSION = "chemistry-point-placement-v5"
VIDEO_LIBRARY_FORBIDDEN_SOURCE_FIELDS = {
    "videos",
    "media_id",
    "media_ids",
    "media_asset_id",
    "media_asset_ids",
    "media_title",
    "media_titles",
    "binding_title",
    "binding_titles",
    "original_file_name",
    "original_file_names",
    "thumbnail_path",
    "thumbnail_paths",
    "thumbnail_relative_path",
    "thumbnail_relative_paths",
    "stream_path",
    "stream_paths",
    "playback_relative_path",
    "playback_relative_paths",
    "source_relative_path",
    "source_relative_paths",
    "relative_path",
    "relative_paths",
    "upload_status",
    "processing_status",
    "processing_phase",
    "processing_progress",
    "binding_status",
    "duplicate_candidates",
    "duration_seconds",
    "video_codec",
    "audio_codec",
    "playback_mime_type",
    "mime_type",
    "file_size_bytes",
    "width",
    "height",
    "fps",
    "bitrate",
}
ANALYZER_ASSET_ROOT = ROOT / "data" / "seed" / "search" / "es_ik"
ANALYZER_ASSET_FILES = [
    ("manifest", ANALYZER_ASSET_ROOT / "manifest.json"),
    ("ik_config", ANALYZER_ASSET_ROOT / "analysis-ik" / "IKAnalyzer.cfg.xml"),
    ("hit_stopwords", ANALYZER_ASSET_ROOT / "analysis-ik" / "custom" / "hit_stopwords.dic"),
    ("project_chemistry_stopwords", ANALYZER_ASSET_ROOT / "analysis-ik" / "custom" / "project_chemistry_stopwords.dic"),
    ("chemistry_custom", ANALYZER_ASSET_ROOT / "analysis-ik" / "custom" / "chemistry_custom.dic"),
    ("es_stopwords", ANALYZER_ASSET_ROOT / "analysis" / "chemistry_stopwords.txt"),
    ("chemistry_synonyms", ANALYZER_ASSET_ROOT / "analysis" / "chemistry_synonyms.txt"),
]


def _json_default(value: Any) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def _json_bytes(value: Any, *, sort_keys: bool = True) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=sort_keys, default=_json_default).encode("utf-8")


def document_hash(document: dict[str, Any]) -> str:
    return hashlib.sha256(_json_bytes(document)).hexdigest()


def forbidden_video_library_document_violations(document: dict[str, Any]) -> list[str]:
    violations: list[str] = []

    def visit(value: Any, path: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}" if path else str(key)
                if key in VIDEO_LIBRARY_FORBIDDEN_SOURCE_FIELDS:
                    violations.append(child_path)
                visit(child, child_path)
        elif isinstance(value, list):
            for index, child in enumerate(value):
                visit(child, f"{path}[{index}]")

    visit(document, "")
    return violations


def _asset_sha256(path: Any) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def video_library_analyzer_assets() -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    missing: list[str] = []
    total_lines = 0
    for asset_id, path in ANALYZER_ASSET_FILES:
        relative_path = path.relative_to(ROOT).as_posix()
        if not path.exists():
            missing.append(relative_path)
            files.append({"id": asset_id, "path": relative_path, "exists": False})
            continue
        line_count = 0
        if path.suffix in {".dic", ".txt"}:
            line_count = sum(1 for line in path.read_text(encoding="utf-8-sig").splitlines() if line.strip())
            total_lines += line_count
        files.append(
            {
                "id": asset_id,
                "path": relative_path,
                "exists": True,
                "size_bytes": path.stat().st_size,
                "sha256": _asset_sha256(path),
                "line_count": line_count if path.suffix in {".dic", ".txt"} else None,
            }
        )
    return {
        "root": ANALYZER_ASSET_ROOT.relative_to(ROOT).as_posix(),
        "ok": not missing,
        "missing": missing,
        "total_dictionary_lines": total_lines,
        "files": files,
    }


def video_library_index_mapping(
    *,
    analyzer: str = "ik_max_word",
    search_tokenizer: str = "ik_smart",
    search_analyzer: str = "chemistry_ik_search",
) -> dict[str, Any]:
    return {
        "settings": {
            "analysis": {
                "filter": {
                    "chemistry_stop": {
                        "type": "stop",
                        "ignore_case": True,
                        "stopwords_path": "analysis/chemistry_stopwords.txt",
                    },
                    "chemistry_synonyms": {
                        "type": "synonym_graph",
                        "lenient": True,
                        "synonyms_path": "analysis/chemistry_synonyms.txt",
                        "updateable": True,
                    },
                },
                "analyzer": {
                    "chemistry_ik": {
                        "type": "custom",
                        "tokenizer": analyzer,
                        "filter": ["lowercase", "chemistry_stop"],
                    },
                    "chemistry_ik_search": {
                        "type": "custom",
                        "tokenizer": search_tokenizer,
                        "filter": ["lowercase", "chemistry_synonyms", "chemistry_stop"],
                    },
                },
                "normalizer": {
                    "chemistry_keyword": {
                        "type": "custom",
                        "filter": ["lowercase"],
                    }
                },
            }
        },
        "mappings": {
            "_meta": {
                "mapping_version": VIDEO_LIBRARY_INDEX_MAPPING_VERSION,
                "retrieval_model": "point-placement-with-chemistry-facets-video-readiness-only",
                "forbidden_video_resource_fields": sorted(VIDEO_LIBRARY_FORBIDDEN_SOURCE_FIELDS),
            },
            "dynamic": "false",
            "properties": {
                "id": {"type": "keyword"},
                "result_type": {"type": "keyword"},
                "node_id": {"type": "keyword"},
                "placement_node_id": {"type": "keyword"},
                "canonical_point_id": {"type": "keyword"},
                "chapter_id": {"type": "keyword"},
                "chapter_ids": {"type": "keyword"},
                "chapter_path": {"type": "text", "analyzer": "chemistry_ik", "search_analyzer": search_analyzer},
                "catalog_path": {"type": "text", "analyzer": "chemistry_ik", "search_analyzer": search_analyzer},
                "category_text": {"type": "text", "analyzer": "chemistry_ik", "search_analyzer": search_analyzer},
                "title": {"type": "text", "analyzer": "chemistry_ik", "search_analyzer": search_analyzer},
                "subtitle": {"type": "text", "analyzer": "chemistry_ik", "search_analyzer": search_analyzer},
                "snippet": {"type": "text", "analyzer": "chemistry_ik", "search_analyzer": search_analyzer},
                "search_text": {"type": "text", "analyzer": "chemistry_ik", "search_analyzer": search_analyzer},
                "principle": {"type": "text", "analyzer": "chemistry_ik", "search_analyzer": search_analyzer},
                "phenomenon_explanation": {"type": "text", "analyzer": "chemistry_ik", "search_analyzer": search_analyzer},
                "safety_note": {"type": "text", "analyzer": "chemistry_ik", "search_analyzer": search_analyzer},
                "related_text": {"type": "text", "analyzer": "chemistry_ik", "search_analyzer": search_analyzer},
                "formulae": {"type": "keyword", "normalizer": "chemistry_keyword"},
                "title_formulae": {"type": "keyword", "normalizer": "chemistry_keyword"},
                "title_formula_pairs": {"type": "keyword", "normalizer": "chemistry_keyword"},
                "aliases": {
                    "type": "text",
                    "analyzer": "chemistry_ik",
                    "search_analyzer": search_analyzer,
                    "fields": {"keyword": {"type": "keyword", "normalizer": "chemistry_keyword"}},
                },
                "strict_aliases": {"type": "keyword", "normalizer": "chemistry_keyword"},
                "reactants": {"type": "keyword", "normalizer": "chemistry_keyword"},
                "products": {"type": "keyword", "normalizer": "chemistry_keyword"},
                "participants": {"type": "keyword", "normalizer": "chemistry_keyword"},
                "equation_formula_pairs": {"type": "keyword", "normalizer": "chemistry_keyword"},
                "equation_rows": {"type": "text", "analyzer": "chemistry_ik", "search_analyzer": search_analyzer},
                "annotation_formulae": {"type": "keyword", "normalizer": "chemistry_keyword"},
                "annotation_aliases": {"type": "keyword", "normalizer": "chemistry_keyword"},
                "reagent_aliases": {
                    "type": "text",
                    "analyzer": "chemistry_ik",
                    "search_analyzer": search_analyzer,
                    "fields": {"keyword": {"type": "keyword", "normalizer": "chemistry_keyword"}},
                },
                "reaction_features": {"type": "keyword"},
                "condition_tags": {"type": "keyword", "normalizer": "chemistry_keyword"},
                "phenomenon_tags": {"type": "keyword", "normalizer": "chemistry_keyword"},
                "property_tags": {"type": "keyword", "normalizer": "chemistry_keyword"},
                "has_video": {"type": "boolean"},
                "video_count": {"type": "integer"},
                "target": {"type": "object", "enabled": True},
                "badges": {"type": "keyword"},
                "updated_at": {"type": "date"},
            },
        },
    }


class VideoLibraryIndexClient:
    def __init__(self, *, base_url: str, index: str, timeout: float = 3.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.index = index
        self.timeout = timeout

    def request(self, method: str, path: str, payload: Any | None = None) -> Any:
        data = None if payload is None else _json_bytes(payload, sort_keys=False)
        request = urllib.request.Request(
            f"{self.base_url}{path}",
            data=data,
            headers={"Content-Type": "application/json"},
            method=method,
        )
        with urllib.request.urlopen(request, timeout=self.timeout) as response:
            body = response.read().decode("utf-8")
        return json.loads(body) if body else {}

    def health(self) -> dict[str, Any]:
        return self.request("GET", "/_cluster/health")

    def ensure_index(self, *, recreate: bool = False, analyzer: str = "ik_max_word") -> None:
        if recreate:
            try:
                self.request("DELETE", f"/{self.index}")
            except urllib.error.HTTPError as exc:
                if exc.code != 404:
                    raise
        try:
            self.request("HEAD", f"/{self.index}")
            return
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
        self.request("PUT", f"/{self.index}", video_library_index_mapping(analyzer=analyzer))

    def upsert_document(self, document: dict[str, Any]) -> None:
        self.request("PUT", f"/{self.index}/_doc/{document['id']}", document)

    def delete_document(self, document_id: str) -> None:
        try:
            self.request("DELETE", f"/{self.index}/_doc/{document_id}")
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise


def configured_index_client() -> VideoLibraryIndexClient | None:
    settings = get_settings()
    if settings.video_library_search_backend != "elasticsearch" or not settings.video_library_search_url:
        return None
    return VideoLibraryIndexClient(
        base_url=settings.video_library_search_url,
        index=settings.video_library_search_index,
        timeout=settings.video_library_search_timeout_seconds,
    )


def video_library_index_diagnostics() -> dict[str, Any]:
    settings = get_settings()
    with db_session() as session:
        status_rows = session.execute(
            text(
                """
                SELECT sync_status, COUNT(*) AS count
                FROM experiment_catalog_point_search_index_state
                GROUP BY sync_status
                """
            )
        ).mappings().all()
        published_point_count = int(
            session.execute(
            text("SELECT COUNT(*) FROM experiment_catalog_point_content WHERE content_status = 'published'")
            ).scalar_one()
            or 0
        )
        failed_rows = [
            dict(row)
            for row in session.execute(
                text(
                    """
                    SELECT node_id, document_id, desired_action, sync_status,
                           attempts, last_error, updated_at
                    FROM experiment_catalog_point_search_index_state
                    WHERE sync_status IN ('failed', 'pending')
                    ORDER BY updated_at DESC
                    LIMIT 20
                    """
                )
            ).mappings().all()
        ]
    client = configured_index_client()
    es: dict[str, Any] = {"configured": client is not None}
    if client is not None:
        try:
            es["health"] = client.health()
            count_payload = client.request("GET", f"/{client.index}/_count")
            es["document_count"] = count_payload.get("count")
            mapping_payload = client.request("GET", f"/{client.index}/_mapping")
            mapping = mapping_payload.get(client.index, {}).get("mappings", {})
            properties = mapping.get("properties", {})
            es["mapping"] = {
                "version": (mapping.get("_meta") or {}).get("mapping_version"),
                "desired_version": VIDEO_LIBRARY_INDEX_MAPPING_VERSION,
                "field_count": len(properties),
                "chemistry_fields_present": {
                    field: field in properties
                    for field in [
                        "formulae",
                        "title_formulae",
                        "title_formula_pairs",
                        "aliases",
                        "reactants",
                        "products",
                        "participants",
                        "equation_formula_pairs",
                        "equation_rows",
                        "reagent_aliases",
                        "condition_tags",
                        "phenomenon_tags",
                        "property_tags",
                    ]
                },
            }
        except Exception as exc:  # noqa: BLE001 - diagnostics should be best-effort.
            es["error"] = str(exc)
    return {
        "settings": {
            "enabled": settings.video_library_search_enabled,
            "backend": settings.video_library_search_backend,
            "index": settings.video_library_search_index,
            "desired_mapping_version": VIDEO_LIBRARY_INDEX_MAPPING_VERSION,
            "analyzer": settings.video_library_search_analyzer,
            "local_fallback": settings.video_library_search_local_fallback,
            "analyzer_assets": video_library_analyzer_assets(),
            "dictionary_assets": chemistry_vocabulary_metadata(),
        },
        "postgres": {
            "published_point_content_count": published_point_count,
            "sync_status_counts": {str(row["sync_status"]): int(row["count"]) for row in status_rows},
            "retryable_rows": failed_rows,
        },
        "elasticsearch": es,
    }


def mark_index_sync_success(*, node_id: str, document_id: str, payload_hash: str) -> None:
    with db_session() as session:
        row = session.execute(
            text("SELECT canonical_point_id FROM experiment_catalog_nodes WHERE id = :node_id"),
            {"node_id": node_id},
        ).mappings().first()
        canonical_point_id = str(row["canonical_point_id"]) if row and row.get("canonical_point_id") else None
        session.execute(
            text(
                """
                INSERT INTO experiment_catalog_point_search_index_state (
                  node_id, placement_node_id, canonical_point_id, document_id, desired_action, sync_status,
                  attempts, document_hash, last_error, indexed_at, last_attempted_at, updated_at
                )
                VALUES (
                  :node_id, :node_id, :canonical_point_id, :document_id, 'upsert', 'synced',
                  1, :document_hash, NULL, now(), now(), now()
                )
                ON CONFLICT (node_id) DO UPDATE SET
                  placement_node_id = EXCLUDED.placement_node_id,
                  canonical_point_id = EXCLUDED.canonical_point_id,
                  document_id = EXCLUDED.document_id,
                  sync_status = 'synced',
                  attempts = experiment_catalog_point_search_index_state.attempts + 1,
                  document_hash = EXCLUDED.document_hash,
                  last_error = NULL,
                  indexed_at = now(),
                  last_attempted_at = now(),
                  updated_at = now()
                """
            ),
            {
                "node_id": node_id,
                "canonical_point_id": canonical_point_id,
                "document_id": document_id,
                "document_hash": payload_hash,
            },
        )


def mark_index_sync_failure(*, node_id: str, document_id: str, action: str, error: str) -> None:
    with db_session() as session:
        row = session.execute(
            text("SELECT canonical_point_id FROM experiment_catalog_nodes WHERE id = :node_id"),
            {"node_id": node_id},
        ).mappings().first()
        canonical_point_id = str(row["canonical_point_id"]) if row and row.get("canonical_point_id") else None
        session.execute(
            text(
                """
                INSERT INTO experiment_catalog_point_search_index_state (
                  node_id, placement_node_id, canonical_point_id, document_id, desired_action, sync_status,
                  attempts, last_error, last_attempted_at, updated_at
                )
                VALUES (
                  :node_id, :node_id, :canonical_point_id, :document_id, :action, 'failed',
                  1, :error, now(), now()
                )
                ON CONFLICT (node_id) DO UPDATE SET
                  placement_node_id = EXCLUDED.placement_node_id,
                  canonical_point_id = EXCLUDED.canonical_point_id,
                  document_id = EXCLUDED.document_id,
                  desired_action = EXCLUDED.desired_action,
                  sync_status = 'failed',
                  attempts = experiment_catalog_point_search_index_state.attempts + 1,
                  last_error = EXCLUDED.last_error,
                  last_attempted_at = now(),
                  updated_at = now()
                """
            ),
            {
                "node_id": node_id,
                "canonical_point_id": canonical_point_id,
                "document_id": document_id,
                "action": action,
                "error": error[:1000],
            },
        )
