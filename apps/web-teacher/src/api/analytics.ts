import type { ApiList } from "./common";
import { api, apiBase } from "./http";
import { getAuthToken } from "./auth";
import type { Experiment } from "./experiments";
import type { Question, QuestionOptionLink, QuestionPoint } from "./questionBank";

export type AnalyticsExperimentState = {
  status: string;
  completion_percent: number;
  best_score: number | null;
  mastery_score: number;
  score: number;
  has_mastery: boolean;
  evidence_count: number;
  attempt_count: number;
};

export type AnalyticsExperimentGroup = {
  id: string;
  code?: string;
  title: string;
  raw_title?: string;
  experiment_ids: string[];
  experiment_count: number;
};

export type AnalyticsExperimentGroupState = {
  status: string;
  mastery_score: number;
  score: number;
  has_mastery: boolean;
  evidence_experiment_count: number;
  experiment_count: number;
  evidence_count: number;
  attempt_count: number;
  lowest_experiment_id?: string | null;
  lowest_experiment_score?: number | null;
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
  experiments: Experiment[];
  experiment_groups?: AnalyticsExperimentGroup[];
  matrix: Array<{
    student_id: string;
    student_name: string;
    status?: string;
    average_score?: number;
    experiments: Record<string, AnalyticsExperimentState>;
    experiment_groups?: Record<string, AnalyticsExperimentGroupState>;
  }>;
  recent_activity: Array<Record<string, unknown>>;
  missing_students: Array<Record<string, unknown>>;
};

export type WeakQuestionItem = {
  experiment_id?: string;
  experiment_code?: string;
  experiment_title?: string;
  question_id?: string;
  stem?: string;
  attempt_count: number;
  incorrect_count: number;
  incorrect_rate: number;
  weak_kp_ids?: string[];
  unmapped?: boolean;
};

export type WeakVideoPointItem = {
  point_key: string;
  point_title: string;
  experiment_id?: string;
  experiment_code?: string;
  experiment_title?: string;
  attempt_count: number;
  incorrect_count: number;
  incorrect_rate: number;
  representative_questions?: Array<{ question_id?: string; stem?: string }>;
  selected_option_links?: QuestionOptionLink[];
  kp_unmapped?: boolean;
};

export type WeakPointsResponse = ApiList<WeakQuestionItem> & {
  point_items: WeakVideoPointItem[];
  point_total: number;
};

export type StudentAttempt = {
  id?: string;
  experiment_id?: string;
  experiment_code?: string;
  experiment_title?: string;
  question_id?: string;
  question_type?: Question["question_type"];
  stem?: string;
  options?: Array<Record<string, unknown>>;
  explanation?: string | null;
  difficulty?: string | null;
  attempt_kind?: string;
  attempt_kind_label?: string;
  correct?: boolean | null;
  score?: number | null;
  submitted_answer?: unknown;
  submitted_answer_value?: unknown;
  answer?: unknown;
  correct_answer?: unknown;
  related_chapter_ids?: string[];
  related_knowledge_point_ids?: string[];
  primary_points?: QuestionPoint[];
  metadata?: {
    primary_points?: QuestionPoint[];
    primary_point_keys?: string[];
    selected_option_label?: string | null;
    selected_option_link?: QuestionOptionLink | null;
    diagnostic_role?: string | null;
    [key: string]: unknown;
  };
  created_at?: string;
};

export type TeacherReportAiContent = {
  text: string;
  source: "ai" | "fallback";
  mode: string;
  generated_at?: string | null;
};

export type TeacherLatestPosttestReport = {
  session_id: string;
  completed_at?: string | null;
  score?: number | null;
  correct_count: number;
  total_count: number;
  experiments: Array<{ id: string; code?: string | null; title?: string | null }>;
  attempts: StudentAttempt[];
  wrong_answers: StudentAttempt[];
  ai_summary?: TeacherReportAiContent | null;
  ai_mistake_explanation?: TeacherReportAiContent | null;
};

export type StudentReport = {
  student?: Record<string, unknown>;
  progress?: Array<Record<string, unknown>>;
  experiment_mastery?: Array<Record<string, unknown>>;
  attempts?: StudentAttempt[];
  latest_posttest_report?: TeacherLatestPosttestReport | null;
  posttest_reports?: TeacherLatestPosttestReport[];
  weak_points?: Array<Record<string, unknown>>;
  weak_video_points?: WeakVideoPointItem[];
  timeline?: Array<Record<string, unknown>>;
};

export function getAnalyticsDashboard(classId: string): Promise<AnalyticsDashboard> {
  return api<AnalyticsDashboard>(`/api/admin/analytics/classes/${classId}/dashboard`);
}

export function getStudentReport(classId: string, studentId: string): Promise<StudentReport> {
  return api<StudentReport>(`/api/admin/analytics/classes/${classId}/students/${studentId}`);
}

export function getAnalyticsExportUrl(classId: string): string {
  return `${apiBase}/api/admin/analytics/classes/${classId}/export`;
}

export function getAnalyticsExportHeaders(): HeadersInit {
  return { Authorization: `Bearer ${getAuthToken()}` };
}
