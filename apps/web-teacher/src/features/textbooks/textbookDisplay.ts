import type { TextbookDocument, TextbookIngestionStage, TextbookPublicationStatus } from "../../api/textbooks";

export const activeIngestionStages = new Set<TextbookIngestionStage>([
  "uploaded",
  "extracting",
  "ocr",
  "structuring",
  "chunking",
  "embedding",
  "indexing",
]);

export const ingestionStageLabels: Record<string, string> = {
  uploaded: "等待处理",
  extracting: "提取原文",
  awaiting_ocr: "等待 OCR",
  ocr: "OCR 识别",
  structuring: "结构化",
  chunking: "生成分块",
  embedding: "向量化",
  indexing: "写入索引",
  review_ready: "等待发布",
  ready: "已完成",
  failed: "处理失败",
  cancelled: "已取消",
};

export const publicationStatusLabels: Record<string, string> = {
  draft: "待处理",
  processing: "处理中",
  review_ready: "待审核发布",
  published: "使用中",
  inactive: "已停用",
  failed: "处理失败",
  deleted: "已删除",
};

export const qualityIssueLabels: Record<string, string> = {
  no_pages: "未提取到页面",
  missing_pages: "存在缺页",
  duplicate_pages: "存在重复页",
  empty_pages: "存在空白页",
  unresolved_ocr_pages: "仍有页面需要 OCR",
  no_chunks: "未生成分块",
  duplicate_chunk_content: "存在重复分块",
  invalid_chunk_page_range: "分块页码范围异常",
  uncovered_searchable_pages: "有正文页面未被分块覆盖",
  ingestion_not_review_ready: "处理任务尚未进入待发布状态",
  quality_not_publishable: "质量门禁未通过",
  index_not_verified: "向量索引尚未校验",
  index_count_mismatch: "索引分块数量不一致",
};

export function ingestionStageLabel(stage?: string | null): string {
  return ingestionStageLabels[String(stage || "")] || String(stage || "未开始");
}

export function publicationStatusLabel(status?: TextbookPublicationStatus | null): string {
  return publicationStatusLabels[String(status || "")] || String(status || "未知");
}

export function publicationStatusColor(status?: TextbookPublicationStatus | null): string {
  if (status === "published") return "green";
  if (status === "review_ready") return "gold";
  if (status === "processing") return "blue";
  if (status === "failed") return "red";
  if (status === "inactive" || status === "deleted") return "default";
  return "cyan";
}

export function ingestionStatusColor(stage?: TextbookIngestionStage | null): string {
  if (stage === "ready") return "green";
  if (stage === "review_ready") return "gold";
  if (stage === "failed") return "red";
  if (stage === "cancelled") return "default";
  if (stage === "awaiting_ocr") return "orange";
  if (stage && activeIngestionStages.has(stage)) return "processing";
  return "default";
}

export function isActiveTextbook(document: TextbookDocument): boolean {
  return Boolean(document.latest_job?.status && activeIngestionStages.has(document.latest_job.status));
}

export function textbookAllows(document: TextbookDocument, action: string): boolean {
  return document.allowed_actions.includes(action);
}

export function textbookSummary(documents: TextbookDocument[]) {
  return {
    versions: documents.length,
    published: documents.filter((document) => document.publication_status === "published").length,
    processing: documents.filter(isActiveTextbook).length,
    attention: documents.filter(
      (document) =>
        document.latest_job?.status === "failed" ||
        document.latest_job?.status === "awaiting_ocr" ||
        document.publication_status === "review_ready",
    ).length,
  };
}

export function formatTextbookBytes(value?: number | null): string {
  const bytes = Number(value || 0);
  if (!bytes) return "-";
  const units = ["B", "KB", "MB", "GB"];
  const exponent = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const number = bytes / 1024 ** exponent;
  return `${number >= 10 || exponent === 0 ? number.toFixed(0) : number.toFixed(1)} ${units[exponent]}`;
}

export function qualityIssueLabel(issue: string): string {
  return qualityIssueLabels[issue] || issue;
}

export function extractionMethodLabel(method?: string | null): string {
  if (method === "native") return "原文提取";
  if (method === "mineru") return "MinerU OCR";
  if (method === "mixed") return "混合提取";
  return method || "未识别";
}

export function qualityPercent(score?: number | null): number {
  const value = Number(score || 0);
  return Math.max(0, Math.min(100, Math.round(value * 100)));
}
