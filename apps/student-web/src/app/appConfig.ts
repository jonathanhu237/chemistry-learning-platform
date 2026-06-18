import type { StudentAppConfigResponse, StudentAppFeatureFlags } from "../api";

export const defaultStudentAppConfig: StudentAppConfigResponse = {
  features: {
    ai_assistant_enabled: true,
    feedback_enabled: true,
    student_ai_assistant_enabled: true,
    rag_access_enabled: true,
  },
};

export function assistantEnabled(features: StudentAppFeatureFlags): boolean {
  return features.ai_assistant_enabled && features.student_ai_assistant_enabled;
}

export function feedbackEnabled(features: StudentAppFeatureFlags): boolean {
  return features.feedback_enabled;
}
