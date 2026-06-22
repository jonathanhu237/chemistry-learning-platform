from __future__ import annotations

from pathlib import Path


MIGRATION = Path("server/migrations/020_experiment_catalog_tree.sql")
SEPARATE_NODE_KIND_MIGRATION = Path("server/migrations/021_separate_catalog_directory_point_nodes.sql")
REACTION_EQUATION_MIGRATION = Path("server/migrations/023_catalog_point_reaction_equations.sql")
POINT_JOBS_MIGRATION = Path("server/migrations/024_catalog_point_jobs.sql")
POINT_PLACEMENTS_MIGRATION = Path("server/migrations/025_catalog_point_placements.sql")
DROP_STUDENT_CARD_FIELDS_MIGRATION = Path("server/migrations/026_drop_catalog_student_card_fields.sql")
DROP_RELATED_LINK_LABELS_MIGRATION = Path("server/migrations/027_drop_related_link_labels.sql")
SIMPLIFY_VIDEO_BINDING_MIGRATION = Path("server/migrations/028_simplify_catalog_video_binding.sql")
ENFORCE_SINGLE_VIDEO_BINDING_MIGRATION = Path("server/migrations/030_enforce_single_catalog_point_video_binding.sql")


def _sql() -> str:
    return MIGRATION.read_text(encoding="utf-8")


def _separate_sql() -> str:
    return SEPARATE_NODE_KIND_MIGRATION.read_text(encoding="utf-8")


def _reaction_equation_sql() -> str:
    return REACTION_EQUATION_MIGRATION.read_text(encoding="utf-8")


def _point_jobs_sql() -> str:
    return POINT_JOBS_MIGRATION.read_text(encoding="utf-8")


def _point_placements_sql() -> str:
    return POINT_PLACEMENTS_MIGRATION.read_text(encoding="utf-8")


def _drop_student_card_fields_sql() -> str:
    return DROP_STUDENT_CARD_FIELDS_MIGRATION.read_text(encoding="utf-8")


def _drop_related_link_labels_sql() -> str:
    return DROP_RELATED_LINK_LABELS_MIGRATION.read_text(encoding="utf-8")


def _simplify_video_binding_sql() -> str:
    return SIMPLIFY_VIDEO_BINDING_MIGRATION.read_text(encoding="utf-8")


def _enforce_single_video_binding_sql() -> str:
    return ENFORCE_SINGLE_VIDEO_BINDING_MIGRATION.read_text(encoding="utf-8")


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


def test_related_link_baseline_migrations_do_not_create_student_title_override_columns() -> None:
    legacy_sql = Path("server/migrations/019_experiment_point_learning_content.sql").read_text(encoding="utf-8")
    catalog_sql = _sql()

    assert "CREATE TABLE IF NOT EXISTS experiment_point_related_links" in legacy_sql
    assert "CREATE TABLE IF NOT EXISTS experiment_catalog_point_related_links" in catalog_sql
    assert "label text" not in legacy_sql
    assert "label text" not in catalog_sql
    assert "l.label" not in catalog_sql
    assert "label = EXCLUDED.label" not in catalog_sql


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


def test_separate_catalog_node_kind_migration_adds_legacy_card_fields_and_tightens_kind_constraint() -> None:
    sql = _separate_sql()

    assert "ADD COLUMN IF NOT EXISTS teacher_note text NOT NULL DEFAULT ''" in sql
    assert "ADD COLUMN IF NOT EXISTS student_description text NOT NULL DEFAULT ''" in sql
    assert "ADD COLUMN IF NOT EXISTS card_image_asset_id uuid REFERENCES media_assets" in sql
    assert "ADD COLUMN IF NOT EXISTS point_card_presentation jsonb NOT NULL DEFAULT '{}'::jsonb" in sql
    assert "DROP COLUMN IF EXISTS shortcut_target_node_id" in sql
    assert "CHECK (node_kind IN ('directory', 'point'))" in sql


def test_drop_student_card_fields_migration_removes_obsolete_manual_card_columns() -> None:
    sql = _drop_student_card_fields_sql()

    assert "DROP CONSTRAINT IF EXISTS experiment_catalog_nodes_card_image_asset_id_fkey" in sql
    assert "DROP INDEX IF EXISTS idx_experiment_catalog_nodes_card_image_asset" in sql
    assert "DROP COLUMN IF EXISTS student_description" in sql
    assert "DROP COLUMN IF EXISTS card_image_asset_id" in sql
    assert "DROP COLUMN IF EXISTS card_icon_key" in sql
    assert "DROP COLUMN IF EXISTS card_accent" in sql
    assert "DROP COLUMN IF EXISTS card_layout" in sql
    assert "DROP COLUMN IF EXISTS card_presentation" in sql
    assert "DROP COLUMN IF EXISTS point_card_presentation" in sql


def test_drop_related_link_labels_migration_removes_obsolete_title_override_columns() -> None:
    sql = _drop_related_link_labels_sql()

    assert "ALTER TABLE experiment_catalog_point_related_links" in sql
    assert "ALTER TABLE experiment_point_related_links" in sql
    assert "DROP COLUMN IF EXISTS label" in sql


def test_simplify_video_binding_migration_keeps_one_active_video_per_point() -> None:
    sql = _simplify_video_binding_sql()

    assert "row_number() OVER" in sql
    assert "PARTITION BY COALESCE(mb.canonical_point_id, mb.node_id)" in sql
    assert "single_active_catalog_point_video" in sql
    assert "idx_catalog_point_media_one_active_canonical" in sql
    assert "WHERE canonical_point_id IS NOT NULL" in sql
    assert "binding_status <> 'archived'" in sql
    assert "idx_catalog_point_media_one_active_node_without_canonical" in sql


def test_enforce_single_video_binding_migration_hard_deletes_duplicate_active_rows() -> None:
    sql = _enforce_single_video_binding_sql()

    assert "one video point has one current video resource" in sql
    assert "row_number() OVER" in sql
    assert "PARTITION BY COALESCE(mb.canonical_point_id, mb.node_id)" in sql
    assert "DELETE FROM experiment_catalog_point_media_bindings" in sql
    assert "ranked.keep_rank > 1" in sql
    assert "'030_enforce_single_catalog_point_video_binding'" in sql
    assert "idx_catalog_point_media_one_active_canonical" in sql
    assert "idx_catalog_point_media_one_active_node_without_canonical" in sql


def test_separate_catalog_node_kind_migration_splits_hybrid_refs_deterministically() -> None:
    sql = _separate_sql()

    assert "n.id || '::hybrid-point'" in sql
    assert "split_role', 'point_child'" in sql
    assert "experiment_catalog_point_search_index_state si" in sql
    assert "OR EXISTS (SELECT 1 FROM experiment_video_point_evidence evidence WHERE evidence.point_node_id = n.id)" in sql
    assert "UPDATE experiment_catalog_point_content pc" in sql
    assert "UPDATE experiment_catalog_point_media_bindings mb" in sql
    assert "UPDATE experiment_catalog_point_related_links rl" in sql
    assert "UPDATE experiment_video_point_evidence evidence" in sql
    assert "UPDATE experiment_question_attempts attempts" in sql
    assert "UPDATE student_events events" in sql
    assert "UPDATE student_feedback feedback" in sql
    assert "UPDATE student_experiment_mastery mastery" in sql
    assert "UPDATE experiment_questions questions" in sql
    assert "UPDATE student_posttest_sessions sessions" in sql


def test_separate_catalog_node_kind_migration_does_not_preserve_index_only_split_points() -> None:
    sql = _separate_sql()

    assert "single search index state is not a point resource" not in sql
    assert "AND NOT EXISTS (SELECT 1 FROM experiment_catalog_point_content pc WHERE pc.node_id = n.id)" in sql
    assert "AND NOT EXISTS (SELECT 1 FROM experiment_catalog_point_media_bindings mb WHERE mb.node_id = n.id)" in sql
    assert "AND NOT EXISTS (SELECT 1 FROM experiment_catalog_legacy_identity_map lm WHERE lm.catalog_node_id = n.id AND lm.legacy_kind = 'experiment_point')" in sql
    assert "DELETE FROM experiment_catalog_nodes n" in sql


def test_separate_catalog_node_kind_migration_archives_shortcuts_with_audit_metadata() -> None:
    sql = _separate_sql()

    assert "WHERE node_kind = 'shortcut'" in sql
    assert "'from_node_kind', 'shortcut'" in sql
    assert "'legacy_shortcut_target_node_id', shortcut_target_node_id" in sql
    assert "status = 'archived'" in sql


def test_reaction_equation_migration_preserves_legacy_single_equations() -> None:
    sql = _reaction_equation_sql()

    assert "CREATE TABLE IF NOT EXISTS experiment_catalog_point_reaction_equations" in sql
    assert "node_id text NOT NULL REFERENCES experiment_catalog_point_content(node_id) ON DELETE CASCADE" in sql
    assert "canonical_mhchem text" in sql
    assert "validation_status text NOT NULL DEFAULT 'warning'" in sql
    assert "migrated_from_principle_equation boolean NOT NULL DEFAULT false" in sql
    assert "INSERT INTO experiment_catalog_point_reaction_equations" in sql
    assert "btrim(principle_equation)" in sql
    assert "principle_mode = 'equation'" in sql
    assert "ON CONFLICT (node_id, row_order) DO NOTHING" in sql


def test_catalog_point_jobs_migration_uses_postgres_outbox_and_catalog_node_evidence() -> None:
    sql = _point_jobs_sql()

    assert "CREATE TABLE IF NOT EXISTS experiment_catalog_point_jobs" in sql
    assert "node_id text NOT NULL REFERENCES experiment_catalog_nodes(id) ON DELETE CASCADE" in sql
    assert "job_type IN ('es_upsert', 'es_delete', 'rag_evidence_refresh', 'rag_evidence_delete')" in sql
    assert "trigger_source IN ('automatic', 'manual', 'retry', 'system')" in sql
    assert "idx_experiment_catalog_point_jobs_open_idempotency" in sql
    assert "WHERE status IN ('pending', 'running')" in sql
    assert "CREATE TABLE IF NOT EXISTS experiment_catalog_point_evidence_state" in sql
    assert "evidence_status IN ('missing', 'pending', 'running', 'succeeded', 'failed', 'stale', 'disabled', 'unavailable')" in sql
    assert "CREATE TABLE IF NOT EXISTS experiment_catalog_point_evidence_bindings" in sql
    assert "chunk_id text NOT NULL REFERENCES source_chunks(id) ON DELETE RESTRICT" in sql


def test_catalog_point_placements_migration_adds_canonical_identity_and_resource_bridges() -> None:
    sql = _point_placements_sql()

    assert "CREATE TABLE IF NOT EXISTS experiment_catalog_points" in sql
    assert "ADD COLUMN IF NOT EXISTS canonical_point_id text REFERENCES experiment_catalog_points" in sql
    assert "row_number() OVER" in sql
    assert "PARTITION BY canonical_point_id" in sql
    assert "experiment_catalog_point_identity_map" in sql
    assert "grouping_decision" in sql
    assert "'question_reference_rows'" in sql
    assert "ALTER TABLE experiment_questions" in sql
    assert "primary_canonical_point_ids text[] NOT NULL DEFAULT '{}'" in sql
    assert "source_placement_node_ids text[] NOT NULL DEFAULT '{}'" in sql
    assert "ALTER TABLE experiment_question_attempts" in sql
    assert "canonical_point_id text REFERENCES experiment_catalog_points" in sql
    assert "ALTER TABLE student_posttest_sessions" in sql
    assert "canonical_point_ids jsonb NOT NULL DEFAULT '[]'::jsonb" in sql
    assert "idx_experiment_catalog_nodes_canonical_point" in sql
    assert "idx_experiment_catalog_point_placement_parent_canonical" in sql
    assert "node_kind = 'point' AND canonical_point_id IS NOT NULL" in sql
    assert "node_kind = 'directory' AND canonical_point_id IS NULL" in sql
