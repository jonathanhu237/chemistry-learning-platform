import { Bot, X } from "lucide-react";
import type { AssistantContext } from "./assistantContext";
import { StudentAiChatPanel } from "./StudentAiChatPanel";

export function StudentAiChatTab({ context, onResetContext }: { context: AssistantContext; onResetContext: () => void }) {
  const hasContextHandoff = context.context_type !== "learning_home" || context.context_title !== "AI 学习助手";
  return (
    <section className="learning-panel assistant-tab-panel" aria-label="AI 学习助手">
      <section className="assistant-intro-card">
        <span className="panel-icon">
          <Bot size={20} />
        </span>
        <div>
          <p>AI 学习助手</p>
          <h2>{context.context_title}</h2>
          <span>{hasContextHandoff ? "已带入当前学习上下文，也可以随时切回全局问答。" : "可以询问课程知识、实验现象、复习顺序和错题思路。"}</span>
        </div>
        {hasContextHandoff ? (
          <button type="button" className="assistant-context-clear" onClick={onResetContext} aria-label="清除当前问答上下文">
            <X size={17} />
          </button>
        ) : null}
      </section>
      <StudentAiChatPanel context={context} />
    </section>
  );
}
