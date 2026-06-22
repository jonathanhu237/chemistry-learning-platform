import { api, apiBase, postJson, postJsonStream } from "./http";
import { getAuthToken } from "./auth";
import type { AIConfiguration } from "./settings";

export type LearningAssistantAskRequest = {
  question: string;
  student_id?: string | null;
  chapter_id?: string | null;
  experiment_id?: string | null;
  point_key?: string | null;
  knowledge_point_ids?: string[];
  allow_progress_lookup: boolean;
  allow_rag_lookup: boolean;
  conversation_history?: Array<{
    role: "user" | "assistant";
    content: string;
  }>;
  max_answer_chars?: number | null;
};

export type LearningAssistantSourceAsset = {
  path: string;
  file_name: string;
  kind: "figure" | "page" | string;
  caption?: string | null;
};

export type LearningAssistantSource = {
  chunk_id: string;
  source_file?: string | null;
  page_number?: number | null;
  text_preview: string;
  content_type?: string | null;
  caption?: string | null;
  section_path?: string[];
  assets?: LearningAssistantSourceAsset[];
};

export type LearningAssistantResponse = {
  answer: string;
  sources: LearningAssistantSource[];
  mode: string;
  classification: Record<string, unknown>;
  tool_calls: Array<Record<string, unknown>>;
  guardrail_decisions: Array<{
    code?: string;
    action?: string;
    reason?: string;
    [key: string]: unknown;
  }>;
  rag_trace?: Record<string, unknown>;
  review_required: boolean;
};

export type LearningAssistantRuntime = {
  checked_at: string;
  rag_runtime?: AIConfiguration["rag_runtime"];
  bge_status?: "not_required" | "checking" | "healthy" | "degraded" | "unreachable" | "not_configured" | string;
  bge_error?: string | null;
  bge_metrics?: {
    ok?: boolean;
    service?: string;
    request_ms?: number;
    config?: {
      embed_model?: string;
      rerank_model?: string;
      device?: string;
      use_fp16?: boolean;
      rerank_backend?: string;
      rerank_max_length?: number;
      offline?: boolean;
      [key: string]: unknown;
    };
    models?: {
      embed_loaded?: boolean;
      rerank_loaded?: boolean;
      [key: string]: unknown;
    };
    requests?: {
      embed?: number;
      rerank?: number;
      [key: string]: unknown;
    };
    process?: {
      uptime_seconds?: number;
      cpu_user_seconds?: number;
      cpu_system_seconds?: number;
      memory_rss_mb?: number | null;
      memory_high_water_mb?: number | null;
      thread_count?: number | null;
      [key: string]: unknown;
    };
    container?: {
      memory_current_mb?: number | null;
      memory_limit_mb?: number | null;
      cpu_usage_seconds?: number | null;
      cpu_user_seconds?: number | null;
      cpu_system_seconds?: number | null;
      cpu_throttled_seconds?: number | null;
      [key: string]: unknown;
    };
    warmup?: {
      enabled?: boolean;
      status?: "disabled" | "not_started" | "running" | "succeeded" | "failed" | string;
      trigger?: string | null;
      started_at?: string | null;
      finished_at?: string | null;
      duration_ms?: number | null;
      error?: string | null;
      models_ready?: boolean;
      [key: string]: unknown;
    };
    [key: string]: unknown;
  } | null;
};

export function getLearningAssistantRuntime(): Promise<LearningAssistantRuntime> {
  return api<LearningAssistantRuntime>("/api/admin/learning-assistant/runtime");
}

export function askLearningAssistant(request: LearningAssistantAskRequest): Promise<LearningAssistantResponse> {
  return postJson<LearningAssistantResponse>("/api/learning/assistant/ask", request);
}

export function streamLearningAssistant<T>(path: string, body: unknown, onEvent: Parameters<typeof postJsonStream<T>>[2]): Promise<void> {
  return postJsonStream<T>(path, body, onEvent);
}

export function getRagAssetUrl(path: string): string {
  return `${apiBase}/api/admin/rag-assets?path=${encodeURIComponent(path)}`;
}

export function getAuthenticatedHeaders(): Headers {
  const headers = new Headers();
  const token = getAuthToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  return headers;
}
