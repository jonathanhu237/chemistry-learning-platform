import { Button, Input, Tag, Typography } from "antd";
import { ReloadOutlined, SearchOutlined } from "@ant-design/icons";

import { buildAttentionItems, buildHealthTiles, tagColorForTone } from "./monitoringMappers";
import type { MonitorModuleKey, MonitoringQueries, TeacherCatalogSearchDiagnostics } from "./monitoringTypes";

const { Text } = Typography;

type MonitoringOverviewProps = {
  queries: MonitoringQueries;
  draft: string;
  query: string;
  onDraftChange: (value: string) => void;
  onSearch: (value: string) => void;
  onModuleChange: (module: MonitorModuleKey) => void;
  onRefresh: () => void;
  lastUpdatedText: string;
};

export function MonitoringOverview({
  queries,
  draft,
  query,
  onDraftChange,
  onSearch,
  onModuleChange,
  onRefresh,
  lastUpdatedText,
}: MonitoringOverviewProps) {
  const tiles = buildHealthTiles({
    aiConfig: queries.aiConfig.data,
    assistantRuntime: queries.assistantRuntime.data,
    indexDiagnostics: queries.indexDiagnostics.data,
  });
  const attention = buildAttentionItems({
    aiConfig: queries.aiConfig.data,
    assistantRuntime: queries.assistantRuntime.data,
    indexDiagnostics: queries.indexDiagnostics.data,
    searchDiagnostics: queries.searchDiagnostics.data,
  });
  const search = queries.searchDiagnostics.data;

  return (
    <section className="ai-monitor-overview">
      <div className="ai-monitor-overview-head">
        <div>
          <Text className="eyebrow">Overview</Text>
          <h2>系统健康总览</h2>
          <Text type="secondary">最近刷新：{lastUpdatedText}</Text>
        </div>
        <Button icon={<ReloadOutlined />} onClick={onRefresh} loading={queries.aiConfig.isFetching || queries.indexDiagnostics.isFetching || queries.assistantRuntime.isFetching}>
          刷新
        </Button>
      </div>
      <div className="ai-monitor-health-strip">
        {tiles.map((tile) => (
          <button key={`${tile.key}-${tile.label}`} type="button" className={`ai-monitor-health-tile ai-monitor-tone-${tile.tone}`} onClick={() => onModuleChange(tile.key)}>
            <span>{tile.label}</span>
            <strong>{tile.status}</strong>
            <em>{tile.value}</em>
            {tile.detail ? <small>{tile.detail}</small> : null}
          </button>
        ))}
      </div>
      <div className="ai-monitor-overview-grid">
        <section className="ai-monitor-attention-panel">
          <div className="ai-monitor-section-title">
            <h3>需要关注</h3>
            <Tag color={attention.length ? "#b8892f" : "#005826"}>{attention.length ? `${attention.length} 项` : "无异常"}</Tag>
          </div>
          {attention.length ? (
            <div className="ai-monitor-attention-list">
              {attention.map((item) => (
                <button key={item.key} type="button" className={`ai-monitor-attention-item ai-monitor-tone-${item.tone}`} onClick={() => onModuleChange(item.module)}>
                  <span>{item.title}</span>
                  <strong>{item.detail}</strong>
                </button>
              ))}
            </div>
          ) : (
            <div className="ai-monitor-quiet-state">当前没有需要立即处理的监控项。</div>
          )}
        </section>
        <section className="ai-monitor-quick-diagnosis">
          <div className="ai-monitor-section-title">
            <h3>快速检索诊断</h3>
            <Tag color={search?.status === "error" ? "#b42318" : "#005826"}>{search?.backend || "elasticsearch"}</Tag>
          </div>
          <Input.Search
            value={draft}
            onChange={(event) => onDraftChange(event.target.value)}
            onSearch={(value) => onSearch(value.trim() || query)}
            loading={queries.searchDiagnostics.isFetching}
            enterButton={
              <span className="ai-es-search-button">
                <SearchOutlined />
                诊断
              </span>
            }
          />
          <QuickDiagnosisResult search={search} onOpenEs={() => onModuleChange("es")} />
        </section>
      </div>
    </section>
  );
}

function QuickDiagnosisResult({ search, onOpenEs }: { search?: TeacherCatalogSearchDiagnostics; onOpenEs: () => void }) {
  const result = search?.results?.[0];
  if (!result) {
    return <div className="ai-monitor-quiet-state">暂无检索诊断结果。</div>;
  }
  return (
    <button type="button" className="ai-monitor-top-result" onClick={onOpenEs}>
      <span>Top result</span>
      <strong>{result.title}</strong>
      <div className="ai-monitor-tag-list">
        <Tag color="#356f9c">score {Number(result.score || 0).toFixed(2)}</Tag>
        {(result.matched_routes || []).slice(0, 4).map((route) => (
          <Tag key={route} color={tagColorForTone("idle")}>{route}</Tag>
        ))}
      </div>
    </button>
  );
}
