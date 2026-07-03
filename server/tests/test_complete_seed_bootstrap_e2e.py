from __future__ import annotations

import os
import subprocess
import sys
from uuid import uuid4

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


def _run_checked(args: list[str], *, env: dict[str, str]) -> None:
    completed = subprocess.run(args, env=env, capture_output=True, text=True)
    if completed.returncode != 0:
        pytest.fail(
            "Command failed: "
            + " ".join(args)
            + "\nSTDOUT:\n"
            + completed.stdout
            + "\nSTDERR:\n"
            + completed.stderr
        )


def _create_disposable_database() -> tuple[str, str]:
    source_url = os.getenv("DATABASE_URL") or "postgresql+psycopg://chemistry:chemistry@127.0.0.1:15432/chemistry_exam"
    parsed = make_url(source_url)
    database_name = f"chemistry_seed_e2e_{uuid4().hex[:12]}"
    maintenance_url = parsed.set(database="postgres")
    target_url = parsed.set(database=database_name)
    engine = create_engine(maintenance_url, isolation_level="AUTOCOMMIT", pool_pre_ping=True, future=True)
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            connection.execute(text(f'CREATE DATABASE "{database_name}"'))
    except Exception as exc:  # noqa: BLE001 - optional integration test skips when DB admin access is unavailable.
        pytest.skip(f"complete seed bootstrap e2e requires PostgreSQL create database access: {exc.__class__.__name__}")
    finally:
        engine.dispose()
    return target_url.render_as_string(hide_password=False), database_name


def _drop_disposable_database(database_name: str) -> None:
    source_url = os.getenv("DATABASE_URL") or "postgresql+psycopg://chemistry:chemistry@127.0.0.1:15432/chemistry_exam"
    maintenance_url = make_url(source_url).set(database="postgres")
    engine = create_engine(maintenance_url, isolation_level="AUTOCOMMIT", pool_pre_ping=True, future=True)
    try:
        with engine.connect() as connection:
            connection.execute(
                text(
                    """
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = :database_name
                      AND pid <> pg_backend_pid()
                    """
                ),
                {"database_name": database_name},
            )
            connection.execute(text(f'DROP DATABASE IF EXISTS "{database_name}"'))
    finally:
        engine.dispose()


@pytest.mark.skipif(
    os.getenv("RUN_COMPLETE_SEED_BOOTSTRAP_E2E") != "1",
    reason="set RUN_COMPLETE_SEED_BOOTSTRAP_E2E=1 to run the disposable PostgreSQL bootstrap test",
)
def test_complete_seed_bootstrap_restores_blank_database_and_login(tmp_path) -> None:
    database_url, database_name = _create_disposable_database()
    env = {
        **os.environ,
        "DATABASE_URL": database_url,
        "MEDIA_ROOT": str(tmp_path / "media"),
        "DATA_BACKEND": "postgres",
        "CHEMISTRY_APP_ENV": "development",
    }
    try:
        _run_checked(
            [
                sys.executable,
                "scripts/bootstrap_production_seed.py",
                "--skip-es",
                "--media-root",
                str(tmp_path / "media"),
            ],
            env=env,
        )
        _run_checked(
            [
                sys.executable,
                "-c",
                (
                    "from server.app.auth import authenticate_user;"
                    "assert authenticate_user('teacher', '123456');"
                    "assert authenticate_user('26320001', '123456')"
                ),
            ],
            env=env,
        )
    finally:
        _drop_disposable_database(database_name)
