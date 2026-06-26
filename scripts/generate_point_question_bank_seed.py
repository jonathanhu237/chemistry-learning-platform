from __future__ import annotations

import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from threading import Lock
from types import SimpleNamespace
from typing import Any

from sqlalchemy import bindparam, text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.app.domains.questions.bank import (  # noqa: E402
    _ensure_catalog_point_experiment,
    process_question_bank_evidence_refresh_jobs,
    refresh_catalog_question_bank_evidence,
)
from server.app.domains.questions.drafts import publish_question_draft  # noqa: E402
from server.app.domains.questions.generation import generate_question_drafts  # noqa: E402
from server.app.domains.questions.workbench import _ensure_question_workbench_rag_ready, _load_workbench_evidence_package  # noqa: E402
from server.app.experiment_admin_schemas import GenerationRequest  # noqa: E402
from server.app.infrastructure.database import apply_migrations, db_session  # noqa: E402
from scripts.seed_current_question_bank import DEFAULT_SEED_PATH, export_seed, validate_seed_payload, write_seed  # noqa: E402


PRINT_LOCK = Lock()


@dataclass(frozen=True)
class PointGroup:
    canonical_point_id: str
    node_ids: list[str]
    title: str
    chapter_id: str


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=str)


def _print_json(payload: dict[str, Any], *, indent: int | None = None) -> None:
    with PRINT_LOCK:
        print(json.dumps(payload, ensure_ascii=False, indent=indent), flush=True)


def _load_user(username: str) -> SimpleNamespace:
    with db_session() as session:
        row = (
            session.execute(
                text(
                    """
                    SELECT id, username, role, display_name, status
                    FROM app_users
                    WHERE username = :username
                    LIMIT 1
                    """
                ),
                {"username": username},
            )
            .mappings()
            .first()
        )
    if not row:
        raise SystemExit(f"Teacher user not found: {username}")
    return SimpleNamespace(**dict(row))


def _point_groups(limit: int | None = None, canonical_point_id: str | None = None) -> list[PointGroup]:
    query = """
        WITH point_nodes AS (
          SELECT n.id,
                 COALESCE(n.canonical_point_id, n.id) AS canonical_point_id,
                 n.chapter_id,
                 n.display_order,
                 COALESCE(content.point_title, cp.title, n.title) AS point_title
          FROM experiment_catalog_nodes n
          LEFT JOIN experiment_catalog_points cp ON cp.id = n.canonical_point_id
          LEFT JOIN LATERAL (
            SELECT pc.point_title
            FROM experiment_catalog_point_content pc
            WHERE pc.node_id = n.id
               OR (n.canonical_point_id IS NOT NULL AND pc.canonical_point_id = n.canonical_point_id)
            ORDER BY
              CASE WHEN pc.node_id = n.id THEN 0 ELSE 1 END,
              pc.updated_at DESC
            LIMIT 1
          ) content ON TRUE
          WHERE n.node_kind = 'point'
            AND n.status <> 'archived'
        )
        SELECT canonical_point_id,
               array_agg(id ORDER BY chapter_id, display_order, id) AS node_ids,
               COALESCE(MAX(point_title), canonical_point_id) AS title,
               MIN(chapter_id) AS chapter_id
        FROM point_nodes
        GROUP BY canonical_point_id
        ORDER BY MIN(chapter_id), MIN(display_order), canonical_point_id
    """
    with db_session() as session:
        rows = [dict(row) for row in session.execute(text(query)).mappings().all()]
    groups = [
        PointGroup(
            canonical_point_id=str(row["canonical_point_id"]),
            node_ids=[str(item) for item in row["node_ids"] if str(item).strip()],
            title=str(row.get("title") or row["canonical_point_id"]),
            chapter_id=str(row.get("chapter_id") or ""),
        )
        for row in rows
    ]
    if canonical_point_id:
        groups = [group for group in groups if group.canonical_point_id == canonical_point_id]
    return groups[:limit] if limit else groups


def _archive_existing_generated_questions() -> dict[str, int]:
    with db_session() as session:
        question_count = int(
            session.execute(
                text(
                    """
                    UPDATE experiment_questions q
                    SET status = 'archived', updated_at = now()
                    FROM experiment_question_banks b
                    WHERE q.bank_id = b.id
                      AND b.bank_kind = 'generated'
                      AND q.status <> 'archived'
                    RETURNING q.id
                    """
                )
            ).rowcount
            or 0
        )
        bank_count = int(
            session.execute(
                text(
                    """
                    UPDATE experiment_question_banks
                    SET status = 'archived', updated_at = now()
                    WHERE bank_kind = 'generated'
                      AND status <> 'archived'
                    RETURNING id
                    """
                )
            ).rowcount
            or 0
        )
        session.execute(text("DELETE FROM experiment_question_workbench_sessions"))
        session.execute(text("DELETE FROM experiment_question_drafts"))
        session.execute(text("DELETE FROM experiment_question_generations"))
        session.execute(text("DELETE FROM question_semantic_fingerprints"))
    return {"archived_questions": question_count, "archived_banks": bank_count}


def _published_count_for_group(node_ids: list[str], canonical_point_id: str) -> int:
    with db_session() as session:
        return int(
            session.execute(
                text(
                    """
                    SELECT COUNT(*)
                    FROM experiment_questions
                    WHERE status = 'published'
                      AND (
                        :canonical_point_id = ANY(primary_canonical_point_ids)
                        OR source_placement_node_ids && CAST(:node_ids AS text[])
                        OR primary_point_node_ids && CAST(:node_ids AS text[])
                      )
                    """
                ),
                {"canonical_point_id": canonical_point_id, "node_ids": node_ids},
            ).scalar_one()
            or 0
        )


def _trim_excess_published_questions(groups: list[PointGroup], *, questions_per_point: int) -> dict[str, Any]:
    archived_ids: list[str] = []
    overfilled_groups: list[dict[str, Any]] = []
    with db_session() as session:
        for group in groups:
            rows = (
                session.execute(
                    text(
                        """
                        SELECT q.id::text AS id
                        FROM experiment_questions q
                        JOIN experiment_question_banks b ON b.id = q.bank_id
                        WHERE q.status = 'published'
                          AND b.bank_kind = 'generated'
                          AND (
                            :canonical_point_id = ANY(q.primary_canonical_point_ids)
                            OR q.source_placement_node_ids && CAST(:node_ids AS text[])
                            OR q.primary_point_node_ids && CAST(:node_ids AS text[])
                          )
                        ORDER BY q.created_at DESC NULLS LAST, q.published_at DESC NULLS LAST, q.id::text DESC
                        """
                    ),
                    {"canonical_point_id": group.canonical_point_id, "node_ids": group.node_ids},
                )
                .mappings()
                .all()
            )
            question_ids = [str(row["id"]) for row in rows]
            if len(question_ids) <= questions_per_point:
                continue
            excess_ids = question_ids[questions_per_point:]
            session.execute(
                text(
                    """
                    UPDATE experiment_questions
                    SET status = 'archived', updated_at = now()
                    WHERE id IN :question_ids
                    """
                ).bindparams(bindparam("question_ids", expanding=True)),
                {"question_ids": excess_ids},
            )
            archived_ids.extend(excess_ids)
            overfilled_groups.append(
                {
                    "canonical_point_id": group.canonical_point_id,
                    "node_ids": group.node_ids,
                    "title": group.title,
                    "before": len(question_ids),
                    "kept": questions_per_point,
                    "archived": len(excess_ids),
                }
            )
    return {
        "examined_groups": len(groups),
        "overfilled_groups": len(overfilled_groups),
        "archived_questions": len(set(archived_ids)),
        "archived_question_id_sample": sorted(set(archived_ids))[:20],
        "examples": overfilled_groups[:20],
    }


def _ensure_evidence_for_group(group: PointGroup, *, force: bool) -> dict[str, Any]:
    queued_jobs: list[str] = []
    skipped_count = 0
    queued_payloads: list[dict[str, Any]] = []
    for point_node_id in group.node_ids:
        queued = refresh_catalog_question_bank_evidence(point_node_id=point_node_id, force=force)
        queued_payloads.append(queued)
        queued_jobs.extend(str(job_id) for job_id in queued.get("job_ids") or [])
        skipped_count += int(queued.get("skipped_count") or 0)
    if queued_jobs:
        processed = process_question_bank_evidence_refresh_jobs(queued_jobs)
    else:
        processed = {"processed_count": 0, "skipped_count": skipped_count, "error_count": 0, "errors": []}
    return {
        "queued": {"job_ids": queued_jobs, "skipped_count": skipped_count, "points": queued_payloads},
        "processed": processed,
    }


def _prompt_for_group(group: PointGroup) -> str:
    return (
        f"请基于该点位的三段式点位内容和教材 RAG 证据，为点位《{group.title}》生成 5 道客观题。"
        "要求：覆盖实验原理、现象解释和安全提示；题目之间不要重复；"
        "必须严格返回 JSON questions 数组，每题包含 question_type、stem、options、answer、explanation；"
        "single_choice 的 answer.value 使用 A/B/C/D，true_false 的 answer.value 使用 true/false，"
        "fill_blank 的 answer.accepted_answers 使用字符串数组。"
    )


def _generate_and_publish_group(
    group: PointGroup,
    *,
    user: SimpleNamespace,
    questions_per_point: int,
    max_attempts: int,
) -> dict[str, Any]:
    with db_session() as session:
        experiment = _ensure_catalog_point_experiment(session, group.node_ids[0], actor_user_id=str(user.id))
    published_ids: list[str] = []
    warnings: list[str] = []
    for attempt in range(1, max_attempts + 1):
        current_count = _published_count_for_group(group.node_ids, group.canonical_point_id)
        remaining = questions_per_point - current_count
        if remaining <= 0:
            break
        request = GenerationRequest(
            experiment_id=str(experiment["id"]),
            prompt=_prompt_for_group(group),
            question_types=["single_choice", "single_choice", "true_false", "fill_blank", "single_choice"],
            count=remaining,
            difficulty="basic",
            chapter_ids=[group.chapter_id] if group.chapter_id else [],
            target_point_node_ids=group.node_ids,
        )
        result = generate_question_drafts(
            payload=request,
            user=user,
            rag_gate=_ensure_question_workbench_rag_ready(),
            evidence_loader=_load_workbench_evidence_package,
        )
        if result.get("mode") != "openai_sdk":
            warnings.append(
                f"attempt {attempt}: LLM generation fallback is not allowed: {result.get('mode') or 'unknown'}"
            )
            time.sleep(min(8.0, 1.5 * attempt))
            continue
        for draft in result.get("drafts") or []:
            try:
                published = publish_question_draft(draft_id=str(draft["id"]), user=user)
                published_ids.append(str(published["id"]))
            except Exception as exc:  # noqa: BLE001 - keep batch generation moving and report failed drafts.
                warnings.append(f"{exc.__class__.__name__}: {str(exc)[:300]}")
        time.sleep(0.2)
    final_count = _published_count_for_group(group.node_ids, group.canonical_point_id)
    return {
        "canonical_point_id": group.canonical_point_id,
        "node_ids": group.node_ids,
        "title": group.title,
        "published_count": final_count,
        "new_question_ids": published_ids,
        "warnings": warnings,
        "ok": final_count >= questions_per_point,
    }


def _export_current_seed(path: Path) -> dict[str, Any]:
    with db_session() as session:
        payload = export_seed(session)
        validation = validate_seed_payload(payload, session=session)
        if not validation["ok"]:
            raise RuntimeError("Generated question-bank seed failed validation:\n" + "\n".join(validation["errors"][:80]))
    write_seed(path, payload)
    return {"path": str(path), "validation": validation, "summary": payload.get("metadata", {}).get("summary") or {}}


def _process_group(
    *,
    index: int,
    total: int,
    group: PointGroup,
    user: SimpleNamespace,
    questions_per_point: int,
    max_attempts: int,
    skip_evidence_refresh: bool,
    force_evidence: bool,
) -> dict[str, Any]:
    _print_json(
        {
            "progress": f"{index}/{total}",
            "canonical_point_id": group.canonical_point_id,
            "node_count": len(group.node_ids),
            "title": group.title,
        }
    )
    try:
        existing_count = _published_count_for_group(group.node_ids, group.canonical_point_id)
        if existing_count >= questions_per_point:
            result = {
                "canonical_point_id": group.canonical_point_id,
                "node_ids": group.node_ids,
                "title": group.title,
                "published_count": existing_count,
                "new_question_ids": [],
                "warnings": [],
                "ok": True,
                "skipped": "already_complete",
            }
            _print_json({"result": result})
            return {"ok": True, "result": result}
        if not skip_evidence_refresh:
            evidence = _ensure_evidence_for_group(group, force=force_evidence)
            if evidence["processed"].get("error_count"):
                raise RuntimeError(json.dumps(evidence["processed"], ensure_ascii=False))
        result = _generate_and_publish_group(
            group,
            user=user,
            questions_per_point=questions_per_point,
            max_attempts=max_attempts,
        )
        _print_json({"result": result})
        if not result["ok"]:
            return {"ok": False, "failure": result}
        return {"ok": True, "result": result}
    except Exception as exc:  # noqa: BLE001 - batch report is more useful than losing progress.
        failure = {
            "canonical_point_id": group.canonical_point_id,
            "node_ids": group.node_ids,
            "title": group.title,
            "error": f"{exc.__class__.__name__}: {str(exc)[:600]}",
        }
        _print_json({"failure": failure})
        return {"ok": False, "failure": failure}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a complete point-bound question bank through real RAG + LLM paths.")
    parser.add_argument("--questions-per-point", type=int, default=5)
    parser.add_argument("--teacher-username", default="admin")
    parser.add_argument("--path", type=Path, default=DEFAULT_SEED_PATH)
    parser.add_argument("--limit", type=int, default=None, help="Only process the first N canonical point groups.")
    parser.add_argument("--canonical-point-id", default=None, help="Only process one canonical point group.")
    parser.add_argument("--only-underfilled", action="store_true", help="Only process groups that currently have fewer than the requested number of published questions.")
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--skip-migrations", action="store_true")
    parser.add_argument("--keep-existing", action="store_true", help="Do not archive existing generated question banks first.")
    parser.add_argument("--skip-evidence-refresh", action="store_true")
    parser.add_argument("--skip-export", action="store_true")
    parser.add_argument("--force-evidence", action="store_true")
    parser.add_argument("--concurrency", type=int, default=8, help="Number of point groups to process concurrently.")
    parser.add_argument("--trim-excess", action="store_true", help="Archive extra published generated questions beyond the requested per-point count before exporting.")
    args = parser.parse_args()

    if not args.skip_migrations:
        apply_migrations()
    user = _load_user(args.teacher_username)
    if not args.keep_existing:
        cleanup = _archive_existing_generated_questions()
        _print_json({"cleanup": cleanup})

    groups = _point_groups(limit=args.limit, canonical_point_id=args.canonical_point_id)
    if args.only_underfilled:
        groups = [
            group
            for group in groups
            if _published_count_for_group(group.node_ids, group.canonical_point_id) < args.questions_per_point
        ]
        _print_json({"underfilled_group_count": len(groups), "questions_per_point": args.questions_per_point})
    failures: list[dict[str, Any]] = []
    concurrency = max(1, int(args.concurrency or 1))
    if concurrency == 1:
        for index, group in enumerate(groups, start=1):
            outcome = _process_group(
                index=index,
                total=len(groups),
                group=group,
                user=user,
                questions_per_point=args.questions_per_point,
                max_attempts=args.max_attempts,
                skip_evidence_refresh=args.skip_evidence_refresh,
                force_evidence=args.force_evidence,
            )
            if not outcome["ok"]:
                failures.append(outcome["failure"])
    else:
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [
                executor.submit(
                    _process_group,
                    index=index,
                    total=len(groups),
                    group=group,
                    user=user,
                    questions_per_point=args.questions_per_point,
                    max_attempts=args.max_attempts,
                    skip_evidence_refresh=args.skip_evidence_refresh,
                    force_evidence=args.force_evidence,
                )
                for index, group in enumerate(groups, start=1)
            ]
            for future in as_completed(futures):
                outcome = future.result()
                if not outcome["ok"]:
                    failures.append(outcome["failure"])

    if failures:
        _print_json({"failed_count": len(failures), "failures": failures[:50]}, indent=2)
        raise SystemExit(1)

    if args.trim_excess:
        trim_result = _trim_excess_published_questions(groups, questions_per_point=args.questions_per_point)
        _print_json({"trim": trim_result}, indent=2)

    if not args.skip_export:
        export_result = _export_current_seed(args.path)
        _print_json({"export": export_result}, indent=2)


if __name__ == "__main__":
    main()
