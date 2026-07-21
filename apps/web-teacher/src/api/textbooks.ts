import type { ApiList } from "./common";
import { api } from "./http";

export type TextbookIngestionStage =
  | "uploaded"
  | "extracting"
  | "awaiting_ocr"
  | "ocr"
  | "structuring"
  | "chunking"
  | "embedding"
  | "indexing"
  | "review_ready"
  | "ready"
  | "failed"
  | "cancelled"
  | string;

export type TextbookPublicationStatus =
  | "draft"
  | "processing"
  | "review_ready"
  | "published"
  | "inactive"
  | "failed"
  | "deleted"
  | string;

export type TextbookOcrConfiguration = {
  provider?: string | null;
  model?: string | null;
  enabled?: boolean;
  credential_configured?: boolean;
  credential_fingerprint?: string | null;
};

export type TextbookUploadPolicy = {
  enabled: boolean;
  max_upload_mb: number;
  max_upload_bytes: number;
  max_pages: number;
  allowed_extensions: string[];
  ocr: TextbookOcrConfiguration;
};

export type TextbookIngestionJob = {
  id: string;
  document_id: string;
  status: TextbookIngestionStage;
  progress: number;
  attempts: number;
  max_attempts: number;
  total_pages: number;
  processed_pages: number;
  ocr_pages: number;
  total_chunks: number;
  embedded_chunks: number;
  indexed_chunks: number;
  error_code?: string | null;
  error_message?: string | null;
  stage_metrics: Record<string, unknown>;
  quality_report: Record<string, unknown>;
  outputs: Record<string, unknown>;
  created_at?: string | null;
  updated_at?: string | null;
  started_at?: string | null;
  finished_at?: string | null;
  allowed_actions: string[];
  ocr: TextbookOcrConfiguration;
};

export type TextbookDocument = {
  id: string;
  logical_textbook_key: string;
  version_number: number;
  version_label?: string | null;
  title: string;
  file_name: string;
  size_bytes?: number | null;
  checksum_sha256?: string | null;
  publication_status: TextbookPublicationStatus;
  quality_summary: Record<string, unknown>;
  metadata: Record<string, unknown>;
  created_at?: string | null;
  updated_at?: string | null;
  published_at?: string | null;
  deactivated_at?: string | null;
  deleted_at?: string | null;
  corpus_revision?: number | null;
  latest_job?: TextbookIngestionJob | null;
  allowed_actions: string[];
  can_publish: boolean;
  publish_blockers: string[];
  ocr: TextbookOcrConfiguration;
};

export type TextbookPage = {
  document_id: string;
  page_number: number;
  extraction_method?: "native" | "mineru" | "mixed" | string | null;
  text: string;
  markdown: string;
  blocks: Array<Record<string, unknown>>;
  content_hash?: string | null;
  quality_score: number;
  quality_flags: string[];
  needs_ocr: boolean;
  ocr_provider?: string | null;
  ocr_model?: string | null;
  diagnostics: Record<string, unknown>;
  updated_at?: string | null;
};

export type TextbookChunk = {
  id: string;
  document_id: string;
  document_version: number;
  chunk_index: number;
  text: string;
  markdown: string;
  page_start: number;
  page_end: number;
  section_title?: string | null;
  section_path: string[];
  content_type: string;
  content_hash: string;
  parent_chunk_id?: string | null;
  previous_chunk_id?: string | null;
  next_chunk_id?: string | null;
  extraction_method?: string | null;
  quality_flags: string[];
  review_required: boolean;
  content_status: string;
  metadata: Record<string, unknown>;
  updated_at?: string | null;
};

export type TextbookJobEvent = {
  id: number;
  job_id: string;
  status: TextbookIngestionStage;
  progress: number;
  event_type: string;
  message?: string | null;
  details: Record<string, unknown>;
  created_at: string;
};

export type TextbookUploadInput = {
  title: string;
  file: File;
  logicalTextbookKey?: string;
  versionLabel?: string;
};

export function getTextbookUploadPolicy(): Promise<TextbookUploadPolicy> {
  return api<TextbookUploadPolicy>("/api/admin/textbooks/upload-policy");
}

export function listTextbooks(): Promise<ApiList<TextbookDocument>> {
  return api<ApiList<TextbookDocument>>("/api/admin/textbooks?limit=500");
}

export function uploadTextbook(input: TextbookUploadInput): Promise<TextbookDocument> {
  const body = new FormData();
  body.set("title", input.title.trim());
  body.set("file", input.file);
  if (input.logicalTextbookKey?.trim()) body.set("logical_textbook_key", input.logicalTextbookKey.trim());
  if (input.versionLabel?.trim()) body.set("version_label", input.versionLabel.trim());
  return api<TextbookDocument>("/api/admin/textbooks", { method: "POST", body });
}

export function getTextbook(documentId: string): Promise<TextbookDocument> {
  return api<TextbookDocument>(`/api/admin/textbooks/${encodeURIComponent(documentId)}`);
}

export function getTextbookJob(jobId: string): Promise<TextbookIngestionJob> {
  return api<TextbookIngestionJob>(`/api/admin/textbooks/jobs/${encodeURIComponent(jobId)}`);
}

export function listTextbookJobEvents(jobId: string): Promise<ApiList<TextbookJobEvent>> {
  return api<ApiList<TextbookJobEvent>>(`/api/admin/textbooks/jobs/${encodeURIComponent(jobId)}/events?limit=2000`);
}

export function listTextbookPages(documentId: string): Promise<ApiList<TextbookPage>> {
  return api<ApiList<TextbookPage>>(`/api/admin/textbooks/${encodeURIComponent(documentId)}/pages?limit=5000`);
}

export function listTextbookChunks(documentId: string): Promise<ApiList<TextbookChunk>> {
  return api<ApiList<TextbookChunk>>(`/api/admin/textbooks/${encodeURIComponent(documentId)}/chunks?limit=5000`);
}

export function cancelTextbookJob(jobId: string): Promise<TextbookIngestionJob> {
  return api<TextbookIngestionJob>(`/api/admin/textbooks/jobs/${encodeURIComponent(jobId)}/cancel`, { method: "POST" });
}

export function retryTextbookJob(jobId: string): Promise<TextbookIngestionJob> {
  return api<TextbookIngestionJob>(`/api/admin/textbooks/jobs/${encodeURIComponent(jobId)}/retry`, { method: "POST" });
}

export function publishTextbook(documentId: string): Promise<TextbookDocument> {
  return api<TextbookDocument>(`/api/admin/textbooks/${encodeURIComponent(documentId)}/publish`, { method: "POST" });
}

export function deactivateTextbook(documentId: string): Promise<TextbookDocument> {
  return api<TextbookDocument>(`/api/admin/textbooks/${encodeURIComponent(documentId)}/deactivate`, { method: "POST" });
}

export function deleteTextbook(documentId: string): Promise<TextbookDocument> {
  return api<TextbookDocument>(`/api/admin/textbooks/${encodeURIComponent(documentId)}`, { method: "DELETE" });
}
