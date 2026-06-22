import { describe, expect, it } from "vitest";

import type { LearningAssistantRuntime } from "../../api/learningAssistant";
import {
  questionWorkbenchGateFromRuntime,
  textbookSectionLabels,
  workbenchEvidenceSectionsFromPackage,
} from "./questionBankDisplay";

function runtimeWithRag(ragRuntime: Record<string, unknown>): LearningAssistantRuntime {
  return {
    checked_at: "2026-06-22T10:00:00Z",
    rag_runtime: {
      rag_enabled: true,
      query_generation_enabled: true,
      textbook_rag_enabled: true,
      textbook_rag_status: "healthy",
      textbook_rag_index: "canonical-rag-chunks-qwen-v1",
      ...ragRuntime,
    } as LearningAssistantRuntime["rag_runtime"],
  };
}

describe("question workbench display helpers", () => {
  it("allows AI workbench actions when textbook RAG is healthy", () => {
    const gate = questionWorkbenchGateFromRuntime(runtimeWithRag({ textbook_rag_status: "healthy" }));

    expect(gate.healthy).toBe(true);
    expect(gate.tone).toBe("ready");
    expect(gate.route).toContain("canonical-rag-chunks-qwen-v1");
    expect(gate.message).toContain("点位三段式描述");
  });

  it("blocks AI workbench actions when the textbook index is stale", () => {
    const gate = questionWorkbenchGateFromRuntime(
      runtimeWithRag({
        textbook_rag_status: "index_stale",
        textbook_rag_message: "教材 chunk 索引需要重建。",
      }),
    );

    expect(gate.healthy).toBe(false);
    expect(gate.tone).toBe("blocked");
    expect(gate.message).toContain("教材 chunk 索引需要重建");
  });

  it("groups workbench evidence by point and textbook section", () => {
    const sections = workbenchEvidenceSectionsFromPackage({
      point_packages: {
        "point-a": {
          point: { point_title: "氯水置换溴离子" },
          sections: {
            principle: {
              sufficient: true,
              sources: [
                { chunk_id: "chunk-1", source_file: "textbook.jsonl" },
                { chunk_id: "chunk-2", source_file: "textbook.jsonl" },
              ],
            },
            safety: {
              sufficient: false,
              missing_reason: "未召回安全提示证据",
              sources: [],
            },
          },
        },
      },
    });

    expect(sections).toHaveLength(2);
    expect(textbookSectionLabels.principle).toBe("实验原理");
    expect(sections[0]).toMatchObject({
      pointKey: "point-a",
      pointTitle: "氯水置换溴离子",
      section: "principle",
      sufficient: true,
      sourceCount: 2,
    });
    expect(sections[1]).toMatchObject({
      section: "safety",
      sufficient: false,
      missingReason: "未召回安全提示证据",
    });
  });
});
