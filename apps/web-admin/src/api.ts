export type TeacherAccount = {
  id: string;
  username: string;
  role: "admin" | "teacher";
  display_name: string;
  status: "active" | "disabled";
  must_change_password: boolean;
  password_version: number;
  created_at?: string | null;
  updated_at?: string | null;
  last_login_at?: string | null;
};

export type WebAdminSession = {
  ok: boolean;
};

export type PreviewInfrastructure = {
  teacher_user_id: string;
  teacher_username?: string | null;
  teacher_display_name?: string | null;
  class_id: string;
  class_name: string;
  class_status: string;
  student_id: string;
  student_name: string;
  student_status: string;
  student_user_id?: string | null;
  user_status?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
  last_session_at?: string | null;
};

export class ApiError extends Error {
  status: number;
  detail: unknown;

  constructor(status: number, detail: unknown) {
    super(typeof detail === "string" ? detail : `HTTP ${status}`);
    this.status = status;
    this.detail = detail;
  }
}

const tokenStorageKey = "chem_web_admin_token";

function browserStorage(): Storage | null {
  try {
    return globalThis.localStorage ?? null;
  } catch {
    return null;
  }
}

let authToken = browserStorage()?.getItem(tokenStorageKey) || "";

export function getAuthToken(): string {
  return authToken;
}

export function setAuthToken(token: string): void {
  authToken = token;
  const storage = browserStorage();
  if (!storage) return;
  if (token) {
    storage.setItem(tokenStorageKey, token);
  } else {
    storage.removeItem(tokenStorageKey);
  }
}

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (typeof error.detail === "string") return translateDetail(error.detail);
    if (error.detail && typeof error.detail === "object" && "detail" in error.detail) {
      const detail = (error.detail as { detail?: unknown }).detail;
      if (typeof detail === "string") return translateDetail(detail);
    }
    return `请求失败（${error.status}）`;
  }
  return error instanceof Error ? error.message : "请求失败";
}

function translateDetail(detail: string): string {
  const messages: Record<string, string> = {
    "Invalid web admin token": "运维访问令牌无效",
    "WEB_ADMIN_ACCESS_TOKEN is not configured": "运维访问令牌未配置",
    "Teacher account not found": "教师账号不存在",
    "Username already exists": "账号已存在",
    "Username and display name are required": "账号和显示名不能为空",
    "Display name is required": "显示名不能为空",
    "Teacher account has owned records; disable it instead": "该账号已有业务归属记录，请改用停用",
  };
  return messages[detail] || detail;
}

async function parseResponse(response: Response): Promise<unknown> {
  const contentType = response.headers.get("content-type") || "";
  if (contentType.includes("application/json")) {
    return response.json();
  }
  return response.text();
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  if (!headers.has("Content-Type") && init.body) {
    headers.set("Content-Type", "application/json");
  }
  if (authToken) {
    headers.set("Authorization", `Bearer ${authToken}`);
  }
  const response = await fetch(path, { ...init, headers });
  if (!response.ok) {
    throw new ApiError(response.status, await parseResponse(response));
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return (await parseResponse(response)) as T;
}

export function verifyWebAdminSession(): Promise<WebAdminSession> {
  return api<WebAdminSession>("/api/web-admin/session");
}

export function listTeacherAccounts(): Promise<TeacherAccount[]> {
  return api<TeacherAccount[]>("/api/web-admin/teacher-accounts");
}

export function createTeacherAccount(values: {
  username: string;
  display_name: string;
  password: string;
  must_change_password: boolean;
}): Promise<TeacherAccount> {
  return api<TeacherAccount>("/api/web-admin/teacher-accounts", {
    method: "POST",
    body: JSON.stringify(values),
  });
}

export function patchTeacherAccount(
  accountId: string,
  values: { display_name?: string; role?: "admin" | "teacher"; status?: "active" | "disabled" },
): Promise<TeacherAccount> {
  return api<TeacherAccount>(`/api/web-admin/teacher-accounts/${encodeURIComponent(accountId)}`, {
    method: "PATCH",
    body: JSON.stringify(values),
  });
}

export function resetTeacherPassword(
  accountId: string,
  values: { password: string; must_change_password: boolean },
): Promise<TeacherAccount> {
  return api<TeacherAccount>(`/api/web-admin/teacher-accounts/${encodeURIComponent(accountId)}/reset-password`, {
    method: "POST",
    body: JSON.stringify(values),
  });
}

export function disableTeacherAccount(accountId: string): Promise<TeacherAccount> {
  return api<TeacherAccount>(`/api/web-admin/teacher-accounts/${encodeURIComponent(accountId)}/disable`, {
    method: "POST",
  });
}

export function enableTeacherAccount(accountId: string): Promise<TeacherAccount> {
  return api<TeacherAccount>(`/api/web-admin/teacher-accounts/${encodeURIComponent(accountId)}/enable`, {
    method: "POST",
  });
}

export function deleteTeacherAccount(accountId: string): Promise<TeacherAccount> {
  return api<TeacherAccount>(`/api/web-admin/teacher-accounts/${encodeURIComponent(accountId)}`, {
    method: "DELETE",
  });
}

export function listPreviewInfrastructure(): Promise<PreviewInfrastructure[]> {
  return api<PreviewInfrastructure[]>("/api/web-admin/student-preview/classes");
}

export function ensurePreviewInfrastructure(teacherUserId: string): Promise<PreviewInfrastructure> {
  return api<PreviewInfrastructure>(`/api/web-admin/student-preview/classes/${encodeURIComponent(teacherUserId)}/ensure`, {
    method: "POST",
  });
}

export function resetPreviewInfrastructure(teacherUserId: string): Promise<PreviewInfrastructure> {
  return api<PreviewInfrastructure>(`/api/web-admin/student-preview/classes/${encodeURIComponent(teacherUserId)}/reset`, {
    method: "POST",
  });
}

export function disablePreviewInfrastructure(teacherUserId: string): Promise<PreviewInfrastructure> {
  return api<PreviewInfrastructure>(`/api/web-admin/student-preview/classes/${encodeURIComponent(teacherUserId)}/disable`, {
    method: "POST",
  });
}

export function restorePreviewInfrastructure(teacherUserId: string): Promise<PreviewInfrastructure> {
  return api<PreviewInfrastructure>(`/api/web-admin/student-preview/classes/${encodeURIComponent(teacherUserId)}/restore`, {
    method: "POST",
  });
}
