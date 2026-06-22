import { describe, expect, it } from "vitest";

import type { CatalogEquationAssistDraft, CatalogEquationPreviewResponse } from "../../api/catalogTree";
import { buildEquationReviewModel } from "./catalogEquationReview";

function previewResponse(): CatalogEquationPreviewResponse {
  return {
    ok: true,
    equations: [
      {
        row_order: 1,
        raw_text: "H2 + O2 = H2O",
        canonical_display: "H2 + O2 → H2O",
        canonical_mhchem: "\\ce{H2 + O2 -> H2O}",
        plain_search_text: "H2 + O2 → H2O",
        formulae: ["H2", "O2", "H2O"],
        aliases: [],
        reactants: ["H2", "O2"],
        products: ["H2O"],
        participants: {},
        reaction_features: [],
        validation_status: "valid",
        warnings: [],
        errors: [],
        parser_version: "natural-v1",
        migrated_from_principle_equation: false,
        suggested_display: null,
        suggested_mhchem: null,
        suggestion_reason: null,
        corrections: [],
      },
    ],
  };
}

describe("catalog equation review model", () => {
  it("attaches AI candidates to matching preview rows", () => {
    const drafts: CatalogEquationAssistDraft[] = [
      {
        source: "ai",
        row_order: 1,
        draft_text: "2 H2 + O2 → 2 H2O",
        replacement_text: "2 H2 + O2 → 2 H2O",
        canonical_display: "2 H2 + O2 → 2 H2O",
        canonical_mhchem: "\\ce{2 H2 + O2 -> 2 H2O}",
        validation_status: "valid",
        rationale: "AI 根据当前输入给出配平候选。",
      },
    ];

    const model = buildEquationReviewModel(previewResponse(), drafts);

    expect(model.rows).toHaveLength(1);
    expect(model.rows[0].candidates).toHaveLength(1);
    expect(model.rows[0].candidates[0]).toMatchObject({
      sourceLabel: "AI 校对",
      replacement_text: "2 H2 + O2 → 2 H2O",
      supplemental: false,
    });
    expect(model.supplementalCandidates).toEqual([]);
  });

  it("keeps unmatched AI candidates as supplemental rendered candidates", () => {
    const drafts: CatalogEquationAssistDraft[] = [
      {
        source: "ai",
        draft_text: "Cl2 + 2 KBr → 2 KCl + Br2",
        replacement_text: "Cl2 + 2 KBr → 2 KCl + Br2",
        canonical_display: "Cl2 + 2 KBr → 2 KCl + Br2",
        canonical_mhchem: "\\ce{Cl2 + 2 KBr -> 2 KCl + Br2}",
        validation_status: "valid",
        rationale: "AI 根据点位内容补充候选反应式。",
        supplemental: true,
      },
    ];

    const model = buildEquationReviewModel({ ok: true, equations: [] }, drafts);

    expect(model.rows).toEqual([]);
    expect(model.supplementalCandidates).toHaveLength(1);
    expect(model.supplementalCandidates[0]).toMatchObject({
      sourceLabel: "AI 校对",
      supplemental: true,
      canonical_display: "Cl2 + 2 KBr → 2 KCl + Br2",
    });
  });

  it("filters invalid AI candidates from adoptable results", () => {
    const model = buildEquationReviewModel(previewResponse(), [
      {
        source: "ai",
        row_order: 1,
        draft_text: "not a reaction",
        canonical_display: "",
        validation_status: "invalid",
        rationale: "invalid",
      },
    ]);

    expect(model.rows[0].candidates).toHaveLength(0);
  });

  it("keeps inline annotation metadata on adoptable AI candidates", () => {
    const model = buildEquationReviewModel(previewResponse(), [
      {
        source: "ai",
        row_order: 1,
        draft_text: "2 H2 + O2 → 2 H2O // 需微热",
        replacement_text: "2 H2 + O2 → 2 H2O // 需微热",
        canonical_display: "2 H2 + O2 → 2 H2O",
        canonical_mhchem: "\\ce{2 H2 + O2 -> 2 H2O}",
        annotation_text: "需微热",
        annotation_formulae: [],
        condition_tags: ["heated"],
        validation_status: "valid",
        rationale: "AI balance check.",
      },
    ]);

    expect(model.rows[0].candidates[0]).toMatchObject({
      replacement_text: "2 H2 + O2 → 2 H2O // 需微热",
      annotation_text: "需微热",
      condition_tags: ["heated"],
    });
  });

  it("does not create adoptable candidates without AI drafts", () => {
    const model = buildEquationReviewModel(previewResponse(), []);

    expect(model.rows).toHaveLength(1);
    expect(model.rows[0].equation.suggested_display).toBeNull();
    expect(model.rows[0].candidates).toEqual([]);
    expect(model.supplementalCandidates).toEqual([]);
  });
});
