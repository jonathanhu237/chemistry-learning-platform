import type { StudentRootRouteId } from "./routeTypes";

export const rootPathById: Record<StudentRootRouteId, string> = {
  home: "/home",
  learn: "/learn",
  ai: "/ai",
  assessment: "/assessment",
  profile: "/profile",
};

export type StudentRouteRole = "root" | "detail" | "redirect";

const rootIds = Object.keys(rootPathById) as StudentRootRouteId[];

export const studentRootRouteIds = rootIds;

export function rootIdForPath(pathname: string): StudentRootRouteId | null {
  return rootIds.find((id) => rootPathById[id] === pathname) || null;
}

export function isRootRoutePath(pathname: string): boolean {
  return rootIdForPath(pathname) !== null;
}

export function isDetailRoutePath(pathname: string): boolean {
  return !isRootRoutePath(pathname) && pathname !== "/";
}

export function routeRoleForPath(pathname: string): StudentRouteRole {
  if (pathname === "/") return "redirect";
  return isRootRoutePath(pathname) ? "root" : "detail";
}

export function fallbackRootPath(source?: string | null): string {
  if (source === "assessment-custom" || source === "assessment-session" || source === "assessment-report") {
    return rootPathById.assessment;
  }
  if (source === "profile-reports") {
    return rootPathById.profile;
  }
  if (source && rootIds.includes(source as StudentRootRouteId)) {
    return rootPathById[source as StudentRootRouteId];
  }
  return rootPathById.home;
}
