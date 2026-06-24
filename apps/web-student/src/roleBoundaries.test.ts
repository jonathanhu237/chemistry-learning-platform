import { describe, expect, it } from "vitest";

import apiSource from "./api.ts?raw";
import appSource from "./App.tsx?raw";
import studentBottomNavSource from "./app/shell/StudentBottomNav.tsx?raw";
import authUtilsSource from "./features/auth/authUtils.ts?raw";
import assistantPanelSource from "./features/assistant/StudentAiChatPanel.tsx?raw";
import authenticatedAppLayoutSource from "./app/shell/AuthenticatedAppLayout.tsx?raw";
import previewInputRuntimeSource from "./app/preview/input/PreviewInputRuntime.tsx?raw";
import periodicTableSource from "./features/periodic-table/PeriodicTable.tsx?raw";
import pointVideoPlayerSource from "./features/catalog/PointVideoPlayer.tsx?raw";
import homeRootPageSource from "./routes/home/HomeRootPage.tsx?raw";
import unifiedSearchSource from "./routes/search/UnifiedSearchPage.tsx?raw";
import backArrowIconSource from "./shared/mobile/BackArrowIcon.tsx?raw";
import pagebarSource from "./shared/mobile/PageBar.tsx?raw";
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
    expect(assistantPanelSource).toContain("safeAssistantSourceCount");
    expect(assistantPanelSource).toContain("ai-message-citation");
    expect(assistantPanelSource).toContain("Citation count");
    expect(assistantPanelSource).not.toMatch(/source\.(title|section)/);
  });

  it("keeps raw teacher-preview checks inside preview runtime boundaries", () => {
    const allowedPreviewAwareFiles = new Set([
      "routes/learn/PreviewCatalogNodePage.tsx",
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
    expect(baseCssSource).toMatch(/body\s*\{[^}]*min-height: 100vh;[^}]*min-height: 100dvh;/s);
    expect(baseCssSource).toMatch(/\.app-shell\s*\{[^}]*min-height: 100vh;[^}]*min-height: 100dvh;/s);
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

  it("keeps the home header quick-return on the passive nav-compressed pattern", async () => {
    // @ts-expect-error The frontend tsconfig intentionally omits Node types, but Vitest runs this contract in Node.
    const { readFileSync } = await import("node:fs");
    const cwd = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
    const appShellCssSource = readFileSync(`${cwd}/src/styles/app-shell.css`, "utf8");
    const homeHeaderBlock = appShellCssSource.match(/\.student-app-shell\.root-route\.root-home \.student-app-header\s*\{[^}]*\}/)?.[0] || "";
    const homeCompressedBlock =
      appShellCssSource.match(/\.student-app-shell\.root-route\.root-home\.nav-compressed \.student-app-header\s*\{[^}]*\}/)?.[0] || "";
    const homeRouteContentBlock =
      appShellCssSource.match(/\.student-app-shell\.root-route\.root-home \.student-route-content\s*\{[^}]*\}/)?.[0] || "";

    expect(authenticatedAppLayoutSource).toContain('window.addEventListener("scroll", handleScroll, { passive: true });');
    expect(authenticatedAppLayoutSource).toContain('navCompressed && isRootRoute ? "nav-compressed" : ""');
    expect(authenticatedAppLayoutSource).not.toMatch(/addEventListener\("touchmove"|addEventListener\("wheel"/);
    expect(authenticatedAppLayoutSource).not.toContain("preventDefault");
    expect(authenticatedAppLayoutSource).not.toContain("window.scrollBy");
    expect(authenticatedAppLayoutSource).not.toContain("home-title");
    expect(authenticatedAppLayoutSource).not.toContain("setProperty(\"--home-title-height\"");
    expect(appShellCssSource).not.toContain("animation-timeline");
    expect(appShellCssSource).not.toContain("animation-range");
    expect(appShellCssSource).not.toContain("@keyframes home-title-scroll-away");
    expect(appShellCssSource).not.toContain("--home-title-height");
    expect(appShellCssSource).toContain("--home-app-header-height: 88px;");
    expect(homeHeaderBlock).toContain("position: fixed;");
    expect(homeHeaderBlock).toContain("top: 0;");
    expect(homeHeaderBlock).toContain("width: min(100%, var(--mobile-content-max));");
    expect(homeHeaderBlock).toContain("margin: 0 auto;");
    expect(homeHeaderBlock).toContain("transition: transform 150ms ease;");
    expect(homeCompressedBlock).toContain("transform: translate3d(0, -100%, 0);");
    expect(homeRouteContentBlock).toContain("padding: var(--home-app-header-height) 0 0;");
  });

  it("keeps the root Atom composer keyboard layout scoped to the visible viewport", async () => {
    // @ts-expect-error The frontend tsconfig intentionally omits Node types, but Vitest runs this contract in Node.
    const { readFileSync } = await import("node:fs");
    const cwd = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
    const appShellCssSource = readFileSync(`${cwd}/src/styles/app-shell.css`, "utf8");
    const assistantCssSource = readFileSync(`${cwd}/src/styles/assistant.css`, "utf8");
    const keyboardShellBlock = appShellCssSource.match(/\.student-app-shell\.root-route\.root-ai\.keyboard-active\s*\{[^}]*\}/)?.[0] || "";
    const keyboardRouteContentBlock =
      appShellCssSource.match(/\.student-app-shell\.root-route\.root-ai\.keyboard-active \.student-route-content\s*\{[^}]*\}/)?.[0] || "";
    const keyboardPanelBlocks: string[] = [];
    for (const match of assistantCssSource.matchAll(/\.student-app-shell\.root-route\.root-ai\.keyboard-active \.ai-chat-panel\.root\s*\{[^}]*\}/g)) {
      keyboardPanelBlocks.push(match[0]);
    }
    const chatMessageBodyBlock = assistantCssSource.match(/\.ai-empty-bubble,\s*\.ai-message\s*\{[^}]*\}/)?.[0] || "";
    const rootTextareaBlock = assistantCssSource.match(/\.ai-chat-panel\.root \.ai-chat-compose\.root textarea\s*\{[^}]*\}/)?.[0] || "";
    const markdownBodyBlock = assistantCssSource.match(/\.ai-markdown\s*\{[^}]*\}/)?.[0] || "";
    const markdownLineBlock = assistantCssSource.match(/\.ai-markdown \.ai-md-paragraph,\s*\.ai-markdown \.ai-md-list-item\s*\{[^}]*\}/)?.[0] || "";

    expect(authenticatedAppLayoutSource).toContain("ROOT_AI_COMPOSER_SELECTOR");
    expect(authenticatedAppLayoutSource).toContain("window.visualViewport?.height");
    expect(authenticatedAppLayoutSource).toContain("\"keyboard-active\"");
    expect(authenticatedAppLayoutSource).toContain("--student-visual-viewport-height");
    expect(authenticatedAppLayoutSource).toContain("--student-keyboard-bottom-inset");
    expect(appShellCssSource).toContain(".student-app-shell.keyboard-active .student-bottom-nav");
    expect(appShellCssSource).toContain(".student-app-shell.context-picker-active .student-bottom-nav");
    expect(appShellCssSource).toContain(".student-app-shell.root-route.root-ai.keyboard-active");
    expect(assistantPanelSource).toContain("context-picker-active");
    expect(appShellCssSource).toContain(".learning-shell:has(.student-app-shell.root-route.root-ai)");
    expect(appShellCssSource).toContain(".learning-shell:has(.student-app-shell.root-route.root-ai)::before");
    expect(appShellCssSource).toContain("overscroll-behavior: none;");
    expect(keyboardShellBlock).toContain("position: fixed;");
    expect(keyboardShellBlock).toContain("bottom: var(--student-keyboard-bottom-inset, 0px);");
    expect(keyboardRouteContentBlock).toContain("height: 100%;");
    expect(keyboardRouteContentBlock).not.toContain("--mobile-bottom-nav-height");
    expect(keyboardPanelBlocks.some((block) => block.includes("padding-bottom: calc(var(--ai-root-breathing-gap) + env(safe-area-inset-bottom, 0px));"))).toBe(
      true,
    );
    expect(assistantCssSource).toContain("--ai-root-breathing-gap: 12px;");
    expect(assistantCssSource).toContain(
      ".student-app-shell.root-route.root-ai.keyboard-active .ai-chat-panel.root .ai-chat-stream.root-empty",
    );
    expect(assistantCssSource).toContain("padding-top: clamp(44px, var(--student-keyboard-welcome-offset, 64px), 96px);");
    expect(assistantCssSource).toContain("grid-template-rows: 74px;");
    expect(assistantCssSource).toContain("--ai-chat-body-font-size: var(--mobile-text-lg);");
    expect(assistantCssSource).toContain("--ai-chat-body-line-height: 1.52;");
    for (const block of [chatMessageBodyBlock, rootTextareaBlock, markdownBodyBlock]) {
      expect(block).toContain("font-family: var(--mobile-font-family);");
      expect(block).toContain("font-size: var(--ai-chat-body-font-size);");
      expect(block).toContain("line-height: var(--ai-chat-body-line-height);");
      expect(block).toContain("font-weight: 400;");
      expect(block).toContain("letter-spacing: 0;");
    }
    expect(markdownLineBlock).toContain("line-height: var(--ai-chat-body-line-height);");
    expect(assistantCssSource).not.toContain("font-size: 22px;");
    expect(assistantCssSource).not.toContain("line-height: 1.65;");
    expect(assistantPanelSource).toContain("measureRootCompactScrollHeight");
    expect(assistantPanelSource).toContain("compactMeasureTextareaRef");
    expect(assistantPanelSource).toContain("measureTextarea.rows = 1;");
    expect(assistantPanelSource).toMatch(/className="ai-chat-compact-measure"[\s\S]*rows=\{1\}/);
    expect(assistantCssSource).toContain(".ai-chat-compact-measure");
  });

  it("keeps the root Atom header veil layered without duplicating the root canvas background", async () => {
    // @ts-expect-error The frontend tsconfig intentionally omits Node types, but Vitest runs this contract in Node.
    const { readFileSync } = await import("node:fs");
    const cwd = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
    const assistantCssSource = readFileSync(`${cwd}/src/styles/assistant.css`, "utf8");
    const rootPanelBlock = assistantCssSource.match(/\.ai-chat-panel\.root\s*\{[^}]*\}/)?.[0] || "";
    const emptyDraftPanelBlock =
      assistantCssSource.match(/\.ai-chat-panel\.root\.root-state-empty,\s*\.ai-chat-panel\.root\.root-state-draft\s*\{[^}]*\}/)?.[0] || "";
    const conversationPanelBlock = assistantCssSource.match(/\.ai-chat-panel\.root\.root-state-conversation\s*\{[^}]*\}/)?.[0] || "";
    const rootLayerBlock =
      assistantCssSource.match(
        /\.ai-chat-panel\.root \.ai-chat-stream,\s*\.ai-chat-panel\.root \.ai-quick-prompts,[\s\S]*?\.ai-chat-panel\.root \.ai-chat-compose\s*\{[^}]*\}/,
      )
        ?.[0] || "";
    const rootHeaderBlock = assistantCssSource.match(/\.ai-chat-panel\.root \.ai-chat-head\.root\s*\{[^}]*\}/)?.[0] || "";
    const rootTitleBlock = assistantCssSource.match(/\.ai-chat-panel\.root \.ai-chat-head\.root h2\s*\{[^}]*\}/)?.[0] || "";
    const rootVeilBlock = assistantCssSource.match(/\.ai-chat-panel\.root \.ai-chat-head\.root::before\s*\{[^}]*\}/)?.[0] || "";
    const rootForegroundLayerBlock =
      assistantCssSource.match(/\.ai-chat-panel\.root \.ai-chat-head\.root > div,\s*\.ai-chat-panel\.root \.ai-chat-head\.root \.ai-root-actions\s*\{[^}]*\}/)?.[0] ||
      "";
    const rootActionsBlocks: string[] = [];
    for (const match of assistantCssSource.matchAll(/\.ai-chat-panel\.root \.ai-chat-head\.root \.ai-root-actions\s*\{[^}]*\}/g)) {
      rootActionsBlocks.push(match[0]);
    }
    const rootActionsBlock = rootActionsBlocks.find((block) => block.includes("width: var(--ai-root-action-capsule-width);")) || "";
    const rootActionButtonBlock = assistantCssSource.match(/\.ai-chat-panel\.root \.ai-chat-head\.root \.ai-root-icon-action\s*\{[^}]*\}/)?.[0] || "";
    const rootStreamBlock = assistantCssSource.match(/\.ai-chat-panel\.root \.ai-chat-stream\s*\{[^}]*\}/)?.[0] || "";
    const rootStreamScrollbarBlock = assistantCssSource.match(/\.ai-chat-panel\.root \.ai-chat-stream::\-webkit\-scrollbar\s*\{[^}]*\}/)?.[0] || "";
    const emptyDraftStreamBlock =
      assistantCssSource.match(/\.ai-chat-panel\.root\.root-state-empty \.ai-chat-stream,\s*\.ai-chat-panel\.root\.root-state-draft \.ai-chat-stream\s*\{[^}]*\}/)?.[0] || "";
    const conversationStreamBlock = assistantCssSource.match(/\.ai-chat-panel\.root\.root-state-conversation \.ai-chat-stream\s*\{[^}]*\}/)?.[0] || "";

    expect(assistantPanelSource).toContain("rootLayoutState");
    expect(assistantPanelSource).toContain('"empty"');
    expect(assistantPanelSource).toContain('"draft"');
    expect(assistantPanelSource).toContain('"conversation"');
    expect(assistantPanelSource).toContain('"is-empty"');
    expect(assistantPanelSource).toContain('"has-draft"');
    expect(assistantPanelSource).toContain('"has-messages"');
    expect(assistantPanelSource).toContain("root-state-${rootLayoutState}");
    expect(assistantPanelSource).toContain("data-root-layout");
    expect(assistantPanelSource).toContain("data-root-state");
    expect(rootPanelBlock).toContain("radial-gradient(circle at 16% 20%");
    expect(rootPanelBlock).toContain("radial-gradient(circle at 78% 72%");
    expect(rootPanelBlock).not.toContain("grid-template-rows");
    expect(emptyDraftPanelBlock).toContain("grid-template-rows: var(--ai-root-header-overlay-height) minmax(0, 1fr) auto;");
    expect(conversationPanelBlock).toContain("grid-template-rows: minmax(0, 1fr) auto auto;");
    expect(rootLayerBlock).toContain(".ai-chat-panel.root .ai-chat-stream");
    expect(rootLayerBlock).not.toContain(".ai-chat-head");
    expect(assistantCssSource).not.toMatch(/\.ai-chat-panel\.root \.ai-chat-head,\s*\.ai-chat-panel\.root \.ai-chat-stream/);
    expect(rootHeaderBlock).toContain("position: absolute;");
    expect(rootHeaderBlock).toContain("top: 0;");
    expect(rootHeaderBlock).toContain("right: var(--ai-root-inline);");
    expect(rootHeaderBlock).toContain("left: var(--ai-root-inline);");
    expect(rootHeaderBlock).toContain("z-index: var(--ai-root-header-z);");
    expect(rootHeaderBlock).toContain("pointer-events: none;");
    expect(rootHeaderBlock).not.toContain("radial-gradient");
    expect(rootHeaderBlock).not.toMatch(/\bopacity\s*:/);
    expect(rootTitleBlock).toContain("text-shadow: none;");
    expect(rootTitleBlock).not.toMatch(/\bfilter\s*:/);
    expect(rootVeilBlock).toContain("background: linear-gradient(");
    expect(rootVeilBlock).toContain("var(--ai-root-header-veil-low) 82%");
    expect(rootVeilBlock).toContain("var(--ai-root-header-veil-end) 100%");
    expect(rootVeilBlock).not.toContain("radial-gradient");
    expect(rootVeilBlock).not.toMatch(/\bopacity\s*:/);
    expect(assistantCssSource).not.toMatch(/\.ai-chat-panel\.root \.ai-chat-head\.root::before\s*\{[^}]*backdrop-filter/s);
    expect(rootForegroundLayerBlock).toContain("z-index: 1;");
    expect(rootActionsBlock).toContain("width: var(--ai-root-action-capsule-width);");
    expect(rootActionsBlock).toContain("height: var(--ai-root-action-capsule-height);");
    expect(rootActionsBlock).toContain("border-radius: 999px;");
    expect(rootActionsBlock).toContain("background: rgba(255, 255, 255, 0.78);");
    expect(rootActionButtonBlock).toContain("flex: 1 1 0;");
    expect(rootActionButtonBlock).toContain("min-width: var(--ai-root-action-cell-size);");
    expect(rootStreamBlock).toContain("align-content: end;");
    expect(rootStreamBlock).toContain("gap: var(--ai-root-flat-turn-gap);");
    expect(rootStreamBlock).toContain("padding: 0;");
    expect(rootStreamBlock).toContain("scrollbar-width: none;");
    expect(rootStreamBlock).toContain("-ms-overflow-style: none;");
    expect(rootStreamScrollbarBlock).toContain("width: 0;");
    expect(rootStreamScrollbarBlock).toContain("height: 0;");
    expect(rootStreamScrollbarBlock).toContain("display: none;");
    expect(rootStreamBlock).not.toContain("var(--ai-root-header-overlay-height) + 8px");
    expect(emptyDraftStreamBlock).toContain("grid-row: 2;");
    expect(emptyDraftStreamBlock).toContain("overflow: hidden;");
    expect(conversationStreamBlock).toContain("grid-row: 1;");
    expect(conversationStreamBlock).toContain("align-content: start;");
    expect(conversationStreamBlock).toContain("overflow: auto;");
    expect(conversationStreamBlock).toContain("padding: calc(var(--ai-root-header-overlay-height) + 8px) 0 0;");
    expect(conversationStreamBlock).toContain("scroll-padding-top: calc(var(--ai-root-header-overlay-height) + 8px);");
    expect(assistantCssSource).toContain(".ai-chat-panel.root.root-state-conversation .ai-quick-prompts");
    expect(assistantCssSource).toContain(".ai-chat-panel.root.root-state-conversation .ai-chat-compose");
    expect(assistantCssSource).not.toContain(".ai-chat-panel.root.has-messages .ai-quick-prompts");
    expect(assistantCssSource).not.toContain(".ai-chat-panel.root.has-messages .ai-chat-compose");
    expect(assistantCssSource).toMatch(/\.ai-chat-panel\.root \.ai-chat-stream\.root-empty\s*\{[^}]*align-content: center;/s);
    expect(assistantCssSource.match(/radial-gradient/g) ?? []).toHaveLength(2);
  });

  it("keeps root flat assistant replies scoped, action-delimited, and source-safe", async () => {
    // @ts-expect-error The frontend tsconfig intentionally omits Node types, but Vitest runs this contract in Node.
    const { readFileSync } = await import("node:fs");
    const cwd = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
    const assistantCssSource = readFileSync(`${cwd}/src/styles/assistant.css`, "utf8");
    const rootDoneBlock = assistantCssSource.match(/\.ai-chat-panel\.root \.ai-message\.assistant\.done\s*\{[^}]*\}/)?.[0] || "";
    const rootRunningBlock = assistantCssSource.match(/\.ai-chat-panel\.root \.ai-message\.assistant\.running\s*\{[^}]*\}/)?.[0] || "";
    const actionRowBlock = assistantCssSource.match(/\.ai-chat-panel\.root \.ai-message-actions\s*\{[^}]*\}/)?.[0] || "";
    const citationBlock = assistantCssSource.match(/\.ai-chat-panel\.root \.ai-message-citation\s*\{[^}]*\}/)?.[0] || "";
    const thinkingLineBlock = assistantCssSource.match(/\.ai-chat-panel\.root \.ai-thinking-line\s*\{[^}]*\}/)?.[0] || "";
    const thinkingAtomMarkBlock = assistantCssSource.match(/\.ai-chat-panel\.root \.ai-thinking-atom-mark\s*\{[^}]*\}/)?.[0] || "";
    const thinkingLottieBlock = assistantCssSource.match(/\.ai-chat-panel\.root \.ai-thinking-lottie,\s*\.ai-chat-panel\.root \.ai-thinking-atom-static\s*\{[^}]*\}/)?.[0] || "";
    const thinkingTextCurrentBlock = assistantCssSource.match(/\.ai-chat-panel\.root \.ai-thinking-text\.current\s*\{[^}]*\}/)?.[0] || "";
    const thinkingTextIncomingBlock = assistantCssSource.match(/\.ai-chat-panel\.root \.ai-thinking-text\.current\.incoming\s*\{[^}]*\}/)?.[0] || "";
    const thinkingTextOutgoingBlock = assistantCssSource.match(/\.ai-chat-panel\.root \.ai-thinking-text\.outgoing\s*\{[^}]*\}/)?.[0] || "";

    expect(assistantPanelSource).toContain("AssistantTurnActions");
    expect(assistantPanelSource).toContain("AssistantThinkingLine");
    expect(assistantPanelSource).toContain("AtomThinkingMark");
    expect(assistantPanelSource).toContain("usePrefersReducedMotion");
    expect(assistantPanelSource).toContain("lottie-react");
    expect(assistantPanelSource).toContain("atom-thinking.json");
    expect(assistantPanelSource).toContain("normalizeVisibleThinkingEvent");
    expect(assistantPanelSource).toContain("assistantVisibleThinkingPhase(activeThinking, status, Boolean(message.content.trim()))");
    expect(assistantPanelSource).toContain('event.event === "thinking"');
    expect(assistantPanelSource).toContain("messageLength");
    expect(assistantPanelSource).toContain("ASSISTANT_THINKING_PHASE_MIN_VISIBLE_MS = 1400");
    expect(assistantPanelSource).toContain("ASSISTANT_THINKING_TRANSITION_MS = 420");
    expect(assistantPanelSource).toContain("queuedPhaseRef");
    expect(assistantPanelSource).toContain('"正在判断问题范围"');
    expect(assistantPanelSource).toContain('"正在检索课程资料"');
    expect(assistantPanelSource).toContain('"正在返回学习建议"');
    expect(assistantPanelSource).toContain('"正在组织回答"');
    expect(assistantPanelSource).toContain('"正在输出回答"');
    expect(assistantPanelSource).toContain("safeAssistantSourceCount");
    expect(assistantPanelSource).toContain("Mark Atom answer helpful");
    expect(assistantPanelSource).toContain("Mark Atom answer unhelpful");
    expect(assistantPanelSource).toContain("Copy Atom answer");
    expect(assistantPanelSource).not.toMatch(/source\.(title|section|score|chunk_id)/);
    expect(assistantPanelSource).not.toContain("rag_trace");
    expect(assistantPanelSource).not.toContain("tool_calls");
    expect(assistantPanelSource).not.toContain("guardrail_decisions");
    expect(assistantPanelSource).not.toContain("reasoning_text");
    expect(assistantPanelSource).not.toContain("provider exploded");
    expect(rootDoneBlock).toContain("max-width: none;");
    expect(rootDoneBlock).toContain("border: 0;");
    expect(rootDoneBlock).toContain("border-radius: 0;");
    expect(rootDoneBlock).toContain("background: transparent;");
    expect(rootDoneBlock).toContain("box-shadow: none;");
    expect(rootDoneBlock).toContain("white-space: normal;");
    expect(rootRunningBlock).toContain("max-width: none;");
    expect(rootRunningBlock).toContain("border: 0;");
    expect(rootRunningBlock).toContain("border-radius: 0;");
    expect(rootRunningBlock).toContain("background: transparent;");
    expect(rootRunningBlock).toContain("box-shadow: none;");
    expect(rootRunningBlock).toContain("white-space: normal;");
    expect(thinkingLineBlock).toContain("display: inline-flex;");
    expect(thinkingLineBlock).toContain("min-height: calc(var(--ai-chat-body-font-size) * var(--ai-chat-body-line-height));");
    expect(thinkingAtomMarkBlock).toContain("display: inline-flex;");
    expect(thinkingAtomMarkBlock).toContain("flex: 0 0 32px;");
    expect(thinkingAtomMarkBlock).toContain("width: 32px;");
    expect(thinkingAtomMarkBlock).toContain("height: 32px;");
    expect(thinkingAtomMarkBlock).toContain("color: var(--green);");
    expect(thinkingLottieBlock).toContain("width: 32px;");
    expect(thinkingLottieBlock).toContain("height: 32px;");
    expect(thinkingTextCurrentBlock).toContain("animation: ai-thinking-text-in 260ms ease-out both;");
    expect(thinkingTextIncomingBlock).toContain("animation: ai-thinking-text-in 260ms cubic-bezier(0.18, 0.9, 0.28, 1) 90ms both;");
    expect(thinkingTextOutgoingBlock).toContain("animation: ai-thinking-text-out 140ms ease-in both;");
    expect(actionRowBlock).toContain("min-height: var(--ai-root-action-row-height);");
    expect(citationBlock).toContain("white-space: nowrap;");
    expect(assistantCssSource).not.toMatch(/(^|\n)\.ai-message\.assistant\.done\s*\{[^}]*background:\s*transparent;/s);
    expect(assistantCssSource).not.toMatch(/(^|\n)\.ai-message\.assistant\.running\s*\{[^}]*background:\s*transparent;/s);
    expect(assistantCssSource).not.toContain("ai-thinking-dots");
    expect(assistantCssSource).not.toContain("@keyframes ai-thinking-dot");
    expect(assistantCssSource).toContain("@keyframes ai-thinking-text-in");
    expect(assistantCssSource).toContain("@keyframes ai-thinking-text-out");
    expect(assistantCssSource).toContain("@media (prefers-reduced-motion: reduce)");
    expect(assistantCssSource).toContain(".ai-chat-panel.root .ai-thinking-atom-mark");
    expect(assistantCssSource).toContain(".ai-chat-panel.root .ai-thinking-text.outgoing");
  });

  it("keeps the compact Atom-centered bottom nav opaque and free of default focus boxes", async () => {
    // @ts-expect-error The frontend tsconfig intentionally omits Node types, but Vitest runs this contract in Node.
    const { readFileSync } = await import("node:fs");
    const cwd = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
    const appShellCssSource = readFileSync(`${cwd}/src/styles/app-shell.css`, "utf8");
    const mobileTokensSource = readFileSync(`${cwd}/src/mobile/tokens.css`, "utf8");
    const bottomNavBlock = appShellCssSource.match(/\.student-bottom-nav\s*\{[^}]*\}/)?.[0] || "";
    const bottomNavButtonBlock = appShellCssSource.match(/\.student-bottom-nav button\s*\{[^}]*\}/)?.[0] || "";
    const bottomNavLabelBlock = appShellCssSource.match(/\.student-bottom-nav-label\s*\{[^}]*\}/)?.[0] || "";
    const activeNavBlock = appShellCssSource.match(/\.student-bottom-nav button\.active\s*\{[^}]*\}/)?.[0] || "";
    const atomLabelBlock = appShellCssSource.match(/\.student-bottom-nav button\[data-root="ai"\] \.student-bottom-nav-label\s*\{[^}]*\}/)?.[0] || "";
    const atomIconBlock = appShellCssSource.match(/\.student-bottom-nav button\[data-root="ai"\] \.student-bottom-nav-icon\s*\{[^}]*\}/)?.[0] || "";
    const activeAtomIconBlock =
      appShellCssSource.match(/\.student-bottom-nav button\[data-root="ai"\]\.active \.student-bottom-nav-icon\s*\{[^}]*\}/)?.[0] || "";

    expect(mobileTokensSource).toContain("--mobile-bottom-nav-height: 56px;");
    expect(mobileTokensSource).toContain("--mobile-bottom-action-space: calc(var(--mobile-bottom-nav-height) + 18px + env(safe-area-inset-bottom));");
    expect(studentBottomNavSource).toContain("student-bottom-nav-primary");
    expect(studentBottomNavSource).toContain("student-bottom-nav-standard");
    expect(studentBottomNavSource).toContain("aria-label={item.label}");
    expect(studentBottomNavSource).toContain("data-root={item.id}");
    expect(studentBottomNavSource).toContain("rootPathById[item.id]");
    expect(bottomNavBlock).toContain("height: calc(var(--mobile-bottom-nav-height) + env(safe-area-inset-bottom, 0px));");
    expect(bottomNavBlock).toContain("overflow: hidden;");
    expect(bottomNavBlock).toContain("background: #fffdf6;");
    expect(bottomNavBlock).toContain("padding: 6px var(--mobile-chrome-inline) calc(6px + env(safe-area-inset-bottom, 0px)) var(--mobile-chrome-inline);");
    expect(bottomNavBlock).not.toContain("background: rgba(255, 253, 246");
    expect(bottomNavBlock).not.toContain("backdrop-filter: blur(18px)");
    expect(bottomNavButtonBlock).toContain("display: flex;");
    expect(bottomNavButtonBlock).toContain("min-height: var(--mobile-touch-md);");
    expect(bottomNavButtonBlock).not.toContain("grid-template-rows: 24px auto;");
    expect(bottomNavButtonBlock).not.toContain("min-height: 54px;");
    expect(bottomNavLabelBlock).toContain("font-size: 17px;");
    expect(bottomNavLabelBlock).toContain("white-space: nowrap;");
    expect(activeNavBlock).toContain("color: var(--green);");
    expect(activeNavBlock).toContain("background: transparent;");
    expect(activeNavBlock).not.toContain("rgba(0, 88, 38, 0.1)");
    expect(atomLabelBlock).toContain("clip: rect(0 0 0 0);");
    expect(atomIconBlock).toContain("width: 64px;");
    expect(atomIconBlock).toContain("height: 42px;");
    expect(atomIconBlock).not.toContain("border:");
    expect(atomIconBlock).toContain("border-radius: 16px;");
    expect(atomIconBlock).toContain("color: var(--green);");
    expect(atomIconBlock).toContain("background: rgba(0, 88, 38, 0.1);");
    expect(activeAtomIconBlock).not.toContain("border-color:");
    expect(activeAtomIconBlock).toContain("color: #ffffff;");
    expect(activeAtomIconBlock).toContain("background: var(--green);");
    expect(appShellCssSource).toContain(".student-bottom-nav button:focus");
    expect(appShellCssSource).toContain("outline-style: none;");
    expect(appShellCssSource).toContain("outline-width: 0;");
    expect(appShellCssSource).toContain(".student-bottom-nav button:focus-visible");
  });

  it("keeps the home video action row compact, icon-led, and search-free", async () => {
    // @ts-expect-error The frontend tsconfig intentionally omits Node types, but Vitest runs this contract in Node.
    const { readFileSync } = await import("node:fs");
    const cwd = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
    const appShellCssSource = readFileSync(`${cwd}/src/styles/app-shell.css`, "utf8");
    const actionRowBlock = appShellCssSource.match(/\.home-video-actions\s*\{[^}]*\}/)?.[0] || "";
    const iconGroupBlock = appShellCssSource.match(/\.home-video-icon-actions\s*\{[^}]*\}/)?.[0] || "";
    const atomActionBlock = appShellCssSource.match(/\.home-video-icon-action\.atom\s*\{[^}]*\}/)?.[0] || "";

    expect(homeRootPageSource).toContain("home-video-open-action");
    expect(homeRootPageSource).toContain("home-video-icon-actions");
    expect(homeRootPageSource).toContain("问问Atom：");
    expect(homeRootPageSource).toContain("<ThumbsUp");
    expect(homeRootPageSource).toContain("<Bookmark");
    expect(homeRootPageSource).toContain("<Share2");
    expect(homeRootPageSource).toContain("<MoreHorizontal");
    expect(homeRootPageSource).not.toContain("搜索相关");
    expect(homeRootPageSource).not.toContain("onSearch");
    expect(actionRowBlock).toContain("display: flex;");
    expect(actionRowBlock).toContain("justify-content: space-between;");
    expect(actionRowBlock).not.toContain("grid-template-columns");
    expect(iconGroupBlock).toContain("justify-content: flex-end;");
    expect(iconGroupBlock).toContain("min-width: 0;");
    expect(atomActionBlock).toContain("color: var(--green);");
    expect(atomActionBlock).toContain("background: rgba(0, 88, 38, 0.11);");
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

  it("keeps point video player chrome aligned with mobile detail page controls", async () => {
    // @ts-expect-error The frontend tsconfig intentionally omits Node types, but Vitest runs this contract in Node.
    const { readFileSync } = await import("node:fs");
    const cwd = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
    const experimentsCssSource = readFileSync(`${cwd}/src/styles/experiments.css`, "utf8");
    const pointDetailBlock = experimentsCssSource.match(/\.catalog-point-detail\s*\{[^}]*\}/)?.[0] || "";
    const playerBlock = experimentsCssSource.match(/\.point-art-player\s*\{[^}]*\}/)?.[0] || "";
    const defaultChromeHideBlock =
      experimentsCssSource.match(
        /\.point-art-player \.art-bottom,[\s\S]*?\.point-art-player \.art-layer-auto-playback\s*\{[^}]*\}/,
      )?.[0] || "";
    const shellBlock = experimentsCssSource.match(/\.point-youtube-shell\s*\{[^}]*\}/)?.[0] || "";
    const controlsBlock = experimentsCssSource.match(/\.point-youtube-controls\s*\{[^}]*\}/)?.[0] || "";
    const activeControlsBlock =
      experimentsCssSource.match(/\.point-youtube-shell-active \.point-youtube-controls\s*\{[^}]*\}/)?.[0] || "";
    const backButtonBlock = experimentsCssSource.match(/\.point-youtube-back,\s*\.point-player-empty-back\s*\{[^}]*\}/)?.[0] || "";
    const playableBackBlock = experimentsCssSource.match(/\.point-youtube-back\s*\{[^}]*\}/)?.[0] || "";
    const emptyBackBlock = experimentsCssSource.match(/\.point-player-empty-back\s*\{[^}]*position: absolute;[^}]*\}/)?.[0] || "";
    const backIconBlock = experimentsCssSource.match(/\.point-player-back-icon\s*\{[^}]*\}/)?.[0] || "";
    const playerVarsBlock =
      experimentsCssSource.match(/\.point-art-player \.art-video-player\s*\{[^}]*--art-theme[^}]*\}/)?.[0] || "";
    const inactiveProgressBlock = experimentsCssSource.match(/\.point-youtube-inactive-progress\s*\{[^}]*\}/)?.[0] || "";
    const activeProgressBlock =
      experimentsCssSource.match(/\.point-youtube-active-progress\s*\{[^}]*height: 30px;[^}]*\}/)?.[0] || "";
    const progressHitBlock = experimentsCssSource.match(/\.point-youtube-progress-hit\s*\{[^}]*\}/)?.[0] || "";
    const progressThumbBlock = experimentsCssSource.match(/\.point-youtube-progress-thumb\s*\{[^}]*\}/)?.[0] || "";
    const timeCapsuleBlock = experimentsCssSource.match(/\.point-youtube-time-capsule\s*\{[^}]*\}/)?.[0] || "";
    const learningCopyBlock = experimentsCssSource.match(/\.point-learning-section > p\s*\{[^}]*\}/)?.[0] || "";
    const equationListBlock = experimentsCssSource.match(/\.point-equation-list\s*\{[^}]*\}/)?.[0] || "";
    const equationRowBlock = experimentsCssSource.match(/\.point-equation-row\s*\{[^}]*\}/)?.[0] || "";
    const equationNoteBlock = experimentsCssSource.match(/\.point-equation-note\s*\{[^}]*\}/)?.[0] || "";
    const safetyCopyBlock = experimentsCssSource.match(/\.safety-section > p\s*\{[^}]*\}/)?.[0] || "";
    const actionAreaBlock = experimentsCssSource.match(/\.point-detail-actions\s*\{[^}]*\}/)?.[0] || "";

    expect(pointVideoPlayerSource).toContain("point-player-back-icon");
    expect(pointVideoPlayerSource).toContain("BackArrowIcon");
    expect(pointVideoPlayerSource).toContain('<BackArrowIcon className="point-player-back-icon" />');
    expect(pointVideoPlayerSource).toContain("autoplay: true");
    expect(pointVideoPlayerSource).toContain("muted: true");
    expect(pointVideoPlayerSource).toContain("miniProgressBar: false");
    expect(pointVideoPlayerSource).toContain("setting: false");
    expect(pointVideoPlayerSource).toContain("lock: false");
    expect(pointVideoPlayerSource).toContain("playbackRate: false");
    expect(pointVideoPlayerSource).toContain("controls: false");
    expect(pointVideoPlayerSource).toContain("point-youtube-shell");
    expect(pointVideoPlayerSource).toContain("point-youtube-inactive-progress");
    expect(pointVideoPlayerSource).toContain("point-youtube-progress-thumb");
    expect(pointVideoPlayerSource).not.toContain('name: "point-time"');
    expect(pointVideoPlayerSource).not.toContain("point-player-back-layer");
    expect(pointVideoPlayerSource).not.toContain("xgplayer");
    expect(pointVideoPlayerSource).not.toContain("import { ArrowLeft");
    expect(pointVideoPlayerSource).not.toContain('const backIconSvg =\\n  \'<svg');
    expect(pointVideoPlayerSource).not.toContain("point-player-back-glyph");
    expect(pointDetailBlock).toContain("padding-top: min(62.5vw, 280px);");
    expect(playerBlock).toContain("position: fixed;");
    expect(playerBlock).toContain("top: 0;");
    expect(playerBlock).toContain("left: 50%;");
    expect(playerBlock).toContain("width: min(100vw, var(--mobile-content-max));");
    expect(playerBlock).toContain("aspect-ratio: 16 / 10;");
    expect(playerBlock).toContain("transform: translateX(-50%);");
    expect(playerBlock).toContain("--point-player-active-progress: linear-gradient");
    expect(defaultChromeHideBlock).toContain("display: none !important;");
    expect(defaultChromeHideBlock).toContain("pointer-events: none !important;");
    expect(defaultChromeHideBlock).toContain(".point-art-player .art-lock");
    expect(defaultChromeHideBlock).toContain(".point-art-player .art-layers");
    expect(shellBlock).toContain("position: absolute;");
    expect(shellBlock).toContain("inset: 0;");
    expect(controlsBlock).toContain("opacity: 0;");
    expect(controlsBlock).toContain("pointer-events: none;");
    expect(activeControlsBlock).toContain("opacity: 1;");
    expect(activeControlsBlock).toContain("pointer-events: auto;");
    expect(backButtonBlock).toContain("width: 44px;");
    expect(backButtonBlock).toContain("height: 44px;");
    expect(backButtonBlock).toContain("background: transparent;");
    expect(backButtonBlock).not.toContain("border-radius: 999px");
    expect(playableBackBlock).toContain("position: absolute;");
    expect(playableBackBlock).toContain("top: 6px;");
    expect(playableBackBlock).toContain("left: 4px;");
    expect(emptyBackBlock).toContain("top: 6px;");
    expect(emptyBackBlock).toContain("left: 4px;");
    expect(backIconBlock).not.toContain("translateX(");
    expect(playerVarsBlock).toContain("--art-theme: #006934;");
    expect(experimentsCssSource).not.toContain("margin: 8px 0 0 18px;");
    expect(experimentsCssSource).not.toContain("left: 18px;");
    expect(experimentsCssSource).not.toContain("transform: translateY(-4px);");
    expect(experimentsCssSource).not.toContain("art-mini-progress-bar");
    expect(experimentsCssSource).not.toContain("art-control-point-time");
    expect(inactiveProgressBlock).toContain("height: 2px;");
    expect(inactiveProgressBlock).toContain("background: var(--point-player-inactive-track);");
    expect(activeProgressBlock).toContain("height: 30px;");
    expect(progressHitBlock).toContain("height: 30px;");
    expect(progressHitBlock).toContain("touch-action: none;");
    expect(progressThumbBlock).toContain("width: 24px;");
    expect(progressThumbBlock).toContain("height: 24px;");
    expect(progressThumbBlock).toContain("background: #ffffff var(--point-player-logo)");
    expect(timeCapsuleBlock).toContain("border-radius: 999px;");
    expect(timeCapsuleBlock).toContain("white-space: nowrap;");
    expect(learningCopyBlock).toContain("font-weight: 640;");
    expect(equationListBlock).toContain("background: transparent;");
    expect(equationRowBlock).toContain("grid-template-columns: 22px minmax(0, 1fr);");
    expect(equationNoteBlock).toContain("font-weight: 650;");
    expect(equationNoteBlock).not.toContain("font-family: ui-monospace");
    expect(safetyCopyBlock).toContain("border-left: 3px solid");
    expect(actionAreaBlock).toContain("padding-bottom: calc(22px + env(safe-area-inset-bottom, 0px));");
  });

  it("keeps secondary-page back arrows shared, flatter, and left-aligned", async () => {
    // @ts-expect-error The frontend tsconfig intentionally omits Node types, but Vitest runs this contract in Node.
    const { readFileSync } = await import("node:fs");
    const cwd = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
    const appShellCssSource = readFileSync(`${cwd}/src/styles/app-shell.css`, "utf8");
    const learningCssSource = readFileSync(`${cwd}/src/styles/learning.css`, "utf8");
    const pagebarButtonBlock = appShellCssSource.match(/\.pagebar \.icon-action\s*\{[^}]*\}/)?.[0] || "";
    const pagebarBlock = appShellCssSource.match(/\.pagebar\s*\{[^}]*minmax\(0, 1fr\)[^}]*\}/)?.[0] || "";
    const searchBackBlock = learningCssSource.match(/\.unified-search-back\s*\{[^}]*\}/)?.[0] || "";

    expect(backArrowIconSource).toContain('studentBackArrowViewBox = "0 0 24 24"');
    expect(backArrowIconSource).toContain(
      'studentBackArrowPath =\n  "M7.414 13l5.043 5.04-1.414 1.42L3.586 12l7.457-7.46 1.414 1.42L7.414 11H21v2H7.414z"',
    );
    expect(backArrowIconSource).toContain('fill="currentColor"');
    expect(backArrowIconSource).toContain("<path d={studentBackArrowPath} />");
    expect(backArrowIconSource).toContain("createBackArrowSvg");
    expect(backArrowIconSource).not.toContain("studentBackArrowStrokeWidth");
    expect(backArrowIconSource).not.toContain("studentBackArrowTipPatchPoints");
    expect(backArrowIconSource).not.toContain("<line");
    expect(backArrowIconSource).not.toContain("<polygon");
    expect(backArrowIconSource).not.toMatch(/base64|\\.png|\\.jpg|\\.jpeg|\\.webp/i);
    expect(pagebarSource).toContain("BackArrowIcon");
    expect(pagebarSource).not.toContain("ArrowLeft");
    expect(unifiedSearchSource).toContain("VideoLibraryPage");
    expect(unifiedSearchSource).not.toContain("ArrowLeft");
    expect(pagebarBlock).toContain("grid-template-columns: 38px minmax(0, 1fr);");
    expect(pagebarBlock).toContain("gap: 4px;");
    expect(pagebarButtonBlock).toContain("width: 44px;");
    expect(pagebarButtonBlock).toContain("height: 44px;");
    expect(appShellCssSource).toContain("margin-left: 12px;");
    expect(pagebarButtonBlock).toContain("transform: translateX(-8px);");
    expect(searchBackBlock).toContain("width: 44px;");
    expect(searchBackBlock).toContain("height: 44px;");
    expect(searchBackBlock).toContain("transform: translateX(-8px);");

    [
      "routes/learn/LearningAreaPage.tsx",
      "routes/learn/ChapterStudyPage.tsx",
      "routes/learn/CatalogDirectoryPage.tsx",
      "routes/learn/ElementDetailPage.tsx",
      "routes/ai/AiChatPage.tsx",
      "routes/assessment/AssessmentSessionPage.tsx",
      "routes/assessment/AssessmentReportPage.tsx",
      "routes/profile/FeedbackPage.tsx",
    ].forEach((file) => {
      const source = routeAndFeatureSources[`./${file}`] || "";
      expect(source).toContain("DetailPageFrame");
      expect(source).not.toContain("ArrowLeft");
      expect(source).not.toContain("ChevronLeft");
    });

    expect(routeAndFeatureSources["./routes/search/UnifiedSearchPage.tsx"]).toContain("VideoLibraryPage");
    expect(routeAndFeatureSources["./routes/search/UnifiedSearchPage.tsx"]).not.toContain("DetailPageFrame");
    expect(routeAndFeatureSources["./routes/video-library/VideoLibraryPage.tsx"]).toContain("BackArrowIcon");
    expect(routeAndFeatureSources["./routes/video-library/VideoLibraryPage.tsx"]).not.toContain("DetailPageFrame");
    expect(routeAndFeatureSources["./routes/video-library/VideoLibraryPage.tsx"]).not.toContain("ArrowLeft");
    expect(routeAndFeatureSources["./routes/video-library/VideoLibraryPage.tsx"]).not.toContain("ChevronLeft");
    expect(routeAndFeatureSources["./routes/learn/ExperimentPointPage.tsx"]).toContain("CatalogPointDetailPanel");
    expect(routeAndFeatureSources["./routes/learn/ExperimentPointPage.tsx"]).not.toContain("DetailPageFrame");
  });
});
