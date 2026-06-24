import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const apiProxyTarget = process.env.VITE_API_PROXY_TARGET || "http://127.0.0.1:8000";
const appDir = dirname(fileURLToPath(import.meta.url));
const appsRoot = resolve(appDir, "..");

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    fs: {
      allow: [appsRoot],
    },
    proxy: {
      "/api": apiProxyTarget,
    },
  },
  preview: {
    port: 4173,
  },
  test: {
    environment: "jsdom",
    environmentOptions: {
      jsdom: {
        url: "http://localhost:5173/",
      },
    },
  },
});
