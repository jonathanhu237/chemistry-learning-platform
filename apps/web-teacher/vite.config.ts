import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const backendPort = process.env.BACKEND_HOST_PORT || "18000";
const proxyTarget = process.env.VITE_API_PROXY_TARGET || `http://127.0.0.1:${backendPort}`;

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": {
        target: proxyTarget,
        changeOrigin: true,
      },
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: "./src/test/setup.ts",
    environmentOptions: {
      jsdom: {
        url: "http://localhost:5177/",
      },
    },
  },
});
