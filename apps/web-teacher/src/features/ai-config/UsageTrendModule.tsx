import { lazy, Suspense } from "react";
import { Segmented, Typography } from "antd";

import type { AIConfiguration } from "../../api/settings";
import { rangeLabels, trendBuckets, trendChartData } from "./monitoringMappers";
import type { UsageRange } from "./monitoringTypes";
import { MetricGrid, MetricTile, ModuleHeader } from "./MonitoringShared";

const { Text } = Typography;
const UsageLineChart = lazy(async () => {
  const module = await import("@ant-design/plots");
  return { default: module.Line };
});

type UsageTrendModuleProps = {
  status?: AIConfiguration["status"];
  range: UsageRange;
  onRangeChange: (range: UsageRange) => void;
};

export function UsageTrendModule({ status, range, onRangeChange }: UsageTrendModuleProps) {
  const requests = status?.recent_request_count || 0;
  const errors = status?.recent_error_count || 0;
  const buckets = trendBuckets(status, range);
  const chartData = trendChartData(status, range);
  const chartConfig = {
    data: chartData,
    xField: "label",
    yField: "value",
    colorField: "type",
    height: 260,
    autoFit: true,
    smooth: true,
    point: { size: 3, shapeField: "circle" },
    scale: { y: { nice: true }, color: { range: ["#005826", "#b42318"] } },
    axis: {
      x: { title: false, labelAutoHide: true, labelAutoRotate: false },
      y: {
        title: false,
        labelFormatter: (value: string) => {
          const numeric = Number(value);
          return Number.isInteger(numeric) ? String(numeric) : "";
        },
      },
    },
    legend: { color: { position: "top" } },
  };
  return (
    <section className="ai-monitor-module">
      <ModuleHeader
        eyebrow="Usage Trends"
        title={`${rangeLabels[range]}调用趋势`}
        description="本系统 Agent 日志"
        extra={
          <Segmented
            size="small"
            value={range}
            onChange={(value) => onRangeChange(value as UsageRange)}
            options={[
              { label: "1天", value: "1d" },
              { label: "7天", value: "7d" },
              { label: "30天", value: "30d" },
            ]}
          />
        }
      />
      <MetricGrid compact>
        <MetricTile label="近 24 小时请求" value={requests} />
        <MetricTile label="错误" value={<span className={errors ? "danger-text" : undefined}>{errors}</span>} tone={errors ? "warn" : "good"} />
        <MetricTile label="成功请求" value={Math.max(0, requests - errors)} />
      </MetricGrid>
      <div className="ai-line-chart" aria-label={`${rangeLabels[range]} AI 调用趋势，${buckets.length}个时间点`} data-trend-points={buckets.length}>
        <Suspense fallback={<div className="ai-line-chart-placeholder" />}>
          <UsageLineChart {...chartConfig} />
        </Suspense>
      </div>
      {!buckets.some((bucket) => bucket.request_count || bucket.error_count) ? (
        <Text type="secondary" className="block-text ai-monitor-empty-note">当前时间范围暂无调用趋势数据。</Text>
      ) : null}
    </section>
  );
}
