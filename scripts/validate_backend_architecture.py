from __future__ import annotations

import ast
import json
import sys
import tomllib
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = REPO_ROOT / "server" / "app"
ROUTE_INVENTORY = REPO_ROOT / "server" / "tests" / "contracts" / "backend_route_inventory.json"
PYPROJECT = REPO_ROOT / "pyproject.toml"
CANONICAL_FASTAPI_ENTRYPOINT = "server.app.app_runtime.main:app"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

LEGACY_PATHS = [
    APP_ROOT / "media.py",
    APP_ROOT / "main.py",
    APP_ROOT / "admin_main.py",
    APP_ROOT / "config.py",
    APP_ROOT / "database.py",
    APP_ROOT / "platform_settings.py",
    APP_ROOT / "formal_experiments.py",
    APP_ROOT / "agent.py",
    APP_ROOT / "video_worker.py",
    APP_ROOT / "db.py",
    APP_ROOT / "rag.py",
    APP_ROOT / "report.py",
    APP_ROOT / "recommendation.py",
    APP_ROOT / "routers",
    APP_ROOT / "services",
]

DOMAIN_FORBIDDEN_IMPORTS = (
    "fastapi",
    "starlette.responses",
    "server.app.api",
    "server.app.auth",
    "server.app.routers",
    "server.app.app_runtime",
    "server.app.services",
    "server.app.workers",
)

WORKER_FORBIDDEN_IMPORTS = (
    "fastapi",
    "starlette.responses",
    "server.app.api",
    "server.app.routers",
    "server.app.app_runtime",
    "server.app.services",
)

API_FORBIDDEN_IMPORTS = ("server.app.workers",)
CATALOG_LIVE_PATHS = [
    APP_ROOT / "catalog_tree_schemas.py",
    APP_ROOT / "api" / "admin" / "admin_catalog_tree.py",
    APP_ROOT / "api" / "student" / "student_catalog.py",
    APP_ROOT / "domains" / "catalog_tree",
    APP_ROOT / "domains" / "video_library",
]
CATALOG_FORBIDDEN_SNIPPETS = (
    "shortcut_target_node_id",
    "upload_and_bind_media",
    "/media/upload",
    "node_kind IN ('point', 'hybrid')",
    'node_kind IN ("point", "hybrid")',
)


@dataclass(frozen=True)
class Violation:
    file: Path
    message: str

    def render(self) -> str:
        return f"{self.file.relative_to(REPO_ROOT)}: {self.message}"


def _python_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*.py") if path.is_file())


def _imports(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.append(node.module)
    return imports


def _matches(module: str, forbidden: tuple[str, ...]) -> str | None:
    for prefix in forbidden:
        if module == prefix or module.startswith(f"{prefix}."):
            return prefix
    return None


def validate_import_boundaries() -> list[Violation]:
    checks = [
        (APP_ROOT / "domains", DOMAIN_FORBIDDEN_IMPORTS, "domain module imports forbidden runtime/web owner"),
        (APP_ROOT / "workers", WORKER_FORBIDDEN_IMPORTS, "worker module imports forbidden runtime/web owner"),
        (APP_ROOT / "api", API_FORBIDDEN_IMPORTS, "api module imports worker entrypoint"),
    ]
    violations: list[Violation] = []
    for root, forbidden, label in checks:
        for path in _python_files(root):
            for module in _imports(path):
                matched = _matches(module, forbidden)
                if matched:
                    violations.append(Violation(path, f"{label}: {module} matches {matched}"))
    return violations


def validate_legacy_paths_removed() -> list[Violation]:
    violations: list[Violation] = []
    for path in LEGACY_PATHS:
        if path.exists():
            violations.append(Violation(path, "legacy compatibility path must not exist"))
    return violations


def validate_fastapi_tool_entrypoint() -> list[Violation]:
    if not PYPROJECT.exists():
        return [Violation(PYPROJECT, "pyproject.toml is missing")]
    pyproject = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    entrypoint = (
        pyproject.get("tool", {})
        .get("fastapi", {})
        .get("entrypoint")
    )
    if entrypoint != CANONICAL_FASTAPI_ENTRYPOINT:
        return [
            Violation(
                PYPROJECT,
                f"FastAPI tool entrypoint must be {CANONICAL_FASTAPI_ENTRYPOINT}, found {entrypoint!r}",
            )
        ]
    return []


def route_table() -> list[dict[str, str]]:
    from server.app.app_runtime.main import app

    rows: list[dict[str, str]] = []
    for route in app.routes:
        path = getattr(route, "path", "")
        name = getattr(route, "name", "")
        methods = sorted(getattr(route, "methods", set()) or [])
        if not methods:
            rows.append({"method": "MOUNT", "path": path, "name": name})
            continue
        for method in methods:
            if method in {"HEAD", "OPTIONS"}:
                continue
            rows.append({"method": method, "path": path, "name": name})
    return sorted(rows, key=lambda item: (item["path"], item["method"], item["name"]))


def validate_route_inventory() -> list[Violation]:
    if not ROUTE_INVENTORY.exists():
        return [Violation(ROUTE_INVENTORY, "route inventory file is missing")]
    expected = json.loads(ROUTE_INVENTORY.read_text(encoding="utf-8"))
    expected_pairs = [(item["method"], item["path"]) for item in expected["routes"]]
    actual_rows = route_table()
    actual_pairs = [(item["method"], item["path"]) for item in actual_rows]
    violations: list[Violation] = []

    actual_counts = Counter(actual_pairs)
    duplicates = sorted(pair for pair, count in actual_counts.items() if count != 1)
    for method, path in duplicates:
        violations.append(Violation(ROUTE_INVENTORY, f"route registered {actual_counts[(method, path)]} times: {method} {path}"))

    missing = sorted(set(expected_pairs) - set(actual_pairs))
    extra = sorted(set(actual_pairs) - set(expected_pairs))
    for method, path in missing:
        violations.append(Violation(ROUTE_INVENTORY, f"missing canonical route: {method} {path}"))
    for method, path in extra:
        violations.append(Violation(ROUTE_INVENTORY, f"route not in canonical inventory: {method} {path}"))

    for removed in expected.get("removed_aliases", []):
        pair = (removed["method"], removed["path"])
        if pair in actual_pairs:
            violations.append(Violation(ROUTE_INVENTORY, f"removed alias is still registered: {pair[0]} {pair[1]}"))
    return violations


def validate_catalog_tree_boundaries() -> list[Violation]:
    violations: list[Violation] = []
    tree_facade = APP_ROOT / "domains" / "catalog_tree" / "tree.py"
    if tree_facade.exists():
        line_count = len(tree_facade.read_text(encoding="utf-8").splitlines())
        if line_count > 120:
            violations.append(Violation(tree_facade, f"catalog tree facade is too large ({line_count} lines); split responsibilities into domain modules"))
    for path in CATALOG_LIVE_PATHS:
        files = [path] if path.is_file() else _python_files(path)
        for file in files:
            text_value = file.read_text(encoding="utf-8")
            for snippet in CATALOG_FORBIDDEN_SNIPPETS:
                if snippet in text_value:
                    violations.append(Violation(file, f"retired catalog tree live path snippet is present: {snippet}"))
            if "hybrid" in text_value and "hybrid_bge" not in text_value and "retrieve_hybrid_context" not in text_value:
                violations.append(Violation(file, "retired catalog hybrid node semantics appear in a live catalog path"))
            if "shortcut" in text_value:
                violations.append(Violation(file, "retired catalog shortcut semantics appear in a live catalog path"))
    return violations


def validate() -> list[Violation]:
    return [
        *validate_import_boundaries(),
        *validate_legacy_paths_removed(),
        *validate_fastapi_tool_entrypoint(),
        *validate_route_inventory(),
        *validate_catalog_tree_boundaries(),
    ]


def main() -> int:
    violations = validate()
    if not violations:
        print("Backend architecture validation passed")
        return 0
    print("Backend architecture validation failed:")
    for violation in violations:
        print(f"- {violation.render()}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
