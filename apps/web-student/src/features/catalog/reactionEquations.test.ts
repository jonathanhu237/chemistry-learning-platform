import { describe, expect, it } from "vitest";

import {
  buildReactionEquationRenderRow,
  buildReactionEquationRows,
  reactionEquationFallbackText,
} from "../../../../shared/reactionEquations";

describe("shared reaction equation rendering core", () => {
  it("uses canonical mhchem as the only renderable chemistry source", () => {
    const row = buildReactionEquationRenderRow(
      {
        row_order: 2,
        raw_text: "raw should not render",
        equation_core: "core fallback",
        canonical_display: "Cl2 + 2 KBr = 2 KCl + Br2",
        canonical_mhchem: "\\ce{Cl2 + 2 KBr -> 2 KCl + Br2}",
        annotation_text: "organic layer turns orange",
      },
      0,
      "studentMobile",
    );

    expect(row).toMatchObject({
      rowOrder: 2,
      latex: "\\ce{Cl2 + 2 KBr -> 2 KCl + Br2}",
      fallback: "Cl2 + 2 KBr = 2 KCl + Br2",
      annotation: "organic layer turns orange",
      presentation: "studentMobile",
      source: "canonical_mhchem",
    });
  });

  it("falls back to confirmed display text without inventing a chemistry parse", () => {
    const row = buildReactionEquationRenderRow(
      {
        raw_text: "KI + H2SO4 -> KHSO4 + HI",
        canonical_display: "KI + H2SO4 -> KHSO4 + HI",
        canonical_mhchem: null,
      },
      0,
      "studentMobile",
    );

    expect(row.latex).toBeNull();
    expect(row.fallback).toBe("KI + H2SO4 -> KHSO4 + HI");
    expect(row.source).toBe("plain_fallback");
  });

  it("filters invalid rows and uses legacy lines as plain fallback text", () => {
    const rows = buildReactionEquationRows({
      equations: [
        {
          row_order: 1,
          raw_text: "bad",
          canonical_mhchem: "\\ce{bad}",
          validation_status: "invalid",
        },
      ],
      legacyText: "Pb(CH3COO)2 + H2S -> PbS + 2 CH3COOH",
      presentation: "studentMobile",
      filterInvalid: true,
    });

    expect(rows).toHaveLength(1);
    expect(rows[0].latex).toBeNull();
    expect(rows[0].fallback).toBe("Pb(CH3COO)2 + H2S -> PbS + 2 CH3COOH");
  });

  it("keeps teacher and student profiles on the same fallback priority", () => {
    const equation = {
      raw_text: "raw",
      equation_core: "core",
      canonical_display: "display",
      canonical_mhchem: "",
    };

    expect(reactionEquationFallbackText(equation)).toBe("display");
    expect(buildReactionEquationRenderRow(equation, 0, "teacherReview").fallback).toBe("display");
    expect(buildReactionEquationRenderRow(equation, 0, "studentMobile").fallback).toBe("display");
  });
});
