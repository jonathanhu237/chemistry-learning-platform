export type User = {
  id: string;
  username: string;
  role: "admin" | "teacher" | "student";
  display_name: string;
  status: string;
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
const tokenKey = "chem_backoffice_token";
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
    if (error.status === 401) return "登录状态已失效，请重新登录。";
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
  if (response.status === 401) setAuthToken("");
  if (!response.ok) {
    const detail = typeof payload === "object" && payload ? (payload as { detail?: unknown }).detail : payload;
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

export function getTeacherDemoOverview(): Promise<TeacherDemoOverview> {
  return api<TeacherDemoOverview>("/api/admin/legacy/teacher-demo/overview");
}

export function getTeacherDemoVideoResources(query = ""): Promise<TeacherDemoVideoResources> {
  const params = new URLSearchParams();
  if (query.trim()) params.set("q", query.trim());
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return api<TeacherDemoVideoResources>(`/api/admin/legacy/teacher-demo/video-resources${suffix}`);
}

export function setLegacyVideoPointRecommendation(nodeId: string, recommended: boolean, sortOrder = 0): Promise<unknown> {
  return api(`/api/admin/legacy/video-points/${encodeURIComponent(nodeId)}/recommendation`, {
    method: "PUT",
    body: JSON.stringify({ recommended, sort_order: sortOrder }),
  });
}

export function getTeacherDemoQuestionResources(): Promise<TeacherDemoQuestionResources> {
  return api<TeacherDemoQuestionResources>("/api/admin/legacy/teacher-demo/question-resources");
}

export function listTeacherClasses(): Promise<TeacherClassSummary[]> {
  return api<TeacherClassSummary[]>("/api/admin/classes");
}

export function createTeacherClass(payload: { class_name: string; description?: string }): Promise<TeacherClassSummary> {
  return postJson<TeacherClassSummary>("/api/admin/classes", payload);
}

export function listTeacherClassStudents(classId: string): Promise<TeacherStudentSummary[]> {
  return api<TeacherStudentSummary[]>(`/api/admin/classes/${encodeURIComponent(classId)}/students`);
}

export function createTeacherClassStudent(
  classId: string,
  payload: { student_id: string; student_name: string; status?: string; activation_mode?: string },
): Promise<TeacherStudentSummary> {
  return postJson<TeacherStudentSummary>(`/api/admin/classes/${encodeURIComponent(classId)}/students`, {
    ...payload,
    status: payload.status || "pending",
    activation_mode: payload.activation_mode || "default_password",
  });
}

export function getTeacherDemoClasses(): Promise<TeacherDemoClasses> {
  return api<TeacherDemoClasses>("/api/admin/legacy/teacher-demo/classes");
}

export function getTeacherDemoClassAnalytics(classId: string): Promise<TeacherDemoAnalytics> {
  return api<TeacherDemoAnalytics>(`/api/admin/legacy/teacher-demo/classes/${encodeURIComponent(classId)}/analytics`);
}

export function getTeacherDemoClassWeakPoints(classId: string): Promise<TeacherDemoWeakPoints> {
  return api<TeacherDemoWeakPoints>(`/api/admin/legacy/teacher-demo/classes/${encodeURIComponent(classId)}/weak-points`);
}

export function getTeacherDemoEvaluationSystem(): Promise<TeacherDemoEvaluationSystem> {
  return api<TeacherDemoEvaluationSystem>("/api/admin/legacy/teacher-demo/evaluation-system");
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
    experiments: Record<string, { status: string; mastery_score: number; score: number; evidence_count: number; attempt_count: number }>;
    experiment_groups?: Record<string, { status: string; mastery_score: number; score: number; evidence_count: number; attempt_count: number }>;
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

export function listCatalogQuestionBank(chapterId?: string): Promise<CatalogQuestionBankResponse> {
  const params = new URLSearchParams();
  if (chapterId) params.set("chapter_id", chapterId);
  const suffix = params.toString() ? `?${params.toString()}` : "";
  return api<CatalogQuestionBankResponse>(`/api/admin/question-banks/catalog${suffix}`);
}

export function getCatalogNode(nodeId: string): Promise<CatalogNodeDetail> {
  return api<CatalogNodeDetail>(`/api/admin/catalog/nodes/${encodeURIComponent(nodeId)}`);
}

export function createCatalogNode(payload: CatalogNodeCreatePayload): Promise<CatalogNodeDetail> {
  return postJson<CatalogNodeDetail>("/api/admin/catalog/nodes", payload);
}

export function updateCatalogNode(nodeId: string, payload: CatalogNodeUpdatePayload): Promise<CatalogNodeDetail> {
  return patchJson<CatalogNodeDetail>(`/api/admin/catalog/nodes/${encodeURIComponent(nodeId)}`, payload);
}

export function changeCatalogNodeStatus(
  nodeId: string,
  action: "archive" | "restore" | "publish" | "unpublish",
  options: { includeSubtree?: boolean } = {},
): Promise<CatalogNodeDetail> {
  return postJson<CatalogNodeDetail>(`/api/admin/catalog/nodes/${encodeURIComponent(nodeId)}/status`, { action, include_subtree: Boolean(options.includeSubtree) });
}

export function saveCatalogPointContent(nodeId: string, payload: CatalogPointContentPayload): Promise<CatalogNodeDetail> {
  return putJson<CatalogNodeDetail>(`/api/admin/catalog/nodes/${encodeURIComponent(nodeId)}/point-content`, payload);
}

export function changeCatalogPointContentPublication(nodeId: string, action: "publish" | "unpublish" | "archive"): Promise<CatalogNodeDetail> {
  return postJson<CatalogNodeDetail>(`/api/admin/catalog/nodes/${encodeURIComponent(nodeId)}/point-content/publication`, { action });
}

export function listQuestionBankQuestions(params: URLSearchParams): Promise<ApiList<Question>> {
  return api<ApiList<Question>>(`/api/admin/question-banks/questions?${params.toString()}`);
}

export function listQuestionDrafts(params: { pointNodeId?: string; canonicalPointId?: string; experimentId?: string }): Promise<ApiList<QuestionDraft>> {
  const search = new URLSearchParams();
  if (params.pointNodeId) search.set("point_node_id", params.pointNodeId);
  if (params.canonicalPointId) search.set("canonical_point_id", params.canonicalPointId);
  if (params.experimentId) search.set("experiment_id", params.experimentId);
  return api<ApiList<QuestionDraft>>(`/api/admin/question-banks/drafts?${search.toString()}`);
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
  return postJson<LegacyPointGenerationResponse>("/api/admin/question-banks/legacy-point-generate", payload);
}

export function publishQuestionDraft(draftId: string): Promise<Question> {
  return postJson<Question>(`/api/admin/question-banks/drafts/${encodeURIComponent(draftId)}/publish`, {});
}

export function rejectQuestionDraft(draftId: string): Promise<QuestionDraft> {
  return postJson<QuestionDraft>(`/api/admin/question-banks/drafts/${encodeURIComponent(draftId)}/reject`, {});
}

export function getAnalyticsDashboard(classId: string): Promise<AnalyticsDashboard> {
  return api<AnalyticsDashboard>(`/api/admin/analytics/classes/${encodeURIComponent(classId)}/dashboard`);
}

export function getStudentReport(classId: string, studentId: string): Promise<StudentReport> {
  return api<StudentReport>(`/api/admin/analytics/classes/${encodeURIComponent(classId)}/students/${encodeURIComponent(studentId)}`);
}

export function getGlobalAssessmentReportPrompts(): Promise<AssessmentReportPromptSettingsResponse> {
  return api<AssessmentReportPromptSettingsResponse>("/api/admin/assessment-report-prompts");
}

export function updateGlobalAssessmentReportPrompts(
  values: AssessmentReportPromptSettings,
): Promise<AssessmentReportPromptSettingsResponse> {
  return putJson<AssessmentReportPromptSettingsResponse>("/api/admin/assessment-report-prompts", values);
}

export function resetGlobalAssessmentReportPrompts(): Promise<AssessmentReportPromptSettingsResponse> {
  return api<AssessmentReportPromptSettingsResponse>("/api/admin/assessment-report-prompts", { method: "DELETE" });
}

export function listTeacherStudentAssessmentReports(classId: string, studentId: string): Promise<{ reports: StudentAssessmentReportSummary[] }> {
  return api<{ reports: StudentAssessmentReportSummary[] }>(
    `/api/admin/classes/${encodeURIComponent(classId)}/students/${encodeURIComponent(studentId)}/assessment-reports`,
  );
}

export function getTeacherStudentAssessmentReport(classId: string, studentId: string, reportId: string): Promise<StudentAssessmentReport> {
  return api<StudentAssessmentReport>(
    `/api/admin/classes/${encodeURIComponent(classId)}/students/${encodeURIComponent(studentId)}/assessment-reports/${encodeURIComponent(reportId)}`,
  );
}
