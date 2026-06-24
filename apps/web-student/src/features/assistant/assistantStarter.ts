import type { AssistantContext } from "./assistantContext";

export type AssistantStarterIntentId =
  | "review"
  | "observe"
  | "phenomenon"
  | "principle"
  | "design"
  | "compare"
  | "mistake"
  | "link"
  | "custom";

export type AssistantStarterIntent = {
  id: AssistantStarterIntentId;
  label: string;
  description: string;
  buildQuestion?: (context: AssistantContext) => string;
};

export function isGlobalAssistantContext(context: AssistantContext): boolean {
  return context.context_type === "learning_home" && context.context_title === "Atom 学习助手";
}

function contextSubject(context: AssistantContext): string {
  return context.context_title.trim() || "当前学习内容";
}

function hasExperimentContext(context: AssistantContext): boolean {
  return Boolean(
    context.experiment_id ||
      context.point_node_id ||
      context.context_type === "experiment_group" ||
      context.context_type === "experiment_detail" ||
      context.context_type === "learning_point",
  );
}

const globalStarterIntents: AssistantStarterIntent[] = [
  {
    id: "review",
    label: "复习顺序",
    description: "先抓重点，再安排顺序",
    buildQuestion: () => "我应该先复习哪一块？请按课程重点给我一个适合现在开始的复习顺序。",
  },
  {
    id: "phenomenon",
    label: "实验现象",
    description: "把现象和结论连起来",
    buildQuestion: () => "帮我解释一个无机化学实验现象，并说明它通常对应什么化学原理。",
  },
  {
    id: "link",
    label: "性质联系",
    description: "把元素性质放回实验",
    buildQuestion: () => "怎样把元素性质和实验现象联系起来？请给我一个学习思路。",
  },
  {
    id: "mistake",
    label: "易错点",
    description: "整理常见误解和边界",
    buildQuestion: () => "学习无机化学实验时有哪些常见易错点？请帮我梳理判断方法。",
  },
  {
    id: "custom",
    label: "我自己问",
    description: "直接输入自己的问题",
  },
];

const structuredBaseIntents: AssistantStarterIntent[] = [
  {
    id: "observe",
    label: "观察什么",
    description: "聚焦对象、现象和依据",
    buildQuestion: (context) => `我正在学习「${contextSubject(context)}」。这个内容主要要观察什么？请指出观察对象、现象和判断依据。`,
  },
  {
    id: "phenomenon",
    label: "现象说明什么",
    description: "把现象和结论连起来",
    buildQuestion: (context) => `请结合「${contextSubject(context)}」，说明可能观察到的现象分别说明什么。`,
  },
  {
    id: "principle",
    label: "背后原理",
    description: "解释对应化学原理",
    buildQuestion: (context) => `请解释「${contextSubject(context)}」背后的化学原理，并说明它和实验结论的关系。`,
  },
  {
    id: "mistake",
    label: "易错点",
    description: "找常见误解和判断边界",
    buildQuestion: (context) => `学习「${contextSubject(context)}」时容易误解哪里？请帮我梳理易错点和判断边界。`,
  },
];

const experimentIntents: AssistantStarterIntent[] = [
  {
    id: "design",
    label: "为什么这样设计",
    description: "理解试剂和步骤安排",
    buildQuestion: (context) => `为什么要这样设计「${contextSubject(context)}」这个实验或点位？试剂和步骤安排想证明什么？`,
  },
  {
    id: "compare",
    label: "和其他点位对比",
    description: "放回同一实验里比较",
    buildQuestion: (context) => `请把「${contextSubject(context)}」放回相关实验中，和相邻点位或相关现象对比说明它的作用。`,
  },
];

const customIntent: AssistantStarterIntent = {
  id: "custom",
  label: "我自己问",
  description: "保留上下文，手动输入",
};

export function assistantStarterIntents(context: AssistantContext): AssistantStarterIntent[] {
  if (isGlobalAssistantContext(context)) return globalStarterIntents;
  return [
    ...structuredBaseIntents,
    ...(hasExperimentContext(context) ? experimentIntents : []),
    customIntent,
  ];
}

export function assistantContextTypeLabel(context: AssistantContext): string {
  const labels: Record<AssistantContext["context_type"], string> = {
    learning_home: "全局课程问答",
    learning_profile: "当前章节",
    experiment_group: "实验组",
    experiment_detail: "实验详情",
    learning_point: "实验点位",
  };
  return labels[context.context_type] || "课程上下文";
}

export function assistantContextHint(context: AssistantContext): string {
  if (isGlobalAssistantContext(context)) {
    return "可以询问课程知识、实验现象、复习顺序和错题思路。";
  }
  if (context.point_node_id) return "已带入实验点位信息，也可以切回全局课程问答。";
  if (context.experiment_id || context.context_type === "experiment_group") return "已带入实验上下文，也可以切回全局课程问答。";
  return "已带入当前学习上下文，也可以切回全局课程问答。";
}

export function buildStarterQuestion(intent: AssistantStarterIntent, context: AssistantContext): string {
  return intent.buildQuestion?.(context).trim() || "";
}
