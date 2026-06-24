import { createServer } from "node:http";
import { createRequire } from "node:module";
import fs from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const require = createRequire(import.meta.url);
const appDir = path.resolve(import.meta.dirname, "..");
const teacherWebDir = path.resolve(appDir, "../web-teacher");
const distDir = path.join(appDir, "dist");

const mockUser = {
  id: "catalog-footer-qa-student",
  username: "catalog-footer-qa",
  role: "student",
  display_name: "Catalog Footer QA",
  status: "active",
  must_change_password: false,
  password_version: 1,
  student_id: "catalog-footer-qa",
  class_id: "qa-class",
  class_name: "QA Class",
  preview_mode: true,
};

const profile = {
  profile_id: "halogens-17",
  chapter_id: "CH17",
  title: "Chapter 17 Halogens",
  subtitle: "p block elements",
  family_number: "17",
  family_name: "Halogens",
  hero: {
    eyebrow: "p block",
    title: "Halogen learning",
    summary: "Catalog footer layout QA.",
  },
  default_element_symbol: "Cl",
  element_symbols: ["Cl", "Br", "I"],
  elements: [
    {
      symbol: "Cl",
      name: "Chlorine",
      atomic_number: 17,
      card_focus: "Oxidation and displacement",
      card_relevance: "Use this element context while browsing the catalog.",
      card_tags: ["17 group", "gas", "oxidizer"],
      group: "17",
      period: 3,
      block: "p",
      state: "Gas",
      common_valence: "-1, +1, +5, +7",
    },
  ],
  property_cards: [],
  family_common_properties: [],
  property_sections: [],
  reference_media: [],
};

function catalogNode(node_id, node_kind, title, parent_id = null) {
  return {
    node_id,
    chapter_id: "CH17",
    parent_id,
    node_kind,
    title,
    summary: "",
    status: "published",
    display_order: 1,
    actions: [node_kind === "directory" ? "open_directory" : "open_point"],
    has_children: node_kind === "directory",
    has_point_content: node_kind === "point",
    media_count: 0,
    published_media_count: 0,
  };
}

const shortDirectoryNode = catalogNode("cat-dir-short", "directory", "Short catalog");
const longDirectoryNode = catalogNode("cat-dir-long", "directory", "Long catalog");
const rootCatalog = {
  chapter_id: "CH17",
  chapter_title: "Chapter 17 Halogens",
  nodes: [shortDirectoryNode, longDirectoryNode],
};

const shortDirectory = {
  node: shortDirectoryNode,
  breadcrumbs: [{ node_id: shortDirectoryNode.node_id, title: shortDirectoryNode.title, node_kind: "directory", chapter_id: "CH17" }],
  children: [
    catalogNode("cat-point-short-1", "point", "Short experiment one", shortDirectoryNode.node_id),
    catalogNode("cat-point-short-2", "point", "Short experiment two", shortDirectoryNode.node_id),
  ],
};

const longDirectory = {
  node: longDirectoryNode,
  breadcrumbs: [{ node_id: longDirectoryNode.node_id, title: longDirectoryNode.title, node_kind: "directory", chapter_id: "CH17" }],
  children: Array.from({ length: 30 }, (_, index) => catalogNode(`cat-point-long-${index + 1}`, "point", `Long experiment ${index + 1}`, longDirectoryNode.node_id)),
};

function jsonResponse(body) {
  return {
    status: 200,
    contentType: "application/json; charset=utf-8",
    body: JSON.stringify(body),
  };
}

async function loadPlaywright() {
  const playwrightPath = require.resolve("playwright", { paths: [appDir, teacherWebDir, process.cwd()] });
  const playwright = await import(pathToFileURL(playwrightPath).href);
  return playwright.chromium ? playwright : playwright.default;
}

function contentTypeFor(filePath) {
  if (filePath.endsWith(".html")) return "text/html; charset=utf-8";
  if (filePath.endsWith(".js")) return "text/javascript; charset=utf-8";
  if (filePath.endsWith(".css")) return "text/css; charset=utf-8";
  if (filePath.endsWith(".svg")) return "image/svg+xml; charset=utf-8";
  if (filePath.endsWith(".woff2")) return "font/woff2";
  if (filePath.endsWith(".woff")) return "font/woff";
  if (filePath.endsWith(".ttf")) return "font/ttf";
  return "application/octet-stream";
}

async function fileExists(filePath) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

async function candidateBrowserPaths() {
  const programFiles = process.env.ProgramFiles;
  const programFilesX86 = process.env["ProgramFiles(x86)"];
  const localAppData = process.env.LOCALAPPDATA;
  const candidates = [
    programFiles ? path.join(programFiles, "Google/Chrome/Application/chrome.exe") : "",
    programFilesX86 ? path.join(programFilesX86, "Google/Chrome/Application/chrome.exe") : "",
    localAppData ? path.join(localAppData, "Google/Chrome/Application/chrome.exe") : "",
    programFiles ? path.join(programFiles, "Microsoft/Edge/Application/msedge.exe") : "",
    programFilesX86 ? path.join(programFilesX86, "Microsoft/Edge/Application/msedge.exe") : "",
  ].filter(Boolean);
  const existing = [];
  for (const candidate of candidates) {
    if (await fileExists(candidate)) existing.push(candidate);
  }
  return existing;
}

async function launchBrowser(chromium) {
  for (const channel of ["chrome", "msedge"]) {
    try {
      return await chromium.launch({ channel, headless: true });
    } catch {
      // Try the next locally installed browser option.
    }
  }
  for (const executablePath of await candidateBrowserPaths()) {
    try {
      return await chromium.launch({ executablePath, headless: true });
    } catch {
      // Try the next executable path.
    }
  }
  return chromium.launch({ headless: true });
}

async function createStaticServer() {
  const indexHtml = await fs.readFile(path.join(distDir, "index.html"));
  const server = createServer(async (request, response) => {
    try {
      const url = new URL(request.url || "/", "http://127.0.0.1");
      const candidate = path.normalize(path.join(distDir, url.pathname));
      const insideDist = candidate === distDir || candidate.startsWith(`${distDir}${path.sep}`);
      if (insideDist && path.extname(candidate)) {
        const bytes = await fs.readFile(candidate);
        response.writeHead(200, { "Content-Type": contentTypeFor(candidate) });
        response.end(bytes);
        return;
      }
      response.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      response.end(indexHtml);
    } catch {
      response.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      response.end(indexHtml);
    }
  });
  await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
  return server;
}

async function installMockApi(page) {
  await page.route("**/api/auth/me", (route) => route.fulfill(jsonResponse(mockUser)));
  await page.route("**/api/student/app-config", (route) =>
    route.fulfill(
      jsonResponse({
        features: {
          ai_assistant_enabled: true,
          feedback_enabled: true,
          student_ai_assistant_enabled: true,
          rag_access_enabled: true,
        },
        preview_mode: false,
        preview_policy: null,
      }),
    ),
  );
  await page.route("**/api/student/learning-page**", (route) =>
    route.fulfill(
      jsonResponse({
        recommended_profile_id: profile.profile_id,
        profiles: [
          {
            profile_id: profile.profile_id,
            chapter_id: profile.chapter_id,
            title: profile.title,
            subtitle: profile.subtitle,
            family_number: profile.family_number,
            family_name: profile.family_name,
            element_symbols: profile.element_symbols,
          },
        ],
        active_profile: profile,
      }),
    ),
  );
  await page.route("**/api/student/chapters/CH17/catalog", (route) => route.fulfill(jsonResponse(rootCatalog)));
  await page.route("**/api/student/catalog/nodes/cat-dir-short", (route) => route.fulfill(jsonResponse(shortDirectory)));
  await page.route("**/api/student/catalog/nodes/cat-dir-long", (route) => route.fulfill(jsonResponse(longDirectory)));
}

async function readGeometry(page) {
  return page.evaluate(() => {
    const grid = document.querySelector(".catalog-node-grid");
    const footer = document.querySelector(".catalog-end-marker");
    const browser = document.querySelector(".family-catalog-browser");
    if (!grid || !footer || !browser) return null;
    const gridRect = grid.getBoundingClientRect();
    const footerRect = footer.getBoundingClientRect();
    const browserRect = browser.getBoundingClientRect();
    return {
      grid: { top: gridRect.top, bottom: gridRect.bottom, height: gridRect.height },
      footer: { top: footerRect.top, bottom: footerRect.bottom, height: footerRect.height },
      browser: { top: browserRect.top, bottom: browserRect.bottom, height: browserRect.height },
      scrollTop: grid.scrollTop,
      scrollHeight: grid.scrollHeight,
      clientHeight: grid.clientHeight,
    };
  });
}

function assertClose(name, actual, expected, tolerance = 4) {
  const delta = Math.abs(actual - expected);
  if (delta > tolerance) throw new Error(`${name} expected ${expected.toFixed(2)}, got ${actual.toFixed(2)} (delta ${delta.toFixed(2)})`);
}

async function openCatalog(page, baseUrl, nodeId) {
  await page.goto(`${baseUrl}/catalog/${nodeId}?profileId=halogens-17&from=chapter`, { waitUntil: "networkidle" });
  await page.waitForSelector(".catalog-end-marker", { timeout: 10000 });
}

async function main() {
  await fs.access(path.join(distDir, "index.html"));
  let server = null;
  let browser = null;

  try {
    server = await createStaticServer();
    const address = server.address();
    const baseUrl = `http://127.0.0.1:${address.port}`;
    const { chromium } = await loadPlaywright();
    browser = await launchBrowser(chromium);
    const page = await browser.newPage({ viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true });
    await page.addInitScript(() => window.localStorage.setItem("chem_student_token", "catalog-footer-qa-token"));
    await installMockApi(page);

    await openCatalog(page, baseUrl, "cat-dir-short");
    const shortGeometry = await readGeometry(page);
    if (!shortGeometry) throw new Error("Short catalog geometry was not readable.");
    if (shortGeometry.scrollHeight > shortGeometry.clientHeight + 4) {
      throw new Error(`Short catalog should not scroll: scrollHeight=${shortGeometry.scrollHeight}, clientHeight=${shortGeometry.clientHeight}`);
    }
    assertClose("Short footer bottom", shortGeometry.footer.bottom, shortGeometry.grid.bottom);
    assertClose("Short grid bottom", shortGeometry.grid.bottom, shortGeometry.browser.bottom);

    await openCatalog(page, baseUrl, "cat-dir-long");
    const initialLongGeometry = await readGeometry(page);
    if (!initialLongGeometry) throw new Error("Long catalog initial geometry was not readable.");
    if (initialLongGeometry.scrollHeight <= initialLongGeometry.clientHeight + 4) {
      throw new Error(`Long catalog should scroll: scrollHeight=${initialLongGeometry.scrollHeight}, clientHeight=${initialLongGeometry.clientHeight}`);
    }
    if (initialLongGeometry.footer.top < initialLongGeometry.grid.bottom) {
      throw new Error("Long catalog footer should not be visible before scrolling to the bottom.");
    }
    await page.$eval(".catalog-node-grid", (grid) => {
      grid.scrollTop = grid.scrollHeight;
    });
    await page.waitForTimeout(80);
    const finalLongGeometry = await readGeometry(page);
    if (!finalLongGeometry) throw new Error("Long catalog final geometry was not readable.");
    assertClose("Long footer bottom after scroll", finalLongGeometry.footer.bottom, finalLongGeometry.grid.bottom);
  } finally {
    if (browser) await browser.close();
    if (server) await new Promise((resolve) => server.close(resolve));
  }
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
