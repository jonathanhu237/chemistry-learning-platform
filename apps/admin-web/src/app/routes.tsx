import { lazy, type ComponentType, type ReactNode } from "react";
import {
  ApiOutlined,
  BarChartOutlined,
  BookOutlined,
  ExperimentOutlined,
  MessageOutlined,
  QuestionCircleOutlined,
  SafetyCertificateOutlined,
  SettingOutlined,
  TeamOutlined,
  VideoCameraOutlined,
} from "@ant-design/icons";

const FeedbackPage = lazy(async () => {
  const module = await import("../features/feedback/FeedbackPage");
  return { default: module.FeedbackPage };
});
const SettingsPage = lazy(async () => {
  const module = await import("../features/settings/SettingsPage");
  return { default: module.SettingsPage };
});
const AIConfigurationPage = lazy(async () => {
  const module = await import("../features/ai-config/AIConfigurationPage");
  return { default: module.AIConfigurationPage };
});
const AnalyticsPage = lazy(async () => {
  const module = await import("../features/analytics/AnalyticsPage");
  return { default: module.AnalyticsPage };
});
const LearningResourcesPage = lazy(async () => {
  const module = await import("../features/resources/LearningResourcesPage");
  return { default: module.LearningResourcesPage };
});
const ClassesPage = lazy(async () => {
  const module = await import("../features/classes/ClassesPage");
  return { default: module.ClassesPage };
});
const VideoResourcesPage = lazy(async () => {
  const module = await import("../features/media/VideoResourcesPage");
  return { default: module.VideoResourcesPage };
});
const ExperimentsPage = lazy(async () => {
  const module = await import("../features/experiments/ExperimentsPage");
  return { default: module.ExperimentsPage };
});
const QuestionBanksPage = lazy(async () => {
  const module = await import("../features/question-bank/QuestionBanksPage");
  return { default: module.QuestionBanksPage };
});
const LearningAssistantPage = lazy(async () => {
  const module = await import("../features/learning-assistant/LearningAssistantPage");
  return { default: module.LearningAssistantPage };
});

export type AdminRole = "admin" | "teacher" | "student";

export type AdminRouteDefinition = {
  path: string;
  Component: ComponentType;
  nav: {
    icon: ReactNode;
    label: string;
    adminOnly?: boolean;
  };
};

export const adminDefaultRoute = "/overview";

export const adminRoutes: AdminRouteDefinition[] = [
  { path: "/overview", Component: LearningResourcesPage, nav: { icon: <BookOutlined />, label: "资源总览" } },
  { path: "/classes", Component: ClassesPage, nav: { icon: <TeamOutlined />, label: "班级与学生" } },
  { path: "/experiments", Component: ExperimentsPage, nav: { icon: <ExperimentOutlined />, label: "实验管理" } },
  { path: "/videos", Component: VideoResourcesPage, nav: { icon: <VideoCameraOutlined />, label: "视频资源" } },
  {
    path: "/question-banks",
    Component: QuestionBanksPage,
    nav: { icon: <QuestionCircleOutlined />, label: "题库管理" },
  },
  { path: "/analytics", Component: AnalyticsPage, nav: { icon: <BarChartOutlined />, label: "学情分析" } },
  { path: "/feedback", Component: FeedbackPage, nav: { icon: <MessageOutlined />, label: "反馈管理" } },
  {
    path: "/learning-assistant",
    Component: LearningAssistantPage,
    nav: { icon: <SafetyCertificateOutlined />, label: "学习助手", adminOnly: true },
  },
  { path: "/settings", Component: SettingsPage, nav: { icon: <SettingOutlined />, label: "系统设置" } },
  { path: "/ai-config", Component: AIConfigurationPage, nav: { icon: <ApiOutlined />, label: "AI 接入" } },
];
