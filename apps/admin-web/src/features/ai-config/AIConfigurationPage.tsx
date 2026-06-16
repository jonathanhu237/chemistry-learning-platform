import { lazy, Suspense, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Alert,
  Card,
  Flex,
  Segmented,
  Space,
  Tag,
  Typography,
} from "antd";
import { CheckCircleOutlined, SafetyCertificateOutlined } from "@ant-design/icons";
import dayjs from "dayjs";

import { api } from "../../api";
import type { AIConfiguration, LearningAssistantRuntime } from "../../api";
import { PageTitle } from "../../components/PageTitle";
import { QueryState } from "../../components/QueryState";
import { formatMemoryMb, formatRuntimeSeconds, formatTraceMs, warmupStatusLabel } from "../learning-assistant/runtimeFormat";
import "./ai-config.css";

const { Text, Title } = Typography;
const UsageLineChart = lazy(async () => {
  const module = await import("@ant-design/plots");
  return { default: module.Line };
});

function errorMessage(error: unknown) {
  if (error instanceof Error) return error.message;
  return String(error || "????");
}

export function AIConfigurationPage() {
  const [usageRange, setUsageRange] = useState<"1d" | "7d" | "30d">("7d");
  const aiConfig = useQuery({
    queryKey: ["ai-configuration"],
    queryFn: () => api<AIConfiguration>("/api/admin/ai-configuration"),
  });
  const assistantRuntime = useQuery({
    queryKey: ["learning-assistant-runtime", "ai-config"],
    queryFn: () => api<LearningAssistantRuntime>("/api/admin/learning-assistant/runtime"),
    enabled: Boolean(aiConfig.data),
    refetchInterval: 10000,
    refetchIntervalInBackground: true,
  });
  const status = aiConfig.data?.status;

  const statusMeta: Record<
    NonNullable<AIConfiguration["status"]>["connectivity_status"],
    { label: string; color: string; valueColor: string }
  > = {
    connected: { label: "连接正常", color: "#005826", valueColor: "#005826" },
    failed: { label: "连接失败", color: "#b42318", valueColor: "#b42318" },
    stale: { label: "需重新检测", color: "#b8892f", valueColor: "#8a6d1f" },
    untested: { label: "未检测", color: "#356f9c", valueColor: "#356f9c" },
    not_configured: { label: "待配置", color: "default", valueColor: "#697a72" },
  };
  const currentStatus = statusMeta[status?.connectivity_status || "not_configured"];
  const lastCheckedText = status?.last_checked_at
    ? dayjs(status.last_checked_at).format("YYYY-MM-DD HH:mm")
    : "尚未检测";
  const nextCheckText = status?.next_check_due_at
    ? dayjs(status.next_check_due_at).format("YYYY-MM-DD HH:mm")
    : "-";
  const modeLabels: Record<string, string> = {
    not_configured: "未启用",
    connection_untested: "待自动检测",
    connection_stale: "需重新检测",
    connection_failed: "暂不可用",
    openai_api: "OpenAI API",
  };
  const modeLabel = modeLabels[status?.effective_mode || "not_configured"] || "未知";
  const recentRequests = status?.recent_request_count || 0;
  const recentErrors = status?.recent_error_count || 0;
  const successRate = recentRequests > 0 ? Math.round(((recentRequests - recentErrors) / recentRequests) * 100) : 0;
  const rangeLabels: Record<typeof usageRange, string> = {
    "1d": "近 1 天",
    "7d": "近 7 天",
    "30d": "近 30 天",
  };
  const currentHalfDayStart = dayjs()
    .startOf("day")
    .add(dayjs().hour() >= 12 ? 12 : 0, "hour");
  const trend = status?.usage_trends?.[usageRange];
  const emptyTrendBuckets =
    usageRange === "1d"
      ? Array.from({ length: 24 }, (_, index) => ({
          bucket: dayjs().subtract(23 - index, "hour").format("YYYY-MM-DD HH:00"),
          request_count: 0,
          error_count: 0,
        }))
      : usageRange === "7d"
        ? Array.from({ length: 14 }, (_, index) => ({
            bucket: currentHalfDayStart.subtract((13 - index) * 12, "hour").format("YYYY-MM-DD HH:00"),
            request_count: 0,
            error_count: 0,
          }))
        : Array.from({ length: 30 }, (_, index) => ({
            bucket: dayjs().subtract(29 - index, "day").format("YYYY-MM-DD"),
            request_count: 0,
            error_count: 0,
          }));
  const trendBuckets = trend?.buckets?.length ? trend.buckets : emptyTrendBuckets;
  const chartData = trendBuckets.flatMap((bucket) => {
    const label =
      usageRange === "1d"
        ? dayjs(bucket.bucket).format("HH:mm")
        : usageRange === "7d"
          ? dayjs(bucket.bucket).format("MM/DD\nHH:mm")
          : dayjs(bucket.bucket).format("MM/DD");
    return [
      { time: bucket.bucket, label, type: "调用", value: bucket.request_count },
      { time: bucket.bucket, label, type: "错误", value: bucket.error_count },
    ];
  });
  const lastRequestText = status?.last_request_summary
    ? `${dayjs(status.last_request_summary.called_at).format("YYYY-MM-DD HH:mm")} · ${status.last_request_summary.channel} · ${
        status.last_request_summary.status === "success" ? "成功" : "失败"
      }`
    : "暂无调用记录";
  const trendChartConfig = {
    data: chartData,
    xField: "label",
    yField: "value",
    colorField: "type",
    height: 220,
    autoFit: true,
    smooth: true,
    point: {
      size: 3,
      shapeField: "circle",
    },
    scale: {
      y: { nice: true },
      color: { range: ["#005826", "#b42318"] },
    },
    axis: {
      x: { title: false, labelAutoHide: false, labelAutoRotate: false },
      y: {
        title: false,
        labelFormatter: (value: string) => {
          const numeric = Number(value);
          return Number.isInteger(numeric) ? String(numeric) : "";
        },
      },
    },
    legend: {
      color: { position: "top" },
    },
  };
  const policyStatus = aiConfig.data?.student_ai_policy;
  const policyOutcomes = policyStatus?.outcomes || [];
  const policyDecisionCount = policyStatus?.recent_decision_count || 0;
  const policyInvalidCount = policyStatus?.invalid_decision_count || 0;
  const policyHandledCount = policyOutcomes
    .filter((item) => item.mode !== "normal_answer")
    .reduce((sum, item) => sum + item.count, 0);
  const policyHealth = policyStatus?.active ? (policyInvalidCount ? "degraded" : "active") : "inactive";
  const policyHealthMeta = {
    active: { label: "主动防护中", color: "#005826", tone: "good" },
    degraded: { label: "兜底保护中", color: "#b8892f", tone: "warn" },
    inactive: { label: "待模型配置", color: "default", tone: "idle" },
  }[policyHealth];
  const maxPolicyOutcome = Math.max(...policyOutcomes.map((item) => item.count), 1);
  const policyRailItems = [
    { key: "scope", title: "课程范围", description: "课程外请求引导回无机化学学习", signal: "Scope" },
    { key: "experiment", title: "实验安全", description: "危险操作只讲原理和安全提醒", signal: "Safety" },
    { key: "assessment", title: "测验保护", description: "索要答案时只给思路提示", signal: "Assessment" },
    { key: "evidence", title: "平台资源", description: "资源存在性必须检索平台来源", signal: "Grounding" },
    { key: "course", title: "课程问答", description: "普通化学问题由模型回答，RAG 辅助", signal: "Answer" },
  ];
  const ragRuntime = assistantRuntime.data?.rag_runtime || aiConfig.data?.rag_runtime;
  const bgeMetrics = assistantRuntime.data?.bge_metrics || null;
  const bgeProcess = bgeMetrics?.process;
  const bgeContainer = bgeMetrics?.container;
  const bgeModels = bgeMetrics?.models;
  const bgeRequests = bgeMetrics?.requests;
  const bgeConfig = bgeMetrics?.config;
  const bgeWarmup = bgeMetrics?.warmup;
  const bgeStatus = bgeMetrics?.ok
    ? "healthy"
    : assistantRuntime.data?.bge_status || (assistantRuntime.data?.bge_error ? "unreachable" : ragRuntime?.bge_service_required ? "checking" : "not_required");
  const ragStatusMeta = (() => {
    if (!ragRuntime?.rag_enabled) return { label: "RAG 关闭", color: "default", tone: "idle", headline: "学生侧 RAG 未启用" };
    if (!ragRuntime.hybrid_bge_enabled) return { label: "Legacy", color: "#356f9c", tone: "legacy", headline: "关键词 RAG 运行中" };
    if (bgeStatus === "healthy") return { label: "Hybrid 可用", color: "#005826", tone: "good", headline: "Hybrid BGE RAG 可用" };
    if (bgeStatus === "degraded") return { label: "BGE 异常", color: "#b8892f", tone: "warn", headline: "BGE 已响应但状态异常" };
    if (bgeStatus === "not_configured") return { label: "未配置", color: "#b42318", tone: "bad", headline: "BGE 服务地址未配置" };
    if (bgeStatus === "unreachable") return { label: "不可达", color: "#b42318", tone: "bad", headline: "BGE 服务不可达" };
    return { label: "检测中", color: "#356f9c", tone: "legacy", headline: "BGE 服务检测中" };
  })();
  const ragRouteSummary = ragRuntime?.hybrid_bge_enabled
    ? "关键词召回 + BGE 向量召回 + BGE 重排"
    : ragRuntime?.rag_enabled
      ? "现有来源/关键词 RAG"
      : "RAG 已关闭";
  const ragCheckedText = assistantRuntime.data?.checked_at
    ? dayjs(assistantRuntime.data.checked_at).format("YYYY-MM-DD HH:mm:ss")
    : assistantRuntime.isLoading
      ? "检测中"
      : "尚未检测";
  const bgeRequestSummary = bgeRequests ? `${bgeRequests.embed || 0} / ${bgeRequests.rerank || 0}` : "-";
  const bgeModelSummary = bgeConfig?.embed_model || bgeConfig?.rerank_model
    ? `${bgeConfig?.embed_model || "-"} / ${bgeConfig?.rerank_model || "-"}`
    : "-";
  const configuredModel = aiConfig.data?.model || "-";

  return (
    <Space direction="vertical" size={18} className="full">
      <PageTitle title="AI接入" description="监控 OpenAI API 连接与 RAG 检索运行状态；模型、Base URL、密钥和学生 AI 能力开关在系统设置维护。" />
      <QueryState loading={aiConfig.isLoading} error={aiConfig.error}>
        <div className="ai-config-dashboard">
            <Card
              title="运行状态监控"
              className="ai-runtime-card ai-runtime-monitor-card"
              extra={
                <Tag color={assistantRuntime.isError ? "#b42318" : assistantRuntime.isFetching ? "#356f9c" : "#005826"}>
                  {assistantRuntime.isError ? "监控异常" : assistantRuntime.isFetching ? "自动检测中" : "自动监控"}
                </Tag>
              }
            >
              <div className="ai-runtime-monitor-grid">
                <section className="ai-monitor-panel ai-monitor-openai-panel">
                  <Flex justify="space-between" align="start" gap={16} className="ai-summary-head">
                    <div>
                      <Text className="eyebrow">OpenAI API</Text>
                      <Title level={3} className="ai-status-title" style={{ color: currentStatus.valueColor }}>
                        {currentStatus.label}
                      </Title>
                      <Text type="secondary">{status?.message}</Text>
                    </div>
                    <Tag color={currentStatus.color}>{currentStatus.label}</Tag>
                  </Flex>
                  {status?.last_check_message ? <Text className="block-text ai-check-message">{status.last_check_message}</Text> : null}
                  <div className="ai-monitor-tile-grid">
                    <div>
                      <span>模型</span>
                      <strong>{configuredModel}</strong>
                    </div>
                    <div>
                      <span>调用健康度</span>
                      <strong>{recentRequests ? `${successRate}%` : "-"}</strong>
                    </div>
                    <div>
                      <span>最近检测</span>
                      <strong>{lastCheckedText}</strong>
                    </div>
                    <div>
                      <span>下次检测</span>
                      <strong>{nextCheckText}</strong>
                    </div>
                    <div>
                      <span>API Key</span>
                      <strong>{aiConfig.data?.api_key_configured ? "已配置" : "未配置"}</strong>
                    </div>
                    <div>
                      <span>AI 通道</span>
                      <strong>{modeLabel}</strong>
                    </div>
                    <div>
                      <span>近 24 小时请求</span>
                      <strong>{recentRequests}</strong>
                    </div>
                    <div>
                      <span>近 24 小时错误</span>
                      <strong className={recentErrors ? "danger-text" : ""}>{recentErrors}</strong>
                    </div>
                    <div className="ai-monitor-tile-wide">
                      <span>最近调用</span>
                      <strong>{lastRequestText}</strong>
                    </div>
                  </div>
                </section>

                <section className={`ai-monitor-panel ai-monitor-rag-panel ai-rag-health-${ragStatusMeta.tone}`}>
                  <Flex justify="space-between" align="start" gap={16} className="ai-summary-head">
                    <div>
                      <Text className="eyebrow">RAG 状态监控</Text>
                      <Title level={3} className="ai-status-title">
                        {ragStatusMeta.headline}
                      </Title>
                      <Text type="secondary">{ragRouteSummary}</Text>
                    </div>
                    <Tag color={ragStatusMeta.color}>{ragStatusMeta.label}</Tag>
                  </Flex>
                  {assistantRuntime.data?.bge_error ? (
                    <Alert
                      type="warning"
                      showIcon
                      className="ai-rag-alert"
                      message="BGE sidecar 当前不可用"
                      description={assistantRuntime.data.bge_error}
                    />
                  ) : null}
                  {assistantRuntime.error ? (
                    <Alert
                      type="error"
                      showIcon
                      className="ai-rag-alert"
                      message="RAG 自动监控接口读取失败"
                      description={errorMessage(assistantRuntime.error)}
                    />
                  ) : null}
                  {bgeWarmup?.error ? (
                    <Alert
                      type="error"
                      showIcon
                      className="ai-rag-alert"
                      message="BGE 预热失败"
                      description={bgeWarmup.error}
                    />
                  ) : null}
                  <div className="ai-rag-status-grid">
                    {[
                      { label: "学生 RAG", value: ragRuntime?.rag_enabled ? "已开启" : "已关闭", tone: ragRuntime?.rag_enabled ? "ok" : "muted" },
                      { label: "BGE 实测", value: ragStatusMeta.label, tone: ragStatusMeta.tone === "bad" ? "bad" : ragStatusMeta.tone === "warn" ? "warn" : "ok" },
                      { label: "Query 生成", value: ragRuntime?.query_generation_enabled ? "已开启" : "未开启", tone: ragRuntime?.query_generation_enabled ? "ok" : "muted" },
                      { label: "最近检测", value: ragCheckedText, tone: assistantRuntime.data?.bge_error ? "bad" : "muted" },
                    ].map((item) => (
                      <div key={item.label} className={`ai-rag-status-tile ai-rag-status-tile-${item.tone}`}>
                        <span>{item.label}</span>
                        <strong>{item.value}</strong>
                      </div>
                    ))}
                  </div>

                  <div className="ai-rag-metric-grid">
                    <div>
                      <span>召回 / 重排 / 返回</span>
                      <strong>{ragRuntime ? `${ragRuntime.vector_top_k} / ${ragRuntime.rerank_top_k} / ${ragRuntime.final_top_k}` : "-"}</strong>
                    </div>
                    <div>
                      <span>服务地址</span>
                      <strong>{ragRuntime?.bge_service_url || "-"}</strong>
                    </div>
                    <div>
                      <span>接口延迟</span>
                      <strong>{formatTraceMs(bgeMetrics?.request_ms)}</strong>
                    </div>
                    <div>
                      <span>模型加载</span>
                      <strong>
                        {bgeModels ? `${bgeModels.embed_loaded ? "E ready" : "E cold"} / ${bgeModels.rerank_loaded ? "R ready" : "R cold"}` : "-"}
                      </strong>
                    </div>
                    <div>
                      <span>向量请求 / 重排请求</span>
                      <strong>{bgeRequestSummary}</strong>
                    </div>
                    <div>
                      <span>内存</span>
                      <strong>{formatMemoryMb(bgeContainer?.memory_current_mb ?? bgeProcess?.memory_rss_mb)}</strong>
                    </div>
                    <div>
                      <span>运行时长</span>
                      <strong>{formatRuntimeSeconds(bgeProcess?.uptime_seconds)}</strong>
                    </div>
                    <div>
                      <span>预热</span>
                      <strong>{warmupStatusLabel(bgeWarmup?.status)}</strong>
                    </div>
                  </div>

                    <div className="ai-rag-model-panel">
                    <span>模型 · 每 10 秒自动更新</span>
                    <strong>{bgeModelSummary}</strong>
                    <small>
                      {bgeConfig?.device ? `device=${bgeConfig.device}` : "BGE metrics 未返回设备信息"}
                      {bgeConfig?.offline !== undefined ? ` · offline=${String(bgeConfig.offline)}` : ""}
                    </small>
                  </div>
                </section>
              </div>
            </Card>

            <Card title="AI 使用概况" className="ai-usage-card">
              <div className="ai-usage-layout">
                <div className="ai-usage-stats">
                  <div className="ai-usage-health">
                    <div>
                      <Text type="secondary">调用健康度</Text>
                      <strong>{recentRequests ? `${successRate}%` : "-"}</strong>
                    </div>
                    <Tag color={recentErrors ? "#b42318" : "#005826"}>{recentErrors ? "存在错误" : "稳定运行"}</Tag>
                  </div>
                  <div className="ai-usage-mini-grid">
                    <div className="ai-usage-mini-card">
                      <span>近 24 小时请求</span>
                      <strong>{recentRequests}</strong>
                    </div>
                    <div className="ai-usage-mini-card">
                      <span>错误</span>
                      <strong className={recentErrors ? "danger-text" : ""}>{recentErrors}</strong>
                    </div>
                    <div className="ai-usage-mini-card">
                      <span>成功请求</span>
                      <strong>{Math.max(0, recentRequests - recentErrors)}</strong>
                    </div>
                  </div>
                  <div className="ai-usage-last-call">
                    <span>最近调用</span>
                    <strong>{lastRequestText}</strong>
                  </div>
                </div>
                <div className="ai-usage-chart">
                  <Flex justify="space-between" align="center" className="ai-chart-heading">
                    <div>
                      <Text strong>{rangeLabels[usageRange]}调用趋势</Text>
                      <Text type="secondary" className="block-text">
                        本系统 Agent 日志
                      </Text>
                    </div>
                    <Segmented
                      size="small"
                      value={usageRange}
                      onChange={(value) => setUsageRange(value as "1d" | "7d" | "30d")}
                      options={[
                        { label: "1天", value: "1d" },
                        { label: "7天", value: "7d" },
                        { label: "30天", value: "30d" },
                      ]}
                    />
                  </Flex>
                  <div
                    className="ai-line-chart"
                    aria-label={`${rangeLabels[usageRange]} AI 调用趋势，${trendBuckets.length}个时间点`}
                    data-trend-points={trendBuckets.length}
                  >
                    <Suspense fallback={<div className="ai-line-chart-placeholder" />}>
                      <UsageLineChart {...trendChartConfig} />
                    </Suspense>
                  </div>
                </div>
              </div>
            </Card>

            <Card
              title={
                <Flex align="center" gap={10}>
                  <SafetyCertificateOutlined />
                  <span>学生 AI 安全护栏</span>
                </Flex>
              }
              extra={<Tag color={policyHealthMeta.color}>{policyHealthMeta.label}</Tag>}
              className="ai-policy-card"
            >
              <div className="ai-guardrail-command">
                <div className={`ai-guardrail-shield ai-guardrail-shield-${policyHealthMeta.tone}`}>
                  <div className="ai-guardrail-radar" aria-hidden="true">
                    <div className="ai-guardrail-radar-grid" />
                    <div className="ai-guardrail-radar-sweep" />
                    <div className="ai-guardrail-radar-pulse ai-guardrail-radar-pulse-one" />
                    <div className="ai-guardrail-radar-pulse ai-guardrail-radar-pulse-two" />
                    <SafetyCertificateOutlined />
                  </div>
                  <div className="ai-guardrail-shield-copy">
                    <Text type="secondary">Guardrail Core</Text>
                    <Title level={3}>{policyHealthMeta.label}</Title>
                    <Text>学生提问进入模型前完成风险判定，命中风险时按策略拦截、提示或降级。</Text>
                  </div>
                </div>

                <div className="ai-guardrail-operations">
                  <div className="ai-guardrail-headline">
                    <div>
                      <Text className="eyebrow">Student AI Defense</Text>
                      <Title level={3}>输入检查、策略判定、受控输出</Title>
                      <Text type="secondary">
                        普通课程问答允许模型回答，RAG 用作辅助；平台资源、安全实验和测验答案仍由护栏强约束。
                      </Text>
                    </div>
                    <div className="ai-guardrail-version">
                      <span>Policy</span>
                      <strong>{policyStatus?.version || "student-ai-policy-v1"}</strong>
                    </div>
                  </div>

                  <div className="ai-guardrail-pipeline">
                    {[
                      { key: "input", label: "输入层", value: "学生提问" },
                      { key: "gate", label: "判定层", value: policyStatus?.model || "本地策略" },
                      { key: "action", label: "处置层", value: "放行 / 提示 / 拒答" },
                    ].map((stage, index) => (
                      <div key={stage.key} className={`ai-guardrail-stage ${index === 1 ? "ai-guardrail-stage-active" : ""}`}>
                        <span>{stage.label}</span>
                        <strong>{stage.value}</strong>
                        {index < 2 ? <i aria-hidden="true" /> : null}
                      </div>
                    ))}
                  </div>

                  <div className="ai-guardrail-metrics">
                    <div className="ai-guardrail-metric">
                      <Text type="secondary">近 24 小时判定</Text>
                      <strong>{policyDecisionCount}</strong>
                      <span>实时日志</span>
                    </div>
                    <div className="ai-guardrail-metric ai-guardrail-metric-warn">
                      <Text type="secondary">已处置风险</Text>
                      <strong>{policyHandledCount}</strong>
                      <span>拒答 / 提示 / 兜底</span>
                    </div>
                    <div className="ai-guardrail-metric">
                      <Text type="secondary">结构兜底</Text>
                      <strong className={policyInvalidCount ? "danger-text" : ""}>{policyInvalidCount}</strong>
                      <span>异常输出保护</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="ai-guardrail-layers">
                {policyRailItems.map((item, index) => (
                  <div key={item.key} className="ai-policy-rail-item">
                    <div className="ai-policy-rail-top">
                      <span className="ai-policy-rail-index">{String(index + 1).padStart(2, "0")}</span>
                      <span className="ai-policy-rail-signal">{item.signal}</span>
                    </div>
                    <div className="ai-policy-rail-content">
                      <Text strong className="ai-policy-rail-title">{item.title}</Text>
                      <Text type="secondary" className="ai-policy-rail-description">
                        {item.description}
                      </Text>
                    </div>
                    <div className="ai-policy-rail-status">
                      <CheckCircleOutlined />
                      <span>已启用</span>
                    </div>
                  </div>
                ))}
              </div>

              <div className="ai-policy-outcome-panel">
                <Flex justify="space-between" align="center" gap={12} className="ai-policy-section-head">
                  <Text strong>最近判定分布</Text>
                  <Text type="secondary">本系统 Agent 日志</Text>
                </Flex>
                {policyOutcomes.length ? (
                  <div className="ai-policy-outcomes">
                    {policyOutcomes.map((item) => (
                      <div key={item.mode} className="ai-policy-outcome">
                        <div>
                          <span>{item.label}</span>
                          <div className="ai-policy-outcome-track">
                            <i style={{ width: `${Math.max(8, Math.round((item.count / maxPolicyOutcome) * 100))}%` }} />
                          </div>
                        </div>
                        <strong>{item.count}</strong>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="ai-policy-empty">
                    暂无学生 AI 安全判定记录
                  </div>
                )}
              </div>
            </Card>

          </div>
      </QueryState>
    </Space>
  );
}
