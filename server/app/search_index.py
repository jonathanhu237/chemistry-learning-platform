from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from datetime import date, datetime
from typing import Any

from server.app.infrastructure.settings import ROOT


ANALYZER_ASSET_ROOT = ROOT / "data" / "seed" / "search" / "es_ik"
ANALYZER_ASSET_FILES = [
    ("manifest", ANALYZER_ASSET_ROOT / "manifest.json"),
    ("ik_config", ANALYZER_ASSET_ROOT / "analysis-ik" / "IKAnalyzer.cfg.xml"),
    ("hit_stopwords", ANALYZER_ASSET_ROOT / "analysis-ik" / "custom" / "hit_stopwords.dic"),
    (
        "project_chemistry_stopwords",
        ANALYZER_ASSET_ROOT / "analysis-ik" / "custom" / "project_chemistry_stopwords.dic",
    ),
    ("chemistry_custom", ANALYZER_ASSET_ROOT / "analysis-ik" / "custom" / "chemistry_custom.dic"),
    ("es_stopwords", ANALYZER_ASSET_ROOT / "analysis" / "chemistry_stopwords.txt"),
    ("chemistry_synonyms", ANALYZER_ASSET_ROOT / "analysis" / "chemistry_synonyms.txt"),
]


def _json_default(value: Any) -> str:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def _json_bytes(value: Any, *, sort_keys: bool = True) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=sort_keys,
        default=_json_default,
    ).encode("utf-8")


def document_hash(document: dict[str, Any]) -> str:
    return hashlib.sha256(_json_bytes(document)).hexdigest()


def _asset_sha256(path: Any) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def chemistry_analyzer_assets() -> dict[str, Any]:
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
            line_count = sum(
                1
                for line in path.read_text(encoding="utf-8-sig").splitlines()
                if line.strip()
            )
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


class SearchIndexClient:
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

    def upsert_document(self, document: dict[str, Any]) -> None:
        self.request("PUT", f"/{self.index}/_doc/{document['id']}", document)

    def delete_document(self, document_id: str) -> None:
        try:
            self.request("DELETE", f"/{self.index}/_doc/{document_id}")
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
