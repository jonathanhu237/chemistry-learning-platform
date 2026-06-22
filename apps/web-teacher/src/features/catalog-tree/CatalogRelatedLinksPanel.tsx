import { useEffect, useMemo, useState, type DragEvent } from "react";
import { App as AntApp, Button, Dropdown, Empty, Form, Input, Modal, Select, Space, Tag, Typography, type FormInstance, type MenuProps } from "antd";
import { ChevronDown, ChevronRight, FlaskConical, Folder, FolderOpen, MoreHorizontal, MoveDown, MoveUp, Plus, Trash2, Undo2 } from "lucide-react";

import { listCatalogChildren, listCatalogRoots, type CatalogNodeCard, type CatalogNodeDetail } from "../../api/catalogTree";
import { formatChapterTitle } from "../../lib/resourceUtils";
import { useCatalogChapters, type CatalogMutations } from "./catalogTreeHooks";
import {
  buildCatalogRelatedLinksPayload,
  catalogNodeKindLabel,
  isPointCapable,
  type CatalogRelatedLinkFormItem,
  type CatalogRelatedLinksFormValues,
} from "./catalogTreeMappers";

const { Text, Title } = Typography;
const RELATED_DRAG_MIME = "application/x-chemistry-admin-related-link-index";

type RelatedPickerNode = {
  node: CatalogNodeCard;
  children: RelatedPickerNode[];
  loaded: boolean;
  open: boolean;
  loading: boolean;
};

function relatedLinkOrderLabel(index: number): string {
  return String(index + 1).padStart(2, "0");
}

function relatedLinkTitle(link: CatalogRelatedLinkFormItem): string {
  return link.target_title?.trim() || link.target_node_id || "未命名实验";
}

function uniqueRelatedLinks(links: CatalogRelatedLinkFormItem[]): CatalogRelatedLinkFormItem[] {
  const seen = new Set<string>();
  return links.filter((link) => {
    const targetNodeId = String(link.target_node_id || "").trim();
    if (!targetNodeId || seen.has(targetNodeId)) return false;
    seen.add(targetNodeId);
    return true;
  });
}

function normalizeRelatedLinks(links: CatalogRelatedLinkFormItem[]): CatalogRelatedLinkFormItem[] {
  return uniqueRelatedLinks(links).map((link, index) => ({
    ...link,
    sort_order: index + 1,
  }));
}

function toRelatedPickerNodes(nodes: CatalogNodeCard[]): RelatedPickerNode[] {
  return nodes.map((node) => ({
    node,
    children: [],
    loaded: false,
    open: false,
    loading: false,
  }));
}

function updateRelatedPickerNode(
  nodes: RelatedPickerNode[],
  nodeId: string,
  updater: (node: RelatedPickerNode) => RelatedPickerNode,
): RelatedPickerNode[] {
  return nodes.map((node) => {
    if (node.node.node_id === nodeId) return updater(node);
    return { ...node, children: updateRelatedPickerNode(node.children, nodeId, updater) };
  });
}

function CatalogRelatedExperimentPicker({
  open,
  currentNode,
  selectedTargetIds,
  saving,
  onClose,
  onSelect,
}: {
  open: boolean;
  currentNode: CatalogNodeCard;
  selectedTargetIds: Set<string>;
  saving: boolean;
  onClose: () => void;
  onSelect: (node: CatalogNodeCard) => void;
}) {
  const { message } = AntApp.useApp();
  const chapters = useCatalogChapters();
  const [chapterId, setChapterId] = useState(currentNode.chapter_id);
  const [tree, setTree] = useState<RelatedPickerNode[]>([]);
  const [loadingRoots, setLoadingRoots] = useState(false);

  const chapterOptions = useMemo(() => {
    const options = (chapters.data || []).map((chapter) => ({
      value: chapter.chapter_id,
      label: formatChapterTitle(chapter.chapter_title, chapter.chapter_id),
    }));
    if (currentNode.chapter_id && !options.some((option) => option.value === currentNode.chapter_id)) {
      options.unshift({ value: currentNode.chapter_id, label: formatChapterTitle(null, currentNode.chapter_id) });
    }
    return options;
  }, [chapters.data, currentNode.chapter_id]);

  const loadRoots = async (nextChapterId: string) => {
    setLoadingRoots(true);
    try {
      const response = await listCatalogRoots(nextChapterId);
      setTree(toRelatedPickerNodes(response.nodes));
    } catch {
      message.error("目录树加载失败");
      setTree([]);
    } finally {
      setLoadingRoots(false);
    }
  };

  useEffect(() => {
    if (!open) return;
    setChapterId(currentNode.chapter_id);
    void loadRoots(currentNode.chapter_id);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, currentNode.chapter_id, currentNode.node_id]);

  const handleChapterChange = (nextChapterId: string) => {
    setChapterId(nextChapterId);
    void loadRoots(nextChapterId);
  };

  const toggleDirectory = async (target: RelatedPickerNode) => {
    if (target.loaded) {
      setTree((existing) =>
        updateRelatedPickerNode(existing, target.node.node_id, (node) => ({
          ...node,
          open: !node.open,
        })),
      );
      return;
    }
    setTree((existing) =>
      updateRelatedPickerNode(existing, target.node.node_id, (node) => ({
        ...node,
        loading: true,
        open: true,
      })),
    );
    try {
      const response = await listCatalogChildren(target.node.node_id);
      setTree((existing) =>
        updateRelatedPickerNode(existing, target.node.node_id, (node) => ({
          ...node,
          children: toRelatedPickerNodes(response.children),
          loaded: true,
          loading: false,
          open: true,
        })),
      );
    } catch {
      message.error("子目录加载失败");
      setTree((existing) =>
        updateRelatedPickerNode(existing, target.node.node_id, (node) => ({
          ...node,
          loading: false,
        })),
      );
    }
  };

  const selectPoint = (target: CatalogNodeCard) => {
    if (!isPointCapable(target.node_kind) || target.node_id === currentNode.node_id || selectedTargetIds.has(target.node_id) || saving) return;
    onSelect(target);
  };

  const renderNodes = (items: RelatedPickerNode[], depth = 0) =>
    items.map((item) => {
      const point = isPointCapable(item.node.node_kind);
      const current = item.node.node_id === currentNode.node_id;
      const selected = selectedTargetIds.has(item.node.node_id);
      const disabled = !point || current || selected || saving;
      const statusLabel = current ? "当前实验" : selected ? "已在列表" : "";
      if (!point) {
        return (
          <div key={item.node.node_id}>
            <div className="catalog-related-picker-row kind-directory" style={{ paddingLeft: 10 + depth * 18 }}>
              <Button
                type="text"
                size="small"
                className="catalog-related-picker-toggle"
                icon={item.open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                loading={item.loading}
                disabled={!item.node.has_children && !item.node.descendant_point_count}
                onClick={() => void toggleDirectory(item)}
                aria-label={item.open ? "收起目录" : "展开目录"}
              />
              <button type="button" className="catalog-related-picker-directory-button" onClick={() => void toggleDirectory(item)}>
                <span className="catalog-related-picker-icon">{item.open ? <FolderOpen size={16} /> : <Folder size={16} />}</span>
                <span className="catalog-related-picker-copy">
                  <strong>{item.node.title}</strong>
                  <small>{item.node.descendant_point_count || 0} 个实验</small>
                </span>
              </button>
            </div>
            {item.open && item.children.length ? renderNodes(item.children, depth + 1) : null}
          </div>
        );
      }
      return (
        <button
          type="button"
          key={item.node.node_id}
          className={`catalog-related-picker-point ${disabled ? "is-disabled" : ""}`}
          style={{ paddingLeft: 42 + depth * 18 }}
          disabled={disabled}
          onClick={() => selectPoint(item.node)}
        >
          <span className="catalog-related-picker-icon">
            <FlaskConical size={16} />
          </span>
          <span className="catalog-related-picker-copy">
            <strong>{item.node.title}</strong>
            <small>{catalogNodeKindLabel(item.node.node_kind)}</small>
          </span>
          {statusLabel ? <Tag color="default">{statusLabel}</Tag> : null}
        </button>
      );
    });

  return (
    <Modal title="选择相关实验" open={open} onCancel={onClose} footer={null} width={720} destroyOnHidden>
      <div className="catalog-related-picker">
        <div className="catalog-related-picker-toolbar">
          <Select
            value={chapterId}
            loading={chapters.isLoading}
            options={chapterOptions}
            onChange={handleChapterChange}
            className="catalog-related-picker-chapter"
          />
          <Text type="secondary">从目录树选择实验，添加后自动保存。</Text>
        </div>
        <div className="catalog-related-picker-tree">
          {loadingRoots ? <Text type="secondary">目录加载中...</Text> : tree.length ? renderNodes(tree) : <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="当前章节暂无可选实验" />}
        </div>
      </div>
    </Modal>
  );
}

export function CatalogRelatedLinksPanel({
  detail,
  linksForm,
  mutations,
}: {
  detail: CatalogNodeDetail;
  linksForm: FormInstance<CatalogRelatedLinksFormValues>;
  mutations: CatalogMutations;
}) {
  const { node } = detail;
  const watchedLinks = Form.useWatch("links", linksForm) || [];
  const links = uniqueRelatedLinks(watchedLinks);
  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const [dropIndex, setDropIndex] = useState<number | null>(null);
  const [pickerOpen, setPickerOpen] = useState(false);
  const selectedTargetIds = useMemo(
    () => new Set(links.map((link) => link.target_node_id).filter((targetNodeId): targetNodeId is string => Boolean(targetNodeId))),
    [links],
  );
  const defaultCount = links.filter((link) => link.relation_type === "generated_default" || link.relation_type === "default_override").length;
  const manualCount = links.filter((link) => link.relation_type === "manual").length;
  const saving = mutations.saveRelatedLinks.isPending;

  const setLinks = (nextLinks: CatalogRelatedLinkFormItem[], persist = false) => {
    const normalized = normalizeRelatedLinks(nextLinks);
    linksForm.setFieldsValue({ links: normalized });
    if (persist) {
      mutations.saveRelatedLinks.mutate({ nodeId: node.node_id, payload: buildCatalogRelatedLinksPayload({ links: normalized }) });
    }
  };

  const addPickedPoint = (item: CatalogNodeCard) => {
    setLinks(
      [
        ...links,
        {
          target_node_id: item.node_id,
          target_title: item.title,
          relation_type: "manual",
          source: "manual",
          hidden: false,
          sort_order: links.length + 1,
          metadata: {},
        },
      ],
      true,
    );
    setPickerOpen(false);
  };

  const moveLink = (fromIndex: number, toIndex: number, persist = false) => {
    if (saving || toIndex < 0 || toIndex >= links.length || fromIndex === toIndex) return;
    const nextLinks = [...links];
    const [item] = nextLinks.splice(fromIndex, 1);
    nextLinks.splice(toIndex, 0, item);
    setLinks(nextLinks, persist);
  };

  const removeLink = (index: number) => {
    if (saving) return;
    setLinks(links.filter((_, itemIndex) => itemIndex !== index), true);
  };

  const resolveDropIndex = (event: DragEvent<HTMLElement>, rowIndex: number): number => {
    const rect = event.currentTarget.getBoundingClientRect();
    return event.clientY < rect.top + rect.height / 2 ? rowIndex : rowIndex + 1;
  };

  const createDragPreview = (title: string) => {
    if (typeof document === "undefined") return null;
    const preview = document.createElement("div");
    preview.className = "catalog-related-drag-preview";
    preview.textContent = title;
    document.body.appendChild(preview);
    return preview;
  };

  const beginRowDrag = (event: DragEvent<HTMLDivElement>, index: number, link: CatalogRelatedLinkFormItem) => {
    if (saving) {
      event.preventDefault();
      return;
    }
    const title = relatedLinkTitle(link);
    setDragIndex(index);
    setDropIndex(index);
    event.dataTransfer.effectAllowed = "move";
    event.dataTransfer.setData(RELATED_DRAG_MIME, String(index));
    event.dataTransfer.setData("text/plain", title);
    const preview = createDragPreview(title);
    if (preview) {
      event.dataTransfer.setDragImage(preview, 12, 12);
      window.setTimeout(() => preview.remove(), 0);
    }
  };

  const dropRow = (event: DragEvent<HTMLDivElement>, rowIndex: number) => {
    event.preventDefault();
    const rawSourceIndex = event.dataTransfer.getData(RELATED_DRAG_MIME).trim();
    const sourceIndex = dragIndex ?? (rawSourceIndex ? Number(rawSourceIndex) : NaN);
    const insertionIndex = dropIndex ?? resolveDropIndex(event, rowIndex);
    if (Number.isInteger(sourceIndex)) {
      const targetIndex = sourceIndex < insertionIndex ? insertionIndex - 1 : insertionIndex;
      moveLink(sourceIndex, targetIndex, true);
    }
    setDragIndex(null);
    setDropIndex(null);
  };

  const relatedRowMenuItems = (index: number): MenuProps["items"] => [
    { key: "move-up", icon: <MoveUp size={14} />, label: "上移一位", disabled: saving || index === 0 },
    { key: "move-down", icon: <MoveDown size={14} />, label: "下移一位", disabled: saving || index === links.length - 1 },
    { type: "divider" },
    { key: "remove", danger: true, icon: <Trash2 size={14} />, label: "移除", disabled: saving },
  ];

  const handleRelatedRowMenu = (index: number, key: string) => {
    if (key === "move-up") moveLink(index, index - 1, true);
    if (key === "move-down") moveLink(index, index + 1, true);
    if (key === "remove") removeLink(index);
  };

  const resetToDefault = () => {
    if (saving) return;
    setLinks([], true);
  };

  if (!isPointCapable(node.node_kind)) {
    return (
      <section className="catalog-editor-section catalog-editor-panel-section">
        <Title level={4}>相关实验</Title>
        <Text type="secondary">当前节点只是目录，不维护实验之间的相关学习顺序。</Text>
      </section>
    );
  }

  return (
    <section className="catalog-editor-section catalog-editor-panel-section catalog-related-panel-section">
      <div className="catalog-panel-title-row catalog-related-title-row">
        <div>
          <Title level={4}>相关实验</Title>
          <Text type="secondary">默认采用同一直接父目录下的其他实验；也可以从目录树手动添加跨目录实验。</Text>
        </div>
        <Space className="catalog-related-header-actions" wrap size={6}>
          <Tag className="catalog-related-count-tag" color="green">默认 {defaultCount}</Tag>
          <Tag className="catalog-related-count-tag" color="blue">手动 {manualCount}</Tag>
          <Button className="catalog-related-reset-button" type="text" size="small" icon={<Undo2 size={14} />} onClick={resetToDefault} loading={saving}>
            重置为同目录默认
          </Button>
        </Space>
      </div>

      <Form form={linksForm} layout="vertical">
        <Form.List name="links">
          {(fields) => {
            const addSlot = (
              <button
                type="button"
                className="catalog-related-add-slot"
                disabled={saving}
                onClick={() => setPickerOpen(true)}
              >
                <span className="catalog-related-add-icon">
                  <Plus size={17} />
                </span>
                <span>
                  <strong>添加相关实验</strong>
                  <small>从目录树选择实验，添加后自动保存</small>
                </span>
              </button>
            );
            return (
              <div className={`catalog-related-builder${fields.length ? "" : " is-empty"}`}>
                {fields.length ? (
                  <div className="catalog-related-table" role="table" aria-label="相关实验列表">
                    <div className="catalog-related-table-head" role="row">
                      <span>顺序</span>
                      <span>相关实验</span>
                    </div>
                    <div className="catalog-related-list" role="rowgroup">
                      {fields.map((field, index) => {
                        const link = links[index] || {};
                        const title = relatedLinkTitle(link);
                        return (
                          <div
                            className={[
                              "catalog-related-row",
                              dragIndex === index ? "is-dragging" : "",
                              dropIndex === index && dragIndex !== index ? "is-drop-before" : "",
                              dropIndex === index + 1 && dragIndex !== index ? "is-drop-after" : "",
                            ]
                              .filter(Boolean)
                              .join(" ")}
                            draggable={!saving}
                            key={field.key}
                            role="row"
                            tabIndex={0}
                            title={title}
                            onDragStart={(event) => beginRowDrag(event, index, link)}
                            onDragOver={(event) => {
                              event.preventDefault();
                              event.dataTransfer.dropEffect = "move";
                              setDropIndex(resolveDropIndex(event, index));
                            }}
                            onDrop={(event) => dropRow(event, index)}
                            onDragEnd={() => {
                              setDragIndex(null);
                              setDropIndex(null);
                            }}
                          >
                            <Form.Item name={[field.name, "target_node_id"]} hidden>
                              <Input />
                            </Form.Item>
                            <Form.Item name={[field.name, "target_title"]} hidden>
                              <Input />
                            </Form.Item>
                            <Form.Item name={[field.name, "relation_type"]} hidden>
                              <Input />
                            </Form.Item>
                            <Form.Item name={[field.name, "source"]} hidden>
                              <Input />
                            </Form.Item>
                            <Form.Item name={[field.name, "sort_order"]} hidden>
                              <Input />
                            </Form.Item>

                            <span className="catalog-related-row-index" aria-label={`Order ${index + 1}`}>
                              {relatedLinkOrderLabel(index)}
                            </span>
                            <div className="catalog-related-row-copy">
                              <strong>{title}</strong>
                            </div>
                            <Dropdown
                              trigger={["click"]}
                              menu={{
                                items: relatedRowMenuItems(index),
                                onClick: ({ key }) => handleRelatedRowMenu(index, String(key)),
                              }}
                            >
                              <Button
                                className="catalog-related-row-menu"
                                size="small"
                                type="text"
                                icon={<MoreHorizontal size={16} />}
                                aria-label="相关实验更多操作"
                                onClick={(event) => event.stopPropagation()}
                              />
                            </Dropdown>
                          </div>
                        );
                      })}
                    </div>
                    {addSlot}
                  </div>
                ) : (
                  addSlot
                )}
              </div>
            );
          }}
        </Form.List>
      </Form>

      <CatalogRelatedExperimentPicker
        open={pickerOpen}
        currentNode={node}
        selectedTargetIds={selectedTargetIds}
        saving={saving}
        onClose={() => setPickerOpen(false)}
        onSelect={addPickedPoint}
      />
    </section>
  );
}
