import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  CheckCircleFilled,
  CloudUploadOutlined,
  DeleteOutlined,
  EyeOutlined,
  FilePdfOutlined,
  PauseCircleOutlined,
  ReloadOutlined,
  RocketOutlined,
  StopOutlined,
} from "@ant-design/icons";
import {
  Alert,
  App as AntApp,
  Button,
  Card,
  Collapse,
  Descriptions,
  Drawer,
  Empty,
  Flex,
  Form,
  Input,
  List,
  Modal,
  Progress,
  Select,
  Space,
  Statistic,
  Table,
  Tabs,
  Tag,
  Timeline,
  Tooltip,
  Typography,
  Upload,
} from "antd";
import type { TableColumnsType, UploadFile } from "antd";
import dayjs from "dayjs";

import {
  cancelTextbookJob,
  deactivateTextbook,
  deleteTextbook,
  getTextbookUploadPolicy,
  listTextbookChunks,
  listTextbookJobEvents,
  listTextbookPages,
  listTextbooks,
  publishTextbook,
  retryTextbookJob,
  uploadTextbook,
  type TextbookChunk,
  type TextbookDocument,
  type TextbookIngestionJob,
  type TextbookJobEvent,
  type TextbookPage,
  type TextbookUploadPolicy,
} from "../../api/textbooks";
import { PageTitle } from "../../components/PageTitle";
import { QueryState } from "../../components/QueryState";
import { AssistantMarkdownContent } from "../../lib/assistant-markdown";
import { errorMessage } from "../../lib/errors";
import {
  extractionMethodLabel,
  formatTextbookBytes,
  ingestionStageLabel,
  ingestionStatusColor,
  isActiveTextbook,
  publicationStatusColor,
  publicationStatusLabel,
  qualityIssueLabel,
  qualityPercent,
  textbookAllows,
  textbookSummary,
} from "./textbookDisplay";
import "./textbooks.css";

const { Text, Title } = Typography;
const { Dragger } = Upload;

type UploadFormValues = {
  title: string;
  logicalTextbookKey?: string;
  versionLabel?: string;
};

type DocumentAction = "cancel" | "retry" | "publish" | "rollback" | "deactivate" | "delete";

const actionSuccessText: Record<DocumentAction, string> = {
  cancel: "已请求取消处理",
  retry: "已重新加入处理队列",
  publish: "教材版本已发布",
  rollback: "已回滚到这个教材版本",
  deactivate: "教材版本已停用",
  delete: "教材文件已删除",
};

const publicationFilterOptions = [
  { value: "all", label: "全部状态" },
  { value: "processing", label: "处理中" },
  { value: "review_ready", label: "待审核发布" },
  { value: "published", label: "使用中" },
  { value: "inactive", label: "已停用" },
  { value: "failed", label: "处理失败" },
];

function stringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.map(String) : [];
}

function numericValue(value: unknown): number {
  const parsed = Number(value || 0);
  return Number.isFinite(parsed) ? parsed : 0;
}

function hasDetails(value: unknown): boolean {
  return Boolean(value && typeof value === "object" && Object.keys(value).length);
}

export function TextbooksPage() {
  const { message, modal } = AntApp.useApp();
  const queryClient = useQueryClient();
  const [uploadForm] = Form.useForm<UploadFormValues>();
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadFiles, setUploadFiles] = useState<UploadFile[]>([]);
  const [keyword, setKeyword] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [detailDocument, setDetailDocument] = useState<TextbookDocument | null>(null);

  const documentsQuery = useQuery({
    queryKey: ["textbooks"],
    queryFn: listTextbooks,
  });
  const policyQuery = useQuery({
    queryKey: ["textbook-upload-policy"],
    queryFn: getTextbookUploadPolicy,
  });

  const documents = useMemo(() => documentsQuery.data?.items || [], [documentsQuery.data?.items]);
  const hasActiveWork = documents.some(isActiveTextbook);
  const summary = useMemo(() => textbookSummary(documents), [documents]);
  const filteredDocuments = useMemo(() => {
    const normalized = keyword.trim().toLocaleLowerCase("zh-CN");
    return documents.filter((document) => {
      if (statusFilter !== "all" && document.publication_status !== statusFilter) return false;
      if (!normalized) return true;
      return [document.title, document.file_name, document.logical_textbook_key, document.version_label]
        .filter(Boolean)
        .join(" ")
        .toLocaleLowerCase("zh-CN")
        .includes(normalized);
    });
  }, [documents, keyword, statusFilter]);

  useEffect(() => {
    if (!hasActiveWork) return undefined;
    const timer = window.setInterval(() => {
      void queryClient.invalidateQueries({ queryKey: ["textbooks"] });
      if (detailDocument?.latest_job?.id) {
        void queryClient.invalidateQueries({ queryKey: ["textbook-events", detailDocument.latest_job.id] });
      }
      if (detailDocument?.id) {
        void queryClient.invalidateQueries({ queryKey: ["textbook-pages", detailDocument.id] });
        void queryClient.invalidateQueries({ queryKey: ["textbook-chunks", detailDocument.id] });
      }
    }, 3000);
    return () => window.clearInterval(timer);
  }, [detailDocument?.id, detailDocument?.latest_job?.id, hasActiveWork, queryClient]);

  useEffect(() => {
    if (!detailDocument) return;
    const latest = documents.find((document) => document.id === detailDocument.id);
    if (latest && latest !== detailDocument) setDetailDocument(latest);
  }, [detailDocument, documents]);

  const invalidateDocuments = async () => {
    await queryClient.invalidateQueries({ queryKey: ["textbooks"] });
  };

  const uploadMutation = useMutation({
    mutationFn: uploadTextbook,
    onSuccess: async (document) => {
      message.success("教材已上传，后台处理任务已创建");
      setUploadOpen(false);
      setUploadFiles([]);
      uploadForm.resetFields();
      setDetailDocument(document);
      await invalidateDocuments();
    },
    onError: (error) => message.error(`上传失败：${errorMessage(error)}`),
  });

  const actionMutation = useMutation({
    mutationFn: async ({ action, document }: { action: DocumentAction; document: TextbookDocument }) => {
      if (!textbookAllows(document, action)) throw new Error("当前版本不允许执行这个操作，请刷新页面后重试");
      if (action === "cancel") {
        if (!document.latest_job) throw new Error("未找到可取消的处理任务");
        return cancelTextbookJob(document.latest_job.id);
      }
      if (action === "retry") {
        if (!document.latest_job) throw new Error("未找到可重试的处理任务");
        return retryTextbookJob(document.latest_job.id);
      }
      if (action === "publish" || action === "rollback") return publishTextbook(document.id);
      if (action === "deactivate") return deactivateTextbook(document.id);
      return deleteTextbook(document.id);
    },
    onSuccess: async (_result, variables) => {
      message.success(actionSuccessText[variables.action]);
      if (variables.action === "delete" && detailDocument?.id === variables.document.id) setDetailDocument(null);
      await invalidateDocuments();
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const runDocumentAction = (document: TextbookDocument, action: DocumentAction) => {
    if (!textbookAllows(document, action)) return;
    const submit = () => actionMutation.mutateAsync({ action, document });
    if (action === "delete") {
      modal.confirm({
        title: "永久删除这个教材文件？",
        icon: <DeleteOutlined />,
        content: (
          <Space orientation="vertical" size={6}>
            <Text>{document.title} · 第 {document.version_number} 版</Text>
            <Text type="secondary">将同时清理该版本的派生索引。此操作只在后台明确允许删除时出现，且不能撤销。</Text>
          </Space>
        ),
        okText: "永久删除文件",
        okButtonProps: { danger: true },
        cancelText: "保留",
        onOk: submit,
      });
      return;
    }
    if (action === "deactivate") {
      modal.confirm({
        title: "停用当前教材版本？",
        content: "停用后，RAG 将不再检索这个版本；已有知识点证据会被标记为需要刷新。",
        okText: "确认停用",
        cancelText: "取消",
        onOk: submit,
      });
      return;
    }
    if (action === "publish" || action === "rollback") {
      modal.confirm({
        title: action === "rollback" ? "回滚到这个教材版本？" : "发布这个教材版本？",
        content:
          action === "rollback"
            ? "同一教材当前使用的版本会自动停用，RAG 只会检索回滚后的版本。"
            : "发布后，同一教材的旧版本会自动停用；知识点证据将按新语料刷新。",
        okText: action === "rollback" ? "确认回滚" : "确认发布",
        cancelText: "取消",
        onOk: submit,
      });
      return;
    }
    void submit();
  };

  const submitUpload = (values: UploadFormValues) => {
    const file = uploadFiles[0]?.originFileObj;
    if (!file) {
      message.error("请选择一份 PDF 教材");
      return;
    }
    uploadMutation.mutate({
      title: values.title,
      logicalTextbookKey: values.logicalTextbookKey,
      versionLabel: values.versionLabel,
      file,
    });
  };

  const uploadPolicy = policyQuery.data;
  const columns: TableColumnsType<TextbookDocument> = [
    {
      title: "教材版本",
      key: "document",
      width: 280,
      render: (_value, document) => (
        <div className="textbook-title-cell">
          <span className="textbook-file-mark"><FilePdfOutlined /></span>
          <div>
            <Space size={7} wrap>
              <Text strong>{document.title}</Text>
              <Tag bordered={false}>v{document.version_number}{document.version_label ? ` · ${document.version_label}` : ""}</Tag>
            </Space>
            <Text type="secondary" ellipsis={{ tooltip: document.file_name }}>{document.file_name}</Text>
            <span className="textbook-key">{document.logical_textbook_key}</span>
          </div>
        </div>
      ),
    },
    {
      title: "上线状态",
      key: "publication_status",
      width: 110,
      render: (_value, document) => (
        <Space orientation="vertical" size={5}>
          <Tag color={publicationStatusColor(document.publication_status)}>{publicationStatusLabel(document.publication_status)}</Tag>
          {document.corpus_revision ? <Text type="secondary">语料修订 {document.corpus_revision}</Text> : null}
        </Space>
      ),
    },
    {
      title: "处理进度",
      key: "job",
      width: 260,
      render: (_value, document) => <JobProgress job={document.latest_job} compact />,
    },
    {
      title: "质量门禁",
      key: "quality",
      width: 170,
      render: (_value, document) => <QualitySummary document={document} />,
    },
    {
      title: "文件",
      key: "file",
      width: 100,
      render: (_value, document) => (
        <Space orientation="vertical" size={2}>
          <Text>{formatTextbookBytes(document.size_bytes)}</Text>
          <Text type="secondary">{document.updated_at ? dayjs(document.updated_at).format("MM-DD HH:mm") : "-"}</Text>
        </Space>
      ),
    },
    {
      title: "操作",
      key: "actions",
      fixed: "right",
      width: 195,
      render: (_value, document) => (
        <Space size={[4, 6]} wrap className="textbook-actions">
          <Button size="small" type="link" icon={<EyeOutlined />} onClick={() => setDetailDocument(document)}>查看</Button>
          {textbookAllows(document, "cancel") ? (
            <Button size="small" type="link" icon={<StopOutlined />} loading={actionMutation.isPending} onClick={() => runDocumentAction(document, "cancel")}>取消</Button>
          ) : null}
          {textbookAllows(document, "retry") ? (
            <Button size="small" type="link" icon={<ReloadOutlined />} loading={actionMutation.isPending} onClick={() => runDocumentAction(document, "retry")}>重试</Button>
          ) : null}
          {textbookAllows(document, "rollback") ? (
            <Button size="small" type="link" icon={<ReloadOutlined />} loading={actionMutation.isPending} onClick={() => runDocumentAction(document, "rollback")}>回滚</Button>
          ) : textbookAllows(document, "publish") ? (
            <Button size="small" type="link" icon={<RocketOutlined />} loading={actionMutation.isPending} onClick={() => runDocumentAction(document, "publish")}>发布</Button>
          ) : null}
          {textbookAllows(document, "deactivate") ? (
            <Button size="small" type="link" icon={<PauseCircleOutlined />} loading={actionMutation.isPending} onClick={() => runDocumentAction(document, "deactivate")}>停用</Button>
          ) : null}
          {textbookAllows(document, "delete") ? (
            <Button danger size="small" type="link" icon={<DeleteOutlined />} loading={actionMutation.isPending} onClick={() => runDocumentAction(document, "delete")}>删除</Button>
          ) : null}
        </Space>
      ),
    },
  ];

  return (
    <Space orientation="vertical" size={18} className="full textbook-page">
      <PageTitle
        title="教材知识库"
        description="在线上传教材，检查文字提取与分块质量，再把通过门禁的版本发布给 RAG。"
        extra={
          <Button
            type="primary"
            icon={<CloudUploadOutlined />}
            disabled={policyQuery.isSuccess && !uploadPolicy?.enabled}
            onClick={() => setUploadOpen(true)}
          >
            上传教材
          </Button>
        }
      />

      <IngestionPipelineGuide policy={uploadPolicy} loading={policyQuery.isLoading} />

      {policyQuery.isError ? (
        <Alert type="error" showIcon title="上传策略读取失败" description={errorMessage(policyQuery.error)} />
      ) : uploadPolicy && !uploadPolicy.enabled ? (
        <Alert type="warning" showIcon title="在线教材处理尚未启用" description="请确认后台已启用教材处理并使用 PostgreSQL 数据后端。" />
      ) : uploadPolicy?.ocr.enabled && !uploadPolicy.ocr.credential_configured ? (
        <Alert
          type="warning"
          showIcon
          title="MinerU 凭证尚未配置"
          description="原生文字层不足的页面会停在“等待 OCR”。配置校内 MinerU 凭证后，可直接重试任务，无需重新上传。"
        />
      ) : null}

      <div className="textbook-stat-grid">
        <Card><Statistic title="教材版本" value={summary.versions} suffix="份" /></Card>
        <Card><Statistic title="RAG 当前使用" value={summary.published} suffix="份" /></Card>
        <Card><Statistic title="后台处理中" value={summary.processing} suffix="份" /></Card>
        <Card><Statistic title="需要处理" value={summary.attention} suffix="份" /></Card>
      </div>

      <Card className="textbook-library-card">
        <Flex justify="space-between" align="center" gap={12} wrap className="textbook-library-toolbar">
          <div>
            <Title level={4}>版本与任务</Title>
            <Text type="secondary">发布、回滚和停用都会影响后续 RAG 可检索的教材版本。</Text>
          </div>
          <Space wrap>
            <Input.Search
              allowClear
              placeholder="搜索教材、文件或逻辑键"
              value={keyword}
              onChange={(event) => setKeyword(event.target.value)}
              style={{ width: 270 }}
            />
            <Select value={statusFilter} options={publicationFilterOptions} onChange={setStatusFilter} style={{ width: 150 }} />
            <Tooltip title="刷新列表">
              <Button icon={<ReloadOutlined />} loading={documentsQuery.isFetching} onClick={() => void documentsQuery.refetch()} />
            </Tooltip>
          </Space>
        </Flex>
        <QueryState loading={documentsQuery.isLoading} error={documentsQuery.error} empty={!documents.length}>
          <Table
            rowKey="id"
            size="middle"
            columns={columns}
            dataSource={filteredDocuments}
            scroll={{ x: 1115 }}
            pagination={{ pageSize: 20, showSizeChanger: true, showTotal: (total) => `共 ${total} 个版本` }}
            locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="没有符合筛选条件的教材" /> }}
          />
        </QueryState>
      </Card>

      <UploadTextbookModal
        open={uploadOpen}
        policy={uploadPolicy}
        form={uploadForm}
        fileList={uploadFiles}
        loading={uploadMutation.isPending}
        onFileListChange={setUploadFiles}
        onCancel={() => {
          if (uploadMutation.isPending) return;
          setUploadOpen(false);
          setUploadFiles([]);
          uploadForm.resetFields();
        }}
        onSubmit={submitUpload}
      />

      <TextbookDetailDrawer
        document={detailDocument}
        open={Boolean(detailDocument)}
        onClose={() => setDetailDocument(null)}
        onAction={runDocumentAction}
        actionPending={actionMutation.isPending}
      />
    </Space>
  );
}

function IngestionPipelineGuide({ policy, loading }: { policy?: TextbookUploadPolicy; loading: boolean }) {
  const stages = [
    ["01", "提取文字", "先读取 PDF 自带文字层"],
    ["02", "按页 OCR", "仅把低质量页面送往 MinerU"],
    ["03", "结构化分块", "保留章节、页码、表格与公式"],
    ["04", "向量与索引", "生成 Embedding 并校验写入数量"],
    ["05", "人工发布", "通过质量门禁后才进入 RAG"],
  ];
  return (
    <Card className="textbook-pipeline-card">
      <div className="textbook-pipeline-heading">
        <div>
          <span className="textbook-pipeline-eyebrow">ONLINE INGESTION</span>
          <Title level={4}>从 PDF 到可追溯的 RAG 语料</Title>
        </div>
        <Space size={6} wrap>
          <Tag color="green">PDF</Tag>
          <Tag>{loading ? "读取上传策略…" : `最大 ${policy?.max_upload_mb || "-"} MB`}</Tag>
          <Tag>{loading ? "" : `最多 ${policy?.max_pages || "-"} 页`}</Tag>
        </Space>
      </div>
      <div className="textbook-pipeline-track">
        {stages.map(([number, title, description]) => (
          <div className="textbook-pipeline-stage" key={number}>
            <span>{number}</span>
            <div><strong>{title}</strong><small>{description}</small></div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function JobProgress({ job, compact = false }: { job?: TextbookIngestionJob | null; compact?: boolean }) {
  if (!job) return <Text type="secondary">尚未创建在线处理任务</Text>;
  const counters = [
    `${job.processed_pages}/${job.total_pages || "?"} 页`,
    `OCR ${job.ocr_pages}`,
    `${job.total_chunks} chunks`,
    `索引 ${job.indexed_chunks}/${job.total_chunks || "?"}`,
  ];
  return (
    <div className={compact ? "textbook-job compact" : "textbook-job"}>
      <Flex justify="space-between" align="center" gap={8}>
        <Tag color={ingestionStatusColor(job.status)}>{ingestionStageLabel(job.status)}</Tag>
        <Text type="secondary">{job.progress}%</Text>
      </Flex>
      <Progress
        percent={job.progress}
        size="small"
        showInfo={false}
        status={job.status === "failed" ? "exception" : job.status === "ready" || job.status === "review_ready" ? "success" : "active"}
      />
      <div className="textbook-counter-line">{counters.map((counter) => <span key={counter}>{counter}</span>)}</div>
      {job.error_message ? <Text type="danger" ellipsis={{ tooltip: job.error_message }}>{job.error_message}</Text> : null}
    </div>
  );
}

function QualitySummary({ document }: { document: TextbookDocument }) {
  const report = document.latest_job?.quality_report || document.quality_summary || {};
  const quality = numericValue(report.average_page_quality);
  const blockers = document.publish_blockers || [];
  if (!document.latest_job) return <Text type="secondary">等待处理后生成</Text>;
  return (
    <Space orientation="vertical" size={5}>
      <Space size={6}>
        {report.publishable ? <Tag color="green">质量通过</Tag> : <Tag color={blockers.length ? "red" : "default"}>未通过</Tag>}
        {quality ? <Text type="secondary">均值 {qualityPercent(quality)}%</Text> : null}
      </Space>
      {blockers.length ? (
        <Text type="secondary" ellipsis={{ tooltip: blockers.map(qualityIssueLabel).join("；") }}>
          {qualityIssueLabel(blockers[0])}{blockers.length > 1 ? ` 等 ${blockers.length} 项` : ""}
        </Text>
      ) : document.can_publish ? <Text type="success">可以发布</Text> : <Text type="secondary">继续等待处理结果</Text>}
    </Space>
  );
}

function UploadTextbookModal({
  open,
  policy,
  form,
  fileList,
  loading,
  onFileListChange,
  onCancel,
  onSubmit,
}: {
  open: boolean;
  policy?: TextbookUploadPolicy;
  form: ReturnType<typeof Form.useForm<UploadFormValues>>[0];
  fileList: UploadFile[];
  loading: boolean;
  onFileListChange: (files: UploadFile[]) => void;
  onCancel: () => void;
  onSubmit: (values: UploadFormValues) => void;
}) {
  const { message } = AntApp.useApp();
  const accept = policy?.allowed_extensions?.join(",") || ".pdf,application/pdf";
  return (
    <Modal
      open={open}
      className="textbook-upload-modal"
      title="上传教材并开始在线处理"
      width={760}
      okText="上传并开始处理"
      cancelText="取消"
      confirmLoading={loading}
      okButtonProps={{ disabled: !policy?.enabled || !fileList.length }}
      mask={{ closable: !loading }}
      closable={!loading}
      onCancel={onCancel}
      onOk={() => form.submit()}
      destroyOnHidden
    >
      <Alert
        type="info"
        showIcon
        title="每次上传都会生成一个独立版本"
        description="同一教材请沿用相同逻辑键。新版本处理完成后由你手动发布，旧版本才会停用；上传不会立即影响 RAG。"
        className="textbook-upload-alert"
      />
      <Form form={form} layout="vertical" requiredMark="optional" onFinish={onSubmit}>
        <Form.Item label="教材 PDF" required>
          <Dragger
            accept={accept}
            maxCount={1}
            fileList={fileList}
            disabled={loading || !policy?.enabled}
            beforeUpload={(file) => {
              if (!file.name.toLocaleLowerCase().endsWith(".pdf")) {
                message.error("教材仅支持 PDF 文件");
                return Upload.LIST_IGNORE;
              }
              if (policy?.max_upload_bytes && file.size > policy.max_upload_bytes) {
                message.error(`文件不能超过 ${policy.max_upload_mb} MB`);
                return Upload.LIST_IGNORE;
              }
              onFileListChange([{ uid: file.uid, name: file.name, size: file.size, type: file.type, status: "done", originFileObj: file }]);
              if (!form.getFieldValue("title")) form.setFieldValue("title", file.name.replace(/\.pdf$/i, ""));
              return false;
            }}
            onRemove={() => {
              onFileListChange([]);
              return true;
            }}
          >
            <p className="ant-upload-drag-icon"><FilePdfOutlined /></p>
            <p className="ant-upload-text">拖入教材 PDF，或点击选择文件</p>
            <p className="ant-upload-hint">
              最大 {policy?.max_upload_mb || "-"} MB、{policy?.max_pages || "-"} 页。系统会先尝试原文提取，只对低质量页调用校内 MinerU。
            </p>
          </Dragger>
        </Form.Item>
        <div className="textbook-upload-form-grid">
          <Form.Item label="教材标题" name="title" rules={[{ required: true, message: "请输入教材标题" }, { max: 300 }]}>
            <Input placeholder="例如：无机化学（下册）（第二版）" />
          </Form.Item>
          <Form.Item label="版本标签" name="versionLabel" tooltip="用于教师识别，不决定版本号">
            <Input placeholder="例如：第二版 / 2026 春" maxLength={120} />
          </Form.Item>
        </div>
        <Form.Item
          label="逻辑教材键"
          name="logicalTextbookKey"
          tooltip="同一本教材的不同上传版本必须使用同一个逻辑键，才能自动替换和回滚"
          extra="建议使用稳定的英文短键，例如 inorganic-chemistry-vol-2。首次可留空由后台生成，后续版本请复制列表中的逻辑键。"
        >
          <Input placeholder="inorganic-chemistry-vol-2" maxLength={128} />
        </Form.Item>
      </Form>
    </Modal>
  );
}

function TextbookDetailDrawer({
  document,
  open,
  onClose,
  onAction,
  actionPending,
}: {
  document: TextbookDocument | null;
  open: boolean;
  onClose: () => void;
  onAction: (document: TextbookDocument, action: DocumentAction) => void;
  actionPending: boolean;
}) {
  const documentId = document?.id || "";
  const jobId = document?.latest_job?.id || "";
  const [activeTab, setActiveTab] = useState("overview");
  useEffect(() => setActiveTab("overview"), [documentId]);
  const pagesQuery = useQuery({
    queryKey: ["textbook-pages", documentId],
    queryFn: () => listTextbookPages(documentId),
    enabled: open && activeTab === "pages" && Boolean(documentId),
  });
  const chunksQuery = useQuery({
    queryKey: ["textbook-chunks", documentId],
    queryFn: () => listTextbookChunks(documentId),
    enabled: open && activeTab === "chunks" && Boolean(documentId),
  });
  const eventsQuery = useQuery({
    queryKey: ["textbook-events", jobId],
    queryFn: () => listTextbookJobEvents(jobId),
    enabled: open && activeTab === "events" && Boolean(jobId),
  });

  return (
    <Drawer
      open={open}
      onClose={onClose}
      title={document ? `${document.title} · v${document.version_number}` : "教材详情"}
      size="large"
      destroyOnHidden
      extra={document ? <DocumentActionButtons document={document} pending={actionPending} onAction={onAction} /> : null}
    >
      {document ? (
        <Space orientation="vertical" size={18} className="full textbook-drawer-content">
          <Descriptions size="small" column={2} bordered>
            <Descriptions.Item label="上线状态"><Tag color={publicationStatusColor(document.publication_status)}>{publicationStatusLabel(document.publication_status)}</Tag></Descriptions.Item>
            <Descriptions.Item label="版本">v{document.version_number}{document.version_label ? ` · ${document.version_label}` : ""}</Descriptions.Item>
            <Descriptions.Item label="逻辑键"><Text copyable>{document.logical_textbook_key}</Text></Descriptions.Item>
            <Descriptions.Item label="文件">{document.file_name} · {formatTextbookBytes(document.size_bytes)}</Descriptions.Item>
            <Descriptions.Item label="上传时间">{document.created_at ? dayjs(document.created_at).format("YYYY-MM-DD HH:mm:ss") : "-"}</Descriptions.Item>
            <Descriptions.Item label="语料修订">{document.corpus_revision || "尚未发布"}</Descriptions.Item>
          </Descriptions>

          {document.latest_job?.error_message ? (
            <Alert
              type="error"
              showIcon
              title={`${document.latest_job.error_code || "处理失败"} · ${ingestionStageLabel(document.latest_job.status)}`}
              description={document.latest_job.error_message}
            />
          ) : null}

          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            items={[
              {
                key: "overview",
                label: "处理与质量",
                children: <TextbookOverview document={document} />,
              },
              {
                key: "pages",
                label: `页面 ${pagesQuery.data?.total ?? ""}`,
                children: <PagesPreview query={pagesQuery} />,
              },
              {
                key: "chunks",
                label: `分块 ${chunksQuery.data?.total ?? ""}`,
                children: <ChunksPreview query={chunksQuery} />,
              },
              {
                key: "events",
                label: `处理日志 ${eventsQuery.data?.total ?? ""}`,
                children: <EventsPreview query={eventsQuery} />,
              },
            ]}
          />
        </Space>
      ) : null}
    </Drawer>
  );
}

function DocumentActionButtons({
  document,
  pending,
  onAction,
}: {
  document: TextbookDocument;
  pending: boolean;
  onAction: (document: TextbookDocument, action: DocumentAction) => void;
}) {
  return (
    <Space wrap>
      {textbookAllows(document, "cancel") ? <Button loading={pending} onClick={() => onAction(document, "cancel")}>取消处理</Button> : null}
      {textbookAllows(document, "retry") ? <Button icon={<ReloadOutlined />} loading={pending} onClick={() => onAction(document, "retry")}>重试</Button> : null}
      {textbookAllows(document, "rollback") ? (
        <Button type="primary" icon={<ReloadOutlined />} loading={pending} onClick={() => onAction(document, "rollback")}>回滚到此版本</Button>
      ) : textbookAllows(document, "publish") ? (
        <Button type="primary" icon={<RocketOutlined />} loading={pending} onClick={() => onAction(document, "publish")}>发布</Button>
      ) : null}
      {textbookAllows(document, "deactivate") ? <Button icon={<PauseCircleOutlined />} loading={pending} onClick={() => onAction(document, "deactivate")}>停用</Button> : null}
      {textbookAllows(document, "delete") ? <Button danger icon={<DeleteOutlined />} loading={pending} onClick={() => onAction(document, "delete")}>删除</Button> : null}
    </Space>
  );
}

function TextbookOverview({ document }: { document: TextbookDocument }) {
  const job = document.latest_job;
  const report = job?.quality_report || {};
  const warnings = stringArray(report.warnings);
  const blockers = document.publish_blockers || [];
  const ocr = document.ocr || {};
  return (
    <Space orientation="vertical" size={18} className="full">
      <JobProgress job={job} />
      <div className="textbook-detail-metrics">
        <Card size="small"><Statistic title="页面" value={job?.processed_pages || 0} suffix={`/ ${job?.total_pages || 0}`} /></Card>
        <Card size="small"><Statistic title="OCR 页面" value={job?.ocr_pages || 0} /></Card>
        <Card size="small"><Statistic title="结构化分块" value={job?.total_chunks || 0} /></Card>
        <Card size="small"><Statistic title="已写入索引" value={job?.indexed_chunks || 0} suffix={`/ ${job?.total_chunks || 0}`} /></Card>
      </div>
      <Card size="small" title="质量门禁" extra={report.publishable ? <Tag color="green" icon={<CheckCircleFilled />}>通过</Tag> : <Tag color="red">未通过</Tag>}>
        <div className="textbook-quality-score">
          <Progress type="dashboard" percent={qualityPercent(numericValue(report.average_page_quality))} size={108} />
          <Descriptions size="small" column={2} className="textbook-quality-descriptions">
            <Descriptions.Item label="原文提取页">{numericValue(report.native_page_count)}</Descriptions.Item>
            <Descriptions.Item label="MinerU 页">{numericValue(report.ocr_page_count)}</Descriptions.Item>
            <Descriptions.Item label="混合提取页">{numericValue(report.mixed_page_count)}</Descriptions.Item>
            <Descriptions.Item label="低质量页">{stringArray(report.low_quality_pages).length}</Descriptions.Item>
          </Descriptions>
        </div>
        {blockers.length ? (
          <Alert
            type="error"
            showIcon
            title="暂时不能发布"
            description={<Space wrap>{blockers.map((issue) => <Tag color="red" key={issue}>{qualityIssueLabel(issue)}</Tag>)}</Space>}
          />
        ) : null}
        {warnings.length ? (
          <div className="textbook-quality-flags"><Text type="secondary">质量提示</Text><Space wrap>{warnings.map((warning) => <Tag color="gold" key={warning}>{qualityIssueLabel(warning)}</Tag>)}</Space></div>
        ) : null}
      </Card>
      <Card size="small" title="OCR 与索引校验">
        <Descriptions size="small" column={2}>
          <Descriptions.Item label="OCR 服务">{ocr.provider || "未使用"}</Descriptions.Item>
          <Descriptions.Item label="OCR 模型">{ocr.model || "-"}</Descriptions.Item>
          <Descriptions.Item label="凭证状态">{ocr.enabled ? ocr.credential_configured ? <Tag color="green">已配置</Tag> : <Tag color="orange">未配置</Tag> : <Tag>未启用</Tag>}</Descriptions.Item>
          <Descriptions.Item label="索引校验">{job?.outputs?.index_verified ? <Tag color="green">数量一致</Tag> : <Tag>尚未完成</Tag>}</Descriptions.Item>
          <Descriptions.Item label="尝试次数">{job ? `${job.attempts} / ${job.max_attempts}` : "-"}</Descriptions.Item>
          <Descriptions.Item label="任务更新时间">{job?.updated_at ? dayjs(job.updated_at).format("YYYY-MM-DD HH:mm:ss") : "-"}</Descriptions.Item>
        </Descriptions>
      </Card>
    </Space>
  );
}

type ListQuery<T> = {
  data?: { items: T[]; total: number };
  isLoading: boolean;
  error: unknown;
};

function PagesPreview({ query }: { query: ListQuery<TextbookPage> }) {
  return (
    <QueryState loading={query.isLoading} error={query.error} empty={!query.data?.items.length}>
      <List
        dataSource={query.data?.items || []}
        pagination={{ pageSize: 10, showSizeChanger: false, showTotal: (total) => `共 ${total} 页` }}
        renderItem={(page) => (
          <List.Item className="textbook-preview-list-item">
            <Collapse
              size="small"
              items={[{
                key: String(page.page_number),
                label: (
                  <Flex align="center" justify="space-between" gap={10} className="textbook-preview-label">
                    <Space wrap>
                      <Text strong>第 {page.page_number} 页</Text>
                      <Tag color={page.needs_ocr ? "orange" : "default"}>{extractionMethodLabel(page.extraction_method)}</Tag>
                      {page.quality_flags.map((flag) => <Tag color="gold" key={flag}>{qualityIssueLabel(flag)}</Tag>)}
                    </Space>
                    <Text type="secondary">质量 {qualityPercent(page.quality_score)}%</Text>
                  </Flex>
                ),
                children: (
                  <div className="textbook-markdown-preview">
                    <AssistantMarkdownContent text={page.markdown || page.text || "（此页未提取到文字）"} />
                    {hasDetails(page.diagnostics) ? <details><summary>提取诊断</summary><pre>{JSON.stringify(page.diagnostics, null, 2)}</pre></details> : null}
                  </div>
                ),
              }]}
            />
          </List.Item>
        )}
      />
    </QueryState>
  );
}

function ChunksPreview({ query }: { query: ListQuery<TextbookChunk> }) {
  return (
    <QueryState loading={query.isLoading} error={query.error} empty={!query.data?.items.length}>
      <List
        dataSource={query.data?.items || []}
        pagination={{ pageSize: 12, showSizeChanger: false, showTotal: (total) => `共 ${total} 个分块` }}
        renderItem={(chunk) => (
          <List.Item className="textbook-preview-list-item">
            <Collapse
              size="small"
              items={[{
                key: chunk.id,
                label: (
                  <Flex align="center" justify="space-between" gap={10} className="textbook-preview-label">
                    <Space wrap>
                      <Text strong>#{chunk.chunk_index} {chunk.section_title || "未命名章节"}</Text>
                      <Tag>第 {chunk.page_start}{chunk.page_end !== chunk.page_start ? `–${chunk.page_end}` : ""} 页</Tag>
                      <Tag color={chunk.review_required ? "orange" : "blue"}>{chunk.content_type}</Tag>
                    </Space>
                    <Text type="secondary">{chunk.text.length} 字符</Text>
                  </Flex>
                ),
                children: (
                  <div className="textbook-markdown-preview">
                    {chunk.section_path?.length ? <div className="textbook-section-path">{chunk.section_path.join(" / ")}</div> : null}
                    <AssistantMarkdownContent text={chunk.markdown || chunk.text} />
                    <Text type="secondary" copyable={{ text: chunk.id }}>Chunk ID: {chunk.id}</Text>
                  </div>
                ),
              }]}
            />
          </List.Item>
        )}
      />
    </QueryState>
  );
}

function EventsPreview({ query }: { query: ListQuery<TextbookJobEvent> }) {
  return (
    <QueryState loading={query.isLoading} error={query.error} empty={!query.data?.items.length}>
      <Timeline
        className="textbook-event-timeline"
        items={(query.data?.items || []).slice().reverse().map((event) => ({
          color: event.status === "failed" ? "red" : event.status === "review_ready" || event.status === "ready" ? "green" : "blue",
          children: (
            <div className="textbook-event-entry">
              <Flex justify="space-between" align="center" gap={10}>
                <Space wrap><Tag color={ingestionStatusColor(event.status)}>{ingestionStageLabel(event.status)}</Tag><Text strong>{event.message || event.event_type}</Text></Space>
                <Text type="secondary">{dayjs(event.created_at).format("MM-DD HH:mm:ss")} · {event.progress}%</Text>
              </Flex>
              {event.message && event.message !== event.event_type ? <Text type="secondary">{event.event_type}</Text> : null}
              {hasDetails(event.details) ? <details><summary>事件数据</summary><pre>{JSON.stringify(event.details, null, 2)}</pre></details> : null}
            </div>
          ),
        }))}
      />
    </QueryState>
  );
}
