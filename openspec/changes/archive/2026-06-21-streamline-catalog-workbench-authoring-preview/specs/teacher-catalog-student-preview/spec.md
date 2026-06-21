## ADDED Requirements

### Requirement: Teacher can preview the real student point experience
The platform SHALL let teachers preview a catalog point through a teacher-authorized, phone-sized rendering of the real student H5 point/detail experience.

#### Scenario: Teacher opens learning card preview
- **WHEN** an authenticated teacher selects a point node and clicks `预览学习卡片`
- **THEN** the system MUST open a phone-sized preview window or equivalent preview shell for that point
- **AND** the preview MUST render the student point/detail learning page rather than a teacher-side mock card.

#### Scenario: Directory preview is requested
- **WHEN** a teacher clicks preview while a directory node is selected
- **THEN** the system MUST either disable the preview action or open a controlled directory preview surface
- **AND** it MUST NOT show point-only video/detail controls for a directory.

#### Scenario: Preview route uses mobile constraints
- **WHEN** the preview window renders a point
- **THEN** the visible preview viewport MUST render inside a standard phone mockup/frame rather than an ad hoc teacher-side card
- **AND** the phone screen MUST use phone-oriented dimensions and styling consistent with the student H5 app
- **AND** the preview MUST fit common phone widths without horizontal scrolling.

#### Scenario: Teacher switches preview phone preset
- **WHEN** the teacher uses the preview shell's device selector
- **THEN** the system MUST offer only a curated set of standard phone presets such as modern iPhone, notched iPhone, legacy iPhone, and Android phone
- **AND** switching presets MUST update the preview frame and screen viewport without mutating point data or student learning data
- **AND** the selector MUST NOT expose freeform resizing, network throttling, user-agent editing, DOM inspection, or other debugging controls.

#### Scenario: Preview shell loads real student page
- **WHEN** the teacher preview shell displays a point inside the selected phone frame
- **THEN** the phone screen MUST load the teacher-authorized student preview route for that point
- **AND** the shell MAY use an iframe or equivalent embedded route
- **AND** the frame/CSP policy MUST allow only the expected internal preview origin when teacher and student apps are served from different origins.

### Requirement: Preview authorization is separate from student login
The preview flow SHALL be authorized by teacher/admin credentials without requiring a student account or creating a student session.

#### Scenario: Teacher preview token is created
- **WHEN** a teacher requests preview for a point node
- **THEN** the backend MUST verify teacher-console authorization
- **AND** it MUST mint a short-lived preview authorization scoped to that point node and preview purpose.

#### Scenario: Teacher opens student frontend directly
- **WHEN** a teacher opens the normal student point URL without a valid student token or preview authorization
- **THEN** the normal student authentication rules MUST still apply
- **AND** the system MUST NOT treat the teacher token as a student token.

#### Scenario: Preview token is reused outside scope
- **WHEN** a preview token is used for a different node, a non-preview endpoint, or after expiry
- **THEN** the backend MUST reject the request
- **AND** it MUST NOT leak point content, media URLs, teacher diagnostics, or student identity.

### Requirement: Preview payload matches student learning shape without student side effects
The preview API SHALL return point detail data compatible with the student point/detail renderer while preventing student-learning mutations.

#### Scenario: Preview point detail is loaded
- **WHEN** the preview page requests the selected point detail
- **THEN** the backend MUST return a payload compatible with the student point detail response shape
- **AND** the payload MUST include title, path context, video availability, principle content, phenomenon explanation, safety note, and related experiments where available.

#### Scenario: Draft or incomplete point is previewed
- **WHEN** a teacher previews a valid point that is draft, missing learning content, or missing video
- **THEN** the preview MUST render the same graceful placeholders expected by the student point page
- **AND** it MUST make the missing content visible without failing the preview route.

#### Scenario: Preview attempts student mutation
- **WHEN** preview mode reaches actions such as finish learning, start assessment, submit feedback, or open a real AI chat session
- **THEN** those actions MUST be disabled, hidden, or routed to a non-mutating preview notice
- **AND** no student progress, assessment session, feedback record, AI chat session, or analytics event MUST be created.

### Requirement: Preview media access is read-only and token scoped
Protected media displayed in preview SHALL use preview-scoped authorization instead of student media tokens.

#### Scenario: Preview renders a bound video
- **WHEN** the point has a previewable bound video
- **THEN** the preview MUST be able to load the video stream or thumbnail through preview-scoped media access
- **AND** the media access MUST be limited to the preview token's point scope and expiry.

#### Scenario: Preview media token is missing or expired
- **WHEN** the preview attempts to load video media without valid preview authorization
- **THEN** the media endpoint MUST reject the request
- **AND** the preview page MUST show a controlled unavailable media state.

### Requirement: Preview does not expose teacher diagnostics
The preview surface SHALL show student-facing learning content only.

#### Scenario: Preview renders point content
- **WHEN** a teacher previews a point
- **THEN** the preview MUST NOT expose teaching notes, raw node ids as primary copy, ES/RAG diagnostics, validation internals, evidence chunks, generated query traces, or backend job details.

#### Scenario: Teacher needs diagnostics
- **WHEN** the teacher wants node status, AI context, or advanced debug details
- **THEN** those details MUST be opened from the teacher diagnostic surface
- **AND** they MUST NOT appear inside the phone-sized student preview.
