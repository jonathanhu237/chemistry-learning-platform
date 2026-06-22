from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

from sqlalchemy import text

from server.app.domains.assistant.rag_sources import _source_evidence_payload, _source_from_chunk
from server.app.domains.catalog_tree.common import (
    breadcrumbs,
    catalog_path_titles_with_chapter,
    clean,
    get_content,
    get_node,
    point_capable,
)
from server.app.domains.catalog_tree.equations import reaction_derived_terms, reaction_principle_text, reaction_row_display_text
from server.app.domains.errors import DomainHTTPException as HTTPException, domain_status as status
from server.app.hybrid_rag import retrieve_hybrid_context
from server.app.infrastructure.database import db_session
from server.app.infrastructure.settings import get_settings
from server.app.repositories import RepositoryProvider, get_repositories
from server.app.retrieval import keyword_score
from server.app.schemas import AgentAskRequest


JOB_TYPES = {"es_upsert", "es_delete", "teacher_search_upsert", "teacher_search_delete", "rag_evidence_refresh", "rag_evidence_delete"}
TRIGGER_SOURCES = {"automatic", "manual", "retry", "system"}
JOB_STATUSES = {"pending", "running", "succeeded", "failed", "disabled", "unavailable"}
SOFT_ES_SYNC_QUIET_SECONDS = 30
SOFT_ES_SYNC_MAX_WAIT_SECONDS = 180


class CatalogPointJobUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class CatalogPointJob:
    id: str
    node_id: str
    job_type: str
    attempts: int
    payload: dict[str, Any]


def _json_param(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=str)


def _json_array_param(value: Any) -> str:
    return json.dumps(value if value is not None else [], ensure_ascii=False, default=str)


def _as_dict(row: Any) -> dict[str, Any]:
    return dict(row) if row else {}


def _result_one(result: Any) -> dict[str, Any]:
    if result is None or not hasattr(result, "mappings"):
        return {}
    return _as_dict(result.mappings().first())


def _payload_key(payload: dict[str, Any] | None) -> str:
    return json.dumps(payload or {}, ensure_ascii=False, sort_keys=True, default=str)


def _public_job(row: dict[str, Any]) -> dict[str, Any]:
    if not row:
        return {}
    return {
        "id": str(row.get("id")),
        "node_id": str(row.get("node_id") or ""),
        "job_type": row.get("job_type"),
        "trigger_source": row.get("trigger_source"),
        "status": row.get("status"),
        "attempts": int(row.get("attempts") or 0),
        "max_attempts": int(row.get("max_attempts") or 0),
        "payload": row.get("payload") if isinstance(row.get("payload"), dict) else {},
        "result": row.get("result") if isinstance(row.get("result"), dict) else {},
        "latest_error": row.get("latest_error"),
        "worker_id": row.get("worker_id"),
        "run_after": row.get("run_after"),
        "started_at": row.get("started_at"),
        "finished_at": row.get("finished_at"),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }


def _default_evidence_state(node_id: str) -> dict[str, Any]:
    return {
        "node_id": node_id,
        "placement_node_id": node_id,
        "canonical_point_id": node_id,
        "evidence_status": "missing",
        "source_mode": "none",
        "trigger_policy": "stale_until_manual_refresh",
        "selected_chunk_ids": [],
        "source_refs": [],
        "diagnostics": {},
        "stale_reason": None,
        "latest_error": None,
        "refreshed_at": None,
        "stale_at": None,
        "last_attempted_at": None,
        "updated_at": None,
    }


def _point_identity(session: Any, node_id: str) -> dict[str, str]:
    row = (
        session.execute(
            text(
                """
                SELECT id AS placement_node_id, canonical_point_id
                FROM experiment_catalog_nodes
                WHERE id = :node_id
                  AND node_kind = 'point'
                """
            ),
            {"node_id": node_id},
        )
        .mappings()
        .first()
    )
    canonical_point_id = str(row["canonical_point_id"]) if row and row.get("canonical_point_id") else node_id
    owner = (
        session.execute(
            text(
                """
                SELECT id
                FROM experiment_catalog_nodes
                WHERE canonical_point_id = :canonical_point_id
                  AND node_kind = 'point'
                  AND status <> 'archived'
                ORDER BY status = 'published' DESC, chapter_id, parent_id NULLS FIRST, display_order, id
                LIMIT 1
                """
            ),
            {"canonical_point_id": canonical_point_id},
        )
        .scalars()
        .first()
    )
    return {
        "placement_node_id": node_id,
        "canonical_point_id": canonical_point_id,
        "owner_node_id": str(owner or node_id),
    }


def enqueue_point_job(
    session: Any,
    *,
    node_id: str,
    job_type: str,
    trigger_source: str = "automatic",
    payload: dict[str, Any] | None = None,
    idempotency_key: str | None = None,
    max_attempts: int = 3,
    run_after_seconds: int = 0,
    coalesce_with_open_job: bool = False,
    max_coalesce_seconds: int | None = None,
) -> dict[str, Any]:
    if job_type not in JOB_TYPES:
        raise ValueError(f"Unsupported catalog point job type: {job_type}")
    if trigger_source not in TRIGGER_SOURCES:
        raise ValueError(f"Unsupported catalog point trigger source: {trigger_source}")
    payload = payload or {}
    run_after_seconds = max(0, int(run_after_seconds or 0))
    max_coalesce_seconds = max(run_after_seconds, int(max_coalesce_seconds or run_after_seconds or 0))
    identity = _point_identity(session, node_id)
    idempotency_key = idempotency_key or f"catalog-point:{node_id}:{job_type}:{_payload_key(payload)}"
    result = session.execute(
        text(
            """
            INSERT INTO experiment_catalog_point_jobs (
              node_id, placement_node_id, canonical_point_id, job_type, trigger_source, status, attempts, max_attempts,
              idempotency_key, payload, result, latest_error, run_after, updated_at
            )
            VALUES (
              :node_id, :placement_node_id, :canonical_point_id, :job_type, :trigger_source, 'pending', 0, :max_attempts,
              :idempotency_key, CAST(:payload AS jsonb), '{}'::jsonb, NULL,
              now() + (:run_after_seconds * INTERVAL '1 second'),
              now()
            )
            ON CONFLICT (idempotency_key) WHERE status IN ('pending', 'running') DO UPDATE SET
              trigger_source = CASE
                WHEN experiment_catalog_point_jobs.trigger_source = 'automatic'
                 AND EXCLUDED.trigger_source IN ('manual', 'retry')
                THEN EXCLUDED.trigger_source
                ELSE experiment_catalog_point_jobs.trigger_source
              END,
              payload = experiment_catalog_point_jobs.payload || EXCLUDED.payload,
              placement_node_id = EXCLUDED.placement_node_id,
              canonical_point_id = EXCLUDED.canonical_point_id,
              run_after = CASE
                WHEN :coalesce_with_open_job THEN LEAST(
                  now() + (:run_after_seconds * INTERVAL '1 second'),
                  experiment_catalog_point_jobs.created_at + (:max_coalesce_seconds * INTERVAL '1 second')
                )
                ELSE EXCLUDED.run_after
              END,
              updated_at = now()
            RETURNING id, node_id, job_type, trigger_source, status, attempts, max_attempts,
                      payload, result, latest_error, worker_id, run_after, started_at,
                      finished_at, created_at, updated_at
            """
        ),
        {
            "node_id": node_id,
            "placement_node_id": identity["placement_node_id"],
            "canonical_point_id": identity["canonical_point_id"],
            "job_type": job_type,
            "trigger_source": trigger_source,
            "max_attempts": max(1, int(max_attempts)),
            "idempotency_key": idempotency_key,
            "run_after_seconds": run_after_seconds,
            "coalesce_with_open_job": bool(coalesce_with_open_job),
            "max_coalesce_seconds": max_coalesce_seconds,
            "payload": _json_param({
                "placement_node_id": identity["placement_node_id"],
                "canonical_point_id": identity["canonical_point_id"],
                **payload,
            }),
        },
    )
    return _public_job(_result_one(result))


def queue_es_sync_job(
    session: Any,
    *,
    node_id: str,
    action: str,
    trigger_source: str = "automatic",
    payload: dict[str, Any] | None = None,
    soft: bool = False,
) -> dict[str, Any]:
    desired_action = "delete" if action == "delete" else "upsert"
    job_type = "es_delete" if desired_action == "delete" else "es_upsert"
    soft_upsert = bool(soft and desired_action == "upsert")
    idempotency_key = f"catalog-point:{node_id}:{job_type}:soft" if soft_upsert else None
    return enqueue_point_job(
        session,
        node_id=node_id,
        job_type=job_type,
        trigger_source=trigger_source,
        payload={
            "desired_action": desired_action,
            **({"sync_mode": "soft", "quiet_seconds": SOFT_ES_SYNC_QUIET_SECONDS, "max_wait_seconds": SOFT_ES_SYNC_MAX_WAIT_SECONDS} if soft_upsert else {}),
            **(payload or {}),
        },
        idempotency_key=idempotency_key,
        run_after_seconds=SOFT_ES_SYNC_QUIET_SECONDS if soft_upsert else 0,
        coalesce_with_open_job=soft_upsert,
        max_coalesce_seconds=SOFT_ES_SYNC_MAX_WAIT_SECONDS if soft_upsert else 0,
    )


def _catalog_node_identity(session: Any, node_id: str) -> dict[str, Any]:
    row = (
        session.execute(
            text(
                """
                SELECT id, node_kind, canonical_point_id
                FROM experiment_catalog_nodes
                WHERE id = :node_id
                """
            ),
            {"node_id": node_id},
        )
        .mappings()
        .first()
    )
    if not row:
        return {"placement_node_id": node_id, "canonical_point_id": None, "node_kind": None}
    return {
        "placement_node_id": node_id,
        "canonical_point_id": str(row["canonical_point_id"]) if row.get("canonical_point_id") else None,
        "node_kind": row.get("node_kind"),
    }


def queue_teacher_search_sync_job(
    session: Any,
    *,
    node_id: str,
    action: str,
    trigger_source: str = "automatic",
    payload: dict[str, Any] | None = None,
    soft: bool = False,
) -> dict[str, Any]:
    if trigger_source not in TRIGGER_SOURCES:
        raise ValueError(f"Unsupported catalog point trigger source: {trigger_source}")
    desired_action = "delete" if action == "delete" else "upsert"
    job_type = "teacher_search_delete" if desired_action == "delete" else "teacher_search_upsert"
    soft_upsert = bool(soft and desired_action == "upsert")
    idempotency_key = f"catalog-teacher-search:{node_id}:{job_type}:soft" if soft_upsert else f"catalog-teacher-search:{node_id}:{job_type}:{_payload_key(payload)}"
    identity = _catalog_node_identity(session, node_id)
    result = session.execute(
        text(
            """
            INSERT INTO experiment_catalog_point_jobs (
              node_id, placement_node_id, canonical_point_id, job_type, trigger_source, status, attempts, max_attempts,
              idempotency_key, payload, result, latest_error, run_after, updated_at
            )
            VALUES (
              :node_id, :placement_node_id, :canonical_point_id, :job_type, :trigger_source, 'pending', 0, 3,
              :idempotency_key, CAST(:payload AS jsonb), '{}'::jsonb, NULL,
              now() + (:run_after_seconds * INTERVAL '1 second'),
              now()
            )
            ON CONFLICT (idempotency_key) WHERE status IN ('pending', 'running') DO UPDATE SET
              trigger_source = CASE
                WHEN experiment_catalog_point_jobs.trigger_source = 'automatic'
                 AND EXCLUDED.trigger_source IN ('manual', 'retry')
                THEN EXCLUDED.trigger_source
                ELSE experiment_catalog_point_jobs.trigger_source
              END,
              payload = experiment_catalog_point_jobs.payload || EXCLUDED.payload,
              placement_node_id = EXCLUDED.placement_node_id,
              canonical_point_id = EXCLUDED.canonical_point_id,
              run_after = CASE
                WHEN :coalesce_with_open_job THEN LEAST(
                  now() + (:run_after_seconds * INTERVAL '1 second'),
                  experiment_catalog_point_jobs.created_at + (:max_coalesce_seconds * INTERVAL '1 second')
                )
                ELSE EXCLUDED.run_after
              END,
              updated_at = now()
            RETURNING id, node_id, job_type, trigger_source, status, attempts, max_attempts,
                      payload, result, latest_error, worker_id, run_after, started_at,
                      finished_at, created_at, updated_at
            """
        ),
        {
            "node_id": node_id,
            "placement_node_id": identity["placement_node_id"],
            "canonical_point_id": identity["canonical_point_id"],
            "job_type": job_type,
            "trigger_source": trigger_source,
            "idempotency_key": idempotency_key,
            "run_after_seconds": SOFT_ES_SYNC_QUIET_SECONDS if soft_upsert else 0,
            "coalesce_with_open_job": soft_upsert,
            "max_coalesce_seconds": SOFT_ES_SYNC_MAX_WAIT_SECONDS if soft_upsert else 0,
            "payload": _json_param(
                {
                    "desired_action": desired_action,
                    "target_index": "teacher_catalog_search",
                    "placement_node_id": identity["placement_node_id"],
                    "canonical_point_id": identity["canonical_point_id"],
                    **(
                        {
                            "sync_mode": "soft",
                            "quiet_seconds": SOFT_ES_SYNC_QUIET_SECONDS,
                            "max_wait_seconds": SOFT_ES_SYNC_MAX_WAIT_SECONDS,
                        }
                        if soft_upsert
                        else {}
                    ),
                    **(payload or {}),
                }
            ),
        },
    )
    return _public_job(_result_one(result))


def _upsert_evidence_state(
    session: Any,
    *,
    node_id: str,
    evidence_status: str,
    source_mode: str = "none",
    trigger_policy: str = "stale_until_manual_refresh",
    selected_chunk_ids: list[str] | None = None,
    source_refs: list[dict[str, Any]] | None = None,
    diagnostics: dict[str, Any] | None = None,
    stale_reason: str | None = None,
    latest_error: str | None = None,
    refreshed: bool = False,
) -> None:
    identity = _point_identity(session, node_id)
    owner_node_id = identity["owner_node_id"]
    session.execute(
        text(
            """
            INSERT INTO experiment_catalog_point_evidence_state (
              node_id, canonical_point_id, source_placement_node_id, evidence_status, source_mode, trigger_policy, selected_chunk_ids,
              source_refs, diagnostics, stale_reason, latest_error, refreshed_at,
              stale_at, last_attempted_at, updated_at
            )
            VALUES (
              :node_id, :canonical_point_id, :source_placement_node_id, :evidence_status, :source_mode, :trigger_policy, :selected_chunk_ids,
              CAST(:source_refs AS jsonb), CAST(:diagnostics AS jsonb), :stale_reason,
              :latest_error,
              CASE WHEN :refreshed THEN now() ELSE NULL END,
              CASE WHEN :evidence_status = 'stale' THEN now() ELSE NULL END,
              CASE WHEN :evidence_status IN ('running', 'failed', 'unavailable', 'succeeded') THEN now() ELSE NULL END,
              now()
            )
            ON CONFLICT (node_id) DO UPDATE SET
              canonical_point_id = EXCLUDED.canonical_point_id,
              source_placement_node_id = EXCLUDED.source_placement_node_id,
              evidence_status = EXCLUDED.evidence_status,
              source_mode = EXCLUDED.source_mode,
              trigger_policy = EXCLUDED.trigger_policy,
              selected_chunk_ids = EXCLUDED.selected_chunk_ids,
              source_refs = EXCLUDED.source_refs,
              diagnostics = experiment_catalog_point_evidence_state.diagnostics || EXCLUDED.diagnostics,
              stale_reason = EXCLUDED.stale_reason,
              latest_error = EXCLUDED.latest_error,
              refreshed_at = CASE WHEN :refreshed THEN now() ELSE experiment_catalog_point_evidence_state.refreshed_at END,
              stale_at = CASE WHEN :evidence_status = 'stale' THEN now() ELSE experiment_catalog_point_evidence_state.stale_at END,
              last_attempted_at = CASE
                WHEN :evidence_status IN ('running', 'failed', 'unavailable', 'succeeded') THEN now()
                ELSE experiment_catalog_point_evidence_state.last_attempted_at
              END,
              updated_at = now()
            """
        ),
        {
            "node_id": owner_node_id,
            "canonical_point_id": identity["canonical_point_id"],
            "source_placement_node_id": identity["placement_node_id"],
            "evidence_status": evidence_status,
            "source_mode": source_mode,
            "trigger_policy": trigger_policy,
            "selected_chunk_ids": selected_chunk_ids or [],
            "source_refs": _json_array_param(source_refs or []),
            "diagnostics": _json_param(diagnostics or {}),
            "stale_reason": stale_reason,
            "latest_error": latest_error,
            "refreshed": bool(refreshed),
        },
    )


def mark_point_evidence_stale(
    session: Any,
    *,
    node_id: str,
    reason: str,
    trigger_source: str = "automatic",
) -> None:
    _upsert_evidence_state(
        session,
        node_id=node_id,
        evidence_status="stale",
        stale_reason=reason,
        diagnostics={"stale_trigger": {"reason": reason, "trigger_source": trigger_source}},
    )
    if get_settings().catalog_point_evidence_auto_refresh:
        queue_rag_evidence_refresh_job(session, node_id=node_id, trigger_source=trigger_source, reason=reason)


def mark_subtree_evidence_stale(
    session: Any,
    *,
    node_id: str,
    reason: str,
    trigger_source: str = "automatic",
) -> None:
    rows = (
        session.execute(
            text(
                """
                WITH RECURSIVE subtree AS (
                  SELECT id, node_kind
                  FROM experiment_catalog_nodes
                  WHERE id = :node_id
                  UNION ALL
                  SELECT child.id, child.node_kind
                  FROM experiment_catalog_nodes child
                  JOIN subtree ON child.parent_id = subtree.id
                )
                SELECT id FROM subtree WHERE node_kind = 'point'
                """
            ),
            {"node_id": node_id},
        )
        .scalars()
        .all()
    )
    for point_node_id in rows:
        mark_point_evidence_stale(session, node_id=str(point_node_id), reason=reason, trigger_source=trigger_source)


def queue_rag_evidence_refresh_job(
    session: Any,
    *,
    node_id: str,
    trigger_source: str = "automatic",
    reason: str = "manual_refresh",
) -> dict[str, Any]:
    _upsert_evidence_state(
        session,
        node_id=node_id,
        evidence_status="pending",
        source_mode="catalog_node_evidence",
        stale_reason=reason,
        diagnostics={"queued": {"reason": reason, "trigger_source": trigger_source}},
    )
    return enqueue_point_job(
        session,
        node_id=node_id,
        job_type="rag_evidence_refresh",
        trigger_source=trigger_source,
        payload={"reason": reason},
    )


def queue_rag_evidence_delete_job(
    session: Any,
    *,
    node_id: str,
    trigger_source: str = "manual",
    reason: str = "manual_delete",
) -> dict[str, Any]:
    _upsert_evidence_state(
        session,
        node_id=node_id,
        evidence_status="pending",
        source_mode="catalog_node_evidence_delete",
        selected_chunk_ids=[],
        source_refs=[],
        stale_reason=reason,
        diagnostics={"queued": {"reason": reason, "trigger_source": trigger_source}},
    )
    return enqueue_point_job(
        session,
        node_id=node_id,
        job_type="rag_evidence_delete",
        trigger_source=trigger_source,
        payload={"reason": reason},
    )


def get_point_job_state(session: Any, *, node_id: str) -> dict[str, Any]:
    identity = _point_identity(session, node_id)
    es_state = _as_dict(
        session.execute(
            text(
                """
                SELECT node_id, document_id, desired_action, sync_status, attempts,
                       document_hash, last_error, indexed_at, last_attempted_at,
                       analyzer_version, created_at, updated_at
                FROM experiment_catalog_point_search_index_state
                WHERE node_id = :node_id
                """
            ),
            {"node_id": node_id},
        )
        .mappings()
        .first()
    )
    teacher_search_state = _as_dict(
        session.execute(
            text(
                """
                SELECT node_id, document_id, desired_action, sync_status, attempts,
                       document_hash, last_error, indexed_at, last_attempted_at,
                       analyzer_version, created_at, updated_at
                FROM experiment_catalog_teacher_search_index_state
                WHERE node_id = :node_id
                """
            ),
            {"node_id": node_id},
        )
        .mappings()
        .first()
    )
    evidence_state = _as_dict(
        session.execute(
            text(
                """
                SELECT node_id, canonical_point_id, source_placement_node_id, evidence_status, source_mode, trigger_policy,
                       selected_chunk_ids, source_refs, diagnostics, stale_reason,
                       latest_error, refreshed_at, stale_at, last_attempted_at, updated_at
                FROM experiment_catalog_point_evidence_state
                WHERE canonical_point_id = :canonical_point_id
                   OR node_id = :node_id
                ORDER BY CASE WHEN canonical_point_id = :canonical_point_id THEN 0 ELSE 1 END,
                         updated_at DESC
                LIMIT 1
                """
            ),
            {"node_id": node_id, "canonical_point_id": identity["canonical_point_id"]},
        )
        .mappings()
        .first()
    ) or _default_evidence_state(node_id)
    jobs = [
        _public_job(dict(row))
        for row in session.execute(
            text(
                """
                SELECT id, node_id, job_type, trigger_source, status, attempts, max_attempts,
                       payload, result, latest_error, worker_id, run_after, started_at,
                       finished_at, created_at, updated_at
                FROM experiment_catalog_point_jobs
                WHERE node_id = :node_id
                ORDER BY updated_at DESC, created_at DESC
                LIMIT 12
                """
            ),
            {"node_id": node_id},
        )
        .mappings()
        .all()
    ]
    return {
        "node_id": node_id,
        "placement_node_id": identity["placement_node_id"],
        "canonical_point_id": identity["canonical_point_id"],
        "es_state": es_state or None,
        "teacher_search_state": teacher_search_state or None,
        "evidence_state": evidence_state,
        "recent_jobs": jobs,
    }


def catalog_point_job_state(*, node_id: str) -> dict[str, Any]:
    with db_session() as session:
        node = get_node(session, node_id)
        if not point_capable(node):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job state is only available for catalog point nodes")
        return get_point_job_state(session, node_id=node_id)


def trigger_catalog_point_job(*, node_id: str, action: str, user: Any) -> dict[str, Any]:
    del user
    with db_session() as session:
        node = get_node(session, node_id)
        if not point_capable(node):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Catalog point jobs require a point node")
        if action == "es-refresh":
            from server.app.domains.catalog_tree.search_documents import queue_index_state

            queue_index_state(session, node_id=node_id, action="upsert", trigger_source="manual")
        elif action == "es-delete":
            from server.app.domains.catalog_tree.search_documents import queue_index_state

            queue_index_state(session, node_id=node_id, action="delete", trigger_source="manual")
        elif action == "rag-refresh":
            queue_rag_evidence_refresh_job(session, node_id=node_id, trigger_source="manual", reason="manual_refresh")
        elif action == "rag-delete":
            queue_rag_evidence_delete_job(session, node_id=node_id, trigger_source="manual", reason="manual_delete")
        elif action == "retry":
            _retry_latest_failed_job(session, node_id=node_id)
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Unsupported catalog point job action")
        return get_point_job_state(session, node_id=node_id)


def _retry_latest_failed_job(session: Any, *, node_id: str) -> None:
    row = (
        session.execute(
            text(
                """
                SELECT job_type, payload
                FROM experiment_catalog_point_jobs
                WHERE node_id = :node_id
                  AND status IN ('failed', 'unavailable')
                ORDER BY updated_at DESC, created_at DESC
                LIMIT 1
                """
            ),
            {"node_id": node_id},
        )
        .mappings()
        .first()
    )
    if row:
        payload = row["payload"] if isinstance(row["payload"], dict) else {}
        if row["job_type"] in {"es_upsert", "es_delete"}:
            queue_es_sync_job(
                session,
                node_id=node_id,
                action="delete" if row["job_type"] == "es_delete" else "upsert",
                trigger_source="retry",
                payload=payload,
            )
            return
        if row["job_type"] in {"teacher_search_upsert", "teacher_search_delete"}:
            queue_teacher_search_sync_job(
                session,
                node_id=node_id,
                action="delete" if row["job_type"] == "teacher_search_delete" else "upsert",
                trigger_source="retry",
                payload=payload,
            )
            return
        if row["job_type"] == "rag_evidence_refresh":
            queue_rag_evidence_refresh_job(session, node_id=node_id, trigger_source="retry", reason=str(payload.get("reason") or "retry"))
            return
        if row["job_type"] == "rag_evidence_delete":
            queue_rag_evidence_delete_job(session, node_id=node_id, trigger_source="retry", reason=str(payload.get("reason") or "retry"))
            return
    es_state = (
        session.execute(
            text("SELECT desired_action FROM experiment_catalog_point_search_index_state WHERE node_id = :node_id AND sync_status = 'failed'"),
            {"node_id": node_id},
        )
        .mappings()
        .first()
    )
    if es_state:
        queue_es_sync_job(session, node_id=node_id, action=str(es_state["desired_action"] or "upsert"), trigger_source="retry")
        return
    teacher_search_state = (
        session.execute(
            text(
                """
                SELECT desired_action
                FROM experiment_catalog_teacher_search_index_state
                WHERE node_id = :node_id
                  AND sync_status IN ('failed', 'unavailable')
                """
            ),
            {"node_id": node_id},
        )
        .mappings()
        .first()
    )
    if teacher_search_state:
        queue_teacher_search_sync_job(
            session,
            node_id=node_id,
            action=str(teacher_search_state["desired_action"] or "upsert"),
            trigger_source="retry",
        )
        return
    evidence_state = (
        session.execute(
            text(
                """
                SELECT evidence_status
                FROM experiment_catalog_point_evidence_state
                WHERE node_id = :node_id
                  AND evidence_status IN ('failed', 'unavailable', 'stale')
                """
            ),
            {"node_id": node_id},
        )
        .mappings()
        .first()
    )
    if evidence_state:
        queue_rag_evidence_refresh_job(session, node_id=node_id, trigger_source="retry", reason="retry_stale_or_failed")
        return
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No failed, unavailable, or stale catalog point job is available to retry")


def claim_next_point_job(worker_id: str) -> CatalogPointJob | None:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    UPDATE experiment_catalog_point_jobs
                    SET status = 'running',
                        attempts = attempts + 1,
                        worker_id = :worker_id,
                        locked_at = now(),
                        started_at = COALESCE(started_at, now()),
                        updated_at = now()
                    WHERE id = (
                      SELECT id
                      FROM experiment_catalog_point_jobs
                      WHERE status = 'pending'
                        AND attempts < max_attempts
                        AND run_after <= now()
                      ORDER BY run_after, created_at
                      FOR UPDATE SKIP LOCKED
                      LIMIT 1
                    )
                    RETURNING id, node_id, job_type, attempts, payload
                    """
                ),
                {"worker_id": worker_id},
            )
            .mappings()
            .first()
        )
    if not row:
        return None
    payload = row["payload"] if isinstance(row["payload"], dict) else {}
    return CatalogPointJob(
        id=str(row["id"]),
        node_id=str(row["node_id"]),
        job_type=str(row["job_type"]),
        attempts=int(row["attempts"] or 0),
        payload=payload,
    )


def finish_point_job(job: CatalogPointJob, *, result: dict[str, Any] | None = None, status_value: str = "succeeded") -> None:
    if status_value not in JOB_STATUSES:
        raise ValueError(f"Unsupported catalog point job status: {status_value}")
    with db_session() as session:
        session.execute(
            text(
                """
                UPDATE experiment_catalog_point_jobs
                SET status = :status,
                    result = CAST(:result AS jsonb),
                    latest_error = NULL,
                    finished_at = now(),
                    updated_at = now()
                WHERE id = CAST(:job_id AS uuid)
                """
            ),
            {"job_id": job.id, "status": status_value, "result": _json_param(result or {})},
        )


def fail_point_job(job: CatalogPointJob, error: str, *, status_value: str = "failed", result: dict[str, Any] | None = None) -> None:
    if status_value not in {"failed", "unavailable", "disabled"}:
        raise ValueError(f"Unsupported catalog point failure status: {status_value}")
    with db_session() as session:
        session.execute(
            text(
                """
                UPDATE experiment_catalog_point_jobs
                SET status = :status,
                    result = CAST(:result AS jsonb),
                    latest_error = :latest_error,
                    finished_at = now(),
                    updated_at = now()
                WHERE id = CAST(:job_id AS uuid)
                """
            ),
            {
                "job_id": job.id,
                "status": status_value,
                "result": _json_param(result or {}),
                "latest_error": error[:1000],
            },
        )


def run_point_job_once(worker_id: str = "local-catalog-point-worker") -> bool:
    job = claim_next_point_job(worker_id)
    if not job:
        return False
    process_point_job(job)
    return True


def process_point_job(job: CatalogPointJob) -> None:
    try:
        if job.job_type in {"es_upsert", "es_delete"}:
            result = _process_es_job(job)
            finish_point_job(job, result=result, status_value=str(result.get("job_status") or "succeeded"))
        elif job.job_type in {"teacher_search_upsert", "teacher_search_delete"}:
            result = _process_teacher_search_job(job)
            finish_point_job(job, result=result, status_value=str(result.get("job_status") or "succeeded"))
        elif job.job_type == "rag_evidence_refresh":
            result = _process_rag_evidence_refresh(job)
            finish_point_job(job, result=result)
        elif job.job_type == "rag_evidence_delete":
            result = _process_rag_evidence_delete(job)
            finish_point_job(job, result=result)
        else:
            raise RuntimeError(f"Unsupported catalog point job type: {job.job_type}")
    except CatalogPointJobUnavailable as exc:
        if job.job_type == "rag_evidence_refresh":
            _mark_evidence_failure(node_id=job.node_id, error=str(exc), evidence_status="unavailable")
        elif job.job_type in {"es_upsert", "es_delete"}:
            _mark_es_state_failure(node_id=job.node_id, action="delete" if job.job_type == "es_delete" else "upsert", error=str(exc))
        elif job.job_type in {"teacher_search_upsert", "teacher_search_delete"}:
            from server.app.domains.catalog_tree.teacher_search import mark_teacher_search_state_failure

            mark_teacher_search_state_failure(
                node_id=job.node_id,
                action="delete" if job.job_type == "teacher_search_delete" else "upsert",
                error=str(exc),
                status_value="unavailable",
            )
        fail_point_job(job, str(exc), status_value="unavailable")
    except Exception as exc:
        if job.job_type == "rag_evidence_refresh":
            _mark_evidence_failure(node_id=job.node_id, error=str(exc), evidence_status="failed")
        elif job.job_type in {"es_upsert", "es_delete"}:
            _mark_es_state_failure(node_id=job.node_id, action="delete" if job.job_type == "es_delete" else "upsert", error=str(exc))
        elif job.job_type in {"teacher_search_upsert", "teacher_search_delete"}:
            from server.app.domains.catalog_tree.teacher_search import mark_teacher_search_state_failure

            mark_teacher_search_state_failure(
                node_id=job.node_id,
                action="delete" if job.job_type == "teacher_search_delete" else "upsert",
                error=str(exc),
            )
        fail_point_job(job, f"{exc.__class__.__name__}: {str(exc)[:900]}")


def _process_es_job(job: CatalogPointJob) -> dict[str, Any]:
    from server.app.domains.catalog_tree.search_documents import student_search_document_for_node, student_search_document_sync_hash
    from server.app.domains.video_library.index_client import configured_index_client

    action = "delete" if job.job_type == "es_delete" else "upsert"
    client = configured_index_client()
    if client is None:
        _mark_es_state_disabled(node_id=job.node_id, action=action, reason="Elasticsearch backend is not configured")
        return {"job_status": "disabled", "action": action, "reason": "elasticsearch_not_configured"}
    if action == "delete":
        client.delete_document(job.node_id)
        _mark_es_state_success(node_id=job.node_id, action="delete", document_hash="deleted")
        return {"job_status": "succeeded", "action": "delete", "document_id": job.node_id}
    indexed_hash = None
    with db_session() as session:
        document = student_search_document_for_node(session, node_id=job.node_id, require_published=True)
        state = (
            session.execute(
                text("SELECT document_hash FROM experiment_catalog_point_search_index_state WHERE node_id = :node_id"),
                {"node_id": job.node_id},
            )
            .mappings()
            .first()
        )
        indexed_hash = str(state["document_hash"]) if state and state.get("document_hash") else None
    if not document:
        client.delete_document(job.node_id)
        _mark_es_state_success(node_id=job.node_id, action="delete", document_hash="not_searchable")
        return {"job_status": "succeeded", "action": "delete", "document_id": job.node_id, "reason": "point_not_searchable"}
    payload_hash = student_search_document_sync_hash(document)
    if indexed_hash == payload_hash:
        _mark_es_state_success(node_id=job.node_id, action="upsert", document_hash=payload_hash, indexed=False)
        return {
            "job_status": "succeeded",
            "action": "upsert",
            "document_id": document["id"],
            "document_hash": payload_hash,
            "no_op": True,
            "reason": "document_hash_unchanged",
        }
    analyzer_version = get_settings().video_library_search_analyzer
    client.ensure_index(analyzer=analyzer_version)
    client.upsert_document(document)
    _mark_es_state_success(node_id=job.node_id, action="upsert", document_hash=payload_hash, analyzer_version=analyzer_version)
    return {"job_status": "succeeded", "action": "upsert", "document_id": document["id"], "document_hash": payload_hash}


def _process_teacher_search_job(job: CatalogPointJob) -> dict[str, Any]:
    from server.app.domains.catalog_tree.teacher_search import (
        configured_teacher_search_client,
        mark_teacher_search_state_failure,
        mark_teacher_search_state_success,
        teacher_search_document_for_node,
        teacher_search_document_sync_hash,
    )

    action = "delete" if job.job_type == "teacher_search_delete" else "upsert"
    client = configured_teacher_search_client()
    if client is None:
        mark_teacher_search_state_failure(
            node_id=job.node_id,
            action=action,
            error="Teacher catalog Elasticsearch backend is not configured",
            status_value="disabled",
        )
        return {"job_status": "disabled", "action": action, "reason": "teacher_search_not_configured"}
    if action == "delete":
        client.delete_document(job.node_id)
        mark_teacher_search_state_success(node_id=job.node_id, action="delete", document_hash="deleted")
        return {"job_status": "succeeded", "action": "delete", "document_id": job.node_id, "target_index": client.index}
    indexed_hash = None
    with db_session() as session:
        document = teacher_search_document_for_node(session, node_id=job.node_id)
        state = (
            session.execute(
                text("SELECT document_hash FROM experiment_catalog_teacher_search_index_state WHERE node_id = :node_id"),
                {"node_id": job.node_id},
            )
            .mappings()
            .first()
        )
        indexed_hash = str(state["document_hash"]) if state and state.get("document_hash") else None
    if not document:
        client.delete_document(job.node_id)
        mark_teacher_search_state_success(node_id=job.node_id, action="delete", document_hash="not_searchable")
        return {"job_status": "succeeded", "action": "delete", "document_id": job.node_id, "reason": "node_not_searchable"}
    payload_hash = teacher_search_document_sync_hash(document)
    if indexed_hash == payload_hash:
        mark_teacher_search_state_success(node_id=job.node_id, action="upsert", document_hash=payload_hash, indexed=False)
        return {
            "job_status": "succeeded",
            "action": "upsert",
            "document_id": document["id"],
            "document_hash": payload_hash,
            "no_op": True,
            "reason": "document_hash_unchanged",
        }
    analyzer_version = get_settings().teacher_catalog_search_analyzer
    client.ensure_index(analyzer=analyzer_version)
    client.upsert_document(document)
    mark_teacher_search_state_success(node_id=job.node_id, action="upsert", document_hash=payload_hash, analyzer_version=analyzer_version)
    return {
        "job_status": "succeeded",
        "action": "upsert",
        "document_id": document["id"],
        "document_hash": payload_hash,
        "target_index": client.index,
    }


def _mark_es_state_success(*, node_id: str, action: str, document_hash: str, indexed: bool = True, analyzer_version: str | None = None) -> None:
    with db_session() as session:
        identity = _point_identity(session, node_id)
        session.execute(
            text(
                """
                INSERT INTO experiment_catalog_point_search_index_state (
                  node_id, placement_node_id, canonical_point_id, document_id, desired_action, sync_status, attempts,
                  document_hash, last_error, indexed_at, last_attempted_at, analyzer_version, updated_at
                )
                VALUES (
                  :node_id, :placement_node_id, :canonical_point_id, :node_id, :action, 'synced', 1,
                  :document_hash, NULL, now(), now(), :analyzer_version, now()
                )
                ON CONFLICT (node_id) DO UPDATE SET
                  placement_node_id = EXCLUDED.placement_node_id,
                  canonical_point_id = EXCLUDED.canonical_point_id,
                  document_id = EXCLUDED.document_id,
                  desired_action = EXCLUDED.desired_action,
                  sync_status = 'synced',
                  attempts = experiment_catalog_point_search_index_state.attempts + 1,
                  document_hash = EXCLUDED.document_hash,
                  last_error = NULL,
                  indexed_at = CASE WHEN :indexed THEN now() ELSE experiment_catalog_point_search_index_state.indexed_at END,
                  last_attempted_at = now(),
                  analyzer_version = COALESCE(EXCLUDED.analyzer_version, experiment_catalog_point_search_index_state.analyzer_version),
                  updated_at = now()
                """
            ),
            {
                "node_id": node_id,
                "placement_node_id": identity["placement_node_id"],
                "canonical_point_id": identity["canonical_point_id"],
                "action": action,
                "document_hash": document_hash,
                "indexed": bool(indexed),
                "analyzer_version": analyzer_version,
            },
        )


def _mark_es_state_failure(*, node_id: str, action: str, error: str) -> None:
    with db_session() as session:
        identity = _point_identity(session, node_id)
        session.execute(
            text(
                """
                INSERT INTO experiment_catalog_point_search_index_state (
                  node_id, placement_node_id, canonical_point_id, document_id, desired_action, sync_status, attempts,
                  last_error, last_attempted_at, updated_at
                )
                VALUES (
                  :node_id, :placement_node_id, :canonical_point_id, :node_id, :action, 'failed', 1,
                  :error, now(), now()
                )
                ON CONFLICT (node_id) DO UPDATE SET
                  placement_node_id = EXCLUDED.placement_node_id,
                  canonical_point_id = EXCLUDED.canonical_point_id,
                  desired_action = EXCLUDED.desired_action,
                  sync_status = 'failed',
                  attempts = experiment_catalog_point_search_index_state.attempts + 1,
                  last_error = EXCLUDED.last_error,
                  last_attempted_at = now(),
                  updated_at = now()
                """
            ),
            {
                "node_id": node_id,
                "placement_node_id": identity["placement_node_id"],
                "canonical_point_id": identity["canonical_point_id"],
                "action": action,
                "error": error[:1000],
            },
        )


def _mark_es_state_disabled(*, node_id: str, action: str, reason: str) -> None:
    with db_session() as session:
        identity = _point_identity(session, node_id)
        session.execute(
            text(
                """
                INSERT INTO experiment_catalog_point_search_index_state (
                  node_id, placement_node_id, canonical_point_id, document_id, desired_action, sync_status, attempts,
                  last_error, last_attempted_at, updated_at
                )
                VALUES (
                  :node_id, :placement_node_id, :canonical_point_id, :node_id, :action, 'disabled', 0,
                  :reason, now(), now()
                )
                ON CONFLICT (node_id) DO UPDATE SET
                  placement_node_id = EXCLUDED.placement_node_id,
                  canonical_point_id = EXCLUDED.canonical_point_id,
                  desired_action = EXCLUDED.desired_action,
                  sync_status = 'disabled',
                  last_error = EXCLUDED.last_error,
                  last_attempted_at = now(),
                  updated_at = now()
                """
            ),
            {
                "node_id": node_id,
                "placement_node_id": identity["placement_node_id"],
                "canonical_point_id": identity["canonical_point_id"],
                "action": action,
                "reason": reason[:1000],
            },
        )


def _process_rag_evidence_delete(job: CatalogPointJob) -> dict[str, Any]:
    with db_session() as session:
        identity = _point_identity(session, job.node_id)
        session.execute(
            text(
                """
                DELETE FROM experiment_catalog_point_evidence_bindings
                WHERE canonical_point_id = :canonical_point_id
                   OR node_id = :node_id
                """
            ),
            {"node_id": job.node_id, "canonical_point_id": identity["canonical_point_id"]},
        )
        _upsert_evidence_state(
            session,
            node_id=job.node_id,
            evidence_status="disabled",
            source_mode="none",
            selected_chunk_ids=[],
            source_refs=[],
            diagnostics={"delete_job": {"job_id": job.id, "reason": job.payload.get("reason")}},
            latest_error=None,
        )
    return {"action": "rag_evidence_delete", "node_id": job.node_id}


def _process_rag_evidence_refresh(job: CatalogPointJob) -> dict[str, Any]:
    with db_session() as session:
        _upsert_evidence_state(
            session,
            node_id=job.node_id,
            evidence_status="running",
            source_mode="catalog_node_evidence",
            diagnostics={"running_job_id": job.id},
        )
        context = _catalog_point_context(session, node_id=job.node_id)
    settings = get_settings()
    gate = _rag_runtime_gate(settings)
    if not gate["healthy"]:
        raise CatalogPointJobUnavailable(str(gate["message"]))

    repositories = get_repositories()
    queries, query_trace = _catalog_point_queries(context)
    prompt = queries[0] if queries else context["title"]

    def query_generator(_question: str) -> tuple[list[str], dict[str, Any]]:
        return queries, query_trace

    request = AgentAskRequest(
        user_role="teacher",
        question=prompt,
        chapter_id=context.get("chapter_id"),
        point_node_id=job.node_id,
        catalog_path=context.get("catalog_path") or [],
        allow_progress_lookup=False,
        allow_rag_lookup=True,
        max_answer_chars=0,
    )
    result = retrieve_hybrid_context(
        repositories=repositories,
        question=prompt,
        request=request,
        settings=settings,
        legacy_retrieve=lambda lookup_query, lookup_limit: _legacy_retrieve_catalog_context(
            repositories,
            context=context,
            query=lookup_query,
            limit=lookup_limit,
        ),
        query_generator=query_generator,
        limit=max(1, int(settings.rag_final_top_k)),
    )
    source_refs = _source_refs_from_chunks(result.chunks)
    if not source_refs:
        raise RuntimeError("No usable source chunks were selected for catalog-node evidence refresh")
    selected_chunk_ids = [str(item["chunk_id"]) for item in source_refs if item.get("chunk_id")]
    diagnostics = {
        "rag_gate": gate,
        "query_generation": query_trace,
        "generated_queries": queries,
        "rag_trace": result.trace,
        "catalog_context_fields": context.get("field_contributors") or [],
        "catalog_node_ids": [job.node_id],
    }
    with db_session() as session:
        identity = _point_identity(session, job.node_id)
        _replace_evidence_bindings(
            session,
            node_id=job.node_id,
            canonical_point_id=identity["canonical_point_id"],
            source_placement_node_id=identity["placement_node_id"],
            owner_node_id=identity["owner_node_id"],
            source_refs=source_refs,
            trace=result.trace,
        )
        _upsert_evidence_state(
            session,
            node_id=job.node_id,
            evidence_status="succeeded",
            source_mode=str(result.trace.get("mode") or "hybrid_bge_rag"),
            trigger_policy="stale_until_manual_refresh",
            selected_chunk_ids=selected_chunk_ids,
            source_refs=source_refs,
            diagnostics=diagnostics,
            stale_reason=None,
            latest_error=None,
            refreshed=True,
        )
    return {
        "action": "rag_evidence_refresh",
        "node_id": job.node_id,
        "source_count": len(source_refs),
        "selected_chunk_ids": selected_chunk_ids,
        "mode": result.trace.get("mode"),
    }


def _mark_evidence_failure(*, node_id: str, error: str, evidence_status: str) -> None:
    with db_session() as session:
        _upsert_evidence_state(
            session,
            node_id=node_id,
            evidence_status=evidence_status,
            source_mode="catalog_node_evidence",
            diagnostics={"failure": {"error": error[:1000], "status": evidence_status}},
            latest_error=error[:1000],
        )


def _catalog_point_context(session: Any, *, node_id: str) -> dict[str, Any]:
    from server.app.domains.catalog_tree.media_bindings import student_video_readiness
    from server.app.domains.catalog_tree.related_links import related_links

    node = get_node(session, node_id)
    if not point_capable(node):
        raise RuntimeError("Catalog-node evidence jobs require a point node")
    content = get_content(session, node_id)
    if not content:
        raise RuntimeError("Catalog-node evidence refresh requires saved point content")
    path = breadcrumbs(session, node_id)
    path_titles = catalog_path_titles_with_chapter(node, path)
    video_readiness = student_video_readiness(session, node_id)
    related = related_links(session, node_id, include_hidden=False, include_defaults=True)
    principle = reaction_principle_text(content) if content.get("principle_mode") == "equation" else clean(content.get("principle_text"))
    equation_terms = reaction_derived_terms(content) if content.get("principle_mode") == "equation" else {
        "formulae": [],
        "aliases": [],
        "reaction_features": [],
        "annotation_formulae": [],
        "annotation_aliases": [],
        "condition_tags": [],
        "participants": [],
    }
    field_contributors = [
        key
        for key, value in {
            "title": content.get("point_title") or node.get("title"),
            "catalog_path": path_titles,
            "normalized_equations": content.get("reaction_equations") or [],
            "phenomenon_explanation": content.get("phenomenon_explanation"),
            "safety_note": content.get("safety_note"),
            "video_readiness": video_readiness if video_readiness.get("has_video") else None,
            "related_points": related,
        }.items()
        if value
    ]
    return {
        "node_id": node_id,
        "placement_node_id": node_id,
        "canonical_point_id": node.get("canonical_point_id") or node_id,
        "chapter_id": node.get("chapter_id"),
        "title": clean(content.get("point_title")) or node.get("title"),
        "catalog_path": path_titles,
        "principle": principle,
        "normalized_equations": content.get("reaction_equations") or [],
        "phenomenon_explanation": clean(content.get("phenomenon_explanation")),
        "safety_note": clean(content.get("safety_note")),
        "formulae": equation_terms.get("formulae") or [],
        "aliases": equation_terms.get("aliases") or [],
        "reaction_features": equation_terms.get("reaction_features") or [],
        "annotation_formulae": equation_terms.get("annotation_formulae") or [],
        "annotation_aliases": equation_terms.get("annotation_aliases") or [],
        "condition_tags": equation_terms.get("condition_tags") or [],
        "video_readiness": video_readiness,
        "related_points": related,
        "field_contributors": field_contributors,
    }


def _catalog_point_queries(context: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    path_text = " ".join(context.get("catalog_path") or [])
    equation_text = " ".join(
        reaction_row_display_text(row)
        for row in context.get("normalized_equations") or []
        if isinstance(row, dict)
    )
    related_text = " ".join(str(item.get("target_title") or item.get("title") or "") for item in context.get("related_points") or [] if isinstance(item, dict))
    base_parts = [
        path_text,
        str(context.get("title") or ""),
        equation_text,
        str(context.get("phenomenon_explanation") or ""),
        str(context.get("safety_note") or ""),
    ]
    chemistry_terms = " ".join(
        [
            *(context.get("formulae") or []),
            *(context.get("aliases") or []),
            *(context.get("reaction_features") or []),
            *(context.get("annotation_formulae") or []),
            *(context.get("annotation_aliases") or []),
            *(context.get("condition_tags") or []),
        ]
    )
    raw_queries = [
        " ".join(item for item in base_parts if item),
        " ".join(item for item in [str(context.get("title") or ""), chemistry_terms, str(context.get("phenomenon_explanation") or "")] if item),
        " ".join(item for item in [path_text, str(context.get("title") or ""), related_text] if item),
    ]
    queries: list[str] = []
    seen: set[str] = set()
    for query in raw_queries:
        normalized = " ".join(str(query or "").split())
        if normalized and normalized not in seen:
            seen.add(normalized)
            queries.append(normalized)
    return queries[:3], {
        "status": "generated" if len(queries) > 1 else "fallback",
        "provider": "catalog_point_job",
        "field_contributors": context.get("field_contributors") or [],
        "queries": queries[:3],
    }


def _rag_runtime_gate(settings: Any) -> dict[str, Any]:
    runtime = {
        "hybrid_bge_enabled": bool(settings.rag_hybrid_bge_enabled),
        "query_generation_enabled": bool(settings.rag_query_generation_enabled),
        "bge_service_url": settings.rag_bge_service_url,
        "vector_top_k": int(settings.rag_vector_top_k),
        "rerank_top_k": int(settings.rag_rerank_top_k),
        "final_top_k": int(settings.rag_final_top_k),
    }
    if not settings.rag_hybrid_bge_enabled:
        return {
            "healthy": False,
            "status": "unavailable",
            "reason_code": "hybrid_bge_disabled",
            "message": "Hybrid BGE RAG is disabled; catalog-node evidence refresh was deferred.",
            "rag_runtime": runtime,
        }
    if not settings.rag_bge_service_url:
        return {
            "healthy": False,
            "status": "unavailable",
            "reason_code": "bge_not_configured",
            "message": "BGE service URL is not configured; catalog-node evidence refresh was deferred.",
            "rag_runtime": runtime,
        }
    try:
        with urllib.request.urlopen(
            f"{settings.rag_bge_service_url.rstrip('/')}/metrics",
            timeout=min(max(1.0, float(settings.rag_bge_timeout_seconds)), 2.0),
        ) as response:
            metrics = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        return {
            "healthy": False,
            "status": "unavailable",
            "reason_code": "bge_unreachable",
            "message": f"BGE service is unreachable; catalog-node evidence refresh was deferred: {exc.__class__.__name__}: {str(exc)[:160]}",
            "rag_runtime": runtime,
        }
    if not isinstance(metrics, dict) or not metrics.get("ok"):
        return {
            "healthy": False,
            "status": "unavailable",
            "reason_code": "bge_degraded",
            "message": "BGE service responded but is not healthy; catalog-node evidence refresh was deferred.",
            "rag_runtime": runtime,
            "bge_metrics": metrics if isinstance(metrics, dict) else None,
        }
    return {
        "healthy": True,
        "status": "healthy",
        "reason_code": "",
        "message": "Hybrid BGE RAG is healthy.",
        "rag_runtime": runtime,
        "bge_metrics": metrics,
    }


def _legacy_retrieve_catalog_context(
    repositories: RepositoryProvider,
    *,
    context: dict[str, Any],
    query: str,
    limit: int,
) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for chunk in repositories.content.source_chunks():
        score = keyword_score(query, chunk, chapter_id=context.get("chapter_id"))
        if score > 0.04:
            candidates.append({**chunk, "_score": score})
    candidates.sort(key=lambda item: float(item.get("_score") or 0.0), reverse=True)
    return candidates[: max(1, limit)]


def _source_refs_from_chunks(chunks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    seen: set[str] = set()
    for chunk in chunks:
        chunk_id = str(chunk.get("chunk_id") or chunk.get("id") or "").strip()
        if not chunk_id or chunk_id in seen:
            continue
        seen.add(chunk_id)
        try:
            ref = _source_evidence_payload(_source_from_chunk(chunk))
        except Exception:
            ref = {
                "chunk_id": chunk_id,
                "source_file": chunk.get("source_file"),
                "document_id": chunk.get("document_id"),
                "page_number": chunk.get("page_number"),
                "section_title": chunk.get("section_title"),
                "text_preview": " ".join(str(chunk.get("text") or chunk.get("markdown") or "").split())[:360],
                "content_type": (chunk.get("metadata") or {}).get("content_type") if isinstance(chunk.get("metadata"), dict) else None,
            }
        refs.append(ref)
    return refs


def _replace_evidence_bindings(
    session: Any,
    *,
    node_id: str,
    canonical_point_id: str,
    source_placement_node_id: str,
    owner_node_id: str,
    source_refs: list[dict[str, Any]],
    trace: dict[str, Any],
) -> None:
    trace_by_chunk = {
        str(item.get("chunk_id")): item
        for item in (trace.get("final_evidence") or [])
        if isinstance(item, dict) and item.get("chunk_id")
    }
    session.execute(
        text(
            """
            UPDATE experiment_catalog_point_evidence_bindings
            SET freshness_status = 'stale',
                selection_status = CASE WHEN selection_status = 'selected' THEN 'stale' ELSE selection_status END,
                updated_at = now()
            WHERE canonical_point_id = :canonical_point_id
               OR node_id = :node_id
            """
        ),
        {"node_id": node_id, "canonical_point_id": canonical_point_id},
    )
    for rank, ref in enumerate(source_refs, start=1):
        chunk_id = str(ref.get("chunk_id") or "").strip()
        if not chunk_id:
            continue
        candidate = trace_by_chunk.get(chunk_id, {})
        session.execute(
            text(
                """
                INSERT INTO experiment_catalog_point_evidence_bindings (
                  node_id, canonical_point_id, source_placement_node_id,
                  chunk_id, evidence_role, selection_status, freshness_status,
                  rank, score, rerank_score, source_metadata, diagnostics, updated_at
                )
                VALUES (
                  :node_id, :canonical_point_id, :source_placement_node_id,
                  :chunk_id, 'dynamic_rag', 'selected', 'fresh',
                  :rank, :score, :rerank_score, CAST(:source_metadata AS jsonb),
                  CAST(:diagnostics AS jsonb), now()
                )
                ON CONFLICT (node_id, chunk_id, evidence_role) DO UPDATE SET
                  canonical_point_id = EXCLUDED.canonical_point_id,
                  source_placement_node_id = EXCLUDED.source_placement_node_id,
                  selection_status = 'selected',
                  freshness_status = 'fresh',
                  rank = EXCLUDED.rank,
                  score = EXCLUDED.score,
                  rerank_score = EXCLUDED.rerank_score,
                  source_metadata = EXCLUDED.source_metadata,
                  diagnostics = EXCLUDED.diagnostics,
                  updated_at = now()
                """
            ),
            {
                "node_id": owner_node_id,
                "canonical_point_id": canonical_point_id,
                "source_placement_node_id": source_placement_node_id,
                "chunk_id": chunk_id,
                "rank": rank,
                "score": candidate.get("score"),
                "rerank_score": candidate.get("rerank_score"),
                "source_metadata": _json_param(ref),
                "diagnostics": _json_param(candidate),
            },
        )
