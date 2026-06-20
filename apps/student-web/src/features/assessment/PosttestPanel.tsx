import type { StudentSmartAssessmentResponse } from "../../api";
import { AssessmentPanel, type AnswerMap } from "../pretest/AssessmentPanel";
import { stripExperimentPrefix } from "../experiments/experimentFormat";

export function PosttestPanel({
  posttest,
  submitting,
  error,
  onSubmit,
}: {
  posttest: StudentSmartAssessmentResponse;
  submitting: boolean;
  error: string;
  onSubmit: (answers: AnswerMap) => void;
}) {
  const names = posttest.experiments.slice(0, 3).map((experiment) => stripExperimentPrefix(experiment.title)).join("、");
  const extraCount = Math.max(0, posttest.experiments.length - 3);
  return (
    <section className="learning-panel" aria-label="智能测评">
      <section className="posttest-context">
        <div>
          <p>智能组卷</p>
          <h2>{names ? `${names}${extraCount ? ` 等 ${posttest.experiments.length} 个实验` : ""}` : "实验测评"}</h2>
          <div className="assessment-composition">
            <span>{posttest.composition.untested_question_count} 题未测实验</span>
            <span>{posttest.composition.measured_question_count} 题已测薄弱实验</span>
            <span>薄弱倾向 {posttest.composition.weak_tendency_percent}%</span>
          </div>
        </div>
        <span>{posttest.questions.length} 题</span>
      </section>
      <div className="assessment-experiment-strip">
        {posttest.experiments.map((experiment) => (
          <div key={experiment.id} className="assessment-experiment-chip">
            <b>{experiment.source === "untested" ? "未测" : "薄弱"}</b>
            <span>{stripExperimentPrefix(experiment.title)}</span>
            {experiment.mastery_score !== null && experiment.mastery_score !== undefined ? (
              <small>{Math.round(experiment.mastery_score)} 分</small>
            ) : null}
          </div>
        ))}
      </div>
      {error ? <div className="form-error">{error}</div> : null}
      <AssessmentPanel
        eyebrow="智能测评"
        title="请完成本轮组卷"
        questions={posttest.questions}
        submitting={submitting}
        onSubmit={onSubmit}
      />
    </section>
  );
}
