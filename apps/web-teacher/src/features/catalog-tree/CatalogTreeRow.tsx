import { useEffect, useState, type CSSProperties, type KeyboardEvent, type MouseEvent, type ReactNode } from "react";
import { Button, Dropdown, Tooltip, Typography, type MenuProps } from "antd";
import type { CursorProps, DragPreviewProps, NodeRendererProps } from "react-arborist";
import {
  Archive,
  Ban,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  CircleAlert,
  Clipboard,
  Copy,
  Folder,
  FolderOpen,
  FlaskConical,
  MoreHorizontal,
  MoveDown,
  MoveUp,
  Plus,
  RotateCcw,
} from "lucide-react";

import type { CatalogNodeCard } from "../../api/catalogTree";
import type { CatalogArboristNode } from "./catalogTreeData";
import { catalogNodeKindLabel, catalogStatusDotClass, catalogStatusLabel } from "./catalogTreeMappers";

const { Text } = Typography;

export type CatalogTreeRowAction =
  | "add-directory"
  | "add-point"
  | "archive"
  | "restore"
  | "publish"
  | "unpublish"
  | "copy-node"
  | "copy-directory"
  | "copy-point"
  | "move-before"
  | "move-after";

export type CatalogTreeActionHandler = (node: CatalogNodeCard, action: CatalogTreeRowAction) => void;
export type CatalogTreeLoadRequester = (nodeId: string) => void;
export type CatalogTreeDragPreviewNodeGetter = (nodeId: string) => CatalogArboristNode | undefined;

function rowIcon(kind: CatalogNodeCard["node_kind"], open: boolean): ReactNode {
  if (kind === "point") return <FlaskConical size={19} strokeWidth={1.9} />;
  return open ? <FolderOpen size={20} strokeWidth={1.85} /> : <Folder size={20} strokeWidth={1.85} />;
}

function pointStatusIcon(status: CatalogNodeCard["status"], hasWarnings: boolean): ReactNode {
  if (hasWarnings || status === "draft") return <CircleAlert size={16} strokeWidth={1.9} />;
  if (status === "archived") return <Archive size={16} strokeWidth={1.9} />;
  return <CheckCircle2 size={16} strokeWidth={1.9} />;
}

function pointStatusClass(status: CatalogNodeCard["status"], hasWarnings: boolean): string {
  if (hasWarnings || status === "draft") return "is-warning";
  if (status === "archived") return "is-archived";
  return "is-published";
}

function actionIcon(action: CatalogTreeRowAction): ReactNode {
  const icons: Record<CatalogTreeRowAction, ReactNode> = {
    "add-directory": <Folder size={14} />,
    "add-point": <FlaskConical size={14} />,
    archive: <Archive size={14} />,
    restore: <RotateCcw size={14} />,
    publish: <CheckCircle2 size={14} />,
    unpublish: <Ban size={14} />,
    "copy-node": <Copy size={14} />,
    "copy-directory": <Copy size={14} />,
    "copy-point": <Copy size={14} />,
    "move-before": <MoveUp size={14} />,
    "move-after": <MoveDown size={14} />,
  };
  return icons[action];
}

function buildMenuItems(node: CatalogNodeCard): MenuProps["items"] {
  const statusAction = node.status === "published" ? "unpublish" : "publish";
  return [
    node.node_kind === "directory"
      ? { key: "add-directory", icon: actionIcon("add-directory"), label: "新建子目录" }
      : null,
    node.node_kind === "directory" ? { key: "add-point", icon: actionIcon("add-point"), label: "新建子点位" } : null,
    node.node_kind === "directory" ? { type: "divider" } : null,
    { key: "move-before", icon: actionIcon("move-before"), label: "上移一位" },
    { key: "move-after", icon: actionIcon("move-after"), label: "下移一位" },
    { type: "divider" },
    {
      key: "copy-node",
      icon: actionIcon("copy-node"),
      label: node.node_kind === "directory" ? "复制当前目录" : "复制当前实验",
    },
    node.status === "archived"
      ? { key: "restore", icon: actionIcon("restore"), label: "恢复节点" }
      : {
          key: statusAction,
          icon: actionIcon(statusAction),
          label: statusAction === "publish" ? "发布节点" : "取消发布",
        },
    node.status !== "archived" ? { key: "archive", danger: true, icon: actionIcon("archive"), label: "归档节点" } : null,
  ].filter(Boolean) as MenuProps["items"];
}

type CatalogTreeGuide = {
  current: boolean;
  continuing: boolean;
  first: boolean;
  only: boolean;
  terminal: boolean;
};

type CatalogTreeNodeApi = NodeRendererProps<CatalogArboristNode>["node"];

function buildCatalogTreeGuides(node: CatalogTreeNodeApi): CatalogTreeGuide[] {
  const level = Math.max(0, node.level);
  if (level === 0) return [];

  const guides: CatalogTreeGuide[] = Array.from({ length: level }, () => ({
    current: false,
    continuing: true,
    first: false,
    only: false,
    terminal: false,
  }));
  const currentIndex = level - 1;
  const currentContinues = Boolean(node.nextSibling);
  const currentIsFirst = node.childIndex === 0;
  guides[currentIndex] = {
    current: true,
    continuing: currentContinues,
    first: currentIsFirst,
    only: currentIsFirst && !currentContinues,
    terminal: !currentContinues,
  };

  let ancestor = node.parent;
  for (let index = currentIndex - 1; index >= 0; index -= 1) {
    if (ancestor && !ancestor.isRoot) {
      guides[index].continuing = Boolean(ancestor.nextSibling);
      ancestor = ancestor.parent;
    }
  }
  return guides;
}

function CatalogTreeGuides({ node }: { node: CatalogTreeNodeApi }) {
  const guides = buildCatalogTreeGuides(node);
  return (
    <span className="catalog-sidebar-guides" aria-hidden="true">
      {guides.map((guide, index) => (
        <span
          className={[
            "catalog-sidebar-guide",
            guide.current ? "is-current" : "",
            guide.continuing ? "is-continuing" : "",
            guide.first ? "is-first" : "",
            guide.only ? "is-only" : "",
            guide.terminal ? "is-terminal" : "",
          ]
            .filter(Boolean)
            .join(" ")}
          key={index}
        />
      ))}
    </span>
  );
}

export function CatalogTreeRow({
  node,
  style,
  tree,
  dragHandle,
  onAction,
  onRequestLoad,
}: NodeRendererProps<CatalogArboristNode> & {
  onAction: CatalogTreeActionHandler;
  onRequestLoad?: CatalogTreeLoadRequester;
}) {
  const catalogNode = node.data.catalogNode;
  const hasWarnings = Boolean(catalogNode.validation?.errors?.length || catalogNode.validation?.warnings?.length);
  const warningText = [...(catalogNode.validation?.errors || []), ...(catalogNode.validation?.warnings || [])].join(" / ");
  const statusLabel = catalogStatusLabel(catalogNode.status);
  const pointStatusLabel = hasWarnings ? `${statusLabel}，有校验提示` : statusLabel;
  const [isPointerDragHover, setIsPointerDragHover] = useState(false);
  const dragNodes = Array.isArray((tree as { dragNodes?: unknown }).dragNodes) ? tree.dragNodes : [];
  const canReceiveDirectoryHover =
    catalogNode.node_kind === "directory" &&
    dragNodes.length > 0 &&
    dragNodes.every(
      (dragNode) =>
        dragNode.id !== node.id &&
        !dragNode.isAncestorOf(node) &&
        dragNode.data.catalogNode.chapter_id === catalogNode.chapter_id,
    );
  const isDirectoryDropHover = node.willReceiveDrop || (isPointerDragHover && canReceiveDirectoryHover);
  const directoryPointCount =
    catalogNode.node_kind === "directory" && catalogNode.descendant_point_count > 0 ? String(catalogNode.descendant_point_count) : null;
  const menuItems = buildMenuItems(catalogNode);
  const shouldAutoExpandDropTarget = isDirectoryDropHover && node.isInternal && !node.isOpen;

  useEffect(() => {
    if (!shouldAutoExpandDropTarget) return;
    const timer = window.setTimeout(() => {
      node.open();
      onRequestLoad?.(catalogNode.node_id);
    }, 500);
    return () => window.clearTimeout(timer);
  }, [catalogNode.node_id, isDirectoryDropHover, node.isInternal, node.isOpen, node.willReceiveDrop, onRequestLoad, shouldAutoExpandDropTarget]);

  const toggleDirectory = (event: MouseEvent<HTMLButtonElement>) => {
    event.stopPropagation();
    if (node.isInternal) node.toggle();
  };

  const activateRow = (event: MouseEvent<HTMLElement> | KeyboardEvent<HTMLElement>) => {
    event.stopPropagation();
    node.handleClick(event as MouseEvent);
    if (node.isInternal) node.toggle();
  };

  const handleRowKeyDown = (event: KeyboardEvent<HTMLDivElement>) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    activateRow(event);
  };

  return (
    <div
      ref={dragHandle}
      className={[
        "catalog-sidebar-item",
        `kind-${catalogNode.node_kind}`,
        node.level > 0 ? "is-nested" : "",
        node.isSelected ? "is-selected" : "",
        node.isOpen ? "is-open" : "",
        node.level > 0 && !node.nextSibling ? "is-last-sibling" : "",
        node.isDragging ? "is-dragging" : "",
        isDirectoryDropHover ? "will-receive-drop" : "",
      ]
        .filter(Boolean)
        .join(" ")}
      title={catalogNode.title}
      style={
        {
          ...style,
          "--catalog-elbow-left": `${13 + Math.max(0, node.level - 1) * 22}px`,
          "--catalog-elbow-width": "10px",
        } as CSSProperties & Record<string, string>
      }
      onMouseEnter={() => setIsPointerDragHover(true)}
      onMouseLeave={() => setIsPointerDragHover(false)}
      onDragEnter={() => setIsPointerDragHover(true)}
      onDragLeave={() => setIsPointerDragHover(false)}
    >
      <CatalogTreeGuides node={node} />
      <div
        role="button"
        tabIndex={0}
        className="catalog-sidebar-row"
        onClick={activateRow}
        onKeyDown={handleRowKeyDown}
      >
        <span className="catalog-sidebar-switcher-wrap">
          {node.isInternal ? (
            <span className="catalog-sidebar-switcher" role="button" tabIndex={-1} onClick={(event) => event.stopPropagation()}>
              <Button
                type="text"
                size="small"
                aria-label={node.isOpen ? "折叠目录" : "展开目录"}
                icon={node.isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                onClick={toggleDirectory}
              />
            </span>
          ) : (
            <span className="catalog-sidebar-switcher-spacer" aria-hidden="true" />
          )}
        </span>
        <span className="catalog-sidebar-icon" aria-hidden="true">
          {rowIcon(catalogNode.node_kind, node.isOpen)}
        </span>
        <span className="catalog-sidebar-copy">
          <strong>{catalogNode.title}</strong>
          <Text type="secondary">
            {catalogNodeKindLabel(catalogNode.node_kind)}
          </Text>
        </span>
        <span className="catalog-sidebar-trailing">
          <span className="catalog-sidebar-slot catalog-sidebar-count-slot">
            {directoryPointCount ? (
              <Tooltip title={`共 ${directoryPointCount} 个点位`}>
                <span className="catalog-sidebar-count" aria-label={`共 ${directoryPointCount} 个点位`}>
                  {directoryPointCount}
                </span>
              </Tooltip>
            ) : null}
          </span>
          <span className="catalog-sidebar-slot catalog-sidebar-directory-status-slot">
            {catalogNode.node_kind === "directory" ? (
              <Tooltip title={statusLabel}>
                <span className="catalog-sidebar-status" aria-label={`状态：${statusLabel}`}>
                  <span className={`catalog-sidebar-status-dot ${catalogStatusDotClass(catalogNode.status)}`} aria-hidden="true" />
                </span>
              </Tooltip>
            ) : null}
          </span>
          <span className="catalog-sidebar-slot catalog-sidebar-primary-action-slot">
            {catalogNode.node_kind === "directory" ? (
              <Dropdown
                trigger={["click"]}
                menu={{
                  items: [
                    { key: "add-directory", icon: actionIcon("add-directory"), label: "新建子目录" },
                    { key: "add-point", icon: actionIcon("add-point"), label: "新建子点位" },
                    { type: "divider" },
                    { key: "copy-directory", icon: actionIcon("copy-directory"), label: "从已有目录复制到此目录" },
                    { key: "copy-point", icon: actionIcon("copy-point"), label: "从已有实验复制到此目录" },
                  ],
                  onClick: ({ key }) => onAction(catalogNode, key as CatalogTreeRowAction),
                }}
              >
                <Button
                  size="small"
                  type="text"
                  aria-label="新建子节点"
                  title="新建子节点"
                  icon={<Plus size={15} />}
                  onClick={(event) => event.stopPropagation()}
                />
              </Dropdown>
            ) : (
              <Tooltip title={hasWarnings && warningText ? `${pointStatusLabel}：${warningText}` : pointStatusLabel}>
                <span
                  className={`catalog-sidebar-point-status ${pointStatusClass(catalogNode.status, hasWarnings)}`}
                  aria-label={`点位状态：${pointStatusLabel}`}
                >
                  {pointStatusIcon(catalogNode.status, hasWarnings)}
                </span>
              </Tooltip>
            )}
          </span>
          <span className="catalog-sidebar-slot catalog-sidebar-more-slot">
            <Dropdown
              trigger={["click"]}
              menu={{
                items: menuItems,
                onClick: ({ key }) => onAction(catalogNode, key as CatalogTreeRowAction),
              }}
            >
              <Button
                size="small"
                type="text"
                aria-label="节点更多操作"
                icon={<MoreHorizontal size={16} />}
                onClick={(event) => event.stopPropagation()}
              />
            </Dropdown>
          </span>
        </span>
      </div>
      {node.isSelected ? <Text className="sr-only">当前选中节点</Text> : null}
    </div>
  );
}

export function CatalogArboristCursor({ top, left, indent }: CursorProps) {
  return <div className="catalog-arborist-cursor" style={{ top, left: left + indent }} />;
}

export function CatalogArboristDragPreview({ id, dragIds, isDragging }: DragPreviewProps) {
  if (!isDragging || !id) return null;
  return (
    <div className="catalog-arborist-drag-preview">
      <Clipboard size={14} />
      <span>{dragIds.length > 1 ? `${dragIds.length} 个节点` : "移动节点"}</span>
    </div>
  );
}
export function CatalogArboristModernDragPreview({
  id,
  dragIds,
  isDragging,
  offset,
  mouse,
  getNode,
}: DragPreviewProps & {
  getNode?: CatalogTreeDragPreviewNodeGetter;
}) {
  const position = offset || mouse;
  if (!isDragging || !position) return null;
  const previewNode = id ? getNode?.(id) : undefined;
  const multiDrag = dragIds.length > 1;
  const title = multiDrag ? `${dragIds.length} 个节点` : previewNode?.catalogNode.title || "移动节点";
  const subtitle = multiDrag ? "批量移动" : previewNode ? catalogNodeKindLabel(previewNode.catalogNode.node_kind) : "正在移动";

  return (
    <div className="catalog-arborist-drag-preview-layer">
      <div className="catalog-arborist-drag-preview" style={{ transform: `translate(${position.x + 8}px, ${position.y + 8}px)` }}>
        <span className="catalog-arborist-drag-preview-icon" aria-hidden="true">
          {multiDrag ? <Clipboard size={15} /> : rowIcon(previewNode?.catalogNode.node_kind || "directory", false)}
        </span>
        <span className="catalog-arborist-drag-preview-copy">
          <strong>{title}</strong>
          <span>{subtitle}</span>
        </span>
      </div>
    </div>
  );
}
