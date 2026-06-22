import { randomBytes } from "node:crypto";
import { existsSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { chromium } from "playwright";

const repoRoot = new URL("../../../", import.meta.url);

const baseUrl = process.env.E2E_BASE_URL || "http://localhost:5174";
const apiBaseUrl = process.env.E2E_API_BASE_URL || "http://localhost:8000";
const username = process.env.E2E_ADMIN_USERNAME || "codex_smoke_admin";
const password = process.env.E2E_ADMIN_PASSWORD || randomBytes(18).toString("base64url");
const shouldBootstrap = process.env.E2E_SKIP_BOOTSTRAP !== "1" && !process.env.E2E_ADMIN_PASSWORD;

const smokePaths = [
  "/overview",
  "/experiments",
  "/videos",
  "/learning-assistant",
  "/question-banks",
  "/analytics",
];

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

function bootstrapSmokeAdmin() {
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
      "Smoke Admin",
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
        "Unable to prepare local smoke admin through Docker Compose.",
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

function isKnownAntdDeprecation(text) {
  return [
    "[antd: Space] `direction` is deprecated",
    "[antd: Tooltip] `overlayClassName` is deprecated",
    "[antd: Alert] `message` is deprecated",
    "[antd: Spin] `tip` is deprecated",
    "[antd: Drawer] `width` is deprecated",
  ].some((message) => text.includes(message));
}

async function main() {
  await requireHttpOk(`${apiBaseUrl}/health`, "backend");
  await requireHttpOk(`${baseUrl}/login`, "frontend");
  const bootstrap = bootstrapSmokeAdmin();
  const loginResponse = await login();

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

  const context = await browser.newContext({ viewport: { width: 1440, height: 980 } });
  await context.addInitScript((token) => {
    window.localStorage.setItem("chem_web_teacher_token", token);
  }, loginResponse.access_token);

  const diagnostics = {
    consoleMessages: [],
    knownAntdDeprecations: [],
    responses404: [],
    failedRequests: [],
    pageErrors: [],
  };
  let currentPath = "";

  context.on("response", (response) => {
    if (response.status() === 404) {
      diagnostics.responses404.push({
        path: currentPath,
        status: response.status(),
        method: response.request().method(),
        resourceType: response.request().resourceType(),
        url: response.url(),
      });
    }
  });
  context.on("requestfailed", (request) => {
    diagnostics.failedRequests.push({
      path: currentPath,
      method: request.method(),
      resourceType: request.resourceType(),
      url: request.url(),
      failure: request.failure()?.errorText ?? "unknown",
    });
  });

  const page = await context.newPage();
  page.on("console", (message) => {
    if (["warning", "error"].includes(message.type())) {
      const entry = {
        path: currentPath,
        type: message.type(),
        text: message.text(),
        location: message.location(),
      };
      diagnostics.consoleMessages.push(entry);
      if (isKnownAntdDeprecation(entry.text)) {
        diagnostics.knownAntdDeprecations.push(entry);
      }
    }
  });
  page.on("pageerror", (error) => {
    diagnostics.pageErrors.push({ path: currentPath, text: String(error) });
  });

  const results = [];
  for (const path of smokePaths) {
    currentPath = path;
    await page.goto(`${baseUrl}${path}`, { waitUntil: "domcontentloaded", timeout: 45_000 });
    await page.waitForTimeout(Number(process.env.E2E_SETTLE_MS || 2500));
    const text = await page.locator("body").innerText({ timeout: 15_000 });
    const url = page.url();
    const loginRedirected = url.includes("/login");
    const hasErrorOverlay =
      text.includes("Internal Server Error") ||
      text.includes("Failed to fetch") ||
      text.includes("Unhandled Runtime Error");
    results.push({
      path,
      url,
      textLength: text.trim().length,
      buttonCount: await page.locator("button").count(),
      loginRedirected,
      hasErrorOverlay,
      ok: !loginRedirected && !hasErrorOverlay && text.trim().length > 300,
    });
  }

  await browser.close();

  const failures = [];
  for (const result of results) {
    if (!result.ok) {
      failures.push(`Route failed smoke check: ${result.path}`);
    }
  }
  if (diagnostics.knownAntdDeprecations.length) {
    failures.push("Known Ant Design deprecation warnings were emitted.");
  }
  if (diagnostics.responses404.length) {
    failures.push("404 responses were observed.");
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
    results,
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
