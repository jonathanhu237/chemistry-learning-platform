from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.app.infrastructure.settings import get_settings
from server.app.domains.media.lifecycle import media_cleanup_dry_run


def _format_bytes(value: int) -> str:
    size = float(value)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} B"
        size /= 1024
    return f"{value} B"


def _safe_orphan_path(relative_path: str) -> Path:
    root = get_settings().media_root.resolve()
    path = (root / relative_path).resolve()
    if root != path and root not in path.parents:
        raise RuntimeError(f"Refusing path outside media root: {relative_path}")
    return path


def _print_summary(plan: dict[str, Any]) -> None:
    print("Media lifecycle cleanup dry run")
    print(f"- media_root: {plan['media_root']}")
    print(f"- assets inspected: {plan['asset_count']} (limit {plan['asset_limit']})")
    print(f"- referenced paths: {plan['referenced_path_count']}")
    print(f"- orphan files: {plan['orphan_file_count']} ({_format_bytes(plan['orphan_file_bytes'])})")
    actions: dict[str, int] = {}
    for asset in plan["assets"]:
        actions[asset["action"]] = actions.get(asset["action"], 0) + 1
    for action, count in sorted(actions.items()):
        print(f"- {action}: {count}")
    if plan["orphan_files"]:
        print("\nFirst orphan files:")
        for item in plan["orphan_files"][:20]:
            print(f"- {item['relative_path']} ({_format_bytes(item['file_size_bytes'])})")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect and safely clean local media lifecycle files.")
    parser.add_argument("--limit", type=int, default=500, help="Maximum media assets to inspect.")
    parser.add_argument("--orphan-limit", type=int, default=200, help="Maximum orphan files to include in output.")
    parser.add_argument("--json", action="store_true", help="Print the plan as JSON.")
    parser.add_argument("--delete-orphans", action="store_true", help="Delete files not referenced by media DB rows.")
    parser.add_argument(
        "--delete-asset-files",
        action="store_true",
        help="Delete files for archived or tombstoned DB-backed media assets only.",
    )
    args = parser.parse_args()

    plan = media_cleanup_dry_run(limit=args.limit, orphan_limit=args.orphan_limit)
    deleted: list[str] = []
    deleted_asset_files: list[str] = []
    refused_asset_files: list[str] = []
    if args.delete_asset_files:
        for asset in plan["assets"]:
            if asset.get("lifecycle_status") not in {"archived", "tombstoned"}:
                if asset.get("media_files"):
                    refused_asset_files.append(str(asset["id"]))
                continue
            for media_file in asset.get("media_files") or []:
                relative_path = str(media_file.get("relative_path") or "")
                if not relative_path:
                    continue
                path = _safe_orphan_path(relative_path)
                if path.is_file():
                    path.unlink()
                    deleted_asset_files.append(relative_path)
        plan["deleted_asset_files"] = deleted_asset_files
        plan["refused_active_asset_file_asset_ids"] = refused_asset_files
    if args.delete_orphans:
        for item in plan["orphan_files"]:
            path = _safe_orphan_path(str(item["relative_path"]))
            if path.is_file():
                path.unlink()
                deleted.append(str(item["relative_path"]))
        plan["deleted_orphans"] = deleted
    if args.json:
        print(json.dumps(plan, ensure_ascii=False, indent=2, default=str))
    else:
        _print_summary(plan)
        if deleted:
            print(f"\nDeleted orphan files: {len(deleted)}")
        if deleted_asset_files:
            print(f"\nDeleted archived asset files: {len(deleted_asset_files)}")
        if refused_asset_files:
            print(f"\nRefused active DB-backed asset file deletion: {len(refused_asset_files)} assets")


if __name__ == "__main__":
    main()
