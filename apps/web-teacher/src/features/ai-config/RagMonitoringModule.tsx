import { Alert, Typography } from "antd";

import type { LearningAssistantRuntime } from "../../api/learningAssistant";
import type { AIConfiguration } from "../../api/settings";
import { formatMemoryMb, formatRuntimeSeconds, formatTraceMs, warmupStatusLabel } from "../../lib/runtimeFormat";
import { formatDateTime, ragRouteSummary, ragStatus } from "./monitoringMappers";
import { LocalQueryState, MetricGrid, MetricTile, ModuleHeader } from "./MonitoringShared";

const { Text } = Typography;

type RagMonitoringModuleProps = {
  aiConfig?: AIConfiguration;
  runtime?: LearningAssistantRuntime;
  loading?: boolean;
  error?: unknown;
  retry?: () => void;
};

export function RagMonitoringModule({ aiConfig, runtime, loading, error, retry }: RagMonitoringModuleProps) {
  const ragRuntime = runtime?.rag_runtime || aiConfig?.rag_runtime;
  const metrics = runtime?.bge_metrics || null;
  const meta = ragStatus(aiConfig, runtime);
  const process = metrics?.process;
  const container = metrics?.container;
  const models = metrics?.models;
  const requests = metrics?.requests;
  const config = metrics?.config;
  const warmup = metrics?.warmup;
  const requestSummary = requests ? `${requests.embed || 0} / ${requests.rerank || 0}` : "-";
  const modelSummary = config?.embed_model || config?.rerank_model ? `${config?.embed_model || "-"} / ${config?.rerank_model || "-"}` : "-";

  return (
    <section className="ai-monitor-module">
      <LocalQueryState loading={loading} error={error} retry={retry}>
        <ModuleHeader eyebrow="RAG Runtime" title={meta.headline} description={ragRouteSummary(aiConfig, runtime)} status={meta.label} tone={meta.tone} />
        {runtime?.bge_error ? (
          <Alert type="warning" showIcon className="ai-monitor-alert" message="BGE sidecar 当前不可用" description={runtime.bge_error} />
        ) : null}
        {warmup?.error ? <Alert type="error" showIcon className="ai-monitor-alert" message="BGE 预热失败" description={warmup.error} /> : null}
        <MetricGrid>
          <MetricTile label="学生 RAG" value={ragRuntime?.rag_enabled ? "已开启" : "已关闭"} tone={ragRuntime?.rag_enabled ? "good" : "idle"} />
          <MetricTile label="BGE 实测" value={meta.label} tone={meta.tone} />
          <MetricTile label="Query 生成" value={ragRuntime?.query_generation_enabled ? "已开启" : "未开启"} tone={ragRuntime?.query_generation_enabled ? "good" : "idle"} />
          <MetricTile label="最近检测" value={runtime?.checked_at ? formatDateTime(runtime.checked_at, "-") : "尚未检测"} />
          <MetricTile label="召回 / 重排 / 返回" value={ragRuntime ? `${ragRuntime.vector_top_k} / ${ragRuntime.rerank_top_k} / ${ragRuntime.final_top_k}` : "-"} />
          <MetricTile label="接口延迟" value={formatTraceMs(metrics?.request_ms)} />
          <MetricTile label="模型加载" value={models ? `${models.embed_loaded ? "E ready" : "E cold"} / ${models.rerank_loaded ? "R ready" : "R cold"}` : "-"} />
          <MetricTile label="向量请求 / 重排请求" value={requestSummary} />
          <MetricTile label="内存" value={formatMemoryMb(container?.memory_current_mb ?? process?.memory_rss_mb)} />
          <MetricTile label="运行时长" value={formatRuntimeSeconds(process?.uptime_seconds)} />
          <MetricTile label="预热" value={warmupStatusLabel(warmup?.status)} />
          <MetricTile label="服务地址" value={ragRuntime?.bge_service_url || "-"} />
        </MetricGrid>
        <div className="ai-monitor-long-value">
          <span>模型</span>
          <strong>{modelSummary}</strong>
          <Text type="secondary">
            {config?.device ? `device=${config.device}` : "BGE metrics 未返回设备信息"}
            {config?.offline !== undefined ? ` · offline=${String(config.offline)}` : ""}
          </Text>
        </div>
      </LocalQueryState>
    </section>
  );
}
