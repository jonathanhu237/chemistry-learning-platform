import type { ApiList } from "./common";
import { api } from "./http";

export type ChapterBinding = {
  chapter_id: string;
  chapter_title?: string;
  chapter_number?: number;
  coverage_type: "primary" | "partial" | "supporting";
  notes?: string | null;
  sort_order?: number;
};

export type MediaResource = {
  binding_id?: string;
  media_id?: string;
  title?: string;
  original_file_name?: string;
  mime_type?: string;
  file_size_bytes?: number;
  thumbnail_relative_path?: string | null;
  upload_status?: string;
  binding_status?: string;
  point_key?: string | null;
  point_title?: string | null;
  published_at?: string;
};

export type Experiment = {
  id: string;
  code: string;
  title: string;
  title_en?: string;
  summary?: string;
  metadata?: Record<string, unknown>;
  family_id?: string;
  family_code?: string;
  family_title?: string;
  status: "draft" | "published" | "archived";
  display_order: number;
  chapter_bindings: ChapterBinding[];
  media_resources: MediaResource[];
  published_question_count: number;
  draft_question_count: number;
  generated_draft_count: number;
};

export type ExperimentListParams = string | URLSearchParams;

function paramsSuffix(params: ExperimentListParams = ""): string {
  const value = typeof params === "string" ? params : params.toString();
  if (!value) return "";
  return value.startsWith("?") ? value : `?${value}`;
}

export function listExperiments(params: ExperimentListParams = ""): Promise<ApiList<Experiment>> {
  return api<ApiList<Experiment>>(`/api/admin/experiments${paramsSuffix(params)}`);
}
