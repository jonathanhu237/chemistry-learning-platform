import type { StudentAssistantAskRequest } from "../../api";

export type AssistantContext = Omit<StudentAssistantAskRequest, "question" | "conversation_history"> & { prompts: string[] };

export function defaultAssistantContext(): AssistantContext {
  return {
    context_type: "learning_home",
    context_title: "AI 学习助手",
    context_summary: "学生端全局课程问答入口",
    prompts: ["我应该先复习哪一块？", "帮我解释一个无机化学实验现象", "怎样把元素性质和实验联系起来？"],
  };
}
