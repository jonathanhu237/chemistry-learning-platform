import type { StudentPosttestReport, StudentPosttestResponse } from "../api";

export type ViewState = "checking" | "login" | "password" | "pretest-loading" | "pretest-error" | "pretest" | "home";

export type ChapterLearningView = "facts" | "experiments";

export type StudentTab = "learn" | "experiments" | "assistant" | "assessment" | "profile";

export type LearningRoute =
  | { screen: "entry" }
  | {
      screen: "chapter";
      profileId?: string | null;
      propertyKey?: string | null;
      elementSymbol?: string | null;
      chapterView?: ChapterLearningView;
    }
  | {
      screen: "point";
      profileId?: string | null;
      propertyKey?: string | null;
      propertyTitle?: string | null;
      elementSymbol?: string | null;
      chapterView?: ChapterLearningView;
      experimentId: string;
      pointKey?: string | null;
      pointTitle?: string | null;
    };

export type AssessmentRoute =
  | { screen: "home" }
  | { screen: "posttest"; posttest: StudentPosttestResponse }
  | { screen: "summary"; report: StudentPosttestReport };

export type ExperimentTabRoute =
  | { screen: "overview" }
  | { screen: "group"; parentCode: string }
  | { screen: "detail"; parentCode?: string | null; experimentId: string };
