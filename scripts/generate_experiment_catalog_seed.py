from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.app.domains.catalog_tree.catalog_seed import (
    CANONICAL_POINT_GROUPS_SEED_PATH,
    CATALOG_SEED_VALIDATION_REPORT_PATH,
    CATALOG_TREE_SEED_PATH,
    EXPECTED_CATALOG_COUNTS,
    load_point_content_seed,
    validate_catalog_seed,
)

OUTLINE_SOURCE = ROOT / "docs" / "实验目录_整理版.md"
EXAMPLE_SOURCE = ROOT / "docs" / "30点位例子.txt"
OUTLINE_SOURCE_LABEL = "docs/实验目录_整理版.md"
EXAMPLE_SOURCE_LABEL = "docs/30点位例子.txt"


@dataclass(frozen=True)
class ExampleMapping:
    example_number: int
    example_title: str
    target_path: tuple[str, ...]


SUBSCRIPT_DIGITS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
FORMULA_PATTERN = re.compile(r"(?:[A-Z][a-z]?[0-9₀-₉]*){1,}")
TOKEN_PATTERN = re.compile(r"[\u4e00-\u9fff]{2,}|[A-Za-z][A-Za-z0-9]*[0-9₀-₉]*|[0-9]+")
SEMANTIC_CANDIDATE_LIMIT = 5
AMBIGUOUS_SCORE_GAP = 2.0

KNOWN_SAMPLE_WORDING_CORRECTIONS: dict[int, dict[str, str]] = {
    21: {
        "corrected": "NaClO + 品红溶液",
        "reason": "Reviewed source correction for the hypochlorite decolorization sample.",
    }
}


EXAMPLE_MAPPINGS: tuple[ExampleMapping, ...] = (
    ExampleMapping(1, "第18章 五 焰色反应", ("第18章 碱金属和碱土金属", "五、焰色反应", "锂、钠、钾、钙、锶、钡盐的焰色反应")),
    ExampleMapping(2, "第18章 一 1.钠加热燃烧实验", ("第18章 碱金属和碱土金属", "一、碱金属、碱土金属单质活泼性的比较", "钠加热燃烧实验")),
    ExampleMapping(3, "第18章 一 2.镁条燃烧实验", ("第18章 碱金属和碱土金属", "一、碱金属、碱土金属单质活泼性的比较", "镁条燃烧实验")),
    ExampleMapping(4, "第18章 一 3.钠与水反应", ("第18章 碱金属和碱土金属", "一、碱金属、碱土金属单质活泼性的比较", "钠与水反应")),
    ExampleMapping(5, "第18章 一 5.镁与冷／热水反应", ("第18章 碱金属和碱土金属", "一、碱金属、碱土金属单质活泼性的比较", "镁与冷／热水反应")),
    ExampleMapping(6, "第18章 一 6.钙与水反应", ("第18章 碱金属和碱土金属", "一、碱金属、碱土金属单质活泼性的比较", "钙与水反应")),
    ExampleMapping(7, "第15章 二 （1）亚硝酸的生成与分解", ("第15章 氮族元素", "二、亚硝酸及其盐的性质", "亚硝酸的生成与分解")),
    ExampleMapping(8, "第15章 二 （2）亚硝酸的氧化性", ("第15章 氮族元素", "二、亚硝酸及其盐的性质", "亚硝酸的氧化性")),
    ExampleMapping(9, "第15章 二 （3）亚硝酸的还原性", ("第15章 氮族元素", "二、亚硝酸及其盐的性质", "亚硝酸的还原性")),
    ExampleMapping(10, "NaNO₂ + 对氨基苯磺酸 + 萘胺 | HAc酸性体系", ("第15章 氮族元素", "二、亚硝酸及其盐的性质", "亚硝酸根的检验方法", "NaNO₂ + 对氨基苯磺酸 + 萘胺 | HAc酸性体系")),
    ExampleMapping(11, "NaNO₂ + KI + CCl₄ | H₂SO₄酸性体系", ("第15章 氮族元素", "二、亚硝酸及其盐的性质", "亚硝酸根的检验方法", "NaNO₂ + KI + CCl₄ | H₂SO₄酸性体系")),
    ExampleMapping(12, "浓硝酸 + 硫粉", ("第15章 氮族元素", "三、硝酸及其盐的性质", "硝酸的氧化性", "浓硝酸 + 硫粉")),
    ExampleMapping(13, "浓硝酸 + Na₂S", ("第15章 氮族元素", "三、硝酸及其盐的性质", "硝酸的氧化性", "浓硝酸 + Na2S")),
    ExampleMapping(14, "浓硝酸/稀硝酸 + 铜", ("第15章 氮族元素", "三、硝酸及其盐的性质", "硝酸的氧化性", "浓硝酸/稀硝酸 + 铜")),
    ExampleMapping(15, "FeSO₄·7H₂O + NaNO₃ + 浓硫酸", ("第15章 氮族元素", "三、硝酸及其盐的性质", "硝酸根的检验", "FeSO₄·7H₂O + NaNO₃ + 浓硫酸")),
    ExampleMapping(16, "难溶性硅酸盐的生成——“水中花园”", ("第17章 硼族元素", "一、硼、硅的相似相异性", "难溶性硅酸盐的生成——“水中花园”")),
    ExampleMapping(17, "KI + 浓硫酸 | 湿的醋酸铅试纸", ("第13章 卤族元素", "三、卤素离子的还原性（通风橱内进行）", "利用浓硫酸比较卤素离子的还原性", "KI + 浓硫酸 | 湿的醋酸铅试纸")),
    ExampleMapping(18, "KBr + 浓硫酸 | 湿的KI-淀粉试纸", ("第13章 卤族元素", "三、卤素离子的还原性（通风橱内进行）", "利用浓硫酸比较卤素离子的还原性", "KBr + 浓硫酸 | 湿的KI-淀粉试纸")),
    ExampleMapping(19, "KCl + 浓硫酸 | 湿的pH试纸", ("第13章 卤族元素", "三、卤素离子的还原性（通风橱内进行）", "利用浓硫酸比较卤素离子的还原性", "KCl + 浓硫酸 | 湿的pH试纸")),
    ExampleMapping(20, "NaClO + MnSO₄", ("第13章 卤族元素", "五、卤素含氧酸盐的氧化性", "次氯酸盐的氧化性", "NaClO + MnSO₄")),
    ExampleMapping(21, "NaClO + 品红溶液", ("第13章 卤族元素", "五、卤素含氧酸盐的氧化性", "次氯酸盐的氧化性", "NaClO + 品红溶液")),
    ExampleMapping(22, "NaClO + KI-淀粉 | 酸性体系", ("第13章 卤族元素", "五、卤素含氧酸盐的氧化性", "次氯酸盐的氧化性", "NaClO + KI-淀粉 | 酸性体系")),
    ExampleMapping(23, "KClO₃ + 浓盐酸 | 湿 KI-淀粉试纸", ("第13章 卤族元素", "五、卤素含氧酸盐的氧化性", "氯酸盐的氧化性", "KClO₃ + 浓盐酸 | 湿 KI-淀粉试纸")),
    ExampleMapping(24, "KClO₃ + Na₂SO₃ + AgNO₃", ("第13章 卤族元素", "五、卤素含氧酸盐的氧化性", "氯酸盐的氧化性", "KClO₃ + Na₂SO₃ + AgNO₃")),
    ExampleMapping(25, "KClO₃ + KI + CCl₄", ("第13章 卤族元素", "五、卤素含氧酸盐的氧化性", "氯酸盐的氧化性", "KClO₃ + KI + CCl₄")),
    ExampleMapping(26, "KClO₃ + KI-淀粉 | 酸性体系", ("第13章 卤族元素", "五、卤素含氧酸盐的氧化性", "氯酸盐的氧化性", "KClO₃ + KI-淀粉 | 酸性体系")),
    ExampleMapping(27, "高氯酸盐的氧化性", ("第13章 卤族元素", "五、卤素含氧酸盐的氧化性", "高氯酸盐的氧化性")),
    ExampleMapping(28, "卤化银的感光性", ("第13章 卤族元素", "七、金属卤化物的性质", "卤化银的感光性")),
    ExampleMapping(29, "过氧化氢的酸性", ("第14章 氧族元素", "三、过氧化氢的制备与性质", "过氧化氢的性质", "过氧化氢的酸性")),
    ExampleMapping(30, "H₂O₂ + KI | 酸性体系", ("第14章 氧族元素", "三、过氧化氢的制备与性质", "过氧化氢的性质", "过氧化氢的氧化性", "H₂O₂ + KI | 酸性体系")),
)


def _slug_hash(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:16]


def _canonical_point_id_from_title(title: str) -> str:
    return f"cat-canon-title-{_slug_hash(title)[:12]}"


def _canonical_point_id_from_seed(seed_key: str) -> str:
    return f"cat-canon-seed-{_slug_hash(seed_key)[:12]}"


def _chapter_title(chapter_number: int, title: str) -> str:
    return f"第{chapter_number}章 {title.strip()}"


def _seed_key(*, chapter_number: int, path_titles: list[str], display_order: int) -> str:
    payload = f"{chapter_number}\0{'/'.join(path_titles)}\0{display_order}"
    return f"cat-outline-ch{chapter_number}-{_slug_hash(payload)}"


def _display_order(order_by_parent: dict[str, int], parent_key: str) -> int:
    order_by_parent[parent_key] = order_by_parent.get(parent_key, 0) + 1
    return order_by_parent[parent_key]


def parse_catalog_outline(path: Path) -> list[dict[str, Any]]:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    nodes: list[dict[str, Any]] = []
    by_key: dict[str, dict[str, Any]] = {}
    stack: list[dict[str, Any]] = []
    order_by_parent: dict[str, int] = {}
    current_chapter: dict[str, Any] | None = None
    current_heading: dict[str, Any] | None = None

    def add_node(title: str, line_number: int, *, parent: dict[str, Any] | None, source_kind: str) -> dict[str, Any]:
        if current_chapter is None:
            raise ValueError(f"line {line_number}: catalog node outside chapter")
        path_titles = [current_chapter["chapter_title"]]
        if parent:
            path_titles.extend(list(parent["path_titles"])[1:])
        path_titles.append(title)
        parent_key = str(parent["seed_key"]) if parent else f"chapter:{current_chapter['chapter_number']}"
        display_order = _display_order(order_by_parent, parent_key)
        seed_key = _seed_key(
            chapter_number=int(current_chapter["chapter_number"]),
            path_titles=path_titles,
            display_order=display_order,
        )
        node = {
            "chapter_number": current_chapter["chapter_number"],
            "chapter_id": f"CH{int(current_chapter['chapter_number']):02d}",
            "seed_key": seed_key,
            "parent_seed_key": str(parent["seed_key"]) if parent else None,
            "node_kind": "directory" if source_kind == "heading" else "unknown",
            "title": title,
            "path_titles": path_titles,
            "display_order": display_order,
            "source_doc": OUTLINE_SOURCE_LABEL,
            "source_line": line_number,
            "source_kind": source_kind,
        }
        nodes.append(node)
        by_key[seed_key] = node
        return node

    for line_number, line in enumerate(lines, start=1):
        chapter_match = re.match(r"^#\s*第\s*(\d+)\s*章\s*(.+?)\s*$", line)
        if chapter_match:
            chapter_number = int(chapter_match.group(1))
            current_chapter = {
                "chapter_number": chapter_number,
                "chapter_title": _chapter_title(chapter_number, chapter_match.group(2)),
            }
            current_heading = None
            stack = []
            continue

        heading_match = re.match(r"^##\s+(.+?)\s*$", line)
        if heading_match and current_chapter:
            title = heading_match.group(1).strip()
            if current_chapter["chapter_number"] == 21 and title == "暂无对应实验内容":
                current_heading = None
                stack = []
                continue
            current_heading = add_node(title, line_number, parent=None, source_kind="heading")
            stack = []
            continue

        bullet_match = re.match(r"^(\s*)-\s+(.+?)\s*$", line)
        if not bullet_match or not current_chapter:
            continue
        title = bullet_match.group(2).strip()
        if current_chapter["chapter_number"] == 21 and title == "暂无对应实验内容":
            continue
        depth = len(bullet_match.group(1).replace("\t", "  ")) // 2
        if depth == 0:
            parent = current_heading
        else:
            if depth - 1 >= len(stack):
                raise ValueError(f"line {line_number}: missing parent bullet for {title}")
            parent = stack[depth - 1]
        node = add_node(title, line_number, parent=parent, source_kind="bullet")
        if depth >= len(stack):
            stack.extend([{}] * (depth - len(stack) + 1))
        stack[depth] = node
        stack = stack[: depth + 1]

    parent_keys = {str(node.get("parent_seed_key")) for node in nodes if node.get("parent_seed_key")}
    for node in nodes:
        if node["node_kind"] == "unknown":
            node["node_kind"] = "directory" if node["seed_key"] in parent_keys else "point"
    return nodes


def build_canonical_point_groups(nodes: list[dict[str, Any]]) -> dict[str, Any]:
    points = [node for node in nodes if node.get("node_kind") == "point"]
    by_title: dict[str, list[dict[str, Any]]] = {}
    for node in points:
        by_title.setdefault(str(node.get("title") or "").strip(), []).append(node)
    duplicate_groups = {
        title: rows
        for title, rows in by_title.items()
        if len(rows) > 1
    }
    groups: list[dict[str, Any]] = []
    canonical_points: list[dict[str, Any]] = []
    for title, rows in sorted(by_title.items(), key=lambda item: (item[0], len(item[1]))):
        if not title:
            continue
        if len(rows) > 1:
            canonical_point_id = _canonical_point_id_from_title(title)
            grouping_decision = "reviewed_exact_duplicate_title"
        else:
            canonical_point_id = _canonical_point_id_from_seed(str(rows[0]["seed_key"]))
            grouping_decision = "singleton_point_node"
        for row in rows:
            row["placement_node_id"] = row["seed_key"]
            row["canonical_point_id"] = canonical_point_id
            row["canonical_point_title"] = title
            row["placement_kind"] = "catalog_point_placement"
        placement_seed_keys = [str(row["seed_key"]) for row in rows]
        canonical_points.append(
            {
                "canonical_point_id": canonical_point_id,
                "title": title,
                "summary": "",
                "status": "published",
                "grouping_decision": grouping_decision,
                "placement_seed_keys": placement_seed_keys,
                "placement_paths": [" / ".join(str(part) for part in row.get("path_titles") or []) for row in rows],
                "source_doc": OUTLINE_SOURCE_LABEL,
                "metadata": {
                    "catalog_outline_seed": True,
                    "grouping_decision": grouping_decision,
                },
            }
        )
        if len(rows) > 1:
            groups.append(
                {
                    "canonical_point_id": canonical_point_id,
                    "title": title,
                    "review_status": "reviewed_current_outline_duplicate",
                    "grouping_decision": grouping_decision,
                    "placement_count": len(rows),
                    "placement_seed_keys": placement_seed_keys,
                    "placement_paths": [" / ".join(str(part) for part in row.get("path_titles") or []) for row in rows],
                }
            )
    hypochlorite = [
        node
        for node in points
        if node.get("title") in {"NaClO + MnSO₄", "NaClO + 品红溶液"}
        and tuple(node.get("path_titles") or [])[:3]
        == ("第13章 卤族元素", "五、卤素含氧酸盐的氧化性", "次氯酸盐的氧化性")
    ]
    return {
        "metadata": {
            "artifact_type": "experiment_catalog_canonical_point_groups",
            "version": "catalog-outline-canonical-groups-v1",
            "source_doc": OUTLINE_SOURCE_LABEL,
            "grouping_policy": "Current outline exact duplicate leaf titles are reviewed as the same canonical experiment; singletons remain independent.",
            "non_goals": [
                "No shortcut/reference node kinds.",
                "No fuzzy or formula-only automatic merge.",
            ],
        },
        "counts": {
            "point_placements": len(points),
            "canonical_points": len(canonical_points),
            "duplicate_group_count": len(groups),
            "duplicate_placement_surplus": sum(group["placement_count"] - 1 for group in groups),
            "ambiguous_duplicate_count": 0,
        },
        "groups": groups,
        "distinct_exceptions": [
            {
                "title": node.get("title"),
                "placement_seed_key": node.get("seed_key"),
                "canonical_point_id": node.get("canonical_point_id"),
                "path": " / ".join(str(part) for part in node.get("path_titles") or []),
                "reason": "Reviewed hypochlorite sibling correction: NaClO + MnSO4 and NaClO + 品红溶液 are different experiments.",
            }
            for node in hypochlorite
        ],
        "ambiguous_groups": [],
        "canonical_points": canonical_points,
    }


def _parse_example_blocks(path: Path) -> dict[int, dict[str, Any]]:
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    blocks: dict[int, dict[str, Any]] = {}
    current: dict[str, Any] | None = None
    current_field: str | None = None
    expected_number = 1
    field_labels = {
        "实验原理": "principle_text",
        "现象解释": "phenomenon_explanation",
        "安全提示": "safety_note",
    }

    def append_field(field: str, value: str) -> None:
        if current is None:
            return
        current.setdefault(field, [])
        if value.strip():
            current[field].append(value.rstrip())

    for line_number, line in enumerate(lines, start=1):
        start_match = re.match(r"^\s*(\d{1,2})[.．]\s*(.+?)\s*$", line)
        is_expected_heading = False
        if start_match and int(start_match.group(1)) == expected_number:
            heading_title = start_match.group(2).strip()
            is_expected_heading = expected_number > 16 or "第" in heading_title
        if is_expected_heading and start_match:
            if current is not None:
                current["source_line_end"] = line_number - 1
                blocks[int(current["example_number"])] = current
            current = {
                "example_number": expected_number,
                "source_line_start": line_number,
                "example_title_from_source": start_match.group(2).strip(),
                "principle_text": [],
                "phenomenon_explanation": [],
                "safety_note": [],
            }
            current_field = None
            expected_number += 1
            continue
        if current is None:
            continue
        stripped = line.strip()
        header = next((label for label in field_labels if stripped.startswith(label)), None)
        if header:
            current_field = field_labels[header]
            remainder = stripped[len(header) :].lstrip("：:").strip()
            append_field(current_field, remainder)
            continue
        if current_field:
            append_field(current_field, line)
    if current is not None:
        current["source_line_end"] = len(lines)
        blocks[int(current["example_number"])] = current
    return blocks


def _normalize_match_text(value: str) -> str:
    return value.translate(SUBSCRIPT_DIGITS).casefold()


def _expand_token(token: str) -> set[str]:
    normalized = _normalize_match_text(token.strip())
    if not normalized:
        return set()
    terms = {normalized}
    if re.fullmatch(r"[\u4e00-\u9fff]+", token) and len(token) > 2:
        terms.update(token[index : index + 2] for index in range(len(token) - 1))
    return terms


def _match_tokens(*values: str) -> set[str]:
    tokens: set[str] = set()
    for value in values:
        if not value:
            continue
        for match in FORMULA_PATTERN.finditer(value):
            tokens.update(_expand_token(match.group(0)))
        normalized = _normalize_match_text(value)
        for match in TOKEN_PATTERN.finditer(normalized):
            tokens.update(_expand_token(match.group(0)))
    return {token for token in tokens if len(token) > 1}


def _formula_tokens(*values: str) -> set[str]:
    tokens: set[str] = set()
    for value in values:
        for match in FORMULA_PATTERN.finditer(value or ""):
            tokens.add(_normalize_match_text(match.group(0)))
    return tokens


def _example_match_text(mapping: ExampleMapping, block: dict[str, Any]) -> str:
    fields = [
        mapping.example_title,
        str(block.get("example_title_from_source") or ""),
        "\n".join(block.get("principle_text") or []),
        "\n".join(block.get("phenomenon_explanation") or []),
        "\n".join(block.get("safety_note") or []),
    ]
    correction = KNOWN_SAMPLE_WORDING_CORRECTIONS.get(mapping.example_number)
    if correction:
        fields.append(correction["corrected"])
    return "\n".join(field for field in fields if field)


def _score_candidate(
    *,
    query_text: str,
    query_tokens: set[str],
    query_formulae: set[str],
    node: dict[str, Any],
) -> dict[str, Any]:
    path_titles = [str(part) for part in node.get("path_titles") or []]
    node_text = " / ".join(path_titles)
    node_tokens = _match_tokens(node_text)
    node_formulae = _formula_tokens(node_text)
    overlap = sorted(query_tokens & node_tokens)
    formula_overlap = sorted(query_formulae & node_formulae)
    normalized_query = _normalize_match_text(query_text)
    normalized_leaf = _normalize_match_text(str(node.get("title") or ""))
    exact_leaf_bonus = 6.0 if normalized_leaf and normalized_leaf in normalized_query else 0.0
    path_bonus = sum(1.0 for part in path_titles[:-1] if _normalize_match_text(part) in normalized_query)
    score = float(len(overlap)) + (2.0 * len(formula_overlap)) + exact_leaf_bonus + path_bonus
    return {
        "seed_key": node["seed_key"],
        "path": node_text,
        "score": round(score, 3),
        "matched_terms": overlap[:16],
        "matched_formulae": formula_overlap,
    }


def _semantic_candidates(nodes: list[dict[str, Any]], mapping: ExampleMapping, block: dict[str, Any]) -> list[dict[str, Any]]:
    query_text = _example_match_text(mapping, block)
    query_tokens = _match_tokens(query_text)
    query_formulae = _formula_tokens(query_text)
    candidates = [
        _score_candidate(
            query_text=query_text,
            query_tokens=query_tokens,
            query_formulae=query_formulae,
            node=node,
        )
        for node in nodes
        if node.get("node_kind") == "point"
    ]
    candidates.sort(key=lambda item: (-float(item["score"]), str(item["path"])))
    return [candidate for candidate in candidates if float(candidate["score"]) > 0]


def _report_candidates(candidates: list[dict[str, Any]], target_seed_key: str) -> list[dict[str, Any]]:
    reported = candidates[:SEMANTIC_CANDIDATE_LIMIT]
    if target_seed_key not in {str(candidate["seed_key"]) for candidate in reported}:
        target_candidate = next(
            (candidate for candidate in candidates if str(candidate["seed_key"]) == target_seed_key),
            None,
        )
        if target_candidate:
            reported = [*reported, target_candidate]
    return reported


def _build_semantic_mapping_report(
    *,
    nodes: list[dict[str, Any]],
    mapping: ExampleMapping,
    block: dict[str, Any],
    target: dict[str, Any],
    allow_reviewed_override: bool,
) -> dict[str, Any]:
    candidates = _semantic_candidates(nodes, mapping, block)
    target_rank = next(
        (index for index, candidate in enumerate(candidates, start=1) if candidate["seed_key"] == target["seed_key"]),
        None,
    )
    target_candidate = next((candidate for candidate in candidates if candidate["seed_key"] == target["seed_key"]), None)
    top_score = float(candidates[0]["score"]) if candidates else 0.0
    second_score = float(candidates[1]["score"]) if len(candidates) > 1 else 0.0
    ambiguous = len(candidates) > 1 and second_score > 0 and (top_score - second_score) <= AMBIGUOUS_SCORE_GAP
    if target_rank is None:
        raise ValueError(f"example {mapping.example_number}: reviewed target is not in semantic candidates")
    if (target_rank != 1 or ambiguous) and not allow_reviewed_override:
        raise ValueError(f"example {mapping.example_number}: semantic mapping is ambiguous and needs a reviewed override")
    review_status = "reviewed_override" if target_rank != 1 or ambiguous else "semantic_match"
    report: dict[str, Any] = {
        "method": "semantic_title_path_reagent_match",
        "review_status": review_status,
        "target_rank": target_rank,
        "target_score": float(target_candidate["score"]) if target_candidate else 0.0,
        "ambiguous": ambiguous,
        "top_candidates": _report_candidates(candidates, str(target["seed_key"])),
        "matched_terms": list(target_candidate.get("matched_terms") or []) if target_candidate else [],
        "matched_formulae": list(target_candidate.get("matched_formulae") or []) if target_candidate else [],
    }
    if review_status == "reviewed_override":
        report["override"] = {
            "type": "reviewed_target_path",
            "reason": "The curated target path resolves the sample when semantic candidates are tied or nearby.",
        }
    correction = KNOWN_SAMPLE_WORDING_CORRECTIONS.get(mapping.example_number)
    if correction:
        report["wording_correction"] = correction
    return report


def build_retired_point_content_examples(nodes: list[dict[str, Any]], example_source: Path) -> list[dict[str, Any]]:
    raise RuntimeError(
        "The 30-example point-content seed path is retired. Use "
        "data/seed/experiment_catalog/point_content_seed.json, generated from the normalized three-element review."
    )
    blocks = _parse_example_blocks(example_source)
    nodes_by_path = {" / ".join(node["path_titles"]): node for node in nodes}
    examples: list[dict[str, Any]] = []
    errors: list[str] = []
    for mapping in EXAMPLE_MAPPINGS:
        block = blocks.get(mapping.example_number)
        if not block:
            errors.append(f"example {mapping.example_number}: missing source block")
            continue
        target_path_text = " / ".join(mapping.target_path)
        target = nodes_by_path.get(target_path_text)
        if not target:
            errors.append(f"example {mapping.example_number}: target path does not resolve: {target_path_text}")
            continue
        try:
            semantic_mapping = _build_semantic_mapping_report(
                nodes=nodes,
                mapping=mapping,
                block=block,
                target=target,
                allow_reviewed_override=True,
            )
        except ValueError as exc:
            errors.append(str(exc))
            continue
        examples.append(
            {
                "example_number": mapping.example_number,
                "example_title": mapping.example_title,
                "example_title_from_source": block["example_title_from_source"],
                "target_seed_key": target["seed_key"],
                "target_canonical_point_id": target.get("canonical_point_id"),
                "target_path_titles": list(mapping.target_path),
                "target_path": target_path_text,
                "principle_mode": "text",
                "principle_text": "\n".join(block["principle_text"]).strip(),
                "phenomenon_explanation": "\n".join(block["phenomenon_explanation"]).strip(),
                "safety_note": "\n".join(block["safety_note"]).strip(),
                "content_status": "published",
                "source_doc": EXAMPLE_SOURCE_LABEL,
                "source_line_start": block["source_line_start"],
                "source_line_end": block["source_line_end"],
                "semantic_mapping": semantic_mapping,
            }
        )
    if errors:
        raise ValueError("Point-content example mapping failed:\n" + "\n".join(errors))
    return examples


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def generate_catalog_seed(
    *,
    outline_path: Path = OUTLINE_SOURCE,
    catalog_path: Path = CATALOG_TREE_SEED_PATH,
    groups_path: Path = CANONICAL_POINT_GROUPS_SEED_PATH,
    report_path: Path = CATALOG_SEED_VALIDATION_REPORT_PATH,
) -> dict[str, Any]:
    nodes = parse_catalog_outline(outline_path)
    grouping = build_canonical_point_groups(nodes)
    canonical_points = grouping["canonical_points"]
    point_content = load_point_content_seed()
    validation = validate_catalog_seed(nodes, point_content)
    catalog_payload = {
        "metadata": {
            "artifact_type": "experiment_catalog_outline_seed",
            "version": "catalog-outline-v2-canonical-placements",
            "source_doc": OUTLINE_SOURCE_LABEL,
            "expected_counts": EXPECTED_CATALOG_COUNTS,
            "classification": "## headings and non-leaf bullets are directories; leaf bullets are point placements targeting canonical experiment points.",
            "canonical_grouping_seed": groups_path.relative_to(ROOT).as_posix(),
        },
        "canonical_points": canonical_points,
        "nodes": nodes,
    }
    report = {
        **validation,
        "catalog_seed": catalog_path.relative_to(ROOT).as_posix(),
        "canonical_point_groups_seed": groups_path.relative_to(ROOT).as_posix(),
        "point_content_seed": "data/seed/experiment_catalog/point_content_seed.json",
        "canonical_grouping": grouping["counts"],
        "reviewed_duplicate_groups": grouping["groups"],
        "ambiguous_duplicate_groups": grouping["ambiguous_groups"],
    }
    write_json(catalog_path, catalog_payload)
    write_json(groups_path, grouping)
    write_json(report_path, report)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate the canonical experiment catalog outline seed.")
    parser.add_argument("--outline", type=Path, default=OUTLINE_SOURCE)
    parser.add_argument("--catalog-output", type=Path, default=CATALOG_TREE_SEED_PATH)
    parser.add_argument("--groups-output", type=Path, default=CANONICAL_POINT_GROUPS_SEED_PATH)
    parser.add_argument("--report", type=Path, default=CATALOG_SEED_VALIDATION_REPORT_PATH)
    args = parser.parse_args()

    report = generate_catalog_seed(
        outline_path=args.outline,
        catalog_path=args.catalog_output,
        groups_path=args.groups_output,
        report_path=args.report,
    )
    sys.stdout.buffer.write((json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    if not report["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
