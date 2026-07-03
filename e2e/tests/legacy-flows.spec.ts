import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

const teacherUrl = stripTrailingSlash(process.env.LEGACY_E2E_TEACHER_URL || "http://127.0.0.1:15177");
const studentUrl = stripTrailingSlash(process.env.LEGACY_E2E_STUDENT_URL || "http://127.0.0.1:15176");
const backendUrl = stripTrailingSlash(process.env.LEGACY_E2E_BACKEND_URL || "http://127.0.0.1:18000");
const teacherUsername = process.env.LEGACY_E2E_TEACHER_USERNAME || "teacher";
const teacherPassword = process.env.LEGACY_E2E_TEACHER_PASSWORD || "123456";
const studentId = process.env.LEGACY_E2E_STUDENT_ID || "SEED001";
const studentPassword = process.env.LEGACY_E2E_STUDENT_PASSWORD || "123456";

function stripTrailingSlash(value: string): string {
  return value.replace(/\/$/, "");
}

async function loginTeacher(page: Page): Promise<void> {
  await page.goto(`${teacherUrl}/`);
  const form = page.getByTestId("teacher-login-form");
  await expect(form).toBeVisible();
  await form.locator('input[name="username"]').fill(teacherUsername);
  await form.locator('input[name="password"]').fill(teacherPassword);
  await form.getByRole("button", { name: "进入后台" }).click();
  await expect(page.getByTestId("teacher-shell")).toBeVisible();
}

async function loginStudent(page: Page): Promise<void> {
  await page.goto(`${studentUrl}/`);
  const form = page.getByTestId("student-login-form");
  await expect(form).toBeVisible();
  await form.locator('input[name="student_id"]').fill(studentId);
  await form.locator('input[name="password"]').fill(studentPassword);
  await form.getByRole("button", { name: "进入学习" }).click();
  await expect(page.getByTestId("student-shell")).toBeVisible();
}

async function expectNoVisibleLegacyError(page: Page): Promise<void> {
  await expect(page.locator(".legacy-error:visible")).toHaveCount(0);
}

async function loginToken(request: APIRequestContext, path: string, data: Record<string, string>): Promise<string> {
  const response = await request.post(`${backendUrl}${path}`, { data });
  expect(response.ok(), `${path} login should succeed`).toBeTruthy();
  const payload = (await response.json()) as { access_token?: string };
  expect(payload.access_token, `${path} should return an access token`).toBeTruthy();
  return String(payload.access_token);
}

test.describe("legacy teacher/student browser flows", () => {
  test("student can log in and traverse learning, assessment, report, and point-detail flows", async ({ page }) => {
    await loginStudent(page);

    await expect(page.getByTestId("student-video-feed")).toBeVisible();
    await expect(page.getByRole("heading", { name: "实验视频库" })).toBeVisible();
    await expect(page.locator(".legacy-video-button").first()).toBeVisible();
    await expectNoVisibleLegacyError(page);

    await page.getByTestId("student-nav-learn").click();
    await expect(page.getByTestId("student-learning-root")).toBeVisible();
    await expect(page.getByRole("heading", { name: "元素周期表学习入口" })).toBeVisible();
    await expectNoVisibleLegacyError(page);

    await page.getByTestId("student-nav-assessment").click();
    await expect(page.getByTestId("student-assessment-page")).toBeVisible();
    await expect(page.getByRole("heading", { name: "按掌握度与范围出题" })).toBeVisible();
    await expect(page.getByRole("button", { name: "开始测评" }).first()).toBeVisible();
    await expectNoVisibleLegacyError(page);

    await page.getByTestId("student-nav-reports").click();
    await expect(page.getByTestId("student-reports-page")).toBeVisible();
    await expect(page.getByText("学习报告").first()).toBeVisible();
    await expectNoVisibleLegacyError(page);

    await page.getByTestId("student-nav-home").click();
    await expect(page.getByTestId("student-video-feed")).toBeVisible();
    await page.locator(".legacy-video-button").first().click();
    await expect(page.getByTestId("student-point-page")).toBeVisible();
    await expect(page.getByText("实验知识单元")).toBeVisible();
    await expectNoVisibleLegacyError(page);
  });

  test("teacher can log in and traverse canonical teacher workbench pages", async ({ page }) => {
    await loginTeacher(page);

    await expect(page.getByTestId("teacher-page-experiments")).toBeVisible();
    await expect(page.getByRole("heading", { name: "章节目录与点位" })).toBeVisible();
    await expectNoVisibleLegacyError(page);

    await page.getByTestId("teacher-nav-questions").click();
    await expect(page.getByTestId("teacher-page-questions")).toBeVisible();
    await expect(page.getByRole("heading", { name: "LLM 出题" })).toBeVisible();
    await expectNoVisibleLegacyError(page);

    await page.getByTestId("teacher-nav-analytics").click();
    await expect(page.getByTestId("teacher-page-analytics")).toBeVisible();
    await expect(page.getByRole("heading", { name: "学情分析" })).toBeVisible();
    await expectNoVisibleLegacyError(page);

    await page.getByTestId("teacher-nav-reports").click();
    await expect(page.getByTestId("teacher-page-reports")).toBeVisible();
    await expect(page.getByRole("heading", { name: "评价报告" })).toBeVisible();
    await expectNoVisibleLegacyError(page);

    await page.goto(`${teacherUrl}/videos`);
    await expect(page.getByTestId("teacher-page-experiments")).toBeVisible();
    await expect(page).toHaveURL(/\/experiments$/);
  });

  test("role and retired-route boundaries reject the wrong products", async ({ request }) => {
    const teacherToken = await loginToken(request, "/api/auth/login", {
      username: teacherUsername,
      password: teacherPassword,
    });
    const studentToken = await loginToken(request, "/api/auth/student/login", {
      student_id: studentId,
      password: studentPassword,
    });

    const studentToTeacher = await request.get(`${backendUrl}/api/teacher/legacy/teacher-demo/overview`, {
      headers: { Authorization: `Bearer ${studentToken}` },
    });
    expect(studentToTeacher.status()).toBe(403);

    const teacherToStudent = await request.get(`${backendUrl}/api/student/legacy/video-points`, {
      headers: { Authorization: `Bearer ${teacherToken}` },
    });
    expect(teacherToStudent.status()).toBe(403);

    const retiredAdmin = await request.get(`${backendUrl}/api/admin/legacy/teacher-demo/overview`, {
      headers: { Authorization: `Bearer ${teacherToken}` },
    });
    expect([404, 405]).toContain(retiredAdmin.status());

    const retiredWebAdmin = await request.get(`${backendUrl}/api/web-admin/auth`, {
      headers: { Authorization: `Bearer ${teacherToken}` },
    });
    expect([404, 405]).toContain(retiredWebAdmin.status());
  });
});
