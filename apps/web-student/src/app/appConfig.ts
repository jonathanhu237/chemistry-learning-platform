import type { StudentAppConfigResponse, StudentAppFeatureFlags } from "../api";

export const defaultStudentAppConfig: StudentAppConfigResponse = {
  features: {
    ai_assistant_enabled: true,
    feedback_enabled: true,
    student_ai_assistant_enabled: true,
    rag_access_enabled: true,
  },
  preview_mode: false,
  preview_policy: null,
};

export function assistantEnabled(features: StudentAppFeatureFlags): boolean {
  return features.ai_assistant_enabled && features.student_ai_assistant_enabled;
}

export function feedbackEnabled(features: StudentAppFeatureFlags): boolean {
  return features.feedback_enabled;
}

export function previewRouteBlocked(config: StudentAppConfigResponse, pathname: string): boolean {
  return Boolean(config.preview_mode && config.preview_policy?.blocked_routes?.includes(pathname));
}
