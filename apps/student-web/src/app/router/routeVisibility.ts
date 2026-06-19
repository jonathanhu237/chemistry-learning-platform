import type { StudentRootRouteId } from "./routeTypes";

export const rootPathById: Record<StudentRootRouteId, string> = {
  home: "/home",
  learn: "/learn",
  ai: "/ai",
  assessment: "/assessment",
  profile: "/profile",
};

const rootIds = Object.keys(rootPathById) as StudentRootRouteId[];

export function rootIdForPath(pathname: string): StudentRootRouteId | null {
  return rootIds.find((id) => rootPathById[id] === pathname) || null;
}

export function isRootRoutePath(pathname: string): boolean {
  return rootIdForPath(pathname) !== null;
}

export function isDetailRoutePath(pathname: string): boolean {
  return !isRootRoutePath(pathname) && pathname !== "/";
}

export function fallbackRootPath(source?: string | null): string {
  if (source && rootIds.includes(source as StudentRootRouteId)) {
    return rootPathById[source as StudentRootRouteId];
  }
  return rootPathById.home;
}
