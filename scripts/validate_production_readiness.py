from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WEB_ADMIN_DIR = ROOT / "apps" / "web-admin"
WEB_TEACHER_DIR = ROOT / "apps" / "web-teacher"
WEB_STUDENT_DIR = ROOT / "apps" / "web-student"
FRONTENDS = [
    ("web-admin frontend", WEB_ADMIN_DIR, False),
    ("web-teacher frontend", WEB_TEACHER_DIR, True),
    ("web-student frontend", WEB_STUDENT_DIR, True),
]
DEFAULT_CHANGE = "split-web-admin-teacher-student-consoles"


@dataclass
class Stage:
    name: str
    command: list[str]
    cwd: Path = ROOT
    required: bool = True
    env: dict[str, str] | None = None


@dataclass
class StageResult:
    name: str
    returncode: int
    seconds: float
    skipped: bool = False

    @property
    def ok(self) -> bool:
        return self.skipped or self.returncode == 0


def _which(name: str) -> str:
    resolved = shutil.which(name)
    if not resolved:
        raise RuntimeError(f"Required executable is not on PATH: {name}")
    if os.name == "nt" and resolved.lower().endswith(".ps1"):
        cmd = Path(resolved).with_suffix(".cmd")
        if cmd.exists():
            return str(cmd)
    return resolved


def _npm() -> str:
    return _which("npm")


def _resolve_command(command: list[str]) -> list[str]:
    if not command:
        return command
    executable = command[0]
    if any(separator in executable for separator in ("/", "\\")) or Path(executable).suffix:
        return command
    return [_which(executable), *command[1:]]


def _run(stage: Stage) -> StageResult:
    command = _resolve_command(stage.command)
    print(f"\n==> {stage.name}", flush=True)
    print("$ " + " ".join(command), flush=True)
    start = time.perf_counter()
    env = os.environ.copy()
    if stage.env:
        env.update(stage.env)
    completed = subprocess.run(command, cwd=stage.cwd, env=env, check=False)
    seconds = time.perf_counter() - start
    status = "ok" if completed.returncode == 0 else "failed"
    print(f"<== {stage.name}: {status} ({seconds:.1f}s)")
    return StageResult(stage.name, completed.returncode, seconds)


def _frontend_dependencies_stage(args: argparse.Namespace) -> list[Stage]:
    if args.skip_frontend and not args.run_e2e:
        return []
    if args.install_frontend:
        return [Stage(f"{name} dependency install", [_npm(), "ci"], cwd=frontend_dir) for name, frontend_dir, _ in FRONTENDS]
    stages: list[Stage] = []
    for name, frontend_dir, _ in FRONTENDS:
        if (frontend_dir / "node_modules").exists():
            continue
        relative_dir = frontend_dir.relative_to(ROOT).as_posix()
        stages.append(
            Stage(
                f"{name} dependency check",
                [
                    sys.executable,
                    "-c",
                    (
                        "raise SystemExit("
                        f"'{relative_dir}/node_modules is missing; rerun with --install-frontend "
                        "or install dependencies before validation'"
                        ")"
                    ),
                ],
            )
        )
    return stages


def _compose_host_env() -> dict[str, str]:
    postgres_port = os.environ.get("POSTGRES_HOST_PORT", "15432")
    elasticsearch_port = os.environ.get("ELASTICSEARCH_HOST_PORT", "9200")
    return {
        "DATA_BACKEND": "postgres",
        "DATABASE_URL": f"postgresql+psycopg://chemistry:chemistry@127.0.0.1:{postgres_port}/chemistry_exam",
        "VIDEO_LIBRARY_SEARCH_BACKEND": "elasticsearch",
        "VIDEO_LIBRARY_SEARCH_URL": f"http://127.0.0.1:{elasticsearch_port}",
        "VIDEO_LIBRARY_SEARCH_LOCAL_FALLBACK": "false",
    }


def _student_mobile_qa_env() -> dict[str, str]:
    has_credentials = bool(os.environ.get("STUDENT_H5_QA_STUDENT_ID") and os.environ.get("STUDENT_H5_QA_PASSWORD"))
    has_auth_override = os.environ.get("STUDENT_H5_QA_ALLOW_AUTH_SKIP") == "1"
    has_mock_override = os.environ.get("STUDENT_H5_QA_MOCK") == "1"
    if has_credentials or has_auth_override or has_mock_override:
        return {}
    return {"STUDENT_H5_QA_MOCK": "1"}


def _stages(args: argparse.Namespace) -> list[Stage]:
    stages: list[Stage] = []
    compose_host_env = _compose_host_env() if args.run_compose_smoke else None
    if args.run_compose_smoke:
        stages.append(
            Stage(
                "Docker Compose required services smoke",
                [sys.executable, "scripts/validate_compose_stack.py"],
            )
        )
    if not args.skip_resource_validation:
        stages.append(
            Stage(
                "catalog outline seed validation",
                [sys.executable, "scripts/validate_experiment_catalog_seed.py", "--write-report"],
            )
        )
        stages.append(
            Stage(
                "protected resource manifest",
                [sys.executable, "scripts/validate_production_resources.py"],
            )
        )
        stages.append(
            Stage(
                "video-library ES/IK readiness",
                [sys.executable, "scripts/validate_video_library_search.py"],
                env=compose_host_env,
            )
        )
        stages.append(
            Stage(
                "catalog point identity validation",
                [sys.executable, "scripts/validate_experiment_points.py"],
                env=compose_host_env,
            )
        )
    if not args.skip_openspec:
        stages.append(
            Stage(
                "openspec strict validation",
                ["openspec", "validate", args.change, "--strict"],
            )
        )
    stages.append(
        Stage(
            "admin app import smoke",
            [sys.executable, "-c", "import server.app.app_runtime.main as m; print(m.app.title)"],
        )
    )
    stages.append(
        Stage(
            "backend slim architecture validation",
            [sys.executable, "scripts/validate_backend_architecture.py"],
        )
    )
    if not args.skip_backend_tests:
        stages.append(Stage("backend tests", [sys.executable, "-m", "pytest", "server/tests", "-q"]))

    stages.extend(_frontend_dependencies_stage(args))
    if not args.skip_frontend:
        stages.append(Stage("web-teacher import boundaries", [_npm(), "run", "validate:boundaries"], cwd=WEB_TEACHER_DIR))
        for name, frontend_dir, has_tests in FRONTENDS:
            stages.append(Stage(f"{name} typecheck", [_npm(), "run", "typecheck"], cwd=frontend_dir))
            if has_tests:
                stages.append(Stage(f"{name} tests", [_npm(), "test"], cwd=frontend_dir))
            stages.append(Stage(f"{name} build", [_npm(), "run", "build"], cwd=frontend_dir))
        stages.append(
            Stage("web-teacher build chunk report", [_npm(), "run", "build:report"], cwd=WEB_TEACHER_DIR)
        )
    if args.run_e2e:
        stages.append(Stage("web-teacher e2e smoke", [_npm(), "run", "e2e:smoke"], cwd=WEB_TEACHER_DIR))
        stages.append(
            Stage(
                "web-student mobile route-stack QA",
                [_npm(), "run", "qa:mobile"],
                cwd=WEB_STUDENT_DIR,
                env=_student_mobile_qa_env(),
            )
        )
    return stages


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the production-readiness validation chain for the admin platform."
    )
    parser.add_argument("--change", default=DEFAULT_CHANGE, help="OpenSpec change to validate.")
    parser.add_argument("--install-frontend", action="store_true", help="Run npm ci before frontend checks.")
    parser.add_argument("--skip-frontend", action="store_true", help="Skip frontend typecheck, tests, and build.")
    parser.add_argument("--skip-backend-tests", action="store_true", help="Skip pytest backend checks.")
    parser.add_argument("--skip-openspec", action="store_true", help="Skip OpenSpec strict validation.")
    parser.add_argument("--skip-resource-validation", action="store_true", help="Skip protected resource validation.")
    parser.add_argument(
        "--run-e2e",
        action="store_true",
        help="Run opt-in browser e2e smoke. Requires backend, admin frontend, and student frontend origins to be running.",
    )
    parser.add_argument(
        "--run-compose-smoke",
        action="store_true",
        help="Run a Docker Compose smoke check for required Postgres, Elasticsearch/IK, and backend services.",
    )
    args = parser.parse_args()

    os.environ.setdefault("PYTHONUTF8", "1")
    results: list[StageResult] = []
    failed = False
    for stage in _stages(args):
        try:
            result = _run(stage)
        except RuntimeError as exc:
            print(f"\n<== {stage.name}: failed")
            print(str(exc))
            result = StageResult(stage.name, 1, 0)
        results.append(result)
        if not result.ok:
            failed = True
            break

    print("\nProduction readiness summary:")
    for result in results:
        status = "SKIP" if result.skipped else ("PASS" if result.ok else "FAIL")
        print(f"- {status}: {result.name} ({result.seconds:.1f}s)")

    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
