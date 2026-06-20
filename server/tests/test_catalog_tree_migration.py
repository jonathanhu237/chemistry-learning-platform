from __future__ import annotations

from pathlib import Path


MIGRATION = Path("server/migrations/020_experiment_catalog_tree.sql")


def _sql() -> str:
    return MIGRATION.read_text(encoding="utf-8")


def test_catalog_tree_migration_uses_deterministic_legacy_identity_mapping() -> None:
    sql = _sql()

    assert "'cat-exp-' || left(encode(digest(convert_to(fe.id, 'UTF8'), 'sha1'), 'hex'), 24)" in sql
    assert "'cat-point-' || left(encode(digest(convert_to(evp.experiment_id || '::' || evp.point_key, 'UTF8'), 'sha1'), 'hex'), 24)" in sql
    assert "CREATE TABLE IF NOT EXISTS experiment_catalog_legacy_identity_map" in sql
    assert "UNIQUE (legacy_kind, legacy_experiment_id, legacy_point_key)" in sql
    assert "legacy_identity, legacy_kind, legacy_experiment_id, legacy_point_key, catalog_node_id" in sql


def test_catalog_tree_migration_backfills_point_content_media_links_and_questions() -> None:
    sql = _sql()

    assert "INSERT INTO experiment_catalog_point_content" in sql
    assert "teacher_note, principle_mode, principle_equation, principle_text" in sql
    assert "''" in sql
    assert "INSERT INTO experiment_catalog_point_media_bindings" in sql
    assert "INSERT INTO experiment_catalog_point_related_links" in sql
    assert "ALTER TABLE experiment_questions" in sql
    assert "ADD COLUMN IF NOT EXISTS primary_point_node_ids" in sql
    assert "'primary_point_node_ids', question_points.point_node_ids_json" in sql


def test_catalog_tree_migration_backfills_evidence_assessment_events_and_feedback() -> None:
    sql = _sql()

    assert "ALTER TABLE experiment_video_point_evidence" in sql
    assert "ADD COLUMN IF NOT EXISTS point_node_id text REFERENCES experiment_catalog_nodes" in sql
    assert "ALTER TABLE experiment_question_attempts" in sql
    assert "idx_experiment_question_attempts_point_node" in sql
    assert "ALTER TABLE student_events" in sql
    assert "idx_student_events_point_node" in sql
    assert "ALTER TABLE student_posttest_sessions" in sql
    assert "point_node_ids jsonb NOT NULL DEFAULT '[]'::jsonb" in sql
    assert "ALTER TABLE student_feedback" in sql
    assert "idx_student_feedback_point_node" in sql
