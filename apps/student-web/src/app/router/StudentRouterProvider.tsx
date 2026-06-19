import { useMemo } from "react";
import { RouterProvider } from "@tanstack/react-router";
import type { AuthUser } from "../../api";
import { StudentShellBaseProvider } from "../shell/studentAppContext";
import { createStudentRouter } from "./router";

export function StudentRouterProvider({ user, onLogout }: { user: AuthUser; onLogout: () => void | Promise<void> }) {
  const router = useMemo(() => createStudentRouter(), []);
  const baseContext = useMemo(() => ({ user, onLogout }), [onLogout, user]);
  return (
    <StudentShellBaseProvider value={baseContext}>
      <RouterProvider router={router} />
    </StudentShellBaseProvider>
  );
}
