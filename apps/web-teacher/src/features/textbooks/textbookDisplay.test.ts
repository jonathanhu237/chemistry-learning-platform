import { describe, expect, it } from "vitest";

import type { TextbookDocument } from "../../api/textbooks";
import {
  formatTextbookBytes,
  isActiveTextbook,
  qualityIssueLabel,
  textbookAllows,
  textbookSummary,
} from "./textbookDisplay";

function textbook(overrides: Partial<TextbookDocument> = {}): TextbookDocument {
  return {
    id: "doc-1",
    logical_textbook_key: "inorganic-chemistry",
    version_number: 1,
    title: "无机化学（下册）",
    file_name: "无机化学.pdf",
    publication_status: "processing",
    quality_summary: {},
    metadata: {},
    allowed_actions: ["cancel"],
    can_publish: false,
    publish_blockers: [],
    ocr: {},
    latest_job: {
      id: "job-1",
      document_id: "doc-1",
      status: "extracting",
      progress: 18,
      attempts: 1,
      max_attempts: 3,
      total_pages: 20,
      processed_pages: 4,
      ocr_pages: 0,
      total_chunks: 0,
      embedded_chunks: 0,
      indexed_chunks: 0,
      stage_metrics: {},
      quality_report: {},
      outputs: {},
      allowed_actions: ["cancel"],
      ocr: {},
    },
    ...overrides,
  };
}

describe("textbook ingestion display contracts", () => {
  it("polls only stages that can still make worker progress", () => {
    expect(isActiveTextbook(textbook())).toBe(true);
    expect(isActiveTextbook(textbook({ latest_job: { ...textbook().latest_job!, status: "awaiting_ocr" } }))).toBe(false);
    expect(isActiveTextbook(textbook({ latest_job: { ...textbook().latest_job!, status: "review_ready" } }))).toBe(false);
  });

  it("never infers lifecycle actions from publication status", () => {
    const publishedWithoutPermission = textbook({ publication_status: "published", allowed_actions: [] });
    expect(textbookAllows(publishedWithoutPermission, "deactivate")).toBe(false);
    expect(textbookAllows(textbook({ allowed_actions: ["rollback", "publish"] }), "rollback")).toBe(true);
  });

  it("summarizes versions, active work, and versions needing attention", () => {
    const summary = textbookSummary([
      textbook(),
      textbook({ id: "doc-2", publication_status: "published", latest_job: { ...textbook().latest_job!, status: "ready" } }),
      textbook({ id: "doc-3", publication_status: "review_ready", latest_job: { ...textbook().latest_job!, status: "review_ready" } }),
      textbook({ id: "doc-4", publication_status: "failed", latest_job: { ...textbook().latest_job!, status: "failed" } }),
    ]);
    expect(summary).toEqual({ versions: 4, published: 1, processing: 1, attention: 2 });
  });

  it("uses readable upload and quality language", () => {
    expect(formatTextbookBytes(20 * 1024 * 1024)).toBe("20 MB");
    expect(qualityIssueLabel("unresolved_ocr_pages")).toBe("仍有页面需要 OCR");
    expect(qualityIssueLabel("active_projection_run_id_missing")).toBe("当前教材版本缺少有效索引批次");
    expect(qualityIssueLabel("job_projection_run_id_missing")).toBe("处理任务缺少索引批次");
    expect(qualityIssueLabel("projection_run_id_mismatch")).toBe("当前教材与处理任务的索引批次不一致");
    expect(qualityIssueLabel("custom_quality_flag")).toBe("custom_quality_flag");
  });
});
