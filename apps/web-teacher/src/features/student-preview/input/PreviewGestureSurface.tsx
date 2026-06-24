import { useCallback, useEffect, useMemo, useRef } from "react";
import type { PointerEvent as ReactPointerEvent, RefObject, WheelEvent as ReactWheelEvent } from "react";

import { createPreviewInputMessage, type PreviewInputMessage, type PreviewInputPoint } from "./previewInputProtocol";

const indicatorIdleMs = 900;

type PreviewGestureSurfaceProps = {
  enabled: boolean;
  iframeRef: RefObject<HTMLIFrameElement | null>;
  frameId: string;
  targetOrigin: string;
};

type ActiveSequence = {
  id: string;
  pointerId: number;
  startedAt: number;
  startPoint: PreviewInputPoint;
  lastPoint: PreviewInputPoint;
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

function pointsMatch(a: PreviewInputPoint, b: PreviewInputPoint): boolean {
  return a.x === b.x && a.y === b.y;
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

function wheelDeltaScale(event: ReactWheelEvent<HTMLElement>, surface: HTMLElement): number {
  if (event.deltaMode === 1) return 16;
  if (event.deltaMode === 2) return surface.clientHeight || surface.offsetHeight || 600;
  return 1;
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
  const latestIndicatorRef = useRef({ x: 0, y: 0, visible: false, active: false });

  const clearHideTimer = useCallback(() => {
    if (hideTimerRef.current !== null) {
      window.clearTimeout(hideTimerRef.current);
      hideTimerRef.current = null;
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

  const releaseCapture = useCallback((pointerId: number) => {
    const surface = surfaceRef.current;
    if (!surface?.hasPointerCapture?.(pointerId)) return;
    try {
      surface.releasePointerCapture(pointerId);
    } catch {
      // The pointer may already be released by the browser.
    }
  }, []);

  const cancelSequence = useCallback(
    (event?: UIEvent | Event) => {
      const sequence = activeSequenceRef.current;
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
        releaseCapture(sequence.pointerId);
      }
      activeSequenceRef.current = null;
      hideIndicator(indicatorIdleMs);
    },
    [frameId, hideIndicator, postInput, releaseCapture],
  );

  const beginSequence = useCallback(
    (event: ReactPointerEvent<HTMLDivElement>, point: PreviewInputPoint) => {
      const existing = activeSequenceRef.current;
      if (existing) return existing;
      const sequence: ActiveSequence = {
        id: createSequenceId(),
        pointerId: event.pointerId,
        startedAt: Date.now(),
        startPoint: point,
        lastPoint: point,
      };
      activeSequenceRef.current = sequence;
      try {
        event.currentTarget.setPointerCapture(event.pointerId);
      } catch {
        // Pointer capture can fail in some synthetic or stale event paths.
      }
      scheduleIndicator(point, { visible: true, active: true });
      postInput({
        frameId,
        sequenceId: sequence.id,
        type: "touchStart",
        point,
        startedAt: sequence.startedAt,
        primaryButton: true,
        modifiers: eventModifiers(event.nativeEvent),
      });
      return sequence;
    },
    [frameId, postInput, scheduleIndicator],
  );

  const moveSequence = useCallback(
    (event: ReactPointerEvent<HTMLDivElement>, point: PreviewInputPoint) => {
      const sequence = activeSequenceRef.current;
      if (!sequence || sequence.pointerId !== event.pointerId) return;
      scheduleIndicator(point, { visible: true, active: true });
      if (pointsMatch(sequence.lastPoint, point)) return;
      postInput({
        frameId,
        sequenceId: sequence.id,
        type: "touchMove",
        point,
        previousPoint: sequence.lastPoint,
        startedAt: sequence.startedAt,
        primaryButton: true,
        modifiers: eventModifiers(event.nativeEvent),
      });
      sequence.lastPoint = point;
    },
    [frameId, postInput, scheduleIndicator],
  );

  const finishSequence = useCallback(
    (event: ReactPointerEvent<HTMLDivElement>, point: PreviewInputPoint) => {
      const sequence = activeSequenceRef.current;
      if (!sequence || sequence.pointerId !== event.pointerId) return;
      postInput({
        frameId,
        sequenceId: sequence.id,
        type: "touchEnd",
        point,
        previousPoint: sequence.lastPoint,
        startedAt: sequence.startedAt,
        primaryButton: false,
        modifiers: eventModifiers(event.nativeEvent),
      });
      activeSequenceRef.current = null;
      releaseCapture(sequence.pointerId);
      hideIndicator(indicatorIdleMs);
    },
    [frameId, hideIndicator, postInput, releaseCapture],
  );

  useEffect(() => {
    if (enabled) return;
    cancelSequence();
  }, [cancelSequence, enabled]);

  useEffect(() => {
    return () => {
      cancelSequence();
      clearHideTimer();
      if (rafRef.current !== null) {
        window.cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
    };
  }, [cancelSequence, clearHideTimer]);

  const surfaceClassName = useMemo(
    () => ["student-preview-gesture-surface", enabled ? "is-enabled" : ""].filter(Boolean).join(" "),
    [enabled],
  );

  return (
    <div
      ref={surfaceRef}
      className={surfaceClassName}
      aria-hidden="true"
      onPointerEnter={(event) => {
        if (!enabled || activeSequenceRef.current) return;
        const point = resolvePoint(event.clientX, event.clientY);
        if (point) scheduleIndicator(point, { visible: true, active: false });
      }}
      onPointerMove={(event) => {
        if (!enabled) return;
        const point = resolvePoint(event.clientX, event.clientY);
        if (!point) return;
        const sequence = activeSequenceRef.current;
        if (sequence) {
          if (sequence.pointerId !== event.pointerId) return;
          event.preventDefault();
          moveSequence(event, point);
          return;
        }
        scheduleIndicator(point, { visible: true, active: false });
      }}
      onPointerLeave={() => {
        if (!activeSequenceRef.current) hideIndicator(indicatorIdleMs);
      }}
      onPointerDown={(event) => {
        if (!enabled || event.button !== 0 || !event.isPrimary) return;
        event.preventDefault();
        const point = resolvePoint(event.clientX, event.clientY);
        if (!point) return;
        beginSequence(event, point);
      }}
      onPointerUp={(event) => {
        if (!enabled) return;
        const point = resolvePoint(event.clientX, event.clientY);
        if (!point) return;
        event.preventDefault();
        finishSequence(event, point);
      }}
      onPointerCancel={(event) => {
        if (activeSequenceRef.current?.pointerId !== event.pointerId) return;
        cancelSequence(event.nativeEvent);
      }}
      onLostPointerCapture={(event) => {
        if (activeSequenceRef.current?.pointerId !== event.pointerId) return;
        cancelSequence(event.nativeEvent);
      }}
      onDragStart={(event) => event.preventDefault()}
      onWheel={(event) => {
        if (!enabled || activeSequenceRef.current) return;
        const point = resolvePoint(event.clientX, event.clientY);
        const surface = surfaceRef.current;
        if (!point || !surface) return;
        event.preventDefault();
        const scale = wheelDeltaScale(event, surface);
        scheduleIndicator(point, { visible: true, active: false });
        hideIndicator(indicatorIdleMs);
        postInput({
          frameId,
          sequenceId: createSequenceId(),
          type: "wheel",
          point,
          deltaX: event.deltaX * scale,
          deltaY: event.deltaY * scale,
          primaryButton: false,
          modifiers: eventModifiers(event.nativeEvent),
        });
      }}
      onContextMenu={(event) => {
        if (activeSequenceRef.current) event.preventDefault();
      }}
    >
      <span ref={indicatorRef} className="student-preview-touch-indicator" />
    </div>
  );
}
