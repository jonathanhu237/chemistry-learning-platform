from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
E2E_DIR = ROOT / "e2e"


def _which(name: str) -> str:
    resolved = shutil.which(name)
    if not resolved:
        raise SystemExit(f"Required executable is not on PATH: {name}")
    if os.name == "nt" and resolved.lower().endswith(".ps1"):
        cmd = Path(resolved).with_suffix(".cmd")
        if cmd.exists():
            return str(cmd)
    return resolved


def _run(command: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    printable = " ".join(command)
    print("$ " + printable, flush=True)
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    completed = subprocess.run(command, cwd=cwd, env=merged_env, text=True, encoding="utf-8", errors="replace", check=False)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)
    return completed


def _capture(command: list[str], *, cwd: Path = ROOT) -> str:
    printable = " ".join(command)
    print("$ " + printable, flush=True)
    completed = subprocess.run(command, cwd=cwd, text=True, encoding="utf-8", errors="replace", capture_output=True, check=False)
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)
    return completed.stdout.strip()


def _compose_url(service: str, port: int) -> str:
    output = _capture(["docker", "compose", "port", service, str(port)])
    line = next((value.strip() for value in output.splitlines() if value.strip()), "")
    if not line:
        raise SystemExit(f"Compose service {service!r} does not publish port {port}")
    if line.startswith("0.0.0.0:") or line.startswith("[::]:"):
        line = "127.0.0.1:" + line.rsplit(":", 1)[1]
    return f"http://{line}"


def _ensure_e2e_dependencies(*, install_deps: bool) -> None:
    node_modules = E2E_DIR / "node_modules"
    package_lock = E2E_DIR / "package-lock.json"
    npm = _which("npm")
    if install_deps or not node_modules.exists():
        command = [npm, "ci"] if package_lock.exists() else [npm, "install"]
        _run(command, cwd=E2E_DIR)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Playwright e2e smoke against the legacy teacher/student Compose runtime.")
    parser.add_argument("--build", action="store_true", help="Build required service images before starting the Compose stack.")
    parser.add_argument("--skip-up", action="store_true", help="Validate already-running Compose services without starting them.")
    parser.add_argument(
        "--skip-seed-bootstrap",
        action="store_true",
        help="Only import demo identities. By default the production seed baseline is imported so content journeys have data.",
    )
    parser.add_argument("--install-deps", action="store_true", help="Run npm ci in e2e/ even if node_modules already exists.")
    parser.add_argument("--headed", action="store_true", help="Run Playwright with a visible browser.")
    args = parser.parse_args()

    compose_command = [sys.executable, "scripts/validate_compose_stack.py"]
    if args.build:
        compose_command.append("--build")
    if args.skip_up:
        compose_command.append("--skip-up")
    _run(compose_command)
    if args.skip_seed_bootstrap:
        _run(["docker", "compose", "exec", "-T", "backend", "python", "scripts/seed_demo_identities.py", "import", "--skip-migrations"])
    else:
        _run(
            [
                "docker",
                "compose",
                "exec",
                "-T",
                "backend",
                "python",
                "scripts/bootstrap_production_seed.py",
                "--skip-migrations",
                "--skip-es",
                "--skip-validation",
            ]
        )

    _ensure_e2e_dependencies(install_deps=args.install_deps)

    env = {
        "LEGACY_E2E_BACKEND_URL": _compose_url("backend", 8000),
        "LEGACY_E2E_STUDENT_URL": _compose_url("web-student", 80),
        "LEGACY_E2E_TEACHER_URL": _compose_url("web-teacher", 80),
    }
    command = [_which("npm"), "run", "test"]
    if args.headed:
        command.append("--")
        command.append("--headed")
    _run(command, cwd=E2E_DIR, env=env)
    print("Legacy browser e2e smoke: ok")


if __name__ == "__main__":
    main()
