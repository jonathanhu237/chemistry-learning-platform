from __future__ import annotations

import asyncio

from server.app.api.admin.admin_catalog_tree import admin_catalog_assist_equations, admin_catalog_preview_equations
from server.app.auth import AuthUser
from server.app.catalog_tree_schemas import CatalogEquationAssistRequest, CatalogEquationPreviewRequest
from server.app.domains.catalog_tree.common import content_publication_errors
from server.app.domains.catalog_tree.equations import (
    _equation_ai_prompt,
    _sanitize_ai_drafts,
    equation_rows_from_inputs,
    normalize_reaction_equations,
    reaction_derived_terms,
    reaction_principle_text,
)
from server.app.domains.catalog_tree.jobs import _catalog_point_queries


def _teacher_user() -> AuthUser:
    return AuthUser(
        id="teacher-1",
        username="teacher",
        role="teacher",
        display_name="Teacher",
        status="active",
    )


def test_normalizes_multiple_reaction_equations_for_backend_consumers() -> None:
    rows = normalize_reaction_equations(
        [
            {"raw_text": "Cl₂ + 2 KBr = 2 KCl + Br₂"},
            {"raw_text": "Br2 + 2 I- -> 2 Br- + I2"},
        ]
    )

    assert len(rows) == 2
    assert rows[0]["canonical_display"] == "Cl2 + 2 KBr → 2 KCl + Br2"
    assert rows[0]["canonical_mhchem"] == "\\ce{Cl2 + 2 KBr -> 2 KCl + Br2}"
    assert {"CL2", "KBR", "KCL", "BR2"}.issubset(set(rows[0]["formulae"]))
    assert rows[0]["reactants"]
    assert rows[0]["products"]
    assert rows[0]["validation_status"] in {"valid", "warning"}


def test_unparseable_equation_rows_do_not_emit_local_parser_errors() -> None:
    [row] = normalize_reaction_equations([{"raw_text": "只观察到橙色分层，没有方程式"}])

    assert row["validation_status"] == "valid"
    assert row["errors"] == []
    assert row["warnings"] == []
    assert row["canonical_display"] == "只观察到橙色分层，没有方程式"
    assert row["canonical_mhchem"] is None
    assert row["suggested_display"] is None
    assert row["formulae"] == []
    assert row["reactants"] == []
    assert {"color_change", "phase_separation"}.issubset(set(row["reaction_features"]))


def test_parseable_but_unbalanced_equation_does_not_emit_local_parser_warning() -> None:
    [row] = normalize_reaction_equations([{"raw_text": "H2 + O2 = H2O"}])

    assert row["validation_status"] == "valid"
    assert row["warnings"] == []
    assert row["suggested_display"] is None
    assert row["suggestion_reason"] is None
    assert row["formulae"]


def test_loose_casing_no_space_and_equals_are_normalized_without_diagnostics() -> None:
    [row] = normalize_reaction_equations([{"raw_text": "CL2+2h2 = 2hcl"}])

    assert row["raw_text"] == "CL2+2h2 = 2hcl"
    assert row["canonical_display"] == "Cl2 + 2 H2 → 2 HCl"
    assert row["canonical_mhchem"] == "\\ce{Cl2 + 2 H2 -> 2 HCl}"
    assert row["validation_status"] == "valid"
    assert row["warnings"] == []
    assert row["suggested_display"] is None
    assert row["corrections"]


def test_compact_ionic_charge_notation_renders_charge_not_subscript() -> None:
    [row] = normalize_reaction_equations(
        [{"raw_text": "ClO3- + 3SO32- + 6H+ -> Cl- + 3SO42- + 3H2O"}]
    )

    assert row["canonical_display"] == "ClO3^- + 3 SO3^2- + 6 H^+ \u2192 Cl^- + 3 SO4^2- + 3 H2O"
    assert row["canonical_mhchem"] == "\\ce{ClO3^- + 3 SO3^2- + 6 H^+ -> Cl^- + 3 SO4^2- + 3 H2O}"
    assert "SO32-" not in row["canonical_mhchem"]
    assert {"CLO3", "SO3", "H", "CL", "SO4", "H2O"}.issubset(set(row["formulae"]))


def test_chinese_substance_aliases_are_preview_diagnostics_not_raw_rewrites() -> None:
    [row] = normalize_reaction_equations([{"raw_text": "氯气 + 氢气 = 氯化氢"}])

    assert row["raw_text"] == "氯气 + 氢气 = 氯化氢"
    assert row["canonical_display"] == "Cl2 + H2 → HCl"
    assert row["suggested_display"] is None
    assert row["warnings"] == []
    assert {"CL2", "H2", "HCL"}.issubset(set(row["formulae"]))
    assert {"氯气", "氢气", "氯化氢"}.issubset({item["alias"] for item in row["metadata"]["alias_mappings"]})


def test_multiline_preview_splits_non_empty_lines_in_order() -> None:
    rows = equation_rows_from_inputs(
        multiline_text="CL2+H2=HCL\n\nCl2 + 2KBr -> 2KCl + Br2",
        rows=[{"raw_text": "stale row should not win"}],
    )

    assert rows == [
        {"raw_text": "CL2+H2=HCL", "row_order": 1},
        {"raw_text": "Cl2 + 2KBr -> 2KCl + Br2", "row_order": 2},
    ]


def test_inline_annotation_stays_on_one_reaction_row_without_polluting_core_terms() -> None:
    raw = (
        "Mn\u00b2\u207a + ClO\u207b + 2OH\u207b -> MnO\u2082\u2193 + Cl\u207b + H\u2082O"
        " // 碱性条件；NaClO溶液本身呈碱性，提供OH\u207b"
    )
    rows = equation_rows_from_inputs(multiline_text=raw)
    [row] = normalize_reaction_equations(rows)

    assert row["raw_text"] == raw
    assert row["equation_core"].startswith("Mn\u00b2\u207a + ClO\u207b")
    assert row["annotation_text"] == "碱性条件；NaClO溶液本身呈碱性，提供OH\u207b"
    assert row["canonical_display"]
    assert "碱性条件" not in row["canonical_display"]
    assert "NACLO" in row["annotation_formulae"]
    assert "OH" in row["annotation_formulae"]
    assert row["condition_tags"] == ["alkaline"]
    assert "NACLO" not in row["formulae"]
    assert "MN2" not in row["formulae"]
    assert "NACLO" not in row["reactants"]
    assert "NACLO" not in row["products"]

    content = {"principle_mode": "equation", "reaction_equations": [row]}
    assert "// 碱性条件" in reaction_principle_text(content)
    assert "// 碱性条件" not in reaction_principle_text(content, include_annotations=False)
    terms = reaction_derived_terms(content)
    assert "NACLO" not in terms["formulae"]
    assert "NACLO" in terms["annotation_formulae"]
    assert terms["condition_tags"] == ["alkaline"]


def test_unparseable_annotated_core_preserves_annotation_without_local_errors() -> None:
    [row] = normalize_reaction_equations([{"raw_text": "not a reaction // note: NaClO provides OH-"}])

    assert row["validation_status"] == "valid"
    assert row["equation_core"] == "not a reaction"
    assert row["annotation_text"] == "NaClO provides OH-"
    assert "NACLO" in row["annotation_formulae"]
    assert row["formulae"] == []
    assert row["reactants"] == []
    assert row["products"] == []


def test_ai_drafts_are_normalized_before_becoming_adoptable() -> None:
    normalized_rows = normalize_reaction_equations([{"raw_text": "H2 + O2 = H2O"}])
    drafts = _sanitize_ai_drafts(
        [{"row_order": 1, "draft_text": "h2+o2=h2o", "rationale": "AI balance check"}],
        normalized_rows,
    )

    assert len(drafts) == 1
    assert drafts[0]["source"] == "ai"
    assert drafts[0]["row_order"] == 1
    assert drafts[0]["replacement_text"] == "H2 + O2 \u2192 H2O"
    assert drafts[0]["canonical_mhchem"] == "\\ce{H2 + O2 -> H2O}"
    assert drafts[0]["validation_status"] == "valid"
    assert drafts[0]["supplemental"] is False


def test_ai_core_correction_preserves_existing_inline_annotation_suffix() -> None:
    normalized_rows = normalize_reaction_equations([{"raw_text": "H2 + O2 = H2O // note: keep this condition"}])
    drafts = _sanitize_ai_drafts(
        [{"row_order": 1, "draft_text": "2 H2 + O2 -> 2 H2O", "rationale": "balance"}],
        normalized_rows,
    )

    assert len(drafts) == 1
    assert drafts[0]["canonical_display"] == "2 H2 + O2 \u2192 2 H2O"
    assert drafts[0]["replacement_text"] == "2 H2 + O2 \u2192 2 H2O // keep this condition"
    assert drafts[0]["annotation_text"] == "keep this condition"


def test_ai_drafts_are_not_rejected_by_local_parser_and_unmatched_rows_are_supplemental() -> None:
    normalized_rows = normalize_reaction_equations([{"raw_text": "H2 + O2 = H2O"}])
    drafts = _sanitize_ai_drafts(
        [
            {"row_order": 1, "draft_text": "not a reaction"},
            {"row_order": 99, "draft_text": "Cl2 + 2 KBr -> 2 KCl + Br2"},
        ],
        normalized_rows,
    )

    assert len(drafts) == 2
    assert drafts[0]["row_order"] == 1
    assert drafts[0]["replacement_text"] == "not a reaction"
    assert drafts[0]["supplemental"] is False
    assert drafts[1]["row_order"] is None
    assert drafts[1]["supplemental"] is True
    assert drafts[1]["canonical_display"] == "Cl2 + 2 KBr \u2192 2 KCl + Br2"

def test_equation_mode_publication_uses_normalized_rows_and_text_mode_ignores_rows() -> None:
    valid_rows = normalize_reaction_equations([{"raw_text": "2 H2 + O2 = 2 H2O"}])
    equation_errors = content_publication_errors(
        {"node_id": "cat-point-1", "canonical_point_id": "cat-canon-1", "node_kind": "point", "title": "Hydrogen combustion"},
        {
            "principle_mode": "equation",
            "principle_equation": "",
            "reaction_equations": valid_rows,
            "phenomenon_explanation": "Water forms.",
            "safety_note": "Keep flame small.",
        },
    )
    text_errors = content_publication_errors(
        {"node_id": "cat-point-1", "canonical_point_id": "cat-canon-1", "node_kind": "point", "title": "Text point"},
        {
            "principle_mode": "text",
            "principle_text": "A descriptive principle is enough in text mode.",
            "reaction_equations": valid_rows,
            "phenomenon_explanation": "Visible change.",
            "safety_note": "Wear goggles.",
        },
    )

    assert equation_errors == []
    assert text_errors == []


def test_reaction_context_helpers_keep_teacher_rows_without_formula_pollution() -> None:
    rows = normalize_reaction_equations(
        [
            {"raw_text": "Cl2 + 2 KBr = 2 KCl + Br2"},
            {"raw_text": "not a reaction"},
        ]
    )
    content = {"principle_mode": "equation", "principle_equation": "legacy", "reaction_equations": rows}

    assert reaction_principle_text(content) == "Cl2 + 2 KBr \u2192 2 KCl + Br2\nnot a reaction"
    terms = reaction_derived_terms(content)
    assert "CL2" in terms["formulae"]
    assert "not a reaction" not in " ".join(terms["formulae"])


def test_rag_queries_include_annotation_terms_without_core_participant_pollution() -> None:
    rows = normalize_reaction_equations(
        [{"raw_text": "Mn^2+ + ClO- + 2OH- -> MnO2 + Cl- + H2O // 碱性条件；NaClO solution provides OH-"}]
    )
    content = {"principle_mode": "equation", "reaction_equations": rows}
    terms = reaction_derived_terms(content)
    queries, trace = _catalog_point_queries(
        {
            "title": "NaClO oxidizes manganese",
            "catalog_path": ["Chapter", "Manganese"],
            "normalized_equations": rows,
            "phenomenon_explanation": "Brown precipitate appears.",
            "safety_note": "Handle oxidants carefully.",
            "formulae": terms["formulae"],
            "aliases": terms["aliases"],
            "reaction_features": terms["reaction_features"],
            "annotation_formulae": terms["annotation_formulae"],
            "annotation_aliases": terms["annotation_aliases"],
            "condition_tags": terms["condition_tags"],
            "videos": [],
            "related_points": [],
            "field_contributors": ["title", "normalized_equations"],
        }
    )

    joined_queries = " ".join(queries)
    assert "NaClO solution provides OH-" in joined_queries
    assert "NACLO" in joined_queries
    assert "alkaline" in joined_queries
    assert "NACLO" not in terms["formulae"]
    assert trace["field_contributors"] == ["title", "normalized_equations"]


def test_preview_route_prefers_multiline_text_without_local_parser_blocking() -> None:
    response = asyncio.run(
        admin_catalog_preview_equations(
            CatalogEquationPreviewRequest(
                multiline_text="H2 + O2 = H2O\nnot a reaction",
                equations=[{"raw_text": "Cl2 = Cl2"}],
            ),
            user=_teacher_user(),
        )
    )

    assert response.ok is True
    assert [row.raw_text for row in response.equations] == ["H2 + O2 = H2O", "not a reaction"]
    assert response.equations[0].suggested_display is None
    assert response.equations[0].warnings == []
    assert response.equations[1].formulae == []


def test_preview_route_round_trips_inline_annotation_fields() -> None:
    response = asyncio.run(
        admin_catalog_preview_equations(
            CatalogEquationPreviewRequest(
                multiline_text="Mn^2+ + ClO- + 2OH- -> MnO2 + Cl- + H2O // note: NaClO solution provides OH-",
            ),
            user=_teacher_user(),
        )
    )

    assert response.ok is True
    assert len(response.equations) == 1
    assert response.equations[0].equation_core == "Mn^2+ + ClO- + 2OH- -> MnO2 + Cl- + H2O"
    assert response.equations[0].annotation_text == "NaClO solution provides OH-"
    assert "NACLO" in response.equations[0].annotation_formulae
    assert "NACLO" not in response.equations[0].formulae


def test_equation_ai_prompt_uses_single_leading_system_message() -> None:
    normalized_rows = normalize_reaction_equations(
        [{"raw_text": "Mn^2+ + ClO- + 2OH- -> MnO2 + Cl- + H2O // 碱性条件"}]
    )
    messages = _equation_ai_prompt(
        CatalogEquationAssistRequest(mode="suggest", multiline_text="Mn^2+ + ClO- -> MnO2"),
        normalized_rows,
    )

    assert [message["role"] for message in messages] == ["system", "user"]
    assert "Inline annotation rule" in messages[0]["content"]
    assert "EQUATION_CORE [ // ANNOTATION ]" in messages[0]["content"]
    assert "Prefer preserving the teacher's equation core" in messages[0]["content"]
    assert "NaClO溶液本身呈碱性" in messages[0]["content"]
    assert "parser_preview" not in messages[0]["content"]
    assert "parser_preview" not in messages[1]["content"]
    assert '"input_rows"' in messages[1]["content"]
    assert all(message["role"] != "system" for message in messages[1:])


def test_equation_ai_prompt_teaches_annotation_only_rewrite_skill() -> None:
    raw = "Mn2+ + ClO- + 2OH- -> MnO2↓ + Cl- + H2O（注：NaClO溶液本身呈碱性，提供OH-）"
    normalized_rows = normalize_reaction_equations([{"raw_text": raw}])
    messages = _equation_ai_prompt(
        CatalogEquationAssistRequest(mode="suggest", multiline_text=raw),
        normalized_rows,
    )

    system_prompt = messages[0]["content"]
    user_payload = messages[1]["content"]
    assert "Return an AI draft for annotation-only rewrites too" in system_prompt
    assert "Never treat formula-internal parentheses as annotations" in system_prompt
    assert "Draft: Mn2+ + ClO- + 2OH- -> MnO2↓ + Cl- + H2O // NaClO溶液本身呈碱性，提供OH-" in system_prompt
    assert raw in user_payload


def test_assist_route_returns_drafts_or_unavailable_without_saving(monkeypatch) -> None:
    monkeypatch.setattr(
        "server.app.domains.catalog_tree.equations._try_ai_equation_drafts",
        lambda payload, normalized_rows: ([], "AI 未配置，无法校对。"),
    )
    draft_response = asyncio.run(
        admin_catalog_assist_equations(
            CatalogEquationAssistRequest(mode="suggest", multiline_text="H2 + O2 = H2O", point_title="氢气燃烧"),
            user=_teacher_user(),
        )
    )
    unavailable_response = asyncio.run(
        admin_catalog_assist_equations(
            CatalogEquationAssistRequest(mode="generate", multiline_text="", point_title="氢气燃烧"),
            user=_teacher_user(),
        )
    )

    assert draft_response.available is False
    assert draft_response.drafts == []
    assert "AI 未配置" in (draft_response.reason or "")
    assert unavailable_response.available is False
    assert unavailable_response.drafts == []
    assert "AI 未配置" in (unavailable_response.reason or "")


def test_assist_route_prefers_ai_candidates_after_input_preview(monkeypatch) -> None:
    def fake_ai(payload, normalized_rows):
        assert normalized_rows[0]["canonical_display"] == "H2 + O2 → H2O"
        return (
            [{"draft_text": "2 H2 + O2 → 2 H2O", "source": "ai", "rationale": "已补齐配平。", "row_order": 1}],
            "AI 已根据当前输入生成建议；采用后会重新渲染预览。",
        )

    monkeypatch.setattr("server.app.domains.catalog_tree.equations._try_ai_equation_drafts", fake_ai)

    response = asyncio.run(
        admin_catalog_assist_equations(
            CatalogEquationAssistRequest(mode="suggest", multiline_text="H2 + O2 = H2O", point_title="氢气燃烧"),
            user=_teacher_user(),
        )
    )

    assert response.available is True
    assert response.drafts[0].source == "ai"
    assert response.drafts[0].row_order == 1
