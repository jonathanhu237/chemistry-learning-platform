import { Atom, BarChart3, BookOpenCheck, CheckCircle2, FlaskConical, Sparkles } from "lucide-react";
import type { StudentAssessmentReport } from "../../api";
import { MobileButton, MobileEmptyState } from "../../mobile/primitives";
import { AiMarkdownBlock } from "../../shared/markdown/AiMarkdownBlock";
import { answerLabel, formatPercent, formatScore } from "./assessmentFormat";
import { stripExperimentPrefix } from "./assessmentText";

type ReportRecord = Record<string, unknown>;

function asRecord(value: unknown): ReportRecord {
  return value && typeof value === "object" && !Array.isArray(value) ? (value as ReportRecord) : {};
}

function asRecordArray(value: unknown): ReportRecord[] {
  return Array.isArray(value) ? value.filter((item): item is ReportRecord => Boolean(item && typeof item === "object" && !Array.isArray(item))) : [];
}

function stringValue(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function numberValue(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function reportTypeLabel(type: StudentAssessmentReport["report_type"]): string {
  if (type === "pretest") return "课前测试报告";
  if (type === "custom") return "自主测评报告";
  if (type === "point") return "点位测评报告";
  if (type === "posttest") return "学习后测报告";
  return "智能测评报告";
}

function reportSourceLabel(source: string): string {
  return source === "ai" ? "Atom 总结" : "规则总结";
}

function experimentMeta(experiment: ReportRecord, report: StudentAssessmentReport): string {
  const points = asRecordArray(experiment.points);
  if (report.report_type === "pretest") return "课前摸底";
  if (report.report_type === "custom") return `自选实验 · 点位 ${points.length}`;
  if (report.report_type === "point") return `点位测评 · ${points.length} 个点位`;
  const source = stringValue(experiment.source);
  if (source === "untested") return `未测点位 · ${points.length} 个`;
  const masteryScore = numberValue(experiment.mastery_score);
  return `掌握度 ${formatScore(masteryScore)} · 点位 ${numberValue(experiment.measured_point_count) ?? 0}/${numberValue(experiment.total_point_count) ?? points.length}`;
}

function recordKey(item: ReportRecord, fallback: string): string {
  return stringValue(item.id) || stringValue(item.question_id) || stringValue(item.knowledge_point_id) || fallback;
}

export function AssessmentReportPanel({ report, onContinue }: { report: StudentAssessmentReport; onContinue: () => void }) {
  const payload = asRecord(report.payload);
  const composition = asRecord(payload.composition);
  const experiments = asRecordArray(payload.experiments);
  const wrongAnswers = asRecordArray(payload.wrong_answers);
  const masteryChanges = asRecordArray(payload.mastery_changes).slice(0, 5);
  const points = experiments.flatMap((experiment) => asRecordArray(experiment.points).slice(0, 4));
  const targetCount = numberValue(composition.requested_question_count) ?? numberValue(composition.target_question_count) ?? report.total_count;
  const masteryBefore = numberValue(payload.mastery_before_average);
  const masteryAfter = numberValue(payload.mastery_after_average);
  const masteryDelta = numberValue(payload.mastery_delta);
  const selectedPointCount = numberValue(composition.selected_point_count) ?? points.length;
  const untestedQuestionCount = numberValue(composition.untested_question_count) ?? 0;
  const measuredQuestionCount = numberValue(composition.measured_question_count) ?? 0;
  const untestedRatio = numberValue(composition.untested_ratio_percent) ?? 0;
  const weakRatio = numberValue(composition.weak_tendency_percent) ?? 0;

  return (
    <section className="learning-panel assessment-report-panel" aria-label="测评报告">
      <section className="summary-hero assessment-report-hero">
        <span className="panel-icon">
          <BarChart3 size={20} />
        </span>
        <div>
          <p>学习报告</p>
          <h2>{report.title || reportTypeLabel(report.report_type)}</h2>
          <AiMarkdownBlock className="summary-ai-text" text={report.summary.text || "本次测评报告已生成。"} />
          <em>
            {report.summary.source === "ai" ? <Atom size={13} /> : <Sparkles size={13} />}
            {reportSourceLabel(report.summary.source)}
          </em>
        </div>
      </section>

      <section className="summary-grid">
        <div>
          <span>测评正确率</span>
          <strong>{formatPercent(report.correct_rate)}</strong>
          <small>
            {report.correct_count}/{report.total_count} 题 · {formatScore(report.score)} 分
          </small>
        </div>
        <div>
          <span>错题数量</span>
          <strong>{report.wrong_count}</strong>
          <small>{report.wrong_count ? "需要回看讲解" : "本轮全部答对"}</small>
        </div>
      </section>

      {report.report_type === "pretest" ? null : (
        <section className="summary-grid smart-composition-grid">
          <div>
            <span>{report.report_type === "point" ? "测评点位" : report.report_type === "custom" ? "自选实验" : "未测点位"}</span>
            <strong>{report.report_type === "custom" ? experiments.length : report.report_type === "point" ? selectedPointCount : untestedQuestionCount}</strong>
            <small>{report.report_type === "smart" ? `目标占比 ${untestedRatio}%` : "本轮选择范围"}</small>
          </div>
          <div>
            <span>{report.report_type === "smart" ? "薄弱点位" : "组卷题量"}</span>
            <strong>{report.report_type === "smart" ? measuredQuestionCount : report.total_count}</strong>
            <small>{report.report_type === "smart" ? `薄弱倾向 ${weakRatio}%` : `目标 ${targetCount} 题`}</small>
          </div>
        </section>
      )}

      {masteryBefore !== null || masteryAfter !== null || masteryDelta !== null ? (
        <section className="summary-grid smart-composition-grid">
          <div>
            <span>掌握度变化</span>
            <strong>{masteryDelta === null ? "未生成" : `${masteryDelta >= 0 ? "+" : ""}${masteryDelta.toFixed(1)}`}</strong>
            <small>
              {formatScore(masteryBefore)}
              {" → "}
              {formatScore(masteryAfter)}
            </small>
          </div>
          <div>
            <span>覆盖实验</span>
            <strong>{experiments.length}</strong>
            <small>本轮报告范围</small>
          </div>
        </section>
      ) : null}

      {experiments.length ? (
        <section className="detail-section">
          <h3>本轮组卷实验</h3>
          <div className="learned-list">
            {experiments.map((experiment, index) => (
              <div key={recordKey(experiment, `experiment-${index}`)}>
                <FlaskConical size={16} />
                <span>{stripExperimentPrefix(stringValue(experiment.title) || stringValue(experiment.experiment_title) || stringValue(experiment.id) || "实验")}</span>
                <small>{experimentMeta(experiment, report)}</small>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {points.length ? (
        <section className="detail-section">
          <h3>点位诊断</h3>
          <div className="mastery-list">
            {points.map((point, index) => (
              <div key={recordKey(point, `point-${index}`)}>
                <span>{stringValue(point.title) || "未命名点位"}</span>
                <strong>{numberValue(point.mastery_score) === null ? "未测" : formatScore(numberValue(point.mastery_score))}</strong>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      {masteryChanges.length ? (
        <section className="detail-section">
          <h3>掌握度变化</h3>
          <div className="mastery-list">
            {masteryChanges.map((item, index) => (
              <div key={recordKey(item, `mastery-${index}`)}>
                <span>{stringValue(item.point_title) || stringValue(item.content) || stringValue(item.knowledge_point_id) || "知识点"}</span>
                <strong>
                  {formatScore(numberValue(item.before_score))}
                  {" → "}
                  {formatScore(numberValue(item.after_score))}
                </strong>
              </div>
            ))}
          </div>
        </section>
      ) : null}

      <section className="detail-section">
        <h3>错题回顾</h3>
        {wrongAnswers.length ? (
          <div className="wrong-list">
            {wrongAnswers.map((item, index) => (
              <article key={recordKey(item, `wrong-${index}`)}>
                <p>Q{index + 1}</p>
                <h4>{stringValue(item.stem) || "题目"}</h4>
                <span>你的答案：{answerLabel(item.submitted_answer)}</span>
                <span>参考答案：{answerLabel(item.correct_answer)}</span>
                {stringValue(item.explanation) ? <small>{stringValue(item.explanation)}</small> : null}
              </article>
            ))}
          </div>
        ) : (
          <MobileEmptyState className="empty-learning-card" icon={<CheckCircle2 size={20} />}>
            <span>本轮没有错题</span>
          </MobileEmptyState>
        )}
        {wrongAnswers.length ? (
          <div className="mistake-ai-answer assessment-report-mistakes">
            <span>
              {report.mistake_explanation.source === "ai" ? <Atom size={13} /> : <Sparkles size={13} />}
              错题讲解
            </span>
            <AiMarkdownBlock text={report.mistake_explanation.text || "暂未生成错题讲解。"} />
          </div>
        ) : null}
      </section>

      <MobileButton className="primary-action full" type="button" onClick={onContinue}>
        <BookOpenCheck size={18} />
        <span>继续学习</span>
      </MobileButton>
    </section>
  );
}
