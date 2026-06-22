import { readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";

const root = path.resolve(import.meta.dirname, "..");
const srcDir = path.join(root, "src");
const sourceExtensions = new Set([".ts", ".tsx"]);
const legacyApiImportPattern =
  /from\s+["'](?:\.\.\/)+(?:api|api\/index)["']|from\s+["']@\/api(?:\/index)?["']|import\s*\(\s*["'](?:\.\.\/)+(?:api|api\/index)["']\s*\)/;
const forbiddenDomainImportPattern = /from\s+["'](?:\.\.\/)+features\//;
const apiReactImportPattern = /from\s+["']react(?:\/[^"']*)?["']/;
const arboristImportPattern = /from\s+["']react-arborist(?:\/[^"']*)?["']/;
const lucideImportPattern = /from\s+["']lucide-react(?:\/[^"']*)?["']/;

async function collectFiles(dir) {
  const entries = await readdir(dir);
  const files = [];
  for (const entry of entries) {
    const fullPath = path.join(dir, entry);
    const info = await stat(fullPath);
    if (info.isDirectory()) {
      files.push(...(await collectFiles(fullPath)));
    } else if (sourceExtensions.has(path.extname(fullPath))) {
      files.push(fullPath);
    }
  }
  return files;
}

const failures = [];
const files = await collectFiles(srcDir);
for (const file of files) {
  const source = await readFile(file, "utf8");
  const relative = path.relative(root, file).replaceAll(path.sep, "/");
  if (legacyApiImportPattern.test(source)) {
    failures.push(`${relative}: imports the legacy api barrel; import a concrete api/* module instead`);
  }
  if (relative.startsWith("src/api/") && forbiddenDomainImportPattern.test(source)) {
    failures.push(`${relative}: api domain modules must not import feature modules`);
  }
  if (relative.startsWith("src/api/") && apiReactImportPattern.test(source)) {
    failures.push(`${relative}: api domain modules must not import React`);
  }
  if (arboristImportPattern.test(source) && !relative.startsWith("src/features/catalog-tree/")) {
    failures.push(`${relative}: react-arborist must stay route-owned by the catalog tree feature`);
  }
  if (lucideImportPattern.test(source) && !relative.startsWith("src/features/catalog-tree/")) {
    failures.push(`${relative}: lucide-react imports from this change must stay in catalog tree UI modules`);
  }
}

if (failures.length) {
  console.error("Admin frontend import boundary validation failed:");
  for (const failure of failures) {
    console.error(`- ${failure}`);
  }
  process.exit(1);
}

console.log("Admin frontend import boundaries OK");
