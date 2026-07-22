import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, ClipboardList, LoaderCircle } from "lucide-react";
import type { PublicPosttestQuestion, PublicSmartAssessmentQuestion } from "../../api";
import { MobileField } from "../../mobile/primitives";

export type AnswerValue = string | string[];
export type AnswerMap = Record<string, AnswerValue>;
export type AssessmentQuestion = PublicPosttestQuestion | PublicSmartAssessmentQuestion;

function optionValue(option: Record<string, unknown>, index: number): string {
  const raw = option.label ?? option.key ?? option.value ?? String.fromCharCode(65 + index);
  return String(raw);
}

function optionText(option: Record<string, unknown>, index: number): string {
  const fallback = optionValue(option, index);
  return String(option.text ?? fallback);
}

function assessmentOptions(question: AssessmentQuestion): Array<{ value: string; marker: string; text: string }> {
  if (question.question_type === "true_false") {
    return [
      { value: "true", marker: "对", text: "正确" },
      { value: "false", marker: "错", text: "错误" },
    ];
  }
  return question.options.map((option, index) => {
    const value = optionValue(option, index);
    return { value, marker: value, text: optionText(option, index) };
  });
}

export function fillBlankSlotCount(stem: string): number {
  const matches = stem.match(/_{2,}|＿{2,}|-{3,}|—{2,}|（\s*）|\(\s*\)/g);
  return Math.max(1, matches?.length || 0);
}

export function fillBlankAnswerValues(value: AnswerValue | undefined, slotCount: number): string[] {
  if (Array.isArray(value)) {
    return Array.from({ length: slotCount }, (_, index) => value[index] || "");
  }
  const text = String(value || "");
  if (slotCount <= 1) return [text];
  return Array.from({ length: slotCount }, (_, index) => (index === 0 ? text : ""));
}

export function isQuestionAnswered(question: AssessmentQuestion, value?: AnswerValue): boolean {
  if (question.question_type !== "fill_blank") return Boolean(String(value || "").trim());
  return fillBlankAnswerValues(value, fillBlankSlotCount(question.stem)).every((item) => item.trim());
}

export function answerForSubmit(question: AssessmentQuestion, value?: AnswerValue): AnswerValue {
  if (question.question_type !== "fill_blank") return String(value || "").trim();
  const values = fillBlankAnswerValues(value, fillBlankSlotCount(question.stem)).map((item) => item.trim());
  return values.length > 1 ? values : values[0] || "";
}

function FillBlankAnswerInputs({
  question,
  answer,
  disabled,
  onAnswer,
}: {
  question: AssessmentQuestion;
  answer?: AnswerValue;
  disabled: boolean;
  onAnswer: (answer: AnswerValue) => void;
}) {
  const slotCount = fillBlankSlotCount(question.stem);
  const values = fillBlankAnswerValues(answer, slotCount);

  if (slotCount === 1) {
    return (
      <MobileField
        className="fill-answer"
        value={values[0] || ""}
        disabled={disabled}
        onChange={(event) => onAnswer(event.target.value)}
        placeholder="请输入答案"
      />
    );
  }

  return (
    <div className="fill-answer-list" aria-label="填空答案">
      {values.map((value, index) => (
        <label className="fill-answer-row" key={`${question.id}-blank-${index + 1}`}>
          <span>第 {index + 1} 空</span>
          <MobileField
            className="fill-answer"
            value={value}
            disabled={disabled}
            onChange={(event) => {
              const next = [...values];
              next[index] = event.target.value;
              onAnswer(next);
            }}
            placeholder={`第 ${index + 1} 空答案`}
          />
        </label>
      ))}
    </div>
  );
}

export function AssessmentPanel({
  eyebrow,
  title,
  questions,
  submitting,
  onSubmit,
}: {
  eyebrow: string;
  title: string;
  questions: AssessmentQuestion[];
  submitting: boolean;
  onSubmit: (answers: AnswerMap) => void;
}) {
  const [answers, setAnswers] = useState<AnswerMap>({});

  useEffect(() => {
    setAnswers({});
  }, [questions]);

  const answeredCount = useMemo(
    () => questions.filter((question) => isQuestionAnswered(question, answers[question.id])).length,
    [answers, questions],
  );
  const allAnswered = questions.length > 0 && answeredCount === questions.length;

  const submit = () => {
    if (!allAnswered || submitting) return;
    const normalizedAnswers = Object.fromEntries(
      questions.map((question) => [question.id, answerForSubmit(question, answers[question.id])]),
    ) as AnswerMap;
    onSubmit(normalizedAnswers);
  };

  return (
    <section className="assessment-panel" aria-label={eyebrow}>
      <div className="assessment-title">
        <span className="panel-icon">
          <ClipboardList size={19} />
        </span>
        <div>
          <p>{eyebrow}</p>
          <h2>{title}</h2>
          <small className={allAnswered ? "assessment-progress is-complete" : "assessment-progress"}>
            已完成 {answeredCount}/{questions.length} 题
          </small>
        </div>
      </div>

      <div className="question-list">
        {questions.map((question, questionIndex) => (
          <article className="question-card" key={question.id}>
            <div className="question-card-head">
              <span>Q{questionIndex + 1}</span>
              <em>{question.question_type === "fill_blank" ? "填空题" : question.question_type === "true_false" ? "判断题" : "单选题"}</em>
            </div>
            <h3>{question.stem}</h3>
            {question.question_type === "fill_blank" ? (
              <FillBlankAnswerInputs
                question={question}
                answer={answers[question.id]}
                disabled={submitting}
                onAnswer={(answer) => setAnswers((current) => ({ ...current, [question.id]: answer }))}
              />
            ) : (
              <div className="option-list">
                {assessmentOptions(question).map((option) => {
                  const selected = answers[question.id] === option.value;
                  return (
                    <button
                      key={`${question.id}-${option.value}`}
                      className={selected ? "option selected" : "option"}
                      type="button"
                      disabled={submitting}
                      aria-pressed={selected}
                      onClick={() => setAnswers((current) => ({ ...current, [question.id]: option.value }))}
                    >
                      <b>{option.marker}</b>
                      <span>{option.text}</span>
                    </button>
                  );
                })}
              </div>
            )}
          </article>
        ))}
      </div>
      {submitting ? (
        <div className="assessment-submit-status" role="status" aria-live="polite">
          <LoaderCircle className="spin" size={20} />
          <div>
            <strong>正在批改答案并生成报告</strong>
            <span>系统会同步更新掌握度；根据网络和模型响应情况，可能需要几十秒，请保持页面打开。</span>
          </div>
        </div>
      ) : null}
      <button className="sticky-action" type="button" disabled={!allAnswered || submitting} onClick={submit}>
        {submitting ? <LoaderCircle className="spin" size={18} /> : <CheckCircle2 size={18} />}
        <span>{submitting ? "正在批改并生成报告" : allAnswered ? "提交答案" : "请完成全部题目"}</span>
      </button>
    </section>
  );
}
