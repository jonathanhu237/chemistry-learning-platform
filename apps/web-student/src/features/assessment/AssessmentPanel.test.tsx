import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { PublicPosttestQuestion } from "../../api";
import {
  AssessmentPanel,
  answerForSubmit,
  fillBlankAnswerValues,
  fillBlankSlotCount,
  isQuestionAnswered,
} from "./AssessmentPanel";

const questions: PublicPosttestQuestion[] = [
  {
    id: "choice-1",
    experiment_id: "experiment-1",
    experiment_title: "氯水性质",
    question_type: "single_choice",
    stem: "氯水中具有漂白性的微粒是？",
    options: [
      { label: "A", text: "HClO" },
      { label: "B", text: "Cl⁻" },
    ],
    related_chapter_ids: [],
    related_knowledge_point_ids: [],
  },
  {
    id: "blank-1",
    experiment_id: "experiment-1",
    experiment_title: "氯水性质",
    question_type: "fill_blank",
    stem: "氯气与____反应，生成____。",
    options: [],
    related_chapter_ids: [],
    related_knowledge_point_ids: [],
  },
];

afterEach(cleanup);

describe("assessment answer normalization", () => {
  it("detects ordered blank slots and rejects partially answered arrays", () => {
    expect(fillBlankSlotCount("先加____，再加（ ）。")).toBe(2);
    expect(fillBlankAnswerValues("水", 2)).toEqual(["水", ""]);
    expect(isQuestionAnswered(questions[1], ["水", ""])).toBe(false);
    expect(isQuestionAnswered(questions[1], ["水", "HClO"])).toBe(true);
    expect(answerForSubmit(questions[1], [" 水 ", " HClO "])).toEqual(["水", "HClO"]);
  });
});

describe("AssessmentPanel", () => {
  it("submits a multi-blank answer as an ordered array only after every slot is filled", () => {
    const onSubmit = vi.fn();
    render(
      <AssessmentPanel eyebrow="智能测评" title="请完成本轮组卷" questions={questions} submitting={false} onSubmit={onSubmit} />,
    );

    const submit = screen.getByRole("button", { name: "请完成全部题目" });
    expect(submit).toBeDisabled();
    fireEvent.click(screen.getByRole("button", { name: /HClO/ }));
    fireEvent.change(screen.getByPlaceholderText("第 1 空答案"), { target: { value: " 水 " } });
    expect(submit).toBeDisabled();
    fireEvent.change(screen.getByPlaceholderText("第 2 空答案"), { target: { value: " HClO " } });

    expect(screen.getByText("已完成 2/2 题")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "提交答案" })).toBeEnabled();
    fireEvent.click(screen.getByRole("button", { name: "提交答案" }));

    expect(onSubmit).toHaveBeenCalledWith({
      "choice-1": "A",
      "blank-1": ["水", "HClO"],
    });
  });

  it("keeps answers visible and disables editing while a report is being generated", () => {
    render(
      <AssessmentPanel eyebrow="智能测评" title="请完成本轮组卷" questions={[questions[1]]} submitting onSubmit={vi.fn()} />,
    );

    expect(screen.getByRole("status")).toHaveTextContent("正在批改答案并生成报告");
    expect(screen.getByPlaceholderText("第 1 空答案")).toBeDisabled();
    expect(screen.getByRole("button", { name: "正在批改并生成报告" })).toBeDisabled();
  });
});
