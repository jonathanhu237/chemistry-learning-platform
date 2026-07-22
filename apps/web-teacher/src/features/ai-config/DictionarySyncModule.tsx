import { Alert, Tag, Typography } from "antd";

import { dictionaryRows, esMappingReady, esStatus, errorMessage } from "./monitoringMappers";
import { LocalQueryState, MetricGrid, MetricTile, ModuleHeader } from "./MonitoringShared";
import type { TeacherCatalogIndexDiagnostics } from "./monitoringTypes";

const { Text } = Typography;

type DictionarySyncModuleProps = {
  data?: TeacherCatalogIndexDiagnostics;
  loading?: boolean;
  error?: unknown;
  retry?: () => void;
};

export function DictionarySyncModule({ data, loading, error, retry }: DictionarySyncModuleProps) {
  const settings = data?.settings;
  const esRuntime = data?.elasticsearch;
  const mapping = esRuntime?.mapping;
  const syncCounts = data?.postgres?.sync_status_counts || {};
  const rows = dictionaryRows(data);
  const fields = Object.entries(mapping?.chemistry_fields_present || {});
  const health = esStatus(data);
  const analyzerMissing = settings?.analyzer_assets?.missing || [];

  return (
    <section className="ai-monitor-module">
      <LocalQueryState loading={loading} error={error} retry={retry}>
        <ModuleHeader
          eyebrow="Dictionary & Sync"
          title={esRuntime?.configured ? `索引 ${settings?.index || "-"}` : "ES 索引未启用"}
          description={`后端：${settings?.backend || "-"} · analyzer：${settings?.analyzer || "-"} · fallback：${String(settings?.local_fallback ?? false)}`}
          status={health.label}
          tone={health.tone}
        />
        {esRuntime?.error || error ? (
          <Alert type="warning" showIcon className="ai-monitor-alert" message="ES 诊断异常" description={esRuntime?.error || errorMessage(error)} />
        ) : null}
        {analyzerMissing.length ? (
          <Alert type="warning" showIcon className="ai-monitor-alert" message="词典资产缺失" description={analyzerMissing.join("，")} />
        ) : null}
        <MetricGrid>
          <MetricTile label="Mapping 版本" value={mapping?.version || "旧索引/未建索引"} tone={esMappingReady(data) ? "good" : "warn"} />
          <MetricTile label="期望版本" value={settings?.desired_mapping_version || mapping?.desired_version || "-"} />
          <MetricTile label="ES 文档数" value={esRuntime?.document_count ?? "-"} />
          <MetricTile label="已发布三要素" value={data?.postgres?.published_point_content_count ?? "-"} />
          <MetricTile label="outbox synced" value={syncCounts.synced ?? 0} tone="good" />
          <MetricTile label="outbox failed" value={syncCounts.failed ?? 0} tone={(syncCounts.failed ?? 0) > 0 ? "bad" : "good"} />
          <MetricTile label="IK 词典行数" value={settings?.analyzer_assets?.total_dictionary_lines ?? "-"} />
          <MetricTile label="词典版本" value={settings?.dictionary_assets?.version || "-"} />
        </MetricGrid>
        <div className="ai-monitor-two-column">
          <section className="ai-monitor-subpanel">
            <h3>化学字段</h3>
            <div className="ai-monitor-tag-list">
              {fields.length ? (
                fields.map(([field, present]) => (
                  <Tag key={field} color={present ? "#005826" : "#b42318"}>
                    {field}
                  </Tag>
                ))
              ) : (
                <Text type="secondary">当前索引尚未暴露化学字段状态</Text>
              )}
            </div>
          </section>
          <section className="ai-monitor-subpanel">
            <h3>词典分类</h3>
            <div className="ai-monitor-dictionary-list">
              {rows.length ? (
                rows.map((row) => (
                  <div key={row.name}>
                    <span>{row.name}</span>
                    <strong>{row.count}</strong>
                  </div>
                ))
              ) : (
                <Text type="secondary">暂无词典分类统计</Text>
              )}
            </div>
          </section>
        </div>
        <section className="ai-monitor-subpanel">
          <h3>Outbox 状态</h3>
          <div className="ai-monitor-tag-list">
            {Object.entries(syncCounts).length ? (
              Object.entries(syncCounts).map(([status, count]) => (
                <Tag key={status} color={status === "failed" && Number(count) > 0 ? "#b42318" : undefined}>
                  {status}: {count}
                </Tag>
              ))
            ) : (
              <Text type="secondary">暂无同步状态统计</Text>
            )}
          </div>
        </section>
      </LocalQueryState>
    </section>
  );
}
