from __future__ import annotations

import json
import math
import os
import re
from collections import Counter
from fractions import Fraction
from typing import Any

from sqlalchemy import text

from server.app.chemistry_search import (
    expand_formula_aliases,
    extract_formulae,
    extract_reaction_features,
    formula_pair_terms,
    normalize_chemistry_text,
)
from server.app.domains.platform.settings import effective_ai_settings
from server.app.infrastructure.settings import get_settings

PARSER_VERSION = "natural-v1"
INLINE_ANNOTATION_DELIMITER = "//"
EQUATION_ANNOTATION_REWRITE_SKILL = """
Task: rewrite teacher-authored reaction lines into the platform reaction-line DSL.

DSL:
- Each non-empty line is exactly one reaction row.
- A row has this shape: EQUATION_CORE [ // ANNOTATION ].
- EQUATION_CORE contains only the chemical equation.
- ANNOTATION is human-readable Chinese supplemental explanation. It may describe conditions, amount notes, medium notes, observation constraints, reagent-source explanations, or teacher prose.

Rewrite rules:
- Prefer preserving the teacher's equation core. Do not change the core merely to explain a condition or reagent source.
- If the teacher wrote a trailing prose note with parentheses, Chinese brackets, "注:", "备注:", "说明:", "酸性/碱性/过量/少量/加热/通风橱", move that prose after // on the same line.
- Never treat formula-internal parentheses as annotations, for example Al(OH)3, Ca3(PO4)2, (NH4)2SO4, or state markers such as (aq).
- If an existing row already has //, preserve or improve the annotation after // and keep it on the same line.
- Do not emit machine labels such as "note:", "condition:", "amount:", or "medium:" in the annotation. Rewrite them as natural Chinese prose because the UI already labels the suffix as "补充说明".
- Return an AI draft for annotation-only rewrites too; the teacher can accept it to standardize the row.
- Only correct the chemistry equation core when you are confident the teacher's core is chemically wrong.

Examples:
- Input: Mn2+ + ClO- + 2OH- -> MnO2↓ + Cl- + H2O（注：NaClO溶液本身呈碱性，提供OH-）
  Draft: Mn2+ + ClO- + 2OH- -> MnO2↓ + Cl- + H2O // NaClO溶液本身呈碱性，提供OH-
- Input: Pb(CH3COO)2 + H2S -> PbS↓ + 2HAc（酸性条件）
  Draft: Pb(CH3COO)2 + H2S -> PbS↓ + 2HAc // 酸性条件
"""

ELEMENT_SYMBOLS = {
    "H",
    "He",
    "Li",
    "Be",
    "B",
    "C",
    "N",
    "O",
    "F",
    "Ne",
    "Na",
    "Mg",
    "Al",
    "Si",
    "P",
    "S",
    "Cl",
    "Ar",
    "K",
    "Ca",
    "Sc",
    "Ti",
    "V",
    "Cr",
    "Mn",
    "Fe",
    "Co",
    "Ni",
    "Cu",
    "Zn",
    "Ga",
    "Ge",
    "As",
    "Se",
    "Br",
    "Kr",
    "Rb",
    "Sr",
    "Ag",
    "Cd",
    "I",
    "Ba",
    "Hg",
    "Pb",
}

CHINESE_ALIASES = {
    "氯气": "Cl2",
    "氯水": "Cl2",
    "氢气": "H2",
    "氧气": "O2",
    "氮气": "N2",
    "溴水": "Br2",
    "溴": "Br2",
    "碘水": "I2",
    "碘": "I2",
    "氯化氢": "HCl",
    "盐酸": "HCl",
    "水": "H2O",
    "过氧化氢": "H2O2",
    "氢氧化钠": "NaOH",
    "氢氧化钾": "KOH",
    "氢氧化钙": "Ca(OH)2",
    "硫酸": "H2SO4",
    "稀硫酸": "H2SO4",
    "硝酸": "HNO3",
    "碳酸钙": "CaCO3",
    "碳酸钠": "Na2CO3",
    "碳酸氢钠": "NaHCO3",
    "氯化钠": "NaCl",
    "氯化钾": "KCl",
    "溴化钾": "KBr",
    "碘化钾": "KI",
    "硫酸铜": "CuSO4",
    "硫酸亚铁": "FeSO4",
    "高锰酸钾": "KMnO4",
    "二氧化碳": "CO2",
    "二氧化硫": "SO2",
    "氨气": "NH3",
    "氨水": "NH3",
    "淀粉": "starch",
}

STATE_RE = re.compile(r"\((aq|s|l|g)\)$", re.IGNORECASE)
ARROW_RE = re.compile(r"(<=>|⇌|--?>|=>|→|=)")
GROUP_RE = re.compile(r"\(([A-Za-z0-9]+)\)(\d*)")
ELEMENT_RE = re.compile(r"([A-Z][a-z]?)(\d*)")
SPECIES_RE = re.compile(r"^\s*(\d+)?\s*(.*)$")
SUBSCRIPT_DIGITS = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
SUPERSCRIPT_SIGNS = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻", "0123456789+-")
UNICODE_SUPERSCRIPT_CHARGE_RE = re.compile(r"(?<=[A-Za-z0-9)\]₀₁₂₃₄₅₆₇₈₉])([⁰¹²³⁴⁵⁶⁷⁸⁹]*[⁺⁻]|[⁺⁻][⁰¹²³⁴⁵⁶⁷⁸⁹]*)")

CONDITION_TAGS = {
    "acidic": ("acidic", "acid", "酸性", "强酸", "稀酸", "浓酸"),
    "alkaline": ("alkaline", "basic", "base", "alkali", "碱性", "强碱", "弱碱", "碱式"),
    "neutral": ("neutral", "中性"),
    "excess": ("excess", "excessive", "过量", "足量"),
    "small_amount": ("small amount", "少量", "微量"),
    "dilute": ("dilute", "稀", "稀溶液"),
    "concentrated": ("concentrated", "浓", "浓溶液"),
    "heated": ("heat", "heated", "heating", "加热", "微热", "水浴"),
    "light": ("light", "hv", "光照"),
    "ventilated": ("ventilated", "通风", "通风橱"),
}

ANNOTATION_LABEL_VALUE_DISPLAY = {
    ("condition", "acidic"): "酸性条件",
    ("condition", "acid"): "酸性条件",
    ("condition", "alkaline"): "碱性条件",
    ("condition", "basic"): "碱性条件",
    ("condition", "neutral"): "中性条件",
    ("condition", "heated"): "加热条件",
    ("condition", "heat"): "加热条件",
    ("condition", "light"): "光照条件",
    ("condition", "concentrated"): "浓溶液条件",
    ("condition", "dilute"): "稀溶液条件",
    ("medium", "acidic"): "酸性介质",
    ("medium", "alkaline"): "碱性介质",
    ("medium", "basic"): "碱性介质",
    ("medium", "neutral"): "中性介质",
    ("amount", "excess"): "过量",
    ("amount", "small amount"): "少量",
}

CHINESE_ANNOTATION_PREFIX_RE = re.compile(r"^(?:补充说明|说明|备注|注)\s*[:：]\s*")
ENGLISH_ANNOTATION_LABEL_RE = re.compile(r"^(?P<label>[A-Za-z][A-Za-z _-]*)\s*[:：]\s*(?P<value>.+)$")


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _dump_model(value: Any) -> dict[str, Any]:
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return dict(value or {})


def _unique(values: list[str]) -> list[str]:
    seen: set[str] = set()
    results: list[str] = []
    for value in values:
        text_value = _clean(value)
        if text_value and text_value not in seen:
            seen.add(text_value)
            results.append(text_value)
    return results


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def _teacher_warning(message: str) -> str:
    return message


def _convert_superscript_charge(match: re.Match[str]) -> str:
    value = match.group(1)
    converted = value.translate(SUPERSCRIPT_SIGNS)
    return f"^{converted}"


def _normalize_unicode_charge_notation(value: str) -> str:
    return UNICODE_SUPERSCRIPT_CHARGE_RE.sub(_convert_superscript_charge, value)


def _normalize_compact_charge_notation(value: str) -> str:
    if not value or value[-1] not in "+-" or re.search(r"\^\{?[0-9+-]+\}?$", value):
        return value
    sign = value[-1]
    body = value[:-1]
    if not body:
        return value
    digit_match = re.search(r"(\d+)$", body)
    if not digit_match:
        return f"{body}^{sign}"
    digits = digit_match.group(1)
    prefix = body[: digit_match.start()]
    if len(digits) >= 2:
        return f"{prefix}{digits[:-1]}^{digits[-1]}{sign}"
    if re.fullmatch(r"[A-Za-z]{1,2}", prefix or ""):
        return f"{prefix}^{digits}{sign}"
    return f"{body}^{sign}"


def _split_inline_annotation(raw_text: str) -> tuple[str, str]:
    if INLINE_ANNOTATION_DELIMITER not in raw_text:
        return raw_text.strip(), ""
    equation_core, annotation_text = raw_text.split(INLINE_ANNOTATION_DELIMITER, 1)
    return equation_core.strip(), _normalize_inline_annotation_text(annotation_text)


def _normalize_inline_annotation_segment(value: str) -> str:
    text = _clean(value)
    previous = None
    while text and previous != text:
        previous = text
        text = CHINESE_ANNOTATION_PREFIX_RE.sub("", text).strip()
    match = ENGLISH_ANNOTATION_LABEL_RE.match(text)
    if not match:
        return text
    label = match.group("label").strip().replace("_", " ").replace("-", " ").lower()
    value_text = match.group("value").strip()
    normalized_value = value_text.lower()
    mapped = ANNOTATION_LABEL_VALUE_DISPLAY.get((label, normalized_value))
    if mapped:
        return mapped
    if label in {"note", "notes", "comment", "annotation"}:
        return value_text
    if label == "condition":
        return f"条件：{value_text}"
    if label == "medium":
        return f"介质：{value_text}"
    if label == "amount":
        return f"用量：{value_text}"
    return text


def _normalize_inline_annotation_text(annotation_text: Any) -> str:
    text = _clean(annotation_text)
    if not text:
        return ""
    segments = [_normalize_inline_annotation_segment(segment) for segment in re.split(r"\s*[;；]\s*", text)]
    return "；".join(segment for segment in segments if segment)


def reaction_row_display_text(row: dict[str, Any]) -> str:
    core = _clean(row.get("canonical_display") or row.get("equation_core") or row.get("raw_text"))
    annotation = _clean(row.get("annotation_text"))
    if annotation and core:
        return f"{core} {INLINE_ANNOTATION_DELIMITER} {annotation}"
    return core


def _annotation_condition_tags(annotation_text: str) -> list[str]:
    normalized = normalize_chemistry_text(annotation_text).lower()
    return [
        tag
        for tag, needles in CONDITION_TAGS.items()
        if any(str(needle).lower() in normalized for needle in needles)
    ]


def _annotation_formulae(annotation_text: str) -> list[str]:
    if not annotation_text:
        return []
    prepared, _, _ = _prepare_text(annotation_text)
    return _unique(extract_formulae(prepared))


def split_multiline_equations(value: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in str(value or "").splitlines():
        raw_text = line.strip()
        if raw_text:
            rows.append({"raw_text": raw_text, "row_order": len(rows) + 1})
    return rows


def equation_rows_from_inputs(rows: list[Any] | None = None, multiline_text: Any = None) -> list[dict[str, Any]]:
    multiline_rows = split_multiline_equations(multiline_text)
    if multiline_rows:
        return multiline_rows
    normalized_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows or [], start=1):
        data = _dump_model(row)
        raw_text = _clean(data.get("raw_text"))
        if raw_text:
            normalized_rows.append({"raw_text": raw_text, "row_order": data.get("row_order") or index, "metadata": data.get("metadata") or {}})
    return normalized_rows


def _replace_chinese_aliases(value: str) -> tuple[str, list[dict[str, str]], list[str]]:
    text_value = value
    mappings: list[dict[str, str]] = []
    warnings: list[str] = []
    for alias, formula in sorted(CHINESE_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        if alias not in text_value:
            continue
        text_value = text_value.replace(alias, formula)
        mappings.append({"alias": alias, "formula": formula})
        warnings.append(_teacher_warning(f"已将“{alias}”识别为 {formula}。"))
    return text_value, mappings, warnings


def _normalize_arrow(arrow: str) -> str:
    if arrow in {"<=>", "⇌"}:
        return "⇌"
    if arrow in {"->", "-->", "=>", "→"}:
        return "→"
    return "="


def _prepare_text(raw_text: str) -> tuple[str, list[dict[str, str]], list[str]]:
    text_value = _normalize_unicode_charge_notation(raw_text)
    text_value = text_value.translate(SUBSCRIPT_DIGITS).translate(SUPERSCRIPT_SIGNS)
    text_value = normalize_chemistry_text(text_value)
    text_value, alias_mappings, warnings = _replace_chinese_aliases(text_value)
    text_value = re.sub(r"\s+", " ", text_value.strip())
    text_value = re.sub(r"\s*(<=>|⇌|--?>|=>|→|=)\s*", lambda match: f" {_normalize_arrow(match.group(1))} ", text_value)
    text_value = re.sub(r"\s+", " ", text_value).strip()
    return text_value, alias_mappings, warnings


def _strip_state_and_charge(formula: str) -> str:
    value = STATE_RE.sub("", formula.strip())
    value = re.sub(r"\^\{?[0-9+-]+\}?$", "", value)
    value = re.sub(r"(?<=[A-Za-z0-9\]])[+-]$", "", value)
    return value


def _canonicalize_formula(value: str) -> tuple[str, bool, bool]:
    original = value
    state = ""
    state_match = STATE_RE.search(value.strip())
    if state_match:
        state = f"({state_match.group(1).lower()})"
        value = STATE_RE.sub("", value.strip())
    value = _normalize_compact_charge_notation(value)
    trailing_charge = ""
    charge_match = re.search(r"(\^\{?[0-9+-]+\}?|[+-])$", value)
    if charge_match and re.search(r"[A-Za-z0-9)\]]", value[: charge_match.start()]):
        trailing_charge = charge_match.group(1)
        value = value[: charge_match.start()]

    changed = False
    uncertain = False
    result: list[str] = []
    index = 0
    while index < len(value):
        char = value[index]
        if char.isalpha():
            two = value[index : index + 2]
            one = value[index]
            two_symbol = two[:1].upper() + two[1:2].lower()
            one_symbol = one.upper()
            if len(two) == 2 and two_symbol in ELEMENT_SYMBOLS:
                result.append(two_symbol)
                changed = changed or two != two_symbol
                index += 2
                continue
            if one_symbol in ELEMENT_SYMBOLS:
                result.append(one_symbol)
                changed = changed or one != one_symbol
                index += 1
                continue
            uncertain = True
            result.append(char)
            index += 1
            continue
        result.append(char)
        index += 1

    canonical = "".join(result) + trailing_charge + state
    return canonical, changed or canonical != original, uncertain


def _split_reaction(display: str) -> tuple[str, str, str] | None:
    match = ARROW_RE.search(display)
    if not match:
        return None
    left = display[: match.start()].strip()
    right = display[match.end() :].strip()
    return left, _normalize_arrow(match.group(1)), right


def _split_species(side: str) -> list[str]:
    spaced_parts = re.split(r"\s+\+\s+", side)
    if len(spaced_parts) > 1:
        return [_clean(part) for part in spaced_parts if _clean(part)]
    parts = re.split(r"(?<=[A-Za-z0-9)\]])\+(?=\d*[A-Za-z(\u4e00-\u9fff])", side)
    return [_clean(part) for part in parts if _clean(part)]


def _canonical_species(species: str) -> tuple[str, str, list[str], bool]:
    match = SPECIES_RE.match(species)
    coefficient = match.group(1) if match else ""
    body = (match.group(2) if match else species).strip()
    canonical_body, changed, uncertain = _canonicalize_formula(body)
    warnings: list[str] = []
    if changed:
        warnings.append(_teacher_warning(f"已将 {body} 识别为 {canonical_body}。"))
    if uncertain:
        warnings.append(_teacher_warning(f"{body} 中有无法确认的元素符号，请检查大小写或写法。"))
    display = f"{coefficient} {canonical_body}".strip() if coefficient else canonical_body
    return display, canonical_body, warnings, uncertain


def _canonical_side(side: str) -> tuple[str, list[str], list[str], bool]:
    displays: list[str] = []
    formulae: list[str] = []
    warnings: list[str] = []
    uncertain = False
    for species in _split_species(side):
        display, formula, species_warnings, species_uncertain = _canonical_species(species)
        displays.append(display)
        formulae.append(formula)
        warnings.extend(species_warnings)
        uncertain = uncertain or species_uncertain
    return " + ".join(displays), formulae, warnings, uncertain


def _mhchem_body(display: str, reversible: bool) -> str:
    body = display.replace("⇌", "<=>").replace("→", "->")
    if not reversible:
        body = body.replace("=", "->")
    body = body.replace("↑", " ^").replace("↓", " v")
    return re.sub(r"\s+", " ", body).strip()


def _species_formula(species: str) -> str:
    match = SPECIES_RE.match(species)
    body = match.group(2) if match else species
    formula = _strip_state_and_charge(body)
    formulae = extract_formulae(formula)
    return formulae[0] if formulae else ""


def _formula_counts(formula: str, coefficient: int = 1) -> Counter[str]:
    text_value = _strip_state_and_charge(formula)
    counts: Counter[str] = Counter()
    for group, multiplier_text in GROUP_RE.findall(text_value):
        multiplier = int(multiplier_text or "1")
        for element, count_text in ELEMENT_RE.findall(group):
            counts[element] += int(count_text or "1") * multiplier * coefficient
        text_value = text_value.replace(f"({group}){multiplier_text}", "")
    for element, count_text in ELEMENT_RE.findall(text_value):
        counts[element] += int(count_text or "1") * coefficient
    return counts


def _side_counts(side: str) -> Counter[str]:
    counts: Counter[str] = Counter()
    for species in _split_species(side):
        match = SPECIES_RE.match(species)
        coefficient = int(match.group(1) or "1") if match else 1
        formula = _species_formula(match.group(2) if match else species)
        if formula:
            counts.update(_formula_counts(formula, coefficient))
    return counts


def _species_without_coefficients(side: str) -> list[str]:
    species_list: list[str] = []
    for species in _split_species(side):
        match = SPECIES_RE.match(species)
        body = (match.group(2) if match else species).strip()
        if body:
            species_list.append(body)
    return species_list


def _matrix_rref(matrix: list[list[Fraction]]) -> tuple[list[list[Fraction]], list[int]]:
    rows = [row[:] for row in matrix]
    pivot_columns: list[int] = []
    row_index = 0
    column_count = len(rows[0]) if rows else 0
    for column in range(column_count):
        pivot = next((candidate for candidate in range(row_index, len(rows)) if rows[candidate][column]), None)
        if pivot is None:
            continue
        rows[row_index], rows[pivot] = rows[pivot], rows[row_index]
        factor = rows[row_index][column]
        rows[row_index] = [value / factor for value in rows[row_index]]
        for other in range(len(rows)):
            if other == row_index or not rows[other][column]:
                continue
            scale = rows[other][column]
            rows[other] = [value - scale * rows[row_index][idx] for idx, value in enumerate(rows[other])]
        pivot_columns.append(column)
        row_index += 1
        if row_index == len(rows):
            break
    return rows, pivot_columns


def _integer_nullspace_vector(matrix: list[list[int]]) -> list[int] | None:
    if not matrix or not matrix[0]:
        return None
    fractions = [[Fraction(value) for value in row] for row in matrix]
    rref, pivots = _matrix_rref(fractions)
    column_count = len(matrix[0])
    free_columns = [column for column in range(column_count) if column not in pivots]
    if not free_columns:
        return None
    solution = [Fraction(0) for _ in range(column_count)]
    free_column = free_columns[-1]
    solution[free_column] = Fraction(1)
    for pivot_row, pivot_column in enumerate(pivots):
        solution[pivot_column] = -sum(rref[pivot_row][column] * solution[column] for column in free_columns)
    denominators = [value.denominator for value in solution if value]
    lcm = 1
    for denominator in denominators:
        lcm = lcm * denominator // math.gcd(lcm, denominator)
    integers = [int(value * lcm) for value in solution]
    if all(value <= 0 for value in integers):
        integers = [-value for value in integers]
    if any(value <= 0 for value in integers):
        return None
    divisor = 0
    for value in integers:
        divisor = math.gcd(divisor, abs(value))
    if divisor > 1:
        integers = [value // divisor for value in integers]
    if max(integers, default=0) > 24:
        return None
    return integers


def _format_balanced_side(species: list[str], coefficients: list[int]) -> str:
    parts: list[str] = []
    for formula, coefficient in zip(species, coefficients, strict=False):
        parts.append(formula if coefficient == 1 else f"{coefficient} {formula}")
    return " + ".join(parts)


def _balance_suggestion(left: str, right: str, arrow: str) -> str | None:
    left_species = _species_without_coefficients(left)
    right_species = _species_without_coefficients(right)
    all_species = [*left_species, *right_species]
    if len(all_species) < 2 or len(all_species) > 8:
        return None
    species_counts = [_formula_counts(species) for species in all_species]
    if any(not counts for counts in species_counts):
        return None
    elements = sorted({element for counts in species_counts for element in counts})
    matrix: list[list[int]] = []
    for element in elements:
        matrix.append(
            [
                *(counts.get(element, 0) for counts in species_counts[: len(left_species)]),
                *(-counts.get(element, 0) for counts in species_counts[len(left_species) :]),
            ]
        )
    coefficients = _integer_nullspace_vector(matrix)
    if not coefficients:
        return None
    left_text = _format_balanced_side(left_species, coefficients[: len(left_species)])
    right_text = _format_balanced_side(right_species, coefficients[len(left_species) :])
    return f"{left_text} {arrow} {right_text}"


def normalize_reaction_equation(row: Any, *, row_order: int) -> dict[str, Any]:
    data = _dump_model(row)
    raw_text = _clean(data.get("raw_text"))
    equation_core, annotation_text = _split_inline_annotation(raw_text)
    annotation_formulae = _annotation_formulae(annotation_text)
    annotation_aliases = expand_formula_aliases(annotation_formulae)
    condition_tags = _annotation_condition_tags(annotation_text)
    metadata = data.get("metadata") if isinstance(data.get("metadata"), dict) else {}
    warnings: list[str] = []
    errors: list[str] = []
    corrections: list[str] = []
    alias_mappings: list[dict[str, str]] = []
    display = ""
    reactants: list[str] = []
    products: list[str] = []
    formulae: list[str] = []
    aliases: list[str] = []
    reaction_features: list[str] = []
    canonical_mhchem: str | None = None
    suggested_display: str | None = None
    suggested_mhchem: str | None = None
    suggestion_reason: str | None = None
    participants: dict[str, Any] = {}

    if not raw_text:
        errors.append("请先输入反应式。")
    else:
        prepared, alias_mappings, _alias_warnings = _prepare_text(equation_core)
        split = _split_reaction(prepared)
        if not split:
            display = equation_core
            formulae = _unique(extract_formulae(equation_core))
            aliases = expand_formula_aliases(formulae)
            reaction_features = extract_reaction_features(equation_core, equation_core)
        else:
            left, arrow, right = split
            canonical_left, reactant_species, left_warnings, left_uncertain = _canonical_side(left)
            canonical_right, product_species, right_warnings, right_uncertain = _canonical_side(right)
            display_arrow = "⇌" if arrow == "⇌" else "→" if arrow in {"=", "→"} else arrow
            display = f"{canonical_left} {display_arrow} {canonical_right}"
            if prepared != display:
                corrections.append(_teacher_warning(f"已规范为：{display}"))
            reactants = _unique(_species_formula(species) for species in reactant_species)
            products = _unique(_species_formula(species) for species in product_species)
            formulae = _unique([*reactants, *products, *extract_formulae(display)])
            aliases = expand_formula_aliases(formulae)
            reaction_features = extract_reaction_features(display, equation_core)
            participants = {"reactants": reactants, "products": products, "all": formulae, "arrow": display_arrow}
            canonical_mhchem = f"\\ce{{{_mhchem_body(display, display_arrow == '⇌')}}}"

    validation_status = "invalid" if errors else "warning" if warnings else "valid"
    if validation_status == "invalid":
        formulae = []
        aliases = []
        reactants = []
        products = []
        participants = {}
        reaction_features = []
        canonical_mhchem = None
        suggested_display = None
        suggested_mhchem = None
        suggestion_reason = None

    metadata = {
        **metadata,
        "alias_mappings": alias_mappings,
        "corrections": corrections,
        "equation_core": equation_core,
        "annotation_text": annotation_text,
        "annotation_formulae": annotation_formulae,
        "annotation_aliases": annotation_aliases,
        "condition_tags": condition_tags,
    }
    plain_search_text = " ".join(
        part
        for part in [
            display if validation_status != "invalid" else equation_core,
            annotation_text,
            " ".join(annotation_formulae),
            " ".join(annotation_aliases),
            " ".join(condition_tags),
        ]
        if part
    )

    def serialized_id(value: Any) -> str | None:
        return str(value) if value is not None else None

    return {
        "id": serialized_id(data.get("id")),
        "node_id": serialized_id(data.get("node_id")),
        "canonical_point_id": serialized_id(data.get("canonical_point_id")),
        "row_order": int(data.get("row_order") or row_order),
        "raw_text": raw_text,
        "equation_core": equation_core,
        "annotation_text": annotation_text,
        "annotation_formulae": annotation_formulae,
        "annotation_aliases": annotation_aliases,
        "condition_tags": condition_tags,
        "canonical_display": display if validation_status != "invalid" else "",
        "canonical_mhchem": canonical_mhchem,
        "plain_search_text": plain_search_text,
        "formulae": formulae,
        "aliases": aliases,
        "reactants": reactants,
        "products": products,
        "participants": participants,
        "reaction_features": reaction_features,
        "validation_status": validation_status,
        "warnings": warnings,
        "errors": errors,
        "parser_version": PARSER_VERSION,
        "migrated_from_principle_equation": bool(data.get("migrated_from_principle_equation")),
        "metadata": metadata,
        "suggested_display": suggested_display,
        "suggested_mhchem": suggested_mhchem,
        "suggestion_reason": suggestion_reason,
        "corrections": corrections,
    }


def normalize_reaction_equations(rows: list[Any]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        data = _dump_model(row)
        if not _clean(data.get("raw_text")):
            continue
        normalized.append(normalize_reaction_equation(data, row_order=index))
    return normalized


def _assist_draft_from_normalized(
    row: dict[str, Any],
    *,
    source: str,
    rationale: str,
    row_order: int | None = None,
    supplemental: bool = False,
) -> dict[str, Any] | None:
    display_text = _clean(row.get("canonical_display") or row.get("equation_core") or row.get("raw_text"))
    replacement_text = reaction_row_display_text({**row, "canonical_display": display_text})
    if not display_text or row.get("validation_status") == "invalid":
        return None
    canonical_mhchem = row.get("canonical_mhchem")
    return {
        "draft_text": replacement_text,
        "replacement_text": replacement_text,
        "canonical_display": display_text,
        "canonical_mhchem": canonical_mhchem,
        "annotation_text": row.get("annotation_text") or "",
        "annotation_formulae": row.get("annotation_formulae") or [],
        "condition_tags": row.get("condition_tags") or [],
        "validation_status": row.get("validation_status") or "warning",
        "warnings": row.get("warnings") or [],
        "errors": row.get("errors") or [],
        "formulae": row.get("formulae") or [],
        "source": source,
        "rationale": rationale,
        "row_order": row_order,
        "supplemental": supplemental or row_order is None,
    }


def _ai_settings_ready() -> tuple[Any | None, str | None]:
    settings = effective_ai_settings(get_settings())
    provider = settings.agent_llm_provider
    api_key = settings.agent_llm_api_key or os.getenv("OPENAI_API_KEY", "")
    model = settings.agent_llm_model or os.getenv("OPENAI_MODEL", "")
    if provider not in {"openai", "openai_compatible"}:
        return None, "AI 反应式校对尚未接入；暂时无法生成 AI 建议。"
    if not api_key or not model:
        return None, "AI 接入缺少模型或密钥；暂时无法生成 AI 建议。"
    return settings, None


def _single_leading_system_message(messages: list[dict[str, str]]) -> list[dict[str, str]]:
    system_parts = [message["content"] for message in messages if message.get("role") == "system" and message.get("content")]
    non_system_messages = [message for message in messages if message.get("role") != "system"]
    if not system_parts:
        return non_system_messages
    return [{"role": "system", "content": "\n\n".join(system_parts)}, *non_system_messages]


def _equation_ai_prompt(payload: Any, normalized_rows: list[dict[str, Any]]) -> list[dict[str, str]]:
    point_context = {
        "point_title": _clean(getattr(payload, "point_title", None)),
        "catalog_path_text": _clean(getattr(payload, "catalog_path_text", None)),
        "phenomenon_explanation": _clean(getattr(payload, "phenomenon_explanation", None)),
        "safety_note": _clean(getattr(payload, "safety_note", None)),
    }
    input_rows = [
        {
            "row_order": row.get("row_order"),
            "raw_text": row.get("raw_text"),
            "equation_core": row.get("equation_core"),
            "annotation_text": row.get("annotation_text"),
        }
        for row in normalized_rows
    ]
    messages = [
        {
            "role": "system",
            "content": (
                EQUATION_ANNOTATION_REWRITE_SKILL
                + "\n\n"
                "You are a high-school chemistry experiment reaction-equation reviewer. "
                "Use only the teacher's current input rows and point context. Do not mention or rely on any local pre-check. "
                "Return JSON only, no Markdown. Shape: {\"drafts\":[{\"row_order\":1,\"draft_text\":\"...\",\"rationale\":\"...\"}]}. "
                "draft_text must be a single-line reaction equation and may use ->, →, <=>, ⇌, ↑, or ↓. "
                "Only return a draft when you are confident it should replace or supplement the teacher input."
            ),
        },
        {
            "role": "system",
            "content": (
                "Inline annotation rule: keep exactly one reaction equation per non-empty line. "
                "When a condition, excess/small-amount note, acid/base medium, or reagent-source explanation is needed, "
                "append it after // on the same line. If raw_text already has a // suffix and only the equation core is corrected, "
                "preserve the existing suffix exactly. The // suffix must be natural Chinese supplemental explanation, "
                "not English machine labels such as note:, condition:, amount:, or medium:."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                {
                    "mode": _clean(getattr(payload, "mode", "suggest")),
                    "point_context": point_context,
                    "input_rows": input_rows,
                    "current_multiline_text": _clean(getattr(payload, "multiline_text", None)),
                },
                ensure_ascii=False,
            ),
        },
    ]
    return _single_leading_system_message(messages)


def _sanitize_ai_drafts(raw_drafts: Any, normalized_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(raw_drafts, list):
        return []
    valid_orders = {int(row["row_order"]) for row in normalized_rows if row.get("row_order")}
    rows_by_order = {int(row["row_order"]): row for row in normalized_rows if row.get("row_order")}
    drafts: list[dict[str, Any]] = []
    seen: set[tuple[int | None, str]] = set()
    for item in raw_drafts[:8]:
        if not isinstance(item, dict):
            continue
        draft_text = _clean(item.get("draft_text"))
        if not draft_text or "\n" in draft_text or len(draft_text) > 500:
            continue
        row_order_raw = item.get("row_order")
        try:
            row_order = int(row_order_raw) if row_order_raw is not None else None
        except (TypeError, ValueError):
            row_order = None
        if row_order is not None and row_order not in valid_orders:
            row_order = None
        current_row = rows_by_order.get(row_order) if row_order is not None else None
        current_annotation = _clean((current_row or {}).get("annotation_text"))
        if current_annotation and INLINE_ANNOTATION_DELIMITER not in draft_text:
            draft_text = f"{draft_text} {INLINE_ANNOTATION_DELIMITER} {current_annotation}"
        normalized = normalize_reaction_equation(
            {"raw_text": draft_text, "row_order": row_order},
            row_order=row_order or len(normalized_rows) + len(drafts) + 1,
        )
        normalized_candidate = _assist_draft_from_normalized(
            normalized,
            source="ai",
            rationale=_clean(item.get("rationale"))[:220] or "AI 已根据点位内容和当前输入给出候选反应式，采用前请核对。",
            row_order=row_order,
            supplemental=row_order is None,
        )
        if not normalized_candidate:
            continue
        key = (row_order, normalized_candidate["canonical_display"])
        if key in seen:
            continue
        seen.add(key)
        drafts.append(normalized_candidate)
    return drafts


def _try_ai_equation_drafts(payload: Any, normalized_rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], str | None]:
    settings, unavailable_reason = _ai_settings_ready()
    if settings is None:
        return [], unavailable_reason
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.agent_llm_api_key or os.getenv("OPENAI_API_KEY"), base_url=settings.agent_llm_base_url or None)
        response = client.chat.completions.create(
            model=settings.agent_llm_model or os.getenv("OPENAI_MODEL", ""),
            response_format={"type": "json_object"},
            messages=_equation_ai_prompt(payload, normalized_rows),
        )
        content = response.choices[0].message.content or "{}"
        data = json.loads(content)
        drafts = _sanitize_ai_drafts(data.get("drafts"), normalized_rows)
        if drafts:
            return drafts, "AI 已根据当前输入生成建议；采用后会重新渲染预览。"
        return [], "AI 没有发现需要替换的反应式。"
    except Exception as exc:
        return [], f"AI 校对暂时失败：{str(exc)[:160]}。"


def assist_reaction_equations(payload: Any) -> dict[str, Any]:
    rows = equation_rows_from_inputs(getattr(payload, "equations", None), getattr(payload, "multiline_text", None))
    normalized_rows = normalize_reaction_equations(rows)
    ai_drafts, ai_reason = _try_ai_equation_drafts(payload, normalized_rows)
    if ai_drafts:
        return {"available": True, "reason": ai_reason, "drafts": ai_drafts}
    return {
        "available": False,
        "reason": ai_reason or "AI 暂不可用；请先输入反应式，或补充点位现象后再试。",
        "drafts": [],
    }


def _canonical_point_id_for_node(session: Any, node_id: str) -> str | None:
    row = (
        session.execute(
            text("SELECT canonical_point_id FROM experiment_catalog_nodes WHERE id = :node_id"),
            {"node_id": node_id},
        )
        .mappings()
        .first()
    )
    return str(row["canonical_point_id"]) if row and row.get("canonical_point_id") else None


def list_reaction_equations(session: Any, node_id: str, *, canonical_point_id: str | None = None) -> list[dict[str, Any]]:
    canonical_point_id = canonical_point_id or _canonical_point_id_for_node(session, node_id)
    rows = (
        session.execute(
            text(
                """
                SELECT id, node_id, canonical_point_id, row_order, raw_text, canonical_display, canonical_mhchem,
                       plain_search_text, formulae, aliases, reactants, products, participants,
                       reaction_features, validation_status, warnings, errors, parser_version,
                       migrated_from_principle_equation, metadata
                FROM experiment_catalog_point_reaction_equations
                WHERE (CAST(:canonical_point_id AS text) IS NOT NULL AND canonical_point_id = CAST(:canonical_point_id AS text))
                   OR node_id = :node_id
                ORDER BY row_order, created_at, id
                """
            ),
            {"node_id": node_id, "canonical_point_id": canonical_point_id},
        )
        .mappings()
        .all()
    )
    return [normalize_reaction_equation(dict(row), row_order=int(row["row_order"] or index)) for index, row in enumerate(rows, start=1)]


def replace_reaction_equations(
    session: Any,
    *,
    node_id: str,
    equations: list[dict[str, Any]],
    canonical_point_id: str | None = None,
) -> None:
    canonical_point_id = canonical_point_id or _canonical_point_id_for_node(session, node_id)
    session.execute(
        text(
            """
            DELETE FROM experiment_catalog_point_reaction_equations
            WHERE (CAST(:canonical_point_id AS text) IS NOT NULL AND canonical_point_id = CAST(:canonical_point_id AS text))
               OR node_id = :node_id
            """
        ),
        {"node_id": node_id, "canonical_point_id": canonical_point_id},
    )
    for index, equation in enumerate(equations, start=1):
        session.execute(
            text(
                """
                INSERT INTO experiment_catalog_point_reaction_equations (
                  node_id, canonical_point_id, row_order, raw_text, canonical_display, canonical_mhchem, plain_search_text,
                  formulae, aliases, reactants, products, participants, reaction_features,
                  validation_status, warnings, errors, parser_version, migrated_from_principle_equation,
                  metadata, updated_at
                )
                VALUES (
                  :node_id, :canonical_point_id, :row_order, :raw_text, :canonical_display, :canonical_mhchem, :plain_search_text,
                  CAST(:formulae AS jsonb), CAST(:aliases AS jsonb), CAST(:reactants AS jsonb),
                  CAST(:products AS jsonb), CAST(:participants AS jsonb), CAST(:reaction_features AS jsonb),
                  :validation_status, CAST(:warnings AS jsonb), CAST(:errors AS jsonb), :parser_version,
                  :migrated_from_principle_equation, CAST(:metadata AS jsonb), now()
                )
                """
            ),
            {
                "node_id": node_id,
                "canonical_point_id": canonical_point_id,
                "row_order": int(equation.get("row_order") or index),
                "raw_text": equation.get("raw_text") or "",
                "canonical_display": equation.get("canonical_display") or None,
                "canonical_mhchem": equation.get("canonical_mhchem") or None,
                "plain_search_text": equation.get("plain_search_text") or "",
                "formulae": _json(equation.get("formulae") or []),
                "aliases": _json(equation.get("aliases") or []),
                "reactants": _json(equation.get("reactants") or []),
                "products": _json(equation.get("products") or []),
                "participants": _json(equation.get("participants") or {}),
                "reaction_features": _json(equation.get("reaction_features") or []),
                "validation_status": equation.get("validation_status") or "warning",
                "warnings": _json(equation.get("warnings") or []),
                "errors": _json(equation.get("errors") or []),
                "parser_version": equation.get("parser_version") or PARSER_VERSION,
                "migrated_from_principle_equation": bool(equation.get("migrated_from_principle_equation")),
                "metadata": _json(equation.get("metadata") or {}),
            },
        )


def active_reaction_equations(content: dict[str, Any] | None) -> list[dict[str, Any]]:
    if not content or content.get("principle_mode") != "equation":
        return []
    return [row for row in content.get("reaction_equations") or [] if row.get("validation_status") != "invalid"]


def reaction_principle_text(content: dict[str, Any] | None, *, include_annotations: bool = True) -> str:
    rows = active_reaction_equations(content)
    parts = [
        reaction_row_display_text(row) if include_annotations else _clean(row.get("canonical_display") or row.get("equation_core") or row.get("raw_text"))
        for row in rows
    ]
    parts = [part for part in parts if part]
    if parts:
        return "\n".join(parts)
    return _clean((content or {}).get("principle_equation"))


def reaction_derived_terms(content: dict[str, Any] | None) -> dict[str, list[str]]:
    rows = active_reaction_equations(content)
    equation_rows = _unique(
        [
            value
            for row in rows
            for value in (
                reaction_row_display_text(row),
                row.get("plain_search_text"),
                row.get("canonical_display"),
                row.get("raw_text"),
            )
            if value
        ]
    )
    reactants = _unique([formula for row in rows for formula in row.get("reactants", [])])
    products = _unique([formula for row in rows for formula in row.get("products", [])])
    participant_values: list[str] = []
    equation_formula_pairs: list[str] = []
    for row in rows:
        participants = row.get("participants")
        if isinstance(participants, dict):
            participant_values.extend(str(item) for item in participants.get("all", []) if item)
        participant_values.extend(str(item) for item in row.get("reactants", []) if item)
        participant_values.extend(str(item) for item in row.get("products", []) if item)
        equation_formula_pairs.extend(formula_pair_terms(row.get("formulae", [])))
    return {
        "formulae": _unique([formula for row in rows for formula in row.get("formulae", [])]),
        "aliases": _unique([alias for row in rows for alias in row.get("aliases", [])]),
        "reactants": reactants,
        "products": products,
        "participants": _unique(participant_values),
        "equation_formula_pairs": _unique(equation_formula_pairs),
        "equation_rows": equation_rows,
        "reaction_features": _unique([feature for row in rows for feature in row.get("reaction_features", [])]),
        "annotation_formulae": _unique([formula for row in rows for formula in row.get("annotation_formulae", [])]),
        "annotation_aliases": _unique([alias for row in rows for alias in row.get("annotation_aliases", [])]),
        "condition_tags": _unique([tag for row in rows for tag in row.get("condition_tags", [])]),
    }
