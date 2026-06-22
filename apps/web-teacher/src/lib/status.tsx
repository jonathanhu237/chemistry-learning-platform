import { Tag } from "antd";

export const statusColor: Record<string, string> = {
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

export const statusLabel: Record<string, string> = {
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

export function statusTag(status?: string) {
  return <Tag color={statusColor[status || ""] || "default"}>{statusLabel[status || ""] || status || "-"}</Tag>;
}

export function optionDiagnosticRoleLabel(role?: string) {
  if (role === "correct_evidence") return "正确证据";
  if (role === "adjacent_point") return "相邻点位";
  if (role === "adjacent_experiment") return "相邻实验";
  if (role === "distractor_misconception") return "误区干扰";
  if (role === "unrelated_distractor") return "无关干扰";
  if (role === "weak_distractor") return "弱干扰";
  return role || "-";
}
