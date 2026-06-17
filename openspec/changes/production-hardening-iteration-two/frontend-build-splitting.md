## Frontend Build Splitting Result: 2026-06-17

Changed files:

- `apps/admin-web/vite.config.ts`
- `apps/admin-web/src/main.tsx`
- `apps/admin-web/src/lib/assistant-markdown/AssistantMarkdownContent.tsx`
- `apps/admin-web/package.json`
- `apps/admin-web/scripts/report-build-chunks.mjs`

Implementation notes:

- Existing page modules were already route-lazy through `React.lazy`, so the route boundary was preserved.
- Added explicit Vite `manualChunks` groups for React/router/query, Ant Design, charts/G2, Markdown/KaTeX, upload/tus/hash, motion, and dayjs.
- Moved KaTeX CSS from the global app entry into the lazy Markdown component boundary.
- Added `npm run build:report` to classify chunk sizes and owners after `npm run build`.
- Removed the catch-all vendor chunk after it produced Rollup circular chunk warnings; only clear dependency families are manually grouped.

Validation:

```powershell
npm run typecheck
npm test
npm run build
npm run build:report
```

Results:

- PASS: frontend typecheck
- PASS: frontend tests, 7 passed
- PASS: production build
- PASS: chunk report
- Browser smoke passed for `/overview`, `/learning-assistant`, `/question-banks`, `/analytics`, and `/videos`.

Largest current chunks:

| Chunk | Size | Gzip | Owner |
| --- | ---: | ---: | --- |
| `charts-vendor-*.js` | 1449.2 KB | 429.9 KB | Charts/G2 vendor |
| `antd-vendor-*.js` | 932.5 KB | 299.6 KB | Ant Design vendor |
| `markdown-vendor-*.js` | 445.9 KB | 131.2 KB | Markdown/KaTeX vendor |
| `react-vendor-*.js` | 267.4 KB | 84.3 KB | React/router/query vendor |
| `upload-vendor-*.js` | 139.7 KB | 44.4 KB | Upload/tus/hash vendor |
| `motion-vendor-*.js` | 121.9 KB | 39.8 KB | Motion vendor |

Known remaining warning:

- Vite still reports chunks over 500 KB, but the remaining oversized chunks are now named third-party vendor budgets: charts/G2 and Ant Design.
- App-owned route chunks are small; representative page chunks are under 35 KB minified in the report.

Browser smoke summary:

| Route | Result | Lazy chunk observed |
| --- | --- | --- |
| `/overview` | PASS | `LearningResourcesPage-*.js` |
| `/learning-assistant` | PASS | `LearningAssistantPage-*.js`, `markdown-vendor-*.js` |
| `/question-banks` | PASS | `QuestionBanksPage-*.js` |
| `/analytics` | PASS | `AnalyticsPage-*.js` |
| `/videos` | PASS | `VideoResourcesPage-*.js` |
