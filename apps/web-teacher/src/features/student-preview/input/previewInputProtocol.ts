export const studentPreviewInputNamespace = "chemistry.studentPreview.input";
export const studentPreviewInputVersion = 1;

export type PreviewInputEventType = "hover" | "touchStart" | "touchMove" | "touchEnd" | "touchCancel" | "tap" | "longPress";

export type PreviewInputPoint = {
  x: number;
  y: number;
};

export type PreviewInputMessage = {
  namespace: typeof studentPreviewInputNamespace;
  version: typeof studentPreviewInputVersion;
  frameId: string;
  sequenceId: string;
  type: PreviewInputEventType;
  point: PreviewInputPoint;
  previousPoint?: PreviewInputPoint;
  startedAt?: number;
  timestamp: number;
  primaryButton: boolean;
  modifiers: {
    alt: boolean;
    ctrl: boolean;
    meta: boolean;
    shift: boolean;
  };
};

export function createPreviewFrameId(): string {
  const random = typeof crypto !== "undefined" && "randomUUID" in crypto ? crypto.randomUUID() : Math.random().toString(36).slice(2);
  return `student-preview-${Date.now().toString(36)}-${random}`;
}

export function appendPreviewFrameId(previewUrl: string, frameId: string): string {
  const url = new URL(previewUrl);
  url.searchParams.set("previewFrameId", frameId);
  url.searchParams.set("previewTeacherOrigin", window.location.origin);
  return url.toString();
}

export function createPreviewInputMessage(
  input: Omit<PreviewInputMessage, "namespace" | "version" | "timestamp"> & { timestamp?: number },
): PreviewInputMessage {
  return {
    namespace: studentPreviewInputNamespace,
    version: studentPreviewInputVersion,
    timestamp: input.timestamp ?? Date.now(),
    ...input,
  };
}
