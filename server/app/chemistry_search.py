from __future__ import annotations

import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from server.app.infrastructure.settings import ROOT


ALIAS_PATH = ROOT / "data" / "seed" / "search" / "chemical_aliases.json"
VOCABULARY_PATH = ROOT / "data" / "seed" / "search" / "chemistry_vocabulary.json"
STOPWORD_PATH = ROOT / "data" / "seed" / "search" / "chemical_stopwords.txt"

UNICODE_SUPERSCRIPT_CHARGE_RE = re.compile(
    r"(?<=[A-Za-z0-9)\]])([⁰¹²³⁴⁵⁶⁷⁸⁹]*[⁺⁻]|[⁺⁻][⁰¹²³⁴⁵⁶⁷⁸⁹]*)"
)
CHARGE_SUFFIX_RE = re.compile(r"(\^\{?[0-9+-]+\}?|(?<=[A-Za-z0-9)\]])[+-])$")
COEFFICIENT_RE = re.compile(r"^\d+")
STATE_MARKER_RE = re.compile(r"\((?:aq|s|l|g)\)", re.IGNORECASE)

SUBSCRIPT_MAP = str.maketrans("₀₁₂₃₄₅₆₇₈₉", "0123456789")
SUPERSCRIPT_MAP = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻", "0123456789+-")
FULLWIDTH_MAP = str.maketrans("０１２３４５６７８９＋－＝（）；，", "0123456789+-=();,")
ARROW_VARIANTS = {
    "==": "=",
    "->": "→",
    "-->": "→",
    "=>": "→",
    "⟶": "→",
    "↔": "⇌",
    "⇄": "⇌",
}

FORMULA_RE = re.compile(
    r"(?<![A-Za-z0-9])"
    r"(?:[A-Z][a-z]?\d*|\([A-Z][a-z]?\d*\)\d*){1,10}"
    r"(?:[·.]\d*(?:[A-Z][a-z]?\d*){1,4})?"
    r"(?:[+-]\d*|[²³]?[+-])?"
    r"(?![a-z])"
)

VOCABULARY_TERM_CATEGORIES = (
    "reagent_aliases",
    "condition_terms",
    "phenomenon_terms",
    "property_terms",
)


def _unique(values: list[Any]) -> list[str]:
    results: list[str] = []
    seen: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if not text or text in seen:
            continue
        results.append(text)
        seen.add(text)
    return results


def normalize_chemistry_text(value: Any) -> str:
    text = str(value or "").strip()
    text = UNICODE_SUPERSCRIPT_CHARGE_RE.sub(
        lambda match: f"^{match.group(1).translate(SUPERSCRIPT_MAP)}",
        text,
    )
    text = text.translate(SUBSCRIPT_MAP).translate(SUPERSCRIPT_MAP).translate(FULLWIDTH_MAP)
    for source, target in ARROW_VARIANTS.items():
        text = text.replace(source, target)
    return re.sub(r"\s+", " ", text)


def normalize_formula(value: Any) -> str:
    text = normalize_chemistry_text(value)
    text = STATE_MARKER_RE.sub("", text)
    text = text.replace("·", "").replace(".", "")
    text = CHARGE_SUFFIX_RE.sub("", text)
    text = re.sub(r"[^A-Za-z0-9]", "", text)
    text = COEFFICIENT_RE.sub("", text)
    return text.upper()


@lru_cache(maxsize=1)
def chemistry_vocabulary() -> dict[str, Any]:
    if not VOCABULARY_PATH.exists():
        return {"version": "missing", "categories": {}}
    raw = json.loads(VOCABULARY_PATH.read_text(encoding="utf-8-sig"))
    categories = raw.get("categories")
    if not isinstance(categories, dict):
        categories = {}
    return {"version": str(raw.get("version") or "unknown"), "categories": categories}


@lru_cache(maxsize=1)
def chemical_aliases() -> dict[str, list[str]]:
    strict = chemistry_vocabulary().get("categories", {}).get("strict_chemical_synonyms")
    if isinstance(strict, dict) and strict:
        return {
            normalize_formula(key): _unique([key, *values])
            for key, values in strict.items()
            if isinstance(values, list)
        }
    if not ALIAS_PATH.exists():
        return {}
    raw = json.loads(ALIAS_PATH.read_text(encoding="utf-8-sig"))
    return {
        normalize_formula(key): _unique([key, *values])
        for key, values in raw.items()
        if isinstance(values, list)
    }


@lru_cache(maxsize=1)
def domain_stopwords() -> list[str]:
    if not STOPWORD_PATH.exists():
        return []
    return [line.strip() for line in STOPWORD_PATH.read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def _vocabulary_terms(category: str) -> list[str]:
    value = chemistry_vocabulary().get("categories", {}).get(category)
    if isinstance(value, list):
        return _unique(value)
    if isinstance(value, dict):
        terms: list[str] = []
        for key, aliases in value.items():
            terms.append(str(key))
            if isinstance(aliases, list):
                terms.extend(str(alias) for alias in aliases)
        return _unique(terms)
    return []


def _normalized_contains(haystack: str, needle: str) -> bool:
    normalized_needle = normalize_chemistry_text(needle).lower()
    if not normalized_needle:
        return False
    return normalized_needle in haystack


def extract_formulae(value: Any) -> list[str]:
    text = normalize_chemistry_text(value)
    results: list[str] = []
    seen: set[str] = set()
    for match in FORMULA_RE.finditer(text):
        formula = normalize_formula(match.group(0))
        if not formula or formula in seen:
            continue
        seen.add(formula)
        results.append(formula)
    return results


def formulae_from_strict_aliases(value: Any) -> list[str]:
    text = normalize_chemistry_text(value)
    text_lower = text.lower()
    formulae = set(extract_formulae(text))
    matches = [formula for formula in formulae if formula in chemical_aliases()]
    seen: set[str] = set(matches)
    accepted_spans: list[tuple[int, int]] = []
    alias_entries: list[tuple[str, str]] = []
    for canonical, aliases in chemical_aliases().items():
        for alias in aliases:
            alias_entries.append((canonical, normalize_chemistry_text(alias)))
    alias_entries.sort(key=lambda item: len(item[1]), reverse=True)
    for canonical, alias in alias_entries:
        if len(alias) < 2 and normalize_formula(alias) != canonical:
            continue
        if normalize_formula(alias) == canonical and re.fullmatch(r"[A-Za-z0-9().·+-]+", alias):
            continue
        alias_lower = alias.lower()
        start = text_lower.find(alias_lower)
        if start < 0:
            continue
        end = start + len(alias_lower)
        if any(start >= span_start and end <= span_end for span_start, span_end in accepted_spans):
            continue
        accepted_spans.append((start, end))
        if canonical not in seen:
            matches.append(canonical)
            seen.add(canonical)
    return matches


def expand_formula_aliases(formulae: list[str]) -> list[str]:
    aliases = chemical_aliases()
    values: list[str] = []
    seen: set[str] = set()
    for formula in formulae:
        normalized = normalize_formula(formula)
        for value in [normalized, *aliases.get(normalized, [])]:
            text = str(value or "").strip()
            if text and text not in seen:
                values.append(text)
                seen.add(text)
    return values


def formula_pair_terms(formulae: list[Any]) -> list[str]:
    normalized = sorted({normalize_formula(formula) for formula in formulae if normalize_formula(formula)})
    pairs: list[str] = []
    for left_index, left in enumerate(normalized):
        for right in normalized[left_index + 1 :]:
            pairs.append(f"{left}|{right}")
    return pairs


def expand_query_strict_aliases(query: Any) -> list[str]:
    text = normalize_chemistry_text(query)
    formulae = _unique([*extract_formulae(text), *formulae_from_strict_aliases(text)])
    return expand_formula_aliases(formulae)


def extract_vocabulary_terms(*parts: Any, category: str) -> list[str]:
    text = normalize_chemistry_text(" ".join(str(part or "") for part in parts)).lower()
    matches: list[str] = []
    seen: set[str] = set()
    for term in _vocabulary_terms(category):
        if not _normalized_contains(text, term):
            continue
        if term not in seen:
            matches.append(term)
            seen.add(term)
    return matches


def extract_reaction_features(*parts: Any) -> list[str]:
    text = normalize_chemistry_text(" ".join(str(part or "") for part in parts))
    formulae = set(extract_formulae(text))
    feature_checks = [
        ("gas_generation", ["↑", "气体", "气泡", "刺激性气体", "gas"]),
        ("precipitation", ["↓", "沉淀", "浑浊", "白色沉淀", "黄色沉淀", "precipitation", "precipitate"]),
        ("heating", ["△", "Δ", "加热", "水浴", "热水", "酒精灯", "高温"]),
        ("color_change", ["褪色", "变色", "颜色", "紫色", "橙色", "红棕色", "蓝色", "黄色"]),
        ("phase_separation", ["分层", "有机层", "水层", "CCl4", "四氯化碳层"]),
        ("redox", ["氧化还原", "氧化性", "还原性", "置换"]),
    ]
    features: list[str] = []
    for feature, needles in feature_checks:
        if any(needle in text for needle in needles):
            features.append(feature)
    if formulae & {"SO2", "CO2", "H2", "NH3", "O2", "CL2"} and "gas_generation" not in features:
        features.append("gas_generation")
    return features


def chemistry_terms_for_document(*parts: Any) -> dict[str, list[str]]:
    text = "\n".join(str(part or "") for part in parts)
    formulae = _unique([*extract_formulae(text), *formulae_from_strict_aliases(text)])
    aliases = _unique([*expand_formula_aliases(formulae), *expand_query_strict_aliases(text)])
    vocabulary_matches = {
        category: extract_vocabulary_terms(text, category=category)
        for category in VOCABULARY_TERM_CATEGORIES
    }
    return {
        "formulae": formulae,
        "aliases": aliases,
        "strict_aliases": aliases,
        "reagent_aliases": vocabulary_matches["reagent_aliases"],
        "condition_tags": vocabulary_matches["condition_terms"],
        "phenomenon_tags": vocabulary_matches["phenomenon_terms"],
        "property_tags": vocabulary_matches["property_terms"],
        "reaction_features": extract_reaction_features(text),
        "stopwords": domain_stopwords(),
    }


def chemistry_query_terms(query: str) -> dict[str, Any]:
    normalized = normalize_chemistry_text(query)
    formulae = _unique([*extract_formulae(normalized), *formulae_from_strict_aliases(normalized)])
    strict_aliases = expand_formula_aliases(formulae)
    vocabulary_matches = {
        category: extract_vocabulary_terms(normalized, category=category)
        for category in VOCABULARY_TERM_CATEGORIES
    }
    expanded_query = _unique(
        [
            normalized,
            *formulae,
            *strict_aliases,
            *vocabulary_matches["reagent_aliases"],
            *vocabulary_matches["condition_terms"],
            *vocabulary_matches["phenomenon_terms"],
            *vocabulary_matches["property_terms"],
        ]
    )
    return {
        "raw_query": query,
        "normalized_query": " ".join(expanded_query),
        "query_text": normalized,
        "formulae": formulae,
        "strict_aliases": strict_aliases,
        "reagent_aliases": vocabulary_matches["reagent_aliases"],
        "condition_tags": vocabulary_matches["condition_terms"],
        "phenomenon_tags": vocabulary_matches["phenomenon_terms"],
        "property_tags": vocabulary_matches["property_terms"],
        "reaction_features": extract_reaction_features(normalized, *expanded_query),
    }


def normalize_search_query(query: str) -> str:
    return chemistry_query_terms(query)["normalized_query"]


def _file_metadata(path: Path, *, name: str) -> dict[str, Any]:
    if not path.exists():
        return {"name": name, "path": str(path.relative_to(ROOT)), "exists": False}
    content = path.read_bytes()
    return {
        "name": name,
        "path": str(path.relative_to(ROOT)),
        "exists": True,
        "line_count": len(path.read_text(encoding="utf-8-sig").splitlines()),
        "sha256": hashlib.sha256(content).hexdigest(),
        "size_bytes": len(content),
    }


def chemistry_vocabulary_metadata() -> dict[str, Any]:
    vocabulary = chemistry_vocabulary()
    categories = vocabulary.get("categories", {})
    category_counts: dict[str, int] = {}
    if isinstance(categories, dict):
        for category, value in categories.items():
            if isinstance(value, dict):
                category_counts[category] = sum(1 + len(aliases) for aliases in value.values() if isinstance(aliases, list))
            elif isinstance(value, list):
                category_counts[category] = len(value)
    return {
        "version": vocabulary.get("version"),
        "category_counts": category_counts,
        "files": [
            _file_metadata(VOCABULARY_PATH, name="chemistry_vocabulary"),
            _file_metadata(ALIAS_PATH, name="chemical_aliases_compat"),
            _file_metadata(STOPWORD_PATH, name="chemical_stopwords"),
        ],
    }
