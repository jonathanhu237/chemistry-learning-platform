import { useCallback, useEffect, useMemo, useRef } from "react";
import type { RefObject } from "react";
import { useGesture } from "@use-gesture/react";

import { createPreviewInputMessage, type PreviewInputMessage, type PreviewInputPoint } from "./previewInputProtocol";

const tapMovementThreshold = 8;
const dragThreshold = 6;
const longPressDelayMs = 520;
const indicatorIdleMs = 900;

type PreviewGestureSurfaceProps = {
  enabled: boolean;
  iframeRef: RefObject<HTMLIFrameElement | null>;
  frameId: string;
  targetOrigin: string;
};

type ActiveSequence = {
  id: string;
  startedAt: number;
  startPoint: PreviewInputPoint;
  lastPoint: PreviewInputPoint;
  moved: boolean;
  longPressSent: boolean;
};

type SurfaceBoxQuad = {
  p1: DOMPointReadOnly;
  p2: DOMPointReadOnly;
  p4: DOMPointReadOnly;
};

type SurfaceWithBoxQuads = HTMLElement & {
  getBoxQuads?: (options?: { box?: "border" }) => SurfaceBoxQuad[];
};

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}

function pointDistance(a: PreviewInputPoint, b: PreviewInputPoint): number {
  return Math.hypot(a.x - b.x, a.y - b.y);
}

function eventModifiers(event: UIEvent | Event): PreviewInputMessage["modifiers"] {
  const maybeMouse = event as MouseEvent;
  return {
    alt: Boolean(maybeMouse.altKey),
    ctrl: Boolean(maybeMouse.ctrlKey),
    meta: Boolean(maybeMouse.metaKey),
    shift: Boolean(maybeMouse.shiftKey),
  };
}

function createSequenceId(): string {
  return `gesture-${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`;
}

export function mapClientPointToSurfacePoint(surface: HTMLElement, clientX: number, clientY: number): PreviewInputPoint {
  const localWidth = surface.offsetWidth || surface.clientWidth || surface.getBoundingClientRect().width;
  const localHeight = surface.offsetHeight || surface.clientHeight || surface.getBoundingClientRect().height;
  const quad = (surface as SurfaceWithBoxQuads).getBoxQuads?.({ box: "border" })?.[0];
  if (quad && localWidth > 0 && localHeight > 0) {
    const xAxis = { x: quad.p2.x - quad.p1.x, y: quad.p2.y - quad.p1.y };
    const yAxis = { x: quad.p4.x - quad.p1.x, y: quad.p4.y - quad.p1.y };
    const point = { x: clientX - quad.p1.x, y: clientY - quad.p1.y };
    const xLengthSq = xAxis.x * xAxis.x + xAxis.y * xAxis.y;
    const yLengthSq = yAxis.x * yAxis.x + yAxis.y * yAxis.y;
    if (xLengthSq > 0 && yLengthSq > 0) {
      return {
        x: clamp(((point.x * xAxis.x + point.y * xAxis.y) / xLengthSq) * localWidth, 0, localWidth),
        y: clamp(((point.x * yAxis.x + point.y * yAxis.y) / yLengthSq) * localHeight, 0, localHeight),
      };
    }
  }

  const rect = surface.getBoundingClientRect();
  const quarterTurnScale = localWidth > 0 && localHeight > 0 ? (rect.width / localHeight + rect.height / localWidth) / 2 : 0;
  if (localHeight > localWidth && rect.width > rect.height && quarterTurnScale > 0) {
    return {
      x: clamp((clientY - rect.top) / quarterTurnScale, 0, localWidth),
      y: clamp((rect.right - clientX) / quarterTurnScale, 0, localHeight),
    };
  }

  const scaleX = localWidth > 0 && rect.width > 0 ? localWidth / rect.width : 1;
  const scaleY = localHeight > 0 && rect.height > 0 ? localHeight / rect.height : 1;
  return {
    x: clamp((clientX - rect.left) * scaleX, 0, localWidth || rect.width),
    y: clamp((clientY - rect.top) * scaleY, 0, localHeight || rect.height),
  };
}

export function PreviewGestureSurface({ enabled, iframeRef, frameId, targetOrigin }: PreviewGestureSurfaceProps) {
  const surfaceRef = useRef<HTMLDivElement | null>(null);
  const indicatorRef = useRef<HTMLSpanElement | null>(null);
  const activeSequenceRef = useRef<ActiveSequence | null>(null);
  const rafRef = useRef<number | null>(null);
  const hideTimerRef = useRef<number | null>(null);
  const longPressTimerRef = useRef<number | null>(null);
  const latestIndicatorRef = useRef({ x: 0, y: 0, visible: false, active: false });

  const clearHideTimer = useCallback(() => {
    if (hideTimerRef.current !== null) {
      window.clearTimeout(hideTimerRef.current);
      hideTimerRef.current = null;
    }
  }, []);

  const clearLongPressTimer = useCallback(() => {
    if (longPressTimerRef.current !== null) {
      window.clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
    }
  }, []);

  const flushIndicator = useCallback(() => {
    rafRef.current = null;
    const indicator = indicatorRef.current;
    if (!indicator) return;
    const { x, y, visible, active } = latestIndicatorRef.current;
    indicator.style.transform = `translate3d(${x}px, ${y}px, 0) translate3d(-50%, -50%, 0) scale(${active ? 0.76 : 1})`;
    indicator.classList.toggle("visible", visible);
    indicator.classList.toggle("active", active);
  }, []);

  const scheduleIndicator = useCallback(
    (point: PreviewInputPoint, options: { visible: boolean; active: boolean }) => {
      latestIndicatorRef.current = { x: point.x, y: point.y, visible: options.visible, active: options.active };
      clearHideTimer();
      if (rafRef.current === null) {
        rafRef.current = window.requestAnimationFrame(flushIndicator);
      }
    },
    [clearHideTimer, flushIndicator],
  );

  const hideIndicator = useCallback(
    (delay = 0) => {
      clearHideTimer();
      const run = () => {
        latestIndicatorRef.current = { ...latestIndicatorRef.current, visible: false, active: false };
        if (rafRef.current === null) {
          rafRef.current = window.requestAnimationFrame(flushIndicator);
        }
      };
      if (delay > 0) {
        hideTimerRef.current = window.setTimeout(run, delay);
      } else {
        run();
      }
    },
    [clearHideTimer, flushIndicator],
  );

  const resolvePoint = useCallback((clientX: number, clientY: number): PreviewInputPoint | null => {
    const surface = surfaceRef.current;
    if (!surface) return null;
    return mapClientPointToSurfacePoint(surface, clientX, clientY);
  }, []);

  const postInput = useCallback(
    (message: Omit<PreviewInputMessage, "namespace" | "version" | "timestamp"> & { timestamp?: number }) => {
      if (!enabled || !targetOrigin) return;
      const targetWindow = iframeRef.current?.contentWindow;
      if (!targetWindow) return;
      targetWindow.postMessage(createPreviewInputMessage(message), targetOrigin);
    },
    [enabled, iframeRef, targetOrigin],
  );

  const cancelSequence = useCallback(
    (event?: UIEvent | Event) => {
      const sequence = activeSequenceRef.current;
      clearLongPressTimer();
      if (sequence) {
        postInput({
          frameId,
          sequenceId: sequence.id,
          type: "touchCancel",
          point: sequence.lastPoint,
          previousPoint: sequence.lastPoint,
          startedAt: sequence.startedAt,
          primaryButton: false,
          modifiers: event ? eventModifiers(event) : { alt: false, ctrl: false, meta: false, shift: false },
        });
      }
      activeSequenceRef.current = null;
      hideIndicator(indicatorIdleMs);
    },
    [clearLongPressTimer, frameId, hideIndicator, postInput],
  );

  const beginSequence = useCallback(
    (event: UIEvent | Event, point: PreviewInputPoint) => {
      const existing = activeSequenceRef.current;
      if (existing) return existing;
      const sequence: ActiveSequence = {
        id: createSequenceId(),
        startedAt: Date.now(),
        startPoint: point,
        lastPoint: point,
        moved: false,
        longPressSent: false,
      };
      activeSequenceRef.current = sequence;
      scheduleIndicator(point, { visible: true, active: true });
      postInput({
        frameId,
        sequenceId: sequence.id,
        type: "touchStart",
        point,
        startedAt: sequence.startedAt,
        primaryButton: true,
        modifiers: eventModifiers(event),
      });
      return sequence;
    },
    [frameId, postInput, scheduleIndicator],
  );

  const startLongPressTimer = useCallback(
    (event: UIEvent | Event, sequence: ActiveSequence) => {
      clearLongPressTimer();
      longPressTimerRef.current = window.setTimeout(() => {
        const current = activeSequenceRef.current;
        if (!current || current.id !== sequence.id || current.moved || current.longPressSent) return;
        current.longPressSent = true;
        postInput({
          frameId,
          sequenceId: current.id,
          type: "longPress",
          point: current.lastPoint,
          previousPoint: current.startPoint,
          startedAt: current.startedAt,
          primaryButton: true,
          modifiers: eventModifiers(event),
        });
      }, longPressDelayMs);
    },
    [clearLongPressTimer, frameId, postInput],
  );

  const finishSequence = useCallback(
    (event: UIEvent | Event, point: PreviewInputPoint) => {
      const sequence = activeSequenceRef.current;
      if (!sequence) return;
      const moved = sequence.moved || pointDistance(sequence.startPoint, point) > tapMovementThreshold;
      postInput({
        frameId,
        sequenceId: sequence.id,
        type: moved ? "touchEnd" : "tap",
        point,
        previousPoint: sequence.lastPoint,
        startedAt: sequence.startedAt,
        primaryButton: false,
        modifiers: eventModifiers(event),
      });
      activeSequenceRef.current = null;
      clearLongPressTimer();
      hideIndicator(indicatorIdleMs);
    },
    [clearLongPressTimer, frameId, hideIndicator, postInput],
  );

  const bind = useGesture(
    {
      onMove: ({ xy: [x, y] }) => {
        if (!enabled || activeSequenceRef.current) return;
        const point = resolvePoint(x, y);
        if (!point) return;
        scheduleIndicator(point, { visible: true, active: false });
      },
      onHover: ({ hovering, xy: [x, y] }) => {
        if (!enabled) return;
        if (!hovering) {
          if (!activeSequenceRef.current) hideIndicator(indicatorIdleMs);
          return;
        }
        const point = resolvePoint(x, y);
        if (!point) return;
        scheduleIndicator(point, { visible: true, active: Boolean(activeSequenceRef.current) });
      },
      onDrag: (state) => {
        if (!enabled) return;
        state.event.preventDefault();
        const point = resolvePoint(state.xy[0], state.xy[1]);
        if (!point) return;

        if (state.first) {
          const sequence = beginSequence(state.event, point);
          startLongPressTimer(state.event, sequence);
          if (pointDistance(sequence.startPoint, point) <= tapMovementThreshold) return;
        }

        const sequence = activeSequenceRef.current;
        if (!sequence) return;
        const movement = pointDistance(sequence.startPoint, point);
        const moved = movement > tapMovementThreshold || Math.abs(state.movement[1]) > dragThreshold || Math.abs(state.movement[0]) > dragThreshold;
        if (moved) {
          sequence.moved = true;
          clearLongPressTimer();
        }
        scheduleIndicator(point, { visible: true, active: state.active });

        if (state.last) {
          finishSequence(state.event, point);
          return;
        }

        postInput({
          frameId,
          sequenceId: sequence.id,
          type: "touchMove",
          point,
          previousPoint: sequence.lastPoint,
          startedAt: sequence.startedAt,
          primaryButton: true,
          modifiers: eventModifiers(state.event),
        });
        sequence.lastPoint = point;
      },
    },
    {
      enabled,
      drag: {
        filterTaps: false,
        threshold: dragThreshold,
        tapsThreshold: tapMovementThreshold,
        preventDefault: true,
        triggerAllEvents: true,
        pointer: { buttons: 1, keys: false, capture: true },
        eventOptions: { passive: false },
      },
      move: { mouseOnly: true },
      hover: { mouseOnly: true },
      eventOptions: { passive: false },
    },
  );

  useEffect(() => {
    if (enabled) return;
    cancelSequence();
  }, [cancelSequence, enabled]);

  useEffect(() => {
    return () => {
      cancelSequence();
      clearHideTimer();
      clearLongPressTimer();
      if (rafRef.current !== null) {
        window.cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
    };
  }, [cancelSequence, clearHideTimer, clearLongPressTimer]);

  const surfaceClassName = useMemo(
    () => ["student-preview-gesture-surface", enabled ? "is-enabled" : ""].filter(Boolean).join(" "),
    [enabled],
  );

  return (
    <div
      {...bind()}
      ref={surfaceRef}
      className={surfaceClassName}
      aria-hidden="true"
      onPointerDownCapture={(event) => {
        if (!enabled || event.button !== 0) return;
        event.preventDefault();
        const point = resolvePoint(event.clientX, event.clientY);
        if (!point) return;
        const sequence = beginSequence(event.nativeEvent, point);
        startLongPressTimer(event.nativeEvent, sequence);
      }}
      onPointerUpCapture={(event) => {
        if (!enabled) return;
        const point = resolvePoint(event.clientX, event.clientY);
        if (!point) return;
        event.preventDefault();
        finishSequence(event.nativeEvent, point);
      }}
      onPointerCancel={(event) => cancelSequence(event.nativeEvent)}
      onLostPointerCapture={(event) => cancelSequence(event.nativeEvent)}
    >
      <span ref={indicatorRef} className="student-preview-touch-indicator" />
    </div>
  );
}
