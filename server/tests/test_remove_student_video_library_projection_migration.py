from __future__ import annotations

from pathlib import Path


MIGRATION = Path(__file__).resolve().parents[1] / "migrations" / "048_remove_student_video_library_projection.sql"


def test_student_video_projection_migration_only_retires_student_search_state() -> None:
    sql = MIGRATION.read_text(encoding="utf-8")

    assert "WHERE job_type IN ('es_upsert', 'es_delete')" in sql
    assert "'teacher_search_upsert'" in sql
    assert "'teacher_search_delete'" in sql
    assert "'rag_evidence_refresh'" in sql
    assert "'rag_evidence_delete'" in sql
    assert "DROP TABLE IF EXISTS experiment_catalog_point_search_index_state" in sql
    assert "DROP TABLE IF EXISTS experiment_video_point_search_index_state" in sql
    assert "DROP TABLE IF EXISTS experiment_catalog_teacher_search_index_state" not in sql
    assert "DROP TABLE IF EXISTS experiment_catalog_point_evidence_state" not in sql
    assert "DROP TABLE IF EXISTS experiment_catalog_point_evidence_bindings" not in sql
    assert "DROP TABLE IF EXISTS textbook" not in sql.lower()
