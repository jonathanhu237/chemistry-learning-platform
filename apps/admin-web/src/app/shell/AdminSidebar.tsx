import { Layout, Menu, Tooltip, Typography } from "antd";
import { LeftOutlined } from "@ant-design/icons";
import { motion, useReducedMotion } from "motion/react";
import { useLocation, useNavigate } from "react-router-dom";

import { adminNavItemsForRole, selectedAdminNavKey } from "../nav";
import type { AdminRole } from "../routes";

const { Sider } = Layout;
const { Text } = Typography;
const sysuLogoSrc = `${import.meta.env.BASE_URL}sysu-logo.svg`;
const adminSiderWidth = 248;
const adminSiderCollapsedWidth = 72;
const navBrandTransition = { type: "tween" as const, duration: 0.16, ease: [0.22, 1, 0.36, 1] as const };

export function AdminSidebar({
  role,
  navCollapsed,
  setNavCollapsed,
}: {
  role: AdminRole;
  navCollapsed: boolean;
  setNavCollapsed: (value: boolean | ((current: boolean) => boolean)) => void;
}) {
  const navigate = useNavigate();
  const location = useLocation();
  const prefersReducedMotion = useReducedMotion();
  const brandTransition = prefersReducedMotion ? { duration: 0 } : navBrandTransition;
  const visibleNavItems = adminNavItemsForRole(role);

  return (
    <Sider
      width={adminSiderWidth}
      collapsedWidth={adminSiderCollapsedWidth}
      collapsed={navCollapsed}
      trigger={null}
      className="admin-sider"
      onBreakpoint={(broken) => setNavCollapsed(broken)}
      breakpoint="lg"
    >
      <Tooltip title={navCollapsed ? "展开导航" : "收起导航"} placement="right">
        <button
          type="button"
          className="brand brand-toggle"
          aria-label={navCollapsed ? "展开导航" : "收起导航"}
          aria-expanded={!navCollapsed}
          onClick={() => setNavCollapsed((value) => !value)}
        >
          <motion.span className="brand-mark" animate={{ scale: 1 }} transition={brandTransition}>
            <img src={sysuLogoSrc} alt="" />
          </motion.span>
          <motion.span
            className="brand-copy"
            animate={{
              opacity: navCollapsed ? 0 : 1,
              x: navCollapsed ? -10 : 0,
            }}
            initial={false}
            transition={brandTransition}
          >
            <Text strong>中大实验学习后台</Text>
          </motion.span>
          <motion.span
            className="brand-arrow"
            aria-hidden="true"
            animate={{
              opacity: navCollapsed ? 0 : 1,
              x: navCollapsed ? -8 : 0,
              rotate: navCollapsed ? 180 : 0,
            }}
            initial={false}
            transition={brandTransition}
          >
            <LeftOutlined />
          </motion.span>
        </button>
      </Tooltip>
      <Menu
        mode="inline"
        inlineCollapsed={navCollapsed}
        selectedKeys={[selectedAdminNavKey(location.pathname, role)]}
        items={visibleNavItems}
        onClick={({ key }) => navigate(String(key))}
      />
    </Sider>
  );
}
