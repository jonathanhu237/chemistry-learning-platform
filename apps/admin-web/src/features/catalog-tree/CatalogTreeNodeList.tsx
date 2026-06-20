import { useState } from "react";
import { Button, Flex, Space, Spin, Tag, Tooltip, Typography } from "antd";
import {
  ArrowDownOutlined,
  ArrowRightOutlined,
  ArrowUpOutlined,
  BranchesOutlined,
  FileTextOutlined,
  FolderOpenOutlined,
  LinkOutlined,
  PlusOutlined,
  WarningOutlined,
} from "@ant-design/icons";

import type { CatalogNodeCard } from "../../api/catalogTree";
import { QueryState } from "../../components/QueryState";
import { useCatalogChildren } from "./catalogTreeHooks";
import { catalogNodeKindLabel, catalogStatusColor, siblingReorderItems } from "./catalogTreeMappers";

const { Text } = Typography;

function nodeIcon(kind: CatalogNodeCard["node_kind"]) {
  if (kind === "point") return <FileTextOutlined />;
  if (kind === "hybrid") return <BranchesOutlined />;
  if (kind === "shortcut") return <LinkOutlined />;
  return <FolderOpenOutlined />;
}

function CatalogTreeNodeRow({
  node,
  selected,
  onSelect,
  onAddChild,
  onReorder,
  siblings,
}: {
  node: CatalogNodeCard;
  selected: boolean;
  onSelect: (node: CatalogNodeCard) => void;
  onAddChild: (node: CatalogNodeCard, kind?: CatalogNodeCard["node_kind"]) => void;
  onReorder: (items: Array<{ node_id: string; display_order: number }>) => void;
  siblings: CatalogNodeCard[];
}) {
  const upItems = siblingReorderItems(siblings, node.node_id, "up");
  const downItems = siblingReorderItems(siblings, node.node_id, "down");
  const hasWarnings = Boolean(node.validation?.errors?.length || node.validation?.warnings?.length);
  return (
    <div className={`catalog-tree-row${selected ? " is-selected" : ""}`}>
      <button className="catalog-tree-row-main" type="button" onClick={() => onSelect(node)}>
        <span className="catalog-tree-node-icon">{nodeIcon(node.node_kind)}</span>
        <span className="catalog-tree-node-copy">
          <strong>{node.title}</strong>
          <span>
            {catalogNodeKindLabel(node.node_kind)}
            {node.media_count ? ` · ${node.published_media_count}/${node.media_count} 视频` : ""}
          </span>
        </span>
      </button>
      <Space size={4} className="catalog-tree-row-actions">
        <Tag color={catalogStatusColor(node.status)}>{node.status}</Tag>
        {hasWarnings ? (
          <Tooltip title={[...(node.validation?.errors || []), ...(node.validation?.warnings || [])].join("；")}>
            <WarningOutlined className="catalog-warning-icon" />
          </Tooltip>
        ) : null}
        <Tooltip title="新增子节点">
          <Button size="small" icon={<PlusOutlined />} onClick={() => onAddChild(node)} />
        </Tooltip>
        <Tooltip title="上移">
          <Button size="small" icon={<ArrowUpOutlined />} disabled={!upItems.length} onClick={() => onReorder(upItems)} />
        </Tooltip>
        <Tooltip title="下移">
          <Button size="small" icon={<ArrowDownOutlined />} disabled={!downItems.length} onClick={() => onReorder(downItems)} />
        </Tooltip>
      </Space>
    </div>
  );
}

function CatalogTreeBranch({
  node,
  selectedNodeId,
  onSelect,
  onAddChild,
  onReorder,
  siblings,
}: {
  node: CatalogNodeCard;
  selectedNodeId?: string | null;
  onSelect: (node: CatalogNodeCard) => void;
  onAddChild: (node: CatalogNodeCard, kind?: CatalogNodeCard["node_kind"]) => void;
  onReorder: (items: Array<{ node_id: string; display_order: number }>) => void;
  siblings: CatalogNodeCard[];
}) {
  const [expanded, setExpanded] = useState(false);
  const children = useCatalogChildren(node.node_id, expanded);
  const childItems = children.data?.children || [];
  return (
    <div className="catalog-tree-branch">
      <Flex align="center" gap={6}>
        <Button
          className="catalog-tree-expand"
          size="small"
          type="text"
          icon={expanded ? <ArrowDownOutlined /> : <ArrowRightOutlined />}
          disabled={!node.has_children}
          onClick={() => setExpanded((value) => !value)}
        />
        <CatalogTreeNodeRow
          node={node}
          selected={selectedNodeId === node.node_id}
          onSelect={onSelect}
          onAddChild={onAddChild}
          onReorder={onReorder}
          siblings={siblings}
        />
      </Flex>
      {expanded ? (
        <div className="catalog-tree-children">
          {children.isLoading ? <Spin size="small" /> : null}
          {children.error ? <Text type="danger">子节点加载失败</Text> : null}
          {childItems.map((child) => (
            <CatalogTreeBranch
              key={child.node_id}
              node={child}
              selectedNodeId={selectedNodeId}
              onSelect={onSelect}
              onAddChild={onAddChild}
              onReorder={onReorder}
              siblings={childItems}
            />
          ))}
        </div>
      ) : null}
    </div>
  );
}

export function CatalogTreeNodeList({
  nodes,
  selectedNodeId,
  loading,
  error,
  onSelect,
  onAddRoot,
  onAddChild,
  onReorder,
}: {
  nodes: CatalogNodeCard[];
  selectedNodeId?: string | null;
  loading?: boolean;
  error?: unknown;
  onSelect: (node: CatalogNodeCard) => void;
  onAddRoot: () => void;
  onAddChild: (node: CatalogNodeCard, kind?: CatalogNodeCard["node_kind"]) => void;
  onReorder: (items: Array<{ node_id: string; display_order: number }>) => void;
}) {
  return (
    <div className="catalog-tree-list">
      <Flex align="center" justify="space-between" className="catalog-tree-list-header">
        <Text strong>章节目录树</Text>
        <Button size="small" icon={<PlusOutlined />} onClick={onAddRoot}>
          根节点
        </Button>
      </Flex>
      <QueryState loading={Boolean(loading)} error={error} empty={!nodes.length}>
        <div className="catalog-tree-root">
          {nodes.map((node) => (
            <CatalogTreeBranch
              key={node.node_id}
              node={node}
              selectedNodeId={selectedNodeId}
              onSelect={onSelect}
              onAddChild={onAddChild}
              onReorder={onReorder}
              siblings={nodes}
            />
          ))}
        </div>
      </QueryState>
    </div>
  );
}
