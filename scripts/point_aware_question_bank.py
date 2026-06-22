from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import text

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.app.canonical_evidence import resolve_source_refs
from server.app.infrastructure.database import apply_migrations, db_session
from server.app.domains.catalog.experiments import _video_candidates
from server.app.domains.experiment_points.canonical_points import candidate_point_key as _candidate_point_key
from server.app.domains.questions.bank import _validate_question_payload

ARTIFACT_DIR = ROOT / "artifacts" / "point-aware-question-bank"
SEED_DIR = ROOT / "data" / "seed"
DEFAULT_INVENTORY = SEED_DIR / "experiment_points" / "formal_experiment_point_inventory.json"
DEFAULT_INVENTORY_AUDIT = ARTIFACT_DIR / "formal_experiment_point_inventory_audit.md"
DEFAULT_SCHEMA = SEED_DIR / "question_bank" / "point_aware_question_bank_schema.json"
DEFAULT_VALIDATION_REPORT = ARTIFACT_DIR / "point_aware_question_bank_validation_report.json"
DEFAULT_SCAFFOLD = ARTIFACT_DIR / "full_candidate_scaffold_v1.json"
DEFAULT_SCAFFOLD_REPORT = ARTIFACT_DIR / "full_candidate_scaffold_v1_review.md"
DEFAULT_REVIEWED_CHUNKS_DIR = ARTIFACT_DIR / "reviewed_old_bank_chunks"
DEFAULT_RELEASE_BANK = SEED_DIR / "question_bank" / "rebuilt_question_bank_merged_v1.json"
DEFAULT_REVIEWED_MERGED = DEFAULT_REVIEWED_CHUNKS_DIR / "reviewed_old_bank_merged_v1.json"
DEFAULT_REVIEWED_MERGE_REPORT = DEFAULT_REVIEWED_CHUNKS_DIR / "reviewed_old_bank_merged_v1_report.md"
DEFAULT_REVIEWED_MERGE_VALIDATION_REPORT = DEFAULT_REVIEWED_CHUNKS_DIR / "reviewed_old_bank_merged_v1_validation_report.json"
DEFAULT_REVIEWED_MERGE_IMPORT_REPORT = DEFAULT_REVIEWED_CHUNKS_DIR / "reviewed_old_bank_merged_v1_import_dry_run_report.json"

ALLOWED_QUESTION_TYPES = {"single_choice", "true_false", "fill_blank"}
ALLOWED_REVIEW_DECISIONS = {"keep", "rewrite", "reject"}
ALLOWED_OPTION_ROLES = {
    "correct_evidence",
    "distractor_misconception",
    "adjacent_experiment",
    "adjacent_point",
    "weak_distractor",
    "unrelated_distractor",
    "uncertain",
}
MAX_PHONE_FILL_ANSWER_LENGTH = 12
PHONE_UNFRIENDLY_PATTERNS = [
    re.compile(r"[+＋].*[+＋]"),
    re.compile(r"->|→|=|⇌"),
    re.compile(r"，|,|；|;|、.*、"),
    re.compile(r"\s{2,}"),
]


def _json_dump(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _json_load(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "").strip()).lower()


def _experiment_rows(session: Any) -> list[dict[str, Any]]:
    rows = session.execute(
        text(
            """
            SELECT fe.id,
                   fe.code,
                   fe.title,
                   fe.summary,
                   fe.status,
                   fe.display_order,
                   fe.source_refs,
                   fe.metadata,
                   COALESCE(
                     jsonb_agg(
                       jsonb_build_object(
                         'chapter_id', ecb.chapter_id,
                         'coverage_type', ecb.coverage_type,
                         'sort_order', ecb.sort_order
                       )
                       ORDER BY ecb.sort_order, ecb.chapter_id
                     ) FILTER (WHERE ecb.chapter_id IS NOT NULL),
                     '[]'::jsonb
                   ) AS chapter_bindings
            FROM formal_experiments fe
            LEFT JOIN experiment_chapter_bindings ecb ON ecb.experiment_id = fe.id
            WHERE fe.status = 'published'
              AND COALESCE(fe.metadata->>'archived_by_catalog_seed', 'false') <> 'true'
            GROUP BY fe.id, fe.code, fe.title, fe.summary, fe.status, fe.display_order, fe.source_refs, fe.metadata
            ORDER BY fe.display_order, fe.code
            """
        )
    ).mappings()
    return [dict(row) for row in rows]


def _media_binding_stats(session: Any) -> dict[str, dict[str, dict[str, Any]]]:
    rows = session.execute(
        text(
            """
            SELECT mb.target_id AS experiment_id,
                   mb.metadata->>'point_key' AS point_key,
                   mb.metadata->>'point_title' AS point_title,
                   COUNT(*) AS resource_count,
                   COUNT(*) FILTER (WHERE mb.status = 'published') AS published_count,
                   array_agg(mb.title ORDER BY mb.sort_order, mb.created_at) AS resource_titles
            FROM media_bindings mb
            WHERE mb.target_type = 'experiment'
              AND mb.status <> 'archived'
            GROUP BY mb.target_id, mb.metadata->>'point_key', mb.metadata->>'point_title'
            """
        )
    ).mappings()
    by_experiment: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in rows:
        experiment_id = str(row["experiment_id"])
        point_key = str(row.get("point_key") or "legacy-unassigned")
        by_experiment[experiment_id][point_key] = {
            "point_key": point_key,
            "point_title": row.get("point_title"),
            "resource_count": int(row.get("resource_count") or 0),
            "published_count": int(row.get("published_count") or 0),
            "resource_titles": list(row.get("resource_titles") or []),
        }
    return by_experiment


def _canonical_chunk_ids_by_experiment(session: Any) -> dict[str, list[str]]:
    rows = session.execute(
        text(
            """
            SELECT l.experiment_id, l.evidence_chunk_id AS chunk_id, MIN(l.sort_order) AS sort_order
            FROM experiment_framework_formal_links l
            JOIN source_chunks sc ON sc.id = l.evidence_chunk_id
            WHERE l.relation_type = 'canonical_evidence'
              AND l.evidence_chunk_id IS NOT NULL
              AND COALESCE(sc.metadata->>'source_collection', '') = 'textbook_experiment_clean_v1'
              AND COALESCE(sc.content_status, 'published') = 'published'
            GROUP BY l.experiment_id, l.evidence_chunk_id
            ORDER BY l.experiment_id, MIN(l.sort_order), l.evidence_chunk_id
            """
        )
    ).mappings()
    by_experiment: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        by_experiment[str(row["experiment_id"])].append(str(row["chunk_id"]))
    return by_experiment


def _theory_chunk_counts(session: Any, chapter_ids: list[str]) -> dict[str, int]:
    if not chapter_ids:
        return {}
    rows = session.execute(
        text(
            """
            SELECT chapter_id, COUNT(*) AS chunk_count
            FROM source_chunks
            WHERE chapter_id = ANY(:chapter_ids)
              AND COALESCE(metadata->>'source_collection', '') = 'textbook_inorganic_lower_v1'
              AND COALESCE(content_status, 'published') = 'published'
            GROUP BY chapter_id
            """
        ),
        {"chapter_ids": chapter_ids},
    ).mappings()
    return {str(row["chapter_id"]): int(row["chunk_count"] or 0) for row in rows}


def _theory_chunk_ids_by_chapter(session: Any, chapter_ids: list[str]) -> dict[str, list[str]]:
    if not chapter_ids:
        return {}
    rows = session.execute(
        text(
            """
            SELECT chapter_id, id AS chunk_id
            FROM source_chunks
            WHERE chapter_id = ANY(:chapter_ids)
              AND COALESCE(metadata->>'source_collection', '') = 'textbook_inorganic_lower_v1'
              AND COALESCE(content_status, 'published') = 'published'
            ORDER BY chapter_id, chunk_index, id
            """
        ),
        {"chapter_ids": chapter_ids},
    ).mappings()
    by_chapter: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        by_chapter[str(row["chapter_id"])].append(str(row["chunk_id"]))
    return by_chapter


def _old_question_stats(session: Any) -> dict[str, dict[str, Any]]:
    rows = session.execute(
        text(
            """
            SELECT experiment_id,
                   COUNT(*) AS total,
                   COUNT(*) FILTER (WHERE question_type = 'single_choice') AS single_choice,
                   COUNT(*) FILTER (WHERE question_type = 'true_false') AS true_false,
                   COUNT(*) FILTER (WHERE question_type = 'fill_blank') AS fill_blank,
                   COUNT(*) FILTER (WHERE cardinality(COALESCE(related_knowledge_point_ids, '{}'::text[])) > 0) AS with_kp,
                   COUNT(*) FILTER (WHERE COALESCE(metadata ? 'primary_point_keys', false)) AS with_point_metadata
            FROM experiment_questions
            WHERE status <> 'archived'
            GROUP BY experiment_id
            """
        )
    ).mappings()
    return {
        str(row["experiment_id"]): {
            "total": int(row["total"] or 0),
            "single_choice": int(row["single_choice"] or 0),
            "true_false": int(row["true_false"] or 0),
            "fill_blank": int(row["fill_blank"] or 0),
            "with_kp": int(row["with_kp"] or 0),
            "with_point_metadata": int(row["with_point_metadata"] or 0),
        }
        for row in rows
    }


def _build_video_points(experiment: dict[str, Any], media_stats: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for index, title in enumerate(_video_candidates(experiment.get("metadata"))):
        point_key = _candidate_point_key(index, title)
        stats = media_stats.get(point_key, {})
        points.append(
            {
                "point_key": point_key,
                "point_title": title,
                "source": "formal_experiment.video_candidates",
                "candidate_index": index + 1,
                "resource_count": int(stats.get("resource_count") or 0),
                "published_count": int(stats.get("published_count") or 0),
                "resource_titles": list(stats.get("resource_titles") or []),
            }
        )
    for point_key, stats in sorted(media_stats.items()):
        if point_key not in {point["point_key"] for point in points}:
            points.append(
                {
                    "point_key": point_key,
                    "point_title": stats.get("point_title") or point_key,
                    "source": "stored_media_binding",
                    "candidate_index": None,
                    "resource_count": int(stats.get("resource_count") or 0),
                    "published_count": int(stats.get("published_count") or 0),
                    "resource_titles": list(stats.get("resource_titles") or []),
                }
            )
    return points


def build_inventory() -> dict[str, Any]:
    with db_session() as session:
        experiments = _experiment_rows(session)
        media_stats = _media_binding_stats(session)
        canonical_ids = _canonical_chunk_ids_by_experiment(session)
        old_stats = _old_question_stats(session)
        all_chapter_ids = sorted(
            {
                str(binding.get("chapter_id"))
                for experiment in experiments
                for binding in _as_list(experiment.get("chapter_bindings"))
                if binding.get("chapter_id")
            }
        )
        theory_counts = _theory_chunk_counts(session, all_chapter_ids)
        theory_ids_by_chapter = _theory_chunk_ids_by_chapter(session, all_chapter_ids)
        all_chunk_ids = sorted({chunk_id for values in canonical_ids.values() for chunk_id in values})
        all_theory_chunk_ids = sorted({chunk_id for values in theory_ids_by_chapter.values() for chunk_id in values})
        source_refs = {str(ref["chunk_id"]): ref for ref in resolve_source_refs(session, all_chunk_ids)}
        theory_source_refs = {
            str(ref["chunk_id"]): ref for ref in resolve_source_refs(session, all_theory_chunk_ids)
        }

    inventory_experiments: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    point_count_distribution: Counter[int] = Counter()
    canonical_count_distribution: Counter[int] = Counter()
    for experiment in experiments:
        experiment_id = str(experiment["id"])
        chapter_bindings = _as_list(experiment.get("chapter_bindings"))
        chapter_ids = [str(binding.get("chapter_id")) for binding in chapter_bindings if binding.get("chapter_id")]
        points = _build_video_points(experiment, media_stats.get(experiment_id, {}))
        canonical_chunk_ids = canonical_ids.get(experiment_id, [])
        point_count_distribution[len([p for p in points if p["source"] == "formal_experiment.video_candidates"])] += 1
        canonical_count_distribution[len(canonical_chunk_ids)] += 1

        normalized_titles: Counter[str] = Counter(_normalize_text(point["point_title"]) for point in points)
        duplicate_titles = [title for title, count in normalized_titles.items() if title and count > 1]
        stored_stale = [point for point in points if point["source"] == "stored_media_binding"]
        if not points:
            issues.append({"severity": "blocker", "experiment_id": experiment_id, "kind": "missing_video_points"})
        if not canonical_chunk_ids:
            issues.append({"severity": "blocker", "experiment_id": experiment_id, "kind": "missing_canonical_evidence"})
        if duplicate_titles:
            issues.append(
                {
                    "severity": "major",
                    "experiment_id": experiment_id,
                    "kind": "duplicate_point_titles",
                    "details": duplicate_titles,
                }
            )
        if stored_stale:
            issues.append(
                {
                    "severity": "major",
                    "experiment_id": experiment_id,
                    "kind": "stale_or_extra_stored_point_keys",
                    "details": [{"point_key": p["point_key"], "point_title": p["point_title"]} for p in stored_stale],
                }
            )

        inventory_experiments.append(
            {
                "experiment_id": experiment_id,
                "code": experiment.get("code"),
                "title": experiment.get("title"),
                "summary": experiment.get("summary"),
                "display_order": int(experiment.get("display_order") or 0),
                "chapter_bindings": chapter_bindings,
                "metadata": experiment.get("metadata") or {},
                "video_points": points,
                "canonical_chunk_ids": canonical_chunk_ids,
                "canonical_source_refs": [source_refs[chunk_id] for chunk_id in canonical_chunk_ids if chunk_id in source_refs],
                "supporting_theory_chunk_counts": {
                    chapter_id: theory_counts.get(chapter_id, 0) for chapter_id in chapter_ids
                },
                "supporting_theory_chunk_ids": {
                    chapter_id: theory_ids_by_chapter.get(chapter_id, []) for chapter_id in chapter_ids
                },
                "supporting_theory_source_refs": {
                    chapter_id: [
                        theory_source_refs[chunk_id]
                        for chunk_id in theory_ids_by_chapter.get(chapter_id, [])[:12]
                        if chunk_id in theory_source_refs
                    ]
                    for chapter_id in chapter_ids
                },
                "current_question_stats": old_stats.get(experiment_id, {}),
            }
        )

    return {
        "metadata": {
            "artifact_type": "formal_experiment_point_inventory",
            "version": "point-aware-question-bank-inventory-v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source": "chemistry-admin postgres",
        },
        "summary": {
            "experiment_count": len(inventory_experiments),
            "total_video_points": sum(len(item["video_points"]) for item in inventory_experiments),
            "formal_candidate_point_count": sum(
                1
                for item in inventory_experiments
                for point in item["video_points"]
                if point["source"] == "formal_experiment.video_candidates"
            ),
            "canonical_chunk_count": len(all_chunk_ids),
            "point_count_distribution": {str(key): value for key, value in sorted(point_count_distribution.items())},
            "canonical_count_distribution": {str(key): value for key, value in sorted(canonical_count_distribution.items())},
            "issue_count": len(issues),
            "blocker_count": sum(1 for issue in issues if issue["severity"] == "blocker"),
            "major_count": sum(1 for issue in issues if issue["severity"] == "major"),
        },
        "issues": issues,
        "experiments": inventory_experiments,
    }


def write_inventory_audit(inventory: dict[str, Any], path: Path) -> None:
    summary = inventory["summary"]
    lines = [
        "# Point-Aware Question Bank Inventory Audit",
        "",
        f"- Generated at: `{inventory['metadata']['generated_at']}`",
        f"- Formal experiments: {summary['experiment_count']}",
        f"- Formal candidate video points: {summary['formal_candidate_point_count']}",
        f"- Total point rows including stored extras: {summary['total_video_points']}",
        f"- Canonical experiment chunks referenced: {summary['canonical_chunk_count']}",
        f"- Issues: {summary['issue_count']} (blocker {summary['blocker_count']}, major {summary['major_count']})",
        "",
        "## Point Count Distribution",
        "",
    ]
    for count, experiment_count in summary["point_count_distribution"].items():
        lines.append(f"- {count} point(s): {experiment_count} experiment(s)")
    lines.extend(["", "## Canonical Evidence Distribution", ""])
    for count, experiment_count in summary["canonical_count_distribution"].items():
        lines.append(f"- {count} chunk(s): {experiment_count} experiment(s)")
    lines.extend(["", "## Issues", ""])
    if inventory["issues"]:
        for issue in inventory["issues"]:
            details = issue.get("details")
            detail_text = f" - {details}" if details else ""
            lines.append(f"- [{issue['severity']}] {issue['experiment_id']}: {issue['kind']}{detail_text}")
    else:
        lines.append("- No blocker or major inventory issues found.")
    lines.extend(["", "## Experiments With Few Points", ""])
    few = [
        item
        for item in inventory["experiments"]
        if len([p for p in item["video_points"] if p["source"] == "formal_experiment.video_candidates"]) <= 1
    ]
    for item in few[:30]:
        lines.append(
            f"- `{item['code']}` {item['title']}: "
            f"{len(item['video_points'])} point(s), {len(item['canonical_chunk_ids'])} canonical chunk(s)"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def artifact_schema() -> dict[str, Any]:
    return {
        "artifact_type": "point_aware_question_bank",
        "version": "point-aware-question-bank-v1",
        "required_top_level_keys": ["metadata", "experiments"],
        "experiment_required_keys": ["experiment_id", "experiment_code", "experiment_title", "video_points", "questions"],
        "question_required_keys": [
            "question_id",
            "question_type",
            "stem",
            "answer",
            "explanation",
            "review_decision",
            "primary_point_keys",
            "coverage_tags",
            "source_audit",
        ],
        "allowed_question_types": sorted(ALLOWED_QUESTION_TYPES),
        "allowed_review_decisions": sorted(ALLOWED_REVIEW_DECISIONS),
        "allowed_option_link_roles": sorted(ALLOWED_OPTION_ROLES),
        "fill_blank_policy": {
            "grading": "deterministic_normalized_exact",
            "max_answer_length": MAX_PHONE_FILL_ANSWER_LENGTH,
            "forbidden_answer_shapes": [
                "long reagent combination",
                "full equation",
                "multi-clause explanation",
                "free-form reasoning",
            ],
        },
    }


def write_schema(path: Path) -> None:
    _json_dump(path, artifact_schema())


class ValidationContext:
    def __init__(self, inventory: dict[str, Any]) -> None:
        self.experiments = {str(item["experiment_id"]): item for item in inventory.get("experiments", [])}
        self.point_keys = {
            experiment_id: {str(point["point_key"]) for point in item.get("video_points", [])}
            for experiment_id, item in self.experiments.items()
        }
        self.canonical_chunks = {
            experiment_id: {str(chunk_id) for chunk_id in item.get("canonical_chunk_ids", [])}
            for experiment_id, item in self.experiments.items()
        }


def _error(errors: list[dict[str, Any]], path: str, message: str, severity: str = "error") -> None:
    errors.append({"severity": severity, "path": path, "message": message})


def _is_phone_friendly_fill_answer(answer: str) -> bool:
    normalized = str(answer or "").strip()
    if not normalized:
        return False
    if len(normalized) > MAX_PHONE_FILL_ANSWER_LENGTH:
        return False
    return not any(pattern.search(normalized) for pattern in PHONE_UNFRIENDLY_PATTERNS)


def _validate_objective_payload(question: dict[str, Any], path: str, errors: list[dict[str, Any]]) -> dict[str, Any] | None:
    normalized, validation_errors = _validate_question_payload(
        {
            "question_type": question.get("question_type"),
            "stem": question.get("stem"),
            "options": question.get("options") or [],
            "answer": question.get("answer"),
            "explanation": question.get("explanation"),
            "difficulty": question.get("difficulty") or "basic",
            "source_chunk_ids": question.get("source_audit", {}).get("canonical_chunk_ids")
            or question.get("source_chunk_ids")
            or [],
            "source_refs": question.get("source_refs") or [],
            "related_chapter_ids": question.get("related_chapter_ids") or [],
            "related_knowledge_point_ids": question.get("related_knowledge_point_ids") or [],
            "status": question.get("status") or "draft",
        }
    )
    for item in validation_errors:
        _error(errors, path, item)
    return normalized


def _validate_point_keys(
    question: dict[str, Any],
    *,
    context: ValidationContext,
    experiment_id: str,
    path: str,
    errors: list[dict[str, Any]],
) -> None:
    valid = context.point_keys.get(experiment_id, set())
    keys = [str(key) for key in question.get("primary_point_keys") or [] if str(key).strip()]
    if question.get("review_decision") != "reject" and not keys:
        _error(errors, path + ".primary_point_keys", "accepted or rewrite question must include primary_point_keys")
    for key in keys:
        if key not in valid:
            _error(errors, path + ".primary_point_keys", f"unknown point key for experiment {experiment_id}: {key}")


def _validate_source_audit(
    question: dict[str, Any],
    *,
    context: ValidationContext,
    experiment_id: str,
    path: str,
    errors: list[dict[str, Any]],
) -> None:
    audit = question.get("source_audit")
    if not isinstance(audit, dict):
        _error(errors, path + ".source_audit", "source_audit is required")
        return
    canonical_ids = [str(item) for item in audit.get("canonical_chunk_ids") or [] if str(item).strip()]
    if question.get("review_decision") != "reject" and not canonical_ids:
        _error(errors, path + ".source_audit.canonical_chunk_ids", "canonical_chunk_ids are required")
    valid = context.canonical_chunks.get(experiment_id, set())
    for chunk_id in canonical_ids:
        if chunk_id not in valid:
            _error(errors, path + ".source_audit.canonical_chunk_ids", f"chunk is not linked to experiment {experiment_id}: {chunk_id}")
    if question.get("review_decision") in {"keep", "rewrite"} and audit.get("evidence_sufficient") is not True:
        _error(errors, path + ".source_audit.evidence_sufficient", "accepted/rewrite evidence_sufficient must be true")
    if not str(audit.get("reviewer_note") or "").strip():
        _error(errors, path + ".source_audit.reviewer_note", "reviewer_note is required")


def _validate_option_links(
    question: dict[str, Any],
    *,
    context: ValidationContext,
    experiment_id: str,
    path: str,
    errors: list[dict[str, Any]],
) -> None:
    if question.get("question_type") != "single_choice":
        return
    options = question.get("options") or []
    option_labels = {str(option.get("label") or "").strip() for option in options if isinstance(option, dict)}
    links = question.get("option_links") or []
    if question.get("review_decision") != "reject" and not links:
        _error(errors, path + ".option_links", "single_choice question should include option_links")
        return
    link_labels = set()
    valid_point_keys = context.point_keys.get(experiment_id, set())
    for index, link in enumerate(links):
        link_path = f"{path}.option_links[{index}]"
        label = str(link.get("label") or "").strip() if isinstance(link, dict) else ""
        role = str(link.get("role") or "").strip() if isinstance(link, dict) else ""
        point_key = str(link.get("point_key") or "").strip() if isinstance(link, dict) else ""
        if label not in option_labels:
            _error(errors, link_path + ".label", f"option link label is not in options: {label}")
        if role not in ALLOWED_OPTION_ROLES:
            _error(errors, link_path + ".role", f"invalid option link role: {role}")
        if point_key and point_key not in valid_point_keys:
            _error(errors, link_path + ".point_key", f"unknown option point key for experiment {experiment_id}: {point_key}")
        link_labels.add(label)
    if option_labels and question.get("review_decision") != "reject" and option_labels != link_labels:
        _error(errors, path + ".option_links", f"option link labels must match options: {sorted(option_labels - link_labels)} missing")


def _validate_fill_blank(question: dict[str, Any], path: str, errors: list[dict[str, Any]]) -> None:
    if question.get("question_type") != "fill_blank":
        return
    accepted = question.get("answer", {}).get("accepted_answers") if isinstance(question.get("answer"), dict) else []
    if accepted and not any(_is_phone_friendly_fill_answer(str(answer)) for answer in accepted):
        _error(errors, path + ".answer.accepted_answers", "fill blank must include at least one phone-friendly accepted answer")
    for answer in accepted or []:
        if not _is_phone_friendly_fill_answer(str(answer)):
            _error(
                errors,
                path + ".answer.accepted_answers",
                f"additional phone-unfriendly accepted answer alias: {answer}",
                severity="warning",
            )


def _validate_proposed_question(
    question: dict[str, Any],
    *,
    context: ValidationContext,
    experiment_id: str,
    path: str,
    errors: list[dict[str, Any]],
) -> None:
    decision = question.get("review_decision")
    proposed = question.get("proposed_question")
    if decision == "rewrite" and not isinstance(proposed, dict):
        _error(errors, path + ".proposed_question", "rewrite decision must include proposed_question")
        return
    if not isinstance(proposed, dict):
        return
    proposed_copy = {
        **proposed,
        "review_decision": "keep",
        "source_audit": proposed.get("source_audit") or question.get("source_audit"),
    }
    _validate_question(proposed_copy, context=context, experiment_id=experiment_id, path=path + ".proposed_question", errors=errors, allow_rewrite=False)


def _validate_question(
    question: dict[str, Any],
    *,
    context: ValidationContext,
    experiment_id: str,
    path: str,
    errors: list[dict[str, Any]],
    allow_rewrite: bool = True,
) -> None:
    if not isinstance(question, dict):
        _error(errors, path, "question must be an object")
        return
    decision = str(question.get("review_decision") or "keep")
    if decision not in ALLOWED_REVIEW_DECISIONS:
        _error(errors, path + ".review_decision", f"invalid review_decision: {decision}")
    if not allow_rewrite and decision == "rewrite":
        _error(errors, path + ".review_decision", "nested proposed_question cannot be rewrite")
    question_type = str(question.get("question_type") or "")
    if question_type not in ALLOWED_QUESTION_TYPES:
        _error(errors, path + ".question_type", f"invalid question_type: {question_type}")
    _validate_objective_payload(question, path, errors)
    _validate_point_keys(question, context=context, experiment_id=experiment_id, path=path, errors=errors)
    _validate_source_audit(question, context=context, experiment_id=experiment_id, path=path, errors=errors)
    _validate_option_links(question, context=context, experiment_id=experiment_id, path=path, errors=errors)
    _validate_fill_blank(question, path, errors)
    if allow_rewrite:
        _validate_proposed_question(question, context=context, experiment_id=experiment_id, path=path, errors=errors)


def validate_artifact(path: Path, inventory_path: Path) -> dict[str, Any]:
    artifact = _json_load(path)
    inventory = _json_load(inventory_path)
    context = ValidationContext(inventory)
    errors: list[dict[str, Any]] = []
    counts: Counter[str] = Counter()
    by_experiment: dict[str, Counter[str]] = defaultdict(Counter)
    point_usage: Counter[str] = Counter()

    if not isinstance(artifact, dict):
        _error(errors, "$", "artifact must be an object")
        artifact = {}
    experiments = artifact.get("experiments")
    if not isinstance(experiments, list):
        _error(errors, "$.experiments", "experiments must be a list")
        experiments = []
    for exp_index, experiment in enumerate(experiments):
        exp_path = f"$.experiments[{exp_index}]"
        if not isinstance(experiment, dict):
            _error(errors, exp_path, "experiment must be an object")
            continue
        experiment_id = str(experiment.get("experiment_id") or "")
        if experiment_id not in context.experiments:
            _error(errors, exp_path + ".experiment_id", f"unknown experiment_id: {experiment_id}")
        questions = experiment.get("questions")
        if not isinstance(questions, list):
            _error(errors, exp_path + ".questions", "questions must be a list")
            questions = []
        for q_index, question in enumerate(questions):
            q_path = f"{exp_path}.questions[{q_index}]"
            if isinstance(question, dict):
                counts[str(question.get("review_decision") or "keep")] += 1
                counts[str(question.get("question_type") or "unknown")] += 1
                by_experiment[experiment_id][str(question.get("review_decision") or "keep")] += 1
                for key in question.get("primary_point_keys") or []:
                    point_usage[f"{experiment_id}:{key}"] += 1
            _validate_question(question, context=context, experiment_id=experiment_id, path=q_path, errors=errors)

    missing_experiments = sorted(set(context.experiments) - {str(item.get("experiment_id") or "") for item in experiments if isinstance(item, dict)})
    for experiment_id in missing_experiments:
        _error(errors, "$.experiments", f"inventory experiment missing from artifact: {experiment_id}", severity="warning")

    return {
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "artifact": str(path),
        "inventory": str(inventory_path),
        "valid": not any(error["severity"] == "error" for error in errors),
        "error_count": sum(1 for error in errors if error["severity"] == "error"),
        "warning_count": sum(1 for error in errors if error["severity"] == "warning"),
        "counts": dict(counts),
        "experiment_count": len(experiments),
        "point_usage_count": len(point_usage),
        "by_experiment": {key: dict(value) for key, value in by_experiment.items()},
        "errors": errors[:500],
    }


def _experiment_chapter_ids(experiment: dict[str, Any]) -> set[str]:
    return {
        str(binding.get("chapter_id"))
        for binding in experiment.get("chapter_bindings") or []
        if binding.get("chapter_id")
    }


def _all_formal_points(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    points: list[dict[str, Any]] = []
    for experiment in inventory.get("experiments", []):
        chapter_ids = _experiment_chapter_ids(experiment)
        for point in experiment.get("video_points") or []:
            if point.get("source") != "formal_experiment.video_candidates":
                continue
            points.append(
                {
                    "experiment_id": experiment["experiment_id"],
                    "experiment_code": experiment["code"],
                    "experiment_title": experiment["title"],
                    "chapter_ids": sorted(chapter_ids),
                    "point_key": point["point_key"],
                    "point_title": point["point_title"],
                    "candidate_index": int(point.get("candidate_index") or 0),
                }
            )
    return points


def _distractors_for_point(
    *,
    point: dict[str, Any],
    current_experiment: dict[str, Any],
    all_points: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    distractors: list[dict[str, Any]] = []
    seen_titles = {_normalize_text(point["point_title"])}

    def add(candidate: dict[str, Any], role_scope: str) -> None:
        if len(distractors) >= 3:
            return
        normalized = _normalize_text(candidate["point_title"])
        if not normalized or normalized in seen_titles:
            return
        seen_titles.add(normalized)
        distractors.append({**candidate, "role_scope": role_scope})

    for other in current_experiment.get("video_points") or []:
        if other.get("source") != "formal_experiment.video_candidates":
            continue
        if other.get("point_key") == point["point_key"]:
            continue
        add(
            {
                "experiment_id": point["experiment_id"],
                "experiment_code": point["experiment_code"],
                "experiment_title": point["experiment_title"],
                "point_key": other["point_key"],
                "point_title": other["point_title"],
            },
            "same_experiment",
        )

    chapter_ids = set(point.get("chapter_ids") or [])
    for other in all_points:
        if other["experiment_id"] == point["experiment_id"]:
            continue
        if chapter_ids and chapter_ids.intersection(other.get("chapter_ids") or []):
            add(other, "same_chapter")
    for other in all_points:
        if other["experiment_id"] != point["experiment_id"]:
            add(other, "global")
    return distractors


def _option_rows(point: dict[str, Any], distractors: list[dict[str, Any]]) -> tuple[list[dict[str, str]], list[dict[str, Any]], str]:
    labels = ["A", "B", "C", "D"]
    items = [{"kind": "correct", **point}, *[{"kind": "distractor", **item} for item in distractors[:3]]]
    while len(items) < 4:
        items.append(
            {
                "kind": "distractor",
                "experiment_id": "",
                "experiment_code": "",
                "experiment_title": "",
                "point_key": "",
                "point_title": "以上都不是本实验点位",
                "role_scope": "fallback",
            }
        )
    correct_index = (int(point.get("candidate_index") or 1) + sum(ord(ch) for ch in point["experiment_id"])) % 4
    ordered: list[dict[str, Any]] = [None, None, None, None]  # type: ignore[list-item]
    ordered[correct_index] = items[0]
    rest = iter(items[1:4])
    for index in range(4):
        if ordered[index] is None:
            ordered[index] = next(rest)

    options: list[dict[str, str]] = []
    links: list[dict[str, Any]] = []
    answer = labels[correct_index]
    for label, item in zip(labels, ordered):
        text_value = str(item["point_title"])
        if item.get("kind") == "distractor" and item.get("experiment_code"):
            text_value = f"{text_value}（{item['experiment_code']}）"
        options.append({"label": label, "text": text_value})
        if item.get("kind") == "correct":
            links.append(
                {
                    "label": label,
                    "point_key": item["point_key"],
                    "role": "correct_evidence",
                    "diagnostic_note": "正确识别本实验的目标视频点位。",
                }
            )
        elif item.get("role_scope") == "same_experiment":
            links.append(
                {
                    "label": label,
                    "point_key": item["point_key"],
                    "role": "adjacent_point",
                    "diagnostic_note": "混淆同一实验下的相邻点位。",
                }
            )
        else:
            links.append(
                {
                    "label": label,
                    "point_key": None,
                    "role": "unrelated_distractor" if item.get("role_scope") != "same_chapter" else "adjacent_point",
                    "diagnostic_note": "选择了其他实验或章节的点位，说明实验点位归属不清。",
                }
            )
    return options, links, answer


def build_candidate_scaffold(inventory_path: Path) -> dict[str, Any]:
    inventory = _json_load(inventory_path)
    all_points = _all_formal_points(inventory)
    experiments_by_id = {str(item["experiment_id"]): item for item in inventory.get("experiments", [])}
    artifact_experiments: list[dict[str, Any]] = []
    for experiment in inventory.get("experiments", []):
        experiment_id = str(experiment["experiment_id"])
        questions: list[dict[str, Any]] = []
        formal_points = [
            point
            for point in all_points
            if point["experiment_id"] == experiment_id
        ]
        for point in formal_points:
            distractors = _distractors_for_point(
                point=point,
                current_experiment=experiments_by_id[experiment_id],
                all_points=all_points,
            )
            options, option_links, answer = _option_rows(point, distractors)
            canonical_chunk_ids = list(experiment.get("canonical_chunk_ids") or [])
            question_id = f"SCF_{experiment_id}_{point['candidate_index']:03d}"
            questions.append(
                {
                    "question_id": question_id,
                    "question_type": "single_choice",
                    "stem": f"在《{point['experiment_code']} {point['experiment_title']}》中，下列哪一项最符合该实验的一个正式视频点位？",
                    "options": options,
                    "answer": {"value": answer},
                    "explanation": f"该实验的正式视频点位包含“{point['point_title']}”。本题用于低深度覆盖检查，后续还需要更高诊断价值的现象、推理或方法题。",
                    "difficulty": "basic",
                    "review_decision": "keep",
                    "quality_flags": ["coverage_scaffold", "basic_point_recognition"],
                    "primary_point_keys": [point["point_key"]],
                    "coverage_tags": ["point_recognition"],
                    "option_links": option_links,
                    "source_audit": {
                        "canonical_chunk_ids": canonical_chunk_ids,
                        "supporting_theory_chunk_ids": [],
                        "evidence_sufficient": bool(canonical_chunk_ids),
                        "reviewer_note": (
                            "Codex batch review: accepted only as a low-depth point-recognition scaffold item. "
                            "The point title comes from formal experiment video_candidates and is backed by the linked canonical experiment chunk(s); "
                            "this does not replace later deeper diagnostic questions."
                        ),
                    },
                }
            )
        artifact_experiments.append(
            {
                "experiment_id": experiment_id,
                "experiment_code": experiment.get("code"),
                "experiment_title": experiment.get("title"),
                "video_points": [
                    {
                        "point_key": point["point_key"],
                        "point_title": point["point_title"],
                    }
                    for point in experiment.get("video_points") or []
                    if point.get("source") == "formal_experiment.video_candidates"
                ],
                "questions": questions,
            }
        )

    return {
        "metadata": {
            "artifact_type": "point_aware_question_bank",
            "version": "full-candidate-scaffold-v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "review_mode": "codex_batch_scaffold_review",
            "note": "One low-depth single-choice scaffold item per formal video point. This is a coverage scaffold, not the final depth-complete bank.",
        },
        "experiments": artifact_experiments,
    }


def write_scaffold_review(scaffold: dict[str, Any], path: Path) -> None:
    experiment_count = len(scaffold.get("experiments") or [])
    question_count = sum(len(exp.get("questions") or []) for exp in scaffold.get("experiments") or [])
    lines = [
        "# Full Candidate Scaffold Review",
        "",
        "This artifact creates one low-depth single-choice scaffold item for every formal experiment video point.",
        "",
        f"- Experiments: {experiment_count}",
        f"- Questions: {question_count}",
        "- Review decision: all scaffold items are marked `keep` only as coverage-scaffold items.",
        "- Quality flags: `coverage_scaffold`, `basic_point_recognition`.",
        "",
        "## Important Boundary",
        "",
        "This is not the final depth-complete default bank. It proves the full 77-experiment artifact shape, point-key binding, source-audit plumbing, option-link validation, and coverage reporting. The next pass must add deeper phenomenon, reasoning, method, and misconception questions per point.",
        "",
        "## Batch Review Rule",
        "",
        "Each scaffold question was generated from a formal video point title and linked canonical experiment chunk ids. Codex batch review accepts them only as low-depth point-recognition items; any import flow should keep the quality flags visible.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _chunk_question_items(experiment: dict[str, Any]) -> list[dict[str, Any]]:
    questions = experiment.get("questions")
    if isinstance(questions, list):
        return [item for item in questions if isinstance(item, dict)]
    reviewed_questions = experiment.get("reviewed_questions")
    if isinstance(reviewed_questions, list):
        return [item for item in reviewed_questions if isinstance(item, dict)]
    return []


def _review_item_id(item: dict[str, Any], *, experiment_code: str, question_index: int) -> str:
    return str(
        item.get("review_id")
        or item.get("review_item_id")
        or item.get("question_id")
        or f"REVIEWED_{experiment_code.replace('-', '_')}_{question_index:03d}"
    )


def _original_review_question(item: dict[str, Any]) -> dict[str, Any]:
    original = item.get("original_question")
    if isinstance(original, dict):
        return original
    if item.get("question_type") and item.get("stem"):
        return item
    return {}


def _effective_review_question(item: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    decision = str(item.get("review_decision") or "keep")
    proposed = item.get("proposed_question")
    if decision in {"rewrite", "reject"} and isinstance(proposed, dict):
        return proposed, True
    return _original_review_question(item), False


def _question_sequence(item: dict[str, Any], original: dict[str, Any], fallback: int) -> int:
    for value in (
        item.get("original_question_index"),
        original.get("source_question_sequence_in_experiment"),
        item.get("source_question_sequence_in_experiment"),
    ):
        try:
            if value is not None:
                return int(value)
        except (TypeError, ValueError):
            continue
    return fallback


def _chapter_ids_from_inventory(experiment: dict[str, Any]) -> list[str]:
    return [
        str(binding.get("chapter_id"))
        for binding in experiment.get("chapter_bindings") or []
        if binding.get("chapter_id")
    ]


def _effective_question_id(
    *,
    item: dict[str, Any],
    question: dict[str, Any],
    review_item_id: str,
    decision: str,
    from_proposed: bool,
) -> str:
    question_id = question.get("question_id")
    if question_id:
        return str(question_id)
    suffix = "R" if from_proposed or decision in {"rewrite", "reject"} else "K"
    return f"{review_item_id}_{suffix}"


def _merge_effective_question(
    *,
    item: dict[str, Any],
    question: dict[str, Any],
    original: dict[str, Any],
    inventory_experiment: dict[str, Any],
    source_chunk_file: str,
    question_index: int,
    from_proposed: bool,
) -> dict[str, Any]:
    experiment_id = str(inventory_experiment["experiment_id"])
    experiment_code = str(inventory_experiment["code"])
    decision = str(item.get("review_decision") or "keep")
    review_item_id = _review_item_id(item, experiment_code=experiment_code, question_index=question_index)
    source_audit = question.get("source_audit") or item.get("source_audit") or {}
    primary_point_keys = question.get("primary_point_keys") or item.get("primary_point_keys") or []
    secondary_point_keys = question.get("secondary_point_keys") or item.get("secondary_point_keys") or []
    coverage_tags = question.get("coverage_tags") or item.get("coverage_tags") or []
    option_links = question.get("option_links") or item.get("option_links") or []
    answer = question.get("answer")
    removed_answer_aliases: list[str] = []
    if question.get("question_type") == "fill_blank" and isinstance(answer, dict):
        accepted_answers = [str(value) for value in answer.get("accepted_answers") or []]
        friendly_answers = [value for value in accepted_answers if _is_phone_friendly_fill_answer(value)]
        if friendly_answers:
            removed_answer_aliases = [value for value in accepted_answers if value not in friendly_answers]
            answer = {**answer, "accepted_answers": friendly_answers}
    quality_flags = _unique_strings(
        [
            *(item.get("quality_flags") or []),
            *(question.get("quality_flags") or []),
            f"original_review_{decision}",
        ]
    )
    if from_proposed:
        quality_flags = _unique_strings([*quality_flags, "uses_proposed_question"])
    source_sequence = _question_sequence(item, original, question_index)
    final_question = {
        "question_id": _effective_question_id(
            item=item,
            question=question,
            review_item_id=review_item_id,
            decision=decision,
            from_proposed=from_proposed,
        ),
        "question_type": question.get("question_type"),
        "stem": question.get("stem"),
        "options": question.get("options") or [],
        "answer": answer,
        "explanation": question.get("explanation"),
        "difficulty": question.get("difficulty") or original.get("difficulty") or "basic",
        "related_chapter_ids": question.get("related_chapter_ids") or original.get("related_chapter_ids") or _chapter_ids_from_inventory(inventory_experiment),
        "related_knowledge_point_ids": question.get("related_knowledge_point_ids") or original.get("related_knowledge_point_ids") or [],
        "source_chunk_ids": _unique_strings(
            [
                *(question.get("source_chunk_ids") or []),
                *(source_audit.get("canonical_chunk_ids") or []),
                *(source_audit.get("supporting_theory_chunk_ids") or []),
            ]
        ),
        "source_refs": question.get("source_refs") or [],
        "status": question.get("status") or original.get("status") or "draft",
        "bank_kind": question.get("bank_kind") or original.get("bank_kind") or "default",
        "review_decision": "keep",
        "quality_flags": quality_flags,
        "primary_point_keys": list(primary_point_keys),
        "secondary_point_keys": list(secondary_point_keys),
        "coverage_tags": list(coverage_tags),
        "option_links": list(option_links),
        "source_audit": source_audit,
        "review_lineage": {
            "review_item_id": review_item_id,
            "source_chunk_file": source_chunk_file,
            "original_review_decision": decision,
            "uses_proposed_question": bool(from_proposed),
            "source_question_sequence_in_experiment": source_sequence,
            "source_original_question_type": original.get("question_type"),
            "source_original_stem": original.get("stem"),
            "removed_phone_unfriendly_answer_aliases": removed_answer_aliases,
        },
    }
    return final_question


def merge_reviewed_old_bank(chunks_dir: Path, inventory_path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    inventory = _json_load(inventory_path)
    inventory_by_id = {str(item["experiment_id"]): item for item in inventory.get("experiments", [])}
    inventory_by_code = {str(item["code"]): item for item in inventory.get("experiments", [])}
    merged_by_experiment: dict[str, list[dict[str, Any]]] = defaultdict(list)
    source_files: list[dict[str, Any]] = []
    original_decisions: Counter[str] = Counter()
    effective_types: Counter[str] = Counter()
    source_items = 0
    proposed_replacement_count = 0
    reject_replacement_count = 0
    merge_errors: list[dict[str, Any]] = []

    for chunk_path in sorted(chunks_dir.glob("chunk_*_reviewed_v1.json")):
        chunk = _json_load(chunk_path)
        source_files.append(
            {
                "file": str(chunk_path),
                "sha256": _file_sha256(chunk_path),
                "version": (chunk.get("metadata") or {}).get("version"),
            }
        )
        for experiment in chunk.get("experiments") or []:
            experiment_id = str(experiment.get("experiment_id") or "")
            experiment_code = str(experiment.get("experiment_code") or experiment.get("code") or "")
            inventory_experiment = inventory_by_id.get(experiment_id) or inventory_by_code.get(experiment_code)
            if not inventory_experiment:
                merge_errors.append(
                    {
                        "file": str(chunk_path),
                        "experiment_code": experiment_code,
                        "message": "reviewed experiment is not present in inventory",
                    }
                )
                continue
            for question_index, item in enumerate(_chunk_question_items(experiment), 1):
                source_items += 1
                decision = str(item.get("review_decision") or "keep")
                original_decisions[decision] += 1
                original = _original_review_question(item)
                effective, from_proposed = _effective_review_question(item)
                if not effective:
                    merge_errors.append(
                        {
                            "file": str(chunk_path),
                            "experiment_code": experiment_code,
                            "question_index": question_index,
                            "message": "review item has no effective question",
                        }
                    )
                    continue
                if from_proposed:
                    proposed_replacement_count += 1
                if decision == "reject" and from_proposed:
                    reject_replacement_count += 1
                if decision in {"rewrite", "reject"} and not from_proposed:
                    merge_errors.append(
                        {
                            "file": str(chunk_path),
                            "experiment_code": experiment_code,
                            "question_index": question_index,
                            "message": f"{decision} item is missing proposed_question",
                        }
                    )
                    continue
                final_question = _merge_effective_question(
                    item=item,
                    question=effective,
                    original=original,
                    inventory_experiment=inventory_experiment,
                    source_chunk_file=chunk_path.name,
                    question_index=question_index,
                    from_proposed=from_proposed,
                )
                effective_types[str(final_question.get("question_type") or "unknown")] += 1
                merged_by_experiment[str(inventory_experiment["experiment_id"])].append(final_question)

    artifact_experiments: list[dict[str, Any]] = []
    for inventory_experiment in inventory.get("experiments", []):
        experiment_id = str(inventory_experiment["experiment_id"])
        questions = merged_by_experiment.get(experiment_id, [])
        artifact_experiments.append(
            {
                "experiment_id": experiment_id,
                "experiment_code": inventory_experiment.get("code"),
                "experiment_title": inventory_experiment.get("title"),
                "video_points": [
                    {
                        "point_key": point.get("point_key"),
                        "point_title": point.get("point_title"),
                    }
                    for point in inventory_experiment.get("video_points") or []
                    if point.get("source") == "formal_experiment.video_candidates"
                ],
                "questions": questions,
            }
        )

    merged = {
        "metadata": {
            "artifact_type": "point_aware_question_bank",
            "version": "reviewed-old-bank-merged-v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "source_bank": "experiment_question_bank_v1",
            "review_mode": "merged_from_five_reviewed_old_bank_chunks",
            "source_files": source_files,
            "source_reviewed_item_count": source_items,
            "effective_question_count": sum(len(exp["questions"]) for exp in artifact_experiments),
            "original_review_decision_counts": dict(original_decisions),
            "effective_question_type_counts": dict(effective_types),
            "proposed_replacement_count": proposed_replacement_count,
            "reject_original_replacement_count": reject_replacement_count,
            "notes": [
                "Effective import questions are flattened: keep uses the reviewed old question, rewrite/reject uses proposed_question.",
                "Original reject items are not imported as originals; their source-grounded proposed replacements are retained for coverage.",
                "Detailed old-question audit remains in the five reviewed chunk artifacts.",
            ],
        },
        "experiments": artifact_experiments,
    }
    merge_report = {
        "valid": not merge_errors,
        "error_count": len(merge_errors),
        "errors": merge_errors[:200],
        "source_reviewed_item_count": source_items,
        "effective_question_count": merged["metadata"]["effective_question_count"],
        "original_review_decision_counts": dict(original_decisions),
        "effective_question_type_counts": dict(effective_types),
        "proposed_replacement_count": proposed_replacement_count,
        "reject_original_replacement_count": reject_replacement_count,
        "experiment_count": len(artifact_experiments),
        "non_empty_experiment_count": sum(1 for exp in artifact_experiments if exp.get("questions")),
    }
    return merged, merge_report


def write_merged_review_report(
    *,
    merge_report: dict[str, Any],
    validation_report: dict[str, Any],
    import_report: dict[str, Any],
    output_path: Path,
    report_path: Path,
) -> None:
    counts = merge_report.get("original_review_decision_counts") or {}
    types = merge_report.get("effective_question_type_counts") or {}
    lines = [
        "# Reviewed Old Bank Merged Artifact Report",
        "",
        "## Result",
        "",
        f"- Merged artifact: `{output_path}`",
        f"- Source reviewed items: `{merge_report.get('source_reviewed_item_count')}`",
        f"- Effective questions: `{merge_report.get('effective_question_count')}`",
        f"- Experiments: `{merge_report.get('non_empty_experiment_count')}` / `{merge_report.get('experiment_count')}`",
        f"- Original review decisions: keep `{counts.get('keep', 0)}`, rewrite `{counts.get('rewrite', 0)}`, reject `{counts.get('reject', 0)}`",
        f"- Proposed replacements used: `{merge_report.get('proposed_replacement_count')}`",
        f"- Reject-original replacements used: `{merge_report.get('reject_original_replacement_count')}`",
        f"- Effective question types: single_choice `{types.get('single_choice', 0)}`, true_false `{types.get('true_false', 0)}`, fill_blank `{types.get('fill_blank', 0)}`",
        "",
        "## Validation",
        "",
        f"- Merge errors: `{merge_report.get('error_count')}`",
        f"- Artifact validator valid: `{validation_report.get('valid')}`",
        f"- Artifact validator errors: `{validation_report.get('error_count')}`",
        f"- Artifact validator warnings: `{validation_report.get('warning_count')}`",
        f"- Import dry-run prepared questions: `{import_report.get('prepared_question_count')}`",
        f"- Import dry-run skipped: `{import_report.get('skipped')}`",
        f"- Import dry-run point usage count: `{import_report.get('point_usage_count')}`",
        "",
        "## Import Semantics",
        "",
        "- `keep` old questions are flattened into importable point-aware questions.",
        "- `rewrite` old questions use their `proposed_question` as the importable effective question.",
        "- `reject` old originals are not imported; when a source-grounded `proposed_question` exists, that replacement is imported and the original reject decision is preserved in `review_lineage`.",
        "- The five chunk artifacts remain the detailed audit source for old-question text.",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _unique_strings(values: list[Any]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        text_value = str(value or "").strip()
        if not text_value or text_value in seen:
            continue
        seen.add(text_value)
        result.append(text_value)
    return result


def _json_ready(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_ready(item) for item in value]
    if isinstance(value, tuple):
        return [_json_ready(item) for item in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _inventory_indexes(inventory: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, dict[str, Any]]]]:
    experiments = {str(item["experiment_id"]): item for item in inventory.get("experiments", [])}
    points = {
        experiment_id: {
            str(point["point_key"]): point
            for point in experiment.get("video_points") or []
            if point.get("point_key")
        }
        for experiment_id, experiment in experiments.items()
    }
    return experiments, points


def _question_for_import(candidate: dict[str, Any]) -> tuple[dict[str, Any] | None, dict[str, Any]]:
    decision = str(candidate.get("review_decision") or "keep")
    existing_lineage = candidate.get("review_lineage") if isinstance(candidate.get("review_lineage"), dict) else {}
    lineage = {
        "source_question_id": candidate.get("question_id"),
        "review_decision": decision,
        "original_quality_flags": list(candidate.get("quality_flags") or []),
        **existing_lineage,
    }
    if decision == "reject":
        return None, lineage
    if decision == "rewrite":
        proposed = candidate.get("proposed_question")
        if not isinstance(proposed, dict):
            raise ValueError(f"rewrite candidate missing proposed_question: {candidate.get('question_id')}")
        lineage["rewritten_from_question_id"] = candidate.get("question_id")
        return {**proposed, "review_decision": "keep"}, lineage
    return candidate, lineage


def prepare_import_rows(artifact_path: Path, inventory_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    validation_report = validate_artifact(artifact_path, inventory_path)
    if not validation_report["valid"]:
        raise ValueError(
            "Point-aware question artifact validation failed:\n"
            + json.dumps(validation_report["errors"][:80], ensure_ascii=False, indent=2)
        )
    artifact = _json_load(artifact_path)
    inventory = _json_load(inventory_path)
    experiments_by_id, point_lookup = _inventory_indexes(inventory)

    rows: list[dict[str, Any]] = []
    skipped: Counter[str] = Counter()
    for exp_index, experiment in enumerate(artifact.get("experiments") or []):
        experiment_id = str(experiment.get("experiment_id") or "")
        inventory_experiment = experiments_by_id.get(experiment_id)
        if not inventory_experiment:
            raise ValueError(f"unknown experiment in artifact: {experiment_id}")
        chapter_ids = [
            str(binding.get("chapter_id"))
            for binding in inventory_experiment.get("chapter_bindings") or []
            if binding.get("chapter_id")
        ]
        for q_index, candidate in enumerate(experiment.get("questions") or []):
            question, lineage = _question_for_import(candidate)
            if question is None:
                skipped["reject"] += 1
                continue
            source_audit = question.get("source_audit") or candidate.get("source_audit") or {}
            canonical_chunk_ids = [str(item) for item in source_audit.get("canonical_chunk_ids") or []]
            supporting_chunk_ids = [str(item) for item in source_audit.get("supporting_theory_chunk_ids") or []]
            source_chunk_ids = _unique_strings([*canonical_chunk_ids, *supporting_chunk_ids])
            primary_point_keys = [str(key) for key in question.get("primary_point_keys") or []]
            primary_points = [
                {
                    "point_key": point_key,
                    "point_title": point_lookup.get(experiment_id, {}).get(point_key, {}).get("point_title", point_key),
                }
                for point_key in primary_point_keys
            ]
            payload = {
                "question_type": question.get("question_type"),
                "stem": question.get("stem"),
                "options": question.get("options") or [],
                "answer": question.get("answer"),
                "explanation": question.get("explanation"),
                "difficulty": question.get("difficulty") or "basic",
                "related_chapter_ids": chapter_ids,
                "related_knowledge_point_ids": question.get("related_knowledge_point_ids") or [],
                "source_chunk_ids": source_chunk_ids,
                "source_refs": [],
                "status": "draft",
            }
            normalized, errors = _validate_question_payload(payload)
            if errors or normalized is None:
                raise ValueError(
                    f"normalized import row failed at experiments[{exp_index}].questions[{q_index}]: "
                    + "; ".join(errors)
                )
            rows.append(
                {
                    "experiment_id": experiment_id,
                    "experiment_code": experiment.get("experiment_code"),
                    "experiment_title": experiment.get("experiment_title"),
                    **normalized,
                    "metadata": {
                        "point_aware_question_bank": True,
                        "artifact_version": artifact.get("metadata", {}).get("version"),
                        "artifact_type": artifact.get("metadata", {}).get("artifact_type"),
                        "source_question_id": question.get("question_id") or candidate.get("question_id"),
                        "review_decision": str(candidate.get("review_decision") or "keep"),
                        "review_lineage": lineage,
                        "quality_flags": list(question.get("quality_flags") or candidate.get("quality_flags") or []),
                        "primary_point_keys": primary_point_keys,
                        "primary_points": primary_points,
                        "coverage_tags": list(question.get("coverage_tags") or []),
                        "option_links": list(question.get("option_links") or []),
                        "source_audit": source_audit,
                    },
                }
            )

    report = {
        "valid": True,
        "prepared_question_count": len(rows),
        "skipped": dict(skipped),
        "type_counts": dict(Counter(row["question_type"] for row in rows)),
        "experiment_count": len({row["experiment_id"] for row in rows}),
        "point_usage_count": len(
            {
                f"{row['experiment_id']}:{point_key}"
                for row in rows
                for point_key in row["metadata"].get("primary_point_keys") or []
            }
        ),
        "coverage_scaffold_count": sum(
            1 for row in rows if "coverage_scaffold" in (row["metadata"].get("quality_flags") or [])
        ),
    }
    return rows, validation_report, report


def attach_import_source_refs(session: Any, rows: list[dict[str, Any]]) -> dict[str, Any]:
    all_chunk_ids = sorted({chunk_id for row in rows for chunk_id in row.get("source_chunk_ids") or []})
    refs_by_id = {str(ref["chunk_id"]): ref for ref in resolve_source_refs(session, all_chunk_ids)}
    missing = [chunk_id for chunk_id in all_chunk_ids if chunk_id not in refs_by_id]
    if missing:
        raise ValueError(f"Missing source refs for chunk ids: {missing[:20]}")
    rows_with_refs = 0
    for row in rows:
        source_refs = [refs_by_id[chunk_id] for chunk_id in row.get("source_chunk_ids") or []]
        row["source_refs"] = source_refs
        if source_refs:
            rows_with_refs += 1
    return {"referenced_chunk_count": len(all_chunk_ids), "rows_with_source_refs": rows_with_refs}


def snapshot_existing_questions(session: Any, *, bank_kind: str, experiment_ids: list[str]) -> dict[str, Any]:
    rows = [
        dict(row)
        for row in session.execute(
            text(
                """
                SELECT b.id::text AS bank_id,
                       b.experiment_id,
                       b.bank_kind,
                       b.title AS bank_title,
                       b.status AS bank_status,
                       b.source_label,
                       b.metadata AS bank_metadata,
                       q.id::text AS question_id,
                       q.question_type,
                       q.stem,
                       q.options,
                       q.answer,
                       q.explanation,
                       q.difficulty,
                       q.related_chapter_ids,
                       q.related_knowledge_point_ids,
                       q.source_chunk_ids,
                       q.source_refs,
                       q.status AS question_status,
                       q.metadata AS question_metadata,
                       q.created_at,
                       q.updated_at
                FROM experiment_question_banks b
                LEFT JOIN experiment_questions q ON q.bank_id = b.id
                WHERE b.bank_kind = :bank_kind
                  AND b.experiment_id = ANY(:experiment_ids)
                ORDER BY b.experiment_id, q.created_at, q.id
                """
            ),
            {"bank_kind": bank_kind, "experiment_ids": experiment_ids},
        )
        .mappings()
        .all()
    ]
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "bank_kind": bank_kind,
        "experiment_ids": experiment_ids,
        "row_count": len(rows),
        "rows": _json_ready(rows),
    }


def import_point_aware_rows(
    session: Any,
    rows: list[dict[str, Any]],
    *,
    artifact_path: Path,
    artifact_sha256: str,
    artifact_metadata: dict[str, Any],
    validation_report: dict[str, Any],
    bank_kind: str,
    bank_status: str,
    question_status: str,
) -> dict[str, Any]:
    experiment_ids = sorted({row["experiment_id"] for row in rows})
    import_id = str(
        session.execute(
            text(
                """
                INSERT INTO experiment_question_imports (
                  source_file, status, total_rows, valid_rows, invalid_rows, errors, metadata
                )
                VALUES (:source_file, 'validating', :total_rows, 0, 0, '[]'::jsonb, CAST(:metadata AS jsonb))
                RETURNING id
                """
            ),
            {
                "source_file": str(artifact_path),
                "total_rows": len(rows),
                "metadata": json.dumps(
                    {
                        "source_sha256": artifact_sha256,
                        "artifact_metadata": artifact_metadata,
                        "validation_report": validation_report,
                        "bank_kind": bank_kind,
                        "bank_status": bank_status,
                        "question_status": question_status,
                        "point_aware_question_bank": True,
                    },
                    ensure_ascii=False,
                ),
            },
        ).scalar_one()
    )

    bank_ids: dict[str, str] = {}
    for experiment_id in experiment_ids:
        bank_id = str(
            session.execute(
                text(
                    """
                    INSERT INTO experiment_question_banks (
                      experiment_id, bank_kind, title, status, source_label, metadata, updated_at
                    )
                    VALUES (
                      :experiment_id, :bank_kind, :title, :bank_status,
                      :source_label, CAST(:metadata AS jsonb), now()
                    )
                    ON CONFLICT (experiment_id, bank_kind) DO UPDATE SET
                      title = EXCLUDED.title,
                      status = EXCLUDED.status,
                      source_label = EXCLUDED.source_label,
                      metadata = EXCLUDED.metadata,
                      updated_at = now()
                    RETURNING id
                    """
                ),
                {
                    "experiment_id": experiment_id,
                    "bank_kind": bank_kind,
                    "title": "点位感知题库（候选）" if bank_kind == "generated" else "点位感知默认题库",
                    "bank_status": bank_status,
                    "source_label": artifact_metadata.get("version") or "point-aware-question-bank",
                    "metadata": json.dumps(
                        {
                            "source_sha256": artifact_sha256,
                            "import_id": import_id,
                            "artifact_version": artifact_metadata.get("version"),
                            "point_aware_question_bank": True,
                        },
                        ensure_ascii=False,
                    ),
                },
            ).scalar_one()
        )
        bank_ids[experiment_id] = bank_id

    deleted = session.execute(
        text(
            """
            DELETE FROM experiment_questions q
            USING experiment_question_banks b
            WHERE q.bank_id = b.id
              AND b.bank_kind = :bank_kind
              AND b.experiment_id = ANY(:experiment_ids)
            """
        ),
        {"bank_kind": bank_kind, "experiment_ids": experiment_ids},
    ).rowcount

    for row in rows:
        session.execute(
            text(
                """
                INSERT INTO experiment_questions (
                  bank_id, experiment_id, question_type, stem, options, answer,
                  explanation, difficulty, related_chapter_ids, related_knowledge_point_ids,
                  source_chunk_ids, source_refs, status, metadata, updated_at
                )
                VALUES (
                  CAST(:bank_id AS uuid), :experiment_id, :question_type, :stem,
                  CAST(:options AS jsonb), CAST(:answer AS jsonb), :explanation,
                  :difficulty, :related_chapter_ids, :related_knowledge_point_ids,
                  :source_chunk_ids, CAST(:source_refs AS jsonb), :status,
                  CAST(:metadata AS jsonb), now()
                )
                """
            ),
            {
                "bank_id": bank_ids[row["experiment_id"]],
                "experiment_id": row["experiment_id"],
                "question_type": row["question_type"],
                "stem": row["stem"],
                "options": json.dumps(row["options"], ensure_ascii=False),
                "answer": json.dumps(row["answer"], ensure_ascii=False),
                "explanation": row.get("explanation"),
                "difficulty": row.get("difficulty") or "basic",
                "related_chapter_ids": row.get("related_chapter_ids") or [],
                "related_knowledge_point_ids": row.get("related_knowledge_point_ids") or [],
                "source_chunk_ids": row.get("source_chunk_ids") or [],
                "source_refs": json.dumps(row.get("source_refs") or [], ensure_ascii=False),
                "status": question_status,
                "metadata": json.dumps(row.get("metadata") or {}, ensure_ascii=False),
            },
        )

    session.execute(
        text(
            """
            UPDATE experiment_question_imports
            SET status = 'succeeded',
                valid_rows = :valid_rows,
                invalid_rows = 0,
                errors = '[]'::jsonb,
                updated_at = now()
            WHERE id = CAST(:import_id AS uuid)
            """
        ),
        {"import_id": import_id, "valid_rows": len(rows)},
    )
    return {
        "import_id": import_id,
        "bank_kind": bank_kind,
        "bank_status": bank_status,
        "question_status": question_status,
        "deleted_existing_questions": max(int(deleted or 0), 0),
        "inserted_questions": len(rows),
        "bank_count": len(bank_ids),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Retired point-aware experiment question bank tools.")
    parser.add_argument(
        "--allow-retired-legacy-workflow",
        action="store_true",
        help="Explicitly run the retired experiment_id + point_key question-bank workflow for historical recovery only.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inventory_parser = subparsers.add_parser("inventory", help="Export formal experiment point inventory.")
    inventory_parser.add_argument("--output", type=Path, default=DEFAULT_INVENTORY)
    inventory_parser.add_argument("--audit", type=Path, default=DEFAULT_INVENTORY_AUDIT)
    inventory_parser.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)

    validate_parser = subparsers.add_parser("validate", help="Validate a point-aware question bank artifact.")
    validate_parser.add_argument("--file", type=Path, default=DEFAULT_RELEASE_BANK)
    validate_parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    validate_parser.add_argument("--report", type=Path, default=DEFAULT_VALIDATION_REPORT)

    scaffold_parser = subparsers.add_parser("scaffold", help="Build a full low-depth candidate scaffold.")
    scaffold_parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    scaffold_parser.add_argument("--output", type=Path, default=DEFAULT_SCAFFOLD)
    scaffold_parser.add_argument("--review", type=Path, default=DEFAULT_SCAFFOLD_REPORT)

    merge_parser = subparsers.add_parser("merge-reviewed", help="Merge five reviewed old-bank chunks into one importable artifact.")
    merge_parser.add_argument("--chunks-dir", type=Path, default=DEFAULT_REVIEWED_CHUNKS_DIR)
    merge_parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    merge_parser.add_argument("--output", type=Path, default=DEFAULT_REVIEWED_MERGED)
    merge_parser.add_argument("--report", type=Path, default=DEFAULT_REVIEWED_MERGE_REPORT)
    merge_parser.add_argument("--validation-report", type=Path, default=DEFAULT_REVIEWED_MERGE_VALIDATION_REPORT)
    merge_parser.add_argument("--import-report", type=Path, default=DEFAULT_REVIEWED_MERGE_IMPORT_REPORT)

    import_parser = subparsers.add_parser("import", help="Validate and import a point-aware artifact into question banks.")
    import_parser.add_argument("--file", type=Path, default=DEFAULT_RELEASE_BANK)
    import_parser.add_argument("--inventory", type=Path, default=DEFAULT_INVENTORY)
    import_parser.add_argument("--bank-kind", choices=["generated", "default", "manual"], default="generated")
    import_parser.add_argument("--bank-status", choices=["draft", "published", "archived", "disabled"], default="draft")
    import_parser.add_argument("--question-status", choices=["draft", "published", "disabled", "archived"], default="draft")
    import_parser.add_argument("--report", type=Path, default=DEFAULT_VALIDATION_REPORT)
    import_parser.add_argument("--rollback-snapshot", type=Path)
    import_parser.add_argument("--dry-run", action="store_true")
    import_parser.add_argument("--skip-migrations", action="store_true")

    args = parser.parse_args()
    if not args.allow_retired_legacy_workflow:
        raise SystemExit(
            "This point-aware question-bank seed workflow is retired for the catalog-outline seed. "
            "The current baseline intentionally has an empty experiment question bank; "
            "regenerate catalog-node evidence before creating a new bank. "
            "Pass --allow-retired-legacy-workflow only for historical artifact inspection."
        )
    if args.command == "inventory":
        inventory = build_inventory()
        _json_dump(args.output, inventory)
        write_inventory_audit(inventory, args.audit)
        write_schema(args.schema)
        print(json.dumps({"output": str(args.output), "audit": str(args.audit), "schema": str(args.schema), **inventory["summary"]}, ensure_ascii=False, indent=2))
    elif args.command == "validate":
        report = validate_artifact(args.file, args.inventory)
        _json_dump(args.report, report)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    elif args.command == "scaffold":
        scaffold = build_candidate_scaffold(args.inventory)
        _json_dump(args.output, scaffold)
        write_scaffold_review(scaffold, args.review)
        print(
            json.dumps(
                {
                    "output": str(args.output),
                    "review": str(args.review),
                    "experiment_count": len(scaffold.get("experiments") or []),
                    "question_count": sum(len(exp.get("questions") or []) for exp in scaffold.get("experiments") or []),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    elif args.command == "merge-reviewed":
        merged, merge_report = merge_reviewed_old_bank(args.chunks_dir, args.inventory)
        if not merge_report["valid"]:
            raise ValueError(
                "Reviewed old-bank merge failed:\n"
                + json.dumps(merge_report["errors"][:80], ensure_ascii=False, indent=2)
            )
        _json_dump(args.output, merged)
        rows, validation_report, import_report = prepare_import_rows(args.output, args.inventory)
        _json_dump(args.validation_report, validation_report)
        _json_dump(args.import_report, import_report)
        write_merged_review_report(
            merge_report=merge_report,
            validation_report=validation_report,
            import_report=import_report,
            output_path=args.output,
            report_path=args.report,
        )
        print(
            json.dumps(
                {
                    "output": str(args.output),
                    "report": str(args.report),
                    "validation_report": str(args.validation_report),
                    "import_report": str(args.import_report),
                    "effective_question_count": len(rows),
                    **merge_report,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    elif args.command == "import":
        rows, validation_report, prepare_report = prepare_import_rows(args.file, args.inventory)
        _json_dump(args.report, validation_report)
        artifact = _json_load(args.file)
        source_sha256 = _file_sha256(args.file)
        result: dict[str, Any] = {
            "source_file": str(args.file),
            "source_sha256": source_sha256,
            "dry_run": bool(args.dry_run),
            **prepare_report,
        }
        if args.dry_run:
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return
        if args.bank_kind == "default" and not args.rollback_snapshot:
            raise ValueError("--rollback-snapshot is required before importing into the default bank")
        if not args.skip_migrations:
            apply_migrations()
        with db_session() as session:
            source_ref_report = attach_import_source_refs(session, rows)
            if args.bank_kind == "default" and args.rollback_snapshot:
                snapshot = snapshot_existing_questions(
                    session,
                    bank_kind="default",
                    experiment_ids=sorted({row["experiment_id"] for row in rows}),
                )
                _json_dump(args.rollback_snapshot, snapshot)
                result["rollback_snapshot"] = str(args.rollback_snapshot)
                result["rollback_snapshot_rows"] = snapshot["row_count"]
            import_report = import_point_aware_rows(
                session,
                rows,
                artifact_path=args.file,
                artifact_sha256=source_sha256,
                artifact_metadata=artifact.get("metadata") if isinstance(artifact, dict) else {},
                validation_report=validation_report,
                bank_kind=args.bank_kind,
                bank_status=args.bank_status,
                question_status=args.question_status,
            )
        result.update(source_ref_report)
        result.update(import_report)
        print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
