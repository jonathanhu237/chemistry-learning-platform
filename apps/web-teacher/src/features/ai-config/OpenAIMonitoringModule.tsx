import { Alert, Button, Tag, Typography } from "antd";

import type { AIConfiguration } from "../../api/settings";
import { aiModeLabel, formatDateTime, lastRequestText, openAiStatus, successRate } from "./monitoringMappers";
import { LocalQueryState, MetricGrid, MetricTile, ModuleHeader } from "./MonitoringShared";

const { Text } = Typography;

type OpenAIMonitoringModuleProps = {
  data?: AIConfiguration;
  loading?: boolean;
  error?: unknown;
  retry?: () => void;
};

export function OpenAIMonitoringModule({ data, loading, error, retry }: OpenAIMonitoringModuleProps) {
  const status = data?.status;
  const currentStatus = openAiStatus(status);
  const recentRequests = status?.recent_request_count || 0;
  const recentErrors = status?.recent_error_count || 0;
  const reasoningSummary = data?.reasoning_summary;
  const reasoningSummaryEnabled = reasoningSummary?.enabled;
  return (
    <section className="ai-monitor-module">
      <LocalQueryState loading={loading} error={error} retry={retry}>
        <ModuleHeader
          eyebrow="OpenAI API"
          title={currentStatus.label}
          description={status?.message || "OpenAI-compatible provider health and recent usage."}
          status={currentStatus.label}
          tone={currentStatus.tone}
          extra={
            currentStatus.tone !== "good" ? (
              <Button size="small" href="/settings">
                去系统设置
              </Button>
            ) : null
          }
        />
        {status?.last_check_message ? (
          <Alert type={currentStatus.tone === "bad" ? "error" : "info"} showIcon className="ai-monitor-alert" message={status.last_check_message} />
        ) : null}
        <MetricGrid>
          <MetricTile label="模型" value={data?.model || "-"} />
          <MetricTile label="调用健康度" value={recentRequests ? `${successRate(recentRequests, recentErrors)}%` : "-"} tone={recentErrors ? "warn" : "good"} />
          <MetricTile label="最近检测" value={formatDateTime(status?.last_checked_at)} />
          <MetricTile label="下次检测" value={formatDateTime(status?.next_check_due_at, "-")} />
          <MetricTile label="API Key" value={data?.api_key_configured ? "已配置" : "未配置"} tone={data?.api_key_configured ? "good" : "warn"} />
          <MetricTile label="AI 通道" value={aiModeLabel(status?.effective_mode)} />
          <MetricTile
            label="思考状态"
            value={reasoningSummaryEnabled ? "Reasoning Summary" : "Agent 轨迹"}
            tone={reasoningSummaryEnabled ? "good" : reasoningSummary?.status === "failed" ? "warn" : "legacy"}
            detail={reasoningSummary?.message || "保存 OpenAI API 接入后自动检测"}
          />
          <MetricTile label="近 24 小时请求" value={recentRequests} />
          <MetricTile label="近 24 小时错误" value={<span className={recentErrors ? "danger-text" : undefined}>{recentErrors}</span>} tone={recentErrors ? "warn" : "good"} />
          <MetricTile label="最近调用" value={lastRequestText(status)} detail={<Text type="secondary">只展示调用摘要，不在监控页编辑密钥或模型。</Text>} />
        </MetricGrid>
        <div className="ai-monitor-note-row">
          <Tag color={currentStatus.color}>{currentStatus.label}</Tag>
          <Text type="secondary">Provider、Base URL、模型名和密钥保存由系统设置维护。</Text>
        </div>
      </LocalQueryState>
    </section>
  );
}
