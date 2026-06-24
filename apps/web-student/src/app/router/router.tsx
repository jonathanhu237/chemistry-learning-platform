import { Navigate, Outlet, createRootRouteWithContext, createRoute, createRouter } from "@tanstack/react-router";
import { AuthenticatedAppLayout } from "../shell/AuthenticatedAppLayout";
import { HomeRootPage } from "../../routes/home/HomeRootPage";
import { LearnRootPage } from "../../routes/learn/LearnRootPage";
import { LearningAreaPage } from "../../routes/learn/LearningAreaPage";
import { ChapterStudyPage } from "../../routes/learn/ChapterStudyPage";
import { CatalogDirectoryPage } from "../../routes/learn/CatalogDirectoryPage";
import { ElementDetailPage } from "../../routes/learn/ElementDetailPage";
import { ExperimentPointPage } from "../../routes/learn/ExperimentPointPage";
import { PreviewCatalogNodePage } from "../../routes/learn/PreviewCatalogNodePage";
import { PreviewCatalogPointPage } from "../../routes/learn/PreviewCatalogPointPage";
import { AiRootPage } from "../../routes/ai/AiRootPage";
import { AiChatPage } from "../../routes/ai/AiChatPage";
import { AssessmentRootPage } from "../../routes/assessment/AssessmentRootPage";
import { AssessmentCustomPage } from "../../routes/assessment/AssessmentCustomPage";
import { AssessmentSessionPage } from "../../routes/assessment/AssessmentSessionPage";
import { AssessmentReportPage } from "../../routes/assessment/AssessmentReportPage";
import { ProfileRootPage } from "../../routes/profile/ProfileRootPage";
import { ProfileReportsPage } from "../../routes/profile/ProfileReportsPage";
import { FeedbackPage } from "../../routes/profile/FeedbackPage";
import { UnifiedSearchPage } from "../../routes/search/UnifiedSearchPage";
import { VideoLibraryPage } from "../../routes/video-library/VideoLibraryPage";
import { parseStudentRouteSearch } from "./routeTypes";

export type StudentRouterContext = Record<string, never>;

const rootRoute = createRootRouteWithContext<StudentRouterContext>()({
  component: Outlet,
  notFoundComponent: () => <Navigate to="/home" replace />,
});

const authenticatedRoute = createRoute({
  getParentRoute: () => rootRoute,
  id: "authenticated",
  component: AuthenticatedAppLayout,
});

const indexRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: "/",
  component: () => <Navigate to="/home" replace />,
});

const homeRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: "/home",
  component: HomeRootPage,
});

const learnRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: "/learn",
  component: LearnRootPage,
});

const learningAreaRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: "/learn/area/$areaId",
  validateSearch: parseStudentRouteSearch,
  component: LearningAreaPage,
});

const chapterRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: "/chapter/$profileId",
  validateSearch: parseStudentRouteSearch,
  component: ChapterStudyPage,
});

const elementRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: "/chapter/$profileId/element/$symbol",
  validateSearch: parseStudentRouteSearch,
  component: ElementDetailPage,
});

const pointRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: "/point/$nodeId",
  validateSearch: parseStudentRouteSearch,
  component: ExperimentPointPage,
});

const catalogNodeRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: "/catalog/$nodeId",
  validateSearch: parseStudentRouteSearch,
  component: CatalogDirectoryPage,
});

const previewPointRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/preview/catalog/points/$nodeId",
  component: PreviewCatalogPointPage,
});

const previewNodeRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/preview/catalog/nodes/$nodeId",
  component: PreviewCatalogNodePage,
});

const videoLibraryRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: "/video-library",
  validateSearch: parseStudentRouteSearch,
  component: VideoLibraryPage,
});

const searchRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: "/search",
  validateSearch: parseStudentRouteSearch,
  component: UnifiedSearchPage,
});

const aiRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: "/ai",
  component: AiRootPage,
});

const aiChatRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: "/ai/chat",
  validateSearch: parseStudentRouteSearch,
  component: AiChatPage,
});

const assessmentRootRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: "/assessment",
  component: AssessmentRootPage,
});

const assessmentCustomRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: "/assessment/custom",
  validateSearch: parseStudentRouteSearch,
  component: AssessmentCustomPage,
});

const assessmentSessionRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: "/assessment/session/$sessionId",
  validateSearch: parseStudentRouteSearch,
  component: AssessmentSessionPage,
});

const assessmentReportRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: "/assessment/report/$sessionId",
  validateSearch: parseStudentRouteSearch,
  component: AssessmentReportPage,
});

const assessmentPersistedReportRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: "/assessment/reports/$reportId",
  validateSearch: parseStudentRouteSearch,
  component: AssessmentReportPage,
});

const profileRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: "/profile",
  component: ProfileRootPage,
});

const profileReportsRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: "/profile/reports",
  validateSearch: parseStudentRouteSearch,
  component: ProfileReportsPage,
});

const feedbackRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: "/feedback/new",
  validateSearch: parseStudentRouteSearch,
  component: FeedbackPage,
});

const routeTree = rootRoute.addChildren([
  previewNodeRoute,
  previewPointRoute,
  authenticatedRoute.addChildren([
    indexRoute,
    homeRoute,
    learnRoute,
    learningAreaRoute,
    chapterRoute,
    elementRoute,
    catalogNodeRoute,
    pointRoute,
    searchRoute,
    videoLibraryRoute,
    aiRoute,
    aiChatRoute,
    assessmentRootRoute,
    assessmentCustomRoute,
    assessmentSessionRoute,
    assessmentReportRoute,
    assessmentPersistedReportRoute,
    profileRoute,
    profileReportsRoute,
    feedbackRoute,
  ]),
]);

export function createStudentRouter() {
  return createRouter({
    routeTree,
    context: {},
    defaultPreload: "intent",
  });
}

export type StudentRouter = ReturnType<typeof createStudentRouter>;

declare module "@tanstack/react-router" {
  interface Register {
    router: StudentRouter;
  }
}
