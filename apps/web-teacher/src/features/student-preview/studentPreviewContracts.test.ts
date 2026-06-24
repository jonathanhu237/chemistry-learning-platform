import { describe, expect, it } from "vitest";

import apiSource from "./studentPreviewApi.ts?raw";
import pageSource from "./StudentDevicePreviewPage.tsx?raw";
import gestureSurfaceSource from "./input/PreviewGestureSurface.tsx?raw";
import inputProtocolSource from "./input/previewInputProtocol.ts?raw";
import deviceFrameSource from "../device-preview/DevicePreviewFrame.tsx?raw";

describe("student device preview contracts", () => {
  it("uses a backend session ticket and the real student app iframe", () => {
    expect(apiSource).toContain('"/api/admin/student-preview/session"');
    expect(pageSource).toContain("<iframe");
    expect(pageSource).toContain("preview_url");
    expect(pageSource).toContain("allowedPreviewUrl");
    expect(deviceFrameSource).toContain("VITE_STUDENT_APP_BASE_URL");
    expect(deviceFrameSource).toContain("http://222.200.189.249:15173");
    expect(pageSource).not.toContain("inferStudentAppBase");
    expect(pageSource).not.toContain("Expected ${expectedOrigin}");
    expect(pageSource).toContain('url.protocol !== "http:" && url.protocol !== "https:"');
    expect(pageSource).toContain("PreviewGestureSurface");
    expect(inputProtocolSource).toContain("previewTeacherOrigin");
  });

  it("shares the device frame primitive and does not import web-student source", () => {
    expect(pageSource).toContain("DeviceFrame");
    expect(deviceFrameSource).toContain("react-device-mockup");
    expect(pageSource).not.toContain("apps/web-student");
    expect(pageSource).not.toContain("../web-student");
    expect(pageSource).not.toContain("routes/learn");
    expect(pageSource).not.toContain("StudentRouterProvider");
  });

  it("uses teacher-owned pointer lifecycle transport without treating it as student code", () => {
    expect(gestureSurfaceSource).not.toContain("@use-gesture/react");
    expect(gestureSurfaceSource).not.toContain("useGesture");
    expect(gestureSurfaceSource).toContain("postMessage");
    expect(gestureSurfaceSource).toContain("requestAnimationFrame");
    expect(gestureSurfaceSource).toContain("translate3d");
    expect(gestureSurfaceSource).toContain("onPointerDown");
    expect(gestureSurfaceSource).toContain("onPointerMove");
    expect(gestureSurfaceSource).toContain("onPointerUp");
    expect(gestureSurfaceSource).toContain("onPointerCancel");
    expect(gestureSurfaceSource).toContain("onLostPointerCapture");
    expect(gestureSurfaceSource).toContain('type: "touchStart"');
    expect(gestureSurfaceSource).toContain('type: "touchMove"');
    expect(gestureSurfaceSource).toContain('type: "touchEnd"');
    expect(gestureSurfaceSource).toContain('type: "touchCancel"');
    expect(gestureSurfaceSource).not.toContain('type: "tap"');
    expect(gestureSurfaceSource).not.toContain('type: "longPress"');
    expect(gestureSurfaceSource).not.toContain("apps/web-student");
    expect(gestureSurfaceSource).not.toContain("document.querySelector");
  });

  it("keeps the preview stage scrollable without exposing desktop scrollbars over the device", async () => {
    // @ts-expect-error The frontend tsconfig intentionally omits Node types, but Vitest runs this contract in Node.
    const { readFileSync } = await import("node:fs");
    const cwd = (globalThis as unknown as { process: { cwd: () => string } }).process.cwd();
    const previewCssSource = readFileSync(`${cwd}/src/features/student-preview/studentPreview.css`, "utf8");

    expect(previewCssSource).toContain("filter: drop-shadow");
    expect(previewCssSource).not.toContain("box-shadow: 0 22px 56px");
    expect(previewCssSource).toContain("scrollbar-width: none");
    expect(previewCssSource).toContain(".student-preview-stage::-webkit-scrollbar");
    expect(previewCssSource).toContain("width: 0");
    expect(previewCssSource).toContain("height: 0");
    expect(previewCssSource).toContain(".student-preview-gesture-surface");
    expect(previewCssSource).toContain("touch-action: none");
    expect(previewCssSource).toContain("cursor: none");
    expect(previewCssSource).toContain(".student-preview-touch-indicator");
    expect(previewCssSource).not.toContain("transition:\n    opacity 80ms ease,\n    transform");
  });

});
