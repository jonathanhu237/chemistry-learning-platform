from __future__ import annotations

from server.app.chemistry_search import (
    chemistry_query_terms,
    chemistry_terms_for_document,
    chemistry_vocabulary_metadata,
)


def test_strict_chemical_synonyms_do_not_absorb_phenomenon_terms() -> None:
    stimulating_gas = "\u523a\u6fc0\u6027\u6c14\u4f53"
    yellow_precipitate = "\u9ec4\u8272\u6c89\u6dc0"
    terms = chemistry_terms_for_document(f"SO2 {stimulating_gas}", yellow_precipitate)

    assert "SO2" in terms["formulae"]
    assert stimulating_gas not in terms["aliases"]
    assert yellow_precipitate not in terms["aliases"]
    assert stimulating_gas in terms["phenomenon_tags"]
    assert yellow_precipitate in terms["phenomenon_tags"]


def test_chinese_reagent_alias_query_expands_to_exact_formulae_without_substring_pollution() -> None:
    query = chemistry_query_terms("\u53cc\u6c27\u6c34 \u9ad8\u9530\u9178\u94be \u9178\u6027")

    assert {"H2O2", "KMNO4"}.issubset(set(query["formulae"]))
    assert "K2MNO4" not in query["formulae"]
    assert "\u53cc\u6c27\u6c34" in query["strict_aliases"]
    assert "\u9ad8\u9530\u9178\u94be" in query["strict_aliases"]
    assert "\u9178\u6027" in query["condition_tags"]


def test_chemistry_vocabulary_metadata_exposes_dictionary_categories() -> None:
    metadata = chemistry_vocabulary_metadata()

    assert metadata["version"] == "chemistry-vocabulary-v1"
    assert metadata["category_counts"]["strict_chemical_synonyms"] > 50
    assert metadata["category_counts"]["phenomenon_terms"] > 0
