import { Tag } from "antd";

import type { MediaAsset } from "../../api/media";

export type VideoUploadStage =
  | "idle"
  | "pending"
  | "hashing"
  | "ready"
  | "duplicate"
  | "uploading"
  | "paused"
  | "finalizing"
  | "processing"
  | "complete"
  | "error";

export type VideoUploadState = {
  stage: VideoUploadStage;
  hashProgress: number;
  progress: number;
  uploadedBytes: number;
  totalBytes: number;
  checksum?: string;
  duplicateAsset?: MediaAsset | null;
  error?: string;
  note?: string;
};

export type VideoUploadQueueItem = {
  id: string;
  file: File;
  title: string;
  status: VideoUploadStage;
  hashProgress: number;
  progress: number;
  uploadedBytes: number;
  totalBytes: number;
  checksum?: string;
  duplicateAsset?: MediaAsset | null;
  error?: string;
  note?: string;
};

export const emptyUploadState: VideoUploadState = {
  stage: "idle",
  hashProgress: 0,
  progress: 0,
  uploadedBytes: 0,
  totalBytes: 0,
};

export const mediaStatusLabels: Record<string, string> = {
  pending: "待处理",
  processing: "处理中",
  ready: "就绪",
  failed: "处理失败",
  replaced: "已替换",
};

export const mediaStatusColors: Record<string, string> = {
  pending: "#b8892f",
  processing: "#356f9c",
  ready: "#005826",
  failed: "#b42318",
  replaced: "default",
};

export const mediaFileStateLabels: Record<string, { label: string; color: string }> = {
  available: { label: "文件完整", color: "#005826" },
  partial: { label: "部分文件缺失", color: "#b8892f" },
  missing: { label: "文件缺失", color: "#b42318" },
  pending: { label: "文件待生成", color: "#356f9c" },
  untracked: { label: "未跟踪文件", color: "default" },
};

export const processingPhaseLabels: Record<string, string> = {
  queued: "已排队",
  starting: "启动中",
  validating: "校验文件",
  probing: "读取元数据",
  thumbnailing: "生成缩略图",
  transcoding: "生成学生播放源",
  fingerprinting: "生成相似度签名",
  comparing: "比对相似视频",
  ready: "已就绪",
  failed: "处理失败",
};

export const duplicateDecisionLabels: Record<string, string> = {
  pending: "待确认",
  kept: "已保留",
  reused: "已复用",
  ignored: "已忽略",
};

export function mediaStatusTag(status?: string) {
  const value = status || "pending";
  return <Tag color={mediaStatusColors[value] || "default"}>{mediaStatusLabels[value] || value}</Tag>;
}

export function mediaFileStateTag(asset: MediaAsset) {
  if (!asset.file_state) return null;
  const state = asset.file_state;
  const meta = mediaFileStateLabels[state] || { label: state, color: "default" };
  if (state === "available") return null;
  return <Tag color={meta.color}>{meta.label}</Tag>;
}

export function processingPhaseText(asset?: MediaAsset | null): string {
  const phase = asset?.processing_phase || asset?.processing_job?.phase || asset?.upload_status || "";
  return processingPhaseLabels[phase] || phase || "-";
}

export function processingProgressValue(asset?: MediaAsset | null): number {
  return Math.max(0, Math.min(100, Number(asset?.processing_progress ?? asset?.processing_job?.progress ?? 0)));
}

export function formatDurationSeconds(value?: number | null): string {
  if (!value) return "-";
  const total = Math.round(Number(value));
  const minutes = Math.floor(total / 60);
  const seconds = String(total % 60).padStart(2, "0");
  if (minutes < 60) return String(minutes) + ":" + seconds;
  const hours = Math.floor(minutes / 60);
  return String(hours) + ":" + String(minutes % 60).padStart(2, "0") + ":" + seconds;
}

export function formatResolution(asset?: { width?: number | null; height?: number | null } | null): string {
  return asset?.width && asset?.height ? String(asset.width) + " x " + String(asset.height) : "-";
}

export function selectedRendition(asset: MediaAsset) {
  return asset.renditions?.find((rendition) => rendition.kind === "learning") || asset.renditions?.[0];
}

export function renditionSavings(asset: MediaAsset) {
  const rendition = selectedRendition(asset);
  const sourceSize = Number(asset.file_size_bytes || 0);
  const renditionSize = Number(rendition?.file_size_bytes || 0);
  const savedBytes = sourceSize && renditionSize ? Math.max(0, sourceSize - renditionSize) : 0;
  const savedPercent = sourceSize && savedBytes ? Math.round((savedBytes / sourceSize) * 100) : 0;
  return { rendition, savedBytes, savedPercent };
}

export function pendingDuplicateCandidates(asset?: MediaAsset | null) {
  return (asset?.duplicate_candidates || []).filter((candidate) => candidate.status === "pending");
}

export function hasPendingDuplicate(asset?: MediaAsset | null): boolean {
  return pendingDuplicateCandidates(asset).length > 0;
}

export function duplicateScoreText(score?: number | null): string {
  if (score == null) return "-";
  const value = Number(score);
  if (!Number.isFinite(value)) return "-";
  return value > 1 ? value.toFixed(1) + "%" : Math.round(value * 100) + "%";
}

export function uploadStepCurrent(stage: VideoUploadStage): number {
  if (["uploading", "paused", "finalizing"].includes(stage)) return 1;
  if (["processing", "complete"].includes(stage)) return 2;
  return 0;
}

export function uploadStageText(stage: VideoUploadStage): string {
  if (stage === "pending") return "已加入队列，点击开始后会按顺序上传";
  if (stage === "hashing") return "正在做 SHA-256 完全重复校验";
  if (stage === "duplicate") return "发现完全相同的已上传文件";
  if (stage === "ready") return "文件已就绪，可以开始上传";
  if (stage === "uploading") return "正在上传文件";
  if (stage === "paused") return "上传已暂停，可继续断点续传";
  if (stage === "finalizing") return "正在完成入库并交给后台";
  if (stage === "processing") return "上传完成，后台正在处理";
  if (stage === "complete") return "上传已完成，已加入后台处理队列";
  if (stage === "error") return "上传遇到问题";
  return "选择视频后会先校验，再上传";
}

export function videoTitleFromFile(file: File): string {
  return file.name.replace(/\.[^.]+$/, "").trim() || file.name;
}

export function uploadQueueItemText(item: VideoUploadQueueItem): string {
  if (item.status === "pending") return "等待上传";
  if (item.status === "hashing") return "校验重复 " + item.hashProgress + "%";
  if (item.status === "ready") return "准备上传";
  if (item.status === "duplicate") return "完全重复，已复用";
  if (item.status === "uploading") return "上传中 " + item.progress + "%";
  if (item.status === "paused") return "已暂停";
  if (item.status === "finalizing") return "正在入库";
  if (item.status === "processing") return "已交给后台处理";
  if (item.status === "complete") return "已完成";
  if (item.status === "error") return item.error || "上传失败";
  return uploadStageText(item.status);
}

export async function computeVideoFileSha256(file: File, onProgress: (progress: number) => void): Promise<string> {
  const { createSHA256 } = await import("hash-wasm");
  const hasher = await createSHA256();
  hasher.init();
  const chunkSize = 8 * 1024 * 1024;
  let offset = 0;
  while (offset < file.size) {
    const nextOffset = Math.min(offset + chunkSize, file.size);
    const chunk = new Uint8Array(await file.slice(offset, nextOffset).arrayBuffer());
    hasher.update(chunk);
    offset = nextOffset;
    onProgress(file.size ? Math.round((offset / file.size) * 100) : 100);
    await new Promise((resolve) => window.setTimeout(resolve, 0));
  }
  return hasher.digest("hex");
}

export function extractTusUploadId(uploadUrl?: string | null): string {
  if (!uploadUrl) return "";
  try {
    const url = new URL(uploadUrl, window.location.href);
    const parts = url.pathname.split("/").filter(Boolean);
    return decodeURIComponent(parts[parts.length - 1] || "");
  } catch {
    const parts = uploadUrl.split("/").filter(Boolean);
    return decodeURIComponent(parts[parts.length - 1] || "");
  }
}
