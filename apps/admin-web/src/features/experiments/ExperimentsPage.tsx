import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  App as AntApp,
  Button,
  Card,
  Checkbox,
  Descriptions,
  Divider,
  Drawer,
  Empty,
  Flex,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Progress,
  Segmented,
  Select,
  Space,
  Spin,
  Statistic,
  Switch,
  Table,
  Tag,
  Tooltip,
  Typography,
} from "antd";
import {
  CloudUploadOutlined,
  CheckCircleOutlined,
  DeleteOutlined,
  EditOutlined,
  ExperimentOutlined,
  EyeOutlined,
  PauseCircleOutlined,
  PlayCircleOutlined,
  PlusOutlined,
  ReloadOutlined,
  VideoCameraOutlined,
} from "@ant-design/icons";

import { api, apiBase, formatBytes, getAuthToken, patchJson, postJson, putJson } from "../../api";
import type { ApiList, Experiment, ExperimentVideoPoint, ExperimentVideoPointResource, ExperimentVideoPointsResponse, MediaAsset } from "../../api";
import { AuthenticatedImage } from "../../components/AuthenticatedImage";
import { PageTitle } from "../../components/PageTitle";
import { QueryState } from "../../components/QueryState";
import { errorMessage } from "../../lib/errors";
import { statusTag } from "../../lib/status";
import { useChapters, useExperiments } from "./experimentHooks";
import { experimentVideoCandidates, formatChapterTitle, isPreviewableVideo, mediaAssetType, theoryChapters } from "../resources/resourceUtils";
import "./experiments.css";

const { Text, Title } = Typography;

type VideoPreviewTarget = {
  id: string;
  title: string;
  original_file_name: string;
  mime_type?: string | null;
  upload_status?: string | null;
};

type VideoPointFilter = "all" | "empty" | "referenced" | "published";

export function ExperimentsPage() {
  const { message } = AntApp.useApp();
  const queryClient = useQueryClient();
  const chapters = useChapters();
  const [experimentKeyword, setExperimentKeyword] = useState("");
  const [chapterId, setChapterId] = useState<string>();
  const [statusFilter, setStatusFilter] = useState<string>();
  const [selected, setSelected] = useState<Experiment | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [form] = Form.useForm();
  const [createForm] = Form.useForm();
  const [videoPointFilter, setVideoPointFilter] = useState<VideoPointFilter>("all");
  const [referencePoint, setReferencePoint] = useState<ExperimentVideoPoint | null>(null);
  const [assetKeyword, setAssetKeyword] = useState("");
  const [selectedAssetIds, setSelectedAssetIds] = useState<string[]>([]);
  const [previewTarget, setPreviewTarget] = useState<VideoPreviewTarget | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string>();
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState("");
  const [pendingVideoBindingAction, setPendingVideoBindingAction] = useState<{
    bindingId: string;
    action: "publish" | "unpublish" | "delete";
  } | null>(null);
  const searchParams = new URLSearchParams();
  if (chapterId) searchParams.set("chapter_id", chapterId);
  if (statusFilter) searchParams.set("status_filter", statusFilter);
  const params = searchParams.toString() ? `?${searchParams.toString()}` : "";
  const experiments = useExperiments(params);
  const selectedExperiment = useQuery({
    queryKey: ["admin-experiment", selected?.id],
    queryFn: () => api<Experiment>(`/api/admin/experiments/${selected?.id}`),
    enabled: Boolean(selected?.id),
  });
  const currentExperiment = selectedExperiment.data || selected;
  const currentExperimentId = currentExperiment?.id;
  const experimentVideoPoints = useQuery({
    queryKey: ["experiment-video-points", currentExperimentId],
    queryFn: () => api<ExperimentVideoPointsResponse>(`/api/admin/experiments/${currentExperimentId}/video-points`),
    enabled: Boolean(currentExperimentId),
  });
  const mediaAssets = useQuery({
    queryKey: ["media-assets"],
    queryFn: () => api<ApiList<MediaAsset>>("/api/admin/media/assets?limit=200"),
    enabled: Boolean(referencePoint),
  });
  const currentMetadata = (currentExperiment?.metadata || {}) as Record<string, unknown>;
  const videoCandidates = experimentVideoCandidates(currentExperiment);
  const videoPointItems = useMemo(() => experimentVideoPoints.data?.points || [], [experimentVideoPoints.data?.points]);
  const parentTitle = typeof currentMetadata.parent_title === "string" ? currentMetadata.parent_title : "";
  const moduleTitle = typeof currentMetadata.module_display_title === "string" ? currentMetadata.module_display_title : "";
  const videoPointCount = experimentVideoPoints.data?.total_points ?? videoCandidates.length;
  const resourceCount = experimentVideoPoints.data?.total_resources ?? currentExperiment?.media_resources.length ?? 0;
  const publishedResourceCount =
    experimentVideoPoints.data?.published_resources ??
    currentExperiment?.media_resources.filter((resource) => resource.binding_status === "published").length ??
    0;
  const referencedAssetIds = useMemo(
    () => new Set(videoPointItems.flatMap((point) => point.resources.map((resource) => resource.media_id))),
    [videoPointItems],
  );
  const currentPointAssetIds = useMemo(
    () => new Set(referencePoint?.resources.map((resource) => resource.media_id) || []),
    [referencePoint?.resources],
  );
  const referenceAssets = useMemo(() => mediaAssets.data?.items || [], [mediaAssets.data?.items]);
  const referenceAssetMap = useMemo(() => new Map(referenceAssets.map((asset) => [asset.id, asset])), [referenceAssets]);
  const filteredReferenceAssets = useMemo(() => {
    const keyword = assetKeyword.trim().toLowerCase();
    return referenceAssets.filter((asset) => {
      if (!keyword) return true;
      return `${asset.title} ${asset.original_file_name}`.toLowerCase().includes(keyword);
    });
  }, [assetKeyword, referenceAssets]);
  const filteredVideoPoints = useMemo(() => {
    if (videoPointFilter === "empty") return videoPointItems.filter((point) => point.resource_count === 0);
    if (videoPointFilter === "referenced") return videoPointItems.filter((point) => point.resource_count > 0);
    if (videoPointFilter === "published") return videoPointItems.filter((point) => point.published_count > 0);
    return videoPointItems;
  }, [videoPointFilter, videoPointItems]);

  useEffect(() => {
    if (currentExperiment) {
      form.setFieldsValue({
        title: currentExperiment.title,
        summary: currentExperiment.summary,
        status: currentExperiment.status,
        chapter_ids: currentExperiment.chapter_bindings.map((item) => item.chapter_id),
      });
    }
  }, [currentExperiment, form]);

  useEffect(() => {
    setVideoPointFilter("all");
    setReferencePoint(null);
    setAssetKeyword("");
    setSelectedAssetIds([]);
    setPreviewTarget(null);
    setPendingVideoBindingAction(null);
  }, [selected?.id]);

  useEffect(() => {
    setSelectedAssetIds([]);
    setAssetKeyword("");
  }, [referencePoint?.point_key]);

  useEffect(() => {
    let objectUrl: string | undefined;
    let cancelled = false;
    setPreviewUrl(undefined);
    setPreviewError("");
    setPreviewLoading(false);
    if (!previewTarget || previewTarget.upload_status !== "ready") {
      return undefined;
    }
    setPreviewLoading(true);
    const headers = new Headers();
    const token = getAuthToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    void fetch(`${apiBase}/api/admin/media/assets/${previewTarget.id}/file`, { headers })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(response.status === 409 ? "视频还未就绪，暂不能预览" : "视频预览加载失败");
        }
        return response.blob();
      })
      .then((blob) => {
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setPreviewUrl(objectUrl);
      })
      .catch((error) => {
        if (!cancelled) setPreviewError(errorMessage(error));
      })
      .finally(() => {
        if (!cancelled) setPreviewLoading(false);
      });
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [previewTarget]);

  const invalidateExperimentData = (experimentId?: string) => {
    void queryClient.invalidateQueries({ queryKey: ["admin-experiments"] });
    void queryClient.invalidateQueries({ queryKey: ["question-banks"] });
    if (experimentId) {
      void queryClient.invalidateQueries({ queryKey: ["admin-experiment", experimentId] });
    }
  };

  const invalidateVideoReferenceData = (experimentId?: string) => {
    invalidateExperimentData(experimentId);
    if (experimentId) {
      void queryClient.invalidateQueries({ queryKey: ["experiment-video-points", experimentId] });
    }
    void queryClient.invalidateQueries({ queryKey: ["media-assets"] });
  };

  const createExperiment = useMutation({
    mutationFn: (values: { title: string; summary?: string; status: string; chapter_ids: string[] }) =>
      postJson<Experiment>("/api/admin/experiments", {
        title: values.title,
        summary: values.summary,
        status: values.status || "draft",
        chapter_ids: values.chapter_ids || [],
      }),
    onSuccess: (experiment) => {
      message.success("实验已创建");
      setCreateOpen(false);
      createForm.resetFields();
      setSelected(experiment);
      invalidateExperimentData(experiment.id);
    },
    onError: (error) => message.error(errorMessage(error)),
  });
  const submitCreateExperiment = async (status: "draft" | "published") => {
    try {
      const values = await createForm.validateFields();
      createExperiment.mutate({ ...values, status });
    } catch {
      // Ant Design will surface field validation messages beside the inputs.
    }
  };

  const save = useMutation({
    mutationFn: (values: { title: string; summary?: string; status: string; chapter_ids: string[] }) =>
      patchJson<Experiment>(`/api/admin/experiments/${currentExperiment?.id}`, {
        title: values.title,
        summary: values.summary,
        status: values.status,
        chapter_ids: values.chapter_ids || [],
      }),
    onSuccess: (experiment) => {
      message.success("实验已保存");
      setSelected(experiment);
      invalidateExperimentData(experiment.id);
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const addPointResources = useMutation({
    mutationFn: async () => {
      if (!currentExperimentId || !referencePoint) {
        throw new Error("请选择实验点位");
      }
      if (!selectedAssetIds.length) {
        throw new Error("请选择要引用的视频资源");
      }
      return Promise.all(
        selectedAssetIds.map((assetId) => {
          const asset = referenceAssetMap.get(assetId);
          return postJson<Record<string, unknown>>(
            `/api/admin/experiments/${currentExperimentId}/video-points/${encodeURIComponent(referencePoint.point_key)}/resources`,
            {
              media_asset_id: assetId,
              title: asset?.title || referencePoint.point_title,
              status: "draft",
            },
          );
        }),
      );
    },
    onSuccess: () => {
      message.success("视频已引用到点位");
      const experimentId = currentExperimentId;
      setReferencePoint(null);
      setSelectedAssetIds([]);
      setAssetKeyword("");
      invalidateVideoReferenceData(experimentId);
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const publishPointResource = useMutation({
    mutationFn: (resource: ExperimentVideoPointResource) =>
      postJson<Record<string, unknown>>(`/api/admin/media/bindings/${resource.binding_id}/publish`, {}),
    onMutate: (resource) => {
      setPendingVideoBindingAction({ bindingId: resource.binding_id, action: "publish" });
    },
    onSuccess: (_, resource) => {
      message.success("视频引用已发布");
      invalidateVideoReferenceData(resource.experiment_id);
    },
    onError: (error) => message.error(errorMessage(error)),
    onSettled: () => setPendingVideoBindingAction(null),
  });

  const unpublishPointResource = useMutation({
    mutationFn: (resource: ExperimentVideoPointResource) =>
      postJson<Record<string, unknown>>(`/api/admin/media/bindings/${resource.binding_id}/unpublish`, {}),
    onMutate: (resource) => {
      setPendingVideoBindingAction({ bindingId: resource.binding_id, action: "unpublish" });
    },
    onSuccess: (_, resource) => {
      message.success("视频引用已取消发布");
      invalidateVideoReferenceData(resource.experiment_id);
    },
    onError: (error) => message.error(errorMessage(error)),
    onSettled: () => setPendingVideoBindingAction(null),
  });

  const deletePointResource = useMutation({
    mutationFn: (resource: ExperimentVideoPointResource) =>
      api<Record<string, unknown>>(`/api/admin/media/bindings/${resource.binding_id}`, { method: "DELETE" }),
    onMutate: (resource) => {
      setPendingVideoBindingAction({ bindingId: resource.binding_id, action: "delete" });
    },
    onSuccess: (_, resource) => {
      message.success("视频引用已移除");
      invalidateVideoReferenceData(resource.experiment_id);
    },
    onError: (error) => message.error(errorMessage(error)),
    onSettled: () => setPendingVideoBindingAction(null),
  });

  const isVideoBindingActionPending = (resource: ExperimentVideoPointResource, action: "publish" | "unpublish" | "delete") =>
    pendingVideoBindingAction?.bindingId === resource.binding_id && pendingVideoBindingAction.action === action;
  const isVideoBindingBusy = (resource: ExperimentVideoPointResource) => pendingVideoBindingAction?.bindingId === resource.binding_id;

  const chapterTitleById = useMemo(() => {
    const values = new Map(theoryChapters.map((chapter) => [chapter.chapter_id, formatChapterTitle(chapter.chapter_title, chapter.chapter_id)]));
    (chapters.data || []).forEach((chapter) => {
      values.set(chapter.chapter_id, formatChapterTitle(chapter.chapter_title, chapter.chapter_id));
    });
    return values;
  }, [chapters.data]);
  const chapterOptions = (chapters.data || []).map((chapter) => ({
    value: chapter.chapter_id,
    label: formatChapterTitle(chapter.chapter_title, chapter.chapter_id),
  }));
  const scopedExperiments = experiments.data?.items || [];
  const filteredExperiments = useMemo(() => {
    const keyword = experimentKeyword.trim().toLowerCase();
    if (!keyword) return scopedExperiments;
    return scopedExperiments.filter((experiment) => experiment.title.toLowerCase().includes(keyword));
  }, [experimentKeyword, scopedExperiments]);
  const statusSummary = useMemo(
    () =>
      scopedExperiments.reduce(
        (summary, experiment) => {
          summary.total += 1;
          if (experiment.status === "draft") summary.draft += 1;
          if (experiment.status === "published") summary.published += 1;
          if (experiment.status === "archived") summary.archived += 1;
          return summary;
        },
        { total: 0, draft: 0, published: 0, archived: 0 },
      ),
    [scopedExperiments],
  );
  const hasFilters = Boolean(experimentKeyword || chapterId || statusFilter);

  return (
    <Space direction="vertical" size={18} className="full">
      <PageTitle
        title="实验管理"
        description="管理实验元信息、理论章节与发布状态；视频素材库作为独立模块维护。"
        extra={
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateOpen(true)}>
            新建实验
          </Button>
        }
      />
      <Card className="toolbar-card">
        <Space direction="vertical" size={14} className="full">
          <Flex justify="space-between" align="center" gap={14} wrap="wrap">
            <Space size={12} wrap className="experiment-filter-controls">
              <Text className="filter-group-label">筛选范围</Text>
              <Select
                allowClear
                placeholder="全部章节"
                style={{ width: 300 }}
                value={chapterId}
                onChange={setChapterId}
                options={chapterOptions}
              />
              <Select
                allowClear
                placeholder="全部状态"
                style={{ width: 160 }}
                value={statusFilter}
                onChange={setStatusFilter}
                options={[
                  { value: "draft", label: "草稿" },
                  { value: "published", label: "已发布" },
                  { value: "archived", label: "已归档" },
                ]}
              />
            </Space>
            <Input.Search
              allowClear
              placeholder="搜索实验名称"
              value={experimentKeyword}
              onChange={(event) => setExperimentKeyword(event.target.value)}
              style={{ width: 320 }}
            />
          </Flex>
          <Flex justify="space-between" align="center" gap={14} wrap="wrap">
            <Space size={8} wrap className="experiment-filter-summary">
              {experiments.isLoading ? (
                <Text type="secondary">正在加载实验...</Text>
              ) : (
                <>
                  <Text type="secondary">当前范围共 {statusSummary.total} 个实验</Text>
                  <Tag>草稿 {statusSummary.draft}</Tag>
                  <Tag color="green">已发布 {statusSummary.published}</Tag>
                  <Tag>已归档 {statusSummary.archived}</Tag>
                  {experimentKeyword.trim() ? <Tag color="blue">搜索结果 {filteredExperiments.length}</Tag> : null}
                </>
              )}
            </Space>
            <Button
              disabled={!hasFilters}
              onClick={() => {
                setExperimentKeyword("");
                setChapterId(undefined);
                setStatusFilter(undefined);
              }}
            >
              重置筛选
            </Button>
          </Flex>
        </Space>
      </Card>
      <Card>
        <QueryState loading={experiments.isLoading} error={experiments.error} empty={!filteredExperiments.length}>
          <Table
            rowKey="id"
            dataSource={filteredExperiments}
            columns={[
              { title: "序号", dataIndex: "display_order", width: 88 },
              {
                title: "实验",
                render: (_: unknown, row: Experiment) => (
                  <Space direction="vertical" size={2}>
                    <Text strong>{row.title}</Text>
                    <Text type="secondary">{row.summary}</Text>
                  </Space>
                ),
              },
              {
                title: "理论章节",
                render: (_: unknown, row: Experiment) => (
                  <Space wrap>
                    {row.chapter_bindings.map((binding) => (
                      <Tag key={binding.chapter_id}>
                        {formatChapterTitle(binding.chapter_title || chapterTitleById.get(binding.chapter_id), binding.chapter_id)}
                      </Tag>
                    ))}
                  </Space>
                ),
              },
              {
                title: "资源",
                width: 170,
                render: (_: unknown, row: Experiment) => (
                  <Space size={6} wrap>
                    <Tag>点位 {experimentVideoCandidates(row).length}</Tag>
                    <Tag color={row.media_resources.length ? "#356f9c" : "default"}>视频 {row.media_resources.length}</Tag>
                  </Space>
                ),
              },
              { title: "状态", width: 110, render: (_: unknown, row: Experiment) => statusTag(row.status) },
              {
                title: "操作",
                width: 90,
                render: (_: unknown, row: Experiment) => (
                  <Button onClick={() => setSelected(row)}>编辑</Button>
                ),
              },
            ]}
          />
        </QueryState>
      </Card>
      <Drawer
        title={currentExperiment ? `编辑实验：${currentExperiment.title}` : "编辑实验"}
        open={Boolean(selected)}
        onClose={() => setSelected(null)}
        width={1180}
        className="experiment-editor-drawer"
      >
        <QueryState loading={selectedExperiment.isLoading} error={selectedExperiment.error} empty={!currentExperiment}>
          <Space direction="vertical" size={16} className="full">
            {currentExperiment ? (
              <div className="experiment-editor-summary">
                <Flex justify="space-between" gap={18} wrap="wrap" align="center">
                  <div className="experiment-editor-summary-main">
                    <Space size={8} wrap>
                      {statusTag(currentExperiment.status)}
                      {currentExperiment.chapter_bindings.slice(0, 3).map((binding) => (
                        <Tag key={binding.chapter_id}>
                          {formatChapterTitle(binding.chapter_title || chapterTitleById.get(binding.chapter_id), binding.chapter_id)}
                        </Tag>
                      ))}
                    </Space>
                    <Title level={4}>{currentExperiment.title}</Title>
                    <Text type="secondary">{currentExperiment.summary || "暂无实验说明"}</Text>
                  </div>
                  <div className="experiment-editor-metrics">
                    <Statistic title="视频点位" value={videoPointCount} />
                    <Statistic title="关联资源" value={resourceCount} />
                    <Statistic title="已发布" value={publishedResourceCount} />
                  </div>
                </Flex>
              </div>
            ) : null}

            <div className="experiment-editor-grid">
              <Space direction="vertical" size={16} className="full">
                <Card title="基础信息" className="experiment-basic-card">
                  <Form form={form} layout="vertical" onFinish={(values) => save.mutate(values)}>
                    <Form.Item name="title" label="实验名称" rules={[{ required: true, message: "请输入实验名称" }]}>
                      <Input />
                    </Form.Item>
                    <Form.Item name="summary" label="实验说明">
                      <Input.TextArea rows={4} maxLength={300} showCount className="fixed-textarea" />
                    </Form.Item>
                    <div className="compact-form-grid">
                      <Form.Item name="status" label="发布状态" rules={[{ required: true }]}>
                        <Select
                          options={[
                            { value: "draft", label: "草稿" },
                            { value: "published", label: "已发布" },
                            { value: "archived", label: "已归档" },
                          ]}
                        />
                      </Form.Item>
                      <Form.Item name="chapter_ids" label="理论章节" rules={[{ required: true, message: "请选择至少一个章节" }]}>
                        <Select mode="multiple" options={chapterOptions} placeholder="选择章节" maxTagCount="responsive" />
                      </Form.Item>
                    </div>
                    <Button type="primary" htmlType="submit" loading={save.isPending}>
                      保存实验信息
                    </Button>
                  </Form>
                </Card>

                <Card title="来源上下文" className="experiment-context-card">
                  {parentTitle || moduleTitle ? (
                    <Descriptions
                      size="small"
                      column={1}
                      items={[
                        ...(parentTitle ? [{ key: "parent", label: "来源大类", children: parentTitle }] : []),
                        ...(moduleTitle ? [{ key: "module", label: "目录模块", children: moduleTitle }] : []),
                      ]}
                    />
                  ) : (
                    <Text type="secondary">暂无来源上下文</Text>
                  )}
                </Card>
              </Space>

              <Card
                title={
                  <Flex justify="space-between" align="center" gap={12} wrap="wrap">
                    <span>点位视频引用</span>
                    <Space size={6} wrap>
                      <Tag>点位 {videoPointCount}</Tag>
                      <Tag color={resourceCount ? "blue" : "default"}>已引用 {resourceCount}</Tag>
                      <Tag color={publishedResourceCount ? "green" : "default"}>已发布 {publishedResourceCount}</Tag>
                    </Space>
                  </Flex>
                }
                className="video-reference-card"
              >
                <Space direction="vertical" size={14} className="full">
                  <Flex justify="space-between" align="center" gap={12} wrap="wrap" className="video-reference-toolbar">
                    <Segmented
                      value={videoPointFilter}
                      onChange={(value) => setVideoPointFilter(value as VideoPointFilter)}
                      options={[
                        { value: "all", label: "全部" },
                        { value: "empty", label: "未引用" },
                        { value: "referenced", label: "已引用" },
                        { value: "published", label: "已发布" },
                      ]}
                    />
                    <Text type="secondary">从视频资源库选择已上传视频，引用到具体候选点。</Text>
                  </Flex>

                  {experimentVideoPoints.isLoading ? (
                    <div className="center-panel">
                      <Spin />
                    </div>
                  ) : experimentVideoPoints.error ? (
                    <Alert type="error" showIcon title="点位视频加载失败" description={errorMessage(experimentVideoPoints.error)} />
                  ) : !videoPointItems.length ? (
                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无候选视频点位" />
                  ) : !filteredVideoPoints.length ? (
                    <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="当前筛选下没有点位" />
                  ) : (
                    <div className="video-point-list">
                      {filteredVideoPoints.map((point) => {
                        const pointIndex = videoPointItems.findIndex((item) => item.point_key === point.point_key) + 1;
                        return (
                          <div className="video-point-card" key={point.point_key}>
                            <Flex justify="space-between" align="start" gap={12} wrap="wrap" className="video-point-header">
                              <Space size={12} align="start" className="video-point-heading">
                                <span className="video-point-index">{pointIndex}</span>
                                <div className="video-point-title">
                                  <Text strong>{point.point_title}</Text>
                                  <Space size={6} wrap>
                                    <Tag color={point.resource_count ? "blue" : "default"}>已引用 {point.resource_count}</Tag>
                                    <Tag color={point.published_count ? "green" : "default"}>已发布 {point.published_count}</Tag>
                                  </Space>
                                </div>
                              </Space>
                              <Button type={point.resource_count ? "default" : "primary"} icon={<PlusOutlined />} onClick={() => setReferencePoint(point)}>
                                引用视频
                              </Button>
                            </Flex>

                            {point.resources.length ? (
                              <div className="video-point-resources">
                                {point.resources.map((resource) => {
                                  const resourceTitle =
                                    resource.media_title || resource.title || resource.binding_title || resource.original_file_name;
                                  const thumbnailSrc = resource.thumbnail_relative_path
                                    ? `${apiBase}/api/admin/media/assets/${resource.media_id}/thumbnail`
                                    : null;
                                  const resourceBusy = isVideoBindingBusy(resource);
                                  const openResourcePreview = () =>
                                    setPreviewTarget({
                                      id: resource.media_id,
                                      title: resource.media_title || resourceTitle,
                                      original_file_name: resource.original_file_name,
                                      mime_type: resource.mime_type,
                                      upload_status: resource.upload_status,
                                    });
                                  return (
                                  <div className="video-point-resource" key={resource.binding_id}>
                                    <button
                                      type="button"
                                      className={thumbnailSrc ? "video-resource-thumb has-image" : "video-resource-thumb"}
                                      disabled={resource.upload_status !== "ready"}
                                      aria-label={`预览视频：${resourceTitle}`}
                                      title={resource.upload_status === "ready" ? "预览视频" : "视频未就绪，暂不能预览"}
                                      onClick={openResourcePreview}
                                    >
                                      <AuthenticatedImage src={thumbnailSrc} alt={resourceTitle} className="video-resource-thumb-image" />
                                      <div className="video-resource-thumb-fallback">
                                        <VideoCameraOutlined />
                                      </div>
                                      {resource.upload_status === "ready" ? (
                                        <span className="video-resource-thumb-play">
                                          <PlayCircleOutlined />
                                        </span>
                                      ) : null}
                                    </button>
                                    <div className="video-point-resource-main">
                                      <Text strong className="video-point-resource-title">
                                        {resourceTitle}
                                      </Text>
                                      <Text type="secondary" className="video-point-resource-file">
                                        {resource.original_file_name}
                                      </Text>
                                      <Space size={6} wrap>
                                        {statusTag(resource.upload_status)}
                                        {statusTag(resource.binding_status)}
                                        <Text type="secondary">{formatBytes(resource.file_size_bytes)}</Text>
                                      </Space>
                                    </div>
                                    <Space size={8} wrap className="video-point-resource-actions">
                                      {resource.binding_status === "published" ? (
                                        <Button
                                          size="small"
                                          icon={<PauseCircleOutlined />}
                                          disabled={resourceBusy}
                                          loading={isVideoBindingActionPending(resource, "unpublish")}
                                          onClick={() => unpublishPointResource.mutate(resource)}
                                        >
                                          取消发布
                                        </Button>
                                      ) : (
                                        <Button
                                          size="small"
                                          type="primary"
                                          icon={<CheckCircleOutlined />}
                                          disabled={resource.upload_status !== "ready" || resourceBusy}
                                          loading={isVideoBindingActionPending(resource, "publish")}
                                          onClick={() => publishPointResource.mutate(resource)}
                                        >
                                          发布引用
                                        </Button>
                                      )}
                                      <Popconfirm
                                        title="移除视频引用？"
                                        description="只删除本实验点位和该视频的引用关系，不删除视频资源库素材。"
                                        okText="移除"
                                        cancelText="取消"
                                        okButtonProps={{ danger: true }}
                                        onConfirm={() => deletePointResource.mutate(resource)}
                                      >
                                        <Button
                                          size="small"
                                          danger
                                          icon={<DeleteOutlined />}
                                          disabled={resourceBusy}
                                          loading={isVideoBindingActionPending(resource, "delete")}
                                        >
                                          移除引用
                                        </Button>
                                      </Popconfirm>
                                    </Space>
                                  </div>
                                  );
                                })}
                              </div>
                            ) : (
                              <button type="button" className="video-point-empty" onClick={() => setReferencePoint(point)}>
                                <PlusOutlined />
                                <span>还没有引用视频</span>
                                <Text type="secondary">点击从视频资源库选择素材</Text>
                              </button>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </Space>
              </Card>
            </div>
          </Space>
        </QueryState>
      </Drawer>

      <Modal
        title={referencePoint ? `为「${referencePoint.point_title}」引用视频` : "引用视频"}
        open={Boolean(referencePoint)}
        width={980}
        onCancel={() => setReferencePoint(null)}
        footer={[
          <Button key="cancel" onClick={() => setReferencePoint(null)}>
            取消
          </Button>,
          <Button
            key="save"
            type="primary"
            loading={addPointResources.isPending}
            disabled={!selectedAssetIds.length}
            onClick={() => addPointResources.mutate()}
          >
            保存引用
          </Button>,
        ]}
      >
        <Space direction="vertical" size={14} className="full">
          <Alert
            type="info"
            showIcon
            message="这里不会上传新视频，只从视频资源库引用已上传素材。保存后默认是草稿引用，需要发布后学生端才可见。"
          />
          <Flex justify="space-between" align="center" gap={12} wrap="wrap">
            <Input.Search
              allowClear
              placeholder="搜索视频标题或文件名"
              value={assetKeyword}
              onChange={(event) => setAssetKeyword(event.target.value)}
              style={{ width: 360 }}
            />
            <Text type="secondary">已选择 {selectedAssetIds.length} 个视频</Text>
          </Flex>
          <QueryState loading={mediaAssets.isLoading} error={mediaAssets.error} empty={!referenceAssets.length}>
            <Table
              rowKey="id"
              dataSource={filteredReferenceAssets}
              pagination={{ pageSize: 6, showSizeChanger: false }}
              rowSelection={{
                selectedRowKeys: selectedAssetIds,
                onChange: (keys) => setSelectedAssetIds(keys.map(String)),
                getCheckboxProps: (asset: MediaAsset) => ({
                  disabled: !isPreviewableVideo(asset) || referencedAssetIds.has(asset.id),
                }),
              }}
              columns={[
                {
                  title: "视频资源",
                  render: (_: unknown, asset: MediaAsset) => (
                    <Space size={10} align="start" className="video-asset-name">
                      <div className="video-file-mark">
                        <VideoCameraOutlined />
                      </div>
                      <Space direction="vertical" size={1}>
                        <Text strong>{asset.title}</Text>
                        <Text type="secondary">{asset.original_file_name}</Text>
                      </Space>
                    </Space>
                  ),
                },
                { title: "类型", width: 90, render: (_: unknown, asset: MediaAsset) => mediaAssetType(asset) },
                { title: "大小", width: 100, render: (_: unknown, asset: MediaAsset) => formatBytes(asset.file_size_bytes) },
                { title: "状态", width: 100, render: (_: unknown, asset: MediaAsset) => statusTag(asset.upload_status) },
                {
                  title: "引用状态",
                  width: 130,
                  render: (_: unknown, asset: MediaAsset) => {
                    if (currentPointAssetIds.has(asset.id)) return <Tag color="green">已在此点位</Tag>;
                    if (referencedAssetIds.has(asset.id)) return <Tag>已被本实验引用</Tag>;
                    if (!isPreviewableVideo(asset)) return <Tag>不可引用</Tag>;
                    return <Tag color="blue">可引用</Tag>;
                  },
                },
                {
                  title: "操作",
                  width: 100,
                  render: (_: unknown, asset: MediaAsset) => (
                    <Button
                      size="small"
                      icon={<EyeOutlined />}
                      disabled={!isPreviewableVideo(asset)}
                      onClick={() =>
                        setPreviewTarget({
                          id: asset.id,
                          title: asset.title,
                          original_file_name: asset.original_file_name,
                          mime_type: asset.mime_type,
                          upload_status: asset.upload_status,
                        })
                      }
                    >
                      预览
                    </Button>
                  ),
                },
              ]}
            />
          </QueryState>
        </Space>
      </Modal>

      <Modal
        title={previewTarget?.title || "视频预览"}
        open={Boolean(previewTarget)}
        width={860}
        footer={null}
        onCancel={() => setPreviewTarget(null)}
      >
        <Space direction="vertical" size={14} className="full">
          <Text type="secondary">{previewTarget?.original_file_name}</Text>
          <div className="experiment-video-preview-stage">
            {previewLoading ? (
              <Spin />
            ) : previewError ? (
              <Alert type="error" showIcon title="预览失败" description={previewError} />
            ) : previewUrl ? (
              <video src={previewUrl} controls className="video-preview-player" />
            ) : (
              <Text type="secondary">正在准备预览...</Text>
            )}
          </div>
        </Space>
      </Modal>

      <Modal
        title="新建实验"
        open={createOpen}
        onCancel={() => setCreateOpen(false)}
        footer={[
          <Button key="cancel" onClick={() => setCreateOpen(false)}>
            取消
          </Button>,
          <Button key="draft" loading={createExperiment.isPending} onClick={() => void submitCreateExperiment("draft")}>
            保存为草稿
          </Button>,
          <Button key="publish" type="primary" loading={createExperiment.isPending} onClick={() => void submitCreateExperiment("published")}>
            保存并发布
          </Button>,
        ]}
      >
        <Text type="secondary" className="modal-helper">
          填写实验名称和说明，并选择它要显示在哪些理论章节下。
        </Text>
        <Form form={createForm} layout="vertical">
          <Form.Item name="title" label="实验名称" rules={[{ required: true, message: "请输入实验名称" }]}>
            <Input placeholder="例如：氯、溴、碘的置换次序" />
          </Form.Item>
          <Form.Item name="summary" label="实验说明">
            <Input.TextArea rows={3} maxLength={300} showCount className="fixed-textarea" />
          </Form.Item>
          <Form.Item name="chapter_ids" label="理论章节" rules={[{ required: true, message: "请选择至少一个章节" }]}>
            <Select mode="multiple" options={chapterOptions} placeholder="选择章节" />
          </Form.Item>
        </Form>
      </Modal>
    </Space>
  );
}
