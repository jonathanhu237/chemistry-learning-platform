import type { CatalogNodeCard, CatalogNodeMovePayload } from "../../api/catalogTree";

export type CatalogArboristNode = {
  id: string;
  name: string;
  kind: CatalogNodeCard["node_kind"];
  catalogNode: CatalogNodeCard;
  loaded: boolean;
  children?: CatalogArboristNode[] | null;
};

export type CatalogTreeDataNode = CatalogArboristNode;

type CatalogTreeParentId = string | null;
type CatalogTreeReorderItem = { node_id: string; display_order: number };

export type CatalogTreeMoveResult =
  | { kind: "invalid"; reason: string }
  | {
      kind: "reorder";
      nodeId: string;
      sourceParentId: CatalogTreeParentId;
      targetParentId: CatalogTreeParentId;
      targetIndex: number;
      items: CatalogTreeReorderItem[];
    }
  | {
      kind: "move";
      nodeId: string;
      sourceParentId: CatalogTreeParentId;
      targetParentId: CatalogTreeParentId;
      targetIndex: number;
      payload: CatalogNodeMovePayload;
    };

export type CatalogTreeDropResult = CatalogTreeMoveResult;

export type CatalogTreeOptimisticMove = {
  kind: "reorder" | "move";
  tree: CatalogTreeDataNode[];
  nodeId: string;
  sourceParentId: CatalogTreeParentId;
  targetParentId: CatalogTreeParentId;
  sourceParentWasLoaded: boolean;
  targetParentWasLoaded: boolean;
  insertedIntoTarget: boolean;
  refreshParentIds: string[];
  refreshRoot: boolean;
  staleParentIds: string[];
};

export function toCatalogTreeNode(node: CatalogNodeCard, previous?: CatalogArboristNode): CatalogArboristNode {
  const isPoint = node.node_kind === "point";
  const existingChildren = previous?.children ?? [];
  return {
    id: node.node_id,
    name: node.title,
    kind: node.node_kind,
    catalogNode: node,
    loaded: isPoint ? true : previous?.loaded ?? !node.has_children,
    children: isPoint ? null : existingChildren,
  };
}

export function mergeCatalogTreeData(nodes: CatalogNodeCard[], previous: CatalogArboristNode[] = []): CatalogArboristNode[] {
  const previousById = new Map(previous.map((item) => [item.id, item]));
  return nodes.map((node) => toCatalogTreeNode(node, previousById.get(node.node_id)));
}

export function replaceCatalogTreeChildren(
  tree: CatalogArboristNode[],
  nodeId: string,
  children: CatalogArboristNode[],
  parentNode?: CatalogNodeCard,
): CatalogArboristNode[] {
  return tree.map((item) => {
    if (item.id === nodeId) {
      const nextParent = parentNode ? toCatalogTreeNode(parentNode, item) : item;
      return { ...nextParent, loaded: true, children };
    }
    if (!item.children?.length) return item;
    return { ...item, children: replaceCatalogTreeChildren(item.children, nodeId, children, parentNode) };
  });
}

export function findCatalogTreeNode(tree: CatalogArboristNode[], nodeId: string): CatalogArboristNode | undefined {
  for (const item of tree) {
    if (item.id === nodeId) return item;
    if (item.children?.length) {
      const match = findCatalogTreeNode(item.children, nodeId);
      if (match) return match;
    }
  }
  return undefined;
}

export function findCatalogTreeParentKey(
  tree: CatalogArboristNode[],
  nodeId: string,
  parentId: string | null = null,
): string | null | undefined {
  for (const item of tree) {
    if (item.id === nodeId) return parentId;
    if (item.children?.length) {
      const match = findCatalogTreeParentKey(item.children, nodeId, item.id);
      if (match !== undefined) return match;
    }
  }
  return undefined;
}

export function catalogTreeSiblings(tree: CatalogArboristNode[], parentId: string | null): CatalogArboristNode[] {
  if (!parentId) return tree;
  const parent = findCatalogTreeNode(tree, parentId);
  return parent?.children || [];
}

export function isCatalogTreeParentLoaded(tree: CatalogArboristNode[], parentId: CatalogTreeParentId): boolean {
  if (!parentId) return true;
  const parent = findCatalogTreeNode(tree, parentId);
  return Boolean(parent && parent.kind === "directory" && parent.loaded);
}

export function isCatalogTreeDescendant(tree: CatalogArboristNode[], parentId: string, candidateId: string): boolean {
  const parent = findCatalogTreeNode(tree, parentId);
  if (!parent?.children?.length) return false;
  return Boolean(findCatalogTreeNode(parent.children, candidateId));
}

function clampIndex(index: number, maxLength: number): number {
  if (!Number.isFinite(index)) return maxLength;
  return Math.max(0, Math.min(index, maxLength));
}

function withCatalogTreePlacement(
  node: CatalogArboristNode,
  parentId: CatalogTreeParentId,
  displayOrder: number,
): CatalogArboristNode {
  return {
    ...node,
    catalogNode: {
      ...node.catalogNode,
      parent_id: parentId,
      display_order: displayOrder,
    },
  };
}

function catalogTreePointWeight(node: CatalogArboristNode): number {
  return node.kind === "point" ? 1 : node.catalogNode.descendant_point_count;
}

function renumberCatalogTreeSiblings(
  siblings: CatalogArboristNode[],
  parentId: CatalogTreeParentId,
): CatalogArboristNode[] {
  return siblings.map((sibling, index) => withCatalogTreePlacement(sibling, parentId, index + 1));
}

function removeCatalogTreeNodeFromParent(
  tree: CatalogArboristNode[],
  parentId: CatalogTreeParentId,
  nodeId: string,
): { tree: CatalogArboristNode[]; node?: CatalogArboristNode } {
  if (!parentId) {
    const currentIndex = tree.findIndex((item) => item.id === nodeId);
    if (currentIndex < 0) return { tree };
    const next = tree.slice();
    const [removed] = next.splice(currentIndex, 1);
    return { tree: renumberCatalogTreeSiblings(next, null), node: removed };
  }

  let removed: CatalogArboristNode | undefined;
  const walk = (items: CatalogArboristNode[]): CatalogArboristNode[] =>
    items.map((item) => {
      if (item.id === parentId) {
        const children = item.children || [];
        const currentIndex = children.findIndex((child) => child.id === nodeId);
        if (currentIndex < 0) return item;
        const nextChildren = children.slice();
        [removed] = nextChildren.splice(currentIndex, 1);
        return {
          ...item,
          catalogNode: {
            ...item.catalogNode,
            has_children: nextChildren.length > 0,
            descendant_point_count: removed
              ? Math.max(0, item.catalogNode.descendant_point_count - catalogTreePointWeight(removed))
              : item.catalogNode.descendant_point_count,
          },
          children: renumberCatalogTreeSiblings(nextChildren, parentId),
        };
      }
      if (!item.children?.length) return item;
      return { ...item, children: walk(item.children) };
    });

  return { tree: walk(tree), node: removed };
}

function insertCatalogTreeNodeIntoParent({
  tree,
  node,
  parentId,
  index,
}: {
  tree: CatalogArboristNode[];
  node: CatalogArboristNode;
  parentId: CatalogTreeParentId;
  index: number;
}): { tree: CatalogArboristNode[]; inserted: boolean } {
  if (!parentId) {
    const next = tree.slice();
    next.splice(clampIndex(index, next.length), 0, node);
    return { tree: renumberCatalogTreeSiblings(next, null), inserted: true };
  }

  let inserted = false;
  const walk = (items: CatalogArboristNode[]): CatalogArboristNode[] =>
    items.map((item) => {
      if (item.id === parentId) {
        if (!item.loaded) {
          return {
            ...item,
            loaded: false,
            catalogNode: { ...item.catalogNode, has_children: true },
          };
        }

        const children = item.children || [];
        const nextChildren = children.slice();
        nextChildren.splice(clampIndex(index, nextChildren.length), 0, node);
        inserted = true;
        return {
          ...item,
          catalogNode: {
            ...item.catalogNode,
            has_children: true,
            descendant_point_count: item.catalogNode.descendant_point_count + catalogTreePointWeight(node),
          },
          children: renumberCatalogTreeSiblings(nextChildren, parentId),
        };
      }
      if (!item.children?.length) return item;
      return { ...item, children: walk(item.children) };
    });

  return { tree: walk(tree), inserted };
}

function reorderCatalogTreeNodeWithinParent({
  tree,
  parentId,
  nodeId,
  index,
}: {
  tree: CatalogArboristNode[];
  parentId: CatalogTreeParentId;
  nodeId: string;
  index: number;
}): CatalogArboristNode[] {
  if (!parentId) {
    const currentIndex = tree.findIndex((item) => item.id === nodeId);
    if (currentIndex < 0) return tree;
    const next = tree.slice();
    const [item] = next.splice(currentIndex, 1);
    next.splice(clampIndex(index, next.length), 0, item);
    return renumberCatalogTreeSiblings(next, null);
  }

  const walk = (items: CatalogArboristNode[]): CatalogArboristNode[] =>
    items.map((item) => {
      if (item.id === parentId) {
        const children = item.children || [];
        const currentIndex = children.findIndex((child) => child.id === nodeId);
        if (currentIndex < 0) return item;
        const nextChildren = children.slice();
        const [child] = nextChildren.splice(currentIndex, 1);
        nextChildren.splice(clampIndex(index, nextChildren.length), 0, child);
        return { ...item, children: renumberCatalogTreeSiblings(nextChildren, parentId) };
      }
      if (!item.children?.length) return item;
      return { ...item, children: walk(item.children) };
    });

  return walk(tree);
}

function moveItemWithinSiblings(
  siblings: CatalogArboristNode[],
  nodeId: string,
  index: number,
): CatalogTreeReorderItem[] {
  const currentIndex = siblings.findIndex((item) => item.id === nodeId);
  if (currentIndex < 0) return [];
  const next = siblings.slice();
  const [item] = next.splice(currentIndex, 1);
  next.splice(clampIndex(index, next.length), 0, item);
  return next.map((sibling, position) => ({ node_id: sibling.id, display_order: position + 1 }));
}

export function resolveCatalogArboristMove({
  tree,
  dragIds,
  parentId,
  index,
}: {
  tree: CatalogArboristNode[];
  dragIds: string[];
  parentId: string | null;
  index: number;
}): CatalogTreeMoveResult {
  if (dragIds.length !== 1) {
    return { kind: "invalid", reason: "一次只能移动一个目录或点位" };
  }

  const nodeId = dragIds[0];
  const draggedNode = findCatalogTreeNode(tree, nodeId);
  if (!draggedNode) {
    return { kind: "invalid", reason: "未找到要移动的节点" };
  }

  const targetParent = parentId ? findCatalogTreeNode(tree, parentId) : undefined;
  if (parentId && !targetParent) {
    return { kind: "invalid", reason: "未找到目标目录" };
  }
  if (targetParent?.kind === "point") {
    return { kind: "invalid", reason: "点位不能作为父级目录" };
  }
  if (parentId && isCatalogTreeDescendant(tree, nodeId, parentId)) {
    return { kind: "invalid", reason: "不能把目录移动到自己的子级中" };
  }
  if (targetParent && targetParent.catalogNode.chapter_id !== draggedNode.catalogNode.chapter_id) {
    return { kind: "invalid", reason: "不能跨章节移动节点" };
  }

  const currentParentId = findCatalogTreeParentKey(tree, nodeId) || null;
  const siblings = catalogTreeSiblings(tree, parentId);
  if (currentParentId === parentId) {
    return {
      kind: "reorder",
      nodeId,
      sourceParentId: currentParentId,
      targetParentId: parentId,
      targetIndex: clampIndex(index, Math.max(0, siblings.length - 1)),
      items: moveItemWithinSiblings(siblings, nodeId, index),
    };
  }

  return {
    kind: "move",
    nodeId,
    sourceParentId: currentParentId,
    targetParentId: parentId,
    targetIndex: clampIndex(index, siblings.length),
    payload: {
      parent_id: parentId,
      display_order: clampIndex(index, siblings.length) + 1,
    },
  };
}

export function resolveCatalogDropDisabled({
  tree,
  dragIds,
  parentId,
}: {
  tree: CatalogArboristNode[];
  dragIds: string[];
  parentId: string | null;
}): boolean {
  if (dragIds.length !== 1) return true;
  const draggedNode = findCatalogTreeNode(tree, dragIds[0]);
  if (!draggedNode) return true;
  const targetParent = parentId ? findCatalogTreeNode(tree, parentId) : undefined;
  if (parentId && !targetParent) return true;
  if (targetParent?.kind === "point") return true;
  if (parentId && isCatalogTreeDescendant(tree, dragIds[0], parentId)) return true;
  return Boolean(targetParent && targetParent.catalogNode.chapter_id !== draggedNode.catalogNode.chapter_id);
}

export function fallbackCatalogTreeReorder(
  tree: CatalogArboristNode[],
  nodeId: string,
  direction: "before" | "after",
): CatalogTreeMoveResult {
  const parentId = findCatalogTreeParentKey(tree, nodeId) || null;
  const siblings = catalogTreeSiblings(tree, parentId);
  const currentIndex = siblings.findIndex((item) => item.id === nodeId);
  if (currentIndex < 0) {
    return { kind: "invalid", reason: "未找到要移动的节点" };
  }
  const targetIndex = direction === "before" ? currentIndex - 1 : currentIndex + 1;
  if (targetIndex < 0 || targetIndex >= siblings.length) {
    return { kind: "invalid", reason: "已经在当前层级的边界" };
  }
  return {
    kind: "reorder",
    nodeId,
    sourceParentId: parentId,
    targetParentId: parentId,
    targetIndex,
    items: moveItemWithinSiblings(siblings, nodeId, targetIndex),
  };
}

function uniqueNonNullParentIds(parentIds: CatalogTreeParentId[]): string[] {
  return Array.from(new Set(parentIds.filter((parentId): parentId is string => Boolean(parentId))));
}

export function applyCatalogTreeMoveOptimistically(
  tree: CatalogArboristNode[],
  result: CatalogTreeMoveResult,
): CatalogTreeOptimisticMove | null {
  if (result.kind === "invalid") return null;

  const sourceParentWasLoaded = isCatalogTreeParentLoaded(tree, result.sourceParentId);
  const targetParentWasLoaded = isCatalogTreeParentLoaded(tree, result.targetParentId);
  const refreshRoot = result.sourceParentId === null || result.targetParentId === null;

  if (result.kind === "reorder") {
    if (!result.items.length) return null;
    return {
      kind: "reorder",
      tree: reorderCatalogTreeNodeWithinParent({
        tree,
        parentId: result.targetParentId,
        nodeId: result.nodeId,
        index: result.targetIndex,
      }),
      nodeId: result.nodeId,
      sourceParentId: result.sourceParentId,
      targetParentId: result.targetParentId,
      sourceParentWasLoaded,
      targetParentWasLoaded,
      insertedIntoTarget: true,
      refreshParentIds: uniqueNonNullParentIds([result.targetParentId]),
      refreshRoot,
      staleParentIds: [],
    };
  }

  const removed = removeCatalogTreeNodeFromParent(tree, result.sourceParentId, result.nodeId);
  if (!removed.node) return null;
  const inserted = insertCatalogTreeNodeIntoParent({
    tree: removed.tree,
    node: removed.node,
    parentId: result.targetParentId,
    index: result.targetIndex,
  });

  return {
    kind: "move",
    tree: inserted.tree,
    nodeId: result.nodeId,
    sourceParentId: result.sourceParentId,
    targetParentId: result.targetParentId,
    sourceParentWasLoaded,
    targetParentWasLoaded,
    insertedIntoTarget: inserted.inserted,
    refreshParentIds: uniqueNonNullParentIds([
      sourceParentWasLoaded ? result.sourceParentId : null,
      targetParentWasLoaded ? result.targetParentId : null,
    ]),
    refreshRoot,
    staleParentIds: !inserted.inserted && result.targetParentId ? [result.targetParentId] : [],
  };
}
