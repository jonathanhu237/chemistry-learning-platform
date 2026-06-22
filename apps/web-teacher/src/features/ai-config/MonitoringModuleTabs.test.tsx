import "@testing-library/jest-dom/vitest";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { MonitoringModuleTabs } from "./MonitoringModuleTabs";

afterEach(() => cleanup());

describe("MonitoringModuleTabs", () => {
  it("renders stable module navigation for the monitoring console", () => {
    render(<MonitoringModuleTabs activeKey="overview" onChange={() => undefined} />);
    expect(screen.getByRole("tablist", { name: "智能监控模块" })).toBeInTheDocument();
    for (const label of ["总览", "OpenAI", "RAG", "ES 检索", "词典与同步", "安全护栏", "调用趋势"]) {
      expect(screen.getByRole("tab", { name: label })).toBeInTheDocument();
    }
    expect(screen.getByRole("tab", { name: "总览" })).toHaveAttribute("aria-selected", "true");
  });

  it("switches modules without rendering every detail panel at once", () => {
    const onChange = vi.fn();
    render(<MonitoringModuleTabs activeKey="es" onChange={onChange} />);
    screen.getByRole("tab", { name: "词典与同步" }).click();
    expect(onChange).toHaveBeenCalledWith("dictionary");
    expect(screen.getByRole("tab", { name: "ES 检索" })).toHaveAttribute("aria-selected", "true");
  });
});
