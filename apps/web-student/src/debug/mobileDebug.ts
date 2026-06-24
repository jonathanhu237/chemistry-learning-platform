const VCONSOLE_STORAGE_KEY = "student.mobileDebug.vconsole";

type DebugWindow = Window & {
  __studentVConsole?: unknown;
  __atomKeyboardDebugLogs?: unknown[];
  __atomKeyboardDebugText?: string;
  atomKeyboardCopy?: () => Promise<string>;
  atomKeyboardDump?: () => string;
};

function normalizeDebugFlag(value: string | null) {
  if (!value) return null;
  const normalized = value.toLowerCase();
  if (["1", "true", "yes", "on"].includes(normalized)) return true;
  if (["0", "false", "no", "off"].includes(normalized)) return false;
  return null;
}

export function isStudentMobileDebugEnabled() {
  if (typeof window === "undefined") return false;
  const params = new URLSearchParams(window.location.search);
  const requestedFlag =
    normalizeDebugFlag(params.get("vconsole")) ??
    normalizeDebugFlag(params.get("debug_vconsole")) ??
    normalizeDebugFlag(params.get("student_debug"));
  if (requestedFlag === true) {
    window.localStorage.setItem(VCONSOLE_STORAGE_KEY, "1");
    return true;
  }
  if (requestedFlag === false) {
    window.localStorage.removeItem(VCONSOLE_STORAGE_KEY);
    return false;
  }
  return window.localStorage.getItem(VCONSOLE_STORAGE_KEY) === "1";
}

export async function installStudentMobileDebugConsole() {
  if (!isStudentMobileDebugEnabled()) return;
  const debugWindow = window as DebugWindow;
  installAtomKeyboardDebugShortcuts();
  installAtomKeyboardDebugExportButton();
  if (!debugWindow.__studentVConsole) {
    const { default: VConsole } = await import("vconsole");
    debugWindow.__studentVConsole = new VConsole();
    console.info("[student-mobile-debug] vConsole enabled. Use ?vconsole=0 to disable.");
  }
}

function roundMetric(value: number | undefined) {
  return typeof value === "number" && Number.isFinite(value) ? Math.round(value * 100) / 100 : null;
}

function readRect(selector: string) {
  const node = document.querySelector<HTMLElement>(selector);
  if (!node) return null;
  const rect = node.getBoundingClientRect();
  return {
    top: roundMetric(rect.top),
    right: roundMetric(rect.right),
    bottom: roundMetric(rect.bottom),
    left: roundMetric(rect.left),
    width: roundMetric(rect.width),
    height: roundMetric(rect.height),
  };
}

function summarizeActiveElement() {
  const active = document.activeElement;
  if (!(active instanceof HTMLElement)) return null;
  return {
    tag: active.tagName,
    id: active.id || "",
    className: active.className || "",
    ariaLabel: active.getAttribute("aria-label") || "",
    placeholder: active.getAttribute("placeholder") || "",
  };
}

function atomKeyboardDebugLogs() {
  const debugWindow = window as DebugWindow;
  debugWindow.__atomKeyboardDebugLogs ||= [];
  return debugWindow.__atomKeyboardDebugLogs;
}

function atomKeyboardDebugText() {
  const debugWindow = window as DebugWindow;
  const logs = atomKeyboardDebugLogs();
  const text = JSON.stringify(
    {
      exportedAt: new Date().toISOString(),
      userAgent: window.navigator.userAgent,
      url: window.location.href,
      count: logs.length,
      logs,
    },
    null,
    2,
  );
  debugWindow.__atomKeyboardDebugText = text;
  return text;
}

async function copyTextToClipboard(text: string) {
  if (window.navigator.clipboard?.writeText) {
    await window.navigator.clipboard.writeText(text);
    return;
  }
  const textarea = document.createElement("textarea");
  textarea.value = text;
  textarea.setAttribute("readonly", "true");
  textarea.style.position = "fixed";
  textarea.style.top = "0";
  textarea.style.left = "0";
  textarea.style.width = "1px";
  textarea.style.height = "1px";
  textarea.style.opacity = "0";
  document.body.appendChild(textarea);
  textarea.focus();
  textarea.select();
  document.execCommand("copy");
  textarea.remove();
}

async function copyAtomKeyboardDebugLogs() {
  debugAtomKeyboardSnapshot("manual-export-before-copy");
  const text = atomKeyboardDebugText();
  await copyTextToClipboard(text);
  console.info("[atom-keyboard-export]", {
    copied: true,
    count: atomKeyboardDebugLogs().length,
    bytes: text.length,
  });
  return text;
}

function installAtomKeyboardDebugShortcuts() {
  const debugWindow = window as DebugWindow;
  debugWindow.atomKeyboardDump = atomKeyboardDebugText;
  debugWindow.atomKeyboardCopy = copyAtomKeyboardDebugLogs;
}

function installAtomKeyboardDebugExportButton() {
  if (document.getElementById("atom-keyboard-debug-copy")) return;
  const button = document.createElement("button");
  button.id = "atom-keyboard-debug-copy";
  button.type = "button";
  button.textContent = "复制调试";
  button.setAttribute("aria-label", "复制 Atom 键盘调试数据");
  button.style.position = "fixed";
  button.style.top = "calc(env(safe-area-inset-top, 0px) + 8px)";
  button.style.left = "8px";
  button.style.zIndex = "2147483647";
  button.style.border = "0";
  button.style.borderRadius = "999px";
  button.style.padding = "8px 10px";
  button.style.color = "#ffffff";
  button.style.background = "rgba(0, 88, 38, 0.9)";
  button.style.boxShadow = "0 8px 20px rgba(0, 0, 0, 0.18)";
  button.style.fontSize = "12px";
  button.style.fontWeight = "900";
  button.style.lineHeight = "1";
  button.addEventListener("click", async () => {
    try {
      await copyAtomKeyboardDebugLogs();
      button.textContent = "已复制";
      window.setTimeout(() => {
        button.textContent = "复制调试";
      }, 1200);
    } catch (error) {
      console.error("[atom-keyboard-export]", error);
      button.textContent = "复制失败";
      window.setTimeout(() => {
        button.textContent = "复制调试";
      }, 1600);
    }
  });
  document.body.appendChild(button);
}

export function debugAtomKeyboardSnapshot(reason: string, extra: Record<string, unknown> = {}) {
  if (!isStudentMobileDebugEnabled()) return;
  const shell = document.querySelector<HTMLElement>(".student-app-shell");
  const shellStyle = shell ? window.getComputedStyle(shell) : null;
  const visualViewport = window.visualViewport;
  const snapshot = {
    reason,
    time: new Date().toISOString(),
    path: window.location.pathname + window.location.search,
    extra,
    focus: summarizeActiveElement(),
    viewport: {
      innerHeight: roundMetric(window.innerHeight),
      innerWidth: roundMetric(window.innerWidth),
      outerHeight: roundMetric(window.outerHeight),
      scrollY: roundMetric(window.scrollY),
      docClientHeight: roundMetric(document.documentElement.clientHeight),
      bodyClientHeight: roundMetric(document.body?.clientHeight),
      screenHeight: roundMetric(window.screen?.height),
      screenAvailHeight: roundMetric(window.screen?.availHeight),
      devicePixelRatio: roundMetric(window.devicePixelRatio),
      visualHeight: roundMetric(visualViewport?.height),
      visualWidth: roundMetric(visualViewport?.width),
      visualOffsetTop: roundMetric(visualViewport?.offsetTop),
      visualPageTop: roundMetric(visualViewport?.pageTop),
      visualScale: roundMetric(visualViewport?.scale),
    },
    shell: {
      className: shell?.className || "",
      cssVisualHeight: shell?.style.getPropertyValue("--student-visual-viewport-height") || "",
      cssVisualTop: shell?.style.getPropertyValue("--student-visual-viewport-top") || "",
      cssKeyboardInset: shell?.style.getPropertyValue("--student-keyboard-bottom-inset") || "",
      position: shellStyle?.position || "",
      top: shellStyle?.top || "",
      bottom: shellStyle?.bottom || "",
      height: shellStyle?.height || "",
      minHeight: shellStyle?.minHeight || "",
    },
    rects: {
      shell: readRect(".student-app-shell"),
      route: readRect(".student-route-content"),
      page: readRect(".ai-root-page"),
      panel: readRect(".ai-chat-panel.root"),
      head: readRect(".ai-chat-head.root"),
      stream: readRect(".ai-chat-stream"),
      welcome: readRect(".ai-root-welcome"),
      compose: readRect(".ai-chat-compose"),
      textarea: readRect(".ai-chat-compose textarea"),
      bottomNav: readRect(".student-bottom-nav"),
    },
  };

  const logs = atomKeyboardDebugLogs();
  logs.push(snapshot);
  if (logs.length > 80) logs.splice(0, logs.length - 80);
  atomKeyboardDebugText();

  console.log("[atom-keyboard]", snapshot);
  console.table({
    reason,
    visualHeight: snapshot.viewport.visualHeight,
    innerHeight: snapshot.viewport.innerHeight,
    cssInset: snapshot.shell.cssKeyboardInset,
    shellBottom: snapshot.rects.shell?.bottom,
    routeBottom: snapshot.rects.route?.bottom,
    panelBottom: snapshot.rects.panel?.bottom,
    composeBottom: snapshot.rects.compose?.bottom,
    textareaBottom: snapshot.rects.textarea?.bottom,
  });
}
