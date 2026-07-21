import dayjs from "dayjs";

import type { LearningAssistantRuntime } from "../../api/learningAssistant";
import type { AIConfiguration } from "../../api/settings";
import type {
  AttentionItem,
  HealthTile,
  MonitorModuleKey,
  MonitorTone,
  UsageRange,
  VideoLibraryIndexDiagnostics,
  VideoLibrarySearchDiagnostics,
} from "./monitoringTypes";

export const monitorModules: Array<{ key: MonitorModuleKey; label: string; shortLabel: string }> = [
  { key: "overview", label: "总览", shortLabel: "总览" },
  { key: "openai", label: "OpenAI", shortLabel: "OpenAI" },
  { key: "rag", label: "RAG", shortLabel: "RAG" },
  { key: "es", label: "ES 检索", shortLabel: "ES" },
  { key: "dictionary", label: "词典与同步", shortLabel: "词典" },
  { key: "guardrail", label: "安全护栏", shortLabel: "护栏" },
  { key: "trends", label: "调用趋势", shortLabel: "趋势" },
];

export const rangeLabels: Record<UsageRange, string> = {
  "1d": "近 1 天",
  "7d": "近 7 天",
  "30d": "近 30 天",
};

export function errorMessage(error: unknown) {
  if (error instanceof Error) return error.message;
  return String(error || "未知错误");
}

export function formatDateTime(value?: string | null, fallback = "尚未检测") {
  return value ? dayjs(value).format("YYYY-MM-DD HH:mm") : fallback;
}

export function tagColorForTone(tone: MonitorTone) {
  if (tone === "good") return "#005826";
  if (tone === "warn") return "#b8892f";
  if (tone === "bad") return "#b42318";
  if (tone === "legacy") return "#356f9c";
  return "default";
}

export function openAiStatus(status?: AIConfiguration["status"]) {
  const meta: Record<AIConfiguration["status"]["connectivity_status"], { label: string; tone: MonitorTone; color: string }> = {
    connected: { label: "连接正常", tone: "good", color: "#005826" },
    failed: { label: "连接失败", tone: "bad", color: "#b42318" },
    stale: { label: "需重新检测", tone: "warn", color: "#b8892f" },
    untested: { label: "未检测", tone: "legacy", color: "#356f9c" },
    not_configured: { label: "待配置", tone: "idle", color: "default" },
  };
  return meta[status?.connectivity_status || "not_configured"];
}

export function aiModeLabel(mode?: string) {
  const labels: Record<string, string> = {
    not_configured: "未启用",
    connection_untested: "待自动检测",
    connection_stale: "需重新检测",
    connection_failed: "暂不可用",
    openai_api: "OpenAI API",
  };
  return labels[mode || "not_configured"] || "未知";
}

export function successRate(requests = 0, errors = 0) {
  if (!requests) return 0;
  return Math.round(((requests - errors) / requests) * 100);
}

export function lastRequestText(status?: AIConfiguration["status"]) {
  const summary = status?.last_request_summary;
  if (!summary) return "暂无调用记录";
  return `${dayjs(summary.called_at).format("YYYY-MM-DD HH:mm")} · ${summary.channel} · ${
    summary.status === "success" ? "成功" : "失败"
  }`;
}

export function ragStatus(aiConfig?: AIConfiguration, assistantRuntime?: LearningAssistantRuntime) {
  const runtime = assistantRuntime?.rag_runtime || aiConfig?.rag_runtime;
  const status = assistantRuntime?.textbook_rag_status || runtime?.textbook_rag_status || runtime?.status || "disabled";
  if (!runtime?.rag_enabled) return { label: "RAG 关闭", color: "default", tone: "idle" as MonitorTone, headline: "学生侧 RAG 未启用" };
  if (status === "healthy") return { label: "教材 RAG 可用", color: "#005826", tone: "good" as MonitorTone, headline: "外部教材 RAG 可用" };
  if (status === "disabled") return { label: "未启用", color: "default", tone: "idle" as MonitorTone, headline: runtime?.textbook_rag_message || "外部教材 RAG 未启用" };
  if (status === "index_stale") return { label: "索引需更新", color: "#b8892f", tone: "warn" as MonitorTone, headline: runtime?.textbook_rag_message || "教材 RAG 索引需更新" };
  if (status === "elasticsearch_not_configured" || status === "embedding_not_configured" || status === "rerank_not_configured" || status === "index_missing") {
    return { label: "配置缺失", color: "#b42318", tone: "bad" as MonitorTone, headline: runtime?.textbook_rag_message || "教材 RAG 配置不完整" };
  }
  if (status === "elasticsearch_unreachable" || status === "elasticsearch_error") {
    return { label: "ES 不可达", color: "#b42318", tone: "bad" as MonitorTone, headline: runtime?.textbook_rag_message || "教材 RAG Elasticsearch 不可达" };
  }
  return { label: "需检查", color: "#b8892f", tone: "warn" as MonitorTone, headline: runtime?.textbook_rag_message || "教材 RAG 状态需检查" };
}

export function ragRouteSummary(aiConfig?: AIConfiguration, assistantRuntime?: LearningAssistantRuntime) {
  const runtime = assistantRuntime?.rag_runtime || aiConfig?.rag_runtime;
  if (runtime?.rag_enabled && runtime?.textbook_rag_enabled) return `外部教材 RAG · ${runtime.textbook_rag_index || "Embedding/ES"}`;
  if (runtime?.rag_enabled) return "外部教材 RAG 未启用";
  return "RAG 已关闭";
}

export function esStatus(index?: VideoLibraryIndexDiagnostics) {
  const runtime = index?.elasticsearch;
  if (runtime?.error) return { label: "异常", tone: "bad" as MonitorTone, color: "#b42318" };
  if (runtime?.health?.status === "green") return { label: "green", tone: "good" as MonitorTone, color: "#005826" };
  if (runtime?.health?.status === "yellow") return { label: "yellow", tone: "warn" as MonitorTone, color: "#b8892f" };
  if (runtime?.configured === false) return { label: "未启用", tone: "idle" as MonitorTone, color: "default" };
  return { label: runtime?.health?.status || "待检测", tone: "idle" as MonitorTone, color: "default" };
}

export function esMappingReady(index?: VideoLibraryIndexDiagnostics) {
  const mapping = index?.elasticsearch?.mapping;
  const fields = Object.entries(mapping?.chemistry_fields_present || {});
  return Boolean(mapping?.version && mapping.version === mapping.desired_version) || (fields.length > 0 && fields.every(([, present]) => present));
}

export function dictionaryHealthy(index?: VideoLibraryIndexDiagnostics) {
  const analyzerOk = index?.settings?.analyzer_assets?.ok;
  const counts = index?.settings?.dictionary_assets?.category_counts || {};
  return analyzerOk !== false && Object.keys(counts).length > 0;
}

export function guardrailStatus(policy?: AIConfiguration["student_ai_policy"]) {
  if (!policy?.active) return { label: "待模型配置", tone: "idle" as MonitorTone, color: "default" };
  if (policy.invalid_decision_count) return { label: "兜底保护中", tone: "warn" as MonitorTone, color: "#b8892f" };
  return { label: "主动防护中", tone: "good" as MonitorTone, color: "#005826" };
}

export function searchTermGroups(search?: VideoLibrarySearchDiagnostics) {
  const terms = search?.query_plan?.terms;
  return [
    { key: "formulae", label: "化学式", values: terms?.formulae || [] },
    { key: "strict_aliases", label: "严格同义词", values: terms?.strict_aliases || [] },
    { key: "reagent_aliases", label: "试剂别名", values: terms?.reagent_aliases || [] },
    { key: "condition_tags", label: "条件标签", values: terms?.condition_tags || [] },
    { key: "phenomenon_tags", label: "现象标签", values: terms?.phenomenon_tags || [] },
    { key: "property_tags", label: "性质标签", values: terms?.property_tags || [] },
    { key: "reaction_features", label: "反应特征", values: terms?.reaction_features || [] },
  ];
}

export function dictionaryRows(index?: VideoLibraryIndexDiagnostics) {
  const counts = index?.settings?.dictionary_assets?.category_counts || {};
  return Object.entries(counts).map(([name, count]) => ({ name, count }));
}

export function buildHealthTiles(args: {
  aiConfig?: AIConfiguration;
  assistantRuntime?: LearningAssistantRuntime;
  indexDiagnostics?: VideoLibraryIndexDiagnostics;
}): HealthTile[] {
  const aiStatus = openAiStatus(args.aiConfig?.status);
  const rag = ragStatus(args.aiConfig, args.assistantRuntime);
  const es = esStatus(args.indexDiagnostics);
  const dictionaryTone: MonitorTone = dictionaryHealthy(args.indexDiagnostics) ? "good" : "warn";
  const syncCounts = args.indexDiagnostics?.postgres?.sync_status_counts || {};
  const failedSync = Number(syncCounts.failed || 0);
  const guardrail = guardrailStatus(args.aiConfig?.student_ai_policy);
  return [
    {
      key: "openai",
      label: "OpenAI",
      status: aiStatus.label,
      value: args.aiConfig?.model || "-",
      tone: aiStatus.tone,
      detail: aiConfigDetail(args.aiConfig),
    },
    {
      key: "rag",
      label: "教材 RAG",
      status: rag.label,
      value: ragRouteSummary(args.aiConfig, args.assistantRuntime),
      tone: rag.tone,
      detail: args.assistantRuntime?.checked_at ? formatDateTime(args.assistantRuntime.checked_at) : "尚未检测",
    },
    {
      key: "es",
      label: "Elasticsearch",
      status: es.label,
      value: args.indexDiagnostics?.settings?.index || "-",
      tone: es.tone,
      detail: `文档 ${args.indexDiagnostics?.elasticsearch?.document_count ?? "-"}`,
    },
    {
      key: "dictionary",
      label: "词典资产",
      status: dictionaryTone === "good" ? "就绪" : "需检查",
      value: `${Object.keys(args.indexDiagnostics?.settings?.dictionary_assets?.category_counts || {}).length} 类词典`,
      tone: dictionaryTone,
      detail: `IK 行数 ${args.indexDiagnostics?.settings?.analyzer_assets?.total_dictionary_lines ?? "-"}`,
    },
    {
      key: "dictionary",
      label: "Outbox",
      status: failedSync ? "有失败" : "已同步",
      value: `synced ${syncCounts.synced ?? 0}`,
      tone: failedSync ? "bad" : "good",
      detail: `failed ${failedSync}`,
    },
    {
      key: "guardrail",
      label: "安全护栏",
      status: guardrail.label,
      value: `${args.aiConfig?.student_ai_policy?.recent_decision_count || 0} 次判定`,
      tone: guardrail.tone,
      detail: `兜底 ${args.aiConfig?.student_ai_policy?.invalid_decision_count || 0}`,
    },
  ];
}

function aiConfigDetail(aiConfig?: AIConfiguration) {
  const status = aiConfig?.status;
  const requests = status?.recent_request_count || 0;
  const errors = status?.recent_error_count || 0;
  return requests ? `健康度 ${successRate(requests, errors)}%` : "暂无调用";
}

export function buildAttentionItems(args: {
  aiConfig?: AIConfiguration;
  assistantRuntime?: LearningAssistantRuntime;
  indexDiagnostics?: VideoLibraryIndexDiagnostics;
  searchDiagnostics?: VideoLibrarySearchDiagnostics;
}): AttentionItem[] {
  const items: AttentionItem[] = [];
  const aiStatus = openAiStatus(args.aiConfig?.status);
  if (aiStatus.tone !== "good" && aiStatus.tone !== "idle") {
    items.push({
      key: "openai-status",
      module: "openai",
      title: "OpenAI 连接需关注",
      detail: args.aiConfig?.status?.message || aiStatus.label,
      tone: aiStatus.tone === "bad" ? "bad" : "warn",
    });
  }
  if ((args.aiConfig?.status?.recent_error_count || 0) > 0) {
    items.push({
      key: "openai-errors",
      module: "openai",
      title: "近 24 小时存在 AI 调用错误",
      detail: `${args.aiConfig?.status?.recent_error_count || 0} 次错误`,
      tone: "warn",
    });
  }
  const rag = ragStatus(args.aiConfig, args.assistantRuntime);
  if (rag.tone === "warn" || rag.tone === "bad") {
    items.push({
      key: "rag-status",
      module: "rag",
      title: "教材 RAG 状态需关注",
      detail: args.assistantRuntime?.textbook_rag_error || rag.headline,
      tone: rag.tone,
    });
  }
  const es = esStatus(args.indexDiagnostics);
  if (es.tone === "warn" || es.tone === "bad") {
    items.push({
      key: "es-health",
      module: "es",
      title: "ES 索引状态需关注",
      detail: args.indexDiagnostics?.elasticsearch?.error || `当前 health=${es.label}`,
      tone: es.tone,
    });
  }
  if (!esMappingReady(args.indexDiagnostics)) {
    items.push({
      key: "es-mapping",
      module: "dictionary",
      title: "ES Mapping 版本或化学字段未完全就绪",
      detail: args.indexDiagnostics?.elasticsearch?.mapping?.version || "未读取到 mapping 版本",
      tone: "warn",
    });
  }
  if (!dictionaryHealthy(args.indexDiagnostics)) {
    items.push({
      key: "dictionary-assets",
      module: "dictionary",
      title: "化学词典资产需检查",
      detail: args.indexDiagnostics?.settings?.analyzer_assets?.missing?.join("，") || "未读取到完整词典分类",
      tone: "warn",
    });
  }
  const failedSync = Number(args.indexDiagnostics?.postgres?.sync_status_counts?.failed || 0);
  if (failedSync > 0) {
    items.push({
      key: "outbox-failed",
      module: "dictionary",
      title: "Outbox 存在失败任务",
      detail: `${failedSync} 条失败同步`,
      tone: "bad",
    });
  }
  if ((args.aiConfig?.student_ai_policy?.invalid_decision_count || 0) > 0) {
    items.push({
      key: "guardrail-invalid",
      module: "guardrail",
      title: "学生 AI 护栏出现结构兜底",
      detail: `${args.aiConfig?.student_ai_policy?.invalid_decision_count || 0} 次异常输出保护`,
      tone: "warn",
    });
  }
  if (args.searchDiagnostics?.status === "error" || args.searchDiagnostics?.error) {
    items.push({
      key: "search-diagnostics",
      module: "es",
      title: "检索诊断异常",
      detail: args.searchDiagnostics?.error || "诊断接口返回错误",
      tone: "warn",
    });
  }
  return items;
}

export function trendBuckets(status: AIConfiguration["status"] | undefined, range: UsageRange) {
  const trend = status?.usage_trends?.[range];
  if (trend?.buckets?.length) return trend.buckets;
  const currentHalfDayStart = dayjs()
    .startOf("day")
    .add(dayjs().hour() >= 12 ? 12 : 0, "hour");
  if (range === "1d") {
    return Array.from({ length: 24 }, (_, index) => ({
      bucket: dayjs().subtract(23 - index, "hour").format("YYYY-MM-DD HH:00"),
      request_count: 0,
      error_count: 0,
    }));
  }
  if (range === "7d") {
    return Array.from({ length: 14 }, (_, index) => ({
      bucket: currentHalfDayStart.subtract((13 - index) * 12, "hour").format("YYYY-MM-DD HH:00"),
      request_count: 0,
      error_count: 0,
    }));
  }
  return Array.from({ length: 30 }, (_, index) => ({
    bucket: dayjs().subtract(29 - index, "day").format("YYYY-MM-DD"),
    request_count: 0,
    error_count: 0,
  }));
}

export function trendChartData(status: AIConfiguration["status"] | undefined, range: UsageRange) {
  return trendBuckets(status, range).flatMap((bucket) => {
    const label =
      range === "1d" ? dayjs(bucket.bucket).format("HH:mm") : range === "7d" ? dayjs(bucket.bucket).format("MM/DD\nHH:mm") : dayjs(bucket.bucket).format("MM/DD");
    return [
      { time: bucket.bucket, label, type: "调用", value: bucket.request_count },
      { time: bucket.bucket, label, type: "错误", value: bucket.error_count },
    ];
  });
}
