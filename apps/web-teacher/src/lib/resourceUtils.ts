import dayjs from "dayjs";

import type { Experiment } from "../api/experiments";
import type { MediaAsset } from "../api/media";

export type TheoryChapter = {
  chapter_id: string;
  chapter_number: number;
  chapter_title: string;
  area_id: string;
  area_name: string;
};

export const theoryChapters: TheoryChapter[] = [
  { chapter_id: "CH13", chapter_number: 13, chapter_title: "第13章 卤族元素", area_id: "p", area_name: "p 区元素" },
  { chapter_id: "CH14", chapter_number: 14, chapter_title: "第14章 氧族元素", area_id: "p", area_name: "p 区元素" },
  { chapter_id: "CH15", chapter_number: 15, chapter_title: "第15章 氮族元素", area_id: "p", area_name: "p 区元素" },
  { chapter_id: "CH16", chapter_number: 16, chapter_title: "第16章 碳族元素", area_id: "p", area_name: "p 区元素" },
  { chapter_id: "CH17", chapter_number: 17, chapter_title: "第17章 硼族元素", area_id: "p", area_name: "p 区元素" },
  { chapter_id: "CH18", chapter_number: 18, chapter_title: "第18章 碱金属和碱土金属", area_id: "s", area_name: "s 区元素" },
  { chapter_id: "CH19", chapter_number: 19, chapter_title: "第19章 铜锌副族元素", area_id: "ds", area_name: "ds 区元素" },
  { chapter_id: "CH20", chapter_number: 20, chapter_title: "第20章 d 区过渡金属元素", area_id: "d", area_name: "d 区元素" },
  { chapter_id: "CH21", chapter_number: 21, chapter_title: "第21章 镧系和锕系元素", area_id: "f", area_name: "f 区元素" },
  { chapter_id: "CH22", chapter_number: 22, chapter_title: "第22章 氢和稀有气体", area_id: "hydrogen", area_name: "氢元素" },
];

const resourceAreaMeta: Record<string, { label: string; shortLabel: string; color: string; ink: string; selected: string }> = {
  hydrogen: { label: "氢元素", shortLabel: "氢", color: "#e4f0cf", ink: "#254509", selected: "#6f9f2e" },
  p: { label: "p 区元素", shortLabel: "p", color: "#cceee6", ink: "#063f31", selected: "#0f8f72" },
  s: { label: "s 区元素", shortLabel: "s", color: "#ead8ae", ink: "#46310a", selected: "#9a6a11" },
  ds: { label: "ds 区元素", shortLabel: "ds", color: "#f2dfa9", ink: "#523a0c", selected: "#c89a2d" },
  d: { label: "d 区元素", shortLabel: "d", color: "#efd0d4", ink: "#4e1018", selected: "#9e2f3d" },
  f: { label: "f 区元素", shortLabel: "f", color: "#ead8ef", ink: "#42204d", selected: "#8d4f9f" },
  general: { label: "通识资源", shortLabel: "通识", color: "#edf3ee", ink: "#375247", selected: "#9bbbaa" },
  other: { label: "其他资源", shortLabel: "其他", color: "#eef1ef", ink: "#53635b", selected: "#aebbb4" },
};

export function areaMeta(areaId?: string | null) {
  return resourceAreaMeta[areaId || ""] || resourceAreaMeta.other;
}

export function countValue(counts: Record<string, number> | undefined, key: string) {
  return Number(counts?.[key] || 0);
}

export function resourcePercent(value: number, total: number) {
  if (!total) return 0;
  return Math.round((value / total) * 100);
}

export function shortResourceTitle(title?: string | null) {
  return (title || "").replace(/^第\s*(\d+)\s*章\s*/, "$1. ").trim();
}

export function questionTypeSummary(counts?: Record<string, number>) {
  return [
    { label: "单选", value: countValue(counts, "single_choice") },
    { label: "判断", value: countValue(counts, "true_false") },
    { label: "填空", value: countValue(counts, "fill_blank") },
  ];
}

export function isGeneralResourceTitle(title?: string | null, chapterId?: string | null) {
  const text = `${chapterId || ""} ${title || ""}`;
  return chapterId === "CH00" || /综合|通识|跨章节|未标章节/.test(text);
}

export function formatChapterTitle(title?: string | null, chapterId?: string | null) {
  const cleanTitle = (title || "").replace(/^CH\d+\s*/i, "").trim();
  const fallback = chapterId ? theoryChapters.find((chapter) => chapter.chapter_id === chapterId)?.chapter_title : "";
  const display = cleanTitle || fallback || (chapterId === "CH00" ? "通识/跨章节" : chapterId || "-");
  if (isGeneralResourceTitle(display, chapterId)) {
    return display.replace(/^第\s*\d+\s*章\s*/, "").trim() || "通识/跨章节";
  }
  return display.replace(/^第\s*(\d+)\s*章\s*/, "第 $1 章 ");
}

export function experimentVideoCandidates(experiment?: Experiment | null): string[] {
  const raw = experiment?.metadata?.video_candidates;
  if (!Array.isArray(raw)) return [];
  return raw.filter((item): item is string => typeof item === "string" && item.trim().length > 0).map((item) => item.trim());
}

export function experimentVideoPointCount(experiment?: Experiment | null): number {
  const candidateCount = experimentVideoCandidates(experiment).length;
  if (candidateCount) return candidateCount;

  const pointKeys = new Set<string>();
  for (const resource of experiment?.media_resources || []) {
    const key = String(resource.point_key || resource.point_title || "").trim();
    if (key) pointKeys.add(key);
  }
  return pointKeys.size;
}

export function mediaAssetType(asset: MediaAsset): string {
  const mime = asset.mime_type || "";
  if (mime.startsWith("video/")) return mime.replace("video/", "").toUpperCase();
  const suffix = asset.original_file_name.split(".").pop();
  return suffix ? suffix.toUpperCase() : "VIDEO";
}

export function mediaAssetTime(asset: MediaAsset): string {
  const value = asset.updated_at || asset.created_at;
  return value ? dayjs(value).format("YYYY-MM-DD HH:mm") : "-";
}

export function isPreviewableVideo(asset?: MediaAsset | null): boolean {
  if (!asset || asset.upload_status !== "ready") return false;
  if (asset.primary_file_available === false) return false;
  return !asset.mime_type || asset.mime_type.startsWith("video/");
}
