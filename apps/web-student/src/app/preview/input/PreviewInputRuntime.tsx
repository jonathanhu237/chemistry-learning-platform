import { useEffect, useRef } from "react";

import { isTeacherStudentPreview } from "../previewSandbox";
import { useStudentRuntime } from "../../shell/studentAppContext";
import {
  parsePreviewInputMessage,
  readPreviewInputHandshake,
  type PreviewInputMessage,
  type PreviewInputPoint,
} from "./previewInputProtocol";

type ActivePreviewInputSequence = {
  sequenceId: string;
  initialTarget: Element | null;
  pressTarget: Element | null;
  lastPoint: PreviewInputPoint;
  moved: boolean;
  suppressTapActivation: boolean;
};

type ScrollTarget =
  | { kind: "element"; element: HTMLElement }
  | { kind: "document"; element: Element };

type ScrollAxis = "x" | "y";

const actionableSelector = [
  "button",
  "a[href]",
  "input",
  "textarea",
  "select",
  "summary",
  "label",
  "[role='button']",
  "[role='tab']",
  "[role='link']",
  "[tabindex]",
].join(",");

function isHTMLElement(value: Element | null): value is HTMLElement {
  return value instanceof HTMLElement;
}

function isDisabledControl(element: Element): boolean {
  return (
    (element instanceof HTMLButtonElement && element.disabled) ||
    (element instanceof HTMLInputElement && element.disabled) ||
    (element instanceof HTMLTextAreaElement && element.disabled) ||
    (element instanceof HTMLSelectElement && element.disabled)
  );
}

function isEditableElement(element: Element): element is HTMLElement {
  return (
    element instanceof HTMLInputElement ||
    element instanceof HTMLTextAreaElement ||
    element instanceof HTMLSelectElement ||
    (element instanceof HTMLElement && element.isContentEditable)
  );
}

function canOverflowY(element: HTMLElement): boolean {
  const style = window.getComputedStyle(element);
  return /(auto|scroll|overlay)/.test(`${style.overflowY} ${style.overflow}`);
}

function canOverflowX(element: HTMLElement): boolean {
  const style = window.getComputedStyle(element);
  return /(auto|scroll|overlay)/.test(`${style.overflowX} ${style.overflow}`);
}

function canOverflowOnAxis(element: HTMLElement, axis: ScrollAxis): boolean {
  return axis === "x" ? canOverflowX(element) : canOverflowY(element);
}

function scrollRange(element: Element, axis: ScrollAxis = "y"): { current: number; max: number } {
  const current = axis === "x" && "scrollLeft" in element ? Number(element.scrollLeft) : "scrollTop" in element ? Number(element.scrollTop) : 0;
  const scrollHeight = "scrollHeight" in element ? Number(element.scrollHeight) : 0;
  const clientHeight = "clientHeight" in element ? Number(element.clientHeight) : 0;
  const scrollWidth = "scrollWidth" in element ? Number(element.scrollWidth) : 0;
  const clientWidth = "clientWidth" in element ? Number(element.clientWidth) : 0;
  return {
    current,
    max: Math.max(0, axis === "x" ? scrollWidth - clientWidth : scrollHeight - clientHeight),
  };
}

function canScrollInDirection(element: Element, deltaScroll: number, axis: ScrollAxis = "y"): boolean {
  const { current, max } = scrollRange(element, axis);
  if (max <= 0) return false;
  if (deltaScroll > 0) return current < max;
  if (deltaScroll < 0) return current > 0;
  return false;
}

export function elementFromPreviewPoint(point: PreviewInputPoint): Element | null {
  if (typeof document.elementFromPoint !== "function") return null;
  return document.elementFromPoint(point.x, point.y);
}

export function findScrollablePreviewTarget(start: Element | null, deltaScroll: number, axis: ScrollAxis = "y"): ScrollTarget | null {
  let current: Element | null = start;
  while (current && current !== document.body && current !== document.documentElement) {
    if (isHTMLElement(current) && canOverflowOnAxis(current, axis) && canScrollInDirection(current, deltaScroll, axis)) {
      return { kind: "element", element: current };
    }
    current = current.parentElement;
  }

  const scrollingElement = document.scrollingElement || document.documentElement;
  return canScrollInDirection(scrollingElement, deltaScroll, axis) ? { kind: "document", element: scrollingElement } : null;
}

export function applyPreviewScroll(target: ScrollTarget | null, deltaScroll: number, axis: ScrollAxis = "y"): void {
  if (!target || deltaScroll === 0) return;
  const { current, max } = scrollRange(target.element, axis);
  const nextTop = Math.min(Math.max(current + deltaScroll, 0), max);
  if (axis === "x" && "scrollLeft" in target.element) {
    target.element.scrollLeft = nextTop;
  } else if ("scrollTop" in target.element) {
    target.element.scrollTop = nextTop;
  }
}

export function applyPreviewDragScroll(
  initialTarget: Element | null,
  hitTarget: Element | null,
  previousPoint: PreviewInputPoint,
  point: PreviewInputPoint,
): boolean {
  const deltaScrollX = previousPoint.x - point.x;
  const deltaScrollY = previousPoint.y - point.y;
  const horizontalTarget =
    findScrollablePreviewTarget(hitTarget, deltaScrollX, "x") ||
    findScrollablePreviewTarget(initialTarget, deltaScrollX, "x");

  if (Math.abs(deltaScrollX) > Math.abs(deltaScrollY) && horizontalTarget) {
    applyPreviewScroll(horizontalTarget, deltaScrollX, "x");
    return true;
  }

  const verticalTarget = findScrollablePreviewTarget(hitTarget || initialTarget, deltaScrollY, "y");
  if (verticalTarget) {
    applyPreviewScroll(verticalTarget, deltaScrollY, "y");
    return true;
  }

  if (horizontalTarget) {
    applyPreviewScroll(horizontalTarget, deltaScrollX, "x");
    return true;
  }

  return false;
}

export function resolvePreviewActionTarget(initialTarget: Element | null, fallbackPoint: PreviewInputPoint): Element | null {
  const fallbackTarget = elementFromPreviewPoint(fallbackPoint);
  const candidate = initialTarget?.isConnected ? initialTarget : fallbackTarget;
  if (!candidate) return null;
  if (isDisabledControl(candidate)) return null;
  const actionable = candidate.closest(actionableSelector);
  if (!actionable || isDisabledControl(actionable)) return null;
  return actionable;
}

export function dispatchPreviewPointerEvent(
  target: Element | null,
  type: "pointerdown" | "pointerup" | "pointercancel",
  point: PreviewInputPoint,
  pressed: boolean,
): boolean {
  if (!target || !target.isConnected) return true;
  const eventInit: PointerEventInit = {
    bubbles: true,
    cancelable: true,
    composed: true,
    clientX: point.x,
    clientY: point.y,
    pointerId: 1,
    pointerType: "touch",
    isPrimary: true,
    button: 0,
    buttons: pressed ? 1 : 0,
  };
  const event =
    typeof window.PointerEvent === "function"
      ? new PointerEvent(type, eventInit)
      : new MouseEvent(type, eventInit);
  return target.dispatchEvent(event);
}

export function activatePreviewTarget(target: Element | null): boolean {
  if (!target || !target.isConnected || isDisabledControl(target)) return false;
  if (isEditableElement(target)) {
    target.focus({ preventScroll: true });
    target.click();
    return true;
  }
  if (target instanceof HTMLElement || target instanceof SVGElement) {
    target.dispatchEvent(new MouseEvent("click", { bubbles: true, cancelable: true }));
    return true;
  }
  return false;
}

function allowedOrigins(teacherOrigin: string): Set<string> {
  const origins = new Set<string>();
  if (teacherOrigin) origins.add(teacherOrigin);
  if (document.referrer) {
    try {
      origins.add(new URL(document.referrer).origin);
    } catch {
      // Ignore malformed referrers.
    }
  }
  origins.add(window.location.origin);
  if (window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost") {
    origins.add(`${window.location.protocol}//${window.location.hostname}:5174`);
    origins.add(`${window.location.protocol}//${window.location.hostname}:4174`);
  }
  return origins;
}

function messageMatchesHandshake(message: PreviewInputMessage, origin: string, frameId: string, teacherOrigin: string): boolean {
  if (frameId && message.frameId !== frameId) return false;
  return allowedOrigins(teacherOrigin).has(origin);
}

export function PreviewInputRuntime() {
  const runtime = useStudentRuntime();
  const activeSequenceRef = useRef<ActivePreviewInputSequence | null>(null);
  const enabled = isTeacherStudentPreview(runtime);

  useEffect(() => {
    if (!enabled) {
      activeSequenceRef.current = null;
      return;
    }

    const { frameId, teacherOrigin } = readPreviewInputHandshake();

    const clearSequence = () => {
      activeSequenceRef.current = null;
    };

    const handleMessage = (event: MessageEvent) => {
      const message = parsePreviewInputMessage(event.data);
      if (!message || !messageMatchesHandshake(message, event.origin, frameId, teacherOrigin)) {
        if (message?.type === "touchCancel") clearSequence();
        return;
      }

      if (message.type === "hover") return;

      if (message.type === "touchCancel") {
        const activeSequence = activeSequenceRef.current;
        const cancelTarget = activeSequence?.pressTarget?.isConnected ? activeSequence.pressTarget : null;
        if (activeSequence) dispatchPreviewPointerEvent(cancelTarget, "pointercancel", activeSequence.lastPoint, false);
        clearSequence();
        return;
      }

      if (message.type === "touchStart") {
        const initialTarget = elementFromPreviewPoint(message.point);
        const pressAllowed = dispatchPreviewPointerEvent(initialTarget, "pointerdown", message.point, true);
        activeSequenceRef.current = {
          sequenceId: message.sequenceId,
          initialTarget,
          pressTarget: initialTarget,
          lastPoint: message.point,
          moved: false,
          suppressTapActivation: !pressAllowed,
        };
        return;
      }

      const activeSequence = activeSequenceRef.current;
      if (!activeSequence || activeSequence.sequenceId !== message.sequenceId) {
        return;
      }

      if (message.type === "longPress") {
        return;
      }

      if (message.type === "tap") {
        const releaseTarget = activeSequence.pressTarget?.isConnected
          ? activeSequence.pressTarget
          : elementFromPreviewPoint(message.point);
        dispatchPreviewPointerEvent(releaseTarget, "pointerup", message.point, false);
        if (!activeSequence.suppressTapActivation) {
          const target = resolvePreviewActionTarget(activeSequence.initialTarget, message.point);
          activatePreviewTarget(target);
        }
        clearSequence();
        return;
      }

      if (message.type === "touchMove") {
        const previousPoint = message.previousPoint || activeSequence.lastPoint;
        const deltaScrollX = previousPoint.x - message.point.x;
        const deltaScrollY = previousPoint.y - message.point.y;
        const hitTarget = elementFromPreviewPoint(message.point) || activeSequence.initialTarget;
        applyPreviewDragScroll(activeSequence.initialTarget, hitTarget, previousPoint, message.point);
        activeSequence.lastPoint = message.point;
        if (Math.abs(deltaScrollX) > 0 || Math.abs(deltaScrollY) > 0) activeSequence.moved = true;
        return;
      }

      if (message.type === "touchEnd") {
        const releaseTarget = activeSequence.pressTarget?.isConnected
          ? activeSequence.pressTarget
          : elementFromPreviewPoint(message.point);
        dispatchPreviewPointerEvent(releaseTarget, "pointerup", message.point, false);
        clearSequence();
      }
    };

    window.addEventListener("message", handleMessage);
    window.addEventListener("beforeunload", clearSequence);
    return () => {
      window.removeEventListener("message", handleMessage);
      window.removeEventListener("beforeunload", clearSequence);
      clearSequence();
    };
  }, [enabled]);

  return null;
}
