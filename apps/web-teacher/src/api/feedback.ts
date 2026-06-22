import type { ApiList } from "./common";
import { apiBase, api, patchJson } from "./http";

export type FeedbackStatus = "open" | "in_progress" | "resolved" | "archived";

export type FeedbackType = "course_content" | "experiment_resource" | "ai_answer" | "system_issue" | "other";

export type FeedbackAttachmentItem = {
  id: string;
  feedback_id: string;
  original_file_name?: string | null;
  mime_type: string;
  file_size_bytes: number;
  created_at?: string | null;
};

export type FeedbackItem = {
  id: string;
  student_id: string;
  class_id?: string | null;
  student_name_snapshot?: string | null;
  class_name_snapshot?: string | null;
  feedback_type: FeedbackType;
  content: string;
  status: FeedbackStatus;
  chapter_id?: string | null;
  unit_id?: string | null;
  knowledge_point_id?: string | null;
  experiment_id?: string | null;
  page_path?: string | null;
  source_event_id?: number | null;
  handler_user_id?: string | null;
  handler_display_name?: string | null;
  internal_note?: string | null;
  metadata?: Record<string, unknown>;
  attachment_count?: number;
  attachments?: FeedbackAttachmentItem[];
  resolved_at?: string | null;
  created_at?: string | null;
  updated_at?: string | null;
};

export type FeedbackSummary = {
  total_count: number;
  open_count: number;
  in_progress_count: number;
  resolved_count: number;
  archived_count: number;
  recent_count: number;
};

export type FeedbackListResponse = ApiList<FeedbackItem>;

export type FeedbackUpdate = {
  status?: FeedbackStatus;
  internal_note?: string | null;
};

export function getFeedbackAttachmentUrl(feedbackId: string, attachmentId: string): string {
  return `${apiBase}/api/admin/feedback/${encodeURIComponent(feedbackId)}/attachments/${encodeURIComponent(attachmentId)}`;
}

export function getFeedbackSummary(): Promise<FeedbackSummary> {
  return api<FeedbackSummary>("/api/admin/feedback/summary");
}

export function listFeedback(params: URLSearchParams): Promise<FeedbackListResponse> {
  return api<FeedbackListResponse>(`/api/admin/feedback?${params.toString()}`);
}

export function getFeedback(feedbackId: string): Promise<FeedbackItem> {
  return api<FeedbackItem>(`/api/admin/feedback/${feedbackId}`);
}

export function updateFeedback(feedbackId: string, payload: FeedbackUpdate): Promise<FeedbackItem> {
  return patchJson<FeedbackItem>(`/api/admin/feedback/${feedbackId}`, payload);
}
