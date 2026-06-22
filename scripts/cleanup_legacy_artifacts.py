from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.validate_production_resources import MANIFEST_PATH, validate_manifest

DEFAULT_REPORT = ROOT / "data" / "seed" / "manifests" / "legacy_cleanup_plan.json"

TARGETS = [
    {
        "path": "artifacts/point-aware-question-bank",
        "category": "historical_question_bank_review",
        "reason": "Retired experiment_id + point_key question-bank review artifacts are no longer production seed.",
    },
    {
        "path": "artifacts/point-aware-question-demo",
        "category": "historical_question_bank_demo",
        "reason": "Demo artifact is not part of the current production seed.",
    },
    {
        "path": "artifacts/video-point-default-evidence",
        "category": "historical_point_evidence_generation",
        "reason": "Retired video-point evidence generation used old experiment_id + point_key identity.",
    },
    {
        "path": "data/seed/experiment_points",
        "category": "retired_legacy_point_seed",
        "reason": "The current catalog seed uses experiment_catalog/catalog_tree.json and no longer protects the 300 old point inventory.",
    },
    {
        "path": "data/seed/question_bank",
        "category": "retired_legacy_question_bank_seed",
        "reason": "The current baseline intentionally keeps experiment question banks empty until catalog-node evidence is regenerated.",
    },
    {
        "path": "data/seed/point_evidence",
        "category": "retired_legacy_point_evidence_seed",
        "reason": "Old point-to-chunk bindings are invalid; canonical chunks and embeddings remain protected separately.",
    },
    {
        "path": "artifacts/playwright",
        "category": "generated_ui_verification_output",
        "reason": "Playwright screenshots are generated verification output.",
    },
    {
        "path": "artifacts/experiment_knowledge_framework_import_report.json",
        "category": "historical_import_report_copy",
        "reason": "Current import report is protected in data/seed/import_reports.",
    },
    {
        "path": ".tmp",
        "category": "local_temporary_output",
        "reason": "Temporary validation and scratch output.",
    },
    {
        "path": "logs",
        "category": "local_logs",
        "reason": "Local runtime logs are not production seed resources.",
    },
    {
        "path": ".pytest_cache",
        "category": "test_cache",
        "reason": "Pytest cache is generated locally.",
    },
    {
        "path": "apps/web-teacher/dist",
        "category": "frontend_build_output",
        "reason": "Vite build output is reproducible.",
    },
    {
        "path": "apps/web-teacher/node_modules",
        "category": "frontend_dependency_directory",
        "reason": "Dependencies are restored from package-lock.json.",
    },
]

GLOB_TARGETS = [
    {
        "pattern": "artifacts/*.png",
        "category": "generated_ui_screenshot",
        "reason": "Root artifact screenshots are generated verification output.",
    },
    {
        "pattern": "apps/web-teacher/*.log",
        "category": "frontend_dev_server_log",
        "reason": "Vite dev-server logs are generated locally.",
    },
    {
        "pattern": "**/__pycache__",
        "category": "python_bytecode_cache",
        "reason": "Python bytecode caches are generated locally.",
    },
]


def _safe_relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _resolve_repo_path(path: str) -> Path:
    resolved = (ROOT / path).resolve()
    try:
        resolved.relative_to(ROOT)
    except ValueError as exc:
        raise ValueError(f"Refusing cleanup target outside repo: {path}") from exc
    return resolved


def _protected_paths(manifest_path: Path) -> list[Path]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    paths: list[Path] = []
    for entry in manifest.get("resources") or []:
        resource_path = (ROOT / entry["path"]).resolve()
        paths.append(resource_path)
    return paths


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _assert_not_protected(target: Path, protected_paths: list[Path]) -> None:
    for protected in protected_paths:
        if target == protected or _is_relative_to(protected, target):
            raise ValueError(f"Refusing to delete protected resource {protected} via target {target}")


def _measure(path: Path) -> tuple[int, int]:
    if not path.exists():
        return 0, 0
    if path.is_file() or path.is_symlink():
        return 1, path.stat().st_size
    file_count = 0
    size_bytes = 0
    for child in path.rglob("*"):
        if child.is_file() or child.is_symlink():
            file_count += 1
            size_bytes += child.stat().st_size
    return file_count, size_bytes


def _target_entry(path: Path, *, category: str, reason: str, source: str) -> dict[str, Any]:
    exists = path.exists()
    file_count, size_bytes = _measure(path)
    return {
        "path": _safe_relative(path),
        "source": source,
        "category": category,
        "reason": reason,
        "exists": exists,
        "kind": "directory" if exists and path.is_dir() and not path.is_symlink() else "file",
        "file_count": file_count,
        "size_bytes": size_bytes,
        "action": "delete" if exists else "skip_missing",
    }


def build_plan(manifest_path: Path = MANIFEST_PATH) -> dict[str, Any]:
    validation = validate_manifest(manifest_path)
    if not validation["ok"]:
        raise ValueError("Protected resources are invalid:\n" + "\n".join(validation["errors"]))
    protected = _protected_paths(manifest_path)
    entries: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for target in TARGETS:
        path = _resolve_repo_path(str(target["path"]))
        _assert_not_protected(path, protected)
        entries.append(
            _target_entry(
                path,
                category=str(target["category"]),
                reason=str(target["reason"]),
                source="target",
            )
        )
        seen.add(path)
    for target in GLOB_TARGETS:
        for path in sorted(ROOT.glob(str(target["pattern"]))):
            resolved = path.resolve()
            if resolved in seen:
                continue
            _assert_not_protected(resolved, protected)
            entries.append(
                _target_entry(
                    resolved,
                    category=str(target["category"]),
                    reason=str(target["reason"]),
                    source=str(target["pattern"]),
                )
            )
            seen.add(resolved)
    existing = [entry for entry in entries if entry["exists"]]
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "manifest": _safe_relative(manifest_path.resolve()),
        "mode": "dry_run",
        "media_cleanup": {
            "path": "data/media",
            "action": "requires_explicit_database_ui_consistency_plan",
            "reason": "media_assets rows can point to local files, so media deletion is not automatic.",
        },
        "summary": {
            "target_count": len(entries),
            "existing_target_count": len(existing),
            "delete_file_count": sum(int(entry["file_count"]) for entry in existing),
            "delete_size_bytes": sum(int(entry["size_bytes"]) for entry in existing),
        },
        "targets": entries,
    }


def apply_plan(plan: dict[str, Any]) -> None:
    for entry in plan["targets"]:
        if entry["action"] != "delete":
            continue
        path = _resolve_repo_path(str(entry["path"]))
        if not path.exists():
            continue
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        else:
            path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description="Dry-run or apply guarded cleanup of legacy artifacts.")
    parser.add_argument("--apply", action="store_true", help="Delete the planned legacy targets.")
    parser.add_argument("--manifest", type=Path, default=MANIFEST_PATH)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    plan = build_plan(args.manifest)
    if args.apply:
        apply_plan(plan)
        plan["mode"] = "applied"
        plan["applied_at"] = datetime.now(timezone.utc).isoformat()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    sys.stdout.buffer.write((json.dumps(plan["summary"], ensure_ascii=False, indent=2) + "\n").encode("utf-8"))


if __name__ == "__main__":
    main()
