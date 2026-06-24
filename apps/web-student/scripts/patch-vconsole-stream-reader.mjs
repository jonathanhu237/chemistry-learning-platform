import { readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const distPath = resolve(scriptDir, "../node_modules/vconsole/dist/vconsole.min.js");

const vulnerableSnippet =
  "if(t){var r=new Uint8Array(t.length+o.value.length);r.set(t),r.set(o.value,t.length),t=r}else t=new Uint8Array(o.value);return e.item.endTime=Date.now()";

const patchedSnippet =
  "if(o.value)if(t){var r=new Uint8Array(t.length+o.value.length);r.set(t),r.set(o.value,t.length),t=r}else t=new Uint8Array(o.value);else t||(t=new Uint8Array(0));return e.item.endTime=Date.now()";

const source = readFileSync(distPath, "utf8");

if (source.includes(patchedSnippet)) {
  console.log("[patch-vconsole] stream reader guard already applied.");
} else if (source.includes(vulnerableSnippet)) {
  writeFileSync(distPath, source.replace(vulnerableSnippet, patchedSnippet));
  console.log("[patch-vconsole] applied stream reader guard for vConsole SSE responses.");
} else {
  console.warn("[patch-vconsole] target snippet not found; vConsole may already include the upstream fix.");
}
