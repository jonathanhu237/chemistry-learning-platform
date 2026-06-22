from __future__ import annotations

import argparse
import json
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
REQUIRED_SERVICES = {"backend", "elasticsearch", "postgres", "tusd", "video-worker", "web-admin", "web-student", "web-teacher"}
ES_ANALYZER_ASSET_PATHS = [
    "/usr/share/elasticsearch/config/analysis-ik/IKAnalyzer.cfg.xml",
    "/usr/share/elasticsearch/config/analysis-ik/custom/hit_stopwords.dic",
    "/usr/share/elasticsearch/config/analysis-ik/custom/project_chemistry_stopwords.dic",
    "/usr/share/elasticsearch/config/analysis-ik/custom/chemistry_custom.dic",
    "/usr/share/elasticsearch/config/analysis/chemistry_stopwords.txt",
    "/usr/share/elasticsearch/config/analysis/chemistry_synonyms.txt",
]


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


def _json_request(url: str, *, method: str = "GET", payload: object | None = None, timeout: float = 5) -> object:
    data = None
    headers: dict[str, str] = {}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=True).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8")
    return json.loads(raw) if raw else {}


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


def _assert_required_services_running() -> None:
    completed = _run(["docker", "compose", "ps", "--services", "--status", "running"])
    running = {line.strip() for line in completed.stdout.splitlines() if line.strip()}
    missing = sorted(REQUIRED_SERVICES - running)
    if missing:
        raise SystemExit("Required Compose services are not running: " + ", ".join(missing))
    print("Required Compose services running: " + ", ".join(sorted(REQUIRED_SERVICES)))


def _wait_json(url: str, *, label: str, timeout_seconds: int = 120) -> object:
    deadline = time.monotonic() + timeout_seconds
    last_error = ""
    while time.monotonic() < deadline:
        try:
            return _json_request(url, timeout=5)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            last_error = str(exc)
            time.sleep(2)
    raise SystemExit(f"{label} did not become healthy within {timeout_seconds}s: {last_error}")


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


def _assert_ik_analyzer(elasticsearch_base_url: str) -> None:
    text = (
        r"\u786b\u4ee3\u786b\u9178\u94a0\u4e0e\u76d0\u9178\u53cd\u5e94"
        r"\u751f\u6210\u4e8c\u6c27\u5316\u786b"
    ).encode("ascii").decode("unicode_escape")
    result = _json_request(
        f"{elasticsearch_base_url}/_analyze",
        method="POST",
        payload={"analyzer": "ik_max_word", "text": text},
        timeout=10,
    )
    tokens = [str(item.get("token", "")) for item in result.get("tokens", []) if isinstance(item, dict)]
    if not tokens:
        raise SystemExit("Elasticsearch responded, but ik_max_word produced no tokens")
    required_tokens = {
        r"\u786b\u4ee3\u786b\u9178\u94a0".encode("ascii").decode("unicode_escape"),
        r"\u76d0\u9178".encode("ascii").decode("unicode_escape"),
        r"\u4e8c\u6c27\u5316\u786b".encode("ascii").decode("unicode_escape"),
    }
    if not required_tokens.issubset(set(tokens)):
        escaped_tokens = json.dumps(tokens[:20], ensure_ascii=True)
        raise SystemExit(f"ik_max_word analyzer did not produce expected chemistry tokens: {escaped_tokens}")
    print("IK analyzer smoke: ok " + json.dumps(tokens[:8], ensure_ascii=True))


def _assert_es_analyzer_assets() -> None:
    for path in ES_ANALYZER_ASSET_PATHS:
        _run(["docker", "compose", "exec", "-T", "elasticsearch", "sh", "-lc", f"test -s {path}"])
    print("ES/IK analyzer assets present: ok")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate the required Docker Compose application services.")
    parser.add_argument("--build", action="store_true", help="Build required service images before starting the stack.")
    parser.add_argument("--keep-orphans", action="store_true", help="Do not remove obsolete Compose service containers.")
    parser.add_argument("--skip-up", action="store_true", help="Validate already-running Compose services without starting them.")
    parser.add_argument("--skip-index-rebuild", action="store_true", help="Skip rebuilding the video-library search index.")
    args = parser.parse_args()

    _run(["docker", "compose", "config", "--quiet"])
    if not args.skip_up:
        command = ["docker", "compose", "up", "-d", *sorted(REQUIRED_SERVICES)]
        if args.build:
            command.insert(4, "--build")
        if not args.keep_orphans:
            command.insert(4 if not args.build else 5, "--remove-orphans")
        _run(command)
    _assert_required_services_running()

    elasticsearch_url = "http://" + _compose_port("elasticsearch", 9200)
    backend_url = "http://" + _compose_port("backend", 8000)
    web_student_url = "http://" + _compose_port("web-student", 80)
    web_teacher_url = "http://" + _compose_port("web-teacher", 80)
    web_admin_url = "http://" + _compose_port("web-admin", 80)

    _run(["docker", "compose", "exec", "-T", "postgres", "pg_isready", "-U", "chemistry", "-d", "chemistry_exam"])
    _wait_json(f"{elasticsearch_url}/_cluster/health", label="Elasticsearch")
    _assert_es_analyzer_assets()
    _assert_ik_analyzer(elasticsearch_url)
    _wait_json(f"{backend_url}/health", label="backend")
    _wait_status(f"{web_student_url}/health", label="web-student frontend health", expected={200})
    _wait_status(f"{web_teacher_url}/health", label="web-teacher frontend health", expected={200})
    _wait_status(f"{web_admin_url}/health", label="web-admin frontend health", expected={200})
    _wait_status(f"{web_student_url}/", label="web-student frontend root", expected={200})
    _wait_status(f"{web_teacher_url}/login", label="web-teacher login", expected={200})
    _wait_status(f"{web_admin_url}/", label="web-admin root", expected={200})
    _wait_status(f"{web_student_url}/api/auth/me", label="web-student API proxy", expected={401})
    _wait_status(f"{web_teacher_url}/api/auth/me", label="web-teacher API proxy", expected={401})
    _wait_status(f"{web_admin_url}/api/web-admin/session", label="web-admin API proxy", expected={401, 503})

    _run(["docker", "compose", "exec", "-T", "backend", "python", "scripts/apply_migrations.py"])
    if not args.skip_index_rebuild:
        _run(["docker", "compose", "exec", "-T", "backend", "python", "scripts/rebuild_video_library_index.py", "--recreate"])
    _run(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "-e",
            "CHEMISTRY_APP_ENV=production",
            "-e",
            "VIDEO_LIBRARY_SEARCH_LOCAL_FALLBACK=false",
            "-e",
            "VIDEO_LIBRARY_SEARCH_REQUIRE_ES_IN_PRODUCTION=true",
            "backend",
            "python",
            "scripts/validate_video_library_search.py",
        ]
    )
    print("Compose stack smoke: ok")


if __name__ == "__main__":
    main()
