import { createRequire } from "node:module";
import path from "node:path";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
const appDir = path.resolve(import.meta.dirname, "..");
const adminWebDir = path.resolve(appDir, "../admin-web");

const viewports = [
  { name: "small-phone", width: 360, height: 780 },
  { name: "regular-phone", width: 390, height: 844 },
  { name: "large-phone", width: 430, height: 932 },
];

const baseUrl = process.env.STUDENT_H5_URL || "http://127.0.0.1:5173";
const studentId = process.env.STUDENT_H5_QA_STUDENT_ID || "";
const password = process.env.STUDENT_H5_QA_PASSWORD || "";
const allowAuthSkip = process.env.STUDENT_H5_QA_ALLOW_AUTH_SKIP === "1";
const useMockApi = process.env.STUDENT_H5_QA_MOCK === "1";

const mockUser = {
  id: "mobile-qa-student",
  username: "20249999",
  role: "student",
  display_name: "移动端测试学生",
  status: "active",
  must_change_password: false,
  password_version: 1,
  student_id: "20249999",
  class_id: "mobile-qa-class",
  class_name: "移动端测试班",
};

const mockLearningPoint = {
  id: "EXP_19_1_01",
  code: "19-1-01",
  title: "氯、溴、碘的置换次序",
  summary: "比较卤素单质氧化性强弱。",
  parent_code: "19-1",
  parent_title: "实验 19-1 卤素",
  module_title: "氯水 + KBr 溶液 + CCl4",
  chapter_ids: ["CH17"],
  video_candidate_count: 1,
  published_video_count: 0,
  question_count: 10,
  property_key: "oxidation",
  property_title: "氧化性",
  point_key: "halogen-displacement",
  point_title: "卤素置换观察",
  formula: "Cl2 + 2Br- -> 2Cl- + Br2",
  videos: [],
  video_candidates: ["氯水 + KBr 溶液 + CCl4"],
};

const mockLearningPage = {
  recommended_profile_id: "halogens-17",
  profiles: [
    {
      profile_id: "halogens-17",
      chapter_id: "CH17",
      title: "第 17 族 卤族元素",
      subtitle: "p区元素性质与实验",
      family_number: "17",
      family_name: "卤族元素",
      element_symbols: ["F", "Cl", "Br", "I"],
    },
  ],
  active_profile: {
    profile_id: "halogens-17",
    chapter_id: "CH17",
    title: "第 17 族 卤族元素",
    subtitle: "p区元素性质与实验",
    family_number: "17",
    family_name: "卤族元素",
    hero: {
      eyebrow: "p区",
      title: "卤素单质氧化性与置换反应",
      summary: "从族元素性质进入实验点位学习。",
    },
    default_element_symbol: "Cl",
    element_symbols: ["F", "Cl", "Br", "I"],
    elements: [
      {
        symbol: "Cl",
        name: "氯",
        atomic_number: 17,
        relative_atomic_mass: "35.45",
        group: "17",
        period: 3,
        block: "p",
        state_at_20c: "Gas",
        density: "0.002898 g/cm3",
        rsc_url: "https://periodic-table.rsc.org/element/17/chlorine",
        fact_source: "Royal Society of Chemistry Periodic Table",
        state: "气体",
        group_label: "第 17 族",
        electron_configuration: "[Ne]3s2 3p5",
        common_valence: "-1, +1, +5, +7",
        redox_tendency: "氧化性较强",
      },
      {
        symbol: "Br",
        name: "溴",
        atomic_number: 35,
        relative_atomic_mass: "79.904",
        group: "17",
        period: 4,
        block: "p",
        state_at_20c: "Liquid",
        density: "3.11 g/cm3",
        rsc_url: "https://periodic-table.rsc.org/element/35/bromine",
        fact_source: "Royal Society of Chemistry Periodic Table",
        state: "液体",
        group_label: "第 17 族",
        electron_configuration: "[Ar]3d10 4s2 4p5",
        common_valence: "-1, +1, +5",
        redox_tendency: "可被氯置换",
      },
    ],
    property_cards: [
      { key: "oxidation", label: "氧化性", value: "F2 > Cl2 > Br2 > I2", description: "卤素单质氧化性沿族递减。" },
    ],
    family_common_properties: [
      { key: "oxidation", label: "氧化性", value: "由强到弱", description: "置换反应可用于比较。" },
    ],
    property_sections: [
      {
        key: "oxidation",
        title: "氧化性",
        subtitle: "置换反应",
        summary: "氯能把溴离子氧化为溴单质。",
        formula: "Cl2 + 2Br- -> 2Cl- + Br2",
        tone: "green",
      },
    ],
    reference_media: [],
    related_groups: [
      {
        property_key: "oxidation",
        property_title: "氧化性",
        parent_code: "19-1",
        parent_title: "实验 19-1 卤素",
        points: [mockLearningPoint],
      },
    ],
    chapter_experiment_groups: [
      {
        parent_code: "19-1",
        parent_title: "实验 19-1 卤素",
        points: [mockLearningPoint],
      },
    ],
  },
};

const mockLearningHome = {
  recommended_area_id: "p",
  recommended_parent_code: "19-1",
  areas: [
    {
      area_id: "p",
      area_name: "p区元素",
      enabled: true,
      parent_codes: ["19-1"],
      experiment_count: 1,
      published_video_count: 0,
      question_count: 10,
    },
  ],
  groups: [
    {
      parent_code: "19-1",
      parent_title: "实验 19-1 卤素",
      area_id: "p",
      area_name: "p区元素",
      chapter_ids: ["CH17"],
      experiment_count: 1,
      published_video_count: 0,
      question_count: 10,
      recommended: true,
    },
  ],
};

const mockExperimentGroup = {
  parent_code: "19-1",
  parent_title: "实验 19-1 卤素",
  area_id: "p",
  area_name: "p区元素",
  experiments: [mockLearningPoint],
};

const mockPosttest = {
  status: "in_progress",
  session_id: "mobile-qa-posttest",
  experiments: [{ id: "EXP_19_1_01", code: "19-1-01", title: "氯、溴、碘的置换次序", parent_code: "19-1", parent_title: "实验 19-1 卤素" }],
  questions: [
    {
      id: "post-q-1",
      experiment_id: "EXP_19_1_01",
      experiment_title: "氯、溴、碘的置换次序",
      question_type: "single_choice",
      stem: "氯水加入 KBr 后，CCl4 层呈什么颜色？",
      options: [
        { label: "A", text: "无色" },
        { label: "B", text: "橙红色" },
      ],
      related_chapter_ids: ["CH17"],
      related_knowledge_point_ids: ["kp-halogen"],
    },
  ],
};

const mockReport = {
  session_id: "mobile-qa-posttest",
  experiments: mockPosttest.experiments,
  correct_count: 1,
  total_count: 1,
  score: 100,
  correct_rate: 1,
  mastery_before_average: 50,
  mastery_after_average: 60,
  mastery_delta: 10,
  mastery_changes: [],
  wrong_answers: [],
  next_recommendation: "建议继续复习卤素置换反应。",
};

async function loadPlaywright() {
  try {
    const playwrightPath = require.resolve("playwright", { paths: [appDir, adminWebDir, process.cwd()] });
    return import(pathToFileURL(playwrightPath).href);
  } catch (error) {
    throw new Error(
      "Playwright is required for mobile QA. Install it in apps/student-web or keep apps/admin-web/node_modules available.",
      { cause: error },
    );
  }
}

async function assertNoHorizontalOverflow(page, label) {
  const metrics = await page.evaluate(() => ({
    viewportWidth: window.innerWidth,
    documentClientWidth: document.documentElement.clientWidth,
    documentScrollWidth: document.documentElement.scrollWidth,
    bodyScrollWidth: document.body.scrollWidth,
  }));
  const maxScrollWidth = Math.max(metrics.documentScrollWidth, metrics.bodyScrollWidth);
  if (maxScrollWidth > metrics.documentClientWidth + 1) {
    throw new Error(`${label}: horizontal overflow ${maxScrollWidth}px > ${metrics.documentClientWidth}px`);
  }
}

async function visibleRects(page, selectors) {
  return page.evaluate((selectorList) => {
    const entries = [];
    for (const selector of selectorList) {
      for (const element of document.querySelectorAll(selector)) {
        const style = window.getComputedStyle(element);
        const rect = element.getBoundingClientRect();
        const visible =
          style.display !== "none" &&
          style.visibility !== "hidden" &&
          Number(style.opacity) !== 0 &&
          rect.width > 0 &&
          rect.height > 0;
        if (!visible) continue;
        entries.push({
          selector,
          left: rect.left,
          top: rect.top,
          right: rect.right,
          bottom: rect.bottom,
          width: rect.width,
          height: rect.height,
        });
      }
    }
    return entries;
  }, selectors);
}

function overlaps(first, second) {
  return first.left < second.right && first.right > second.left && first.top < second.bottom && first.bottom > second.top;
}

async function assertNoOverlap(page, label, selectors) {
  const rects = await visibleRects(page, selectors);
  for (let index = 0; index < rects.length; index += 1) {
    for (let nextIndex = index + 1; nextIndex < rects.length; nextIndex += 1) {
      const first = rects[index];
      const second = rects[nextIndex];
      if (first.selector === second.selector) continue;
      if (overlaps(first, second)) {
        throw new Error(`${label}: ${first.selector} overlaps ${second.selector} ${JSON.stringify({ first, second })}`);
      }
    }
  }
}

async function assertElementChipRowBalanced(page, label) {
  const metrics = await page.evaluate(() => {
    const row = document.querySelector(".element-chip-row");
    if (!row) return null;

    const chips = Array.from(row.querySelectorAll(".element-chip")).filter((chip) => {
      const rect = chip.getBoundingClientRect();
      const style = window.getComputedStyle(chip);
      return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0;
    });
    if (chips.length < 2) return null;

    const rowRect = row.getBoundingClientRect();
    const firstRect = chips[0].getBoundingClientRect();
    const lastRect = chips[chips.length - 1].getBoundingClientRect();
    const chipRects = chips.map((chip) => chip.getBoundingClientRect());

    return {
      chipCount: chips.length,
      rowWidth: rowRect.width,
      leftInset: firstRect.left - rowRect.left,
      rightInset: rowRect.right - lastRect.right,
      minChipHeight: Math.min(...chipRects.map((rect) => rect.height)),
      minChipWidth: Math.min(...chipRects.map((rect) => rect.width)),
    };
  });

  if (!metrics) return;
  if (metrics.minChipHeight < 44 || metrics.minChipWidth < 44) {
    throw new Error(
      `${label}: element chip touch size too small ${metrics.minChipWidth.toFixed(1)}x${metrics.minChipHeight.toFixed(1)}`,
    );
  }

  const imbalance = Math.abs(metrics.leftInset - metrics.rightInset);
  const tolerance = Math.max(12, metrics.rowWidth * 0.06);
  if (imbalance > tolerance) {
    throw new Error(
      `${label}: element row is not balanced for ${metrics.chipCount} chips, left ${metrics.leftInset.toFixed(1)}px vs right ${metrics.rightInset.toFixed(1)}px`,
    );
  }
}

async function assertAtomModelRenderable(page, label) {
  await page.locator(".atom-model-card").first().waitFor({ state: "visible", timeout: 10000 });
  await page.locator(".atom-canvas").first().waitFor({ state: "visible", timeout: 10000 });
  await page.waitForTimeout(300);

  const metrics = await page.evaluate(() => {
    const canvas = document.querySelector(".atom-canvas");
    const modeButtons = Array.from(document.querySelectorAll(".atom-mode-segment button"));
    if (!(canvas instanceof HTMLCanvasElement)) return null;
    const rect = canvas.getBoundingClientRect();
    let nonBlankPixelCount = 0;
    try {
      const context = canvas.getContext("2d");
      if (context && canvas.width > 0 && canvas.height > 0) {
        const sampleWidth = Math.min(canvas.width, 96);
        const sampleHeight = Math.min(canvas.height, 96);
        const imageData = context.getImageData(
          Math.max(0, Math.floor((canvas.width - sampleWidth) / 2)),
          Math.max(0, Math.floor((canvas.height - sampleHeight) / 2)),
          sampleWidth,
          sampleHeight,
        );
        for (let index = 3; index < imageData.data.length; index += 4) {
          if (imageData.data[index] > 0) nonBlankPixelCount += 1;
        }
      }
    } catch {
      nonBlankPixelCount = -1;
    }
    return {
      rectWidth: rect.width,
      rectHeight: rect.height,
      canvasWidth: canvas.width,
      canvasHeight: canvas.height,
      nonBlankPixelCount,
      modeButtonCount: modeButtons.length,
      modeButtonHeight: Math.min(...modeButtons.map((button) => button.getBoundingClientRect().height)),
    };
  });

  if (!metrics) throw new Error(`${label}: atom canvas was not found`);
  if (metrics.rectWidth < 180 || metrics.rectHeight < 180) {
    throw new Error(`${label}: atom canvas CSS size too small ${metrics.rectWidth}x${metrics.rectHeight}`);
  }
  if (metrics.canvasWidth < 180 || metrics.canvasHeight < 180) {
    throw new Error(`${label}: atom canvas backing size too small ${metrics.canvasWidth}x${metrics.canvasHeight}`);
  }
  if (metrics.nonBlankPixelCount === 0) {
    throw new Error(`${label}: atom canvas appears blank`);
  }
  if (metrics.modeButtonCount < 2 || metrics.modeButtonHeight < 34) {
    throw new Error(`${label}: atom mode controls are not reachable`);
  }
}

async function waitForAny(page, selectors, timeout = 10000) {
  const deadline = Date.now() + timeout;
  while (Date.now() < deadline) {
    for (const selector of selectors) {
      if (await page.locator(selector).first().isVisible().catch(() => false)) return selector;
    }
    await page.waitForTimeout(150);
  }
  throw new Error(`Timed out waiting for any selector: ${selectors.join(", ")}`);
}

async function submitVisibleAssessment(page) {
  const questionCards = page.locator("article.question-card");
  const questionCount = await questionCards.count();
  for (let index = 0; index < questionCount; index += 1) {
    const card = questionCards.nth(index);
    const option = card.locator("button.option").first();
    if (await option.isVisible().catch(() => false)) {
      await option.click();
    }
  }
  const submitButton = page.locator(".assessment-panel .sticky-action").first();
  await submitButton.waitFor({ state: "visible", timeout: 10000 });
  await submitButton.click();
}

async function clickRoot(page, root) {
  const tabButton = page.locator('.student-bottom-nav button[data-root="' + root + '"]').first();
  await tabButton.waitFor({ state: "visible", timeout: 10000 });
  await tabButton.click({ force: true });
  await page.waitForFunction(
    (rootId) => {
      const active = document.querySelector(".student-bottom-nav button.active");
      return window.location.pathname === "/" + rootId && active?.getAttribute("data-root") === rootId;
    },
    root,
    { timeout: 10000 },
  );
  await page.waitForFunction(() => window.scrollY === 0, null, { timeout: 10000 });
}

async function expectBottomNavHidden(page, label) {
  await page.waitForFunction(() => !document.querySelector(".student-bottom-nav"), null, { timeout: 10000 });
  const navCount = await page.locator(".student-bottom-nav").count();
  if (navCount > 0) throw new Error(label + ": bottom navigation should be hidden on detail route");
}

async function expectRootNav(page, root, label) {
  await page.locator(".student-bottom-nav").first().waitFor({ state: "visible", timeout: 10000 });
  await page.waitForFunction(
    (rootId) => document.querySelector(".student-bottom-nav button.active")?.getAttribute("data-root") === rootId,
    root,
    { timeout: 10000 },
  );
  await assertNoHorizontalOverflow(page, label);
}

async function ensureAuthenticatedShell(page) {
  const skipBarrierButton = page.locator(".success-panel button").first();
  if (await skipBarrierButton.isVisible().catch(() => false)) {
    await skipBarrierButton.click({ force: true });
  }
  await page.locator(".student-app-shell").first().waitFor({ state: "visible", timeout: 15000 });
}

function jsonResponse(payload, status = 200) {
  return {
    status,
    contentType: "application/json; charset=utf-8",
    body: JSON.stringify(payload),
  };
}

function sseResponse(events) {
  return {
    status: 200,
    contentType: "text/event-stream; charset=utf-8",
    body: events.map((event) => `event: ${event.event}\ndata: ${JSON.stringify(event.data || {})}\n\n`).join(""),
  };
}

async function installMockApi(page) {
  await page.route("**/api/auth/student/login", (route) =>
    route.fulfill(
      jsonResponse({
        access_token: "mobile-qa-token",
        token_type: "bearer",
        expires_at: "2099-01-01T00:00:00Z",
        user: mockUser,
      }),
    ),
  );
  await page.route("**/api/auth/me", (route) => route.fulfill(jsonResponse(mockUser)));
  await page.route("**/api/auth/logout", (route) => route.fulfill(jsonResponse({ ok: true })));
  await page.route("**/api/student/app-config", (route) =>
    route.fulfill(
      jsonResponse({
        features: {
          ai_assistant_enabled: true,
          feedback_enabled: true,
          student_ai_assistant_enabled: true,
          rag_access_enabled: true,
        },
      }),
    ),
  );
  await page.route("**/api/student/learning-home", (route) => route.fulfill(jsonResponse(mockLearningHome)));
  await page.route("**/api/student/learning-page**", (route) => route.fulfill(jsonResponse(mockLearningPage)));
  await page.route("**/api/student/experiment-groups/19-1", (route) => route.fulfill(jsonResponse(mockExperimentGroup)));
  await page.route("**/api/student/experiments/EXP_19_1_01", (route) =>
    route.fulfill(
      jsonResponse({
        id: mockLearningPoint.id,
        code: mockLearningPoint.code,
        title: mockLearningPoint.title,
        summary: mockLearningPoint.summary,
        parent_code: mockLearningPoint.parent_code,
        parent_title: mockLearningPoint.parent_title,
        module_title: mockLearningPoint.module_title,
        chapter_ids: mockLearningPoint.chapter_ids,
        video_candidate_count: mockLearningPoint.video_candidate_count,
        published_video_count: mockLearningPoint.published_video_count,
        question_count: mockLearningPoint.question_count,
        video_candidates: mockLearningPoint.video_candidates,
        videos: [],
      }),
    ),
  );
  await page.route("**/api/student/posttest/start", (route) => route.fulfill(jsonResponse(mockPosttest)));
  await page.route("**/api/student/posttest/submit", (route) =>
    route.fulfill(jsonResponse({ status: "completed", report: mockReport })),
  );
  await page.route("**/api/student/assistant/ask/stream", (route) =>
    route.fulfill(
      sseResponse([
        { event: "status", data: { message: "正在检索课程资料" } },
        {
          event: "delta",
          data: {
            delta: "### 回答思路\n\n- **现象**：CCl4 层变橙红色通常说明生成了 $\\ce{Br2}$。",
          },
        },
        {
          event: "final",
          data: {
            response: {
              text: "",
              source_count: 1,
              sources: [{ title: "卤素置换实验资料", section: "实验现象", chunk_id: "halogen-displacement" }],
            },
          },
        },
      ]),
    ),
  );
  await page.route("**/api/student/assistant/posttest-summary", (route) =>
    route.fulfill(jsonResponse({ text: "### 学习总结\n\n- 本轮重点是 **卤素置换**。", source: "ai", mode: "qa", cached: true })),
  );
  await page.route("**/api/student/assistant/posttest-mistakes", (route) =>
    route.fulfill(jsonResponse({ text: "暂无错题。", source: "fallback", mode: "qa", cached: true })),
  );
  await page.route("**/api/student/feedback", (route) =>
    route.fulfill(
      jsonResponse({
        id: "mobile-qa-feedback",
        student_id: mockUser.student_id,
        class_id: mockUser.class_id,
        feedback_type: "course_content",
        content: "移动端反馈 QA",
        status: "open",
        metadata: {},
        attachment_count: 1,
        attachments: [],
        created_at: null,
        updated_at: null,
      }),
    ),
  );
}

async function loginIfConfigured(page) {
  await page.goto(baseUrl, { waitUntil: "networkidle" });
  await assertNoHorizontalOverflow(page, "login");
  await page.locator(".auth-panel").first().waitFor({ state: "visible", timeout: 10000 });

  if (useMockApi) {
    await page.locator(".auth-form input").nth(0).fill(mockUser.student_id);
    await page.locator(".auth-form input").nth(1).fill("MobileQa2026!");
    await page.locator(".auth-form button[type='submit']").click();
    await page.locator(".success-panel").first().waitFor({ state: "visible", timeout: 15000 });
    await page.locator(".success-panel button").first().click({ force: true });
    await page.locator(".learning-panel").first().waitFor({ state: "visible", timeout: 15000 });
    return true;
  }

  if (!studentId || !password) {
    if (allowAuthSkip) return false;
    throw new Error("Set STUDENT_H5_QA_STUDENT_ID and STUDENT_H5_QA_PASSWORD, or set STUDENT_H5_QA_ALLOW_AUTH_SKIP=1.");
  }

  await page.locator(".auth-form input").nth(0).fill(studentId);
  await page.locator(".auth-form input").nth(1).fill(password);
  await page.locator(".auth-form button[type='submit']").click();

  const loginResult = await waitForAny(page, [".learning-panel", ".success-panel", ".assessment-panel", ".form-error"], 15000);
  if (loginResult === ".form-error") {
    const errorText = await page.locator(".form-error").first().innerText();
    throw new Error(`Login failed: ${errorText}`);
  }
  if (await page.locator(".success-panel").first().isVisible().catch(() => false)) {
    await page.locator(".success-panel button").first().click({ force: true });
  }
  if (await page.locator(".assessment-panel").first().isVisible().catch(() => false)) {
    throw new Error("Pretest rendered instead of the temporary skip barrier; provide an account that can enter learning directly.");
  }
  await page.locator(".learning-panel").first().waitFor({ state: "visible", timeout: 15000 });
  return true;
}

async function checkAuthenticatedFlows(page, viewportName) {
  await assertNoHorizontalOverflow(page, viewportName + ': initial route');
  await page.locator('.student-app-shell').first().waitFor({ state: 'visible', timeout: 10000 });
  const obsoleteFloatingCount = await page.locator('.ai-chat-toggle, .feedback-toggle, .ai-chat-fab, .feedback-fab').count();
  if (obsoleteFloatingCount > 0) {
    throw new Error(viewportName + ': obsolete floating AI/feedback entries are still rendered');
  }

  const roots = ['home', 'learn', 'ai', 'assessment', 'profile'];
  const navRoots = await page.locator('.student-bottom-nav button').evaluateAll((buttons) =>
    buttons.map((button) => button.getAttribute('data-root')),
  );
  if (JSON.stringify(navRoots) !== JSON.stringify(roots)) {
    throw new Error(viewportName + ': expected five root nav entries, got ' + JSON.stringify(navRoots));
  }

  for (const root of roots) {
    await clickRoot(page, root);
    await expectRootNav(page, root, viewportName + ': root /' + root);
  }

  await clickRoot(page, 'learn');
  await page.locator('.periodic-grid').first().waitFor({ state: 'visible', timeout: 10000 });
  await page.locator('.chapter-entry-card').first().click();
  await page.waitForURL(/\/chapter\/halogens-17/, { timeout: 10000 });
  await expectBottomNavHidden(page, viewportName + ': chapter detail');
  await page.locator('.chapter-element-summary').first().waitFor({ state: 'visible', timeout: 10000 });
  await page.locator('.learning-point-card').first().waitFor({ state: 'visible', timeout: 10000 });
  const chapterAtomCount = await page.locator('.atom-model-card').count();
  if (chapterAtomCount > 0) {
    throw new Error(viewportName + ': chapter detail should not render the full atom model');
  }
  const chapterSwitcherCount = await page.locator('.chapter-view-switcher').count();
  if (chapterSwitcherCount > 0) {
    throw new Error(viewportName + ': chapter detail should not render the old view switcher');
  }
  const chapterFinishCount = await page.locator('.finish-action').count();
  if (chapterFinishCount > 0) {
    throw new Error(viewportName + ': chapter detail should not render finish-learning action');
  }
  await assertElementChipRowBalanced(page, viewportName + ': chapter element chips');

  await page.locator('.chapter-element-detail-action').first().click();
  await page.waitForURL(/\/chapter\/halogens-17\/element\/Cl/, { timeout: 10000 });
  await expectBottomNavHidden(page, viewportName + ': element detail');
  await assertAtomModelRenderable(page, viewportName + ': element atom model');
  await page.goBack({ waitUntil: 'networkidle' });
  await page.waitForURL(/\/chapter\/halogens-17/, { timeout: 10000 });
  await page.waitForFunction(() => {
    const action = document.querySelector('.detail-page-actions .student-app-header-action');
    return action && !action.disabled;
  }, null, { timeout: 10000 });

  await page.locator('.detail-page-actions .student-app-header-action').first().click();
  await page.waitForURL(/\/ai\/chat/, { timeout: 10000 });
  await expectBottomNavHidden(page, viewportName + ': contextual chapter AI');
  await page.locator('.ai-chat-panel').first().waitFor({ state: 'visible', timeout: 10000 });
  await page.goBack({ waitUntil: 'networkidle' });
  await page.waitForURL(/\/chapter\/halogens-17/, { timeout: 10000 });

  await page.locator('.learning-point-card').first().waitFor({ state: 'visible', timeout: 10000 });
  await page.locator('.learning-point-card').first().click();
  await page.waitForURL(/\/point\/EXP_19_1_01/, { timeout: 10000 });
  await expectBottomNavHidden(page, viewportName + ': point detail');
  await assertNoHorizontalOverflow(page, viewportName + ': point detail');
  await assertNoOverlap(page, viewportName + ': point detail fixed action', ['.finish-action', '.pagebar']);

  await page.locator('.context-assistant-action').first().click();
  await page.waitForURL(/\/ai\/chat/, { timeout: 10000 });
  await expectBottomNavHidden(page, viewportName + ': contextual point AI');
  await page.goBack({ waitUntil: 'networkidle' });
  await page.waitForURL(/\/point\/EXP_19_1_01/, { timeout: 10000 });

  await page.locator('.finish-action').first().click();
  await page.waitForURL(/\/assessment\/session\/mobile-qa-posttest/, { timeout: 10000 });
  await expectBottomNavHidden(page, viewportName + ': assessment session');
  await page.locator('.assessment-panel').first().waitFor({ state: 'visible', timeout: 10000 });
  await submitVisibleAssessment(page);
  await page.waitForURL(/\/assessment\/report\/mobile-qa-posttest/, { timeout: 10000 });
  await expectBottomNavHidden(page, viewportName + ': assessment report');
  await page.locator('.summary-hero').first().waitFor({ state: 'visible', timeout: 10000 });
  await assertNoHorizontalOverflow(page, viewportName + ': assessment report');

  const reportAiAction = page.locator('.detail-page-actions .student-app-header-action').first();
  if (await reportAiAction.isVisible().catch(() => false)) {
    await reportAiAction.click();
    await page.waitForURL(/\/ai\/chat/, { timeout: 10000 });
    await expectBottomNavHidden(page, viewportName + ': contextual report AI');
    await page.goBack({ waitUntil: 'networkidle' });
    await page.waitForURL(/\/assessment\/report\/mobile-qa-posttest/, { timeout: 10000 });
  }

  await page.goto(baseUrl + '/profile', { waitUntil: 'networkidle' });
  await ensureAuthenticatedShell(page);
  await expectRootNav(page, 'profile', viewportName + ': profile root');
  await page.locator('.profile-entry-card').first().click();
  await page.waitForURL(/\/feedback\/new/, { timeout: 10000 });
  await expectBottomNavHidden(page, viewportName + ': feedback detail');
  const feedbackFile = {
    name: 'mobile-feedback.png',
    mimeType: 'image/png',
    buffer: Buffer.from([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]),
  };
  const feedbackInput = page.locator('.feedback-panel input[type="file"]').first();
  await feedbackInput.setInputFiles(feedbackFile);
  await page.locator('.feedback-file-pill').first().waitFor({ state: 'visible', timeout: 10000 });
  await page.locator('.feedback-file-pill').first().click();
  await page.locator('.feedback-file-pill').first().waitFor({ state: 'hidden', timeout: 10000 });
  await feedbackInput.setInputFiles(feedbackFile);
  await page.locator('.feedback-file-pill').first().waitFor({ state: 'visible', timeout: 10000 });
  await page.locator('.feedback-panel textarea').first().fill('mobile route stack feedback');
  await page.locator('.feedback-panel button[type="submit"]').first().click();
  await page.locator('.feedback-success').first().waitFor({ state: 'visible', timeout: 10000 });
  await assertNoHorizontalOverflow(page, viewportName + ': feedback detail');

  const directRoutes = [
    { path: '/home', root: 'home', selector: '.home-root-page' },
    { path: '/learn', root: 'learn', selector: '.periodic-grid' },
    { path: '/ai', root: 'ai', selector: '.assistant-intro-card' },
    { path: '/assessment', root: 'assessment', selector: '.assessment-home-panel' },
    { path: '/profile', root: 'profile', selector: '.profile-card' },
    { path: '/chapter/halogens-17', detail: true, selector: '.chapter-element-summary' },
    { path: '/chapter/halogens-17/element/Cl', detail: true, selector: '.atom-model-card' },
    { path: '/point/EXP_19_1_01', detail: true, selector: '.experiment-detail-card' },
    { path: '/ai/chat', detail: true, selector: '.ai-chat-panel' },
    { path: '/assessment/session/mobile-qa-posttest', detail: true, selector: '.assessment-panel' },
    { path: '/assessment/report/mobile-qa-posttest', detail: true, selector: '.summary-hero' },
    { path: '/feedback/new', detail: true, selector: '.feedback-panel' },
  ];

  for (const route of directRoutes) {
    await page.goto(baseUrl + route.path, { waitUntil: 'networkidle' });
    await ensureAuthenticatedShell(page);
    await page.locator(route.selector).first().waitFor({ state: 'visible', timeout: 15000 });
    if (route.detail) {
      await expectBottomNavHidden(page, viewportName + ': direct ' + route.path);
    } else {
      await expectRootNav(page, route.root, viewportName + ': direct ' + route.path);
    }
    await assertNoHorizontalOverflow(page, viewportName + ': direct ' + route.path);
  }
}

const playwright = await loadPlaywright();
const chromium = playwright.chromium || playwright.default?.chromium;
if (!chromium) {
  throw new Error("Playwright loaded, but chromium launcher was not available.");
}

async function launchBrowser() {
  try {
    return await chromium.launch({ headless: true });
  } catch (error) {
    const message = error instanceof Error ? error.message : String(error);
    if (!message.includes("Executable doesn't exist")) throw error;
    for (const channel of ["msedge", "chrome"]) {
      try {
        return await chromium.launch({ channel, headless: true });
      } catch {
        // Try the next locally installed browser channel.
      }
    }
    throw error;
  }
}

const browser = await launchBrowser();
const results = [];

try {
  for (const viewport of viewports) {
    try {
      const context = await browser.newContext({
        viewport: { width: viewport.width, height: viewport.height },
        isMobile: true,
        hasTouch: true,
        deviceScaleFactor: 2,
      });
      const page = await context.newPage();
      if (useMockApi) {
        await installMockApi(page);
      }
      const authenticated = await loginIfConfigured(page);
      if (authenticated) {
        await checkAuthenticatedFlows(page, viewport.name);
      }
      await context.close();
      results.push({ ...viewport, authenticated });
    } catch (error) {
      throw new Error(`${viewport.name} ${viewport.width}x${viewport.height}: ${error instanceof Error ? error.message : String(error)}`, {
        cause: error,
      });
    }
  }
} finally {
  await browser.close();
}

console.log(JSON.stringify({ baseUrl, results }, null, 2));
