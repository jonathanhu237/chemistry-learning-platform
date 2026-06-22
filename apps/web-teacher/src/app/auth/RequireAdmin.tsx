import { useEffect } from "react";
import type { ReactNode } from "react";
import { Spin } from "antd";
import { useQueryClient } from "@tanstack/react-query";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import { getAuthToken, setAuthToken } from "../../api/auth";
import { AdminShell } from "../shell/AdminShell";
import { useAdminSession } from "./useAdminSession";

export function RequireAdmin({ children }: { children?: ReactNode }) {
  const token = getAuthToken();
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const meQuery = useAdminSession(token);

  useEffect(() => {
    if (meQuery.isError) {
      setAuthToken("");
      navigate("/login", { replace: true, state: { from: location.pathname } });
    }
  }, [location.pathname, meQuery.isError, navigate]);

  if (!token) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  if (meQuery.isLoading || !meQuery.data) {
    return (
      <div className="center-screen">
        <Spin size="large" />
      </div>
    );
  }
  if (meQuery.data.role !== "admin" && meQuery.data.role !== "teacher") {
    return <Navigate to="/login" replace />;
  }

  const logout = () => {
    setAuthToken("");
    queryClient.clear();
    navigate("/login", { replace: true });
  };

  if (children) return <>{children}</>;

  return <AdminShell user={meQuery.data} onLogout={logout} />;
}
