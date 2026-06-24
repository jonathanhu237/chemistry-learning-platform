## MODIFIED Requirements

### Requirement: Teacher can preview the real student point experience
The platform SHALL let teachers preview a catalog directory or catalog point through a teacher-authorized, phone-sized rendering of the real student H5 catalog/detail experience.

#### Scenario: Teacher opens point preview
- **WHEN** an authenticated teacher selects a point node and clicks the student preview action
- **THEN** the system MUST open a phone-sized preview window or equivalent preview shell for that point
- **AND** the preview MUST render the student point/detail learning page rather than a teacher-side mock card.

#### Scenario: Teacher opens directory preview
- **WHEN** an authenticated teacher selects a directory node and clicks the student preview action
- **THEN** the system MUST open a phone-sized preview window or equivalent preview shell for that directory
- **AND** the preview MUST render the student catalog second-level directory page with that directory selected
- **AND** the visible directory preview MUST reuse the same second-level student catalog shell/component path used by the real student app, not an isolated catalog-node detail panel or teacher-side mock
- **AND** it MUST show directory children, point children, selected-directory state, path context, and counts using the same student H5 catalog layout conventions
- **AND** it MUST NOT show point-only video/detail controls for a directory.

#### Scenario: Preview route uses mobile constraints
- **WHEN** the preview window renders a catalog node
- **THEN** the visible preview viewport MUST render inside a standard phone mockup/frame rather than an ad hoc teacher-side card
- **AND** the phone screen MUST use phone-oriented dimensions and styling consistent with the student H5 app
- **AND** the preview MUST fit common phone widths without horizontal scrolling.

#### Scenario: Teacher switches preview phone preset
- **WHEN** the teacher uses the preview shell's device selector
- **THEN** the system MUST offer only a curated set of standard phone presets such as modern iPhone, notched iPhone, legacy iPhone, and Android phone
- **AND** switching presets MUST update the preview frame and screen viewport without mutating catalog data or student learning data
- **AND** the selector MUST NOT expose freeform resizing, network throttling, user-agent editing, DOM inspection, or other debugging controls.

#### Scenario: Preview shell loads real student page
- **WHEN** the teacher preview shell displays a catalog node inside the selected phone frame
- **THEN** the phone screen MUST load the teacher-authorized student preview route for that selected node
- **AND** the shell MAY use an iframe or equivalent embedded route
- **AND** the frame/CSP policy MUST allow only the expected internal preview origin when teacher and student apps are served from different origins.

#### Scenario: Catalog preview remains separate from full student sandbox
- **WHEN** the teacher opens catalog-tree preview for a directory or point
- **THEN** the preview MUST NOT bootstrap the full student-preview sandbox, student login flow, pretest gate, or complete student route history
- **AND** the full student-preview sandbox MUST remain the system used for whole-app student simulation.

### Requirement: Preview authorization is separate from student login
The preview flow SHALL be authorized by teacher/admin credentials without requiring a student account or creating a student session.

#### Scenario: Teacher preview token is created
- **WHEN** a teacher requests preview for a directory or point node
- **THEN** the backend MUST verify teacher-console authorization
- **AND** it MUST mint a short-lived preview authorization scoped to the selected catalog node and preview purpose
- **AND** the token scope MUST record whether the selected node is a directory or point.

#### Scenario: Directory preview token is used within subtree
- **WHEN** a valid directory preview token is used to load the selected directory or one of its descendant nodes
- **THEN** the backend MUST authorize the preview request
- **AND** it MUST preserve the same preview purpose and expiry for descendant navigation.

#### Scenario: Teacher opens student frontend directly
- **WHEN** a teacher opens the normal student catalog or point URL without a valid student token or preview authorization
- **THEN** the normal student authentication rules MUST still apply
- **AND** the system MUST NOT treat the teacher token as a student token.

#### Scenario: Preview token is reused outside scope
- **WHEN** a preview token is used for a different node outside the selected point or directory subtree, a non-preview endpoint, or after expiry
- **THEN** the backend MUST reject the request
- **AND** it MUST NOT leak catalog content, point content, media URLs, teacher diagnostics, or student identity.

### Requirement: Preview payload matches student learning shape without student side effects
The preview API SHALL return directory and point data compatible with the student catalog/detail renderers while preventing student-learning mutations.

#### Scenario: Preview directory node is loaded
- **WHEN** the preview page requests the selected directory
- **THEN** the backend MUST return a payload compatible with the student catalog second-level shell and selected-directory renderer
- **AND** the payload MUST include node kind, title, breadcrumb/path context, selected-directory context, child directories, child points, ordering, and child counts where available.
- **AND** the payload MUST include enough chapter learning context for the student second-level shell to render the correct family/element header without calling normal student learning endpoints or recording learning events.

#### Scenario: Preview point detail is loaded
- **WHEN** the preview page requests the selected point detail
- **THEN** the backend MUST return a payload compatible with the student point detail response shape
- **AND** the payload MUST include title, path context, video availability, principle content, phenomenon explanation, safety note, and related experiments where available.

#### Scenario: Draft or incomplete node is previewed
- **WHEN** a teacher previews a valid directory or point that is draft, missing learning content, or missing video
- **THEN** the preview MUST render the graceful placeholders expected by the corresponding student page
- **AND** it MUST make the missing content visible without failing the preview route.

#### Scenario: Preview attempts student mutation
- **WHEN** preview mode reaches actions such as finish learning, start assessment, submit feedback, open a real AI chat session, or write analytics
- **THEN** those actions MUST be disabled, hidden, or routed to a non-mutating preview notice
- **AND** no student progress, assessment session, feedback record, AI chat session, analytics event, or student session MUST be created.

### Requirement: Preview media access is read-only and token scoped
Protected media displayed in preview SHALL use preview-scoped authorization instead of student media tokens.

#### Scenario: Preview renders a bound video
- **WHEN** the selected point or a descendant point in a selected-directory preview has a previewable bound video
- **THEN** the preview MUST be able to load the video stream or thumbnail through preview-scoped media access
- **AND** the media access MUST be limited to the preview token's selected point or selected directory subtree scope and expiry.

#### Scenario: Preview media token is missing or expired
- **WHEN** the preview attempts to load video media without valid preview authorization
- **THEN** the media endpoint MUST reject the request
- **AND** the preview page MUST show a controlled unavailable media state.

### Requirement: Preview does not expose teacher diagnostics
The preview surface SHALL show student-facing learning content only.

#### Scenario: Preview renders catalog node content
- **WHEN** a teacher previews a directory or point
- **THEN** the preview MUST NOT expose teaching notes, raw node ids as primary copy, ES/RAG diagnostics, validation internals, evidence chunks, generated query traces, or backend job details.

#### Scenario: Teacher needs diagnostics
- **WHEN** the teacher wants node status, AI context, or advanced debug details
- **THEN** those details MUST be opened from the teacher diagnostic surface
- **AND** they MUST NOT appear inside the phone-sized student preview.

## ADDED Requirements

### Requirement: Catalog node preview has preview-local navigation
The catalog-tree preview SHALL provide local navigation for the selected node without depending on the full student sandbox route history.

#### Scenario: Teacher navigates inside a directory preview
- **WHEN** a directory preview displays child directories or child points authorized by the token
- **THEN** opening a child directory MUST show that directory inside the same preview shell
- **AND** opening a child point MUST show the point detail preview inside the same preview shell.

#### Scenario: Preview point returns to directory context
- **WHEN** a point preview was opened from a directory preview
- **THEN** the point/player back action MUST return to the originating directory preview
- **AND** it MUST NOT use a no-op back handler.

#### Scenario: Isolated preview root goes back
- **WHEN** the selected preview root has no preview-local parent in the current shell
- **THEN** the back action MUST ask the preview shell to close or use browser history fallback
- **AND** it MUST NOT silently do nothing.
