import { postJson } from "../../api/http";

export type TeacherStudentPreviewSession = {
  preview_url: string;
  ticket: string;
  expires_at: string;
};

export function createStudentPreviewSession(): Promise<TeacherStudentPreviewSession> {
  return postJson<TeacherStudentPreviewSession>("/api/admin/student-preview/session", {});
}
