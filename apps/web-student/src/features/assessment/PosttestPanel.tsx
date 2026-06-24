import type { StudentSmartAssessmentResponse } from "../../api";
import { AssessmentPanel, type AnswerMap } from "../pretest/AssessmentPanel";
import { stripExperimentPrefix } from "./assessmentText";

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
  const isCustom = posttest.assessment_mode === "custom";
  const isPoint = posttest.assessment_mode === "point";
  const names = posttest.experiments.slice(0, 3).map((experiment) => stripExperimentPrefix(experiment.title)).join("、");
  const extraCount = Math.max(0, posttest.experiments.length - 3);
  const targetCount = posttest.composition.requested_question_count || posttest.composition.target_question_count;
  const underfilled = Boolean(posttest.composition.warnings?.underfilled);
  const selectedPointCount = posttest.composition.selected_point_count || posttest.experiments.reduce((total, experiment) => total + (experiment.points?.length || 0), 0);
  return (
    <section className="learning-panel" aria-label={isCustom ? "自主测评" : isPoint ? "点位测评" : "智能测评"}>
      <section className="posttest-context">
        <div>
          <p>{isCustom ? "自主测评" : isPoint ? "点位测评" : "智能组卷"}</p>
          <h2>{names ? `${names}${extraCount ? ` 等 ${posttest.experiments.length} 个实验` : ""}` : "实验测评"}</h2>
          <div className="assessment-composition">
            {isCustom ? (
              <>
                <span>自选实验 {posttest.experiments.length} 个</span>
                <span>
                  实际 {posttest.questions.length}/目标 {targetCount} 题
                </span>
                <span>每实验最多 {posttest.composition.max_questions_per_experiment} 题</span>
              </>
            ) : isPoint ? (
              <>
                <span>当前点位</span>
                <span>
                  实际 {posttest.questions.length}/目标 {targetCount} 题
                </span>
                <span>覆盖 {selectedPointCount} 个点位</span>
              </>
            ) : (
              <>
                <span>{posttest.composition.untested_question_count} 题未测点位</span>
                <span>{posttest.composition.measured_question_count} 题薄弱点位</span>
                <span>覆盖 {selectedPointCount} 个点位</span>
                <span>薄弱倾向 {posttest.composition.weak_tendency_percent}%</span>
              </>
            )}
          </div>
        </div>
        <span>{posttest.questions.length} 题</span>
      </section>
      {underfilled ? <div className="form-hint">可用题目不足，系统已按当前题库生成 {posttest.questions.length} 题。</div> : null}
      <div className="assessment-experiment-strip">
        {posttest.experiments.map((experiment) => (
          <div key={experiment.id} className="assessment-experiment-chip">
            <b>{isCustom ? "自选" : isPoint ? "点位" : experiment.source === "untested" ? "未测" : "薄弱"}</b>
            <span>{stripExperimentPrefix(experiment.title)}</span>
            {experiment.measured_point_count !== undefined || experiment.total_point_count !== undefined ? (
              <small>
                点位 {experiment.measured_point_count || 0}/{experiment.total_point_count || experiment.points?.length || 0}
              </small>
            ) : null}
            {!isCustom && experiment.mastery_score !== null && experiment.mastery_score !== undefined ? (
              <small>{Math.round(experiment.mastery_score)} 分</small>
            ) : null}
          </div>
        ))}
      </div>
      {error ? <div className="form-error">{error}</div> : null}
      <AssessmentPanel
        eyebrow={isCustom ? "自主测评" : isPoint ? "点位测评" : "智能测评"}
        title="请完成本轮组卷"
        questions={posttest.questions}
        submitting={submitting}
        onSubmit={onSubmit}
      />
    </section>
  );
}
