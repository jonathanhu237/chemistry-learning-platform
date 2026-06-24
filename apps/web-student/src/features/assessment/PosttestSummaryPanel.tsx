import { useEffect, useState } from "react";
import { Atom, BarChart3, BookOpenCheck, CheckCircle2, FlaskConical, LoaderCircle, Sparkles } from "lucide-react";
import type { StudentSmartAssessmentReport } from "../../api";
import { errorMessage, explainPosttestMistakes, generatePosttestAiSummary } from "../../api";
import { MobileButton, MobileEmptyState } from "../../mobile/primitives";
import { AiMarkdownBlock } from "../../shared/markdown/AiMarkdownBlock";
import { stripExperimentPrefix } from "./assessmentText";
import { answerLabel, formatPercent, formatScore } from "./assessmentFormat";

export function PosttestSummaryPanel({ report, onContinue }: { report: StudentSmartAssessmentReport; onContinue: () => void }) {
  const masteryChanges = report.mastery_changes.slice(0, 5);
  const isCustom = report.assessment_mode === "custom";
  const isPoint = report.assessment_mode === "point";
  const targetCount = report.composition.requested_question_count || report.composition.target_question_count;
  const [aiSummary, setAiSummary] = useState(report.next_recommendation);
  const [aiSummaryLoading, setAiSummaryLoading] = useState(true);
  const [aiSummarySource, setAiSummarySource] = useState<"ai" | "fallback">("fallback");
  const [mistakeAnswer, setMistakeAnswer] = useState("");
  const [mistakeLoading, setMistakeLoading] = useState(false);
  const [mistakeError, setMistakeError] = useState("");

  useEffect(() => {
    let cancelled = false;
    setAiSummary(report.next_recommendation);
    setAiSummarySource("fallback");
    setAiSummaryLoading(true);
    generatePosttestAiSummary(report.session_id)
      .then((response) => {
        if (cancelled) return;
        setAiSummary(response.text);
        setAiSummarySource(response.source);
      })
      .catch(() => {
        if (!cancelled) {
          setAiSummary(report.next_recommendation);
          setAiSummarySource("fallback");
        }
      })
      .finally(() => {
        if (!cancelled) setAiSummaryLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [report.session_id, report.next_recommendation]);

  const explainMistakes = async () => {
    if (mistakeLoading || !report.wrong_answers.length) return;
    setMistakeLoading(true);
    setMistakeError("");
    try {
      const response = await explainPosttestMistakes(report.session_id);
      setMistakeAnswer(response.text);
    } catch (requestError) {
      setMistakeError(errorMessage(requestError));
    } finally {
      setMistakeLoading(false);
    }
  };

  return (
    <section className="learning-panel" aria-label="学习总结">
      <section className="summary-hero">
        <span className="panel-icon">
          <BarChart3 size={20} />
        </span>
        <div>
          <p>学习总结</p>
          <h2>{isCustom ? "自主测评报告" : isPoint ? "点位测评报告" : "智能测评报告"}</h2>
          <AiMarkdownBlock className="summary-ai-text" text={aiSummaryLoading ? "正在生成 Atom 学习总结..." : aiSummary} />
          <em>
            {aiSummarySource === "ai" ? <Atom size={13} /> : <Sparkles size={13} />}
            {aiSummarySource === "ai" ? "Atom 总结" : "规则总结"}
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
        {isCustom ? (
          <>
            <div>
              <span>自选实验</span>
              <strong>{report.experiments.length}</strong>
              <small>本轮选择范围</small>
            </div>
            <div>
              <span>组卷题量</span>
              <strong>{report.total_count}</strong>
              <small>目标 {targetCount} 题</small>
            </div>
          </>
        ) : isPoint ? (
          <>
            <div>
              <span>测评点位</span>
              <strong>{report.composition.selected_point_count || report.experiments.reduce((total, experiment) => total + (experiment.points?.length || 0), 0)}</strong>
              <small>完成学习后测评</small>
            </div>
            <div>
              <span>组卷题量</span>
              <strong>{report.total_count}</strong>
              <small>目标 {targetCount} 题</small>
            </div>
          </>
        ) : (
          <>
            <div>
              <span>未测点位</span>
              <strong>{report.composition.untested_question_count}</strong>
              <small>目标占比 {report.composition.untested_ratio_percent}%</small>
            </div>
            <div>
              <span>薄弱点位</span>
              <strong>{report.composition.measured_question_count}</strong>
              <small>薄弱倾向 {report.composition.weak_tendency_percent}%</small>
            </div>
          </>
        )}
      </section>

      <section className="detail-section">
        <h3>本轮组卷实验</h3>
        <div className="learned-list">
          {report.experiments.map((experiment) => (
            <div key={experiment.id}>
              <FlaskConical size={16} />
              <span>{stripExperimentPrefix(experiment.title)}</span>
              <small>
                {isCustom
                  ? `自选实验 · 点位 ${experiment.points?.length || 0}`
                  : isPoint
                    ? `点位测评 · ${experiment.points?.length || 0} 个点位`
                  : experiment.source === "untested"
                    ? `未测点位 · ${experiment.points?.length || 0} 个`
                    : `掌握度 ${formatScore(experiment.mastery_score)} · 点位 ${experiment.measured_point_count || 0}/${experiment.total_point_count || experiment.points?.length || 0}`}
              </small>
            </div>
          ))}
        </div>
      </section>

      {report.experiments.some((experiment) => experiment.points?.length) ? (
        <section className="detail-section">
          <h3>点位诊断</h3>
          <div className="mastery-list">
            {report.experiments.flatMap((experiment) =>
              (experiment.points || []).slice(0, 4).map((point) => (
                <div key={`${experiment.id}-${point.id}`}>
                  <span>{point.title}</span>
                  <strong>{point.mastery_score === null || point.mastery_score === undefined ? "未测" : formatScore(point.mastery_score)}</strong>
                </div>
              )),
            )}
          </div>
        </section>
      ) : null}

      {masteryChanges.length ? (
        <section className="detail-section">
          <h3>掌握度变化</h3>
          <div className="mastery-list">
            {masteryChanges.map((item) => (
              <div key={item.knowledge_point_id}>
                <span>{item.point_title || item.content || item.knowledge_point_id}</span>
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
        {report.wrong_answers.length ? (
          <>
            <MobileButton
              variant="secondary"
              className="secondary-action full ai-mistake-action"
              type="button"
              loading={mistakeLoading}
              onClick={() => void explainMistakes()}
            >
              {mistakeLoading ? <LoaderCircle className="spin" size={18} /> : <Atom size={18} />}
              <span>{mistakeLoading ? "Atom 正在讲解" : "Atom 讲解错题"}</span>
            </MobileButton>
            {mistakeError ? <div className="form-error">{mistakeError}</div> : null}
            {mistakeAnswer ? (
              <div className="mistake-ai-answer">
                <span>
                  <Atom size={13} />
                  Atom 解答
                </span>
                <AiMarkdownBlock text={mistakeAnswer} />
              </div>
            ) : null}
          </>
        ) : null}
      </section>

      <MobileButton className="primary-action full" type="button" onClick={onContinue}>
        <BookOpenCheck size={18} />
        <span>继续学习</span>
      </MobileButton>
    </section>
  );
}
