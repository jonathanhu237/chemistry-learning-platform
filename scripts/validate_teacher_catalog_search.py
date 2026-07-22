from __future__ import annotations

import json
import sys
import urllib.error
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.app.domains.catalog_tree.teacher_search import (
    TEACHER_CATALOG_SEARCH_INDEX_MAPPING_VERSION,
    configured_teacher_search_client,
    teacher_catalog_search_index_mapping,
)
from server.app.chemistry_search import chemistry_vocabulary_metadata
from server.app.infrastructure.settings import get_settings
from server.app.search_index import chemistry_analyzer_assets


def _token_list(payload: object) -> list[str]:
    if not isinstance(payload, dict):
        return []
    return [str(item.get("token") or "") for item in payload.get("tokens", []) if isinstance(item, dict)]


def main() -> None:
    settings = get_settings()
    mapping = teacher_catalog_search_index_mapping(analyzer=settings.teacher_catalog_search_analyzer)
    properties = mapping["mappings"]["properties"]
    required_fields = [
        "node_kind",
        "teacher_note",
        "point_teacher_note",
        "legacy_text",
        "formulae",
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
        "primary_state",
        "missing_field_keys",
    ]
    assets = chemistry_analyzer_assets()
    vocabulary = chemistry_vocabulary_metadata()
    missing_fields = [field for field in required_fields if field not in properties]
    errors: list[str] = []
    if missing_fields:
        errors.append(f"Teacher catalog mapping is missing fields: {', '.join(missing_fields)}")
    if not assets.get("ok"):
        errors.append("Required ES/IK chemistry analyzer assets are missing")
    if not vocabulary.get("version"):
        errors.append("Chemistry search vocabulary metadata is missing a version")
    if mapping["mappings"]["_meta"]["mapping_version"] != TEACHER_CATALOG_SEARCH_INDEX_MAPPING_VERSION:
        errors.append("Teacher catalog mapping version does not match the declared version")

    production_required = settings.is_production and settings.teacher_catalog_search_enabled
    if production_required and settings.teacher_catalog_search_backend != "elasticsearch":
        errors.append("TEACHER_CATALOG_SEARCH_BACKEND must be elasticsearch in production")
    if production_required and not settings.teacher_catalog_search_url:
        errors.append("TEACHER_CATALOG_SEARCH_URL is required in production")
    if production_required and settings.teacher_catalog_search_local_fallback:
        errors.append("TEACHER_CATALOG_SEARCH_LOCAL_FALLBACK must be false in production")

    elasticsearch: dict[str, object] = {"configured": False}
    client = configured_teacher_search_client()
    if client is not None:
        elasticsearch["configured"] = True
        try:
            elasticsearch["health"] = client.health()
            mapping_payload = client.request("GET", f"/{client.index}/_mapping")
            settings_payload = client.request("GET", f"/{client.index}/_settings")
            current_mapping = mapping_payload.get(client.index, {}).get("mappings", {})
            current_version = (current_mapping.get("_meta") or {}).get("mapping_version")
            analysis = settings_payload.get(client.index, {}).get("settings", {}).get("index", {}).get("analysis", {})
            analyzers = analysis.get("analyzer", {})
            filters = analysis.get("filter", {})
            elasticsearch.update(
                {
                    "mapping_version": current_version,
                    "desired_mapping_version": TEACHER_CATALOG_SEARCH_INDEX_MAPPING_VERSION,
                    "index_analyzers": sorted(analyzers),
                    "index_filters": sorted(filters),
                }
            )
            if production_required and current_version != TEACHER_CATALOG_SEARCH_INDEX_MAPPING_VERSION:
                errors.append("Teacher catalog index mapping is stale; rebuild the teacher catalog search index")
            for analyzer in ("chemistry_ik", "chemistry_ik_search"):
                if production_required and analyzer not in analyzers:
                    errors.append(f"Teacher catalog index is missing {analyzer} analyzer")
            for filter_name in ("chemistry_stop", "chemistry_synonyms"):
                if production_required and filter_name not in filters:
                    errors.append(f"Teacher catalog index is missing {filter_name} filter")
            analyzed = client.request(
                "POST",
                f"/{client.index}/_analyze",
                {"analyzer": "chemistry_ik_search", "text": "HCl 盐酸 的 硫代硫酸钠 生成 二氧化硫"},
            )
            tokens = _token_list(analyzed)
            elasticsearch["analyzer_smoke_tokens"] = tokens[:30]
            if production_required and "的" in set(tokens):
                errors.append("chemistry_ik_search did not filter the expected stopword")
            if production_required and not ({"盐酸", "硫代硫酸钠", "二氧化硫"} & set(tokens)):
                errors.append("chemistry_ik_search did not emit expected chemistry tokens")
        except urllib.error.HTTPError as exc:
            elasticsearch["error"] = f"HTTP {exc.code}"
            if production_required:
                errors.append(f"Teacher catalog Elasticsearch index is unavailable: HTTP {exc.code}")
        except Exception as exc:  # noqa: BLE001 - readiness returns actionable diagnostics.
            elasticsearch["error"] = str(exc)
            if production_required:
                errors.append(f"Teacher catalog Elasticsearch health check failed: {exc}")
    elif production_required:
        errors.append("Teacher catalog Elasticsearch client is not configured")

    payload = {
        "ok": not errors,
        "errors": errors,
        "mapping_version": mapping["mappings"]["_meta"]["mapping_version"],
        "index": settings.teacher_catalog_search_index,
        "missing_fields": missing_fields,
        "analyzer_assets": assets,
        "dictionary_assets": vocabulary,
        "elasticsearch": elasticsearch,
    }
    sys.stdout.buffer.write((json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n").encode("utf-8"))
    if not payload["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
