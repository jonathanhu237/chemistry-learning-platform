from __future__ import annotations

import hashlib
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy import text

from server.app.domains.catalog_tree.catalog_seed import reset_legacy_experiment_seed_data
from server.app.domains.catalog_tree.equations import normalize_reaction_equations, replace_reaction_equations
from server.app.domains.catalog_tree.teacher_search import queue_teacher_index_state
from server.app.domains.experiment_points.textbook_import import normalize_import_text
from server.app.infrastructure.database import db_session

POINT_MARKER_RE = re.compile(r"[（(](?:点位|重复点位\s*\d+)[）)]")
HEADING_NUMBER_RE = re.compile(r"^\s*(?:\d+|[一二三四五六七八九十百〇零两]+)[.、]\s*")
CHAPTER_RE = re.compile(r"^#\s*第\s*(\d+)\s*章\s*(.+?)\s*$")
HEADING_RE = re.compile(r"^##\s+(.+?)\s*$")
BULLET_RE = re.compile(r"^(\s*)-\s+(.+?)\s*$")
DESCRIPTION_HEADING_RE = re.compile(r"^(#{2,4})\s+(.+)$")
DESCRIPTION_PATH_RE = re.compile(r"\*\*目录路径：\*\*\s*(.+)")
REACTION_ARROW_RE = re.compile(r"(<=>|⇌|--?>|=>|→)")
EQUATION_SPLIT_RE = re.compile(r"\s*(?:[；;]|[,，]\s*或)\s*")
TRAILING_CN_PAREN_RE = re.compile(r"\s*[（(]([^）)]*[\u4e00-\u9fff][^）)]*)[）)]\s*$")


@dataclass
class MarkdownCatalogNode:
    node_id: str
    chapter_id: str
    chapter_title: str
    parent_id: str | None
    node_kind: str
    title: str
    path_titles: list[str]
    display_order: int
    source_line: int
    normalized_title: str
    canonical_point_id: str | None = None
    duplicate_ordinal: int = 1


@dataclass(frozen=True)
class MarkdownDescription:
    chapter_title: str
    experiment_title: str
    title: str
    source_line: int
    source_order: int
    directory_path: list[str]
    principle: str
    phenomenon: str
    safety: str


@dataclass
class PrincipleImport:
    mode: str
    principle_text: str
    reaction_rows: list[dict[str, Any]] = field(default_factory=list)
    extraction_notes: list[str] = field(default_factory=list)

    @property
    def principle_equation(self) -> str:
        return "\n".join(str(row.get("raw_text") or "").strip() for row in self.reaction_rows if str(row.get("raw_text") or "").strip())


def _sha1(value: str, length: int = 20) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:length]


def _json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, default=str)


def _json_array(value: Any) -> str:
    return json.dumps(value if value is not None else [], ensure_ascii=False, default=str)


def clean_display_title(value: str) -> str:
    cleaned = str(value or "").strip()
    cleaned = POINT_MARKER_RE.sub("", cleaned)
    cleaned = HEADING_NUMBER_RE.sub("", cleaned)
    return cleaned.strip()


def _chapter_id(chapter_number: int) -> str:
    return f"CH{chapter_number:02d}"


def _node_id(chapter_id: str, path_titles: list[str], display_order: int) -> str:
    return f"cat-md-{chapter_id.lower()}-{_sha1(chr(0).join([*path_titles, str(display_order)]), 18)}"


def _canonical_point_id(group_key: str) -> str:
    return f"cat-md-canon-{_sha1(group_key, 24)}"


def _path_key(parts: list[str] | tuple[str, ...]) -> str:
    return "\0".join(normalize_import_text(part) for part in parts)


def _text_after_label(block: str, label: str, next_labels: tuple[str, ...]) -> str:
    start = block.find(label)
    if start < 0:
        return ""
    start += len(label)
    end_candidates = [block.find(next_label, start) for next_label in next_labels]
    end_candidates = [position for position in end_candidates if position >= 0]
    end = min(end_candidates) if end_candidates else len(block)
    return block[start:end].strip()


def _description_directory_path(block: str) -> list[str]:
    match = DESCRIPTION_PATH_RE.search(block)
    if not match:
        return []
    return [clean_display_title(part) for part in match.group(1).split("/") if clean_display_title(part)]


def parse_catalog_markdown(path: str | Path) -> list[MarkdownCatalogNode]:
    lines = Path(path).read_text(encoding="utf-8-sig").splitlines()
    nodes: list[MarkdownCatalogNode] = []
    stack: list[MarkdownCatalogNode] = []
    current_chapter_title = ""
    current_chapter_id = ""
    current_heading: MarkdownCatalogNode | None = None
    order_by_parent: dict[str, int] = defaultdict(int)
    bullet_rows: list[dict[str, Any]] = []

    def next_order(parent_key: str) -> int:
        order_by_parent[parent_key] += 1
        return order_by_parent[parent_key]

    def add_node(title: str, line_number: int, *, parent: MarkdownCatalogNode | None, node_kind: str) -> MarkdownCatalogNode:
        target_chapter_id = parent.chapter_id if parent else current_chapter_id
        target_chapter_title = parent.chapter_title if parent else current_chapter_title
        if not target_chapter_id or not target_chapter_title:
            raise ValueError(f"line {line_number}: catalog node outside chapter")
        path_titles = [target_chapter_title]
        if parent:
            path_titles.extend(parent.path_titles[1:])
        path_titles.append(title)
        parent_key = parent.node_id if parent else f"chapter:{target_chapter_id}"
        display_order = next_order(parent_key)
        node = MarkdownCatalogNode(
            node_id=_node_id(target_chapter_id, path_titles, display_order),
            chapter_id=target_chapter_id,
            chapter_title=target_chapter_title,
            parent_id=parent.node_id if parent else None,
            node_kind=node_kind,
            title=title,
            path_titles=path_titles,
            display_order=display_order,
            source_line=line_number,
            normalized_title=normalize_import_text(title),
        )
        nodes.append(node)
        return node

    for line_number, line in enumerate(lines, start=1):
        chapter_match = CHAPTER_RE.match(line)
        if chapter_match:
            chapter_number = int(chapter_match.group(1))
            current_chapter_title = f"第{chapter_number}章 {chapter_match.group(2).strip()}"
            current_chapter_id = _chapter_id(chapter_number)
            current_heading = None
            stack = []
            continue

        heading_match = HEADING_RE.match(line)
        if heading_match and current_chapter_id:
            heading_title = clean_display_title(heading_match.group(1))
            if "暂无对应实验内容" in heading_title:
                current_heading = None
                stack = []
                continue
            current_heading = add_node(heading_title, line_number, parent=None, node_kind="directory")
            stack = []
            continue

        bullet_match = BULLET_RE.match(line)
        if not bullet_match or not current_chapter_id or not current_heading:
            continue
        bullet_rows.append(
            {
                "line": line_number,
                "indent": len(bullet_match.group(1).replace("\t", "  ")),
                "title": clean_display_title(bullet_match.group(2)),
                "heading": current_heading,
            }
        )

    for index, bullet in enumerate(bullet_rows):
        while stack and int(stack[-1].display_order) < 0:
            stack.pop()
        depth = int(bullet["indent"]) // 2
        while len(stack) > depth:
            stack.pop()
        next_bullet = bullet_rows[index + 1] if index + 1 < len(bullet_rows) else None
        is_leaf = not (next_bullet and int(next_bullet["indent"]) > int(bullet["indent"]))
        parent = bullet["heading"] if depth == 0 else stack[depth - 1]
        node = add_node(
            str(bullet["title"]),
            int(bullet["line"]),
            parent=parent,
            node_kind="point" if is_leaf else "directory",
        )
        if is_leaf:
            continue
        while len(stack) <= depth:
            placeholder = MarkdownCatalogNode(
                node_id="",
                chapter_id="",
                chapter_title="",
                parent_id=None,
                node_kind="directory",
                title="",
                path_titles=[],
                display_order=-1,
                source_line=0,
                normalized_title="",
            )
            stack.append(placeholder)
        stack[depth] = node
        stack = stack[: depth + 1]

    _assign_canonical_points(nodes)
    return nodes


def _assign_canonical_points(nodes: list[MarkdownCatalogNode]) -> None:
    points = [node for node in nodes if node.node_kind == "point"]
    sibling_counts = Counter((node.parent_id or "", node.normalized_title) for node in points)
    title_has_sibling_duplicate: dict[str, bool] = defaultdict(bool)
    for (_parent_id, normalized_title), count in sibling_counts.items():
        if count > 1:
            title_has_sibling_duplicate[normalized_title] = True

    seen_in_parent: dict[tuple[str, str], int] = defaultdict(int)
    groups: dict[str, list[MarkdownCatalogNode]] = defaultdict(list)
    for node in points:
        parent_key = node.parent_id or ""
        duplicate_key = (parent_key, node.normalized_title)
        seen_in_parent[duplicate_key] += 1
        node.duplicate_ordinal = seen_in_parent[duplicate_key]
        group_key = node.normalized_title
        if title_has_sibling_duplicate[node.normalized_title]:
            group_key = f"{node.normalized_title}\0sibling-ordinal:{node.duplicate_ordinal}"
        groups[group_key].append(node)

    for group_key, rows in groups.items():
        canonical_point_id = _canonical_point_id(group_key)
        for row in rows:
            row.canonical_point_id = canonical_point_id


def parse_description_markdown(path: str | Path) -> list[MarkdownDescription]:
    lines = Path(path).read_text(encoding="utf-8-sig").splitlines()
    headings: list[tuple[int, int, str]] = []
    for line_number, line in enumerate(lines, start=1):
        match = DESCRIPTION_HEADING_RE.match(line)
        if match:
            headings.append((line_number, len(match.group(1)), match.group(2).strip()))

    descriptions: list[MarkdownDescription] = []
    current_chapter = ""
    current_experiment = ""
    for index, (line_number, level, title) in enumerate(headings):
        next_line = headings[index + 1][0] if index + 1 < len(headings) else len(lines) + 1
        if level == 2:
            current_chapter = title
            current_experiment = ""
            continue
        if level == 3:
            current_experiment = clean_display_title(title)
            continue
        if level != 4 or not current_chapter or not current_experiment:
            continue
        block = "\n".join(lines[line_number: next_line - 1])
        descriptions.append(
            MarkdownDescription(
                chapter_title=current_chapter,
                experiment_title=current_experiment,
                title=clean_display_title(title),
                source_line=line_number,
                source_order=len(descriptions) + 1,
                directory_path=_description_directory_path(block),
                principle=_text_after_label(block, "实验原理：", ("现象解释：", "安全提示：")),
                phenomenon=_text_after_label(block, "现象解释：", ("安全提示：",)),
                safety=_text_after_label(block, "安全提示：", ()),
            )
        )
    return descriptions


def _strip_sentence_punctuation(value: str) -> str:
    return str(value or "").strip().strip("。；;，,")


def _split_prefix_annotation(value: str) -> tuple[str, str]:
    arrow_match = REACTION_ARROW_RE.search(value)
    if not arrow_match:
        return value.strip(), ""
    prefix = value[: arrow_match.start()]
    colon_positions = [prefix.rfind("："), prefix.rfind(":")]
    colon_position = max(colon_positions)
    if colon_position < 0:
        return value.strip(), ""
    annotation = value[:colon_position].strip()
    core = value[colon_position + 1 :].strip()
    return core, annotation


def _move_trailing_annotation(core: str) -> tuple[str, str]:
    match = TRAILING_CN_PAREN_RE.search(core)
    if not match:
        return core.strip(), ""
    before = core[: match.start()].strip()
    if not before or not REACTION_ARROW_RE.search(before):
        return core.strip(), ""
    return before, match.group(1).strip()


def _append_annotation(raw_text: str, annotation: str) -> str:
    text = _strip_sentence_punctuation(raw_text)
    note = _strip_sentence_punctuation(annotation)
    if not note:
        return text
    if "//" in text:
        return f"{text}；{note}"
    return f"{text} // {note}"


def _extract_reaction_rows(principle: str) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    notes: list[str] = []
    pending_non_equation: list[str] = []
    for raw_line in str(principle or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if not REACTION_ARROW_RE.search(line):
            if rows:
                pending_non_equation.append(line)
            continue
        for clause in [part.strip() for part in EQUATION_SPLIT_RE.split(line) if part.strip()]:
            if not REACTION_ARROW_RE.search(clause):
                if rows:
                    previous = rows[-1]["raw_text"]
                    rows[-1]["raw_text"] = _append_annotation(previous, clause)
                continue
            core, prefix_annotation = _split_prefix_annotation(clause)
            core, trailing_annotation = _move_trailing_annotation(core)
            annotations = [value for value in [prefix_annotation, trailing_annotation] if value]
            rows.append(
                {
                    "raw_text": _append_annotation(core, "；".join(annotations)),
                    "row_order": len(rows) + 1,
                    "metadata": {"source": "markdown_principle_equation_extraction"},
                }
            )
    if pending_non_equation and rows:
        rows[-1]["raw_text"] = _append_annotation(rows[-1]["raw_text"], "；".join(pending_non_equation))
        notes.append("non_equation_lines_attached_to_last_reaction_annotation")
    return rows, notes


def principle_import_from_text(principle: str) -> PrincipleImport:
    rows, notes = _extract_reaction_rows(principle)
    if not rows:
        return PrincipleImport(mode="text", principle_text=str(principle or "").strip(), extraction_notes=notes)
    normalized = normalize_reaction_equations(rows)
    valid_rows = [row for row in normalized if row.get("validation_status") != "invalid"]
    if not valid_rows:
        return PrincipleImport(
            mode="text",
            principle_text=str(principle or "").strip(),
            extraction_notes=[*notes, "all_extracted_reactions_invalid_fallback_to_text"],
        )
    normalized_by_order = {int(row.get("row_order") or index): row for index, row in enumerate(normalized, start=1)}
    imported_rows = []
    for index, row in enumerate(rows, start=1):
        normalized_row = normalized_by_order.get(index)
        if normalized_row and normalized_row.get("validation_status") != "invalid":
            imported_rows.append(row)
    if len(imported_rows) != len(rows):
        notes.append("invalid_reaction_rows_dropped")
    return PrincipleImport(mode="equation", principle_text="", reaction_rows=imported_rows, extraction_notes=notes)


def build_markdown_import_plan(
    *,
    catalog_path: str | Path,
    description_path: str | Path,
) -> dict[str, Any]:
    nodes = parse_catalog_markdown(catalog_path)
    descriptions = parse_description_markdown(description_path)
    point_nodes = [node for node in nodes if node.node_kind == "point"]
    points_by_path: dict[str, list[MarkdownCatalogNode]] = defaultdict(list)
    points_by_description_key: dict[tuple[str, str, str], list[MarkdownCatalogNode]] = defaultdict(list)
    for node in point_nodes:
        points_by_path[_path_key(node.path_titles)].append(node)
        if len(node.path_titles) >= 3:
            points_by_description_key[
                (
                    normalize_import_text(node.path_titles[0]),
                    normalize_import_text(node.path_titles[1]),
                    normalize_import_text(node.title),
                )
            ].append(node)
    matched: list[tuple[MarkdownCatalogNode, MarkdownDescription, PrincipleImport]] = []
    unresolved: list[dict[str, Any]] = []
    used_node_ids: set[str] = set()

    def take_unused(candidates: list[MarkdownCatalogNode]) -> MarkdownCatalogNode | None:
        for candidate in candidates:
            if candidate.node_id not in used_node_ids:
                used_node_ids.add(candidate.node_id)
                return candidate
        return None

    for description in descriptions:
        key = _path_key(description.directory_path)
        node = take_unused(points_by_path.get(key) or [])
        if not node:
            node = take_unused(
                points_by_description_key.get(
                    (
                        normalize_import_text(description.chapter_title),
                        normalize_import_text(description.experiment_title),
                        normalize_import_text(description.title),
                    ),
                    [],
                )
            )
        if not node:
            unresolved.append(
                {
                    "source_line": description.source_line,
                    "title": description.title,
                    "directory_path": " / ".join(description.directory_path),
                }
            )
            continue
        matched.append((node, description, principle_import_from_text(description.principle)))

    content_node_ids = {node.node_id for node, _description, _principle in matched}
    duplicate_parent_canonical = [
        {
            "parent_id": parent_id,
            "canonical_point_id": canonical_point_id,
            "count": count,
        }
        for (parent_id, canonical_point_id), count in Counter(
            (node.parent_id or "", node.canonical_point_id or "") for node in point_nodes
        ).items()
        if count > 1
    ]
    equation_records = [item for item in matched if item[2].mode == "equation"]
    text_records = [item for item in matched if item[2].mode == "text"]
    canonical_reaction_row_counts: dict[str, int] = {}
    for node, _description, principle in equation_records:
        if node.canonical_point_id:
            canonical_reaction_row_counts[node.canonical_point_id] = len(principle.reaction_rows)
    return {
        "ok": not unresolved and not duplicate_parent_canonical,
        "catalog_path": str(catalog_path),
        "description_path": str(description_path),
        "nodes": nodes,
        "descriptions": descriptions,
        "matched_content": matched,
        "errors": [
            *([f"unresolved descriptions: {len(unresolved)}"] if unresolved else []),
            *([f"duplicate parent/canonical placements: {len(duplicate_parent_canonical)}"] if duplicate_parent_canonical else []),
        ],
        "unresolved_descriptions": unresolved,
        "duplicate_parent_canonical": duplicate_parent_canonical,
        "counts": {
            "total_nodes": len(nodes),
            "directory_nodes": len([node for node in nodes if node.node_kind == "directory"]),
            "point_nodes": len(point_nodes),
            "canonical_points": len({node.canonical_point_id for node in point_nodes if node.canonical_point_id}),
            "description_points": len(descriptions),
            "matched_content_records": len(matched),
            "missing_content_records": len(point_nodes) - len(content_node_ids),
            "equation_content_records": len(equation_records),
            "text_content_records": len(text_records),
            "reaction_equation_rows": sum(len(principle.reaction_rows) for _node, _description, principle in equation_records),
            "canonical_reaction_equation_rows": sum(canonical_reaction_row_counts.values()),
        },
    }


def _serializable_plan_summary(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        "ok": bool(plan["ok"]),
        "catalog_path": plan["catalog_path"],
        "description_path": plan["description_path"],
        "counts": plan["counts"],
        "errors": plan["errors"],
        "unresolved_descriptions": plan["unresolved_descriptions"][:20],
        "duplicate_parent_canonical": plan["duplicate_parent_canonical"][:20],
    }


def _canonical_points_from_nodes(nodes: list[MarkdownCatalogNode]) -> list[dict[str, Any]]:
    groups: dict[str, list[MarkdownCatalogNode]] = defaultdict(list)
    for node in nodes:
        if node.node_kind == "point" and node.canonical_point_id:
            groups[node.canonical_point_id].append(node)
    canonical_points: list[dict[str, Any]] = []
    for canonical_point_id, rows in sorted(groups.items(), key=lambda item: item[0]):
        first = rows[0]
        canonical_points.append(
            {
                "id": canonical_point_id,
                "title": first.title,
                "summary": "",
                "placement_node_ids": [row.node_id for row in rows],
                "duplicate_ordinal": first.duplicate_ordinal,
                "metadata": {
                    "source": "textbook_markdown_catalog_import",
                    "grouping_policy": "normalized_title_with_sibling_duplicate_ordinals",
                    "placement_paths": [" / ".join(row.path_titles) for row in rows],
                },
            }
        )
    return canonical_points


def import_textbook_catalog_workspace(
    *,
    catalog_path: str | Path,
    description_path: str | Path,
    dry_run: bool = True,
    reset: bool = False,
    publish: bool = True,
    user_id: str | None = None,
) -> dict[str, Any]:
    plan = build_markdown_import_plan(catalog_path=catalog_path, description_path=description_path)
    summary = _serializable_plan_summary(plan)
    if not plan["ok"]:
        return {"dry_run": dry_run, "applied": False, **summary}
    if dry_run:
        return {"dry_run": True, "applied": False, **summary}

    nodes: list[MarkdownCatalogNode] = plan["nodes"]
    matched_content: list[tuple[MarkdownCatalogNode, MarkdownDescription, PrincipleImport]] = plan["matched_content"]
    canonical_points = _canonical_points_from_nodes(nodes)
    status_value = "published" if publish else "draft"
    published_at_sql = "now()" if publish else "NULL"
    now = datetime.now(timezone.utc).isoformat()

    with db_session() as session:
        reset_report = reset_legacy_experiment_seed_data(session) if reset else {}

        for canonical_point in canonical_points:
            metadata = {**canonical_point["metadata"], "imported_at": now}
            session.execute(
                text(
                    f"""
                    INSERT INTO experiment_catalog_points (
                      id, title, summary, status, metadata, published_at, created_by, updated_by, updated_at
                    )
                    VALUES (
                      :id, :title, :summary, :status, CAST(:metadata AS jsonb), {published_at_sql},
                      CAST(:user_id AS uuid), CAST(:user_id AS uuid), now()
                    )
                    ON CONFLICT (id) DO UPDATE SET
                      title = EXCLUDED.title,
                      summary = EXCLUDED.summary,
                      status = EXCLUDED.status,
                      metadata = EXCLUDED.metadata,
                      published_at = EXCLUDED.published_at,
                      archived_at = NULL,
                      updated_by = EXCLUDED.updated_by,
                      updated_at = now()
                    """
                ),
                {
                    "id": canonical_point["id"],
                    "title": canonical_point["title"],
                    "summary": canonical_point["summary"],
                    "status": status_value,
                    "metadata": _json(metadata),
                    "user_id": user_id,
                },
            )

        for node in nodes:
            metadata = {
                "source": "textbook_markdown_catalog_import",
                "source_file": str(catalog_path),
                "source_line": node.source_line,
                "path_titles": node.path_titles,
                "duplicate_ordinal": node.duplicate_ordinal,
                "imported_at": now,
            }
            session.execute(
                text(
                    f"""
                    INSERT INTO experiment_catalog_nodes (
                      id, chapter_id, parent_id, node_kind, title, summary, status, display_order,
                      canonical_point_id, metadata, published_at, created_by, updated_by, updated_at
                    )
                    VALUES (
                      :id, :chapter_id, :parent_id, :node_kind, :title, '', :status, :display_order,
                      :canonical_point_id, CAST(:metadata AS jsonb), {published_at_sql},
                      CAST(:user_id AS uuid), CAST(:user_id AS uuid), now()
                    )
                    ON CONFLICT (id) DO UPDATE SET
                      chapter_id = EXCLUDED.chapter_id,
                      parent_id = EXCLUDED.parent_id,
                      node_kind = EXCLUDED.node_kind,
                      title = EXCLUDED.title,
                      summary = EXCLUDED.summary,
                      status = EXCLUDED.status,
                      display_order = EXCLUDED.display_order,
                      canonical_point_id = EXCLUDED.canonical_point_id,
                      metadata = EXCLUDED.metadata,
                      published_at = EXCLUDED.published_at,
                      updated_by = EXCLUDED.updated_by,
                      updated_at = now()
                    """
                ),
                {
                    "id": node.node_id,
                    "chapter_id": node.chapter_id,
                    "parent_id": node.parent_id,
                    "node_kind": node.node_kind,
                    "title": node.title,
                    "status": status_value,
                    "display_order": node.display_order,
                    "canonical_point_id": node.canonical_point_id if node.node_kind == "point" else None,
                    "metadata": _json(metadata),
                    "user_id": user_id,
                },
            )

        for node, description, principle in matched_content:
            metadata = {
                "source": "textbook_markdown_point_description_import",
                "source_file": str(description_path),
                "source_line": description.source_line,
                "source_order": description.source_order,
                "catalog_path": node.path_titles,
                "description_directory_path": description.directory_path,
                "principle_import_mode": principle.mode,
                "principle_extraction_notes": principle.extraction_notes,
                "imported_at": now,
            }
            session.execute(
                text(
                    f"""
                    INSERT INTO experiment_catalog_point_content (
                      node_id, canonical_point_id, point_title, teacher_note, principle_mode, principle_equation, principle_text,
                      phenomenon_explanation, safety_note, content_status, published_at, published_by,
                      created_by, updated_by, metadata, updated_at
                    )
                    VALUES (
                      :node_id, :canonical_point_id, :point_title, '', :principle_mode, :principle_equation, :principle_text,
                      :phenomenon_explanation, :safety_note, :content_status, {published_at_sql}, CAST(:user_id AS uuid),
                      CAST(:user_id AS uuid), CAST(:user_id AS uuid), CAST(:metadata AS jsonb), now()
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
                      published_at = EXCLUDED.published_at,
                      published_by = EXCLUDED.published_by,
                      updated_by = EXCLUDED.updated_by,
                      metadata = EXCLUDED.metadata,
                      updated_at = now()
                    """
                ),
                {
                    "node_id": node.node_id,
                    "canonical_point_id": node.canonical_point_id,
                    "point_title": node.title,
                    "principle_mode": principle.mode,
                    "principle_equation": principle.principle_equation or None,
                    "principle_text": principle.principle_text or None,
                    "phenomenon_explanation": description.phenomenon,
                    "safety_note": description.safety,
                    "content_status": status_value,
                    "metadata": _json(metadata),
                    "user_id": user_id,
                },
            )
            if principle.mode == "equation":
                normalized_rows = normalize_reaction_equations(principle.reaction_rows)
                replace_reaction_equations(
                    session,
                    node_id=node.node_id,
                    canonical_point_id=node.canonical_point_id,
                    equations=normalized_rows,
                )

        for node in nodes:
            if node.node_kind == "point":
                queue_teacher_index_state(session, node_id=node.node_id, action="upsert", trigger_source="system", soft=True)

    return {
        "dry_run": False,
        "applied": True,
        "reset": reset,
        "publish": publish,
        "reset_report": reset_report,
        **summary,
    }
