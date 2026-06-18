import type { LoginResponse } from "../../api";

export function normalizeStudentId(value: string): string {
  return value.trim().toUpperCase();
}

export function isStudent(response: LoginResponse): boolean {
  return response.user.role === "student";
}
