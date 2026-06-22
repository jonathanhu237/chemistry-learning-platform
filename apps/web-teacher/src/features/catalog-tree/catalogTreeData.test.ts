import { describe, expect, it } from "vitest";

import type { CatalogNodeCard } from "../../api/catalogTree";
import {
  applyCatalogTreeMoveOptimistically,
  fallbackCatalogTreeReorder,
  findCatalogTreeNode,
  isCatalogTreeDescendant,
  isCatalogTreeParentLoaded,
  mergeCatalogTreeData,
  replaceCatalogTreeChildren,
  resolveCatalogArboristMove,
  resolveCatalogDropDisabled,
  toCatalogTreeNode,
  type CatalogTreeDataNode,
} from "./catalogTreeData";

function node(partial: Partial<CatalogNodeCard> & { node_id: string; title: string; node_kind: "directory" | "point" }): CatalogNodeCard {
  return {
    chapter_id: "CH13",
    parent_id: null,
    summary: "",
    status: "draft",
    display_order: 1,
    actions: [],
    has_children: false,
    descendant_point_count: 0,
    has_point_content: partial.node_kind === "point",
    media_count: 0,
    published_media_count: 0,
    validation: { ok: true, errors: [], warnings: [] },
    ...partial,
  };
}

function sampleTree(): CatalogTreeDataNode[] {
  const root = toCatalogTreeNode(node({ node_id: "dir-a", title: "A", node_kind: "directory", has_children: true }));
  root.loaded = true;
  root.children = [
    toCatalogTreeNode(node({ node_id: "point-a", title: "P1", node_kind: "point", parent_id: "dir-a", display_order: 1 })),
    toCatalogTreeNode(node({ node_id: "point-b", title: "P2", node_kind: "point", parent_id: "dir-a", display_order: 2 })),
    toCatalogTreeNode(node({ node_id: "dir-b", title: "B", node_kind: "directory", parent_id: "dir-a", display_order: 3, has_children: true })),
  ];
  root.children[2].loaded = true;
  root.children[2].children = [
    toCatalogTreeNode(node({ node_id: "point-c", title: "P3", node_kind: "point", parent_id: "dir-b", display_order: 1 })),
  ];
  return [root];
}

describe("catalog tree data helpers", () => {
  it("builds Arborist internal directory nodes and point leaves", () => {
    const point = toCatalogTreeNode(node({ node_id: "p", title: "Point", node_kind: "point" }));
    const directory = toCatalogTreeNode(node({ node_id: "d", title: "Directory", node_kind: "directory", has_children: true, descendant_point_count: 4 }));

    expect(point.children).toBeNull();
    expect(point.loaded).toBe(true);
    expect(directory.children).toEqual([]);
    expect(directory.loaded).toBe(false);
    expect(directory.catalogNode.descendant_point_count).toBe(4);
  });

  it("preserves loaded children when root cards refresh", () => {
    const previous = sampleTree();
    const merged = mergeCatalogTreeData([node({ node_id: "dir-a", title: "A updated", node_kind: "directory", has_children: true })], previous);

    expect(merged[0].name).toBe("A updated");
    expect(merged[0].children?.map((item) => item.id)).toEqual(["point-a", "point-b", "dir-b"]);
  });

  it("replaces lazy-loaded directory children", () => {
    const tree = [toCatalogTreeNode(node({ node_id: "dir-a", title: "A", node_kind: "directory", has_children: true }))];
    const next = replaceCatalogTreeChildren(tree, "dir-a", [
      toCatalogTreeNode(node({ node_id: "point-a", title: "P1", node_kind: "point", parent_id: "dir-a" })),
    ]);

    expect(next[0].loaded).toBe(true);
    expect(next[0].children?.[0].id).toBe("point-a");
  });

  it("updates the refreshed directory card while replacing its children", () => {
    const tree = sampleTree();
    const next = replaceCatalogTreeChildren(
      tree,
      "dir-b",
      [toCatalogTreeNode(node({ node_id: "point-c", title: "P3 updated", node_kind: "point", parent_id: "dir-b" }))],
      node({ node_id: "dir-b", title: "B updated", node_kind: "directory", parent_id: "dir-a", has_children: true, descendant_point_count: 2 }),
    );
    const refreshed = findCatalogTreeNode(next, "dir-b");

    expect(refreshed?.name).toBe("B updated");
    expect(refreshed?.catalogNode.descendant_point_count).toBe(2);
    expect(refreshed?.children?.map((item) => item.name)).toEqual(["P3 updated"]);
  });

  it("detects descendant moves", () => {
    expect(isCatalogTreeDescendant(sampleTree(), "dir-a", "point-c")).toBe(true);
    expect(isCatalogTreeDescendant(sampleTree(), "dir-b", "point-a")).toBe(false);
  });

  it("detects loaded parent branches including chapter root", () => {
    const tree = sampleTree();
    const unloaded = toCatalogTreeNode(node({ node_id: "dir-unloaded", title: "Unloaded", node_kind: "directory", has_children: true }));
    tree.push(unloaded);

    expect(isCatalogTreeParentLoaded(tree, null)).toBe(true);
    expect(isCatalogTreeParentLoaded(tree, "dir-a")).toBe(true);
    expect(isCatalogTreeParentLoaded(tree, "dir-unloaded")).toBe(false);
    expect(isCatalogTreeParentLoaded(tree, "missing")).toBe(false);
  });

  it("rejects moving a node into a point", () => {
    expect(
      resolveCatalogArboristMove({
        tree: sampleTree(),
        dragIds: ["point-b"],
        parentId: "point-a",
        index: 0,
      }),
    ).toMatchObject({ kind: "invalid" });
  });

  it("rejects multi-node drags, missing dragged nodes, missing targets, and cross-chapter targets", () => {
    const tree = sampleTree();
    tree.push(toCatalogTreeNode(node({ node_id: "other-dir", title: "Other", node_kind: "directory", chapter_id: "CH14" })));

    expect(resolveCatalogArboristMove({ tree, dragIds: ["point-a", "point-b"], parentId: "dir-a", index: 0 })).toMatchObject({
      kind: "invalid",
    });
    expect(resolveCatalogArboristMove({ tree, dragIds: ["missing"], parentId: "dir-a", index: 0 })).toMatchObject({ kind: "invalid" });
    expect(resolveCatalogArboristMove({ tree, dragIds: ["point-a"], parentId: "missing-parent", index: 0 })).toMatchObject({
      kind: "invalid",
    });
    expect(resolveCatalogArboristMove({ tree, dragIds: ["point-a"], parentId: "other-dir", index: 0 })).toMatchObject({
      kind: "invalid",
    });
    expect(resolveCatalogDropDisabled({ tree, dragIds: ["point-a"], parentId: "missing-parent" })).toBe(true);
    expect(resolveCatalogDropDisabled({ tree, dragIds: ["point-a"], parentId: "other-dir" })).toBe(true);
  });

  it("rejects moving a directory into its descendant", () => {
    expect(resolveCatalogDropDisabled({ tree: sampleTree(), dragIds: ["dir-a"], parentId: "dir-b" })).toBe(true);
  });

  it("builds sibling reorder payloads from Arborist moves", () => {
    expect(
      resolveCatalogArboristMove({
        tree: sampleTree(),
        dragIds: ["point-b"],
        parentId: "dir-a",
        index: 0,
      }),
    ).toEqual({
      kind: "reorder",
      nodeId: "point-b",
      sourceParentId: "dir-a",
      targetParentId: "dir-a",
      targetIndex: 0,
      items: [
        { node_id: "point-b", display_order: 1 },
        { node_id: "point-a", display_order: 2 },
        { node_id: "dir-b", display_order: 3 },
      ],
    });
  });

  it("builds move payloads into a directory", () => {
    expect(
      resolveCatalogArboristMove({
        tree: sampleTree(),
        dragIds: ["point-a"],
        parentId: "dir-b",
        index: 1,
      }),
    ).toEqual({
      kind: "move",
      nodeId: "point-a",
      sourceParentId: "dir-a",
      targetParentId: "dir-b",
      targetIndex: 1,
      payload: { parent_id: "dir-b", display_order: 2 },
    });
  });

  it("builds move payloads back to the chapter root", () => {
    expect(
      resolveCatalogArboristMove({
        tree: sampleTree(),
        dragIds: ["point-a"],
        parentId: null,
        index: 1,
      }),
    ).toEqual({
      kind: "move",
      nodeId: "point-a",
      sourceParentId: "dir-a",
      targetParentId: null,
      targetIndex: 1,
      payload: { parent_id: null, display_order: 2 },
    });
  });

  it("builds directory move payloads", () => {
    expect(
      resolveCatalogArboristMove({
        tree: sampleTree(),
        dragIds: ["dir-b"],
        parentId: null,
        index: 0,
      }),
    ).toEqual({
      kind: "move",
      nodeId: "dir-b",
      sourceParentId: "dir-a",
      targetParentId: null,
      targetIndex: 0,
      payload: { parent_id: null, display_order: 1 },
    });
  });

  it("keeps fallback movement for menus and keyboard-adjacent controls", () => {
    expect(fallbackCatalogTreeReorder(sampleTree(), "point-b", "before")).toEqual({
      kind: "reorder",
      nodeId: "point-b",
      sourceParentId: "dir-a",
      targetParentId: "dir-a",
      targetIndex: 0,
      items: [
        { node_id: "point-b", display_order: 1 },
        { node_id: "point-a", display_order: 2 },
        { node_id: "dir-b", display_order: 3 },
      ],
    });
  });

  it("applies optimistic same-parent reorder without mutating previous tree state", () => {
    const tree = sampleTree();
    const result = resolveCatalogArboristMove({ tree, dragIds: ["point-b"], parentId: "dir-a", index: 0 });
    const optimistic = applyCatalogTreeMoveOptimistically(tree, result);

    expect(optimistic?.kind).toBe("reorder");
    expect(optimistic?.refreshParentIds).toEqual(["dir-a"]);
    expect(optimistic?.refreshRoot).toBe(false);
    expect(findCatalogTreeNode(optimistic?.tree || [], "dir-a")?.children?.map((item) => item.id)).toEqual(["point-b", "point-a", "dir-b"]);
    expect(findCatalogTreeNode(tree, "dir-a")?.children?.map((item) => item.id)).toEqual(["point-a", "point-b", "dir-b"]);
  });

  it("applies optimistic cross-parent moves into loaded directories", () => {
    const tree = sampleTree();
    const result = resolveCatalogArboristMove({ tree, dragIds: ["point-a"], parentId: "dir-b", index: 1 });
    const optimistic = applyCatalogTreeMoveOptimistically(tree, result);

    expect(optimistic).toMatchObject({
      kind: "move",
      nodeId: "point-a",
      sourceParentId: "dir-a",
      targetParentId: "dir-b",
      sourceParentWasLoaded: true,
      targetParentWasLoaded: true,
      insertedIntoTarget: true,
      refreshParentIds: ["dir-a", "dir-b"],
      refreshRoot: false,
      staleParentIds: [],
    });
    expect(findCatalogTreeNode(optimistic?.tree || [], "dir-a")?.children?.map((item) => item.id)).toEqual(["point-b", "dir-b"]);
    expect(findCatalogTreeNode(optimistic?.tree || [], "dir-b")?.children?.map((item) => item.id)).toEqual(["point-c", "point-a"]);
    expect(findCatalogTreeNode(optimistic?.tree || [], "point-a")?.catalogNode.parent_id).toBe("dir-b");
    expect(findCatalogTreeNode(optimistic?.tree || [], "point-a")?.catalogNode.display_order).toBe(2);
  });

  it("applies optimistic moves into the chapter root", () => {
    const tree = sampleTree();
    const result = resolveCatalogArboristMove({ tree, dragIds: ["point-a"], parentId: null, index: 1 });
    const optimistic = applyCatalogTreeMoveOptimistically(tree, result);

    expect(optimistic?.refreshRoot).toBe(true);
    expect(optimistic?.refreshParentIds).toEqual(["dir-a"]);
    expect(optimistic?.tree.map((item) => item.id)).toEqual(["dir-a", "point-a"]);
    expect(findCatalogTreeNode(optimistic?.tree || [], "point-a")?.catalogNode.parent_id).toBeNull();
  });

  it("marks unloaded destination branches stale while removing the visible source node", () => {
    const tree = sampleTree();
    const unloaded = toCatalogTreeNode(node({ node_id: "dir-unloaded", title: "Unloaded", node_kind: "directory", has_children: true }));
    tree.push(unloaded);
    const result = resolveCatalogArboristMove({ tree, dragIds: ["point-a"], parentId: "dir-unloaded", index: 0 });
    const optimistic = applyCatalogTreeMoveOptimistically(tree, result);

    expect(optimistic).toMatchObject({
      kind: "move",
      targetParentId: "dir-unloaded",
      targetParentWasLoaded: false,
      insertedIntoTarget: false,
      refreshParentIds: ["dir-a"],
      staleParentIds: ["dir-unloaded"],
    });
    expect(findCatalogTreeNode(optimistic?.tree || [], "dir-a")?.children?.map((item) => item.id)).toEqual(["point-b", "dir-b"]);
    expect(findCatalogTreeNode(optimistic?.tree || [], "dir-unloaded")?.loaded).toBe(false);
    expect(findCatalogTreeNode(optimistic?.tree || [], "point-a")).toBeUndefined();
  });
});
