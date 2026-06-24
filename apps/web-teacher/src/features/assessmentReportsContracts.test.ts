import { describe, expect, it } from "vitest";

import assessmentReportsApiSource from "../api/assessmentReports.ts?raw";
import analyticsPageSource from "./analytics/AnalyticsPage.tsx?raw";
import classesPageSource from "./classes/ClassesPage.tsx?raw";
import settingsPageSource from "./settings/SettingsPage.tsx?raw";

describe("assessment report contracts", () => {
  it("exposes durable report and prompt endpoints through typed API helpers", () => {
    expect(assessmentReportsApiSource).toContain("type StudentAssessmentReport");
    expect(assessmentReportsApiSource).toContain("type AssessmentReportPromptSettingsResponse");
    expect(assessmentReportsApiSource).toContain('"/api/admin/assessment-report-prompts"');
    expect(assessmentReportsApiSource).toContain("`/api/admin/classes/${classId}/assessment-report-prompts`");
    expect(assessmentReportsApiSource).toContain("`/api/admin/classes/${classId}/students/${studentId}/assessment-reports`");
    expect(assessmentReportsApiSource).toContain("getTeacherStudentAssessmentReport");
  });

  it("connects global prompts, class overrides, and teacher report viewing UI", () => {
    expect(settingsPageSource).toContain("测评报告 Prompt");
    expect(settingsPageSource).toContain('queryKey: ["assessment-report-prompts"]');
    expect(settingsPageSource).toContain("updateGlobalAssessmentReportPrompts");
    expect(classesPageSource).toContain('queryKey: ["class-assessment-report-prompts", selectedClassId]');
    expect(classesPageSource).toContain("updateClassAssessmentReportPrompts");
    expect(classesPageSource).toContain("继承全局");
    expect(analyticsPageSource).toContain('queryKey: ["student-assessment-reports", classId, studentId]');
    expect(analyticsPageSource).toContain("TeacherAssessmentReportDetail");
    expect(analyticsPageSource).toContain("错题讲解");
  });
});
