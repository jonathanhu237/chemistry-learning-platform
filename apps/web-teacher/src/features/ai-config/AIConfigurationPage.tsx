import { useMemo, useState } from "react";
import dayjs from "dayjs";

import { PageTitle } from "../../components/PageTitle";
import { QueryState } from "../../components/QueryState";
import { DictionarySyncModule } from "./DictionarySyncModule";
import { EsRetrievalModule } from "./EsRetrievalModule";
import { GuardrailModule } from "./GuardrailModule";
import { MonitoringModuleTabs } from "./MonitoringModuleTabs";
import { MonitoringOverview } from "./MonitoringOverview";
import { OpenAIMonitoringModule } from "./OpenAIMonitoringModule";
import { RagMonitoringModule } from "./RagMonitoringModule";
import { UsageTrendModule } from "./UsageTrendModule";
import { useMonitoringData } from "./useMonitoringData";
import type { MonitorModuleKey, UsageRange } from "./monitoringTypes";
import "./ai-config.css";

const defaultDiagnosticQuery = "H2O2 KMnO4 酸性";

export function AIConfigurationPage() {
  const [activeModule, setActiveModule] = useState<MonitorModuleKey>("overview");
  const [usageRange, setUsageRange] = useState<UsageRange>("7d");
  const [retrievalDraft, setRetrievalDraft] = useState(defaultDiagnosticQuery);
  const [retrievalQuery, setRetrievalQuery] = useState(defaultDiagnosticQuery);
  const queries = useMonitoringData(retrievalQuery);

  const lastUpdatedText = useMemo(() => {
    const updatedAt = Math.max(
      queries.aiConfig.dataUpdatedAt || 0,
      queries.assistantRuntime.dataUpdatedAt || 0,
      queries.indexDiagnostics.dataUpdatedAt || 0,
      queries.searchDiagnostics.dataUpdatedAt || 0,
    );
    return updatedAt ? dayjs(updatedAt).format("YYYY-MM-DD HH:mm:ss") : "尚未刷新";
  }, [
    queries.aiConfig.dataUpdatedAt,
    queries.assistantRuntime.dataUpdatedAt,
    queries.indexDiagnostics.dataUpdatedAt,
    queries.searchDiagnostics.dataUpdatedAt,
  ]);

  const refreshAll = () => {
    void queries.aiConfig.refetch();
    void queries.assistantRuntime.refetch();
    void queries.indexDiagnostics.refetch();
    void queries.searchDiagnostics.refetch();
  };

  const runDiagnostic = (value: string) => {
    const nextQuery = value.trim() || retrievalQuery;
    setRetrievalDraft(nextQuery);
    setRetrievalQuery(nextQuery);
  };

  return (
    <div className="ai-monitor-page">
      <PageTitle
        title="AI/RAG/ES 监控"
        description="监控 OpenAI API、RAG 服务、ES 点位召回、化学词典与 outbox 同步状态；模型、Base URL、密钥和学生 AI 能力开关在系统设置维护。"
      />
      <QueryState loading={queries.aiConfig.isLoading} error={queries.aiConfig.error}>
        <div className="ai-monitor-console">
          <MonitoringModuleTabs activeKey={activeModule} onChange={setActiveModule} />
          {activeModule === "overview" ? (
            <MonitoringOverview
              queries={queries}
              draft={retrievalDraft}
              query={retrievalQuery}
              onDraftChange={setRetrievalDraft}
              onSearch={runDiagnostic}
              onModuleChange={setActiveModule}
              onRefresh={refreshAll}
              lastUpdatedText={lastUpdatedText}
            />
          ) : null}
          {activeModule === "openai" ? (
            <OpenAIMonitoringModule
              data={queries.aiConfig.data}
              loading={queries.aiConfig.isLoading}
              error={queries.aiConfig.error}
              retry={() => void queries.aiConfig.refetch()}
            />
          ) : null}
          {activeModule === "rag" ? (
            <RagMonitoringModule
              aiConfig={queries.aiConfig.data}
              runtime={queries.assistantRuntime.data}
              loading={queries.assistantRuntime.isLoading}
              error={queries.assistantRuntime.error}
              retry={() => void queries.assistantRuntime.refetch()}
            />
          ) : null}
          {activeModule === "es" ? (
            <EsRetrievalModule
              draft={retrievalDraft}
              query={retrievalQuery}
              onDraftChange={setRetrievalDraft}
              onSearch={runDiagnostic}
              data={queries.searchDiagnostics.data}
              loading={queries.searchDiagnostics.isLoading}
              fetching={queries.searchDiagnostics.isFetching}
              error={queries.searchDiagnostics.error}
              retry={() => void queries.searchDiagnostics.refetch()}
            />
          ) : null}
          {activeModule === "dictionary" ? (
            <DictionarySyncModule
              data={queries.indexDiagnostics.data}
              loading={queries.indexDiagnostics.isLoading}
              error={queries.indexDiagnostics.error}
              retry={() => void queries.indexDiagnostics.refetch()}
            />
          ) : null}
          {activeModule === "guardrail" ? <GuardrailModule policy={queries.aiConfig.data?.student_ai_policy} /> : null}
          {activeModule === "trends" ? (
            <UsageTrendModule status={queries.aiConfig.data?.status} range={usageRange} onRangeChange={setUsageRange} />
          ) : null}
        </div>
      </QueryState>
    </div>
  );
}
