from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd


COLUMN_ALIASES = {
    "class_name": {"class", "class_name", "班级", "班级名称"},
    "student_id": {"student_id", "student_no", "学号", "学生学号"},
    "student_name": {"name", "student_name", "姓名", "学生姓名"},
}


@dataclass(frozen=True)
class RosterRow:
    row_number: int
    class_name: str
    student_id: str
    student_name: str
    errors: list[str]

    @property
    def valid(self) -> bool:
        return not self.errors


def _normalize_header(value: Any) -> str:
    return str(value or "").strip().lower().replace(" ", "_")


def _column_lookup(columns: list[Any]) -> dict[str, str]:
    normalized = {_normalize_header(column): str(column) for column in columns}
    lookup: dict[str, str] = {}
    for target, aliases in COLUMN_ALIASES.items():
        for alias in aliases:
            key = _normalize_header(alias)
            if key in normalized:
                lookup[target] = normalized[key]
                break
    return lookup


def _read_dataframe(filename: str, content: bytes) -> pd.DataFrame:
    suffix = Path(filename).suffix.lower()
    if suffix in {".xlsx", ".xls"}:
        return pd.read_excel(BytesIO(content), dtype=str).fillna("")
    if suffix == ".csv":
        for encoding in ("utf-8-sig", "utf-8", "gb18030"):
            try:
                return pd.read_csv(BytesIO(content), dtype=str, encoding=encoding).fillna("")
            except UnicodeDecodeError:
                continue
        return pd.read_csv(BytesIO(content), dtype=str, encoding="utf-8", errors="ignore").fillna("")
    raise ValueError("Roster file must be CSV, XLS, or XLSX.")


def parse_roster(filename: str, content: bytes, default_class_name: str = "") -> list[RosterRow]:
    frame = _read_dataframe(filename, content)
    lookup = _column_lookup(list(frame.columns))
    missing = [key for key in ("student_id", "student_name") if key not in lookup]
    if missing:
        raise ValueError("Roster file is missing required columns: " + ", ".join(missing))

    rows: list[RosterRow] = []
    seen_student_ids: set[str] = set()
    for index, item in frame.iterrows():
        row_number = int(index) + 2
        student_id = str(item.get(lookup["student_id"], "")).strip()
        student_name = str(item.get(lookup["student_name"], "")).strip()
        class_name = str(item.get(lookup.get("class_name", ""), "")).strip() if "class_name" in lookup else default_class_name
        errors: list[str] = []
        if not student_id:
            errors.append("missing_student_id")
        if not student_name:
            errors.append("missing_student_name")
        if not class_name:
            errors.append("missing_class_name")
        if student_id and student_id in seen_student_ids:
            errors.append("duplicate_student_id_in_file")
        seen_student_ids.add(student_id)
        rows.append(
            RosterRow(
                row_number=row_number,
                class_name=class_name,
                student_id=student_id,
                student_name=student_name,
                errors=errors,
            )
        )
    return rows


def roster_preview(rows: list[RosterRow]) -> dict[str, Any]:
    valid_rows = [row for row in rows if row.valid]
    invalid_rows = [row for row in rows if not row.valid]
    return {
        "total_rows": len(rows),
        "valid_rows": len(valid_rows),
        "invalid_rows": len(invalid_rows),
        "rows": [
            {
                "row_number": row.row_number,
                "class_name": row.class_name,
                "student_id": row.student_id,
                "student_name": row.student_name,
                "valid": row.valid,
                "errors": row.errors,
            }
            for row in rows
        ],
    }
