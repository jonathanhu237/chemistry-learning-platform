import { api, putJson } from "./http";

export type LearningBehaviorSettings = {
  assessment: {
    pretest_enabled: boolean;
    pretest_question_count: number;
    posttest_enabled: boolean;
    posttest_question_count: number;
    smart_assessment: SmartAssessmentSettings;
    custom_assessment: CustomAssessmentSettings;
  };
  learning_features: {
    ai_assistant_enabled: boolean;
    feedback_enabled: boolean;
    student_review_preview_enabled: boolean;
  };
};

export type SmartAssessmentSettings = {
  enabled: boolean;
  question_count: number;
  untested_ratio_percent: number;
  weak_tendency_percent: number;
  max_questions_per_experiment: number;
  weak_curve: number;
  weak_max_bonus: number;
};

export type CustomAssessmentSettings = {
  enabled: boolean;
  default_question_count: number;
  max_question_count: number;
  max_questions_per_experiment: number;
};

export type PlatformSettingsResponse = {
  settings: LearningBehaviorSettings;
  can_edit: boolean;
};

export type AIProviderRole = {
  role: string;
  provider: "openai";
  base_url: string;
  model: string;
  api_key_configured: boolean;
  api_key_fingerprint?: string | null;
};

export type TextbookRAGConfiguration = {
  enabled: boolean;
  elasticsearch_url: string;
  index_name: string;
  embedding: AIProviderRole;
  rerank: AIProviderRole;
  embedding_dimension: number;
  keyword_top_k: number;
  vector_top_k: number;
  rerank_top_k: number;
  final_top_k: number;
  min_rerank_score: number;
  timeout_seconds: number;
};

export type AIConfiguration = {
  provider: "openai";
  base_url: string;
  model: string;
  connection_check_interval_minutes: number;
  api_key_configured: boolean;
  api_key_fingerprint?: string | null;
  enabled_features: {
    rag_access_enabled: boolean;
    student_ai_assistant: boolean;
    student_learning_analytics: boolean;
    question_bank_assistant: boolean;
    teacher_learning_analytics: boolean;
  };
  status: {
    ready: boolean;
    message: string;
    effective_mode: string;
    connectivity_status: "not_configured" | "untested" | "connected" | "failed" | "stale";
    last_checked_at?: string | null;
    last_check_message?: string | null;
    check_interval_minutes: number;
    next_check_due_at?: string | null;
    recent_request_count: number;
    recent_error_count: number;
    last_request_at?: string | null;
    last_error_at?: string | null;
    usage_buckets: Array<{
      bucket: string;
      request_count: number;
      error_count: number;
    }>;
    usage_trends: Partial<Record<
      "1d" | "7d" | "30d",
      {
        range: "1d" | "7d" | "30d";
        bucket_unit: "hour" | "half_day" | "day";
        buckets: Array<{
          bucket: string;
          request_count: number;
          error_count: number;
        }>;
      }
    >>;
    last_request_summary?: {
      called_at: string;
      channel: string;
      status: "success" | "error";
    } | null;
  };
  reasoning_summary?: {
    enabled: boolean;
    status: "not_configured" | "untested" | "supported" | "unsupported" | "failed";
    source: "reasoning_summary" | "agent_trace";
    message: string;
    last_checked_at?: string | null;
  };
  student_ai_policy: {
    active: boolean;
    version: string;
    model: string;
    coverage: string[];
    recent_decision_count: number;
    invalid_decision_count: number;
    outcomes: Array<{
      mode: string;
      label: string;
      count: number;
    }>;
  };
  rag_runtime?: {
    rag_enabled: boolean;
    hybrid_bge_enabled: boolean;
    bge_service_required: boolean;
    bge_service_url: string;
    query_generation_enabled: boolean;
    vector_top_k: number;
    rerank_top_k: number;
    final_top_k: number;
    status: string;
    message: string;
    textbook_rag_enabled?: boolean;
    textbook_rag_status?: string;
    textbook_rag_message?: string;
    textbook_rag_index?: string;
    textbook_rag_models?: Record<string, string>;
    textbook_rag_diagnostics?: Record<string, unknown>;
  };
  chat_provider?: AIProviderRole | null;
  textbook_rag?: TextbookRAGConfiguration | null;
  can_edit: boolean;
};

export type AIConfigurationUpdate = {
  provider: "openai";
  base_url: string;
  model: string;
  connection_check_interval_minutes: number;
  api_key?: string | null;
  enabled_features: AIConfiguration["enabled_features"];
  chat_provider?: {
    provider: "openai";
    base_url: string;
    model: string;
    api_key?: string | null;
  } | null;
  textbook_rag?: {
    enabled: boolean;
    elasticsearch_url: string;
    index_name: string;
    embedding: {
      provider: "openai";
      base_url: string;
      model: string;
      api_key?: string | null;
    };
    rerank: {
      provider: "openai";
      base_url: string;
      model: string;
      api_key?: string | null;
    };
    embedding_dimension: number;
    keyword_top_k: number;
    vector_top_k: number;
    rerank_top_k: number;
    final_top_k: number;
    min_rerank_score: number;
    timeout_seconds: number;
  } | null;
};

export function getPlatformSettings(): Promise<PlatformSettingsResponse> {
  return api<PlatformSettingsResponse>("/api/admin/platform-settings");
}

export function updatePlatformSettings(values: LearningBehaviorSettings): Promise<PlatformSettingsResponse> {
  return putJson<PlatformSettingsResponse>("/api/admin/platform-settings", values);
}

export function getAIConfiguration(): Promise<AIConfiguration> {
  return api<AIConfiguration>("/api/admin/ai-configuration");
}

export function updateAIConfiguration(values: AIConfigurationUpdate): Promise<AIConfiguration> {
  return putJson<AIConfiguration>("/api/admin/ai-configuration", values);
}
