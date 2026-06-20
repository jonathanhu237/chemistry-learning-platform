import { useEffect, useState } from "react";
import { BarChart3, Bot, BookOpenCheck, CheckCircle2, FlaskConical, LoaderCircle, Sparkles } from "lucide-react";
import { StudentPosttestReport, errorMessage, explainPosttestMistakes, generatePosttestAiSummary } from "../../api";
import { MobileButton, MobileEmptyState } from "../../mobile/primitives";
import { AiMarkdownBlock } from "../../shared/markdown/AiMarkdownBlock";
import { stripExperimentPrefix } from "./assessmentText";
import { answerLabel, formatPercent, formatScore } from "./assessmentFormat";

export function PosttestSummaryPanel({ report, onContinue }: { report: StudentPosttestReport; onContinue: () => void }) {
  const masteryChanges = report.mastery_changes.slice(0, 5);
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
          <h2>本轮实验报告</h2>
          <AiMarkdownBlock className="summary-ai-text" text={aiSummaryLoading ? "正在生成 AI 学习总结..." : aiSummary} />
          <em>
            <Sparkles size={13} />
            {aiSummarySource === "ai" ? "AI 总结" : "规则总结"}
          </em>
        </div>
      </section>

      <section className="summary-grid">
        <div>
          <span>后测正确率</span>
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

      <section className="detail-section">
        <h3>本轮实验</h3>
        <div className="learned-list">
          {report.experiments.map((experiment) => (
            <div key={experiment.id}>
              <FlaskConical size={16} />
              <span>{stripExperimentPrefix(experiment.title)}</span>
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
        {report.wrong_answers.length ? (
          <>
            <MobileButton
              variant="secondary"
              className="secondary-action full ai-mistake-action"
              type="button"
              loading={mistakeLoading}
              onClick={() => void explainMistakes()}
            >
              {mistakeLoading ? <LoaderCircle className="spin" size={18} /> : <Bot size={18} />}
              <span>{mistakeLoading ? "AI 正在讲解" : "AI 讲解错题"}</span>
            </MobileButton>
            {mistakeError ? <div className="form-error">{mistakeError}</div> : null}
            {mistakeAnswer ? (
              <div className="mistake-ai-answer">
                <span>
                  <Sparkles size={13} />
                  AI 解答
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
