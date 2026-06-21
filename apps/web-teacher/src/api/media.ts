import type { ApiList } from "./common";
import { apiBase, api, patchJson, postJson } from "./http";
import { getAuthToken } from "./auth";

export type MediaAsset = {
  id: string;
  title: string;
  original_file_name: string;
  relative_path?: string;
  source_relative_path?: string | null;
  thumbnail_relative_path?: string | null;
  playback_relative_path?: string | null;
  playback_mime_type?: string | null;
  checksum_sha256?: string | null;
  mime_type?: string | null;
  file_size_bytes?: number | null;
  duration_seconds?: number | null;
  width?: number | null;
  height?: number | null;
  fps?: number | null;
  bitrate?: number | null;
  video_codec?: string | null;
  audio_codec?: string | null;
  upload_status: string;
  processing_phase?: string | null;
  processing_progress?: number | null;
  error_reason?: string | null;
  created_at?: string;
  updated_at?: string;
  association_count?: number;
  file_state?: "available" | "partial" | "missing" | "pending" | "untracked" | string;
  primary_file_available?: boolean;
  existing_file_count?: number;
  missing_file_count?: number;
  media_files?: MediaFileEntry[];
  processing_job?: MediaProcessingJob | null;
  renditions?: MediaRendition[];
  duplicate_candidates?: MediaDuplicateCandidate[];
};

export type MediaFileEntry = {
  kind: string;
  kinds?: string[];
  relative_path: string;
  exists: boolean;
  file_size_bytes?: number | null;
  error?: string | null;
};

export type MediaProcessingJob = {
  id: string;
  status: string;
  phase?: string | null;
  progress?: number | null;
  attempts?: number | null;
  error_reason?: string | null;
  updated_at?: string | null;
};

export type MediaRendition = {
  id?: string;
  kind: string;
  relative_path?: string | null;
  mime_type?: string | null;
  file_size_bytes?: number | null;
  duration_seconds?: number | null;
  width?: number | null;
  height?: number | null;
  status?: string | null;
  video_codec?: string | null;
  audio_codec?: string | null;
};

export type MediaDuplicateCandidate = {
  id: string;
  duplicate_type: "exact" | "suspected";
  score?: number | null;
  algorithm: string;
  status: "pending" | "kept" | "reused" | "ignored";
  candidate_asset_id?: string | null;
  candidate_title?: string | null;
  candidate_thumbnail_relative_path?: string | null;
};

export type MediaDuplicatePrecheck = {
  exists: boolean;
  asset?: MediaAsset | null;
};

export function listMediaAssets(limit = 200): Promise<ApiList<MediaAsset>> {
  return api<ApiList<MediaAsset>>(`/api/admin/media/assets?limit=${limit}`);
}

export function getMediaAssetThumbnailUrl(assetId: string): string {
  const accessToken = getAuthToken();
  if (accessToken) {
    return `${apiBase}/api/admin/media/assets/${assetId}/thumbnail-stream?access_token=${encodeURIComponent(accessToken)}`;
  }
  return `${apiBase}/api/admin/media/assets/${assetId}/thumbnail`;
}

export function getMediaAssetFileUrl(assetId: string): string {
  const accessToken = getAuthToken();
  if (accessToken) {
    return getMediaAssetStreamUrl(assetId, accessToken);
  }
  return `${apiBase}/api/admin/media/assets/${assetId}/file`;
}

export function getMediaAssetStreamUrl(assetId: string, accessToken: string): string {
  return `${apiBase}/api/admin/media/assets/${assetId}/stream?access_token=${encodeURIComponent(accessToken)}`;
}

export function getMediaAssetUploadUrl(): string {
  return apiBase + "/api/admin/media/assets";
}

export function precheckMediaDuplicate(payload: unknown): Promise<MediaDuplicatePrecheck> {
  return postJson<MediaDuplicatePrecheck>("/api/admin/media/assets/precheck", payload);
}

export function completeMediaUpload(payload: unknown): Promise<MediaAsset> {
  return postJson<MediaAsset>("/api/admin/media/assets/complete-upload", payload);
}

export function retryMediaProcessing(assetId: string): Promise<unknown> {
  return postJson("/api/admin/media/assets/" + assetId + "/retry-processing", {});
}

export function updateMediaDuplicateCandidate(id: string, status: string): Promise<unknown> {
  return patchJson("/api/admin/media/duplicate-candidates/" + id, { status });
}
