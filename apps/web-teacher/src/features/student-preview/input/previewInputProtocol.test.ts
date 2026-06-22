import { describe, expect, it } from "vitest";

import { mapClientPointToSurfacePoint } from "./PreviewGestureSurface";
import {
  appendPreviewFrameId,
  createPreviewInputMessage,
  studentPreviewInputNamespace,
  studentPreviewInputVersion,
} from "./previewInputProtocol";

describe("teacher preview input protocol", () => {
  it("adds frame and teacher-origin context to the student preview URL", () => {
    const url = appendPreviewFrameId("http://127.0.0.1:5173/preview/session?ticket=abc", "frame-1");
    const parsed = new URL(url);

    expect(parsed.searchParams.get("ticket")).toBe("abc");
    expect(parsed.searchParams.get("previewFrameId")).toBe("frame-1");
    expect(parsed.searchParams.get("previewTeacherOrigin")).toBe(window.location.origin);
  });

  it("creates versioned messages with the stable namespace", () => {
    const message = createPreviewInputMessage({
      frameId: "frame-1",
      sequenceId: "sequence-1",
      type: "tap",
      point: { x: 10, y: 20 },
      primaryButton: false,
      timestamp: 12345,
      modifiers: { alt: false, ctrl: false, meta: false, shift: false },
    });

    expect(message).toMatchObject({
      namespace: studentPreviewInputNamespace,
      version: studentPreviewInputVersion,
      frameId: "frame-1",
      sequenceId: "sequence-1",
      type: "tap",
      point: { x: 10, y: 20 },
      primaryButton: false,
    });
    expect(message.timestamp).toBe(12345);
  });

  it("maps teacher client coordinates into the phone screen viewport", () => {
    const surface = document.createElement("div");
    surface.getBoundingClientRect = () =>
      ({
        left: 100,
        top: 200,
        width: 300,
        height: 600,
        right: 400,
        bottom: 800,
        x: 100,
        y: 200,
        toJSON: () => ({}),
      }) as DOMRect;

    expect(mapClientPointToSurfacePoint(surface, 160, 260)).toEqual({ x: 60, y: 60 });
    expect(mapClientPointToSurfacePoint(surface, 20, 900)).toEqual({ x: 0, y: 600 });
  });

  it("maps transformed screen coordinates back to unscaled iframe CSS pixels", () => {
    const surface = document.createElement("div");
    Object.defineProperty(surface, "offsetWidth", { value: 300 });
    Object.defineProperty(surface, "offsetHeight", { value: 600 });
    surface.getBoundingClientRect = () =>
      ({
        left: 100,
        top: 200,
        width: 258,
        height: 516,
        right: 358,
        bottom: 716,
        x: 100,
        y: 200,
        toJSON: () => ({}),
      }) as DOMRect;

    expect(mapClientPointToSurfacePoint(surface, 186, 286)).toEqual({ x: 100, y: 100 });
    expect(mapClientPointToSurfacePoint(surface, 358, 716)).toEqual({ x: 300, y: 600 });
  });

  it("maps rotated screen coordinates through the browser box quad when available", () => {
    const surface = document.createElement("div");
    Object.defineProperty(surface, "offsetWidth", { value: 300 });
    Object.defineProperty(surface, "offsetHeight", { value: 600 });
    Object.assign(surface, {
      getBoxQuads: () => [
        {
          p1: { x: 500, y: 100 },
          p2: { x: 500, y: 358 },
          p4: { x: -16, y: 100 },
        },
      ],
    });

    expect(mapClientPointToSurfacePoint(surface, 242, 229)).toEqual({ x: 150, y: 300 });
  });

  it("maps clockwise landscape coordinates when box quads are unavailable", () => {
    const surface = document.createElement("div");
    Object.defineProperty(surface, "offsetWidth", { value: 300 });
    Object.defineProperty(surface, "offsetHeight", { value: 600 });
    surface.getBoundingClientRect = () =>
      ({
        left: -16,
        top: 100,
        width: 516,
        height: 258,
        right: 500,
        bottom: 358,
        x: -16,
        y: 100,
        toJSON: () => ({}),
      }) as DOMRect;

    expect(mapClientPointToSurfacePoint(surface, 242, 229)).toEqual({ x: 150, y: 300 });
  });
});
