import { describe, expect, it } from "vitest";

import loginPageSource from "./auth/LoginPage.tsx?raw";
import requireAdminSource from "./auth/RequireAdmin.tsx?raw";
import navSource from "./nav.tsx?raw";
import learningResourcesPageSource from "../features/resources/LearningResourcesPage.tsx?raw";
import resourceUtilsSource from "../lib/resourceUtils.ts?raw";
import authApiSource from "../api/auth.ts?raw";
import routesSource from "./routes.tsx?raw";
import { adminNavItemsForRole, selectedAdminNavKey } from "./nav";
import { adminDefaultRoute, adminRoutes } from "./routes";
import { areaMeta } from "../lib/resourceUtils";

const teacherWorkflowPaths = [
  "/overview",
  "/textbooks",
  "/classes",
  "/experiments",
  "/videos",
  "/question-banks",
  "/analytics",
  "/feedback",
  "/learning-assistant",
  "/student-preview",
  "/settings",
  "/ai-config",
];

describe("teacher console role boundaries", () => {
  it("exposes the same complete teacher workflow menu to every teacher account role", () => {
    expect(adminRoutes.map((route) => route.path)).toEqual(teacherWorkflowPaths);
    expect(adminNavItemsForRole("admin").map((item) => item.key)).toEqual(teacherWorkflowPaths);
    expect(adminNavItemsForRole("teacher").map((item) => item.key)).toEqual(teacherWorkflowPaths);
    expect(navSource).not.toContain("filter(");
    expect(navSource).not.toContain('role === "admin"');
    expect(selectedAdminNavKey("/learning-assistant", "teacher")).toBe("/learning-assistant");
    expect(selectedAdminNavKey("/textbooks", "teacher")).toBe("/textbooks");
    expect(selectedAdminNavKey("/ai-config", "teacher")).toBe("/ai-config");
    expect(selectedAdminNavKey("/unknown", "teacher")).toBe(adminDefaultRoute);
  });

  it("keeps non-teacher account roles out at login and authenticated route guards", () => {
    expect(loginPageSource).toContain('response.user.role !== "admin" && response.user.role !== "teacher"');
    expect(requireAdminSource).toContain('meQuery.data.role !== "admin" && meQuery.data.role !== "teacher"');
    expect(loginPageSource).not.toContain('response.user.role === "admin"');
    expect(requireAdminSource).not.toContain('meQuery.data.role === "admin"');
    expect(authApiSource).not.toContain("platform_admin");
    expect(routesSource).not.toContain("platform_admin");
  });

  it("keeps resource overview on teacher-owned periodic rendering with shared area semantics", () => {
    expect(learningResourcesPageSource).not.toContain("web-student");
    expect(learningResourcesPageSource).not.toContain("features/periodic-table/PeriodicTable");
    expect(learningResourcesPageSource).not.toContain("integrated");
    expect(resourceUtilsSource).not.toContain("integrated");

    expect(areaMeta("hydrogen").selected).toBe("#6f9f2e");
    expect(areaMeta("p").selected).toBe("#0f8f72");
    expect(areaMeta("s").selected).toBe("#9a6a11");
    expect(areaMeta("ds").selected).toBe("#c89a2d");
    expect(areaMeta("d").selected).toBe("#9e2f3d");
    expect(areaMeta("f").selected).toBe("#8d4f9f");
    expect(areaMeta("general").label).toBe("通识资源");
  });

  it("renders teacher f-block rows from La and Ac while noble gases stay in p area", () => {
    expect(learningResourcesPageSource).toContain('["La", "Ce", "Pr"');
    expect(learningResourcesPageSource).toContain('["Ac", "Th", "Pa"');
    expect(learningResourcesPageSource).toContain("!(cell.group === 3 && (cell.period === 6 || cell.period === 7))");
    expect(learningResourcesPageSource).toContain('if (period === 1 && group === 1) return "hydrogen";');
    expect(learningResourcesPageSource).toContain('if (group === 18) return "p";');
    expect(learningResourcesPageSource).toContain('{ area: "p", group: 18, period: 1');
  });
});
