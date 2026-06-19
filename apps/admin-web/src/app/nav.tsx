import { adminDefaultRoute, adminRoutes, type AdminRole } from "./routes";

export function adminNavItemsForRole(role: AdminRole) {
  return adminRoutes
    .filter((route) => !route.nav.adminOnly || role === "admin")
    .map((route) => ({
      key: route.path,
      icon: route.nav.icon,
      label: route.nav.label,
      title: route.nav.label,
    }));
}

export function selectedAdminNavKey(pathname: string, role: AdminRole): string {
  return adminNavItemsForRole(role).find((item) => pathname.startsWith(item.key))?.key || adminDefaultRoute;
}
