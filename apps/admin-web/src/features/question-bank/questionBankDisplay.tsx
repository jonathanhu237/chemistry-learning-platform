import { Tag } from "antd";

import type { LearningAssistantRuntime } from "../../api/learningAssistant";
import type {
  Question,
  QuestionWorkbenchCandidate,
} from "../../api/questionBank";
import { statusTag } from "../../lib/status";

export function questionTypeLabel(type?: string) {
  if (type === "single_choice") return "??";
  if (type === "true_false") return "??";
  if (type === "fill_blank") return "??";
  return type || "-";
}

export function coverageTagLabel(tag?: string) {
  const labels: Record<string, string> = {
    experiment_purpose: "????",
    true_false: "???",
    single_choice: "???",
    fill_blank: "???",
    evidence_based: "???",
    diagnostic: "???",
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
  const page = ref.page_number ? ` p.${ref.page_number}` : "";
  const section = ref.section_title ? ` · ${ref.section_title}` : "";
  return `${file}${page}${section}`;
}

export function questionPoints(question: Question) {
  const points = question.metadata?.primary_points || [];
  if (points.length) {
    return points
      .map((point) => ({
        point_node_id: String(point.point_node_id || "").trim(),
        point_key: String(point.point_key || "").trim(),
        point_title: String(point.point_title || point.point_key || point.point_node_id || "").trim(),
      }))
      .filter((point) => point.point_node_id || point.point_key || point.point_title);
  }
  const nodeIds = question.metadata?.primary_point_node_ids || [];
  if (nodeIds.length) {
    return nodeIds
      .map((id) => ({ point_node_id: String(id), point_key: "", point_title: String(id) }))
      .filter((point) => point.point_node_id);
  }
  return (question.metadata?.primary_point_keys || [])
    .map((key) => ({ point_node_id: "", point_key: String(key), point_title: String(key) }))
    .filter((point) => point.point_key);
}

export function questionPointTitles(question: Question) {
  return questionPoints(question).map((point) => point.point_title || point.point_key || point.point_node_id).filter(Boolean);
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

export function candidateQuestionPoints(candidate: QuestionWorkbenchCandidate) {
  const metadata = candidatePayload(candidate).metadata || {};
  const points = Array.isArray(metadata.primary_points) ? metadata.primary_points : [];
  if (points.length) {
    return points
      .map((point) => ({
        point_node_id: String(point?.point_node_id || "").trim(),
        point_key: String(point?.point_key || "").trim(),
        point_title: String(point?.point_title || point?.point_key || point?.point_node_id || "").trim(),
      }))
      .filter((point) => point.point_node_id || point.point_key || point.point_title);
  }
  const nodeIds = Array.isArray(metadata.primary_point_node_ids) ? metadata.primary_point_node_ids : [];
  if (nodeIds.length) {
    return nodeIds
      .map((id) => ({ point_node_id: String(id), point_key: "", point_title: String(id) }))
      .filter((point) => point.point_node_id);
  }
  const keys = Array.isArray(metadata.primary_point_keys) ? metadata.primary_point_keys : [];
  return keys.map((key) => ({ point_node_id: "", point_key: String(key), point_title: String(key) })).filter((point) => point.point_key);
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
  return questionPoints(question).some((point) => selected.has(point.point_node_id) || selected.has(point.point_key));
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
  bgeStatus: string;
  route: string;
  tone: "ready" | "checking" | "blocked";
};

export function questionWorkbenchGateFromRuntime(runtime?: LearningAssistantRuntime): QuestionWorkbenchGateState {
  const ragRuntime = runtime?.rag_runtime;
  const bgeStatus = runtime?.bge_metrics?.ok
    ? "healthy"
    : runtime?.bge_status || (runtime?.bge_error ? "unreachable" : ragRuntime?.bge_service_required ? "checking" : "not_required");
  const route = ragRuntime?.hybrid_bge_enabled
    ? "来源检索正常"
    : ragRuntime?.rag_enabled
      ? "基础来源检索"
      : "来源检索关闭";

  if (!runtime || !ragRuntime) {
    return {
      healthy: false,
      label: "正在检查",
      message: "正在确认来源检索状态，稍等一下再使用 AI 建议。",
      tagColor: "#356f9c",
      alertType: "info",
      bgeStatus: "checking",
      route,
      tone: "checking",
    };
  }
  if (!ragRuntime.rag_enabled) {
    return {
      healthy: false,
      label: "AI 暂不可用",
      message: "来源检索还没开启，暂时不能让 AI 出题或修题。",
      tagColor: "#b42318",
      alertType: "error",
      bgeStatus,
      route,
      tone: "blocked",
    };
  }
  if (!ragRuntime.hybrid_bge_enabled) {
    return {
      healthy: false,
      label: "AI 暂不可用",
      message: "来源检索还没准备好，暂时不能使用 AI 建议。",
      tagColor: "#b42318",
      alertType: "error",
      bgeStatus,
      route,
      tone: "blocked",
    };
  }
  if (!ragRuntime.query_generation_enabled) {
    return {
      healthy: false,
      label: "AI 暂不可用",
      message: "来源检索的扩展查询未开启，暂时不能使用 AI 建议。",
      tagColor: "#b42318",
      alertType: "error",
      bgeStatus,
      route,
      tone: "blocked",
    };
  }
  if (bgeStatus !== "healthy") {
    const statusText: Record<string, string> = {
      checking: "正在检查来源检索服务",
      degraded: "来源检索服务异常",
      unreachable: "来源检索服务连接不上",
      not_configured: "来源检索服务未配置",
    };
    return {
      healthy: false,
      label: bgeStatus === "checking" ? "正在检查" : "AI 暂不可用",
      message: `${statusText[bgeStatus] || "来源检索还没准备好"}，稍后再使用 AI 建议。`,
      tagColor: bgeStatus === "checking" ? "#356f9c" : "#b42318",
      alertType: bgeStatus === "checking" ? "info" : "error",
      bgeStatus,
      route,
      tone: bgeStatus === "checking" ? "checking" : "blocked",
    };
  }
  return {
    healthy: true,
    label: "AI 建议可用",
    message: "会先读取当前实验和点位的来源片段，再生成出题/修题建议。",
    tagColor: "#005826",
    alertType: "success",
    bgeStatus,
    route,
    tone: "ready",
  };
}
