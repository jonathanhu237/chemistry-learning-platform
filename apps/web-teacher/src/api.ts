export type User = {
  id: string;
  username: string;
  role: "teacher" | "student";
  display_name: string;
  status: string;
};

export type TeacherAccount = User & {
  must_change_password: boolean;
};

export type LoginResponse = {
  access_token: string;
  token_type: string;
  user: User;
};

export type TeacherDemoMetric = {
  key: string;
  label: string;
  value: number | string;
  unit?: string;
  description?: string;
};

export type TeacherDemoLoopStep = {
  title: string;
  description: string;
};

export type TeacherDemoOverview = {
  metrics: TeacherDemoMetric[];
  loop: TeacherDemoLoopStep[];
  resource_summary: Record<string, number | string>;
};

export type TeacherDemoVideoResource = {
  node_id: string;
  chapter_id?: string | null;
  title: string;
  summary?: string;
  catalog_path: string[];
  media_count: number;
  published_media_count: number;
  question_count: number;
  published_question_count: number;
  has_video: boolean;
  is_recommended: boolean;
  resource_status: string;
};

export type TeacherDemoVideoResources = {
  total: number;
  items: TeacherDemoVideoResource[];
};

export type TeacherDemoQuestionResource = {
  node_id: string;
  chapter_id?: string | null;
  node_kind: "directory" | "point" | string;
  title: string;
  status: string;
  breadcrumb_titles: string[];
  experiment_id?: string | null;
  question_count: number;
  published_count: number;
  draft_count: number;
  choice_count: number;
  true_false_count: number;
  fill_blank_count: number;
  media_count: number;
  published_media_count: number;
  point_count: number;
};

export type TeacherDemoQuestionResources = {
  total: number;
  totals: Record<string, number | string | Record<string, number>>;
  items: TeacherDemoQuestionResource[];
};

export type TeacherDemoClassSummary = {
  id: string;
  class_name: string;
  description?: string | null;
  status: string;
  student_count: number;
  active_students: number;
  completion_rate: number;
  average_score: number;
  missing_students: number;
};

export type TeacherDemoClasses = {
  classes: TeacherDemoClassSummary[];
};

export type TeacherClassSummary = {
  id: string;
  class_name: string;
  description?: string | null;
  status: string;
  student_count?: number;
  active_students?: number;
  completion_rate?: number;
  average_score?: number;
  missing_students?: number;
};

export type TeacherStudentSummary = {
  id?: string;
  class_id?: string;
  student_id: string;
  student_name: string;
  username?: string;
  display_name?: string;
  status: string;
  activation_mode?: string;
  activated?: boolean;
  class_name?: string;
};

export type TeacherClassRegistrationSettings = {
  mode: "roster_only" | "self_registration" | string;
  default_password_policy: string;
  default_password_mode: "student_id" | "shared" | string;
  has_default_password: boolean;
  source?: string | null;
};

export type TeacherRosterImportResult = {
  import_id: string;
  mode: "upsert" | "overwrite" | string;
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  disabled_missing: number;
};

export type TeacherDemoStudentAnalytics = {
  student_id: string;
  student_name: string;
  average_score: number;
  evidence_count: number;
  attempt_count: number;
  status: string;
};

export type TeacherDemoAnalytics = {
  class_id: string;
  metrics: Record<string, number | string>;
  experiment_groups: Array<{ id?: string; title?: string; experiment_count?: number }>;
  students: TeacherDemoStudentAnalytics[];
};

export type TeacherDemoWeakPoint = {
  point_node_id?: string | null;
  point_key?: string | null;
  point_title: string;
  experiment_id?: string | null;
  experiment_title?: string | null;
  attempt_count: number;
  incorrect_count: number;
  incorrect_rate: number;
  representative_questions: Array<{ question_id: string; stem: string }>;
};

export type TeacherDemoWeakPoints = {
  items: TeacherDemoWeakPoint[];
  point_items: TeacherDemoWeakPoint[];
  total: number;
  point_total: number;
};

export type TeacherDemoEvaluationSystem = {
  evaluated_objects: string[];
  evidence_sources: string[];
  update_mechanism: string;
  score_bands: Array<{
    label: string;
    min_score?: number | null;
    max_score?: number | null;
    description: string;
  }>;
  outputs: string[];
};

export const apiBase = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const tokenKey = "chem_teacher_token";
let authToken = readStoredToken();

function readStoredToken(): string {
  try {
    return globalThis.localStorage?.getItem(tokenKey) || "";
  } catch {
    return "";
  }
}

export function getAuthToken(): string {
  return authToken;
}

export function setAuthToken(token: string): void {
  authToken = token;
  try {
    if (token) globalThis.localStorage?.setItem(tokenKey, token);
    else globalThis.localStorage?.removeItem(tokenKey);
  } catch {
    // Keep in-memory auth usable in tests and restricted browser contexts.
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

export function legacyTeacherErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 401) {
      if (error.detail === "Current password is invalid") return "当前密码不正确。";
      return "登录状态已失效，请重新登录。";
    }
    if (error.status >= 500) return "教学服务暂不可用，请稍后再试。";
    return "当前数据暂不可用，请稍后重试。";
  }
  return "当前数据暂不可用，请稍后重试。";
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers || {});
  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (authToken) headers.set("Authorization", `Bearer ${authToken}`);
  const response = await fetch(`${apiBase}${path}`, { ...options, headers });
  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json") ? await response.json() : await response.text();
  if (!response.ok) {
    const detail = typeof payload === "object" && payload ? (payload as { detail?: unknown }).detail : payload;
    if (response.status === 401 && detail !== "Current password is invalid") setAuthToken("");
    throw new ApiError(response.status, detail);
  }
  return payload as T;
}

function postJson<T>(path: string, body: unknown): Promise<T> {
  return api<T>(path, { method: "POST", body: JSON.stringify(body) });
}

function putJson<T>(path: string, body: unknown): Promise<T> {
  return api<T>(path, { method: "PUT", body: JSON.stringify(body) });
}

function patchJson<T>(path: string, body: unknown): Promise<T> {
  return api<T>(path, { method: "PATCH", body: JSON.stringify(body) });
}

export function teacherLogin(username: string, password: string): Promise<LoginResponse> {
  return postJson<LoginResponse>("/api/auth/login", { username, password });
}

export function loadCurrentUser(): Promise<User> {
  return api<User>("/api/auth/me");
}

export function changeCurrentPassword(payload: { current_password: string; new_password: string }): Promise<{ ok: boolean }> {
  return postJson<{ ok: boolean }>("/api/auth/password", payload);
}

export function createTeacherAccount(payload: {
  username: string;
  display_name: string;
  password: string;
  must_change_password?: boolean;
}): Promise<TeacherAccount> {
  return postJson<TeacherAccount>("/api/teacher/accounts/teachers", payload);
}

export function listTeacherAccounts(): Promise<TeacherAccount[]> {
  return api<TeacherAccount[]>("/api/teacher/accounts/teachers");
}

export function updateTeacherAccount(
  teacherId: string,
  payload: { display_name?: string; status?: "active" | "disabled"; must_change_password?: boolean },
): Promise<TeacherAccount> {
  return patchJson<TeacherAccount>(`/api/teacher/accounts/teachers/${encodeURIComponent(teacherId)}`, payload);
}

export function getTeacherDemoOverview(): Promise<TeacherDemoOverview> {
  return api<TeacherDemoOverview>("/api/teacher/legacy/teacher-demo/overview");
}

export function getTeacherDemoVideoResources(query = ""): Promise<TeacherDemoVideoResources> {
  const params = new URLSearchParams();
  if (query.trim()) params.set("q", query.trim());
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return api<TeacherDemoVideoResources>(`/api/teacher/legacy/teacher-demo/video-resources${suffix}`);
}

export function setLegacyVideoPointRecommendation(nodeId: string, recommended: boolean, sortOrder = 0): Promise<unknown> {
  return api(`/api/teacher/legacy/video-points/${encodeURIComponent(nodeId)}/recommendation`, {
    method: "PUT",
    body: JSON.stringify({ recommended, sort_order: sortOrder }),
  });
}

export function getTeacherDemoQuestionResources(): Promise<TeacherDemoQuestionResources> {
  return api<TeacherDemoQuestionResources>("/api/teacher/legacy/teacher-demo/question-resources");
}

export function listTeacherClasses(): Promise<TeacherClassSummary[]> {
  return api<TeacherClassSummary[]>("/api/teacher/classes");
}

export function createTeacherClass(payload: { class_name: string; description?: string }): Promise<TeacherClassSummary> {
  return postJson<TeacherClassSummary>("/api/teacher/classes", payload);
}

export function listTeacherClassStudents(classId: string): Promise<TeacherStudentSummary[]> {
  return api<TeacherStudentSummary[]>(`/api/teacher/classes/${encodeURIComponent(classId)}/students`);
}

export function createTeacherClassStudent(
  classId: string,
  payload: { student_id: string; student_name: string; status?: string; activation_mode?: string },
): Promise<TeacherStudentSummary> {
  return postJson<TeacherStudentSummary>(`/api/teacher/classes/${encodeURIComponent(classId)}/students`, {
    ...payload,
    status: payload.status || "pending",
    activation_mode: payload.activation_mode || "default_password",
  });
}

export function getTeacherClassRegistrationSettings(classId: string): Promise<TeacherClassRegistrationSettings> {
  return api<TeacherClassRegistrationSettings>(`/api/teacher/classes/${encodeURIComponent(classId)}/registration-settings`);
}

export function updateTeacherClassRegistrationSettings(
  classId: string,
  payload: { default_password_mode: "student_id" | "shared"; default_password?: string },
): Promise<TeacherClassRegistrationSettings> {
  return api<TeacherClassRegistrationSettings>(`/api/teacher/classes/${encodeURIComponent(classId)}/registration-settings`, {
    method: "PUT",
    body: JSON.stringify({
      mode: "roster_only",
      default_password_policy: "student_id_name_activation",
      ...payload,
    }),
  });
}

export function importTeacherClassRoster(classId: string, payload: { file: File; mode: "upsert" | "overwrite" }): Promise<TeacherRosterImportResult> {
  const formData = new FormData();
  formData.append("file", payload.file);
  formData.append("mode", payload.mode);
  return api<TeacherRosterImportResult>(`/api/teacher/classes/${encodeURIComponent(classId)}/roster/import`, {
    method: "POST",
    body: formData,
  });
}

export function getTeacherDemoClasses(): Promise<TeacherDemoClasses> {
  return api<TeacherDemoClasses>("/api/teacher/legacy/teacher-demo/classes");
}

export function getTeacherDemoClassAnalytics(classId: string): Promise<TeacherDemoAnalytics> {
  return api<TeacherDemoAnalytics>(`/api/teacher/legacy/teacher-demo/classes/${encodeURIComponent(classId)}/analytics`);
}

export function getTeacherDemoClassWeakPoints(classId: string): Promise<TeacherDemoWeakPoints> {
  return api<TeacherDemoWeakPoints>(`/api/teacher/legacy/teacher-demo/classes/${encodeURIComponent(classId)}/weak-points`);
}

export function getTeacherDemoEvaluationSystem(): Promise<TeacherDemoEvaluationSystem> {
  return api<TeacherDemoEvaluationSystem>("/api/teacher/legacy/teacher-demo/evaluation-system");
}

export type CatalogNodeKind = "directory" | "point";
export type CatalogPrincipleMode = "text" | "equation";

export type CatalogQuestionBankCounts = {
  question_count: number;
  published_count: number;
  draft_count: number;
  disabled_count?: number;
  choice_count: number;
  true_false_count: number;
  fill_blank_count: number;
  draft_candidate_count?: number;
  rejected_candidate_count?: number;
  published_candidate_count?: number;
  point_count?: number;
  directory_count?: number;
};

export type CatalogQuestionBankChapter = {
  chapter_id: string;
  chapter_number?: number | null;
  chapter_title: string;
  element_area?: string | null;
  point_count: number;
};

export type CatalogQuestionBankNode = {
  node_id: string;
  parent_id?: string | null;
  chapter_id: string;
  node_kind: CatalogNodeKind;
  title: string;
  summary?: string | null;
  status: string;
  display_order: number;
  canonical_point_id?: string | null;
  canonical_point_title?: string | null;
  content_status?: string | null;
  principle_mode?: CatalogPrincipleMode | string | null;
  principle_equation?: string | null;
  principle_text?: string | null;
  phenomenon_explanation?: string | null;
  safety_note?: string | null;
  media_count: number;
  published_media_count: number;
  evidence_status?: string;
  evidence_source_mode?: string;
  breadcrumb_titles: string[];
  root_node_id: string;
  experiment_id: string;
  descendant_point_count: number;
  counts: CatalogQuestionBankCounts;
};

export type CatalogQuestionBankResponse = {
  items: CatalogQuestionBankNode[];
  total: number;
  chapters: CatalogQuestionBankChapter[];
  chapter_id?: string | null;
  totals: CatalogQuestionBankCounts;
};

export type CatalogPointMediaBinding = {
  binding_id: string;
  node_id: string;
  media_id: string;
  title: string;
  binding_status: string;
  display_order: number;
  published_at?: string | null;
  metadata?: Record<string, unknown> | null;
  original_file_name?: string | null;
  mime_type?: string | null;
  playback_mime_type?: string | null;
  source_file_size_bytes?: number | null;
  playback_file_size_bytes?: number | null;
  playback_width?: number | null;
  playback_height?: number | null;
  playback_duration_seconds?: number | null;
  playback_fps?: number | null;
  playback_bitrate?: number | null;
  playback_video_codec?: string | null;
  playback_audio_codec?: string | null;
  playback_rendition_kind?: string | null;
  upload_status: string;
  processing_phase?: string | null;
  processing_progress?: number | null;
  error_reason?: string | null;
  has_thumbnail?: boolean;
  created_at?: string;
  updated_at?: string;
};

export type CatalogNodeDetail = {
  node: CatalogQuestionBankNode & {
    teacher_note?: string | null;
    validation?: { ok: boolean; errors: string[]; warnings: string[] };
  };
  breadcrumbs: Array<{ node_id: string; title: string; node_kind: CatalogNodeKind; chapter_id: string }>;
  children: CatalogQuestionBankNode[];
  point_content?: {
    node_id: string;
    canonical_point_id?: string | null;
    point_title: string;
    teacher_note?: string | null;
    principle_mode: CatalogPrincipleMode | string;
    principle_equation?: string | null;
    principle_text?: string | null;
    phenomenon_explanation?: string | null;
    safety_note?: string | null;
    content_status: string;
  } | null;
  media_bindings?: CatalogPointMediaBinding[];
  validation?: { ok: boolean; errors: string[]; warnings: string[] };
};

export type CatalogNodeCreatePayload = {
  chapter_id: string;
  parent_id?: string | null;
  node_kind: CatalogNodeKind;
  title: string;
  summary?: string | null;
  teacher_note?: string | null;
};

export type CatalogNodeUpdatePayload = {
  title?: string;
  summary?: string | null;
  teacher_note?: string | null;
};

export type CatalogPointContentPayload = {
  point_title: string;
  teacher_note?: string | null;
  principle_mode: CatalogPrincipleMode;
  principle_equation?: string | null;
  principle_text?: string | null;
  phenomenon_explanation?: string | null;
  safety_note?: string | null;
};

export type TeacherMediaUploadPolicy = {
  max_media_upload_mb: number;
  max_media_upload_bytes: number;
  allowed_extensions: string[];
};

export type TeacherMediaAsset = {
  id: string;
  title: string;
  original_file_name?: string | null;
  mime_type?: string | null;
  file_size_bytes?: number | null;
  upload_status: string;
  processing_phase?: string | null;
  processing_progress?: number | null;
  error_reason?: string | null;
  reused_existing?: boolean;
  duplicate_type?: string;
  created_at?: string;
  updated_at?: string;
};

export type CatalogPointMediaBindPayload = {
  media_asset_id: string;
  title?: string | null;
  metadata?: Record<string, unknown>;
};

export type Question = {
  id: string;
  experiment_id: string;
  question_type: "single_choice" | "true_false" | "fill_blank";
  stem: string;
  options: Array<{ label?: string; text?: string } | string>;
  answer: Record<string, unknown>;
  explanation?: string | null;
  difficulty?: string | null;
  status: string;
  metadata?: Record<string, unknown>;
};

export type QuestionDraft = {
  id: string;
  generation_id: string;
  experiment_id: string;
  status: "draft" | "published" | "rejected" | string;
  payload: Partial<Question> & Record<string, unknown>;
  validation_errors: string[];
  prompt?: string;
  mode?: string;
  warning?: string;
  created_at?: string;
};

export type LegacyPointGenerationResponse = {
  generation_id: string;
  mode: string;
  warning?: string;
  source_refs: Array<Record<string, unknown>>;
  evidence_package?: Record<string, unknown>;
  drafts: QuestionDraft[];
};

export type ApiList<T> = {
  items: T[];
  total: number;
};

export type AnalyticsPointScore = {
  point_node_id?: string | null;
  point_title: string;
  experiment_id?: string | null;
  experiment_code?: string | null;
  experiment_title?: string | null;
  family_id?: string | null;
  family_title?: string | null;
  mastery_score: number;
  score: number;
  evidence_count: number;
  updated_at?: string | null;
};

export type AnalyticsScoreCell = {
  status: string;
  mastery_score: number;
  score: number;
  evidence_count: number;
  attempt_count: number;
  points?: AnalyticsPointScore[];
};

export type AnalyticsDashboard = {
  class_id: string;
  metrics: {
    class_size: number;
    active_students: number;
    published_experiments: number;
    published_experiment_groups?: number;
    completion_rate: number;
    average_score: number;
    missing_students: number;
  };
  experiments: Array<{ id: string; code?: string; title: string }>;
  experiment_groups?: Array<{ id: string; code?: string; title: string; experiment_count: number }>;
  matrix: Array<{
    student_id: string;
    student_name: string;
    status?: string;
    average_score?: number;
    experiments: Record<string, AnalyticsScoreCell>;
    experiment_groups?: Record<string, AnalyticsScoreCell>;
  }>;
  recent_activity: Array<Record<string, unknown>>;
  missing_students: Array<Record<string, unknown>>;
};

export type StudentReport = {
  student?: Record<string, unknown>;
  progress?: Array<Record<string, unknown>>;
  latest_posttest_report?: {
    session_id: string;
    score?: number | null;
    correct_count: number;
    total_count: number;
    ai_summary?: { text: string; source: string; mode: string } | null;
    ai_mistake_explanation?: { text: string; source: string; mode: string } | null;
  } | null;
  weak_video_points?: Array<{ point_title: string; incorrect_rate: number; attempt_count: number }>;
};

export type AssessmentReportPromptSettings = {
  summary_prompt: string;
  mistake_prompt: string;
};

export type AssessmentReportPromptSettingsResponse = {
  settings: AssessmentReportPromptSettings;
  inherited_settings?: AssessmentReportPromptSettings | null;
  source: "global" | "class";
  has_override: boolean;
  supported_variables: string[];
  can_edit: boolean;
};

export type StudentAssessmentReportSummary = {
  id: string;
  student_id: string;
  class_id?: string | null;
  report_type: string;
  source_session_id: string;
  title: string;
  score: number;
  correct_count: number;
  total_count: number;
  correct_rate: number;
  wrong_count: number;
  completed_at: string;
};

export type StudentAssessmentReport = StudentAssessmentReportSummary & {
  summary: { text: string; source: string; mode: string };
  mistake_explanation: { text: string; source: string; mode: string };
  prompt_snapshot: Record<string, unknown>;
  payload: Record<string, unknown>;
};

export type AIEnabledFeatureScopes = {
  rag_access_enabled?: boolean;
  student_ai_assistant?: boolean;
  student_learning_analytics?: boolean;
  question_bank_assistant?: boolean;
  teacher_learning_analytics?: boolean;
};

export type AIProviderRoleResponse = {
  role: string;
  provider: string;
  base_url: string;
  model: string;
  api_key_configured: boolean;
  api_key_fingerprint?: string | null;
};

export type AIConfigurationResponse = {
  provider: string;
  base_url: string;
  model: string;
  connection_check_interval_minutes: number;
  api_key_configured: boolean;
  api_key_fingerprint?: string | null;
  enabled_features: AIEnabledFeatureScopes;
  status: {
    ready: boolean;
    message: string;
    effective_mode: string;
    connectivity_status: "not_configured" | "untested" | "connected" | "failed" | "stale" | string;
    last_checked_at?: string | null;
    last_check_message?: string | null;
    recent_request_count?: number;
    recent_error_count?: number;
    last_request_at?: string | null;
    last_error_at?: string | null;
  };
  chat_provider?: AIProviderRoleResponse | null;
  can_edit: boolean;
};

export type AIConfigurationUpdate = {
  provider: "openai";
  base_url: string;
  model: string;
  api_key?: string;
  connection_check_interval_minutes?: number;
  enabled_features?: AIEnabledFeatureScopes;
  chat_provider: {
    provider: "openai";
    base_url: string;
    model: string;
    api_key?: string;
  };
};

export function listCatalogQuestionBank(chapterId?: string): Promise<CatalogQuestionBankResponse> {
  const params = new URLSearchParams();
  if (chapterId) params.set("chapter_id", chapterId);
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return api<CatalogQuestionBankResponse>(`/api/teacher/question-banks/catalog${suffix}`);
}

export function getCatalogNode(nodeId: string): Promise<CatalogNodeDetail> {
  return api<CatalogNodeDetail>(`/api/teacher/catalog/nodes/${encodeURIComponent(nodeId)}`);
}

export function createCatalogNode(payload: CatalogNodeCreatePayload): Promise<CatalogNodeDetail> {
  return postJson<CatalogNodeDetail>("/api/teacher/catalog/nodes", payload);
}

export function updateCatalogNode(nodeId: string, payload: CatalogNodeUpdatePayload): Promise<CatalogNodeDetail> {
  return patchJson<CatalogNodeDetail>(`/api/teacher/catalog/nodes/${encodeURIComponent(nodeId)}`, payload);
}

export function changeCatalogNodeStatus(
  nodeId: string,
  action: "archive" | "restore" | "publish" | "unpublish",
  options: { includeSubtree?: boolean } = {},
): Promise<CatalogNodeDetail> {
  return postJson<CatalogNodeDetail>(`/api/teacher/catalog/nodes/${encodeURIComponent(nodeId)}/status`, { action, include_subtree: Boolean(options.includeSubtree) });
}

export function saveCatalogPointContent(nodeId: string, payload: CatalogPointContentPayload): Promise<CatalogNodeDetail> {
  return putJson<CatalogNodeDetail>(`/api/teacher/catalog/nodes/${encodeURIComponent(nodeId)}/point-content`, payload);
}

export function changeCatalogPointContentPublication(nodeId: string, action: "publish" | "unpublish" | "archive"): Promise<CatalogNodeDetail> {
  return postJson<CatalogNodeDetail>(`/api/teacher/catalog/nodes/${encodeURIComponent(nodeId)}/point-content/publication`, { action });
}

export function getTeacherMediaUploadPolicy(): Promise<TeacherMediaUploadPolicy> {
  return api<TeacherMediaUploadPolicy>("/api/teacher/media/upload-policy");
}

export function uploadTeacherMediaAsset(payload: { title: string; file: File }): Promise<TeacherMediaAsset> {
  const formData = new FormData();
  formData.append("title", payload.title);
  formData.append("file", payload.file);
  return api<TeacherMediaAsset>("/api/teacher/media/assets", { method: "POST", body: formData });
}

export function bindCatalogPointMedia(nodeId: string, payload: CatalogPointMediaBindPayload): Promise<{ binding_id: string; detail: CatalogNodeDetail }> {
  return postJson<{ binding_id: string; detail: CatalogNodeDetail }>(`/api/teacher/catalog/nodes/${encodeURIComponent(nodeId)}/media-bindings`, payload);
}

export function changeCatalogPointMediaBinding(bindingId: string, action: "publish" | "unpublish" | "delete"): Promise<CatalogNodeDetail> {
  return postJson<CatalogNodeDetail>(`/api/teacher/catalog/media-bindings/${encodeURIComponent(bindingId)}/${action}`, {});
}

export function listQuestionBankQuestions(params: URLSearchParams): Promise<ApiList<Question>> {
  return api<ApiList<Question>>(`/api/teacher/question-banks/questions?${params.toString()}`);
}

export function revokeQuestionToDraft(questionId: string): Promise<QuestionDraft> {
  return postJson<QuestionDraft>(`/api/teacher/question-banks/questions/${encodeURIComponent(questionId)}/revoke-to-draft`, {});
}

export function listQuestionDrafts(params: { pointNodeId?: string; canonicalPointId?: string; experimentId?: string }): Promise<ApiList<QuestionDraft>> {
  const search = new URLSearchParams();
  if (params.pointNodeId) search.set("point_node_id", params.pointNodeId);
  if (params.canonicalPointId) search.set("canonical_point_id", params.canonicalPointId);
  if (params.experimentId) search.set("experiment_id", params.experimentId);
  return api<ApiList<QuestionDraft>>(`/api/teacher/question-banks/drafts?${search.toString()}`);
}

export function generateLegacyPointQuestions(payload: {
  experiment_id: string;
  prompt: string;
  question_types: Array<Question["question_type"]>;
  count: number;
  difficulty?: string | null;
  chapter_ids?: string[];
  target_point_node_ids: string[];
}): Promise<LegacyPointGenerationResponse> {
  return postJson<LegacyPointGenerationResponse>("/api/teacher/question-banks/legacy-point-generate", payload);
}

export function publishQuestionDraft(draftId: string): Promise<Question> {
  return postJson<Question>(`/api/teacher/question-banks/drafts/${encodeURIComponent(draftId)}/publish`, {});
}

export function updateQuestionDraft(draftId: string, payload: { payload: QuestionDraft["payload"]; status?: "draft" | "published" | "rejected" }): Promise<QuestionDraft> {
  return patchJson<QuestionDraft>(`/api/teacher/question-banks/drafts/${encodeURIComponent(draftId)}`, payload);
}

export function rejectQuestionDraft(draftId: string): Promise<QuestionDraft> {
  return postJson<QuestionDraft>(`/api/teacher/question-banks/drafts/${encodeURIComponent(draftId)}/reject`, {});
}

export function getAnalyticsDashboard(classId: string): Promise<AnalyticsDashboard> {
  return api<AnalyticsDashboard>(`/api/teacher/analytics/classes/${encodeURIComponent(classId)}/dashboard`);
}

export function getStudentReport(classId: string, studentId: string): Promise<StudentReport> {
  return api<StudentReport>(`/api/teacher/analytics/classes/${encodeURIComponent(classId)}/students/${encodeURIComponent(studentId)}`);
}

export function getGlobalAssessmentReportPrompts(): Promise<AssessmentReportPromptSettingsResponse> {
  return api<AssessmentReportPromptSettingsResponse>("/api/teacher/assessment-report-prompts");
}

export function updateGlobalAssessmentReportPrompts(
  values: AssessmentReportPromptSettings,
): Promise<AssessmentReportPromptSettingsResponse> {
  return putJson<AssessmentReportPromptSettingsResponse>("/api/teacher/assessment-report-prompts", values);
}

export function resetGlobalAssessmentReportPrompts(): Promise<AssessmentReportPromptSettingsResponse> {
  return api<AssessmentReportPromptSettingsResponse>("/api/teacher/assessment-report-prompts", { method: "DELETE" });
}

export function getAIConfiguration(): Promise<AIConfigurationResponse> {
  return api<AIConfigurationResponse>("/api/teacher/ai-configuration");
}

export function updateAIConfiguration(payload: AIConfigurationUpdate): Promise<AIConfigurationResponse> {
  return putJson<AIConfigurationResponse>("/api/teacher/ai-configuration", payload);
}

export function listTeacherStudentAssessmentReports(classId: string, studentId: string): Promise<{ reports: StudentAssessmentReportSummary[] }> {
  return api<{ reports: StudentAssessmentReportSummary[] }>(
    `/api/teacher/classes/${encodeURIComponent(classId)}/students/${encodeURIComponent(studentId)}/assessment-reports`,
  );
}

export function getTeacherStudentAssessmentReport(classId: string, studentId: string, reportId: string): Promise<StudentAssessmentReport> {
  return api<StudentAssessmentReport>(
    `/api/teacher/classes/${encodeURIComponent(classId)}/students/${encodeURIComponent(studentId)}/assessment-reports/${encodeURIComponent(reportId)}`,
  );
}
