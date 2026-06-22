import { useEffect, useRef, useState } from "react";
import { Form, Modal, Tabs, Typography, type TabsProps } from "antd";
import { FlaskConical, Folder } from "lucide-react";

import type { CatalogNodeCard, CatalogNodeDetail, CatalogNodeKind } from "../../api/catalogTree";
import { QueryState } from "../../components/QueryState";
import { CatalogAdvancedPanel } from "./CatalogAdvancedPanel";
import { CatalogAiContextPanel } from "./CatalogAiContextPanel";
import { CatalogEditorHeader, type CatalogHeaderDiagnosticsKey } from "./CatalogEditorHeader";
import { CatalogNodeContentPanel } from "./CatalogNodeContentPanel";
import { CatalogNodeStatusPanel } from "./CatalogNodeStatusPanel";
import { CatalogRelatedLinksPanel } from "./CatalogRelatedLinksPanel";
import { CatalogVideoPanel } from "./CatalogVideoPanel";
import { useCatalogMediaAssets, useCatalogValidation, type CatalogMutations } from "./catalogTreeHooks";
import {
  buildCatalogNodeUpdatePayload,
  buildCatalogPointContentPayload,
  displayCatalogPointTitle,
  hydrateCatalogNodeForm,
  hydrateCatalogPointContentForm,
  hydrateCatalogRelatedLinksForm,
  isPointCapable,
  resolveCatalogNodeStatus,
  type CatalogNodeFormValues,
  type CatalogPointContentFormValues,
  type CatalogRelatedLinksFormValues,
} from "./catalogTreeMappers";

const { Text, Title } = Typography;

export const directoryCatalogEditorTabKeys = ["content"] as const;
export const pointCatalogEditorTabKeys = ["content", "video", "related"] as const;

export type CatalogEditorTabKey = (typeof pointCatalogEditorTabKeys)[number];

export function catalogEditorTabKeysForNode(kind?: CatalogNodeKind | null): CatalogEditorTabKey[] {
  return [...(isPointCapable(kind) ? pointCatalogEditorTabKeys : directoryCatalogEditorTabKeys)];
}

export function CatalogTreeEditor({
  detail,
  loading,
  error,
  siblings,
  mutations,
}: {
  detail?: CatalogNodeDetail;
  loading?: boolean;
  error?: unknown;
  siblings: CatalogNodeCard[];
  onSelectNode: (nodeId: string) => void;
  mutations: CatalogMutations;
}) {
  const [nodeForm] = Form.useForm<CatalogNodeFormValues>();
  const [pointForm] = Form.useForm<CatalogPointContentFormValues>();
  const [linksForm] = Form.useForm<CatalogRelatedLinksFormValues>();
  const [taskNodeForm] = Form.useForm<CatalogNodeFormValues>();
  const [taskPointForm] = Form.useForm<CatalogPointContentFormValues>();
  const [moveParentId, setMoveParentId] = useState<string>("");
  const [moveDisplayOrder, setMoveDisplayOrder] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<CatalogEditorTabKey>("content");
  const [diagnosticsPanel, setDiagnosticsPanel] = useState<CatalogHeaderDiagnosticsKey | null>(null);
  const [contentTaskOpen, setContentTaskOpen] = useState(false);
  const [videoPickerOpen, setVideoPickerOpen] = useState(false);
  const [previewFallbackUrl, setPreviewFallbackUrl] = useState("");
  const previousNodeIdRef = useRef<string | null>(null);
  const dirtyPointContentNodeIdRef = useRef<string | null>(null);
  const node = detail?.node;
  const pointCapable = isPointCapable(node?.node_kind);
  const principleMode = Form.useWatch("principle_mode", pointForm);
  const taskPrincipleMode = Form.useWatch("principle_mode", taskPointForm);
  const validation = useCatalogValidation(node?.node_id, true);
  const mediaAssets = useCatalogMediaAssets(pointCapable);
  const nodeStatus = detail ? resolveCatalogNodeStatus(detail) : null;
  const canBindVideo = !pointCapable || nodeStatus?.core_readiness.content_fields === "complete";

  useEffect(() => {
    const nextNodeId = detail?.node.node_id || null;
    const selectedNodeChanged = previousNodeIdRef.current !== nextNodeId;
    previousNodeIdRef.current = nextNodeId;
    if (selectedNodeChanged) {
      dirtyPointContentNodeIdRef.current = null;
    }
    const shouldHydratePointContent = selectedNodeChanged || dirtyPointContentNodeIdRef.current !== nextNodeId;
    const timeout = window.setTimeout(() => {
      nodeForm.setFieldsValue(hydrateCatalogNodeForm(detail));
      if (shouldHydratePointContent) {
        pointForm.setFieldsValue(hydrateCatalogPointContentForm(detail));
      }
      linksForm.setFieldsValue(hydrateCatalogRelatedLinksForm(detail));
    }, 0);
    setMoveParentId(detail?.node.parent_id || "");
    setMoveDisplayOrder(detail?.node.display_order ?? null);
    if (selectedNodeChanged) {
      setActiveTab("content");
      setContentTaskOpen(false);
      setVideoPickerOpen(false);
    }
    return () => window.clearTimeout(timeout);
  }, [detail, linksForm, nodeForm, pointForm]);

  const markPointContentLocalChange = () => {
    if (node?.node_id) {
      dirtyPointContentNodeIdRef.current = node.node_id;
    }
  };

  useEffect(() => {
    if (!pointCapable && (activeTab === "video" || activeTab === "related")) {
      setActiveTab("content");
    }
  }, [activeTab, pointCapable]);

  useEffect(() => {
    if (!pointCapable && diagnosticsPanel === "ai-context") {
      setDiagnosticsPanel(null);
    }
  }, [diagnosticsPanel, pointCapable]);

  const savePointContent = async (values: CatalogPointContentFormValues, options: { silent?: boolean } = {}) => {
    if (!node) return;
    const pointTitle = values.point_title.trim();
    if (pointTitle && pointTitle !== node.title) {
      const currentNodeValues = {
        ...hydrateCatalogNodeForm(detail),
        ...nodeForm.getFieldsValue(true),
        title: pointTitle,
        node_kind: node.node_kind,
      };
      await mutations.updateNode.mutateAsync({ nodeId: node.node_id, payload: buildCatalogNodeUpdatePayload(currentNodeValues), silent: options.silent });
    }
    await mutations.savePointContent.mutateAsync({ nodeId: node.node_id, payload: buildCatalogPointContentPayload(values), silent: options.silent });
  };

  const contentValuesForTask = () => {
    const hydrated = hydrateCatalogPointContentForm(detail);
    return {
      ...hydrated,
      ...pointForm.getFieldsValue(true),
      point_title: pointForm.getFieldValue("point_title") || hydrated.point_title || displayCatalogPointTitle(detail) || node?.title || "",
    };
  };

  const openContentTask = () => {
    if (!detail || !node || !pointCapable) return;
    setActiveTab("content");
    taskNodeForm.setFieldsValue({ ...hydrateCatalogNodeForm(detail), ...nodeForm.getFieldsValue(true) });
    taskPointForm.setFieldsValue(contentValuesForTask());
    setContentTaskOpen(true);
  };

  useEffect(() => {
    if (!contentTaskOpen) return;
    const timeout = window.setTimeout(() => {
      taskPointForm.validateFields().catch((error: { errorFields?: Array<{ name?: (string | number)[] }> }) => {
        const firstMissing = error.errorFields?.[0]?.name;
        if (firstMissing) {
          taskPointForm.scrollToField(firstMissing, { focus: true });
        }
      });
    }, 140);
    return () => window.clearTimeout(timeout);
  }, [contentTaskOpen, taskPointForm]);

  const saveTaskPointContent = async (values: CatalogPointContentFormValues, options?: { silent?: boolean }) => {
    await savePointContent(values, options);
    pointForm.setFieldsValue(values);
    markPointContentLocalChange();
  };

  const publishPointContentFromHeader = () => {
    if (!node) return;
    if (pointForm.isFieldsTouched(true)) {
      openContentTask();
      return;
    }
    mutations.changePointPublication.mutate({ nodeId: node.node_id, action: "publish" });
  };

  const savePointTitleFromHeader = async (nextTitle: string) => {
    const nextValues = {
      ...contentValuesForTask(),
      point_title: nextTitle,
    };
    pointForm.setFieldsValue({ point_title: nextTitle });
    markPointContentLocalChange();
    await savePointContent(nextValues);
  };

  const saveDirectoryTitleFromHeader = async (nextTitle: string) => {
    if (!node) return;
    const nextValues = {
      ...hydrateCatalogNodeForm(detail),
      ...nodeForm.getFieldsValue(true),
      title: nextTitle,
      node_kind: node.node_kind,
    };
    nodeForm.setFieldsValue({ title: nextTitle });
    await mutations.updateNode.mutateAsync({ nodeId: node.node_id, payload: buildCatalogNodeUpdatePayload(nextValues) });
  };

  const saveTitleFromHeader = async (nextTitle: string) => {
    if (pointCapable) {
      await savePointTitleFromHeader(nextTitle);
      return;
    }
    await saveDirectoryTitleFromHeader(nextTitle);
  };

  const formAnchors = (
    <div className="catalog-form-anchors" aria-hidden="true">
      <Form form={nodeForm} component={false} />
      <Form form={pointForm} component={false} />
      <Form form={linksForm} component={false} />
    </div>
  );

  const openLearningCardPreview = async () => {
    if (!node || !pointCapable) return;
    const response = await mutations.createPreviewToken.mutateAsync({ nodeId: node.node_id });
    const params = new URLSearchParams({
      nodeId: node.node_id,
      title: displayCatalogPointTitle(detail) || node.title,
      previewUrl: response.preview_url,
      expiresAt: response.expires_at,
    });
    const previewWindowUrl = `/catalog-preview?${params.toString()}`;
    const opened = window.open(previewWindowUrl, "_blank", "popup,width=520,height=920");
    if (!opened) {
      setPreviewFallbackUrl(previewWindowUrl);
      return;
    }
    opened.opener = null;
    opened.focus();
  };

  if (!detail && !loading && !error) {
    return (
      <div className="catalog-editor catalog-editor-empty">
        {formAnchors}
        <div className="catalog-editor-empty-state">
          <div className="catalog-editor-empty-mark" aria-hidden="true">
            <Folder className="catalog-editor-empty-folder" size={32} strokeWidth={1.85} />
            <FlaskConical className="catalog-editor-empty-flask" size={22} strokeWidth={1.9} />
          </div>
          <div className="catalog-editor-empty-copy">
            <Title level={4}>从左侧选择一个节点</Title>
            <Text type="secondary">目录组织学生导航；点位维护学习内容、视频与发布状态。</Text>
          </div>
          <div className="catalog-editor-empty-hints" aria-label="节点类型提示">
            <span>
              <Folder size={14} strokeWidth={1.9} aria-hidden="true" />
              目录导航
            </span>
            <span>
              <FlaskConical size={14} strokeWidth={1.9} aria-hidden="true" />
              点位内容
            </span>
          </div>
        </div>
      </div>
    );
  }

  if (!detail || !node) {
    return (
      <QueryState loading={Boolean(loading)} error={error} empty={!detail}>
        {null}
      </QueryState>
    );
  }

  const visibleTabKeys = catalogEditorTabKeysForNode(node?.node_kind);
  const contentPanel = (
    <CatalogNodeContentPanel
      detail={detail}
      nodeForm={nodeForm}
      pointForm={pointForm}
      principleMode={principleMode}
      mutations={mutations}
      onSavePointContent={savePointContent}
      onLocalContentChange={markPointContentLocalChange}
    />
  );
  const allTabItems: NonNullable<TabsProps["items"]> = [
    {
      key: "content",
      label: "知识内容",
      forceRender: true,
      children: contentPanel,
    },
    {
      key: "video",
      label: "实验视频",
      forceRender: true,
      children: (
          <CatalogVideoPanel
            detail={detail}
            mediaAssets={mediaAssets}
            mutations={mutations}
            canBindVideo={canBindVideo}
            pickerOpen={videoPickerOpen}
            onPickerOpenChange={setVideoPickerOpen}
            onOpenContentTask={openContentTask}
          />
      ),
    },
    {
      key: "related",
      label: "相关实验",
      forceRender: true,
      children: (
        <CatalogRelatedLinksPanel
          detail={detail}
          linksForm={linksForm}
          mutations={mutations}
        />
      ),
    },
  ];
  const tabItems = allTabItems.filter((item) => visibleTabKeys.includes(item.key as CatalogEditorTabKey));
  const diagnosticsTitle =
    diagnosticsPanel === "ai-context" ? "点位检索诊断" : diagnosticsPanel === "advanced" ? "高级调试" : "节点状态";
  const diagnosticsContent =
    diagnosticsPanel === "ai-context" ? (
      <CatalogAiContextPanel detail={detail} mutations={mutations} />
    ) : diagnosticsPanel === "advanced" ? (
      <CatalogAdvancedPanel
        detail={detail}
        siblings={siblings}
        moveParentId={moveParentId}
        setMoveParentId={setMoveParentId}
        moveDisplayOrder={moveDisplayOrder}
        setMoveDisplayOrder={setMoveDisplayOrder}
        mutations={mutations}
      />
    ) : diagnosticsPanel === "node-status" ? (
      <CatalogNodeStatusPanel detail={detail} validation={validation} mutations={mutations} />
    ) : null;

  return (
    <QueryState loading={Boolean(loading)} error={error} empty={!detail}>
      {detail && node ? (
        <div className="catalog-editor catalog-editor-selected">
          {formAnchors}
          <CatalogEditorHeader
            detail={detail}
            mutations={mutations}
            onPreviewLearningCard={openLearningCardPreview}
            previewLoading={mutations.createPreviewToken.isPending}
            onOpenDiagnostics={setDiagnosticsPanel}
            onOpenContentTask={openContentTask}
            onOpenVideoPicker={() => {
              setActiveTab("video");
              setVideoPickerOpen(true);
            }}
            onPublishPointContent={publishPointContentFromHeader}
            onSaveTitle={saveTitleFromHeader}
          />
          {pointCapable ? (
            <Tabs
              className="catalog-editor-tabs"
              activeKey={activeTab}
              onChange={(key) => setActiveTab(key as CatalogEditorTabKey)}
              destroyOnHidden={false}
              items={tabItems}
            />
          ) : (
            <div className="catalog-editor-direct-panel">{contentPanel}</div>
          )}
          <Modal
            title={diagnosticsTitle}
            open={Boolean(diagnosticsPanel)}
            onCancel={() => setDiagnosticsPanel(null)}
            footer={null}
            width={diagnosticsPanel === "advanced" || diagnosticsPanel === "ai-context" ? 1080 : 920}
            destroyOnHidden={false}
          >
            <div className="catalog-diagnostics-modal-body">{diagnosticsContent}</div>
          </Modal>
          <Modal
            className="catalog-content-task-modal"
            title="编辑内容"
            open={contentTaskOpen}
            onCancel={() => setContentTaskOpen(false)}
            footer={null}
            width={1180}
            destroyOnHidden
          >
            <CatalogNodeContentPanel
              detail={detail}
              nodeForm={taskNodeForm}
              pointForm={taskPointForm}
              principleMode={taskPrincipleMode}
              mutations={mutations}
              onSavePointContent={saveTaskPointContent}
              onLocalContentChange={markPointContentLocalChange}
              variant="task"
            />
          </Modal>
          <Modal
            title="打开学习卡片预览"
            open={Boolean(previewFallbackUrl)}
            onCancel={() => setPreviewFallbackUrl("")}
            footer={null}
            width={520}
          >
            <div className="catalog-preview-fallback">
              <Text type="secondary">浏览器拦截了新窗口。请用下面的按钮打开本次短时预览。</Text>
              <a href={previewFallbackUrl} target="_blank" rel="noreferrer" className="catalog-preview-fallback-link">
                打开预览窗口
              </a>
            </div>
          </Modal>
        </div>
      ) : null}
    </QueryState>
  );
}
