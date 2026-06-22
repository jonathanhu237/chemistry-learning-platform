import { describe, expect, it } from "vitest";

import apiSource from "../../api.ts?raw";
import pointDetailSource from "./CatalogPointDetailPanel.tsx?raw";

describe("student catalog AI diagnostic boundaries", () => {
  it("keeps teacher-only evidence diagnostics out of student point APIs and pages", () => {
    const studentPointSurface = `${apiSource}\n${pointDetailSource}`;

    expect(studentPointSurface).toContain("point_node_id");
    expect(studentPointSurface).not.toContain("chunk_id");
    expect(studentPointSurface).not.toContain("selected_chunk_ids");
    expect(studentPointSurface).not.toContain("rerank_score");
    expect(studentPointSurface).not.toContain("generated_queries");
    expect(studentPointSurface).not.toContain("job_state");
    expect(studentPointSurface).not.toContain("evidence_state");
    expect(studentPointSurface).not.toContain("rag_trace");
    expect(studentPointSurface).not.toContain("teacher_only");
    expect(studentPointSurface).not.toContain("diagnostics");
  });
});
