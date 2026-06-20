import { useEffect, useMemo, useState } from "react";
import { App as AntApp, Button, Flex, Form, Input, Modal, Radio, Select, Space, Tag, Typography } from "antd";
import { BranchesOutlined, FileTextOutlined, FolderOpenOutlined, LinkOutlined, PlusOutlined, ReloadOutlined, SearchOutlined } from "@ant-design/icons";

import type { CatalogNodeCard, CatalogNodeKind } from "../../api/catalogTree";
import { PageTitle } from "../../components/PageTitle";
import { QueryState } from "../../components/QueryState";
import { formatChapterTitle } from "../../lib/resourceUtils";
import { CatalogTreeEditor } from "./CatalogTreeEditor";
import { useCatalogChildren, useCatalogChapters, useCatalogMutations, useCatalogNodeDetail, useCatalogRoots, useCatalogSearch } from "./catalogTreeHooks";
import { CatalogTreeNodeList } from "./CatalogTreeNodeList";
import { buildCatalogNodeCreatePayload, catalogNodeKindLabel } from "./catalogTreeMappers";
import type { CatalogNodeFormValues } from "./catalogTreeMappers";
import "./catalogTree.css";

const { Text, Title } = Typography;

type CreateIntent = {
  parentId?: string | null;
  chapterId: string;
  kind: CatalogNodeKind;
};

function kindIcon(kind: CatalogNodeKind) {
  if (kind === "point") return <FileTextOutlined />;
  if (kind === "hybrid") return <BranchesOutlined />;
  if (kind === "shortcut") return <LinkOutlined />;
  return <FolderOpenOutlined />;
}

export function CatalogTreeWorkspacePage() {
  const { message } = AntApp.useApp();
  const [chapterId, setChapterId] = useState<string>();
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [searchText, setSearchText] = useState("");
  const [createIntent, setCreateIntent] = useState<CreateIntent | null>(null);
  const [createForm] = Form.useForm<CatalogNodeFormValues>();
  const chapters = useCatalogChapters();
  const roots = useCatalogRoots(chapterId);
  const selectedDetail = useCatalogNodeDetail(selectedNodeId || undefined);
  const selectedParentId = selectedDetail.data?.node.parent_id || undefined;
  const selectedSiblingChildren = useCatalogChildren(selectedParentId, Boolean(selectedParentId));
  const search = useCatalogSearch(searchText, chapterId, searchText.trim().length >= 2);
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
      createForm.setFieldsValue({ title: "", summary: "", node_kind: createIntent.kind, shortcut_target_node_id: "" });
    }
  }, [createForm, createIntent]);

  const chapterOptions = (chapters.data || []).map((chapter) => ({
    value: chapter.chapter_id,
    label: formatChapterTitle(chapter.chapter_title, chapter.chapter_id),
  }));
  const rootItems = roots.data?.nodes || [];
  const siblingItems = selectedDetail.data?.node.parent_id ? selectedSiblingChildren.data?.children || [] : rootItems;
  const currentChapter = chapters.data?.find((chapter) => chapter.chapter_id === chapterId);
  const selectedValidation = selectedDetail.data?.validation;
  const validationSummary = useMemo(() => {
    if (!selectedValidation) return null;
    if (selectedValidation.errors.length) return <Tag color="red">错误 {selectedValidation.errors.length}</Tag>;
    if (selectedValidation.warnings.length) return <Tag color="gold">提示 {selectedValidation.warnings.length}</Tag>;
    return <Tag color="green">可发布</Tag>;
  }, [selectedValidation]);

  const openCreate = (kind: CatalogNodeKind, parentId?: string | null) => {
    if (!chapterId) return;
    setCreateIntent({ chapterId, parentId: parentId || null, kind });
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

  const selectNode = (node: CatalogNodeCard) => {
    if (node.chapter_id !== chapterId) setChapterId(node.chapter_id);
    setSelectedNodeId(node.node_id);
  };

  return (
    <div className="catalog-workspace">
      <PageTitle
        title="章节目录与点位工作台"
        description="章节、多级目录、点位、快捷入口统一维护。"
        extra={
          <Space wrap>
            {validationSummary}
            <Button icon={<ReloadOutlined />} onClick={() => roots.refetch()}>
              刷新
            </Button>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => openCreate("directory")}>
              新建根目录
            </Button>
          </Space>
        }
      />

      <div className="catalog-workspace-toolbar">
        <Select
          className="catalog-chapter-select"
          value={chapterId}
          onChange={setChapterId}
          loading={chapters.isLoading}
          options={chapterOptions}
          placeholder="选择章节"
        />
        <Input
          prefix={<SearchOutlined />}
          value={searchText}
          onChange={(event) => setSearchText(event.target.value)}
          placeholder="搜索目录、点位、老师备注或旧身份"
          allowClear
        />
      </div>

      {searchText.trim().length >= 2 ? (
        <div className="catalog-search-results">
          <QueryState loading={search.isFetching} error={search.error} empty={!search.data?.items.length}>
            <Flex gap={8} wrap>
              {(search.data?.items || []).map((item) => (
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

      <div className="catalog-workspace-grid">
        <aside className="catalog-tree-panel">
          <Flex align="center" justify="space-between" className="catalog-panel-heading">
            <div>
              <Text type="secondary">当前章节</Text>
              <Title level={4}>{currentChapter ? formatChapterTitle(currentChapter.chapter_title, currentChapter.chapter_id) : "未选择"}</Title>
            </div>
            <Space.Compact>
              <Button icon={<FolderOpenOutlined />} onClick={() => openCreate("directory")}>目录</Button>
              <Button icon={<FileTextOutlined />} onClick={() => openCreate("point")}>点位</Button>
              <Button icon={<BranchesOutlined />} onClick={() => openCreate("hybrid")}>混合</Button>
            </Space.Compact>
          </Flex>
          <CatalogTreeNodeList
            nodes={rootItems}
            selectedNodeId={selectedNodeId}
            loading={roots.isLoading}
            error={roots.error}
            onSelect={selectNode}
            onAddRoot={() => openCreate("directory")}
            onAddChild={(node, kind = "directory") => openCreate(kind, node.node_id)}
            onReorder={(items) => mutations.reorderNodes.mutate(items)}
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
        title={createIntent?.parentId ? "新增子节点" : "新增根节点"}
        open={Boolean(createIntent)}
        onCancel={() => setCreateIntent(null)}
        onOk={submitCreate}
        okButtonProps={{ loading: mutations.createNode.isPending }}
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
              <Radio.Button value="hybrid">混合</Radio.Button>
              <Radio.Button value="shortcut">快捷</Radio.Button>
            </Radio.Group>
          </Form.Item>
          <Form.Item name="summary" label="摘要">
            <Input.TextArea autoSize={{ minRows: 2, maxRows: 4 }} />
          </Form.Item>
          <Form.Item noStyle shouldUpdate={(prev, next) => prev.node_kind !== next.node_kind}>
            {({ getFieldValue }) =>
              getFieldValue("node_kind") === "shortcut" ? (
                <Form.Item name="shortcut_target_node_id" label="快捷入口目标点位 Node ID" rules={[{ required: true, message: "请输入目标 Node ID" }]}>
                  <Input />
                </Form.Item>
              ) : null
            }
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}
