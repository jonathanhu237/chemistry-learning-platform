import { useSearch } from "@tanstack/react-router";
import { loadAssistantContext } from "../../app/router/assistantContextStore";
import type { StudentRouteSearch } from "../../app/router/routeTypes";
import { DetailPageFrame } from "../../app/shell/DetailPageFrame";
import { useStudentRuntime } from "../../app/shell/studentAppContext";
import { StudentAiChatTab } from "../../features/assistant/StudentAiChatTab";
import { defaultAssistantContext } from "../../features/assistant/assistantContext";
import { Atom } from "lucide-react";
import { MobileEmptyState } from "../../mobile/primitives";

export function AiChatPage() {
  const search = useSearch({ strict: false }) as StudentRouteSearch;
  const { canUseAssistant } = useStudentRuntime();
  const context = loadAssistantContext(search.contextKey);

  return (
    <DetailPageFrame title="Atom 对话" source={search.from || "ai"}>
      {canUseAssistant ? (
        <StudentAiChatTab context={context} onResetContext={() => undefined} variant="detail" />
      ) : (
        <section className="learning-panel">
          <MobileEmptyState className="empty-learning-card" icon={<Atom size={20} />}>
            <span>{defaultAssistantContext().context_title}暂未开放</span>
          </MobileEmptyState>
        </section>
      )}
    </DetailPageFrame>
  );
}
