import { theme, type ThemeConfig } from "antd";

export const adminTheme: ThemeConfig = {
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
    Card: {
      borderRadiusLG: 8,
    },
    Menu: {
      itemSelectedBg: "#e8f2ec",
      itemSelectedColor: "#005826",
      itemHoverBg: "#f6f9f7",
      itemHoverColor: "#005826",
    },
    Segmented: {
      itemSelectedBg: "#ffffff",
    },
    Table: {
      headerBg: "#f1f7f3",
      borderColor: "#dfe8e2",
      rowHoverBg: "#f6f9f7",
    },
  },
};
