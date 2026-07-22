import { useNavigate } from "@tanstack/react-router";
import { BrainCircuit, ChevronRight, ListChecks, LoaderCircle } from "lucide-react";
import { navigateToAssessmentCustom, navigateToAssessmentSession } from "../../app/router/navigation";
import { useStudentRuntime } from "../../app/shell/studentAppContext";

export function AssessmentRootPage() {
  const navigate = useNavigate();
  const { startAssessmentSession, posttestLoading, posttestError } = useStudentRuntime();

  const startAssessment = async () => {
    const posttest = await startAssessmentSession();
    if (posttest) navigateToAssessmentSession(navigate, posttest.session_id, "assessment");
  };

  return (
    <section className="assessment-root-page">
      <section className={`assessment-entry-list${posttestError ? " has-error" : ""}`} aria-label="测评入口">
        {posttestError ? <div className="form-error">{posttestError}</div> : null}
        <button type="button" className="assessment-entry-card assessment-entry-card--smart primary" disabled={posttestLoading} onClick={startAssessment}>
          <span className="assessment-entry-visual" aria-hidden="true">
            <span className="assessment-entry-icon">{posttestLoading ? <LoaderCircle className="spin" size={54} /> : <BrainCircuit size={54} />}</span>
          </span>
          <span className="assessment-entry-copy">
            <b>{posttestLoading ? "正在智能组卷" : "智能组卷"}</b>
            <small>自动抽题</small>
          </span>
          <span className="assessment-entry-action" aria-hidden="true">
            <ChevronRight size={22} />
          </span>
        </button>
        <button type="button" className="assessment-entry-card assessment-entry-card--custom" onClick={() => navigateToAssessmentCustom(navigate, "assessment")}>
          <span className="assessment-entry-visual" aria-hidden="true">
            <span className="assessment-entry-icon">
              <ListChecks size={54} />
            </span>
          </span>
          <span className="assessment-entry-copy">
            <b>自主测评</b>
            <small>选择章节、目录或点位</small>
          </span>
          <span className="assessment-entry-action" aria-hidden="true">
            <ChevronRight size={22} />
          </span>
        </button>
      </section>
    </section>
  );
}
