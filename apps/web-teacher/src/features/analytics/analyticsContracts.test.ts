import { describe, expect, it } from "vitest";

import analyticsApiSource from "../../api/analytics.ts?raw";
import analyticsPageSource from "./AnalyticsPage.tsx?raw";

describe("element-family analytics contracts", () => {
  it("keeps point evidence in the typed family response", () => {
    expect(analyticsApiSource).toContain("type AnalyticsPointState");
    expect(analyticsApiSource).toContain("evidence_point_count?: number");
    expect(analyticsApiSource).toContain("points?: AnalyticsPointState[]");
  });

  it("presents element families and point scores as the primary matrix drilldown", () => {
    expect(analyticsPageSource).toContain("班级元素族得分与点位证据总览");
    expect(analyticsPageSource).toContain('title="学生元素族得分"');
    expect(analyticsPageSource).toContain("点位得分");
    expect(analyticsPageSource).toContain("有证据点位");
    expect(analyticsPageSource).not.toContain("请选择实验组");
    expect(analyticsPageSource).not.toContain("暂无包含该实验组的后测报告");
  });
});
