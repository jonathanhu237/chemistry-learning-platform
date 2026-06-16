import { useEffect, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Alert,
  App as AntApp,
  Button,
  Card,
  Descriptions,
  Drawer,
  Empty,
  Flex,
  Input,
  Select,
  Segmented,
  Space,
  Statistic,
  Table,
  Tag,
  Typography,
} from "antd";
import dayjs from "dayjs";

import { api, patchJson } from "../../api";
import type {
  ClassItem,
  FeedbackItem,
  FeedbackListResponse,
  FeedbackStatus,
  FeedbackSummary,
  FeedbackType,
  FeedbackUpdate,
} from "../../api";
import { PageTitle } from "../../components/PageTitle";
import { QueryState } from "../../components/QueryState";
import "./feedback.css";

const { Text, Title } = Typography;

function formatDateTime(value?: string | null) {
  if (!value) return "-";
  return dayjs(value).format("YYYY-MM-DD HH:mm");
}

function errorMessage(error: unknown) {
  if (error instanceof Error) return error.message;
  return String(error || "????");
}

const feedbackStatusLabels: Record<FeedbackStatus, string> = {
  open: "未处理",
  in_progress: "处理中",
  resolved: "已解决",
  archived: "已归档",
};

const feedbackStatusColors: Record<FeedbackStatus, string> = {
  open: "#b8892f",
  in_progress: "#356f9c",
  resolved: "#005826",
  archived: "default",
};

const feedbackTypeLabels: Record<FeedbackType, string> = {
  course_content: "课程内容",
  experiment_resource: "实验资源",
  ai_answer: "AI 回答",
  system_issue: "系统问题",
  other: "其他",
};

function feedbackStatusTag(status?: FeedbackStatus) {
  if (!status) return <Tag>-</Tag>;
  return <Tag color={feedbackStatusColors[status]}>{feedbackStatusLabels[status]}</Tag>;
}

function feedbackTypeTag(type?: FeedbackType) {
  if (!type) return <Tag>-</Tag>;
  return <Tag>{feedbackTypeLabels[type]}</Tag>;
}

export function FeedbackPage() {
  const { message } = AntApp.useApp();
  const queryClient = useQueryClient();
  const [statusFilter, setStatusFilter] = useState<FeedbackStatus | "all">("all");
  const [typeFilter, setTypeFilter] = useState<FeedbackType | "all">("all");
  const [classFilter, setClassFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [selectedFeedbackId, setSelectedFeedbackId] = useState<string>();
  const [draftStatus, setDraftStatus] = useState<FeedbackStatus>("open");
  const [draftNote, setDraftNote] = useState("");

  const classes = useQuery({ queryKey: ["classes"], queryFn: () => api<ClassItem[]>("/api/admin/classes") });
  const summary = useQuery({
    queryKey: ["feedback-summary"],
    queryFn: () => api<FeedbackSummary>("/api/admin/feedback/summary"),
  });
  const feedbackList = useQuery({
    queryKey: ["feedback-list", statusFilter, typeFilter, classFilter, search],
    queryFn: () => {
      const params = new URLSearchParams({ limit: "200" });
      if (statusFilter !== "all") params.set("status", statusFilter);
      if (typeFilter !== "all") params.set("feedback_type", typeFilter);
      if (classFilter !== "all") params.set("class_id", classFilter);
      if (search.trim()) params.set("search", search.trim());
      return api<FeedbackListResponse>(`/api/admin/feedback?${params.toString()}`);
    },
  });
  const feedbackDetail = useQuery({
    queryKey: ["feedback-detail", selectedFeedbackId],
    queryFn: () => api<FeedbackItem>(`/api/admin/feedback/${selectedFeedbackId}`),
    enabled: Boolean(selectedFeedbackId),
  });

  const activeFeedback =
    feedbackDetail.data || feedbackList.data?.items.find((item) => item.id === selectedFeedbackId) || null;

  useEffect(() => {
    if (!feedbackDetail.data) return;
    setDraftStatus(feedbackDetail.data.status);
    setDraftNote(feedbackDetail.data.internal_note || "");
  }, [feedbackDetail.data?.id, feedbackDetail.data?.internal_note, feedbackDetail.data?.status]);

  const updateFeedback = useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: FeedbackUpdate }) =>
      patchJson<FeedbackItem>(`/api/admin/feedback/${id}`, payload),
    onSuccess: (item) => {
      message.success("反馈处理已保存");
      setDraftStatus(item.status);
      setDraftNote(item.internal_note || "");
      void queryClient.invalidateQueries({ queryKey: ["feedback-summary"] });
      void queryClient.invalidateQueries({ queryKey: ["feedback-list"] });
      void queryClient.invalidateQueries({ queryKey: ["feedback-detail", item.id] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const saveFeedback = () => {
    if (!selectedFeedbackId) return;
    updateFeedback.mutate({
      id: selectedFeedbackId,
      payload: {
        status: draftStatus,
        internal_note: draftNote.trim() || null,
      },
    });
  };

  const summaryData = summary.data || {
    total_count: 0,
    open_count: 0,
    in_progress_count: 0,
    resolved_count: 0,
    archived_count: 0,
    recent_count: 0,
  };
  const statusOptions = [
    { label: `全部 ${summaryData.total_count}`, value: "all" },
    { label: `未处理 ${summaryData.open_count}`, value: "open" },
    { label: `处理中 ${summaryData.in_progress_count}`, value: "in_progress" },
    { label: `已解决 ${summaryData.resolved_count}`, value: "resolved" },
    { label: `已归档 ${summaryData.archived_count}`, value: "archived" },
  ];
  const typeOptions = [
    { label: "全部类型", value: "all" },
    ...Object.entries(feedbackTypeLabels).map(([value, label]) => ({ value, label })),
  ];
  const classOptions = [
    { label: "全部班级", value: "all" },
    ...(classes.data || []).map((item) => ({ value: item.id, label: item.class_name })),
  ];

  return (
    <Space direction="vertical" size={18} className="full">
      <PageTitle title="反馈管理" description="查看学生从 H5/手机学习端提交的课程、实验、AI 和系统反馈。" />

      <div className="stat-grid">
        <Card loading={summary.isLoading}>
          <Statistic title="未处理" value={summaryData.open_count} valueStyle={{ color: "#b8892f" }} />
        </Card>
        <Card loading={summary.isLoading}>
          <Statistic title="处理中" value={summaryData.in_progress_count} valueStyle={{ color: "#356f9c" }} />
        </Card>
        <Card loading={summary.isLoading}>
          <Statistic title="已解决" value={summaryData.resolved_count} valueStyle={{ color: "#005826" }} />
        </Card>
        <Card loading={summary.isLoading}>
          <Statistic title="近 7 天提交" value={summaryData.recent_count} />
        </Card>
      </div>

      <Card className="toolbar-card">
        <Flex wrap="wrap" align="center" justify="space-between" gap={12}>
          <Segmented
            value={statusFilter}
            onChange={(value) => setStatusFilter(value as FeedbackStatus | "all")}
            options={statusOptions}
          />
          <Space wrap size={10}>
            <Select
              value={typeFilter}
              onChange={(value) => setTypeFilter(value as FeedbackType | "all")}
              options={typeOptions}
              style={{ width: 150 }}
            />
            <Select
              value={classFilter}
              onChange={(value) => setClassFilter(value)}
              options={classOptions}
              loading={classes.isLoading}
              style={{ width: 190 }}
            />
            <Input.Search
              allowClear
              placeholder="搜索学生、班级或反馈内容"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              onSearch={(value) => setSearch(value)}
              className="feedback-search"
            />
          </Space>
        </Flex>
      </Card>

      <Card title="反馈列表" className="feedback-list-card">
        {feedbackList.isError ? (
          <Alert type="error" showIcon title="加载失败" description={errorMessage(feedbackList.error)} />
        ) : (
          <Table<FeedbackItem>
            rowKey="id"
            loading={feedbackList.isLoading || feedbackList.isFetching}
            dataSource={feedbackList.data?.items || []}
            pagination={{ pageSize: 10, showSizeChanger: false }}
            locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无反馈" /> }}
            onRow={(record) => ({
              onClick: () => setSelectedFeedbackId(record.id),
            })}
            columns={[
              {
                title: "提交时间",
                width: 150,
                render: (_: unknown, row: FeedbackItem) => (row.created_at ? dayjs(row.created_at).format("MM-DD HH:mm") : "-"),
              },
              {
                title: "学生",
                width: 180,
                render: (_: unknown, row: FeedbackItem) => (
                  <Space direction="vertical" size={0}>
                    <Text strong>{row.student_name_snapshot || row.student_id}</Text>
                    {row.student_name_snapshot ? <Text type="secondary">{row.student_id}</Text> : null}
                  </Space>
                ),
              },
              {
                title: "班级",
                width: 170,
                render: (_: unknown, row: FeedbackItem) => row.class_name_snapshot || row.class_id || "-",
              },
              {
                title: "类型",
                width: 120,
                render: (_: unknown, row: FeedbackItem) => feedbackTypeTag(row.feedback_type),
              },
              {
                title: "反馈内容",
                render: (_: unknown, row: FeedbackItem) => (
                  <Text className="feedback-content-preview">{row.content}</Text>
                ),
              },
              {
                title: "状态",
                width: 110,
                render: (_: unknown, row: FeedbackItem) => feedbackStatusTag(row.status),
              },
              {
                title: "操作",
                width: 90,
                render: (_: unknown, row: FeedbackItem) => (
                  <Button
                    type="link"
                    onClick={(event) => {
                      event.stopPropagation();
                      setSelectedFeedbackId(row.id);
                    }}
                  >
                    查看
                  </Button>
                ),
              },
            ]}
          />
        )}
      </Card>

      <Drawer
        title="反馈详情"
        open={Boolean(selectedFeedbackId)}
        width={720}
        onClose={() => {
          setSelectedFeedbackId(undefined);
          setDraftNote("");
        }}
      >
        <QueryState loading={feedbackDetail.isLoading} error={feedbackDetail.error} empty={!activeFeedback}>
          {activeFeedback ? (
            <Space direction="vertical" size={16} className="full">
              <div className="drawer-section feedback-detail-summary">
                <Flex justify="space-between" align="flex-start" gap={14}>
                  <div>
                    <Text type="secondary">学生反馈</Text>
                    <Title level={4}>{activeFeedback.student_name_snapshot || activeFeedback.student_id}</Title>
                    <Space wrap>
                      {feedbackTypeTag(activeFeedback.feedback_type)}
                      {feedbackStatusTag(activeFeedback.status)}
                      <Tag>{activeFeedback.class_name_snapshot || activeFeedback.class_id || "未关联班级"}</Tag>
                    </Space>
                  </div>
                  <Text type="secondary">{formatDateTime(activeFeedback.created_at)}</Text>
                </Flex>
              </div>

              <div className="drawer-section">
                <Text strong>反馈内容</Text>
                <div className="feedback-content-box">{activeFeedback.content}</div>
              </div>

              <div className="drawer-section">
                <Descriptions size="small" column={2}>
                  <Descriptions.Item label="学号">{activeFeedback.student_id}</Descriptions.Item>
                  <Descriptions.Item label="班级">{activeFeedback.class_name_snapshot || activeFeedback.class_id || "-"}</Descriptions.Item>
                  <Descriptions.Item label="页面">{activeFeedback.page_path || "-"}</Descriptions.Item>
                  <Descriptions.Item label="章节">{activeFeedback.chapter_id || "-"}</Descriptions.Item>
                  <Descriptions.Item label="知识点">{activeFeedback.knowledge_point_id || "-"}</Descriptions.Item>
                  <Descriptions.Item label="实验">{activeFeedback.experiment_id || "-"}</Descriptions.Item>
                  <Descriptions.Item label="处理人">{activeFeedback.handler_display_name || "-"}</Descriptions.Item>
                  <Descriptions.Item label="更新时间">{formatDateTime(activeFeedback.updated_at)}</Descriptions.Item>
                </Descriptions>
              </div>

              <div className="drawer-section">
                <Space direction="vertical" size={12} className="full">
                  <Text strong>处理记录</Text>
                  <Select
                    value={draftStatus}
                    onChange={(value) => setDraftStatus(value)}
                    options={[
                      { label: "未处理", value: "open" },
                      { label: "处理中", value: "in_progress" },
                      { label: "已解决", value: "resolved" },
                      { label: "已归档", value: "archived" },
                    ]}
                    className="full"
                  />
                  <Input.TextArea
                    value={draftNote}
                    onChange={(event) => setDraftNote(event.target.value)}
                    rows={5}
                    maxLength={4000}
                    showCount
                    placeholder="记录内部处理说明"
                  />
                  <Flex justify="flex-end">
                    <Button type="primary" onClick={saveFeedback} loading={updateFeedback.isPending}>
                      保存处理
                    </Button>
                  </Flex>
                </Space>
              </div>
            </Space>
          ) : null}
        </QueryState>
      </Drawer>
    </Space>
  );
}
