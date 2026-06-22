import { useEffect, useMemo, useRef, useState, type KeyboardEvent, type ReactNode } from "react";
import { App as AntApp, Button, Dropdown, Flex, Form, Input, Modal, Radio, Select, Tag, Typography } from "antd";
import { DownOutlined, SearchOutlined } from "@ant-design/icons";
import { CheckCircle2, ChevronDown, ChevronRight, CircleAlert, CircleDashed, CircleX, FlaskConical, Folder, FolderOpen, RefreshCw, RotateCcw, TriangleAlert } from "lucide-react";

import { listCatalogChildren, type CatalogChapterTreeSummary, type CatalogNodeCard, type CatalogNodeKind, type CatalogSearchMeta, type CatalogSearchResult } from "../../api/catalogTree";
import { PageTitle } from "../../components/PageTitle";
import { QueryState } from "../../components/QueryState";
import { formatChapterTitle } from "../../lib/resourceUtils";
import { CatalogStatusCompositeWarningIcon } from "./CatalogStatusCompositeWarningIcon";
import { CatalogTreeEditor } from "./CatalogTreeEditor";
import {
  useCatalogChapterTreeSummary,
  useCatalogChildren,
  useCatalogChapters,
  useCatalogMutations,
  useCatalogNodeDetail,
  useCatalogRoots,
  useCatalogSearch,
} from "./catalogTreeHooks";
import { CatalogTreeNodeList } from "./CatalogTreeNodeList";
import {
  buildCatalogNodeCreatePayload,
  catalogMissingFieldFilterOptions,
  catalogNodeKindLabel,
  catalogPrimaryStatusFilterOptions,
  catalogStatusFilterCount,
} from "./catalogTreeMappers";
import type { CatalogNodeFormValues, CatalogStatusFilter } from "./catalogTreeMappers";
import "./catalogTree.css";

const { Text } = Typography;

type CreateIntent = {
  parentId?: string | null;
  chapterId: string;
  kind: CatalogNodeKind;
};

type CopyIntent = {
  mode: "fixed-source" | "fixed-target";
  sourceKind: CatalogNodeKind;
  sourceNode?: CatalogNodeCard | null;
  targetChapterId: string;
  targetParentId: string | null;
  targetNode?: CatalogNodeCard | null;
};

type CopyFormValues = {
  title: string;
};

type CopyDestinationNode = {
  node: CatalogNodeCard;
  children: CopyDestinationNode[];
  loaded: boolean;
  open: boolean;
  loading: boolean;
};

function displaySummaryCount(summary: CatalogChapterTreeSummary | undefined, value: number | undefined, loading: boolean): string | number {
  if (summary) return value ?? 0;
  return loading ? "..." : 0;
}

type CatalogStatusVisualTone = "neutral" | "error" | "warning" | "ready" | "success" | "sync";

function catalogStatusVisual(value: CatalogStatusFilter | string): { tone: CatalogStatusVisualTone; icon: ReactNode } {
  if (value === "blocked") return { tone: "error", icon: <CircleX size={13} strokeWidth={2.1} /> };
  if (value === "needs_content" || value === "missing_principle" || value === "missing_phenomenon" || value === "missing_safety") {
    return { tone: "warning", icon: <CatalogStatusCompositeWarningIcon kind="content" size={14} strokeWidth={2.1} /> };
  }
  if (value === "needs_video") {
    return { tone: "warning", icon: <CatalogStatusCompositeWarningIcon kind="video" size={14} strokeWidth={2.1} /> };
  }
  if (value === "unpublished") return { tone: "ready", icon: <CircleAlert size={13} strokeWidth={2.1} /> };
  if (value === "published") return { tone: "success", icon: <CheckCircle2 size={13} strokeWidth={2.1} /> };
  if (value === "sync_attention") return { tone: "sync", icon: <RefreshCw size={13} strokeWidth={2.1} /> };
  if (value === "actionable") return { tone: "warning", icon: <TriangleAlert size={13} strokeWidth={2.1} /> };
  return { tone: "neutral", icon: <CircleDashed size={13} strokeWidth={2.1} /> };
}

function CatalogTreeOverview({ summary, loading }: { summary?: CatalogChapterTreeSummary; loading: boolean }) {
  const pointCounts = summary?.point_status_counts || {};
  const statusItems = [
    { key: "blocked", label: "异常", value: Number(pointCounts.blocked || 0), tone: "error" },
    { key: "needs_content", label: "缺内容", value: Number(pointCounts.needs_content || 0), tone: "warning" },
    { key: "needs_video", label: "缺视频", value: Number(pointCounts.needs_video || 0), tone: "warning" },
    { key: "unpublished", label: "待发布", value: Number(pointCounts.ready || 0) + Number(pointCounts.draft || 0), tone: "ready" },
    { key: "published", label: "已发布", value: Number(pointCounts.published || 0), tone: "success" },
    { key: "sync_attention", label: "同步异常", value: Number(pointCounts.sync_attention || 0), tone: "sync" },
  ];
  const primaryStats = [
    { label: "目录", value: displaySummaryCount(summary, summary?.directory_count, loading) },
    { label: "点位", value: displaySummaryCount(summary, summary?.point_count, loading) },
    { label: "已发布", value: displaySummaryCount(summary, Number(pointCounts.published || 0), loading) },
    { label: "待处理", value: displaySummaryCount(summary, summary?.actionable_point_count, loading) },
  ];

  return (
    <section className="catalog-tree-overview" aria-label="章节资源统计">
      <div className="catalog-tree-overview-main">
        {primaryStats.map((item) => (
          <div key={item.label} className="catalog-tree-overview-stat">
            <span>{item.label}</span>
            <strong>{item.value}</strong>
          </div>
        ))}
      </div>
      <div className="catalog-tree-overview-statuses" aria-label="点位状态统计">
        {statusItems.map((item) => (
          <Tag key={item.key} className={`catalog-tree-overview-chip is-${item.tone}`}>
            <span className="catalog-status-chip-icon" aria-hidden="true">{catalogStatusVisual(item.key).icon}</span>
            <span>{item.label}</span>
            <strong>{summary ? item.value : loading ? "..." : 0}</strong>
          </Tag>
        ))}
      </div>
    </section>
  );
}

function CatalogStatusFilterBar({
  value,
  summary,
  onChange,
}: {
  value: CatalogStatusFilter;
  summary?: CatalogChapterTreeSummary;
  onChange: (value: CatalogStatusFilter) => void;
}) {
  const renderChip = (option: { value: CatalogStatusFilter; label: string }, variant: "primary" | "secondary" = "primary") => {
    const count = catalogStatusFilterCount(summary, option.value);
    const selected = value === option.value;
    return (
      <button
        key={option.value}
        type="button"
        role="radio"
        aria-checked={selected}
        className={`catalog-status-filter-chip${selected ? " is-active" : ""}${variant === "secondary" ? " is-secondary" : ""}`}
        onClick={() => onChange(option.value)}
      >
        <span>{option.label}</span>
        {count !== null ? <strong>{count}</strong> : null}
      </button>
    );
  };
  return (
    <div className="catalog-status-filter" role="radiogroup" aria-label="点位状态筛选">
      <div className="catalog-status-filter-row">{catalogPrimaryStatusFilterOptions.map((option) => renderChip(option))}</div>
      <div className="catalog-status-filter-row is-secondary">{catalogMissingFieldFilterOptions.map((option) => renderChip(option, "secondary"))}</div>
    </div>
  );
}

function kindIcon(kind: CatalogNodeKind) {
  if (kind === "point") return <FlaskConical size={14} />;
  return <Folder size={14} />;
}

function searchBackendNotice(meta?: CatalogSearchMeta) {
  if (!meta) return "";
  if (meta.backend === "postgres_fallback") return "有限搜索：ES 暂不可用，当前结果不包含同义词和结构化化学召回。";
  if (meta.stale_hit_count) return `已隐藏 ${meta.stale_hit_count} 个过期搜索命中。`;
  return "";
}

type CatalogSearchOverlayGroup = {
  key: string;
  label: string;
  hint: string;
  entries: Array<{ item: CatalogSearchResult; index: number }>;
  emptyText?: string;
};

function searchScope(item: CatalogSearchResult) {
  return item.search_scope || item.search_match?.search_scope || "all";
}

function groupSearchItemsByScope(items: CatalogSearchResult[], meta?: CatalogSearchMeta): CatalogSearchOverlayGroup[] {
  const buckets: Record<string, CatalogSearchOverlayGroup["entries"]> = {
    current_chapter: [],
    other_chapter: [],
    all: [],
  };
  items.forEach((item, index) => {
    const scope = searchScope(item);
    if (scope === "other_chapter") {
      buckets.other_chapter.push({ item, index });
      return;
    }
    if (scope === "current_chapter") {
      buckets.current_chapter.push({ item, index });
      return;
    }
    buckets.all.push({ item, index });
  });
  const countLabel = (scope: string, count: number) => {
    const total = meta?.scope_totals?.[scope];
    return total && total > count ? `${count}/${total}` : String(count);
  };
  const groups: CatalogSearchOverlayGroup[] = [];
  const showCurrentChapterEmpty = Boolean(meta?.cross_chapter_enabled && !buckets.current_chapter.length && buckets.other_chapter.length);
  if (buckets.current_chapter.length || showCurrentChapterEmpty) {
    groups.push({
      key: "current_chapter",
      label: "本章",
      hint: `${countLabel("current_chapter", buckets.current_chapter.length)} 个结果`,
      entries: buckets.current_chapter,
      emptyText: showCurrentChapterEmpty ? "本章暂无匹配，以下为跨章结果" : undefined,
    });
  }
  if (buckets.other_chapter.length) {
    groups.push({
      key: "other_chapter",
      label: "跨章",
      hint: `${countLabel("other_chapter", buckets.other_chapter.length)} 个结果`,
      entries: buckets.other_chapter,
    });
  }
  if (buckets.all.length) {
    groups.push({
      key: "all",
      label: "结果",
      hint: `${countLabel("all", buckets.all.length)} 个结果`,
      entries: buckets.all,
    });
  }
  return groups;
}

function CatalogSearchOverlay({
  open,
  queryReady,
  loading,
  error,
  items,
  meta,
  activeIndex,
  selectedNodeId,
  onActiveIndex,
  onSelect,
}: {
  open: boolean;
  queryReady: boolean;
  loading: boolean;
  error: unknown;
  items: CatalogSearchResult[];
  meta?: CatalogSearchMeta;
  activeIndex: number;
  selectedNodeId?: string | null;
  onActiveIndex: (index: number) => void;
  onSelect: (item: CatalogSearchResult) => void;
}) {
  if (!open || !queryReady) return null;
  const notice = searchBackendNotice(meta);
  const groups = groupSearchItemsByScope(items, meta);
  return (
    <div className="catalog-search-overlay" role="listbox" aria-label="目录搜索结果">
      {notice ? <div className="catalog-search-overlay-notice">{notice}</div> : null}
      {loading ? <div className="catalog-search-overlay-state">正在搜索...</div> : null}
      {!loading && error ? <div className="catalog-search-overlay-state is-error">搜索暂时失败，请稍后重试。</div> : null}
      {!loading && !error && !items.length ? <div className="catalog-search-overlay-state">没有匹配结果。</div> : null}
      {!loading && !error && groups.length ? (
        <div className="catalog-search-overlay-list">
          {groups.map((group) => (
            <section key={group.key} className="catalog-search-overlay-section" aria-label={group.label}>
              <div className="catalog-search-overlay-section-header">
                <span>{group.label}</span>
                <em>{group.hint}</em>
              </div>
              {!group.entries.length && group.emptyText ? <div className="catalog-search-overlay-empty-row">{group.emptyText}</div> : null}
              {group.entries.map(({ item, index }) => {
                const statusLabel = item.node_status?.primary_label || item.node_status?.primary_state || item.status;
                const breadcrumb = item.breadcrumb_path || (item.breadcrumbs || []).map((entry) => entry.title).join(" / ");
                return (
                  <button
                    key={`${group.key}:${item.node_id}:${index}`}
                    type="button"
                    role="option"
                    aria-selected={selectedNodeId === item.node_id || activeIndex === index}
                    className={`catalog-search-overlay-row${activeIndex === index ? " is-active" : ""}${selectedNodeId === item.node_id ? " is-selected" : ""}`}
                    onMouseEnter={() => onActiveIndex(index)}
                    onClick={() => onSelect(item)}
                  >
                    <span className="catalog-search-overlay-kind" aria-hidden="true">{kindIcon(item.node_kind)}</span>
                    <span className="catalog-search-overlay-main">
                      <span className="catalog-search-overlay-title">{item.title}</span>
                      <span className="catalog-search-overlay-breadcrumb">{breadcrumb || catalogNodeKindLabel(item.node_kind)}</span>
                    </span>
                    {item.search_match?.field_label ? <span className="catalog-search-overlay-match">{item.search_match.field_label}</span> : null}
                    <span className={`catalog-search-overlay-status is-${item.node_status?.primary_state || item.status}`}>{statusLabel}</span>
                  </button>
                );
              })}
            </section>
          ))}
        </div>
      ) : null}
      {meta?.limited ? <div className="catalog-search-overlay-footer">只显示前 {items.length} 个结果，请继续输入以缩小范围。</div> : null}
    </div>
  );
}

function copyKindLabel(kind?: CatalogNodeKind) {
  return kind === "point" ? "实验" : "目录";
}

function copyOperationVerb(kind?: CatalogNodeKind) {
  return kind === "point" ? "引用" : "复制";
}

function copyTitle(title: string) {
  return title || "未命名节点";
}

function toCopyDestinationNodes(nodes: CatalogNodeCard[]): CopyDestinationNode[] {
  return nodes
    .filter((node) => node.node_kind === "directory")
    .map((node) => ({
      node,
      children: [],
      loaded: false,
      open: false,
      loading: false,
    }));
}

function updateCopyDestinationNode(
  nodes: CopyDestinationNode[],
  nodeId: string,
  updater: (node: CopyDestinationNode) => CopyDestinationNode,
): CopyDestinationNode[] {
  return nodes.map((node) => {
    if (node.node.node_id === nodeId) return updater(node);
    return { ...node, children: updateCopyDestinationNode(node.children, nodeId, updater) };
  });
}

function CatalogCopyDestinationTree({
  chapterId,
  roots,
  selectedParentId,
  onSelectParent,
}: {
  chapterId?: string;
  roots: CatalogNodeCard[];
  selectedParentId: string | null;
  onSelectParent: (parentId: string | null) => void;
}) {
  const { message } = AntApp.useApp();
  const [tree, setTree] = useState<CopyDestinationNode[]>([]);

  useEffect(() => {
    setTree(toCopyDestinationNodes(roots));
  }, [chapterId, roots]);

  const toggleDirectory = async (target: CopyDestinationNode) => {
    if (target.loaded) {
      setTree((existing) =>
        updateCopyDestinationNode(existing, target.node.node_id, (node) => ({
          ...node,
          open: !node.open,
        })),
      );
      return;
    }
    setTree((existing) =>
      updateCopyDestinationNode(existing, target.node.node_id, (node) => ({
        ...node,
        loading: true,
        open: true,
      })),
    );
    try {
      const response = await listCatalogChildren(target.node.node_id);
      setTree((existing) =>
        updateCopyDestinationNode(existing, target.node.node_id, (node) => ({
          ...node,
          children: toCopyDestinationNodes(response.children),
          loaded: true,
          loading: false,
          open: true,
        })),
      );
    } catch {
      message.error("目标目录加载失败");
      setTree((existing) =>
        updateCopyDestinationNode(existing, target.node.node_id, (node) => ({
          ...node,
          loading: false,
        })),
      );
    }
  };

  const renderNodes = (items: CopyDestinationNode[], depth = 0) =>
    items.map((item) => (
      <div key={item.node.node_id}>
        <div className={`catalog-copy-target-row ${selectedParentId === item.node.node_id ? "is-selected" : ""}`} style={{ paddingLeft: 10 + depth * 18 }}>
          <Button
            type="text"
            size="small"
            className="catalog-copy-target-toggle"
            icon={item.open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
            loading={item.loading}
            onClick={() => void toggleDirectory(item)}
            aria-label={item.open ? "收起目录" : "展开目录"}
          />
          <button type="button" className="catalog-copy-target-button" onClick={() => onSelectParent(item.node.node_id)}>
            <span className="catalog-copy-target-icon">{item.open ? <FolderOpen size={16} /> : <Folder size={16} />}</span>
            <span>{item.node.title}</span>
          </button>
        </div>
        {item.open && item.children.length ? renderNodes(item.children, depth + 1) : null}
      </div>
    ));

  return (
    <div className="catalog-copy-target-tree">
      <button
        type="button"
        className={`catalog-copy-root-target ${selectedParentId === null ? "is-selected" : ""}`}
        onClick={() => onSelectParent(null)}
      >
        <Folder size={16} />
        <span>章节根目录</span>
      </button>
      {tree.length ? renderNodes(tree) : <Text type="secondary">当前章节还没有可选目录，可以放到章节根目录。</Text>}
    </div>
  );
}

export function CatalogTreeWorkspacePage() {
  const { message } = AntApp.useApp();
  const [chapterId, setChapterId] = useState<string>();
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [searchText, setSearchText] = useState("");
  const [statusFilter, setStatusFilter] = useState<CatalogStatusFilter>("all");
  const [searchOverlayOpen, setSearchOverlayOpen] = useState(false);
  const [activeSearchIndex, setActiveSearchIndex] = useState(0);
  const [searchReveal, setSearchReveal] = useState<{ nodeId: string; pathIds: string[]; version: number } | null>(null);
  const [reuseSearchText, setReuseSearchText] = useState("");
  const [copySourceSearchText, setCopySourceSearchText] = useState("");
  const [createIntent, setCreateIntent] = useState<CreateIntent | null>(null);
  const [copyIntent, setCopyIntent] = useState<CopyIntent | null>(null);
  const [copyChapterId, setCopyChapterId] = useState<string>();
  const [copyParentId, setCopyParentId] = useState<string | null>(null);
  const [workspaceResetVersion, setWorkspaceResetVersion] = useState(0);
  const searchBoxRef = useRef<HTMLDivElement | null>(null);
  const [createForm] = Form.useForm<CatalogNodeFormValues>();
  const [copyForm] = Form.useForm<CopyFormValues>();
  const chapters = useCatalogChapters();
  const roots = useCatalogRoots(chapterId);
  const chapterSummary = useCatalogChapterTreeSummary(chapterId);
  const copyRoots = useCatalogRoots(copyChapterId);
  const selectedDetail = useCatalogNodeDetail(selectedNodeId || undefined);
  const selectedParentId = selectedDetail.data?.node.parent_id || undefined;
  const selectedSiblingChildren = useCatalogChildren(selectedParentId, Boolean(selectedParentId));
  const selectedBranchDirectoryIds = useMemo(
    () => (selectedDetail.data?.breadcrumbs || []).filter((item) => item.node_kind === "directory").map((item) => item.node_id),
    [selectedDetail.data?.breadcrumbs],
  );
  const searchReady = searchText.trim().length >= 2;
  const search = useCatalogSearch(searchText, chapterId, searchReady, statusFilter);
  const reuseSearch = useCatalogSearch(
    reuseSearchText,
    null,
    Boolean(createIntent?.kind === "point" && reuseSearchText.trim().length >= 2),
  );
  const copySourceSearch = useCatalogSearch(
    copySourceSearchText,
    null,
    Boolean(copyIntent?.mode === "fixed-target" && copySourceSearchText.trim().length >= 2),
  );
  const mutations = useCatalogMutations(message);

  useEffect(() => {
    if (!chapterId && chapters.data?.length) {
      setChapterId(chapters.data.find((chapter) => chapter.chapter_id !== "CH00")?.chapter_id || chapters.data[0].chapter_id);
    }
  }, [chapterId, chapters.data]);

  useEffect(() => {
    if (searchReveal?.nodeId) return;
    setSelectedNodeId(null);
    setSearchText("");
    setSearchOverlayOpen(false);
    setActiveSearchIndex(0);
  }, [chapterId, searchReveal?.nodeId]);

  useEffect(() => {
    if (!searchReady) {
      setSearchOverlayOpen(false);
      setActiveSearchIndex(0);
      return;
    }
    setSearchOverlayOpen(true);
    setActiveSearchIndex(0);
  }, [chapterId, searchReady, searchText, statusFilter]);

  useEffect(() => {
    const handlePointerDown = (event: MouseEvent) => {
      if (!searchBoxRef.current) return;
      if (searchBoxRef.current.contains(event.target as Node)) return;
      setSearchOverlayOpen(false);
    };
    document.addEventListener("mousedown", handlePointerDown);
    return () => document.removeEventListener("mousedown", handlePointerDown);
  }, []);

  useEffect(() => {
    if (createIntent) {
      createForm.setFieldsValue({
        title: "",
        summary: "",
        node_kind: createIntent.kind,
        canonical_point_id: "",
        teacher_note: "",
      });
    }
  }, [createForm, createIntent]);

  useEffect(() => {
    if (!copyIntent) return;
    setCopyChapterId(copyIntent.targetChapterId);
    setCopyParentId(copyIntent.targetParentId);
    copyForm.setFieldsValue({ title: copyIntent.sourceNode ? copyTitle(copyIntent.sourceNode.title) : "" });
  }, [copyForm, copyIntent]);

  const chapterOptions = (chapters.data || []).map((chapter) => ({
    value: chapter.chapter_id,
    label: formatChapterTitle(chapter.chapter_title, chapter.chapter_id),
  }));
  const chapterMenuItems = chapterOptions.map((chapter) => ({
    key: chapter.value,
    label: chapter.label,
  }));
  const rootItems = roots.data?.nodes || [];
  const searchItems = search.data?.items || [];
  useEffect(() => {
    if (!searchItems.length) {
      setActiveSearchIndex(0);
      return;
    }
    setActiveSearchIndex((index) => Math.min(index, searchItems.length - 1));
  }, [searchItems.length]);
  const siblingItems = selectedDetail.data?.node.parent_id ? selectedSiblingChildren.data?.children || [] : rootItems;
  const currentChapter = chapters.data?.find((chapter) => chapter.chapter_id === chapterId);
  const currentChapterLabel = currentChapter ? formatChapterTitle(currentChapter.chapter_title, currentChapter.chapter_id) : "未选择章节";

  const resetWorkspace = () => {
    setSelectedNodeId(null);
    setSearchText("");
    setStatusFilter("all");
    setReuseSearchText("");
    setCopySourceSearchText("");
    setCreateIntent(null);
    setCopyIntent(null);
    setCopyChapterId(undefined);
    setCopyParentId(null);
    createForm.resetFields();
    copyForm.resetFields();
    setWorkspaceResetVersion((version) => version + 1);
  };

  const openCreate = (kind: CatalogNodeKind, parentId?: string | null) => {
    if (!chapterId) return;
    setReuseSearchText("");
    setCreateIntent({ chapterId, parentId: parentId || null, kind });
  };

  const openCopy = (node: CatalogNodeCard) => {
    setCopySourceSearchText("");
    copyForm.resetFields();
    setCopyIntent({
      mode: "fixed-source",
      sourceKind: node.node_kind,
      sourceNode: node,
      targetChapterId: node.chapter_id,
      targetParentId: node.node_kind === "point" ? null : node.parent_id || null,
    });
  };

  const openCopyInto = (parentNode: CatalogNodeCard | null, kind: CatalogNodeKind) => {
    const targetChapterId = parentNode?.chapter_id || chapterId;
    if (!targetChapterId) return;
    setCopySourceSearchText("");
    copyForm.resetFields();
    setCopyIntent({
      mode: "fixed-target",
      sourceKind: kind,
      sourceNode: null,
      targetChapterId,
      targetParentId: parentNode?.node_id || null,
      targetNode: parentNode,
    });
  };

  const closeCopy = () => {
    setCopyIntent(null);
    setCopySourceSearchText("");
    copyForm.resetFields();
  };

  const selectCopySource = (node: CatalogNodeCard) => {
    setCopyIntent((previous) =>
      previous
        ? { ...previous, sourceKind: node.node_kind, sourceNode: node }
        : {
            mode: "fixed-source",
            sourceKind: node.node_kind,
            sourceNode: node,
            targetChapterId: node.chapter_id,
            targetParentId: node.parent_id || null,
          },
    );
    copyForm.setFieldsValue({ title: copyTitle(node.title) });
  };

  const submitCreate = async () => {
    if (!createIntent) return;
    const values = await createForm.validateFields();
    mutations.createNode.mutate(buildCatalogNodeCreatePayload(values, createIntent.chapterId, createIntent.parentId), {
      onSuccess: (detail) => {
        setSelectedNodeId(detail.node.node_id);
        setCreateIntent(null);
      },
    });
  };

  const submitCopy = async () => {
    if (!copyIntent?.sourceNode || !copyChapterId) return;
    const values = await copyForm.validateFields();
    try {
      const detail = await mutations.copyNode.mutateAsync({
        nodeId: copyIntent.sourceNode.node_id,
        payload: {
          chapter_id: copyChapterId,
          parent_id: copyParentId,
          title: values.title,
          include_subtree: true,
        },
      });
      closeCopy();
      setChapterId(detail.node.chapter_id);
      setSelectedNodeId(detail.node.node_id);
    } catch {
      // Mutation already reports the user-facing error.
    }
  };

  const selectNode = (node: CatalogNodeCard, revealPathIds?: string[]) => {
    if (node.chapter_id !== chapterId) setChapterId(node.chapter_id);
    setSelectedNodeId(node.node_id);
    if (revealPathIds?.length) {
      setSearchReveal({ nodeId: node.node_id, pathIds: revealPathIds, version: Date.now() });
    }
  };
  const selectSearchResult = (node: CatalogSearchResult) => {
    const pathIds = (node.breadcrumbs || []).map((item) => item.node_id);
    setSearchOverlayOpen(false);
    selectNode(node, pathIds);
  };
  const handleSearchKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (!searchOverlayOpen || !searchReady) return;
    if (event.key === "Escape") {
      setSearchOverlayOpen(false);
      return;
    }
    if (!searchItems.length) return;
    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveSearchIndex((index) => Math.min(index + 1, searchItems.length - 1));
      return;
    }
    if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveSearchIndex((index) => Math.max(index - 1, 0));
      return;
    }
    if (event.key === "Enter") {
      event.preventDefault();
      selectSearchResult(searchItems[Math.min(activeSearchIndex, searchItems.length - 1)]);
    }
  };
  const reusablePointResults = (reuseSearch.data?.items || []).filter((item) => item.node_kind === "point" && item.canonical_point_id);
  const copySourceResults = (copySourceSearch.data?.items || []).filter(
    (item) => item.node_kind === copyIntent?.sourceKind && item.status !== "archived",
  );
  const copyModalTitle =
    copyIntent?.mode === "fixed-source"
      ? `${copyOperationVerb(copyIntent.sourceKind)}当前${copyKindLabel(copyIntent.sourceKind)}`
      : `从已有${copyKindLabel(copyIntent?.sourceKind)}${copyOperationVerb(copyIntent?.sourceKind)}到此处`;
  const copySemanticsNote =
    copyIntent?.sourceKind === "point"
      ? "引用实验会在目标目录新增一个点位入口，复用同一个实验身份和视频资源；内容、视频后续统一管理，不会生成新的实验身份。"
      : "复制目录会创建新的目录结构；目录中的实验点位会以引用方式复用原实验身份，内容和视频后续统一管理。";
  const copySourceLocked = copyIntent?.mode === "fixed-source";
  const copyTargetLocked = copyIntent?.mode === "fixed-target";
  const sourceSearchReady = copySourceSearchText.trim().length >= 2;
  const formatCopyNodeChapter = (node: CatalogNodeCard) => {
    const chapter = chapters.data?.find((candidate) => candidate.chapter_id === node.chapter_id);
    return chapter ? formatChapterTitle(chapter.chapter_title, chapter.chapter_id) : node.chapter_id;
  };
  const copyTargetChapterLabel = (() => {
    const targetChapter = chapters.data?.find((candidate) => candidate.chapter_id === copyChapterId);
    return targetChapter ? formatChapterTitle(targetChapter.chapter_title, targetChapter.chapter_id) : copyChapterId || "";
  })();
  const selectReusablePoint = (item: CatalogNodeCard) => {
    createForm.setFieldsValue({
      title: item.canonical_point_title || item.title,
      canonical_point_id: item.canonical_point_id || "",
    });
  };

  return (
    <div className="catalog-workspace">
      <PageTitle
        title="章节目录与点位工作台"
        description="在当前章节下维护多级目录和视频点位，目录负责分组导航，点位负责学习内容。一个视频点位唯一对应一个视频资源；如需让同一视频在多个目录中统一管理，请引用已有点位，不要新建节点。"
        extra={
          <Button icon={<RotateCcw size={16} />} onClick={resetWorkspace}>
            重置工作台
          </Button>
        }
      />

      <div className="catalog-workspace-grid">
        <aside className="catalog-tree-panel">
          <Flex align="center" justify="space-between" className="catalog-panel-heading">
            <div className="catalog-chapter-heading-copy">
              <Text type="secondary">当前章节</Text>
              <Dropdown
                trigger={["click"]}
                disabled={chapters.isLoading || !chapterMenuItems.length}
                menu={{
                  items: chapterMenuItems,
                  selectedKeys: chapterId ? [chapterId] : [],
                  onClick: ({ key }) => setChapterId(String(key)),
                }}
              >
                <button
                  type="button"
                  className="catalog-chapter-switcher"
                  aria-label="切换当前章节"
                  title={chapters.isLoading ? "章节加载中" : "切换当前章节"}
                >
                  <span>{currentChapterLabel}</span>
                  <DownOutlined />
                </button>
              </Dropdown>
            </div>
          </Flex>
          <CatalogTreeOverview summary={chapterSummary.data} loading={chapterSummary.isFetching} />
          <div className="catalog-tree-filterbar catalog-tree-searchbar" ref={searchBoxRef}>
            <div className="catalog-tree-searchbox">
              <Input
              prefix={<SearchOutlined />}
              value={searchText}
              onFocus={() => {
                if (searchReady) setSearchOverlayOpen(true);
              }}
              onChange={(event) => setSearchText(event.target.value)}
              onKeyDown={handleSearchKeyDown}
              placeholder="搜索标题、实验内容、教学备注、旧实验 ID"
              allowClear
            />
              <CatalogSearchOverlay
                open={searchOverlayOpen}
                queryReady={searchReady}
                loading={search.isFetching}
                error={search.error}
                items={searchItems}
                meta={search.data?.meta}
                activeIndex={activeSearchIndex}
                selectedNodeId={selectedNodeId}
                onActiveIndex={setActiveSearchIndex}
                onSelect={selectSearchResult}
              />
            </div>
            <CatalogStatusFilterBar value={statusFilter} summary={chapterSummary.data} onChange={setStatusFilter} />
          </div>
          {false && searchText.trim().length >= 2 ? (
            <div className="catalog-search-results catalog-tree-search-results">
              <QueryState loading={search.isFetching} error={search.error} empty={!searchItems.length}>
                <Flex gap={8} wrap>
                  {searchItems.map((item) => (
                    <Button
                      key={item.node_id}
                      icon={kindIcon(item.node_kind)}
                      onClick={() => selectNode(item)}
                      className={selectedNodeId === item.node_id ? "is-selected-search" : ""}
                    >
                      {item.title}
                      <Text type="secondary"> · {catalogNodeKindLabel(item.node_kind)}</Text>
                    </Button>
                  ))}
                </Flex>
              </QueryState>
            </div>
          ) : null}
          <CatalogTreeNodeList
            nodes={rootItems}
            treeScopeKey={chapterId || ""}
            resetVersion={workspaceResetVersion}
            selectedNodeId={selectedNodeId}
            loading={roots.isLoading}
            error={roots.error}
            onSelect={selectNode}
            onAddRoot={(kind) => openCreate(kind)}
            onAddChild={(node, kind = "directory") => openCreate(kind, node.node_id)}
            onCopyInto={openCopyInto}
            onCopyNode={openCopy}
            onMove={(nodeId, payload) => mutations.moveNode.mutateAsync({ nodeId, payload })}
            onReorder={(items) => mutations.reorderNodes.mutateAsync(items)}
            onRefreshRoots={() => roots.refetch()}
            onChangeStatus={(node, action) => mutations.changeNodeStatus.mutate({ nodeId: node.node_id, action })}
            statusFilter={statusFilter}
            refreshedChildrenParentId={selectedParentId}
            refreshedParent={selectedSiblingChildren.data?.parent}
            refreshedChildren={selectedSiblingChildren.data?.children}
            branchRefreshVersion={selectedDetail.dataUpdatedAt}
            branchRefreshDirectoryIds={selectedBranchDirectoryIds}
            revealNodeId={searchReveal?.nodeId}
            revealPathIds={searchReveal?.pathIds || []}
            revealVersion={searchReveal?.version || 0}
          />
        </aside>

        <main className="catalog-editor-panel">
          <CatalogTreeEditor
            detail={selectedDetail.data}
            loading={selectedDetail.isLoading}
            error={selectedDetail.error}
            siblings={siblingItems}
            onSelectNode={setSelectedNodeId}
            mutations={mutations}
          />
        </main>
      </div>

      <Modal
        title={createIntent?.parentId ? "新增子节点" : "添加到本章"}
        open={Boolean(createIntent)}
        onCancel={() => setCreateIntent(null)}
        onOk={submitCreate}
        okButtonProps={{ loading: mutations.createNode.isPending }}
        forceRender
        destroyOnHidden
      >
        <Form form={createForm} layout="vertical">
          <Form.Item name="title" label="节点标题" rules={[{ required: true, message: "请输入节点标题" }]}>
            <Input autoFocus />
          </Form.Item>
          <Form.Item name="node_kind" label="节点类型" rules={[{ required: true }]}>
            <Radio.Group optionType="button" buttonStyle="solid">
              <Radio.Button value="directory">目录</Radio.Button>
              <Radio.Button value="point">点位</Radio.Button>
            </Radio.Group>
          </Form.Item>
          <Form.Item
            noStyle
            shouldUpdate={(previous, current) => previous.node_kind !== current.node_kind}
          >
            {({ getFieldValue }) =>
              getFieldValue("node_kind") === "point" ? (
                <>
                  <div className="catalog-reuse-picker">
                    <div className="catalog-reuse-picker-copy">
                      <Text strong>引用已有实验</Text>
                      <Text type="secondary">搜索已有点位，选择后会把同一个实验引用到当前目录。</Text>
                    </div>
                    <Input.Search
                      value={reuseSearchText}
                      onChange={(event) => setReuseSearchText(event.target.value)}
                      onSearch={setReuseSearchText}
                      placeholder="搜索已有实验名称或目录路径"
                      allowClear
                    />
                    {reuseSearchText.trim().length >= 2 ? (
                      <QueryState loading={reuseSearch.isFetching} error={reuseSearch.error} empty={!reusablePointResults.length}>
                        <div className="catalog-reuse-result-list">
                          {reusablePointResults.slice(0, 8).map((item) => (
                            <button
                              key={item.node_id}
                              type="button"
                              className="catalog-reuse-result-button"
                              onClick={() => selectReusablePoint(item)}
                            >
                              <span>{item.canonical_point_title || item.title}</span>
                              <Text type="secondary">{item.chapter_id}</Text>
                              <Tag>{item.active_placement_count ? `${item.active_placement_count} 个位置` : "单位置"}</Tag>
                            </button>
                          ))}
                        </div>
                      </QueryState>
                    ) : null}
                  </div>
                  <Form.Item
                    name="canonical_point_id"
                    label="引用实验 ID（可选）"
                    extra="留空会创建一个新实验；选择或填写已有实验 ID 会把同一个实验引用到当前目录。"
                  >
                    <Input placeholder="cat-canon-..." />
                  </Form.Item>
                </>
              ) : null
            }
          </Form.Item>
          <Form.Item
            name="teacher_note"
            label="教学备注"
            extra="仅教师端可见，不进入学生端、学生搜索或题目证据链。"
          >
            <Input.TextArea autoSize={{ minRows: 2, maxRows: 4 }} />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={copyModalTitle}
        open={Boolean(copyIntent)}
        onCancel={closeCopy}
        onOk={submitCopy}
        okButtonProps={{ loading: mutations.copyNode.isPending, disabled: !copyChapterId || !copyIntent?.sourceNode }}
        destroyOnHidden
        width={760}
      >
        <Form form={copyForm} layout="vertical">
          <div className={`catalog-copy-semantics-note ${copyIntent?.sourceKind === "point" ? "is-point" : "is-directory"}`}>
            {copySemanticsNote}
          </div>
          <Form.Item label={`来源${copyKindLabel(copyIntent?.sourceKind)}`} required>
            <div className="catalog-copy-source-picker">
              {copyIntent?.sourceNode ? (
                <div className="catalog-copy-source-card">
                  <span className="catalog-copy-target-icon">{kindIcon(copyIntent.sourceNode.node_kind)}</span>
                  <div className="catalog-copy-source-copy">
                    <strong>{copyIntent.sourceNode.title}</strong>
                    <Text type="secondary">{formatCopyNodeChapter(copyIntent.sourceNode)}</Text>
                  </div>
                  <Tag>{catalogNodeKindLabel(copyIntent.sourceNode.node_kind)}</Tag>
                </div>
              ) : (
                <Text type="secondary">请先搜索并选择一个已有{copyKindLabel(copyIntent?.sourceKind)}作为{copyOperationVerb(copyIntent?.sourceKind)}来源。</Text>
              )}
              {copySourceLocked ? null : (
                <>
                  <Input.Search
                    value={copySourceSearchText}
                    onChange={(event) => setCopySourceSearchText(event.target.value)}
                    onSearch={setCopySourceSearchText}
                    placeholder={`搜索已有${copyKindLabel(copyIntent?.sourceKind)}名称`}
                    allowClear
                    autoFocus={!copyIntent?.sourceNode}
                  />
                  {sourceSearchReady ? (
                    <QueryState loading={copySourceSearch.isFetching} error={copySourceSearch.error} empty={!copySourceResults.length}>
                      <div className="catalog-copy-source-results">
                        {copySourceResults.slice(0, 10).map((item) => (
                          <button
                            key={item.node_id}
                            type="button"
                            className={
                              item.node_id === copyIntent?.sourceNode?.node_id ? "catalog-copy-source-result is-selected" : "catalog-copy-source-result"
                            }
                            onClick={() => selectCopySource(item)}
                          >
                            <span className="catalog-copy-target-icon">{kindIcon(item.node_kind)}</span>
                            <span className="catalog-copy-source-result-main">
                              <strong>{item.title}</strong>
                              <Text type="secondary">{formatCopyNodeChapter(item)}</Text>
                            </span>
                            <Tag>{catalogNodeKindLabel(item.node_kind)}</Tag>
                          </button>
                        ))}
                      </div>
                    </QueryState>
                  ) : null}
                </>
              )}
            </div>
          </Form.Item>
          <Form.Item name="title" label="节点名称" rules={[{ required: true, message: "请输入节点名称" }]}>
            <Input autoFocus={Boolean(copyIntent?.sourceNode)} />
          </Form.Item>
          {copyTargetLocked ? (
            <Form.Item label="目标位置">
              <div className="catalog-copy-source-card catalog-copy-fixed-target-card">
                <span className="catalog-copy-target-icon"><Folder size={14} /></span>
                <div className="catalog-copy-source-copy">
                  <strong>{copyIntent?.targetNode?.title || "章节根目录"}</strong>
                  <Text type="secondary">{copyTargetChapterLabel}</Text>
                </div>
                <Tag>{copyIntent?.targetNode ? "目录" : "本章根目录"}</Tag>
              </div>
            </Form.Item>
          ) : (
            <>
              <Form.Item label="目标章节">
                <Select
                  value={copyChapterId}
                  options={chapterOptions}
                  onChange={(value) => {
                    setCopyChapterId(value);
                    setCopyParentId(null);
                  }}
                />
              </Form.Item>
              <Form.Item label="目标目录">
                <QueryState loading={copyRoots.isLoading} error={copyRoots.error} empty={false}>
                  <CatalogCopyDestinationTree
                    chapterId={copyChapterId}
                    roots={copyRoots.data?.nodes || []}
                    selectedParentId={copyParentId}
                    onSelectParent={setCopyParentId}
                  />
                </QueryState>
              </Form.Item>
            </>
          )}
        </Form>
      </Modal>
    </div>
  );
}
