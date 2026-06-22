import { lazy, Suspense } from "react";
import { Spin } from "antd";
import { Navigate, Route, Routes } from "react-router-dom";

import { LoginPage } from "./auth/LoginPage";
import { RequireAdmin } from "./auth/RequireAdmin";
import { AdminAppProviders } from "./providers";
import { adminDefaultRoute } from "./routes";

const CatalogPointPreviewWindow = lazy(async () => {
  const module = await import("../features/catalog-tree/CatalogPointPreviewWindow");
  return { default: module.CatalogPointPreviewWindow };
});

function WindowFallback() {
  return (
    <div className="center-screen">
      <Spin size="large" />
    </div>
  );
}

export function AdminApp() {
  return (
    <AdminAppProviders>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/catalog-preview"
          element={
            <RequireAdmin>
              <Suspense fallback={<WindowFallback />}>
                <CatalogPointPreviewWindow />
              </Suspense>
            </RequireAdmin>
          }
        />
        <Route path="/" element={<Navigate to={adminDefaultRoute} replace />} />
        <Route path="/*" element={<RequireAdmin />} />
      </Routes>
    </AdminAppProviders>
  );
}
