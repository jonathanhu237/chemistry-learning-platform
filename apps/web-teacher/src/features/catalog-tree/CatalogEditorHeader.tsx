import { useEffect, useRef, useState, type ReactNode } from "react";
import { Button, Dropdown, Input, Modal, Popover, Space, Tag, Typography, type InputRef } from "antd";
import { CheckCircleOutlined, DeleteOutlined, EditOutlined, MoreOutlined, StopOutlined } from "@ant-design/icons";
import { Archive, CircleAlert, CircleCheck, CircleX, FileText, FlaskConical, Folder, Link2, ListTree, RefreshCw, TriangleAlert, Video } from "lucide-react";

import type { CatalogNodeDetail } from "../../api/catalogTree";
import { CatalogStatusCompositeWarningIcon } from "./CatalogStatusCompositeWarningIcon";
import {
  catalogStatusLabel,
  catalogNodePrimaryStateClass,
  catalogNodeStatusTooltip,
  catalogHeaderPrimaryAction,
  displayCatalogPointTitle,
  isPointCapable,
  resolveCatalogNodeStatus,
} from "./catalogTreeMappers";
import type { CatalogMutations } from "./catalogTreeHooks";
import { catalogDirectoryPathLabel, catalogPathLabel } from "./catalogPath";

const { Text, Title } = Typography;
const TITLE_MAX_LENGTH = 64;

type SummaryTone = "ok" | "warning" | "error" | "sync" | "ready" | "muted" | "published" | "draft" | "archived";

type SummaryItem = {
  key: string;
  icon: ReactNode;
  label: string;
  value: string;
  note?: string;
  tone?: SummaryTone;
  emphasis?: boolean;
};

type CatalogPointPlacement = NonNullable<CatalogNodeDetail["placements"]>[number];

export type CatalogHeaderDiagnosticsKey = "node-status" | "ai-context" | "advanced";

function pointContentSummary(detail: CatalogNodeDetail): Pick<SummaryItem, "value" | "note" | "tone" | "emphasis"> {
  const status = resolveCatalogNodeStatus(detail);
  const contentStatus = detail.point_content?.content_status;
  const missingLabels = status.core_readiness.missing_field_labels || status.core_readiness.missing_fields || [];

  if (contentStatus === "archived") {
    return { value: "已归档", note: "学习字段", tone: "archived", emphasis: true };
  }
  if (status.core_readiness.content_fields === "missing" || status.primary_state === "needs_content") {
    return {
      value: "待补充",
      note: missingLabels.length ? `缺${missingLabels.join("、")}` : detail.point_content ? "学习字段未完整" : "需手动添加",
      tone: "warning",
      emphasis: true,
    };
  }
  if (status.core_readiness.video === "absent" || status.primary_state === "needs_video") {
    return { value: "已补齐", note: "等待视频", tone: "ready", emphasis: false };
  }
  if (contentStatus === "published") {
    return { value: "已发布", note: "学习字段", tone: "ok", emphasis: false };
  }
  if (contentStatus === "draft") {
    return { value: "待发布", note: "学习字段", tone: "ready", emphasis: false };
  }
  return { value: "待补充", note: "需手动添加", tone: "warning", emphasis: true };
}

function publicationIcon(status?: string | null): ReactNode {
  if (status === "published") return <CircleCheck size={16} />;
  if (status === "draft") return <CircleAlert size={16} />;
  if (status === "archived") return <Archive size={16} />;
  return <TriangleAlert size={16} />;
}

function nodeStatusIcon(state: string): ReactNode {
  if (state === "blocked") return <CircleX size={16} />;
  if (state === "sync_attention") return <RefreshCw size={16} />;
  if (state === "needs_content") return <CatalogStatusCompositeWarningIcon kind="content" size={22} strokeWidth={1.85} />;
  if (state === "needs_video") return <CatalogStatusCompositeWarningIcon kind="video" size={22} strokeWidth={1.85} />;
  if (state === "ready" || state === "draft") return <CircleAlert size={16} />;
  if (state === "archived") return <Archive size={16} />;
  return <CircleCheck size={16} />;
}

function nodeStatusTone(state: string): SummaryTone {
  if (state === "blocked") return "error";
  if (state === "sync_attention") return "sync";
  if (state === "needs_content" || state === "needs_video") return "warning";
  if (state === "ready" || state === "draft") return "ready";
  if (state === "archived") return "archived";
  return "ok";
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
    icon: nodeStatusIcon(status.primary_state),
    label: "节点状态",
    value: status.primary_label || status.primary_state,
    note: status.primary_reason || catalogNodeStatusTooltip(detail),
    tone: nodeStatusTone(status.primary_state),
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
  const contentSummary = pointContentSummary(detail);
  const hasVideo = resolveCatalogNodeStatus(detail).core_readiness.video === "present";
  const relatedCount = detail.related_links.filter((link) => !link.hidden).length;

  return [
    {
      key: "content",
      icon: <FileText size={16} />,
      label: "学习内容",
      ...contentSummary,
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
      note: relatedCount > 0 ? "可串联学习" : "可手动添加",
      tone: relatedCount > 0 ? "muted" : "muted",
    },
  ];
}

function placementDirectoryPath(placement: CatalogPointPlacement): string {
  return catalogDirectoryPathLabel(placement.breadcrumbs || [], placement.chapter_id) || placement.title;
}

function sharedPlacementPopover(detail: CatalogNodeDetail): ReactNode {
  const placements = detail.placements || [];
  const currentNodeId = detail.node.node_id;
  const otherPlacements = placements.filter((placement) => placement.node_id !== currentNodeId);
  if (otherPlacements.length === 0) {
    const count = detail.canonical_point?.active_placement_count ?? detail.node.active_placement_count ?? 0;
    return <span>同一实验共出现在 {count} 个目录位置。</span>;
  }
  return (
    <div className="catalog-shared-placement-popover">
      <Text type="secondary">同一实验还出现在：</Text>
      <ul>
        {otherPlacements.map((placement) => (
          <li key={placement.node_id}>{placementDirectoryPath(placement)}</li>
        ))}
      </ul>
    </div>
  );
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
  onSaveTitle,
}: {
  detail: CatalogNodeDetail;
  mutations: CatalogMutations;
  onPreviewLearningCard?: () => void;
  previewLoading?: boolean;
  onOpenDiagnostics?: (key: CatalogHeaderDiagnosticsKey) => void;
  onOpenContentTask?: () => void;
  onOpenVideoPicker?: () => void;
  onPublishPointContent?: () => void;
  onSaveTitle?: (title: string) => Promise<void> | void;
}) {
  const { node } = detail;
  const pointCapable = isPointCapable(node.node_kind);
  const title = pointCapable ? displayCatalogPointTitle(detail) : node.title;
  const nodeStatus = resolveCatalogNodeStatus(detail);
  const summaryItems = pointCapable ? buildPointSummaryItems(detail) : buildDirectorySummaryItems(detail);
  const nodeStatusItem = nodeStatusSummary(detail);
  const primaryAction = catalogHeaderPrimaryAction(detail);
  const canEditTitle = Boolean(onSaveTitle);
  const activePlacementCount = detail.canonical_point?.active_placement_count ?? node.active_placement_count ?? 0;
  const showSharedExperimentTag = pointCapable && activePlacementCount > 1;
  const [titleEditing, setTitleEditing] = useState(false);
  const [draftTitle, setDraftTitle] = useState(title.slice(0, TITLE_MAX_LENGTH));
  const [titleSaving, setTitleSaving] = useState(false);
  const titleInputRef = useRef<InputRef>(null);
  const titleCommitRef = useRef(false);

  useEffect(() => {
    if (!titleEditing) setDraftTitle(title.slice(0, TITLE_MAX_LENGTH));
  }, [title, titleEditing]);

  useEffect(() => {
    if (!titleEditing) return;
    const timer = window.setTimeout(() => titleInputRef.current?.focus({ cursor: "all" }), 0);
    return () => window.clearTimeout(timer);
  }, [titleEditing]);

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
    if (primaryAction.key === "preview-student") {
      onPreviewLearningCard?.();
      return;
    }
    if (primaryAction.key === "publish-placement") {
      mutations.changeNodeStatus.mutate({ nodeId: node.node_id, action: "publish", includeSubtree: false });
    }
  };

  const startTitleEdit = () => {
    if (!canEditTitle) return;
    setDraftTitle(title.slice(0, TITLE_MAX_LENGTH));
    setTitleEditing(true);
  };

  const cancelTitleEdit = () => {
    setDraftTitle(title.slice(0, TITLE_MAX_LENGTH));
    setTitleEditing(false);
  };

  const commitTitleEdit = async () => {
    if (titleCommitRef.current) return;
    const nextTitle = draftTitle.trim().slice(0, TITLE_MAX_LENGTH);
    if (!nextTitle || nextTitle === title) {
      cancelTitleEdit();
      return;
    }
    titleCommitRef.current = true;
    setTitleSaving(true);
    try {
      await onSaveTitle?.(nextTitle);
      setTitleEditing(false);
    } catch {
      setDraftTitle(nextTitle);
    } finally {
      setTitleSaving(false);
      titleCommitRef.current = false;
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
          <span className={`catalog-editor-kind-icon ${pointCapable ? "is-point" : "is-directory"}`} aria-hidden="true">
            {pointCapable ? <FlaskConical size={20} /> : <Folder size={20} />}
          </span>
          <div className="catalog-editor-title-copy">
            <div className="catalog-editor-title-row">
              {titleEditing ? (
                <Input
                  ref={titleInputRef}
                  className="catalog-editor-title-input"
                  value={draftTitle}
                  maxLength={TITLE_MAX_LENGTH}
                  disabled={titleSaving}
                  aria-label={pointCapable ? "编辑点位名" : "编辑目录标题"}
                  onBlur={() => void commitTitleEdit()}
                  onChange={(event) => setDraftTitle(event.target.value.slice(0, TITLE_MAX_LENGTH))}
                  onPressEnter={() => titleInputRef.current?.blur()}
                  onKeyDown={(event) => {
                    if (event.key === "Escape") {
                      event.preventDefault();
                      cancelTitleEdit();
                    }
                  }}
                />
              ) : (
                <>
                  <Title level={3}>{title}</Title>
                  {canEditTitle ? (
                    <Button
                      className="catalog-editor-title-edit"
                      type="text"
                      size="small"
                      icon={<EditOutlined />}
                      aria-label={pointCapable ? "编辑点位名" : "编辑目录标题"}
                      onClick={startTitleEdit}
                    />
                  ) : null}
                </>
              )}
            </div>
            <div className="catalog-editor-path-line">
              {showSharedExperimentTag ? (
                <Popover content={sharedPlacementPopover(detail)} trigger={["hover", "focus"]} placement="bottomLeft">
                  <Tag className="catalog-shared-experiment-tag" color="green" tabIndex={0}>
                    多目录共享实验
                  </Tag>
                </Popover>
              ) : null}
              <Text type="secondary">
                {pointCapable ? "实验点位" : "目录分组"} · {catalogPathLabel(detail.breadcrumbs, node.chapter_id)}
              </Text>
            </div>
          </div>
        </div>
        <Space wrap className="catalog-editor-header-actions">
          {primaryAction ? (
            <Button
              type={primaryAction.tone === "primary" ? "primary" : "default"}
              danger={primaryAction.tone === "danger"}
              icon={primaryAction.key === "publish-content" || primaryAction.key === "publish-placement" ? <CheckCircleOutlined /> : undefined}
              onClick={handlePrimaryAction}
              loading={
                mutations.changeNodeStatus.isPending ||
                mutations.changePointPublication.isPending ||
                (primaryAction.key === "preview-student" && Boolean(previewLoading))
              }
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
      <div className="catalog-editor-summary-layout" aria-label="节点概览">
        <div className="catalog-editor-summary-grid" aria-label={pointCapable ? "维护概览" : "目录概览"}>
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
        <div
          className={`catalog-editor-summary-item catalog-editor-summary-status ${nodeStatusItem.tone ? `is-${nodeStatusItem.tone}` : ""} ${
            nodeStatusItem.emphasis ? "is-emphasis" : ""
          }`}
        >
          <span className="catalog-editor-summary-icon" aria-hidden="true">
            {nodeStatusItem.icon}
          </span>
          <div>
            <span>{nodeStatusItem.label}</span>
            <strong>{nodeStatusItem.value}</strong>
            {nodeStatusItem.note ? <small>{nodeStatusItem.note}</small> : null}
          </div>
        </div>
      </div>
    </div>
  );
}
