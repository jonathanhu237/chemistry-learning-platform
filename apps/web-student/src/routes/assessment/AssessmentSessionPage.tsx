import { useEffect, useState } from "react";
import { useNavigate, useParams, useSearch } from "@tanstack/react-router";
import { ClipboardList, LoaderCircle } from "lucide-react";
import { errorMessage, submitStudentSmartAssessment, type StudentSmartAssessmentResponse } from "../../api";
import {
  consumePosttestSessionNotice,
  loadPosttestSession,
  storePosttestReport,
  storePosttestSession,
} from "../../app/router/assessmentSessionStore";
import { navigateToAssessmentReport, navigateToLegacyAssessmentReport } from "../../app/router/navigation";
import type { StudentRouteSearch } from "../../app/router/routeTypes";
import { DetailPageFrame } from "../../app/shell/DetailPageFrame";
import { useStudentRuntime } from "../../app/shell/studentAppContext";
import { PosttestPanel } from "../../features/assessment/PosttestPanel";
import type { AnswerMap } from "../../features/pretest/AssessmentPanel";
import { MobileEmptyState } from "../../mobile/primitives";

export function AssessmentSessionPage() {
  const navigate = useNavigate();
  const params = useParams({ strict: false }) as { sessionId?: string };
  const search = useSearch({ strict: false }) as StudentRouteSearch;
  const { startAssessmentSession } = useStudentRuntime();
  const sessionId = params.sessionId || "";
  const [posttest, setPosttest] = useState<StudentSmartAssessmentResponse | null>(() => loadPosttestSession(sessionId));
  const [notice, setNotice] = useState("");
  const [loading, setLoading] = useState(!posttest);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setNotice(consumePosttestSessionNotice(sessionId));
  }, [sessionId]);

  useEffect(() => {
    if (posttest || !sessionId) return;
    let cancelled = false;
    setLoading(true);
    startAssessmentSession()
      .then((response) => {
        if (cancelled || !response) return;
        storePosttestSession(response);
        setPosttest(response);
        if (response.session_id !== sessionId) {
          void navigate({
            to: "/assessment/session/$sessionId",
            params: { sessionId: response.session_id },
            search: { from: search.from || "assessment" },
            replace: true,
          });
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [navigate, posttest, search.from, sessionId, startAssessmentSession]);

  const submit = async (answers: AnswerMap) => {
    if (!posttest) return;
    setSubmitting(true);
    setError("");
    try {
      const response = await submitStudentSmartAssessment(
        posttest.session_id,
        Object.entries(answers).map(([questionId, answer]) => ({ question_id: questionId, answer })),
      );
      storePosttestReport(response.report);
      if (response.assessment_report?.id) {
        navigateToAssessmentReport(navigate, response.assessment_report.id, "assessment-session");
      } else {
        navigateToLegacyAssessmentReport(navigate, response.report.session_id, "assessment-session");
      }
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <DetailPageFrame title="学习测评" source={search.from || "assessment"}>
      {loading ? (
        <section className="learning-panel">
          <MobileEmptyState className="empty-learning-card" icon={<LoaderCircle className="spin" size={20} />}>
            <span>正在打开测评</span>
          </MobileEmptyState>
        </section>
      ) : posttest ? (
        <>
          {notice ? <div className="form-hint">{notice}</div> : null}
          <PosttestPanel posttest={posttest} submitting={submitting} error={error} onSubmit={submit} />
        </>
      ) : (
        <section className="learning-panel">
          <MobileEmptyState className="empty-learning-card" icon={<ClipboardList size={20} />}>
            <span>暂时无法打开测评，请返回后重新开始。</span>
          </MobileEmptyState>
        </section>
      )}
    </DetailPageFrame>
  );
}
