import { cleanup, render } from "@testing-library/react";
import { createElement } from "react";
import { beforeEach, afterEach, describe, expect, it, vi } from "vitest";

import {
  activatePreviewTarget,
  applyPreviewDragScroll,
  applyPreviewDragScrollWithLock,
  applyPreviewScroll,
  applyPreviewWheelScroll,
  dispatchPreviewPointerEvent,
  findScrollablePreviewTarget,
  PreviewInputRuntime,
  previewLongPressDelayMs,
  resolvePreviewActionTarget,
} from "./PreviewInputRuntime";
import {
  parsePreviewInputMessage,
  storePreviewInputHandshake,
  studentPreviewInputNamespace,
  studentPreviewInputVersion,
  type PreviewInputMessage,
} from "./previewInputProtocol";
import { StudentRuntimeProvider, type StudentRuntimeContextValue } from "../../shell/studentAppContext";

function defineScrollMetrics(
  element: HTMLElement,
  metrics: {
    scrollHeight?: number;
    clientHeight?: number;
    scrollTop?: number;
    scrollWidth?: number;
    clientWidth?: number;
    scrollLeft?: number;
  },
) {
  Object.defineProperty(element, "scrollHeight", { configurable: true, value: metrics.scrollHeight ?? 0 });
  Object.defineProperty(element, "clientHeight", { configurable: true, value: metrics.clientHeight ?? 0 });
  Object.defineProperty(element, "scrollWidth", { configurable: true, value: metrics.scrollWidth ?? 0 });
  Object.defineProperty(element, "clientWidth", { configurable: true, value: metrics.clientWidth ?? 0 });
  Object.defineProperty(element, "scrollTop", {
    configurable: true,
    get: () => metrics.scrollTop ?? 0,
    set: (value) => {
      metrics.scrollTop = value;
    },
  });
  Object.defineProperty(element, "scrollLeft", {
    configurable: true,
    get: () => metrics.scrollLeft ?? 0,
    set: (value) => {
      metrics.scrollLeft = value;
    },
  });
}

class TestPointerEvent extends MouseEvent {
  pointerId: number;
  pointerType: string;
  isPrimary: boolean;

  constructor(type: string, init: PointerEventInit = {}) {
    super(type, init);
    this.pointerId = init.pointerId ?? 1;
    this.pointerType = init.pointerType ?? "";
    this.isPrimary = init.isPrimary ?? true;
  }
}

function previewRuntimeContext(preview = true): StudentRuntimeContextValue {
  return {
    user: {
      id: 1,
      username: "preview-student",
      display_name: "Preview Student",
      role: "student",
      student_id: "00000000",
      class_name: "Preview Class",
      preview_mode: preview,
      preview_purpose: preview ? "teacher_student_device_preview" : "",
    },
    appConfig: {
      preview_mode: preview,
      preview_policy: {},
    },
    configError: "",
    previewMode: preview,
    previewPolicy: {},
    canUseAssistant: true,
    canUseFeedback: true,
    onLogout: vi.fn(),
    startAssessmentSession: vi.fn(),
    startPointAssessmentSession: vi.fn(),
    posttestLoading: false,
    posttestError: "",
  } as unknown as StudentRuntimeContextValue;
}

function renderPreviewRuntime(preview = true) {
  storePreviewInputHandshake("frame-1", window.location.origin);
  return render(
    createElement(
      StudentRuntimeProvider,
      { value: previewRuntimeContext(preview) },
      createElement(PreviewInputRuntime),
    ),
  );
}

function previewMessage(
  type: PreviewInputMessage["type"],
  overrides: Partial<PreviewInputMessage> = {},
): PreviewInputMessage {
  return {
    namespace: studentPreviewInputNamespace,
    version: studentPreviewInputVersion,
    frameId: "frame-1",
    sequenceId: "sequence-1",
    type,
    point: { x: 12, y: 24 },
    timestamp: 1000,
    primaryButton: type !== "touchEnd" && type !== "touchCancel",
    modifiers: { alt: false, ctrl: false, meta: false, shift: false },
    ...overrides,
  };
}

function dispatchPreviewMessage(message: PreviewInputMessage, origin = window.location.origin) {
  window.dispatchEvent(new MessageEvent("message", { origin, data: message }));
}

describe("student preview input runtime helpers", () => {
  beforeEach(() => {
    document.body.innerHTML = "";
    sessionStorage.clear();
    vi.useRealTimers();
    vi.restoreAllMocks();
    Object.defineProperty(window, "PointerEvent", { configurable: true, value: TestPointerEvent });
    Object.defineProperty(document, "elementFromPoint", { configurable: true, value: vi.fn(() => null) });
  });

  afterEach(() => {
    cleanup();
    vi.useRealTimers();
  });

  it("parses only versioned preview input messages", () => {
    const valid = {
      namespace: studentPreviewInputNamespace,
      version: studentPreviewInputVersion,
      frameId: "frame-1",
      sequenceId: "sequence-1",
      type: "touchStart",
      point: { x: 12, y: 24 },
      timestamp: 123,
      primaryButton: false,
      modifiers: { alt: false, ctrl: false, meta: false, shift: false },
    };

    expect(parsePreviewInputMessage(valid)).toMatchObject(valid);
    expect(parsePreviewInputMessage({ ...valid, version: 1 })).toBeNull();
    expect(parsePreviewInputMessage({ ...valid, type: "wheel", deltaY: 24, primaryButton: false })).toMatchObject({
      type: "wheel",
      deltaY: 24,
    });
    expect(parsePreviewInputMessage({ ...valid, type: "tap" })).toBeNull();
    expect(parsePreviewInputMessage({ ...valid, type: "longPress" })).toBeNull();
    expect(parsePreviewInputMessage({ ...valid, namespace: "other" })).toBeNull();
    expect(parsePreviewInputMessage({ ...valid, point: { x: Number.NaN, y: 24 } })).toBeNull();
    expect(parsePreviewInputMessage({ ...valid, type: "wheel", deltaX: Number.NaN })).toBeNull();
    expect(parsePreviewInputMessage({ ...valid, type: "wheel", deltaX: undefined, deltaY: undefined })).toBeNull();
  });

  it("stores preview frame and teacher origin handshake data", () => {
    storePreviewInputHandshake("frame-1", "http://127.0.0.1:5174");

    expect(sessionStorage.getItem("chem_student_preview_frame_id")).toBe("frame-1");
    expect(sessionStorage.getItem("chem_student_preview_teacher_origin")).toBe("http://127.0.0.1:5174");
  });

  it("activates real actionable elements through click without leaving desktop focus", () => {
    const button = document.createElement("button");
    const clickHandler = vi.fn();
    button.addEventListener("click", clickHandler);
    document.body.appendChild(button);

    const target = resolvePreviewActionTarget(button, { x: 0, y: 0 });
    expect(activatePreviewTarget(target)).toBe(true);

    expect(clickHandler).toHaveBeenCalledTimes(1);
    expect(document.activeElement).toBe(document.body);
  });

  it("dispatches cancelable pointer events so preview taps match mobile outside dismissal", () => {
    const backdrop = document.createElement("div");
    const events: string[] = [];
    backdrop.addEventListener("pointerdown", (event) => {
      events.push(`pointerdown:${(event as PointerEvent).pointerType}`);
      event.preventDefault();
    });
    backdrop.addEventListener("pointerup", () => events.push("pointerup"));
    backdrop.addEventListener("pointermove", () => events.push("pointermove"));
    document.body.appendChild(backdrop);

    const pressAllowed = dispatchPreviewPointerEvent(backdrop, "pointerdown", { x: 12, y: 24 }, true);
    const moveAllowed = dispatchPreviewPointerEvent(backdrop, "pointermove", { x: 16, y: 24 }, true);
    const releaseAllowed = dispatchPreviewPointerEvent(backdrop, "pointerup", { x: 12, y: 24 }, false);

    expect(pressAllowed).toBe(false);
    expect(moveAllowed).toBe(true);
    expect(releaseAllowed).toBe(true);
    expect(events).toEqual(["pointerdown:touch", "pointermove", "pointerup"]);
  });

  it("focuses editable elements without replacing them", () => {
    const input = document.createElement("input");
    const clickHandler = vi.fn();
    input.addEventListener("click", clickHandler);
    document.body.appendChild(input);

    expect(activatePreviewTarget(input)).toBe(true);
    expect(document.activeElement).toBe(input);
    expect(clickHandler).toHaveBeenCalledTimes(1);
  });

  it("finds the nearest scrollable ancestor for upward and downward drags", () => {
    const outer = document.createElement("div");
    const inner = document.createElement("div");
    const child = document.createElement("button");
    outer.style.overflowY = "auto";
    inner.style.overflowY = "auto";
    defineScrollMetrics(outer, { scrollHeight: 1000, clientHeight: 300, scrollTop: 100 });
    defineScrollMetrics(inner, { scrollHeight: 800, clientHeight: 200, scrollTop: 20 });
    inner.appendChild(child);
    outer.appendChild(inner);
    document.body.appendChild(outer);

    expect(findScrollablePreviewTarget(child, 30)).toMatchObject({ kind: "element", element: inner });
    applyPreviewScroll(findScrollablePreviewTarget(child, 30), 30);
    expect(inner.scrollTop).toBe(50);

    applyPreviewScroll(findScrollablePreviewTarget(child, -40), -40);
    expect(inner.scrollTop).toBe(10);
  });

  it("clamps scroll positions to valid ranges", () => {
    const scroller = document.createElement("div");
    scroller.style.overflowY = "auto";
    defineScrollMetrics(scroller, { scrollHeight: 500, clientHeight: 100, scrollTop: 390 });
    document.body.appendChild(scroller);

    applyPreviewScroll({ kind: "element", element: scroller }, 100);
    expect(scroller.scrollTop).toBe(400);

    applyPreviewScroll({ kind: "element", element: scroller }, -999);
    expect(scroller.scrollTop).toBe(0);
  });

  it("finds and applies horizontal scroll for preview left and right swipes", () => {
    const rail = document.createElement("div");
    const tile = document.createElement("button");
    rail.style.overflowX = "auto";
    defineScrollMetrics(rail, { scrollWidth: 620, clientWidth: 260, scrollLeft: 80 });
    rail.appendChild(tile);
    document.body.appendChild(rail);

    const target = findScrollablePreviewTarget(tile, 60, "x");
    expect(target).toMatchObject({ kind: "element", element: rail });

    applyPreviewScroll(target, 60, "x");
    expect(rail.scrollLeft).toBe(140);

    applyPreviewScroll(findScrollablePreviewTarget(tile, -200, "x"), -200, "x");
    expect(rail.scrollLeft).toBe(0);

    applyPreviewScroll(findScrollablePreviewTarget(tile, 999, "x"), 999, "x");
    expect(rail.scrollLeft).toBe(360);
  });

  it("applies preview wheel deltas to the nearest real scroll containers", () => {
    const page = document.createElement("div");
    const rail = document.createElement("div");
    const tile = document.createElement("button");
    page.style.overflowY = "auto";
    rail.style.overflowX = "auto";
    defineScrollMetrics(page, { scrollHeight: 900, clientHeight: 300, scrollTop: 10 });
    defineScrollMetrics(rail, { scrollWidth: 620, clientWidth: 260, scrollLeft: 80 });
    rail.appendChild(tile);
    page.appendChild(rail);
    document.body.appendChild(page);

    expect(applyPreviewWheelScroll(tile, 40, 70)).toBe(true);
    expect(rail.scrollLeft).toBe(120);
    expect(page.scrollTop).toBe(80);
  });

  it("keeps horizontal preview swipes locked to the starting rail when the pointer leaves it", () => {
    const rail = document.createElement("div");
    const tile = document.createElement("button");
    const summary = document.createElement("section");
    rail.style.overflowX = "auto";
    defineScrollMetrics(rail, { scrollWidth: 620, clientWidth: 260, scrollLeft: 80 });
    rail.appendChild(tile);
    document.body.append(rail, summary);

    const scrolled = applyPreviewDragScroll(tile, summary, { x: 220, y: 40 }, { x: 160, y: 43 });

    expect(scrolled).toBe(true);
    expect(rail.scrollLeft).toBe(140);

    const next = applyPreviewDragScrollWithLock(tile, summary, { x: 160, y: 43 }, { x: 100, y: 45 }, {
      target: { kind: "element", element: rail },
      axis: "x",
    });
    expect(next.scrolled).toBe(true);
    expect(next.lock?.target).toMatchObject({ kind: "element", element: rail });
    expect(rail.scrollLeft).toBe(200);
  });

  it("accumulates locked horizontal drag distance when scroll snap rejects tiny move steps", () => {
    const rail = document.createElement("div");
    const tile = document.createElement("button");
    const label = document.createElement("strong");
    let scrollLeft = 0;
    rail.style.overflowX = "auto";
    Object.defineProperty(rail, "scrollWidth", { configurable: true, value: 620 });
    Object.defineProperty(rail, "clientWidth", { configurable: true, value: 260 });
    Object.defineProperty(rail, "scrollLeft", {
      configurable: true,
      get: () => scrollLeft,
      set: (value) => {
        scrollLeft = value < 40 ? 0 : value;
      },
    });
    tile.appendChild(label);
    rail.appendChild(tile);
    document.body.appendChild(rail);

    const first = applyPreviewDragScrollWithLock(tile, label, { x: 180, y: 40 }, { x: 166, y: 40 });
    expect(first.scrolled).toBe(true);
    expect(rail.scrollLeft).toBe(0);

    const second = applyPreviewDragScrollWithLock(tile, label, { x: 166, y: 40 }, { x: 152, y: 40 }, first.lock);
    expect(second.scrolled).toBe(true);
    expect(rail.scrollLeft).toBe(0);

    const third = applyPreviewDragScrollWithLock(tile, label, { x: 152, y: 40 }, { x: 138, y: 40 }, second.lock);
    expect(third.scrolled).toBe(true);
    expect(rail.scrollLeft).toBe(42);
  });

  it("activates a real target once after a short lifecycle tap", () => {
    const button = document.createElement("button");
    const events: string[] = [];
    button.addEventListener("pointerdown", (event) => events.push(`down:${(event as PointerEvent).pointerType}`));
    button.addEventListener("pointerup", (event) => events.push(`up:${(event as PointerEvent).pointerType}`));
    button.addEventListener("click", () => events.push("click"));
    document.body.appendChild(button);
    vi.mocked(document.elementFromPoint).mockReturnValue(button);

    renderPreviewRuntime();
    dispatchPreviewMessage(previewMessage("touchStart", { point: { x: 10, y: 10 }, timestamp: 1000, startedAt: 1000 }));
    dispatchPreviewMessage(previewMessage("touchEnd", { point: { x: 11, y: 11 }, timestamp: 1100, startedAt: 1000, primaryButton: false }));

    expect(events).toEqual(["down:touch", "up:touch", "click"]);
  });

  it("suppresses click activation after drag movement and scrolls the real container", () => {
    const scroller = document.createElement("div");
    const tile = document.createElement("button");
    const events: string[] = [];
    scroller.style.overflowY = "auto";
    defineScrollMetrics(scroller, { scrollHeight: 800, clientHeight: 200, scrollTop: 0 });
    tile.addEventListener("pointerdown", () => events.push("down"));
    tile.addEventListener("pointermove", () => events.push("move"));
    tile.addEventListener("pointerup", () => events.push("up"));
    tile.addEventListener("click", () => events.push("click"));
    scroller.appendChild(tile);
    document.body.appendChild(scroller);
    vi.mocked(document.elementFromPoint).mockReturnValue(tile);

    renderPreviewRuntime();
    dispatchPreviewMessage(previewMessage("touchStart", { point: { x: 40, y: 100 }, timestamp: 1000, startedAt: 1000 }));
    dispatchPreviewMessage(
      previewMessage("touchMove", {
        point: { x: 40, y: 60 },
        previousPoint: { x: 40, y: 100 },
        timestamp: 1040,
        startedAt: 1000,
      }),
    );
    dispatchPreviewMessage(previewMessage("touchEnd", { point: { x: 40, y: 60 }, timestamp: 1080, startedAt: 1000, primaryButton: false }));

    expect(scroller.scrollTop).toBe(40);
    expect(events).toEqual(["down", "move", "up"]);
  });

  it("scrolls real content from preview wheel messages", () => {
    const scroller = document.createElement("div");
    const tile = document.createElement("button");
    scroller.style.overflowY = "auto";
    defineScrollMetrics(scroller, { scrollHeight: 800, clientHeight: 200, scrollTop: 0 });
    scroller.appendChild(tile);
    document.body.appendChild(scroller);
    vi.mocked(document.elementFromPoint).mockReturnValue(tile);

    renderPreviewRuntime();
    dispatchPreviewMessage(
      previewMessage("wheel", {
        point: { x: 40, y: 100 },
        deltaY: 72,
        timestamp: 1040,
        primaryButton: false,
      }),
    );

    expect(scroller.scrollTop).toBe(72);
  });

  it("suppresses normal tap activation after a long press", () => {
    vi.useFakeTimers();
    const button = document.createElement("button");
    const events: string[] = [];
    button.addEventListener("pointerdown", () => events.push("down"));
    button.addEventListener("pointerup", () => events.push("up"));
    button.addEventListener("click", () => events.push("click"));
    document.body.appendChild(button);
    vi.mocked(document.elementFromPoint).mockReturnValue(button);

    renderPreviewRuntime();
    dispatchPreviewMessage(previewMessage("touchStart", { point: { x: 10, y: 10 }, timestamp: 1000, startedAt: 1000 }));
    vi.advanceTimersByTime(previewLongPressDelayMs);
    dispatchPreviewMessage(
      previewMessage("touchEnd", {
        point: { x: 10, y: 10 },
        timestamp: 1000 + previewLongPressDelayMs + 1,
        startedAt: 1000,
        primaryButton: false,
      }),
    );

    expect(events).toEqual(["down", "up"]);
  });

  it("cancels active lifecycle sequences without click activation", () => {
    const button = document.createElement("button");
    const events: string[] = [];
    button.addEventListener("pointerdown", () => events.push("down"));
    button.addEventListener("pointercancel", () => events.push("cancel"));
    button.addEventListener("click", () => events.push("click"));
    document.body.appendChild(button);
    vi.mocked(document.elementFromPoint).mockReturnValue(button);

    renderPreviewRuntime();
    dispatchPreviewMessage(previewMessage("touchStart", { point: { x: 10, y: 10 }, timestamp: 1000, startedAt: 1000 }));
    dispatchPreviewMessage(previewMessage("touchCancel", { point: { x: 10, y: 10 }, timestamp: 1020, startedAt: 1000, primaryButton: false }));

    expect(events).toEqual(["down", "cancel"]);
  });

  it("does not click through when the pressed target consumes pointerdown", () => {
    const backdrop = document.createElement("div");
    const events: string[] = [];
    backdrop.setAttribute("role", "button");
    backdrop.addEventListener("pointerdown", (event) => {
      events.push("down");
      event.preventDefault();
    });
    backdrop.addEventListener("pointerup", () => events.push("up"));
    backdrop.addEventListener("click", () => events.push("click"));
    document.body.appendChild(backdrop);
    vi.mocked(document.elementFromPoint).mockReturnValue(backdrop);

    renderPreviewRuntime();
    dispatchPreviewMessage(previewMessage("touchStart", { point: { x: 10, y: 10 }, timestamp: 1000, startedAt: 1000 }));
    dispatchPreviewMessage(previewMessage("touchEnd", { point: { x: 10, y: 10 }, timestamp: 1020, startedAt: 1000, primaryButton: false }));

    expect(events).toEqual(["down", "up"]);
  });

  it("ignores preview messages in ordinary student sessions", () => {
    const button = document.createElement("button");
    const clickHandler = vi.fn();
    button.addEventListener("click", clickHandler);
    document.body.appendChild(button);
    vi.mocked(document.elementFromPoint).mockReturnValue(button);

    renderPreviewRuntime(false);
    dispatchPreviewMessage(previewMessage("touchStart", { point: { x: 10, y: 10 }, timestamp: 1000, startedAt: 1000 }));
    dispatchPreviewMessage(previewMessage("touchEnd", { point: { x: 10, y: 10 }, timestamp: 1020, startedAt: 1000, primaryButton: false }));

    expect(clickHandler).not.toHaveBeenCalled();
  });

  it("rejects messages from unexpected origins without canceling the active sequence", () => {
    const button = document.createElement("button");
    const events: string[] = [];
    button.addEventListener("pointerdown", () => events.push("down"));
    button.addEventListener("pointercancel", () => events.push("cancel"));
    button.addEventListener("pointerup", () => events.push("up"));
    button.addEventListener("click", () => events.push("click"));
    document.body.appendChild(button);
    vi.mocked(document.elementFromPoint).mockReturnValue(button);

    renderPreviewRuntime();
    dispatchPreviewMessage(previewMessage("touchStart", { point: { x: 10, y: 10 }, timestamp: 1000, startedAt: 1000 }));
    dispatchPreviewMessage(previewMessage("touchCancel", { point: { x: 10, y: 10 }, timestamp: 1010, startedAt: 1000, primaryButton: false }), "http://evil.example");
    dispatchPreviewMessage(previewMessage("touchEnd", { point: { x: 10, y: 10 }, timestamp: 1020, startedAt: 1000, primaryButton: false }));

    expect(events).toEqual(["down", "up", "click"]);
  });
});
