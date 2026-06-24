import type { AssistantContext } from "./assistantContext";
import type { StudentAiHistoryEntry } from "./assistantHistoryStore";
import { StudentAiChatPanel, type StudentAiChatPanelVariant } from "./StudentAiChatPanel";

export function StudentAiChatTab({
  context,
  onResetContext,
  variant = "detail",
  historyEntry = null,
  onOpenHistory,
  onHistoryChange,
}: {
  context: AssistantContext;
  onResetContext: () => void;
  variant?: StudentAiChatPanelVariant;
  historyEntry?: StudentAiHistoryEntry | null;
  onOpenHistory?: () => void;
  onHistoryChange?: () => void;
}) {
  return (
    <section className={`learning-panel assistant-tab-panel ${variant}`} aria-label="Atom 学习助手">
      <StudentAiChatPanel
        context={context}
        onResetContext={onResetContext}
        variant={variant}
        historyEntry={historyEntry}
        onOpenHistory={onOpenHistory}
        onHistoryChange={onHistoryChange}
      />
    </section>
  );
}
