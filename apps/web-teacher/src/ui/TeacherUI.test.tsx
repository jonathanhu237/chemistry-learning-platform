import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { TeacherAlert, TeacherButton, TeacherEmptyState, TeacherMetricGrid, TeacherUiProvider } from "./TeacherUI";

describe("TeacherUI adapters", () => {
  it("preserves pass-through attributes for testable controls", () => {
    render(
      <TeacherUiProvider>
        <TeacherButton data-testid="teacher-action" className="custom-action">
          保存
        </TeacherButton>
      </TeacherUiProvider>,
    );

    const button = screen.getByTestId("teacher-action");
    expect(button.textContent).toContain("保存");
    expect(button.className).toContain("custom-action");
  });

  it("renders teacher state and metric primitives through the provider", () => {
    render(
      <TeacherUiProvider>
        <TeacherAlert type="success" message="已保存" />
        <TeacherEmptyState message="暂无数据" compact />
        <TeacherMetricGrid metrics={[{ label: "点位", value: 12, unit: "项" }]} />
      </TeacherUiProvider>,
    );

    expect(screen.getByText("已保存")).toBeTruthy();
    expect(screen.getByText("暂无数据")).toBeTruthy();
    expect(screen.getByText("点位")).toBeTruthy();
    expect(screen.getByText("12")).toBeTruthy();
    expect(screen.getByText("项")).toBeTruthy();
  });
});
