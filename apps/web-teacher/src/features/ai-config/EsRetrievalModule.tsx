import { Alert, Collapse, Input, Tag, Typography } from "antd";
import { SearchOutlined } from "@ant-design/icons";

import { errorMessage, searchTermGroups } from "./monitoringMappers";
import { LocalQueryState, ModuleHeader, TagsList } from "./MonitoringShared";
import type { TeacherCatalogSearchDiagnostics } from "./monitoringTypes";

const { Text } = Typography;

type EsRetrievalModuleProps = {
  draft: string;
  query: string;
  onDraftChange: (value: string) => void;
  onSearch: (value: string) => void;
  data?: TeacherCatalogSearchDiagnostics;
  loading?: boolean;
  fetching?: boolean;
  error?: unknown;
  retry?: () => void;
};

export function EsRetrievalModule({ draft, query, onDraftChange, onSearch, data, loading, fetching, error, retry }: EsRetrievalModuleProps) {
  const routes = data?.query_plan?.routes || [];
  const results = data?.results || [];
  const hasRawDetails = Boolean(data?.query_plan);

  return (
    <section className="ai-monitor-module ai-monitor-es-workbench">
      <ModuleHeader
        eyebrow="Retrieval Explain"
        title="点位召回路诊断"
        description="对象固定为点位；目录、三要素、方程式、同义词和标签共同参与召回。"
        status={data?.backend || "local"}
        tone={data?.status === "error" || data?.error ? "warn" : "good"}
      />
      <div className="ai-monitor-search-row">
        <Input.Search
          value={draft}
          onChange={(event) => onDraftChange(event.target.value)}
          onSearch={(value) => onSearch(value.trim() || query)}
          enterButton={
            <span className="ai-es-search-button">
              <SearchOutlined />
              诊断
            </span>
          }
          loading={fetching}
        />
      </div>
      <LocalQueryState loading={loading} error={error} retry={retry}>
        {data?.error ? <Alert type="warning" showIcon className="ai-monitor-alert" message="检索诊断异常" description={data.error} /> : null}
        <div className="ai-monitor-workbench-grid">
          <section className="ai-monitor-workbench-panel">
            <h3>解析词项</h3>
            <div className="ai-monitor-term-list">
              {searchTermGroups(data).map((group) => (
                <div key={group.key} className="ai-monitor-term-row">
                  <span>{group.label}</span>
                  <TagsList values={group.values} />
                </div>
              ))}
            </div>
          </section>
          <section className="ai-monitor-workbench-panel">
            <h3>召回路数</h3>
            <div className="ai-monitor-route-list">
              {routes.length ? (
                routes.map((route) => (
                  <div key={route.name} className="ai-monitor-route-row">
                    <strong>{route.label || route.name}</strong>
                    <span>{route.name} · boost {route.weight ?? "-"}</span>
                    {route.fields?.length ? <Text type="secondary">{route.fields.join(", ")}</Text> : null}
                  </div>
                ))
              ) : (
                <Text type="secondary">暂无召回路数</Text>
              )}
            </div>
          </section>
          <section className="ai-monitor-workbench-panel ai-monitor-results-panel">
            <h3>排序结果</h3>
            <div className="ai-monitor-result-list">
              {results.length ? (
                results.map((item, index) => (
                  <div key={item.id} className="ai-monitor-result-row">
                    <div className="ai-monitor-result-rank">{index + 1}</div>
                    <div className="ai-monitor-result-main">
                      <strong>{item.title}</strong>
                      <span>{item.subtitle || item.id}</span>
                      <div className="ai-monitor-tag-list">
                        <Tag color="#356f9c">score {Number(item.score || 0).toFixed(2)}</Tag>
                        {(item.matched_routes || []).slice(0, 6).map((route) => (
                          <Tag key={route}>{route}</Tag>
                        ))}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="ai-policy-empty">暂无检索诊断结果</div>
              )}
            </div>
          </section>
        </div>
        {hasRawDetails ? (
          <Collapse
            className="ai-monitor-raw-collapse"
            size="small"
            items={[
              {
                key: "raw",
                label: "原始诊断详情",
                children: <pre className="json-preview">{JSON.stringify(data?.query_plan, null, 2)}</pre>,
              },
            ]}
          />
        ) : null}
      </LocalQueryState>
    </section>
  );
}
