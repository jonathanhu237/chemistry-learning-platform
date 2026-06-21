import type { ReactNode } from "react";
import { Alert, Button, Empty, Spin, Tag, Typography } from "antd";

import { errorMessage, tagColorForTone } from "./monitoringMappers";
import type { MonitorTone } from "./monitoringTypes";

const { Text, Title } = Typography;

export function ModuleHeader({
  eyebrow,
  title,
  description,
  status,
  tone = "idle",
  extra,
}: {
  eyebrow: string;
  title: string;
  description?: ReactNode;
  status?: string;
  tone?: MonitorTone;
  extra?: ReactNode;
}) {
  return (
    <div className="ai-monitor-module-head">
      <div>
        <Text className="eyebrow">{eyebrow}</Text>
        <Title level={3}>{title}</Title>
        {description ? <Text type="secondary" className="block-text">{description}</Text> : null}
      </div>
      <div className="ai-monitor-module-actions">
        {status ? <Tag color={tagColorForTone(tone)}>{status}</Tag> : null}
        {extra}
      </div>
    </div>
  );
}

export function MetricGrid({ children, compact = false }: { children: ReactNode; compact?: boolean }) {
  return <div className={compact ? "ai-monitor-metric-grid ai-monitor-metric-grid-compact" : "ai-monitor-metric-grid"}>{children}</div>;
}

export function MetricTile({ label, value, tone, detail }: { label: string; value: ReactNode; tone?: MonitorTone; detail?: ReactNode }) {
  return (
    <div className={tone ? `ai-monitor-metric-tile ai-monitor-tone-${tone}` : "ai-monitor-metric-tile"}>
      <span>{label}</span>
      <strong>{value}</strong>
      {detail ? <small>{detail}</small> : null}
    </div>
  );
}

export function TagsList({ values, limit = 8 }: { values?: string[]; limit?: number }) {
  if (!values?.length) return <Text type="secondary">-</Text>;
  return (
    <div className="ai-monitor-tag-list">
      {values.slice(0, limit).map((value) => (
        <Tag key={value}>{value}</Tag>
      ))}
      {values.length > limit ? <Tag>+{values.length - limit}</Tag> : null}
    </div>
  );
}

export function LocalQueryState({
  loading,
  error,
  empty,
  children,
  retry,
}: {
  loading?: boolean;
  error?: unknown;
  empty?: boolean;
  children: ReactNode;
  retry?: () => void;
}) {
  if (loading) {
    return (
      <div className="ai-monitor-local-state">
        <Spin />
      </div>
    );
  }
  if (error) {
    return (
      <Alert
        type="error"
        showIcon
        title="模块读取失败"
        description={errorMessage(error)}
        action={retry ? <Button size="small" onClick={retry}>重试</Button> : undefined}
      />
    );
  }
  if (empty) {
    return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无数据" />;
  }
  return children;
}
