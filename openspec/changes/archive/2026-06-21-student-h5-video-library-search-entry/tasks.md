## 1. Route And Home Entry

- [x] 1.1 Add typed route helpers and route visibility support for `/video-library` as a hidden-bottom-nav detail route.
- [x] 1.2 Add a video library route page folder under `apps/student-web/src/routes/video-library` or equivalent route-page ownership location.
- [x] 1.3 Add a home-page experiment video library entry card without adding a large home-page global search input.
- [x] 1.4 Ensure opening the home entry pushes `/video-library` with source-aware back behavior.
- [x] 1.5 Add direct route rendering for `/video-library` after refresh/deep link.
- [x] 1.6 Define and use route-role helpers/docs so first-level pages are only bottom-nav roots, while all other authenticated task, collection, and detail routes remain non-tab detail pages regardless of stack depth.

## 2. Backend Search Contract

- [x] 2.1 Define request and response schemas for video-library search queries, result groups, result items, and route targets.
- [x] 2.2 Add a student-authenticated search endpoint scoped to experiment-video learning content.
- [x] 2.3 Add backend validation that rejects unrelated global/admin/teacher-draft search domains.
- [x] 2.4 Add typed result target fields for point detail, experiment detail/list, chapter detail, knowledge context, and AI prompt actions.
- [x] 2.5 Add disabled/unavailable/empty response states so the frontend can render graceful fallbacks.

## 3. Search Adapter And Index Source

- [x] 3.1 Add configuration for Elasticsearch/OpenSearch endpoint, index name, enabled flag, timeout, and local fallback mode.
- [x] 3.2 Implement a video-library search adapter interface with Elasticsearch-compatible and deterministic local metadata implementations.
- [x] 3.3 Build index documents only from student-visible experiment/video/point/chapter/knowledge content.
- [x] 3.4 Include searchable fields for experiment title/code/aliases, video point title/key, candidate observations, reagents, apparatus, phenomenon tags, chapters, elements, knowledge points, equations, and formulas where available.
- [x] 3.5 Ensure draft, archived, unpublished, unready, teacher-only, and non-student-visible content cannot appear in indexed documents or search responses.
- [x] 3.6 Add tests for indexing visibility filters and local fallback search behavior.

## 4. Video Library Page UX

- [x] 4.1 Build the video library page with a top search box, page back control, and hidden bottom navigation.
- [x] 4.2 Build the default browse state with supported modules such as recommended videos, recent/continue learning, phenomenon chips, reagent chips, chapter chips, or element-family chips.
- [x] 4.3 Build loading, disabled, error, empty, and populated result states.
- [x] 4.4 Group results by learning action, such as video points, experiments, chapter/knowledge results, and AI explanation actions.
- [x] 4.5 Preserve the active query and grouped results when returning from a result detail where browser history allows.
- [x] 4.6 Ensure the page does not visually read as a generic all-site search page.

## 5. Result Navigation

- [x] 5.1 Map `video_point` results to the existing point detail route with experiment and point context.
- [x] 5.2 Map `experiment` results to a supported experiment or point detail destination without restoring an experiment root tab.
- [x] 5.3 Map chapter, element-family, or knowledge-point results to chapter learning routes with `from=video-library` source context.
- [x] 5.4 Map AI explanation actions to shared AI chat with compact result context.
- [x] 5.5 Omit or disable any backend result that lacks a valid supported route target.
- [x] 5.6 Verify result navigation never changes first-level root identity as a side effect.
- [x] 5.7 Verify learning-page tags, chapter cards, experiment cards, and point cards still navigate directly to their matching target routes instead of opening `/video-library`.
- [x] 5.8 Verify navigation such as `home -> /video-library -> point detail` remains detail-to-detail stack navigation and does not introduce a separate third-level product category or bottom-nav state.

## 6. Serving And Readiness

- [x] 6.1 Update FastAPI SPA fallback tests to include direct `/video-library` serving.
- [x] 6.2 Update production readiness or student frontend validation docs/checks to include the video library direct route when enabled.
- [x] 6.3 Document required search service environment variables and local fallback behavior.

## 7. Verification

- [x] 7.1 Add backend unit tests for search schemas, auth, result filtering, visibility rules, and fallback behavior.
- [x] 7.2 Add student frontend route/e2e tests for home entry, video library default state, query state, result grouping, and result navigation.
- [x] 7.3 Add mobile viewport QA coverage for 360px, 390px, and 430px video library default/search/result/error states.
- [x] 7.4 Run backend tests relevant to student search and visibility filtering.
- [x] 7.5 Run student H5 typecheck, tests, build, and mobile QA.
- [x] 7.6 Run `openspec validate student-h5-video-library-search-entry --strict`.
