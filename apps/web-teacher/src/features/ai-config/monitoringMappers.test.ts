import { describe, expect, it } from "vitest";

import {
  buildAttentionItems,
  buildHealthTiles,
  monitorModules,
  openAiStatus,
  searchTermGroups,
  trendBuckets,
} from "./monitoringMappers";
import type { VideoLibraryIndexDiagnostics, VideoLibrarySearchDiagnostics } from "./monitoringTypes";
import type { AIConfiguration } from "../../api/settings";

const connectedStatus = {
  ready: true,
  message: "ok",
  effective_mode: "openai_api",
  connectivity_status: "connected",
  check_interval_minutes: 30,
  recent_request_count: 12,
  recent_error_count: 0,
  usage_buckets: [],
  usage_trends: {},
} as AIConfiguration["status"];

function aiConfig(overrides: Partial<AIConfiguration> = {}): AIConfiguration {
  return {
    provider: "openai",
    base_url: "https://example.test",
    model: "qwen-max",
    connection_check_interval_minutes: 30,
    api_key_configured: true,
    enabled_features: {
      rag_access_enabled: true,
      student_ai_assistant: true,
      student_learning_analytics: true,
      question_bank_assistant: true,
      teacher_learning_analytics: true,
    },
    status: connectedStatus,
    student_ai_policy: {
      active: true,
      version: "student-ai-policy-v1",
      model: "local",
      coverage: [],
      recent_decision_count: 2,
      invalid_decision_count: 0,
      outcomes: [],
    },
    rag_runtime: {
      rag_enabled: true,
      hybrid_bge_enabled: true,
      bge_service_required: true,
      bge_service_url: "http://bge-rag:8010",
      query_generation_enabled: true,
      vector_top_k: 24,
      rerank_top_k: 9,
      final_top_k: 5,
      status: "ok",
      message: "ok",
    },
    can_edit: true,
    ...overrides,
  };
}

describe("intelligent monitoring mappers", () => {
  it("defines stable monitoring modules instead of one long dashboard", () => {
    expect(monitorModules.map((item) => item.key)).toEqual([
      "overview",
      "openai",
      "rag",
      "es",
      "dictionary",
      "guardrail",
      "trends",
    ]);
  });

  it("maps provider status and health tiles for the overview", () => {
    expect(openAiStatus(connectedStatus)).toMatchObject({ label: "连接正常", tone: "good" });
    const tiles = buildHealthTiles({ aiConfig: aiConfig(), indexDiagnostics: indexDiagnostics() });
    expect(tiles.map((tile) => tile.label)).toContain("Outbox");
    expect(tiles.find((tile) => tile.label === "OpenAI")).toMatchObject({ status: "连接正常", value: "qwen-max" });
  });

  it("builds attention items for ES, mapping, dictionary, and outbox warnings", () => {
    const items = buildAttentionItems({
      aiConfig: aiConfig(),
      indexDiagnostics: indexDiagnostics({
        elasticsearch: {
          configured: true,
          document_count: 76,
          health: { status: "yellow" },
          mapping: { version: "old", desired_version: "new", chemistry_fields_present: { formulae: true, equation_rows: false } },
        },
        settings: {
          backend: "elasticsearch",
          index: "student-video-library",
          analyzer_assets: { ok: false, missing: ["analysis/chemistry_synonyms.txt"] },
          dictionary_assets: { category_counts: {} },
        },
        postgres: { sync_status_counts: { synced: 70, failed: 2 } },
      }),
    });
    expect(items.map((item) => item.key)).toEqual(
      expect.arrayContaining(["es-health", "es-mapping", "dictionary-assets", "outbox-failed"]),
    );
  });

  it("keeps query diagnostic term groups separate by chemistry semantics", () => {
    const groups = searchTermGroups({
      query_plan: {
        terms: {
          formulae: ["H2O2", "KMNO4"],
          strict_aliases: ["双氧水", "高锰酸钾"],
          condition_tags: ["酸性"],
          phenomenon_tags: ["褪色"],
          property_tags: ["氧化性"],
        },
      },
    } as VideoLibrarySearchDiagnostics);
    expect(groups.find((group) => group.key === "formulae")?.values).toEqual(["H2O2", "KMNO4"]);
    expect(groups.find((group) => group.key === "condition_tags")?.values).toEqual(["酸性"]);
  });

  it("creates stable empty trend buckets for each range", () => {
    expect(trendBuckets(connectedStatus, "1d")).toHaveLength(24);
    expect(trendBuckets(connectedStatus, "7d")).toHaveLength(14);
    expect(trendBuckets(connectedStatus, "30d")).toHaveLength(30);
  });
});

function indexDiagnostics(overrides: Partial<VideoLibraryIndexDiagnostics> = {}): VideoLibraryIndexDiagnostics {
  return {
    settings: {
      backend: "elasticsearch",
      index: "student-video-library",
      desired_mapping_version: "chemistry-point-placement-v4",
      analyzer: "ik_max_word",
      local_fallback: false,
      analyzer_assets: { ok: true, total_dictionary_lines: 50 },
      dictionary_assets: { version: "v1", category_counts: { strict_chemical_synonyms: 20 } },
    },
    postgres: {
      published_point_content_count: 76,
      sync_status_counts: { synced: 76, failed: 0 },
    },
    elasticsearch: {
      configured: true,
      document_count: 76,
      health: { status: "green" },
      mapping: {
        version: "chemistry-point-placement-v4",
        desired_version: "chemistry-point-placement-v4",
        chemistry_fields_present: { formulae: true, equation_rows: true },
      },
    },
    ...overrides,
  };
}
