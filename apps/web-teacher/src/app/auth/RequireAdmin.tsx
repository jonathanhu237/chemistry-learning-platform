import { useCallback, useEffect, useState } from "react";
import type { ReactNode } from "react";
import { Spin } from "antd";
import { useQueryClient } from "@tanstack/react-query";
import { Navigate, useLocation, useNavigate } from "react-router-dom";

import type { LoginResponse } from "../../api/auth";
import { getAuthToken, setAuthToken } from "../../api/auth";
import { ForcedPasswordChangePage } from "../../features/account/ForcedPasswordChangePage";
import { AdminShell } from "../shell/AdminShell";
import { useAdminSession } from "./useAdminSession";

export function RequireAdmin({ children }: { children?: ReactNode }) {
  const [token, setSessionToken] = useState(getAuthToken);
  const navigate = useNavigate();
  const location = useLocation();
  const queryClient = useQueryClient();
  const meQuery = useAdminSession(token);

  const replaceSession = useCallback(
    (response: LoginResponse) => {
      setAuthToken(response.access_token);
      queryClient.removeQueries({ queryKey: ["me"] });
      queryClient.setQueryData(["me", response.access_token], response.user);
      setSessionToken(response.access_token);
    },
    [queryClient],
  );

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
    setSessionToken("");
    queryClient.clear();
    navigate("/login", { replace: true });
  };

  if (meQuery.data.must_change_password) {
    return <ForcedPasswordChangePage user={meQuery.data} onChanged={replaceSession} onLogout={logout} />;
  }

  if (children) return <>{children}</>;

  return <AdminShell user={meQuery.data} onLogout={logout} onSessionReplaced={replaceSession} />;
}
