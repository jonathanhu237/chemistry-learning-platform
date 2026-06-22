from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import text

from server.app.domains.catalog_tree.equations import normalize_reaction_equations, replace_reaction_equations
from server.app.infrastructure.settings import ROOT

CATALOG_SEED_DIR = ROOT / "data" / "seed" / "experiment_catalog"
CATALOG_TREE_SEED_PATH = CATALOG_SEED_DIR / "catalog_tree.json"
CANONICAL_POINT_GROUPS_SEED_PATH = CATALOG_SEED_DIR / "canonical_point_groups.json"
POINT_CONTENT_SEED_PATH = CATALOG_SEED_DIR / "point_content_seed.json"
CATALOG_SEED_VALIDATION_REPORT_PATH = (
    ROOT / "data" / "seed" / "import_reports" / "catalog_outline_seed_validation_report.json"
)

EXPECTED_CATALOG_COUNTS = {
    "total_nodes": 569,
    "directory_nodes": 176,
    "point_nodes": 393,
    "point_placements": 393,
    "canonical_points": 357,
    "duplicate_group_count": 32,
    "duplicate_placement_surplus": 36,
    "chapter_21_nodes": 0,
    "point_content_records": 76,
    "equation_content_records": 71,
    "text_content_records": 5,
    "reaction_equation_rows": 122,
}

CORRECTED_HYPOCHLORITE_PARENT = (
    "第13章 卤族元素",
    "五、卤素含氧酸盐的氧化性",
    "次氯酸盐的氧化性",
)
CORRECTED_HYPOCHLORITE_POINTS = {"NaClO + MnSO₄", "NaClO + 品红溶液"}
CORRECTED_SAMPLE_WORDING = "NaClO + 品红溶液"
LEGACY_IDENTITY_KEYS = {
    "experiment_id",
    "legacy_experiment_id",
    "point_key",
    "legacy_point_key",
}


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=str)


def _json_array(value: Any) -> str:
    return json.dumps(value if value is not None else [], ensure_ascii=False, default=str)


def load_catalog_seed(path: Path = CATALOG_TREE_SEED_PATH) -> list[dict[str, Any]]:
    data = _read_json(path)
    nodes = data.get("nodes")
    if not isinstance(nodes, list):
        raise ValueError(f"{path} must contain a top-level nodes list")
    return [dict(item) for item in nodes if isinstance(item, dict)]


def load_canonical_point_seed(path: Path = CATALOG_TREE_SEED_PATH) -> list[dict[str, Any]]:
    data = _read_json(path)
    canonical_points = data.get("canonical_points")
    if isinstance(canonical_points, list):
        return [dict(item) for item in canonical_points if isinstance(item, dict)]
    nodes = [dict(item) for item in data.get("nodes") or [] if isinstance(item, dict)]
    by_canonical: dict[str, dict[str, Any]] = {}
    for node in nodes:
        if node.get("node_kind") != "point":
            continue
        canonical_point_id = str(node.get("canonical_point_id") or "").strip()
        if not canonical_point_id:
            continue
        by_canonical.setdefault(
            canonical_point_id,
            {
                "canonical_point_id": canonical_point_id,
                "title": node.get("title") or "",
                "summary": "",
                "status": "published",
                "placement_seed_keys": [],
                "metadata": {"derived_from": "legacy_catalog_tree_nodes"},
            },
        )
        by_canonical[canonical_point_id]["placement_seed_keys"].append(node.get("seed_key"))
    return list(by_canonical.values())


def load_point_content_seed(path: Path = POINT_CONTENT_SEED_PATH) -> list[dict[str, Any]]:
    data = _read_json(path)
    records = data.get("records")
    if not isinstance(records, list):
        raise ValueError(f"{path} must contain a top-level records list")
    return [dict(item) for item in records if isinstance(item, dict)]

def validate_catalog_seed(
    nodes: list[dict[str, Any]],
    point_content: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    errors: list[str] = []
    by_key: dict[str, dict[str, Any]] = {}
    child_counts: dict[str, int] = {}
    path_to_nodes: dict[str, list[dict[str, Any]]] = {}
    point_nodes: list[dict[str, Any]] = []

    for index, node in enumerate(nodes, start=1):
        seed_key = str(node.get("seed_key") or "").strip()
        parent_seed_key = str(node.get("parent_seed_key") or "").strip()
        node_kind = str(node.get("node_kind") or "").strip()
        path_titles = node.get("path_titles")
        if not seed_key:
            errors.append(f"nodes[{index}]: seed_key is required")
            continue
        if seed_key in by_key:
            errors.append(f"nodes[{index}]: duplicate seed_key {seed_key}")
        by_key[seed_key] = node
        if node_kind not in {"directory", "point"}:
            errors.append(f"{seed_key}: invalid node_kind {node_kind!r}")
        if node_kind == "point":
            point_nodes.append(node)
            canonical_point_id = str(node.get("canonical_point_id") or "").strip()
            if not canonical_point_id:
                errors.append(f"{seed_key}: point placement requires canonical_point_id")
        elif str(node.get("canonical_point_id") or "").strip():
            errors.append(f"{seed_key}: directory node must not have canonical_point_id")
        if not isinstance(path_titles, list) or not path_titles:
            errors.append(f"{seed_key}: path_titles must be a non-empty list")
        else:
            path_to_nodes.setdefault(" / ".join(str(item) for item in path_titles), []).append(node)
        if parent_seed_key:
            child_counts[parent_seed_key] = child_counts.get(parent_seed_key, 0) + 1

    for seed_key, node in by_key.items():
        parent_seed_key = str(node.get("parent_seed_key") or "").strip()
        if parent_seed_key and parent_seed_key not in by_key:
            errors.append(f"{seed_key}: parent_seed_key does not resolve: {parent_seed_key}")
        if node.get("node_kind") == "point" and child_counts.get(seed_key, 0) > 0:
            errors.append(f"{seed_key}: point node has children")

    directory_nodes = [node for node in nodes if node.get("node_kind") == "directory"]
    canonical_ids = [str(node.get("canonical_point_id") or "").strip() for node in point_nodes]
    canonical_ids = [canonical_point_id for canonical_point_id in canonical_ids if canonical_point_id]
    title_groups: dict[str, list[dict[str, Any]]] = {}
    for node in point_nodes:
        title_groups.setdefault(str(node.get("title") or ""), []).append(node)
    duplicate_groups = {title: rows for title, rows in title_groups.items() if len(rows) > 1}
    duplicate_placement_surplus = sum(len(rows) - 1 for rows in duplicate_groups.values())
    for title, rows in duplicate_groups.items():
        grouped_canonical_ids = {str(row.get("canonical_point_id") or "").strip() for row in rows}
        if len(grouped_canonical_ids) != 1:
            errors.append(f"duplicate placement title {title!r} must resolve to one reviewed canonical_point_id")
    chapter_21_nodes = [node for node in nodes if int(node.get("chapter_number") or 0) == 21]
    placeholder_nodes = [
        node
        for node in nodes
        if "暂无对应实验内容" in str(node.get("title") or "")
        or any("暂无对应实验内容" in str(part) for part in (node.get("path_titles") or []))
    ]

    counts = {
        "total_nodes": len(nodes),
        "directory_nodes": len(directory_nodes),
        "point_nodes": len(point_nodes),
        "point_placements": len(point_nodes),
        "canonical_points": len(set(canonical_ids)),
        "duplicate_group_count": len(duplicate_groups),
        "duplicate_placement_surplus": duplicate_placement_surplus,
        "chapter_21_nodes": len(chapter_21_nodes),
        "placeholder_nodes": len(placeholder_nodes),
    }
    for key in [
        "total_nodes",
        "directory_nodes",
        "point_nodes",
        "point_placements",
        "canonical_points",
        "duplicate_group_count",
        "duplicate_placement_surplus",
        "chapter_21_nodes",
    ]:
        expected = EXPECTED_CATALOG_COUNTS[key]
        if counts[key] != expected:
            errors.append(f"{key}: expected {expected}, got {counts[key]}")
    if placeholder_nodes:
        errors.append("chapter 21 placeholder text must not be seeded")

    hypochlorite_nodes = [
        node
        for node in point_nodes
        if tuple(node.get("path_titles") or [])[: len(CORRECTED_HYPOCHLORITE_PARENT)] == CORRECTED_HYPOCHLORITE_PARENT
    ]
    hypochlorite_titles = {str(node.get("title") or "") for node in hypochlorite_nodes}
    missing_hypochlorite = sorted(CORRECTED_HYPOCHLORITE_POINTS - hypochlorite_titles)
    if missing_hypochlorite:
        errors.append("missing corrected hypochlorite point(s): " + ", ".join(missing_hypochlorite))
    hypochlorite_canonical_ids = {
        str(node.get("canonical_point_id") or "").strip()
        for node in hypochlorite_nodes
        if str(node.get("title") or "") in CORRECTED_HYPOCHLORITE_POINTS
    }
    if len(hypochlorite_canonical_ids) != len(CORRECTED_HYPOCHLORITE_POINTS):
        errors.append("corrected hypochlorite sibling points must target distinct canonical experiments")

    content_counts: dict[str, int] = {
        "point_content_records": 0,
        "equation_content_records": 0,
        "text_content_records": 0,
        "reaction_equation_rows": 0,
        "unique_target_seed_keys": 0,
        "unique_target_canonical_point_ids": 0,
    }
    if point_content is not None:
        target_seed_keys: list[str] = []
        target_canonical_point_ids: list[str] = []
        semantic_mapped_records = 0
        user_kept_source_records = 0
        researched_update_records = 0
        equation_content_records = 0
        text_content_records = 0
        reaction_equation_rows = 0
        for index, record in enumerate(point_content, start=1):
            record_label = str(record.get("record_id") or f"content[{index}]")
            leaked_keys = sorted(key for key in LEGACY_IDENTITY_KEYS if record.get(key))
            if leaked_keys:
                errors.append(f"{record_label}: legacy identity keys are not allowed: {', '.join(leaked_keys)}")
            target_seed_key = str(record.get("target_seed_key") or "").strip()
            if not target_seed_key:
                errors.append(f"{record_label}: target_seed_key is required")
                continue
            target_seed_keys.append(target_seed_key)
            target_canonical_point_id = str(record.get("target_canonical_point_id") or "").strip()
            if not target_canonical_point_id:
                errors.append(f"{record_label}: target_canonical_point_id is required")
            else:
                target_canonical_point_ids.append(target_canonical_point_id)
            target = by_key.get(target_seed_key)
            if not target:
                errors.append(f"{record_label}: target seed key does not resolve: {target_seed_key}")
            elif target.get("node_kind") != "point":
                errors.append(f"{record_label}: target must resolve to a point node: {target_seed_key}")
            elif target_canonical_point_id and target_canonical_point_id != str(target.get("canonical_point_id") or ""):
                errors.append(f"{record_label}: target_canonical_point_id does not match target placement")
            target_path_titles = record.get("target_path_titles") or []
            if target and list(target.get("path_titles") or []) != list(target_path_titles):
                errors.append(f"{record_label}: target path does not match catalog seed")
            semantic_mapping = record.get("semantic_mapping")
            if not isinstance(semantic_mapping, dict):
                errors.append(f"{record_label}: semantic_mapping report is required")
            else:
                if semantic_mapping.get("method") != "normalized_three_element_semantic_node_mapping":
                    errors.append(f"{record_label}: unsupported semantic mapping method")
                if semantic_mapping.get("mapping_status") != "matched":
                    errors.append(f"{record_label}: semantic mapping must be matched")
                target_report = semantic_mapping.get("target")
                if not isinstance(target_report, dict) or target_report.get("seed_key") != target_seed_key:
                    errors.append(f"{record_label}: semantic mapping target must match target_seed_key")
                semantic_mapped_records += 1
            mode = str(record.get("principle_mode") or "").strip()
            if mode not in {"equation", "text"}:
                errors.append(f"{record_label}: principle_mode must be equation or text")
            elif mode == "equation":
                equation_content_records += 1
                equations = record.get("reaction_equations")
                if not isinstance(equations, list) or not equations:
                    errors.append(f"{record_label}: equation mode requires reaction_equations")
                else:
                    for row_index, equation in enumerate(equations, start=1):
                        if not isinstance(equation, dict) or not str(equation.get("raw_text") or "").strip():
                            errors.append(f"{record_label}: reaction_equations[{row_index}] raw_text is required")
                    reaction_equation_rows += len(equations)
                if str(record.get("principle_text") or "").strip():
                    errors.append(f"{record_label}: equation mode must not put equations in principle_text")
            elif mode == "text":
                text_content_records += 1
                if not str(record.get("principle_text") or "").strip():
                    errors.append(f"{record_label}: text mode requires principle_text")
            for field in ["phenomenon_explanation", "safety_note"]:
                if not str(record.get(field) or "").strip():
                    errors.append(f"{record_label}: {field} is required")
            notes = str(record.get("normalization_notes") or "")
            if "user_kept_source" in notes:
                user_kept_source_records += 1
            if "researched_update" in notes:
                researched_update_records += 1
        content_counts = {
            "point_content_records": len(point_content),
            "equation_content_records": equation_content_records,
            "text_content_records": text_content_records,
            "reaction_equation_rows": reaction_equation_rows,
            "unique_target_seed_keys": len(set(target_seed_keys)),
            "unique_target_canonical_point_ids": len(set(target_canonical_point_ids)),
            "semantic_mapped_records": semantic_mapped_records,
            "user_kept_source_records": user_kept_source_records,
            "researched_update_records": researched_update_records,
        }
        for key in ["point_content_records", "equation_content_records", "text_content_records", "reaction_equation_rows"]:
            expected = EXPECTED_CATALOG_COUNTS[key]
            if content_counts[key] != expected:
                errors.append(f"{key}: expected {expected}, got {content_counts[key]}")
        if len(set(target_seed_keys)) != len(target_seed_keys):
            errors.append("point content seed records must target unique catalog point nodes")
        if len(set(target_canonical_point_ids)) != len(target_canonical_point_ids):
            errors.append("point content seed records must target unique canonical point ids")

    return {
        "ok": not errors,
        "errors": errors,
        "counts": {**counts, **content_counts},
        "corrected_hypochlorite_points": sorted(hypochlorite_titles & CORRECTED_HYPOCHLORITE_POINTS),
        "corrected_sample_wording": CORRECTED_SAMPLE_WORDING,
    }


def validate_catalog_seed_files(
    *,
    catalog_path: Path = CATALOG_TREE_SEED_PATH,
    content_path: Path = POINT_CONTENT_SEED_PATH,
) -> dict[str, Any]:
    nodes = load_catalog_seed(catalog_path)
    point_content = load_point_content_seed(content_path)
    result = validate_catalog_seed(nodes, point_content)
    return {
        **result,
        "catalog_seed": str(catalog_path.relative_to(ROOT).as_posix()),
        "point_content_seed": str(content_path.relative_to(ROOT).as_posix()),
    }


def reset_legacy_experiment_seed_data(session: Any) -> dict[str, int]:
    statements: list[tuple[str, str]] = [
        ("question_workbench_candidates", "DELETE FROM experiment_question_workbench_candidates"),
        ("question_workbench_turns", "DELETE FROM experiment_question_workbench_turns"),
        ("question_workbench_sessions", "DELETE FROM experiment_question_workbench_sessions"),
        ("question_drafts", "DELETE FROM experiment_question_drafts"),
        ("questions", "DELETE FROM experiment_questions"),
        ("question_banks", "DELETE FROM experiment_question_banks"),
        ("question_generations", "DELETE FROM experiment_question_generations"),
        ("question_imports", "DELETE FROM experiment_question_imports"),
        ("legacy_point_evidence", "DELETE FROM experiment_video_point_evidence"),
        ("catalog_search_state", "DELETE FROM experiment_catalog_point_search_index_state"),
        ("catalog_point_jobs", "DELETE FROM experiment_catalog_point_jobs"),
        ("catalog_point_evidence_bindings", "DELETE FROM experiment_catalog_point_evidence_bindings"),
        ("catalog_point_evidence_state", "DELETE FROM experiment_catalog_point_evidence_state"),
        ("catalog_media_bindings", "DELETE FROM experiment_catalog_point_media_bindings"),
        ("catalog_related_links", "DELETE FROM experiment_catalog_point_related_links"),
        ("catalog_reaction_equations", "DELETE FROM experiment_catalog_point_reaction_equations"),
        ("catalog_point_content", "DELETE FROM experiment_catalog_point_content"),
        ("catalog_legacy_identity_map", "DELETE FROM experiment_catalog_legacy_identity_map"),
        ("catalog_point_identity_map", "DELETE FROM experiment_catalog_point_identity_map"),
        ("catalog_nodes", "DELETE FROM experiment_catalog_nodes"),
        ("catalog_points", "DELETE FROM experiment_catalog_points"),
        (
            "legacy_video_point_search_state",
            "DELETE FROM experiment_video_point_search_index_state",
        ),
        ("legacy_point_related_links", "DELETE FROM experiment_point_related_links"),
        ("legacy_point_learning_content", "DELETE FROM experiment_point_learning_content"),
        ("legacy_video_points", "DELETE FROM experiment_video_points"),
        (
            "legacy_experiment_media_bindings",
            """
            DELETE FROM media_bindings
            WHERE target_type = 'experiment'
              AND (
                metadata ? 'point_key'
                OR metadata ? 'point_title'
                OR metadata ? 'catalog_node_id'
              )
            """,
        ),
    ]
    report: dict[str, int] = {}
    for key, statement in statements:
        result = session.execute(text(statement))
        report[key] = max(int(result.rowcount or 0), 0)
    return report


def import_catalog_seed(
    session: Any,
    *,
    nodes: list[dict[str, Any]] | None = None,
    canonical_points: list[dict[str, Any]] | None = None,
    point_content: list[dict[str, Any]] | None = None,
    reset: bool = True,
) -> dict[str, Any]:
    nodes = nodes or load_catalog_seed()
    canonical_points = canonical_points or load_canonical_point_seed()
    point_content = point_content or load_point_content_seed()
    validation = validate_catalog_seed(nodes, point_content)
    if not validation["ok"]:
        raise ValueError("Catalog outline seed validation failed:\n" + "\n".join(validation["errors"][:80]))

    reset_report = reset_legacy_experiment_seed_data(session) if reset else {}
    imported_nodes = 0
    imported_canonical_points = 0
    imported_point_content = 0
    imported_equation_rows = 0
    queued_search_documents = 0
    now = datetime.now(timezone.utc).isoformat()

    for point in canonical_points:
        placement_seed_keys = point.get("placement_seed_keys") if isinstance(point.get("placement_seed_keys"), list) else []
        metadata = {
            "catalog_outline_seed": True,
            "source_doc": point.get("source_doc") or "docs/实验目录_整理版.md",
            "placement_seed_keys": placement_seed_keys,
            "grouping_decision": point.get("grouping_decision") or "singleton_point_node",
            "imported_at": now,
            **(point.get("metadata") if isinstance(point.get("metadata"), dict) else {}),
        }
        session.execute(
            text(
                """
                INSERT INTO experiment_catalog_points (
                  id, title, summary, status, metadata, published_at, updated_at
                )
                VALUES (
                  :id, :title, :summary, 'published', CAST(:metadata AS jsonb), now(), now()
                )
                ON CONFLICT (id) DO UPDATE SET
                  title = EXCLUDED.title,
                  summary = EXCLUDED.summary,
                  status = EXCLUDED.status,
                  metadata = EXCLUDED.metadata,
                  published_at = COALESCE(experiment_catalog_points.published_at, EXCLUDED.published_at),
                  archived_at = NULL,
                  updated_at = now()
                """
            ),
            {
                "id": point["canonical_point_id"],
                "title": point["title"],
                "summary": point.get("summary") or "",
                "metadata": _json(metadata),
            },
        )
        imported_canonical_points += 1

    for node in nodes:
        metadata = {
            "catalog_outline_seed": True,
            "seed_key": node["seed_key"],
            "placement_node_id": node["seed_key"],
            "canonical_point_id": node.get("canonical_point_id"),
            "source_doc": node.get("source_doc"),
            "source_line": node.get("source_line"),
            "path_titles": node.get("path_titles") or [],
            "imported_at": now,
        }
        session.execute(
            text(
                """
                INSERT INTO experiment_catalog_nodes (
                  id, chapter_id, parent_id, node_kind, title, summary, status, display_order,
                  canonical_point_id, metadata, published_at, updated_at
                )
                VALUES (
                  :id, :chapter_id, :parent_id, :node_kind, :title, '', 'published', :display_order,
                  :canonical_point_id, CAST(:metadata AS jsonb), now(), now()
                )
                ON CONFLICT (id) DO UPDATE SET
                  chapter_id = EXCLUDED.chapter_id,
                  parent_id = EXCLUDED.parent_id,
                  node_kind = EXCLUDED.node_kind,
                  title = EXCLUDED.title,
                  status = EXCLUDED.status,
                  display_order = EXCLUDED.display_order,
                  canonical_point_id = EXCLUDED.canonical_point_id,
                  metadata = EXCLUDED.metadata,
                  published_at = COALESCE(experiment_catalog_nodes.published_at, EXCLUDED.published_at),
                  updated_at = now()
                """
            ),
            {
                "id": node["seed_key"],
                "chapter_id": node["chapter_id"],
                "parent_id": node.get("parent_seed_key") or None,
                "node_kind": node["node_kind"],
                "title": node["title"],
                "display_order": int(node.get("display_order") or 0),
                "canonical_point_id": node.get("canonical_point_id") if node.get("node_kind") == "point" else None,
                "metadata": _json(metadata),
            },
        )
        imported_nodes += 1

    for content_record in point_content:
        mode = str(content_record.get("principle_mode") or "text").strip()
        reaction_inputs = (
            content_record.get("reaction_equations")
            if isinstance(content_record.get("reaction_equations"), list)
            else []
        )
        normalized_equations = normalize_reaction_equations(reaction_inputs) if mode == "equation" else []
        principle_equation = "\n".join(row["raw_text"] for row in normalized_equations if str(row.get("raw_text") or "").strip())
        principle_text = str(content_record.get("principle_text") or "").strip() if mode == "text" else ""
        metadata = {
            "catalog_point_content_seed": True,
            "record_id": content_record.get("record_id"),
            "normalized_title": content_record.get("normalized_title"),
            "target_seed_key": content_record.get("target_seed_key"),
            "target_canonical_point_id": content_record.get("target_canonical_point_id"),
            "target_path_titles": content_record.get("target_path_titles") or [],
            "sources": content_record.get("sources") or [],
            "normalization_notes": content_record.get("normalization_notes"),
            "semantic_mapping": content_record.get("semantic_mapping") if isinstance(content_record.get("semantic_mapping"), dict) else {},
            "imported_at": now,
        }
        session.execute(
            text(
                """
                INSERT INTO experiment_catalog_point_content (
                  node_id, canonical_point_id, point_title, teacher_note, principle_mode, principle_equation, principle_text,
                  phenomenon_explanation, safety_note, content_status, published_at, metadata, updated_at
                )
                VALUES (
                  :node_id, :canonical_point_id, :point_title, '', :principle_mode, :principle_equation, :principle_text,
                  :phenomenon_explanation, :safety_note, 'published', now(),
                  CAST(:metadata AS jsonb), now()
                )
                ON CONFLICT (node_id) DO UPDATE SET
                  canonical_point_id = EXCLUDED.canonical_point_id,
                  point_title = EXCLUDED.point_title,
                  teacher_note = EXCLUDED.teacher_note,
                  principle_mode = EXCLUDED.principle_mode,
                  principle_equation = EXCLUDED.principle_equation,
                  principle_text = EXCLUDED.principle_text,
                  phenomenon_explanation = EXCLUDED.phenomenon_explanation,
                  safety_note = EXCLUDED.safety_note,
                  content_status = EXCLUDED.content_status,
                  published_at = COALESCE(experiment_catalog_point_content.published_at, EXCLUDED.published_at),
                  metadata = EXCLUDED.metadata,
                  updated_at = now()
                """
            ),
            {
                "node_id": content_record["target_seed_key"],
                "canonical_point_id": content_record["target_canonical_point_id"],
                "point_title": content_record.get("point_title") or (content_record.get("target_path_titles") or [""])[-1],
                "principle_mode": mode,
                "principle_equation": principle_equation or None,
                "principle_text": principle_text or None,
                "phenomenon_explanation": content_record["phenomenon_explanation"],
                "safety_note": content_record["safety_note"],
                "metadata": _json(metadata),
            },
        )
        if mode == "equation":
            replace_reaction_equations(
                session,
                node_id=content_record["target_seed_key"],
                canonical_point_id=content_record["target_canonical_point_id"],
                equations=normalized_equations,
            )
            imported_equation_rows += len(normalized_equations)
        imported_point_content += 1
        session.execute(
            text(
                """
                INSERT INTO experiment_catalog_point_search_index_state (
                  node_id, placement_node_id, canonical_point_id, document_id, desired_action, sync_status, attempts, updated_at
                )
                VALUES (:node_id, :node_id, :canonical_point_id, :node_id, 'upsert', 'pending', 0, now())
                ON CONFLICT (node_id) DO UPDATE SET
                  placement_node_id = EXCLUDED.placement_node_id,
                  canonical_point_id = EXCLUDED.canonical_point_id,
                  document_id = EXCLUDED.document_id,
                  desired_action = 'upsert',
                  sync_status = 'pending',
                  attempts = 0,
                  last_error = NULL,
                  updated_at = now()
                """
            ),
            {"node_id": content_record["target_seed_key"], "canonical_point_id": content_record["target_canonical_point_id"]},
        )
        queued_search_documents += 1

    return {
        "imported_at": now,
        "reset": bool(reset),
        "reset_report": reset_report,
        "canonical_points": imported_canonical_points,
        "catalog_nodes": imported_nodes,
        "directory_nodes": validation["counts"]["directory_nodes"],
        "point_nodes": validation["counts"]["point_nodes"],
        "point_placements": validation["counts"]["point_placements"],
        "canonical_point_count": validation["counts"]["canonical_points"],
        "duplicate_group_count": validation["counts"]["duplicate_group_count"],
        "duplicate_placement_surplus": validation["counts"]["duplicate_placement_surplus"],
        "ambiguous_duplicate_count": 0,
        "point_content_records": imported_point_content,
        "reaction_equation_rows": imported_equation_rows,
        "queued_search_documents": queued_search_documents,
        "validation": validation,
        "preserved_resources": [
            "source_documents",
            "source_chunks",
            "chunk_embeddings",
            "data/seed/canonical_rag/**",
            "data/seed/search/**",
            "app_users",
            "roles/classes/courses",
            "media_assets",
        ],
    }
