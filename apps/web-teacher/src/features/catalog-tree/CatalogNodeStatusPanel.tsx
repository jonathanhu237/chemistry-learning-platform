import { Alert, Button, Descriptions, Divider, Space, Spin, Tag, Typography } from "antd";
import type { UseQueryResult } from "@tanstack/react-query";

import type { CatalogNodeDetail, CatalogValidation } from "../../api/catalogTree";
import type { CatalogMutations } from "./catalogTreeHooks";
import {
  catalogNodePrimaryStateLabel,
  catalogNodeStatusTooltip,
  catalogStatusLabel,
  resolveCatalogNodeStatus,
} from "./catalogTreeMappers";

const { Text, Title } = Typography;

function statusTagColor(status?: string | null): string {
  if (!status || status === "idle" || status === "not_applicable") return "default";
  if (["published", "complete", "present", "synced", "available"].includes(status)) return "green";
  if (["blocked", "failed", "unavailable"].includes(status)) return "red";
  if (
    [
      "missing",
      "absent",
      "needs_content",
      "needs_video",
      "sync_attention",
      "pending",
      "running",
      "stale",
      "draft",
      "ready",
    ].includes(status)
  ) {
    return "gold";
  }
  return "default";
}

function valueLabel(value?: string | null): string {
  const labels: Record<string, string> = {
    complete: "完整",
    missing: "缺失",
    present: "有视频",
    absent: "无视频",
    not_applicable: "不适用",
    published: "已发布",
    draft: "草稿",
    archived: "已归档",
    blocked: "异常",
    needs_content: "缺内容",
    needs_video: "缺视频",
    sync_attention: "同步异常",
    ready: "待发布",
    idle: "未开始",
    pending: "待处理",
    running: "处理中",
    synced: "已同步",
    available: "可用",
    stale: "已过期",
    failed: "失败",
    disabled: "已停用",
    unavailable: "不可用",
  };
  return labels[value || ""] || value || "-";
}

function primaryAlertType(primaryState: string): "success" | "info" | "warning" | "error" {
  if (primaryState === "blocked") return "error";
  if (primaryState === "published") return "success";
  if (primaryState === "sync_attention") return "warning";
  return "info";
}

function StatusTag({ value }: { value?: string | null }) {
  return <Tag color={statusTagColor(value)}>{valueLabel(value)}</Tag>;
}

function conditionsForGroup(detail: CatalogNodeDetail, group: string) {
  return resolveCatalogNodeStatus(detail).conditions.filter((condition) => condition.group === group);
}

function ConditionList({ detail, group }: { detail: CatalogNodeDetail; group: string }) {
  const conditions = conditionsForGroup(detail, group).filter((condition) => condition.group !== "advanced");
  if (!conditions.length) return <Text type="secondary">暂无需要处理的问题。</Text>;
  return (
    <div className="catalog-node-status-condition-list">
      {conditions.map((condition) => (
        <div className={`catalog-node-status-condition is-${condition.severity}`} key={condition.key}>
          <strong>{condition.reason}</strong>
          <span>{condition.message}</span>
          {condition.action ? <small>{condition.action}</small> : null}
        </div>
      ))}
    </div>
  );
}

function CoreReadinessSection({ detail }: { detail: CatalogNodeDetail }) {
  const status = resolveCatalogNodeStatus(detail);
  const core = status.core_readiness;
  const counts = core.descendant_status_counts || {};
  const missingFieldLabels = core.missing_field_labels || core.missing_fields || [];
  const isDirectory = detail.node.node_kind === "directory";
  return (
    <section className="catalog-node-status-card">
      <div className="catalog-node-status-card-heading">
        <Title level={5}>核心完整性</Title>
        <StatusTag value={status.primary_state} />
      </div>
      {isDirectory ? (
        <Descriptions size="small" column={2}>
          <Descriptions.Item label="待处理点位">{core.descendant_action_count ?? 0}</Descriptions.Item>
          <Descriptions.Item label="缺内容">{counts.needs_content ?? 0}</Descriptions.Item>
          <Descriptions.Item label="缺视频">{counts.needs_video ?? 0}</Descriptions.Item>
          <Descriptions.Item label="异常">{counts.blocked ?? 0}</Descriptions.Item>
        </Descriptions>
      ) : (
        <Descriptions size="small" column={2}>
          <Descriptions.Item label="学习字段">
            <StatusTag value={core.content_fields} />
          </Descriptions.Item>
          <Descriptions.Item label="实验视频">
            <StatusTag value={core.video} />
          </Descriptions.Item>
          <Descriptions.Item label="缺失字段" span={2}>
            {missingFieldLabels.length ? missingFieldLabels.join("、") : "无"}
          </Descriptions.Item>
        </Descriptions>
      )}
      <ConditionList detail={detail} group="core_readiness" />
    </section>
  );
}

function VisibilitySection({ detail }: { detail: CatalogNodeDetail }) {
  const status = resolveCatalogNodeStatus(detail);
  const visibility = status.visibility;
  return (
    <section className="catalog-node-status-card">
      <div className="catalog-node-status-card-heading">
        <Title level={5}>学生可见性</Title>
        <StatusTag value={visibility.student_available ? "published" : "draft"} />
      </div>
      <Descriptions size="small" column={2}>
        <Descriptions.Item label="目录位置">
          <StatusTag value={visibility.placement} />
        </Descriptions.Item>
        <Descriptions.Item label="多目录共享实验">
          <StatusTag value={visibility.shared_content} />
        </Descriptions.Item>
        <Descriptions.Item label="学生可打开">{visibility.student_available ? "是" : "否"}</Descriptions.Item>
        {detail.node.node_kind === "point" ? (
          <Descriptions.Item label="目录位置 / 共享实验">
            {detail.node.placement_node_id || detail.node.node_id} / {detail.node.canonical_point_id || "-"}
          </Descriptions.Item>
        ) : null}
      </Descriptions>
      <ConditionList detail={detail} group="visibility" />
    </section>
  );
}

function SyncDiagnosticsSection({ detail, mutations }: { detail: CatalogNodeDetail; mutations: CatalogMutations }) {
  const status = resolveCatalogNodeStatus(detail);
  const sync = status.async_consumption;
  const nodeId = detail.node.node_id;
  const jobState = detail.job_state;
  const latestError = jobState?.es_state?.last_error || jobState?.evidence_state?.latest_error || "";
  if (detail.node.node_kind !== "point") {
    return (
      <section className="catalog-node-status-card is-secondary">
        <div className="catalog-node-status-card-heading">
          <Title level={5}>同步诊断</Title>
          <StatusTag value="not_applicable" />
        </div>
        <Text type="secondary">目录不直接消费 ES 或 AI/RAG 证据；相关问题会以目录后代聚合呈现。</Text>
      </section>
    );
  }
  return (
    <section className="catalog-node-status-card is-secondary">
      <div className="catalog-node-status-card-heading">
        <Title level={5}>同步诊断</Title>
        <Space wrap>
          <Button size="small" onClick={() => mutations.triggerPointJob.mutate({ nodeId, action: "es-refresh" })}>
            刷新 ES
          </Button>
          <Button size="small" onClick={() => mutations.triggerPointJob.mutate({ nodeId, action: "rag-refresh" })}>
            刷新 RAG
          </Button>
          <Button size="small" onClick={() => mutations.triggerPointJob.mutate({ nodeId, action: "retry" })}>
            重试失败任务
          </Button>
        </Space>
      </div>
      <Descriptions size="small" column={2}>
        <Descriptions.Item label="搜索 ES">
          <StatusTag value={sync.search_index} />
        </Descriptions.Item>
        <Descriptions.Item label="AI/RAG 证据">
          <StatusTag value={sync.ai_evidence} />
        </Descriptions.Item>
        <Descriptions.Item label="最近 ES 更新">{jobState?.es_state?.updated_at || "-"}</Descriptions.Item>
        <Descriptions.Item label="最近证据更新">{jobState?.evidence_state?.updated_at || "-"}</Descriptions.Item>
        <Descriptions.Item label="最近错误" span={2}>
          {latestError || "-"}
        </Descriptions.Item>
      </Descriptions>
      <ConditionList detail={detail} group="async_consumption" />
    </section>
  );
}

export function CatalogNodeStatusPanel({
  detail,
  validation,
  mutations,
}: {
  detail: CatalogNodeDetail;
  validation: UseQueryResult<CatalogValidation>;
  mutations: CatalogMutations;
}) {
  const status = resolveCatalogNodeStatus(detail);
  const summary = catalogNodeStatusTooltip(detail);
  const primaryLabel = status.primary_label || catalogNodePrimaryStateLabel(status.primary_state);

  return (
    <section className="catalog-editor-section catalog-editor-panel-section">
      <div className="catalog-panel-title-row">
        <div>
          <Title level={4}>节点状态</Title>
          <Text type="secondary">按核心完整性、学生可见性和同步诊断拆开呈现，树上只保留一个主状态。</Text>
        </div>
        {validation.isFetching ? <Spin size="small" /> : null}
      </div>
      <Alert type={primaryAlertType(status.primary_state)} showIcon title={primaryLabel} description={summary} />
      <CoreReadinessSection detail={detail} />
      <VisibilitySection detail={detail} />
      <SyncDiagnosticsSection detail={detail} mutations={mutations} />
      {status.conditions.some((condition) => condition.group === "advanced") ? (
        <>
          <Divider />
          <section className="catalog-node-status-card is-secondary">
            <div className="catalog-node-status-card-heading">
              <Title level={5}>高级提示</Title>
            </div>
            <ConditionList detail={detail} group="advanced" />
          </section>
        </>
      ) : null}
    </section>
  );
}
