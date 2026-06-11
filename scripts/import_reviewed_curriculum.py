from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from scripts.common import PROCESSED_DIR, now_iso
    from scripts.parse_knowledge_md import parse_knowledge_markdown
except ModuleNotFoundError:
    from common import PROCESSED_DIR, now_iso
    from parse_knowledge_md import parse_knowledge_markdown

ROOT = Path(__file__).resolve().parents[1]
STUDENTS_DOCS_DIR = ROOT / "docs" / "students"
DEFAULT_OUTPUT = PROCESSED_DIR / "reviewed_curriculum.json"
EXPECTED_COUNTS = {"chapters": 11, "knowledge_units": 133, "knowledge_points": 385}


def find_reviewed_curriculum_source() -> Path:
    candidates = [path for path in STUDENTS_DOCS_DIR.glob("*.md") if not path.name.lower().startswith("ai")]
    if not candidates:
        raise FileNotFoundError("Could not find reviewed curriculum markdown under docs/students.")
    return sorted(candidates, key=lambda path: path.name)[0]


def validate_reviewed_curriculum(
    chapters: list[dict[str, Any]],
    units: list[dict[str, Any]],
    points: list[dict[str, Any]],
    expected_counts: dict[str, int] | None = None,
) -> dict[str, Any]:
    expected_counts = expected_counts or EXPECTED_COUNTS
    errors: list[str] = []
    counts = {"chapters": len(chapters), "knowledge_units": len(units), "knowledge_points": len(points)}
    for key, expected in expected_counts.items():
        if counts[key] != expected:
            errors.append(f"{key} count mismatch: expected {expected}, got {counts[key]}")

    chapter_ids = {chapter["chapter_id"] for chapter in chapters}
    unit_ids = {unit["unit_id"] for unit in units}
    if "CH00" not in chapter_ids:
        errors.append("CH00 general/cross-chapter chapter is missing")
    general_units = [unit for unit in units if unit["chapter_id"] == "CH00"]
    if len(general_units) != 5:
        errors.append(f"CH00 general/cross-chapter unit count mismatch: expected 5, got {len(general_units)}")
    if any(unit["chapter_id"] == "CH22" and unit.get("source_label") == "第 999 章 未标章节" for unit in units):
        errors.append("Unmarked units were attached to CH22")
    for unit in units:
        if unit["chapter_id"] not in chapter_ids:
            errors.append(f"Unit {unit['unit_id']} references missing chapter {unit['chapter_id']}")
    for point in points:
        if point["chapter_id"] not in chapter_ids:
            errors.append(f"Point {point['knowledge_point_id']} references missing chapter {point['chapter_id']}")
        if point["unit_id"] not in unit_ids:
            errors.append(f"Point {point['knowledge_point_id']} references missing unit {point['unit_id']}")

    return {"ok": not errors, "counts": counts, "errors": errors}


def build_reviewed_curriculum(source: Path) -> dict[str, Any]:
    chapters, units, points = parse_knowledge_markdown(source)
    validation = validate_reviewed_curriculum(chapters, units, points)
    return {
        "version_code": f"reviewed-{now_iso()[:10]}",
        "title": "审核版无机元素化学 KC/KP 树",
        "source_path": str(source.relative_to(ROOT)),
        "status": "draft",
        "validation": validation,
        "chapters": chapters,
        "knowledge_units": units,
        "knowledge_points": points,
        "created_at": now_iso(),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Import the reviewed KC/KP tree into a draft JSON artifact.")
    parser.add_argument("--source", type=Path, default=None)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--sync-processed",
        action="store_true",
        help="Also replace processed chapters, knowledge_units, and knowledge_points with this reviewed curriculum.",
    )
    args = parser.parse_args()

    source = args.source or find_reviewed_curriculum_source()
    if not source.is_absolute():
        source = ROOT / source
    source = source.resolve()
    curriculum = build_reviewed_curriculum(source)
    if not curriculum["validation"]["ok"]:
        raise ValueError("Reviewed curriculum validation failed:\n" + "\n".join(curriculum["validation"]["errors"]))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(curriculum, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.sync_processed:
        for key, file_name in [
            ("chapters", "chapters.json"),
            ("knowledge_units", "knowledge_units.json"),
            ("knowledge_points", "knowledge_points.json"),
        ]:
            (PROCESSED_DIR / file_name).write_text(
                json.dumps(curriculum[key], ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
    print(f"wrote {args.output}")
    if args.sync_processed:
        print("synced processed curriculum tables")
    print(curriculum["validation"]["counts"])


if __name__ == "__main__":
    main()
