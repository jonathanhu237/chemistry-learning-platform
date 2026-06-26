from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import bindparam, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.app.domains.questions.bank import _validate_question_payload
from server.app.infrastructure.database import apply_migrations, db_session, get_session_factory

DEFAULT_SEED_PATH = ROOT / "data" / "seed" / "question_banks" / "current_catalog_node_question_bank_seed_v1.json"
SEED_ARTIFACT_TYPE = "current_catalog_node_question_bank_seed"
SEED_VERSION = "current-catalog-node-question-bank-seed-v1"
EXPECTED_BANK_COUNT = 78
EXPECTED_QUESTION_COUNT = 2311
EXPECTED_STATUS = "published"
EXPECTED_BANK_KIND = "generated"
OBJECTIVE_TYPES = {"single_choice", "true_false", "fill_blank"}

BANK_COLUMNS = [
    "id",
    "experiment_id",
    "bank_kind",
    "title",
    "status",
    "source_label",
    "imported_by",
    "metadata",
    "created_at",
    "updated_at",
]

QUESTION_COLUMNS = [
    "id",
    "bank_id",
    "experiment_id",
    "generation_id",
    "question_type",
    "stem",
    "options",
    "answer",
    "explanation",
    "difficulty",
    "related_chapter_ids",
    "related_knowledge_point_ids",
    "source_chunk_ids",
    "source_refs",
    "primary_point_node_ids",
    "primary_canonical_point_ids",
    "source_placement_node_ids",
    "status",
    "created_by",
    "published_by",
    "published_at",
    "metadata",
    "created_at",
    "updated_at",
]

SUPPLEMENTAL_EXPERIMENT_COLUMNS = [
    "id",
    "code",
    "title",
    "title_en",
    "summary",
    "status",
    "display_order",
    "source_refs",
    "metadata",
    "published_at",
    "created_at",
    "updated_at",
]

GENERATION_COLUMNS = [
    "id",
    "experiment_id",
    "prompt",
    "question_types",
    "difficulty",
    "requested_count",
    "provider",
    "model",
    "mode",
    "rag_sources",
    "warning",
    "status",
    "created_by",
    "metadata",
    "created_at",
    "updated_at",
]

FINGERPRINT_COLUMNS = [
    "id",
    "owner_kind",
    "owner_id",
    "point_node_id",
    "text_hash",
    "embedding_model",
    "embedding",
    "created_at",
    "updated_at",
]


def _json_default(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return str(value)


def _json_param(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=_json_default)


def _json_array_param(value: Any) -> str:
    return json.dumps(value if value is not None else [], ensure_ascii=False, default=_json_default)


def _row_payload(row: Any, columns: list[str]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    for column in columns:
        value = row.get(column)
        if isinstance(value, datetime):
            value = value.isoformat()
        elif isinstance(value, date):
            value = value.isoformat()
        elif value is not None and not isinstance(value, (str, int, float, bool, dict, list)):
            value = str(value)
        payload[column] = value
    return payload


def _summary(
    question_banks: list[dict[str, Any]],
    questions: list[dict[str, Any]],
    *,
    supplemental_experiments: list[dict[str, Any]] | None = None,
    generations: list[dict[str, Any]] | None = None,
    fingerprints: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "bank_count": len(question_banks),
        "question_count": len(questions),
        "supplemental_experiment_count": len(supplemental_experiments or []),
        "generation_count": len(generations or []),
        "question_fingerprint_count": len(fingerprints or []),
        "question_type_counts": dict(Counter(str(item.get("question_type") or "") for item in questions)),
        "question_status_counts": dict(Counter(str(item.get("status") or "") for item in questions)),
        "bank_kind_counts": dict(Counter(str(item.get("bank_kind") or "") for item in question_banks)),
        "bank_status_counts": dict(Counter(str(item.get("status") or "") for item in question_banks)),
        "experiment_count": len({str(item.get("experiment_id") or "") for item in question_banks}),
        "questions_with_primary_point_nodes": sum(1 for item in questions if item.get("primary_point_node_ids")),
        "questions_with_canonical_points": sum(1 for item in questions if item.get("primary_canonical_point_ids")),
        "questions_with_source_refs": sum(1 for item in questions if item.get("source_refs")),
        "questions_with_source_chunks": sum(1 for item in questions if item.get("source_chunk_ids")),
        "questions_with_point_aware_metadata": sum(
            1
            for item in questions
            if isinstance(item.get("metadata"), dict) and item["metadata"].get("point_aware_question_bank") is True
        ),
        "distinct_primary_point_nodes": len(
            {str(node_id) for item in questions for node_id in (item.get("primary_point_node_ids") or [])}
        ),
        "distinct_primary_canonical_points": len(
            {str(point_id) for item in questions for point_id in (item.get("primary_canonical_point_ids") or [])}
        ),
    }


def _portable_row(row: Any, columns: list[str], *, clear_user_fields: bool = False) -> dict[str, Any]:
    payload = _row_payload(row, columns)
    if clear_user_fields:
        for key in ["imported_by", "created_by", "published_by"]:
            if key in payload:
                payload[key] = None
    return payload


def export_seed(session: Any) -> dict[str, Any]:
    bank_rows = session.execute(
        text(
            """
            SELECT id, experiment_id, bank_kind, title, status, source_label, imported_by,
                   metadata, created_at, updated_at
            FROM experiment_question_banks
            WHERE status = :status
              AND bank_kind = :bank_kind
            ORDER BY experiment_id, id
            """
        ),
        {"status": EXPECTED_STATUS, "bank_kind": EXPECTED_BANK_KIND},
    ).mappings().all()
    bank_ids = [row["id"] for row in bank_rows]
    if bank_ids:
        question_rows = session.execute(
            text(
                """
                SELECT id, bank_id, experiment_id, generation_id, question_type, stem, options,
                       answer, explanation, difficulty, related_chapter_ids,
                       related_knowledge_point_ids, source_chunk_ids, source_refs,
                       primary_point_node_ids, primary_canonical_point_ids, source_placement_node_ids,
                       status, created_by, published_by, published_at, metadata, created_at, updated_at
                FROM experiment_questions
                WHERE status = :status
                  AND bank_id IN :bank_ids
                ORDER BY experiment_id, bank_id, id
                """
            ).bindparams(bindparam("bank_ids", expanding=True)),
            {"status": EXPECTED_STATUS, "bank_ids": bank_ids},
        ).mappings().all()
    else:
        question_rows = []
    banks = [_portable_row(row, BANK_COLUMNS, clear_user_fields=True) for row in bank_rows]
    questions = [_portable_row(row, QUESTION_COLUMNS, clear_user_fields=True) for row in question_rows]
    seed_experiment_ids = {
        str(item.get("id") or "").strip()
        for item in (
            json.loads((ROOT / "data" / "seed" / "formal_experiments.json").read_text(encoding="utf-8-sig")).get(
                "experiments"
            )
            or []
        )
        if isinstance(item, dict) and str(item.get("id") or "").strip()
    }
    referenced_experiment_ids = {
        str(item.get("experiment_id") or "").strip()
        for item in [*banks, *questions]
        if str(item.get("experiment_id") or "").strip()
    }
    supplemental_experiment_ids = sorted(referenced_experiment_ids - seed_experiment_ids)
    if supplemental_experiment_ids:
        supplemental_rows = session.execute(
            text(
                """
                SELECT id, code, title, title_en, summary, status, display_order, source_refs,
                       metadata, published_at, created_at, updated_at
                FROM formal_experiments
                WHERE id IN :experiment_ids
                ORDER BY display_order, id
                """
            ).bindparams(bindparam("experiment_ids", expanding=True)),
            {"experiment_ids": supplemental_experiment_ids},
        ).mappings().all()
    else:
        supplemental_rows = []
    generation_ids = {
        str(item.get("generation_id") or "").strip()
        for item in questions
        if str(item.get("generation_id") or "").strip()
    }
    if generation_ids:
        generation_rows = session.execute(
            text(
                """
                SELECT id, experiment_id, prompt, question_types, difficulty, requested_count,
                       provider, model, mode, rag_sources, warning, status, created_by,
                       metadata, created_at, updated_at
                FROM experiment_question_generations
                WHERE id IN :generation_ids
                ORDER BY created_at, id
                """
            ).bindparams(bindparam("generation_ids", expanding=True)),
            {"generation_ids": sorted(generation_ids)},
        ).mappings().all()
    else:
        generation_rows = []
    question_ids = {str(item.get("id") or "").strip() for item in questions if str(item.get("id") or "").strip()}
    if question_ids:
        fingerprint_rows = session.execute(
            text(
                """
                SELECT id, owner_kind, owner_id, point_node_id, text_hash, embedding_model,
                       embedding, created_at, updated_at
                FROM question_semantic_fingerprints
                WHERE owner_kind = 'question'
                  AND CAST(owner_id AS text) IN :question_ids
                ORDER BY point_node_id, owner_id, id
                """
            ).bindparams(bindparam("question_ids", expanding=True)),
            {"question_ids": sorted(question_ids)},
        ).mappings().all()
    else:
        fingerprint_rows = []
    supplemental_experiments = [_row_payload(row, SUPPLEMENTAL_EXPERIMENT_COLUMNS) for row in supplemental_rows]
    generations = [_portable_row(row, GENERATION_COLUMNS, clear_user_fields=True) for row in generation_rows]
    fingerprints = [_row_payload(row, FINGERPRINT_COLUMNS) for row in fingerprint_rows]
    return {
        "metadata": {
            "artifact_type": SEED_ARTIFACT_TYPE,
            "version": SEED_VERSION,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "source": "experiment_question_banks + experiment_questions + portable supporting rows",
            "status_filter": EXPECTED_STATUS,
            "bank_kind_filter": EXPECTED_BANK_KIND,
            "user_foreign_keys": "cleared for portable import",
            "expected_counts": {
                "question_banks": EXPECTED_BANK_COUNT,
                "questions": EXPECTED_QUESTION_COUNT,
            },
            "summary": _summary(
                banks,
                questions,
                supplemental_experiments=supplemental_experiments,
                generations=generations,
                fingerprints=fingerprints,
            ),
        },
        "supplemental_formal_experiments": supplemental_experiments,
        "question_generations": generations,
        "question_banks": banks,
        "questions": questions,
        "question_semantic_fingerprints": fingerprints,
    }


def write_seed(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=_json_default) + "\n", encoding="utf-8")


def load_seed(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    metadata = payload.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError(f"{path} metadata must be an object")
    if metadata.get("artifact_type") != SEED_ARTIFACT_TYPE:
        raise ValueError(f"{path} artifact_type must be {SEED_ARTIFACT_TYPE!r}")
    if metadata.get("version") != SEED_VERSION:
        raise ValueError(f"{path} version must be {SEED_VERSION!r}")
    if not isinstance(payload.get("question_banks"), list):
        raise ValueError(f"{path} question_banks must be a list")
    if not isinstance(payload.get("questions"), list):
        raise ValueError(f"{path} questions must be a list")
    for field in ["supplemental_formal_experiments", "question_generations", "question_semantic_fingerprints"]:
        if field in payload and not isinstance(payload.get(field), list):
            raise ValueError(f"{path} {field} must be a list")
    return payload


def _existing_ids(session: Any, *, table: str, column: str, ids: set[str]) -> set[str]:
    if not ids:
        return set()
    rows = session.execute(
        text(f"SELECT {column} FROM {table} WHERE {column} IN :ids").bindparams(bindparam("ids", expanding=True)),
        {"ids": sorted(ids)},
    ).all()
    return {str(row[0]) for row in rows}


def validate_seed_references(session: Any, payload: dict[str, Any]) -> dict[str, Any]:
    banks = [item for item in payload.get("question_banks") or [] if isinstance(item, dict)]
    questions = [item for item in payload.get("questions") or [] if isinstance(item, dict)]
    supplemental_experiments = [
        item for item in payload.get("supplemental_formal_experiments") or [] if isinstance(item, dict)
    ]
    generations = [item for item in payload.get("question_generations") or [] if isinstance(item, dict)]
    fingerprints = [item for item in payload.get("question_semantic_fingerprints") or [] if isinstance(item, dict)]
    bank_ids = {str(item.get("id") or "").strip() for item in banks}
    question_bank_ids = {str(item.get("bank_id") or "").strip() for item in questions}
    experiment_ids = {
        str(item.get("experiment_id") or "").strip()
        for item in [*banks, *questions]
        if str(item.get("experiment_id") or "").strip()
    }
    supplemental_experiment_ids = {
        str(item.get("id") or "").strip() for item in supplemental_experiments if str(item.get("id") or "").strip()
    }
    generation_ids = {str(item.get("id") or "").strip() for item in generations if str(item.get("id") or "").strip()}
    question_generation_ids = {
        str(item.get("generation_id") or "").strip()
        for item in questions
        if str(item.get("generation_id") or "").strip()
    }
    question_ids = {str(item.get("id") or "").strip() for item in questions}
    fingerprint_owner_ids = {
        str(item.get("owner_id") or "").strip() for item in fingerprints if str(item.get("owner_id") or "").strip()
    }
    point_node_ids = {
        str(node_id).strip()
        for item in questions
        for node_id in (item.get("primary_point_node_ids") or [])
        if str(node_id).strip()
    }
    point_node_ids.update(
        str(item.get("point_node_id") or "").strip()
        for item in fingerprints
        if str(item.get("point_node_id") or "").strip()
    )
    canonical_point_ids = {
        str(point_id).strip()
        for item in questions
        for point_id in (item.get("primary_canonical_point_ids") or [])
        if str(point_id).strip()
    }
    chunk_ids = {
        str(chunk_id).strip()
        for item in questions
        for chunk_id in (item.get("source_chunk_ids") or [])
        if str(chunk_id).strip()
    }
    existing_experiments = _existing_ids(session, table="formal_experiments", column="id", ids=experiment_ids)
    existing_experiments.update(supplemental_experiment_ids)
    existing_nodes = _existing_ids(session, table="experiment_catalog_nodes", column="id", ids=point_node_ids)
    existing_canonical_points = _existing_ids(
        session,
        table="experiment_catalog_points",
        column="id",
        ids=canonical_point_ids,
    )
    existing_chunks = _existing_ids(session, table="source_chunks", column="id", ids=chunk_ids)
    return {
        "bank_ids": len(bank_ids),
        "question_bank_ids": len(question_bank_ids),
        "experiment_ids": len(experiment_ids),
        "supplemental_experiment_ids": len(supplemental_experiment_ids),
        "generation_ids": len(generation_ids),
        "question_generation_ids": len(question_generation_ids),
        "fingerprint_owner_ids": len(fingerprint_owner_ids),
        "point_node_ids": len(point_node_ids),
        "canonical_point_ids": len(canonical_point_ids),
        "chunk_ids": len(chunk_ids),
        "missing_question_bank_ids": sorted(question_bank_ids - bank_ids),
        "missing_experiment_ids": sorted(experiment_ids - existing_experiments),
        "missing_question_generation_ids": sorted(question_generation_ids - generation_ids),
        "missing_fingerprint_owner_ids": sorted(fingerprint_owner_ids - question_ids),
        "missing_point_node_ids": sorted(point_node_ids - existing_nodes),
        "missing_canonical_point_ids": sorted(canonical_point_ids - existing_canonical_points),
        "missing_chunk_ids": sorted(chunk_ids - existing_chunks),
    }


def validate_seed_payload(payload: dict[str, Any], *, session: Any | None = None) -> dict[str, Any]:
    errors: list[str] = []
    supplemental_experiments = [
        item for item in payload.get("supplemental_formal_experiments") or [] if isinstance(item, dict)
    ]
    generations = [item for item in payload.get("question_generations") or [] if isinstance(item, dict)]
    fingerprints = [item for item in payload.get("question_semantic_fingerprints") or [] if isinstance(item, dict)]
    banks = [item for item in payload.get("question_banks") or [] if isinstance(item, dict)]
    questions = [item for item in payload.get("questions") or [] if isinstance(item, dict)]
    if len(banks) != EXPECTED_BANK_COUNT:
        errors.append(f"question_banks: expected {EXPECTED_BANK_COUNT}, got {len(banks)}")
    if len(questions) != EXPECTED_QUESTION_COUNT:
        errors.append(f"questions: expected {EXPECTED_QUESTION_COUNT}, got {len(questions)}")
    bank_ids: set[str] = set()
    for index, bank in enumerate(banks, start=1):
        bank_id = str(bank.get("id") or "").strip()
        if not bank_id:
            errors.append(f"question_banks[{index}]: id is required")
        elif bank_id in bank_ids:
            errors.append(f"question_banks[{index}]: duplicate id {bank_id}")
        bank_ids.add(bank_id)
        if bank.get("bank_kind") != EXPECTED_BANK_KIND:
            errors.append(f"question_banks[{index}]: bank_kind must be {EXPECTED_BANK_KIND}")
        if bank.get("status") != EXPECTED_STATUS:
            errors.append(f"question_banks[{index}]: status must be {EXPECTED_STATUS}")
        if not str(bank.get("experiment_id") or "").strip():
            errors.append(f"question_banks[{index}]: experiment_id is required")
    supplemental_experiment_ids: set[str] = set()
    for index, experiment in enumerate(supplemental_experiments, start=1):
        experiment_id = str(experiment.get("id") or "").strip()
        if not experiment_id:
            errors.append(f"supplemental_formal_experiments[{index}]: id is required")
        elif experiment_id in supplemental_experiment_ids:
            errors.append(f"supplemental_formal_experiments[{index}]: duplicate id {experiment_id}")
        supplemental_experiment_ids.add(experiment_id)
        for key in ["code", "title", "status"]:
            if not str(experiment.get(key) or "").strip():
                errors.append(f"supplemental_formal_experiments[{index}]: {key} is required")
    generation_ids: set[str] = set()
    for index, generation in enumerate(generations, start=1):
        generation_id = str(generation.get("id") or "").strip()
        if not generation_id:
            errors.append(f"question_generations[{index}]: id is required")
        elif generation_id in generation_ids:
            errors.append(f"question_generations[{index}]: duplicate id {generation_id}")
        generation_ids.add(generation_id)
        if not str(generation.get("experiment_id") or "").strip():
            errors.append(f"question_generations[{index}]: experiment_id is required")
        if not str(generation.get("prompt") or "").strip():
            errors.append(f"question_generations[{index}]: prompt is required")
    question_ids: set[str] = set()
    for index, question in enumerate(questions, start=1):
        question_id = str(question.get("id") or "").strip()
        if not question_id:
            errors.append(f"questions[{index}]: id is required")
        elif question_id in question_ids:
            errors.append(f"questions[{index}]: duplicate id {question_id}")
        question_ids.add(question_id)
        if str(question.get("bank_id") or "").strip() not in bank_ids:
            errors.append(f"questions[{index}]: bank_id does not resolve")
        if question.get("status") != EXPECTED_STATUS:
            errors.append(f"questions[{index}]: status must be {EXPECTED_STATUS}")
        if question.get("question_type") not in OBJECTIVE_TYPES:
            errors.append(f"questions[{index}]: unsupported question_type {question.get('question_type')!r}")
        normalized, validation_errors = _validate_question_payload(question)
        if normalized is None or validation_errors:
            errors.append(f"questions[{index}]: {'; '.join(validation_errors)}")
            continue
        metadata = question.get("metadata") if isinstance(question.get("metadata"), dict) else {}
        legacy_point_aware = metadata.get("point_aware_question_bank") is True
        if not normalized.get("primary_point_node_ids") and not legacy_point_aware:
            errors.append(f"questions[{index}]: primary_point_node_ids are required unless legacy point-aware metadata is present")
        if not normalized.get("primary_canonical_point_ids") and not legacy_point_aware:
            errors.append(
                f"questions[{index}]: primary_canonical_point_ids are required unless legacy point-aware metadata is present"
            )
        if not question.get("source_refs"):
            errors.append(f"questions[{index}]: source_refs are required")
        if not question.get("source_chunk_ids"):
            errors.append(f"questions[{index}]: source_chunk_ids are required")
        if str(question.get("generation_id") or "").strip() and str(question.get("generation_id") or "").strip() not in generation_ids:
            errors.append(f"questions[{index}]: generation_id does not resolve")
        mock_probe = json.dumps(metadata, ensure_ascii=False).lower() + " " + str(question.get("explanation") or "").lower()
        if "mock" in mock_probe:
            errors.append(f"questions[{index}]: mock/fake question metadata or explanation is not allowed")
    for index, fingerprint in enumerate(fingerprints, start=1):
        if fingerprint.get("owner_kind") != "question":
            errors.append(f"question_semantic_fingerprints[{index}]: owner_kind must be 'question'")
        if str(fingerprint.get("owner_id") or "").strip() not in question_ids:
            errors.append(f"question_semantic_fingerprints[{index}]: owner_id does not resolve")
        if not str(fingerprint.get("point_node_id") or "").strip():
            errors.append(f"question_semantic_fingerprints[{index}]: point_node_id is required")
        if not str(fingerprint.get("embedding_model") or "").strip():
            errors.append(f"question_semantic_fingerprints[{index}]: embedding_model is required")
        if not isinstance(fingerprint.get("embedding"), list):
            errors.append(f"question_semantic_fingerprints[{index}]: embedding must be a list")
    references = None
    if session is not None:
        references = validate_seed_references(session, payload)
        for key in [
            "missing_question_bank_ids",
            "missing_experiment_ids",
            "missing_question_generation_ids",
            "missing_fingerprint_owner_ids",
            "missing_point_node_ids",
            "missing_canonical_point_ids",
            "missing_chunk_ids",
        ]:
            missing = references.get(key) or []
            if missing:
                errors.append(f"{key}: {', '.join(missing[:20])}")
    return {
        "ok": not errors,
        "errors": errors,
        "summary": _summary(
            banks,
            questions,
            supplemental_experiments=supplemental_experiments,
            generations=generations,
            fingerprints=fingerprints,
        ),
        "references": references,
    }


def import_seed(session: Any, payload: dict[str, Any], *, replace: bool = True) -> dict[str, Any]:
    validation = validate_seed_payload(payload, session=session)
    if not validation["ok"]:
        raise ValueError("Current question-bank seed validation failed:\n" + "\n".join(validation["errors"][:80]))
    supplemental_experiments = [
        item for item in payload.get("supplemental_formal_experiments") or [] if isinstance(item, dict)
    ]
    generations = [item for item in payload.get("question_generations") or [] if isinstance(item, dict)]
    banks = [item for item in payload.get("question_banks") or [] if isinstance(item, dict)]
    questions = [item for item in payload.get("questions") or [] if isinstance(item, dict)]
    fingerprints = [item for item in payload.get("question_semantic_fingerprints") or [] if isinstance(item, dict)]
    experiment_ids = sorted({str(item["experiment_id"]) for item in banks})
    question_ids = sorted({str(item.get("id") or "").strip() for item in questions if str(item.get("id") or "").strip()})
    generation_ids = sorted({str(item.get("id") or "").strip() for item in generations if str(item.get("id") or "").strip()})
    for experiment in supplemental_experiments:
        session.execute(
            text(
                """
                INSERT INTO formal_experiments (
                  id, code, title, title_en, summary, status, display_order, source_refs,
                  metadata, published_at, created_at, updated_at
                )
                VALUES (
                  :id, :code, :title, :title_en, :summary, :status, :display_order,
                  CAST(:source_refs AS jsonb), CAST(:metadata AS jsonb),
                  CAST(:published_at AS timestamptz),
                  COALESCE(CAST(:created_at AS timestamptz), now()),
                  COALESCE(CAST(:updated_at AS timestamptz), now())
                )
                ON CONFLICT (id) DO UPDATE SET
                  code = EXCLUDED.code,
                  title = EXCLUDED.title,
                  title_en = EXCLUDED.title_en,
                  summary = EXCLUDED.summary,
                  status = EXCLUDED.status,
                  display_order = EXCLUDED.display_order,
                  source_refs = EXCLUDED.source_refs,
                  metadata = EXCLUDED.metadata,
                  published_at = EXCLUDED.published_at,
                  updated_at = EXCLUDED.updated_at
                """
            ),
            {
                "id": experiment.get("id"),
                "code": experiment.get("code"),
                "title": experiment.get("title"),
                "title_en": experiment.get("title_en"),
                "summary": experiment.get("summary"),
                "status": experiment.get("status") or EXPECTED_STATUS,
                "display_order": int(experiment.get("display_order") or 0),
                "source_refs": _json_array_param(experiment.get("source_refs") or []),
                "metadata": _json_param(experiment.get("metadata") or {}),
                "published_at": experiment.get("published_at"),
                "created_at": experiment.get("created_at"),
                "updated_at": experiment.get("updated_at"),
            },
        )
    if replace and experiment_ids:
        if question_ids:
            session.execute(
                text(
                    """
                    DELETE FROM question_semantic_fingerprints
                    WHERE owner_kind = 'question'
                      AND CAST(owner_id AS text) IN :question_ids
                    """
                ).bindparams(bindparam("question_ids", expanding=True)),
                {"question_ids": question_ids},
            )
        session.execute(
            text(
                """
                DELETE FROM experiment_questions q
                USING experiment_question_banks b
                WHERE q.bank_id = b.id
                  AND b.bank_kind = :bank_kind
                  AND b.experiment_id IN :experiment_ids
                """
            ).bindparams(bindparam("experiment_ids", expanding=True)),
            {"bank_kind": EXPECTED_BANK_KIND, "experiment_ids": experiment_ids},
        )
        session.execute(
            text(
                """
                DELETE FROM experiment_question_banks
                WHERE bank_kind = :bank_kind
                  AND experiment_id IN :experiment_ids
                """
            ).bindparams(bindparam("experiment_ids", expanding=True)),
            {"bank_kind": EXPECTED_BANK_KIND, "experiment_ids": experiment_ids},
        )
        if generation_ids:
            session.execute(
                text(
                    """
                    DELETE FROM experiment_question_generations
                    WHERE id IN :generation_ids
                    """
                ).bindparams(bindparam("generation_ids", expanding=True)),
                {"generation_ids": generation_ids},
            )
    for generation in generations:
        session.execute(
            text(
                """
                INSERT INTO experiment_question_generations (
                  id, experiment_id, prompt, question_types, difficulty, requested_count,
                  provider, model, mode, rag_sources, warning, status, created_by,
                  metadata, created_at, updated_at
                )
                VALUES (
                  CAST(:id AS uuid), :experiment_id, :prompt, :question_types, :difficulty,
                  :requested_count, :provider, :model, :mode, CAST(:rag_sources AS jsonb),
                  :warning, :status, CAST(:created_by AS uuid), CAST(:metadata AS jsonb),
                  COALESCE(CAST(:created_at AS timestamptz), now()),
                  COALESCE(CAST(:updated_at AS timestamptz), now())
                )
                ON CONFLICT (id) DO UPDATE SET
                  experiment_id = EXCLUDED.experiment_id,
                  prompt = EXCLUDED.prompt,
                  question_types = EXCLUDED.question_types,
                  difficulty = EXCLUDED.difficulty,
                  requested_count = EXCLUDED.requested_count,
                  provider = EXCLUDED.provider,
                  model = EXCLUDED.model,
                  mode = EXCLUDED.mode,
                  rag_sources = EXCLUDED.rag_sources,
                  warning = EXCLUDED.warning,
                  status = EXCLUDED.status,
                  created_by = EXCLUDED.created_by,
                  metadata = EXCLUDED.metadata,
                  updated_at = EXCLUDED.updated_at
                """
            ),
            {
                "id": generation.get("id"),
                "experiment_id": generation.get("experiment_id"),
                "prompt": generation.get("prompt"),
                "question_types": generation.get("question_types") or [],
                "difficulty": generation.get("difficulty"),
                "requested_count": int(generation.get("requested_count") or 5),
                "provider": generation.get("provider"),
                "model": generation.get("model"),
                "mode": generation.get("mode") or "local",
                "rag_sources": _json_array_param(generation.get("rag_sources") or []),
                "warning": generation.get("warning"),
                "status": generation.get("status") or "published",
                "created_by": generation.get("created_by"),
                "metadata": _json_param(generation.get("metadata") or {}),
                "created_at": generation.get("created_at"),
                "updated_at": generation.get("updated_at"),
            },
        )
    for bank in banks:
        session.execute(
            text(
                """
                INSERT INTO experiment_question_banks (
                  id, experiment_id, bank_kind, title, status, source_label, imported_by,
                  metadata, created_at, updated_at
                )
                VALUES (
                  CAST(:id AS uuid), :experiment_id, :bank_kind, :title, :status, :source_label,
                  CAST(:imported_by AS uuid), CAST(:metadata AS jsonb),
                  COALESCE(CAST(:created_at AS timestamptz), now()),
                  COALESCE(CAST(:updated_at AS timestamptz), now())
                )
                ON CONFLICT (id) DO UPDATE SET
                  experiment_id = EXCLUDED.experiment_id,
                  bank_kind = EXCLUDED.bank_kind,
                  title = EXCLUDED.title,
                  status = EXCLUDED.status,
                  source_label = EXCLUDED.source_label,
                  imported_by = EXCLUDED.imported_by,
                  metadata = EXCLUDED.metadata,
                  updated_at = EXCLUDED.updated_at
                """
            ),
            {
                "id": bank.get("id"),
                "experiment_id": bank.get("experiment_id"),
                "bank_kind": bank.get("bank_kind"),
                "title": bank.get("title"),
                "status": bank.get("status"),
                "source_label": bank.get("source_label"),
                "imported_by": bank.get("imported_by"),
                "metadata": _json_param(bank.get("metadata") or {}),
                "created_at": bank.get("created_at"),
                "updated_at": bank.get("updated_at"),
            },
        )
    for question in questions:
        session.execute(
            text(
                """
                INSERT INTO experiment_questions (
                  id, bank_id, experiment_id, generation_id, question_type, stem, options, answer,
                  explanation, difficulty, related_chapter_ids, related_knowledge_point_ids,
                  source_chunk_ids, source_refs, primary_point_node_ids, primary_canonical_point_ids,
                  source_placement_node_ids, status, created_by, published_by, published_at,
                  metadata, created_at, updated_at
                )
                VALUES (
                  CAST(:id AS uuid), CAST(:bank_id AS uuid), :experiment_id,
                  CAST(:generation_id AS uuid), :question_type, :stem,
                  CAST(:options AS jsonb), CAST(:answer AS jsonb), :explanation, :difficulty,
                  :related_chapter_ids, :related_knowledge_point_ids, :source_chunk_ids,
                  CAST(:source_refs AS jsonb), :primary_point_node_ids, :primary_canonical_point_ids,
                  :source_placement_node_ids, :status, CAST(:created_by AS uuid),
                  CAST(:published_by AS uuid), CAST(:published_at AS timestamptz),
                  CAST(:metadata AS jsonb), COALESCE(CAST(:created_at AS timestamptz), now()),
                  COALESCE(CAST(:updated_at AS timestamptz), now())
                )
                ON CONFLICT (id) DO UPDATE SET
                  bank_id = EXCLUDED.bank_id,
                  experiment_id = EXCLUDED.experiment_id,
                  generation_id = EXCLUDED.generation_id,
                  question_type = EXCLUDED.question_type,
                  stem = EXCLUDED.stem,
                  options = EXCLUDED.options,
                  answer = EXCLUDED.answer,
                  explanation = EXCLUDED.explanation,
                  difficulty = EXCLUDED.difficulty,
                  related_chapter_ids = EXCLUDED.related_chapter_ids,
                  related_knowledge_point_ids = EXCLUDED.related_knowledge_point_ids,
                  source_chunk_ids = EXCLUDED.source_chunk_ids,
                  source_refs = EXCLUDED.source_refs,
                  primary_point_node_ids = EXCLUDED.primary_point_node_ids,
                  primary_canonical_point_ids = EXCLUDED.primary_canonical_point_ids,
                  source_placement_node_ids = EXCLUDED.source_placement_node_ids,
                  status = EXCLUDED.status,
                  created_by = EXCLUDED.created_by,
                  published_by = EXCLUDED.published_by,
                  published_at = EXCLUDED.published_at,
                  metadata = EXCLUDED.metadata,
                  updated_at = EXCLUDED.updated_at
                """
            ),
            {
                "id": question.get("id"),
                "bank_id": question.get("bank_id"),
                "experiment_id": question.get("experiment_id"),
                "generation_id": question.get("generation_id"),
                "question_type": question.get("question_type"),
                "stem": question.get("stem"),
                "options": _json_array_param(question.get("options") or []),
                "answer": _json_param(question.get("answer") or {}),
                "explanation": question.get("explanation"),
                "difficulty": question.get("difficulty"),
                "related_chapter_ids": question.get("related_chapter_ids") or [],
                "related_knowledge_point_ids": question.get("related_knowledge_point_ids") or [],
                "source_chunk_ids": question.get("source_chunk_ids") or [],
                "source_refs": _json_array_param(question.get("source_refs") or []),
                "primary_point_node_ids": question.get("primary_point_node_ids") or [],
                "primary_canonical_point_ids": question.get("primary_canonical_point_ids") or [],
                "source_placement_node_ids": question.get("source_placement_node_ids") or [],
                "status": question.get("status"),
                "created_by": question.get("created_by"),
                "published_by": question.get("published_by"),
                "published_at": question.get("published_at"),
                "metadata": _json_param(question.get("metadata") or {}),
                "created_at": question.get("created_at"),
                "updated_at": question.get("updated_at"),
            },
        )
    for fingerprint in fingerprints:
        session.execute(
            text(
                """
                INSERT INTO question_semantic_fingerprints (
                  id, owner_kind, owner_id, point_node_id, text_hash, embedding_model,
                  embedding, created_at, updated_at
                )
                VALUES (
                  CAST(:id AS uuid), :owner_kind, CAST(:owner_id AS uuid), :point_node_id,
                  :text_hash, :embedding_model, CAST(:embedding AS jsonb),
                  COALESCE(CAST(:created_at AS timestamptz), now()),
                  COALESCE(CAST(:updated_at AS timestamptz), now())
                )
                ON CONFLICT (owner_kind, owner_id, point_node_id, embedding_model, text_hash)
                DO UPDATE SET
                  embedding = EXCLUDED.embedding,
                  updated_at = EXCLUDED.updated_at
                """
            ),
            {
                "id": fingerprint.get("id"),
                "owner_kind": fingerprint.get("owner_kind") or "question",
                "owner_id": fingerprint.get("owner_id"),
                "point_node_id": fingerprint.get("point_node_id"),
                "text_hash": fingerprint.get("text_hash"),
                "embedding_model": fingerprint.get("embedding_model"),
                "embedding": _json_array_param(fingerprint.get("embedding") or []),
                "created_at": fingerprint.get("created_at"),
                "updated_at": fingerprint.get("updated_at"),
            },
        )
    return {
        "supplemental_formal_experiments": len(supplemental_experiments),
        "question_generations": len(generations),
        "question_banks": len(banks),
        "questions": len(questions),
        "question_semantic_fingerprints": len(fingerprints),
        "replace": replace,
        "validation": validation,
    }


def round_trip_seed(payload: dict[str, Any]) -> dict[str, Any]:
    banks = [item for item in payload.get("question_banks") or [] if isinstance(item, dict)]
    questions = [item for item in payload.get("questions") or [] if isinstance(item, dict)]
    bank_ids = {str(item.get("id") or "").strip() for item in banks if str(item.get("id") or "").strip()}
    question_ids = {str(item.get("id") or "").strip() for item in questions if str(item.get("id") or "").strip()}
    session = get_session_factory()()
    transaction = session.begin()
    try:
        import_result = import_seed(session, payload, replace=True)
        restored_bank_count = session.execute(
            text(
                """
                SELECT COUNT(*)
                FROM experiment_question_banks
                WHERE status = :status
                  AND bank_kind = :bank_kind
                  AND id IN :bank_ids
                """
            ).bindparams(bindparam("bank_ids", expanding=True)),
            {"status": EXPECTED_STATUS, "bank_kind": EXPECTED_BANK_KIND, "bank_ids": sorted(bank_ids)},
        ).scalar_one()
        restored_question_count = session.execute(
            text(
                """
                SELECT COUNT(*)
                FROM experiment_questions
                WHERE status = :status
                  AND id IN :question_ids
                """
            ).bindparams(bindparam("question_ids", expanding=True)),
            {"status": EXPECTED_STATUS, "question_ids": sorted(question_ids)},
        ).scalar_one()
        errors: list[str] = []
        if int(restored_bank_count or 0) != EXPECTED_BANK_COUNT:
            errors.append(f"restored question_banks: expected {EXPECTED_BANK_COUNT}, got {restored_bank_count}")
        if int(restored_question_count or 0) != EXPECTED_QUESTION_COUNT:
            errors.append(f"restored questions: expected {EXPECTED_QUESTION_COUNT}, got {restored_question_count}")
        return {
            "ok": not errors,
            "mode": "transactional_round_trip",
            "rolled_back": True,
            "errors": errors,
            "restored_question_banks": int(restored_bank_count or 0),
            "restored_questions": int(restored_question_count or 0),
            "import": import_result,
        }
    finally:
        transaction.rollback()
        session.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Export, import, or validate the current catalog-node question-bank seed.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    export_parser = subparsers.add_parser("export")
    export_parser.add_argument("--path", type=Path, default=DEFAULT_SEED_PATH)
    export_parser.add_argument("--skip-migrations", action="store_true")

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--path", type=Path, default=DEFAULT_SEED_PATH)
    validate_parser.add_argument("--skip-db", action="store_true")

    import_parser = subparsers.add_parser("import")
    import_parser.add_argument("--path", type=Path, default=DEFAULT_SEED_PATH)
    import_parser.add_argument("--skip-migrations", action="store_true")
    import_parser.add_argument("--merge", action="store_true", help="Do not replace existing generated banks for seed experiments first.")

    round_trip_parser = subparsers.add_parser("round-trip")
    round_trip_parser.add_argument("--path", type=Path, default=DEFAULT_SEED_PATH)

    args = parser.parse_args()

    if args.command == "export":
        if not args.skip_migrations:
            apply_migrations()
        with db_session() as session:
            payload = export_seed(session)
            validation = validate_seed_payload(payload, session=session)
            if not validation["ok"]:
                raise SystemExit("Exported seed failed validation:\n" + "\n".join(validation["errors"][:80]))
        write_seed(args.path, payload)
        sys.stdout.buffer.write((json.dumps({"path": str(args.path), **validation}, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        return

    payload = load_seed(args.path)
    if args.command == "validate":
        if args.skip_db:
            result = validate_seed_payload(payload)
        else:
            with db_session() as session:
                result = validate_seed_payload(payload, session=session)
        sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        if not result["ok"]:
            raise SystemExit(1)
        return

    if args.command == "import":
        if not args.skip_migrations:
            apply_migrations()
        with db_session() as session:
            result = import_seed(session, payload, replace=not args.merge)
        sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        return

    if args.command == "round-trip":
        result = round_trip_seed(payload)
        sys.stdout.buffer.write((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        if not result["ok"]:
            raise SystemExit(1)
        return


if __name__ == "__main__":
    main()
