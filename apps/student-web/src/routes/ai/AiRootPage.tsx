import { useNavigate } from "@tanstack/react-router";
import { MessageCircle, Sparkles } from "lucide-react";
import { navigateToAiChat } from "../../app/router/navigation";
import { useStudentRuntime } from "../../app/shell/studentAppContext";
import { defaultAssistantContext } from "../../features/assistant/assistantContext";
import { MobileButton, MobileEmptyState } from "../../mobile/primitives";

export function AiRootPage() {
  const navigate = useNavigate();
  const { canUseAssistant } = useStudentRuntime();
  const context = defaultAssistantContext();

  return (
    <section className="learning-panel ai-root-page" aria-label="AI 中心">
      <section className="assistant-intro-card">
        <Sparkles size={22} />
        <div>
          <p>AI 中心</p>
          <h2>{context.context_title}</h2>
          <span>从这里开启新的学习对话；来自首页、章节、实验点和报告的上下文问答会进入同一个聊天详情页。</span>
        </div>
        <MessageCircle size={20} />
      </section>
      {canUseAssistant ? (
        <div className="ai-center-actions">
          <MobileButton className="primary-action full" type="button" onClick={() => navigateToAiChat(navigate, context, "ai")}>
            <MessageCircle size={18} />
            <span>新对话</span>
          </MobileButton>
          <div className="ai-suggestion-list" aria-label="推荐问题">
            {context.prompts.map((prompt) => (
              <button key={prompt} type="button" onClick={() => navigateToAiChat(navigate, { ...context, prompts: [prompt, ...context.prompts] }, "ai")}>
                {prompt}
              </button>
            ))}
          </div>
        </div>
      ) : (
        <MobileEmptyState className="empty-learning-card" icon={<MessageCircle size={20} />}>
          <span>AI 学习助手暂未开放</span>
        </MobileEmptyState>
      )}
    </section>
  );
}
