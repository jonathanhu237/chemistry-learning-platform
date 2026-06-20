import { Navigate, Outlet, createRootRouteWithContext, createRoute, createRouter } from "@tanstack/react-router";
import { AuthenticatedAppLayout } from "../shell/AuthenticatedAppLayout";
import { HomeRootPage } from "../../routes/home/HomeRootPage";
import { LearnRootPage } from "../../routes/learn/LearnRootPage";
import { ChapterStudyPage } from "../../routes/learn/ChapterStudyPage";
import { CatalogDirectoryPage } from "../../routes/learn/CatalogDirectoryPage";
import { ElementDetailPage } from "../../routes/learn/ElementDetailPage";
import { ExperimentPointPage } from "../../routes/learn/ExperimentPointPage";
import { AiRootPage } from "../../routes/ai/AiRootPage";
import { AiChatPage } from "../../routes/ai/AiChatPage";
import { AssessmentRootPage } from "../../routes/assessment/AssessmentRootPage";
import { AssessmentSessionPage } from "../../routes/assessment/AssessmentSessionPage";
import { AssessmentReportPage } from "../../routes/assessment/AssessmentReportPage";
import { ProfileRootPage } from "../../routes/profile/ProfileRootPage";
import { FeedbackPage } from "../../routes/profile/FeedbackPage";
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

const videoLibraryRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: "/video-library",
  validateSearch: parseStudentRouteSearch,
  component: VideoLibraryPage,
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

const profileRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: "/profile",
  component: ProfileRootPage,
});

const feedbackRoute = createRoute({
  getParentRoute: () => authenticatedRoute,
  path: "/feedback/new",
  validateSearch: parseStudentRouteSearch,
  component: FeedbackPage,
});

const routeTree = rootRoute.addChildren([
  authenticatedRoute.addChildren([
    indexRoute,
    homeRoute,
    learnRoute,
    chapterRoute,
    elementRoute,
    catalogNodeRoute,
    pointRoute,
    videoLibraryRoute,
    aiRoute,
    aiChatRoute,
    assessmentRootRoute,
    assessmentSessionRoute,
    assessmentReportRoute,
    profileRoute,
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
