import { BarChart3, BookOpenCheck, CheckCircle2, FlaskConical, Sparkles } from "lucide-react";
import type { StudentSmartAssessmentReport } from "../../api";
import { MobileButton, MobileEmptyState } from "../../mobile/primitives";
import { AiMarkdownBlock } from "../../shared/markdown/AiMarkdownBlock";
import { stripExperimentPrefix } from "../experiments/experimentFormat";
import { answerLabel, formatPercent, formatScore } from "./assessmentFormat";

export function PosttestSummaryPanel({ report, onContinue }: { report: StudentSmartAssessmentReport; onContinue: () => void }) {
  const masteryChanges = report.mastery_changes.slice(0, 5);

  return (
    <section className="learning-panel" aria-label="学习总结">
      <section className="summary-hero">
        <span className="panel-icon">
          <BarChart3 size={20} />
        </span>
        <div>
          <p>学习总结</p>
          <h2>智能测评报告</h2>
          <AiMarkdownBlock className="summary-ai-text" text={report.next_recommendation} />
          <em>
            <Sparkles size={13} />
            规则总结
          </em>
        </div>
      </section>

      <section className="summary-grid">
        <div>
          <span>测评正确率</span>
          <strong>{formatPercent(report.correct_rate)}</strong>
          <small>
            {report.correct_count}/{report.total_count} 题
          </small>
        </div>
        <div>
          <span>掌握度变化</span>
          <strong>{report.mastery_delta === null || report.mastery_delta === undefined ? "未生成" : `${report.mastery_delta >= 0 ? "+" : ""}${report.mastery_delta}`}</strong>
          <small>
            {formatScore(report.mastery_before_average)} → {formatScore(report.mastery_after_average)}
          </small>
        </div>
      </section>

      <section className="summary-grid smart-composition-grid">
        <div>
          <span>未测实验</span>
          <strong>{report.composition.untested_question_count}</strong>
          <small>目标占比 {report.composition.untested_ratio_percent}%</small>
        </div>
        <div>
          <span>薄弱实验</span>
          <strong>{report.composition.measured_question_count}</strong>
          <small>薄弱倾向 {report.composition.weak_tendency_percent}%</small>
        </div>
      </section>

      <section className="detail-section">
        <h3>本轮组卷实验</h3>
        <div className="learned-list">
          {report.experiments.map((experiment) => (
            <div key={experiment.id}>
              <FlaskConical size={16} />
              <span>{stripExperimentPrefix(experiment.title)}</span>
              <small>
                {experiment.source === "untested" ? "未测" : `掌握度 ${formatScore(experiment.mastery_score)}`}
              </small>
            </div>
          ))}
        </div>
      </section>

      {masteryChanges.length ? (
        <section className="detail-section">
          <h3>掌握度变化</h3>
          <div className="mastery-list">
            {masteryChanges.map((item) => (
              <div key={item.knowledge_point_id}>
                <span>{item.content || item.knowledge_point_id}</span>
                <strong>
                  {formatScore(item.before_score)} → {formatScore(item.after_score)}
                </strong>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <section className="detail-section">
        <h3>错题回顾</h3>
        {report.wrong_answers.length ? (
          <div className="wrong-list">
            {report.wrong_answers.map((item, index) => (
              <article key={item.question_id}>
                <p>Q{index + 1}</p>
                <h4>{item.stem}</h4>
                <span>你的答案：{answerLabel(item.submitted_answer)}</span>
                <span>参考答案：{answerLabel(item.correct_answer)}</span>
                {item.explanation ? <small>{item.explanation}</small> : null}
              </article>
            ))}
          </div>
        ) : (
          <MobileEmptyState className="empty-learning-card" icon={<CheckCircle2 size={20} />}>
            <span>本轮没有错题</span>
          </MobileEmptyState>
        )}
      </section>

      <MobileButton className="primary-action full" type="button" onClick={onContinue}>
        <BookOpenCheck size={18} />
        <span>继续学习</span>
      </MobileButton>
    </section>
  );
}
