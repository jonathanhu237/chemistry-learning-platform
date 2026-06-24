import { api, putJson } from "./http";

export type AssessmentReportType = "pretest" | "smart" | "custom" | "point" | "posttest";

export type AssessmentReportGeneratedText = {
  text: string;
  source: "ai" | "fallback";
  mode: string;
  generated_at?: string | null;
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
  report_type: AssessmentReportType;
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
  summary: AssessmentReportGeneratedText;
  mistake_explanation: AssessmentReportGeneratedText;
  prompt_snapshot: Record<string, unknown>;
  payload: Record<string, unknown>;
};

export type StudentAssessmentReportListResponse = {
  reports: StudentAssessmentReportSummary[];
};

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

export function getClassAssessmentReportPrompts(classId: string): Promise<AssessmentReportPromptSettingsResponse> {
  return api<AssessmentReportPromptSettingsResponse>(`/api/admin/classes/${classId}/assessment-report-prompts`);
}

export function updateClassAssessmentReportPrompts(
  classId: string,
  values: AssessmentReportPromptSettings,
): Promise<AssessmentReportPromptSettingsResponse> {
  return putJson<AssessmentReportPromptSettingsResponse>(`/api/admin/classes/${classId}/assessment-report-prompts`, values);
}

export function resetClassAssessmentReportPrompts(classId: string): Promise<AssessmentReportPromptSettingsResponse> {
  return api<AssessmentReportPromptSettingsResponse>(`/api/admin/classes/${classId}/assessment-report-prompts`, { method: "DELETE" });
}

export function listTeacherStudentAssessmentReports(
  classId: string,
  studentId: string,
): Promise<StudentAssessmentReportListResponse> {
  return api<StudentAssessmentReportListResponse>(`/api/admin/classes/${classId}/students/${studentId}/assessment-reports`);
}

export function getTeacherStudentAssessmentReport(
  classId: string,
  studentId: string,
  reportId: string,
): Promise<StudentAssessmentReport> {
  return api<StudentAssessmentReport>(
    `/api/admin/classes/${classId}/students/${studentId}/assessment-reports/${reportId}`,
  );
}
