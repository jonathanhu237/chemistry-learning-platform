import { useNavigate } from "@tanstack/react-router";
import { ClipboardList, LoaderCircle } from "lucide-react";
import { navigateToAssessmentSession } from "../../app/router/navigation";
import { useStudentRuntime } from "../../app/shell/studentAppContext";
import { AssessmentHomePanel } from "../../features/assessment/AssessmentHomePanel";
import { MobileButton } from "../../mobile/primitives";

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
      <section className="learning-panel assessment-center-actions" aria-label="测评入口">
        {posttestError ? <div className="form-error">{posttestError}</div> : null}
        <MobileButton className="primary-action full" type="button" loading={posttestLoading} onClick={startAssessment}>
          {posttestLoading ? <LoaderCircle className="spin" size={18} /> : <ClipboardList size={18} />}
          <span>{posttestLoading ? "正在创建测评" : "开始学习测评"}</span>
        </MobileButton>
      </section>
    </section>
  );
}
