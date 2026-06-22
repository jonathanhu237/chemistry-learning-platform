from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SERVICES = [
    "backend",
    "web-student",
    "web-teacher",
    "web-admin",
    "postgres",
    "elasticsearch",
    "tusd",
    "video-worker",
]


def _run(command: list[str]) -> None:
    print("$ " + " ".join(command), flush=True)
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> None:
    parser = argparse.ArgumentParser(description="Deploy the default chemistry platform Docker Compose stack.")
    parser.add_argument("--skip-build", action="store_true", help="Reuse existing images instead of rebuilding.")
    parser.add_argument("--keep-orphans", action="store_true", help="Do not remove obsolete Compose service containers.")
    parser.add_argument("--with-rag", action="store_true", help="Also deploy the optional bge-rag profile service.")
    parser.add_argument("--skip-smoke", action="store_true", help="Skip post-deploy Compose smoke validation.")
    parser.add_argument("--skip-index-rebuild", action="store_true", help="Skip video-library index rebuild during smoke.")
    args = parser.parse_args()

    _run(["docker", "compose", "config", "--quiet"])

    up_command = ["docker", "compose"]
    if args.with_rag:
        up_command.extend(["--profile", "rag"])
    up_command.extend(["up", "-d"])
    if not args.skip_build:
        up_command.append("--build")
    if not args.keep_orphans:
        up_command.append("--remove-orphans")
    up_command.extend(DEFAULT_SERVICES)
    if args.with_rag:
        up_command.append("bge-rag")
    _run(up_command)

    if not args.skip_smoke:
        smoke_command = [sys.executable, "scripts/validate_compose_stack.py", "--skip-up"]
        if args.skip_index_rebuild:
            smoke_command.append("--skip-index-rebuild")
        _run(smoke_command)

    _run(["docker", "compose", "ps"])


if __name__ == "__main__":
    main()
