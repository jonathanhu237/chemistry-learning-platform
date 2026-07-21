import { Tag } from "antd";

import type { LearningAssistantRuntime } from "../../api/learningAssistant";
import type {
  Question,
  QuestionWorkbenchCandidate,
} from "../../api/questionBank";
import { statusTag } from "../../lib/status";

export type DisplayQuestionPoint = {
  point_node_id: string;
  source_placement_node_id: string;
  canonical_point_id: string;
  point_key: string;
  point_title: string;
};

function pointDisplayTitle(point: {
  point_title?: string;
  point_key?: string;
  canonical_point_id?: string;
  source_placement_node_id?: string;
  point_node_id?: string;
}) {
  return (
    point.point_title ||
    point.point_key ||
    point.canonical_point_id ||
    point.source_placement_node_id ||
    point.point_node_id ||
    ""
  );
}

export function questionTypeLabel(type?: string) {
  if (type === "single_choice") return "选择";
  if (type === "true_false") return "判断";
  if (type === "fill_blank") return "填空";
  return type || "-";
}

export function coverageTagLabel(tag?: string) {
  const labels: Record<string, string> = {
    experiment_purpose: "实验目的",
    true_false: "判断题",
    single_choice: "选择题",
    fill_blank: "填空题",
    evidence_based: "证据题",
    diagnostic: "诊断题",
  };
  return labels[String(tag || "")] || String(tag || "-").replace(/_/g, " ");
}

export function answerText(answer?: Record<string, unknown>) {
  if (!answer) return "-";
  if (Array.isArray(answer.accepted_answers)) return answer.accepted_answers.map(String).join("，");
  if (answer.value !== undefined) {
    if (typeof answer.value === "boolean") return answer.value ? "正确" : "错误";
    return String(answer.value);
  }
  return JSON.stringify(answer);
}

export function sourceRefLabel(ref: Record<string, unknown>) {
  const file = String(ref.source_file || "资料片段");
  const page = ref.page_number ? ` 第 ${ref.page_number} 页` : "";
  const section = ref.section_title ? ` · ${ref.section_title}` : "";
  return `${file}${page}${section}`;
}

export function questionPoints(question: Question): DisplayQuestionPoint[] {
  const points = question.metadata?.primary_points || [];
  if (points.length) {
    return points
      .map((point) => ({
        point_node_id: String(point.point_node_id || "").trim(),
        source_placement_node_id: String(point.source_placement_node_id || point.point_node_id || "").trim(),
        canonical_point_id: String(point.canonical_point_id || "").trim(),
        point_key: String(point.point_key || "").trim(),
        point_title: pointDisplayTitle(point).trim(),
      }))
      .filter((point) => point.point_node_id || point.source_placement_node_id || point.canonical_point_id || point.point_key || point.point_title);
  }
  const nodeIds = question.metadata?.primary_point_node_ids || [];
  if (nodeIds.length) {
    return nodeIds
      .map((id) => ({
        point_node_id: String(id),
        source_placement_node_id: String(id),
        canonical_point_id: "",
        point_key: "",
        point_title: String(id),
      }))
      .filter((point) => point.point_node_id);
  }
  const canonicalIds = question.metadata?.primary_canonical_point_ids || [];
  if (canonicalIds.length) {
    return canonicalIds
      .map((id) => ({ point_node_id: "", source_placement_node_id: "", canonical_point_id: String(id), point_key: "", point_title: String(id) }))
      .filter((point) => point.canonical_point_id);
  }
  return (question.metadata?.primary_point_keys || [])
    .map((key) => ({ point_node_id: "", source_placement_node_id: "", canonical_point_id: "", point_key: String(key), point_title: String(key) }))
    .filter((point) => point.point_key);
}

export function questionPointTitles(question: Question) {
  return questionPoints(question).map(pointDisplayTitle).filter(Boolean);
}

export function candidatePayload(candidate: QuestionWorkbenchCandidate) {
  return candidate.payload || {};
}

export function candidateStem(candidate: QuestionWorkbenchCandidate) {
  return String(candidatePayload(candidate).stem || "");
}

export function candidateQuestionType(candidate: QuestionWorkbenchCandidate) {
  return String(candidatePayload(candidate).question_type || "");
}

export function candidateQuestionPoints(candidate: QuestionWorkbenchCandidate): DisplayQuestionPoint[] {
  const metadata = candidatePayload(candidate).metadata || {};
  const points = Array.isArray(metadata.primary_points) ? metadata.primary_points : [];
  if (points.length) {
    return points
      .map((point) => ({
        point_node_id: String(point?.point_node_id || "").trim(),
        source_placement_node_id: String(point?.source_placement_node_id || point?.point_node_id || "").trim(),
        canonical_point_id: String(point?.canonical_point_id || "").trim(),
        point_key: String(point?.point_key || "").trim(),
        point_title: pointDisplayTitle(point || {}).trim(),
      }))
      .filter((point) => point.point_node_id || point.source_placement_node_id || point.canonical_point_id || point.point_key || point.point_title);
  }
  const nodeIds = Array.isArray(metadata.primary_point_node_ids) ? metadata.primary_point_node_ids : [];
  if (nodeIds.length) {
    return nodeIds
      .map((id) => ({
        point_node_id: String(id),
        source_placement_node_id: String(id),
        canonical_point_id: "",
        point_key: "",
        point_title: String(id),
      }))
      .filter((point) => point.point_node_id);
  }
  const canonicalIds = Array.isArray(metadata.primary_canonical_point_ids) ? metadata.primary_canonical_point_ids : [];
  if (canonicalIds.length) {
    return canonicalIds
      .map((id) => ({ point_node_id: "", source_placement_node_id: "", canonical_point_id: String(id), point_key: "", point_title: String(id) }))
      .filter((point) => point.canonical_point_id);
  }
  const keys = Array.isArray(metadata.primary_point_keys) ? metadata.primary_point_keys : [];
  return keys.map((key) => ({ point_node_id: "", source_placement_node_id: "", canonical_point_id: "", point_key: String(key), point_title: String(key) })).filter((point) => point.point_key);
}

export function candidateValidationErrors(candidate: QuestionWorkbenchCandidate) {
  return candidate.validation_errors?.length
    ? candidate.validation_errors
    : candidate.draft_validation_errors?.length
      ? candidate.draft_validation_errors
      : [];
}

export function questionHasAnyPoint(question: Question, pointKeys: string[]) {
  if (!pointKeys.length) return true;
  const selected = new Set(pointKeys);
  return questionPoints(question).some(
    (point) =>
      selected.has(point.point_node_id) ||
      selected.has(point.source_placement_node_id) ||
      selected.has(point.canonical_point_id) ||
      selected.has(point.point_key),
  );
}

export function evidenceStatusTag(question: Question) {
  if (question.metadata?.source_audit?.evidence_sufficient) return <Tag color="green">证据已核对</Tag>;
  if (question.source_refs?.length) return <Tag color="gold">有来源</Tag>;
  return <Tag>待核对</Tag>;
}

export function evidenceStatusText(question: Question) {
  if (question.metadata?.source_audit?.evidence_sufficient) return "证据已核对";
  if (question.source_refs?.length) return "有来源";
  return "待核对";
}

export function reviewDecisionText(decision?: string) {
  if (decision === "keep") return "审查保留";
  if (decision === "rewrite") return "建议改写";
  if (decision === "reject") return "已拒绝";
  return "未审查";
}

export function questionBankStatusTag(status?: string) {
  if (status === "published") return <Tag color="green">启用</Tag>;
  if (status === "disabled") return <Tag>未启用</Tag>;
  return statusTag(status);
}

export function questionBankStatusText(status?: string) {
  if (status === "published") return "启用";
  if (status === "disabled") return "未启用";
  return status || "-";
}

export type QuestionWorkbenchGateState = {
  healthy: boolean;
  label: string;
  message: string;
  tagColor: string;
  alertType: "success" | "info" | "warning" | "error";
  textbookStatus: string;
  route: string;
  tone: "ready" | "checking" | "blocked";
};

export const textbookSectionLabels: Record<string, string> = {
  principle: "实验原理",
  phenomenon: "现象解释",
  safety: "安全提示",
};

export type WorkbenchEvidenceSection = {
  pointKey: string;
  pointTitle: string;
  section: string;
  sufficient: boolean;
  sourceCount: number;
  sources: Record<string, unknown>[];
  missingReason: string;
};

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as Record<string, unknown>) : {};
}

export function workbenchEvidenceSectionsFromPackage(evidencePackage?: Record<string, unknown> | null): WorkbenchEvidenceSection[] {
  const pointPackages = asRecord(evidencePackage?.point_packages);
  const fromPointPackages = Object.entries(pointPackages).flatMap(([pointKey, rawPointPackage]) => {
    const pointPackage = asRecord(rawPointPackage);
    const point = asRecord(pointPackage.point);
    const sections = asRecord(pointPackage.sections);
    return Object.entries(sections).map(([section, rawSectionPackage]) => {
      const sectionPackage = asRecord(rawSectionPackage);
      const sources = Array.isArray(sectionPackage.sources)
        ? sectionPackage.sources.map((source) => asRecord(source))
        : [];
      return {
        pointKey,
        pointTitle: String(point.point_title || pointKey),
        section,
        sufficient: Boolean(sectionPackage.sufficient),
        sourceCount: sources.length,
        sources,
        missingReason: String(sectionPackage.missing_reason || ""),
      };
    });
  });
  if (fromPointPackages.length) return fromPointPackages;
  const sourceRefs = Array.isArray(evidencePackage?.source_refs)
    ? evidencePackage.source_refs.map((source) => asRecord(source))
    : [];
  const grouped = new Map<string, WorkbenchEvidenceSection>();
  sourceRefs.forEach((source) => {
    const section = String(source.evidence_role || source.section || "supplemental");
    const pointKey = String(source.point_node_id || source.canonical_point_id || "当前点位");
    const key = `${pointKey}:${section}`;
    const current =
      grouped.get(key) ||
      {
        pointKey,
        pointTitle: String(source.point_title || pointKey),
        section,
        sufficient: true,
        sourceCount: 0,
        sources: [],
        missingReason: "",
      };
    current.sources.push(source);
    current.sourceCount = current.sources.length;
    grouped.set(key, current);
  });
  return Array.from(grouped.values());
}

export function questionWorkbenchGateFromRuntime(runtime?: LearningAssistantRuntime): QuestionWorkbenchGateState {
  const ragRuntime = runtime?.rag_runtime;
  const textbookStatus = runtime?.textbook_rag_status || ragRuntime?.textbook_rag_status || "disabled";
  const route = ragRuntime?.textbook_rag_enabled
    ? `教材 RAG · ${ragRuntime.textbook_rag_index || "Embedding/ES"}`
    : ragRuntime?.rag_enabled
      ? "教材 RAG 未启用"
      : "来源检索关闭";

  if (!runtime || !ragRuntime) {
    return {
      healthy: false,
      label: "正在检查",
      message: "正在确认来源检索状态，稍等一下再使用 AI 建议。",
      tagColor: "#356f9c",
      alertType: "info",
      textbookStatus,
      route,
      tone: "checking",
    };
  }
  return {
    healthy: true,
    label: "AI 出题可用",
    message:
      textbookStatus === "healthy"
        ? "出题会读取已绑定教材证据；需要更新证据时可刷新本章或当前点位。"
        : "出题只读取已绑定教材证据；刷新证据前需先检查 Embedding、Rerank 与 Elasticsearch 配置。",
    tagColor: "#005826",
    alertType: "success",
    textbookStatus,
    route,
    tone: "ready",
  };
}
