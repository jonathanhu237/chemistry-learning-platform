from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text

from server.app.mastery import DEFAULT_EXPERIMENT_MASTERY_PROB, update_experiment_mastery


_CREATE_POINT_MASTERY_SQL = """
CREATE TABLE IF NOT EXISTS student_point_mastery (
  student_id text NOT NULL,
  class_id text REFERENCES classes(id) ON DELETE SET NULL,
  point_node_id text NOT NULL REFERENCES experiment_catalog_nodes(id) ON DELETE CASCADE,
  experiment_id text REFERENCES formal_experiments(id) ON DELETE SET NULL,
  canonical_point_id text REFERENCES experiment_catalog_points(id) ON DELETE SET NULL,
  mastery_prob numeric NOT NULL DEFAULT 0.5,
  mastery_score numeric NOT NULL DEFAULT 50,
  evidence_count int NOT NULL DEFAULT 0,
  last_evidence_kind text,
  metadata jsonb NOT NULL DEFAULT '{}'::jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  updated_at timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (student_id, point_node_id)
);

CREATE INDEX IF NOT EXISTS idx_student_point_mastery_class
  ON student_point_mastery(class_id, point_node_id, mastery_score);

CREATE INDEX IF NOT EXISTS idx_student_point_mastery_experiment
  ON student_point_mastery(student_id, experiment_id, mastery_score)
  WHERE experiment_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_student_point_mastery_canonical
  ON student_point_mastery(canonical_point_id, mastery_score)
  WHERE canonical_point_id IS NOT NULL;
"""


def ensure_student_point_mastery_table(session: Any) -> None:
    session.connection().exec_driver_sql(_CREATE_POINT_MASTERY_SQL)


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=str)


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def update_point_mastery_from_attempt_rows(
    session: Any,
    *,
    student_id: str,
    class_id: str | None,
    attempt_rows: list[dict[str, Any]],
    evidence_kind: str,
    evidence_id: str | None = None,
) -> None:
    ensure_student_point_mastery_table(session)
    point_ids = sorted(
        {
            str(point_id)
            for row in attempt_rows
            for point_id in (
                _as_list(row.get("source_placement_node_ids"))
                or _as_list(row.get("point_node_ids"))
                or _as_list(row.get("point_node_id"))
            )
            if str(point_id).strip()
        }
    )
    if not point_ids:
        return

    point_meta = {
        str(row["point_node_id"]): {
            "point_node_id": str(row["point_node_id"]),
            "canonical_point_id": str(row.get("canonical_point_id") or "") or None,
            "experiment_id": str(row.get("experiment_id") or "") or None,
        }
        for row in session.execute(
            text(
                """
                SELECT n.id AS point_node_id,
                       n.canonical_point_id,
                       fe.id AS experiment_id
                FROM experiment_catalog_nodes n
                LEFT JOIN LATERAL (
                  WITH RECURSIVE path AS (
                    SELECT id, parent_id, title, 0 AS depth
                    FROM experiment_catalog_nodes
                    WHERE id = n.id
                    UNION ALL
                    SELECT parent.id, parent.parent_id, parent.title, path.depth + 1
                    FROM experiment_catalog_nodes parent
                    JOIN path ON path.parent_id = parent.id
                  )
                  SELECT id
                  FROM path
                  WHERE parent_id IS NULL
                  ORDER BY depth DESC
                  LIMIT 1
                ) root ON true
                LEFT JOIN formal_experiments fe
                  ON fe.metadata->>'catalog_root_node_id' = root.id
                WHERE n.id = ANY(:point_ids)
                  AND n.node_kind = 'point'
                  AND n.status = 'published'
                """
            ),
            {"point_ids": point_ids},
        ).mappings()
    }
    if not point_meta:
        return

    current = {
        str(row["point_node_id"]): {
            "mastery_prob": float(row["mastery_prob"]),
            "evidence_count": int(row["evidence_count"] or 0),
        }
        for row in session.execute(
            text(
                """
                SELECT point_node_id, mastery_prob, evidence_count
                FROM student_point_mastery
                WHERE student_id = :student_id
                  AND point_node_id = ANY(:point_ids)
                """
            ),
            {"student_id": student_id, "point_ids": list(point_meta)},
        ).mappings()
    }

    next_states: dict[str, dict[str, Any]] = {}
    for row in attempt_rows:
        raw_point_ids = (
            _as_list(row.get("source_placement_node_ids"))
            or _as_list(row.get("point_node_ids"))
            or _as_list(row.get("point_node_id"))
        )
        for point_id in raw_point_ids:
            point_id = str(point_id).strip()
            if point_id not in point_meta:
                continue
            if not point_meta[point_id].get("experiment_id") and row.get("experiment_id"):
                point_meta[point_id]["experiment_id"] = str(row.get("experiment_id") or "") or None
            state = next_states.get(point_id) or current.get(
                point_id,
                {"mastery_prob": DEFAULT_EXPERIMENT_MASTERY_PROB, "evidence_count": 0},
            )
            updated = update_experiment_mastery(
                state.get("mastery_prob"),
                question_type=str(row.get("question_type") or "single_choice"),
                correct=bool(row.get("correct")),
            )
            next_states[point_id] = {
                **updated,
                "evidence_count": int(state.get("evidence_count") or 0) + 1,
            }

    for point_id, state in next_states.items():
        meta = point_meta[point_id]
        session.execute(
            text(
                """
                INSERT INTO student_point_mastery (
                  student_id, class_id, point_node_id, experiment_id, canonical_point_id,
                  mastery_prob, mastery_score, evidence_count,
                  last_evidence_kind, metadata, updated_at
                )
                VALUES (
                  :student_id, :class_id, :point_node_id, :experiment_id, :canonical_point_id,
                  :mastery_prob, :mastery_score, :evidence_count,
                  :last_evidence_kind, CAST(:metadata AS jsonb), now()
                )
                ON CONFLICT (student_id, point_node_id)
                DO UPDATE SET
                  class_id = COALESCE(EXCLUDED.class_id, student_point_mastery.class_id),
                  experiment_id = COALESCE(EXCLUDED.experiment_id, student_point_mastery.experiment_id),
                  canonical_point_id = COALESCE(EXCLUDED.canonical_point_id, student_point_mastery.canonical_point_id),
                  mastery_prob = EXCLUDED.mastery_prob,
                  mastery_score = EXCLUDED.mastery_score,
                  evidence_count = EXCLUDED.evidence_count,
                  last_evidence_kind = EXCLUDED.last_evidence_kind,
                  metadata = EXCLUDED.metadata,
                  updated_at = now()
                """
            ),
            {
                "student_id": student_id,
                "class_id": class_id,
                "point_node_id": point_id,
                "experiment_id": meta.get("experiment_id"),
                "canonical_point_id": meta.get("canonical_point_id"),
                "mastery_prob": state["mastery_prob"],
                "mastery_score": state["mastery_score"],
                "evidence_count": state["evidence_count"],
                "last_evidence_kind": evidence_kind,
                "metadata": _json(
                    {
                        "evidence_kind": evidence_kind,
                        "evidence_id": evidence_id,
                        "point_node_id": point_id,
                        "canonical_point_id": meta.get("canonical_point_id"),
                        "experiment_id": meta.get("experiment_id"),
                    }
                ),
            },
        )


def update_experiment_mastery_from_attempt_rows(
    session: Any,
    *,
    student_id: str,
    class_id: str | None,
    attempt_rows: list[dict[str, Any]],
    evidence_kind: str,
    evidence_id: str | None = None,
) -> None:
    experiment_ids = sorted(
        {
            str(row.get("experiment_id") or "").strip()
            for row in attempt_rows
            if str(row.get("experiment_id") or "").strip()
        }
    )
    if not experiment_ids:
        return

    valid_experiment_ids = {
        str(row["id"])
        for row in session.execute(
            text("SELECT id FROM formal_experiments WHERE id = ANY(:experiment_ids)"),
            {"experiment_ids": experiment_ids},
        ).mappings()
    }
    if not valid_experiment_ids:
        return

    current = {
        str(row["experiment_id"]): {
            "point_node_id": str(row.get("point_node_id") or "") or None,
            "canonical_point_id": str(row.get("canonical_point_id") or "") or None,
            "source_placement_node_id": str(row.get("source_placement_node_id") or "") or None,
            "mastery_prob": float(row["mastery_prob"]),
            "evidence_count": int(row["evidence_count"] or 0),
        }
        for row in session.execute(
            text(
                """
                SELECT experiment_id, point_node_id, canonical_point_id, source_placement_node_id,
                       mastery_prob, evidence_count
                FROM student_experiment_mastery
                WHERE student_id = :student_id
                  AND experiment_id = ANY(:experiment_ids)
                """
            ),
            {"student_id": student_id, "experiment_ids": list(valid_experiment_ids)},
        ).mappings()
    }

    next_states: dict[str, dict[str, Any]] = {}
    for row in attempt_rows:
        experiment_id = str(row.get("experiment_id") or "").strip()
        if experiment_id not in valid_experiment_ids:
            continue
        point_node_id = str(row.get("point_node_id") or "").strip() or None
        canonical_point_id = str(row.get("canonical_point_id") or "").strip() or None
        source_placement_node_id = str(row.get("source_placement_node_id") or "").strip() or point_node_id
        state = next_states.get(experiment_id) or current.get(
            experiment_id,
            {"mastery_prob": DEFAULT_EXPERIMENT_MASTERY_PROB, "evidence_count": 0},
        )
        updated = update_experiment_mastery(
            state.get("mastery_prob"),
            question_type=str(row.get("question_type") or "single_choice"),
            correct=bool(row.get("correct")),
        )
        next_states[experiment_id] = {
            **updated,
            "point_node_id": point_node_id or state.get("point_node_id"),
            "canonical_point_id": canonical_point_id or state.get("canonical_point_id"),
            "source_placement_node_id": source_placement_node_id or state.get("source_placement_node_id"),
            "evidence_count": int(state.get("evidence_count") or 0) + 1,
        }

    for experiment_id, state in next_states.items():
        session.execute(
            text(
                """
                INSERT INTO student_experiment_mastery (
                  student_id, class_id, experiment_id, point_node_id, canonical_point_id,
                  source_placement_node_id, mastery_prob, mastery_score,
                  evidence_count, last_evidence_kind, metadata, updated_at
                )
                VALUES (
                  :student_id, :class_id, :experiment_id, :point_node_id, :canonical_point_id,
                  :source_placement_node_id, :mastery_prob, :mastery_score,
                  :evidence_count, :last_evidence_kind, CAST(:metadata AS jsonb), now()
                )
                ON CONFLICT (student_id, experiment_id)
                DO UPDATE SET
                  class_id = COALESCE(EXCLUDED.class_id, student_experiment_mastery.class_id),
                  point_node_id = COALESCE(EXCLUDED.point_node_id, student_experiment_mastery.point_node_id),
                  canonical_point_id = COALESCE(EXCLUDED.canonical_point_id, student_experiment_mastery.canonical_point_id),
                  source_placement_node_id = COALESCE(EXCLUDED.source_placement_node_id, student_experiment_mastery.source_placement_node_id),
                  mastery_prob = EXCLUDED.mastery_prob,
                  mastery_score = EXCLUDED.mastery_score,
                  evidence_count = EXCLUDED.evidence_count,
                  last_evidence_kind = EXCLUDED.last_evidence_kind,
                  metadata = EXCLUDED.metadata,
                  updated_at = now()
                """
            ),
            {
                "student_id": student_id,
                "class_id": class_id,
                "experiment_id": experiment_id,
                "point_node_id": state.get("point_node_id"),
                "canonical_point_id": state.get("canonical_point_id"),
                "source_placement_node_id": state.get("source_placement_node_id"),
                "mastery_prob": state["mastery_prob"],
                "mastery_score": state["mastery_score"],
                "evidence_count": state["evidence_count"],
                "last_evidence_kind": evidence_kind,
                "metadata": _json(
                    {
                        "evidence_kind": evidence_kind,
                        "evidence_id": evidence_id,
                        "point_node_id": state.get("point_node_id"),
                        "canonical_point_id": state.get("canonical_point_id"),
                        "source_placement_node_id": state.get("source_placement_node_id"),
                    }
                ),
            },
        )
