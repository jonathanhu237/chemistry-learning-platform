import { api, patchJson, postJson, putJson } from "./http";
import type { CustomAssessmentSettings, SmartAssessmentSettings } from "./settings";

export type ClassItem = {
  id: string;
  class_name: string;
  description?: string | null;
  status: string;
  student_count: number;
};

export type RosterStudent = {
  id: string;
  class_id: string;
  student_id: string;
  student_name: string;
  status: "pending" | "active" | "disabled";
  activation_mode: "default_password" | "self_registration";
  activated: boolean;
  user_id?: string | null;
  activated_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type RosterImportResult = {
  import_id: string;
  mode: "upsert" | "overwrite";
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  disabled_missing: number;
};

export type RegistrationSettings = {
  mode: "roster_only" | "self_registration";
  default_password_policy: string;
  default_password_mode: "student_id" | "shared";
  has_default_password: boolean;
  source?: "system_default" | "class" | null;
};

export type SmartAssessmentStrategyResponse = {
  strategy: SmartAssessmentSettings;
  inherited_strategy: SmartAssessmentSettings;
  source: "system_default" | "class";
  has_override: boolean;
  can_edit: boolean;
};

export type SmartAssessmentClassPreviewExperiment = {
  id: string;
  title: string;
  candidate_point_count: number;
  untested_point_count: number;
  measured_point_count: number;
  average_mastery_score?: number | null;
  estimated_draw_tickets: number;
  estimated_question_count: number;
};

export type SmartAssessmentClassPreviewResponse = {
  strategy: SmartAssessmentSettings;
  source: "system_default" | "class";
  has_override: boolean;
  class_student_count: number;
  candidate_point_count: number;
  measured_point_count: number;
  untested_point_count: number;
  target_question_count: number;
  untested_target_count: number;
  measured_target_count: number;
  experiments: SmartAssessmentClassPreviewExperiment[];
  warnings: Record<string, unknown>;
};

export type CustomAssessmentSettingsResponse = {
  settings: CustomAssessmentSettings;
  inherited_settings: CustomAssessmentSettings;
  source: "system_default" | "class";
  has_override: boolean;
  can_edit: boolean;
};

export function listClasses(): Promise<ClassItem[]> {
  return api<ClassItem[]>("/api/admin/classes");
}

export function listRosterStudents(classId: string): Promise<RosterStudent[]> {
  return api<RosterStudent[]>(`/api/admin/classes/${classId}/students`);
}

export function getRegistrationSettings(classId: string): Promise<RegistrationSettings> {
  return api<RegistrationSettings>(`/api/admin/classes/${classId}/registration-settings`);
}

export function createClass(values: { class_name: string; description?: string }): Promise<ClassItem> {
  return postJson<ClassItem>("/api/admin/classes", values);
}

export function updateClass(classId: string, values: { class_name?: string; description?: string | null; status?: string }): Promise<ClassItem> {
  return patchJson<ClassItem>(`/api/admin/classes/${classId}`, values);
}

export function updateRegistrationSettings(classId: string, values: Partial<RegistrationSettings>): Promise<RegistrationSettings> {
  return putJson<RegistrationSettings>(`/api/admin/classes/${classId}/registration-settings`, values);
}

export function getSmartAssessmentStrategy(classId: string): Promise<SmartAssessmentStrategyResponse> {
  return api<SmartAssessmentStrategyResponse>(`/api/admin/classes/${classId}/smart-assessment-strategy`);
}

export function updateSmartAssessmentStrategy(
  classId: string,
  values: SmartAssessmentSettings,
): Promise<SmartAssessmentStrategyResponse> {
  return putJson<SmartAssessmentStrategyResponse>(`/api/admin/classes/${classId}/smart-assessment-strategy`, values);
}

export function clearSmartAssessmentStrategy(classId: string): Promise<SmartAssessmentStrategyResponse> {
  return api<SmartAssessmentStrategyResponse>(`/api/admin/classes/${classId}/smart-assessment-strategy`, { method: "DELETE" });
}

export function getSmartAssessmentPreview(classId: string): Promise<SmartAssessmentClassPreviewResponse> {
  return api<SmartAssessmentClassPreviewResponse>(`/api/admin/classes/${classId}/smart-assessment-preview`);
}

export function getCustomAssessmentSettings(classId: string): Promise<CustomAssessmentSettingsResponse> {
  return api<CustomAssessmentSettingsResponse>(`/api/admin/classes/${classId}/custom-assessment-settings`);
}

export function updateCustomAssessmentSettings(
  classId: string,
  values: CustomAssessmentSettings,
): Promise<CustomAssessmentSettingsResponse> {
  return putJson<CustomAssessmentSettingsResponse>(`/api/admin/classes/${classId}/custom-assessment-settings`, values);
}

export function clearCustomAssessmentSettings(classId: string): Promise<CustomAssessmentSettingsResponse> {
  return api<CustomAssessmentSettingsResponse>(`/api/admin/classes/${classId}/custom-assessment-settings`, { method: "DELETE" });
}

export function upsertRosterStudent(classId: string, studentId: string | null, values: unknown): Promise<RosterStudent> {
  if (studentId) return patchJson<RosterStudent>(`/api/admin/classes/${classId}/students/${studentId}`, values);
  return postJson<RosterStudent>(`/api/admin/classes/${classId}/students`, values);
}

export function deleteRosterStudent(classId: string, studentId: string): Promise<RosterStudent> {
  return api<RosterStudent>(`/api/admin/classes/${classId}/students/${studentId}`, { method: "DELETE" });
}

export function resetRosterStudentPassword(classId: string, studentId: string): Promise<unknown> {
  return postJson(`/api/admin/classes/${classId}/students/${studentId}/reset-password`, { force_change: true });
}

export function resetRosterStudentActivation(classId: string, studentId: string): Promise<RosterStudent> {
  return patchJson<RosterStudent>(`/api/admin/classes/${classId}/students/${studentId}`, { status: "pending" });
}

export function importRoster(classId: string, body: FormData): Promise<RosterImportResult> {
  return api<RosterImportResult>(`/api/admin/classes/${classId}/roster/import`, { method: "POST", body });
}
