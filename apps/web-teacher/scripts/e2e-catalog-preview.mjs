import { randomBytes } from "node:crypto";
import { existsSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { chromium } from "playwright";

const repoRoot = new URL("../../../", import.meta.url);

const baseUrl = process.env.E2E_BASE_URL || "http://localhost:5174";
const apiBaseUrl = process.env.E2E_API_BASE_URL || "http://localhost:8000";
const username = process.env.E2E_ADMIN_USERNAME || "codex_catalog_preview_admin";
const password = process.env.E2E_ADMIN_PASSWORD || randomBytes(18).toString("base64url");
const shouldBootstrap = process.env.E2E_SKIP_BOOTSTRAP !== "1" && !process.env.E2E_ADMIN_PASSWORD;

function candidateChromePaths() {
  const paths = [];
  if (process.env.E2E_CHROME_PATH) {
    paths.push(process.env.E2E_CHROME_PATH);
  }
  if (process.platform === "win32") {
    const programFiles = process.env.ProgramFiles || "C:\\Program Files";
    const programFilesX86 = process.env["ProgramFiles(x86)"] || "C:\\Program Files (x86)";
    paths.push(
      `${programFiles}\\Google\\Chrome\\Application\\chrome.exe`,
      `${programFilesX86}\\Google\\Chrome\\Application\\chrome.exe`,
      `${programFiles}\\Microsoft\\Edge\\Application\\msedge.exe`,
      `${programFilesX86}\\Microsoft\\Edge\\Application\\msedge.exe`,
    );
  }
  return paths.filter((candidate) => candidate && existsSync(candidate));
}

async function requireHttpOk(url, name) {
  let response;
  try {
    response = await fetch(url);
  } catch (error) {
    throw new Error(`${name} is not reachable at ${url}: ${String(error)}`);
  }
  if (!response.ok) {
    throw new Error(`${name} returned HTTP ${response.status} at ${url}`);
  }
}

function bootstrapAdmin() {
  if (!shouldBootstrap) {
    return { skipped: true, reason: process.env.E2E_ADMIN_PASSWORD ? "password provided" : "E2E_SKIP_BOOTSTRAP=1" };
  }

  const result = spawnSync(
    "docker",
    [
      "compose",
      "exec",
      "-T",
      "-e",
      "PYTHONPATH=/app",
      "backend",
      "python",
      "scripts/bootstrap_admin.py",
      "--skip-migrations",
      "--username",
      username,
      "--display-name",
      "Catalog Preview E2E Admin",
      "--role",
      "admin",
      "--password",
      password,
    ],
    {
      cwd: repoRoot,
      encoding: "utf8",
    },
  );

  if (result.status !== 0) {
    throw new Error(
      [
        "Unable to prepare local catalog preview admin through Docker Compose.",
        "Start the backend service or set E2E_ADMIN_PASSWORD for an existing local admin.",
        result.stdout,
        result.stderr,
      ]
        .filter(Boolean)
        .join("\n"),
    );
  }

  return { skipped: false, username };
}

async function login() {
  const response = await fetch(`${apiBaseUrl}/api/auth/login`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (!response.ok) {
    throw new Error(`login failed with HTTP ${response.status}: ${await response.text()}`);
  }
  return response.json();
}

async function api(path, token) {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    headers: { authorization: `Bearer ${token}` },
  });
  if (!response.ok) {
    throw new Error(`${path} failed with HTTP ${response.status}: ${await response.text()}`);
  }
  return response.json();
}

async function findPreviewCandidate(token) {
  const chapters = await api("/api/chapters", token);
  const preferredChapters = [
    ...chapters.filter((chapter) => chapter.chapter_id === "CH13"),
    ...chapters.filter((chapter) => chapter.chapter_id !== "CH13" && chapter.chapter_id !== "CH00"),
    ...chapters.filter((chapter) => chapter.chapter_id === "CH00"),
  ];

  for (const chapter of preferredChapters) {
    const roots = (await api(`/api/admin/catalog/chapters/${encodeURIComponent(chapter.chapter_id)}/roots`, token)).nodes;
    for (const root of roots) {
      const found = await findPointBelow(root, token);
      if (found) {
        return { chapter, root: found.root, point: found.point };
      }
    }
  }

  throw new Error("No catalog point is available for preview E2E.");
}

async function findPointBelow(root, token) {
  if (root.node_kind === "point") {
    return { root, point: root };
  }
  if (!root.has_children) {
    return null;
  }
  const response = await api(`/api/admin/catalog/nodes/${encodeURIComponent(root.node_id)}/children`, token);
  const directPoint = response.children.find((child) => child.node_kind === "point");
  if (directPoint) {
    return { root, point: directPoint };
  }
  for (const child of response.children) {
    const nested = await findPointBelow(child, token);
    if (nested) {
      return { root, point: nested.point };
    }
  }
  return null;
}

async function main() {
  await requireHttpOk(`${apiBaseUrl}/health`, "backend");
  await requireHttpOk(`${baseUrl}/login`, "teacher frontend");
  const bootstrap = bootstrapAdmin();
  const loginResponse = await login();
  const candidate = await findPreviewCandidate(loginResponse.access_token);

  const launchOptions = { headless: true };
  const chromePath = candidateChromePaths()[0];
  if (chromePath) {
    launchOptions.executablePath = chromePath;
  }

  let browser;
  try {
    browser = await chromium.launch(launchOptions);
  } catch (error) {
    throw new Error(
      [
        `Unable to launch a Chromium browser: ${String(error)}`,
        "Set E2E_CHROME_PATH to a local Chrome/Edge executable or install Playwright browsers.",
      ].join("\n"),
    );
  }

  const diagnostics = {
    failedRequests: [],
    pageErrors: [],
    consoleMessages: [],
  };

  const context = await browser.newContext({ viewport: { width: 1440, height: 980 } });
  await context.addInitScript((token) => {
    window.localStorage.setItem("chem_web_teacher_token", token);
  }, loginResponse.access_token);
  context.on("requestfailed", (request) => {
    diagnostics.failedRequests.push({
      method: request.method(),
      resourceType: request.resourceType(),
      url: request.url(),
      failure: request.failure()?.errorText ?? "unknown",
    });
  });

  const page = await context.newPage();
  page.on("pageerror", (error) => diagnostics.pageErrors.push({ page: "teacher", text: String(error) }));
  page.on("console", (message) => {
    if (["error", "warning"].includes(message.type())) {
      diagnostics.consoleMessages.push({ page: "teacher", type: message.type(), text: message.text() });
    }
  });

  await page.goto(`${baseUrl}/experiments`, { waitUntil: "domcontentloaded", timeout: 45_000 });
  await page.waitForTimeout(Number(process.env.E2E_SETTLE_MS || 2500));
  await page.getByText(candidate.root.title, { exact: true }).first().click({ timeout: 15_000 });
  await page.waitForTimeout(1000);
  await page.getByText(candidate.point.title, { exact: true }).first().click({ timeout: 15_000 });
  await page.waitForTimeout(1200);

  const [popup] = await Promise.all([
    page.waitForEvent("popup", { timeout: 15_000 }),
    page.locator(".catalog-editor-header-actions button").first().click(),
  ]);
  popup.on("pageerror", (error) => diagnostics.pageErrors.push({ page: "preview", text: String(error) }));
  popup.on("console", (message) => {
    if (["error", "warning"].includes(message.type())) {
      diagnostics.consoleMessages.push({ page: "preview", type: message.type(), text: message.text() });
    }
  });

  await popup.waitForLoadState("domcontentloaded", { timeout: 45_000 });
  await popup.locator(".catalog-preview-device-select").waitFor({ state: "visible", timeout: 15_000 });
  await popup.locator("iframe.catalog-preview-iframe").waitFor({ state: "visible", timeout: 15_000 });
  await popup.frameLocator("iframe.catalog-preview-iframe").locator("body").waitFor({ state: "visible", timeout: 15_000 });
  await popup.waitForTimeout(1500);

  const teacherFallbackVisible = await page.locator(".catalog-preview-fallback").isVisible().catch(() => false);
  const iframeText = await popup.frameLocator("iframe.catalog-preview-iframe").locator("body").innerText({ timeout: 15_000 });
  const titleRendered = iframeText.includes(candidate.point.title);
  if (!titleRendered) {
    throw new Error(`Student preview iframe did not render selected point title: ${candidate.point.title}`);
  }

  await popup.locator(".catalog-preview-device-select").click();
  await popup.locator(".ant-select-item-option").filter({ hasText: "HUAWEI Mate 80 Pro" }).click({ timeout: 15_000 });
  await popup.waitForTimeout(500);
  const deviceSelectText = await popup.locator(".catalog-preview-device-select").innerText();
  const huaweiSelected = deviceSelectText.includes("HUAWEI Mate 80 Pro");
  if (!huaweiSelected) {
    throw new Error(`Device selector did not switch to HUAWEI Mate 80 Pro. Current text: ${deviceSelectText}`);
  }

  const [pagePreview] = await Promise.all([
    popup.waitForEvent("popup", { timeout: 15_000 }),
    popup.locator(".catalog-preview-page-button").click(),
  ]);
  pagePreview.on("pageerror", (error) => diagnostics.pageErrors.push({ page: "student-page-preview", text: String(error) }));
  pagePreview.on("console", (message) => {
    if (["error", "warning"].includes(message.type())) {
      diagnostics.consoleMessages.push({ page: "student-page-preview", type: message.type(), text: message.text() });
    }
  });
  await pagePreview.waitForLoadState("domcontentloaded", { timeout: 45_000 });
  await pagePreview.locator("body").waitFor({ state: "visible", timeout: 15_000 });
  await pagePreview.waitForTimeout(1000);
  const pagePreviewText = await pagePreview.locator("body").innerText({ timeout: 15_000 });
  const pagePreviewTitleRendered = pagePreviewText.includes(candidate.point.title);
  if (!pagePreviewTitleRendered) {
    throw new Error(`Student page preview did not render selected point title: ${candidate.point.title}`);
  }
  const pagePreviewViewport = await pagePreview.evaluate(() => ({
    innerWidth: window.innerWidth,
    outerWidth: window.outerWidth,
  }));
  const pagePreviewMobileSized =
    pagePreviewViewport.innerWidth >= 320 && pagePreviewViewport.innerWidth <= 620;
  if (!pagePreviewMobileSized) {
    throw new Error(`Student page preview opened with a desktop-sized viewport: ${JSON.stringify(pagePreviewViewport)}`);
  }

  await browser.close();

  const failures = [];
  if (teacherFallbackVisible) {
    failures.push("Preview fallback modal appeared even though the popup opened.");
  }
  if (diagnostics.failedRequests.length) {
    failures.push("Failed network requests were observed.");
  }
  if (diagnostics.pageErrors.length) {
    failures.push("Page errors were observed.");
  }
  if (diagnostics.consoleMessages.length) {
    failures.push("Console warnings or errors were observed.");
  }

  const summary = {
    ok: failures.length === 0,
    baseUrl,
    apiBaseUrl,
    username,
    bootstrap,
    candidate: {
      chapter_id: candidate.chapter.chapter_id,
      root_node_id: candidate.root.node_id,
      root_title: candidate.root.title,
      point_node_id: candidate.point.node_id,
      point_title: candidate.point.title,
    },
    preview: {
      popup_url: popup.url(),
      title_rendered: titleRendered,
      selected_device: deviceSelectText,
      page_preview_url: pagePreview.url(),
      page_preview_title_rendered: pagePreviewTitleRendered,
      page_preview_viewport: pagePreviewViewport,
      page_preview_mobile_sized: pagePreviewMobileSized,
      fallback_visible: teacherFallbackVisible,
    },
    diagnostics,
    failures,
  };

  console.log(JSON.stringify(summary, null, 2));
  if (!summary.ok) {
    process.exitCode = 1;
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.stack || error.message : String(error));
  process.exit(1);
});
