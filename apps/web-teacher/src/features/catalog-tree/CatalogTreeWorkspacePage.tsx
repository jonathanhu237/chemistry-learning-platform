import { useEffect, useMemo, useState } from "react";
import { App as AntApp, Button, Dropdown, Flex, Form, Input, Modal, Radio, Select, Space, Tag, Typography } from "antd";
import { DownOutlined, ReloadOutlined, SearchOutlined } from "@ant-design/icons";
import { ChevronDown, ChevronRight, FlaskConical, Folder, FolderOpen } from "lucide-react";

import { listCatalogChildren, type CatalogNodeCard, type CatalogNodeKind } from "../../api/catalogTree";
import { PageTitle } from "../../components/PageTitle";
import { QueryState } from "../../components/QueryState";
import { formatChapterTitle } from "../../lib/resourceUtils";
import { CatalogTreeEditor } from "./CatalogTreeEditor";
import { useCatalogChildren, useCatalogChapters, useCatalogMutations, useCatalogNodeDetail, useCatalogRoots, useCatalogSearch } from "./catalogTreeHooks";
import { CatalogTreeNodeList } from "./CatalogTreeNodeList";
import {
  buildCatalogNodeCreatePayload,
  catalogNodeKindLabel,
  catalogNodePrimaryStateLabel,
  catalogStatusFilterOptions,
  matchesCatalogNodeStatusFilter,
  resolveCatalogNodeStatus,
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

function kindIcon(kind: CatalogNodeKind) {
  if (kind === "point") return <FlaskConical size={14} />;
  return <Folder size={14} />;
}

function copyKindLabel(kind?: CatalogNodeKind) {
  return kind === "point" ? "实验" : "目录";
}

function copyTitle(title: string) {
  return `${title || "未命名节点"} 副本`;
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
      {tree.length ? renderNodes(tree) : <Text type="secondary">当前章节还没有可选目录，可以复制到章节根目录。</Text>}
    </div>
  );
}

export function CatalogTreeWorkspacePage() {
  const { message } = AntApp.useApp();
  const [chapterId, setChapterId] = useState<string>();
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [searchText, setSearchText] = useState("");
  const [statusFilter, setStatusFilter] = useState<CatalogStatusFilter>("all");
  const [reuseSearchText, setReuseSearchText] = useState("");
  const [copySourceSearchText, setCopySourceSearchText] = useState("");
  const [createIntent, setCreateIntent] = useState<CreateIntent | null>(null);
  const [copyIntent, setCopyIntent] = useState<CopyIntent | null>(null);
  const [copyChapterId, setCopyChapterId] = useState<string>();
  const [copyParentId, setCopyParentId] = useState<string | null>(null);
  const [createForm] = Form.useForm<CatalogNodeFormValues>();
  const [copyForm] = Form.useForm<CopyFormValues>();
  const chapters = useCatalogChapters();
  const roots = useCatalogRoots(chapterId);
  const copyRoots = useCatalogRoots(copyChapterId);
  const selectedDetail = useCatalogNodeDetail(selectedNodeId || undefined);
  const selectedParentId = selectedDetail.data?.node.parent_id || undefined;
  const selectedSiblingChildren = useCatalogChildren(selectedParentId, Boolean(selectedParentId));
  const search = useCatalogSearch(searchText, chapterId, searchText.trim().length >= 2);
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
    setSelectedNodeId(null);
  }, [chapterId]);

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
  const searchItems = useMemo(
    () => (search.data?.items || []).filter((item) => matchesCatalogNodeStatusFilter(item, statusFilter)),
    [search.data?.items, statusFilter],
  );
  const siblingItems = selectedDetail.data?.node.parent_id ? selectedSiblingChildren.data?.children || [] : rootItems;
  const currentChapter = chapters.data?.find((chapter) => chapter.chapter_id === chapterId);
  const currentChapterLabel = currentChapter ? formatChapterTitle(currentChapter.chapter_title, currentChapter.chapter_id) : "未选择章节";
  const nodeStatusSummary = useMemo(() => {
    if (!selectedDetail.data) return null;
    const status = resolveCatalogNodeStatus(selectedDetail.data);
    const color = status.primary_state === "blocked"
      ? "red"
      : ["needs_content", "needs_video", "sync_attention"].includes(status.primary_state)
        ? "gold"
        : status.primary_state === "published"
          ? "green"
          : "default";
    return <Tag color={color}>{status.primary_label || catalogNodePrimaryStateLabel(status.primary_state)}</Tag>;
  }, [selectedDetail.data]);

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
      targetParentId: node.parent_id || null,
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

  const selectNode = (node: CatalogNodeCard) => {
    if (node.chapter_id !== chapterId) setChapterId(node.chapter_id);
    setSelectedNodeId(node.node_id);
  };
  const reusablePointResults = (reuseSearch.data?.items || []).filter((item) => item.node_kind === "point" && item.canonical_point_id);
  const copySourceResults = (copySourceSearch.data?.items || []).filter(
    (item) => item.node_kind === copyIntent?.sourceKind && item.status !== "archived",
  );
  const copyModalTitle =
    copyIntent?.mode === "fixed-source"
      ? `复制当前${copyKindLabel(copyIntent.sourceKind)}`
      : `从已有${copyKindLabel(copyIntent?.sourceKind)}复制到此处`;
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
        description="在当前章节下维护多级目录和视频点位，目录负责分组导航，点位负责学习内容。"
        extra={
          <Space wrap>
            {nodeStatusSummary}
            <Button icon={<ReloadOutlined />} onClick={() => roots.refetch()}>
              刷新
            </Button>
          </Space>
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
          <div className="catalog-tree-filterbar catalog-tree-searchbar">
            <Input
              prefix={<SearchOutlined />}
              value={searchText}
              onChange={(event) => setSearchText(event.target.value)}
              placeholder="搜索目录、点位、教学备注或旧身份"
              allowClear
            />
            <Radio.Group
              className="catalog-status-filter"
              size="small"
              optionType="button"
              buttonStyle="solid"
              value={statusFilter}
              options={catalogStatusFilterOptions}
              onChange={(event) => setStatusFilter(event.target.value as CatalogStatusFilter)}
            />
          </div>
          {searchText.trim().length >= 2 ? (
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
            refreshedChildren={selectedSiblingChildren.data?.children}
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
                      <Text strong>复用已有实验</Text>
                      <Text type="secondary">搜索已有点位，选择后会把同一个实验同步添加到当前目录。</Text>
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
                    label="同步实验 ID（可选）"
                    extra="留空会创建一个新实验；选择或填写已有实验 ID 会把同一个实验添加到当前目录。"
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
                <Text type="secondary">请先搜索并选择一个已有{copyKindLabel(copyIntent?.sourceKind)}作为复制来源。</Text>
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
          <Form.Item name="title" label="副本名称" rules={[{ required: true, message: "请输入副本名称" }]}>
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
