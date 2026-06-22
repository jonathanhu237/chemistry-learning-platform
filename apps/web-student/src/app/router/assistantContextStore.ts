import { defaultAssistantContext, type AssistantContext } from "../../features/assistant/assistantContext";

const storagePrefix = "student-ai-context:";

function storage(): Storage | null {
  try {
    return typeof window === "undefined" ? null : window.sessionStorage;
  } catch {
    return null;
  }
}

export function saveAssistantContext(context: AssistantContext): string {
  const key = `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
  storage()?.setItem(`${storagePrefix}${key}`, JSON.stringify(context));
  return key;
}

export function loadAssistantContext(contextKey?: string | null): AssistantContext {
  if (!contextKey) return defaultAssistantContext();
  const raw = storage()?.getItem(`${storagePrefix}${contextKey}`);
  if (!raw) return defaultAssistantContext();
  try {
    const parsed = JSON.parse(raw) as AssistantContext;
    return parsed.context_type && parsed.context_title ? parsed : defaultAssistantContext();
  } catch {
    return defaultAssistantContext();
  }
}
