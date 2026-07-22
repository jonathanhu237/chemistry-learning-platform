import type { StudentSmartAssessmentReport, StudentSmartAssessmentResponse } from "../../api";

export type ViewState = "checking" | "login" | "password" | "baseline" | "home";

export type ChapterLearningView = "facts" | "experiments";

export type StudentRootRouteId = "home" | "learn" | "ai" | "assessment" | "profile";

export type StudentDetailSource =
  | StudentRootRouteId
  | "chapter"
  | "element"
  | "point"
  | "assessment-custom"
  | "assessment-session"
  | "assessment-report"
  | "profile-reports"
  | "feedback";

export type StudentRouteSearch = {
  from?: StudentDetailSource;
  contextKey?: string;
  profileId?: string;
  chapterId?: string;
  nodeId?: string;
  sourceNodeId?: string;
  propertyKey?: string;
  propertyTitle?: string;
  elementSymbol?: string;
  chapterView?: ChapterLearningView;
  pointTitle?: string;
  catalogPath?: string;
};

export type StoredPosttestSession = StudentSmartAssessmentResponse;

export type StoredPosttestReport = StudentSmartAssessmentReport;

function optionalString(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value : undefined;
}

export function parseStudentRouteSearch(search: Record<string, unknown>): StudentRouteSearch {
  const chapterView = optionalString(search.chapterView);
  return {
    from: optionalString(search.from) as StudentDetailSource | undefined,
    contextKey: optionalString(search.contextKey),
    profileId: optionalString(search.profileId),
    chapterId: optionalString(search.chapterId),
    nodeId: optionalString(search.nodeId),
    sourceNodeId: optionalString(search.sourceNodeId),
    propertyKey: optionalString(search.propertyKey),
    propertyTitle: optionalString(search.propertyTitle),
    elementSymbol: optionalString(search.elementSymbol),
    chapterView: chapterView === "facts" || chapterView === "experiments" ? chapterView : undefined,
    pointTitle: optionalString(search.pointTitle),
    catalogPath: optionalString(search.catalogPath),
  };
}
