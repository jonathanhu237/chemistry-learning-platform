import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { QuestionLifecycleActions } from "./QuestionLifecycleActions";

beforeEach(() => {
  vi.stubGlobal(
    "ResizeObserver",
    class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    },
  );
  vi.stubGlobal(
    "matchMedia",
    vi.fn(() => ({
      matches: false,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      addListener: vi.fn(),
      removeListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  );
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe("QuestionLifecycleActions", () => {
  it("keeps withdrawal and disable as separate published-question actions", async () => {
    const onWithdraw = vi.fn();
    const onDisable = vi.fn();

    render(
      <QuestionLifecycleActions
        question={{ id: "question-1", status: "published" }}
        onWithdraw={onWithdraw}
        onDisable={onDisable}
      />,
    );

    expect(screen.getByRole("button", { name: /撤回修改/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /停用/ })).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: /撤回修改/ }));
    expect(await screen.findByText("题目会暂时从学生端停用，并生成唯一待审草稿；重新发布后仍沿用原题。")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "确认撤回" }));

    await waitFor(() => expect(onWithdraw).toHaveBeenCalledWith("question-1"));
    expect(onDisable).not.toHaveBeenCalled();
  });

  it("describes disable as a no-draft action", async () => {
    const onDisable = vi.fn();

    render(
      <QuestionLifecycleActions
        question={{ id: "question-2", status: "draft" }}
        onWithdraw={vi.fn()}
        onDisable={onDisable}
      />,
    );

    expect(screen.queryByRole("button", { name: /撤回修改/ })).not.toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: /停用/ }));
    expect(await screen.findByText("只停用题目，不会生成修订草稿。")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "确认停用" }));

    await waitFor(() => expect(onDisable).toHaveBeenCalledWith("question-2"));
  });

  it("does not offer lifecycle mutations for an already disabled question", () => {
    render(
      <QuestionLifecycleActions
        question={{ id: "question-3", status: "disabled" }}
        onWithdraw={vi.fn()}
        onDisable={vi.fn()}
      />,
    );

    expect(screen.getByText("已停用")).toBeInTheDocument();
    expect(screen.queryByRole("button")).not.toBeInTheDocument();
  });
});
