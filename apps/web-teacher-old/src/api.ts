export type User = {
  id: string;
  username: string;
  role: "platform_admin" | "admin" | "teacher" | "student";
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
const tokenKey = "chem_teacher_old_token";
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
