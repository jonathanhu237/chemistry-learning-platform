export type AuthUser = {
  id: string;
  username: string;
  role: "admin" | "teacher" | "student";
  display_name: string;
  status: string;
  must_change_password: boolean;
  password_version: number;
  student_id?: string | null;
  class_id?: string | null;
  class_name?: string | null;
};

export type LoginResponse = {
  access_token: string;
  token_type: "bearer";
  expires_at: string;
  user: AuthUser;
};

export type StudentAppFeatureFlags = {
  ai_assistant_enabled: boolean;
  feedback_enabled: boolean;
  student_ai_assistant_enabled: boolean;
  rag_access_enabled: boolean;
};

export type StudentAppConfigResponse = {
  features: StudentAppFeatureFlags;
};

export type PretestQuestionOption = {
  label?: string;
  key?: string;
  value?: string;
  text?: string;
  [key: string]: unknown;
};

export type PublicPretestQuestion = {
  id: string;
  question_type: "single_choice" | "true_false" | "fill_blank";
  stem: string;
  options: PretestQuestionOption[];
  area: string;
  related_chapter_ids: string[];
  related_knowledge_point_ids: string[];
};

export type PublicPosttestQuestion = {
  id: string;
  experiment_id: string;
  experiment_title: string;
  question_type: "single_choice" | "true_false" | "fill_blank";
  stem: string;
  options: PretestQuestionOption[];
  related_chapter_ids: string[];
  related_knowledge_point_ids: string[];
};

export type StudentPretestResponse = {
  status: "in_progress" | "completed";
  stage: 1 | 2 | null;
  questions: PublicPretestQuestion[];
};

export type StudentPretestAnswer = {
  question_id: string;
  answer: unknown;
};

export type StudentLearningArea = {
  area_id: string;
  area_name: string;
  enabled: boolean;
  parent_codes: string[];
  experiment_count: number;
  published_video_count: number;
  question_count: number;
};

export type StudentLearningHomeGroupSummary = {
  parent_code: string;
  parent_title: string;
  area_id: string;
  area_name: string;
  chapter_ids: string[];
  experiment_count: number;
  published_video_count: number;
  question_count: number;
  recommended: boolean;
};

export type StudentLearningHomeResponse = {
  recommended_area_id: string | null;
  recommended_parent_code: string | null;
  areas: StudentLearningArea[];
  groups: StudentLearningHomeGroupSummary[];
};

export type StudentLearningHero = {
  eyebrow: string;
  title: string;
  summary: string;
};

export type StudentLearningElementBadge = {
  symbol: string;
  name: string;
  atomic_number?: number | null;
  card_focus?: string | null;
  card_relevance?: string | null;
  card_tags?: string[];
  relative_atomic_mass?: string | null;
  group?: string | null;
  period?: number | null;
  block?: string | null;
  state_at_20c?: string | null;
  density?: string | null;
  rsc_url?: string | null;
  fact_source?: string | null;
  state?: string | null;
  group_label?: string | null;
  electron_configuration?: string | null;
  common_valence?: string | null;
  redox_tendency?: string | null;
  note?: string | null;
};

export type StudentLearningPropertyCard = {
  key: string;
  label: string;
  value: string;
  description: string;
};

export type StudentLearningPropertySection = {
  key: string;
  title: string;
  subtitle: string;
  summary: string;
  formula: string;
  tone: string;
};

export type StudentLearningReferenceMedia = {
  id: string;
  usage: string;
  asset_type: string;
  source_url: string;
  license: string;
  attribution: string;
  alt_text: string;
  local_path?: string | null;
  element_symbols: string[];
  property_keys: string[];
};

export type StudentCatalogNodeKind = "directory" | "point" | "hybrid" | "shortcut";

export type StudentCatalogBreadcrumb = {
  node_id: string;
  title: string;
  node_kind: StudentCatalogNodeKind;
  chapter_id: string;
};

export type StudentCatalogNodeCard = {
  node_id: string;
  chapter_id: string;
  parent_id?: string | null;
  node_kind: StudentCatalogNodeKind;
  title: string;
  summary: string;
  status: string;
  display_order: number;
  shortcut_target_node_id?: string | null;
  actions: string[];
  has_children: boolean;
  has_point_content: boolean;
  media_count: number;
  published_media_count: number;
  validation?: Record<string, unknown>;
  index_state?: Record<string, unknown> | null;
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

export type StudentPointVideo = {
  media_id: string;
  title: string;
  mime_type?: string | null;
  stream_path?: string | null;
  thumbnail_path?: string | null;
};

export type StudentRelatedPoint = {
  node_id: string;
  title: string;
  relation_type?: string | null;
  source_node_id?: string | null;
};

export type StudentPointDetailResponse = {
  node_id: string;
  canonical_node_id: string;
  source_node_id?: string | null;
  chapter_id: string;
  title: string;
  summary: string;
  breadcrumbs: StudentCatalogBreadcrumb[];
  principle_mode: "equation" | "text" | string;
  principle_equation?: string | null;
  principle_text?: string | null;
  phenomenon_explanation?: string | null;
  safety_note?: string | null;
  videos: StudentPointVideo[];
  has_video: boolean;
  no_video_reason?: string | null;
  related_points: StudentRelatedPoint[];
  assessment_context: {
    point_node_id: string;
    chapter_id: string;
    source_node_id?: string | null;
    catalog_path: StudentCatalogBreadcrumb[];
  };
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

export type StudentLearningProfile = {
  profile_id: string;
  chapter_id: string;
  title: string;
  subtitle: string;
  family_number: string;
  family_name: string;
  hero: StudentLearningHero;
  default_element_symbol?: string | null;
  element_symbols: string[];
  elements: StudentLearningElementBadge[];
  property_cards: StudentLearningPropertyCard[];
  family_common_properties?: StudentLearningPropertyCard[];
  property_sections: StudentLearningPropertySection[];
  reference_media?: StudentLearningReferenceMedia[];
};

export type StudentLearningPageResponse = {
  recommended_profile_id?: string | null;
  profiles: StudentLearningProfileSummary[];
  active_profile?: StudentLearningProfile | null;
};

export type VideoLibraryResultType = "video_point" | "experiment" | "chapter_experiment" | "knowledge_point" | "ai_prompt";
export type VideoLibraryTargetKind = "point_detail" | "chapter_detail" | "ai_chat";
export type VideoLibrarySearchStatus = "ok" | "fallback" | "disabled" | "empty" | "error";
export type VideoLibrarySearchBackend = "local" | "elasticsearch" | "disabled";
export type VideoLibraryBrowseChipKind = "phenomenon" | "reagent" | "chapter" | "element_family" | "knowledge";

export type StudentVideoLibraryRouteTarget = {
  kind: VideoLibraryTargetKind;
  route: string;
  node_id?: string | null;
  source_node_id?: string | null;
  profile_id?: string | null;
  chapter_id?: string | null;
  catalog_path?: string[] | null;
  property_key?: string | null;
  property_title?: string | null;
  element_symbol?: string | null;
  point_title?: string | null;
  context_title?: string | null;
  context_summary?: string | null;
  prompt?: string | null;
};

export type StudentVideoLibraryResultItem = {
  id: string;
  type: VideoLibraryResultType;
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

export type StudentVideoLibraryBrowseChip = {
  kind: VideoLibraryBrowseChipKind;
  label: string;
  query: string;
  profile_id?: string | null;
  chapter_id?: string | null;
  element_symbol?: string | null;
};

export type StudentVideoLibraryBrowseState = {
  recommended: StudentVideoLibraryResultItem[];
  recent: StudentVideoLibraryResultItem[];
  chips: StudentVideoLibraryBrowseChip[];
};

export type StudentVideoLibrarySearchResponse = {
  query: string;
  status: VideoLibrarySearchStatus;
  backend: VideoLibrarySearchBackend;
  message: string;
  total: number;
  groups: StudentVideoLibraryResultGroup[];
  browse: StudentVideoLibraryBrowseState;
};

export type PosttestExperimentSummary = {
  id: string;
  code: string;
  title: string;
  parent_code?: string | null;
  parent_title?: string | null;
};

export type StudentPosttestResponse = {
  status: "in_progress" | "completed";
  session_id: string;
  experiments: PosttestExperimentSummary[];
  questions: PublicPosttestQuestion[];
};

export type StudentPosttestAnswer = {
  question_id: string;
  answer: unknown;
};

export type StudentPosttestWrongAnswer = {
  question_id: string;
  experiment_id: string;
  experiment_title: string;
  question_type: string;
  stem: string;
  options: PretestQuestionOption[];
  submitted_answer: unknown;
  correct_answer: unknown;
  explanation?: string | null;
};

export type StudentPosttestMasteryChange = {
  knowledge_point_id: string;
  experiment_id?: string | null;
  experiment_title?: string | null;
  content?: string | null;
  before_score: number;
  after_score: number;
  delta: number;
};

export type StudentPosttestReport = {
  session_id: string;
  experiments: PosttestExperimentSummary[];
  correct_count: number;
  total_count: number;
  score: number;
  correct_rate: number;
  mastery_before_average?: number | null;
  mastery_after_average?: number | null;
  mastery_delta?: number | null;
  mastery_changes: StudentPosttestMasteryChange[];
  wrong_answers: StudentPosttestWrongAnswer[];
  next_recommendation: string;
};

export type StudentPosttestSubmitResponse = {
  status: "completed";
  report: StudentPosttestReport;
};

export type AgentChatMessage = {
  role: "user" | "assistant";
  content: string;
};

export type StudentAssistantFinalMetadata = {
  source_count?: number;
  sources?: Array<{
    title?: string | null;
    section?: string | null;
    chunk_id?: string | null;
    score?: number | null;
  }>;
  [key: string]: unknown;
};

export type StudentAssistantAskRequest = {
  question: string;
  context_type: "learning_home" | "experiment_group" | "experiment_detail" | "learning_profile" | "learning_point";
  context_title: string;
  context_summary: string;
  chapter_id?: string | null;
  experiment_id?: string | null;
  point_node_id?: string | null;
  source_node_id?: string | null;
  catalog_path?: string[];
  knowledge_point_ids?: string[];
  conversation_history?: AgentChatMessage[];
};

export type StudentAssistantGeneratedResponse = {
  text: string;
  source: "ai" | "fallback";
  mode: string;
  cached: boolean;
};

export type StudentFeedbackType = "system_issue" | "course_content" | "experiment_resource" | "ai_answer" | "other";

export type StudentFeedbackSubmit = {
  feedback_type: StudentFeedbackType;
  content: string;
  page_path?: string | null;
  chapter_id?: string | null;
  unit_id?: string | null;
  knowledge_point_id?: string | null;
  experiment_id?: string | null;
  point_node_id?: string | null;
  catalog_path?: string[];
  metadata?: Record<string, unknown>;
  attachment?: File | null;
};

export type StudentFeedbackSubmitResponse = {
  id: string;
  status: string;
  attachment_count: number;
};

export type StudentAssistantStreamEvent =
  | { event: "status"; message?: string }
  | { event: "delta"; delta?: string }
  | { event: "replace"; answer?: string }
  | { event: "final"; response?: StudentAssistantFinalMetadata | unknown }
  | { event: "error"; message?: string }
  | { event: string; [key: string]: unknown };

export type StudentFeedbackSubmitRequest = {
  feedback_type?: string;
  content: string;
  chapter_id?: string | null;
  unit_id?: string | null;
  knowledge_point_id?: string | null;
  experiment_id?: string | null;
  point_node_id?: string | null;
  catalog_path?: string[];
  page_path?: string | null;
  metadata?: Record<string, unknown>;
  attachment?: File | null;
};

export type StudentFeedbackItem = {
  id: string;
  student_id: string;
  class_id?: string | null;
  feedback_type: string;
  content: string;
  status: string;
  chapter_id?: string | null;
  unit_id?: string | null;
  knowledge_point_id?: string | null;
  experiment_id?: string | null;
  point_node_id?: string | null;
  catalog_path?: string[];
  page_path?: string | null;
  metadata?: Record<string, unknown>;
  attachment_count?: number;
  attachments?: Array<{
    id: string;
    feedback_id: string;
    original_file_name?: string | null;
    mime_type: string;
    file_size_bytes: number;
    created_at?: string | null;
  }>;
  created_at?: string | null;
  updated_at?: string | null;
};

export const apiBase = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
const tokenKey = "chem_student_token";

let authToken = localStorage.getItem(tokenKey) || "";

export function getAuthToken(): string {
  return authToken;
}

export function setAuthToken(token: string): void {
  authToken = token;
  if (token) {
    localStorage.setItem(tokenKey, token);
  } else {
    localStorage.removeItem(tokenKey);
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

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 409) {
      if (typeof error.detail === "string" && error.detail.includes("Pretest question bank")) {
        return "课前摸底题库暂未配置，请联系教师";
      }
      if (typeof error.detail === "string" && error.detail.includes("Posttest question bank")) {
        return "课后摸底题库暂未配置，请联系教师";
      }
      if (typeof error.detail === "string" && error.detail.includes("No learning experiments")) {
        return "请先进入至少一个实验详情页学习";
      }
      if (typeof error.detail === "string" && error.detail.includes("AI")) {
        return error.detail;
      }
      return "账号或题库配置异常，请联系教师";
    }
    if (typeof error.detail === "string") return error.detail;
    return "请求失败，请稍后重试";
  }
  if (error instanceof Error) return error.message;
  return "请求失败，请稍后重试";
}

async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
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

function postJson<T>(path: string, body: unknown): Promise<T> {
  return api<T>(path, { method: "POST", body: JSON.stringify(body) });
}

function appendOptionalFormValue(formData: FormData, key: string, value: unknown): void {
  const text = String(value || "").trim();
  if (text) formData.append(key, text);
}

function parseSseBlock(block: string): StudentAssistantStreamEvent | null {
  if (!block.trim()) return null;
  let event = "message";
  const dataLines: string[] = [];
  for (const rawLine of block.split("\n")) {
    const line = rawLine.trimEnd();
    if (line.startsWith("event:")) {
      event = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trimStart());
    }
  }
  let payload: Record<string, unknown> = {};
  if (dataLines.length) {
    try {
      const parsed = JSON.parse(dataLines.join("\n"));
      payload = typeof parsed === "object" && parsed ? parsed : {};
    } catch {
      payload = { message: dataLines.join("\n") };
    }
  }
  return { event, ...payload } as StudentAssistantStreamEvent;
}

export async function streamStudentAssistantAsk(
  payload: StudentAssistantAskRequest,
  onEvent: (event: StudentAssistantStreamEvent) => void,
): Promise<void> {
  const headers = new Headers({ "Content-Type": "application/json" });
  if (authToken) headers.set("Authorization", `Bearer ${authToken}`);
  const response = await fetch(`${apiBase}/api/student/assistant/ask/stream`, {
    method: "POST",
    headers,
    body: JSON.stringify(payload),
  });
  if (response.status === 401) setAuthToken("");
  if (!response.ok) {
    const contentType = response.headers.get("content-type") || "";
    const errorPayload = contentType.includes("application/json") ? await response.json() : await response.text();
    throw new ApiError(response.status, typeof errorPayload === "object" && errorPayload ? errorPayload.detail : errorPayload);
  }
  if (!response.body) throw new Error("AI 响应流不可用");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() || "";
    for (const block of blocks) {
      const event = parseSseBlock(block);
      if (event) onEvent(event);
    }
    if (done) break;
  }
  const event = parseSseBlock(buffer);
  if (event) onEvent(event);
}

export function studentLogin(studentId: string, password: string): Promise<LoginResponse> {
  return postJson<LoginResponse>("/api/auth/student/login", {
    student_id: studentId,
    password,
  });
}

export function changeStudentPassword(newPassword: string, currentPassword?: string): Promise<LoginResponse> {
  return postJson<LoginResponse>("/api/auth/student/password", {
    current_password: currentPassword || undefined,
    new_password: newPassword,
  });
}

export function loadCurrentUser(): Promise<AuthUser> {
  return api<AuthUser>("/api/auth/me");
}

export function getStudentAppConfig(): Promise<StudentAppConfigResponse> {
  return api<StudentAppConfigResponse>("/api/student/app-config");
}

export function startStudentPretest(): Promise<StudentPretestResponse> {
  return postJson<StudentPretestResponse>("/api/student/pretest/start", {});
}

export function submitStudentPretest(stage: 1 | 2, answers: StudentPretestAnswer[]): Promise<StudentPretestResponse> {
  return postJson<StudentPretestResponse>("/api/student/pretest/submit", {
    stage,
    answers,
  });
}

export function getStudentLearningHome(): Promise<StudentLearningHomeResponse> {
  return api<StudentLearningHomeResponse>("/api/student/learning-home");
}

export function getStudentLearningPage(profileId?: string | null): Promise<StudentLearningPageResponse> {
  const query = profileId ? `?profile_id=${encodeURIComponent(profileId)}` : "";
  return api<StudentLearningPageResponse>(`/api/student/learning-page${query}`);
}

export function getStudentChapterCatalog(chapterId: string): Promise<StudentCatalogChapterResponse> {
  return api<StudentCatalogChapterResponse>(`/api/student/chapters/${encodeURIComponent(chapterId)}/catalog`);
}

export function getStudentCatalogNode(nodeId: string): Promise<StudentCatalogNodeResponse> {
  return api<StudentCatalogNodeResponse>(`/api/student/catalog/nodes/${encodeURIComponent(nodeId)}`);
}

export function getStudentCatalogPointDetail(nodeId: string): Promise<StudentPointDetailResponse> {
  return api<StudentPointDetailResponse>(`/api/student/catalog/points/${encodeURIComponent(nodeId)}`);
}

export function searchStudentVideoLibrary(query = "", limit = 24): Promise<StudentVideoLibrarySearchResponse> {
  const params = new URLSearchParams({ domain: "experiment_video", limit: String(limit) });
  if (query.trim()) params.set("q", query.trim());
  return api<StudentVideoLibrarySearchResponse>(`/api/student/video-library/search?${params.toString()}`);
}

export function startStudentPosttest(): Promise<StudentPosttestResponse> {
  return postJson<StudentPosttestResponse>("/api/student/posttest/start", {});
}

export function submitStudentPosttest(sessionId: string, answers: StudentPosttestAnswer[]): Promise<StudentPosttestSubmitResponse> {
  return postJson<StudentPosttestSubmitResponse>("/api/student/posttest/submit", {
    session_id: sessionId,
    answers,
  });
}

export function generatePosttestAiSummary(sessionId: string): Promise<StudentAssistantGeneratedResponse> {
  return postJson<StudentAssistantGeneratedResponse>("/api/student/assistant/posttest-summary", {
    session_id: sessionId,
  });
}

export function explainPosttestMistakes(sessionId: string): Promise<StudentAssistantGeneratedResponse> {
  return postJson<StudentAssistantGeneratedResponse>("/api/student/assistant/posttest-mistakes", {
    session_id: sessionId,
  });
}

export function submitStudentFeedback(payload: StudentFeedbackSubmitRequest): Promise<StudentFeedbackItem> {
  const formData = new FormData();
  formData.append("feedback_type", payload.feedback_type || "other");
  formData.append("content", payload.content);
  appendOptionalFormValue(formData, "page_path", payload.page_path);
  appendOptionalFormValue(formData, "chapter_id", payload.chapter_id);
  appendOptionalFormValue(formData, "unit_id", payload.unit_id);
  appendOptionalFormValue(formData, "knowledge_point_id", payload.knowledge_point_id);
  appendOptionalFormValue(formData, "experiment_id", payload.experiment_id);
  appendOptionalFormValue(formData, "point_node_id", payload.point_node_id);
  if (payload.catalog_path?.length) formData.append("catalog_path", JSON.stringify(payload.catalog_path));
  const metadata = { ...(payload.metadata || {}) };
  if (payload.catalog_path?.length) metadata.catalog_path = payload.catalog_path;
  if (payload.point_node_id) metadata.point_node_id = payload.point_node_id;
  if (Object.keys(metadata).length) formData.append("metadata", JSON.stringify(metadata));
  if (payload.attachment) formData.append("attachment", payload.attachment);
  return api<StudentFeedbackItem>("/api/student/feedback", { method: "POST", body: formData });
}

export function studentMediaUrl(path: string): string {
  const separator = path.includes("?") ? "&" : "?";
  return `${apiBase}${path}${separator}access_token=${encodeURIComponent(authToken)}`;
}

export async function logout(): Promise<void> {
  if (!authToken) return;
  try {
    await postJson<{ ok: boolean }>("/api/auth/logout", {});
  } finally {
    setAuthToken("");
  }
}
