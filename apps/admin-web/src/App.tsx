import { useEffect, useMemo, useState } from "react";
import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { lazy, Suspense } from "react";
import {
  Alert,
  App as AntApp,
  Badge,
  Button,
  Card,
  Checkbox,
  ConfigProvider,
  Descriptions,
  Drawer,
  Empty,
  Flex,
  Form,
  Input,
  InputNumber,
  Layout,
  Menu,
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
  Tabs,
  Tag,
  Typography,
  Upload,
  theme,
} from "antd";
import {
  ArrowRightOutlined,
  ApiOutlined,
  AppstoreOutlined,
  BarChartOutlined,
  BookOutlined,
  CheckCircleOutlined,
  CloudUploadOutlined,
  DatabaseOutlined,
  DeleteOutlined,
  EditOutlined,
  ExperimentOutlined,
  EyeOutlined,
  IdcardOutlined,
  KeyOutlined,
  LogoutOutlined,
  MessageOutlined,
  PlusOutlined,
  QuestionCircleOutlined,
  SafetyCertificateOutlined,
  SettingOutlined,
  TeamOutlined,
  UnorderedListOutlined,
  VideoCameraOutlined,
} from "@ant-design/icons";
import dayjs from "dayjs";
import {
  api,
  apiBase,
  formatBytes,
  getAuthToken,
  patchJson,
  postJson,
  putJson,
  setAuthToken,
} from "./api";
import type {
  AnalyticsDashboard,
  AIConfiguration,
  AIConfigurationUpdate,
  ApiList,
  Chapter,
  ClassItem,
  Experiment,
  ExperimentVideoPoint,
  ExperimentVideoPointResource,
  ExperimentVideoPointsResponse,
  FeedbackItem,
  FeedbackListResponse,
  FeedbackStatus,
  FeedbackSummary,
  FeedbackType,
  FeedbackUpdate,
  LearningResourceOverview,
  MediaAsset,
  Question,
  ChapterQuestion,
  QuestionBankAssistantPreview,
  QuestionBankChapterSummary,
  QuestionBankSummary,
  LearningBehaviorSettings,
  PlatformSettingsResponse,
  RegistrationSettings,
  RosterImportResult,
  RosterStudent,
  User,
} from "./api";

const { Header, Sider, Content } = Layout;
const { Text, Title } = Typography;
const sysuLogoSrc = `${import.meta.env.BASE_URL}sysu-logo.svg`;
const UsageLineChart = lazy(async () => {
  const module = await import("@ant-design/plots");
  return { default: module.Line };
});

type LoginResponse = {
  access_token: string;
  user: User;
};

type QuestionFormValues = {
  experiment_id: string;
  question_type: "single_choice" | "true_false" | "fill_blank";
  stem: string;
  options_text?: string;
  answer_text: string;
  explanation?: string;
  difficulty?: string;
  status?: string;
};

type VideoPreviewTarget = {
  id: string;
  title: string;
  original_file_name: string;
  mime_type?: string | null;
  upload_status?: string | null;
};

type VideoPointFilter = "all" | "empty" | "referenced" | "published";

const navItems = [
  { key: "/overview", icon: <BookOutlined />, label: "学习资源" },
  { key: "/classes", icon: <TeamOutlined />, label: "班级与学生" },
  { key: "/experiments", icon: <ExperimentOutlined />, label: "实验管理" },
  { key: "/videos", icon: <VideoCameraOutlined />, label: "视频资源" },
  { key: "/question-banks", icon: <QuestionCircleOutlined />, label: "题库管理" },
  { key: "/analytics", icon: <BarChartOutlined />, label: "学情分析" },
  { key: "/feedback", icon: <MessageOutlined />, label: "反馈管理" },
  { key: "/settings", icon: <SettingOutlined />, label: "系统设置" },
  { key: "/ai-config", icon: <ApiOutlined />, label: "AI配置" },
];

const statusColor: Record<string, string> = {
  published: "#005826",
  ready: "#005826",
  active: "#005826",
  draft: "#b8892f",
  pending: "#b8892f",
  processing: "#356f9c",
  failed: "#b42318",
  disabled: "default",
  archived: "default",
  not_started: "default",
  in_progress: "#356f9c",
  completed: "#005826",
  needs_attention: "#b42318",
};

const statusLabel: Record<string, string> = {
  published: "已发布",
  ready: "就绪",
  active: "使用中",
  draft: "草稿",
  pending: "未激活",
  processing: "处理中",
  failed: "失败",
  disabled: "已禁用",
  archived: "已归档",
  not_started: "未开始",
  in_progress: "进行中",
  completed: "已完成",
  needs_attention: "需关注",
};

function statusTag(status?: string) {
  return <Tag color={statusColor[status || ""] || "default"}>{statusLabel[status || ""] || status || "-"}</Tag>;
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

function formatDateTime(value?: string | null) {
  return value ? dayjs(value).format("YYYY-MM-DD HH:mm") : "-";
}

function questionTypeLabel(type?: string) {
  if (type === "single_choice") return "选择";
  if (type === "true_false") return "判断";
  if (type === "fill_blank") return "填空";
  return type || "-";
}

function errorMessage(error: unknown) {
  if (error instanceof Error) return error.message;
  return String(error || "请求失败");
}

function App() {
  return (
    <ConfigProvider
      theme={{
        algorithm: theme.defaultAlgorithm,
        token: {
          colorPrimary: "#005826",
          colorInfo: "#356f9c",
          colorSuccess: "#005826",
          colorWarning: "#b8892f",
          colorError: "#b42318",
          colorText: "#0d1f17",
          colorTextSecondary: "#697a72",
          colorBorder: "#dfe8e2",
          colorBorderSecondary: "#dfe8e2",
          colorBgLayout: "#f6f8f5",
          colorBgContainer: "#ffffff",
          borderRadius: 8,
          fontFamily: '"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
        },
        components: {
          Layout: {
            bodyBg: "#f6f8f5",
            headerBg: "#ffffff",
            siderBg: "#ffffff",
          },
          Button: {
            primaryShadow: "0 12px 24px rgba(0, 88, 38, 0.16)",
          },
          Card: {
            borderRadiusLG: 8,
          },
          Menu: {
            itemSelectedBg: "#e8f2ec",
            itemSelectedColor: "#005826",
            itemHoverBg: "#f6f9f7",
            itemHoverColor: "#005826",
          },
          Segmented: {
            itemSelectedBg: "#ffffff",
          },
          Table: {
            headerBg: "#f1f7f3",
            borderColor: "#dfe8e2",
            rowHoverBg: "#f6f9f7",
          },
        },
      }}
    >
      <AntApp>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<Navigate to="/overview" replace />} />
          <Route path="/curriculum" element={<Navigate to="/experiments" replace />} />
          <Route path="/review" element={<Navigate to="/question-banks" replace />} />
          <Route element={<ProtectedShell />}>
          <Route path="/overview" element={<LearningResourcesPage />} />
            <Route path="/classes" element={<ClassesPage />} />
            <Route path="/experiments" element={<ExperimentsPage />} />
            <Route path="/videos" element={<VideoResourcesPage />} />
            <Route path="/question-banks" element={<QuestionBanksPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/feedback" element={<FeedbackPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/ai-config" element={<AIConfigurationPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/overview" replace />} />
        </Routes>
      </AntApp>
    </ConfigProvider>
  );
}

function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { message } = AntApp.useApp();
  const [form] = Form.useForm();
  const [submitting, setSubmitting] = useState(false);
  const from = (location.state as { from?: string } | null)?.from || "/overview";

  const submit = async (values: { username: string; password: string }) => {
    setSubmitting(true);
    try {
      const response = await api<LoginResponse>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify(values),
      });
      if (response.user.role === "student") {
        throw new Error("学生账号不能登录教师后台");
      }
      setAuthToken(response.access_token);
      message.success("登录成功");
      navigate(from, { replace: true });
    } catch (error) {
      message.error(errorMessage(error));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="login-page">
      <Card className="login-card">
        <Space direction="vertical" size={20} className="full">
          <div className="login-brand-lockup">
            <img src={sysuLogoSrc} alt="" />
            <div>
              <Text strong>中山大学</Text>
              <Text type="secondary" className="block-text">
                SYSU Chemistry Learning
              </Text>
            </div>
          </div>
          <div className="login-title">
            <Text className="eyebrow">Teacher Console</Text>
            <Title level={2}>无机化学实验学习后台</Title>
            <Text type="secondary" className="block-text">
              班级、资源、题库与学情分析管理
            </Text>
          </div>
          <Form form={form} layout="vertical" onFinish={submit} initialValues={{ username: "admin" }}>
            <Form.Item name="username" label="账号" rules={[{ required: true, message: "请输入账号" }]}>
              <Input size="large" autoComplete="username" />
            </Form.Item>
            <Form.Item name="password" label="密码" rules={[{ required: true, message: "请输入密码" }]}>
              <Input.Password size="large" autoComplete="current-password" />
            </Form.Item>
            <Button type="primary" size="large" htmlType="submit" loading={submitting} block>
              登录后台
            </Button>
          </Form>
        </Space>
      </Card>
    </div>
  );
}

function ProtectedShell() {
  const token = getAuthToken();
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();

  const meQuery = useQuery({
    queryKey: ["me", token],
    queryFn: () => api<User>("/api/auth/me"),
    enabled: Boolean(token),
    retry: false,
  });

  useEffect(() => {
    if (meQuery.isError) {
      setAuthToken("");
      navigate("/login", { replace: true, state: { from: location.pathname } });
    }
  }, [location.pathname, meQuery.isError, navigate]);

  if (!token) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  if (meQuery.isLoading || !meQuery.data) {
    return (
      <div className="center-screen">
        <Spin size="large" />
      </div>
    );
  }
  if (meQuery.data.role === "student") {
    return <Navigate to="/login" replace />;
  }

  const logout = () => {
    setAuthToken("");
    queryClient.clear();
    navigate("/login", { replace: true });
  };

  return (
    <Layout className="admin-shell">
      <Sider width={248} className="admin-sider">
        <div className="brand">
          <div className="brand-mark">
            <img src={sysuLogoSrc} alt="" />
          </div>
          <div>
            <Text strong>中大实验学习后台</Text>
            <Text type="secondary" className="block-text">
              SYSU teacher console
            </Text>
          </div>
        </div>
        <Menu
          mode="inline"
          selectedKeys={[navItems.find((item) => location.pathname.startsWith(item.key))?.key || "/overview"]}
          items={navItems}
          onClick={({ key }) => navigate(String(key))}
        />
      </Sider>
      <Layout>
        <Header className="admin-header">
          <Space>
            <Badge status="success" />
            <Text>
              {meQuery.data.display_name} · {meQuery.data.role}
            </Text>
          </Space>
          <Button icon={<LogoutOutlined />} onClick={logout}>
            退出
          </Button>
        </Header>
        <Content className="admin-content">
          <Routes>
            <Route path="/overview" element={<LearningResourcesPage />} />
            <Route path="/classes" element={<ClassesPage />} />
            <Route path="/experiments" element={<ExperimentsPage />} />
            <Route path="/videos" element={<VideoResourcesPage />} />
            <Route path="/question-banks" element={<QuestionBanksPage />} />
            <Route path="/analytics" element={<AnalyticsPage />} />
            <Route path="/feedback" element={<FeedbackPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/ai-config" element={<AIConfigurationPage />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}

function PageTitle({ title, description, extra }: { title: string; description?: string; extra?: React.ReactNode }) {
  return (
    <Flex align="center" justify="space-between" gap={16} className="page-title">
      <div>
        <Title level={2}>{title}</Title>
        {description ? <Text type="secondary">{description}</Text> : null}
      </div>
      {extra}
    </Flex>
  );
}

function QueryState({
  loading,
  error,
  empty,
  children,
}: {
  loading: boolean;
  error?: unknown;
  empty?: boolean;
  children: React.ReactNode;
}) {
  if (loading) {
    return (
      <div className="center-panel">
        <Spin />
      </div>
    );
  }
  if (error) {
    return <Alert type="error" showIcon title="加载失败" description={errorMessage(error)} />;
  }
  if (empty) {
    return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无数据" />;
  }
  return children;
}

function useChapters() {
  return useQuery({ queryKey: ["chapters"], queryFn: () => api<Chapter[]>("/api/chapters") });
}

function useExperiments(params = "") {
  return useQuery({
    queryKey: ["admin-experiments", params],
    queryFn: () => api<ApiList<Experiment>>(`/api/admin/experiments${params}`),
  });
}

type TheoryChapter = {
  chapter_id: string;
  chapter_number: number;
  chapter_title: string;
  area_id: string;
  area_name: string;
};

const theoryChapters: TheoryChapter[] = [
  { chapter_id: "CH13", chapter_number: 13, chapter_title: "第13章 卤族元素", area_id: "p", area_name: "p 区元素" },
  { chapter_id: "CH14", chapter_number: 14, chapter_title: "第14章 氧族元素", area_id: "p", area_name: "p 区元素" },
  { chapter_id: "CH15", chapter_number: 15, chapter_title: "第15章 氮族元素", area_id: "p", area_name: "p 区元素" },
  { chapter_id: "CH16", chapter_number: 16, chapter_title: "第16章 碳族元素", area_id: "p", area_name: "p 区元素" },
  { chapter_id: "CH17", chapter_number: 17, chapter_title: "第17章 硼族元素", area_id: "p", area_name: "p 区元素" },
  { chapter_id: "CH18", chapter_number: 18, chapter_title: "第18章 碱金属和碱土金属", area_id: "s", area_name: "s 区元素" },
  { chapter_id: "CH19", chapter_number: 19, chapter_title: "第19章 铜锌副族元素", area_id: "ds", area_name: "ds 区元素" },
  { chapter_id: "CH20", chapter_number: 20, chapter_title: "第20章 d 区过渡金属元素", area_id: "d", area_name: "d 区元素" },
  { chapter_id: "CH21", chapter_number: 21, chapter_title: "第21章 镧系和锕系元素", area_id: "f", area_name: "f 区元素" },
  { chapter_id: "CH22", chapter_number: 22, chapter_title: "第22章 氢和稀有气体", area_id: "integrated", area_name: "综合章节" },
];

function isGeneralResourceTitle(title?: string | null, chapterId?: string | null) {
  const text = `${chapterId || ""} ${title || ""}`;
  return chapterId === "CH00" || /综合|通识|跨章节|未标章节/.test(text);
}

function formatChapterTitle(title?: string | null, chapterId?: string | null) {
  const cleanTitle = (title || "").replace(/^CH\d+\s*/i, "").trim();
  const fallback = chapterId ? theoryChapters.find((chapter) => chapter.chapter_id === chapterId)?.chapter_title : "";
  const display = cleanTitle || fallback || (chapterId === "CH00" ? "通识/跨章节" : chapterId || "-");
  if (isGeneralResourceTitle(display, chapterId)) {
    return display.replace(/^第\s*\d+\s*章\s*/, "").trim() || "通识/跨章节";
  }
  return display.replace(/^第\s*(\d+)\s*章\s*/, "第 $1 章 ");
}

function experimentVideoCandidates(experiment?: Experiment | null): string[] {
  const raw = experiment?.metadata?.video_candidates;
  if (!Array.isArray(raw)) return [];
  return raw.filter((item): item is string => typeof item === "string" && item.trim().length > 0).map((item) => item.trim());
}

function mediaAssetType(asset: MediaAsset): string {
  const mime = asset.mime_type || "";
  if (mime.startsWith("video/")) return mime.replace("video/", "").toUpperCase();
  const suffix = asset.original_file_name.split(".").pop();
  return suffix ? suffix.toUpperCase() : "VIDEO";
}

function mediaAssetTime(asset: MediaAsset): string {
  const value = asset.updated_at || asset.created_at;
  return value ? dayjs(value).format("YYYY-MM-DD HH:mm") : "-";
}

function isPreviewableVideo(asset?: MediaAsset | null): boolean {
  if (!asset || asset.upload_status !== "ready") return false;
  return !asset.mime_type || asset.mime_type.startsWith("video/");
}

function LearningResourcesPage() {
  const overview = useQuery({
    queryKey: ["admin-learning-resources-overview"],
    queryFn: () => api<LearningResourceOverview>("/api/admin/learning-resources/overview"),
  });
  const groups = overview.data?.groups || [];
  const [selectedGroupId, setSelectedGroupId] = useState<string>();

  useEffect(() => {
    if (!groups.length) return;
    if (!selectedGroupId || !groups.some((group) => group.id === selectedGroupId)) {
      setSelectedGroupId(groups[0].id);
    }
  }, [groups, selectedGroupId]);

  const selectedGroup = groups.find((group) => group.id === selectedGroupId) || groups[0];
  const metrics = overview.data?.metrics;
  const selectedGroupMetrics = selectedGroup
    ? [
        { label: "知识单元", value: selectedGroup.knowledge_unit_count },
        { label: "知识点", value: selectedGroup.knowledge_point_count },
        { label: "实验", value: selectedGroup.experiment_count },
        { label: "视频", value: selectedGroup.media_count },
        { label: "题目", value: selectedGroup.question_count },
      ]
    : [];
  const totalUnitCount = selectedGroup?.units.length || 0;
  const totalExperimentQuestionCount = selectedGroup?.experiments.reduce((sum, item) => sum + Number(item.question_count || 0), 0) || 0;

  return (
    <Space direction="vertical" size={18} className="full">
      <PageTitle
        title="学习资源"
        description="按章节和通识资源查看知识单元、知识点、实验、视频和题目覆盖。"
      />
      <div className="resource-metric-grid">
        <Card>
          <Statistic title="知识单元" value={metrics?.knowledge_unit_count || 0} prefix={<DatabaseOutlined />} />
        </Card>
        <Card>
          <Statistic title="知识点" value={metrics?.knowledge_point_count || 0} prefix={<DatabaseOutlined />} />
        </Card>
        <Card>
          <Statistic title="实验" value={metrics?.experiment_count || 0} prefix={<ExperimentOutlined />} />
        </Card>
        <Card>
          <Statistic title="媒体资源" value={metrics?.media_resource_count || 0} prefix={<CloudUploadOutlined />} />
        </Card>
        <Card>
          <Statistic title="题目" value={metrics?.question_count || 0} prefix={<QuestionCircleOutlined />} />
        </Card>
      </div>

      <QueryState loading={overview.isLoading} error={overview.error} empty={!groups.length}>
        <div className="learning-resource-layout">
          <Card title="资源目录" className="learning-resource-directory">
            {(overview.data?.areas || []).map((area) => (
              <div key={area.area_id} className="resource-directory-section">
                <Flex align="center" justify="space-between" className="resource-directory-heading">
                  <Text strong>{area.area_name}</Text>
                  <Tag>{area.metrics.group_count}</Tag>
                </Flex>
                <div className="resource-directory-list">
                  {area.group_ids.map((groupId) => {
                    const group = groups.find((item) => item.id === groupId);
                    if (!group) return null;
                    const active = group.id === selectedGroup?.id;
                    return (
                      <button
                        key={group.id}
                        type="button"
                        className={`resource-directory-item${active ? " resource-directory-item-active" : ""}`}
                        onClick={() => setSelectedGroupId(group.id)}
                      >
                        <span>{group.title}</span>
                        <small>
                          知识单元 {group.knowledge_unit_count} · 知识点 {group.knowledge_point_count}
                        </small>
                      </button>
                    );
                  })}
                </div>
              </div>
            ))}
          </Card>

          <div className="learning-resource-main">
            <Card
              className="learning-resource-map-card"
              title={
                <Flex align="center" justify="space-between" gap={12}>
                  <span>{selectedGroup?.title || "资源总览"}</span>
                  {selectedGroup ? <Tag color={selectedGroup.kind === "general" ? "#356f9c" : "#005826"}>{selectedGroup.area_name}</Tag> : null}
                </Flex>
              }
            >
              <div className="resource-group-summary">
                {selectedGroupMetrics.map((item) => (
                  <div key={item.label}>
                    <Text type="secondary">{item.label}</Text>
                    <strong>{item.value}</strong>
                  </div>
                ))}
              </div>

              <div className="learning-resource-map">
                <div className="resource-map-root">
                  <Text type="secondary">{selectedGroup?.kind === "general" ? "通识资源" : "理论章节"}</Text>
                  <strong>{selectedGroup?.title}</strong>
                  <span>{totalUnitCount} 个知识单元</span>
                </div>

                <div className="resource-map-units">
                  {(selectedGroup?.units || []).map((unit) => (
                    <div key={unit.unit_id} className="resource-unit-card">
                      <Flex align="center" justify="space-between" gap={10}>
                        <Text strong>{unit.unit_title}</Text>
                        <Tag>知识点 {unit.knowledge_point_count}</Tag>
                      </Flex>
                      <div className="resource-kp-list">
                        {unit.knowledge_points.slice(0, 4).map((point) => (
                          <div key={point.knowledge_point_id} className="resource-kp-node">
                            <span>{point.content}</span>
                          </div>
                        ))}
                        {unit.knowledge_points.length > 4 ? (
                          <Text type="secondary" className="resource-more-text">
                            另有 {unit.knowledge_points.length - 4} 个知识点。
                          </Text>
                        ) : null}
                      </div>
                    </div>
                  ))}
                </div>

                <div className="resource-map-assets">
                  <div className="resource-asset-block">
                    <Flex align="center" justify="space-between">
                      <Text strong>实验</Text>
                      <Tag>{selectedGroup?.experiment_count || 0}</Tag>
                    </Flex>
                    <div className="resource-chip-list">
                      {(selectedGroup?.experiments || []).length ? (
                        selectedGroup?.experiments.map((experiment) => (
                          <div key={experiment.id} className="resource-experiment-row">
                            <div>
                              <Text strong>
                                {experiment.code ? `${experiment.code} · ` : ""}
                                {experiment.title}
                              </Text>
                              <div className="resource-experiment-meta">
                                <Tag color={statusColor[experiment.status] || "default"}>{statusLabel[experiment.status] || experiment.status}</Tag>
                              </div>
                            </div>
                            <div className="resource-experiment-counts">
                              <Tag color={experiment.media_count ? "#356f9c" : "default"}>视频 {experiment.media_count}</Tag>
                              <Tag color={experiment.question_count ? "#005826" : "default"}>题目 {experiment.question_count}</Tag>
                            </div>
                          </div>
                        ))
                      ) : (
                        <Text type="secondary">暂无绑定实验</Text>
                      )}
                    </div>
                  </div>
                  <div className="resource-asset-block">
                    <Text strong>覆盖摘要</Text>
                    <div className="resource-coverage-list">
                      <div>
                        <span>媒体资源</span>
                        <strong>{selectedGroup?.media_count || 0}</strong>
                      </div>
                      <div>
                        <span>题目</span>
                        <strong>{selectedGroup?.question_count || totalExperimentQuestionCount}</strong>
                      </div>
                      <div>
                        <span>知识点</span>
                        <strong>{selectedGroup?.knowledge_point_count || 0}</strong>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        </div>
      </QueryState>
    </Space>
  );
}

function OverviewPage() {
  const classes = useQuery({ queryKey: ["classes"], queryFn: () => api<ClassItem[]>("/api/admin/classes") });
  const experiments = useExperiments();
  const banks = useQuery({
    queryKey: ["question-banks"],
    queryFn: () => api<ApiList<QuestionBankSummary>>("/api/admin/question-banks"),
  });
  const firstClassId = classes.data?.[0]?.id;
  const dashboard = useQuery({
    queryKey: ["class-dashboard", firstClassId],
    queryFn: () => api<AnalyticsDashboard>(`/api/admin/analytics/classes/${firstClassId}/dashboard`),
    enabled: Boolean(firstClassId),
  });

  const publishedQuestions = (banks.data?.items || []).reduce(
    (sum, item) => sum + item.banks.reduce((inner, bank) => inner + Number(bank.published_count || 0), 0),
    0,
  );

  return (
    <Space direction="vertical" size={18} className="full">
      <PageTitle title="总览" description="以精选目录中的具体实验点为核心的教学运营状态。" />
      <div className="stat-grid">
        <Card>
          <Statistic title="正式实验" value={experiments.data?.items.length || 0} prefix={<ExperimentOutlined />} />
        </Card>
        <Card>
          <Statistic title="班级" value={classes.data?.length || 0} prefix={<TeamOutlined />} />
        </Card>
        <Card>
          <Statistic title="已发布题目" value={publishedQuestions} prefix={<DatabaseOutlined />} />
        </Card>
        <Card>
          <Statistic title="班级完成率" value={dashboard.data?.metrics.completion_rate || 0} suffix="%" prefix={<CheckCircleOutlined />} />
        </Card>
      </div>
      <Card title="实验目录状态">
        <QueryState loading={experiments.isLoading} error={experiments.error} empty={!experiments.data?.items.length}>
          <Table
            rowKey="id"
            size="middle"
            pagination={false}
            dataSource={experiments.data?.items || []}
            columns={[
              { title: "实验", dataIndex: "title", render: (_: unknown, row: Experiment) => <Text strong>{row.title}</Text> },
              { title: "编号", dataIndex: "code", width: 90 },
              {
                title: "章节",
                render: (_: unknown, row: Experiment) => (
                <Space wrap>
                  {row.chapter_bindings.map((binding) => (
                    <Tag key={binding.chapter_id}>{formatChapterTitle(binding.chapter_title, binding.chapter_id)}</Tag>
                  ))}
                </Space>
              ),
              },
              { title: "视频", width: 120, render: (_: unknown, row: Experiment) => row.media_resources.length },
              { title: "发布题", width: 120, dataIndex: "published_question_count" },
              { title: "状态", width: 110, render: (_: unknown, row: Experiment) => statusTag(row.status) },
            ]}
          />
        </QueryState>
      </Card>
    </Space>
  );
}

function ClassesPage() {
  const { message } = AntApp.useApp();
  const queryClient = useQueryClient();
  const [createOpen, setCreateOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);
  const [importingRoster, setImportingRoster] = useState(false);
  const [selectedClassId, setSelectedClassId] = useState<string>();
  const [rosterFile, setRosterFile] = useState<File | null>(null);
  const [importMode, setImportMode] = useState<"upsert" | "overwrite">("upsert");
  const [rosterView, setRosterView] = useState<"current" | "disabled">("current");
  const [studentSearch, setStudentSearch] = useState("");
  const [studentOpen, setStudentOpen] = useState(false);
  const [editingStudent, setEditingStudent] = useState<RosterStudent | null>(null);
  const [classForm] = Form.useForm();
  const [classSettingsForm] = Form.useForm();
  const [registrationForm] = Form.useForm();
  const [studentForm] = Form.useForm();
  const classes = useQuery({ queryKey: ["classes"], queryFn: () => api<ClassItem[]>("/api/admin/classes") });
  const selectedClass = (classes.data || []).find((item) => item.id === selectedClassId) || null;
  const roster = useQuery({
    queryKey: ["class-roster", selectedClassId],
    queryFn: () => api<RosterStudent[]>(`/api/admin/classes/${selectedClassId}/students`),
    enabled: Boolean(selectedClassId),
  });
  const registration = useQuery({
    queryKey: ["class-registration-settings", selectedClassId],
    queryFn: () => api<RegistrationSettings>(`/api/admin/classes/${selectedClassId}/registration-settings`),
    enabled: Boolean(selectedClassId),
  });
  const defaultPasswordMode =
    Form.useWatch("default_password_mode", registrationForm) ||
    registration.data?.default_password_mode ||
    (registration.data?.has_default_password ? "shared" : "student_id");
  const classStatus = Form.useWatch("status", classSettingsForm) || selectedClass?.status || "active";
  const rosterRows = roster.data || [];
  const currentRoster = rosterRows.filter((row) => row.status !== "disabled");
  const disabledRoster = rosterRows.filter((row) => row.status === "disabled");
  const activeCount = currentRoster.filter((row) => row.activated || row.status === "active").length;
  const inactiveCount = currentRoster.length - activeCount;
  const tableRoster = rosterView === "current" ? currentRoster : disabledRoster;
  const normalizedStudentSearch = studentSearch.trim().toLowerCase();
  const filteredTableRoster = normalizedStudentSearch
    ? tableRoster.filter(
        (row) =>
          row.student_id.toLowerCase().includes(normalizedStudentSearch) ||
          row.student_name.toLowerCase().includes(normalizedStudentSearch),
      )
    : tableRoster;
  const initialPasswordLabel = defaultPasswordMode === "shared" ? "统一初始密码" : "使用学号";

  useEffect(() => {
    if (selectedClass) {
      classSettingsForm.setFieldsValue({
        class_name: selectedClass.class_name,
        description: selectedClass.description,
        status: selectedClass.status,
      });
    }
  }, [classSettingsForm, selectedClass]);

  useEffect(() => {
    if (registration.data) {
      registrationForm.setFieldsValue({
        ...registration.data,
        mode: "roster_only",
        default_password_mode:
          registration.data.default_password_mode || (registration.data.has_default_password ? "shared" : "student_id"),
        default_password: "",
      });
    }
  }, [registration.data, registrationForm]);

  useEffect(() => {
    if (!studentOpen) return;
    if (editingStudent) {
      studentForm.setFieldsValue(editingStudent);
    } else {
      studentForm.setFieldsValue({
        student_id: "",
        student_name: "",
      });
    }
  }, [editingStudent, studentForm, studentOpen]);

  const createClass = useMutation({
    mutationFn: (values: { class_name: string; description?: string }) => postJson<ClassItem>("/api/admin/classes", values),
    onSuccess: (item) => {
      message.success("班级已创建");
      setCreateOpen(false);
      classForm.resetFields();
      setSelectedClassId(item.id);
      void queryClient.invalidateQueries({ queryKey: ["classes"] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const updateClass = useMutation({
    mutationFn: (values: { class_name?: string; description?: string; status?: string }) =>
      patchJson<ClassItem>(`/api/admin/classes/${selectedClassId}`, values),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["classes"] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const updateRegistration = useMutation({
    mutationFn: (values: Record<string, unknown>) => {
      const passwordMode = String(values.default_password_mode || "student_id");
      if (!selectedClassId) throw new Error("请先选择班级");
      return putJson<RegistrationSettings>(`/api/admin/classes/${selectedClassId}/registration-settings`, {
        mode: "roster_only",
        default_password_policy: "student_id_name_activation",
        default_password_mode: passwordMode,
        default_password: passwordMode === "shared" ? values.default_password || undefined : undefined,
      });
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["class-registration-settings", selectedClassId] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const saveStudent = useMutation({
    mutationFn: (values: Record<string, unknown>) => {
      if (!selectedClassId) throw new Error("请先选择班级");
      if (editingStudent) {
        return patchJson<RosterStudent>(`/api/admin/classes/${selectedClassId}/students/${editingStudent.student_id}`, values);
      }
      return postJson<RosterStudent>(`/api/admin/classes/${selectedClassId}/students`, values);
    },
    onSuccess: () => {
      message.success(editingStudent ? "学生已更新" : "学生已添加");
      setStudentOpen(false);
      setEditingStudent(null);
      studentForm.resetFields();
      void queryClient.invalidateQueries({ queryKey: ["class-roster", selectedClassId] });
      void queryClient.invalidateQueries({ queryKey: ["classes"] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const disableStudent = useMutation({
    mutationFn: (studentId: string) => {
      if (!selectedClassId) throw new Error("请先选择班级");
      return api<RosterStudent>(`/api/admin/classes/${selectedClassId}/students/${studentId}`, { method: "DELETE" });
    },
    onSuccess: () => {
      message.success("学生已禁用");
      setRosterView("current");
      void queryClient.invalidateQueries({ queryKey: ["class-roster", selectedClassId] });
      void queryClient.invalidateQueries({ queryKey: ["classes"] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const resetPassword = useMutation({
    mutationFn: (studentId: string) => {
      if (!selectedClassId) throw new Error("请先选择班级");
      return postJson(`/api/admin/classes/${selectedClassId}/students/${studentId}/reset-password`, { force_change: true });
    },
    onSuccess: () => message.success("已重置为学号初始密码"),
    onError: (error) => message.error(errorMessage(error)),
  });

  const restoreStudent = useMutation({
    mutationFn: (studentId: string) => {
      if (!selectedClassId) throw new Error("请先选择班级");
      return patchJson<RosterStudent>(`/api/admin/classes/${selectedClassId}/students/${studentId}`, { status: "pending" });
    },
    onSuccess: () => {
      message.success("学生已恢复到当前名单");
      setRosterView("current");
      void queryClient.invalidateQueries({ queryKey: ["class-roster", selectedClassId] });
      void queryClient.invalidateQueries({ queryKey: ["classes"] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const saveClassConfiguration = async () => {
    try {
      const [classValues, registrationValues] = await Promise.all([
        classSettingsForm.validateFields(),
        registrationForm.validateFields(),
      ]);
      await updateClass.mutateAsync(classValues);
      await updateRegistration.mutateAsync(registrationValues);
      message.success("班级设置已保存");
      setSettingsOpen(false);
    } catch (error) {
      if (error instanceof Error) {
        message.error(errorMessage(error));
      }
    }
  };

  const importRoster = async () => {
    if (!selectedClassId || !rosterFile) {
      message.warning("请先选择名单文件");
      return;
    }
    const body = new FormData();
    body.append("file", rosterFile);
    body.append("mode", importMode);
    setImportingRoster(true);
    try {
      const result = await api<RosterImportResult>(`/api/admin/classes/${selectedClassId}/roster/import`, { method: "POST", body });
      message.success(
        importMode === "overwrite"
          ? `覆盖导入完成：${result.valid_rows} 条有效，禁用 ${result.disabled_missing} 条缺失名单`
          : `导入完成：${result.valid_rows} 条有效`,
      );
      setRosterFile(null);
      setImportOpen(false);
      void queryClient.invalidateQueries({ queryKey: ["class-roster", selectedClassId] });
      void queryClient.invalidateQueries({ queryKey: ["classes"] });
    } catch (error) {
      message.error(errorMessage(error));
    } finally {
      setImportingRoster(false);
    }
  };

  const openStudentEditor = (student?: RosterStudent) => {
    setEditingStudent(student || null);
    setStudentOpen(true);
  };

  return (
    <Space direction="vertical" size={18} className="full">
      <PageTitle title="班级与学生" description="一个班级一张卡片；多个班级可以同时使用，点击卡片后管理班级名单。" />
      <QueryState loading={classes.isLoading} error={classes.error}>
        <div className="class-card-grid">
          {(classes.data || []).map((item) => (
            <Card
              key={item.id}
              hoverable
              className="class-card"
              onClick={() => setSelectedClassId(item.id)}
              tabIndex={0}
              onKeyDown={(event) => {
                if (event.key === "Enter") setSelectedClassId(item.id);
              }}
            >
              <div className="class-card-content">
                <Flex justify="space-between" align="flex-start" gap={12}>
                  <div>
                    <Text className="eyebrow">班级</Text>
                    <Title level={4} className="class-card-title">{item.class_name}</Title>
                  </div>
                  {statusTag(item.status)}
                </Flex>
                <Text type="secondary" className="class-card-description">
                  {item.description || "暂无班级说明"}
                </Text>
                <Flex justify="space-between" align="end" className="class-card-footer">
                  <Statistic title="当前名单" value={item.student_count || 0} prefix={<TeamOutlined />} />
                  <Text className="class-card-action">
                    <ArrowRightOutlined /> 进入管理
                  </Text>
                </Flex>
              </div>
            </Card>
          ))}
          <button type="button" className="class-create-card" onClick={() => setCreateOpen(true)}>
            <PlusOutlined />
            <Text strong>新建班级</Text>
            <Text type="secondary">填写班级名称后即可导入名单</Text>
          </button>
        </div>
      </QueryState>

      <Drawer
        title={selectedClass ? selectedClass.class_name : "班级详情"}
        open={Boolean(selectedClassId)}
        onClose={() => {
          setSelectedClassId(undefined);
          setRosterFile(null);
          setStudentSearch("");
          setSettingsOpen(false);
          setImportOpen(false);
        }}
        width={980}
      >
        {selectedClass ? (
          <Space direction="vertical" size={18} className="full">
            <div className="class-detail-hero">
              <div className="class-detail-copy">
                <Text className="eyebrow">班级管理</Text>
                <Title level={3}>{selectedClass.class_name}</Title>
                <Space wrap className="class-hero-meta">
                  {statusTag(selectedClass.status)}
                  <Tag color="blue">初始密码：{initialPasswordLabel}</Tag>
                </Space>
                <Text type="secondary" className="class-detail-description">
                  {selectedClass.description || "暂无班级说明"}
                </Text>
              </div>
              <div className="class-hero-side">
                <div className="class-hero-actions">
                  <Button type="primary" icon={<SettingOutlined />} onClick={() => setSettingsOpen(true)}>
                    编辑班级设置
                  </Button>
                </div>
                <div className="class-hero-stats">
                  <Statistic title="当前名单" value={currentRoster.length} prefix={<IdcardOutlined />} />
                  <Statistic title="已激活" value={activeCount} />
                  <Statistic title="未激活" value={inactiveCount} />
                  <Statistic title="已禁用" value={disabledRoster.length} />
                </div>
              </div>
            </div>

            <div className="drawer-section roster-section">
              <Flex justify="space-between" align="flex-start" gap={16} className="drawer-table-heading roster-heading">
                <div className="roster-heading-copy">
                  <Text strong>学生名单</Text>
                  <Text type="secondary" className="block-text">
                    导入或添加即完成班级登记；学生首次登录并修改密码后才算已激活。
                  </Text>
                </div>
                <Space className="roster-heading-actions" size={10}>
                  <Button icon={<CloudUploadOutlined />} onClick={() => setImportOpen(true)}>
                    导入名单
                  </Button>
                  <Button type="primary" icon={<PlusOutlined />} onClick={() => openStudentEditor()}>
                    添加学生
                  </Button>
                </Space>
              </Flex>
              <Tabs
                activeKey={rosterView}
                onChange={(key) => setRosterView(key as "current" | "disabled")}
                tabBarExtraContent={
                  <Input.Search
                    allowClear
                    className="roster-search"
                    placeholder="搜索学号或姓名"
                    value={studentSearch}
                    onChange={(event) => setStudentSearch(event.target.value)}
                  />
                }
                items={[
                  { key: "current", label: `当前名单 (${currentRoster.length})` },
                  { key: "disabled", label: `已禁用 (${disabledRoster.length})` },
                ]}
              />
              <QueryState loading={roster.isLoading} error={roster.error} empty={!filteredTableRoster.length}>
                <Table<RosterStudent>
                  rowKey="id"
                  dataSource={filteredTableRoster}
                  pagination={{ pageSize: 10, showSizeChanger: true }}
                  size="middle"
                  columns={[
                    { title: "学号", dataIndex: "student_id", width: 150 },
                    { title: "姓名", dataIndex: "student_name" },
                    {
                      title: "状态",
                      width: 120,
                      render: (_: unknown, row) => {
                        if (row.status === "disabled") return <Tag>已禁用</Tag>;
                        if (row.activated || row.status === "active") return <Tag color="green">已激活</Tag>;
                        return <Tag color="gold">未激活</Tag>;
                      },
                    },
                    {
                      title: "操作",
                      width: rosterView === "current" ? 250 : 150,
                      render: (_: unknown, row) => (
                        <Space>
                          <Button icon={<EditOutlined />} onClick={() => openStudentEditor(row)}>
                            编辑
                          </Button>
                          {rosterView === "current" ? (
                            <>
                              <Button icon={<KeyOutlined />} disabled={!row.activated} onClick={() => resetPassword.mutate(row.student_id)}>
                                重置
                              </Button>
                              <Popconfirm title="确认禁用该学生？" onConfirm={() => disableStudent.mutate(row.student_id)}>
                                <Button danger icon={<DeleteOutlined />}>
                                  禁用
                                </Button>
                              </Popconfirm>
                            </>
                          ) : (
                            <Button onClick={() => restoreStudent.mutate(row.student_id)}>
                              恢复
                            </Button>
                          )}
                        </Space>
                      ),
                    },
                  ]}
                />
              </QueryState>
            </div>

          </Space>
        ) : null}
      </Drawer>

      <Modal
        title="班级设置"
        open={settingsOpen}
        okText="保存设置"
        cancelText="取消"
        width={720}
        confirmLoading={updateClass.isPending || updateRegistration.isPending}
        onCancel={() => setSettingsOpen(false)}
        onOk={() => void saveClassConfiguration()}
      >
        <QueryState loading={registration.isLoading} error={registration.error}>
          <Space direction="vertical" size={18} className="full">
            <div className="modal-section">
              <Text strong>班级基本信息</Text>
              <Text type="secondary" className="block-text">
                用于老师后台识别班级，学生端只感知自己所属班级。
              </Text>
              <Form form={classSettingsForm} layout="vertical" className="modal-form">
                <Form.Item name="class_name" label="班级名称" rules={[{ required: true, message: "请输入班级名称" }]}>
                  <Input />
                </Form.Item>
                <Form.Item name="description" label="班级说明" rules={[{ max: 200, message: "班级说明请控制在 200 字以内" }]}>
                  <Input.TextArea rows={3} maxLength={200} showCount className="fixed-textarea" />
                </Form.Item>
                <Form.Item name="status" hidden>
                  <Input />
                </Form.Item>
                <div className="option-group-label">班级状态</div>
                <div className="choice-grid two compact">
                  <button
                    type="button"
                    className={`choice-card ${classStatus === "active" ? "choice-card-active" : ""}`}
                    onClick={() => classSettingsForm.setFieldsValue({ status: "active" })}
                  >
                    <Text strong>使用中</Text>
                    <Text type="secondary">学生可以继续学习和做题。</Text>
                  </button>
                  <button
                    type="button"
                    className={`choice-card ${classStatus === "archived" ? "choice-card-active" : ""}`}
                    onClick={() => classSettingsForm.setFieldsValue({ status: "archived" })}
                  >
                    <Text strong>已归档</Text>
                    <Text type="secondary">保留记录，不再作为当前运营班级。</Text>
                  </button>
                </div>
              </Form>
            </div>

            <div className="modal-section">
              <Text strong>登录规则</Text>
              <Text type="secondary" className="block-text">
                当前名单内学生首次登录时使用这里设置的初始密码；完成改密后才算已激活。
              </Text>
              <Form form={registrationForm} layout="vertical" className="modal-form">
                <Form.Item name="mode" hidden>
                  <Input />
                </Form.Item>
                <Form.Item name="default_password_mode" hidden>
                  <Input />
                </Form.Item>
                <div className="option-group-label">初始密码</div>
                <div className="choice-grid two">
                  <button
                    type="button"
                    className={`choice-card ${defaultPasswordMode === "student_id" ? "choice-card-active" : ""}`}
                    onClick={() => registrationForm.setFieldsValue({ default_password_mode: "student_id", default_password: "" })}
                  >
                    <Text strong>使用学号</Text>
                    <Text type="secondary">初始密码等于学号，适合演示和小班。</Text>
                  </button>
                  <button
                    type="button"
                    className={`choice-card ${defaultPasswordMode === "shared" ? "choice-card-active" : ""}`}
                    onClick={() => registrationForm.setFieldsValue({ default_password_mode: "shared" })}
                  >
                    <Text strong>统一初始密码</Text>
                    <Text type="secondary">老师设置一个统一密码，学生首次登录后修改。</Text>
                  </button>
                </div>
                {defaultPasswordMode === "shared" ? (
                  <Form.Item
                    name="default_password"
                    label="统一初始密码"
                    extra={registration.data?.has_default_password ? "留空则继续使用当前统一密码。" : "至少 8 位。"}
                    rules={[
                      {
                        validator: (_, value) => {
                          if (!value && registration.data?.has_default_password) return Promise.resolve();
                          if (!value) return Promise.reject(new Error("请输入统一初始密码"));
                          if (String(value).length < 8) return Promise.reject(new Error("至少 8 位"));
                          return Promise.resolve();
                        },
                      },
                    ]}
                  >
                    <Input.Password placeholder="输入新的统一初始密码" />
                  </Form.Item>
                ) : (
                  <Form.Item label="当前初始密码" extra="初始密码等于学生学号，学生首次登录后必须修改。">
                    <Input value="使用学生学号" disabled />
                  </Form.Item>
                )}
              </Form>
            </div>
          </Space>
        </QueryState>
      </Modal>

      <Modal
        title="导入学生名单"
        open={importOpen}
        okText="导入名单"
        cancelText="取消"
        width={640}
        confirmLoading={importingRoster}
        okButtonProps={{ disabled: !rosterFile }}
        onCancel={() => {
          setImportOpen(false);
          setRosterFile(null);
        }}
        onOk={() => void importRoster()}
      >
        <Space direction="vertical" size={16} className="full">
          <Text type="secondary">上传 CSV/XLSX。普通导入适合补充名单，覆盖导入适合用一份新名单替换当前名单。</Text>
          <div className="choice-grid two">
            <button
              type="button"
              className={`choice-card ${importMode === "upsert" ? "choice-card-active" : ""}`}
              onClick={() => setImportMode("upsert")}
            >
              <Text strong>普通导入</Text>
              <Text type="secondary">新增学生，更新已有学生姓名，不影响缺失学生。</Text>
            </button>
            <button
              type="button"
              className={`choice-card ${importMode === "overwrite" ? "choice-card-active" : ""}`}
              onClick={() => setImportMode("overwrite")}
            >
              <Text strong>覆盖导入</Text>
              <Text type="secondary">以本次文件为准，缺失学生会被禁用。</Text>
            </button>
          </div>
          <Upload
            maxCount={1}
            beforeUpload={(file) => {
              setRosterFile(file as File);
              return false;
            }}
            onRemove={() => setRosterFile(null)}
          >
            <Button icon={<CloudUploadOutlined />}>选择 CSV/XLSX</Button>
          </Upload>
        </Space>
      </Modal>

      <Modal
        title="新建班级"
        open={createOpen}
        okText="创建班级"
        cancelText="取消"
        confirmLoading={createClass.isPending}
        onCancel={() => setCreateOpen(false)}
        onOk={() => classForm.submit()}
      >
        <Text type="secondary" className="modal-helper">
          只需要填写班级名称，后续可以在班级卡片里导入学生名单。
        </Text>
        <Form form={classForm} layout="vertical" onFinish={(values) => createClass.mutate(values)}>
          <Form.Item name="class_name" label="班级名称" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="description" label="班级说明" rules={[{ max: 200, message: "班级说明请控制在 200 字以内" }]}>
            <Input.TextArea rows={3} maxLength={200} showCount className="fixed-textarea" />
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title={editingStudent ? "编辑学生" : "添加学生"}
        open={studentOpen}
        okText={editingStudent ? "保存学生" : "添加学生"}
        cancelText="取消"
        onCancel={() => {
          setStudentOpen(false);
          setEditingStudent(null);
        }}
        onOk={() => studentForm.submit()}
      >
        <Text type="secondary" className="modal-helper">
          添加或导入即完成班级登记；学生首次登录并修改密码后会显示为已激活。
        </Text>
        <Form form={studentForm} layout="vertical" onFinish={(values) => saveStudent.mutate(values)}>
          <Form.Item name="student_id" label="学号" rules={[{ required: true }]}>
            <Input disabled={Boolean(editingStudent?.activated)} />
          </Form.Item>
          <Form.Item name="student_name" label="姓名" rules={[{ required: true }]}>
            <Input />
          </Form.Item>
        </Form>
      </Modal>
    </Space>
  );
}
function ExperimentsPage() {
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
    onSuccess: (_, resource) => {
      message.success("视频引用已发布，学生端可见");
      invalidateVideoReferenceData(resource.experiment_id);
    },
    onError: (error) => message.error(errorMessage(error)),
  });

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
                      <Tag color={publishedResourceCount ? "green" : "default"}>学生可见 {publishedResourceCount}</Tag>
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
                                    <Tag color={point.published_count ? "green" : "default"}>学生可见 {point.published_count}</Tag>
                                  </Space>
                                </div>
                              </Space>
                              <Button type={point.resource_count ? "default" : "primary"} icon={<PlusOutlined />} onClick={() => setReferencePoint(point)}>
                                引用视频
                              </Button>
                            </Flex>

                            {point.resources.length ? (
                              <div className="video-point-resources">
                                {point.resources.map((resource) => (
                                  <div className="video-point-resource" key={resource.binding_id}>
                                    <div className="video-resource-thumb">
                                      <VideoCameraOutlined />
                                    </div>
                                    <div className="video-point-resource-main">
                                      <Text strong className="video-point-resource-title">
                                        {resource.media_title || resource.title || resource.binding_title || resource.original_file_name}
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
                                      <Button
                                        size="small"
                                        icon={<EyeOutlined />}
                                        disabled={resource.upload_status !== "ready"}
                                        onClick={() =>
                                          setPreviewTarget({
                                            id: resource.media_id,
                                            title: resource.media_title || resource.original_file_name,
                                            original_file_name: resource.original_file_name,
                                            mime_type: resource.mime_type,
                                            upload_status: resource.upload_status,
                                          })
                                        }
                                      >
                                        预览
                                      </Button>
                                      {resource.binding_status === "published" ? (
                                        <Tag color="green">学生可见</Tag>
                                      ) : (
                                        <Button
                                          size="small"
                                          type="primary"
                                          icon={<CheckCircleOutlined />}
                                          disabled={resource.upload_status !== "ready"}
                                          loading={publishPointResource.isPending}
                                          onClick={() => publishPointResource.mutate(resource)}
                                        >
                                          发布引用
                                        </Button>
                                      )}
                                    </Space>
                                  </div>
                                ))}
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

function VideoResourcesPage() {
  const { message } = AntApp.useApp();
  const queryClient = useQueryClient();
  const assets = useQuery({
    queryKey: ["media-assets"],
    queryFn: () => api<ApiList<MediaAsset>>("/api/admin/media/assets?limit=200"),
  });
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [keyword, setKeyword] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>();
  const [sortKey, setSortKey] = useState<"updated_desc" | "name_asc" | "size_desc">("updated_desc");
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [previewAsset, setPreviewAsset] = useState<MediaAsset | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string>();
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState("");

  const assetItems = useMemo(() => assets.data?.items || [], [assets.data?.items]);
  const readyAssets = useMemo(() => assetItems.filter((asset) => asset.upload_status === "ready"), [assetItems]);
  const workingAssets = useMemo(
    () => assetItems.filter((asset) => ["pending", "processing"].includes(asset.upload_status)),
    [assetItems],
  );
  const totalBytes = useMemo(
    () => assetItems.reduce((sum, asset) => sum + Number(asset.file_size_bytes || 0), 0),
    [assetItems],
  );
  const filteredAssets = useMemo(() => {
    const normalized = keyword.trim().toLowerCase();
    const list = assetItems.filter((asset) => {
      if (statusFilter && asset.upload_status !== statusFilter) return false;
      if (!normalized) return true;
      return `${asset.title} ${asset.original_file_name}`.toLowerCase().includes(normalized);
    });
    return [...list].sort((left, right) => {
      if (sortKey === "name_asc") {
        return left.title.localeCompare(right.title, "zh-Hans-CN");
      }
      if (sortKey === "size_desc") {
        return Number(right.file_size_bytes || 0) - Number(left.file_size_bytes || 0);
      }
      const rightTime = new Date(right.updated_at || right.created_at || "").getTime() || 0;
      const leftTime = new Date(left.updated_at || left.created_at || "").getTime() || 0;
      return rightTime - leftTime;
    });
  }, [assetItems, keyword, sortKey, statusFilter]);

  useEffect(() => {
    let objectUrl: string | undefined;
    let cancelled = false;
    setPreviewUrl(undefined);
    setPreviewError("");
    setPreviewLoading(false);
    if (!previewAsset || !isPreviewableVideo(previewAsset)) {
      return undefined;
    }
    setPreviewLoading(true);
    const headers = new Headers();
    const token = getAuthToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
    void fetch(`${apiBase}/api/admin/media/assets/${previewAsset.id}/file`, { headers })
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
  }, [previewAsset]);

  const invalidateVideoData = () => {
    void queryClient.invalidateQueries({ queryKey: ["media-assets"] });
  };

  const uploadAsset = useMutation({
    mutationFn: async () => {
      if (!uploadTitle.trim() || !uploadFile) {
        throw new Error("请输入视频标题并选择文件");
      }
      const body = new FormData();
      body.append("title", uploadTitle.trim());
      body.append("file", uploadFile);
      return api<MediaAsset>("/api/admin/media/assets", { method: "POST", body });
    },
    onSuccess: () => {
      message.success("视频已上传到资源库");
      setUploadTitle("");
      setUploadFile(null);
      setUploadOpen(false);
      invalidateVideoData();
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const renderAssetName = (asset: MediaAsset) => (
    <Space size={10} align="start" className="video-asset-name">
      <div className="video-file-mark">
        <VideoCameraOutlined />
      </div>
      <Space direction="vertical" size={1}>
        <Text strong>{asset.title}</Text>
        <Text type="secondary">{asset.original_file_name}</Text>
      </Space>
    </Space>
  );

  return (
    <Space direction="vertical" size={18} className="full">
      <PageTitle
        title="视频资源"
        description="像素材网盘一样管理已上传视频：上传、搜索、预览和查看处理状态；实验引用不在这个页面完成。"
        extra={
          <Button type="primary" icon={<CloudUploadOutlined />} onClick={() => setUploadOpen(true)}>
            上传视频
          </Button>
        }
      />

      <div className="video-resource-metrics">
        <Card>
          <Statistic title="资源库视频" value={assets.data?.total || 0} prefix={<VideoCameraOutlined />} />
        </Card>
        <Card>
          <Statistic title="可预览" value={readyAssets.length} />
        </Card>
        <Card>
          <Statistic title="处理中" value={workingAssets.length} />
        </Card>
        <Card>
          <Statistic title="占用空间" value={formatBytes(totalBytes)} />
        </Card>
      </div>

      <div className="video-drive-panel">
        <Flex justify="space-between" align="center" gap={14} wrap="wrap" className="video-drive-toolbar">
          <Input.Search
            allowClear
            placeholder="搜索视频标题或文件名"
            value={keyword}
            onChange={(event) => setKeyword(event.target.value)}
            style={{ width: 360 }}
          />
          <Space size={10} wrap>
            <Select
              allowClear
              placeholder="全部状态"
              value={statusFilter}
              onChange={setStatusFilter}
              style={{ width: 140 }}
              options={[
                { value: "ready", label: "就绪" },
                { value: "processing", label: "处理中" },
                { value: "pending", label: "待处理" },
                { value: "failed", label: "失败" },
                { value: "replaced", label: "已替换" },
              ]}
            />
            <Select
              value={sortKey}
              onChange={setSortKey}
              style={{ width: 150 }}
              options={[
                { value: "updated_desc", label: "最近更新" },
                { value: "name_asc", label: "名称 A-Z" },
                { value: "size_desc", label: "文件最大" },
              ]}
            />
            <Segmented
              value={viewMode}
              onChange={(value) => setViewMode(value as "grid" | "list")}
              options={[
                { value: "list", icon: <UnorderedListOutlined />, label: "条" },
                { value: "grid", icon: <AppstoreOutlined />, label: "块" },
              ]}
            />
          </Space>
        </Flex>

        <QueryState loading={assets.isLoading} error={assets.error} empty={!assetItems.length}>
          {!filteredAssets.length ? (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="没有匹配的视频" />
          ) : viewMode === "grid" ? (
            <div className="video-drive-grid">
              {filteredAssets.map((asset) => (
                <div className="video-asset-card" key={asset.id}>
                  <button
                    type="button"
                    className="video-asset-cover"
                    onClick={() => setPreviewAsset(asset)}
                    disabled={!isPreviewableVideo(asset)}
                  >
                    <VideoCameraOutlined />
                    <span>{mediaAssetType(asset)}</span>
                  </button>
                  <Space direction="vertical" size={8} className="full">
                    <div>
                      <Text strong className="video-asset-title">
                        {asset.title}
                      </Text>
                      <Text type="secondary" className="video-asset-file">
                        {asset.original_file_name}
                      </Text>
                    </div>
                    <Flex justify="space-between" align="center" gap={8}>
                      {statusTag(asset.upload_status)}
                      <Text type="secondary">{formatBytes(asset.file_size_bytes)}</Text>
                    </Flex>
                    <Flex justify="space-between" align="center" gap={8}>
                      <Text type="secondary">{mediaAssetTime(asset)}</Text>
                      <Button
                        size="small"
                        icon={<EyeOutlined />}
                        disabled={!isPreviewableVideo(asset)}
                        onClick={() => setPreviewAsset(asset)}
                      >
                        预览
                      </Button>
                    </Flex>
                  </Space>
                </div>
              ))}
            </div>
          ) : (
            <Table
              rowKey="id"
              dataSource={filteredAssets}
              pagination={{ pageSize: 12, showSizeChanger: false }}
              columns={[
                {
                  title: "文件名",
                  render: (_: unknown, asset: MediaAsset) => renderAssetName(asset),
                },
                { title: "类型", width: 96, render: (_: unknown, asset: MediaAsset) => mediaAssetType(asset) },
                { title: "大小", width: 110, render: (_: unknown, asset: MediaAsset) => formatBytes(asset.file_size_bytes) },
                { title: "状态", width: 110, render: (_: unknown, asset: MediaAsset) => statusTag(asset.upload_status) },
                { title: "引用", width: 90, render: (_: unknown, asset: MediaAsset) => asset.association_count || 0 },
                { title: "更新时间", width: 170, render: (_: unknown, asset: MediaAsset) => mediaAssetTime(asset) },
                {
                  title: "操作",
                  width: 110,
                  render: (_: unknown, asset: MediaAsset) => (
                    <Button
                      size="small"
                      icon={<EyeOutlined />}
                      disabled={!isPreviewableVideo(asset)}
                      onClick={() => setPreviewAsset(asset)}
                    >
                      预览
                    </Button>
                  ),
                },
              ]}
            />
          )}
        </QueryState>
      </div>

      <Modal
        title="上传视频"
        open={uploadOpen}
        onCancel={() => {
          setUploadOpen(false);
          setUploadFile(null);
          setUploadTitle("");
        }}
        okText="上传到视频库"
        cancelText="取消"
        okButtonProps={{ loading: uploadAsset.isPending, disabled: !uploadTitle.trim() || !uploadFile }}
        onOk={() => uploadAsset.mutate()}
      >
        <Space direction="vertical" size={14} className="full">
          <Input placeholder="视频标题" value={uploadTitle} onChange={(event) => setUploadTitle(event.target.value)} />
          <Upload.Dragger
            accept="video/*,.mp4,.mov,.m4v,.webm,.avi"
            maxCount={1}
            fileList={
              uploadFile
                ? [
                    {
                      uid: "local-video",
                      name: uploadFile.name,
                      status: "done",
                    },
                  ]
                : []
            }
            beforeUpload={(file) => {
              const nextFile = file as File;
              setUploadFile(nextFile);
              if (!uploadTitle.trim()) {
                setUploadTitle(nextFile.name.replace(/\.[^.]+$/, ""));
              }
              return false;
            }}
            onRemove={() => setUploadFile(null)}
          >
            <p className="ant-upload-drag-icon">
              <CloudUploadOutlined />
            </p>
            <p className="ant-upload-text">拖拽视频到这里，或点击选择文件</p>
            <p className="ant-upload-hint">支持 mp4、mov、m4v、webm、avi；上传后先进入素材库。</p>
          </Upload.Dragger>
        </Space>
      </Modal>

      <Modal
        title={previewAsset?.title || "视频预览"}
        open={Boolean(previewAsset)}
        onCancel={() => setPreviewAsset(null)}
        footer={[
          <Button key="close" onClick={() => setPreviewAsset(null)}>
            关闭
          </Button>,
        ]}
        width={920}
      >
        {previewAsset ? (
          <div className="video-preview-layout">
            <div className="video-preview-stage">
              {previewLoading ? (
                <Spin />
              ) : previewError ? (
                <Alert type="error" showIcon message={previewError} />
              ) : previewUrl ? (
                <video controls src={previewUrl} />
              ) : (
                <Alert type="info" showIcon message="该视频当前不可预览" description="只有上传状态为就绪的视频可以在线播放。" />
              )}
            </div>
            <Descriptions
              size="small"
              column={1}
              items={[
                { key: "file", label: "原始文件", children: previewAsset.original_file_name },
                { key: "type", label: "类型", children: mediaAssetType(previewAsset) },
                { key: "size", label: "大小", children: formatBytes(previewAsset.file_size_bytes) },
                { key: "status", label: "状态", children: statusTag(previewAsset.upload_status) },
                { key: "time", label: "更新时间", children: mediaAssetTime(previewAsset) },
              ]}
            />
          </div>
        ) : null}
      </Modal>
    </Space>
  );
}

type AssistantFormValues = {
  intent: "add_questions" | "repair_question";
  prompt: string;
  question_types: Array<"single_choice" | "true_false" | "fill_blank">;
  count: number;
};

function answerText(answer?: Record<string, unknown>) {
  if (!answer) return "-";
  if (Array.isArray(answer.accepted_answers)) return answer.accepted_answers.map(String).join("，");
  if (answer.value !== undefined) {
    if (typeof answer.value === "boolean") return answer.value ? "正确" : "错误";
    return String(answer.value);
  }
  return JSON.stringify(answer);
}

function sourceRefLabel(ref: Record<string, unknown>) {
  const file = String(ref.source_file || "资料片段");
  const page = ref.page_number ? ` p.${ref.page_number}` : "";
  const section = ref.section_title ? ` · ${ref.section_title}` : "";
  return `${file}${page}${section}`;
}

function assistantActionLabel(action: QuestionBankAssistantPreview["actions"][number]) {
  if (action.action_type === "add_question") return "新增题目建议";
  if (action.action_type === "repair_question") return "审核建议";
  return action.title || action.action_type;
}

function questionBankStatusTag(status?: string) {
  if (status === "published") return <Tag color="green">启用</Tag>;
  if (status === "disabled") return <Tag>未启用</Tag>;
  return statusTag(status);
}

function assistantPromptPlaceholder(intent?: AssistantFormValues["intent"]) {
  if (intent === "add_questions") return "例如：为本章补充 3 道覆盖实验现象和关键结论的选择、判断、填空题。";
  return "例如：请审核这道题的题干、答案和解析是否准确，并给出修改建议。";
}

function QuestionBanksPage() {
  const { message } = AntApp.useApp();
  const experiments = useExperiments();
  const [chapterId, setChapterId] = useState<string>();
  const [questionType, setQuestionType] = useState<string>();
  const [experimentId, setExperimentId] = useState<string>();
  const [search, setSearch] = useState("");
  const [workbenchOpen, setWorkbenchOpen] = useState(false);
  const [workbenchMode, setWorkbenchMode] = useState<"assistant" | "question">("assistant");
  const [selectedQuestion, setSelectedQuestion] = useState<ChapterQuestion | null>(null);
  const [assistantPreview, setAssistantPreview] = useState<QuestionBankAssistantPreview | null>(null);
  const [assistantForm] = Form.useForm<AssistantFormValues>();
  const assistantIntent = Form.useWatch("intent", assistantForm) as AssistantFormValues["intent"] | undefined;

  const chapters = useQuery({
    queryKey: ["question-bank-chapters"],
    queryFn: () => api<ApiList<QuestionBankChapterSummary>>("/api/admin/question-banks/chapters"),
  });

  useEffect(() => {
    if (!chapterId && chapters.data?.items.length) {
      setChapterId(chapters.data.items[0].chapter_id);
    }
  }, [chapterId, chapters.data?.items]);

  const questionParams = new URLSearchParams();
  if (chapterId) questionParams.set("chapter_id", chapterId);
  if (questionType) questionParams.set("question_type", questionType);
  if (experimentId) questionParams.set("experiment_id", experimentId);
  if (search.trim()) questionParams.set("search", search.trim());

  const questions = useQuery({
    queryKey: ["chapter-questions", questionParams.toString()],
    queryFn: () => api<ApiList<ChapterQuestion>>(`/api/admin/question-banks/chapter-questions?${questionParams.toString()}`),
    enabled: Boolean(chapterId),
  });

  const selectedChapter = useMemo(
    () => chapters.data?.items.find((item) => item.chapter_id === chapterId),
    [chapterId, chapters.data?.items],
  );
  const totals = useMemo(
    () =>
      (chapters.data?.items || []).reduce(
        (acc, item) => ({
          total: acc.total + item.total_count,
          choice: acc.choice + item.choice_count,
          trueFalse: acc.trueFalse + item.true_false_count,
          fillBlank: acc.fillBlank + item.fill_blank_count,
          enabled: acc.enabled + item.enabled_count,
        }),
        { total: 0, choice: 0, trueFalse: 0, fillBlank: 0, enabled: 0 },
      ),
    [chapters.data?.items],
  );
  const selectedChapterExperiments = useMemo(() => {
    if (!chapterId) return [];
    return (experiments.data?.items || []).filter((experiment) =>
      experiment.chapter_bindings.some((binding) => binding.chapter_id === chapterId),
    );
  }, [chapterId, experiments.data?.items]);

  const openAssistantWorkbench = () => {
    setWorkbenchMode("assistant");
    setSelectedQuestion(null);
    setAssistantPreview(null);
    assistantForm.setFieldsValue({
      intent: "add_questions",
      prompt: "",
      count: 5,
      question_types: ["single_choice", "true_false", "fill_blank"],
    });
    setWorkbenchOpen(true);
  };

  const openQuestionWorkbench = (question: ChapterQuestion) => {
    setWorkbenchMode("question");
    setSelectedQuestion(question);
    setAssistantPreview(null);
    assistantForm.setFieldsValue({
      intent: "repair_question",
      prompt: "",
      count: 5,
      question_types: [question.question_type],
    });
    setWorkbenchOpen(true);
  };

  const closeWorkbench = () => {
    setWorkbenchOpen(false);
    setAssistantPreview(null);
  };

  const assistant = useMutation({
    mutationFn: (values: AssistantFormValues) => {
      if (values.intent === "repair_question" && !selectedQuestion) {
        throw new Error("请先打开一道题目");
      }
      return postJson<QuestionBankAssistantPreview>("/api/admin/question-banks/assistant/preview", {
        ...values,
        chapter_id: chapterId,
        experiment_id: selectedQuestion?.experiment_id || experimentId,
        question_id: values.intent === "repair_question" ? selectedQuestion?.id : undefined,
      });
    },
    onSuccess: (data) => {
      setAssistantPreview(data);
      message.success("已生成 AI 建议预览");
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const showAddControls = assistantIntent === "add_questions";
  const workbenchTitle = workbenchMode === "question" ? "题目详情" : "新增题目建议";

  return (
    <Space direction="vertical" size={18} className="full">
      <PageTitle
        title="题库管理"
        description="按理论章节查看当前题库；新增建议和当前题审核由题库助手生成预览，确认前不会修改题库。"
      />

      <div className="stat-grid">
        <Card>
          <Statistic title="当前题库" value={totals.total} suffix="题" prefix={<DatabaseOutlined />} />
        </Card>
        <Card>
          <Statistic title="选择题" value={totals.choice} />
        </Card>
        <Card>
          <Statistic title="判断题" value={totals.trueFalse} />
        </Card>
        <Card>
          <Statistic title="填空题" value={totals.fillBlank} />
        </Card>
      </div>

      <div className="question-bank-layout">
        <Card className="question-chapter-panel">
          <Flex justify="space-between" align="center" className="drawer-table-heading">
            <div>
              <Text strong>章节题库</Text>
              <Text type="secondary" className="block-text">
                先选章节，再查看该章节下的题目。
              </Text>
            </div>
            <Tag color="green">启用 {totals.enabled}</Tag>
          </Flex>
          <QueryState loading={chapters.isLoading} error={chapters.error} empty={!chapters.data?.items.length}>
            <Table
              rowKey="chapter_id"
              size="small"
              pagination={false}
              dataSource={chapters.data?.items || []}
              rowClassName={(row) => (row.chapter_id === chapterId ? "question-chapter-row-active" : "")}
              onRow={(record) => ({
                onClick: () => {
                  setChapterId(record.chapter_id);
                  setQuestionType(undefined);
                  setExperimentId(undefined);
                  setSearch("");
                  setWorkbenchOpen(false);
                  setSelectedQuestion(null);
                  setAssistantPreview(null);
                },
              })}
              columns={[
                {
                  title: "章节",
                  render: (_: unknown, row: QuestionBankChapterSummary) => (
                    <Space direction="vertical" size={2}>
                      <Text strong>{row.chapter_title}</Text>
                      <Text type="secondary">{row.linked_experiment_count} 个绑定实验</Text>
                    </Space>
                  ),
                },
                { title: "总题", dataIndex: "total_count", width: 68 },
                {
                  title: "构成",
                  width: 150,
                  render: (_: unknown, row: QuestionBankChapterSummary) => (
                    <Space size={4} wrap>
                      <Tag>选 {row.choice_count}</Tag>
                      <Tag>判 {row.true_false_count}</Tag>
                      <Tag>填 {row.fill_blank_count}</Tag>
                    </Space>
                  ),
                },
              ]}
            />
          </QueryState>
        </Card>

        <Card title="当前章节题目" className="question-bank-question-panel">
          <Flex justify="space-between" gap={16} wrap="wrap" className="question-list-heading">
            <div>
              <Text className="eyebrow">当前章节</Text>
              <Title level={3}>{selectedChapter?.chapter_title || "请选择章节"}</Title>
              <Space wrap>
                <Tag color="green">启用 {selectedChapter?.enabled_count || 0}</Tag>
                <Tag>选择 {selectedChapter?.choice_count || 0}</Tag>
                <Tag>判断 {selectedChapter?.true_false_count || 0}</Tag>
                <Tag>填空 {selectedChapter?.fill_blank_count || 0}</Tag>
              </Space>
            </div>
            <Space wrap className="question-list-heading-actions">
              <Button type="primary" disabled={!selectedChapter} icon={<PlusOutlined />} onClick={openAssistantWorkbench}>
                新增题目建议
              </Button>
            </Space>
          </Flex>

          <div className="question-bank-actions">
            <Select
              allowClear
              placeholder="题型"
              value={questionType}
              onChange={setQuestionType}
              options={[
                { value: "single_choice", label: "选择" },
                { value: "true_false", label: "判断" },
                { value: "fill_blank", label: "填空" },
              ]}
            />
            <Select
              allowClear
              placeholder="绑定实验"
              value={experimentId}
              onChange={setExperimentId}
              options={selectedChapterExperiments.map((experiment) => ({
                value: experiment.id,
                label: `${experiment.code} ${experiment.title}`,
              }))}
            />
            <Input.Search
              allowClear
              placeholder="搜索题干或解析"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              onSearch={setSearch}
            />
          </div>

          <QueryState loading={questions.isLoading} error={questions.error} empty={!questions.data?.items.length}>
            <Table
              rowKey="id"
              dataSource={questions.data?.items || []}
              pagination={{ pageSize: 8 }}
              onRow={(record) => ({ onClick: () => openQuestionWorkbench(record) })}
              columns={[
                { title: "题型", width: 90, dataIndex: "question_type", render: questionTypeLabel },
                { title: "题干", dataIndex: "stem" },
                {
                  title: "绑定实验",
                  width: 220,
                  render: (_: unknown, row: ChapterQuestion) => `${row.experiment_code || ""} ${row.experiment_title || ""}`,
                },
                { title: "状态", width: 100, dataIndex: "status", render: questionBankStatusTag },
                {
                  title: "操作",
                  width: 130,
                  render: (_: unknown, row: ChapterQuestion) => (
                    <Button
                      type="link"
                      icon={<EditOutlined />}
                      onClick={(event) => {
                        event.stopPropagation();
                        openQuestionWorkbench(row);
                      }}
                    >
                      查看详情
                    </Button>
                  ),
                },
              ]}
            />
          </QueryState>
        </Card>
      </div>

      <Modal
        title={workbenchTitle}
        open={workbenchOpen}
        width={920}
        onCancel={closeWorkbench}
        footer={[
          <Button key="close" onClick={closeWorkbench}>
            关闭
          </Button>,
        ]}
      >
        <Space direction="vertical" size={16} className="full">
          {workbenchMode === "question" && selectedQuestion ? (
            <div className="modal-section question-detail-card">
              <div>
                <Text className="eyebrow">题目详情</Text>
                <Title level={4}>{selectedQuestion.stem}</Title>
                <Space wrap className="question-detail-meta">
                  <Tag color="blue">{questionTypeLabel(selectedQuestion.question_type)}</Tag>
                  {questionBankStatusTag(selectedQuestion.status)}
                  {selectedQuestion.experiment_code || selectedQuestion.experiment_title ? (
                    <Tag>
                      {selectedQuestion.experiment_code} {selectedQuestion.experiment_title}
                    </Tag>
                  ) : null}
                </Space>
              </div>
              {selectedQuestion.options?.length ? (
                <div className="question-options question-workbench-options">
                  {selectedQuestion.options.map((option, index) => {
                    const label = typeof option === "string" ? String.fromCharCode(65 + index) : option.label || String.fromCharCode(65 + index);
                    const text = typeof option === "string" ? option : option.text || "";
                    return (
                      <div key={`${label}-${index}`} className="question-option">
                        <Text strong>{label}</Text>
                        <Text>{text}</Text>
                      </div>
                    );
                  })}
                </div>
              ) : null}
              <Descriptions size="small" column={1} className="question-workbench-descriptions">
                <Descriptions.Item label="答案">{answerText(selectedQuestion.answer)}</Descriptions.Item>
                <Descriptions.Item label="解析">{selectedQuestion.explanation || "暂无解析"}</Descriptions.Item>
              </Descriptions>
              {selectedQuestion.source_refs?.length ? (
                <div className="question-source-section">
                  <Text strong>来源依据</Text>
                  <Space wrap className="question-source-list">
                    {selectedQuestion.source_refs.slice(0, 3).map((ref, index) => (
                      <Tag key={index}>{sourceRefLabel(ref)}</Tag>
                    ))}
                  </Space>
                </div>
              ) : null}
            </div>
          ) : (
            <Alert
              type="info"
              showIcon
              message={selectedChapter?.chapter_title || "请选择章节"}
              description="题库助手会基于当前章节和可用资料生成待确认建议，不会直接修改题库。"
            />
          )}

          <div className="modal-section question-assistant-card">
            <Flex justify="space-between" align="flex-start" gap={12} wrap="wrap">
              <div>
                <Text strong>题库助手</Text>
                <Text type="secondary" className="block-text">
                  {workbenchMode === "question"
                    ? "让 AI 审核当前题，生成修改建议预览；这里不会直接改题。"
                    : "让 AI 为当前章节生成新增题目建议预览；这里不会直接写入题库。"}
                </Text>
              </div>
              <Tag color="green">{workbenchMode === "question" ? "审核当前题" : "新增题目建议"}</Tag>
            </Flex>
            <Form<AssistantFormValues>
              form={assistantForm}
              layout="vertical"
              className="modal-form"
              initialValues={{
                intent: "add_questions",
                count: 5,
                question_types: ["single_choice", "true_false", "fill_blank"],
              }}
              onFinish={(values) => assistant.mutate(values)}
            >
              <Form.Item name="intent" hidden>
                <Input />
              </Form.Item>
              <Form.Item name="prompt" label="给 AI 的要求" rules={[{ required: true, message: "请输入需求" }]}>
                <Input.TextArea rows={4} placeholder={assistantPromptPlaceholder(assistantIntent)} className="fixed-textarea" />
              </Form.Item>
              {showAddControls ? (
                <div className="compact-form-grid">
                  <Form.Item name="question_types" label="题型">
                    <Select
                      mode="multiple"
                      options={[
                        { value: "single_choice", label: "选择" },
                        { value: "true_false", label: "判断" },
                        { value: "fill_blank", label: "填空" },
                      ]}
                    />
                  </Form.Item>
                  <Form.Item name="count" label="建议数量">
                    <InputNumber min={1} max={20} className="full" />
                  </Form.Item>
                </div>
              ) : null}
              <Button type="primary" htmlType="submit" loading={assistant.isPending} icon={<QuestionCircleOutlined />}>
                {workbenchMode === "question" ? "生成审核建议" : "生成新增建议"}
              </Button>
            </Form>
            <Alert
              className="drawer-hint"
              type="info"
              showIcon
              message="助手只生成待确认建议"
              description="本轮预览不会直接改动题库。"
            />
            {assistantPreview ? (
              <div className="assistant-preview">
                <Text strong>{assistantPreview.summary}</Text>
                {assistantPreview.warnings.map((warning) => (
                  <Alert key={warning} type="warning" showIcon title={warning} />
                ))}
                <Space direction="vertical" size={10} className="full">
                  {assistantPreview.actions.map((action, index) => (
                    <div key={`${action.action_type}-${index}`} className="assistant-action">
                      <Space direction="vertical" size={6} className="full">
                        <Space>
                          <Tag color="blue">{assistantActionLabel(action)}</Tag>
                          {action.question_type ? <Tag>{questionTypeLabel(action.question_type)}</Tag> : null}
                        </Space>
                        <Text>{action.stem || action.suggested_stem || action.summary}</Text>
                        {action.answer ? <Text type="secondary">答案：{answerText(action.answer)}</Text> : null}
                      </Space>
                    </div>
                  ))}
                </Space>
              </div>
            ) : null}
          </div>
        </Space>
      </Modal>
    </Space>
  );
}

function AnalyticsPage() {
  const { message } = AntApp.useApp();
  const classes = useQuery({ queryKey: ["classes"], queryFn: () => api<ClassItem[]>("/api/admin/classes") });
  const [classId, setClassId] = useState<string>();
  const [studentId, setStudentId] = useState<string>();
  const activeClassId = classId || classes.data?.[0]?.id;
  const dashboard = useQuery({
    queryKey: ["analytics-dashboard", activeClassId],
    queryFn: () => api<AnalyticsDashboard>(`/api/admin/analytics/classes/${activeClassId}/dashboard`),
    enabled: Boolean(activeClassId),
  });
  const weakPoints = useQuery({
    queryKey: ["weak-points", activeClassId],
    queryFn: () => api<ApiList<Record<string, unknown>>>(`/api/admin/analytics/classes/${activeClassId}/weak-points`),
    enabled: Boolean(activeClassId),
  });
  const studentReport = useQuery({
    queryKey: ["student-report", activeClassId, studentId],
    queryFn: () => api<Record<string, unknown>>(`/api/admin/analytics/classes/${activeClassId}/students/${studentId}`),
    enabled: Boolean(activeClassId && studentId),
  });

  const exportReport = async () => {
    if (!activeClassId) return;
    const response = await fetch(`${apiBase}/api/admin/analytics/classes/${activeClassId}/export`, {
      headers: { Authorization: `Bearer ${getAuthToken()}` },
    });
    if (!response.ok) {
      message.error("导出失败");
      return;
    }
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `class-${activeClassId}-experiment-report.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  const matrixColumns = useMemo(() => {
    const experiments = dashboard.data?.experiments || [];
    return [
      { title: "学号", dataIndex: "student_id", fixed: "left" as const, width: 130 },
      { title: "姓名", dataIndex: "student_name", fixed: "left" as const, width: 120 },
      ...experiments.map((experiment) => ({
        title: experiment.code,
        width: 140,
        render: (_: unknown, row: AnalyticsDashboard["matrix"][number]) => {
          const state = row.experiments[experiment.id];
          return (
            <Space direction="vertical" size={2} className="full">
              {statusTag(state?.status)}
              <Progress percent={Math.round(state?.completion_percent || 0)} size="small" />
              <Text type="secondary">{state?.best_score ?? "-"} 分</Text>
            </Space>
          );
        },
      })),
    ];
  }, [dashboard.data?.experiments]);

  return (
    <Space direction="vertical" size={18} className="full">
      <PageTitle
        title="学情分析"
        description="按班级查看实验进度、答题情况、个人路径和薄弱点。"
        extra={<Button onClick={() => void exportReport()}>导出报告</Button>}
      />
      <Card>
        <Select
          placeholder="选择班级"
          style={{ width: 280 }}
          value={activeClassId}
          onChange={(value) => {
            setClassId(value);
            setStudentId(undefined);
          }}
          options={(classes.data || []).map((item) => ({ value: item.id, label: item.class_name }))}
        />
      </Card>
      <QueryState loading={dashboard.isLoading} error={dashboard.error} empty={!activeClassId}>
        <div className="stat-grid">
          <Card>
            <Statistic title="班级人数" value={dashboard.data?.metrics.class_size || 0} />
          </Card>
          <Card>
            <Statistic title="活跃学生" value={dashboard.data?.metrics.active_students || 0} />
          </Card>
          <Card>
            <Statistic title="完成率" value={dashboard.data?.metrics.completion_rate || 0} suffix="%" />
          </Card>
          <Card>
            <Statistic title="平均分" value={dashboard.data?.metrics.average_score || 0} suffix="分" />
          </Card>
        </div>
        <Card title="实验完成矩阵">
          <Table
            rowKey="student_id"
            scroll={{ x: 1180 }}
            dataSource={dashboard.data?.matrix || []}
            columns={matrixColumns}
            onRow={(record) => ({
              onClick: () => setStudentId(record.student_id),
            })}
          />
        </Card>
        <div className="two-column">
          <Card title="薄弱点">
            <Table
              rowKey={(row) => String(row.question_id || row.experiment_id || row.stem)}
              size="small"
              dataSource={weakPoints.data?.items || []}
              pagination={{ pageSize: 6 }}
              columns={[
                { title: "实验", render: (_: unknown, row: Record<string, unknown>) => `${row.experiment_code || ""} ${row.experiment_title || ""}` },
                { title: "题目", dataIndex: "stem" },
                { title: "错误率", dataIndex: "incorrect_rate", width: 90, render: (value) => `${value || 0}%` },
                { title: "KP", dataIndex: "unmapped", width: 90, render: (value) => (value ? <Tag>未映射</Tag> : <Tag color="green">已映射</Tag>) },
              ]}
            />
          </Card>
          <Card title="学生路径">
            {studentId ? (
              <QueryState loading={studentReport.isLoading} error={studentReport.error}>
                <pre className="json-preview">{JSON.stringify(studentReport.data, null, 2)}</pre>
              </QueryState>
            ) : (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="点击矩阵中的学生查看路径" />
            )}
          </Card>
        </div>
      </QueryState>
    </Space>
  );
}

function FeedbackPage() {
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

function SettingsPage() {
  const { message } = AntApp.useApp();
  const queryClient = useQueryClient();
  const [form] = Form.useForm();
  const platformSettings = useQuery({
    queryKey: ["platform-settings"],
    queryFn: () => api<PlatformSettingsResponse>("/api/admin/platform-settings"),
  });

  useEffect(() => {
    if (platformSettings.data) {
      form.setFieldsValue(platformSettings.data.settings);
    }
  }, [form, platformSettings.data]);

  const save = useMutation({
    mutationFn: (values: LearningBehaviorSettings) => putJson<PlatformSettingsResponse>("/api/admin/platform-settings", values),
    onSuccess: () => {
      message.success("设置已保存");
      void queryClient.invalidateQueries({ queryKey: ["platform-settings"] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const canEdit = Boolean(platformSettings.data?.can_edit);

  return (
    <Space direction="vertical" size={18} className="full">
      <PageTitle title="系统设置" description="控制全体 H5/手机学习端的测试、助手和反馈入口。" />
      <QueryState loading={platformSettings.isLoading} error={platformSettings.error}>
        <Form form={form} layout="vertical" onFinish={(values) => save.mutate(values as LearningBehaviorSettings)}>
          <Space direction="vertical" size={18} className="full">
            {!canEdit ? <Alert type="info" showIcon title="当前账号可查看全局学习端设置，只有管理员可以修改。" /> : null}
            <Card title="测试流程">
              <div className="settings-grid">
                <div className="settings-section">
                  <Flex justify="space-between" align="center" gap={12}>
                    <div>
                      <Text strong>课前摸底</Text>
                      <Text type="secondary" className="block-text">
                        控制学生进入章节前是否看到摸底测试。
                      </Text>
                    </div>
                    <Form.Item name={["assessment", "pretest_enabled"]} valuePropName="checked" noStyle>
                      <Switch disabled={!canEdit} />
                    </Form.Item>
                  </Flex>
                  <Form.Item
                    name={["assessment", "pretest_question_count"]}
                    label="摸底题数"
                    rules={[{ required: true, message: "请输入摸底题数" }]}
                  >
                    <InputNumber min={1} max={50} precision={0} disabled={!canEdit} className="full" />
                  </Form.Item>
                </div>
                <div className="settings-section">
                  <Flex justify="space-between" align="center" gap={12}>
                    <div>
                      <Text strong>课后测试</Text>
                      <Text type="secondary" className="block-text">
                        控制章节学习后的巩固测试入口和题量。
                      </Text>
                    </div>
                    <Form.Item name={["assessment", "posttest_enabled"]} valuePropName="checked" noStyle>
                      <Switch disabled={!canEdit} />
                    </Form.Item>
                  </Flex>
                  <Form.Item
                    name={["assessment", "posttest_question_count"]}
                    label="课后题数"
                    rules={[{ required: true, message: "请输入课后题数" }]}
                  >
                    <InputNumber min={1} max={50} precision={0} disabled={!canEdit} className="full" />
                  </Form.Item>
                </div>
              </div>
            </Card>
            <Card title="学习端功能">
              <div className="settings-grid">
                <div className="settings-section compact">
                  <Flex justify="space-between" align="center" gap={12}>
                    <div>
                      <Text strong>AI 学习助手</Text>
                      <Text type="secondary" className="block-text">
                        控制学生端课程问答入口是否可用。
                      </Text>
                    </div>
                    <Form.Item name={["learning_features", "ai_assistant_enabled"]} valuePropName="checked" noStyle>
                      <Switch disabled={!canEdit} />
                    </Form.Item>
                  </Flex>
                </div>
                <div className="settings-section compact">
                  <Flex justify="space-between" align="center" gap={12}>
                    <div>
                      <Text strong>反馈入口</Text>
                      <Text type="secondary" className="block-text">
                        控制学生是否能提交课程或系统反馈。
                      </Text>
                    </div>
                    <Form.Item name={["learning_features", "feedback_enabled"]} valuePropName="checked" noStyle>
                      <Switch disabled={!canEdit} />
                    </Form.Item>
                  </Flex>
                </div>
                <div className="settings-section compact">
                  <Flex justify="space-between" align="center" gap={12}>
                    <div>
                      <Text strong>教师审核/调试入口</Text>
                      <Text type="secondary" className="block-text">
                        控制学生端是否显示审核预览和调试类入口。
                      </Text>
                    </div>
                    <Form.Item name={["learning_features", "student_review_preview_enabled"]} valuePropName="checked" noStyle>
                      <Switch disabled={!canEdit} />
                    </Form.Item>
                  </Flex>
                </div>
              </div>
            </Card>
            <Button type="primary" htmlType="submit" loading={save.isPending} disabled={!canEdit}>
              保存设置
            </Button>
          </Space>
          </Form>
      </QueryState>
    </Space>
  );
}

function AIConfigurationPage() {
  const { message } = AntApp.useApp();
  const queryClient = useQueryClient();
  const [form] = Form.useForm();
  const [usageRange, setUsageRange] = useState<"1d" | "7d" | "30d">("7d");
  const aiConfig = useQuery({
    queryKey: ["ai-configuration"],
    queryFn: () => api<AIConfiguration>("/api/admin/ai-configuration"),
  });

  useEffect(() => {
    if (aiConfig.data) {
      form.setFieldsValue({
        provider: aiConfig.data.provider,
        base_url: aiConfig.data.base_url,
        model: aiConfig.data.model,
        connection_check_interval_minutes: aiConfig.data.connection_check_interval_minutes,
        api_key: "",
        enabled_features: aiConfig.data.enabled_features,
      });
    }
  }, [aiConfig.data, form]);

  const save = useMutation({
    mutationFn: (values: AIConfigurationUpdate) => putJson<AIConfiguration>("/api/admin/ai-configuration", values),
    onSuccess: () => {
      message.success("AI 配置已保存");
      void queryClient.invalidateQueries({ queryKey: ["ai-configuration"] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const canEdit = Boolean(aiConfig.data?.can_edit);
  const status = aiConfig.data?.status;
  const submit = (values: AIConfigurationUpdate & { api_key?: string }) => {
    const currentScopes = aiConfig.data?.enabled_features;
    const submittedScopes = values.enabled_features || currentScopes;
    const payload: AIConfigurationUpdate = {
      provider: "openai",
      base_url: values.base_url || "",
      model: values.model || "",
      connection_check_interval_minutes: values.connection_check_interval_minutes || 30,
      enabled_features: {
        rag_access_enabled: submittedScopes?.rag_access_enabled ?? true,
        student_ai_assistant: submittedScopes?.student_ai_assistant ?? true,
        student_learning_analytics: submittedScopes?.student_learning_analytics ?? true,
        question_bank_assistant: true,
        teacher_learning_analytics: true,
      },
    };
    const newSecret = String(values.api_key || "").trim();
    if (newSecret) {
      payload.api_key = newSecret;
    }
    save.mutate(payload);
  };

  const statusMeta: Record<
    NonNullable<AIConfiguration["status"]>["connectivity_status"],
    { label: string; color: string; valueColor: string }
  > = {
    connected: { label: "连接正常", color: "#005826", valueColor: "#005826" },
    failed: { label: "连接失败", color: "#b42318", valueColor: "#b42318" },
    stale: { label: "需重新检测", color: "#b8892f", valueColor: "#8a6d1f" },
    untested: { label: "未检测", color: "#356f9c", valueColor: "#356f9c" },
    not_configured: { label: "待配置", color: "default", valueColor: "#697a72" },
  };
  const currentStatus = statusMeta[status?.connectivity_status || "not_configured"];
  const lastCheckedText = status?.last_checked_at
    ? dayjs(status.last_checked_at).format("YYYY-MM-DD HH:mm")
    : "尚未检测";
  const nextCheckText = status?.next_check_due_at
    ? dayjs(status.next_check_due_at).format("YYYY-MM-DD HH:mm")
    : "-";
  const modeLabels: Record<string, string> = {
    not_configured: "未启用",
    connection_untested: "待自动检测",
    connection_stale: "需重新检测",
    connection_failed: "暂不可用",
    openai_api: "OpenAI API",
  };
  const modeLabel = modeLabels[status?.effective_mode || "not_configured"] || "未知";
  const recentRequests = status?.recent_request_count || 0;
  const recentErrors = status?.recent_error_count || 0;
  const successRate = recentRequests > 0 ? Math.round(((recentRequests - recentErrors) / recentRequests) * 100) : 0;
  const rangeLabels: Record<typeof usageRange, string> = {
    "1d": "近 1 天",
    "7d": "近 7 天",
    "30d": "近 30 天",
  };
  const currentHalfDayStart = dayjs()
    .startOf("day")
    .add(dayjs().hour() >= 12 ? 12 : 0, "hour");
  const trend = status?.usage_trends?.[usageRange];
  const emptyTrendBuckets =
    usageRange === "1d"
      ? Array.from({ length: 24 }, (_, index) => ({
          bucket: dayjs().subtract(23 - index, "hour").format("YYYY-MM-DD HH:00"),
          request_count: 0,
          error_count: 0,
        }))
      : usageRange === "7d"
        ? Array.from({ length: 14 }, (_, index) => ({
            bucket: currentHalfDayStart.subtract((13 - index) * 12, "hour").format("YYYY-MM-DD HH:00"),
            request_count: 0,
            error_count: 0,
          }))
        : Array.from({ length: 30 }, (_, index) => ({
            bucket: dayjs().subtract(29 - index, "day").format("YYYY-MM-DD"),
            request_count: 0,
            error_count: 0,
          }));
  const trendBuckets = trend?.buckets?.length ? trend.buckets : emptyTrendBuckets;
  const chartData = trendBuckets.flatMap((bucket) => {
    const label =
      usageRange === "1d"
        ? dayjs(bucket.bucket).format("HH:mm")
        : usageRange === "7d"
          ? dayjs(bucket.bucket).format("MM/DD\nHH:mm")
          : dayjs(bucket.bucket).format("MM/DD");
    return [
      { time: bucket.bucket, label, type: "调用", value: bucket.request_count },
      { time: bucket.bucket, label, type: "错误", value: bucket.error_count },
    ];
  });
  const lastRequestText = status?.last_request_summary
    ? `${dayjs(status.last_request_summary.called_at).format("YYYY-MM-DD HH:mm")} · ${status.last_request_summary.channel} · ${
        status.last_request_summary.status === "success" ? "成功" : "失败"
      }`
    : "暂无调用记录";
  const trendChartConfig = {
    data: chartData,
    xField: "label",
    yField: "value",
    colorField: "type",
    height: 220,
    autoFit: true,
    smooth: true,
    point: {
      size: 3,
      shapeField: "circle",
    },
    scale: {
      y: { nice: true },
      color: { range: ["#005826", "#b42318"] },
    },
    axis: {
      x: { title: false, labelAutoHide: false, labelAutoRotate: false },
      y: {
        title: false,
        labelFormatter: (value: string) => {
          const numeric = Number(value);
          return Number.isInteger(numeric) ? String(numeric) : "";
        },
      },
    },
    legend: {
      color: { position: "top" },
    },
  };
  const policyStatus = aiConfig.data?.student_ai_policy;
  const policyOutcomes = policyStatus?.outcomes || [];
  const policyRailItems = [
    { key: "scope", title: "课程范围", description: "课程外请求引导回无机化学学习" },
    { key: "experiment", title: "实验安全", description: "危险操作只讲原理和安全提醒" },
    { key: "assessment", title: "测验保护", description: "索要答案时只给思路提示" },
    { key: "evidence", title: "平台证据", description: "实验现象、视频和资料先检索来源" },
    { key: "course", title: "课程问答", description: "普通问题进入学生 AI 学习助手" },
  ];

  return (
    <Space direction="vertical" size={18} className="full">
      <PageTitle title="AI配置" description="配置 OpenAI API 接入、连接检测和 Agent 功能范围。" />
      <QueryState loading={aiConfig.isLoading} error={aiConfig.error}>
        <Form form={form} layout="vertical" onFinish={submit}>
          <div className="ai-config-dashboard">
            <Card title="运行状态" className="ai-runtime-card">
              <div className="ai-runtime-grid">
                <div className="ai-runtime-primary">
                  <Flex justify="space-between" align="start" gap={16} className="ai-summary-head">
                    <div>
                      <Text type="secondary">连接状态</Text>
                      <Title level={3} className="ai-status-title" style={{ color: currentStatus.valueColor }}>
                        {currentStatus.label}
                      </Title>
                      <Text type="secondary">{status?.message}</Text>
                    </div>
                    <Tag color={currentStatus.color}>{currentStatus.label}</Tag>
                  </Flex>
                  {status?.last_check_message ? <Text className="block-text ai-check-message">{status.last_check_message}</Text> : null}
                </div>

                <Descriptions size="small" column={1} className="ai-runtime-descriptions">
                  <Descriptions.Item label="最近检测">{lastCheckedText}</Descriptions.Item>
                  <Descriptions.Item label="下次检测">{nextCheckText}</Descriptions.Item>
                  <Descriptions.Item label="API Key">{aiConfig.data?.api_key_configured ? "已配置" : "未配置"}</Descriptions.Item>
                  <Descriptions.Item label="AI 通道">{modeLabel}</Descriptions.Item>
                </Descriptions>
              </div>
            </Card>

            <Card title="AI 使用概况" className="ai-usage-card">
              <div className="ai-usage-layout">
                <div className="ai-usage-stats">
                  <Statistic title="近 24 小时请求" value={recentRequests} />
                  <Statistic
                    title="错误"
                    value={recentErrors}
                    valueStyle={{ color: recentErrors ? "#b42318" : "#0d1f17" }}
                  />
                  <Statistic title="成功率" value={recentRequests ? successRate : "-"} suffix={recentRequests ? "%" : ""} />
                  <div>
                    <Text type="secondary">最近调用</Text>
                    <Text className="block-text">{lastRequestText}</Text>
                  </div>
                </div>
                <div className="ai-usage-chart">
                  <Flex justify="space-between" align="center" className="ai-chart-heading">
                    <div>
                      <Text strong>{rangeLabels[usageRange]}调用趋势</Text>
                      <Text type="secondary" className="block-text">
                        本系统 Agent 日志
                      </Text>
                    </div>
                    <Segmented
                      size="small"
                      value={usageRange}
                      onChange={(value) => setUsageRange(value as "1d" | "7d" | "30d")}
                      options={[
                        { label: "1天", value: "1d" },
                        { label: "7天", value: "7d" },
                        { label: "30天", value: "30d" },
                      ]}
                    />
                  </Flex>
                  <div
                    className="ai-line-chart"
                    aria-label={`${rangeLabels[usageRange]} AI 调用趋势，${trendBuckets.length}个时间点`}
                    data-trend-points={trendBuckets.length}
                  >
                    <Suspense fallback={<div className="ai-line-chart-placeholder" />}>
                      <UsageLineChart {...trendChartConfig} />
                    </Suspense>
                  </div>
                </div>
              </div>
            </Card>

            <Card
              title={
                <Flex align="center" gap={10}>
                  <SafetyCertificateOutlined />
                  <span>学生 AI 安全护栏</span>
                </Flex>
              }
              extra={<Tag color={policyStatus?.active ? "#005826" : "default"}>{policyStatus?.active ? "运行中" : "待模型配置"}</Tag>}
              className="ai-policy-card"
            >
              <div className="ai-policy-overview">
                <div className="ai-policy-flow">
                  <div className="ai-policy-flow-node">
                    <span>学生提问</span>
                    <strong>进入 AI 前</strong>
                  </div>
                  <ArrowRightOutlined />
                  <div className="ai-policy-flow-node ai-policy-flow-node-active">
                    <span>安全判定</span>
                    <strong>{policyStatus?.model || "未配置模型"}</strong>
                  </div>
                  <ArrowRightOutlined />
                  <div className="ai-policy-flow-node">
                    <span>学生 AI</span>
                    <strong>按判定处理</strong>
                  </div>
                </div>
                <div className="ai-policy-kpis">
                  <div>
                    <Text type="secondary">近 24 小时判定</Text>
                    <strong>{policyStatus?.recent_decision_count || 0}</strong>
                  </div>
                  <div>
                    <Text type="secondary">结构兜底</Text>
                    <strong className={policyStatus?.invalid_decision_count ? "danger-text" : ""}>
                      {policyStatus?.invalid_decision_count || 0}
                    </strong>
                  </div>
                  <div>
                    <Text type="secondary">策略版本</Text>
                    <strong>{policyStatus?.version || "student-ai-policy-v1"}</strong>
                  </div>
                </div>
              </div>

              <div className="ai-policy-rail">
                {policyRailItems.map((item) => (
                  <div key={item.key} className="ai-policy-rail-item">
                    <CheckCircleOutlined />
                    <div>
                      <Text strong>{item.title}</Text>
                      <Text type="secondary" className="block-text">
                        {item.description}
                      </Text>
                    </div>
                  </div>
                ))}
              </div>

              <div className="ai-policy-outcome-panel">
                <Flex justify="space-between" align="center" gap={12} className="ai-policy-section-head">
                  <Text strong>最近判定分布</Text>
                  <Text type="secondary">本系统 Agent 日志</Text>
                </Flex>
                {policyOutcomes.length ? (
                  <div className="ai-policy-outcomes">
                    {policyOutcomes.map((item) => (
                      <div key={item.mode} className="ai-policy-outcome">
                        <span>{item.label}</span>
                        <strong>{item.count}</strong>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="ai-policy-empty">
                    暂无学生 AI 安全判定记录
                  </div>
                )}
              </div>
            </Card>

            <div className="ai-config-body-grid">
              <Card title="OpenAI API 接入" className="ai-config-main-card">
                {!canEdit ? <Alert type="info" showIcon title="当前账号可查看 AI 配置，只有管理员可以修改。" className="section-alert" /> : null}
                <div className="ai-provider-fixed compact">
                  <div>
                    <Text type="secondary">供应商</Text>
                    <Text strong className="block-text">
                      OpenAI API
                    </Text>
                  </div>
                  <div>
                    <Text type="secondary">说明</Text>
                    <Text type="secondary" className="block-text">
                      使用 OpenAI API 格式；代理网关可填写 Base URL。系统按配置间隔自动检测已保存配置，保存模型、Base URL 或密钥后进入新的检测周期。
                    </Text>
                  </div>
                </div>
                <div className="settings-grid">
                  <Form.Item name="model" label="模型名称" rules={[{ required: true, message: "请填写模型名称" }]}>
                    <Input disabled={!canEdit} placeholder="此处填写模型名称" />
                  </Form.Item>
                  <Form.Item name="base_url" label="Base URL" rules={[{ required: true, message: "请填写AI调用地址" }]}>
                    <Input disabled={!canEdit} placeholder="此处填写AI调用地址" />
                  </Form.Item>
                  <Form.Item
                    name="api_key"
                    label={`API Key${aiConfig.data?.api_key_configured ? `（已配置 ${aiConfig.data.api_key_fingerprint || ""}）` : ""}`}
                    required
                    rules={[
                      {
                        validator: (_, value) => {
                          if (aiConfig.data?.api_key_configured || String(value || "").trim()) {
                            return Promise.resolve();
                          }
                          return Promise.reject(new Error("请填写AI调用API Key"));
                        },
                      },
                    ]}
                  >
                    <Input.Password disabled={!canEdit} placeholder="此处填写AI调用API Key" autoComplete="new-password" />
                  </Form.Item>
                  <Form.Item name="connection_check_interval_minutes" label="自动检测间隔（分钟）">
                    <InputNumber min={5} max={1440} precision={0} disabled={!canEdit} className="full" />
                  </Form.Item>
                </div>
                <div className="ai-config-actions">
                  <Button type="primary" htmlType="submit" loading={save.isPending} disabled={!canEdit}>
                    保存 AI 配置
                  </Button>
                </div>
              </Card>

              <Card title="Agent 功能范围" className="ai-side-card ai-agent-card">
                <Text type="secondary" className="block-text ai-card-description">
                  只控制学生端 AI 学习使用。老师侧题库助手、老师 AI 学情分析始终开启。
                </Text>
                <div className="ai-feature-scroll">
                  <div className="ai-feature-list">
                    <Flex justify="space-between" align="center" gap={12} className="ai-feature-row">
                      <div>
                        <Text strong>允许学生 AI 接入 RAG</Text>
                        <Text type="secondary" className="block-text">
                          允许学生侧 Agent 检索课本作为来源证据。
                        </Text>
                      </div>
                      <Form.Item name={["enabled_features", "rag_access_enabled"]} valuePropName="checked" noStyle>
                        <Switch disabled={!canEdit} />
                      </Form.Item>
                    </Flex>
                    <Flex justify="space-between" align="center" gap={12} className="ai-feature-row">
                      <div>
                        <Text strong>学生 AI 学习助手</Text>
                        <Text type="secondary" className="block-text">
                          学生端课程问答入口是否可用。
                        </Text>
                      </div>
                      <Form.Item name={["enabled_features", "student_ai_assistant"]} valuePropName="checked" noStyle>
                        <Switch disabled={!canEdit} />
                      </Form.Item>
                    </Flex>
                    <Flex justify="space-between" align="center" gap={12} className="ai-feature-row">
                      <div>
                        <Text strong>学生 AI 学情分析</Text>
                        <Text type="secondary" className="block-text">
                          学生端学习报告和个性化推荐是否可用。
                        </Text>
                      </div>
                      <Form.Item name={["enabled_features", "student_learning_analytics"]} valuePropName="checked" noStyle>
                        <Switch disabled={!canEdit} />
                      </Form.Item>
                    </Flex>
                  </div>
                </div>
              </Card>
            </div>

          </div>
        </Form>
      </QueryState>
    </Space>
  );
}

export default App;
