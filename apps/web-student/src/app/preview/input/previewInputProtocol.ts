export const studentPreviewInputNamespace = "chemistry.studentPreview.input";
export const studentPreviewInputVersion = 1;

export const previewInputFrameIdKey = "chem_student_preview_frame_id";
export const previewInputTeacherOriginKey = "chem_student_preview_teacher_origin";

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

export function storePreviewInputHandshake(frameId: string, teacherOrigin: string): void {
  try {
    if (frameId) sessionStorage.setItem(previewInputFrameIdKey, frameId);
    if (teacherOrigin) sessionStorage.setItem(previewInputTeacherOriginKey, teacherOrigin);
  } catch {
    // Session storage may be unavailable in restricted WebViews.
  }
}

export function readPreviewInputHandshake(): { frameId: string; teacherOrigin: string } {
  try {
    return {
      frameId: sessionStorage.getItem(previewInputFrameIdKey) || "",
      teacherOrigin: sessionStorage.getItem(previewInputTeacherOriginKey) || "",
    };
  } catch {
    return { frameId: "", teacherOrigin: "" };
  }
}

function isPlainObject(value: unknown): value is Record<string, unknown> {
  return Boolean(value && typeof value === "object" && !Array.isArray(value));
}

function isPoint(value: unknown): value is PreviewInputPoint {
  return isPlainObject(value) && Number.isFinite(value.x) && Number.isFinite(value.y);
}

function isEventType(value: unknown): value is PreviewInputEventType {
  return (
    value === "hover" ||
    value === "touchStart" ||
    value === "touchMove" ||
    value === "touchEnd" ||
    value === "touchCancel" ||
    value === "tap" ||
    value === "longPress"
  );
}

export function parsePreviewInputMessage(value: unknown): PreviewInputMessage | null {
  if (!isPlainObject(value)) return null;
  if (value.namespace !== studentPreviewInputNamespace || value.version !== studentPreviewInputVersion) return null;
  if (typeof value.frameId !== "string" || !value.frameId) return null;
  if (typeof value.sequenceId !== "string" || !value.sequenceId) return null;
  if (!isEventType(value.type)) return null;
  if (!isPoint(value.point)) return null;
  if (value.previousPoint !== undefined && !isPoint(value.previousPoint)) return null;
  if (!Number.isFinite(value.timestamp)) return null;
  if (typeof value.primaryButton !== "boolean") return null;
  return value as PreviewInputMessage;
}
