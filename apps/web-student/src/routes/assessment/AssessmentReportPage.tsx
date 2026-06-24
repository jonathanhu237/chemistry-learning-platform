import { useEffect, useState } from "react";
import { useNavigate, useParams, useSearch } from "@tanstack/react-router";
import { Atom, ClipboardList, LoaderCircle } from "lucide-react";
import { errorMessage, getStudentAssessmentReport, type StudentAssessmentReport } from "../../api";
import { loadPosttestReport } from "../../app/router/assessmentSessionStore";
import { navigateToAiChat, navigateToRoot } from "../../app/router/navigation";
import type { StudentRouteSearch } from "../../app/router/routeTypes";
import { DetailPageFrame } from "../../app/shell/DetailPageFrame";
import { useStudentRuntime } from "../../app/shell/studentAppContext";
import { AssessmentReportPanel } from "../../features/assessment/AssessmentReportPanel";
import { PosttestSummaryPanel } from "../../features/assessment/PosttestSummaryPanel";
import type { AssistantContext } from "../../features/assistant/assistantContext";
import { MobileEmptyState } from "../../mobile/primitives";

export function AssessmentReportPage() {
  const navigate = useNavigate();
  const params = useParams({ strict: false }) as { reportId?: string; sessionId?: string };
  const search = useSearch({ strict: false }) as StudentRouteSearch;
  const { canUseAssistant } = useStudentRuntime();
  const legacyReport = params.sessionId ? loadPosttestReport(params.sessionId) : null;
  const [report, setReport] = useState<StudentAssessmentReport | null>(null);
  const [loading, setLoading] = useState(Boolean(params.reportId));
  const [error, setError] = useState("");

  useEffect(() => {
    if (!params.reportId) {
      setReport(null);
      setLoading(false);
      setError("");
      return;
    }
    let cancelled = false;
    setLoading(true);
    setError("");
    getStudentAssessmentReport(params.reportId)
      .then((response) => {
        if (!cancelled) setReport(response);
      })
      .catch((requestError) => {
        if (!cancelled) setError(errorMessage(requestError));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [params.reportId]);

  const actions =
    report && canUseAssistant ? (
      <button
        className="student-app-header-action"
        type="button"
        onClick={() => {
          const context: AssistantContext = {
            context_type: "learning_home",
            context_title: report.title || "学习报告",
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
      {params.reportId ? (
        loading ? (
          <section className="learning-panel">
            <MobileEmptyState className="empty-learning-card" icon={<LoaderCircle className="spin" size={20} />}>
              <span>正在加载报告</span>
            </MobileEmptyState>
          </section>
        ) : report ? (
          <AssessmentReportPanel report={report} onContinue={() => navigateToRoot(navigate, "learn")} />
        ) : (
          <section className="learning-panel">
            <MobileEmptyState className="empty-learning-card" icon={<ClipboardList size={20} />}>
              <span>{error || "报告不存在或你没有权限查看。"}</span>
            </MobileEmptyState>
          </section>
        )
      ) : legacyReport ? (
        <PosttestSummaryPanel report={legacyReport} onContinue={() => navigateToRoot(navigate, "learn")} />
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
