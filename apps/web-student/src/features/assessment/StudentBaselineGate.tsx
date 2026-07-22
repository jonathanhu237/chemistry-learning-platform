import { useCallback, useEffect, useRef, useState } from "react";
import { ClipboardCheck, LoaderCircle, LogOut, RotateCcw } from "lucide-react";
import {
  errorMessage,
  getStudentAssessmentStatus,
  startStudentSmartAssessment,
  submitStudentSmartAssessment,
  type StudentSmartAssessmentResponse,
} from "../../api";
import { storePosttestReport, storePosttestSession } from "../../app/router/assessmentSessionStore";
import { MobileButton, MobileEmptyState } from "../../mobile/primitives";
import type { AnswerMap } from "./AssessmentPanel";
import { PosttestPanel } from "./PosttestPanel";

type GatePhase = "checking" | "session" | "error";

function sessionGateCopy(assessment: StudentSmartAssessmentResponse): string {
  if (assessment.assessment_mode === "custom") {
    return "先继续未完成的自主测评；提交后，系统会确认是否还需要首次智能基线。";
  }
  if (assessment.assessment_mode === "point") {
    return "先继续未完成的点位测评；提交后，系统会确认是否还需要首次智能基线。";
  }
  return "完成这轮智能基线后，即可进入首页、学习、Atom、测评和我的。";
}

export function StudentBaselineGate({
  onReady,
  onLogout,
}: {
  onReady: () => void;
  onLogout: () => void | Promise<void>;
}) {
  const [phase, setPhase] = useState<GatePhase>("checking");
  const [assessment, setAssessment] = useState<StudentSmartAssessmentResponse | null>(null);
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [loggingOut, setLoggingOut] = useState(false);
  const runId = useRef(0);
  const mounted = useRef(true);

  const checkAndResume = useCallback(async () => {
    const currentRun = ++runId.current;
    setPhase("checking");
    setAssessment(null);
    setError("");
    try {
      const status = await getStudentAssessmentStatus();
      if (currentRun !== runId.current) return;
      if (!status.has_open_assessment && status.has_completed_smart_baseline && !status.needs_smart_baseline) {
        onReady();
        return;
      }
      const response = await startStudentSmartAssessment();
      if (currentRun !== runId.current) return;
      storePosttestSession(response);
      setAssessment(response);
      setPhase("session");
    } catch (requestError) {
      if (currentRun !== runId.current) return;
      setError(errorMessage(requestError));
      setPhase("error");
    }
  }, [onReady]);

  useEffect(() => {
    mounted.current = true;
    void checkAndResume();
    return () => {
      mounted.current = false;
      runId.current += 1;
    };
  }, [checkAndResume]);

  const submit = async (answers: AnswerMap) => {
    if (!assessment || submitting) return;
    setSubmitting(true);
    setError("");
    try {
      const response = await submitStudentSmartAssessment(
        assessment.session_id,
        Object.entries(answers).map(([questionId, answer]) => ({ question_id: questionId, answer })),
      );
      storePosttestReport(response.report);
      await checkAndResume();
    } catch (requestError) {
      if (mounted.current) setError(errorMessage(requestError));
    } finally {
      if (mounted.current) setSubmitting(false);
    }
  };

  const leave = async () => {
    if (loggingOut) return;
    setLoggingOut(true);
    try {
      await onLogout();
    } finally {
      if (mounted.current) setLoggingOut(false);
    }
  };

  if (phase === "checking") {
    return (
      <section className="baseline-gate baseline-gate--state" aria-live="polite">
        <MobileEmptyState className="baseline-gate-state" icon={<LoaderCircle className="spin" size={24} />}>
          <div>
            <strong>正在确认首次测评状态</strong>
            <span>如有未完成测评，系统会直接恢复。</span>
          </div>
        </MobileEmptyState>
      </section>
    );
  }

  if (phase === "error" || !assessment) {
    return (
      <section className="baseline-gate baseline-gate--state" aria-live="assertive">
        <MobileEmptyState className="baseline-gate-state baseline-gate-state--error" icon={<ClipboardCheck size={24} />}>
          <div>
            <strong>暂时无法确认首次测评状态</strong>
            <span>{error || "状态检查未返回有效结果。"}</span>
          </div>
          <div className="baseline-gate-actions">
            <MobileButton type="button" onClick={() => void checkAndResume()}>
              <RotateCcw size={17} />
              <span>重试</span>
            </MobileButton>
            <MobileButton variant="secondary" type="button" loading={loggingOut} onClick={() => void leave()}>
              <LogOut size={17} />
              <span>{loggingOut ? "正在退出" : "退出登录"}</span>
            </MobileButton>
          </div>
        </MobileEmptyState>
      </section>
    );
  }

  return (
    <section className="baseline-gate" aria-label="首次智能基线">
      <header className="baseline-gate-header">
        <span className="baseline-gate-mark" aria-hidden="true">
          <ClipboardCheck size={22} />
        </span>
        <div>
          <p>首次学习准备</p>
          <h2>{assessment.assessment_mode === "smart" ? "完成智能基线" : "继续未完成测评"}</h2>
          <span>{sessionGateCopy(assessment)}</span>
        </div>
        <button type="button" className="baseline-gate-logout" disabled={loggingOut || submitting} onClick={() => void leave()}>
          <LogOut size={16} />
          <span>{loggingOut ? "退出中" : "退出"}</span>
        </button>
      </header>
      <PosttestPanel posttest={assessment} submitting={submitting} error={error} onSubmit={submit} />
    </section>
  );
}
