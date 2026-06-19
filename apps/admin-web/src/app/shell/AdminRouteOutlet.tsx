import { Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { Spin } from "antd";

import { adminDefaultRoute, adminRoutes } from "../routes";

function RouteFallback() {
  return (
    <div className="center-panel">
      <Spin />
    </div>
  );
}

export function AdminRouteOutlet() {
  return (
    <Routes>
      {adminRoutes.map(({ path, Component }) => (
        <Route
          key={path}
          path={path}
          element={
            <Suspense fallback={<RouteFallback />}>
              <Component />
            </Suspense>
          }
        />
      ))}
      <Route path="*" element={<Navigate to={adminDefaultRoute} replace />} />
    </Routes>
  );
}
