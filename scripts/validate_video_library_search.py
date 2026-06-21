from __future__ import annotations

import json
import sys
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.app.infrastructure.settings import get_settings
from server.app.infrastructure.database import db_session
from server.app.domains.video_library.index_client import (
    VIDEO_LIBRARY_INDEX_MAPPING_VERSION,
    configured_index_client,
    forbidden_video_library_document_violations,
    video_library_analyzer_assets,
)
from server.app.domains.video_library.search import _build_documents, _learning_profiles, _load_published_point_rows


def _token_list(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return []
    return [str(item.get("token", "")) for item in payload.get("tokens", []) if isinstance(item, dict)]


def _first_query_token(value: object) -> str:
    text = str(value or "").strip()
    for token in text.replace("/", " ").replace(",", " ").split():
        candidate = token.strip()
        if len(candidate) >= 2:
            return candidate
    return text[:32]


def main() -> None:
    settings = get_settings()
    errors: list[str] = []
    details: dict[str, object] = {
        "enabled": settings.video_library_search_enabled,
        "backend": settings.video_library_search_backend,
        "url": settings.video_library_search_url,
        "index": settings.video_library_search_index,
        "analyzer": settings.video_library_search_analyzer,
        "local_fallback": settings.video_library_search_local_fallback,
        "production": settings.is_production,
        "analyzer_assets": video_library_analyzer_assets(),
    }
    required = settings.is_production and settings.video_library_search_enabled and settings.video_library_search_require_es_in_production
    assets = details["analyzer_assets"]
    if required and (not isinstance(assets, dict) or not assets.get("ok")):
        errors.append("Required ES/IK analyzer dictionary assets are missing from the backend image")
    if required and settings.video_library_search_backend != "elasticsearch":
        errors.append("VIDEO_LIBRARY_SEARCH_BACKEND must be elasticsearch in production")
    if required and not settings.video_library_search_url:
        errors.append("VIDEO_LIBRARY_SEARCH_URL is required in production")
    if required and settings.video_library_search_local_fallback:
        errors.append("VIDEO_LIBRARY_SEARCH_LOCAL_FALLBACK must be false in production")
    try:
        with db_session() as session:
            point_rows = _load_published_point_rows(session)
        generated_payloads = [
            document.index_source
            for document in _build_documents([], _learning_profiles(), point_rows=point_rows)
            if document.index_source
        ]
        generated_violations = [
            {"id": payload.get("id"), "violations": violations}
            for payload in generated_payloads
            if (violations := forbidden_video_library_document_violations(payload))
        ]
        details["generated_document_purity"] = {
            "document_count": len(generated_payloads),
            "violation_count": len(generated_violations),
            "violations": generated_violations[:20],
        }
        if generated_violations:
            errors.append("Generated video-library documents contain forbidden video resource fields")
    except Exception as exc:  # noqa: BLE001 - readiness should report DB/generator failures without hiding ES checks.
        details["generated_document_purity_error"] = str(exc)
        if required:
            errors.append(f"Generated video-library document purity check failed: {exc}")
    client = configured_index_client()
    if client is None:
        result = {"ok": not errors and not required, "errors": errors, "details": details}
        sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        if not result["ok"]:
            raise SystemExit(1)
        return
    try:
        details["health"] = client.health()
        try:
            mapping = client.request("GET", f"/{client.index}/_mapping")
            settings_payload = client.request("GET", f"/{client.index}/_settings")
            details["index_exists"] = client.index in mapping
            analyzer_settings = (
                settings_payload.get(client.index, {})
                .get("settings", {})
                .get("index", {})
                .get("analysis", {})
                .get("analyzer", {})
            )
            filter_settings = (
                settings_payload.get(client.index, {})
                .get("settings", {})
                .get("index", {})
                .get("analysis", {})
                .get("filter", {})
            )
            details["index_analyzers"] = sorted(analyzer_settings)
            details["index_filters"] = sorted(filter_settings)
            index_mapping = mapping.get(client.index, {}).get("mappings", {}) if isinstance(mapping, dict) else {}
            mapping_version = (index_mapping.get("_meta") or {}).get("mapping_version")
            details["mapping_version"] = mapping_version
            details["desired_mapping_version"] = VIDEO_LIBRARY_INDEX_MAPPING_VERSION
            if required and mapping_version != VIDEO_LIBRARY_INDEX_MAPPING_VERSION:
                errors.append(
                    "Video-library index mapping is stale; run scripts/rebuild_video_library_index.py --recreate"
                )
            if required and "chemistry_ik" not in analyzer_settings:
                errors.append("Video-library index is missing chemistry_ik analyzer; run scripts/rebuild_video_library_index.py --recreate")
            if required and "chemistry_ik_search" not in analyzer_settings:
                errors.append("Video-library index is missing chemistry_ik_search analyzer; run scripts/rebuild_video_library_index.py --recreate")
            if required and "chemistry_stop" not in filter_settings:
                errors.append("Video-library index is missing chemistry_stop filter; run scripts/rebuild_video_library_index.py --recreate")
            if required and "chemistry_synonyms" not in filter_settings:
                errors.append("Video-library index is missing chemistry_synonyms filter; run scripts/rebuild_video_library_index.py --recreate")
            try:
                source_scan = client.request(
                    "POST",
                    f"/{client.index}/_search",
                    {
                        "size": 1000,
                        "_source": True,
                        "query": {"match_all": {}},
                    },
                )
                source_hits = source_scan.get("hits", {}).get("hits", []) if isinstance(source_scan, dict) else []
                source_violations = []
                for hit in source_hits:
                    source = hit.get("_source", {}) if isinstance(hit, dict) else {}
                    if not isinstance(source, dict):
                        continue
                    violations = forbidden_video_library_document_violations(source)
                    if violations:
                        source_violations.append({"id": source.get("id") or hit.get("_id"), "violations": violations})
                details["indexed_document_purity"] = {
                    "scanned_count": len(source_hits),
                    "violation_count": len(source_violations),
                    "violations": source_violations[:20],
                }
                if source_violations:
                    errors.append("Indexed video-library documents contain forbidden video resource fields")
            except Exception as exc:  # noqa: BLE001 - readiness should keep reporting other ES checks.
                if required:
                    errors.append(f"Indexed document purity scan failed: {exc}")
                details["indexed_document_purity_error"] = str(exc)
            try:
                analyze_payload = client.request(
                    "POST",
                    f"/{client.index}/_analyze",
                    {
                        "analyzer": "chemistry_ik_search",
                        "text": "HCl 盐酸 的 硫代硫酸钠 生成 二氧化硫",
                    },
                )
                tokens = _token_list(analyze_payload)
                details["analyzer_smoke_tokens"] = tokens[:30]
                token_set = set(tokens)
                if required and "的" in token_set:
                    errors.append("chemistry_ik_search analyzer did not filter HIT stopword '的'")
                if required and not ({"盐酸", "硫代硫酸钠", "二氧化硫"} & token_set):
                    errors.append("chemistry_ik_search analyzer did not emit expected chemistry Chinese tokens")
            except Exception as exc:  # noqa: BLE001 - readiness should report analyzer smoke failures.
                if required:
                    errors.append(f"chemistry_ik_search analyzer smoke failed: {exc}")
                details["analyzer_smoke_error"] = str(exc)
            try:
                category_seed = client.request(
                    "POST",
                    f"/{client.index}/_search",
                    {
                        "size": 1,
                        "_source": ["id", "result_type", "node_id", "category_text"],
                        "query": {"bool": {"filter": [{"exists": {"field": "category_text"}}]}},
                    },
                )
                seed_hits = category_seed.get("hits", {}).get("hits", []) if isinstance(category_seed, dict) else []
                seed_source = seed_hits[0].get("_source", {}) if seed_hits and isinstance(seed_hits[0], dict) else {}
                directory_query = _first_query_token(seed_source.get("category_text"))
                if directory_query:
                    directory_query_payload = client.request(
                        "POST",
                        f"/{client.index}/_search",
                        {
                            "size": 5,
                            "_source": ["id", "result_type", "node_id", "category_text"],
                            "query": {
                                "multi_match": {
                                    "query": directory_query,
                                    "fields": ["category_text^3", "search_text"],
                                }
                            },
                        },
                    )
                    directory_hits = directory_query_payload.get("hits", {}).get("hits", []) if isinstance(directory_query_payload, dict) else []
                    details["directory_query_smoke"] = {
                        "query": directory_query,
                        "hit_count": len(directory_hits),
                        "hits": [hit.get("_source", {}) for hit in directory_hits[:3] if isinstance(hit, dict)],
                    }
                    if required and not directory_hits:
                        errors.append("Directory category text query did not return descendant point results")
                    for hit in directory_hits:
                        source = hit.get("_source", {}) if isinstance(hit, dict) else {}
                        if source.get("result_type") != "video_point" or not source.get("node_id"):
                            errors.append("Directory category text query returned a non-point video-library document")
                            break
                else:
                    details["directory_query_smoke"] = "skipped_no_category_text_documents"
            except Exception as exc:  # noqa: BLE001 - readiness should keep reporting other ES checks.
                if required:
                    errors.append(f"Directory category text query smoke failed: {exc}")
                details["directory_query_smoke_error"] = str(exc)
        except urllib.error.HTTPError as exc:
            if required:
                errors.append(f"Video-library index {client.index!r} is missing or unhealthy: HTTP {exc.code}")
            details["index_error"] = f"HTTP {exc.code}"
    except Exception as exc:  # noqa: BLE001 - readiness validation should produce actionable errors.
        if required:
            errors.append(f"Elasticsearch/IK health check failed: {exc}")
        details["health_error"] = str(exc)
    result = {"ok": not errors, "errors": errors, "details": details}
    sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
