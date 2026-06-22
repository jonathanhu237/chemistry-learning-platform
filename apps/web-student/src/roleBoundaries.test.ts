import { describe, expect, it } from "vitest";

import apiSource from "./api.ts?raw";
import appSource from "./App.tsx?raw";
import authUtilsSource from "./features/auth/authUtils.ts?raw";
import assistantPanelSource from "./features/assistant/StudentAiChatPanel.tsx?raw";
import authenticatedAppLayoutSource from "./app/shell/AuthenticatedAppLayout.tsx?raw";
import previewInputRuntimeSource from "./app/preview/input/PreviewInputRuntime.tsx?raw";
import periodicTableSource from "./features/periodic-table/PeriodicTable.tsx?raw";
import studentPackageSource from "../package.json?raw";
import { periodicElements } from "./periodic";
import {
  areaSwatches,
  periodicAreaIdForElement,
  periodicAreaOrder,
  profileAreaIds,
} from "./features/periodic-table/periodicHelpers";

const routeAndFeatureSources = import.meta.glob("./{routes,features}/**/*.{ts,tsx}", {
  query: "?raw",
  import: "default",
  eager: true,
}) as Record<string, string>;

describe("student console role boundaries", () => {
  it("keeps student routes on student APIs and rejects teacher/operator sessions", () => {
    expect(apiSource).toContain('api<AuthUser>("/api/auth/me")');
    expect(apiSource).toContain('"/api/preview/student-session/exchange"');
    expect(apiSource).not.toContain("/api/admin");
    expect(apiSource).not.toContain("/api/web-admin");
    expect(appSource).toContain('currentUser.role !== "student"');
    expect(authUtilsSource).toContain('response.user.role === "student"');
  });

  it("does not expose teacher notes or raw RAG/chunk traces in student AI metadata rendering", () => {
    expect(apiSource).not.toContain("teacher_note");
    expect(apiSource).not.toContain("chunk_id?:");
    expect(assistantPanelSource).not.toContain("chunk_id");
    expect(assistantPanelSource).not.toContain("score");
    expect(assistantPanelSource).toContain("引用资料");
    expect(assistantPanelSource).not.toMatch(/source\.(title|section)/);
  });

  it("keeps raw teacher-preview checks inside preview runtime boundaries", () => {
    const allowedPreviewAwareFiles = new Set([
      "routes/learn/PreviewCatalogPointPage.tsx",
      "features/catalog/CatalogPointDetailPanel.tsx",
    ]);
    const forbiddenPatterns = [
      { label: "previewMode", pattern: /\bpreviewMode\b/ },
      { label: "user.preview_mode", pattern: /\buser\.preview_mode\b/ },
      { label: "preview purpose", pattern: /preview_purpose|teacher_student_device_preview/ },
      { label: "preview identity", pattern: /00000000|施测平|数智一班/ },
      { label: "previewPolicy", pattern: /\bpreviewPolicy\b/ },
    ];
    const offenders = Object.entries(routeAndFeatureSources).flatMap(([file, source]) => {
      const sourcePath = file.replace(/^\.\//, "");
      if (/\.test\.(ts|tsx)$/.test(sourcePath)) return [];
      if (allowedPreviewAwareFiles.has(sourcePath)) return [];
      const matches = forbiddenPatterns.filter(({ pattern }) => pattern.test(source)).map(({ label }) => label);
      return matches.length ? [`${sourcePath}: ${matches.join(", ")}`] : [];
    });

    expect(offenders).toEqual([]);
  });

  it("keeps the mobile H5 root free of desktop iframe scrollbars", async () => {
    // @ts-expect-error The frontend tsconfig intentionally omits Node types, but Vitest runs this contract in Node.
    const { readFileSync } = await import("node:fs");
    const cwd = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
    const baseCssSource = readFileSync(`${cwd}/src/styles/base.css`, "utf8");

    expect(baseCssSource).toContain("overflow-x: hidden");
    expect(baseCssSource).toContain("scrollbar-width: none");
    expect(baseCssSource).toContain("html::-webkit-scrollbar");
    expect(baseCssSource).toContain("body::-webkit-scrollbar");
  });

  it("scopes the simulated touch runtime to teacher preview infrastructure", async () => {
    // @ts-expect-error The frontend tsconfig intentionally omits Node types, but Vitest runs this contract in Node.
    const { readFileSync } = await import("node:fs");
    const cwd = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
    const appShellCssSource = readFileSync(`${cwd}/src/styles/app-shell.css`, "utf8");

    expect(authenticatedAppLayoutSource).toContain("baseContext.user.preview_mode || appConfig.preview_mode");
    expect(authenticatedAppLayoutSource).toContain("<PreviewInputRuntime />");
    expect(previewInputRuntimeSource).toContain("window.addEventListener(\"message\"");
    expect(previewInputRuntimeSource).toContain("elementFromPreviewPoint");
    expect(previewInputRuntimeSource).toContain("findScrollablePreviewTarget");
    expect(previewInputRuntimeSource).not.toContain("@use-gesture/react");
    expect(studentPackageSource).not.toContain("@use-gesture/react");
    expect(appShellCssSource).not.toContain(".student-preview-runtime-touch-cursor");
    expect(appShellCssSource).not.toContain(".student-preview-touch-runtime");
  });

  it("keeps the mobile bottom nav fully offscreen while compressed", async () => {
    // @ts-expect-error The frontend tsconfig intentionally omits Node types, but Vitest runs this contract in Node.
    const { readFileSync } = await import("node:fs");
    const cwd = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
    const appShellCssSource = readFileSync(`${cwd}/src/styles/app-shell.css`, "utf8");

    expect(authenticatedAppLayoutSource).not.toContain("setTimeout(() => setNavCompressed(false)");
    expect(appShellCssSource).toContain(".student-app-shell.nav-compressed .student-bottom-nav");
    expect(appShellCssSource).toContain("pointer-events: none;");
    expect(appShellCssSource).toContain("translateY(calc(100% + 2px))");
    expect(appShellCssSource).not.toContain("opacity: 0;");
    expect(appShellCssSource).not.toContain("opacity 180ms ease");
    expect(appShellCssSource).not.toContain("opacity: 0.14");
    expect(appShellCssSource).not.toContain("var(--mobile-bottom-nav-height) * 0.62");
  });

  it("keeps the visible mobile bottom nav opaque and free of default focus boxes", async () => {
    // @ts-expect-error The frontend tsconfig intentionally omits Node types, but Vitest runs this contract in Node.
    const { readFileSync } = await import("node:fs");
    const cwd = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
    const appShellCssSource = readFileSync(`${cwd}/src/styles/app-shell.css`, "utf8");
    const bottomNavBlock = appShellCssSource.match(/\.student-bottom-nav\s*\{[^}]*\}/)?.[0] || "";

    expect(bottomNavBlock).toContain("height: calc(var(--mobile-bottom-nav-height) + env(safe-area-inset-bottom, 0px));");
    expect(bottomNavBlock).toContain("overflow: hidden;");
    expect(bottomNavBlock).toContain("background: #fffdf6;");
    expect(bottomNavBlock).not.toContain("background: rgba(255, 253, 246");
    expect(bottomNavBlock).not.toContain("backdrop-filter: blur(18px)");
    expect(appShellCssSource).toContain(".student-bottom-nav button:focus");
    expect(appShellCssSource).toContain("outline-style: none;");
    expect(appShellCssSource).toContain("outline-width: 0;");
    expect(appShellCssSource).toContain(".student-bottom-nav button:focus-visible");
  });

  it("locks the student periodic learning taxonomy without the removed combined area", () => {
    const bySymbol = new Map(periodicElements.map((element) => [element.symbol, element]));

    expect(periodicAreaOrder).toEqual(["hydrogen", "p", "s", "ds", "d", "f"]);
    expect(Object.keys(areaSwatches)).toEqual(["hydrogen", "p", "s", "ds", "d", "f"]);
    expect(areaSwatches).toMatchObject({
      hydrogen: "#6f9f2e",
      p: "#0f8f72",
      s: "#9a6a11",
      ds: "#c89a2d",
      d: "#9e2f3d",
      f: "#8d4f9f",
    });
    expect(periodicAreaIdForElement(bySymbol.get("H")!)).toBe("hydrogen");
    ["He", "Ne", "Ar", "Kr", "Xe", "Rn", "Og"].forEach((symbol) => {
      expect(periodicAreaIdForElement(bySymbol.get(symbol)!)).toBe("p");
    });
    ["La", "Lu", "Ac", "Lr"].forEach((symbol) => {
      expect(periodicAreaIdForElement(bySymbol.get(symbol)!)).toBe("f");
    });
    expect(profileAreaIds({ chapter_id: "CH21" } as Parameters<typeof profileAreaIds>[0])).toEqual(["f"]);
    expect(profileAreaIds({ chapter_id: "CH22" } as Parameters<typeof profileAreaIds>[0])).toEqual(["hydrogen", "p"]);
  });

  it("keeps recommendation chrome out of the periodic table selector", async () => {
    // @ts-expect-error The frontend tsconfig intentionally omits Node types, but Vitest runs this contract in Node.
    const { readFileSync } = await import("node:fs");
    const cwd = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
    const periodicCssSource = readFileSync(`${cwd}/src/styles/periodic-table.css`, "utf8");

    expect(periodicTableSource).not.toContain("recommendedArea");
    expect(periodicTableSource).not.toContain("recommendedSymbols");
    expect(periodicTableSource).not.toContain("selectedArea");
    expect(periodicTableSource).not.toContain("learnableSymbols");
    expect(periodicCssSource).not.toContain("area-legend button.selected");
    expect(periodicCssSource).not.toContain("selected-area");
    expect(periodicCssSource).not.toContain("learnable-element");
    expect(periodicCssSource).not.toContain("muted-area");
    expect(periodicCssSource).not.toContain("recommended-area");
    expect(periodicCssSource).not.toContain("recommended-element");
  });
});
