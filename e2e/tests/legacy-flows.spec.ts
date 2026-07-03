import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

const teacherUrl = stripTrailingSlash(process.env.LEGACY_E2E_TEACHER_URL || "http://127.0.0.1:15177");
const studentUrl = stripTrailingSlash(process.env.LEGACY_E2E_STUDENT_URL || "http://127.0.0.1:15176");
const backendUrl = stripTrailingSlash(process.env.LEGACY_E2E_BACKEND_URL || "http://127.0.0.1:18000");
const teacherUsername = process.env.LEGACY_E2E_TEACHER_USERNAME || "teacher";
const teacherPassword = process.env.LEGACY_E2E_TEACHER_PASSWORD || "123456";
const studentId = process.env.LEGACY_E2E_STUDENT_ID || "26320001";
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

async function expandVisibleCatalogDirectories(page: Page): Promise<void> {
  for (let index = 0; index < 20; index += 1) {
    const toggle = page.locator("button.legacy-file-tree-toggle[aria-label^='展开']").first();
    if ((await toggle.count()) === 0) return;
    await toggle.click();
  }
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

    await page.getByTestId("teacher-nav-classes").click();
    await expect(page.getByTestId("teacher-page-classes")).toBeVisible();
    await expect(page.getByRole("heading", { name: "班级管理" })).toHaveCount(0);
    await expect(page.getByRole("heading", { name: "学生名单" })).toBeVisible();
    await expect(page.getByText("登录方式")).toHaveCount(0);
    await expectNoVisibleLegacyError(page);

    await page.getByTestId("teacher-nav-questions").click();
    await expect(page.getByTestId("teacher-page-questions")).toBeVisible();
    await expect(page.getByRole("heading", { name: "命题工作区" })).toBeVisible();
    await expectNoVisibleLegacyError(page);

    await page.getByTestId("teacher-nav-analytics").click();
    await expect(page.getByTestId("teacher-page-analytics")).toBeVisible();
    await expect(page.getByRole("heading", { name: "学情分析" })).toHaveCount(0);
    await expect(page.getByRole("heading", { name: "各族元素得分" })).toBeVisible();
    await expectNoVisibleLegacyError(page);

    await page.getByTestId("teacher-nav-reports").click();
    await expect(page.getByTestId("teacher-page-reports")).toBeVisible();
    await expect(page.getByRole("heading", { name: "评价报告" })).toHaveCount(0);
    await expect(page.getByRole("heading", { name: "报告生成 Prompt" })).toBeVisible();
    await expectNoVisibleLegacyError(page);

    await page.goto(`${teacherUrl}/videos`);
    await expect(page.getByTestId("teacher-page-experiments")).toBeVisible();
    await expect(page).toHaveURL(/\/experiments$/);

    await page.getByTestId("teacher-nav-settings").click();
    await expect(page).toHaveURL(/\/settings$/);
    await expect(page.getByTestId("teacher-page-settings")).toBeVisible();
    await expect(page.getByRole("dialog", { name: "设置" })).toHaveCount(0);
    const aiConfigSidebar = page.getByTestId("teacher-ai-config-settings");
    await expect(aiConfigSidebar).toBeVisible();
    await expect(page.getByRole("heading", { name: "AI 模型配置" })).toHaveCount(0);
    await expect(aiConfigSidebar.getByLabel("模型名称", { exact: true })).toBeVisible();
    await expectNoVisibleLegacyError(page);
  });

  test("teacher can open settings and validate password changes", async ({ page }) => {
    await loginTeacher(page);

    await page.getByTestId("teacher-nav-settings").click();
    const settingsPage = page.getByTestId("teacher-settings-page");
    await expect(settingsPage).toBeVisible();
    await expect(page.getByRole("dialog", { name: "设置" })).toHaveCount(0);
    await expect(settingsPage.getByText(teacherUsername)).toBeVisible();
    await expect(settingsPage.getByText("添加教师账号")).toBeVisible();

    await settingsPage.getByLabel("当前密码", { exact: true }).fill(teacherPassword);
    await settingsPage.getByLabel("新密码", { exact: true }).fill("new-password-123");
    await settingsPage.getByLabel("确认新密码", { exact: true }).fill("new-password-456");
    await settingsPage.getByRole("button", { name: "保存密码" }).click();
    await expect(settingsPage.getByText("两次输入的新密码不一致。")).toBeVisible();
  });

  test("teacher can upload and bind a video from the catalog point editor", async ({ page, request }) => {
    const teacherToken = await loginToken(request, "/api/auth/login", {
      username: teacherUsername,
      password: teacherPassword,
    });
    const headers = { Authorization: `Bearer ${teacherToken}` };
    const pointTitle = `E2E 视频点位 ${Date.now()}`;
    let pointNodeId = "";

    try {
      const catalogResponse = await request.get(`${backendUrl}/api/teacher/question-banks/catalog`, { headers });
      expect(catalogResponse.ok(), "catalog should load for teacher setup").toBeTruthy();
      const catalog = (await catalogResponse.json()) as {
        items: Array<{ node_id: string; node_kind: string; chapter_id: string }>;
        chapters: Array<{ chapter_id: string }>;
      };
      const parent = catalog.items.find((item) => item.node_kind === "directory") || null;
      const chapterId = parent?.chapter_id || catalog.chapters[0]?.chapter_id;
      expect(chapterId, "seed catalog should expose at least one chapter").toBeTruthy();

      const createResponse = await request.post(`${backendUrl}/api/teacher/catalog/nodes`, {
        headers,
        data: {
          chapter_id: chapterId,
          parent_id: parent?.node_id || null,
          node_kind: "point",
          title: pointTitle,
        },
      });
      expect(createResponse.ok(), "temporary point should be created").toBeTruthy();
      const created = (await createResponse.json()) as { node?: { node_id?: string } };
      pointNodeId = String(created.node?.node_id || "");
      expect(pointNodeId, "temporary point id should be returned").toBeTruthy();

      await loginTeacher(page);
      await expect(page.getByTestId("teacher-page-experiments")).toBeVisible();
      await expandVisibleCatalogDirectories(page);
      await page.getByRole("treeitem", { name: pointTitle }).click();

      const videoRegion = page.getByRole("region", { name: "视频" });
      await expect(videoRegion).toBeVisible();
      await expect(videoRegion.getByText("暂无真实视频")).toBeVisible();

      await videoRegion.locator("input[type='file']").setInputFiles({
        name: "e2e-point-video.mp4",
        mimeType: "video/mp4",
        buffer: Buffer.from("e2e video content"),
      });
      await expect(videoRegion.getByText("e2e-point-video.mp4")).toBeVisible();
      await expect(videoRegion.getByText("待保存")).toBeVisible();

      const uploadResponse = page.waitForResponse((response) => response.url().includes("/api/teacher/media/assets") && response.request().method() === "POST");
      const bindingResponse = page.waitForResponse((response) => response.url().includes(`/api/teacher/catalog/nodes/${pointNodeId}/media-bindings`));
      await page.getByRole("button", { name: "保存" }).click();
      expect((await uploadResponse).ok(), "media upload should succeed").toBeTruthy();
      expect((await bindingResponse).ok(), "point media binding should succeed").toBeTruthy();
      await expect(page.getByText("已保存节点资料。")).toBeVisible();
      await expectNoVisibleLegacyError(page);
    } finally {
      if (pointNodeId) {
        await request.post(`${backendUrl}/api/teacher/catalog/nodes/${pointNodeId}/status`, {
          headers,
          data: { action: "archive", include_subtree: true },
        });
      }
    }
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
