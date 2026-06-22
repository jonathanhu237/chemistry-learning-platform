import type {
  CatalogEquationAssistDraft,
  CatalogEquationPreviewResponse,
  CatalogReactionEquationNormalized,
} from "../../api/catalogTree";

export type CatalogEquationReviewCandidate = {
  key: string;
  sources: string[];
  sourceLabel: string;
  row_order?: number | null;
  supplemental: boolean;
  draft_text: string;
  replacement_text: string;
  canonical_display: string;
  canonical_mhchem?: string | null;
  annotation_text?: string;
  annotation_formulae?: string[];
  condition_tags?: string[];
  validation_status: CatalogReactionEquationNormalized["validation_status"];
  warnings: string[];
  errors: string[];
  formulae: string[];
  rationale: string;
};

export type CatalogEquationReviewRow = {
  equation: CatalogReactionEquationNormalized;
  candidates: CatalogEquationReviewCandidate[];
};

export type CatalogEquationReviewModel = {
  rows: CatalogEquationReviewRow[];
  supplementalCandidates: CatalogEquationReviewCandidate[];
};

export function equationCandidateSourceLabel(sources: string[]): string {
  const uniqueSources = Array.from(new Set(sources));
  const hasAi = uniqueSources.includes("ai");
  if (hasAi) return "AI 校对";
  return uniqueSources.join(" + ") || "AI 建议";
}

function candidateKey(rowOrder: number | null | undefined, display: string): string {
  return `${rowOrder || "supplemental"}::${display.trim()}`;
}

function mergeCandidate(
  candidates: CatalogEquationReviewCandidate[],
  candidate: CatalogEquationReviewCandidate | null,
): CatalogEquationReviewCandidate[] {
  if (!candidate) return candidates;
  const existingIndex = candidates.findIndex((item) => item.key === candidate.key);
  if (existingIndex < 0) return [...candidates, candidate];
  return candidates.map((item, index) => {
    if (index !== existingIndex) return item;
    const sources = Array.from(new Set([...item.sources, ...candidate.sources]));
    const rationales = [item.rationale, candidate.rationale].filter(Boolean);
    return {
      ...item,
      sources,
      sourceLabel: equationCandidateSourceLabel(sources),
      rationale: Array.from(new Set(rationales)).join("；"),
      warnings: Array.from(new Set([...item.warnings, ...candidate.warnings])),
      errors: Array.from(new Set([...item.errors, ...candidate.errors])),
      formulae: Array.from(new Set([...item.formulae, ...candidate.formulae])),
      canonical_mhchem: item.canonical_mhchem || candidate.canonical_mhchem,
      annotation_text: item.annotation_text || candidate.annotation_text,
      annotation_formulae: Array.from(new Set([...(item.annotation_formulae || []), ...(candidate.annotation_formulae || [])])),
      condition_tags: Array.from(new Set([...(item.condition_tags || []), ...(candidate.condition_tags || [])])),
    };
  });
}

function assistCandidateFromDraft(draft: CatalogEquationAssistDraft): CatalogEquationReviewCandidate | null {
  const replacement = (draft.replacement_text || draft.draft_text || draft.canonical_display || "").trim();
  const display = (draft.canonical_display || replacement).trim();
  const status = draft.validation_status || "warning";
  if (!replacement || !display || status === "invalid") return null;
  const source = draft.source || "ai";
  if (source === "deterministic") return null;
  return {
    key: candidateKey(draft.row_order, display),
    sources: ["ai"],
    sourceLabel: equationCandidateSourceLabel(["ai"]),
    row_order: draft.row_order,
    supplemental: Boolean(draft.supplemental || !draft.row_order),
    draft_text: draft.draft_text || replacement,
    replacement_text: replacement,
    canonical_display: display,
    canonical_mhchem: draft.canonical_mhchem,
    annotation_text: draft.annotation_text || "",
    annotation_formulae: draft.annotation_formulae || [],
    condition_tags: draft.condition_tags || [],
    validation_status: status,
    warnings: draft.warnings || [],
    errors: draft.errors || [],
    formulae: draft.formulae || [],
    rationale: draft.rationale || "",
  };
}

export function buildEquationReviewModel(
  preview: CatalogEquationPreviewResponse | null | undefined,
  drafts: CatalogEquationAssistDraft[],
): CatalogEquationReviewModel {
  const rows: CatalogEquationReviewRow[] = (preview?.equations || []).map((equation) => ({
    equation,
    candidates: [],
  }));
  const rowMap = new Map(rows.map((row) => [row.equation.row_order, row]));
  let supplementalCandidates: CatalogEquationReviewCandidate[] = [];

  drafts.forEach((draft) => {
    const candidate = assistCandidateFromDraft(draft);
    if (!candidate) return;
    const row = candidate.row_order ? rowMap.get(candidate.row_order) : undefined;
    if (row) {
      row.candidates = mergeCandidate(row.candidates, { ...candidate, supplemental: false });
    } else {
      supplementalCandidates = mergeCandidate(supplementalCandidates, { ...candidate, supplemental: true, row_order: null });
    }
  });

  return { rows, supplementalCandidates };
}
