import { Alert, Button, Descriptions, Input, InputNumber, Space, Tag, Typography } from "antd";

import type { CatalogNodeCard, CatalogNodeDetail } from "../../api/catalogTree";
import type { CatalogMutations } from "./catalogTreeHooks";
import { buildMovePayload, hasDivergentPointTitle } from "./catalogTreeMappers";

const { Text, Title } = Typography;

function prettyJson(value: unknown) {
  return JSON.stringify(value || {}, null, 2);
}

function syncTagColor(status?: string | null) {
  if (status === "synced" || status === "succeeded") return "green";
  if (status === "failed" || status === "unavailable") return "red";
  if (status === "stale") return "orange";
  if (status === "pending" || status === "running") return "gold";
  return "default";
}

function displayLabel(value?: string | null) {
  if (!value) return "-";
  const labels: Record<string, string> = {
    synced: "已同步",
    succeeded: "成功",
    failed: "失败",
    unavailable: "不可用",
    stale: "已过期",
    pending: "等待中",
    running: "运行中",
    missing_fallback_evidence: "缺少静态兜底证据",
    available_static_fallback: "静态兜底可用",
    stale_fallback_evidence: "静态兜底已过期",
    fresh: "最新",
    es_refresh: "刷新 ES",
    "es-refresh": "刷新 ES",
    es_delete: "删除 ES",
    "es-delete": "删除 ES",
    rag_refresh: "刷新 RAG 证据",
    "rag-refresh": "刷新 RAG 证据",
    retry: "重试",
    user: "用户触发",
    system: "系统触发",
    seed: "种子数据",
    static_catalog_node_evidence: "静态目录点证据",
    dynamic_rag_catalog_node_evidence: "动态 RAG 目录点证据",
    catalog_node_evidence: "目录点证据",
    hybrid_bge_rag: "混合 BGE RAG",
    runtime_health: "运行健康度",
    hybrid_candidates: "混合召回候选",
    reranked_candidates: "重排候选",
    deterministic_catalog_context_query: "目录点上下文兜底查询",
  };
  return labels[value] || value.replace(/_/g, " ");
}

export function CatalogAdvancedPanel({
  detail,
  siblings,
  moveParentId,
  setMoveParentId,
  moveDisplayOrder,
  setMoveDisplayOrder,
  mutations,
}: {
  detail: CatalogNodeDetail;
  siblings: CatalogNodeCard[];
  moveParentId: string;
  setMoveParentId: (value: string) => void;
  moveDisplayOrder: number | null;
  setMoveDisplayOrder: (value: number | null) => void;
  mutations: CatalogMutations;
}) {
  const { node } = detail;
  const divergentTitle = hasDivergentPointTitle(detail);
  const pointJobState = detail.job_state;
  const evidenceState = pointJobState?.evidence_state;
  const jobActionLoading = mutations.triggerPointJob.isPending;
  const canRunPointJobs = node.node_kind === "point";

  return (
    <section className="catalog-editor-section catalog-editor-panel-section">
      <div>
        <Title level={4}>高级</Title>
        <Text type="secondary">节点、搜索索引和证据任务</Text>
      </div>
      <Descriptions size="small" column={2} bordered>
        {node.node_kind === "point" ? (
          <>
            <Descriptions.Item label="位置节点">{node.placement_node_id || node.node_id}</Descriptions.Item>
            <Descriptions.Item label="多目录共享实验">{node.canonical_point_id || "-"}</Descriptions.Item>
            <Descriptions.Item label="共享目录数">{detail.canonical_point?.active_placement_count ?? node.active_placement_count ?? 0}</Descriptions.Item>
            <Descriptions.Item label="共享实验状态">{displayLabel(detail.canonical_point?.status || node.canonical_point_status)}</Descriptions.Item>
          </>
        ) : null}
        <Descriptions.Item label="节点 ID">{node.node_id}</Descriptions.Item>
        <Descriptions.Item label="父节点">{node.parent_id || "根节点"}</Descriptions.Item>
        <Descriptions.Item label="显示顺序">{node.display_order}</Descriptions.Item>
        <Descriptions.Item label="同级节点">{siblings.length}</Descriptions.Item>
      </Descriptions>
      {divergentTitle ? (
        <Alert
          type="warning"
          showIcon
          title="点位名称与节点标题不一致"
          description="内容自动保存时会以点位名称同步节点标题。"
        />
      ) : null}
      <div className="catalog-form-grid">
        <Input value={moveParentId} onChange={(event) => setMoveParentId(event.target.value)} placeholder="父节点 ID，留空为章根目录" />
        <InputNumber value={moveDisplayOrder ?? undefined} min={1} className="full" onChange={(value) => setMoveDisplayOrder(value ?? null)} placeholder="显示顺序" />
      </div>
      <Space wrap>
        <Button
          onClick={() => mutations.moveNode.mutate({ nodeId: node.node_id, payload: buildMovePayload(moveParentId, moveDisplayOrder) })}
          loading={mutations.moveNode.isPending}
        >
          移动节点
        </Button>
        <Button onClick={() => void navigator.clipboard?.writeText(node.node_id)}>复制 Node ID</Button>
      </Space>
      <div className="catalog-index-diagnostics">
        <div className="catalog-panel-title-row">
          <Title level={5}>搜索与证据任务</Title>
          <Space size={6} wrap>
            {node.node_kind === "point" ? <Tag color="cyan">placement: {node.placement_node_id || node.node_id}</Tag> : null}
            {node.node_kind === "point" ? <Tag color="blue">canonical: {node.canonical_point_id || "-"}</Tag> : null}
            {detail.index_state ? <Tag color={syncTagColor(detail.index_state.sync_status)}>{displayLabel(detail.index_state.sync_status)}</Tag> : <Tag>未入队</Tag>}
          </Space>
        </div>
        <Space wrap className="catalog-job-actions">
          <Button
            size="small"
            disabled={!canRunPointJobs}
            loading={jobActionLoading}
            onClick={() => mutations.triggerPointJob.mutate({ nodeId: node.node_id, action: "es-refresh" })}
          >
            刷新 ES
          </Button>
          <Button
            size="small"
            disabled={!canRunPointJobs}
            loading={jobActionLoading}
            onClick={() => mutations.triggerPointJob.mutate({ nodeId: node.node_id, action: "es-delete" })}
          >
            删除 ES
          </Button>
          <Button
            size="small"
            disabled={!canRunPointJobs}
            loading={jobActionLoading}
            onClick={() => mutations.triggerPointJob.mutate({ nodeId: node.node_id, action: "rag-refresh" })}
          >
            刷新 RAG 证据
          </Button>
          <Button
            size="small"
            disabled={!canRunPointJobs}
            loading={jobActionLoading}
            onClick={() => mutations.triggerPointJob.mutate({ nodeId: node.node_id, action: "retry" })}
          >
            重试
          </Button>
        </Space>
        {detail.search_preview ? (
          <pre className="catalog-search-preview">{prettyJson(detail.search_preview)}</pre>
        ) : (
          <Alert type="info" showIcon title="当前节点没有可预览的学生搜索文档" />
        )}
        <Descriptions size="small" column={2}>
          <Descriptions.Item label="期望动作">{detail.index_state?.desired_action || "-"}</Descriptions.Item>
          <Descriptions.Item label="尝试次数">{detail.index_state?.attempts ?? "-"}</Descriptions.Item>
          <Descriptions.Item label="最近索引">{detail.index_state?.indexed_at || "-"}</Descriptions.Item>
          <Descriptions.Item label="错误">{detail.index_state?.last_error || "-"}</Descriptions.Item>
        </Descriptions>
        <Descriptions size="small" column={2} className="catalog-job-state">
          <Descriptions.Item label="证据状态">
            {evidenceState ? <Tag color={syncTagColor(evidenceState.evidence_status)}>{displayLabel(evidenceState.evidence_status)}</Tag> : "-"}
          </Descriptions.Item>
          <Descriptions.Item label="证据模式">{displayLabel(evidenceState?.source_mode)}</Descriptions.Item>
          <Descriptions.Item label="证据块数">{evidenceState?.selected_chunk_ids?.length ?? "-"}</Descriptions.Item>
          <Descriptions.Item label="最近刷新">{evidenceState?.refreshed_at || evidenceState?.updated_at || "-"}</Descriptions.Item>
          <Descriptions.Item label="stale 原因">{evidenceState?.stale_reason || "-"}</Descriptions.Item>
          <Descriptions.Item label="证据错误">{evidenceState?.latest_error || "-"}</Descriptions.Item>
        </Descriptions>
        {pointJobState?.recent_jobs?.length ? (
          <div className="catalog-job-list">
            {pointJobState.recent_jobs.slice(0, 5).map((job) => (
              <div className="catalog-job-row" key={job.id}>
                <span>{displayLabel(job.job_type)}</span>
                <Tag color={syncTagColor(job.status)}>{displayLabel(job.status)}</Tag>
                <Text type="secondary">{displayLabel(job.trigger_source)}</Text>
                <Text type="secondary">{job.updated_at || job.created_at || "-"}</Text>
              </div>
            ))}
          </div>
        ) : null}
      </div>
    </section>
  );
}
