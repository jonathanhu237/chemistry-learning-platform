import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = __dirname;
const imagesDir = path.join(projectRoot, "images");

const mime = {
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".gif": "image/gif",
  ".webp": "image/webp",
  ".svg": "image/svg+xml; charset=utf-8",
};

function projectImagesPlugin() {
  return {
    name: "project-images",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        if (!req.url || !req.url.startsWith("/images/")) return next();
        const clean = decodeURIComponent(req.url.split("?")[0].replace(/^\/images\//, ""));
        const target = path.normalize(path.join(imagesDir, clean));
        if (!target.startsWith(imagesDir)) {
          res.writeHead(403);
          res.end("Forbidden");
          return;
        }
        fs.readFile(target, (error, data) => {
          if (error) {
            res.writeHead(404);
            res.end("Not found");
            return;
          }
          res.writeHead(200, {
            "Content-Type": mime[path.extname(target).toLowerCase()] || "application/octet-stream",
            "Cache-Control": "no-store"
          });
          res.end(data);
        });
      });
    }
  };
}

export default defineConfig({
  root: __dirname,
  plugins: [react(), projectImagesPlugin()],
  server: {
    host: "127.0.0.1",
    port: 5178,
    strictPort: false,
    fs: {
      allow: [__dirname, projectRoot]
    }
  }
});
