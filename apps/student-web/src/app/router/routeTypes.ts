import type { StudentSmartAssessmentReport, StudentSmartAssessmentResponse } from "../../api";

export type ViewState = "checking" | "login" | "password" | "pretest-loading" | "pretest-error" | "pretest" | "home";

export type ChapterLearningView = "facts" | "experiments";

export type StudentRootRouteId = "home" | "learn" | "ai" | "assessment" | "profile";

export type StudentDetailSource =
  | StudentRootRouteId
  | "chapter"
  | "element"
  | "point"
  | "video-library"
  | "assessment-session"
  | "assessment-report"
  | "feedback";

export type StudentRouteSearch = {
  from?: StudentDetailSource;
  contextKey?: string;
  profileId?: string;
  propertyKey?: string;
  propertyTitle?: string;
  elementSymbol?: string;
  chapterView?: ChapterLearningView;
  pointKey?: string;
  pointTitle?: string;
  q?: string;
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
    propertyKey: optionalString(search.propertyKey),
    propertyTitle: optionalString(search.propertyTitle),
    elementSymbol: optionalString(search.elementSymbol),
    chapterView: chapterView === "facts" || chapterView === "experiments" ? chapterView : undefined,
    pointKey: optionalString(search.pointKey),
    pointTitle: optionalString(search.pointTitle),
    q: optionalString(search.q),
  };
}
