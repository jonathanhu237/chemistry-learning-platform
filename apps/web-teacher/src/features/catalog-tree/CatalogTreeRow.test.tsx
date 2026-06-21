import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { CatalogNodeCard } from "../../api/catalogTree";
import type { CatalogArboristNode } from "./catalogTreeData";
import { CatalogArboristModernDragPreview, CatalogTreeRow, type CatalogTreeActionHandler } from "./CatalogTreeRow";

afterEach(() => {
  cleanup();
  vi.useRealTimers();
});

function node(partial: Partial<CatalogNodeCard> & { node_id: string; title: string; node_kind: "directory" | "point" }): CatalogNodeCard {
  return {
    chapter_id: "CH13",
    parent_id: null,
    summary: "",
    status: "draft",
    display_order: 1,
    student_description: "",
    card_layout: "default",
    card_presentation: {},
    point_card_presentation: {},
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

function mockParentChain(level: number, ancestorGuideContinuations: boolean[]) {
  let parent: { isRoot: boolean; nextSibling: unknown; parent: unknown } = { isRoot: true, nextSibling: null, parent: null };
  for (let index = 0; index < Math.max(0, level - 1); index += 1) {
    parent = {
      isRoot: false,
      nextSibling: (ancestorGuideContinuations[index] ?? true) ? { id: `ancestor-next-${index}` } : null,
      parent,
    };
  }
  return parent;
}

function renderRow({
  catalogNode,
  isInternal = catalogNode.node_kind === "directory",
  isOpen = false,
  isSelected = false,
  isDragging = false,
  willReceiveDrop = false,
  level = 1,
  childIndex = 1,
  hasNextSibling = true,
  ancestorGuideContinuations = [],
}: {
  catalogNode: CatalogNodeCard;
  isInternal?: boolean;
  isOpen?: boolean;
  isSelected?: boolean;
  isDragging?: boolean;
  willReceiveDrop?: boolean;
  level?: number;
  childIndex?: number;
  hasNextSibling?: boolean;
  ancestorGuideContinuations?: boolean[];
}) {
  const onAction = vi.fn<CatalogTreeActionHandler>();
  const onRequestLoad = vi.fn();
  const toggle = vi.fn();
  const open = vi.fn();
  const handleClick = vi.fn();
  const props = {
    style: {},
    dragHandle: vi.fn(),
    tree: {} as never,
    node: {
      id: catalogNode.node_id,
      data: {
        id: catalogNode.node_id,
        name: catalogNode.title,
        kind: catalogNode.node_kind,
        catalogNode,
        loaded: true,
        children: catalogNode.node_kind === "directory" ? [] : null,
      } satisfies CatalogArboristNode,
      level,
      childIndex,
      isInternal,
      isOpen,
      isSelected,
      isDragging,
      willReceiveDrop,
      parent: mockParentChain(level, ancestorGuideContinuations),
      nextSibling: hasNextSibling ? { id: `${catalogNode.node_id}-next` } : null,
      open,
      toggle,
      handleClick,
    } as never,
    onAction,
    onRequestLoad,
  };
  const view = render(<CatalogTreeRow {...props} />);
  return { ...view, onAction, onRequestLoad, open, toggle, handleClick };
}

describe("CatalogTreeRow", () => {
  it("renders directory rows with a directory chevron and directory-only add actions", () => {
    const { container } = renderRow({
      catalogNode: node({ node_id: "dir-a", title: "氧化性模块", node_kind: "directory", has_children: true, descendant_point_count: 3 }),
      isInternal: true,
    });

    expect(screen.getByText("氧化性模块")).toBeInTheDocument();
    expect(screen.getByLabelText("展开目录")).toBeInTheDocument();
    expect(screen.getByLabelText("新建子节点")).toBeInTheDocument();
    expect(screen.getByLabelText("共 3 个点位")).toHaveTextContent("3");
    expect(screen.getByLabelText("状态：草稿")).toBeInTheDocument();
    expect(container.querySelector(".catalog-sidebar-status-dot")).toHaveClass("is-draft");
    expect(container).not.toHaveTextContent("draft");
    expect(container.querySelector(".catalog-sidebar-switcher-spacer")).toBeNull();
  });

  it("toggles directory rows when the row body is clicked", () => {
    const { container, toggle, handleClick } = renderRow({
      catalogNode: node({ node_id: "dir-click", title: "Directory", node_kind: "directory", has_children: true }),
      isInternal: true,
    });

    const row = container.querySelector(".catalog-sidebar-row");
    expect(row).not.toBeNull();
    fireEvent.click(row!);

    expect(handleClick).toHaveBeenCalledTimes(1);
    expect(toggle).toHaveBeenCalledTimes(1);
  });

  it("renders point rows as leaves with an experiment icon affordance and video metadata", () => {
    const { container } = renderRow({
      catalogNode: node({
        node_id: "point-a",
        title: "氯水 + KBr 溶液 + CCl4",
        node_kind: "point",
        status: "published",
        media_count: 2,
        published_media_count: 1,
      }),
      isInternal: false,
    });

    expect(screen.getByText("氯水 + KBr 溶液 + CCl4")).toBeInTheDocument();
    expect(screen.queryByLabelText("视频 1/2")).toBeNull();
    expect(screen.getByLabelText("点位状态：已发布")).toBeInTheDocument();
    expect(screen.queryByLabelText("展开目录")).toBeNull();
    expect(screen.queryByLabelText("新建子节点")).toBeNull();
    expect(screen.queryByLabelText(/共 \d+ 个点位/)).toBeNull();
    expect(container).not.toHaveTextContent("published");
    expect(container.querySelector(".catalog-sidebar-switcher-spacer")).not.toBeNull();
    expect(container.querySelector(".kind-point .catalog-sidebar-icon svg")).not.toBeNull();
    expect(container.querySelector(".catalog-sidebar-point-status")).toHaveClass("is-published");
  });

  it("keeps selected state and long-title title text on the row shell", () => {
    const title = "氯水对溴离子、碘离子混合溶液的氧化性验证实验";
    const { container } = renderRow({
      catalogNode: node({ node_id: "dir-long", title, node_kind: "directory" }),
      isSelected: true,
    });

    const row = container.querySelector(".catalog-sidebar-item");
    expect(row).toHaveClass("is-selected");
    expect(row).toHaveAttribute("title", title);
  });

  it("does not render archived backend status text visibly", () => {
    const { container } = renderRow({
      catalogNode: node({ node_id: "dir-archived", title: "归档目录", node_kind: "directory", status: "archived" }),
    });

    expect(screen.getByLabelText("状态：已归档")).toBeInTheDocument();
    expect(container).not.toHaveTextContent("archived");
  });
});
describe("CatalogTreeRow drag and drop interaction states", () => {
  it("marks dragging source rows and valid directory drop targets", () => {
    const { container } = renderRow({
      catalogNode: node({ node_id: "dir-drop", title: "Directory", node_kind: "directory" }),
      isDragging: true,
      willReceiveDrop: true,
    });

    const row = container.querySelector(".catalog-sidebar-item");
    expect(row).toHaveClass("is-dragging");
    expect(row).toHaveClass("will-receive-drop");
  });

  it("positions short elbow branches from the current level guide", () => {
    const first = renderRow({
      catalogNode: node({ node_id: "level-1", title: "Level 1", node_kind: "directory" }),
      level: 1,
    });
    const third = renderRow({
      catalogNode: node({ node_id: "level-3", title: "Level 3", node_kind: "directory" }),
      level: 3,
    });

    expect(first.container.querySelector(".catalog-sidebar-item")).toHaveStyle({
      "--catalog-elbow-left": "13px",
      "--catalog-elbow-width": "10px",
    });
    expect(third.container.querySelector(".catalog-sidebar-item")).toHaveStyle({
      "--catalog-elbow-left": "57px",
      "--catalog-elbow-width": "10px",
    });
  });

  it("marks the current branch as terminal when the node is the last sibling", () => {
    const { container } = renderRow({
      catalogNode: node({ node_id: "last-child", title: "Last child", node_kind: "point" }),
      level: 2,
      childIndex: 2,
      hasNextSibling: false,
      ancestorGuideContinuations: [true],
    });

    const row = container.querySelector(".catalog-sidebar-item");
    const guides = container.querySelectorAll(".catalog-sidebar-guide");
    expect(row).toHaveClass("is-last-sibling");
    expect(guides).toHaveLength(2);
    expect(guides[0]).toHaveClass("is-continuing");
    expect(guides[0]).not.toHaveClass("is-current");
    expect(guides[1]).toHaveClass("is-current");
    expect(guides[1]).toHaveClass("is-terminal");
    expect(guides[1]).not.toHaveClass("is-continuing");
    expect(guides[1]).not.toHaveClass("is-first");
    expect(guides[1]).not.toHaveClass("is-only");
  });

  it("marks the first current branch without treating it as terminal", () => {
    const { container } = renderRow({
      catalogNode: node({ node_id: "first-child", title: "First child", node_kind: "directory" }),
      level: 1,
      childIndex: 0,
      hasNextSibling: true,
    });

    const guides = container.querySelectorAll(".catalog-sidebar-guide");
    expect(guides).toHaveLength(1);
    expect(guides[0]).toHaveClass("is-current");
    expect(guides[0]).toHaveClass("is-first");
    expect(guides[0]).not.toHaveClass("is-terminal");
    expect(guides[0]).not.toHaveClass("is-only");
  });

  it("marks only children so the current vertical guide can be suppressed", () => {
    const { container } = renderRow({
      catalogNode: node({ node_id: "only-child", title: "Only child", node_kind: "point" }),
      level: 1,
      childIndex: 0,
      hasNextSibling: false,
    });

    const guides = container.querySelectorAll(".catalog-sidebar-guide");
    expect(guides).toHaveLength(1);
    expect(guides[0]).toHaveClass("is-current");
    expect(guides[0]).toHaveClass("is-first");
    expect(guides[0]).toHaveClass("is-terminal");
    expect(guides[0]).toHaveClass("is-only");
    expect(guides[0]).not.toHaveClass("is-continuing");
  });

  it("continues ancestor guides only when that ancestor has following siblings", () => {
    const { container } = renderRow({
      catalogNode: node({ node_id: "middle-child", title: "Middle child", node_kind: "point" }),
      level: 3,
      childIndex: 1,
      hasNextSibling: true,
      ancestorGuideContinuations: [true, false],
    });

    const guides = container.querySelectorAll(".catalog-sidebar-guide");
    expect(guides).toHaveLength(3);
    expect(guides[0]).toHaveClass("is-continuing");
    expect(guides[1]).not.toHaveClass("is-continuing");
    expect(guides[2]).toHaveClass("is-current");
    expect(guides[2]).toHaveClass("is-continuing");
    expect(guides[2]).not.toHaveClass("is-terminal");
  });

  it("auto-expands valid collapsed directory drop targets after the hover delay", () => {
    vi.useFakeTimers();
    const { open, onRequestLoad } = renderRow({
      catalogNode: node({ node_id: "dir-hover", title: "Directory", node_kind: "directory", has_children: true }),
      isInternal: true,
      isOpen: false,
      willReceiveDrop: true,
    });

    vi.advanceTimersByTime(499);
    expect(open).not.toHaveBeenCalled();
    expect(onRequestLoad).not.toHaveBeenCalled();

    vi.advanceTimersByTime(1);
    expect(open).toHaveBeenCalledTimes(1);
    expect(onRequestLoad).toHaveBeenCalledWith("dir-hover");
  });

  it("does not auto-expand when the directory is already open", () => {
    vi.useFakeTimers();
    const { open, onRequestLoad } = renderRow({
      catalogNode: node({ node_id: "dir-open", title: "Directory", node_kind: "directory", has_children: true }),
      isInternal: true,
      isOpen: true,
      willReceiveDrop: true,
    });

    vi.advanceTimersByTime(500);
    expect(open).not.toHaveBeenCalled();
    expect(onRequestLoad).not.toHaveBeenCalled();
  });

  it("renders a cursor-following drag preview with node metadata", () => {
    const catalogNode = node({ node_id: "point-preview", title: "Preview point", node_kind: "point" });
    const { container } = render(
      <CatalogArboristModernDragPreview
        id="point-preview"
        dragIds={["point-preview"]}
        isDragging
        offset={{ x: 20, y: 40 }}
        mouse={null}
        getNode={() => ({
          id: catalogNode.node_id,
          name: catalogNode.title,
          kind: catalogNode.node_kind,
          catalogNode,
          loaded: true,
          children: null,
        })}
      />,
    );

    expect(screen.getByText("Preview point")).toBeInTheDocument();
    expect(container.querySelector(".catalog-arborist-drag-preview-layer")).toBeInTheDocument();
    expect(container.querySelector(".catalog-arborist-drag-preview")).toHaveStyle({ transform: "translate(28px, 48px)" });
  });
});
