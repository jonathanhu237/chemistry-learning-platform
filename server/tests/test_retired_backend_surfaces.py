from __future__ import annotations

from pathlib import Path

from server.app.app_runtime.main import app
from server.app.domains.assessments import posttest, smart_assessment
from server.app.domains.platform.settings import AssessmentSettings
from server.app.infrastructure.settings import Settings


ROOT = Path(__file__).resolve().parents[2]


def test_retired_backend_routes_are_absent_and_current_routes_remain() -> None:
    paths = app.openapi()["paths"]

    assert all(not path.startswith("/api/student/legacy/") for path in paths)
    assert all(not path.startswith("/api/admin/legacy/") for path in paths)
    assert all(not path.startswith("/api/web-admin/") for path in paths)
    assert all(not path.startswith("/api/teacher/") for path in paths)
    assert "/api/student/pretest/start" not in paths
    assert "/api/student/pretest/submit" not in paths
    assert "/api/admin/question-banks/legacy-point-generate" not in paths

    assert "/api/student/smart-assessment/start" in paths
    assert "/api/student/custom-assessment/start" in paths
    assert "/api/student/posttest/start" in paths
    assert "/api/admin/question-banks/generate" in paths
    assert "/api/admin/student-preview/session" in paths
    assert "/api/preview/student-session/exchange" in paths


def test_retired_backend_modules_and_active_pretest_schema_are_removed() -> None:
    removed_paths = [
        "server/app/api/admin/admin_legacy.py",
        "server/app/api/student/student_legacy.py",
        "server/app/api/student/student_pretest.py",
        "server/app/api/web_admin/__init__.py",
        "server/app/api/web_admin/auth.py",
        "server/app/api/web_admin/student_preview.py",
        "server/app/api/web_admin/teacher_accounts.py",
        "server/app/domains/assessments/pretest.py",
        "server/app/domains/student_legacy/__init__.py",
        "server/app/domains/student_legacy/reports.py",
        "server/app/domains/student_legacy/video_points.py",
        "server/app/domains/teacher_legacy/__init__.py",
        "server/app/domains/teacher_legacy/read_models.py",
        "server/app/student_legacy_schemas.py",
        "server/app/student_pretest_schemas.py",
        "server/app/teacher_legacy_schemas.py",
    ]

    assert all(not (ROOT / path).exists() for path in removed_paths)
    assert not hasattr(AssessmentSettings(), "pretest_enabled")
    assert not hasattr(AssessmentSettings(), "pretest_question_count")
    assert "web_admin_access_token" not in Settings.__dataclass_fields__


def test_current_assessments_use_neutral_student_context_owner() -> None:
    assert smart_assessment._load_student_context.__module__.endswith("assessments.student_context")
    assert smart_assessment._ensure_student_row.__module__.endswith("assessments.student_context")
    assert posttest._load_student_context.__module__.endswith("assessments.student_context")
    assert posttest._ensure_student_row.__module__.endswith("assessments.student_context")


def test_historical_pretest_reads_and_migration_remain_available() -> None:
    migration = ROOT / "server/migrations/015_student_pretest_sessions.sql"
    reports_source = (ROOT / "server/app/domains/assessments/reports.py").read_text(encoding="utf-8")
    point_detail_source = (ROOT / "server/app/domains/student_learning/point_detail.py").read_text(encoding="utf-8")

    assert migration.exists()
    assert "student_pretest_sessions" in reports_source
    assert "create_pretest_report" in reports_source
    assert "student_pretest_sessions" in point_detail_source


def test_legacy_question_creation_is_removed_but_lineage_reader_remains() -> None:
    generation_source = (ROOT / "server/app/domains/questions/generation.py").read_text(encoding="utf-8")
    bank_source = (ROOT / "server/app/domains/questions/bank.py").read_text(encoding="utf-8")

    assert "generate_legacy_point_content_question_drafts" not in generation_source
    assert "attach_legacy_point_content_lineage" not in generation_source
    assert 'evidence_contract == "legacy_point_content"' in generation_source
    assert "LEGACY_QUESTION_WITHDRAWAL_MODE" in bank_source
