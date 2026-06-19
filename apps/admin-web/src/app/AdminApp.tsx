import { Navigate, Route, Routes } from "react-router-dom";

import { LoginPage } from "./auth/LoginPage";
import { RequireAdmin } from "./auth/RequireAdmin";
import { AdminAppProviders } from "./providers";
import { adminDefaultRoute } from "./routes";

export function AdminApp() {
  return (
    <AdminAppProviders>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/" element={<Navigate to={adminDefaultRoute} replace />} />
        <Route path="/*" element={<RequireAdmin />} />
      </Routes>
    </AdminAppProviders>
  );
}
