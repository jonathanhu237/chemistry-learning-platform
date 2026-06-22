export type FeedbackContext = {
  pagePath: string;
  contextTitle: string;
  chapterId?: string | null;
  experimentId?: string | null;
  pointNodeId?: string | null;
  catalogPath?: string[];
  metadata?: Record<string, unknown>;
};

export const feedbackTypes = [
  { value: "content", label: "内容问题" },
  { value: "experience", label: "体验问题" },
  { value: "suggestion", label: "功能建议" },
] as const;
