import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { App as AntApp, Button, Dropdown, Flex, Spin, Typography, type MenuProps } from "antd";
import { Tree, type DragPreviewProps, type MoveHandler, type NodeRendererProps, type TreeApi } from "react-arborist";
import { Copy, Folder, FlaskConical, Plus } from "lucide-react";

import { listCatalogChildren, type CatalogNodeCard, type CatalogNodeMovePayload } from "../../api/catalogTree";
import { QueryState } from "../../components/QueryState";
import { errorMessage } from "../../lib/errors";
import {
  applyCatalogTreeMoveOptimistically,
  fallbackCatalogTreeReorder,
  findCatalogTreeNode,
  mergeCatalogTreeData,
  replaceCatalogTreeChildren,
  resolveCatalogArboristMove,
  resolveCatalogDropDisabled,
  toCatalogTreeNode,
  type CatalogArboristNode,
  type CatalogTreeDataNode,
  type CatalogTreeMoveResult,
  type CatalogTreeOptimisticMove,
} from "./catalogTreeData";
import {
  CatalogArboristCursor,
  CatalogArboristModernDragPreview,
  CatalogTreeRow,
  type CatalogTreeRowAction,
} from "./CatalogTreeRow";

const { Text } = Typography;

function useElementSize<T extends HTMLElement>() {
  const ref = useRef<T | null>(null);
  const [size, setSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    const element = ref.current;
    if (!element) return;
    const update = () => {
      const rect = element.getBoundingClientRect();
      setSize({ width: Math.floor(rect.width), height: Math.floor(rect.height) });
    };
    update();
    if (typeof ResizeObserver === "undefined") {
      window.addEventListener("resize", update);
      return () => window.removeEventListener("resize", update);
    }
    const resizeObserver = new ResizeObserver(update);
    resizeObserver.observe(element);
    return () => resizeObserver.disconnect();
  }, []);

  return [ref, size] as const;
}

function collectCatalogTreeNodes(nodes: CatalogTreeDataNode[], map = new Map<string, CatalogTreeDataNode>()) {
  for (const node of nodes) {
    map.set(node.id, node);
    if (node.children?.length) collectCatalogTreeNodes(node.children, map);
  }
  return map;
}

export function CatalogTreeNodeList({
  nodes,
  treeScopeKey,
  selectedNodeId,
  loading,
  error,
  onSelect,
  onAddRoot,
  onAddChild,
  onCopyInto,
  onMove,
  onCopyNode,
  onReorder,
  onRefreshRoots,
  onChangeStatus,
}: {
  nodes: CatalogNodeCard[];
  treeScopeKey: string;
  selectedNodeId?: string | null;
  loading?: boolean;
  error?: unknown;
  onSelect: (node: CatalogNodeCard) => void;
  onAddRoot: (kind: CatalogNodeCard["node_kind"]) => void;
  onAddChild: (node: CatalogNodeCard, kind?: CatalogNodeCard["node_kind"]) => void;
  onCopyInto: (parentNode: CatalogNodeCard | null, kind: CatalogNodeCard["node_kind"]) => void;
  onMove: (nodeId: string, payload: CatalogNodeMovePayload) => Promise<unknown> | unknown;
  onCopyNode: (node: CatalogNodeCard) => void;
  onReorder: (items: Array<{ node_id: string; display_order: number }>) => Promise<unknown> | unknown;
  onRefreshRoots?: () => Promise<unknown> | unknown;
  onChangeStatus: (node: CatalogNodeCard, action: "archive" | "restore" | "publish" | "unpublish") => void;
}) {
  const { message } = AntApp.useApp();
  const [treeData, setTreeData] = useState<CatalogTreeDataNode[]>([]);
  const [loadingDirectoryIds, setLoadingDirectoryIds] = useState<Set<string>>(() => new Set());
  const loadingDirectoryIdsRef = useRef<Set<string>>(new Set());
  const previousTreeScopeKeyRef = useRef(treeScopeKey);
  const [treeBoxRef, treeBoxSize] = useElementSize<HTMLDivElement>();
  const arboristRef = useRef<TreeApi<CatalogArboristNode> | null>(null);

  useEffect(() => {
    const scopeChanged = previousTreeScopeKeyRef.current !== treeScopeKey;
    if (scopeChanged) {
      previousTreeScopeKeyRef.current = treeScopeKey;
      loadingDirectoryIdsRef.current.clear();
      setLoadingDirectoryIds(new Set());
    }
    const scopedNodes = nodes.filter((node) => node.chapter_id === treeScopeKey);
    setTreeData((previous) => mergeCatalogTreeData(scopedNodes, scopeChanged ? [] : previous));
  }, [nodes, treeScopeKey]);

  const addRootItems: MenuProps["items"] = useMemo(
    () => [
      { key: "directory", icon: <Folder size={14} />, label: "新建目录" },
      { key: "point", icon: <FlaskConical size={14} />, label: "新建点位" },
      { type: "divider" },
      { key: "copy-directory", icon: <Copy size={14} />, label: "从已有目录复制到本章" },
      { key: "copy-point", icon: <Copy size={14} />, label: "从已有实验复制到本章" },
    ],
    [],
  );

  const loadDirectory = useCallback(
    async (nodeId: string, options: { force?: boolean } = {}) => {
      const current = findCatalogTreeNode(treeData, nodeId);
      if (!current || current.kind === "point" || (!options.force && current.loaded) || loadingDirectoryIdsRef.current.has(nodeId)) return;
      loadingDirectoryIdsRef.current.add(nodeId);
      setLoadingDirectoryIds((previous) => new Set(previous).add(nodeId));
      try {
        const response = await listCatalogChildren(nodeId);
        setTreeData((existing) => replaceCatalogTreeChildren(existing, nodeId, response.children.map((child) => toCatalogTreeNode(child))));
      } catch (caught) {
        message.error(errorMessage(caught));
      } finally {
        setLoadingDirectoryIds((previous) => {
          const next = new Set(previous);
          next.delete(nodeId);
          return next;
        });
        loadingDirectoryIdsRef.current.delete(nodeId);
      }
    },
    [message, treeData],
  );

  const refreshMoveBranches = useCallback(
    async (move: CatalogTreeOptimisticMove) => {
      if (move.refreshRoot && onRefreshRoots) {
        await onRefreshRoots();
      }
      const orderedParentIds = [
        move.sourceParentWasLoaded ? move.sourceParentId : null,
        move.targetParentWasLoaded ? move.targetParentId : null,
        ...move.refreshParentIds,
      ].filter((parentId, index, parentIds): parentId is string => Boolean(parentId) && parentIds.indexOf(parentId) === index);
      for (const parentId of orderedParentIds) {
        await loadDirectory(parentId, { force: true });
      }
    },
    [loadDirectory, onRefreshRoots],
  );

  const applyMoveResult = useCallback(
    async (result: CatalogTreeMoveResult) => {
      if (result.kind === "invalid") {
        message.warning(result.reason);
        return;
      }
      const optimistic = applyCatalogTreeMoveOptimistically(treeData, result);
      if (!optimistic) return;
      const previousTree = treeData;
      setTreeData(optimistic.tree);

      try {
        if (result.kind === "reorder") {
          if (!result.items.length) return;
          await onReorder(result.items);
        } else {
          await onMove(result.nodeId, result.payload);
        }
        await refreshMoveBranches(optimistic);
        if (findCatalogTreeNode(optimistic.tree, optimistic.nodeId)) {
          void arboristRef.current?.scrollTo(optimistic.nodeId, "smart");
        }
      } catch (caught) {
        setTreeData(previousTree);
        message.error(`移动失败，已恢复原位置：${errorMessage(caught)}`);
      }
    },
    [message, onMove, onReorder, refreshMoveBranches, treeData],
  );

  const handleMove: MoveHandler<CatalogArboristNode> = useCallback(
    ({ dragIds, parentId, index }) => {
      void applyMoveResult(resolveCatalogArboristMove({ tree: treeData, dragIds, parentId, index }));
    },
    [applyMoveResult, treeData],
  );

  const handleRowAction = useCallback(
    (node: CatalogNodeCard, action: CatalogTreeRowAction) => {
      if (action === "add-directory") {
        onAddChild(node, "directory");
        return;
      }
      if (action === "add-point") {
        onAddChild(node, "point");
        return;
      }
      if (action === "copy-node") {
        onCopyNode(node);
        return;
      }
      if (action === "copy-directory") {
        onCopyInto(node, "directory");
        return;
      }
      if (action === "copy-point") {
        onCopyInto(node, "point");
        return;
      }
      if (action === "move-before" || action === "move-after") {
        void applyMoveResult(fallbackCatalogTreeReorder(treeData, node.node_id, action === "move-before" ? "before" : "after"));
        return;
      }
      onChangeStatus(node, action);
    },
    [applyMoveResult, onAddChild, onChangeStatus, onCopyInto, onCopyNode, treeData],
  );

  const dragPreviewNodesById = useMemo(() => collectCatalogTreeNodes(treeData), [treeData]);

  const NodeRenderer = useMemo(
    () =>
      function CatalogTreeNodeRenderer(props: NodeRendererProps<CatalogArboristNode>) {
        return <CatalogTreeRow {...props} onAction={handleRowAction} onRequestLoad={(nodeId) => void loadDirectory(nodeId)} />;
      },
    [handleRowAction, loadDirectory],
  );

  const DragPreviewRenderer = useMemo(
    () =>
      function CatalogTreeDragPreviewRenderer(props: DragPreviewProps) {
        return <CatalogArboristModernDragPreview {...props} getNode={(nodeId) => dragPreviewNodesById.get(nodeId)} />;
      },
    [dragPreviewNodesById],
  );

  const treeHeight = Math.max(520, treeBoxSize.height || 620);
  const treeWidth = treeBoxSize.width > 0 ? treeBoxSize.width : "100%";

  useEffect(() => {
    if (!selectedNodeId) return;
    if (!findCatalogTreeNode(treeData, selectedNodeId)) return;
    void arboristRef.current?.scrollTo(selectedNodeId, "smart");
  }, [selectedNodeId, treeData]);

  return (
    <div className="catalog-tree-list">
      <Flex align="center" justify="space-between" className="catalog-tree-list-header">
        <Text strong>章节目录树</Text>
        <Dropdown
          trigger={["click"]}
          menu={{
            items: addRootItems,
            onClick: ({ key }) => {
              if (key === "copy-directory") {
                onCopyInto(null, "directory");
                return;
              }
              if (key === "copy-point") {
                onCopyInto(null, "point");
                return;
              }
              onAddRoot(key as CatalogNodeCard["node_kind"]);
            },
          }}
        >
          <Button size="small" type="text" icon={<Plus size={17} />} aria-label="添加到本章" title="添加到本章" />
        </Dropdown>
      </Flex>
      <QueryState loading={Boolean(loading)} error={error} empty={!nodes.length}>
        <div ref={treeBoxRef} className="catalog-arborist-shell">
          <Tree<CatalogArboristNode>
            key={treeScopeKey}
            ref={arboristRef}
            aria-label="章节目录树"
            className="catalog-arborist-tree"
            data={treeData}
            width={treeWidth}
            height={treeHeight}
            indent={22}
            rowHeight={38}
            overscanCount={8}
            selection={selectedNodeId || undefined}
            disableMultiSelection
            onActivate={(node) => onSelect(node.data.catalogNode)}
            onToggle={(id) => void loadDirectory(id)}
            onMove={handleMove}
            disableDrop={({ parentNode, dragNodes }) =>
              resolveCatalogDropDisabled({
                tree: treeData,
                dragIds: dragNodes.map((dragNode) => dragNode.id),
                parentId: parentNode?.isRoot ? null : parentNode?.id ?? null,
              })
            }
            renderCursor={CatalogArboristCursor}
            renderDragPreview={DragPreviewRenderer}
            openByDefault={false}
          >
            {NodeRenderer}
          </Tree>
          {loadingDirectoryIds.size ? <Spin size="small" className="catalog-tree-inline-spinner" /> : null}
        </div>
      </QueryState>
    </div>
  );
}
