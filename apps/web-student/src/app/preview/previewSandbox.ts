import type { StudentRuntimeContextValue } from "../shell/studentAppContext";

const teacherStudentPreviewPurpose = "teacher_student_device_preview";

const teacherPreviewProfile = {
  studentId: "00000000",
  displayName: "施测平",
  className: "数智一班",
};

const feedbackSubmitBlockedDialog = {
  ariaLabel: "预览模式提示",
  title: "预览模式不能提交反馈",
  body: "这里可以体验真实填写流程，但不会向老师后台提交数据。",
  actionLabel: "知道了",
};

export type StudentPreviewRuntime = Pick<
  StudentRuntimeContextValue,
  "user" | "previewMode" | "previewPolicy" | "canUseFeedback"
>;

export type StudentProfilePresentation = {
  studentId: string;
  displayName: string;
  className?: string | null;
};

export type PreviewBlockedDialog = typeof feedbackSubmitBlockedDialog;

export type FeedbackCapability = {
  canOpenEntry: boolean;
  canOpenForm: boolean;
  interceptSubmit: boolean;
  blockedSubmitDialog: PreviewBlockedDialog;
};

export type FeedbackSubmitCommandResult<T> =
  | { kind: "blocked"; dialog: PreviewBlockedDialog }
  | { kind: "submitted"; result: T };

export function isTeacherStudentPreview(runtime: StudentPreviewRuntime): boolean {
  return Boolean(
    runtime.previewMode ||
      runtime.user.preview_mode ||
      runtime.user.preview_purpose === teacherStudentPreviewPurpose,
  );
}

export function getStudentProfilePresentation(runtime: StudentPreviewRuntime): StudentProfilePresentation {
  if (isTeacherStudentPreview(runtime)) {
    return teacherPreviewProfile;
  }

  return {
    studentId: runtime.user.student_id || runtime.user.username,
    displayName: runtime.user.display_name,
    className: runtime.user.class_name,
  };
}

export function getFeedbackCapability(runtime: StudentPreviewRuntime): FeedbackCapability {
  const teacherPreview = isTeacherStudentPreview(runtime);
  const canOpen = runtime.canUseFeedback || teacherPreview;

  return {
    canOpenEntry: canOpen,
    canOpenForm: canOpen,
    interceptSubmit: teacherPreview,
    blockedSubmitDialog: feedbackSubmitBlockedDialog,
  };
}

export async function executeFeedbackSubmitCommand<T>(
  runtime: StudentPreviewRuntime,
  submitRealFeedback: () => Promise<T>,
): Promise<FeedbackSubmitCommandResult<T>> {
  const capability = getFeedbackCapability(runtime);

  if (capability.interceptSubmit) {
    return { kind: "blocked", dialog: capability.blockedSubmitDialog };
  }

  return { kind: "submitted", result: await submitRealFeedback() };
}
