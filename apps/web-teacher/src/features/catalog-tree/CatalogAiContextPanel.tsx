import { Button, Descriptions, Empty, Space, Tag, Typography } from "antd";

import type { CatalogNodeDetail, CatalogPointRagProbe, CatalogStaticEvidenceBinding } from "../../api/catalogTree";
import { QueryState } from "../../components/QueryState";
import { useCatalogPointAiContext, type CatalogMutations } from "./catalogTreeHooks";

const { Text, Title } = Typography;

function statusColor(status?: string | null) {
  if (status === "healthy" || status === "succeeded" || status === "synced" || status === "available_static_fallback" || status === "fresh") return "green";
  if (status === "failed" || status === "unavailable") return "red";
  if (status === "stale" || status === "stale_fallback_evidence") return "orange";
  if (status === "pending" || status === "running") return "gold";
  return "default";
}

function valueList(value: unknown) {
  if (!value || typeof value !== "object") return [];
  return Object.entries(value as Record<string, unknown>).map(([key, item]) => `${displayLabel(key)}：${String(item ?? "-")}`);
}

function previewText(value: unknown) {
  return String(value || "").trim() || "-";
}

function displayLabel(value?: unknown) {
  const raw = String(value || "").trim();
  const labels: Record<string, string> = {
    healthy: "健康",
    succeeded: "成功",
    synced: "已同步",
    available_static_fallback: "静态兜底可用",
    fresh: "最新",
    failed: "失败",
    unavailable: "不可用",
    stale: "已过期",
    stale_fallback_evidence: "静态兜底已过期",
    pending: "等待中",
    running: "运行中",
    missing: "缺失",
    missing_fallback_evidence: "缺少静态兜底证据",
    "no-es-state": "未建立 ES 状态",
    unknown: "未知",
    draft: "草稿",
    published: "已发布",
    archived: "已归档",
    selected: "已选用",
    candidate: "候选",
    rejected: "已拒绝",
    experiment: "实验证据",
    theory: "理论证据",
    supplemental: "补充证据",
    fallback: "兜底证据",
    dynamic_rag: "真实 RAG",
    catalog_node_evidence: "目录点证据",
    static_catalog_node_evidence: "静态目录点证据",
    dynamic_rag_catalog_node_evidence: "真实 RAG 目录点证据",
    hybrid_bge_rag: "混合 BGE RAG",
    generated: "已生成",
    deterministic_catalog_context_query: "目录点上下文兜底查询",
    runtime_health: "运行健康度",
    hybrid_candidates: "混合召回候选",
    reranked_candidates: "重排候选",
    final_evidence: "最终证据",
  };
  return labels[raw] || raw || "-";
}

type StaticEvidenceStage = "not_started" | "searching" | "selected" | "available" | "missed" | "failed" | "stale";

const STATIC_EVIDENCE_PRIMARY_STEPS: Array<{ id: StaticEvidenceStage; title: string; description: string }> = [
  { id: "not_started", title: "未建立", description: "等待刷新任务" },
  { id: "searching", title: "证据搜索中", description: "召回并重排片段" },
  { id: "selected", title: "已选证据", description: "保存候选片段" },
  { id: "available", title: "可作为兜底", description: "补充真实 RAG" },
];

const STATIC_EVIDENCE_BRANCH_STEPS: Array<{ id: StaticEvidenceStage; title: string; description: string }> = [
  { id: "missed", title: "未命中", description: "暂无静态绑定" },
  { id: "failed", title: "搜索失败", description: "需要重试任务" },
  { id: "stale", title: "已过期", description: "等待重新刷新" },
];

function staticEvidenceStage(status?: string | null): StaticEvidenceStage {
  if (status === "pending" || status === "running") return "searching";
  if (status === "selected") return "selected";
  if (status === "available_static_fallback" || status === "fresh" || status === "succeeded" || status === "synced") return "available";
  if (status === "stale" || status === "stale_fallback_evidence") return "stale";
  if (status === "failed" || status === "unavailable") return "failed";
  if (status === "missing" || status === "missing_fallback_evidence") return "missed";
  return "not_started";
}

function staticEvidenceSummary(stage: StaticEvidenceStage, bindingCount: number) {
  if (stage === "searching") return "正在为当前点位搜索可用的静态证据。";
  if (stage === "available") return `已选 ${bindingCount} 条静态证据，可作为真实 RAG 的补充兜底。`;
  if (stage === "selected") return `已选 ${bindingCount} 条候选证据，等待确认可用状态。`;
  if (stage === "stale") return "静态证据已过期，需要刷新后再作为兜底来源。";
  if (stage === "failed") return "最近一次静态证据搜索失败，可重试证据任务。";
  if (stage === "missed") return "当前没有静态兜底证据；真实 RAG 搜索仍可独立运行。";
  return "尚未建立静态证据状态。";
}

function StaticEvidenceLifecycle({ status, bindingCount }: { status?: string | null; bindingCount: number }) {
  const currentStage = staticEvidenceStage(status);
  const renderNode = (step: { id: StaticEvidenceStage; title: string; description: string }) => (
    <div className={`catalog-static-lifecycle-node${currentStage === step.id ? " is-current" : ""}`} data-stage={step.id} key={step.id}>
      <span className="catalog-static-lifecycle-dot" />
      <strong>{step.title}</strong>
      <small>{step.description}</small>
    </div>
  );

  return (
    <div className="catalog-static-lifecycle-card">
      <div className="catalog-static-lifecycle-header">
        <div>
          <strong>静态证据状态流</strong>
          <p>{staticEvidenceSummary(currentStage, bindingCount)}</p>
        </div>
        <Tag color={statusColor(status)}>{displayLabel(status || "missing")}</Tag>
      </div>
      <div className="catalog-static-lifecycle-track">{STATIC_EVIDENCE_PRIMARY_STEPS.map(renderNode)}</div>
      <div className="catalog-static-lifecycle-branches">{STATIC_EVIDENCE_BRANCH_STEPS.map(renderNode)}</div>
    </div>
  );
}

function EvidenceRow({ binding }: { binding: CatalogStaticEvidenceBinding }) {
  return (
    <div className="catalog-ai-evidence-row">
      <div>
        <Text strong copyable>
          {binding.chunk_id}
        </Text>
        <p>{binding.source_title || binding.source_file || binding.document_id || "-"}</p>
        <small>
          {[
            binding.page_number ? `第 ${binding.page_number} 页` : "",
            binding.section_title || "",
            binding.content_type ? `类型 ${displayLabel(binding.content_type)}` : "",
          ]
            .filter(Boolean)
            .join(" / ") || "-"}
        </small>
      </div>
      <Space wrap>
        <Tag>{displayLabel(binding.evidence_role)}</Tag>
        <Tag color={statusColor(binding.selection_status)}>{displayLabel(binding.selection_status)}</Tag>
        <Tag color={statusColor(binding.freshness_status)}>{displayLabel(binding.freshness_status)}</Tag>
      </Space>
      <div className="catalog-ai-score-grid">
        <span>初筛分 {binding.score ?? "-"}</span>
        <span>重排分 {binding.rerank_score ?? "-"}</span>
      </div>
      <Text type="secondary">{binding.text_preview || "-"}</Text>
    </div>
  );
}

function ProbeResult({ probe }: { probe?: CatalogPointRagProbe }) {
  if (!probe) return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="运行一次真实 RAG 搜索后，可查看召回和重排行为。" />;
  return (
    <div className="catalog-ai-probe-result">
      <div className={`catalog-rag-search-result-card${probe.ok ? " is-ok" : " is-blocked"}`}>
        <span className="catalog-rag-search-result-mark" />
        <div>
          <strong>{probe.ok ? "真实 RAG 搜索完成" : `真实 RAG 搜索停在：${displayLabel(probe.failed_stage || "unknown")}`}</strong>
          <small>{probe.ok ? "已从配置的 RAG 管线中选择证据。" : "检查运行状态、索引或证据刷新任务。"}</small>
        </div>
      </div>
      <Descriptions size="small" column={2}>
        <Descriptions.Item label="运行状态">{displayLabel(probe.runtime_health?.status || "-")}</Descriptions.Item>
        <Descriptions.Item label="召回来源">{displayLabel(probe.recall_source || "-")}</Descriptions.Item>
        <Descriptions.Item label="查询状态">{displayLabel(probe.query_strategy?.status || "-")}</Descriptions.Item>
        <Descriptions.Item label="兜底原因">{displayLabel(probe.query_strategy?.fallback_reason || "-")}</Descriptions.Item>
      </Descriptions>
      <div className="catalog-ai-split">
        <section>
          <Title level={5}>生成查询</Title>
          {probe.generated_queries.length ? (
            <ol>
              {probe.generated_queries.map((query) => (
                <li key={query}>{query}</li>
              ))}
            </ol>
          ) : (
            <Text type="secondary">暂无查询变体。</Text>
          )}
        </section>
        <section>
          <Title level={5}>候选数量</Title>
          {valueList(probe.candidate_counts).map((line) => (
            <Tag key={line}>{line}</Tag>
          ))}
        </section>
      </div>
      <section>
        <Title level={5}>最终证据</Title>
        {probe.final_evidence.length ? (
          <div className="catalog-ai-evidence-list">
            {probe.final_evidence.map((item, index) => (
              <div className="catalog-ai-probe-evidence" key={`${item.chunk_id || index}`}>
                <Text strong copyable>
                  {String(item.chunk_id || "-")}
                </Text>
                <Space wrap>
                  <Tag>{displayLabel(item.recall_source || item.source || "-")}</Tag>
                  <Tag>初筛分 {String(item.score ?? "-")}</Tag>
                  <Tag>重排分 {String(item.rerank_score ?? "-")}</Tag>
                </Space>
                <Text type="secondary">{String(item.source_file || item.source_title || "-")}</Text>
                <p>{String(item.text_preview || "")}</p>
              </div>
            ))}
          </div>
        ) : (
          <Text type="secondary">暂无可接地证据。</Text>
        )}
      </section>
    </div>
  );
}

export function CatalogAiContextPanel({ detail, mutations }: { detail: CatalogNodeDetail; mutations: CatalogMutations }) {
  const nodeId = detail.node.node_id;
  const contextQuery = useCatalogPointAiContext(nodeId, detail.node.node_kind === "point");
  const probe = mutations.runRagProbe.data?.node_id === nodeId ? mutations.runRagProbe.data : undefined;
  const jobState = contextQuery.data?.job_state || detail.job_state;
  const evidenceState = jobState?.evidence_state;

  return (
    <section className="catalog-editor-section catalog-ai-context-panel">
      <div className="catalog-panel-title-row">
        <div>
          <Title level={4}>点位检索诊断</Title>
          <Text type="secondary">仅教师可见，用于诊断学生端可见内容、ES 同步状态、静态兜底证据、真实 RAG 搜索和点位上下文。</Text>
        </div>
        <Space wrap>
          <Button
            size="small"
            loading={mutations.triggerPointJob.isPending}
            onClick={() => mutations.triggerPointJob.mutate({ nodeId, action: "rag-refresh" })}
          >
            刷新 RAG 证据
          </Button>
          <Button size="small" loading={mutations.triggerPointJob.isPending} onClick={() => mutations.triggerPointJob.mutate({ nodeId, action: "retry" })}>
            重试失败任务
          </Button>
          <Button size="small" type="primary" loading={mutations.runRagProbe.isPending} onClick={() => mutations.runRagProbe.mutate({ nodeId })}>
            运行真实 RAG 搜索
          </Button>
        </Space>
      </div>
      <QueryState loading={contextQuery.isLoading} error={contextQuery.error} empty={!contextQuery.data}>
        {contextQuery.data ? (
          <>
            <section className="catalog-ai-band">
              <Title level={5}>学生端可见点位内容</Title>
              <Descriptions size="small" column={2} bordered>
                <Descriptions.Item label="节点 ID">{contextQuery.data.node_id}</Descriptions.Item>
                <Descriptions.Item label="canonical 点位">{contextQuery.data.canonical_point_id || "-"}</Descriptions.Item>
                <Descriptions.Item label="目录路径">{contextQuery.data.catalog_path_text || "-"}</Descriptions.Item>
                <Descriptions.Item label="标题">{contextQuery.data.point_title}</Descriptions.Item>
                <Descriptions.Item label="发布状态">{displayLabel(contextQuery.data.publication_state.content_status || "-")}</Descriptions.Item>
                <Descriptions.Item label="现象解释">{previewText(contextQuery.data.student_facing_content.phenomenon_explanation)}</Descriptions.Item>
                <Descriptions.Item label="安全提示">{previewText(contextQuery.data.student_facing_content.safety_note)}</Descriptions.Item>
              </Descriptions>
              <div className="catalog-ai-equations">
                {(contextQuery.data.student_facing_content.reaction_equations || []).length ? (
                  contextQuery.data.student_facing_content.reaction_equations?.map((equation) => (
                    <Tag key={`${equation.row_order}-${equation.raw_text}`}>{equation.canonical_display || equation.raw_text}</Tag>
                  ))
                ) : (
                  <Text type="secondary">{previewText(contextQuery.data.student_facing_content.principle_text)}</Text>
                )}
              </div>
            </section>

            <section className="catalog-ai-band">
              <div className="catalog-panel-title-row">
                <Title level={5}>静态兜底证据</Title>
                <Tag color={statusColor(contextQuery.data.static_evidence.status)}>{displayLabel(contextQuery.data.static_evidence.status)}</Tag>
              </div>
              <StaticEvidenceLifecycle
                status={contextQuery.data.static_evidence.status}
                bindingCount={contextQuery.data.static_evidence.bindings.length}
              />
              {contextQuery.data.static_evidence.bindings.length ? (
                <div className="catalog-ai-evidence-list">
                  {contextQuery.data.static_evidence.bindings.map((binding) => (
                    <EvidenceRow binding={binding} key={`${binding.chunk_id}-${binding.evidence_role}`} />
                  ))}
                </div>
              ) : null}
            </section>

            <section className="catalog-ai-band">
              <div className="catalog-panel-title-row">
                <Title level={5}>真实 RAG 搜索</Title>
                <Tag color={statusColor(String(contextQuery.data.dynamic_rag.runtime_health?.status || ""))}>
                  {displayLabel(contextQuery.data.dynamic_rag.runtime_health?.status || "unknown")}
                </Tag>
              </div>
              <ProbeResult probe={probe} />
            </section>

            <section className="catalog-ai-band">
              <Title level={5}>仅教师可见教学备注</Title>
              <Descriptions size="small" column={1} bordered>
                <Descriptions.Item label="节点备注">{contextQuery.data.teacher_only_notes.node_teacher_note || "-"}</Descriptions.Item>
                <Descriptions.Item label="点位备注">{contextQuery.data.teacher_only_notes.point_teacher_note || "-"}</Descriptions.Item>
              </Descriptions>
            </section>

            <section className="catalog-ai-band">
              <div className="catalog-panel-title-row">
                <Title level={5}>ES 与证据任务</Title>
                <Space>
                  <Tag color={statusColor(jobState?.es_state?.sync_status)}>{displayLabel(jobState?.es_state?.sync_status || "no-es-state")}</Tag>
                  <Tag color={statusColor(evidenceState?.evidence_status)}>{displayLabel(evidenceState?.evidence_status || "missing")}</Tag>
                </Space>
              </div>
              <Descriptions size="small" column={2}>
                <Descriptions.Item label="ES 动作">{displayLabel(jobState?.es_state?.desired_action || "-")}</Descriptions.Item>
                <Descriptions.Item label="ES 错误">{jobState?.es_state?.last_error || "-"}</Descriptions.Item>
                <Descriptions.Item label="证据模式">{displayLabel(evidenceState?.source_mode || "-")}</Descriptions.Item>
                <Descriptions.Item label="证据错误">{evidenceState?.latest_error || "-"}</Descriptions.Item>
              </Descriptions>
            </section>
          </>
        ) : null}
      </QueryState>
    </section>
  );
}
