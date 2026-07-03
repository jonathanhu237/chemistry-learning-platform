from __future__ import annotations

import argparse
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_SERVICES = {"backend", "postgres", "web-teacher", "web-student"}
RETIRED_SERVICES = {"bge-rag", "web-admin", "web-backoffice", "web-student-old", "web-teacher-old"}


def _run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    print("$ " + " ".join(command), flush=True)
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, end="", file=sys.stderr)
    if check and completed.returncode != 0:
        raise SystemExit(completed.returncode)
    return completed


def _request_status(url: str, *, method: str = "GET", timeout: float = 5) -> int:
    request = urllib.request.Request(url, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            response.read()
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code


def _compose_port(service: str, port: int) -> str:
    completed = _run(["docker", "compose", "port", service, str(port)])
    lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
    if not lines:
        raise SystemExit(f"Compose service {service!r} does not publish port {port}")
    line = lines[0]
    if line.startswith("0.0.0.0:") or line.startswith("[::]:"):
        return "127.0.0.1:" + line.rsplit(":", 1)[1]
    return line


def _assert_required_services_running(required_services: set[str]) -> None:
    completed = _run(["docker", "compose", "ps", "--services", "--status", "running"])
    running = {line.strip() for line in completed.stdout.splitlines() if line.strip()}
    missing = sorted(required_services - running)
    if missing:
        raise SystemExit("Required Compose services are not running: " + ", ".join(missing))
    print("Required Compose services running: " + ", ".join(sorted(required_services)))


def _assert_no_retired_services_configured() -> None:
    completed = _run(["docker", "compose", "config", "--services"])
    configured = {line.strip() for line in completed.stdout.splitlines() if line.strip()}
    retired = sorted(RETIRED_SERVICES & configured)
    if retired:
        raise SystemExit("Retired Compose services are still configured: " + ", ".join(retired))


def _wait_status(url: str, *, label: str, expected: set[int], timeout_seconds: int = 120) -> int:
    deadline = time.monotonic() + timeout_seconds
    last_status: int | None = None
    last_error = ""
    while time.monotonic() < deadline:
        try:
            last_status = _request_status(url, timeout=5)
            if last_status in expected:
                return last_status
            last_error = f"HTTP {last_status}"
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = str(exc)
        time.sleep(2)
    expected_text = ", ".join(str(status_code) for status_code in sorted(expected))
    detail = last_error or (f"HTTP {last_status}" if last_status is not None else "no response")
    raise SystemExit(f"{label} did not return expected status {{{expected_text}}} within {timeout_seconds}s: {detail}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the required Docker Compose application services.")
    parser.add_argument("--build", action="store_true", help="Build required service images before starting the stack.")
    parser.add_argument("--keep-orphans", action="store_true", help="Do not remove obsolete Compose service containers.")
    parser.add_argument("--skip-up", action="store_true", help="Validate already-running Compose services without starting them.")
    args = parser.parse_args()

    required_services = REQUIRED_SERVICES

    _run(["docker", "compose", "config", "--quiet"])
    _assert_no_retired_services_configured()
    if not args.skip_up:
        command = ["docker", "compose", "up", "-d", *sorted(required_services)]
        if args.build:
            command.insert(4, "--build")
        if not args.keep_orphans:
            command.insert(4 if not args.build else 5, "--remove-orphans")
        _run(command)
    _assert_required_services_running(required_services)

    backend_url = "http://" + _compose_port("backend", 8000)
    web_student_url = "http://" + _compose_port("web-student", 80)
    web_teacher_url = "http://" + _compose_port("web-teacher", 80)

    _run(["docker", "compose", "exec", "-T", "postgres", "pg_isready", "-U", "chemistry", "-d", "chemistry_exam"])
    _wait_status(f"{backend_url}/health", label="backend", expected={200})
    _wait_status(f"{web_student_url}/health", label="web-student frontend health", expected={200})
    _wait_status(f"{web_teacher_url}/health", label="web-teacher frontend health", expected={200})
    _wait_status(f"{web_student_url}/", label="web-student frontend root", expected={200})
    _wait_status(f"{web_teacher_url}/login", label="web-teacher login", expected={200})
    _wait_status(f"{web_student_url}/api/auth/me", label="web-student API proxy", expected={401})
    _wait_status(f"{web_student_url}/assessment", label="web-student deep route", expected={200})
    _wait_status(f"{web_teacher_url}/api/auth/me", label="web-teacher API proxy", expected={401})
    _wait_status(f"{web_teacher_url}/scores", label="web-teacher deep route", expected={200})

    _run(["docker", "compose", "exec", "-T", "backend", "python", "scripts/apply_migrations.py"])
    print("Compose stack smoke: ok")


if __name__ == "__main__":
    main()
