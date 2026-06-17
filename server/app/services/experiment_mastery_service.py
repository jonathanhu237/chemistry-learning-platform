from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text

from server.app.mastery import DEFAULT_EXPERIMENT_MASTERY_PROB, update_experiment_mastery


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=str)


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
            "mastery_prob": float(row["mastery_prob"]),
            "evidence_count": int(row["evidence_count"] or 0),
        }
        for row in session.execute(
            text(
                """
                SELECT experiment_id, mastery_prob, evidence_count
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
            "evidence_count": int(state.get("evidence_count") or 0) + 1,
        }

    for experiment_id, state in next_states.items():
        session.execute(
            text(
                """
                INSERT INTO student_experiment_mastery (
                  student_id, class_id, experiment_id, mastery_prob, mastery_score,
                  evidence_count, last_evidence_kind, metadata, updated_at
                )
                VALUES (
                  :student_id, :class_id, :experiment_id, :mastery_prob, :mastery_score,
                  :evidence_count, :last_evidence_kind, CAST(:metadata AS jsonb), now()
                )
                ON CONFLICT (student_id, experiment_id)
                DO UPDATE SET
                  class_id = COALESCE(EXCLUDED.class_id, student_experiment_mastery.class_id),
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
                "mastery_prob": state["mastery_prob"],
                "mastery_score": state["mastery_score"],
                "evidence_count": state["evidence_count"],
                "last_evidence_kind": evidence_kind,
                "metadata": _json({"evidence_kind": evidence_kind, "evidence_id": evidence_id}),
            },
        )
