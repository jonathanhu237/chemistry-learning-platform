import { gzipSync } from "node:zlib";
import { readdir, readFile, stat } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import { join } from "node:path";

const root = fileURLToPath(new URL("..", import.meta.url));
const assetsDir = join(root, "dist", "assets");
const largeChunkBytes = 500 * 1024;

const owners = [
  [/^react-vendor-.*\.js$/, "React/router/query vendor"],
  [/^antd-vendor-.*\.js$/, "Ant Design vendor"],
  [/^charts-vendor-.*\.js$/, "Charts/G2 vendor"],
  [/^markdown-vendor-.*\.js$/, "Markdown/KaTeX vendor"],
  [/^upload-vendor-.*\.js$/, "Upload/tus/hash vendor"],
  [/^motion-vendor-.*\.js$/, "Motion vendor"],
  [/^date-vendor-.*\.js$/, "Date utility vendor"],
  [/^vendor-.*\.js$/, "Other vendor"],
  [/Page-.*\.js$/, "Lazy page chunk"],
  [/^Table-.*\.js$/, "Ant Design table chunk"],
  [/\.css$/, "Extracted CSS"],
];

function ownerFor(fileName) {
  return owners.find(([pattern]) => pattern.test(fileName))?.[1] || "Application/shared chunk";
}

function kb(value) {
  return `${(value / 1024).toFixed(1)} KB`;
}

let entries;
try {
  entries = await readdir(assetsDir);
} catch {
  console.error("dist/assets is missing. Run `npm run build` before `npm run build:report`.");
  process.exit(1);
}

const chunks = [];
for (const fileName of entries) {
  if (!/\.(js|css)$/.test(fileName)) continue;
  const filePath = join(assetsDir, fileName);
  const [metadata, source] = await Promise.all([stat(filePath), readFile(filePath)]);
  chunks.push({
    fileName,
    bytes: metadata.size,
    gzipBytes: gzipSync(source).byteLength,
    owner: ownerFor(fileName),
  });
}

chunks.sort((left, right) => right.bytes - left.bytes);

console.log("Production chunk report");
console.log("=======================");
for (const chunk of chunks.slice(0, 24)) {
  const marker = chunk.bytes > largeChunkBytes ? "!" : " ";
  console.log(`${marker} ${chunk.fileName.padEnd(46)} ${kb(chunk.bytes).padStart(10)} gzip ${kb(chunk.gzipBytes).padStart(9)}  ${chunk.owner}`);
}

const largeChunks = chunks.filter((chunk) => chunk.bytes > largeChunkBytes);
if (largeChunks.length) {
  console.log("");
  console.log("Large chunks above 500 KB:");
  for (const chunk of largeChunks) {
    console.log(`- ${chunk.fileName}: ${kb(chunk.bytes)} (${chunk.owner})`);
  }
}
