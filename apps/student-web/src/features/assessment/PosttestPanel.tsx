import type { StudentPosttestResponse } from "../../api";
import { AssessmentPanel, type AnswerMap } from "../pretest/AssessmentPanel";
import { stripExperimentPrefix } from "./assessmentText";

export function PosttestPanel({
  posttest,
  submitting,
  error,
  onSubmit,
}: {
  posttest: StudentPosttestResponse;
  submitting: boolean;
  error: string;
  onSubmit: (answers: AnswerMap) => void;
}) {
  const names = posttest.experiments.map((experiment) => stripExperimentPrefix(experiment.title)).join("、");
  return (
    <section className="learning-panel" aria-label="课后摸底">
      <section className="posttest-context">
        <div>
          <p>本轮学习</p>
          <h2>{names || "实验学习"}</h2>
        </div>
        <span>{posttest.questions.length} 题</span>
      </section>
      {error ? <div className="form-error">{error}</div> : null}
      <AssessmentPanel
        eyebrow="课后摸底"
        title="请完成学习后测"
        questions={posttest.questions}
        submitting={submitting}
        onSubmit={onSubmit}
      />
    </section>
  );
}
