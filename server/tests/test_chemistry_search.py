from __future__ import annotations

from server.app.chemistry_search import (
    chemistry_terms_for_document,
    expand_formula_aliases,
    extract_formulae,
    extract_reaction_features,
    normalize_formula,
    normalize_search_query,
)


def test_normalize_formula_handles_unicode_subscripts_and_coefficients() -> None:
    assert normalize_formula("2 Na₂S₂O₃(aq)") == "NA2S2O3"
    assert normalize_formula("SO₂↑") == "SO2"


def test_extract_formulae_strips_equation_noise() -> None:
    formulae = extract_formulae("Na₂S₂O₃ + 2 HCl = 2 NaCl + S↓ + SO₂↑ + H₂O")

    assert formulae == ["NA2S2O3", "HCL", "NACL", "S", "SO2", "H2O"]


def test_extract_formulae_normalizes_unicode_ion_charges_without_count_pollution() -> None:
    formulae = extract_formulae("Mn\u00b2\u207a + ClO\u207b + OH\u207b")

    assert formulae == ["MN", "CLO", "OH"]
    assert "MN2" not in formulae


def test_formula_aliases_expand_common_chemistry_names() -> None:
    aliases = expand_formula_aliases(["HCl", "Na2S2O3"])

    assert "HCL" in aliases
    assert "盐酸" in aliases
    assert "NA2S2O3" in aliases
    assert "硫代硫酸钠" in aliases


def test_reaction_features_and_search_query_are_chemistry_aware() -> None:
    features = extract_reaction_features("Na2S2O3 + 2HCl -> S↓ + SO2↑", "生成黄色沉淀和刺激性气体")
    query = normalize_search_query("S₂O₃²⁻ 盐酸")
    terms = chemistry_terms_for_document("Na2S2O3 + HCl", "有沉淀和气体生成")

    assert "gas_generation" in features
    assert "precipitation" in features
    assert "NA2S2O3" in terms["formulae"]
    assert "盐酸" in terms["aliases"]
    assert "S2O32-" in query
