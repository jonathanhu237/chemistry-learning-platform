import { Layout } from "antd";
import { useEffect, useState } from "react";

import type { User } from "../../api/auth";
import { AdminHeader } from "./AdminHeader";
import { AdminRouteOutlet } from "./AdminRouteOutlet";
import { AdminSidebar } from "./AdminSidebar";

const { Content } = Layout;

export function AdminShell({ user, onLogout }: { user: User; onLogout: () => void }) {
  const [navCollapsed, setNavCollapsed] = useState(() => {
    if (typeof window === "undefined") return false;
    return window.localStorage.getItem("admin-nav-collapsed") === "true";
  });

  useEffect(() => {
    window.localStorage.setItem("admin-nav-collapsed", String(navCollapsed));
  }, [navCollapsed]);

  return (
    <Layout className={`admin-shell ${navCollapsed ? "admin-shell-collapsed" : ""}`}>
      <AdminSidebar role={user.role} navCollapsed={navCollapsed} setNavCollapsed={setNavCollapsed} />
      <Layout className="admin-main">
        <AdminHeader user={user} onLogout={onLogout} />
        <Content className="admin-content">
          <AdminRouteOutlet />
        </Content>
      </Layout>
    </Layout>
  );
}
