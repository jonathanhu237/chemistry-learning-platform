import { useEffect, useMemo, useRef, useState } from "react";
import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import type { ReactNode } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { lazy, Suspense } from "react";
import { motion, useReducedMotion } from "motion/react";
import {
  Alert,
  App as AntApp,
  Badge,
  Button,
  Card,
  Checkbox,
  ConfigProvider,
  Descriptions,
  Divider,
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
  Tooltip,
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
  CloseCircleOutlined,
  DatabaseOutlined,
  DeleteOutlined,
  EditOutlined,
  ExperimentOutlined,
  EyeOutlined,
  IdcardOutlined,
  KeyOutlined,
  LeftOutlined,
  LogoutOutlined,
  MessageOutlined,
  PauseCircleOutlined,
  PlayCircleOutlined,
  PlusOutlined,
  QuestionCircleOutlined,
  ReloadOutlined,
  SafetyCertificateOutlined,
  SettingOutlined,
  TeamOutlined,
  UnorderedListOutlined,
  VideoCameraOutlined,
} from "@ant-design/icons";
import Uppy from "@uppy/core";
import Tus from "@uppy/tus";
import { createSHA256 } from "hash-wasm";
import dayjs from "dayjs";
import {
  api,
  apiBase,
  formatBytes,
  getAuthToken,
  patchJson,
  postJson,
  postJsonStream,
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
  MediaDuplicatePrecheck,
  PointAwareSuggestionResponse,
  Question,
  QuestionBankSummary,
  QuestionDraft,
  QuestionWorkbenchCandidate,
  QuestionWorkbenchSession,
  StudentReport,
  WeakPointsResponse,
  LearningBehaviorSettings,
  LearningAssistantAskRequest,
  LearningAssistantResponse,
  LearningAssistantRuntime,
  LearningAssistantSource,
  PlatformSettingsResponse,
  RegistrationSettings,
  RosterImportResult,
  RosterStudent,
  User,
} from "./api";

const { Header, Sider, Content } = Layout;
const { Text, Title } = Typography;
const sysuLogoSrc = `${import.meta.env.BASE_URL}sysu-logo.svg`;
const adminSiderWidth = 248;
const adminSiderCollapsedWidth = 72;
const navBrandTransition = { type: "tween" as const, duration: 0.16, ease: [0.22, 1, 0.36, 1] as const };
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

const navItems: Array<{ key: string; icon: ReactNode; label: string; adminOnly?: boolean }> = [
  { key: "/overview", icon: <BookOutlined />, label: "资源总览" },
  { key: "/classes", icon: <TeamOutlined />, label: "班级与学生" },
  { key: "/experiments", icon: <ExperimentOutlined />, label: "实验管理" },
  { key: "/videos", icon: <VideoCameraOutlined />, label: "视频资源" },
  { key: "/question-banks", icon: <QuestionCircleOutlined />, label: "题库管理" },
  { key: "/analytics", icon: <BarChartOutlined />, label: "学情分析" },
  { key: "/feedback", icon: <MessageOutlined />, label: "反馈管理" },
  { key: "/learning-assistant", icon: <SafetyCertificateOutlined />, label: "学习助手", adminOnly: true },
  { key: "/settings", icon: <SettingOutlined />, label: "系统设置" },
  { key: "/ai-config", icon: <ApiOutlined />, label: "AI接入" },
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

function coverageTagLabel(tag?: string) {
  const labels: Record<string, string> = {
    experiment_purpose: "实验目的",
    true_false: "判断题",
    single_choice: "选择题",
    fill_blank: "填空题",
    evidence_based: "证据题",
    diagnostic: "诊断题",
  };
  return labels[String(tag || "")] || String(tag || "-").replace(/_/g, " ");
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
          <Route path="/*" element={<ProtectedShell />} />
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
  const prefersReducedMotion = useReducedMotion();
  const [navCollapsed, setNavCollapsed] = useState(() => {
    if (typeof window === "undefined") return false;
    return window.localStorage.getItem("admin-nav-collapsed") === "true";
  });
  const brandTransition = prefersReducedMotion ? { duration: 0 } : navBrandTransition;

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

  useEffect(() => {
    window.localStorage.setItem("admin-nav-collapsed", String(navCollapsed));
  }, [navCollapsed]);

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
  if (meQuery.data.role !== "admin" && location.pathname.startsWith("/learning-assistant")) {
    return <Navigate to="/overview" replace />;
  }

  const visibleNavItems = navItems
    .filter((item) => !item.adminOnly || meQuery.data.role === "admin")
    .map(({ adminOnly, label, ...item }) => ({ ...item, label, title: label }));

  const logout = () => {
    setAuthToken("");
    queryClient.clear();
    navigate("/login", { replace: true });
  };

  return (
    <Layout className={`admin-shell ${navCollapsed ? "admin-shell-collapsed" : ""}`}>
      <Sider
        width={adminSiderWidth}
        collapsedWidth={adminSiderCollapsedWidth}
        collapsed={navCollapsed}
        trigger={null}
        className="admin-sider"
        onBreakpoint={(broken) => setNavCollapsed(broken)}
        breakpoint="lg"
      >
        <Tooltip title={navCollapsed ? "展开导航" : "收起导航"} placement="right">
          <button
            type="button"
            className="brand brand-toggle"
            aria-label={navCollapsed ? "展开导航" : "收起导航"}
            aria-expanded={!navCollapsed}
            onClick={() => setNavCollapsed((value) => !value)}
          >
            <motion.span
              className="brand-mark"
              animate={{ scale: 1 }}
              transition={brandTransition}
            >
              <img src={sysuLogoSrc} alt="" />
            </motion.span>
            <motion.span
              className="brand-copy"
              animate={{
                opacity: navCollapsed ? 0 : 1,
                x: navCollapsed ? -10 : 0,
              }}
              initial={false}
              transition={brandTransition}
            >
              <Text strong>中大实验学习后台</Text>
            </motion.span>
            <motion.span
              className="brand-arrow"
              aria-hidden="true"
              animate={{
                opacity: navCollapsed ? 0 : 1,
                x: navCollapsed ? -8 : 0,
                rotate: navCollapsed ? 180 : 0,
              }}
              initial={false}
              transition={brandTransition}
            >
              <LeftOutlined />
            </motion.span>
          </button>
        </Tooltip>
        <Menu
          mode="inline"
          inlineCollapsed={navCollapsed}
          selectedKeys={[visibleNavItems.find((item) => location.pathname.startsWith(item.key))?.key || "/overview"]}
          items={visibleNavItems}
          onClick={({ key }) => navigate(String(key))}
        />
      </Sider>
      <Layout className="admin-main">
        <Header className="admin-header">
          <div className="admin-header-left">
            <Space>
              <Badge status="success" />
              <Text>
                {meQuery.data.display_name} · {meQuery.data.role}
              </Text>
            </Space>
          </div>
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
            <Route path="/learning-assistant" element={<LearningAssistantPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/ai-config" element={<AIConfigurationPage />} />
            <Route path="*" element={<Navigate to="/overview" replace />} />
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
        {description ? <Text type="secondary" className="page-title-description">{description}</Text> : null}
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
  { chapter_id: "CH22", chapter_number: 22, chapter_title: "第22章 氢和稀有气体", area_id: "integrated", area_name: "氢和稀有气体" },
];

const resourceAreaMeta: Record<string, { label: string; shortLabel: string; color: string; ink: string; selected: string }> = {
  s: { label: "s 区元素", shortLabel: "s", color: "#d9f0c7", ink: "#355b16", selected: "#91c96d" },
  p: { label: "p 区元素", shortLabel: "p", color: "#cdeee1", ink: "#005826", selected: "#2fa66d" },
  d: { label: "d 区元素", shortLabel: "d", color: "#d8e7ff", ink: "#254a7a", selected: "#83a9e8" },
  ds: { label: "ds 区元素", shortLabel: "ds", color: "#f3dfb8", ink: "#76531b", selected: "#e1b94f" },
  f: { label: "f 区元素", shortLabel: "f", color: "#eadcf8", ink: "#6b4a86", selected: "#ba8cde" },
  integrated: { label: "氢和稀有气体", shortLabel: "氢/稀气", color: "#e8f1f7", ink: "#356f9c", selected: "#7ba3c9" },
  general: { label: "通识资源", shortLabel: "通识", color: "#edf3ee", ink: "#375247", selected: "#9bbbaa" },
  other: { label: "其他资源", shortLabel: "其他", color: "#eef1ef", ink: "#53635b", selected: "#aebbb4" },
};

const periodicElementSymbols: Record<string, string> = {
  "1-1": "H",
  "1-18": "He",
  "2-1": "Li",
  "2-2": "Be",
  "2-13": "B",
  "2-14": "C",
  "2-15": "N",
  "2-16": "O",
  "2-17": "F",
  "2-18": "Ne",
  "3-1": "Na",
  "3-2": "Mg",
  "3-13": "Al",
  "3-14": "Si",
  "3-15": "P",
  "3-16": "S",
  "3-17": "Cl",
  "3-18": "Ar",
  "4-1": "K",
  "4-2": "Ca",
  "4-3": "Sc",
  "4-4": "Ti",
  "4-5": "V",
  "4-6": "Cr",
  "4-7": "Mn",
  "4-8": "Fe",
  "4-9": "Co",
  "4-10": "Ni",
  "4-11": "Cu",
  "4-12": "Zn",
  "4-13": "Ga",
  "4-14": "Ge",
  "4-15": "As",
  "4-16": "Se",
  "4-17": "Br",
  "4-18": "Kr",
  "5-1": "Rb",
  "5-2": "Sr",
  "5-3": "Y",
  "5-4": "Zr",
  "5-5": "Nb",
  "5-6": "Mo",
  "5-7": "Tc",
  "5-8": "Ru",
  "5-9": "Rh",
  "5-10": "Pd",
  "5-11": "Ag",
  "5-12": "Cd",
  "5-13": "In",
  "5-14": "Sn",
  "5-15": "Sb",
  "5-16": "Te",
  "5-17": "I",
  "5-18": "Xe",
  "6-1": "Cs",
  "6-2": "Ba",
  "6-3": "La",
  "6-4": "Hf",
  "6-5": "Ta",
  "6-6": "W",
  "6-7": "Re",
  "6-8": "Os",
  "6-9": "Ir",
  "6-10": "Pt",
  "6-11": "Au",
  "6-12": "Hg",
  "6-13": "Tl",
  "6-14": "Pb",
  "6-15": "Bi",
  "6-16": "Po",
  "6-17": "At",
  "6-18": "Rn",
  "7-1": "Fr",
  "7-2": "Ra",
  "7-3": "Ac",
  "7-4": "Rf",
  "7-5": "Db",
  "7-6": "Sg",
  "7-7": "Bh",
  "7-8": "Hs",
  "7-9": "Mt",
  "7-10": "Ds",
  "7-11": "Rg",
  "7-12": "Cn",
  "7-13": "Nh",
  "7-14": "Fl",
  "7-15": "Mc",
  "7-16": "Lv",
  "7-17": "Ts",
  "7-18": "Og",
};

const fBlockSymbols = [
  ["Ce", "Pr", "Nd", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu"],
  ["Th", "Pa", "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr"],
];

const hydrogenNobleGasPositions = new Set(["1-1", "1-18", "2-18", "3-18", "4-18", "5-18", "6-18", "7-18"]);

function periodicAreaForPosition(defaultArea: string, period: number, group: number) {
  return hydrogenNobleGasPositions.has(`${period}-${group}`) ? "integrated" : defaultArea;
}

const periodicAreaCells = [
  ...Array.from({ length: 7 }, (_, index) => ({
    area: periodicAreaForPosition("s", index + 1, 1),
    group: 1,
    period: index + 1,
    symbol: periodicElementSymbols[`${index + 1}-1`],
  })),
  ...Array.from({ length: 6 }, (_, index) => ({ area: "s", group: 2, period: index + 2, symbol: periodicElementSymbols[`${index + 2}-2`] })),
  ...Array.from({ length: 4 }, (_, periodIndex) =>
    Array.from({ length: 8 }, (_, groupIndex) => ({
      area: "d",
      group: groupIndex + 3,
      period: periodIndex + 4,
      symbol: periodicElementSymbols[`${periodIndex + 4}-${groupIndex + 3}`],
    })),
  ).flat(),
  ...Array.from({ length: 4 }, (_, periodIndex) =>
    Array.from({ length: 2 }, (_, groupIndex) => ({
      area: "ds",
      group: groupIndex + 11,
      period: periodIndex + 4,
      symbol: periodicElementSymbols[`${periodIndex + 4}-${groupIndex + 11}`],
    })),
  ).flat(),
  ...Array.from({ length: 6 }, (_, periodIndex) =>
    Array.from({ length: 6 }, (_, groupIndex) => ({
      area: periodicAreaForPosition("p", periodIndex + 2, groupIndex + 13),
      group: groupIndex + 13,
      period: periodIndex + 2,
      symbol: periodicElementSymbols[`${periodIndex + 2}-${groupIndex + 13}`],
    })),
  ).flat(),
  ...Array.from({ length: 2 }, (_, periodIndex) =>
    Array.from({ length: 14 }, (_, groupIndex) => ({
      area: "f",
      group: groupIndex + 5,
      period: periodIndex + 8,
      symbol: fBlockSymbols[periodIndex][groupIndex],
    })),
  ).flat(),
  { area: "integrated", group: 18, period: 1, symbol: periodicElementSymbols["1-18"] },
];

function areaMeta(areaId?: string | null) {
  return resourceAreaMeta[areaId || ""] || resourceAreaMeta.other;
}

function countValue(counts: Record<string, number> | undefined, key: string) {
  return Number(counts?.[key] || 0);
}

function resourcePercent(value: number, total: number) {
  if (!total) return 0;
  return Math.round((value / total) * 100);
}

function ResourceMiniStat({
  label,
  value,
  tone = "default",
  compact = false,
}: {
  label: string;
  value: string | number;
  tone?: "default" | "green" | "blue" | "amber";
  compact?: boolean;
}) {
  const className = ["resource-mini-stat", `resource-mini-stat-${tone}`, compact ? "compact" : ""].filter(Boolean).join(" ");
  return (
    <div className={className}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function shortResourceTitle(title?: string | null) {
  return (title || "").replace(/^第\s*(\d+)\s*章\s*/, "$1. ").trim();
}

function questionTypeSummary(counts?: Record<string, number>) {
  return [
    { label: "单选", value: countValue(counts, "single_choice") },
    { label: "判断", value: countValue(counts, "true_false") },
    { label: "填空", value: countValue(counts, "fill_blank") },
  ];
}

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

function ResourceDomainCard({
  title,
  eyebrow,
  value,
  icon,
  children,
  tone = "green",
}: {
  title: string;
  eyebrow: string;
  value: React.ReactNode;
  icon: React.ReactNode;
  children: React.ReactNode;
  tone?: "green" | "blue" | "amber" | "purple";
}) {
  return (
    <Card className={`resource-domain-card resource-domain-${tone}`}>
      <Flex align="flex-start" justify="space-between" gap={14}>
        <div className="resource-domain-copy">
          <Text type="secondary">{eyebrow}</Text>
          <strong>{title}</strong>
        </div>
        <span className="resource-domain-icon">{icon}</span>
      </Flex>
      <div className="resource-domain-value">{value}</div>
      {children}
    </Card>
  );
}

function ResourceOverviewNavigator({
  overview,
  selectedGroupId,
  onSelectGroup,
}: {
  overview?: LearningResourceOverview;
  selectedGroupId?: string;
  onSelectGroup: (groupId: string) => void;
}) {
  const groups = overview?.groups || [];
  const areas = overview?.areas || [];
  const selectedGroup = groups.find((group) => group.id === selectedGroupId) || groups[0];
  const selectedAreaId = selectedGroup?.area_id || areas[0]?.area_id;
  const selectedArea = areas.find((area) => area.area_id === selectedAreaId) || areas[0];
  const areaLookup = new Map(areas.map((area) => [area.area_id, area]));
  const generalArea = areaLookup.get("general");
  const specialAreas = ["other"]
    .map((areaId) => areaLookup.get(areaId))
    .filter((area): area is NonNullable<typeof area> => Boolean(area));
  const selectedAreaGroups = (selectedArea?.group_ids || [])
    .map((groupId) => groups.find((item) => item.id === groupId))
    .filter((group): group is NonNullable<typeof group> => Boolean(group));
  const showFamilyGrid = !(selectedArea?.area_id === "general" && selectedAreaGroups.length <= 1);

  const selectArea = (areaId: string) => {
    const area = areaLookup.get(areaId);
    const firstGroup = area?.group_ids.find((groupId) => groups.some((group) => group.id === groupId));
    if (firstGroup) onSelectGroup(firstGroup);
  };

  return (
    <Card className="resource-periodic-card">
      <Flex justify="space-between" align="flex-start" gap={16} className="resource-periodic-heading">
        <div>
          <Text type="secondary">资源目录</Text>
          <Title level={4}>按元素区选择章节</Title>
        </div>
        {selectedArea ? (
          <Tag color={areaMeta(selectedArea.area_id).ink}>
            {areaMeta(selectedArea.area_id).label} · {selectedArea.metrics.group_count}
          </Tag>
        ) : null}
      </Flex>

      <div className="resource-area-legend">
        {areas.map((area) => {
          const meta = areaMeta(area.area_id);
          const active = area.area_id === selectedArea?.area_id;
          return (
            <button
              key={area.area_id}
              type="button"
              className={active ? "selected" : ""}
              style={{ "--area-color": meta.color, "--area-ink": meta.ink } as React.CSSProperties}
              onClick={() => selectArea(area.area_id)}
            >
              <i />
              <span>{meta.label}</span>
              <b>{area.metrics.group_count}</b>
            </button>
          );
        })}
      </div>

      <div className="resource-periodic-grid" aria-label="元素周期表式资源区选择">
        {Array.from({ length: 18 }, (_, index) => (
          <div className="resource-periodic-group-number" key={index + 1} style={{ gridColumn: index + 2, gridRow: 1 }}>
            {index + 1}
          </div>
        ))}
        {["一", "二", "三", "四", "五", "六", "七", "镧系", "锕系"].map((period, index) => (
          <div className="resource-periodic-period-number" key={period} style={{ gridColumn: 1, gridRow: index + 2 }}>
            {period}
          </div>
        ))}
        {generalArea ? (
          <button
            type="button"
            aria-label={`选择通识资源，${generalArea.metrics.knowledge_point_count} 个知识点`}
            className={
              selectedArea?.area_id === "general"
                ? "resource-periodic-general-zone active"
                : "resource-periodic-general-zone"
            }
            style={
              {
                "--area-color": areaMeta("general").color,
                "--area-ink": areaMeta("general").ink,
              } as React.CSSProperties
            }
            onClick={() => selectArea("general")}
          />
        ) : null}
        {periodicAreaCells.map((cell, index) => {
          const meta = areaMeta(cell.area);
          const available = areaLookup.has(cell.area);
          const active = selectedArea?.area_id === cell.area;
          return (
            <button
              key={`${cell.area}-${cell.group}-${cell.period}-${index}`}
              type="button"
              disabled={!available}
              className={active ? "resource-element-cell selected-area" : "resource-element-cell"}
              style={{
                gridColumn: cell.group + 1,
                gridRow: cell.period + 1,
                background: active ? meta.selected : meta.color,
                "--cell-ink": meta.ink,
              } as React.CSSProperties}
              title={`${cell.symbol || meta.label} · ${meta.label}`}
              onClick={() => selectArea(cell.area)}
            >
              <span>{cell.symbol}</span>
            </button>
          );
        })}
      </div>

      {specialAreas.length ? (
        <div className="resource-periodic-specials">
          {specialAreas.map((area) => {
            const meta = areaMeta(area.area_id);
            const active = area.area_id === selectedArea?.area_id;
            return (
              <button
                key={area.area_id}
                type="button"
                className={active ? "active" : ""}
                style={{ "--area-color": meta.color, "--area-ink": meta.ink } as React.CSSProperties}
                onClick={() => selectArea(area.area_id)}
              >
                <span>{meta.label}</span>
                <strong>{area.area_id === "general" ? "通识/跨章节" : area.area_name}</strong>
                <small>
                  知识点 {area.metrics.knowledge_point_count} · 实验 {area.metrics.experiment_count} · 题目 {area.metrics.question_count}
                </small>
              </button>
            );
          })}
        </div>
      ) : null}

      {showFamilyGrid ? (
        <div className="resource-family-grid">
          {selectedAreaGroups.map((group) => {
            const active = group.id === selectedGroup?.id;
            return (
              <button
                key={group.id}
                type="button"
                className={active ? "resource-family-card active" : "resource-family-card"}
                onClick={() => onSelectGroup(group.id)}
              >
                <span>{group.area_name}</span>
                <strong>{shortResourceTitle(group.title)}</strong>
                <small>
                  知识点 {group.knowledge_point_count} · 实验 {group.experiment_count} · 题目 {group.question_count}
                </small>
              </button>
            );
          })}
        </div>
      ) : null}
    </Card>
  );
}

function ResourceChapterWorkbench({ group }: { group?: LearningResourceOverview["groups"][number] }) {
  if (!group) return null;
  const area = areaMeta(group.area_id);
  const isGeneralGroup = group.kind === "general" || group.area_id === "general";
  const publishedQuestions = countValue(group.question_status_counts, "published");
  const publishedVideo = Number(group.media_published_count || 0);
  const pendingVideo = Math.max(0, Number(group.media_count || 0) - publishedVideo);
  const questionTypes = questionTypeSummary(group.question_type_counts);

  return (
    <Card className="resource-workbench-card">
      <div className="resource-workbench-hero" style={{ "--area-color": area.color, "--area-ink": area.ink } as React.CSSProperties}>
        <div>
          <Space wrap className="resource-workbench-tags">
            <Tag color={area.ink}>{area.label}</Tag>
            {group.kind === "general" ? <Tag color="blue">通识</Tag> : <Tag>章节</Tag>}
          </Space>
          <Title level={3}>{group.title}</Title>
        </div>
        <div className="resource-workbench-metrics">
          <Statistic title="知识单元" value={group.knowledge_unit_count} />
          <Statistic title="知识点" value={group.knowledge_point_count} />
          <Statistic title="实验" value={group.experiment_count} />
          <Statistic title="视频" value={group.media_count} />
          <Statistic title="题目" value={group.question_count} />
        </div>
      </div>

      <div className="resource-workbench-grid">
        <section className="resource-workbench-panel resource-knowledge-panel">
          <Flex justify="space-between" align="center" gap={12}>
            <div>
              <Text type="secondary">知识框架</Text>
              <h3>知识单元与知识点</h3>
            </div>
          </Flex>
          <div className="resource-knowledge-status">
            <div>
              <span>知识单元</span>
              <strong>{group.knowledge_unit_count}</strong>
            </div>
            <div>
              <span>知识点</span>
              <strong>{group.knowledge_point_count}</strong>
            </div>
          </div>
          <div className="resource-unit-stack">
            {group.units.length ? (
              group.units.map((unit) => (
                <div key={unit.unit_id} className="resource-unit-card">
                  <Text strong>{unit.unit_title}</Text>
                  <div className="resource-kp-list">
                    {unit.knowledge_points.slice(0, 4).map((point) => (
                      <Tooltip key={point.knowledge_point_id} title={point.content} placement="right" overlayClassName="resource-kp-tooltip">
                        <div className="resource-kp-node">
                          <span>{point.content}</span>
                        </div>
                      </Tooltip>
                    ))}
                    {unit.knowledge_points.length > 4 ? (
                      <Text type="secondary" className="resource-more-text">
                        另有 {unit.knowledge_points.length - 4} 个知识点
                      </Text>
                    ) : null}
                  </div>
                </div>
              ))
            ) : (
              <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无知识单元" />
            )}
          </div>
        </section>

        <section className="resource-workbench-panel resource-experiment-panel">
          <Flex justify="space-between" align="center" gap={12}>
            <div>
              <Text type="secondary">{isGeneralGroup ? "通识定位" : "实验与视频"}</Text>
              <h3>{isGeneralGroup ? "通识资源说明" : "正式实验资源"}</h3>
            </div>
          </Flex>
          {isGeneralGroup ? (
            <div className="resource-general-context-card">
              <strong>通识资源不绑定正式实验</strong>
              <span>这里用于承载跨章节基础知识、模型方法和通用概念，作为理论教材的背景支撑，不要求引用实验视频。</span>
              <div className="resource-general-context-tags">
                <Tag color="green">跨章节</Tag>
              </div>
              <div className="resource-general-context-stats">
                <ResourceMiniStat label="知识单元" value={group.knowledge_unit_count} compact />
                <ResourceMiniStat label="知识点" value={group.knowledge_point_count} compact />
              </div>
            </div>
          ) : (
            <>
              <div className="resource-readiness-row">
                <div>
                  <span>已绑定视频</span>
                  <strong>{group.media_count}</strong>
                </div>
                <div>
                  <span>已发布视频</span>
                  <strong>{publishedVideo}</strong>
                </div>
                <div>
                  <span>待发布</span>
                  <strong>{pendingVideo}</strong>
                </div>
              </div>
              {!group.media_count ? <Alert type="warning" showIcon message="本章节实验还没有绑定视频资源" /> : null}
              <div className="resource-experiment-list">
                {group.experiments.length ? (
                  group.experiments.map((experiment) => (
                    <div key={experiment.id} className="resource-experiment-card">
                      <Flex justify="space-between" gap={12} align="flex-start">
                        <div>
                          <Text strong>
                            {experiment.code ? `${experiment.code} · ` : ""}
                            {experiment.title}
                          </Text>
                          <Space wrap className="resource-experiment-meta">
                            <Tag color={statusColor[experiment.status] || "default"}>{statusLabel[experiment.status] || experiment.status}</Tag>
                            <Tag color={experiment.media_count ? "blue" : "default"}>视频 {experiment.media_count}</Tag>
                            <Tag color={experiment.media_published_count ? "green" : "default"}>已发布视频 {experiment.media_published_count || 0}</Tag>
                            <Tag color={experiment.question_count ? "green" : "default"}>题目 {experiment.question_count}</Tag>
                          </Space>
                        </div>
                      </Flex>
                    </div>
                  ))
                ) : (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无绑定实验" />
                )}
              </div>
            </>
          )}
        </section>

        <section className="resource-workbench-panel resource-question-panel">
          <Flex justify="space-between" align="center" gap={12}>
            <div>
              <Text type="secondary">题库覆盖</Text>
              <h3>总数与题型</h3>
            </div>
          </Flex>
          <div className="resource-question-status">
            <div>
              <span>题目总数</span>
              <strong>{group.question_count}</strong>
            </div>
            <div>
              <span>已发布</span>
              <strong>{publishedQuestions}</strong>
            </div>
          </div>
          <div className="resource-question-type-list">
            {questionTypes.map((item) => (
              <div key={item.label}>
                <span>{item.label}</span>
                <Progress percent={resourcePercent(item.value, group.question_count)} size="small" showInfo={false} />
                <strong>{item.value}</strong>
              </div>
            ))}
          </div>
        </section>
      </div>
    </Card>
  );
}

type ExperimentFrameworkOverviewData = NonNullable<LearningResourceOverview["experiment_framework"]>;
type ExperimentFrameworkNodeData = ExperimentFrameworkOverviewData["nodes"][number];
type ExperimentFrameworkLinkData = ExperimentFrameworkOverviewData["formal_links"][number];

function experimentFrameworkNodeLabel(node?: ExperimentFrameworkNodeData | null) {
  if (!node) return "-";
  if (node.node_type === "book") return "教材";
  if (node.node_type === "chapter") return "章节";
  if (node.node_type === "protocol") return "实验条目";
  return "小节";
}

function collectExperimentFrameworkNodeIds(framework: ExperimentFrameworkOverviewData, rootId: string) {
  const children = new Map<string, string[]>();
  framework.nodes.forEach((node) => {
    if (!node.parent_id) return;
    const list = children.get(node.parent_id) || [];
    list.push(node.id);
    children.set(node.parent_id, list);
  });
  const ids = new Set<string>();
  const stack = [rootId];
  while (stack.length) {
    const nodeId = stack.pop();
    if (!nodeId || ids.has(nodeId)) continue;
    ids.add(nodeId);
    (children.get(nodeId) || []).forEach((childId) => stack.push(childId));
  }
  return ids;
}

function uniqueExperimentFrameworkLinks(links: ExperimentFrameworkLinkData[]) {
  const byExperiment = new Map<string, ExperimentFrameworkLinkData & { relation_count: number; has_canonical_evidence: boolean }>();
  links.forEach((link) => {
    const existing = byExperiment.get(link.experiment_id);
    if (!existing) {
      byExperiment.set(link.experiment_id, {
        ...link,
        relation_count: 1,
        has_canonical_evidence: link.relation_type === "canonical_evidence",
      });
      return;
    }
    existing.relation_count += 1;
    existing.has_canonical_evidence = existing.has_canonical_evidence || link.relation_type === "canonical_evidence";
  });
  return Array.from(byExperiment.values()).sort((a, b) => {
    const orderA = Number(a.sort_order || 0);
    const orderB = Number(b.sort_order || 0);
    if (orderA !== orderB) return orderA - orderB;
    return String(a.experiment_code || "").localeCompare(String(b.experiment_code || ""), "zh-Hans-CN");
  });
}

function preferredExperimentFrameworkRoot(roots: ExperimentFrameworkNodeData[]) {
  return [...roots].sort((a, b) => {
    const formalDelta = Number(b.formal_experiment_count || 0) - Number(a.formal_experiment_count || 0);
    if (formalDelta) return formalDelta;
    const evidenceDelta = Number(b.evidence_count || 0) - Number(a.evidence_count || 0);
    if (evidenceDelta) return evidenceDelta;
    return a.display_order - b.display_order;
  })[0];
}

function isStructuralExperimentFrameworkRoot(node: ExperimentFrameworkNodeData) {
  const compactTitle = node.title.replace(/\s+/g, "");
  return (
    /^第[一二三四五六七八九十]+部分/.test(compactTitle) &&
    Number(node.evidence_count || 0) <= 1 &&
    Number(node.child_count || 0) === 0 &&
    Number(node.formal_experiment_count || 0) === 0
  );
}

function experimentFrameworkDisplayRoots(roots: ExperimentFrameworkNodeData[]) {
  const visible = roots.filter((node) => !isStructuralExperimentFrameworkRoot(node));
  return visible.length ? visible : roots;
}

function experimentFrameworkSourceContext(roots: ExperimentFrameworkNodeData[]) {
  return roots.find((node) => isStructuralExperimentFrameworkRoot(node));
}

function experimentFrameworkRootActive(
  framework: ExperimentFrameworkOverviewData,
  root: ExperimentFrameworkNodeData,
  selectedNode?: ExperimentFrameworkNodeData,
) {
  if (!selectedNode) return false;
  if (root.id === selectedNode.id) return true;
  return collectExperimentFrameworkNodeIds(framework, root.id).has(selectedNode.id);
}

function ExperimentKnowledgeFrameworkPanel({ framework }: { framework?: LearningResourceOverview["experiment_framework"] | null }) {
  const rawRoots = framework?.roots || [];
  const roots = useMemo(() => experimentFrameworkDisplayRoots(rawRoots), [rawRoots]);
  const [selectedNodeId, setSelectedNodeId] = useState<string>();

  useEffect(() => {
    if (!framework?.available || !roots.length) return;
    if (!selectedNodeId || !framework.nodes.some((node) => node.id === selectedNodeId)) {
      setSelectedNodeId(preferredExperimentFrameworkRoot(roots).id);
    }
  }, [framework, roots, selectedNodeId]);

  if (!framework) return null;
  if (!framework.available) {
    return (
      <section className="experiment-framework-card">
        <Alert
          type="info"
          showIcon
          message="实验教材知识框架尚未导入"
          description="导入无机化学实验教材的标准分块后，这里会展示实验基本知识、基本操作、元素性质实验和通识内容。"
        />
      </section>
    );
  }

  const selectedNode = framework.nodes.find((node) => node.id === selectedNodeId) || preferredExperimentFrameworkRoot(roots);
  const selectedNodeIds = selectedNode ? collectExperimentFrameworkNodeIds(framework, selectedNode.id) : new Set<string>();
  const childNodes = framework.nodes
    .filter((node) => node.parent_id === selectedNode?.id)
    .sort((a, b) => a.display_order - b.display_order);
  const relatedLinks = uniqueExperimentFrameworkLinks(
    framework.formal_links.filter((link) => selectedNodeIds.has(link.node_id)),
  );
  const evidenceLinkCount = framework.formal_links.filter(
    (link) => selectedNodeIds.has(link.node_id) && link.relation_type === "canonical_evidence",
  ).length;
  const hasOperationalCoverage =
    Number(selectedNode?.formal_experiment_count || 0) > 0 ||
    Number(selectedNode?.video_count || 0) > 0 ||
    Number(selectedNode?.question_count || 0) > 0;

  return (
    <section className="experiment-framework-card">
      <div className="experiment-framework-layout">
        <section className="experiment-framework-tree">
          <Flex justify="space-between" align="center" gap={12}>
            <div>
              <Text type="secondary">教材目录</Text>
              <h3>{framework.source.book_title || "无机化学实验（第四版）"}</h3>
            </div>
          </Flex>
          <div className="experiment-framework-root-list">
            {roots.map((node) => (
              <button
                key={node.id}
                type="button"
                className={experimentFrameworkRootActive(framework, node, selectedNode) ? "active" : ""}
                onClick={() => setSelectedNodeId(node.id)}
              >
                <span>{experimentFrameworkNodeLabel(node)}</span>
                <strong>{node.title}</strong>
                <small>
                  语料分块 {node.evidence_count}
                  {node.formal_experiment_count ? ` · 实验 ${node.formal_experiment_count}` : ""}
                  {node.question_count ? ` · 题目 ${node.question_count}` : ""}
                </small>
              </button>
            ))}
          </div>
        </section>

        <section className="experiment-framework-detail">
          <div className="experiment-framework-detail-hero">
            <div>
              <Space wrap>
                <Tag color="green">{experimentFrameworkNodeLabel(selectedNode)}</Tag>
                {selectedNode?.page_start ? <Tag>页码 {selectedNode.page_start}-{selectedNode.page_end || selectedNode.page_start}</Tag> : null}
              </Space>
              <Title level={4}>{selectedNode?.title}</Title>
              <Text type="secondary">{(selectedNode?.full_path || []).join(" / ")}</Text>
            </div>
            <div className={hasOperationalCoverage ? "experiment-framework-detail-stats" : "experiment-framework-support-summary"}>
              <Statistic title="语料分块" value={selectedNode?.evidence_count || 0} />
              <Statistic title="小节" value={childNodes.length} />
              {hasOperationalCoverage ? (
                <>
                  <Statistic title="正式实验" value={selectedNode?.formal_experiment_count || 0} />
                  <Statistic title="题目" value={selectedNode?.question_count || 0} />
                </>
              ) : null}
            </div>
          </div>

          <div className="experiment-framework-detail-grid">
            <div className="experiment-framework-child-panel">
              <Flex justify="space-between" align="center" gap={12}>
                <h3>小节</h3>
                <Tag>{childNodes.length} 个小节</Tag>
              </Flex>
              <div className="experiment-framework-child-list">
                {childNodes.length ? (
                  childNodes.map((node) => (
                    <div key={node.id} className="experiment-framework-child-card">
                      <span>{experimentFrameworkNodeLabel(node)}</span>
                      <strong>{node.title}</strong>
                      <small>
                        语料分块 {node.evidence_count}
                        {node.formal_experiment_count ? ` · 实验 ${node.formal_experiment_count}` : ""}
                        {node.question_count ? ` · 题目 ${node.question_count}` : ""}
                      </small>
                    </div>
                  ))
                ) : (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无小节" />
                )}
              </div>
            </div>

            <div className="experiment-framework-formal-panel">
              <Flex justify="space-between" align="center" gap={12}>
                <h3>关联正式实验</h3>
                <Tag color={evidenceLinkCount ? "green" : "default"}>语料映射 {evidenceLinkCount}</Tag>
              </Flex>
              <div className="experiment-framework-formal-list">
                {relatedLinks.length ? (
                  relatedLinks.map((link) => (
                    <div key={link.experiment_id} className="experiment-framework-formal-card">
                      <Text strong>
                        {link.experiment_code ? `${link.experiment_code} · ` : ""}
                        {link.experiment_title}
                      </Text>
                      <Space wrap>
                        <Tag color={statusColor[link.experiment_status] || "default"}>
                          {statusLabel[link.experiment_status] || link.experiment_status}
                        </Tag>
                        <Tag color={link.has_canonical_evidence ? "green" : "blue"}>
                          {link.has_canonical_evidence ? "教材语料" : "目录映射"}
                        </Tag>
                        {link.relation_count > 1 ? <Tag>关联 {link.relation_count}</Tag> : null}
                      </Space>
                    </div>
                  ))
                ) : (
                  <Alert
                    className="experiment-framework-support-alert"
                    type="info"
                    showIcon
                    message="本章暂无正式实验引用"
                    description="本章属于实验通识、基本操作无需关联实验。"
                  />
                )}
              </div>
            </div>
          </div>
        </section>
      </div>
    </section>
  );
}

type ResourceSourceKey = "theory" | "experiment";

function ResourceSourceWorkspace({
  overview,
  selectedGroup,
  onSelectGroup,
}: {
  overview?: LearningResourceOverview;
  selectedGroup?: LearningResourceOverview["groups"][number];
  onSelectGroup: (groupId: string) => void;
}) {
  const [activeSource, setActiveSource] = useState<ResourceSourceKey>("theory");
  const knowledgeDomain = overview?.domains?.knowledge;
  const experimentFramework = overview?.experiment_framework;

  return (
    <section className="resource-source-workspace">
      <div className="resource-source-workspace-header">
        <Segmented
          value={activeSource}
          onChange={(value) => setActiveSource(value as ResourceSourceKey)}
          options={[
            {
              value: "theory",
              label: (
                <span className="resource-source-switch-label">
                  <span>理论教材</span>
                  <b>{knowledgeDomain?.source_chunk_count || 0} 语料分块</b>
                </span>
              ),
            },
            {
              value: "experiment",
              label: (
                <span className="resource-source-switch-label">
                  <span>实验教材</span>
                  <b>{experimentFramework?.metrics.linked_chunk_count || 0} 语料分块</b>
                </span>
              ),
            },
          ]}
        />
      </div>

      {activeSource === "theory" ? (
        <div className="resource-source-panel resource-source-theory-panel">
          <ResourceOverviewNavigator overview={overview} selectedGroupId={selectedGroup?.id} onSelectGroup={onSelectGroup} />
          <ResourceChapterWorkbench group={selectedGroup} />
        </div>
      ) : (
        <div className="resource-source-panel resource-source-experiment-panel">
          <ExperimentKnowledgeFrameworkPanel framework={overview?.experiment_framework} />
        </div>
      )}
    </section>
  );
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
  const domains = overview.data?.domains;
  const knowledge = domains?.knowledge;
  const experimentVideo = domains?.experiment_video;
  const questionBank = domains?.question_bank;
  const classesStudents = domains?.classes_students;
  const publishedQuestions = Number(questionBank?.published_question_count || 0);
  const totalQuestions = Number(questionBank?.question_count || 0);
  const publishedVideos = Number(experimentVideo?.published_video_count || 0);
  const totalVideoAssets = Number(experimentVideo?.video_asset_count || 0);
  const rosterCount = Number(classesStudents?.roster_count || 0);
  const activeStudents = Number(classesStudents?.active_student_count || 0);

  return (
    <Space direction="vertical" size={18} className="full">
      <PageTitle
        title="资源总览"
        description="统一查看知识框架、智能检索事实资源、实验视频、题库与班级学生的建设状态。"
      />

      <QueryState loading={overview.isLoading} error={overview.error} empty={!groups.length}>
        <div className="resource-dashboard-grid">
          <ResourceDomainCard
            title="知识框架 / 检索语料"
            eyebrow="教材事实资源"
            value={`${knowledge?.knowledge_unit_count || 0} / ${knowledge?.knowledge_point_count || 0}`}
            icon={<DatabaseOutlined />}
          >
            <div className="resource-domain-subgrid">
              <span>知识单元</span>
              <strong>{knowledge?.knowledge_unit_count || 0}</strong>
              <span>知识点</span>
              <strong>{knowledge?.knowledge_point_count || 0}</strong>
              <span>标准语料分块</span>
              <strong>{knowledge?.source_chunk_count || 0}</strong>
              <span>向量索引</span>
              <strong>{knowledge?.embedding_count || 0}</strong>
            </div>
          </ResourceDomainCard>

          <ResourceDomainCard
            title="实验与视频"
            eyebrow="实验管理概况"
            value={`${experimentVideo?.experiment_count || 0} 个实验`}
            icon={<ExperimentOutlined />}
            tone="blue"
          >
            <Progress percent={resourcePercent(publishedVideos, Math.max(totalVideoAssets, 1))} showInfo={false} />
            <div className="resource-domain-subgrid">
              <span>视频库</span>
              <strong>{totalVideoAssets}</strong>
              <span>已发布引用</span>
              <strong>{publishedVideos}</strong>
            </div>
            {!totalVideoAssets ? <Text type="secondary">视频库暂未上传资源</Text> : null}
          </ResourceDomainCard>

          <ResourceDomainCard
            title="题库"
            eyebrow="当前题目状态"
            value={`${totalQuestions} 道`}
            icon={<QuestionCircleOutlined />}
            tone="amber"
          >
            <Progress percent={resourcePercent(publishedQuestions, totalQuestions)} showInfo={false} />
            <div className="resource-domain-subgrid">
              <span>题目总数</span>
              <strong>{totalQuestions}</strong>
              <span>已发布</span>
              <strong>{publishedQuestions}</strong>
              <span>单选/判断/填空</span>
              <strong>
                {countValue(questionBank?.type_counts, "single_choice")} / {countValue(questionBank?.type_counts, "true_false")} / {countValue(questionBank?.type_counts, "fill_blank")}
              </strong>
            </div>
          </ResourceDomainCard>

          <ResourceDomainCard
            title="班级与学生"
            eyebrow="教学运营"
            value={`${classesStudents?.class_count || 0} 个班级`}
            icon={<TeamOutlined />}
            tone="purple"
          >
            <Progress percent={resourcePercent(activeStudents, rosterCount)} showInfo={false} />
            <div className="resource-domain-subgrid">
              <span>花名册学生</span>
              <strong>{rosterCount}</strong>
              <span>已激活账号</span>
              <strong>{activeStudents}</strong>
            </div>
            {!classesStudents?.class_count ? <Text type="secondary">尚未建立班级与花名册</Text> : null}
          </ResourceDomainCard>
        </div>

        <ResourceSourceWorkspace overview={overview.data} selectedGroup={selectedGroup} onSelectGroup={setSelectedGroupId} />
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

type VideoUploadStage =
  | "idle"
  | "pending"
  | "hashing"
  | "ready"
  | "duplicate"
  | "uploading"
  | "paused"
  | "finalizing"
  | "processing"
  | "complete"
  | "error";

type VideoUploadState = {
  stage: VideoUploadStage;
  hashProgress: number;
  progress: number;
  uploadedBytes: number;
  totalBytes: number;
  checksum?: string;
  duplicateAsset?: MediaAsset | null;
  error?: string;
  note?: string;
};

type VideoUploadQueueItem = {
  id: string;
  file: File;
  title: string;
  status: VideoUploadStage;
  hashProgress: number;
  progress: number;
  uploadedBytes: number;
  totalBytes: number;
  checksum?: string;
  duplicateAsset?: MediaAsset | null;
  error?: string;
  note?: string;
};

const emptyUploadState: VideoUploadState = {
  stage: "idle",
  hashProgress: 0,
  progress: 0,
  uploadedBytes: 0,
  totalBytes: 0,
};

const mediaStatusLabels: Record<string, string> = {
  pending: "待处理",
  processing: "处理中",
  ready: "就绪",
  failed: "处理失败",
  replaced: "已替换",
};

const mediaStatusColors: Record<string, string> = {
  pending: "#b8892f",
  processing: "#356f9c",
  ready: "#005826",
  failed: "#b42318",
  replaced: "default",
};

const processingPhaseLabels: Record<string, string> = {
  queued: "已排队",
  starting: "启动中",
  validating: "校验文件",
  probing: "读取元数据",
  thumbnailing: "生成缩略图",
  transcoding: "生成学生播放源",
  fingerprinting: "生成相似度签名",
  comparing: "比对相似视频",
  ready: "已就绪",
  failed: "处理失败",
};

const duplicateDecisionLabels: Record<string, string> = {
  pending: "待确认",
  kept: "已保留",
  reused: "已复用",
  ignored: "已忽略",
};

function mediaStatusTag(status?: string) {
  const value = status || "pending";
  return <Tag color={mediaStatusColors[value] || "default"}>{mediaStatusLabels[value] || value}</Tag>;
}

function processingPhaseText(asset?: MediaAsset | null): string {
  const phase = asset?.processing_phase || asset?.processing_job?.phase || asset?.upload_status || "";
  return processingPhaseLabels[phase] || phase || "-";
}

function processingProgressValue(asset?: MediaAsset | null): number {
  return Math.max(0, Math.min(100, Number(asset?.processing_progress ?? asset?.processing_job?.progress ?? 0)));
}

function formatDurationSeconds(value?: number | null): string {
  if (!value) return "-";
  const total = Math.round(Number(value));
  const minutes = Math.floor(total / 60);
  const seconds = String(total % 60).padStart(2, "0");
  if (minutes < 60) return String(minutes) + ":" + seconds;
  const hours = Math.floor(minutes / 60);
  return String(hours) + ":" + String(minutes % 60).padStart(2, "0") + ":" + seconds;
}

function formatResolution(asset?: { width?: number | null; height?: number | null } | null): string {
  return asset?.width && asset?.height ? String(asset.width) + " x " + String(asset.height) : "-";
}

function selectedRendition(asset: MediaAsset) {
  return asset.renditions?.find((rendition) => rendition.kind === "learning") || asset.renditions?.[0];
}

function renditionSavings(asset: MediaAsset) {
  const rendition = selectedRendition(asset);
  const sourceSize = Number(asset.file_size_bytes || 0);
  const renditionSize = Number(rendition?.file_size_bytes || 0);
  const savedBytes = sourceSize && renditionSize ? Math.max(0, sourceSize - renditionSize) : 0;
  const savedPercent = sourceSize && savedBytes ? Math.round((savedBytes / sourceSize) * 100) : 0;
  return { rendition, savedBytes, savedPercent };
}

function pendingDuplicateCandidates(asset?: MediaAsset | null) {
  return (asset?.duplicate_candidates || []).filter((candidate) => candidate.status === "pending");
}

function hasPendingDuplicate(asset?: MediaAsset | null): boolean {
  return pendingDuplicateCandidates(asset).length > 0;
}

function duplicateScoreText(score?: number | null): string {
  if (score == null) return "-";
  const value = Number(score);
  if (!Number.isFinite(value)) return "-";
  return value > 1 ? value.toFixed(1) + "%" : Math.round(value * 100) + "%";
}

function uploadStepCurrent(stage: VideoUploadStage): number {
  if (["uploading", "paused", "finalizing"].includes(stage)) return 1;
  if (["processing", "complete"].includes(stage)) return 2;
  return 0;
}

function uploadStageText(stage: VideoUploadStage): string {
  if (stage === "pending") return "已加入队列，点击开始后会按顺序上传";
  if (stage === "hashing") return "正在做 SHA-256 完全重复校验";
  if (stage === "duplicate") return "发现完全相同的已上传文件";
  if (stage === "ready") return "文件已就绪，可以开始上传";
  if (stage === "uploading") return "正在上传文件";
  if (stage === "paused") return "上传已暂停，可继续断点续传";
  if (stage === "finalizing") return "正在完成入库并交给后台";
  if (stage === "processing") return "上传完成，后台正在处理";
  if (stage === "complete") return "上传已完成，已加入后台处理队列";
  if (stage === "error") return "上传遇到问题";
  return "选择视频后会先校验，再上传";
}

function videoTitleFromFile(file: File): string {
  return file.name.replace(/\.[^.]+$/, "").trim() || file.name;
}

function uploadQueueItemText(item: VideoUploadQueueItem): string {
  if (item.status === "pending") return "等待上传";
  if (item.status === "hashing") return "校验重复 " + item.hashProgress + "%";
  if (item.status === "ready") return "准备上传";
  if (item.status === "duplicate") return "完全重复，已复用";
  if (item.status === "uploading") return "上传中 " + item.progress + "%";
  if (item.status === "paused") return "已暂停";
  if (item.status === "finalizing") return "正在入库";
  if (item.status === "processing") return "已交给后台处理";
  if (item.status === "complete") return "已完成";
  if (item.status === "error") return item.error || "上传失败";
  return uploadStageText(item.status);
}

async function computeVideoFileSha256(file: File, onProgress: (progress: number) => void): Promise<string> {
  const hasher = await createSHA256();
  hasher.init();
  const chunkSize = 8 * 1024 * 1024;
  let offset = 0;
  while (offset < file.size) {
    const nextOffset = Math.min(offset + chunkSize, file.size);
    const chunk = new Uint8Array(await file.slice(offset, nextOffset).arrayBuffer());
    hasher.update(chunk);
    offset = nextOffset;
    onProgress(file.size ? Math.round((offset / file.size) * 100) : 100);
    await new Promise((resolve) => window.setTimeout(resolve, 0));
  }
  return hasher.digest("hex");
}

function extractTusUploadId(uploadUrl?: string | null): string {
  if (!uploadUrl) return "";
  try {
    const url = new URL(uploadUrl, window.location.href);
    const parts = url.pathname.split("/").filter(Boolean);
    return decodeURIComponent(parts[parts.length - 1] || "");
  } catch {
    const parts = uploadUrl.split("/").filter(Boolean);
    return decodeURIComponent(parts[parts.length - 1] || "");
  }
}

function AuthenticatedImage({ src, alt, className }: { src?: string | null; alt: string; className?: string }) {
  const [objectUrl, setObjectUrl] = useState<string>();
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    let cancelled = false;
    let nextUrl: string | undefined;
    setObjectUrl(undefined);
    setFailed(false);
    if (!src) return undefined;
    const headers = new Headers();
    const token = getAuthToken();
    if (token) headers.set("Authorization", "Bearer " + token);
    void fetch(src, { headers })
      .then((response) => {
        if (!response.ok) throw new Error("image_load_failed");
        return response.blob();
      })
      .then((blob) => {
        if (cancelled) return;
        nextUrl = URL.createObjectURL(blob);
        setObjectUrl(nextUrl);
      })
      .catch(() => {
        if (!cancelled) {
          setObjectUrl(undefined);
          setFailed(true);
        }
      });
    return () => {
      cancelled = true;
      if (nextUrl) URL.revokeObjectURL(nextUrl);
    };
  }, [src]);
  return objectUrl && !failed ? (
    <img
      src={objectUrl}
      alt={alt}
      className={className}
      onError={() => {
        setObjectUrl(undefined);
        setFailed(true);
      }}
    />
  ) : null;
}

function MediaThumbnail({ asset, compact = false }: { asset: MediaAsset; compact?: boolean }) {
  const src = asset.thumbnail_relative_path ? apiBase + "/api/admin/media/assets/" + asset.id + "/thumbnail" : null;
  const className = compact ? "video-thumb-image compact" : "video-thumb-image";
  return (
    <div className={compact ? "video-thumb-frame compact" : "video-thumb-frame"}>
      <AuthenticatedImage src={src} alt={asset.title} className={className} />
      <div className="video-thumb-fallback">
        <VideoCameraOutlined />
        <span>{asset.thumbnail_relative_path ? "缩略图" : asset.upload_status === "ready" ? mediaAssetType(asset) : processingPhaseText(asset)}</span>
      </div>
    </div>
  );
}

function VideoResourcesPage() {
  const { message } = AntApp.useApp();
  const queryClient = useQueryClient();
  const assets = useQuery({
    queryKey: ["media-assets"],
    queryFn: () => api<ApiList<MediaAsset>>("/api/admin/media/assets?limit=200"),
  });
  const tusEndpoint = String(import.meta.env.VITE_TUS_ENDPOINT || "").trim().replace(/\/+$/, "");
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [keyword, setKeyword] = useState("");
  const [statusFilter, setStatusFilter] = useState<string>();
  const [sortKey, setSortKey] = useState<"updated_desc" | "name_asc" | "size_desc">("updated_desc");
  const [uploadOpen, setUploadOpen] = useState(false);
  const [uploadTitle, setUploadTitle] = useState("");
  const [uploadItems, setUploadItems] = useState<VideoUploadQueueItem[]>([]);
  const [currentUploadId, setCurrentUploadId] = useState<string>();
  const [batchRunning, setBatchRunning] = useState(false);
  const [uploadState, setUploadState] = useState<VideoUploadState>(emptyUploadState);
  const [previewAsset, setPreviewAsset] = useState<MediaAsset | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string>();
  const [previewPosterUrl, setPreviewPosterUrl] = useState<string>();
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState("");
  const uppyRef = useRef<Uppy | null>(null);
  const uppyFileIdRef = useRef("");
  const xhrRef = useRef<XMLHttpRequest | null>(null);
  const hashRunRef = useRef(0);
  const uploadItemsRef = useRef<VideoUploadQueueItem[]>([]);
  const currentUploadIdRef = useRef<string | undefined>(undefined);
  const cancelBatchRef = useRef(false);

  const assetItems = useMemo(() => assets.data?.items || [], [assets.data?.items]);
  const readyAssets = useMemo(() => assetItems.filter((asset) => asset.upload_status === "ready"), [assetItems]);
  const workingAssets = useMemo(
    () => assetItems.filter((asset) => ["pending", "processing"].includes(asset.upload_status)),
    [assetItems],
  );
  const failedAssets = useMemo(() => assetItems.filter((asset) => asset.upload_status === "failed"), [assetItems]);
  const pendingDuplicateAssets = useMemo(() => assetItems.filter((asset) => hasPendingDuplicate(asset)), [assetItems]);
  const sourceBytes = useMemo(
    () => assetItems.reduce((sum, asset) => sum + Number(asset.file_size_bytes || 0), 0),
    [assetItems],
  );
  const renditionBytes = useMemo(
    () => assetItems.reduce((sum, asset) => sum + (asset.renditions || []).reduce((subtotal, rendition) => subtotal + Number(rendition.file_size_bytes || 0), 0), 0),
    [assetItems],
  );
  const savedBytes = Math.max(0, sourceBytes - renditionBytes);
  const savedPercent = sourceBytes > 0 && renditionBytes > 0 ? Math.round((savedBytes / sourceBytes) * 100) : 0;
  const currentUploadItem = useMemo(
    () => uploadItems.find((item) => item.id === currentUploadId) || null,
    [currentUploadId, uploadItems],
  );
  const uploadQueueDoneCount = useMemo(
    () => uploadItems.filter((item) => ["duplicate", "processing", "complete"].includes(item.status)).length,
    [uploadItems],
  );
  const uploadQueueTotalBytes = useMemo(() => uploadItems.reduce((sum, item) => sum + item.totalBytes, 0), [uploadItems]);
  const uploadQueueUploadedBytes = useMemo(() => uploadItems.reduce((sum, item) => sum + item.uploadedBytes, 0), [uploadItems]);
  const uploadQueueProgress = uploadQueueTotalBytes ? Math.round((uploadQueueUploadedBytes / uploadQueueTotalBytes) * 100) : 0;
  const hasActiveWork = workingAssets.length > 0 || batchRunning || uploadItems.some((item) => ["uploading", "paused", "finalizing", "hashing"].includes(item.status));
  const filteredAssets = useMemo(() => {
    const normalized = keyword.trim().toLowerCase();
    const list = assetItems.filter((asset) => {
      if (statusFilter === "duplicate_pending" && !hasPendingDuplicate(asset)) return false;
      if (statusFilter && statusFilter !== "duplicate_pending" && asset.upload_status !== statusFilter) return false;
      if (!normalized) return true;
      return (asset.title + " " + asset.original_file_name).toLowerCase().includes(normalized);
    });
    return [...list].sort((left, right) => {
      if (sortKey === "name_asc") return left.title.localeCompare(right.title, "zh-Hans-CN");
      if (sortKey === "size_desc") return Number(right.file_size_bytes || 0) - Number(left.file_size_bytes || 0);
      const rightTime = new Date(right.updated_at || right.created_at || "").getTime() || 0;
      const leftTime = new Date(left.updated_at || left.created_at || "").getTime() || 0;
      return rightTime - leftTime;
    });
  }, [assetItems, keyword, sortKey, statusFilter]);

  useEffect(() => {
    uploadItemsRef.current = uploadItems;
  }, [uploadItems]);

  useEffect(() => {
    if (!hasActiveWork) return undefined;
    const timer = window.setInterval(() => {
      void queryClient.invalidateQueries({ queryKey: ["media-assets"] });
    }, 3000);
    return () => window.clearInterval(timer);
  }, [hasActiveWork, queryClient]);

  useEffect(() => {
    let posterObjectUrl: string | undefined;
    let cancelled = false;
    setPreviewUrl(undefined);
    setPreviewPosterUrl(undefined);
    setPreviewError("");
    setPreviewLoading(false);
    if (!previewAsset || !isPreviewableVideo(previewAsset)) return undefined;
    setPreviewLoading(true);
    const headers = new Headers();
    const token = getAuthToken();
    if (token) headers.set("Authorization", "Bearer " + token);
    if (!token) {
      setPreviewError("登录状态已失效，请重新登录后预览视频");
      setPreviewLoading(false);
      return undefined;
    }
    setPreviewUrl(apiBase + "/api/admin/media/assets/" + previewAsset.id + "/stream?access_token=" + encodeURIComponent(token));
    setPreviewLoading(false);
    if (previewAsset.thumbnail_relative_path) {
      void fetch(apiBase + "/api/admin/media/assets/" + previewAsset.id + "/thumbnail", { headers })
        .then((response) => {
          if (!response.ok) throw new Error("poster_load_failed");
          return response.blob();
        })
        .then((blob) => {
          if (cancelled) return;
          posterObjectUrl = URL.createObjectURL(blob);
          setPreviewPosterUrl(posterObjectUrl);
        })
        .catch(() => {
          if (!cancelled) setPreviewPosterUrl(undefined);
        });
    }
    return () => {
      cancelled = true;
      if (posterObjectUrl) URL.revokeObjectURL(posterObjectUrl);
    };
  }, [previewAsset]);

  useEffect(() => {
    return () => {
      uppyRef.current?.destroy();
      xhrRef.current?.abort();
    };
  }, []);

  const invalidateVideoData = () => {
    void queryClient.invalidateQueries({ queryKey: ["media-assets"] });
  };

  const disposeUploadClient = () => {
    uppyRef.current?.destroy();
    uppyRef.current = null;
    uppyFileIdRef.current = "";
    xhrRef.current?.abort();
    xhrRef.current = null;
  };

  const resetUploadModal = () => {
    hashRunRef.current += 1;
    cancelBatchRef.current = true;
    disposeUploadClient();
    setUploadTitle("");
    uploadItemsRef.current = [];
    currentUploadIdRef.current = undefined;
    setUploadItems([]);
    setCurrentUploadId(undefined);
    setBatchRunning(false);
    setUploadState(emptyUploadState);
  };

  const makeUploadQueueItem = (file: File, id?: string): VideoUploadQueueItem => ({
    id: id || `${file.name}-${file.size}-${file.lastModified}-${Math.random().toString(36).slice(2)}`,
    file,
    title: videoTitleFromFile(file),
    status: "pending",
    hashProgress: 0,
    progress: 0,
    uploadedBytes: 0,
    totalBytes: file.size,
  });

  const updateUploadItem = (itemId: string, patch: Partial<VideoUploadQueueItem>) => {
    const nextItems = uploadItemsRef.current.map((item) => (item.id === itemId ? { ...item, ...patch } : item));
    uploadItemsRef.current = nextItems;
    setUploadItems(nextItems);
  };

  const setActiveUploadItemState = (itemId: string, patch: Partial<VideoUploadQueueItem>) => {
    updateUploadItem(itemId, patch);
    setUploadState((current) => ({
      ...current,
      stage: patch.status || current.stage,
      hashProgress: patch.hashProgress ?? current.hashProgress,
      progress: patch.progress ?? current.progress,
      uploadedBytes: patch.uploadedBytes ?? current.uploadedBytes,
      totalBytes: patch.totalBytes ?? current.totalBytes,
      checksum: patch.checksum ?? current.checksum,
      duplicateAsset: patch.duplicateAsset !== undefined ? patch.duplicateAsset : current.duplicateAsset,
      error: patch.error,
      note: patch.note,
    }));
  };

  const handleUploadFiles = (files: File[]) => {
    if (batchRunning) {
      message.warning("队列正在上传，请先暂停或取消当前队列");
      return;
    }
    hashRunRef.current += 1;
    disposeUploadClient();
    const videoFiles = files.filter((file) => file.type.startsWith("video/") || /\.(mp4|mov|m4v|webm|avi)$/i.test(file.name));
    const nextItems = videoFiles.map((file) => makeUploadQueueItem(file, (file as File & { uid?: string }).uid));
    uploadItemsRef.current = nextItems;
    currentUploadIdRef.current = undefined;
    setUploadItems(nextItems);
    setCurrentUploadId(undefined);
    setUploadTitle(nextItems.length === 1 ? nextItems[0].title : "");
    setUploadState({
      ...emptyUploadState,
      stage: nextItems.length ? "pending" : "idle",
      totalBytes: nextItems.reduce((sum, item) => sum + item.totalBytes, 0),
      note: nextItems.length > 1 ? `已选择 ${nextItems.length} 个视频，将按顺序逐个上传。` : undefined,
    });
    if (files.length && !videoFiles.length) {
      message.warning("请选择视频文件");
    }
  };

  const updateSingleUploadTitle = (value: string) => {
    setUploadTitle(value);
    if (uploadItems.length === 1) {
      updateUploadItem(uploadItems[0].id, { title: value });
    }
  };

  const runDuplicatePrecheck = async (item: VideoUploadQueueItem) => {
    const runId = hashRunRef.current;
    setActiveUploadItemState(item.id, {
      status: "hashing",
      hashProgress: 0,
      progress: 0,
      uploadedBytes: 0,
      totalBytes: item.file.size,
      error: undefined,
      note: undefined,
      duplicateAsset: null,
    });
    try {
      const checksum = await computeVideoFileSha256(item.file, (progress) => {
        if (hashRunRef.current !== runId) return;
        setActiveUploadItemState(item.id, { hashProgress: progress });
      });
      if (hashRunRef.current !== runId || cancelBatchRef.current) return { checksum: undefined, duplicateAsset: null };
      const precheck = await postJson<MediaDuplicatePrecheck>("/api/admin/media/assets/precheck", {
        checksum_sha256: checksum,
        file_size_bytes: item.file.size,
      });
      if (hashRunRef.current !== runId || cancelBatchRef.current) return { checksum, duplicateAsset: null };
      setActiveUploadItemState(item.id, {
        status: precheck.exists && precheck.asset ? "duplicate" : "ready",
        hashProgress: 100,
        totalBytes: item.file.size,
        checksum,
        duplicateAsset: precheck.asset || null,
        note: precheck.exists && precheck.asset ? "发现完全相同的已上传文件，已复用已有视频。" : undefined,
      });
      return { checksum, duplicateAsset: precheck.asset || null };
    } catch (error) {
      if (hashRunRef.current !== runId || cancelBatchRef.current) return { checksum: undefined, duplicateAsset: null };
      setActiveUploadItemState(item.id, {
        status: "ready",
        totalBytes: item.file.size,
        note: "预检未完成：" + errorMessage(error),
      });
      return { checksum: undefined, duplicateAsset: null };
    }
  };

  const finalizeResumableUpload = async (item: VideoUploadQueueItem, uploadUrl?: string | null, checksum?: string) => {
    const uploadId = extractTusUploadId(uploadUrl);
    if (!uploadId) throw new Error("无法识别 tus 上传编号");
    setActiveUploadItemState(item.id, { status: "finalizing", progress: 100, uploadedBytes: item.file.size, totalBytes: item.file.size });
    const asset = await postJson<MediaAsset>("/api/admin/media/assets/complete-upload", {
      title: item.title.trim() || videoTitleFromFile(item.file),
      upload_id: uploadId,
      filename: item.file.name,
      content_type: item.file.type || "video/mp4",
      checksum_sha256: checksum || undefined,
    });
    setActiveUploadItemState(item.id, {
      status: asset.upload_status === "ready" ? "complete" : "processing",
      progress: 100,
      uploadedBytes: item.file.size,
      totalBytes: item.file.size,
      note: asset.upload_status === "ready" ? "已复用已有视频" : "已进入后台处理",
    });
    invalidateVideoData();
  };

  const uploadItemWithTus = async (item: VideoUploadQueueItem, checksum?: string) => {
    if (!tusEndpoint) throw new Error("未配置 tus 上传端点");
    disposeUploadClient();
    const uppy = new Uppy({ autoProceed: false, restrictions: { maxNumberOfFiles: 1 } });
    uppy.use(Tus, {
      endpoint: tusEndpoint + "/",
      chunkSize: 10 * 1024 * 1024,
      retryDelays: [0, 1000, 3000, 5000],
      storeFingerprintForResuming: true,
      removeFingerprintOnSuccess: false,
      metadata: {
        filename: item.file.name,
        filetype: item.file.type || "video/mp4",
      },
    });
    uppyFileIdRef.current = uppy.addFile({ name: item.file.name, type: item.file.type || "video/mp4", data: item.file });
    uppyRef.current = uppy;
    setActiveUploadItemState(item.id, { status: "uploading", progress: 0, uploadedBytes: 0, totalBytes: item.file.size, error: undefined });
    await new Promise<void>((resolve, reject) => {
      let settled = false;
      const settle = (fn: () => void) => {
        if (settled) return;
        settled = true;
        fn();
      };
      uppy.on("upload-progress", (_file, progress) => {
        const uploadedBytes = Number(progress.bytesUploaded || 0);
        const totalBytes = Number(progress.bytesTotal || item.file.size || 0);
        setActiveUploadItemState(item.id, {
          status: "uploading",
          uploadedBytes,
          totalBytes,
          progress: totalBytes ? Math.round((uploadedBytes / totalBytes) * 100) : item.progress,
        });
      });
      uppy.on("upload-error", (_file, error) => {
        settle(() => reject(error));
      });
      uppy.on("upload-success", (file, response) => {
        const uploadUrl = response.uploadURL || (file as unknown as { uploadURL?: string }).uploadURL;
        void finalizeResumableUpload(item, uploadUrl, checksum).then(() => settle(resolve)).catch((error) => settle(() => reject(error)));
      });
      void uppy.upload().catch((error) => settle(() => reject(error)));
    });
  };

  const uploadItemWithFallback = async (item: VideoUploadQueueItem, checksum?: string) => {
    disposeUploadClient();
    const body = new FormData();
    body.append("title", item.title.trim() || videoTitleFromFile(item.file));
    body.append("file", item.file);
    if (checksum) body.append("checksum_sha256", checksum);
    setActiveUploadItemState(item.id, { status: "uploading", progress: 0, uploadedBytes: 0, totalBytes: item.file.size, error: undefined });
    await new Promise<void>((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhrRef.current = xhr;
      xhr.open("POST", apiBase + "/api/admin/media/assets");
      const token = getAuthToken();
      if (token) xhr.setRequestHeader("Authorization", "Bearer " + token);
      xhr.upload.onprogress = (event) => {
        if (!event.lengthComputable) return;
        setActiveUploadItemState(item.id, {
          status: "uploading",
          uploadedBytes: event.loaded,
          totalBytes: event.total,
          progress: Math.round((event.loaded / event.total) * 100),
        });
      };
      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          const asset = JSON.parse(xhr.responseText || "{}") as MediaAsset;
          setActiveUploadItemState(item.id, {
            status: asset.upload_status === "ready" ? "complete" : "processing",
            progress: 100,
            uploadedBytes: item.file.size,
            totalBytes: item.file.size,
            note: asset.upload_status === "ready" ? "已复用已有视频" : "已进入后台处理",
          });
          invalidateVideoData();
          resolve();
        } else {
          reject(new Error(xhr.responseText || "HTTP " + xhr.status));
        }
      };
      xhr.onerror = () => reject(new Error("上传失败"));
      xhr.onabort = () => reject(new Error("上传已取消"));
      xhr.send(body);
    });
  };

  const processUploadItem = async (item: VideoUploadQueueItem) => {
    currentUploadIdRef.current = item.id;
    setCurrentUploadId(item.id);
    const title = item.title.trim() || videoTitleFromFile(item.file);
    updateUploadItem(item.id, { title });
    const precheck = await runDuplicatePrecheck({ ...item, title });
    if (cancelBatchRef.current) return;
    if (precheck.duplicateAsset) {
      setActiveUploadItemState(item.id, {
        status: "duplicate",
        progress: 100,
        uploadedBytes: item.file.size,
        totalBytes: item.file.size,
        duplicateAsset: precheck.duplicateAsset,
        note: "完全相同文件已存在，未重复上传。",
      });
      invalidateVideoData();
      return;
    }
    const itemForUpload = { ...item, title };
    if (tusEndpoint) await uploadItemWithTus(itemForUpload, precheck.checksum);
    else await uploadItemWithFallback(itemForUpload, precheck.checksum);
  };

  const startUpload = async () => {
    if (!uploadItems.length) {
      message.warning("请先选择视频文件");
      return;
    }
    if (uploadItems.length === 1 && !uploadItems[0].title.trim()) {
      message.warning("请输入视频标题");
      return;
    }
    cancelBatchRef.current = false;
    hashRunRef.current += 1;
    setBatchRunning(true);
    try {
      const queue = uploadItemsRef.current.filter((item) => ["pending", "ready", "error"].includes(item.status));
      for (const queuedItem of queue) {
        if (cancelBatchRef.current) break;
        const latest = uploadItemsRef.current.find((item) => item.id === queuedItem.id) || queuedItem;
        await processUploadItem(latest);
      }
      disposeUploadClient();
      currentUploadIdRef.current = undefined;
      setCurrentUploadId(undefined);
      if (cancelBatchRef.current) {
        setUploadState((current) => ({ ...current, stage: uploadItemsRef.current.length ? "pending" : "idle", note: "上传队列已取消" }));
      } else {
        setUploadState((current) => ({ ...current, stage: "complete", progress: 100, note: `队列已处理 ${uploadItemsRef.current.length} 个视频，后台会继续生成缩略图和学生播放源。` }));
        message.success("上传队列已处理完成");
        invalidateVideoData();
      }
    } catch (error) {
      const failedItemId = currentUploadIdRef.current || currentUploadId;
      if (failedItemId) updateUploadItem(failedItemId, { status: "error", error: errorMessage(error) });
      setUploadState((current) => ({ ...current, stage: "error", error: errorMessage(error), note: "队列已暂停，修复后可点击重试继续。" }));
      message.error(errorMessage(error));
    } finally {
      setBatchRunning(false);
    }
  };

  const toggleUploadPause = () => {
    if (!uppyRef.current || !uppyFileIdRef.current) return;
    const paused = uppyRef.current.pauseResume(uppyFileIdRef.current);
    const activeItemId = currentUploadIdRef.current || currentUploadId;
    if (activeItemId) updateUploadItem(activeItemId, { status: paused ? "paused" : "uploading" });
    setUploadState((current) => ({ ...current, stage: paused ? "paused" : "uploading" }));
  };

  const retryUpload = () => {
    if (uppyRef.current && uppyFileIdRef.current) {
      setUploadState((current) => ({ ...current, stage: "uploading", error: undefined }));
      void uppyRef.current.retryUpload(uppyFileIdRef.current);
      return;
    }
    void startUpload();
  };

  const cancelUpload = () => {
    cancelBatchRef.current = true;
    disposeUploadClient();
    setBatchRunning(false);
    const activeItemId = currentUploadIdRef.current || currentUploadId;
    if (activeItemId) {
      updateUploadItem(activeItemId, { status: "error", error: "已取消，可重新开始队列" });
    }
    currentUploadIdRef.current = undefined;
    setUploadState((current) => ({ ...current, stage: uploadItems.length ? "pending" : "idle", progress: 0, uploadedBytes: 0, note: "上传队列已取消" }));
  };

  const reuseDuplicate = () => {
    if (!currentUploadItem?.duplicateAsset && !uploadState.duplicateAsset) return;
    message.success("已使用已有视频，未重复上传");
    invalidateVideoData();
  };

  const retryProcessing = useMutation({
    mutationFn: (assetId: string) => postJson("/api/admin/media/assets/" + assetId + "/retry-processing", {}),
    onSuccess: () => {
      message.success("已重新排队处理");
      invalidateVideoData();
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const duplicateDecision = useMutation({
    mutationFn: ({ id, status }: { id: string; status: "kept" | "reused" | "ignored" }) =>
      patchJson("/api/admin/media/duplicate-candidates/" + id, { status }),
    onSuccess: () => {
      message.success("重复提示已更新");
      invalidateVideoData();
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const uploadBusy = batchRunning || ["hashing", "uploading", "paused", "finalizing"].includes(uploadState.stage);
  const canStartUpload = uploadItems.length > 0 && !batchRunning && uploadItems.some((item) => ["pending", "ready", "error"].includes(item.status)) && (uploadItems.length > 1 || Boolean(uploadItems[0].title.trim()));
  const canPause = Boolean(tusEndpoint && uppyRef.current && uppyFileIdRef.current && ["uploading", "paused"].includes(uploadState.stage));
  const canCancel = batchRunning || ["uploading", "paused", "finalizing", "hashing"].includes(uploadState.stage);
  const uploadFinished = uploadState.stage === "complete";
  const closeUploadModal = () => {
    resetUploadModal();
    setUploadOpen(false);
  };
  const uploadModalFooter = uploadFinished
    ? [
        <Button key="again" onClick={resetUploadModal}>继续上传其他视频</Button>,
        <Button key="done" type="primary" icon={<CheckCircleOutlined />} onClick={closeUploadModal}>完成并查看列表</Button>,
      ]
    : [
        <Button key="close" onClick={closeUploadModal}>关闭</Button>,
        canPause ? <Button key="pause" icon={uploadState.stage === "paused" ? <PlayCircleOutlined /> : <PauseCircleOutlined />} onClick={toggleUploadPause}>{uploadState.stage === "paused" ? "继续当前文件" : "暂停当前文件"}</Button> : null,
        uploadState.stage === "error" && !batchRunning ? <Button key="retry" icon={<ReloadOutlined />} onClick={retryUpload}>重试队列</Button> : null,
        canCancel ? <Button key="cancel" danger icon={<CloseCircleOutlined />} onClick={cancelUpload}>取消队列</Button> : null,
        <Button key="upload" type="primary" icon={<CloudUploadOutlined />} loading={uploadBusy && uploadState.stage !== "paused"} disabled={!canStartUpload} onClick={() => void startUpload()}>{uploadItems.length > 1 ? "开始队列上传" : tusEndpoint ? "开始上传" : "小文件上传"}</Button>,
      ].filter(Boolean);

  const renderAssetBadges = (asset: MediaAsset) => (
    <Space size={[4, 4]} wrap className="video-asset-badges">
      {hasPendingDuplicate(asset) ? <Tag color="#b8892f">疑似重复待确认</Tag> : null}
      {asset.upload_status !== "ready" && asset.upload_status !== "failed" ? <Tag>{processingPhaseText(asset)}</Tag> : null}
    </Space>
  );

  const renderAssetName = (asset: MediaAsset) => (
    <Space size={10} align="start" className="video-asset-name">
      <MediaThumbnail asset={asset} compact />
      <Space direction="vertical" size={1}>
        <Text strong>{asset.title}</Text>
        <Text type="secondary">{asset.original_file_name}</Text>
        {renderAssetBadges(asset)}
      </Space>
    </Space>
  );

  const renderProcessingLine = (asset: MediaAsset) => {
    if (asset.upload_status === "ready") return <Text type="secondary">{formatDurationSeconds(asset.duration_seconds)} · {formatResolution(asset)}</Text>;
    if (asset.upload_status === "failed") return <Text type="danger">{asset.error_reason || asset.processing_job?.error_reason || "处理失败"}</Text>;
    return <Progress percent={processingProgressValue(asset)} size="small" status="active" format={() => processingPhaseText(asset)} />;
  };

  const renderVersionPanel = (asset: MediaAsset) => {
    const { rendition, savedPercent } = renditionSavings(asset);
    return (
      <div className="video-version-panel">
        <div className="video-version-item">
          <Text strong>原始文件</Text>
          <Text type="secondary" className="block-text">老师上传的源文件，保留在本地媒体目录，用于备份、审计和后续重新处理。</Text>
          <Text>{formatBytes(asset.file_size_bytes)} · {formatResolution(asset)} · {(asset.video_codec || "-") + " / " + (asset.audio_codec || "-")}</Text>
        </div>
        <div className="video-version-item">
          <Text strong>学生播放源</Text>
          <Text type="secondary" className="block-text">后台用 FFmpeg 生成或确认的学生观看文件；这里会显示体积、分辨率和节省比例。</Text>
          <Text>{rendition ? formatBytes(rendition.file_size_bytes) + " · " + formatResolution(rendition) + (savedPercent ? " · 节省 " + savedPercent + "%" : " · 未明显压缩") : "未生成或仍在处理中"}</Text>
        </div>
      </div>
    );
  };

  const renderDuplicateCandidates = (asset: MediaAsset) => {
    const candidates = asset.duplicate_candidates || [];
    if (!candidates.length) return null;
    return (
      <div className="video-duplicate-panel">
        <Flex justify="space-between" align="start" gap={12} wrap="wrap">
          <div>
            <Text strong>疑似内容重复</Text>
            <Text type="secondary" className="block-text">这是 vPDQ/ThreatExchange 相似度工具给出的内容相近提示，不代表 SHA-256 完全相同；系统不会自动删除或跳过。</Text>
          </div>
          <Tag color={hasPendingDuplicate(asset) ? "#b8892f" : "default"}>{pendingDuplicateCandidates(asset).length ? pendingDuplicateCandidates(asset).length + " 个待确认" : "已处理"}</Tag>
        </Flex>
        <div className="video-duplicate-list">
          {candidates.map((candidate) => (
            <div key={candidate.id} className="video-duplicate-item">
              <Space align="center" size={10} className="video-duplicate-copy">
                <div className="video-duplicate-thumb">
                  <AuthenticatedImage
                    src={candidate.candidate_asset_id ? apiBase + "/api/admin/media/assets/" + candidate.candidate_asset_id + "/thumbnail" : null}
                    alt={candidate.candidate_title || "疑似重复视频"}
                    className="video-thumb-image compact"
                  />
                  <VideoCameraOutlined />
                </div>
                <div>
                  <Text strong>{candidate.candidate_title || candidate.candidate_asset_id || "未知视频"}</Text>
                  <Text type="secondary" className="block-text">
                    内容相似度 {duplicateScoreText(candidate.score)} · {candidate.algorithm} · {duplicateDecisionLabels[candidate.status] || candidate.status}
                  </Text>
                </div>
              </Space>
              <div className="video-duplicate-actions">
                {candidate.status === "pending" ? (
                  <Space size={6} wrap>
                    <Button size="small" onClick={() => duplicateDecision.mutate({ id: candidate.id, status: "kept" })}>保留两个</Button>
                    <Button size="small" onClick={() => duplicateDecision.mutate({ id: candidate.id, status: "reused" })}>复用已有</Button>
                    <Button size="small" onClick={() => duplicateDecision.mutate({ id: candidate.id, status: "ignored" })}>忽略提示</Button>
                  </Space>
                ) : (
                  <Tag>{duplicateDecisionLabels[candidate.status] || candidate.status}</Tag>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <Space direction="vertical" size={18} className="full">
      <PageTitle
        title="视频资源"
        description="这里是后台的视频资源库，用来集中管理老师上传的视频文件。上传支持断点续传，上传完成后系统会在后台自动读取视频信息、生成真实缩略图、为学生端选择或生成更适合在线播放的学生播放源，并提示可能重复的视频。这个页面只负责上传、检索、预览和处理状态查看；把视频引用到具体实验点，仍然在实验管理页面完成。若出现处理失败，通常表示后台无法读取或生成视频输出，比如文件损坏、编码不兼容、磁盘空间不足或视频处理服务中断，可以稍后重试。"
        extra={<Button type="primary" icon={<CloudUploadOutlined />} onClick={() => setUploadOpen(true)}>上传视频</Button>}
      />

      <div className="video-resource-metrics">
        <Card><Statistic title="资源库视频" value={assets.data?.total || 0} prefix={<VideoCameraOutlined />} /></Card>
        <Card><Statistic title="可预览" value={readyAssets.length} /></Card>
        <Card><Statistic title="处理中" value={workingAssets.length} /></Card>
        <Card><Statistic title="待确认重复" value={pendingDuplicateAssets.length} /></Card>
        <Card><Statistic title="处理失败" value={failedAssets.length} /></Card>
        <Card><Statistic title="原始空间" value={formatBytes(sourceBytes)} /></Card>
        <Card><Statistic title="学生播放源空间" value={formatBytes(renditionBytes)} /></Card>
        <Card><Statistic title="已节省空间" value={savedBytes ? formatBytes(savedBytes) : "-"} suffix={savedPercent ? " / " + savedPercent + "%" : undefined} /></Card>
      </div>

      <div className="video-drive-panel">
        {pendingDuplicateAssets.length ? (
          <Alert
            type="warning"
            showIcon
            className="video-review-alert"
            message={"有 " + pendingDuplicateAssets.length + " 个疑似重复视频待确认"}
            description="这些视频内容可能与已有视频相近，但不是完全相同文件。建议集中查看后决定保留、复用已有视频或忽略提示。"
            action={<Button size="small" onClick={() => setStatusFilter("duplicate_pending")}>查看待确认</Button>}
          />
        ) : null}
        <Flex justify="space-between" align="center" gap={14} wrap="wrap" className="video-drive-toolbar">
          <Input.Search allowClear placeholder="搜索视频标题或文件名" value={keyword} onChange={(event) => setKeyword(event.target.value)} style={{ width: 360 }} />
          <Space size={10} wrap>
            <Select allowClear placeholder="全部状态" value={statusFilter} onChange={setStatusFilter} style={{ width: 160 }} options={[{ value: "duplicate_pending", label: "待确认重复" }, { value: "ready", label: "就绪" }, { value: "processing", label: "处理中" }, { value: "pending", label: "待处理" }, { value: "failed", label: "处理失败" }, { value: "replaced", label: "已替换" }]} />
            <Select value={sortKey} onChange={setSortKey} style={{ width: 150 }} options={[{ value: "updated_desc", label: "最近更新" }, { value: "name_asc", label: "名称 A-Z" }, { value: "size_desc", label: "文件最大" }]} />
            <Segmented value={viewMode} onChange={(value) => setViewMode(value as "grid" | "list")} options={[{ value: "list", icon: <UnorderedListOutlined />, label: "条" }, { value: "grid", icon: <AppstoreOutlined />, label: "块" }]} />
          </Space>
        </Flex>

        <QueryState loading={assets.isLoading} error={assets.error} empty={!assetItems.length}>
          {!filteredAssets.length ? <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="没有匹配的视频" /> : viewMode === "grid" ? (
            <div className="video-drive-grid">
              {filteredAssets.map((asset) => (
                <div className="video-asset-card" key={asset.id}>
                  <button type="button" className="video-asset-cover" onClick={() => setPreviewAsset(asset)} disabled={!isPreviewableVideo(asset)}><MediaThumbnail asset={asset} /></button>
                  <Space direction="vertical" size={8} className="full">
                    <div><Text strong className="video-asset-title">{asset.title}</Text><Text type="secondary" className="video-asset-file">{asset.original_file_name}</Text></div>
                    <Flex justify="space-between" align="center" gap={8}>{mediaStatusTag(asset.upload_status)}<Text type="secondary">{formatBytes(asset.file_size_bytes)}</Text></Flex>
                    {renderProcessingLine(asset)}
                    {renderAssetBadges(asset)}
                    <Flex justify="space-between" align="center" gap={8}>
                      <Text type="secondary">{mediaAssetTime(asset)}</Text>
                      <Space size={6}>{asset.upload_status === "failed" ? <Button size="small" icon={<ReloadOutlined />} loading={retryProcessing.isPending} onClick={() => retryProcessing.mutate(asset.id)}>重试</Button> : null}<Button size="small" icon={<EyeOutlined />} disabled={!isPreviewableVideo(asset)} onClick={() => setPreviewAsset(asset)}>预览</Button></Space>
                    </Flex>
                  </Space>
                </div>
              ))}
            </div>
          ) : (
            <Table rowKey="id" dataSource={filteredAssets} pagination={{ pageSize: 12, showSizeChanger: false }} columns={[{ title: "文件名", render: (_: unknown, asset: MediaAsset) => renderAssetName(asset) }, { title: "处理", width: 190, render: (_: unknown, asset: MediaAsset) => renderProcessingLine(asset) }, { title: "大小", width: 110, render: (_: unknown, asset: MediaAsset) => formatBytes(asset.file_size_bytes) }, { title: "状态", width: 110, render: (_: unknown, asset: MediaAsset) => mediaStatusTag(asset.upload_status) }, { title: "引用", width: 90, render: (_: unknown, asset: MediaAsset) => asset.association_count || 0 }, { title: "更新时间", width: 170, render: (_: unknown, asset: MediaAsset) => mediaAssetTime(asset) }, { title: "操作", width: 170, render: (_: unknown, asset: MediaAsset) => <Space size={6}>{asset.upload_status === "failed" ? <Button size="small" icon={<ReloadOutlined />} onClick={() => retryProcessing.mutate(asset.id)}>重试</Button> : null}<Button size="small" icon={<EyeOutlined />} disabled={!isPreviewableVideo(asset)} onClick={() => setPreviewAsset(asset)}>预览</Button></Space> }]} />
          )}
        </QueryState>
      </div>

      <Modal title="上传视频" open={uploadOpen} onCancel={closeUploadModal} footer={uploadModalFooter} width={780}>
        <Space direction="vertical" size={14} className="full">
          {!uploadFinished ? (
            <>
              {!tusEndpoint ? <Alert type="warning" showIcon message="当前使用小文件回退上传" description="配置 VITE_TUS_ENDPOINT 后可启用断点续传。" /> : null}
              <Input
                placeholder={uploadItems.length > 1 ? "多个视频将默认使用各自文件名作为标题" : "视频标题"}
                value={uploadItems.length > 1 ? "" : uploadTitle}
                disabled={uploadItems.length > 1 || batchRunning}
                onChange={(event) => updateSingleUploadTitle(event.target.value)}
              />
              <div className="video-upload-guide">
                <div className="video-upload-guide-head">
                  <div>
                    <Text strong>上传后会自动处理</Text>
                    <Text type="secondary" className="block-text">{uploadStageText(uploadState.stage)}</Text>
                  </div>
                  <span>{tusEndpoint ? "断点续传" : "小文件上传"}</span>
                </div>
                <div className="video-upload-flow">
                  {[
                    {
                      title: "校验",
                      description: uploadState.stage === "hashing" ? "正在校验 " + uploadState.hashProgress + "%" : "识别完全重复文件",
                    },
                    {
                      title: "上传",
                      description: tusEndpoint ? "中断后可继续传" : "当前走普通上传",
                    },
                    {
                      title: "处理",
                      description: "缩略图、学生播放源、相似度",
                    },
                  ].map((step, index) => {
                    const currentStep = uploadStepCurrent(uploadState.stage);
                    const stateClass = currentStep > index ? "done" : currentStep === index ? "active" : "";
                    return (
                      <div key={step.title} className={`video-upload-flow-step ${stateClass}`}>
                        <span className="video-upload-flow-dot">{currentStep > index ? <CheckCircleOutlined /> : index + 1}</span>
                        <div>
                          <strong>{step.title}</strong>
                          <small>{step.description}</small>
                        </div>
                      </div>
                    );
                  })}
                </div>
                <div className="video-upload-guide-notes">
                  <span>同一浏览器重新选择同一文件，会尽量从已上传位置继续</span>
                  <span>多个视频会按队列串行上传，完成后进入后台处理</span>
                </div>
              </div>
              <Upload.Dragger
                accept="video/*,.mp4,.mov,.m4v,.webm,.avi"
                multiple
                showUploadList={false}
                disabled={batchRunning}
                beforeUpload={(file, fileList) => {
                  const maybeFile = file as File & { uid?: string };
                  const lastFile = fileList[fileList.length - 1] as File & { uid?: string };
                  if (maybeFile.uid === lastFile?.uid) handleUploadFiles(fileList as File[]);
                  return false;
                }}
              >
                <p className="ant-upload-drag-icon"><CloudUploadOutlined /></p>
                <p className="ant-upload-text">拖拽一个或多个视频到这里，或点击选择文件</p>
                <p className="ant-upload-hint">支持 mp4、mov、m4v、webm、avi；多个文件会串行上传，上传完成后自动进入后台处理。</p>
              </Upload.Dragger>
            </>
          ) : (
            <div className="video-upload-complete-card">
              <span className="video-upload-complete-icon"><CheckCircleOutlined /></span>
              <div>
                <Text strong>上传已完成，视频已加入后台处理队列</Text>
                <Text type="secondary" className="block-text">现在可以回到列表查看结果。后台会继续读取元数据、生成真实缩略图、准备学生播放源，并完成相似视频检测；列表会自动刷新处理阶段。</Text>
              </div>
            </div>
          )}
          {uploadItems.length ? (
            <div className="video-upload-queue">
              <Flex justify="space-between" align="center" gap={10} wrap="wrap">
                <Text strong>{batchRunning ? "队列上传中" : "上传队列"}</Text>
                <Text type="secondary">{uploadQueueDoneCount} / {uploadItems.length} 个已处理 · {formatBytes(uploadQueueUploadedBytes)} / {formatBytes(uploadQueueTotalBytes)}</Text>
              </Flex>
              <Progress percent={uploadQueueProgress} status={uploadState.stage === "error" ? "exception" : batchRunning ? "active" : "normal"} />
              <div className="video-upload-queue-list">
                {uploadItems.map((item, index) => {
                  const itemPercent = item.status === "hashing" ? item.hashProgress : item.progress;
                  const itemActive = item.id === currentUploadId;
                  return (
                    <div key={item.id} className={itemActive ? "video-upload-queue-item active" : "video-upload-queue-item"}>
                      <div className="video-upload-queue-copy">
                        <Text strong>{index + 1}. {item.title || videoTitleFromFile(item.file)}</Text>
                        <Text type="secondary" className="block-text">{item.file.name} · {formatBytes(item.file.size)}</Text>
                        {item.duplicateAsset ? <Text type="secondary" className="block-text">复用：{item.duplicateAsset.title}</Text> : null}
                      </div>
                      <div className="video-upload-queue-state">
                        <Tag color={item.status === "error" ? "red" : ["duplicate", "processing", "complete"].includes(item.status) ? "green" : itemActive ? "#b8892f" : "default"}>{uploadQueueItemText(item)}</Tag>
                        {["hashing", "uploading", "paused", "finalizing"].includes(item.status) ? <Progress percent={itemPercent} size="small" status={item.status === "paused" ? "normal" : "active"} /> : null}
                      </div>
                      {!batchRunning && !uploadFinished ? (
                        <Button
                          size="small"
                          danger
                          icon={<DeleteOutlined />}
                          onClick={() => {
                            const nextItems = uploadItems.filter((candidate) => candidate.id !== item.id);
                            uploadItemsRef.current = nextItems;
                            setUploadItems(nextItems);
                            if (!nextItems.length) {
                              setUploadTitle("");
                              setUploadState(emptyUploadState);
                              return;
                            }
                            if (nextItems.length === 1) setUploadTitle(nextItems[0].title);
                            setUploadState((current) => ({
                              ...current,
                              stage: nextItems.length ? current.stage : "idle",
                              uploadedBytes: nextItems.reduce((sum, candidate) => sum + candidate.uploadedBytes, 0),
                              totalBytes: nextItems.reduce((sum, candidate) => sum + candidate.totalBytes, 0),
                              note: nextItems.length > 1 ? `已选择 ${nextItems.length} 个视频，将按顺序逐个上传。` : undefined,
                            }));
                          }}
                        >
                          移除
                        </Button>
                      ) : null}
                    </div>
                  );
                })}
              </div>
            </div>
          ) : null}
          {uploadState.stage === "hashing" ? <div className="video-upload-status"><Text strong>正在校验当前文件</Text><Progress percent={uploadState.hashProgress} /></div> : null}
          {uploadState.note && !["processing", "complete"].includes(uploadState.stage) ? <div className="video-upload-inline-note">{uploadState.note}</div> : null}
          {(currentUploadItem?.duplicateAsset || uploadState.duplicateAsset) ? <Alert type="success" showIcon message="发现完全相同的已上传文件" description={<Space align="center" size={12}><MediaThumbnail asset={(currentUploadItem?.duplicateAsset || uploadState.duplicateAsset) as MediaAsset} compact /><div><Text strong>{(currentUploadItem?.duplicateAsset || uploadState.duplicateAsset)?.title}</Text><Text type="secondary" className="block-text">{(currentUploadItem?.duplicateAsset || uploadState.duplicateAsset)?.original_file_name} · {formatBytes((currentUploadItem?.duplicateAsset || uploadState.duplicateAsset)?.file_size_bytes)} · {mediaStatusLabels[(currentUploadItem?.duplicateAsset || uploadState.duplicateAsset)?.upload_status || ""] || (currentUploadItem?.duplicateAsset || uploadState.duplicateAsset)?.upload_status}</Text></div></Space>} /> : null}
          {["uploading", "paused", "finalizing"].includes(uploadState.stage) ? <div className="video-upload-status"><Flex justify="space-between" align="center"><Text strong>{uploadState.stage === "finalizing" ? "正在完成当前文件入库" : uploadState.stage === "paused" ? "当前文件已暂停" : "正在上传当前文件"}</Text><Text type="secondary">{formatBytes(uploadState.uploadedBytes)} / {formatBytes(uploadState.totalBytes || currentUploadItem?.file.size)}</Text></Flex><Progress percent={uploadState.progress} status={uploadState.stage === "paused" ? "normal" : "active"} /></div> : null}
          {uploadState.stage === "processing" ? (
            <div className="video-upload-inline-note success">当前文件已上传，队列会继续上传后续文件；已完成的视频会留在列表里显示后台处理阶段。</div>
          ) : null}
          {uploadState.error ? <Alert type="error" showIcon message={uploadState.error} /> : null}
        </Space>
      </Modal>

      <Modal
        title={previewAsset ? (
          <Space size={8} wrap className="video-preview-title">
            <span>{previewAsset.title}</span>
            {hasPendingDuplicate(previewAsset) ? <Tag color="#b8892f">疑似重复待确认</Tag> : null}
          </Space>
        ) : "视频预览"}
        open={Boolean(previewAsset)}
        onCancel={() => setPreviewAsset(null)}
        footer={[<Button key="close" onClick={() => setPreviewAsset(null)}>关闭</Button>]}
        width={1040}
      >
        {previewAsset ? (
          <Space direction="vertical" size={16} className="full">
            {hasPendingDuplicate(previewAsset) ? (
              <Alert
                type="warning"
                showIcon
                message="这个视频可能与已有视频内容相近"
                description="这是感知相似度检测结果，不是完全相同文件。请在下方重复审核区确认保留、复用或忽略。"
              />
            ) : null}
            <div className="video-preview-layout">
              <div className="video-preview-stage">
                {previewLoading ? <Spin /> : previewError ? <Alert type="error" showIcon message={previewError} /> : previewUrl ? <video controls preload="metadata" className="video-preview-player" src={previewUrl} poster={previewPosterUrl} /> : <Alert type="info" showIcon message="该视频当前不可预览" description="只有上传状态为就绪的视频可以在线播放。" />}
              </div>
              <Descriptions
                size="small"
                column={1}
                items={[
                  { key: "file", label: "原始文件", children: previewAsset.original_file_name },
                  { key: "status", label: "状态", children: mediaStatusTag(previewAsset.upload_status) },
                  { key: "phase", label: "处理阶段", children: processingPhaseText(previewAsset) },
                  { key: "source", label: "原始大小", children: formatBytes(previewAsset.file_size_bytes) },
                  { key: "duration", label: "时长", children: formatDurationSeconds(previewAsset.duration_seconds) },
                  { key: "resolution", label: "分辨率", children: formatResolution(previewAsset) },
                  { key: "codec", label: "编码", children: (previewAsset.video_codec || "-") + " / " + (previewAsset.audio_codec || "-") },
                  { key: "rendition", label: "学生播放源", children: selectedRendition(previewAsset) ? formatBytes(selectedRendition(previewAsset)?.file_size_bytes) + " · " + formatResolution(selectedRendition(previewAsset)) : "未生成" },
                  { key: "playback", label: "播放源", children: previewAsset.playback_relative_path ? "学生播放源（预览/学生端优先使用）" : "原始文件（原文件已可播放）" },
                  { key: "time", label: "更新时间", children: mediaAssetTime(previewAsset) },
                ]}
              />
            </div>
            {renderVersionPanel(previewAsset)}
            {previewAsset.upload_status !== "ready" ? <Progress percent={processingProgressValue(previewAsset)} status={previewAsset.upload_status === "failed" ? "exception" : "active"} format={() => processingPhaseText(previewAsset)} /> : null}
            {previewAsset.error_reason ? <Alert type="error" showIcon message={previewAsset.error_reason} /> : null}
            {renderDuplicateCandidates(previewAsset)}
          </Space>
        ) : null}
      </Modal>
    </Space>
  );
}

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

function questionPoints(question: Question) {
  const points = question.metadata?.primary_points || [];
  if (points.length) {
    return points
      .map((point) => ({
        point_key: String(point.point_key || "").trim(),
        point_title: String(point.point_title || point.point_key || "").trim(),
      }))
      .filter((point) => point.point_key || point.point_title);
  }
  return (question.metadata?.primary_point_keys || [])
    .map((key) => ({ point_key: String(key), point_title: String(key) }))
    .filter((point) => point.point_key);
}

function questionPointTitles(question: Question) {
  return questionPoints(question).map((point) => point.point_title || point.point_key).filter(Boolean);
}

function draftPayload(draft: QuestionDraft) {
  return draft.payload || {};
}

function draftStem(draft: QuestionDraft) {
  return String(draftPayload(draft).stem || "");
}

function draftQuestionType(draft: QuestionDraft) {
  return String(draftPayload(draft).question_type || "");
}

function draftQuestionPoints(draft: QuestionDraft) {
  const metadata = draftPayload(draft).metadata || {};
  const points = Array.isArray(metadata.primary_points) ? metadata.primary_points : [];
  if (points.length) {
    return points
      .map((point) => ({
        point_key: String(point?.point_key || "").trim(),
        point_title: String(point?.point_title || point?.point_key || "").trim(),
      }))
      .filter((point) => point.point_key || point.point_title);
  }
  const keys = Array.isArray(metadata.primary_point_keys) ? metadata.primary_point_keys : [];
  return keys.map((key) => ({ point_key: String(key), point_title: String(key) })).filter((point) => point.point_key);
}

function candidatePayload(candidate: QuestionWorkbenchCandidate) {
  return candidate.payload || {};
}

function candidateStem(candidate: QuestionWorkbenchCandidate) {
  return String(candidatePayload(candidate).stem || "");
}

function candidateQuestionType(candidate: QuestionWorkbenchCandidate) {
  return String(candidatePayload(candidate).question_type || "");
}

function candidateQuestionPoints(candidate: QuestionWorkbenchCandidate) {
  const metadata = candidatePayload(candidate).metadata || {};
  const points = Array.isArray(metadata.primary_points) ? metadata.primary_points : [];
  if (points.length) {
    return points
      .map((point) => ({
        point_key: String(point?.point_key || "").trim(),
        point_title: String(point?.point_title || point?.point_key || "").trim(),
      }))
      .filter((point) => point.point_key || point.point_title);
  }
  const keys = Array.isArray(metadata.primary_point_keys) ? metadata.primary_point_keys : [];
  return keys.map((key) => ({ point_key: String(key), point_title: String(key) })).filter((point) => point.point_key);
}

function candidateValidationErrors(candidate: QuestionWorkbenchCandidate) {
  return candidate.validation_errors?.length
    ? candidate.validation_errors
    : candidate.draft_validation_errors?.length
      ? candidate.draft_validation_errors
      : [];
}

function questionHasAnyPoint(question: Question, pointKeys: string[]) {
  if (!pointKeys.length) return true;
  const selected = new Set(pointKeys);
  return questionPoints(question).some((point) => selected.has(point.point_key));
}

function evidenceStatusTag(question: Question) {
  if (question.metadata?.source_audit?.evidence_sufficient) return <Tag color="green">证据已核对</Tag>;
  if (question.source_refs?.length) return <Tag color="gold">有来源</Tag>;
  return <Tag>待核对</Tag>;
}

function evidenceStatusText(question: Question) {
  if (question.metadata?.source_audit?.evidence_sufficient) return "证据已核对";
  if (question.source_refs?.length) return "有来源";
  return "待核对";
}

function reviewDecisionText(decision?: string) {
  if (decision === "keep") return "审查保留";
  if (decision === "rewrite") return "建议改写";
  if (decision === "reject") return "已拒绝";
  return "未审查";
}

function optionDiagnosticRoleLabel(role?: string) {
  if (role === "correct_evidence") return "正确证据";
  if (role === "adjacent_point") return "相邻点位";
  if (role === "adjacent_experiment") return "相邻实验";
  if (role === "distractor_misconception") return "误区干扰";
  if (role === "unrelated_distractor") return "无关干扰";
  if (role === "weak_distractor") return "弱干扰";
  return role || "-";
}

function questionBankStatusTag(status?: string) {
  if (status === "published") return <Tag color="green">启用</Tag>;
  if (status === "disabled") return <Tag>未启用</Tag>;
  return statusTag(status);
}

function questionBankStatusText(status?: string) {
  if (status === "published") return "启用";
  if (status === "disabled") return "未启用";
  return status || "-";
}

function QuestionBanksPage() {
  const { message } = AntApp.useApp();
  const queryClient = useQueryClient();
  const [experimentId, setExperimentId] = useState<string>();
  const [questionType, setQuestionType] = useState<string>();
  const [pointKeys, setPointKeys] = useState<string[]>([]);
  const [statusFilter, setStatusFilter] = useState<string>("published");
  const [search, setSearch] = useState("");
  const [workbenchOpen, setWorkbenchOpen] = useState(false);
  const [selectedQuestion, setSelectedQuestion] = useState<Question | null>(null);
  const [assistantIntent, setAssistantIntent] = useState<"add_questions" | "repair_question">("add_questions");
  const [assistantQuestion, setAssistantQuestion] = useState<Question | null>(null);
  const [assistantPointKey, setAssistantPointKey] = useState<string>();
  const [aiWorkbenchOpen, setAiWorkbenchOpen] = useState(false);
  const [aiWorkbenchSessionId, setAiWorkbenchSessionId] = useState<string>();
  const [workbenchPrompt, setWorkbenchPrompt] = useState("");
  const [workbenchQuestionTypes, setWorkbenchQuestionTypes] = useState<Question["question_type"][]>(["single_choice", "true_false"]);
  const [workbenchCount, setWorkbenchCount] = useState(3);
  const [workbenchStreaming, setWorkbenchStreaming] = useState(false);
  const [workbenchStreamStatus, setWorkbenchStreamStatus] = useState("");

  const banks = useQuery({
    queryKey: ["question-banks"],
    queryFn: () => api<ApiList<QuestionBankSummary>>("/api/admin/question-banks"),
  });

  const bankExperiments = banks.data?.items || [];

  useEffect(() => {
    if (!experimentId && bankExperiments.length) {
      const firstWithBank = bankExperiments.find((experiment) =>
        experiment.banks.some((bank) => bank.bank_kind === "default" && Number(bank.published_count || bank.question_count || 0) > 0),
      );
      setExperimentId((firstWithBank || bankExperiments[0]).id);
    }
  }, [bankExperiments, experimentId]);

  const questionParams = new URLSearchParams({ limit: "1000" });
  if (experimentId) questionParams.set("experiment_id", experimentId);
  if (questionType) questionParams.set("question_type", questionType);
  if (statusFilter) questionParams.set("status_filter", statusFilter);
  if (search.trim()) questionParams.set("search", search.trim());

  const questions = useQuery({
    queryKey: ["experiment-bank-questions", questionParams.toString()],
    queryFn: () => api<ApiList<Question>>(`/api/admin/question-banks/questions?${questionParams.toString()}`),
    enabled: Boolean(experimentId),
  });

  const experimentPoints = useQuery({
    queryKey: ["question-bank-video-points", experimentId],
    queryFn: () => api<ExperimentVideoPointsResponse>(`/api/admin/experiments/${experimentId}/video-points`),
    enabled: Boolean(experimentId),
  });

  const drafts = useQuery({
    queryKey: ["question-bank-drafts", experimentId],
    queryFn: () => api<ApiList<QuestionDraft>>(`/api/admin/question-banks/drafts?experiment_id=${experimentId}`),
    enabled: Boolean(experimentId),
  });

  const aiWorkbench = useQuery({
    queryKey: ["question-ai-workbench", aiWorkbenchSessionId],
    queryFn: () => api<QuestionWorkbenchSession>(`/api/admin/question-banks/workbench-sessions/${aiWorkbenchSessionId}`),
    enabled: Boolean(aiWorkbenchOpen && aiWorkbenchSessionId),
  });

  const selectedExperiment = useMemo(
    () => bankExperiments.find((item) => item.id === experimentId),
    [bankExperiments, experimentId],
  );
  const selectedBank = selectedExperiment?.banks.find((bank) => bank.bank_kind === "default") || selectedExperiment?.banks[0];

  const totals = useMemo(
    () =>
      bankExperiments.reduce(
        (acc, experiment) => {
          const bank = experiment.banks.find((item) => item.bank_kind === "default") || experiment.banks[0];
          return {
            total: acc.total + Number(bank?.question_count || 0),
            published: acc.published + Number(bank?.published_count || 0),
            choice: acc.choice + Number(bank?.choice_count || 0),
            trueFalse: acc.trueFalse + Number(bank?.true_false_count || 0),
            fillBlank: acc.fillBlank + Number(bank?.fill_blank_count || 0),
          };
        },
        { total: 0, published: 0, choice: 0, trueFalse: 0, fillBlank: 0 },
      ),
    [bankExperiments],
  );

  const pointOptions = useMemo(() => {
    const byKey = new Map<string, string>();
    for (const point of experimentPoints.data?.points || []) {
      if (point.point_key && point.source !== "legacy") byKey.set(point.point_key, point.point_title || point.point_key);
    }
    for (const question of questions.data?.items || []) {
      for (const point of questionPoints(question)) {
        const key = point.point_key || point.point_title;
        if (key && !byKey.has(key)) byKey.set(key, point.point_title || key);
      }
    }
    return [...byKey.entries()].map(([value, label]) => ({ value, label }));
  }, [experimentPoints.data?.points, questions.data?.items]);

  const visibleQuestions = useMemo(
    () => (questions.data?.items || []).filter((question) => questionHasAnyPoint(question, pointKeys)),
    [pointKeys, questions.data?.items],
  );

  const workbenchCandidates = aiWorkbench.data?.candidates || [];
  const workbenchTurns = aiWorkbench.data?.turns || [];
  const workbenchContext = aiWorkbench.data?.context_snapshot || {};
  const workbenchOriginalQuestion = aiWorkbench.data?.original_question_snapshot || assistantQuestion || null;

  const openQuestionWorkbench = (question: Question) => {
    setSelectedQuestion(question);
    setWorkbenchOpen(true);
  };

  const closeWorkbench = () => {
    setWorkbenchOpen(false);
    setSelectedQuestion(null);
  };

  const openAddSuggestion = () => {
    const primaryPointKey = pointKeys[0];
    setAssistantIntent("add_questions");
    setAssistantQuestion(null);
    setAssistantPointKey(primaryPointKey);
    setWorkbenchPrompt(selectedExperiment ? `为《${selectedExperiment.code} ${selectedExperiment.title}》补充点位诊断题。` : "补充点位诊断题。");
    setWorkbenchQuestionTypes(["single_choice", "true_false"]);
    setWorkbenchCount(3);
    if (experimentId) {
      startWorkbench.mutate({ mode: "create", experiment_id: experimentId, point_key: primaryPointKey || null });
    }
  };

  const openRepairSuggestion = (question: Question) => {
    setAssistantIntent("repair_question");
    setAssistantQuestion(question);
    setWorkbenchOpen(false);
    setAssistantPointKey(questionPoints(question)[0]?.point_key);
    setWorkbenchPrompt("请基于当前实验点位、来源证据和选项诊断链接，给出一版更清晰、更可诊断的修正题。");
    setWorkbenchQuestionTypes([question.question_type]);
    setWorkbenchCount(1);
    startWorkbench.mutate({
      mode: "repair",
      experiment_id: question.experiment_id,
      question_id: question.id,
      point_key: questionPoints(question)[0]?.point_key || null,
    });
  };

  const refreshQuestionBank = () => {
    void queryClient.invalidateQueries({ queryKey: ["question-banks"] });
    void queryClient.invalidateQueries({ queryKey: ["question-bank-drafts", experimentId] });
    void queryClient.invalidateQueries({ queryKey: ["experiment-bank-questions"] });
  };

  const startWorkbench = useMutation({
    mutationFn: (payload: {
      mode: "repair" | "create";
      experiment_id: string;
      question_id?: string | null;
      point_key?: string | null;
    }) => postJson<QuestionWorkbenchSession>("/api/admin/question-banks/workbench-sessions", payload),
    onSuccess: (result) => {
      setAiWorkbenchSessionId(result.id);
      setAiWorkbenchOpen(true);
      void queryClient.invalidateQueries({ queryKey: ["question-ai-workbench", result.id] });
    },
    onError: (error) => message.error(`AI 工作台打开失败：${errorMessage(error)}`),
  });

  const sendWorkbenchMessage = async () => {
    if (!aiWorkbenchSessionId || !workbenchPrompt.trim() || workbenchStreaming) return;
    const prompt = workbenchPrompt.trim();
    setWorkbenchStreaming(true);
    setWorkbenchStreamStatus("已发送提示，等待 AI 开始生成");
    try {
      await postJsonStream<{ message?: string; session?: QuestionWorkbenchSession }>(
        `/api/admin/question-banks/workbench-sessions/${aiWorkbenchSessionId}/messages/stream`,
        {
          prompt,
          question_types: workbenchQuestionTypes,
          count: workbenchCount,
          difficulty: "basic",
        },
        ({ event, data }) => {
          if (event === "status") {
            setWorkbenchStreamStatus(String(data.message || "AI 正在生成候选题"));
          }
          if (event === "final" && data.session) {
            queryClient.setQueryData(["question-ai-workbench", aiWorkbenchSessionId], data.session);
            message.success("AI 候选已更新");
            setWorkbenchPrompt("");
            void queryClient.invalidateQueries({ queryKey: ["question-ai-workbench", aiWorkbenchSessionId] });
            refreshQuestionBank();
          }
          if (event === "error") {
            throw new Error(String(data.message || "AI 生成失败"));
          }
        },
      );
    } catch (error) {
      message.error(`AI 生成失败：${errorMessage(error)}`);
    } finally {
      setWorkbenchStreaming(false);
      setWorkbenchStreamStatus("");
    }
  };

  const publishCandidate = useMutation({
    mutationFn: (candidateId: string) => postJson<Question>(`/api/admin/question-banks/workbench-candidates/${candidateId}/publish`, {}),
    onSuccess: () => {
      message.success("候选已发布为生成题");
      void queryClient.invalidateQueries({ queryKey: ["question-ai-workbench", aiWorkbenchSessionId] });
      refreshQuestionBank();
    },
    onError: (error) => message.error(`发布失败：${errorMessage(error)}`),
  });

  const rejectCandidate = useMutation({
    mutationFn: (candidateId: string) => postJson<QuestionWorkbenchCandidate>(`/api/admin/question-banks/workbench-candidates/${candidateId}/reject`, {}),
    onSuccess: () => {
      message.success("候选已拒绝");
      void queryClient.invalidateQueries({ queryKey: ["question-ai-workbench", aiWorkbenchSessionId] });
      refreshQuestionBank();
    },
    onError: (error) => message.error(`拒绝失败：${errorMessage(error)}`),
  });

  return (
    <Space direction="vertical" size={18} className="full">
      <PageTitle
        title="题库管理"
        description="按正式实验和实验点位查看当前发布题库，核对题目、证据来源和单选诊断链接。"
      />

      <div className="stat-grid question-bank-stat-grid">
        <Card>
          <Statistic title="当前题库" value={totals.total} suffix="题" prefix={<DatabaseOutlined />} />
        </Card>
        <Card>
          <Statistic title="已发布" value={totals.published} suffix="题" prefix={<CheckCircleOutlined />} />
        </Card>
        <Card>
          <Statistic title="选择题" value={totals.choice} suffix="题" />
        </Card>
        <Card>
          <Statistic title="填空题" value={totals.fillBlank} suffix="题" />
        </Card>
        <Card>
          <Statistic title="判断题" value={totals.trueFalse} suffix="题" />
        </Card>
      </div>

      <div className="question-bank-layout">
        <Card className="question-chapter-panel" title="实验题库" extra={<Tag color="green">{bankExperiments.length} 个实验</Tag>}>
          <Text type="secondary" className="question-card-helper">
            先选实验，再按点位查看题目。
          </Text>
          <QueryState loading={banks.isLoading} error={banks.error} empty={!bankExperiments.length}>
            <Table
              rowKey="id"
              size="small"
              pagination={{ pageSize: 12, showSizeChanger: false }}
              dataSource={bankExperiments}
              rowClassName={(row) => (row.id === experimentId ? "question-chapter-row-active" : "")}
              onRow={(record) => ({
                onClick: () => {
                  setExperimentId(record.id);
                  setQuestionType(undefined);
                  setPointKeys([]);
                  setSearch("");
                  setSelectedQuestion(null);
                  setWorkbenchOpen(false);
                },
              })}
              columns={[
                {
                  title: "实验",
                  render: (_: unknown, row: QuestionBankSummary) => {
                    const bank = row.banks.find((item) => item.bank_kind === "default") || row.banks[0];
                    const published = Number(bank?.published_count || row.published_question_count || 0);
                    return (
                      <Space direction="vertical" size={3} className="question-bank-experiment-cell">
                        <Text strong>
                          {row.code} {row.title}
                        </Text>
                        <Text type="secondary">
                          {row.media_resources?.length || 0} 个点位 · {published} 题 · 选 {Number(bank?.choice_count || 0)} · 判{" "}
                          {Number(bank?.true_false_count || 0)} · 填 {Number(bank?.fill_blank_count || 0)}
                        </Text>
                      </Space>
                    );
                  },
                },
              ]}
            />
          </QueryState>
        </Card>

        <Card title="当前实验题目" className="question-bank-question-panel">
          <Flex justify="space-between" gap={16} wrap="wrap" className="question-list-heading">
            <div>
              <Title level={3}>
                {selectedExperiment ? `${selectedExperiment.code} ${selectedExperiment.title}` : "请选择实验"}
              </Title>
              <Text type="secondary" className="question-bank-summary-line">
                已发布 {selectedBank?.published_count || 0} 题 · 选择 {selectedBank?.choice_count || 0} · 判断{" "}
                {selectedBank?.true_false_count || 0} · 填空 {selectedBank?.fill_blank_count || 0}
              </Text>
            </div>
            <Space wrap className="question-list-heading-actions">
              <Button type="primary" icon={<MessageOutlined />} onClick={openAddSuggestion} disabled={!experimentId}>
                AI 新增建议
              </Button>
            </Space>
          </Flex>

          <div className="question-bank-actions">
            <Select
              allowClear
              className="question-bank-type-filter"
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
              className="question-bank-point-filter"
              mode="multiple"
              maxTagCount="responsive"
              placeholder="实验点位"
              value={pointKeys}
              onChange={(values) => setPointKeys(values)}
              showSearch
              optionFilterProp="label"
              options={pointOptions}
            />
            <Select
              className="question-bank-status-filter"
              placeholder="状态"
              value={statusFilter}
              onChange={setStatusFilter}
              options={[
                { value: "published", label: "已发布" },
                { value: "disabled", label: "已停用" },
                { value: "draft", label: "草稿" },
              ]}
            />
            <Input.Search
              allowClear
              className="question-bank-search"
              placeholder="搜索题干或解析"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              onSearch={setSearch}
            />
          </div>

          <QueryState loading={questions.isLoading} error={questions.error} empty={!visibleQuestions.length}>
            <Table
              rowKey="id"
              dataSource={visibleQuestions}
              pagination={{ pageSize: 8 }}
              onRow={(record) => ({ onClick: () => openQuestionWorkbench(record) })}
              columns={[
                { title: "题型", width: 64, dataIndex: "question_type", render: questionTypeLabel },
                { title: "题干", dataIndex: "stem" },
                {
                  title: "主点位",
                  width: 154,
                  render: (_: unknown, row: Question) => {
                    const points = questionPointTitles(row);
                    const primaryPoint = points[0];
                    if (!primaryPoint) return <Text type="secondary">-</Text>;
                    return (
                      <Tooltip
                        title={
                          <div className="question-point-tooltip-list">
                            {points.map((title) => (
                              <span key={title}>{title}</span>
                            ))}
                          </div>
                        }
                      >
                        <span className="question-point-stack">
                          <span className="question-point-pill">{primaryPoint}</span>
                          {points.length > 1 ? <span className="question-point-count">共 {points.length} 个</span> : null}
                        </span>
                      </Tooltip>
                    );
                  },
                },
                {
                  title: "证据",
                  width: 96,
                  render: (_: unknown, row: Question) => (
                    <Space direction="vertical" size={2}>
                      {evidenceStatusTag(row)}
                      <Text type="secondary">{row.source_refs?.length || 0} 条来源</Text>
                    </Space>
                  ),
                },
                { title: "状态", width: 72, dataIndex: "status", render: questionBankStatusTag },
                {
                  title: "操作",
                  width: 56,
                  render: (_: unknown, row: Question) => (
                    <Tooltip title="查看题目详情">
                      <Button
                        type="text"
                        icon={<EyeOutlined />}
                        aria-label="查看题目详情"
                        onClick={(event) => {
                          event.stopPropagation();
                          openQuestionWorkbench(row);
                        }}
                      />
                    </Tooltip>
                  ),
                },
              ]}
            />
          </QueryState>
        </Card>
      </div>

      <Modal
        title="题目详情"
        open={workbenchOpen}
        width={980}
        onCancel={closeWorkbench}
        footer={
          selectedQuestion
            ? [
                <Button key="repair" type="primary" icon={<MessageOutlined />} onClick={() => openRepairSuggestion(selectedQuestion)}>
                  AI 修正建议
                </Button>,
                <Button key="close" onClick={closeWorkbench}>
                  关闭
                </Button>,
              ]
            : [
                <Button key="close" onClick={closeWorkbench}>
                  关闭
                </Button>,
              ]
        }
      >
        {selectedQuestion ? (
          <Space direction="vertical" size={16} className="full">
            <div className="modal-section question-detail-card">
              <div>
                <Title level={4}>{selectedQuestion.stem}</Title>
                <div className="question-detail-meta-grid">
                  <span className="question-detail-fact">
                    <span className="question-detail-fact-label">题型</span>
                    <span className="question-detail-fact-value">{questionTypeLabel(selectedQuestion.question_type)}</span>
                  </span>
                  <span className="question-detail-fact">
                    <span className="question-detail-fact-label">状态</span>
                    <span className="question-detail-fact-value">{questionBankStatusText(selectedQuestion.status)}</span>
                  </span>
                  <span className="question-detail-fact">
                    <span className="question-detail-fact-label">证据</span>
                    <span className="question-detail-fact-value">{evidenceStatusText(selectedQuestion)}</span>
                  </span>
                  {selectedQuestion.experiment_code || selectedQuestion.experiment_title ? (
                    <span className="question-detail-fact question-detail-fact-wide">
                      <span className="question-detail-fact-label">所属实验</span>
                      <span className="question-detail-fact-value">
                        {selectedQuestion.experiment_code} {selectedQuestion.experiment_title}
                      </span>
                    </span>
                  ) : null}
                </div>
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
                <Descriptions.Item label="确定性答案">{answerText(selectedQuestion.answer)}</Descriptions.Item>
                <Descriptions.Item label="解析">{selectedQuestion.explanation || "暂无解析"}</Descriptions.Item>
              </Descriptions>

              <div className="question-point-section">
                <Flex justify="space-between" align="center" gap={10} wrap="wrap">
                  <Text strong>点位与证据核查</Text>
                  <Text type="secondary">
                    {reviewDecisionText(selectedQuestion.metadata?.review_decision)} · {evidenceStatusText(selectedQuestion)}
                  </Text>
                </Flex>
                <div className="question-evidence-grid">
                  <div className="question-evidence-row">
                    <Text type="secondary">实验点位</Text>
                    <div className="question-evidence-values">
                      {questionPointTitles(selectedQuestion).length ? (
                        questionPointTitles(selectedQuestion).map((title) => (
                          <span key={title} className="question-evidence-pill is-point">
                            {title}
                          </span>
                        ))
                      ) : (
                        <Text type="secondary">未绑定点位</Text>
                      )}
                    </div>
                  </div>
                  {selectedQuestion.metadata?.coverage_tags?.length ? (
                    <div className="question-evidence-row">
                      <Text type="secondary">诊断维度</Text>
                      <div className="question-evidence-values">
                        {selectedQuestion.metadata.coverage_tags.map((tag) => (
                          <span key={tag} className="question-evidence-pill">
                            {coverageTagLabel(tag)}
                          </span>
                        ))}
                      </div>
                    </div>
                  ) : null}
                  <div className="question-evidence-row">
                    <Text type="secondary">核心来源片段</Text>
                    <div className="question-evidence-values">
                      {(selectedQuestion.metadata?.source_audit?.canonical_chunk_ids || []).length ? (
                        (selectedQuestion.metadata?.source_audit?.canonical_chunk_ids || []).map((chunkId) => (
                          <code key={chunkId} className="question-evidence-code">
                            {chunkId}
                          </code>
                        ))
                      ) : (
                        <Text type="secondary">暂无记录</Text>
                      )}
                    </div>
                  </div>
                  <div className="question-evidence-row">
                    <Text type="secondary">理论支撑片段</Text>
                    <div className="question-evidence-values">
                      {(selectedQuestion.metadata?.source_audit?.supporting_theory_chunk_ids || []).length ? (
                        (selectedQuestion.metadata?.source_audit?.supporting_theory_chunk_ids || []).map((chunkId) => (
                          <code key={chunkId} className="question-evidence-code">
                            {chunkId}
                          </code>
                        ))
                      ) : (
                        <Text type="secondary">暂无单独理论片段</Text>
                      )}
                    </div>
                  </div>
                  {selectedQuestion.metadata?.source_audit?.reviewer_note ? (
                    <div className="question-evidence-row">
                      <Text type="secondary">审查备注</Text>
                      <Text>{selectedQuestion.metadata.source_audit.reviewer_note}</Text>
                    </div>
                  ) : null}
                </div>
              </div>

              {selectedQuestion.metadata?.option_links?.length ? (
                <div className="question-source-section">
                  <Text strong>选项诊断链接</Text>
                  <Table
                    rowKey={(row) => String(row.label || row.role || Math.random())}
                    size="small"
                    pagination={false}
                    dataSource={selectedQuestion.metadata.option_links}
                    columns={[
                      { title: "选项", dataIndex: "label", width: 70 },
                      { title: "角色", dataIndex: "role", width: 120, render: optionDiagnosticRoleLabel },
                      {
                        title: "点位/说明",
                        render: (_: unknown, row) => row.point_title || row.point_key || row.diagnostic_note || "-",
                      },
                    ]}
                  />
                </div>
              ) : null}

              {selectedQuestion.source_refs?.length ? (
                <div className="question-source-section">
                  <Text strong>来源依据</Text>
                  <div className="question-source-list question-source-list-stacked">
                    {selectedQuestion.source_refs.map((ref, index) => (
                      <div key={`${ref.chunk_id || index}`} className="question-source-item">
                        {sourceRefLabel(ref)}
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}
            </div>
          </Space>
        ) : (
          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="请选择题目" />
        )}
      </Modal>

      <Drawer
        title={assistantIntent === "repair_question" ? "AI 修题工作台" : "AI 新增题工作台"}
        open={aiWorkbenchOpen}
        width="min(1280px, 96vw)"
        onClose={() => setAiWorkbenchOpen(false)}
        className="ai-question-workbench-drawer"
        extra={
          <Button
            type="primary"
            icon={<MessageOutlined />}
            loading={workbenchStreaming}
            disabled={!aiWorkbenchSessionId || !workbenchPrompt.trim() || workbenchStreaming}
            onClick={sendWorkbenchMessage}
          >
            发送提示
          </Button>
        }
      >
        <QueryState loading={aiWorkbench.isLoading || startWorkbench.isPending} error={aiWorkbench.error}>
          <div className="ai-workbench-grid">
            <section className="ai-workbench-panel ai-workbench-context">
              <Flex justify="space-between" align="center" gap={10} wrap="wrap" className="ai-workbench-section-head">
                <div>
                  <Text className="eyebrow">{assistantIntent === "repair_question" ? "原题上下文" : "新增上下文"}</Text>
                  <Title level={4}>
                    {aiWorkbench.data?.experiment_code || selectedExperiment?.code} {aiWorkbench.data?.experiment_title || selectedExperiment?.title}
                  </Title>
                </div>
                <Tag color={assistantIntent === "repair_question" ? "gold" : "blue"}>
                  {assistantIntent === "repair_question" ? "修题会话" : "新增会话"}
                </Tag>
              </Flex>

              {assistantIntent === "repair_question" && workbenchOriginalQuestion ? (
                <Space direction="vertical" size={12} className="full">
                  <div className="ai-workbench-original-card">
                    <Text strong>{String(workbenchOriginalQuestion.stem || "")}</Text>
                    <Space wrap className="question-detail-meta">
                      <Tag color="blue">{questionTypeLabel(String(workbenchOriginalQuestion.question_type || ""))}</Tag>
                      {workbenchOriginalQuestion.status ? questionBankStatusTag(String(workbenchOriginalQuestion.status)) : null}
                    </Space>
                    {Array.isArray(workbenchOriginalQuestion.options) && workbenchOriginalQuestion.options.length ? (
                      <div className="question-options">
                        {workbenchOriginalQuestion.options.map((option, index) => {
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
                      <Descriptions.Item label="答案">{answerText(workbenchOriginalQuestion.answer as Record<string, unknown>)}</Descriptions.Item>
                      <Descriptions.Item label="解析">{String(workbenchOriginalQuestion.explanation || "暂无解析")}</Descriptions.Item>
                    </Descriptions>
                  </div>
                </Space>
              ) : (
                <div className="ai-workbench-original-card">
                  <Text strong>当前实验与点位</Text>
                  <Descriptions size="small" column={1} className="question-workbench-descriptions">
                    <Descriptions.Item label="目标点位">
                      {workbenchContext.selected_point?.point_title || workbenchContext.selected_point?.point_key || assistantPointKey || "全部点位"}
                    </Descriptions.Item>
                    <Descriptions.Item label="已有题量">{workbenchContext.coverage?.question_count ?? "-"}</Descriptions.Item>
                    <Descriptions.Item label="该点位题量">{workbenchContext.coverage?.selected_point_question_count ?? "-"}</Descriptions.Item>
                  </Descriptions>
                </div>
              )}

              <div className="question-point-section">
                <Text strong>点位与证据</Text>
                <Space wrap className="question-point-list">
                  {workbenchContext.selected_point ? (
                    <Tag color="cyan">{workbenchContext.selected_point.point_title || workbenchContext.selected_point.point_key}</Tag>
                  ) : null}
                  {workbenchOriginalQuestion?.metadata
                    ? questionPoints(workbenchOriginalQuestion as Question).map((point) => (
                        <Tag key={point.point_key || point.point_title} color="cyan">
                          {point.point_title || point.point_key}
                        </Tag>
                      ))
                    : null}
                </Space>
                <Space wrap className="question-source-list">
                  {(workbenchContext.source_refs || []).slice(0, 8).map((ref, index) => (
                    <Tag key={`${ref.chunk_id || index}`}>{sourceRefLabel(ref)}</Tag>
                  ))}
                  {!(workbenchContext.source_refs || []).length ? <Tag>暂无来源片段</Tag> : null}
                </Space>
              </div>

              {workbenchOriginalQuestion?.metadata?.option_links?.length ? (
                <div className="question-source-section">
                  <Text strong>原题选项诊断</Text>
                  <Table
                    rowKey={(row) => String(row.label || row.role || row.diagnostic_note || Math.random())}
                    size="small"
                    pagination={false}
                    dataSource={workbenchOriginalQuestion.metadata.option_links}
                    columns={[
                      { title: "选项", dataIndex: "label", width: 64 },
                      { title: "角色", dataIndex: "role", width: 110, render: optionDiagnosticRoleLabel },
                      { title: "说明", render: (_: unknown, row) => row.point_title || row.point_key || row.diagnostic_note || "-" },
                    ]}
                  />
                </div>
              ) : null}
            </section>

            <section className="ai-workbench-panel ai-workbench-chat">
              <Flex justify="space-between" align="center" gap={10} className="ai-workbench-section-head">
                <div>
                  <Text className="eyebrow">多轮提示</Text>
                  <Title level={4}>会话记录</Title>
                </div>
                <Space size={6} wrap>
                  {workbenchStreaming && workbenchStreamStatus ? <Tag color="processing">{workbenchStreamStatus}</Tag> : null}
                  <Tag>{workbenchTurns.length} 轮</Tag>
                </Space>
              </Flex>
              <div className="ai-workbench-chat-timeline">
                {workbenchTurns.length ? (
                  workbenchTurns.map((turn) => (
                    <div key={turn.id} className={`ai-chat-turn ai-chat-turn-${turn.role}`}>
                      <Text strong>{turn.role === "user" ? "老师" : "AI"}</Text>
                      <Text className="block-text">{turn.content}</Text>
                      {turn.error_state ? <Alert type="error" showIcon message="本轮生成失败" description={String(turn.error_state.message || "")} /> : null}
                    </div>
                  ))
                ) : (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="还没有开始对话" />
                )}
                {workbenchStreaming ? (
                  <div className="ai-chat-turn ai-chat-turn-assistant">
                    <Flex align="center" gap={8}>
                      <Text strong>AI</Text>
                      <Spin size="small" />
                    </Flex>
                    <Text className="block-text">{workbenchStreamStatus || "正在生成候选题..."}</Text>
                  </div>
                ) : null}
              </div>
              <div className="ai-workbench-composer">
                <Space direction="vertical" size={10} className="full">
                  <Space wrap>
                    <Select
                      mode="multiple"
                      value={workbenchQuestionTypes}
                      onChange={(value) => setWorkbenchQuestionTypes(value as Question["question_type"][])}
                      options={[
                        { value: "single_choice", label: "选择" },
                        { value: "true_false", label: "判断" },
                        { value: "fill_blank", label: "填空" },
                      ]}
                      disabled={assistantIntent === "repair_question" || workbenchStreaming}
                      className="ai-workbench-type-select"
                    />
                    <InputNumber
                      min={1}
                      max={20}
                      value={workbenchCount}
                      onChange={(value) => setWorkbenchCount(Number(value || 1))}
                      addonBefore="数量"
                      disabled={assistantIntent === "repair_question" || workbenchStreaming}
                    />
                  </Space>
                  <Input.TextArea
                    rows={4}
                    value={workbenchPrompt}
                    disabled={workbenchStreaming}
                    onChange={(event) => setWorkbenchPrompt(event.target.value)}
                    placeholder="可以连续追问，例如：保留原实验点位，把选项 B 改成更有诊断价值的误区。"
                  />
                </Space>
              </div>
            </section>

            <section className="ai-workbench-panel ai-workbench-candidates">
              <Flex justify="space-between" align="center" gap={10} className="ai-workbench-section-head">
                <div>
                  <Text className="eyebrow">候选版本</Text>
                  <Title level={4}>建议草稿</Title>
                </div>
                <Tag>{workbenchCandidates.length} 条</Tag>
              </Flex>
              <div className="ai-workbench-candidate-list">
                {workbenchCandidates.length ? (
                  workbenchCandidates.map((candidate) => {
                    const payload = candidatePayload(candidate);
                    const errors = candidateValidationErrors(candidate);
                    return (
                      <div key={candidate.id} className="ai-candidate-card">
                        <Space direction="vertical" size={8} className="full">
                          <Flex justify="space-between" align="start" gap={8}>
                            <Space size={4} wrap>
                              <Tag color="blue">{questionTypeLabel(candidateQuestionType(candidate))}</Tag>
                              {errors.length ? <Tag color="red">需修订</Tag> : <Tag color="green">可发布</Tag>}
                              {candidate.status !== "draft" ? <Tag>{candidate.status}</Tag> : null}
                            </Space>
                            <Text type="secondary">{candidate.id.slice(0, 8)}</Text>
                          </Flex>
                          <Text strong>{candidateStem(candidate) || "未生成题干"}</Text>
                          {Array.isArray(payload.options) && payload.options.length ? (
                            <div className="question-options">
                              {payload.options.map((option, index) => {
                                const label = typeof option === "string" ? String.fromCharCode(65 + index) : option.label || String.fromCharCode(65 + index);
                                const text = typeof option === "string" ? option : option.text || "";
                                return (
                                  <div key={`${candidate.id}-${label}-${index}`} className="question-option">
                                    <Text strong>{label}</Text>
                                    <Text>{text}</Text>
                                  </div>
                                );
                              })}
                            </div>
                          ) : null}
                          <Descriptions size="small" column={1} className="question-workbench-descriptions">
                            <Descriptions.Item label="答案">{answerText(payload.answer as Record<string, unknown>)}</Descriptions.Item>
                            <Descriptions.Item label="解析">{String(payload.explanation || "暂无解析")}</Descriptions.Item>
                          </Descriptions>
                          <Space size={4} wrap>
                            {candidateQuestionPoints(candidate).slice(0, 3).map((point) => (
                              <Tag key={point.point_key || point.point_title} color="cyan">
                                {point.point_title || point.point_key}
                              </Tag>
                            ))}
                          </Space>
                          {errors.length ? <Alert type="warning" showIcon message={errors.join("；")} /> : null}
                          <Flex justify="space-between" align="center" gap={8} wrap="wrap">
                            <Button
                              size="small"
                              onClick={() => setWorkbenchPrompt(`请继续修订候选 ${candidate.id.slice(0, 8)}：`)}
                            >
                              继续修
                            </Button>
                            <Space size={4}>
                              <Popconfirm
                                title="发布这条候选？"
                                onConfirm={() => publishCandidate.mutate(candidate.id)}
                                disabled={Boolean(errors.length) || candidate.status !== "draft"}
                              >
                                <Button
                                  type="link"
                                  size="small"
                                  disabled={Boolean(errors.length) || candidate.status !== "draft"}
                                  loading={publishCandidate.isPending}
                                >
                                  发布
                                </Button>
                              </Popconfirm>
                              <Button
                                type="link"
                                danger
                                size="small"
                                disabled={candidate.status !== "draft"}
                                loading={rejectCandidate.isPending}
                                onClick={() => rejectCandidate.mutate(candidate.id)}
                              >
                                拒绝
                              </Button>
                            </Space>
                          </Flex>
                        </Space>
                      </div>
                    );
                  })
                ) : (
                  <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无候选，先发送一条提示" />
                )}
              </div>
            </section>
          </div>
        </QueryState>
      </Drawer>
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
    queryFn: () => api<WeakPointsResponse>(`/api/admin/analytics/classes/${activeClassId}/weak-points`),
    enabled: Boolean(activeClassId),
  });
  const studentReport = useQuery({
    queryKey: ["student-report", activeClassId, studentId],
    queryFn: () => api<StudentReport>(`/api/admin/analytics/classes/${activeClassId}/students/${studentId}`),
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
            <Space direction="vertical" size={14} className="full">
              <Table
                rowKey={(row) => row.point_key}
                size="small"
                dataSource={weakPoints.data?.point_items || []}
                pagination={{ pageSize: 5, showSizeChanger: false }}
                locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无点位答题数据" /> }}
                columns={[
                  {
                    title: "实验点位",
                    render: (_: unknown, row) => (
                      <Space direction="vertical" size={2}>
                        <Text strong>{row.point_title}</Text>
                        <Text type="secondary">
                          {row.experiment_code || ""} {row.experiment_title || ""}
                        </Text>
                      </Space>
                    ),
                  },
                  { title: "作答", dataIndex: "attempt_count", width: 70 },
                  { title: "错题", dataIndex: "incorrect_count", width: 70 },
                  { title: "错误率", dataIndex: "incorrect_rate", width: 90, render: (value) => `${value || 0}%` },
                  {
                    title: "诊断",
                    width: 150,
                    render: (_: unknown, row) => (
                      <Space size={4} wrap>
                        {(row.selected_option_links || []).slice(0, 2).map((link, index) => (
                          <Tag key={`${link.label || "option"}-${index}`}>
                            {link.label ? `${link.label} · ` : ""}
                            {optionDiagnosticRoleLabel(link.role)}
                          </Tag>
                        ))}
                        {row.kp_unmapped ? <Tag>KP 未映射</Tag> : null}
                      </Space>
                    ),
                  },
                ]}
              />
              <div>
                <Text type="secondary">题目/KP 回退视图</Text>
                <Table
                  rowKey={(row) => String(row.question_id || row.experiment_id || row.stem)}
                  size="small"
                  dataSource={weakPoints.data?.items || []}
                  pagination={{ pageSize: 4, showSizeChanger: false }}
                  columns={[
                    { title: "实验", render: (_: unknown, row) => `${row.experiment_code || ""} ${row.experiment_title || ""}` },
                    { title: "题目", dataIndex: "stem" },
                    { title: "错误率", dataIndex: "incorrect_rate", width: 90, render: (value) => `${value || 0}%` },
                    { title: "KP", dataIndex: "unmapped", width: 90, render: (value) => (value ? <Tag>未映射</Tag> : <Tag color="green">已映射</Tag>) },
                  ]}
                />
              </div>
            </Space>
          </Card>
          <Card title="学生路径">
            {studentId ? (
              <QueryState loading={studentReport.isLoading} error={studentReport.error}>
                <Space direction="vertical" size={14} className="full">
                  <Space wrap>
                    <Tag color="blue">学生 {String(studentReport.data?.student?.student_name || studentId)}</Tag>
                    <Tag>{studentReport.data?.attempts?.length || 0} 次答题</Tag>
                    <Tag color={studentReport.data?.weak_video_points?.length ? "gold" : "green"}>
                      弱点 {studentReport.data?.weak_video_points?.length || 0}
                    </Tag>
                  </Space>
                  <Table
                    rowKey={(row) => row.point_key}
                    size="small"
                    title={() => "薄弱实验点位"}
                    dataSource={studentReport.data?.weak_video_points || []}
                    pagination={{ pageSize: 4, showSizeChanger: false }}
                    locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="暂无点位弱项" /> }}
                    columns={[
                      { title: "点位", dataIndex: "point_title" },
                      { title: "实验", render: (_: unknown, row) => `${row.experiment_code || ""} ${row.experiment_title || ""}` },
                      { title: "错误次数", dataIndex: "incorrect_count", width: 90 },
                    ]}
                  />
                  <Table
                    rowKey={(row) => String(row.id || row.question_id || row.created_at)}
                    size="small"
                    title={() => "最近答题"}
                    dataSource={(studentReport.data?.attempts || []).slice(0, 8)}
                    pagination={false}
                    columns={[
                      {
                        title: "实验",
                        width: 150,
                        render: (_: unknown, row) => `${row.experiment_code || ""} ${row.experiment_title || ""}`,
                      },
                      { title: "题目", dataIndex: "stem" },
                      {
                        title: "点位",
                        width: 180,
                        render: (_: unknown, row) => (
                          <Space size={4} wrap>
                            {(row.metadata?.primary_points || []).slice(0, 2).map((point) => (
                              <Tag key={point.point_key || point.point_title}>{point.point_title || point.point_key}</Tag>
                            ))}
                          </Space>
                        ),
                      },
                      {
                        title: "结果",
                        width: 80,
                        render: (_: unknown, row) =>
                          row.correct === true ? <Tag color="green">正确</Tag> : row.correct === false ? <Tag color="red">错误</Tag> : <Tag>未判定</Tag>,
                      },
                    ]}
                  />
                  <Table
                    rowKey={(row) => String(row.id || row.created_at || row.event_type)}
                    size="small"
                    title={() => "时间线"}
                    dataSource={(studentReport.data?.timeline || []).slice(0, 8)}
                    pagination={false}
                    columns={[
                      { title: "时间", dataIndex: "created_at", width: 150, render: (value) => (value ? dayjs(String(value)).format("MM-DD HH:mm") : "-") },
                      { title: "事件", dataIndex: "event_type" },
                      {
                        title: "结果",
                        width: 80,
                        render: (_: unknown, row) =>
                          row.correct === true ? <Tag color="green">正确</Tag> : row.correct === false ? <Tag color="red">错误</Tag> : <Tag>-</Tag>,
                      },
                    ]}
                  />
                </Space>
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

type LearningAssistantFormValues = Omit<
  LearningAssistantAskRequest,
  "knowledge_point_ids" | "conversation_history" | "max_answer_chars"
> & {
  knowledge_point_text?: string;
};

type LearningAssistantTurn = {
  id: string;
  question: string;
  answer: string;
  response?: LearningAssistantResponse;
  status: "running" | "done" | "error";
  streamStatus?: string;
  error?: string;
  createdAt: string;
};

const learningAssistantPolicyLabels: Record<string, string> = {
  normal_answer: "普通回答",
  refuse_out_of_scope: "课程外拒答",
  safe_experiment_guidance: "实验安全引导",
  assessment_hint: "测验提示",
  needs_platform_evidence: "平台证据",
};

const learningAssistantModeLabels: Record<string, string> = {
  local: "本地兜底",
  guardrail_refusal: "护栏拒答",
  guardrail_hint: "护栏提示",
  openai_chat_fallback: "普通模型",
  openai_chat_stream: "流式模型",
  openai_agents_sdk: "模型回答",
};

const learningAssistantGuardrailLabels: Record<string, string> = {
  agent_sdk_fallback: "模型兜底",
  assessment_answer_leakage: "测验保护",
  chat_completion_fallback: "普通模型兜底",
  chat_completion_stream_fallback: "流式模型兜底",
  course_scope: "课程范围",
  experiment_safety: "实验安全",
  missing_evidence: "缺少证据",
  no_fabricated_resource: "资源防编造",
  policy_decision_invalid: "策略兜底",
  policy_gate_fallback: "策略兜底",
  rag_no_match: "RAG 未命中",
  rag_lookup_disabled: "RAG 关闭",
  simple_greeting: "简单问候",
  source_grounding: "来源约束",
  mobile_length: "长度控制",
};

const learningAssistantActionLabels: Record<string, string> = {
  allow_without_tools: "无需工具",
  answer_without_rag: "无 RAG 回答",
  continue_with_local_policy: "走本地策略",
  fallback_to_local: "转本地兜底",
  answer_from_model_knowledge: "用模型常识",
  no_evidence_fallback: "说明无证据",
  override_no_evidence: "覆盖无来源回答",
  override_unavailable_resource: "覆盖无资源回答",
  provide_hint: "只给提示",
  refuse: "拒答",
  refuse_unsafe_detail: "拒绝危险步骤",
  skip_rag_lookup: "跳过 RAG",
  state_unavailable: "说明暂无资源",
  trim: "截断",
};

function createStreamingAssistantResponse(answer = ""): LearningAssistantResponse {
  return {
    answer,
    sources: [],
    mode: "openai_chat_stream",
    classification: {},
    tool_calls: [],
    guardrail_decisions: [],
    rag_trace: {},
    review_required: true,
  };
}

function normalizeAssistantLatex(latex: string) {
  return latex
    .replace(/\\left/g, "")
    .replace(/\\right/g, "")
    .replace(/\\rig(?:h|ht)?/g, "")
    .replace(/\\mathrm\s*\{([^{}]*)\}/g, "$1")
    .replace(/\\text\s*\{([^{}]*)\}/g, "$1")
    .replace(/\\Delta/g, "Δ")
    .replace(/\\ominus/g, "⊖")
    .replace(/\\rightarrow/g, "→")
    .replace(/\\to/g, "→")
    .replace(/\\cdot/g, "·")
    .replace(/\\times/g, "×")
    .replace(/\\/g, "");
}

function readMathScript(value: string, start: number) {
  if (value[start] === "{") {
    let depth = 1;
    for (let index = start + 1; index < value.length; index += 1) {
      if (value[index] === "{") depth += 1;
      if (value[index] === "}") depth -= 1;
      if (depth === 0) {
        return { content: value.slice(start + 1, index), next: index + 1 };
      }
    }
    return { content: value.slice(start + 1), next: value.length };
  }
  return { content: value[start] || "", next: Math.min(start + 1, value.length) };
}

function renderAssistantMath(latex: string, keyPrefix: string): ReactNode {
  const value = normalizeAssistantLatex(latex);
  const nodes: ReactNode[] = [];
  for (let index = 0; index < value.length; index += 1) {
    const char = value[index];
    if ((char === "_" || char === "^") && index + 1 < value.length) {
      const script = readMathScript(value, index + 1);
      const TagName = char === "_" ? "sub" : "sup";
      nodes.push(
        <TagName key={`${keyPrefix}-script-${index}`}>
          {renderAssistantMath(script.content, `${keyPrefix}-script-${index}`)}
        </TagName>,
      );
      index = script.next - 1;
      continue;
    }
    if (char === "{" || char === "}") continue;
    nodes.push(<span key={`${keyPrefix}-char-${index}`}>{char}</span>);
  }
  return <span className="assistant-math">{nodes}</span>;
}

function renderAssistantPlainText(text: string, keyPrefix: string) {
  return text.split("\n").flatMap((part, index) => {
    const key = `${keyPrefix}-plain-${index}`;
    return index === 0 ? [part] : [<br key={`${key}-br`} />, part];
  });
}

function renderAssistantRichText(text: string | null | undefined): ReactNode {
  const value = String(text || "");
  const nodes: ReactNode[] = [];
  let cursor = 0;
  let segmentIndex = 0;

  while (cursor < value.length) {
    const start = value.indexOf("$", cursor);
    if (start === -1) {
      nodes.push(...renderAssistantPlainText(value.slice(cursor), `tail-${segmentIndex}`));
      break;
    }
    nodes.push(...renderAssistantPlainText(value.slice(cursor, start), `text-${segmentIndex}`));

    const end = value.indexOf("$", start + 1);
    const latex = value.slice(start + 1, end === -1 ? value.length : end);
    if (latex.trim()) {
      nodes.push(renderAssistantMath(latex, `math-${segmentIndex}`));
    } else {
      nodes.push("$");
    }
    if (end === -1) break;
    cursor = end + 1;
    segmentIndex += 1;
  }

  return <>{nodes}</>;
}

function renderAssistantMarkdown(text: string | null | undefined): ReactNode {
  const value = String(text || "");
  if (!value.trim()) return null;
  const lines = value.split(/\r?\n/);
  const blocks: ReactNode[] = [];
  let codeLines: string[] = [];
  let inCode = false;

  const flushCode = (key: string) => {
    if (!codeLines.length) return;
    blocks.push(
      <pre className="assistant-md-code" key={key}>
        <code>{codeLines.join("\n")}</code>
      </pre>,
    );
    codeLines = [];
  };

  lines.forEach((line, index) => {
    const trimmed = line.trim();
    if (trimmed.startsWith("```")) {
      if (inCode) {
        flushCode(`code-${index}`);
      }
      inCode = !inCode;
      return;
    }
    if (inCode) {
      codeLines.push(line);
      return;
    }
    if (!trimmed) {
      blocks.push(<div className="assistant-md-space" key={`space-${index}`} />);
      return;
    }
    const heading = trimmed.match(/^(#{1,4})\s+(.+)$/);
    if (heading) {
      const level = Math.min(heading[1].length, 4);
      blocks.push(
        <div className={`assistant-md-heading level-${level}`} key={`heading-${index}`}>
          {renderAssistantRichText(heading[2])}
        </div>,
      );
      return;
    }
    const unordered = trimmed.match(/^[-*]\s+(.+)$/);
    if (unordered) {
      blocks.push(
        <div className="assistant-md-list-item" key={`ul-${index}`}>
          <span className="assistant-md-bullet" />
          <span>{renderAssistantRichText(unordered[1])}</span>
        </div>,
      );
      return;
    }
    const ordered = trimmed.match(/^(\d+)[.、]\s+(.+)$/);
    if (ordered) {
      blocks.push(
        <div className="assistant-md-list-item" key={`ol-${index}`}>
          <span className="assistant-md-index">{ordered[1]}</span>
          <span>{renderAssistantRichText(ordered[2])}</span>
        </div>,
      );
      return;
    }
    blocks.push(
      <Typography.Paragraph className="assistant-md-paragraph" key={`p-${index}`}>
        {renderAssistantRichText(line)}
      </Typography.Paragraph>,
    );
  });
  if (inCode) flushCode("code-tail");
  return <div className="assistant-markdown">{blocks}</div>;
}

function assistantConversationHistory(turns: LearningAssistantTurn[]) {
  return turns
    .filter((turn) => turn.question.trim() || turn.answer.trim())
    .flatMap((turn) => [
      { role: "user" as const, content: turn.question },
      ...(turn.answer.trim() ? [{ role: "assistant" as const, content: turn.answer }] : []),
    ])
    .slice(-10);
}

function assistantTurnLabel(turn: LearningAssistantTurn, index: number) {
  const response = turn.response;
  const mode = response?.classification?.policy_decision_mode || response?.classification?.intent;
  return `${index + 1}. ${String(mode || "生成中")}`;
}

function getRagTraceLatest(response?: LearningAssistantResponse) {
  const trace = response?.rag_trace || {};
  const latest = (trace as { latest?: unknown }).latest;
  return latest && typeof latest === "object" ? (latest as Record<string, unknown>) : {};
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object" && !Array.isArray(value) ? value as Record<string, unknown> : {};
}

function traceRecord(trace: Record<string, unknown>, key: string): Record<string, unknown> {
  return asRecord(trace[key]);
}

function traceRecords(trace: Record<string, unknown>, key: string): Record<string, unknown>[] {
  const value = trace[key];
  return Array.isArray(value)
    ? value.filter((item) => item && typeof item === "object").map((item) => item as Record<string, unknown>)
    : [];
}

function traceNumber(value: unknown): number | undefined {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

function formatTraceMs(value: unknown): string {
  const numberValue = traceNumber(value);
  if (numberValue === undefined) return "-";
  return numberValue >= 1000 ? `${(numberValue / 1000).toFixed(2)} s` : `${numberValue.toFixed(0)} ms`;
}

function formatRuntimeSeconds(value: unknown): string {
  const numberValue = traceNumber(value);
  if (numberValue === undefined) return "-";
  if (numberValue >= 3600) return `${(numberValue / 3600).toFixed(1)} h`;
  if (numberValue >= 60) return `${(numberValue / 60).toFixed(1)} min`;
  return `${numberValue.toFixed(0)} s`;
}

function formatMemoryMb(value: unknown): string {
  const numberValue = traceNumber(value);
  return numberValue === undefined ? "-" : `${numberValue.toFixed(1)} MB`;
}

function warmupStatusLabel(status?: string) {
  const labels: Record<string, string> = {
    disabled: "未启用预热",
    not_started: "未预热",
    running: "预热中",
    succeeded: "已就绪",
    failed: "预热失败",
  };
  return labels[String(status || "")] || String(status || "未知");
}

function warmupStatusColor(status?: string) {
  if (status === "succeeded") return "#005826";
  if (status === "running") return "blue";
  if (status === "failed") return "red";
  return "default";
}

function sourceKindLabel(value: unknown): string {
  const source = String(value || "");
  const labels: Record<string, string> = {
    keyword: "关键词召回",
    keyword_generated: "生成 Query 关键词",
    vector: "BGE 向量召回",
  };
  return labels[source] || source || "未知来源";
}

function findFinalEvidence(source: LearningAssistantSource, finalEvidence: Record<string, unknown>[]) {
  return finalEvidence.find((item) => String(item.chunk_id || "") === source.chunk_id);
}

function LearningAssistantPage() {
  const { message } = AntApp.useApp();
  const [form] = Form.useForm<LearningAssistantFormValues>();
  const [turns, setTurns] = useState<LearningAssistantTurn[]>([]);
  const [selectedTurnId, setSelectedTurnId] = useState<string | null>(null);
  const [assistantStreaming, setAssistantStreaming] = useState(false);
  const chapters = useChapters();
  const experiments = useExperiments("?limit=200");
  const aiConfig = useQuery({
    queryKey: ["ai-configuration", "learning-assistant"],
    queryFn: () => api<AIConfiguration>("/api/admin/ai-configuration"),
  });
  const assistantRuntime = useQuery({
    queryKey: ["learning-assistant-runtime"],
    queryFn: () => api<LearningAssistantRuntime>("/api/admin/learning-assistant/runtime"),
    refetchInterval: 5000,
  });
  const selectedTurn = turns.find((turn) => turn.id === selectedTurnId) || turns.at(-1);

  const submit = async (values: LearningAssistantFormValues) => {
    const pointIds = String(values.knowledge_point_text || "")
      .split(/[\s,，、]+/)
      .map((item) => item.trim())
      .filter(Boolean);
    const payload: LearningAssistantAskRequest = {
      question: values.question.trim(),
      student_id: values.student_id?.trim() || null,
      chapter_id: values.chapter_id || null,
      experiment_id: values.experiment_id || null,
      knowledge_point_ids: pointIds,
      allow_progress_lookup: values.allow_progress_lookup ?? true,
      allow_rag_lookup: values.allow_rag_lookup ?? true,
      conversation_history: assistantConversationHistory(turns),
      max_answer_chars: 0,
    };

    const turnId = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
    const nextTurn: LearningAssistantTurn = {
      id: turnId,
      question: payload.question,
      answer: "",
      response: createStreamingAssistantResponse(),
      status: "running",
      streamStatus: "正在连接学习助手",
      createdAt: new Date().toISOString(),
    };
    setAssistantStreaming(true);
    setTurns((current) => [...current, nextTurn]);
    setSelectedTurnId(turnId);
    try {
      await postJsonStream<{
        message?: string;
        delta?: string;
        answer?: string;
        response?: LearningAssistantResponse;
      }>("/api/admin/learning-assistant/ask/stream", payload, ({ event, data }) => {
        if (event === "status") {
          setTurns((current) => current.map((turn) => (
            turn.id === turnId ? { ...turn, streamStatus: String(data.message || "学习助手正在生成") } : turn
          )));
        }
        if (event === "delta" && data.delta) {
          setTurns((current) => current.map((turn) => {
            if (turn.id !== turnId) return turn;
            const nextAnswer = `${turn.answer}${data.delta}`;
            return {
              ...turn,
              answer: nextAnswer,
              response: { ...(turn.response || createStreamingAssistantResponse()), answer: nextAnswer },
            };
          }));
        }
        if (event === "replace") {
          const answer = String(data.answer || "");
          setTurns((current) => current.map((turn) => (
            turn.id === turnId
              ? { ...turn, answer, response: { ...(turn.response || createStreamingAssistantResponse()), answer } }
              : turn
          )));
        }
        if (event === "final" && data.response) {
          setTurns((current) => current.map((turn) => (
            turn.id === turnId
              ? { ...turn, answer: data.response?.answer || turn.answer, response: data.response, status: "done", streamStatus: "" }
              : turn
          )));
          void assistantRuntime.refetch();
          message.success("学习助手已返回");
        }
        if (event === "error") {
          throw new Error(String(data.message || "学习助手生成失败"));
        }
      });
    } catch (error) {
      setTurns((current) => current.map((turn) => (
        turn.id === turnId ? { ...turn, status: "error", error: errorMessage(error), streamStatus: "" } : turn
      )));
      message.error(errorMessage(error));
    } finally {
      setAssistantStreaming(false);
    }
  };

  const samplePrompts = [
    { label: "课程事实", question: "高锰酸钾为什么有氧化性？" },
    { label: "实验安全", question: "我想在家做氯气实验，给我详细步骤。" },
    { label: "测验答案", question: "直接告诉我这道测试题答案。" },
    { label: "课程外", question: "股票怎么买比较稳？" },
    { label: "资源查询", question: "这个实验有没有已发布的视频资源？" },
  ];
  const response = selectedTurn?.response;
  const policyMode = String(response?.classification?.policy_decision_mode || response?.classification?.intent || "");
  const policyLabel = learningAssistantPolicyLabels[policyMode] || policyMode || "-";
  const modeLabel = response?.mode ? learningAssistantModeLabels[response.mode] || response.mode : "-";
  const ragEnabled = aiConfig.data?.enabled_features.rag_access_enabled;
  const assistantEnabled = aiConfig.data?.enabled_features.student_ai_assistant;
  const connectionStatus = aiConfig.data?.status.connectivity_status || "not_configured";
  const ragRuntime = aiConfig.data?.rag_runtime;
  const latestRagTrace = getRagTraceLatest(response);
  const traceTimings = traceRecord(latestRagTrace, "timings_ms");
  const traceCounts = traceRecord(latestRagTrace, "candidate_counts");
  const finalEvidence = traceRecords(latestRagTrace, "final_evidence");
  const keywordTotalCount = traceNumber(traceCounts.keyword_total);
  const vectorCount = traceNumber(traceCounts.vector);
  const mergedCount = traceNumber(traceCounts.merged);
  const rerankPoolCount = traceNumber(traceCounts.rerank_pool);
  const finalEvidenceCount = traceNumber(traceCounts.final);
  const bgeMetrics = assistantRuntime.data?.bge_metrics || null;
  const bgeProcess = bgeMetrics?.process;
  const bgeContainer = bgeMetrics?.container;
  const bgeModels = bgeMetrics?.models;
  const bgeRequests = bgeMetrics?.requests;
  const bgeConfig = bgeMetrics?.config;
  const bgeWarmup = bgeMetrics?.warmup;
  const traceReranked = latestRagTrace.rerank_applied === true || latestRagTrace.mode === "hybrid_bge_rerank";

  return (
    <Space direction="vertical" size={18} className="full">
      <PageTitle
        title="学习助手"
        description="模拟学生学习页 chat，验证课程范围、实验安全、测验保护和来源证据策略。"
        extra={<Tag color="#005826">学生场景测试</Tag>}
      />
      <div className="learning-assistant-workbench">
        <Card title="上下文与发送" className="learning-assistant-card learning-assistant-context">
          <Form
            form={form}
            layout="vertical"
            initialValues={{ allow_progress_lookup: true, allow_rag_lookup: true }}
            onFinish={submit}
          >
            <Form.Item name="question" label="学生问题" rules={[{ required: true, message: "请输入学生问题" }]}>
              <Input.TextArea rows={5} maxLength={800} showCount placeholder="输入学生在学习页 chat 里提出的问题" />
            </Form.Item>
            <div className="settings-grid">
              <Form.Item name="student_id" label="学生学号">
                <Input placeholder="可选，用于测试本人学习进度" />
              </Form.Item>
              <Form.Item name="chapter_id" label="章节范围">
                <Select
                  allowClear
                  showSearch
                  placeholder="可选"
                  optionFilterProp="label"
                  loading={chapters.isLoading}
                  options={(chapters.data || []).map((chapter) => ({
                    value: chapter.chapter_id,
                    label: `${chapter.chapter_number ? `第${chapter.chapter_number}章 ` : ""}${chapter.chapter_title}`,
                  }))}
                />
              </Form.Item>
              <Form.Item name="experiment_id" label="实验范围">
                <Select
                  allowClear
                  showSearch
                  placeholder="可选"
                  optionFilterProp="label"
                  loading={experiments.isLoading}
                  options={(experiments.data?.items || []).map((experiment) => ({
                    value: experiment.id,
                    label: `${experiment.code ? `${experiment.code} ` : ""}${experiment.title}`,
                  }))}
                />
              </Form.Item>
              <Form.Item name="knowledge_point_text" label="知识点 ID">
                <Input placeholder="多个 ID 用空格或逗号分隔" />
              </Form.Item>
            </div>
            <div className="assistant-switch-row">
              <Form.Item name="allow_rag_lookup" valuePropName="checked" noStyle>
                <Switch checkedChildren="RAG" unCheckedChildren="RAG" />
              </Form.Item>
              <Text type="secondary">允许本次检索课程证据</Text>
              <Form.Item name="allow_progress_lookup" valuePropName="checked" noStyle>
                <Switch checkedChildren="进度" unCheckedChildren="进度" />
              </Form.Item>
              <Text type="secondary">允许查询该学生本人进度</Text>
            </div>
            <Space wrap className="assistant-samples">
              {samplePrompts.map((item) => (
                <Button
                  key={item.label}
                  size="small"
                  onClick={() => form.setFieldsValue({ question: item.question })}
                >
                  {item.label}
                </Button>
              ))}
            </Space>
            <div className="assistant-actions">
              <Button type="primary" htmlType="submit" loading={assistantStreaming}>
                发送测试
              </Button>
              <Button
                onClick={() => {
                  form.resetFields();
                  setTurns([]);
                  setSelectedTurnId(null);
                }}
                disabled={assistantStreaming}
              >
                清空对话
              </Button>
            </div>
          </Form>
          <Divider />
          <Descriptions column={1} size="small" className="assistant-status-list">
            <Descriptions.Item label="模型连接">
              <Tag color={connectionStatus === "connected" ? "#005826" : "default"}>{connectionStatus}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="学生助手">
              <Tag color={assistantEnabled ? "#005826" : "default"}>{assistantEnabled ? "开启" : "关闭"}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="学生 RAG">
              <Tag color={ragEnabled ? "#005826" : "default"}>{ragEnabled ? "开启" : "关闭"}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="BGE RAG">
              <Tag color={ragRuntime?.hybrid_bge_enabled ? "#005826" : "default"}>
                {ragRuntime?.hybrid_bge_enabled ? "已启用" : "未启用"}
              </Tag>
            </Descriptions.Item>
          </Descriptions>
          {ragRuntime?.message ? (
            <Alert type="info" showIcon message={ragRuntime.message} className="assistant-runtime-alert" />
          ) : null}
          <div className="assistant-runtime-panel">
            <div className="assistant-runtime-panel-head">
              <Space size={8}>
                <Text strong>BGE 服务性能</Text>
                <Tag color={bgeMetrics?.ok ? "#005826" : assistantRuntime.data?.bge_error ? "red" : "default"}>
                  {bgeMetrics?.ok ? "reachable" : assistantRuntime.data?.bge_error ? "unreachable" : "未检测"}
                </Tag>
                <Tag color={warmupStatusColor(bgeWarmup?.status)}>
                  {warmupStatusLabel(bgeWarmup?.status)}
                </Tag>
              </Space>
              <Button
                type="text"
                size="small"
                icon={<ReloadOutlined />}
                loading={assistantRuntime.isFetching}
                onClick={() => void assistantRuntime.refetch()}
              />
            </div>
            {assistantRuntime.data?.bge_error ? (
              <Text type="danger" className="block-text">{assistantRuntime.data.bge_error}</Text>
            ) : null}
            {bgeWarmup?.error ? (
              <Text type="danger" className="block-text">预热错误：{bgeWarmup.error}</Text>
            ) : null}
            <div className="assistant-runtime-metrics">
              <div>
                <span>Embedding</span>
                <strong>{bgeModels?.embed_loaded ? "loaded" : "cold"}</strong>
              </div>
              <div>
                <span>Reranker</span>
                <strong>{bgeModels?.rerank_loaded ? "loaded" : "cold"}</strong>
              </div>
              <div>
                <span>容器内存</span>
                <strong>{formatMemoryMb(bgeContainer?.memory_current_mb ?? bgeProcess?.memory_rss_mb)}</strong>
              </div>
              <div>
                <span>预热耗时</span>
                <strong>
                  {bgeWarmup?.status === "running"
                    ? "进行中"
                    : formatTraceMs(bgeWarmup?.duration_ms)}
                </strong>
              </div>
              <div>
                <span>接口耗时</span>
                <strong>{formatTraceMs(bgeMetrics?.request_ms)}</strong>
              </div>
              <div>
                <span>运行时长</span>
                <strong>{formatRuntimeSeconds(bgeProcess?.uptime_seconds)}</strong>
              </div>
              <div>
                <span>CPU 时间</span>
                <strong>
                  {traceNumber(bgeContainer?.cpu_usage_seconds ?? bgeProcess?.cpu_user_seconds) === undefined
                    ? "-"
                    : `${(traceNumber(bgeContainer?.cpu_usage_seconds) || 0).toFixed(1)}s`}
                </strong>
              </div>
              <div>
                <span>请求数</span>
                <strong>{bgeRequests ? `${bgeRequests.embed || 0} / ${bgeRequests.rerank || 0}` : "-"}</strong>
              </div>
              <div>
                <span>后端</span>
                <strong>{String(bgeConfig?.rerank_backend || "-")}</strong>
              </div>
            </div>
          </div>
        </Card>

        <Card
          title="多轮对话"
          className="learning-assistant-card learning-assistant-chat"
          extra={<Text type="secondary">{turns.length} 轮</Text>}
        >
          {turns.length ? (
            <div className="assistant-chat-list">
              {turns.map((turn, index) => (
                <button
                  type="button"
                  key={turn.id}
                  className={`assistant-turn ${selectedTurn?.id === turn.id ? "selected" : ""}`}
                  onClick={() => setSelectedTurnId(turn.id)}
                >
                  <div className="assistant-message user">
                    <div className="assistant-message-meta">
                      <Text strong>学生</Text>
                      <Text type="secondary">{dayjs(turn.createdAt).format("HH:mm:ss")}</Text>
                    </div>
                    <div>{turn.question}</div>
                  </div>
                  <div className={`assistant-message assistant ${turn.status}`}>
                    <div className="assistant-message-meta">
                      <Space size={8}>
                        <Text strong>学习助手</Text>
                        <Tag color={turn.status === "done" ? "#005826" : turn.status === "error" ? "red" : "blue"}>
                          {turn.status === "done" ? "完成" : turn.status === "error" ? "失败" : "生成中"}
                        </Tag>
                      </Space>
                      <Text type="secondary">{assistantTurnLabel(turn, index)}</Text>
                    </div>
                    {turn.streamStatus ? <Alert type="info" showIcon message={turn.streamStatus} /> : null}
                    {turn.error ? <Alert type="error" showIcon message={turn.error} /> : null}
                    <div className="assistant-answer">{renderAssistantMarkdown(turn.answer || "等待模型输出...")}</div>
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="发送一个学生问题后开始多轮调试" />
          )}
        </Card>

        <Card title="轮次诊断" className="learning-assistant-card learning-assistant-inspector">
          {selectedTurn && response ? (
            <Space direction="vertical" size={14} className="full">
              <Space wrap>
                <Tag color="#005826">{policyLabel}</Tag>
                <Tooltip title={response.mode}>
                  <Tag>{modeLabel}</Tag>
                </Tooltip>
                {response.review_required ? <Tag color="#b8892f">记录留痕</Tag> : null}
              </Space>

              <div>
                <Text strong>护栏评估</Text>
                <div className="assistant-pill-list">
                  {response.guardrail_decisions.length ? response.guardrail_decisions.map((item, index) => {
                    const guardrailCode = String(item.code || "");
                    const guardrailAction = String(item.action || "");
                    return (
                      <Tooltip
                        key={`${guardrailCode || "guardrail"}-${index}`}
                        title={`${guardrailCode || "guardrail"} · ${guardrailAction || "-"}${item.reason ? `：${item.reason}` : ""}`}
                      >
                        <Tag color="#356f9c">
                          {learningAssistantGuardrailLabels[guardrailCode] || guardrailCode || "护栏"} · {learningAssistantActionLabels[guardrailAction] || guardrailAction || "-"}
                        </Tag>
                      </Tooltip>
                    );
                  }) : <Text type="secondary">无触发</Text>}
                </div>
              </div>

              <div>
                <Text strong>RAG 查询与重排</Text>
                <Descriptions column={1} size="small" className="assistant-rag-desc">
                  <Descriptions.Item label="模式">{String(latestRagTrace.mode || "-")}</Descriptions.Item>
                  <Descriptions.Item label="最终排序">
                    <Tag color={traceReranked ? "#005826" : "default"}>
                      {traceReranked ? "BGE reranker 已重排" : String(latestRagTrace.final_sort || "未使用重排")}
                    </Tag>
                    {traceReranked ? <Text type="secondary">来源证据按 final_evidence.rank 展示</Text> : null}
                  </Descriptions.Item>
                  <Descriptions.Item label="生成 Query">
                    {Array.isArray(latestRagTrace.generated_queries) && latestRagTrace.generated_queries.length
                      ? latestRagTrace.generated_queries.map((item) => <Tag key={String(item)}>{String(item)}</Tag>)
                      : <Text type="secondary">无</Text>}
                  </Descriptions.Item>
                  <Descriptions.Item label="降级">
                    {Array.isArray(latestRagTrace.fallbacks) && latestRagTrace.fallbacks.length
                      ? latestRagTrace.fallbacks.map((item, index) => (
                        <Tag color="orange" key={`fallback-${index}`}>
                          {String((item as Record<string, unknown>).stage || "fallback")}
                        </Tag>
                      ))
                      : <Text type="secondary">无</Text>}
                  </Descriptions.Item>
                </Descriptions>
                <div className="assistant-trace-metrics">
                  <div>
                    <span>总耗时</span>
                    <strong>{formatTraceMs(traceTimings.total_ms)}</strong>
                  </div>
                  <div>
                    <span>Query 生成</span>
                    <strong>{formatTraceMs(traceTimings.query_generation_ms)}</strong>
                  </div>
                  <div>
                    <span>BGE Embedding</span>
                    <strong>{formatTraceMs(traceTimings.bge_embed_ms_total)}</strong>
                  </div>
                  <div>
                    <span>向量召回</span>
                    <strong>{formatTraceMs(traceTimings.vector_recall_ms_total)}</strong>
                  </div>
                  <div>
                    <span>BGE Rerank</span>
                    <strong>{formatTraceMs(traceTimings.bge_rerank_ms)}</strong>
                  </div>
                  <div>
                    <span>候选池</span>
                    <strong>
                      {mergedCount === undefined
                        ? "-"
                        : `${keywordTotalCount || 0} + ${vectorCount || 0} → ${mergedCount}`}
                    </strong>
                  </div>
                  <div>
                    <span>重排池</span>
                    <strong>{rerankPoolCount === undefined ? "-" : String(rerankPoolCount)}</strong>
                  </div>
                  <div>
                    <span>最终证据</span>
                    <strong>{finalEvidenceCount === undefined ? "-" : String(finalEvidenceCount)}</strong>
                  </div>
                </div>
              </div>

              <div>
                <Text strong>来源证据</Text>
                <div className="assistant-source-list">
                  {response.sources.length ? response.sources.map((source, index) => {
                    const evidence = findFinalEvidence(source, finalEvidence);
                    return (
                      <div key={source.chunk_id} className="assistant-source-item">
                        <div className="assistant-source-head">
                          <Space size={8} wrap>
                            <Tag color={traceReranked ? "#005826" : "default"}>
                              #{String(evidence?.rank || index + 1)}
                            </Tag>
                            <Text strong>{source.source_file || source.chunk_id}</Text>
                          </Space>
                          {source.page_number ? <Text type="secondary">p.{source.page_number}</Text> : null}
                        </div>
                        <div className="assistant-source-tags">
                          <Tag>{sourceKindLabel(evidence?.source)}</Tag>
                          {evidence?.rerank_score !== undefined ? (
                            <Tag color="#005826">rerank {String(evidence.rerank_score)}</Tag>
                          ) : null}
                          {evidence?.score !== undefined ? <Tag>score {String(evidence.score)}</Tag> : null}
                          <Tag>{source.chunk_id}</Tag>
                        </div>
                        {evidence?.query ? (
                          <Text type="secondary" className="block-text">Query：{String(evidence.query)}</Text>
                        ) : null}
                        <Text type="secondary" className="block-text">
                          {renderAssistantRichText(source.text_preview)}
                        </Text>
                      </div>
                    );
                  }) : <Text type="secondary" className="block-text">无来源</Text>}
                </div>
              </div>

              <div>
                <Text strong>分类与工具调用</Text>
                <pre className="assistant-json">
                  {JSON.stringify({
                    classification: response.classification,
                    tool_calls: response.tool_calls,
                    rag_trace: response.rag_trace,
                    guardrail_decisions: response.guardrail_decisions,
                  }, null, 2)}
                </pre>
              </div>
            </Space>
          ) : (
            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="选择一个助手轮次查看诊断" />
          )}
        </Card>
      </div>
    </Space>
  );
}

function SettingsPage() {
  const { message } = AntApp.useApp();
  const queryClient = useQueryClient();
  const [form] = Form.useForm();
  const [aiFeatureForm] = Form.useForm();
  const platformSettings = useQuery({
    queryKey: ["platform-settings"],
    queryFn: () => api<PlatformSettingsResponse>("/api/admin/platform-settings"),
  });
  const aiConfig = useQuery({
    queryKey: ["ai-configuration", "settings"],
    queryFn: () => api<AIConfiguration>("/api/admin/ai-configuration"),
  });

  useEffect(() => {
    if (platformSettings.data) {
      form.setFieldsValue(platformSettings.data.settings);
    }
  }, [form, platformSettings.data]);

  useEffect(() => {
    if (aiConfig.data) {
      aiFeatureForm.setFieldsValue({ enabled_features: aiConfig.data.enabled_features });
    }
  }, [aiConfig.data, aiFeatureForm]);

  const save = useMutation({
    mutationFn: (values: LearningBehaviorSettings) => putJson<PlatformSettingsResponse>("/api/admin/platform-settings", values),
    onSuccess: () => {
      message.success("设置已保存");
      void queryClient.invalidateQueries({ queryKey: ["platform-settings"] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });
  const saveAiFeatures = useMutation({
    mutationFn: (values: { enabled_features?: Partial<AIConfiguration["enabled_features"]> }) => {
      if (!aiConfig.data) {
        throw new Error("AI 接入配置尚未加载");
      }
      const enabledFeatures = {
        ...aiConfig.data.enabled_features,
        ...(values.enabled_features || {}),
      };
      const payload: AIConfigurationUpdate = {
        provider: "openai",
        base_url: aiConfig.data.base_url || "",
        model: aiConfig.data.model || "",
        connection_check_interval_minutes: aiConfig.data.connection_check_interval_minutes || 30,
        enabled_features: enabledFeatures,
      };
      return putJson<AIConfiguration>("/api/admin/ai-configuration", payload);
    },
    onSuccess: () => {
      message.success("学生 AI 能力开关已保存");
      void queryClient.invalidateQueries({ queryKey: ["ai-configuration"] });
      void queryClient.invalidateQueries({ queryKey: ["ai-configuration", "settings"] });
    },
    onError: (error) => message.error(errorMessage(error)),
  });

  const canEdit = Boolean(platformSettings.data?.can_edit);
  const canEditAiFeatures = Boolean(aiConfig.data?.can_edit);

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
                      <Text strong>AI 学习助手入口</Text>
                      <Text type="secondary" className="block-text">
                        控制学生端是否显示课程问答入口；模型调用能力在下方学生 AI 能力中维护。
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
      <QueryState loading={aiConfig.isLoading} error={aiConfig.error}>
        <Form
          form={aiFeatureForm}
          layout="vertical"
          onFinish={(values) => saveAiFeatures.mutate(values as { enabled_features?: Partial<AIConfiguration["enabled_features"]> })}
        >
          <Card
            title="学生 AI 能力"
            extra={<Tag color="default">AI 接入页维护 API 凭据</Tag>}
            className="settings-ai-feature-card"
          >
            {!canEditAiFeatures ? <Alert type="info" showIcon title="当前账号可查看学生 AI 能力开关，只有管理员可以修改。" className="section-alert" /> : null}
            <Text type="secondary" className="block-text ai-card-description">
              这里控制学生端 Agent 能力范围。OpenAI 兼容 API 的模型、Base URL 和密钥在 AI接入 页面维护；RAG 运行状态也在那里只读查看。
            </Text>
            <div className="settings-grid settings-ai-feature-grid">
              <div className="settings-section compact">
                <Flex justify="space-between" align="center" gap={12}>
                  <div>
                    <Text strong>允许学生 AI 接入 RAG</Text>
                    <Text type="secondary" className="block-text">
                      允许学生侧 Agent 检索课本与平台来源作为回答证据。
                    </Text>
                  </div>
                  <Form.Item name={["enabled_features", "rag_access_enabled"]} valuePropName="checked" noStyle>
                    <Switch disabled={!canEditAiFeatures} />
                  </Form.Item>
                </Flex>
              </div>
              <div className="settings-section compact">
                <Flex justify="space-between" align="center" gap={12}>
                  <div>
                    <Text strong>学生 AI 学习助手能力</Text>
                    <Text type="secondary" className="block-text">
                      控制 Agent 是否可响应学生端课程问答；入口开关关闭时学生仍看不到入口。
                    </Text>
                  </div>
                  <Form.Item name={["enabled_features", "student_ai_assistant"]} valuePropName="checked" noStyle>
                    <Switch disabled={!canEditAiFeatures} />
                  </Form.Item>
                </Flex>
              </div>
              <div className="settings-section compact">
                <Flex justify="space-between" align="center" gap={12}>
                  <div>
                    <Text strong>学生 AI 学情分析</Text>
                    <Text type="secondary" className="block-text">
                      控制学生端学习报告和个性化推荐是否可以调用 AI。
                    </Text>
                  </div>
                  <Form.Item name={["enabled_features", "student_learning_analytics"]} valuePropName="checked" noStyle>
                    <Switch disabled={!canEditAiFeatures} />
                  </Form.Item>
                </Flex>
              </div>
            </div>
            <div className="settings-card-actions">
              <Button
                type="primary"
                htmlType="submit"
                loading={saveAiFeatures.isPending}
                disabled={!canEditAiFeatures}
              >
                保存学生 AI 能力
              </Button>
            </div>
          </Card>
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
      message.success("AI 接入配置已保存");
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
  const policyDecisionCount = policyStatus?.recent_decision_count || 0;
  const policyInvalidCount = policyStatus?.invalid_decision_count || 0;
  const policyHandledCount = policyOutcomes
    .filter((item) => item.mode !== "normal_answer")
    .reduce((sum, item) => sum + item.count, 0);
  const policyHealth = policyStatus?.active ? (policyInvalidCount ? "degraded" : "active") : "inactive";
  const policyHealthMeta = {
    active: { label: "主动防护中", color: "#005826", tone: "good" },
    degraded: { label: "兜底保护中", color: "#b8892f", tone: "warn" },
    inactive: { label: "待模型配置", color: "default", tone: "idle" },
  }[policyHealth];
  const maxPolicyOutcome = Math.max(...policyOutcomes.map((item) => item.count), 1);
  const policyRailItems = [
    { key: "scope", title: "课程范围", description: "课程外请求引导回无机化学学习", signal: "Scope" },
    { key: "experiment", title: "实验安全", description: "危险操作只讲原理和安全提醒", signal: "Safety" },
    { key: "assessment", title: "测验保护", description: "索要答案时只给思路提示", signal: "Assessment" },
    { key: "evidence", title: "平台资源", description: "资源存在性必须检索平台来源", signal: "Grounding" },
    { key: "course", title: "课程问答", description: "普通化学问题由模型回答，RAG 辅助", signal: "Answer" },
  ];
  const ragRuntime = aiConfig.data?.rag_runtime;

  return (
    <Space direction="vertical" size={18} className="full">
      <PageTitle title="AI接入" description="配置 OpenAI 兼容 API 接入；学生端 AI 功能范围在系统设置维护，RAG 运行状态在本页只读查看。" />
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
                  <div className="ai-usage-health">
                    <div>
                      <Text type="secondary">调用健康度</Text>
                      <strong>{recentRequests ? `${successRate}%` : "-"}</strong>
                    </div>
                    <Tag color={recentErrors ? "#b42318" : "#005826"}>{recentErrors ? "存在错误" : "稳定运行"}</Tag>
                  </div>
                  <div className="ai-usage-mini-grid">
                    <div className="ai-usage-mini-card">
                      <span>近 24 小时请求</span>
                      <strong>{recentRequests}</strong>
                    </div>
                    <div className="ai-usage-mini-card">
                      <span>错误</span>
                      <strong className={recentErrors ? "danger-text" : ""}>{recentErrors}</strong>
                    </div>
                    <div className="ai-usage-mini-card">
                      <span>成功请求</span>
                      <strong>{Math.max(0, recentRequests - recentErrors)}</strong>
                    </div>
                  </div>
                  <div className="ai-usage-last-call">
                    <span>最近调用</span>
                    <strong>{lastRequestText}</strong>
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
              extra={<Tag color={policyHealthMeta.color}>{policyHealthMeta.label}</Tag>}
              className="ai-policy-card"
            >
              <div className="ai-guardrail-command">
                <div className={`ai-guardrail-shield ai-guardrail-shield-${policyHealthMeta.tone}`}>
                  <div className="ai-guardrail-radar" aria-hidden="true">
                    <div className="ai-guardrail-radar-grid" />
                    <div className="ai-guardrail-radar-sweep" />
                    <div className="ai-guardrail-radar-pulse ai-guardrail-radar-pulse-one" />
                    <div className="ai-guardrail-radar-pulse ai-guardrail-radar-pulse-two" />
                    <SafetyCertificateOutlined />
                  </div>
                  <div className="ai-guardrail-shield-copy">
                    <Text type="secondary">Guardrail Core</Text>
                    <Title level={3}>{policyHealthMeta.label}</Title>
                    <Text>学生提问进入模型前完成风险判定，命中风险时按策略拦截、提示或降级。</Text>
                  </div>
                </div>

                <div className="ai-guardrail-operations">
                  <div className="ai-guardrail-headline">
                    <div>
                      <Text className="eyebrow">Student AI Defense</Text>
                      <Title level={3}>输入检查、策略判定、受控输出</Title>
                      <Text type="secondary">
                        普通课程问答允许模型回答，RAG 用作辅助；平台资源、安全实验和测验答案仍由护栏强约束。
                      </Text>
                    </div>
                    <div className="ai-guardrail-version">
                      <span>Policy</span>
                      <strong>{policyStatus?.version || "student-ai-policy-v1"}</strong>
                    </div>
                  </div>

                  <div className="ai-guardrail-pipeline">
                    {[
                      { key: "input", label: "输入层", value: "学生提问" },
                      { key: "gate", label: "判定层", value: policyStatus?.model || "本地策略" },
                      { key: "action", label: "处置层", value: "放行 / 提示 / 拒答" },
                    ].map((stage, index) => (
                      <div key={stage.key} className={`ai-guardrail-stage ${index === 1 ? "ai-guardrail-stage-active" : ""}`}>
                        <span>{stage.label}</span>
                        <strong>{stage.value}</strong>
                        {index < 2 ? <i aria-hidden="true" /> : null}
                      </div>
                    ))}
                  </div>

                  <div className="ai-guardrail-metrics">
                    <div className="ai-guardrail-metric">
                      <Text type="secondary">近 24 小时判定</Text>
                      <strong>{policyDecisionCount}</strong>
                      <span>实时日志</span>
                    </div>
                    <div className="ai-guardrail-metric ai-guardrail-metric-warn">
                      <Text type="secondary">已处置风险</Text>
                      <strong>{policyHandledCount}</strong>
                      <span>拒答 / 提示 / 兜底</span>
                    </div>
                    <div className="ai-guardrail-metric">
                      <Text type="secondary">结构兜底</Text>
                      <strong className={policyInvalidCount ? "danger-text" : ""}>{policyInvalidCount}</strong>
                      <span>异常输出保护</span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="ai-guardrail-layers">
                {policyRailItems.map((item, index) => (
                  <div key={item.key} className="ai-policy-rail-item">
                    <div className="ai-policy-rail-top">
                      <span className="ai-policy-rail-index">{String(index + 1).padStart(2, "0")}</span>
                      <span className="ai-policy-rail-signal">{item.signal}</span>
                    </div>
                    <div className="ai-policy-rail-content">
                      <Text strong className="ai-policy-rail-title">{item.title}</Text>
                      <Text type="secondary" className="ai-policy-rail-description">
                        {item.description}
                      </Text>
                    </div>
                    <div className="ai-policy-rail-status">
                      <CheckCircleOutlined />
                      <span>已启用</span>
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
                        <div>
                          <span>{item.label}</span>
                          <div className="ai-policy-outcome-track">
                            <i style={{ width: `${Math.max(8, Math.round((item.count / maxPolicyOutcome) * 100))}%` }} />
                          </div>
                        </div>
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
                    保存接入配置
                  </Button>
                </div>
              </Card>

              <Card
                title="RAG 状态"
                className="ai-side-card ai-agent-card"
                extra={
                  ragRuntime ? (
                    <Tag color={ragRuntime.hybrid_bge_enabled ? "#005826" : ragRuntime.rag_enabled ? "default" : "#b42318"}>
                      {ragRuntime.hybrid_bge_enabled ? "Hybrid" : ragRuntime.rag_enabled ? "Legacy" : "Disabled"}
                    </Tag>
                  ) : null
                }
              >
                <Text type="secondary" className="block-text ai-card-description">
                  学生端 RAG 开关在系统设置维护；这里展示当前检索运行路径、BGE sidecar 需求和召回/重排参数。
                </Text>
                {ragRuntime ? (
                  <div className="ai-rag-runtime-panel">
                    <Flex justify="space-between" align="center" gap={12}>
                      <div>
                        <Text strong>BGE RAG 运行时</Text>
                        <Text type="secondary" className="block-text">
                          {ragRuntime.message}
                        </Text>
                      </div>
                      <Tag color={ragRuntime.hybrid_bge_enabled ? "#005826" : "default"}>
                        {ragRuntime.hybrid_bge_enabled ? "Hybrid" : "Legacy"}
                      </Tag>
                    </Flex>
                    <Descriptions size="small" column={1} className="ai-rag-runtime-desc">
                      <Descriptions.Item label="学生 RAG 开关">
                        {aiConfig.data?.enabled_features.rag_access_enabled ? "已开启" : "已关闭"}
                      </Descriptions.Item>
                      <Descriptions.Item label="BGE 服务">{ragRuntime.bge_service_required ? "需要启动" : "非必需"}</Descriptions.Item>
                      <Descriptions.Item label="服务地址">{ragRuntime.bge_service_url || "-"}</Descriptions.Item>
                      <Descriptions.Item label="Query 生成">{ragRuntime.query_generation_enabled ? "已开启" : "未开启"}</Descriptions.Item>
                      <Descriptions.Item label="召回/重排">
                        {ragRuntime.vector_top_k} / {ragRuntime.rerank_top_k} / {ragRuntime.final_top_k}
                      </Descriptions.Item>
                    </Descriptions>
                  </div>
                ) : null}
                <div className="ai-rag-status-list">
                  <div>
                    <span>检索路径</span>
                    <strong>{ragRuntime?.hybrid_bge_enabled ? "关键词 + BGE 向量 + BGE 重排" : ragRuntime?.rag_enabled ? "现有来源/关键词 RAG" : "RAG 已关闭"}</strong>
                  </div>
                  <div>
                    <span>能力开关位置</span>
                    <strong>系统设置 / 学生 AI 能力</strong>
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
