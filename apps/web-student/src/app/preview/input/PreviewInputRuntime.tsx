import { useEffect, useRef } from "react";

import { isTeacherStudentPreview } from "../previewSandbox";
import { useStudentRuntime } from "../../shell/studentAppContext";
import {
  parsePreviewInputMessage,
  readPreviewInputHandshake,
  type PreviewInputMessage,
  type PreviewInputPoint,
} from "./previewInputProtocol";

export const previewTapMovementThreshold = 8;
export const previewDragMovementThreshold = 8;
export const previewTapDurationLimitMs = 300;
export const previewLongPressDelayMs = 520;

type PreviewInputPhase = "pressing" | "dragging" | "longPressReady";

type ActivePreviewInputSequence = {
  sequenceId: string;
  initialTarget: Element | null;
  pressTarget: Element | null;
  startPoint: PreviewInputPoint;
  lastPoint: PreviewInputPoint;
  startedAt: number;
  totalMovement: number;
  phase: PreviewInputPhase;
  suppressTapActivation: boolean;
  scrollLock: PreviewScrollLock | null;
};

type ScrollTarget =
  | { kind: "element"; element: HTMLElement }
  | { kind: "document"; element: Element };

type ScrollAxis = "x" | "y";

export type PreviewScrollLock = {
  target: ScrollTarget;
  axis: ScrollAxis;
  startScroll?: number;
  accumulatedDelta?: number;
};

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

function pointDistance(a: PreviewInputPoint, b: PreviewInputPoint): number {
  return Math.hypot(a.x - b.x, a.y - b.y);
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

function dominantAxis(deltaScrollX: number, deltaScrollY: number): ScrollAxis {
  return Math.abs(deltaScrollX) > Math.abs(deltaScrollY) ? "x" : "y";
}

function nonZeroDeltaForAxis(axis: ScrollAxis, deltaScrollX: number, deltaScrollY: number): number {
  return axis === "x" ? deltaScrollX : deltaScrollY;
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

function applyPreviewScrollPosition(target: ScrollTarget, nextScroll: number, axis: ScrollAxis): void {
  const { max } = scrollRange(target.element, axis);
  const clamped = Math.min(Math.max(nextScroll, 0), max);
  if (axis === "x" && "scrollLeft" in target.element) {
    target.element.scrollLeft = clamped;
  } else if ("scrollTop" in target.element) {
    target.element.scrollTop = clamped;
  }
}

function choosePreviewScrollLock(
  initialTarget: Element | null,
  hitTarget: Element | null,
  deltaScrollX: number,
  deltaScrollY: number,
): PreviewScrollLock | null {
  const preferredAxis = dominantAxis(deltaScrollX, deltaScrollY);
  const fallbackAxis = preferredAxis === "x" ? "y" : "x";
  const preferredDelta = nonZeroDeltaForAxis(preferredAxis, deltaScrollX, deltaScrollY);
  const fallbackDelta = nonZeroDeltaForAxis(fallbackAxis, deltaScrollX, deltaScrollY);
  const preferredTarget =
    findScrollablePreviewTarget(hitTarget, preferredDelta, preferredAxis) ||
    findScrollablePreviewTarget(initialTarget, preferredDelta, preferredAxis);

  if (preferredTarget) return { target: preferredTarget, axis: preferredAxis };

  const fallbackTarget =
    findScrollablePreviewTarget(hitTarget || initialTarget, fallbackDelta, fallbackAxis) ||
    findScrollablePreviewTarget(initialTarget, fallbackDelta, fallbackAxis);
  return fallbackTarget ? { target: fallbackTarget, axis: fallbackAxis } : null;
}

export function applyPreviewDragScrollWithLock(
  initialTarget: Element | null,
  hitTarget: Element | null,
  previousPoint: PreviewInputPoint,
  point: PreviewInputPoint,
  existingLock: PreviewScrollLock | null = null,
): { scrolled: boolean; lock: PreviewScrollLock | null } {
  const deltaScrollX = previousPoint.x - point.x;
  const deltaScrollY = previousPoint.y - point.y;
  const existingDelta = existingLock ? nonZeroDeltaForAxis(existingLock.axis, deltaScrollX, deltaScrollY) : 0;

  if (existingLock && canScrollInDirection(existingLock.target.element, existingDelta, existingLock.axis)) {
    const startScroll = existingLock.startScroll ?? scrollRange(existingLock.target.element, existingLock.axis).current;
    const accumulatedDelta = (existingLock.accumulatedDelta ?? 0) + existingDelta;
    const nextLock = { ...existingLock, startScroll, accumulatedDelta };
    applyPreviewScrollPosition(nextLock.target, startScroll + accumulatedDelta, nextLock.axis);
    return { scrolled: existingDelta !== 0, lock: nextLock };
  }

  const nextLock = choosePreviewScrollLock(initialTarget, hitTarget, deltaScrollX, deltaScrollY);
  if (!nextLock) return { scrolled: false, lock: existingLock };

  const delta = nonZeroDeltaForAxis(nextLock.axis, deltaScrollX, deltaScrollY);
  const startScroll = scrollRange(nextLock.target.element, nextLock.axis).current;
  const lockedScroll = { ...nextLock, startScroll, accumulatedDelta: delta };
  applyPreviewScrollPosition(lockedScroll.target, startScroll + delta, lockedScroll.axis);
  return { scrolled: delta !== 0, lock: lockedScroll };
}

export function applyPreviewDragScroll(
  initialTarget: Element | null,
  hitTarget: Element | null,
  previousPoint: PreviewInputPoint,
  point: PreviewInputPoint,
): boolean {
  return applyPreviewDragScrollWithLock(initialTarget, hitTarget, previousPoint, point).scrolled;
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
  type: "pointerdown" | "pointermove" | "pointerup" | "pointercancel",
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
    origins.add(`${window.location.protocol}//${window.location.hostname}:15174`);
    origins.add(`${window.location.protocol}//${window.location.hostname}:5174`);
    origins.add(`${window.location.protocol}//${window.location.hostname}:4174`);
  }
  return origins;
}

function messageMatchesHandshake(message: PreviewInputMessage, origin: string, frameId: string, teacherOrigin: string): boolean {
  if (frameId && message.frameId !== frameId) return false;
  return allowedOrigins(teacherOrigin).has(origin);
}

function releaseTargetForSequence(sequence: ActivePreviewInputSequence, point: PreviewInputPoint): Element | null {
  return sequence.pressTarget?.isConnected ? sequence.pressTarget : elementFromPreviewPoint(point);
}

function shouldActivateTap(sequence: ActivePreviewInputSequence, point: PreviewInputPoint, timestamp: number): boolean {
  const duration = timestamp - sequence.startedAt;
  return (
    sequence.phase === "pressing" &&
    !sequence.suppressTapActivation &&
    duration <= previewTapDurationLimitMs &&
    sequence.totalMovement <= previewTapMovementThreshold &&
    pointDistance(sequence.startPoint, point) <= previewTapMovementThreshold
  );
}

export function PreviewInputRuntime() {
  const runtime = useStudentRuntime();
  const activeSequenceRef = useRef<ActivePreviewInputSequence | null>(null);
  const longPressTimerRef = useRef<number | null>(null);
  const enabled = isTeacherStudentPreview(runtime);

  useEffect(() => {
    if (!enabled) {
      activeSequenceRef.current = null;
      return;
    }

    const { frameId, teacherOrigin } = readPreviewInputHandshake();

    const clearLongPressTimer = () => {
      if (longPressTimerRef.current !== null) {
        window.clearTimeout(longPressTimerRef.current);
        longPressTimerRef.current = null;
      }
    };

    const clearSequence = () => {
      clearLongPressTimer();
      activeSequenceRef.current = null;
    };

    const cancelActiveSequence = () => {
      const activeSequence = activeSequenceRef.current;
      if (activeSequence) {
        const cancelTarget = releaseTargetForSequence(activeSequence, activeSequence.lastPoint);
        dispatchPreviewPointerEvent(cancelTarget, "pointercancel", activeSequence.lastPoint, false);
      }
      clearSequence();
    };

    const armLongPressTimer = (sequenceId: string) => {
      clearLongPressTimer();
      longPressTimerRef.current = window.setTimeout(() => {
        const activeSequence = activeSequenceRef.current;
        if (!activeSequence || activeSequence.sequenceId !== sequenceId) return;
        if (activeSequence.phase !== "pressing") return;
        if (activeSequence.totalMovement > previewTapMovementThreshold) return;
        activeSequence.phase = "longPressReady";
      }, previewLongPressDelayMs);
    };

    const handleMessage = (event: MessageEvent) => {
      const message = parsePreviewInputMessage(event.data);
      if (!message || !messageMatchesHandshake(message, event.origin, frameId, teacherOrigin)) return;

      if (message.type === "hover") return;

      if (message.type === "touchCancel") {
        cancelActiveSequence();
        return;
      }

      if (message.type === "touchStart") {
        cancelActiveSequence();
        const initialTarget = elementFromPreviewPoint(message.point);
        const pressAllowed = dispatchPreviewPointerEvent(initialTarget, "pointerdown", message.point, true);
        activeSequenceRef.current = {
          sequenceId: message.sequenceId,
          initialTarget,
          pressTarget: initialTarget,
          startPoint: message.point,
          lastPoint: message.point,
          startedAt: message.startedAt ?? message.timestamp,
          totalMovement: 0,
          phase: "pressing",
          suppressTapActivation: !pressAllowed,
          scrollLock: null,
        };
        armLongPressTimer(message.sequenceId);
        return;
      }

      const activeSequence = activeSequenceRef.current;
      if (!activeSequence || activeSequence.sequenceId !== message.sequenceId) {
        return;
      }

      if (message.type === "touchMove") {
        const previousPoint = message.previousPoint || activeSequence.lastPoint;
        const movementDelta = pointDistance(previousPoint, message.point);
        activeSequence.totalMovement += movementDelta;
        const distanceFromStart = pointDistance(activeSequence.startPoint, message.point);
        const hitTarget = elementFromPreviewPoint(message.point) || activeSequence.initialTarget;
        const moveTarget = activeSequence.pressTarget?.isConnected ? activeSequence.pressTarget : hitTarget;
        dispatchPreviewPointerEvent(moveTarget, "pointermove", message.point, true);

        if (
          activeSequence.phase !== "dragging" &&
          (activeSequence.totalMovement > previewDragMovementThreshold || distanceFromStart > previewDragMovementThreshold)
        ) {
          activeSequence.phase = "dragging";
          clearLongPressTimer();
        }

        if (activeSequence.phase === "dragging") {
          const result = applyPreviewDragScrollWithLock(
            activeSequence.initialTarget,
            hitTarget,
            previousPoint,
            message.point,
            activeSequence.scrollLock,
          );
          activeSequence.scrollLock = result.lock;
        }

        activeSequence.lastPoint = message.point;
        return;
      }

      if (message.type === "touchEnd") {
        clearLongPressTimer();
        const releaseTarget = releaseTargetForSequence(activeSequence, message.point);
        dispatchPreviewPointerEvent(releaseTarget, "pointerup", message.point, false);
        if (shouldActivateTap(activeSequence, message.point, message.timestamp)) {
          const target = resolvePreviewActionTarget(activeSequence.initialTarget, message.point);
          activatePreviewTarget(target);
        }
        clearSequence();
      }
    };

    window.addEventListener("message", handleMessage);
    window.addEventListener("beforeunload", cancelActiveSequence);
    return () => {
      window.removeEventListener("message", handleMessage);
      window.removeEventListener("beforeunload", cancelActiveSequence);
      cancelActiveSequence();
    };
  }, [enabled]);

  return null;
}
