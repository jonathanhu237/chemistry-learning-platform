import type { AssistantContext } from "../../features/assistant/assistantContext";
import type { AreaId } from "../../features/periodic-table/periodicHelpers";
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

export function navigateToLearningArea(
  navigate: NavigateLike,
  areaId: AreaId,
  options: {
    from?: StudentDetailSource;
  } = {},
): void {
  void navigate({
    to: "/learn/area/$areaId",
    params: { areaId },
    search: compactSearch({
      from: options.from || "learn",
    }),
  });
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
  nodeId: string,
  options: {
    from?: StudentDetailSource;
    profileId?: string | null;
    chapterId?: string | null;
    sourceNodeId?: string | null;
    catalogPath?: string | null;
    propertyKey?: string | null;
    propertyTitle?: string | null;
    elementSymbol?: string | null;
    pointTitle?: string | null;
  } = {},
): void {
  void navigate({
    to: "/point/$nodeId",
    params: { nodeId },
    search: compactSearch({
      from: options.from || "chapter",
      profileId: options.profileId || "",
      chapterId: options.chapterId || "",
      sourceNodeId: options.sourceNodeId || "",
      catalogPath: options.catalogPath || "",
      propertyKey: options.propertyKey || "",
      propertyTitle: options.propertyTitle || "",
      elementSymbol: options.elementSymbol || "",
      pointTitle: options.pointTitle || "",
    }),
  });
}

export function navigateToCatalogNode(
  navigate: NavigateLike,
  nodeId: string,
  options: {
    from?: StudentDetailSource;
    profileId?: string | null;
    chapterId?: string | null;
    catalogPath?: string | null;
    elementSymbol?: string | null;
  } = {},
): void {
  void navigate({
    to: "/catalog/$nodeId",
    params: { nodeId },
    search: compactSearch({
      from: options.from || "chapter",
      profileId: options.profileId || "",
      chapterId: options.chapterId || "",
      catalogPath: options.catalogPath || "",
      elementSymbol: options.elementSymbol || "",
    }),
  });
}

export function navigateToSearch(
  navigate: NavigateLike,
  options: {
    from?: StudentDetailSource;
    profileId?: string | null;
    chapterId?: string | null;
    sourceNodeId?: string | null;
    catalogPath?: string | null;
    elementSymbol?: string | null;
    q?: string | null;
    replace?: boolean;
  } = {},
): void {
  void navigate({
    to: "/search",
    replace: options.replace,
    search: compactSearch({
      from: options.from || "chapter",
      profileId: options.profileId || "",
      chapterId: options.chapterId || "",
      sourceNodeId: options.sourceNodeId || "",
      catalogPath: options.catalogPath || "",
      elementSymbol: options.elementSymbol || "",
      q: options.q || "",
    }),
  });
}

export function navigateToVideoLibrary(
  navigate: NavigateLike,
  options: {
    from?: StudentDetailSource;
    q?: string | null;
  } = {},
): void {
  void navigate({
    to: "/video-library",
    search: compactSearch({
      from: options.from || "home",
      q: options.q || "",
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

export function navigateToAssessmentCustom(navigate: NavigateLike, from: StudentDetailSource = "assessment"): void {
  void navigate({
    to: "/assessment/custom",
    search: compactSearch({ from }),
  });
}

export function navigateToAssessmentReport(navigate: NavigateLike, reportId: string, from: StudentDetailSource): void {
  void navigate({
    to: "/assessment/reports/$reportId",
    params: { reportId },
    search: compactSearch({ from }),
  });
}

export function navigateToLegacyAssessmentReport(navigate: NavigateLike, sessionId: string, from: StudentDetailSource): void {
  void navigate({
    to: "/assessment/report/$sessionId",
    params: { sessionId },
    search: compactSearch({ from }),
  });
}

export function navigateToProfileReports(navigate: NavigateLike, from: StudentDetailSource = "profile"): void {
  void navigate({
    to: "/profile/reports",
    search: compactSearch({ from }),
  });
}

export function navigateToFeedback(navigate: NavigateLike, from: StudentDetailSource = "profile"): void {
  void navigate({
    to: "/feedback/new",
    search: compactSearch({ from }),
  });
}
