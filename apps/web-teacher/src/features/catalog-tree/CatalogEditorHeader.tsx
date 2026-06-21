import { useEffect, useState, type ReactNode } from "react";
import { Button, Dropdown, Input, Modal, Space, Tag, Typography } from "antd";
import { CheckCircleOutlined, DeleteOutlined, EditOutlined, MoreOutlined, StopOutlined } from "@ant-design/icons";
import { AlertTriangle, CircleCheck, CircleDashed, FlaskConical, Folder, Link2, ListTree, Video } from "lucide-react";

import type { CatalogNodeDetail } from "../../api/catalogTree";
import {
  catalogStatusDotClass,
  catalogStatusLabel,
  catalogNodePrimaryStateClass,
  catalogNodeStatusTooltip,
  catalogHeaderPrimaryAction,
  displayCatalogPointTitle,
  isPointCapable,
  resolveCatalogNodeStatus,
} from "./catalogTreeMappers";
import type { CatalogMutations } from "./catalogTreeHooks";

const { Text, Title } = Typography;

type SummaryTone = "ok" | "warning" | "error" | "muted" | "published" | "draft" | "archived";

type SummaryItem = {
  key: string;
  icon: ReactNode;
  label: string;
  value: string;
  note?: string;
  tone?: SummaryTone;
  emphasis?: boolean;
};

export type CatalogHeaderDiagnosticsKey = "node-status" | "ai-context" | "advanced";

function pointContentStatusLabel(status?: string | null): string {
  if (status === "published") return "已发布";
  if (status === "archived") return "已归档";
  if (status === "draft") return "草稿";
  return "待补充";
}

function pointContentTone(status?: string | null): SummaryTone {
  if (status === "published") return "ok";
  if (status === "archived") return "archived";
  if (status === "draft") return "draft";
  return "warning";
}

function publicationIcon(status?: string | null): ReactNode {
  if (status === "published") return <CircleCheck size={16} />;
  if (status === "draft") return <CircleDashed size={16} />;
  return <AlertTriangle size={16} />;
}

function statusNote(status: string): string {
  if (status === "published") return "学生端可见";
  if (status === "archived") return "已从常规目录隐藏";
  return "可继续维护";
}

function nodeStatusSummary(detail: CatalogNodeDetail): SummaryItem {
  const status = resolveCatalogNodeStatus(detail);
  const isError = status.primary_state === "blocked";
  const isAttention = isError || ["needs_content", "needs_video", "sync_attention"].includes(status.primary_state);
  return {
    key: "node-status",
    icon: isAttention ? <AlertTriangle size={16} /> : <CircleCheck size={16} />,
    label: "节点状态",
    value: status.primary_label || status.primary_state,
    note: status.primary_reason || catalogNodeStatusTooltip(detail),
    tone: isError ? "error" : isAttention ? "warning" : status.primary_state === "archived" ? "archived" : status.primary_state === "draft" ? "draft" : "ok",
    emphasis: isAttention,
  };
}

function buildDirectorySummaryItems(detail: CatalogNodeDetail): SummaryItem[] {
  const { node } = detail;
  const directChildren = detail.children.length;
  const pointCount = node.descendant_point_count;
  const structureValue =
    directChildren === pointCount
      ? `${pointCount} 个点位`
      : `${directChildren} 个直接子项 · ${pointCount} 个点位`;

  return [
    {
      key: "structure",
      icon: <ListTree size={16} />,
      label: "目录结构",
      value: structureValue,
      note: pointCount > 0 ? "组织学生学习路径" : "还没有点位内容",
      tone: pointCount > 0 ? "muted" : "warning",
      emphasis: pointCount === 0,
    },
    nodeStatusSummary(detail),
    {
      key: "visibility",
      icon: publicationIcon(node.status),
      label: "学生可见性",
      value: catalogStatusLabel(node.status),
      note: statusNote(node.status),
      tone: node.status,
      emphasis: node.status !== "published" && node.status !== "draft",
    },
  ];
}

function buildPointSummaryItems(detail: CatalogNodeDetail): SummaryItem[] {
  const contentStatus = detail.point_content?.content_status;
  const hasVideo = resolveCatalogNodeStatus(detail).core_readiness.video === "present";
  const relatedCount = detail.related_links.filter((link) => !link.hidden).length;

  return [
    {
      key: "content",
      icon: publicationIcon(contentStatus),
      label: "学习内容",
      value: pointContentStatusLabel(contentStatus),
      note: detail.point_content ? "学习字段" : "待维护",
      tone: pointContentTone(contentStatus),
      emphasis: contentStatus !== "published" && contentStatus !== "draft",
    },
    {
      key: "video",
      icon: <Video size={16} />,
      label: "视频",
      value: hasVideo ? "有视频" : "无视频",
      note: hasVideo ? "已绑定实验视频" : "请绑定实验视频",
      tone: hasVideo ? "ok" : "warning",
      emphasis: !hasVideo,
    },
    {
      key: "related",
      icon: <Link2 size={16} />,
      label: "相关实验",
      value: relatedCount > 0 ? `${relatedCount} 个` : "无",
      note: relatedCount > 0 ? "可串联学习" : "可选补充",
      tone: relatedCount > 0 ? "muted" : "muted",
    },
    nodeStatusSummary(detail),
  ];
}

export function CatalogEditorHeader({
  detail,
  mutations,
  onPreviewLearningCard,
  previewLoading,
  onOpenDiagnostics,
  onOpenContentTask,
  onOpenVideoPicker,
  onPublishPointContent,
  onSavePointTitle,
}: {
  detail: CatalogNodeDetail;
  mutations: CatalogMutations;
  onPreviewLearningCard?: () => void;
  previewLoading?: boolean;
  onOpenDiagnostics?: (key: CatalogHeaderDiagnosticsKey) => void;
  onOpenContentTask?: () => void;
  onOpenVideoPicker?: () => void;
  onPublishPointContent?: () => void;
  onSavePointTitle?: (title: string) => Promise<void> | void;
}) {
  const { node } = detail;
  const pointCapable = isPointCapable(node.node_kind);
  const title = pointCapable ? displayCatalogPointTitle(detail) : node.title;
  const nodeStatus = resolveCatalogNodeStatus(detail);
  const summaryItems = pointCapable ? buildPointSummaryItems(detail) : buildDirectorySummaryItems(detail);
  const primaryAction = catalogHeaderPrimaryAction(detail);
  const activePlacementCount = detail.canonical_point?.active_placement_count ?? node.active_placement_count ?? 0;
  const [titleEditorOpen, setTitleEditorOpen] = useState(false);
  const [draftTitle, setDraftTitle] = useState(title);
  const [titleSaving, setTitleSaving] = useState(false);

  useEffect(() => {
    setDraftTitle(title);
  }, [title]);

  const confirmStatusAction = (action: "unpublish" | "archive") => {
    Modal.confirm({
      title: action === "unpublish" ? "取消发布该节点？" : "归档该节点？",
      content: action === "unpublish" ? "学生端将暂时不可见，可稍后重新发布。" : "节点将从常规目录隐藏，必要时可恢复。",
      okText: action === "unpublish" ? "取消发布" : "归档",
      okButtonProps: { danger: action === "archive" },
      cancelText: "再想想",
      onOk: () => mutations.changeNodeStatus.mutate({ nodeId: node.node_id, action }),
    });
  };

  const handlePrimaryAction = () => {
    if (!primaryAction) return;
    if (primaryAction.key === "restore") {
      mutations.changeNodeStatus.mutate({ nodeId: node.node_id, action: "restore" });
      return;
    }
    if (primaryAction.key === "view-issues" || primaryAction.key === "view-sync") {
      onOpenDiagnostics?.("node-status");
      return;
    }
    if (primaryAction.key === "edit-content") {
      onOpenContentTask?.();
      return;
    }
    if (primaryAction.key === "publish-content") {
      onPublishPointContent?.();
      return;
    }
    if (primaryAction.key === "bind-video") {
      onOpenVideoPicker?.();
      return;
    }
    if (primaryAction.key === "publish-placement") {
      mutations.changeNodeStatus.mutate({ nodeId: node.node_id, action: "publish", includeSubtree: false });
    }
  };

  const handleSaveTitle = async () => {
    const nextTitle = draftTitle.trim();
    if (!nextTitle || nextTitle === title) {
      setTitleEditorOpen(false);
      return;
    }
    setTitleSaving(true);
    try {
      await onSavePointTitle?.(nextTitle);
      setTitleEditorOpen(false);
    } finally {
      setTitleSaving(false);
    }
  };

  const moreItems = [
    ...(pointCapable ? [{ key: "preview", label: "预览学生端", disabled: previewLoading }] : []),
    { key: "node-status", label: "节点状态" },
    ...(pointCapable ? [{ key: "ai-context", label: "点位检索诊断" }] : []),
    { key: "advanced", label: "高级调试" },
    ...(node.status !== "archived" ? [{ type: "divider" as const }] : []),
    ...(node.status === "published" ? [{ key: "unpublish", label: "取消发布", icon: <StopOutlined /> }] : []),
    ...(node.status !== "archived" ? [{ key: "archive", label: "归档节点", icon: <DeleteOutlined />, danger: true }] : []),
  ];

  return (
    <div className="catalog-editor-header">
      <div className="catalog-editor-summary-top">
        <div className="catalog-editor-title-block">
          <span
            className={`catalog-editor-title-status ${catalogNodePrimaryStateClass(nodeStatus.primary_state) || catalogStatusDotClass(node.status)}`}
            aria-hidden="true"
          />
          <span className={`catalog-editor-kind-icon ${pointCapable ? "is-point" : "is-directory"}`} aria-hidden="true">
            {pointCapable ? <FlaskConical size={20} /> : <Folder size={20} />}
          </span>
          <div className="catalog-editor-title-copy">
            <div className="catalog-editor-title-row">
              <Title level={3}>{title}</Title>
              {pointCapable ? (
                <Button
                  className="catalog-editor-title-edit"
                  type="text"
                  size="small"
                  icon={<EditOutlined />}
                  aria-label="编辑点位名"
                  onClick={() => setTitleEditorOpen(true)}
                />
              ) : null}
            </div>
            <Text type="secondary">
              {pointCapable ? "实验点位" : "目录分组"} · {detail.breadcrumbs.map((item) => item.title).join(" / ")}
            </Text>
            {pointCapable ? (
              <div className="catalog-editor-identity-note">
                <Tag color="green">多目录共享实验</Tag>
                <span>{activePlacementCount > 1 ? `已复用到 ${activePlacementCount} 个目录位置` : "当前点位内容、视频和相关实验属于同一个共享实验"}</span>
              </div>
            ) : null}
          </div>
        </div>
        <Space wrap className="catalog-editor-header-actions">
          {primaryAction ? (
            <Button
              type={primaryAction.tone === "primary" ? "primary" : "default"}
              danger={primaryAction.tone === "danger"}
              icon={primaryAction.key === "publish-content" || primaryAction.key === "publish-placement" ? <CheckCircleOutlined /> : undefined}
              onClick={handlePrimaryAction}
              loading={mutations.changeNodeStatus.isPending || mutations.changePointPublication.isPending}
            >
              {primaryAction.label}
            </Button>
          ) : (
            <span className={`catalog-editor-state-pill ${catalogNodePrimaryStateClass(nodeStatus.primary_state)}`}>
              {nodeStatus.primary_label || catalogStatusLabel(node.status)}
            </span>
          )}
          <Dropdown
            trigger={["click"]}
            menu={{
              items: moreItems,
              onClick: ({ key }) => {
                if (key === "preview") {
                  onPreviewLearningCard?.();
                  return;
                }
                if (key === "unpublish" || key === "archive") {
                  confirmStatusAction(key);
                  return;
                }
                onOpenDiagnostics?.(key as CatalogHeaderDiagnosticsKey);
              },
            }}
          >
            <Button icon={<MoreOutlined />}>更多</Button>
          </Dropdown>
        </Space>
      </div>
      <Modal
        title="编辑点位名"
        open={titleEditorOpen}
        okText="保存"
        confirmLoading={titleSaving}
        onOk={handleSaveTitle}
        onCancel={() => setTitleEditorOpen(false)}
        destroyOnHidden
      >
        <Input value={draftTitle} onChange={(event) => setDraftTitle(event.target.value)} placeholder="请输入点位名" autoFocus />
      </Modal>
      <div className="catalog-editor-summary-grid" aria-label="节点概览">
        {summaryItems.map((item) => (
          <div className={`catalog-editor-summary-item ${item.tone ? `is-${item.tone}` : ""} ${item.emphasis ? "is-emphasis" : ""}`} key={item.key}>
            <span className="catalog-editor-summary-icon" aria-hidden="true">
              {item.icon}
            </span>
            <div>
              <span>{item.label}</span>
              <strong>{item.value}</strong>
              {item.note ? <small>{item.note}</small> : null}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
