from __future__ import annotations

import json
import sys
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.app.infrastructure.settings import get_settings
from server.app.domains.video_library.index_client import configured_index_client, video_library_analyzer_assets


def _token_list(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return []
    return [str(item.get("token", "")) for item in payload.get("tokens", []) if isinstance(item, dict)]


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
            if required and "chemistry_ik" not in analyzer_settings:
                errors.append("Video-library index is missing chemistry_ik analyzer; run scripts/rebuild_video_library_index.py --recreate")
            if required and "chemistry_ik_search" not in analyzer_settings:
                errors.append("Video-library index is missing chemistry_ik_search analyzer; run scripts/rebuild_video_library_index.py --recreate")
            if required and "chemistry_stop" not in filter_settings:
                errors.append("Video-library index is missing chemistry_stop filter; run scripts/rebuild_video_library_index.py --recreate")
            if required and "chemistry_synonyms" not in filter_settings:
                errors.append("Video-library index is missing chemistry_synonyms filter; run scripts/rebuild_video_library_index.py --recreate")
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
