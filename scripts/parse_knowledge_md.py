from __future__ import annotations

import re
from pathlib import Path
from typing import Any

try:
    from common import (
        CHAPTER_RE,
        GENERAL_CHAPTER_HEADING,
        GENERAL_CHAPTER_SOURCE_NUMBER,
        GENERAL_CHAPTER_TITLE,
        PROCESSED_DIR,
        chapter_id,
        dump_json,
        ensure_dirs,
        extract_tags,
        find_source_file,
        infer_chapter_number,
        infer_chapter_source_number,
        infer_element_area,
        now_iso,
        read_text,
        save_source_documents,
    )
except ModuleNotFoundError:
    from scripts.common import (
        CHAPTER_RE,
        GENERAL_CHAPTER_HEADING,
        GENERAL_CHAPTER_SOURCE_NUMBER,
        GENERAL_CHAPTER_TITLE,
        PROCESSED_DIR,
        chapter_id,
        dump_json,
        ensure_dirs,
        extract_tags,
        find_source_file,
        infer_chapter_number,
        infer_chapter_source_number,
        infer_element_area,
        now_iso,
        read_text,
        save_source_documents,
    )


def _chapter_title_from_line(line: str) -> str | None:
    candidate = re.sub(r"^#+\s*", "", line.strip()).strip()
    if candidate == GENERAL_CHAPTER_HEADING or CHAPTER_RE.match(candidate):
        return candidate
    return None


def parse_knowledge_markdown(path: Path) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    text = read_text(path)
    chapters: list[dict[str, Any]] = []
    units: list[dict[str, Any]] = []
    points: list[dict[str, Any]] = []

    current_chapter: dict[str, Any] | None = None
    current_unit: dict[str, Any] | None = None
    unit_counter_by_chapter: dict[str, int] = {}
    point_counter_by_unit: dict[str, int] = {}

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line == "---":
            continue

        chapter_title = _chapter_title_from_line(line)
        if chapter_title:
            title = chapter_title
            is_general_heading = title == GENERAL_CHAPTER_HEADING
            source_number = GENERAL_CHAPTER_SOURCE_NUMBER if is_general_heading else infer_chapter_source_number(title)
            number = 0 if is_general_heading else infer_chapter_number(title)
            if number is None:
                continue
            cid = chapter_id(number)
            normalized_title = GENERAL_CHAPTER_TITLE if source_number == GENERAL_CHAPTER_SOURCE_NUMBER else title
            current_chapter = {
                "chapter_id": cid,
                "chapter_number": number,
                "chapter_title": normalized_title,
                "element_area": GENERAL_CHAPTER_TITLE if source_number == GENERAL_CHAPTER_SOURCE_NUMBER else infer_element_area(title),
                "source_file": str(path.name),
                "source_label": title,
                "review_required": False,
                "created_at": now_iso(),
            }
            chapters.append(current_chapter)
            current_unit = None
            unit_counter_by_chapter[cid] = 0
            continue

        if line.startswith("### ") and current_chapter:
            title = line[4:].strip()
            cid = current_chapter["chapter_id"]
            unit_counter_by_chapter[cid] += 1
            unit_index = unit_counter_by_chapter[cid]
            unit_id = f"KU_{int(cid[2:]):02d}_{unit_index:03d}"
            current_unit = {
                "unit_id": unit_id,
                "chapter_id": cid,
                "chapter_title": current_chapter["chapter_title"],
                "unit_index": unit_index,
                "unit_title": title,
                "source_file": str(path.name),
                "source_label": current_chapter.get("source_label"),
                "review_required": False,
                "created_at": now_iso(),
            }
            units.append(current_unit)
            point_counter_by_unit[unit_id] = 0
            continue

        if line.startswith("- ") and current_chapter and current_unit:
            content = re.sub(r"^\-\s*", "", line).strip()
            if not content:
                continue
            unit_id = current_unit["unit_id"]
            point_counter_by_unit[unit_id] += 1
            point_index = point_counter_by_unit[unit_id]
            point_id = f"KP_{int(current_chapter['chapter_id'][2:]):02d}_{current_unit['unit_index']:03d}_{point_index:03d}"
            difficulty = "basic"
            if any(word in content for word in ["计算", "判断", "解释", "综合", "机制"]):
                difficulty = "medium"
            if any(word in content for word in ["Frost", "E-pH", "Nernst", "分子轨道", "反馈", "多重平衡"]):
                difficulty = "hard"
            points.append(
                {
                    "knowledge_point_id": point_id,
                    "id": point_id,
                    "chapter_id": current_chapter["chapter_id"],
                    "chapter_title": current_chapter["chapter_title"],
                    "unit_id": current_unit["unit_id"],
                    "unit_title": current_unit["unit_title"],
                    "content": content,
                    "element_area": current_chapter["element_area"],
                    "tags": extract_tags(content, [current_chapter["element_area"]]),
                    "difficulty": difficulty,
                    "review_required": False,
                    "source_file": str(path.name),
                    "source_label": current_chapter.get("source_label"),
                    "created_at": now_iso(),
                }
            )

    return chapters, units, points


def main() -> None:
    ensure_dirs()
    save_source_documents()
    path = find_source_file("知识框架", suffixes={".md"})
    if path is None:
        raise FileNotFoundError("Could not find 知识框架.md or a close Markdown source file under docs/.")

    chapters, units, points = parse_knowledge_markdown(path)
    dump_json(PROCESSED_DIR / "chapters.json", chapters)
    dump_json(PROCESSED_DIR / "knowledge_units.json", units)
    dump_json(PROCESSED_DIR / "knowledge_points.json", points)
    print(f"parsed {len(chapters)} chapters, {len(units)} units, {len(points)} knowledge points from {path}")


if __name__ == "__main__":
    main()
