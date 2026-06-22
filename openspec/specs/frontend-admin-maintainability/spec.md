# frontend-admin-maintainability Specification

## Purpose
TBD - created by archiving change production-quality-iteration-four. Update Purpose after archive.
## Requirements
### Requirement: Frontend feature modules are decomposed incrementally
The admin frontend SHALL reduce large feature-page modules through behavior-preserving extraction of pure helpers, local components, or local hooks.

#### Scenario: A large feature slice is extracted
- **WHEN** a feature-page slice is moved into a new module
- **THEN** existing route paths, API calls, query keys, mutation behavior, and visible workflows MUST remain compatible

### Requirement: App shell avoids feature-heavy eager imports
The admin app shell SHALL keep feature-only dependencies behind lazy route boundaries.

#### Scenario: Heavy feature dependencies remain route-owned
- **WHEN** the production build is run
- **THEN** charts, markdown/math rendering, upload/tus utilities, and assistant/video/question-bank feature code MUST NOT be newly imported eagerly by the top-level app shell

### Requirement: Build warnings remain owned and actionable
Large production chunks SHALL be named, associated with an owner, and documented as intentional or targeted for later splitting.

#### Scenario: A vendor chunk exceeds the warning threshold
- **WHEN** Vite reports a chunk larger than the warning threshold
- **THEN** the build report MUST identify the chunk owner, and the pass MUST document whether it is accepted or a follow-up target

### Requirement: CI trigger posture remains unchanged
The production readiness workflow SHALL remain manually triggered during this pass.

#### Scenario: Fourth-pass changes are pushed
- **WHEN** commits are pushed to `codex/productionize-admin-platform`
- **THEN** no workflow change in this pass MUST cause production readiness to run solely because of that push

### Requirement: Catalog editor feature boundary
The admin frontend SHALL implement the teacher catalog editor as a feature-owned module with clear submodule boundaries.

#### Scenario: Developer edits tree behavior
- **WHEN** a developer changes tree search, selection, expansion, drag-move, reorder, drop validation, or row actions
- **THEN** the code MUST be localized to catalog tree interaction modules
- **AND** it MUST NOT require editing an unrelated admin shell or monolithic route page.

#### Scenario: Developer edits node editor behavior
- **WHEN** a developer changes directory basics, directory card presentation, point content, point card presentation, videos, related links, publication, validation, or search preview
- **THEN** the code MUST be localized to selected-node editor modules
- **AND** shared formatting or mapping helpers MUST have explicit module ownership.

### Requirement: Catalog domain API client boundary
The admin frontend SHALL use domain-specific catalog API clients instead of a monolithic API module.

#### Scenario: Catalog APIs are added
- **WHEN** admin catalog tree, node content, media binding, related link, publication, or search diagnostics APIs are introduced
- **THEN** they MUST live in feature-appropriate domain API client modules
- **AND** imports MUST respect the admin import boundary validation.

#### Scenario: Legacy experiment API client is removed
- **WHEN** the catalog-node APIs replace experiment video-point APIs
- **THEN** admin feature code MUST stop importing removed legacy experiment point functions
- **AND** boundary validation MUST fail if old APIs are accidentally reintroduced as a compatibility layer.

### Requirement: Large editor surfaces remain split
The admin catalog workspace SHALL avoid becoming another large all-in-one experiments page.

#### Scenario: Catalog workspace grows
- **WHEN** tree editing, drag/drop state, directory card forms, point content forms, video binding panels, related-link editors, search preview, and validation panels are implemented
- **THEN** each major surface MUST be split into route-local components, hooks, and pure mappers
- **AND** the route page MUST remain an orchestration layer rather than the owner of all behavior.

#### Scenario: Catalog editor line-count risk appears
- **WHEN** a single catalog-tree React module begins to own tree rendering, drag/drop behavior, directory forms, point forms, media bindings, and related links together
- **THEN** the implementation MUST split the module before completion
- **AND** admin maintainability validation or task review MUST call out the ownership boundary.

### Requirement: Frontend apps keep product-specific ownership
The repository SHALL keep `web-admin`, `web-teacher`, and `web-student` frontend source, package metadata, and build scripts product-specific.

#### Scenario: Teacher app owns teacher workflows
- **WHEN** a developer edits experiment catalog, question bank, learning assistant, AI access, settings, classes, resources, media, analytics, or feedback workflows
- **THEN** the code MUST live under the `web-teacher` app
- **AND** it MUST NOT import or depend on `web-admin` account-management modules.

#### Scenario: Platform app owns account management
- **WHEN** a developer edits teacher-account list, create, status update, display-name update, password reset, or disable/delete behavior
- **THEN** the code MUST live under the `web-admin` app
- **AND** it MUST NOT import teacher experiment, question-bank, AI, settings, media, analytics, learning-assistant, or student-H5 feature modules.

#### Scenario: Student app remains independent
- **WHEN** a developer edits student learning, assessment, assistant, feedback, auth, or catalog behavior
- **THEN** the code MUST live under the `web-student` app or its shared student modules
- **AND** service/package naming MUST NOT refer to the app as `student-web`.

### Requirement: Teacher shell avoids role-based feature forks
The teacher frontend SHALL avoid product-obsolete feature visibility branches based on `admin` versus legacy `teacher` roles.

#### Scenario: Route registry is evaluated
- **WHEN** the teacher route registry and navigation model are loaded
- **THEN** learning assistant, AI access, settings, experiment catalog, question bank, resources, classes, analytics, feedback, and media routes MUST be available to teacher-console users
- **AND** route visibility MUST NOT depend on an `adminOnly` flag for those modules.

#### Scenario: Teacher auth guard evaluates role
- **WHEN** an active `admin` or legacy `teacher` account opens `/learning-assistant`
- **THEN** the guard MUST allow the route
- **AND** it MUST NOT redirect the user away because the role is `teacher`.

### Requirement: Catalog tree drag behavior remains feature-local and verified
The admin frontend SHALL implement modern catalog tree drag behavior through feature-owned modules, focused pure helpers, and real interaction verification rather than broad shell changes or superficial visual checks.

#### Scenario: Developer changes catalog drag behavior
- **WHEN** a developer updates drag preview, drop cursor, hover expansion, optimistic movement, rollback, or move reconciliation
- **THEN** the implementation MUST remain localized to catalog tree feature modules and existing catalog domain API clients
- **AND** it MUST NOT require editing unrelated admin shell, routing, or monolithic application modules.

#### Scenario: Developer adds optimistic movement logic
- **WHEN** optimistic tree movement, source/target branch detection, stale-branch marking, or rollback logic is introduced
- **THEN** the pure transformation behavior MUST be covered by focused tests
- **AND** tests MUST cover same-parent reorder, cross-parent move, root move, unloaded target parent, invalid point target, invalid descendant target, success reconciliation, and failure rollback.

#### Scenario: Developer verifies real drag interactions
- **WHEN** the modern tree movement change is implemented
- **THEN** browser or equivalent interaction QA MUST exercise real pointer drag behavior on the catalog tree
- **AND** QA MUST verify drag preview, source dragging state, before/after insertion feedback, directory drop-target feedback, hover auto-expansion, post-drop visible update, and post-success reconciliation.

#### Scenario: Browser drag tooling is unavailable
- **WHEN** local Playwright or browser tooling is missing or cannot simulate drag reliably
- **THEN** the implementation pass MUST either install/use available browser tooling or record a concrete blocker
- **AND** it MUST NOT downgrade the verification plan to payload-only unit tests.

#### Scenario: Existing fallback movement commands are maintained
- **WHEN** menu-based move before/after or other precision movement commands remain available
- **THEN** those commands MUST use the same refresh and rollback semantics as drag movement
- **AND** they MUST remain accessible without relying on drag-and-drop alone.

### Requirement: Contextual catalog summaries remain feature-local
The admin frontend SHALL implement contextual selected-node summaries inside catalog-tree owned modules and styles using existing catalog detail data.

#### Scenario: Developer changes directory or point summary items
- **WHEN** a developer updates the selected-node summary header for directories or point nodes
- **THEN** the change MUST remain localized to catalog editor components and catalog-tree styles
- **AND** it MUST derive values from existing `CatalogNodeDetail` fields without introducing new API calls.

#### Scenario: Developer verifies contextual summaries
- **WHEN** contextual summary rendering is implemented
- **THEN** focused verification MUST cover at least one directory node and one point node
- **AND** it MUST include automated typecheck, focused tests, or equivalent catalog editor behavior checks.

### Requirement: Catalog editor presentation refinements remain feature-local
The admin frontend SHALL implement selected-node title-card and tab-view refinements inside catalog-tree owned modules and styles without introducing broad shell changes or a parallel editor behavior model.

#### Scenario: Developer changes selected-node header presentation
- **WHEN** a developer updates the catalog selected-node title card, status information blocks, or header actions
- **THEN** the change MUST remain localized to catalog editor components and catalog-tree styles
- **AND** it MUST reuse existing selected-node data, derived counts, publication state, and action handlers.

#### Scenario: Developer changes the selected-node status plaque
- **WHEN** a developer changes the right-aligned node status plaque in the selected-node header
- **THEN** the implementation MUST keep status rendering inside catalog-tree owned header components and styles
- **AND** it MUST preserve the existing status summary data shape rather than adding a new backend contract
- **AND** focused verification MUST check that the plaque remains visually distinct from maintenance summary cards without stretching them.

#### Scenario: Developer changes editor panel switching presentation
- **WHEN** a developer updates the selected-node panel switcher styling
- **THEN** the change MUST preserve the existing tab item filtering and active-tab behavior
- **AND** it MUST NOT require route shell, backend API, or global design-system rewrites.

#### Scenario: Developer changes catalog authoring panel labels or directory surface
- **WHEN** a developer changes the selected-node authoring labels or the directory-only editor surface
- **THEN** point tab labels and directory direct-panel behavior MUST remain localized to catalog-tree editor, panel, and feature CSS modules
- **AND** directory title editing MUST continue to use the selected-node header identity controls rather than a duplicate routine content-body field.

#### Scenario: Developer verifies the refined editor presentation
- **WHEN** the title-card and tab-view refinements are implemented
- **THEN** focused verification MUST cover at least one selected directory or point state
- **AND** it MUST include automated typecheck, focused tests, or an equivalent catalog editor behavior check.

### Requirement: Catalog workspace visual polish stays feature-local
The admin frontend SHALL keep catalog workspace visual polish inside catalog-tree owned modules and styles.

#### Scenario: Developer polishes catalog chapter switching
- **WHEN** a developer changes the chapter selector presentation for the catalog workspace
- **THEN** the code MUST remain localized to catalog workspace components and catalog-tree styles
- **AND** it MUST reuse existing chapter data, state, and query behavior rather than introducing a parallel chapter-selection model.

#### Scenario: Developer polishes the selected-node editor shell
- **WHEN** a developer changes the selected-node editor header, tabs, empty state, or content surface
- **THEN** the code MUST remain localized to selected-node editor modules and catalog-tree styles
- **AND** it MUST NOT require broad admin shell changes or a new global design-system abstraction.

#### Scenario: Developer verifies catalog polish
- **WHEN** catalog workspace polish is implemented
- **THEN** focused verification MUST cover selected-node and no-selection states
- **AND** it MUST include at least one check that existing catalog editor behavior still works or typechecks.

### Requirement: Catalog sidebar metadata polish remains feature-local
The admin frontend SHALL keep catalog sidebar row metadata, status labels, counts, and toolbar controls inside catalog-owned feature modules and API types.

#### Scenario: Developer adds recursive point counts to the admin API contract
- **WHEN** `descendant_point_count` is added to catalog node cards
- **THEN** the TypeScript contract MUST be owned by the catalog API client module
- **AND** catalog feature test fixtures MUST include the field so missing count handling is caught by tests.

#### Scenario: Developer maps catalog node status for visible UI
- **WHEN** catalog node status is displayed in the left tree
- **THEN** status-to-label and status-to-dot mapping MUST be centralized in catalog tree mapping or row helper modules
- **AND** feature UI code MUST NOT render backend enum values directly as visible tree text.

#### Scenario: Developer changes the tree header controls
- **WHEN** root creation, refresh, expand, collapse, or more-menu controls are changed for the catalog tree
- **THEN** those controls MUST remain in catalog tree workspace/list modules
- **AND** the change MUST NOT require modifying unrelated admin shell, route registry, or global layout modules.

#### Scenario: Developer updates row styling
- **WHEN** icon size, status dot, count, warning, hover action, or selected-row styling changes
- **THEN** CSS MUST remain scoped to the catalog tree feature
- **AND** it MUST NOT introduce global Ant Design overrides for tree rows or buttons.

### Requirement: Catalog sidebar polish is covered by focused regression checks
The admin frontend SHALL include focused checks for localized tree metadata, authoritative directory counts, and non-duplicated creation controls.

#### Scenario: Unit or contract tests render tree rows
- **WHEN** tree row tests render draft, published, or archived nodes
- **THEN** tests MUST assert Chinese-facing status labels, status-dot semantics, or accessible status labels
- **AND** tests MUST fail if visible row text contains raw `published`, `draft`, or `archived`.

#### Scenario: Directory count behavior is tested
- **WHEN** tree row or mapper tests render a directory with `descendant_point_count`
- **THEN** tests MUST assert that the directory count is shown as directory trailing metadata
- **AND** tests MUST assert that point rows do not show the directory descendant count.

#### Scenario: Root creation controls are tested
- **WHEN** catalog tree workspace or list tests inspect root creation controls
- **THEN** tests MUST assert that there is a single visible root creation surface for the selected chapter
- **AND** tests MUST assert that the creation menu provides Chinese entries for directory and point creation.

#### Scenario: Browser QA captures the teacher tree
- **WHEN** the change is implementation-complete
- **THEN** browser QA MUST capture the left tree at normal admin width and narrow laptop width
- **AND** the screenshots MUST show aligned chevrons, icons, directory counts, status dots, and non-duplicated root creation controls without text overlap.

### Requirement: Backend catalog count shape is validated with admin read-model tests
The backend SHALL include focused tests for the recursive count field used by the admin catalog sidebar.

#### Scenario: Backend returns root and child cards
- **WHEN** backend tests create nested directory and point nodes
- **THEN** root and child list responses MUST include `descendant_point_count`
- **AND** directory counts MUST include point descendants across multiple levels.

#### Scenario: Backend excludes archived descendants
- **WHEN** a point descendant is archived
- **THEN** subsequent admin catalog card responses MUST exclude that archived point from normal `descendant_point_count`
- **AND** point node cards MUST still return `descendant_point_count` as `0`.

#### Scenario: Backend count updates after movement
- **WHEN** a point or directory subtree is moved between directory parents
- **THEN** subsequent admin catalog card responses MUST reflect the updated recursive point counts for old and new ancestors.

### Requirement: Arborist catalog tree dependency is route-owned
The admin frontend SHALL keep the Arborist tree dependency and related icon dependency scoped to the lazy-loaded catalog workspace.

#### Scenario: Arborist dependency is introduced
- **WHEN** `react-arborist` is added to the admin frontend
- **THEN** imports from `react-arborist` MUST live in catalog-tree feature modules
- **AND** the production build report MUST show the resulting tree behavior code is not eagerly imported by unrelated admin shell routes.

#### Scenario: Catalog icon dependency is introduced
- **WHEN** `lucide-react` or another icon package is added for sidebar tree icons
- **THEN** imports from that package MUST be limited to catalog-tree UI modules unless another feature explicitly adopts the same dependency in its own change
- **AND** the icon usage MUST remain tree-shakeable and route-scoped.

#### Scenario: Developer changes the tree engine
- **WHEN** a developer changes Arborist configuration, node rendering, row rendering, drag preview, drop cursor, open state, lazy loading, or move mapping
- **THEN** the change MUST be localized to catalog tree modules
- **AND** selected-node content, video binding, related-link, and media upload modules MUST NOT depend on Arborist types.

### Requirement: Catalog tree visual skin has a stable feature boundary
The admin frontend SHALL implement the Dribbble/Gmail sidebar tree visual skin as feature-owned styling and render helpers.

#### Scenario: Developer changes sidebar tree visuals
- **WHEN** a developer changes chevrons, guide lines, directory icons, point experiment icons, selected state, hover state, drag affordance, trailing metadata, or row actions
- **THEN** those changes MUST live in catalog tree feature CSS or catalog tree row/render modules
- **AND** they MUST NOT introduce global Ant Design or app-shell overrides.

#### Scenario: Developer changes point iconography
- **WHEN** a developer changes the experiment point icon from flask to test tube or another chemistry icon
- **THEN** the icon mapping MUST be centralized in a catalog tree renderer or icon helper
- **AND** point rows MUST NOT fall back to generic document/file icons unless an explicit visual QA decision accepts it.

#### Scenario: Developer removes Ant Design Tree
- **WHEN** the catalog tree migrates from Ant Design Tree to Arborist
- **THEN** tests MUST no longer assert Ant Design Tree-specific wrapper classes as the source of truth
- **AND** tests MUST assert catalog behavior, feature-owned classes, and user-visible tree semantics instead.

### Requirement: Directory and point panel boundaries are test-owned
The admin frontend SHALL keep directory-only and point-only editor panel visibility covered by focused tests.

#### Scenario: Directory node editor is rendered
- **WHEN** a test renders or inspects the selected-node editor for a directory node
- **THEN** it MUST verify that video and related experiment tabs are absent
- **AND** it MUST verify point-only media and related search queries are gated off for directory nodes.

#### Scenario: Point node editor is rendered
- **WHEN** a test renders or inspects the selected-node editor for a point node
- **THEN** it MUST verify that video and related experiment tabs are present
- **AND** it MUST verify those panels remain separate from primary content and advanced diagnostics.

### Requirement: Sidebar tree visual QA is explicit
The admin frontend SHALL validate the Arborist sidebar tree against the requested visual direction with browser or screenshot QA.

#### Scenario: Sidebar tree visual QA runs
- **WHEN** visual QA is run for this change
- **THEN** screenshots MUST cover normal-width and narrow laptop-width catalog tree layouts
- **AND** screenshots MUST include expanded directory, collapsed directory, selected directory, selected point, hover or focus actions, and at least one nested point node with experiment iconography.

#### Scenario: Drag visual QA runs
- **WHEN** browser automation can simulate tree drag movement reliably
- **THEN** the QA MUST capture or assert a visible drop cursor or valid drop-target state
- **AND** if drag screenshot capture is not reliable, the limitation MUST be documented and move/drop behavior MUST still be covered by focused tests.

#### Scenario: Editor capability QA runs
- **WHEN** visual QA validates the right editor after this change
- **THEN** it MUST capture a directory selection without video or related experiment tabs
- **AND** it MUST capture a point selection with video and related experiment tabs.

### Requirement: Catalog tree interaction has an explicit module boundary
The admin frontend SHALL isolate catalog tree behavior from selected-node editing and route orchestration.

#### Scenario: Developer changes tree drag behavior
- **WHEN** a developer changes expansion, selection, search result focusing, drag/drop state, drop validation, reorder, move, or row action behavior
- **THEN** the change MUST be localized to catalog tree interaction modules
- **AND** it MUST NOT require editing point-content forms, media-binding panels, related-link panels, or unrelated admin shell code.

#### Scenario: Tree library adapter is introduced
- **WHEN** implementation uses React Arborist, Ant Design Tree, or another mature tree package
- **THEN** package-specific adapter code MUST be owned by catalog tree modules
- **AND** domain payload construction for move/reorder operations MUST remain in catalog API/mapping owners rather than inside visual row components.

#### Scenario: Tree visual skin changes
- **WHEN** a developer changes row icons, chevrons, guide lines, selected states, hover states, drag handles, status display, or row action placement
- **THEN** those styles and render helpers MUST remain local to the catalog tree feature
- **AND** they MUST NOT introduce global Ant Design overrides that affect unrelated tree, menu, table, or list components.

### Requirement: Selected-node editor panels are split by task
The admin frontend SHALL split the catalog selected-node editor into task-owned panels instead of one large all-concern component.

#### Scenario: Developer changes primary point content
- **WHEN** a developer changes point title mapping, teacher-only note, principle mode, equation/text principle, phenomenon explanation, or safety note UI
- **THEN** the change MUST be localized to point content editor modules and shared catalog form mappers
- **AND** it MUST NOT require editing tree rendering or media upload feature code.

#### Scenario: Developer changes directory card presentation
- **WHEN** a developer changes directory title, teacher note, student description, image, icon, accent, layout variant, or card preview UI
- **THEN** the change MUST be localized to directory editor or student-card panel modules
- **AND** point content, video binding, and related-link modules MUST remain separate.

#### Scenario: Developer changes low-frequency diagnostics
- **WHEN** a developer changes raw node id display, parent/order diagnostics, search-index preview, validation internals, or copy-debug actions
- **THEN** those changes MUST be localized to advanced or publish-check panels
- **AND** the default content panel MUST NOT become the owner of debug/search/order concerns.

### Requirement: Catalog editor dependency and bundle impact are documented
The admin frontend SHALL document any new tree/drag dependency decision and keep it scoped to the catalog workspace.

#### Scenario: New tree dependency is added
- **WHEN** implementation adds a dependency such as `react-arborist`, `react-dnd`, or another tree/drag package
- **THEN** the implementation notes or task review MUST document why it was chosen over Ant Design Tree and MUI X Tree View
- **AND** admin build output MUST be checked so unrelated routes are not eagerly loading the new tree behavior.

#### Scenario: Existing Ant Design Tree is retained
- **WHEN** implementation keeps Ant Design Tree instead of adding a new dependency
- **THEN** the implementation notes MUST document how it satisfies the required source-list visual language, drop indicator, accessibility fallback, and layout stability
- **AND** custom code added to compensate for missing behavior MUST remain feature-local.

### Requirement: Catalog editor visual regression has a stable owner
The admin frontend SHALL treat catalog tree/editor visual acceptance as part of the feature boundary.

#### Scenario: Visual checks are added
- **WHEN** Playwright, browser screenshots, DOM measurements, or manual screenshot notes are added for this change
- **THEN** the checks MUST live with admin catalog feature tests or documented admin QA artifacts
- **AND** they MUST cover both tree interaction states and selected-node editor panel states.

#### Scenario: Build or test validation runs
- **WHEN** admin frontend validation is run for this change
- **THEN** it MUST include typecheck, unit tests or focused component tests, build, boundary validation, and the catalog visual/interaction QA described by the teacher editor spec
- **AND** any accepted visual limitation MUST be documented before the change is considered complete.

### Requirement: Catalog tree uses a mature drag interaction boundary
The admin frontend SHALL implement catalog ordering and movement through a mature draggable tree interaction rather than bespoke per-row move buttons.

#### Scenario: Drag tree dependency is selected
- **WHEN** implementation selects Ant Design Tree, React Arborist, or another mature tree/drag approach
- **THEN** the decision MUST be documented with rationale, bundle/UX trade-offs, and how it integrates with the existing Ant Design admin shell
- **AND** the dependency MUST be route-owned or otherwise avoid eager-loading unrelated admin routes.

#### Scenario: Tree movement is implemented
- **WHEN** a teacher drags a node to reorder or move it
- **THEN** the UI MUST call catalog move/reorder APIs through the catalog API client
- **AND** drag/drop code MUST remain inside catalog tree interaction modules rather than point editor modules.

### Requirement: Catalog upload UI stays outside the catalog editor
The admin frontend SHALL keep video upload UI owned by the media/video feature rather than the catalog editor.

#### Scenario: Catalog point video panel renders
- **WHEN** a point node is selected
- **THEN** the video panel MUST allow choosing, previewing, binding, unbinding, publishing, or unpublishing existing media assets
- **AND** it MUST NOT render local file input or upload-and-bind controls.

#### Scenario: Teacher needs new media
- **WHEN** no suitable existing media asset exists
- **THEN** the catalog editor MAY provide a navigation hint or link to the media upload page
- **AND** the upload workflow MUST remain owned by the media feature.

### Requirement: Catalog node type assumptions are centralized
The admin frontend SHALL centralize directory-vs-point type helpers and remove hybrid/shortcut assumptions from live components.

#### Scenario: Node kind helpers are updated
- **WHEN** catalog node kind handling changes
- **THEN** type definitions, labels, icons, action rules, form hydration, and payload builders MUST support only directory and point
- **AND** repository search MUST show no live admin catalog editor imports or UI controls for hybrid or shortcut node kinds.

#### Scenario: Stale server data appears
- **WHEN** a stale API response includes an unknown node kind
- **THEN** the frontend MUST render a controlled unsupported-node state
- **AND** it MUST NOT silently treat it as point-capable content.

### Requirement: Admin feature imports reveal ownership
Admin feature modules SHALL import API clients and types from explicit ownership paths rather than catch-all barrels.

#### Scenario: Feature API import is reviewed
- **WHEN** a feature module needs backend data
- **THEN** it MUST import from a domain API module or shared HTTP/auth module with a specific file path
- **AND** it MUST NOT import from a global API index that obscures domain ownership.

### Requirement: Large admin feature pages split by responsibility
Admin feature pages SHALL be decomposed by stable responsibilities before new feature behavior is added to them.

#### Scenario: Large feature page is refactored
- **WHEN** a large feature page is split
- **THEN** route-level page code MUST remain a composition boundary
- **AND** data hooks, pure mappers, forms/modals, list/table display, and feature-specific helpers MUST move to explicit owner modules.

#### Scenario: New behavior is added to a large feature
- **WHEN** a new behavior is added to a feature that already has extracted owners
- **THEN** the change MUST land in the narrowest relevant owner module
- **AND** it MUST NOT re-expand the route-level page into a monolith.

### Requirement: Admin structural refactors keep lazy route boundaries
Admin frontend structural refactors SHALL preserve route-level lazy loading unless a deliberate performance change is specified.

#### Scenario: Production build is inspected
- **WHEN** admin production build and build report run after a structural refactor
- **THEN** large feature dependencies MUST remain behind lazy route chunks
- **AND** the app shell MUST NOT newly import experiments, media, question-bank, analytics, or learning-assistant feature code eagerly.

### Requirement: Admin shell refactors are destructive and canonical
Teacher/admin maintainability SHALL prefer canonical app ownership over compatibility wrappers when moving shell responsibilities.

#### Scenario: App shell is moved
- **WHEN** the admin shell is moved into `src/app/*`
- **THEN** the old root `App.tsx` owner MUST be deleted
- **AND** no compatibility re-export MUST be kept solely to preserve the old internal path.

#### Scenario: Admin shell code is reviewed
- **WHEN** reviewers inspect app-level admin code
- **THEN** provider/theme, auth guard/login, route registry, nav model, sidebar/header, and route outlet responsibilities MUST be identifiable by file path
- **AND** feature pages MUST remain separate from global shell ownership.

### Requirement: Admin frontend is audited but not refactored in backend slim pass
The backend slim architecture change SHALL include a teacher/admin frontend maintainability audit without performing admin frontend module restructuring.

#### Scenario: Admin frontend audit is produced
- **WHEN** the backend slim refactor is complete
- **THEN** implementation notes MUST identify oversized admin feature pages, monolithic API areas, route-shell coupling, backend endpoint assumptions, and recommended follow-up changes.

#### Scenario: Admin frontend structure is not optimized in this pass
- **WHEN** this backend slim change is implemented
- **THEN** admin frontend code MUST NOT be broadly reorganized into new feature/API module architecture as part of this change
- **AND** admin frontend edits MUST be limited to endpoint updates, test updates, and minimal fixes required by backend canonical route cleanup.

#### Scenario: Admin frontend follow-up is actionable
- **WHEN** the audit identifies frontend maintainability problems
- **THEN** the audit MUST group follow-up recommendations by feature owner, expected risk, and verification gate.

### Requirement: Intelligent monitoring feature boundary
The admin frontend SHALL implement the intelligent monitoring page as route-local modules, hooks, mappers, and styles rather than a single large behavior-owning page component.

#### Scenario: Developer changes OpenAI monitoring UI
- **WHEN** a developer changes provider health, recent request summary, connectivity labels, or OpenAI usage metrics on the monitoring page
- **THEN** the change MUST be localized to an OpenAI monitoring module, route-local mapper, or route-local data hook
- **AND** it MUST NOT require editing ES retrieval, dictionary/outbox, guardrail, or trend modules.

#### Scenario: Developer changes RAG monitoring UI
- **WHEN** a developer changes BGE runtime, warmup, model load, memory, latency, or retrieval/rerank count display
- **THEN** the change MUST be localized to a RAG monitoring module, route-local mapper, or route-local data hook
- **AND** it MUST NOT require editing OpenAI provider health or ES query workbench UI.

#### Scenario: Developer changes ES retrieval diagnostics UI
- **WHEN** a developer changes query input, normalized term display, recall route display, ranked result display, or raw diagnostic disclosure
- **THEN** the change MUST be localized to an ES retrieval workbench module and shared search-diagnostic mappers
- **AND** it MUST NOT require editing safety guardrail, usage trend, or provider credential code.

#### Scenario: Developer changes dictionary or outbox diagnostics UI
- **WHEN** a developer changes dictionary category counts, analyzer asset display, mapping version state, document counts, sync status counts, or retry/readiness presentation
- **THEN** the change MUST be localized to dictionary/outbox monitoring modules and mappers
- **AND** it MUST NOT require editing the query workbench result renderer.

#### Scenario: Route-level page code is reviewed
- **WHEN** reviewers inspect the intelligent monitoring route page
- **THEN** the route page MUST primarily compose data hooks and module components
- **AND** it MUST NOT contain all module markup, status mapping, chart mapping, query diagnostic rendering, and CSS class orchestration in one monolithic component.

### Requirement: Intelligent monitoring validation is focused
The admin frontend SHALL verify the monitoring UX with type, build, behavior, and visual checks appropriate to a dense operational page.

#### Scenario: Automated frontend validation runs
- **WHEN** implementation of this UX refactor is complete
- **THEN** teacher frontend typecheck and production build MUST pass
- **AND** any new or changed production chunk warning MUST be documented as accepted or targeted for follow-up.

#### Scenario: Component or mapper tests run
- **WHEN** monitoring modules or mappers are extracted
- **THEN** focused tests MUST cover health tone mapping, attention item generation, query diagnostic term rendering, route/result mapping, and empty/error state behavior where feasible.

#### Scenario: Browser or screenshot QA runs
- **WHEN** visual QA validates the intelligent monitoring page
- **THEN** it MUST capture or inspect the overview and at least the ES retrieval, dictionary/outbox, and RAG modules at normal desktop width
- **AND** it MUST capture or inspect the overview and ES retrieval module at narrow laptop width to verify no text overlap or unusable horizontal clipping.

#### Scenario: Existing route lazy loading is checked
- **WHEN** the production build is inspected after the refactor
- **THEN** the monitoring route and chart dependencies MUST remain behind the existing lazy route boundary
- **AND** unrelated teacher routes MUST NOT newly import monitoring-only modules eagerly.

### Requirement: Catalog content editor layout refinements remain feature-local
The admin frontend SHALL keep point content editor layout refinements inside catalog-tree owned modules and styles without changing backend contracts or creating a parallel editor model.

#### Scenario: Developer changes point content form layout
- **WHEN** a developer updates teacher-only note, experiment principle, reaction-equation presentation, phenomenon explanation, or safety note layout
- **THEN** the implementation MUST remain localized to catalog-tree selected-node editor components, catalog content mappers where needed, and catalog-tree feature CSS
- **AND** it MUST NOT require broad admin shell changes, global Ant Design overrides, backend API changes, or new dependencies.

#### Scenario: Developer compacts reaction equation presentation
- **WHEN** a developer changes the visible layout of the reaction-equation input, preview, AI action, or suggestion list
- **THEN** the implementation MUST preserve existing preview, AI assistance, suggestion application, hydration, autosave, and save payload behavior
- **AND** verification MUST include focused catalog editor checks such as contract tests, typecheck, or equivalent browser QA.
