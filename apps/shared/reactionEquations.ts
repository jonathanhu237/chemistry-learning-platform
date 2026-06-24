export type ReactionEquationInput = {
  row_order?: number | null;
  raw_text?: string | null;
  canonical_display?: string | null;
  canonical_mhchem?: string | null;
  equation_core?: string | null;
  annotation_text?: string | null;
  validation_status?: string | null;
};

export type ReactionEquationPresentation = "teacherReview" | "studentMobile";

export type ReactionEquationRenderRow = {
  key: string;
  rowOrder: number;
  latex: string | null;
  fallback: string;
  annotation: string;
  presentation: ReactionEquationPresentation;
  source: "canonical_mhchem" | "plain_fallback";
};

export function reactionEquationFallbackText(equation: ReactionEquationInput): string {
  return [
    equation.canonical_display,
    equation.equation_core,
    equation.raw_text,
  ]
    .map((value) => String(value || "").trim())
    .find(Boolean) || "";
}

export function buildReactionEquationRenderRow(
  equation: ReactionEquationInput,
  index: number,
  presentation: ReactionEquationPresentation,
): ReactionEquationRenderRow {
  const latex = String(equation.canonical_mhchem || "").trim();
  const fallback = reactionEquationFallbackText(equation) || latex;
  const annotation = String(equation.annotation_text || "").trim();
  const rowOrder = Number(equation.row_order || index + 1);
  const rawKey = String(equation.raw_text || equation.canonical_display || latex || fallback || rowOrder);

  return {
    key: `${rowOrder}-${rawKey}`,
    rowOrder,
    latex: latex || null,
    fallback,
    annotation,
    presentation,
    source: latex ? "canonical_mhchem" : "plain_fallback",
  };
}

export function buildReactionEquationRows({
  equations,
  legacyText,
  presentation,
  filterInvalid = false,
}: {
  equations?: ReactionEquationInput[] | null;
  legacyText?: string | null;
  presentation: ReactionEquationPresentation;
  filterInvalid?: boolean;
}): ReactionEquationRenderRow[] {
  const validEquations = (equations || []).filter((equation) => !filterInvalid || equation.validation_status !== "invalid");

  if (validEquations.length) {
    return validEquations
      .map((equation, index) => buildReactionEquationRenderRow(equation, index, presentation))
      .filter((row) => row.latex || row.fallback);
  }

  return String(legacyText || "")
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line, index) =>
      buildReactionEquationRenderRow(
        {
          row_order: index + 1,
          raw_text: line,
          canonical_display: line,
          canonical_mhchem: null,
        },
        index,
        presentation,
      ),
    );
}
