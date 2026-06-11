from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DOCS_DIR = ROOT / "docs"
DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SEED_DIR = DATA_DIR / "seed"
INTERMEDIATE_DIR = DATA_DIR / "intermediate"
EXPORTS_DIR = DATA_DIR / "exports"
REVIEW_CSV_DIR = EXPORTS_DIR / "review_csv"
RAG_PREVIEW_DIR = EXPORTS_DIR / "rag_preview"

GENERATED_DOC_NAMES = {
    "data_pipeline.md",
    "data_model.md",
    "rag_design.md",
    "extraction_quality_report.md",
    "teacher_review_guide.md",
    "next_steps.md",
}

SOURCE_SUFFIXES = {".pdf", ".pptx", ".ppt", ".md", ".txt"}
COURSE_SOURCE_DOCUMENT_KINDS = {"courseware", "knowledge_framework", "experiment_material"}
GENERAL_CHAPTER_SOURCE_NUMBER = 999
GENERAL_CHAPTER_NUMBER = 0
GENERAL_CHAPTER_TITLE = "通识/跨章节"
GENERAL_CHAPTER_HEADING = "无机化学通识"
CHAPTER_RE = re.compile(r"第\s*([0-9]{1,3})\s*章")

CHEMISTRY_TERMS = [
    "卤素",
    "氟",
    "氯",
    "溴",
    "碘",
    "氧",
    "硫",
    "硒",
    "氮",
    "磷",
    "砷",
    "碳",
    "硅",
    "硼",
    "铝",
    "锂",
    "钠",
    "钾",
    "镁",
    "钙",
    "铜",
    "锌",
    "铁",
    "钴",
    "镍",
    "锰",
    "铬",
    "镧",
    "锕",
    "稀有气体",
    "氢",
    "氧化",
    "还原",
    "沉淀",
    "配位",
    "水解",
    "酸性",
    "碱性",
    "稳定性",
    "电势",
    "Frost",
    "VSEPR",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def ensure_dirs() -> None:
    for path in [
        RAW_DIR,
        PROCESSED_DIR,
        SEED_DIR,
        INTERMEDIATE_DIR / "markdown",
        INTERMEDIATE_DIR / "json",
        INTERMEDIATE_DIR / "chunks",
        INTERMEDIATE_DIR / "extraction_reports",
        REVIEW_CSV_DIR,
        RAG_PREVIEW_DIR,
    ]:
        path.mkdir(parents=True, exist_ok=True)


def read_text(path: Path) -> str:
    for encoding in ("utf-8", "utf-8-sig", "gb18030"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="utf-8", errors="ignore")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def dump_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: stringify_csv_value(row.get(key, "")) for key in fieldnames})


def stringify_csv_value(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def normalize_ws(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def stable_hash(value: str, length: int = 10) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:length].upper()


def sanitize_id_part(value: str) -> str:
    cleaned = re.sub(r"[^0-9A-Za-z]+", "_", value).strip("_")
    return cleaned.upper() or stable_hash(value, 8)


def chapter_id(number: int | str | None) -> str | None:
    if number is None:
        return None
    try:
        parsed = int(number)
        if parsed == GENERAL_CHAPTER_SOURCE_NUMBER:
            parsed = GENERAL_CHAPTER_NUMBER
        return f"CH{parsed:02d}"
    except (TypeError, ValueError):
        return None


def infer_chapter_source_number(text: str) -> int | None:
    match = CHAPTER_RE.search(text.replace("\u00a0", " "))
    if match:
        return int(match.group(1))
    return None


def infer_chapter_number(text: str) -> int | None:
    source_number = infer_chapter_source_number(text)
    if source_number is not None:
        if source_number == GENERAL_CHAPTER_SOURCE_NUMBER:
            return GENERAL_CHAPTER_NUMBER
        return source_number
    match = re.search(r"\b(?:CH)?([1-2][0-9])\b", text, flags=re.IGNORECASE)
    if match:
        number = int(match.group(1))
        if 13 <= number <= 22:
            return number
    return None


def infer_element_area(chapter_title: str | None) -> str:
    if not chapter_title:
        return ""
    if infer_chapter_source_number(chapter_title) == GENERAL_CHAPTER_SOURCE_NUMBER:
        return GENERAL_CHAPTER_TITLE
    title = re.sub(r"^第\s*[0-9]{1,3}\s*章\s*", "", chapter_title.replace("\u00a0", " "))
    return title.strip()


def infer_document_kind(path: Path) -> str:
    name = path.name.replace("\u00a0", " ")
    suffix = path.suffix.lower()
    if name == "知识框架.md" or "知识框架" in name:
        return "knowledge_framework"
    if "精选实验" in name or "实验内容" in name:
        return "experiment_material"
    if "小程序学习流程" in name:
        return "learning_flow"
    if name.lower() == "jd.txt":
        return "job_description"
    if "AI助教" in name or "韩艳阳" in name:
        return "teaching_paper"
    if suffix == ".pdf" and infer_chapter_number(name):
        return "courseware"
    return suffix.lstrip(".") or "unknown"


def document_id_for(path: Path) -> str:
    kind = infer_document_kind(path)
    number = infer_chapter_number(path.name)
    if kind == "courseware" and number:
        return f"DOC_CH{number:02d}_COURSEWARE"
    if kind == "knowledge_framework":
        return "DOC_KNOWLEDGE_FRAMEWORK"
    if kind == "experiment_material":
        return "DOC_EXPERIMENTS_SELECTED"
    if kind == "learning_flow":
        return "DOC_LEARNING_FLOW"
    if kind == "job_description":
        return "DOC_JOB_DESCRIPTION"
    if kind == "teaching_paper":
        return "DOC_AI_TEACHING_PAPER"
    return f"DOC_{sanitize_id_part(path.stem)[:32]}_{stable_hash(path.name, 6)}"


def discover_source_files() -> list[Path]:
    if not DOCS_DIR.exists():
        return []
    files: list[Path] = []
    for path in DOCS_DIR.iterdir():
        if not path.is_file():
            continue
        if path.name.startswith(".") or path.name in GENERATED_DOC_NAMES:
            continue
        if path.suffix.lower() not in SOURCE_SUFFIXES:
            continue
        if infer_document_kind(path) not in COURSE_SOURCE_DOCUMENT_KINDS:
            continue
        files.append(path)
    return sorted(files, key=lambda p: (infer_chapter_number(p.name) or 99, p.name))


def find_source_file(*keywords: str, suffixes: set[str] | None = None) -> Path | None:
    suffixes = suffixes or SOURCE_SUFFIXES
    files = [p for p in discover_source_files() if p.suffix.lower() in suffixes]
    normalized_keywords = [k.lower() for k in keywords if k]
    for path in files:
        name = path.name.lower()
        if all(k in name for k in normalized_keywords):
            return path
    for path in files:
        name = path.name.lower()
        if any(k in name for k in normalized_keywords):
            return path
    return None


def make_source_document_record(path: Path) -> dict[str, Any]:
    stat = path.stat()
    kind = infer_document_kind(path)
    number = infer_chapter_number(path.name)
    rel_path = str(path.relative_to(ROOT))
    archive_path = RAW_DIR / f"{document_id_for(path)}{path.suffix.lower()}"
    return {
        "document_id": document_id_for(path),
        "file_name": path.name,
        "path": rel_path,
        "archive_path": str(archive_path.relative_to(ROOT)),
        "type": path.suffix.lower().lstrip("."),
        "document_kind": kind,
        "size_bytes": stat.st_size,
        "chapter_id": chapter_id(number),
        "chapter_number": number,
        "processing_status": "discovered",
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }


def archive_source_files(records: list[dict[str, Any]]) -> None:
    ensure_dirs()
    for record in records:
        source = ROOT / record["path"]
        target = ROOT / record["archive_path"]
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.exists():
            if target.exists() and target.stat().st_size == source.stat().st_size:
                continue
            try:
                if target.exists():
                    target.chmod(0o644)
                shutil.copy2(source, target)
            except PermissionError as exc:
                record.setdefault("archive_warnings", []).append(str(exc))


def save_source_documents(update_status: dict[str, str] | None = None) -> list[dict[str, Any]]:
    update_status = update_status or {}
    records = [make_source_document_record(path) for path in discover_source_files()]
    for record in records:
        if record["document_id"] in update_status:
            record["processing_status"] = update_status[record["document_id"]]
            record["updated_at"] = now_iso()
    archive_source_files(records)
    dump_json(PROCESSED_DIR / "source_documents.json", records)
    return records


def source_documents_by_id() -> dict[str, dict[str, Any]]:
    docs = load_json(PROCESSED_DIR / "source_documents.json", [])
    if not docs:
        docs = save_source_documents()
    return {doc["document_id"]: doc for doc in docs}


def extract_tags(text: str, extra: list[str] | None = None) -> list[str]:
    tags: list[str] = []
    for term in CHEMISTRY_TERMS:
        if term and term in text and term not in tags:
            tags.append(term)
    if extra:
        for item in extra:
            if item and item not in tags:
                tags.append(item)
    return tags[:12]


def tokenize_for_match(text: str) -> set[str]:
    text = normalize_ws(text)
    tokens = set(re.findall(r"[A-Za-z][A-Za-z0-9+\-]*|[0-9]+|[\u4e00-\u9fff]{2,}", text))
    for term in CHEMISTRY_TERMS:
        if term in text:
            tokens.add(term)
    return tokens


def top_terms(text: str, limit: int = 12) -> list[str]:
    tokens = [t for t in tokenize_for_match(text) if len(t) >= 2]
    counts = Counter(tokens)
    return [term for term, _ in counts.most_common(limit)]


def split_text(text: str, max_chars: int = 900, overlap: int = 120) -> list[str]:
    text = normalize_ws(text)
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        if end < len(text):
            punctuation_positions = [text.rfind(mark, start, end) for mark in "。；;.!?！？"]
            best = max(punctuation_positions)
            if best > start + max_chars * 0.55:
                end = best + 1
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return [chunk for chunk in chunks if chunk]


def first_heading(text: str) -> str:
    for line in (text or "").splitlines():
        line = line.strip("# \t")
        if 4 <= len(line) <= 80:
            return line
    return ""


def unique_dicts(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    seen: set[Any] = set()
    result: list[dict[str, Any]] = []
    for row in rows:
        value = row.get(key)
        if value in seen:
            continue
        seen.add(value)
        result.append(row)
    return result
