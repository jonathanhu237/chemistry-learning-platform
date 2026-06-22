import type { AssistantContext } from "./assistantContext";
import { StudentAiChatPanel } from "./StudentAiChatPanel";

export function StudentAiChatTab({ context, onResetContext }: { context: AssistantContext; onResetContext: () => void }) {
  return (
    <section className="learning-panel assistant-tab-panel" aria-label="AI 学习助手">
      <StudentAiChatPanel context={context} onResetContext={onResetContext} />
    </section>
  );
}
