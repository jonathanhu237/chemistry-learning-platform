import { useEffect, useMemo, useState } from "react";
import { Form, Tabs, Typography, type TabsProps } from "antd";
import { FlaskConical, Folder } from "lucide-react";

import type { CatalogNodeCard, CatalogNodeDetail, CatalogNodeKind } from "../../api/catalogTree";
import { QueryState } from "../../components/QueryState";
import { CatalogAdvancedPanel } from "./CatalogAdvancedPanel";
import { CatalogAiContextPanel } from "./CatalogAiContextPanel";
import { CatalogEditorHeader } from "./CatalogEditorHeader";
import { CatalogNodeContentPanel } from "./CatalogNodeContentPanel";
import { CatalogPublishChecksPanel } from "./CatalogPublishChecksPanel";
import { CatalogRelatedLinksPanel } from "./CatalogRelatedLinksPanel";
import { CatalogStudentCardPanel } from "./CatalogStudentCardPanel";
import { CatalogVideoPanel } from "./CatalogVideoPanel";
import { useCatalogMediaAssets, useCatalogSearch, useCatalogValidation, type CatalogMutations } from "./catalogTreeHooks";
import {
  buildCatalogNodeUpdatePayload,
  buildCatalogPointContentPayload,
  hydrateCatalogNodeForm,
  hydrateCatalogPointContentForm,
  hydrateCatalogRelatedLinksForm,
  isPointCapable,
  type CatalogNodeFormValues,
  type CatalogPointContentFormValues,
  type CatalogRelatedLinksFormValues,
} from "./catalogTreeMappers";

const { Text, Title } = Typography;

export const directoryCatalogEditorTabKeys = ["content", "student-card", "publish", "advanced"] as const;
export const pointCatalogEditorTabKeys = ["content", "video", "related", "student-card", "ai-context", "publish", "advanced"] as const;

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
  const [moveParentId, setMoveParentId] = useState<string>("");
  const [moveDisplayOrder, setMoveDisplayOrder] = useState<number | null>(null);
  const [mediaAssetIds, setMediaAssetIds] = useState<string[]>([]);
  const [relatedQuery, setRelatedQuery] = useState("");
  const [activeTab, setActiveTab] = useState<CatalogEditorTabKey>("content");
  const node = detail?.node;
  const pointCapable = isPointCapable(node?.node_kind);
  const principleMode = Form.useWatch("principle_mode", pointForm);
  const validation = useCatalogValidation(node?.node_id, true);
  const mediaAssets = useCatalogMediaAssets(pointCapable);
  const relatedSearch = useCatalogSearch(relatedQuery, node?.chapter_id, pointCapable && relatedQuery.trim().length >= 2);
  const mediaAssetMap = useMemo(
    () => new Map((mediaAssets.data?.items || []).map((asset) => [asset.id, asset])),
    [mediaAssets.data?.items],
  );

  useEffect(() => {
    const timeout = window.setTimeout(() => {
      nodeForm.setFieldsValue(hydrateCatalogNodeForm(detail));
      pointForm.setFieldsValue(hydrateCatalogPointContentForm(detail));
      linksForm.setFieldsValue(hydrateCatalogRelatedLinksForm(detail));
    }, 0);
    setMoveParentId(detail?.node.parent_id || "");
    setMoveDisplayOrder(detail?.node.display_order ?? null);
    setMediaAssetIds([]);
    setRelatedQuery("");
    setActiveTab("content");
    return () => window.clearTimeout(timeout);
  }, [detail, linksForm, nodeForm, pointForm]);

  useEffect(() => {
    if (!pointCapable && (activeTab === "video" || activeTab === "related" || activeTab === "ai-context")) {
      setActiveTab("content");
    }
  }, [activeTab, pointCapable]);

  const savePointContent = async (values: CatalogPointContentFormValues) => {
    if (!node) return;
    const pointTitle = values.point_title.trim();
    if (pointTitle && pointTitle !== node.title) {
      const currentNodeValues = {
        ...hydrateCatalogNodeForm(detail),
        ...nodeForm.getFieldsValue(true),
        title: pointTitle,
        node_kind: node.node_kind,
      };
      await mutations.updateNode.mutateAsync({ nodeId: node.node_id, payload: buildCatalogNodeUpdatePayload(currentNodeValues) });
    }
    await mutations.savePointContent.mutateAsync({ nodeId: node.node_id, payload: buildCatalogPointContentPayload(values) });
  };

  const formAnchors = (
    <div className="catalog-form-anchors" aria-hidden="true">
      <Form form={nodeForm} component={false} />
      <Form form={pointForm} component={false} />
      <Form form={linksForm} component={false} />
    </div>
  );

  if (!detail && !loading && !error) {
    return (
      <div className="catalog-editor catalog-editor-empty">
        {formAnchors}
        <div className="catalog-editor-empty-state">
          <div className="catalog-editor-empty-mark" aria-hidden="true">
            <Folder size={28} />
            <FlaskConical size={20} />
          </div>
          <div className="catalog-editor-empty-copy">
            <Title level={4}>请选择左侧目录或点位</Title>
            <Text type="secondary">目录负责组织学生导航，点位负责维护学习内容、视频绑定与发布检查。</Text>
          </div>
          <div className="catalog-editor-empty-hints" aria-hidden="true">
            <span>目录</span>
            <span>点位</span>
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
  const allTabItems: NonNullable<TabsProps["items"]> = [
    {
      key: "content",
      label: "内容",
      forceRender: true,
      children: (
        <CatalogNodeContentPanel
          detail={detail}
          nodeForm={nodeForm}
          pointForm={pointForm}
          principleMode={principleMode}
          mutations={mutations}
          onSavePointContent={savePointContent}
        />
      ),
    },
    {
      key: "video",
      label: "视频",
      forceRender: true,
      children: (
        <CatalogVideoPanel
          detail={detail}
          mediaAssets={mediaAssets}
          mediaAssetIds={mediaAssetIds}
          setMediaAssetIds={setMediaAssetIds}
          mediaAssetMap={mediaAssetMap}
          mutations={mutations}
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
          relatedQuery={relatedQuery}
          setRelatedQuery={setRelatedQuery}
          relatedSearch={relatedSearch}
          mutations={mutations}
        />
      ),
    },
    {
      key: "student-card",
      label: "学生卡片",
      forceRender: true,
      children: <CatalogStudentCardPanel detail={detail} nodeForm={nodeForm} mutations={mutations} />,
    },
    {
      key: "ai-context",
      label: "AI 上下文",
      forceRender: true,
      children: <CatalogAiContextPanel detail={detail} mutations={mutations} />,
    },
    {
      key: "publish",
      label: "发布检查",
      forceRender: true,
      children: <CatalogPublishChecksPanel detail={detail} validation={validation} />,
    },
    {
      key: "advanced",
      label: "高级",
      forceRender: true,
      children: (
        <CatalogAdvancedPanel
          detail={detail}
          siblings={siblings}
          moveParentId={moveParentId}
          setMoveParentId={setMoveParentId}
          moveDisplayOrder={moveDisplayOrder}
          setMoveDisplayOrder={setMoveDisplayOrder}
          mutations={mutations}
        />
      ),
    },
  ];
  const tabItems = allTabItems.filter((item) => visibleTabKeys.includes(item.key as CatalogEditorTabKey));

  return (
    <QueryState loading={Boolean(loading)} error={error} empty={!detail}>
      {detail && node ? (
        <div className="catalog-editor catalog-editor-selected">
          {formAnchors}
          <CatalogEditorHeader detail={detail} mutations={mutations} />
          <Tabs
            className="catalog-editor-tabs"
            activeKey={activeTab}
            onChange={(key) => setActiveTab(key as CatalogEditorTabKey)}
            destroyOnHidden={false}
            items={tabItems}
          />
        </div>
      ) : null}
    </QueryState>
  );
}
