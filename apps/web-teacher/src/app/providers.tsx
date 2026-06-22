import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { App as AntApp, ConfigProvider } from "antd";
import { BrowserRouter } from "react-router-dom";
import type { ReactNode } from "react";

import { adminTheme } from "./theme";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 20_000,
    },
  },
});

export function AdminAppProviders({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ConfigProvider theme={adminTheme}>
          <AntApp>{children}</AntApp>
        </ConfigProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
