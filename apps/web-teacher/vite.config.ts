import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

const vendorChunks: Array<{ name: string; patterns: string[] }> = [
  {
    name: "react-vendor",
    patterns: [
      "/node_modules/react/",
      "/node_modules/react-dom/",
      "/node_modules/react-router",
      "/node_modules/@tanstack/react-query/",
    ],
  },
  {
    name: "antd-vendor",
    patterns: [
      "/node_modules/antd/",
      "/node_modules/@ant-design/icons/",
      "/node_modules/@ant-design/cssinjs/",
      "/node_modules/@rc-component/",
      "/node_modules/rc-",
    ],
  },
  {
    name: "charts-vendor",
    patterns: [
      "/node_modules/@ant-design/plots/",
      "/node_modules/@antv/",
      "/node_modules/d3",
    ],
  },
  {
    name: "markdown-vendor",
    patterns: [
      "/node_modules/katex/",
      "/node_modules/react-markdown/",
      "/node_modules/remark-",
      "/node_modules/rehype-",
      "/node_modules/unified/",
      "/node_modules/micromark",
      "/node_modules/mdast-util-",
      "/node_modules/hast-util-",
      "/node_modules/unist-util-",
      "/node_modules/parse-entities/",
    ],
  },
  {
    name: "upload-vendor",
    patterns: [
      "/node_modules/@uppy/",
      "/node_modules/hash-wasm/",
    ],
  },
  {
    name: "motion-vendor",
    patterns: [
      "/node_modules/motion/",
      "/node_modules/framer-motion/",
    ],
  },
  {
    name: "monaco-vendor",
    patterns: [
      "/node_modules/monaco-editor/",
      "/node_modules/@monaco-editor/",
    ],
  },
  {
    name: "date-vendor",
    patterns: [
      "/node_modules/dayjs/",
    ],
  },
];

function manualVendorChunk(id: string): string | undefined {
  if (!id.includes("node_modules")) return undefined;
  const normalizedId = id.replace(/\\/g, "/");
  const chunk = vendorChunks.find(({ patterns }) => patterns.some((pattern) => normalizedId.includes(pattern)));
  return chunk?.name;
}

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
  build: {
    rollupOptions: {
      output: {
        manualChunks: manualVendorChunk,
      },
    },
  },
  test: {
    environment: "jsdom",
  },
});
