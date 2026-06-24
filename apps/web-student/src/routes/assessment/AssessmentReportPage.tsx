import { useNavigate, useParams, useSearch } from "@tanstack/react-router";
import { Atom, ClipboardList } from "lucide-react";
import { loadPosttestReport } from "../../app/router/assessmentSessionStore";
import { navigateToAiChat, navigateToRoot } from "../../app/router/navigation";
import type { StudentRouteSearch } from "../../app/router/routeTypes";
import { DetailPageFrame } from "../../app/shell/DetailPageFrame";
import { useStudentRuntime } from "../../app/shell/studentAppContext";
import { PosttestSummaryPanel } from "../../features/assessment/PosttestSummaryPanel";
import type { AssistantContext } from "../../features/assistant/assistantContext";
import { MobileEmptyState } from "../../mobile/primitives";

export function AssessmentReportPage() {
  const navigate = useNavigate();
  const params = useParams({ strict: false }) as { sessionId?: string };
  const search = useSearch({ strict: false }) as StudentRouteSearch;
  const { canUseAssistant } = useStudentRuntime();
  const report = params.sessionId ? loadPosttestReport(params.sessionId) : null;

  const actions =
    report && canUseAssistant ? (
      <button
        className="student-app-header-action"
        type="button"
        onClick={() => {
          const context: AssistantContext = {
            context_type: "learning_home",
            context_title: "学习报告",
            context_summary: `测评得分 ${report.score}，正确 ${report.correct_count}/${report.total_count}`,
            prompts: ["帮我总结这次测评", "下一步应该复习什么？", "解释我的错题原因"],
          };
          navigateToAiChat(navigate, context, "assessment-report");
        }}
      >
        <Atom size={18} />
        <span>问问Atom</span>
      </button>
    ) : null;

  return (
    <DetailPageFrame title="测评报告" source={search.from || "assessment"} actions={actions}>
      {report ? (
        <PosttestSummaryPanel report={report} onContinue={() => navigateToRoot(navigate, "learn")} />
      ) : (
        <section className="learning-panel">
          <MobileEmptyState className="empty-learning-card" icon={<ClipboardList size={20} />}>
            <span>报告数据不在当前设备缓存中，请从测评中心重新进入。</span>
          </MobileEmptyState>
        </section>
      )}
    </DetailPageFrame>
  );
}
