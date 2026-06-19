import type { AssistantContext } from "../../features/assistant/assistantContext";
import { saveAssistantContext } from "./assistantContextStore";
import { rootPathById } from "./routeVisibility";
import type { StudentDetailSource } from "./routeTypes";

type NavigateLike = (options: {
  to: string;
  params?: Record<string, string>;
  search?: Record<string, unknown>;
  replace?: boolean;
}) => unknown;

function compactSearch(search: Record<string, unknown>): Record<string, string> {
  return Object.fromEntries(
    Object.entries(search)
      .map(([key, value]) => [key, typeof value === "string" ? value.trim() : ""] as const)
      .filter(([, value]) => value.length > 0),
  );
}

export function navigateToRoot(navigate: NavigateLike, root: keyof typeof rootPathById): void {
  void navigate({ to: rootPathById[root] });
  window.requestAnimationFrame(() => window.scrollTo({ top: 0, behavior: "auto" }));
}

export function navigateToChapter(
  navigate: NavigateLike,
  profileId: string,
  options: {
    from?: StudentDetailSource;
    propertyKey?: string | null;
    elementSymbol?: string | null;
  } = {},
): void {
  void navigate({
    to: "/chapter/$profileId",
    params: { profileId },
    search: compactSearch({
      from: options.from || "learn",
      propertyKey: options.propertyKey || "",
      elementSymbol: options.elementSymbol || "",
    }),
  });
}

export function navigateToElement(
  navigate: NavigateLike,
  profileId: string,
  symbol: string,
  options: {
    from?: StudentDetailSource;
  } = {},
): void {
  void navigate({
    to: "/chapter/$profileId/element/$symbol",
    params: { profileId, symbol },
    search: compactSearch({
      from: options.from || "chapter",
    }),
  });
}

export function navigateToPoint(
  navigate: NavigateLike,
  experimentId: string,
  options: {
    from?: StudentDetailSource;
    profileId?: string | null;
    propertyKey?: string | null;
    propertyTitle?: string | null;
    elementSymbol?: string | null;
    pointKey?: string | null;
    pointTitle?: string | null;
  } = {},
): void {
  void navigate({
    to: "/point/$experimentId",
    params: { experimentId },
    search: compactSearch({
      from: options.from || "chapter",
      profileId: options.profileId || "",
      propertyKey: options.propertyKey || "",
      propertyTitle: options.propertyTitle || "",
      elementSymbol: options.elementSymbol || "",
      pointKey: options.pointKey || "",
      pointTitle: options.pointTitle || "",
    }),
  });
}

export function navigateToAiChat(navigate: NavigateLike, context: AssistantContext, from: StudentDetailSource): void {
  const contextKey = saveAssistantContext(context);
  void navigate({
    to: "/ai/chat",
    search: compactSearch({ from, contextKey }),
  });
}

export function navigateToAssessmentSession(navigate: NavigateLike, sessionId: string, from: StudentDetailSource): void {
  void navigate({
    to: "/assessment/session/$sessionId",
    params: { sessionId },
    search: compactSearch({ from }),
  });
}

export function navigateToAssessmentReport(navigate: NavigateLike, sessionId: string, from: StudentDetailSource): void {
  void navigate({
    to: "/assessment/report/$sessionId",
    params: { sessionId },
    search: compactSearch({ from }),
  });
}

export function navigateToFeedback(navigate: NavigateLike, from: StudentDetailSource = "profile"): void {
  void navigate({
    to: "/feedback/new",
    search: compactSearch({ from }),
  });
}
