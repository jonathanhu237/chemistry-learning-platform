import { useNavigate } from "@tanstack/react-router";
import { FlaskConical, LoaderCircle, Sparkles } from "lucide-react";
import { navigateToAssessmentCustom, navigateToAssessmentSession } from "../../app/router/navigation";
import { useStudentRuntime } from "../../app/shell/studentAppContext";
import { AssessmentHomePanel } from "../../features/assessment/AssessmentHomePanel";

export function AssessmentRootPage() {
  const navigate = useNavigate();
  const { startAssessmentSession, posttestLoading, posttestError } = useStudentRuntime();

  const startAssessment = async () => {
    const posttest = await startAssessmentSession();
    if (posttest) navigateToAssessmentSession(navigate, posttest.session_id, "assessment");
  };

  return (
    <section className="assessment-root-page">
      <AssessmentHomePanel />
      <section className="learning-panel assessment-entry-list" aria-label="测评入口">
        {posttestError ? <div className="form-error">{posttestError}</div> : null}
        <button type="button" className="assessment-entry-card primary" disabled={posttestLoading} onClick={startAssessment}>
          <span>{posttestLoading ? <LoaderCircle className="spin" size={20} /> : <Sparkles size={20} />}</span>
          <b>{posttestLoading ? "正在智能组卷" : "智能组卷"}</b>
          <small>系统按未测与薄弱实验自动抽题</small>
        </button>
        <button type="button" className="assessment-entry-card" onClick={() => navigateToAssessmentCustom(navigate, "assessment")}>
          <span>
            <FlaskConical size={20} />
          </span>
          <b>自主测评</b>
          <small>自己选择本轮要测的实验</small>
        </button>
      </section>
    </section>
  );
}
