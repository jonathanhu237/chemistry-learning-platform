export type AuthUser = {
  id: string;
  username: string;
  role: "admin" | "teacher" | "student";
  display_name: string;
  status: string;
  student_id?: string | null;
  class_id?: string | null;
  class_name?: string | null;
};

export type LoginResponse = {
  access_token: string;
  token_type: "bearer";
  user: AuthUser;
};

export type StudentVideo = {
  media_id: string;
  title: string;
  stream_path?: string | null;
  thumbnail_path?: string | null;
  duration_seconds?: number | null;
};

export type HomeVideoFeedItem = {
  id: string;
  instance_id?: string;
  node_id: string;
  placement_node_id?: string | null;
  canonical_point_id?: string | null;
  chapter_id?: string | null;
  title: string;
  summary?: string | null;
  snippet?: string | null;
  catalog_path?: string[];
  badges?: string[];
  target?: StudentVideoLibraryRouteTarget | null;
  video: StudentVideo & { stream_path?: string | null };
};

export type HomeVideoFeedResponse = {
  status: "ok" | "empty";
  message?: string;
  topic?: string;
  next_cursor?: string | null;
  has_more?: boolean;
  batch_size?: number;
  pool_size?: number;
  repeat_mode?: "cycled" | "none";
  items: HomeVideoFeedItem[];
};

export type LegacyVideoPointItem = {
  id: string;
  node_id: string;
  chapter_id?: string | null;
  title: string;
  summary?: string | null;
  snippet?: string | null;
  catalog_path?: string[];
  media_count?: number;
  published_media_count?: number;
  thumbnail_path?: string | null;
  is_recommended?: boolean;
  recommended_order?: number | null;
};

export type LegacyVideoPointResponse = {
  status: "ok" | "empty";
  query: string;
  total: number;
  items: LegacyVideoPointItem[];
};

export type StudentLearningHero = {
  eyebrow?: string;
  title?: string;
  summary?: string;
};

export type StudentLearningElementBadge = {
  symbol: string;
  name: string;
  atomic_number?: number | null;
  card_focus?: string | null;
  card_relevance?: string | null;
  card_tags?: string[];
  group?: string | null;
  group_label?: string | null;
  period?: number | null;
  block?: string | null;
  state_at_20c?: string | null;
  common_valence?: string | null;
};

export type StudentLearningPropertyCard = {
  key: string;
  label: string;
  value: string;
  description: string;
};

export type StudentLearningProfileSummary = {
  profile_id: string;
  chapter_id: string;
  title: string;
  subtitle: string;
  family_number: string;
  family_name: string;
  element_symbols: string[];
};

export type StudentLearningProfile = StudentLearningProfileSummary & {
  hero: StudentLearningHero;
  default_element_symbol?: string | null;
  elements: StudentLearningElementBadge[];
  property_cards: StudentLearningPropertyCard[];
  family_common_properties?: StudentLearningPropertyCard[];
  property_sections?: Array<{
    key: string;
    title: string;
    subtitle: string;
    summary: string;
    formula: string;
    tone: string;
  }>;
};

export type StudentLearningPageResponse = {
  recommended_profile_id?: string | null;
  profiles: StudentLearningProfileSummary[];
  active_profile?: StudentLearningProfile | null;
};

export type StudentCatalogNodeKind = "directory" | "point";

export type StudentCatalogBreadcrumb = {
  node_id: string;
  title: string;
  node_kind: StudentCatalogNodeKind;
  chapter_id: string;
};

export type StudentCatalogNodeCard = {
  node_id: string;
  placement_node_id?: string | null;
  canonical_point_id?: string | null;
  canonical_point_title?: string | null;
  chapter_id: string;
  parent_id?: string | null;
  node_kind: StudentCatalogNodeKind;
  title: string;
  summary: string;
  status: string;
  display_order: number;
  actions?: string[];
  has_children: boolean;
  has_point_content: boolean;
  media_count: number;
  published_media_count: number;
};

export type StudentCatalogChapterResponse = {
  chapter_id: string;
  chapter_title: string;
  nodes: StudentCatalogNodeCard[];
};

export type StudentCatalogNodeResponse = {
  node: StudentCatalogNodeCard;
  breadcrumbs: StudentCatalogBreadcrumb[];
  children: StudentCatalogNodeCard[];
};

export type VideoLibraryTargetKind = "point_detail" | "chapter_detail" | "ai_chat";

export type StudentVideoLibraryRouteTarget = {
  kind: VideoLibraryTargetKind;
  route: string;
  node_id?: string | null;
  placement_node_id?: string | null;
  canonical_point_id?: string | null;
  source_node_id?: string | null;
  profile_id?: string | null;
  chapter_id?: string | null;
  catalog_path?: string[] | null;
  element_symbol?: string | null;
  point_title?: string | null;
};

export type StudentVideoLibraryResultItem = {
  id: string;
  type: string;
  title: string;
  subtitle: string;
  snippet: string;
  score: number;
  badges: string[];
  action_label: string;
  target?: StudentVideoLibraryRouteTarget | null;
  disabled_reason?: string | null;
};

export type StudentVideoLibraryResultGroup = {
  key: string;
  title: string;
  summary: string;
  items: StudentVideoLibraryResultItem[];
};

export type StudentVideoLibrarySearchResponse = {
  query: string;
  status: "ok" | "fallback" | "disabled" | "empty" | "error";
  backend: "local" | "elasticsearch" | "disabled";
  message: string;
  total: number;
  groups: StudentVideoLibraryResultGroup[];
};

export type StudentRelatedPoint = {
  node_id: string;
  placement_node_id?: string | null;
  canonical_point_id?: string | null;
  title: string;
  relation_type?: string | null;
  source_node_id?: string | null;
};

export type PointDetail = {
  node_id: string;
  canonical_node_id?: string;
  source_node_id?: string | null;
  placement_node_id?: string | null;
  canonical_point_id?: string | null;
  title: string;
  summary?: string | null;
  chapter_id?: string | null;
  breadcrumbs?: StudentCatalogBreadcrumb[];
  principle_text?: string | null;
  principle_equation?: string | null;
  phenomenon_explanation?: string | null;
  safety_note?: string | null;
  videos?: StudentVideo[];
  related_points?: StudentRelatedPoint[];
  assessment_context?: {
    point_node_id?: string | null;
    placement_node_id?: string | null;
    canonical_point_id?: string | null;
    chapter_id?: string | null;
    source_node_id?: string | null;
    catalog_path?: StudentCatalogBreadcrumb[];
  } | null;
};

export type AssessmentReportSummary = {
  id: string;
  title: string;
  report_type?: string;
  source_session_id?: string;
  score: number;
  correct_count: number;
  total_count: number;
  correct_rate?: number;
  wrong_count?: number;
  completed_at: string;
};

export type AssessmentReportListResponse = {
  reports: AssessmentReportSummary[];
};

export type LegacyReportGeneratedText = {
  text: string;
  source?: "ai" | "fallback";
  mode?: string;
  generated_at?: string | null;
};

export type LegacyWrongQuestionExplanation = {
  question_id: string;
  stem: string;
  experiment_title?: string;
  question_type?: string;
  submitted_answer: string;
  correct_answer: string;
  explanation: string;
  explanation_source?: "stored" | "fallback";
  options?: string[];
};

export type LegacyAssessmentReportDetail = AssessmentReportSummary & {
  ai_summary: LegacyReportGeneratedText;
  mistake_explanation?: LegacyReportGeneratedText | null;
  next_steps?: string;
  covered_experiments?: string[];
  wrong_questions: LegacyWrongQuestionExplanation[];
};

export type AssessmentMode = "smart" | "custom" | "point";
export type QuestionType = "single_choice" | "true_false" | "fill_blank";

export type SmartAssessmentStrategy = {
  enabled?: boolean;
  question_count?: number;
  untested_ratio_percent?: number;
  weak_tendency_percent?: number;
  max_questions_per_experiment?: number;
  weak_curve?: number;
  weak_max_bonus?: number;
};

export type SmartAssessmentCompositionSummary = {
  total_questions: number;
  target_question_count?: number;
  requested_question_count?: number | null;
  selected_point_count?: number;
  candidate_point_count?: number;
  untested_question_count?: number;
  measured_question_count?: number;
  custom_question_count?: number;
  untested_ratio_percent?: number;
  weak_tendency_percent?: number;
  max_questions_per_experiment?: number;
  warnings?: Record<string, unknown>;
};

export type PublicSmartAssessmentQuestion = {
  id: string;
  experiment_id?: string;
  experiment_title?: string;
  point_node_ids?: string[];
  canonical_point_ids?: string[];
  question_type: QuestionType;
  stem: string;
  options: Array<Record<string, unknown>>;
  related_chapter_ids?: string[];
  related_knowledge_point_ids?: string[];
};

export type SmartAssessmentPointSummary = {
  id: string;
  title: string;
  experiment_id?: string | null;
  experiment_title?: string | null;
  canonical_point_id?: string | null;
  mastery_score?: number | null;
  before_score?: number | null;
  after_score?: number | null;
  evidence_count?: number;
  source?: "measured" | "untested" | "custom" | "point";
  draw_tickets?: number | null;
  question_count?: number;
  reason?: string | null;
};

export type SmartAssessmentExperimentSummary = {
  id: string;
  code?: string;
  title: string;
  parent_code?: string | null;
  parent_title?: string | null;
  mastery_score?: number | null;
  evidence_count?: number;
  source?: "measured" | "untested" | "custom" | "point";
  draw_tickets?: number | null;
  question_count?: number;
  measured_point_count?: number;
  total_point_count?: number;
  weak_point_count?: number;
  reason?: string | null;
  points?: SmartAssessmentPointSummary[];
};

export type SmartAssessmentResponse = {
  status: "in_progress" | "completed";
  session_id: string;
  assessment_mode?: AssessmentMode;
  strategy?: SmartAssessmentStrategy;
  composition?: SmartAssessmentCompositionSummary;
  experiments?: SmartAssessmentExperimentSummary[];
  questions?: PublicSmartAssessmentQuestion[];
};

export type CustomAssessmentExperimentOption = {
  id: string;
  code: string;
  title: string;
  parent_code?: string | null;
  parent_title?: string | null;
  question_count: number;
};

export type CustomAssessmentOptionsSettings = {
  enabled: boolean;
  question_count_options: number[];
  default_question_count: number;
  max_question_count?: number;
  max_questions_per_experiment: number;
};

export type CustomAssessmentOptionsResponse = {
  settings: CustomAssessmentOptionsSettings;
  experiments: CustomAssessmentExperimentOption[];
};

export type SmartAssessmentAnswer = {
  question_id: string;
  answer: unknown;
};

export type SmartAssessmentWrongAnswer = {
  question_id: string;
  experiment_id?: string;
  experiment_title?: string;
  point_node_ids?: string[];
  canonical_point_ids?: string[];
  question_type?: string;
  stem: string;
  options?: Array<Record<string, unknown>>;
  submitted_answer?: unknown;
  correct_answer?: unknown;
  explanation?: string | null;
};

export type SmartAssessmentMasteryChange = {
  knowledge_point_id: string;
  point_node_id?: string | null;
  point_title?: string | null;
  experiment_id?: string | null;
  experiment_title?: string | null;
  canonical_point_id?: string | null;
  content?: string | null;
  before_score: number;
  after_score: number;
  delta: number;
};

export type SmartAssessmentReport = {
  session_id: string;
  assessment_mode?: AssessmentMode;
  strategy?: SmartAssessmentStrategy;
  composition?: SmartAssessmentCompositionSummary;
  experiments?: SmartAssessmentExperimentSummary[];
  correct_count: number;
  total_count: number;
  score: number;
  correct_rate: number;
  mastery_before_average?: number | null;
  mastery_after_average?: number | null;
  mastery_delta?: number | null;
  mastery_changes?: SmartAssessmentMasteryChange[];
  wrong_answers?: SmartAssessmentWrongAnswer[];
  next_recommendation?: string;
};

export type SmartAssessmentSubmitResponse = {
  status: "completed";
  report: SmartAssessmentReport;
  assessment_report?: AssessmentReportSummary | null;
};

export const apiBase = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const tokenKey = "chem_student_old_token";
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
    // The in-memory token is enough for tests and restricted browser contexts.
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

function apiErrorDetailText(detail: unknown): string {
  if (typeof detail === "string") return detail;
  if (detail && typeof detail === "object") {
    const message = (detail as { message?: unknown }).message;
    if (typeof message === "string") return message;
  }
  return "";
}

export function legacyStudentErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    const detail = apiErrorDetailText(error.detail);
    if (error.status === 401) return "登录状态已失效，请重新登录。";
    if (error.status === 404) return "暂未找到对应的实验学习内容。";
    if (error.status === 400) {
      if (detail.includes("Submitted answers must match")) return "本轮题目状态已变化，请返回评测重新开始。";
      return "当前提交内容不完整，请检查题目后重试。";
    }
    if (error.status === 409) {
      if (detail.includes("No active assessment session")) return "本轮测评已经提交或已失效，请返回评测重新开始。";
      if (detail.includes("question bank has changed")) return "题库内容已更新，请返回评测重新开始。";
      return "本轮测评状态已变化，请返回评测重新开始。";
    }
    if (error.status >= 500) return "学习服务暂不可用，请稍后再试。";
    return "当前操作未完成，请检查学习条件后重试。";
  }
  return "当前操作未完成，请稍后再试。";
}

async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
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

export function studentLogin(studentId: string, password: string): Promise<LoginResponse> {
  return postJson<LoginResponse>("/api/auth/student/login", { student_id: studentId, password });
}

export function loadCurrentUser(): Promise<AuthUser> {
  return api<AuthUser>("/api/auth/me");
}

export function loadHomeVideoFeed(limit = 18, cursor?: string | null): Promise<HomeVideoFeedResponse> {
  const params = new URLSearchParams({ limit: String(limit), topic: "all" });
  if (cursor) params.set("cursor", cursor);
  return api<HomeVideoFeedResponse>(`/api/student/home-video-feed?${params.toString()}`);
}

export function loadLegacyVideoPoints(query = "", limit = 200): Promise<LegacyVideoPointResponse> {
  const params = new URLSearchParams({ limit: String(limit) });
  if (query.trim()) params.set("q", query.trim());
  return api<LegacyVideoPointResponse>(`/api/student/legacy/video-points?${params.toString()}`);
}

export function searchVideoLibrary(query: string, limit = 24): Promise<StudentVideoLibrarySearchResponse> {
  const params = new URLSearchParams({ domain: "experiment_video", limit: String(limit), q: query });
  return api<StudentVideoLibrarySearchResponse>(`/api/student/video-library/search?${params.toString()}`);
}

export function loadLearningPage(profileId?: string | null): Promise<StudentLearningPageResponse> {
  const query = profileId ? `?profile_id=${encodeURIComponent(profileId)}` : "";
  return api<StudentLearningPageResponse>(`/api/student/learning-page${query}`);
}

export function loadChapterCatalog(chapterId: string): Promise<StudentCatalogChapterResponse> {
  return api<StudentCatalogChapterResponse>(`/api/student/chapters/${encodeURIComponent(chapterId)}/catalog`);
}

export function loadCatalogNode(nodeId: string): Promise<StudentCatalogNodeResponse> {
  return api<StudentCatalogNodeResponse>(`/api/student/catalog/nodes/${encodeURIComponent(nodeId)}`);
}

export function loadPointDetail(nodeId: string): Promise<PointDetail> {
  return api<PointDetail>(`/api/student/catalog/points/${encodeURIComponent(nodeId)}`);
}

export function startSmartAssessment(): Promise<SmartAssessmentResponse> {
  return postJson<SmartAssessmentResponse>("/api/student/smart-assessment/start", {});
}

export function startPointAssessment(pointNodeId: string): Promise<SmartAssessmentResponse> {
  return postJson<SmartAssessmentResponse>("/api/student/point-assessment/start", {
    point_node_id: pointNodeId,
  });
}

export function loadCustomAssessmentOptions(): Promise<CustomAssessmentOptionsResponse> {
  return api<CustomAssessmentOptionsResponse>("/api/student/custom-assessment/options");
}

export function startCustomAssessment(experimentIds: string[], questionCount: number): Promise<SmartAssessmentResponse> {
  return postJson<SmartAssessmentResponse>("/api/student/custom-assessment/start", {
    experiment_ids: experimentIds,
    question_count: questionCount,
  });
}

export function submitSmartAssessment(sessionId: string, answers: SmartAssessmentAnswer[]): Promise<SmartAssessmentSubmitResponse> {
  return postJson<SmartAssessmentSubmitResponse>("/api/student/legacy/smart-assessment/submit", {
    session_id: sessionId,
    answers,
  });
}

export function loadLegacyAssessmentReports(): Promise<AssessmentReportListResponse> {
  return api<AssessmentReportListResponse>("/api/student/legacy/reports");
}

export function loadLegacyAssessmentReport(reportId: string): Promise<LegacyAssessmentReportDetail> {
  return api<LegacyAssessmentReportDetail>(`/api/student/legacy/reports/${encodeURIComponent(reportId)}`);
}

export function mediaUrl(path?: string | null): string {
  if (!path) return "";
  if (/^https?:\/\//i.test(path)) return path;
  if (!authToken) return `${apiBase}${path}`;
  const separator = path.includes("?") ? "&" : "?";
  return `${apiBase}${path}${separator}access_token=${encodeURIComponent(authToken)}`;
}
