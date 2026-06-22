import React from "react";
import ReactDOM from "react-dom/client";
import { App as AntApp, ConfigProvider, theme } from "antd";
import zhCN from "antd/locale/zh_CN";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { PlatformAdminApp } from "./PlatformAdminApp";
import "./styles.css";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <ConfigProvider
        locale={zhCN}
        theme={{
          algorithm: theme.defaultAlgorithm,
          token: {
            colorPrimary: "#005826",
            colorInfo: "#356f9c",
            colorSuccess: "#005826",
            colorWarning: "#b8892f",
            colorError: "#b42318",
            colorText: "#0d1f17",
            colorTextSecondary: "#697a72",
            colorBorder: "#dfe8e2",
            colorBorderSecondary: "#dfe8e2",
            colorBgLayout: "#f6f8f5",
            colorBgContainer: "#ffffff",
            borderRadius: 8,
            fontFamily:
              '"PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
          },
          components: {
            Layout: {
              bodyBg: "#f6f8f5",
              headerBg: "#ffffff",
              siderBg: "#ffffff",
            },
            Button: {
              primaryShadow: "0 12px 24px rgba(0, 88, 38, 0.16)",
            },
            Table: {
              headerBg: "#f1f7f3",
              borderColor: "#dfe8e2",
              rowHoverBg: "#f6f9f7",
            },
            Card: {
              borderRadiusLG: 8,
            },
          },
        }}
      >
        <AntApp>
          <PlatformAdminApp />
        </AntApp>
      </ConfigProvider>
    </QueryClientProvider>
  </React.StrictMode>,
);
