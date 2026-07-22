import type { LoginResponse } from "./auth";
import { api, postJson } from "./http";

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

export type TeacherAccountCreate = {
  username: string;
  display_name: string;
  password: string;
};

export function changeOwnPassword(currentPassword: string, newPassword: string): Promise<LoginResponse> {
  return postJson<LoginResponse>("/api/auth/password", {
    current_password: currentPassword,
    new_password: newPassword,
  });
}

export function listTeacherAccounts(): Promise<TeacherAccount[]> {
  return api<TeacherAccount[]>("/api/admin/teacher-accounts");
}

export function createTeacherAccount(payload: TeacherAccountCreate): Promise<TeacherAccount> {
  return postJson<TeacherAccount>("/api/admin/teacher-accounts", payload);
}

export function resetTeacherAccountPassword(accountId: string, password: string): Promise<TeacherAccount> {
  return postJson<TeacherAccount>(`/api/admin/teacher-accounts/${encodeURIComponent(accountId)}/reset-password`, {
    password,
  });
}

export function disableTeacherAccount(accountId: string): Promise<TeacherAccount> {
  return postJson<TeacherAccount>(`/api/admin/teacher-accounts/${encodeURIComponent(accountId)}/disable`, {});
}

export function enableTeacherAccount(accountId: string): Promise<TeacherAccount> {
  return postJson<TeacherAccount>(`/api/admin/teacher-accounts/${encodeURIComponent(accountId)}/enable`, {});
}
