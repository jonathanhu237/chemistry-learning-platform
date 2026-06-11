from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import text

from server.app.config import ROOT

DEFAULT_FORMAL_EXPERIMENTS_PATH = ROOT / "data" / "seed" / "formal_experiments.json"


def load_formal_experiment_catalog(path: Path = DEFAULT_FORMAL_EXPERIMENTS_PATH) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    experiments = list(data.get("experiments") or [])
    validate_formal_experiment_catalog(experiments)
    return experiments


def validate_formal_experiment_catalog(experiments: list[dict[str, Any]]) -> None:
    if not experiments:
        raise ValueError("Formal experiment catalog must contain at least one item")
    codes = {str(item.get("code") or "") for item in experiments}
    if "" in codes or len(codes) != len(experiments):
        raise ValueError("Formal experiment codes must be present and unique")
    ids = [str(item.get("id") or "") for item in experiments]
    if "" in ids or len(set(ids)) != len(ids):
        raise ValueError("Formal experiment ids must be present and unique")
    for item in experiments:
        if not item.get("title"):
            raise ValueError(f"Experiment {item.get('code')} is missing title")
        if not item.get("chapter_bindings"):
            raise ValueError(f"Experiment {item.get('code')} must bind to at least one chapter")
        for binding in item.get("chapter_bindings") or []:
            if binding.get("coverage_type") not in {"primary", "partial", "supporting"}:
                raise ValueError(f"Invalid coverage_type for {item.get('code')}: {binding.get('coverage_type')}")


def seed_formal_experiments(session: Any, experiments: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    experiments = experiments or load_formal_experiment_catalog()
    validate_formal_experiment_catalog(experiments)
    missing_chapters: set[str] = set()
    binding_count = 0
    catalog_ids = [str(item["id"]) for item in experiments]
    for item in experiments:
        session.execute(
            text(
                """
                INSERT INTO formal_experiments (
                  id, code, title, title_en, summary, status, display_order,
                  source_refs, metadata, published_at, updated_at
                )
                VALUES (
                  :id, :code, :title, :title_en, :summary, :status, :display_order,
                  CAST(:source_refs AS jsonb), CAST(:metadata AS jsonb),
                  CASE WHEN :status = 'published' THEN COALESCE(CAST(:published_at AS timestamptz), now()) ELSE NULL END,
                  now()
                )
                ON CONFLICT (id) DO UPDATE SET
                  code = EXCLUDED.code,
                  title = EXCLUDED.title,
                  title_en = EXCLUDED.title_en,
                  summary = EXCLUDED.summary,
                  status = EXCLUDED.status,
                  display_order = EXCLUDED.display_order,
                  source_refs = EXCLUDED.source_refs,
                  metadata = formal_experiments.metadata || EXCLUDED.metadata,
                  published_at = COALESCE(formal_experiments.published_at, EXCLUDED.published_at),
                  updated_at = now()
                """
            ),
            {
                "id": item["id"],
                "code": item["code"],
                "title": item["title"],
                "title_en": item.get("title_en"),
                "summary": item.get("summary"),
                "status": item.get("status") or "published",
                "display_order": item.get("display_order") or 0,
                "source_refs": json.dumps(item.get("source_refs") or [], ensure_ascii=False),
                "metadata": json.dumps({"formal_catalog": True, **(item.get("metadata") or {})}, ensure_ascii=False),
                "published_at": item.get("published_at"),
            },
        )
        session.execute(
            text("DELETE FROM experiment_chapter_bindings WHERE experiment_id = :experiment_id"),
            {"experiment_id": item["id"]},
        )
        for binding in item.get("chapter_bindings") or []:
            chapter_id = binding.get("chapter_id")
            chapter_exists = session.execute(
                text("SELECT 1 FROM chapters WHERE id = :chapter_id"),
                {"chapter_id": chapter_id},
            ).first()
            if not chapter_exists:
                missing_chapters.add(str(chapter_id))
                continue
            session.execute(
                text(
                    """
                    INSERT INTO experiment_chapter_bindings (
                      experiment_id, chapter_id, coverage_type, notes, sort_order, updated_at
                    )
                    VALUES (
                      :experiment_id, :chapter_id, :coverage_type, :notes, :sort_order, now()
                    )
                    ON CONFLICT (experiment_id, chapter_id) DO UPDATE SET
                      coverage_type = EXCLUDED.coverage_type,
                      notes = EXCLUDED.notes,
                      sort_order = EXCLUDED.sort_order,
                      updated_at = now()
                    """
                ),
                {
                    "experiment_id": item["id"],
                    "chapter_id": chapter_id,
                    "coverage_type": binding.get("coverage_type") or "primary",
                    "notes": binding.get("notes"),
                    "sort_order": binding.get("sort_order") or 0,
                },
            )
            binding_count += 1
    session.execute(
        text(
            """
            DELETE FROM formal_experiments
            WHERE COALESCE(metadata->>'formal_catalog', 'false') = 'true'
              AND NOT (id = ANY(:catalog_ids))
            """
        ),
        {"catalog_ids": catalog_ids},
    )
    sync_formal_experiments_to_legacy_table(session)
    return {
        "experiment_count": len(experiments),
        "binding_count": binding_count,
        "missing_chapters": sorted(missing_chapters),
    }


def sync_formal_experiments_to_legacy_table(session: Any) -> None:
    session.execute(
        text(
            """
            DELETE FROM links
            WHERE (
                from_type = 'experiment'
                AND NOT EXISTS (
                  SELECT 1 FROM formal_experiments fe
                  WHERE fe.id = links.from_id AND fe.status <> 'archived'
                )
              )
              OR (
                to_type = 'experiment'
                AND NOT EXISTS (
                  SELECT 1 FROM formal_experiments fe
                  WHERE fe.id = links.to_id AND fe.status <> 'archived'
                )
              )
            """
        )
    )
    session.execute(
        text(
            """
            UPDATE questions
            SET related_experiment_ids = ARRAY(
              SELECT experiment_id
              FROM unnest(related_experiment_ids) AS experiment_id
              WHERE EXISTS (
                SELECT 1 FROM formal_experiments fe
                WHERE fe.id = experiment_id AND fe.status <> 'archived'
              )
            )
            WHERE related_experiment_ids IS NOT NULL
            """
        )
    )
    session.execute(
        text(
            """
            UPDATE source_chunks
            SET related_experiment_ids = ARRAY(
              SELECT experiment_id
              FROM unnest(related_experiment_ids) AS experiment_id
              WHERE EXISTS (
                SELECT 1 FROM formal_experiments fe
                WHERE fe.id = experiment_id AND fe.status <> 'archived'
              )
            )
            WHERE related_experiment_ids IS NOT NULL
            """
        )
    )
    session.execute(
        text(
            """
            DELETE FROM experiment_learning_cards
            WHERE NOT EXISTS (
              SELECT 1 FROM formal_experiments fe
              WHERE fe.id = experiment_learning_cards.experiment_id
                AND fe.status <> 'archived'
            )
            """
        )
    )
    session.execute(
        text(
            """
            DELETE FROM student_events
            WHERE experiment_id IS NOT NULL
              AND NOT EXISTS (
                SELECT 1 FROM formal_experiments fe
                WHERE fe.id = student_events.experiment_id
                  AND fe.status <> 'archived'
              )
            """
        )
    )
    session.execute(
        text(
            """
            INSERT INTO experiments (
              id, name, element_area, element_group, objective, video_url, media_status,
              resource_mode, review_required, content_status, metadata, published_at, updated_at
            )
            SELECT
              fe.id,
              fe.title,
              NULL,
              (
                SELECT ecb.chapter_id
                FROM experiment_chapter_bindings ecb
                WHERE ecb.experiment_id = fe.id
                ORDER BY CASE ecb.coverage_type WHEN 'primary' THEN 0 WHEN 'partial' THEN 1 ELSE 2 END,
                         ecb.sort_order,
                         ecb.chapter_id
                LIMIT 1
              ),
              fe.summary,
              NULL,
              'pending',
              'formal_experiment_fk',
              false,
              fe.status,
              jsonb_build_object('formal_experiment_id', fe.id, 'formal_catalog', true),
              fe.published_at,
              now()
            FROM formal_experiments fe
            WHERE fe.status <> 'archived'
            ON CONFLICT (id) DO UPDATE SET
              name = EXCLUDED.name,
              element_group = EXCLUDED.element_group,
              objective = EXCLUDED.objective,
              resource_mode = EXCLUDED.resource_mode,
              review_required = EXCLUDED.review_required,
              content_status = EXCLUDED.content_status,
              metadata = experiments.metadata || EXCLUDED.metadata,
              updated_at = now()
            """
        )
    )
    session.execute(
        text(
            """
            DELETE FROM experiments e
            WHERE e.resource_mode <> 'formal_experiment_fk'
               OR NOT EXISTS (
                SELECT 1
                FROM formal_experiments fe
                WHERE fe.id = e.id
                  AND fe.status <> 'archived'
              )
            """
        )
    )
