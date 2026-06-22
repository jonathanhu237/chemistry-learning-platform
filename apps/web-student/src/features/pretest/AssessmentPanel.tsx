import { useEffect, useState } from "react";
import { CheckCircle2, ClipboardList, LoaderCircle } from "lucide-react";
import type { PublicPosttestQuestion, PublicPretestQuestion, PublicSmartAssessmentQuestion } from "../../api";
import { MobileField } from "../../mobile/primitives";

export type AnswerMap = Record<string, string>;
export type AssessmentQuestion = PublicPretestQuestion | PublicPosttestQuestion | PublicSmartAssessmentQuestion;

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

  const allAnswered = questions.length > 0 && questions.every((question) => String(answers[question.id] || "").trim());

  return (
    <section className="assessment-panel" aria-label={eyebrow}>
      <div className="assessment-title">
        <span className="panel-icon">
          <ClipboardList size={19} />
        </span>
        <div>
          <p>{eyebrow}</p>
          <h2>{title}</h2>
        </div>
      </div>

      <div className="question-list">
        {questions.map((question, questionIndex) => (
          <article className="question-card" key={question.id}>
            <div className="question-card-head">
              <span>Q{questionIndex + 1}</span>
            </div>
            <h3>{question.stem}</h3>
            {question.question_type === "fill_blank" ? (
              <MobileField
                className="fill-answer"
                value={answers[question.id] || ""}
                onChange={(event) => setAnswers((current) => ({ ...current, [question.id]: event.target.value }))}
                placeholder="请输入答案"
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
      <button className="sticky-action" type="button" disabled={!allAnswered || submitting} onClick={() => onSubmit(answers)}>
        {submitting ? <LoaderCircle className="spin" size={18} /> : <CheckCircle2 size={18} />}
        <span>{submitting ? "正在提交" : "提交答案"}</span>
      </button>
    </section>
  );
}
