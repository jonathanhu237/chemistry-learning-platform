export type User = {
  id: string;
  username: string;
  role: "admin" | "teacher" | "student";
  display_name: string;
  status: string;
  must_change_password?: boolean;
};

export type ClassItem = {
  id: string;
  class_name: string;
  description?: string | null;
  status: string;
  student_count: number;
};

export type RosterStudent = {
  id: string;
  class_id: string;
  student_id: string;
  student_name: string;
  status: "pending" | "active" | "disabled";
  activation_mode: "default_password" | "self_registration";
  activated: boolean;
  user_id?: string | null;
  activated_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type RosterImportResult = {
  import_id: string;
  mode: "upsert" | "overwrite";
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  disabled_missing: number;
};

export type RegistrationSettings = {
  mode: "roster_only" | "self_registration";
  default_password_policy: string;
  default_password_mode: "student_id" | "shared";
  has_default_password: boolean;
  source?: "system_default" | "class" | null;
};

export type LearningBehaviorSettings = {
  assessment: {
    pretest_enabled: boolean;
    pretest_question_count: number;
    posttest_enabled: boolean;
    posttest_question_count: number;
  };
  learning_features: {
    ai_assistant_enabled: boolean;
    feedback_enabled: boolean;
    student_review_preview_enabled: boolean;
  };
};

export type PlatformSettingsResponse = {
  settings: LearningBehaviorSettings;
  can_edit: boolean;
};

export type FeedbackStatus = "open" | "in_progress" | "resolved" | "archived";

export type FeedbackType = "course_content" | "experiment_resource" | "ai_answer" | "system_issue" | "other";

export type FeedbackItem = {
  id: string;
  student_id: string;
  class_id?: string | null;
  student_name_snapshot?: string | null;
  class_name_snapshot?: string | null;
  feedback_type: FeedbackType;
  content: string;
  status: FeedbackStatus;
  chapter_id?: string | null;
  unit_id?: string | null;
  knowledge_point_id?: string | null;
  experiment_id?: string | null;
  page_path?: string | null;
  source_event_id?: number | null;
  handler_user_id?: string | null;
  handler_display_name?: string | null;
  internal_note?: string | null;
  metadata?: Record<string, unknown>;
  resolved_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type FeedbackSummary = {
  total_count: number;
  open_count: number;
  in_progress_count: number;
  resolved_count: number;
  archived_count: number;
  recent_count: number;
};

export type FeedbackListResponse = ApiList<FeedbackItem>;

export type FeedbackUpdate = {
  status?: FeedbackStatus;
  internal_note?: string | null;
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
  can_edit: boolean;
};

export type AIConfigurationUpdate = {
  provider: "openai";
  base_url: string;
  model: string;
  connection_check_interval_minutes: number;
  api_key?: string | null;
  enabled_features: AIConfiguration["enabled_features"];
};

export type Chapter = {
  chapter_id: string;
  area_id?: string | null;
  chapter_number?: number;
  chapter_title: string;
  element_area?: string | null;
  knowledge_point_count?: number;
  visible_experiment_count?: number;
  question_count?: number;
};

export type LearningResourceKnowledgePoint = {
  knowledge_point_id: string;
  content: string;
};

export type LearningResourceUnit = {
  unit_id: string;
  unit_index?: number | null;
  unit_title: string;
  knowledge_point_count: number;
  knowledge_points: LearningResourceKnowledgePoint[];
};

export type LearningResourceExperiment = {
  id: string;
  code?: string;
  title: string;
  status: string;
  display_order?: number | null;
  media_count: number;
  question_count: number;
};

export type LearningResourceGroup = {
  id: string;
  kind: "chapter" | "general";
  chapter_id: string;
  chapter_number?: number | null;
  title: string;
  subtitle?: string | null;
  area_id: string;
  area_name: string;
  knowledge_unit_count: number;
  knowledge_point_count: number;
  experiment_count: number;
  question_count: number;
  media_count: number;
  units: LearningResourceUnit[];
  experiments: LearningResourceExperiment[];
};

export type LearningResourceArea = {
  area_id: string;
  area_name: string;
  kind: "theory" | "general";
  group_ids: string[];
  metrics: {
    group_count: number;
    knowledge_unit_count: number;
    knowledge_point_count: number;
    experiment_count: number;
    question_count: number;
    media_count: number;
  };
};

export type LearningResourceOverview = {
  metrics: {
    knowledge_unit_count: number;
    knowledge_point_count: number;
    experiment_count: number;
    media_resource_count: number;
    question_count: number;
  };
  areas: LearningResourceArea[];
  groups: LearningResourceGroup[];
};

export type ChapterBinding = {
  chapter_id: string;
  chapter_title?: string;
  chapter_number?: number;
  coverage_type: "primary" | "partial" | "supporting";
  notes?: string | null;
  sort_order?: number;
};

export type MediaResource = {
  binding_id?: string;
  media_id?: string;
  title?: string;
  original_file_name?: string;
  mime_type?: string;
  file_size_bytes?: number;
  upload_status?: string;
  binding_status?: string;
  point_key?: string | null;
  point_title?: string | null;
  published_at?: string;
};

export type Experiment = {
  id: string;
  code: string;
  title: string;
  title_en?: string;
  summary?: string;
  metadata?: Record<string, unknown>;
  status: "draft" | "published" | "archived";
  display_order: number;
  chapter_bindings: ChapterBinding[];
  media_resources: MediaResource[];
  published_question_count: number;
  draft_question_count: number;
  generated_draft_count: number;
};

export type MediaAsset = {
  id: string;
  title: string;
  original_file_name: string;
  relative_path?: string;
  mime_type?: string | null;
  file_size_bytes?: number | null;
  upload_status: string;
  error_reason?: string | null;
  created_at?: string;
  updated_at?: string;
  association_count?: number;
};

export type ExperimentVideoPointResource = {
  binding_id: string;
  experiment_id: string;
  experiment_title?: string;
  binding_title?: string | null;
  binding_status: string;
  point_key?: string | null;
  point_title?: string | null;
  media_id: string;
  media_title: string;
  title?: string;
  original_file_name: string;
  mime_type?: string | null;
  file_size_bytes?: number | null;
  upload_status: string;
  error_reason?: string | null;
  published_at?: string | null;
  created_at?: string;
  updated_at?: string;
};

export type ExperimentVideoPoint = {
  point_key: string;
  point_title: string;
  source: "candidate" | "stored" | "legacy";
  resources: ExperimentVideoPointResource[];
  resource_count: number;
  published_count: number;
};

export type ExperimentVideoPointsResponse = {
  experiment: {
    id: string;
    code: string;
    title: string;
    status: Experiment["status"];
  };
  points: ExperimentVideoPoint[];
  total_points: number;
  total_resources: number;
  published_resources: number;
};

export type QuestionBankSummary = Experiment & {
  banks: Array<{
    id: string;
    experiment_id: string;
    bank_kind: string;
    title: string;
    status: string;
    question_count: number;
    published_count: number;
    draft_count: number;
  }>;
};

export type Question = {
  id: string;
  experiment_id: string;
  experiment_code?: string;
  experiment_title?: string;
  bank_kind?: string;
  question_type: "single_choice" | "true_false" | "fill_blank";
  stem: string;
  options: Array<{ label?: string; text?: string } | string>;
  answer: Record<string, unknown>;
  explanation?: string;
  difficulty?: string;
  status: string;
  related_chapter_ids?: string[];
  related_knowledge_point_ids?: string[];
  source_chunk_ids?: string[];
  source_refs?: Array<Record<string, unknown>>;
  created_at?: string;
  updated_at?: string;
};

export type QuestionBankChapterSummary = {
  chapter_id: string;
  chapter_number?: number | null;
  chapter_title: string;
  element_area?: string | null;
  total_count: number;
  choice_count: number;
  true_false_count: number;
  fill_blank_count: number;
  enabled_count: number;
  disabled_count: number;
  draft_count?: number;
  archived_count?: number;
  linked_experiment_count: number;
  updated_at?: string | null;
};

export type ChapterQuestion = Question & {
  chapter_ids?: string[];
  chapter_titles?: string[];
};

export type QuestionBankAssistantAction = {
  action_type: "add_question" | "repair_question" | "disable_question" | "coverage_report";
  title?: string;
  summary?: string;
  question_id?: string;
  question_type?: Question["question_type"];
  stem?: string;
  original_stem?: string;
  suggested_stem?: string;
  options?: Array<{ label?: string; text?: string } | string>;
  answer?: Record<string, unknown>;
  explanation?: string;
  counts?: Record<string, number>;
};

export type QuestionBankAssistantPreview = {
  proposal_id: string;
  intent: "add_questions" | "repair_question" | "coverage_check" | "disable_question";
  mode: string;
  mutates_bank: boolean;
  summary: string;
  warnings: string[];
  target: {
    chapter_id?: string | null;
    chapter_title?: string | null;
    experiment_id?: string | null;
    question_id?: string | null;
  };
  actions: QuestionBankAssistantAction[];
  source_refs: Array<Record<string, unknown>>;
};

export type QuestionDraft = {
  id: string;
  generation_id: string;
  experiment_id: string;
  experiment_code?: string;
  experiment_title?: string;
  payload: Record<string, unknown>;
  validation_errors: string[];
  status: string;
  prompt?: string;
  mode?: string;
  warning?: string;
  created_at?: string;
};

export type AnalyticsDashboard = {
  class_id: string;
  metrics: {
    class_size: number;
    active_students: number;
    published_experiments: number;
    completion_rate: number;
    average_score: number;
    missing_students: number;
  };
  experiments: Experiment[];
  matrix: Array<{
    student_id: string;
    student_name: string;
    status?: string;
    experiments: Record<
      string,
      {
        status: string;
        completion_percent: number;
        best_score: number | null;
        attempt_count: number;
      }
    >;
  }>;
  recent_activity: Array<Record<string, unknown>>;
  missing_students: Array<Record<string, unknown>>;
};

export type ApiList<T> = {
  items: T[];
  total: number;
};

export const apiBase = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");

let authToken = localStorage.getItem("chem_admin_token") || "";

export function getAuthToken(): string {
  return authToken;
}

export function setAuthToken(token: string): void {
  authToken = token;
  if (token) {
    localStorage.setItem("chem_admin_token", token);
  } else {
    localStorage.removeItem("chem_admin_token");
  }
}

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(typeof detail === "string" ? detail : `HTTP ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (authToken) {
    headers.set("Authorization", `Bearer ${authToken}`);
  }
  const response = await fetch(`${apiBase}${path}`, { ...options, headers });
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();
  if (response.status === 401) {
    setAuthToken("");
  }
  if (!response.ok) {
    throw new ApiError(response.status, typeof payload === "object" && payload ? payload.detail : payload);
  }
  return payload as T;
}

export function postJson<T>(path: string, body: unknown): Promise<T> {
  return api<T>(path, { method: "POST", body: JSON.stringify(body) });
}

export function patchJson<T>(path: string, body: unknown): Promise<T> {
  return api<T>(path, { method: "PATCH", body: JSON.stringify(body) });
}

export function putJson<T>(path: string, body: unknown): Promise<T> {
  return api<T>(path, { method: "PUT", body: JSON.stringify(body) });
}

export function formatBytes(value?: number | null): string {
  if (!value) return "-";
  if (value > 1024 * 1024) return `${(value / 1024 / 1024).toFixed(1)} MB`;
  if (value > 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${value} B`;
}
