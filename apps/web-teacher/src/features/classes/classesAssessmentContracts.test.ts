import { describe, expect, it } from "vitest";

import classesApiSource from "../../api/classes.ts?raw";
import classesPageSource from "./ClassesPage.tsx?raw";

describe("class assessment settings contracts", () => {
  it("exposes class override and preview endpoints through typed API helpers", () => {
    expect(classesApiSource).toContain("type SmartAssessmentStrategyResponse");
    expect(classesApiSource).toContain("type SmartAssessmentClassPreviewResponse");
    expect(classesApiSource).toContain("getSmartAssessmentStrategy");
    expect(classesApiSource).toContain("updateSmartAssessmentStrategy");
    expect(classesApiSource).toContain("clearSmartAssessmentStrategy");
    expect(classesApiSource).toContain("getSmartAssessmentPreview");
    expect(classesApiSource).toContain("getCustomAssessmentSettings");
    expect(classesApiSource).toContain("updateCustomAssessmentSettings");
    expect(classesApiSource).toContain("clearCustomAssessmentSettings");
    expect(classesApiSource).toContain("`/api/admin/classes/${classId}/smart-assessment-preview`");
    expect(classesApiSource).toContain("source: \"system_default\" | \"class\"");
    expect(classesApiSource).toContain("has_override: boolean");
  });

  it("shows inherited or class override state and refreshes preview after strategy changes", () => {
    expect(classesPageSource).toContain('queryKey: ["class-smart-assessment-preview", selectedClassId]');
    expect(classesPageSource).toContain("getSmartAssessmentPreview(selectedClassId || \"\")");
    expect(classesPageSource).toContain("ClassSmartDataPreview");
    expect(classesPageSource).toContain("当前班级数据预估");
    expect(classesPageSource).toContain("正式试卷仍会按题库可用性和会话抽样生成");
    expect(classesPageSource).toContain("本班覆盖");
    expect(classesPageSource).toContain("全局默认");
    expect(classesPageSource).toContain("本班策略");
    expect(classesPageSource).toContain("继承策略");
    expect(classesPageSource).toContain('queryKey: ["class-smart-assessment-preview", selectedClassId]');
    expect(classesPageSource).toContain("已恢复为全局智能组卷策略");
  });
});
