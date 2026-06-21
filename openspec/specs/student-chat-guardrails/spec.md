# student-chat-guardrails Specification

## Purpose
TBD - created by archiving change student-chat-guardrails. Update Purpose after archive.
## Requirements
### Requirement: Student chat policy scope
The student learning assistant SHALL apply guardrails only to student learning-page chat requests and SHALL NOT change teacher AI workflows.

#### Scenario: Student chat request is processed
- **WHEN** a learning assistant request is executed as `user_role="student"`
- **THEN** the system SHALL classify the request against the student AI policy
- **AND** the response SHALL include policy version, classification, guardrail decisions, tool calls, sources, and final mode.

#### Scenario: Teacher AI workflow is used
- **WHEN** a teacher uses question-bank assistant, teacher analytics, or another teacher AI workflow
- **THEN** the student chat guardrails SHALL NOT be required for that workflow
- **AND** the workflow SHALL continue to use its existing teacher-facing AI behavior.

### Requirement: Course-scope refusal
The student learning assistant SHALL refuse requests that are outside inorganic chemistry experiment learning scope.

#### Scenario: Student asks an unrelated question
- **WHEN** the student asks for advice unrelated to the course, such as financial, entertainment, or general life advice
- **THEN** the assistant SHALL refuse with a course-scope explanation
- **AND** it SHALL NOT call learning tools or produce the requested unrelated answer.

### Requirement: Unsafe experiment-detail refusal
The student learning assistant SHALL refuse unsafe experiment-operation detail requests while allowing safe conceptual or teacher-supervised safety guidance.

#### Scenario: Student asks for hazardous home experiment steps
- **WHEN** the student asks for detailed steps to perform hazardous chemistry outside supervised teaching conditions
- **THEN** the assistant SHALL refuse to provide actionable operation steps
- **AND** it SHALL redirect to safety principles or supervised-lab guidance.

### Requirement: Assessment answer protection
The student learning assistant SHALL avoid giving direct answers to assessments and SHALL provide learning hints instead.

#### Scenario: Student asks for a direct test answer
- **WHEN** the student asks the assistant to directly answer a quiz, pretest, posttest, exam, or assignment item
- **THEN** the assistant SHALL avoid revealing the direct answer
- **AND** it SHALL provide a hint, reasoning path, or relevant knowledge-point guidance.

### Requirement: RAG-assisted course answering
The student learning assistant SHALL treat RAG and platform evidence as helpful support for ordinary chemistry questions, not as a hard requirement.

#### Scenario: Student asks a course-factual question
- **WHEN** the student asks an ordinary inorganic chemistry factual question
- **THEN** the assistant SHALL answer using available chemistry knowledge
- **AND** it SHALL use RAG evidence as supporting context when evidence is enabled and found.

#### Scenario: RAG is disabled or has no match
- **WHEN** RAG lookup is disabled or no suitable evidence is found for an ordinary course-factual question
- **THEN** the assistant SHALL still answer from reliable model chemistry knowledge when a model is configured
- **AND** it SHALL NOT claim that the answer came from platform evidence.

### Requirement: Platform resource grounding
The student learning assistant SHALL require platform lookup only for claims about published platform resource availability, playback, download, or upload status.

#### Scenario: Student asks for a published resource
- **WHEN** the student asks whether a video, file, link, download, or platform material has been uploaded, published, or is available to watch
- **THEN** the assistant SHALL only report ready and published resources found by platform lookup
- **AND** it SHALL state unavailable when no matching published resource exists.

#### Scenario: Student asks to explain a video point
- **WHEN** the student asks to explain a current video point, experiment phenomenon, source figure, or material content
- **THEN** the assistant SHALL treat the request as a learning answer
- **AND** it SHALL NOT route the request to platform resource availability solely because the words "video", "material", or "resource" appear.

#### Scenario: Student asks about an evidence image or figure
- **WHEN** the student asks what a source figure, evidence image, or figure-backed point shows
- **THEN** the assistant SHALL keep the request on the learning evidence rail
- **AND** it SHALL NOT treat the request as a platform resource availability query unless the student explicitly asks whether an uploaded platform resource exists.

#### Scenario: No published resource exists
- **WHEN** a true platform-resource availability query finds no ready and published resources
- **THEN** the assistant SHALL answer with the factual unavailable state
- **AND** the turn SHALL NOT be presented as an unsafe or out-of-course refusal.

### Requirement: Feature-switch enforcement
The student learning assistant SHALL respect student AI feature switches.

#### Scenario: Student AI assistant is disabled
- **WHEN** the student AI assistant entry switch is disabled
- **THEN** the admin test endpoint SHALL reject learning assistant test requests
- **AND** it SHALL NOT invoke the agent.

#### Scenario: Student RAG access is disabled
- **WHEN** student RAG access is disabled
- **THEN** learning assistant requests SHALL execute without RAG lookup permission
- **AND** the guardrail diagnostics SHALL record that RAG lookup was disabled when relevant.

### Requirement: Policy gate fail-closed fallback
The student learning assistant SHALL fall back to deterministic local policy when the optional model policy gate is unavailable or invalid.

#### Scenario: Policy gate is unavailable
- **WHEN** the optional model policy gate raises an error or is not configured
- **THEN** the assistant SHALL continue with the local student policy classification
- **AND** risky requests SHALL still be refused or converted to hints according to local policy.

#### Scenario: Policy gate returns invalid structured output
- **WHEN** the optional model policy gate returns malformed JSON, an unknown mode, or another invalid policy decision
- **THEN** the assistant SHALL record an invalid policy decision guardrail
- **AND** it SHALL continue with the local student policy classification instead of treating the request as a normal answer.

### Requirement: H5 student assistant endpoint guardrails
Student H5 assistant APIs SHALL use the existing student chat guardrail policy and feature-switch behavior.

#### Scenario: Student asks from learning page
- **WHEN** an authenticated student sends a learning-page assistant request from the H5 app
- **THEN** the backend SHALL process it as a student learning assistant request
- **AND** it SHALL apply the existing student policy classification, assessment-answer protection, resource grounding, and feature switches.

#### Scenario: Student AI feature is disabled
- **WHEN** the student AI assistant switch is disabled
- **THEN** H5 assistant endpoints SHALL reject assistant generation
- **AND** they SHALL NOT invoke the agent model.

### Requirement: Submitted posttest review scope
The student assistant SHALL only explain posttest mistakes from the authenticated student's submitted completed posttest data.

#### Scenario: Student requests posttest mistake help
- **WHEN** a student requests posttest mistake explanations
- **THEN** the backend SHALL scope explanations to that student's completed submitted answers
- **AND** it SHALL avoid revealing direct answers for unrelated assessment items.

### Requirement: Context-aware policy classification
The student learning assistant SHALL classify policy decisions using resolved multi-turn context, not only the latest raw question text.

#### Scenario: Short follow-up inherits prior course context
- **WHEN** the student asks a short follow-up such as "why", "this one?", or "explain the second point" after an in-scope chemistry answer
- **THEN** the policy gate SHALL evaluate the request against the prior course topic and structured context
- **AND** it SHALL NOT refuse the request solely because the latest text is ambiguous.

#### Scenario: Structured point context guides policy
- **WHEN** a request includes `chapter_id`, `experiment_id`, or `point_key`
- **THEN** the policy gate SHALL receive those fields or an equivalent resolved question
- **AND** ordinary point explanation SHALL be classified as a normal learning answer unless another safety or assessment rule applies.

#### Scenario: Risky follow-up still protected
- **WHEN** a follow-up asks for unsafe experiment steps or direct assessment answers
- **THEN** the safety or assessment guardrail SHALL still apply
- **AND** inherited context SHALL NOT override the risky-request policy.

### Requirement: Student H5 assistant presentation
The student H5 assistant SHALL present starter guidance, model answers, point context, chat status, and source summaries in a student-readable form while preserving existing student guardrail enforcement.

#### Scenario: Student chat renders chemistry answer
- **WHEN** the student assistant streams a markdown or chemistry-formatted answer
- **THEN** the H5 app MUST render the answer with markdown-compatible formatting
- **AND** it MUST support student-facing chemistry notation used elsewhere in the student H5, including formulas rendered by the shared student markdown or equivalent chemistry renderer
- **AND** it MUST keep the streaming fallback behavior for plain text answers.

#### Scenario: Student chat receives final response metadata
- **WHEN** the student assistant stream emits a final response with sources
- **THEN** the H5 app MUST retain the final response metadata for that turn
- **AND** it MUST show a compact source or evidence summary suitable for students
- **AND** it MUST NOT show raw retrieval traces, rerank scores, guardrail arrays, runtime health, or JSON diagnostics in the student chat surface.

#### Scenario: Student chat starts from global context
- **WHEN** a student opens the assistant from the bottom navigation without a current chapter, experiment, or point handoff
- **THEN** the H5 app MUST submit assistant requests with a valid `learning_home` context
- **AND** the page MUST provide starter guidance for ordinary course questions before the first turn.

#### Scenario: Student chat starts from point context
- **WHEN** a student opens the assistant from a property section or experiment point
- **THEN** the H5 app MUST include the selected chapter, experiment, point, and context summary in the request
- **AND** quick prompts or starter intents MUST be relevant to the active property or point
- **AND** the active context MUST be visible and dismissible rather than trapping the student in that point.

#### Scenario: Student chat shows streaming progress
- **WHEN** the student assistant request is running and no final answer has arrived
- **THEN** the H5 app MUST show an in-chat running state near the active assistant turn
- **AND** the running state MUST use student-readable language such as checking scope, looking up course material, or generating an answer
- **AND** it MUST fall back to a generic generating state when stream status text is unavailable.

#### Scenario: Student chat handles failure
- **WHEN** a student assistant request fails
- **THEN** the H5 app MUST show the failure in the active chat turn or composer area
- **AND** the student MUST remain able to edit or send another question without reloading the page.

#### Scenario: Student AI switch is disabled
- **WHEN** student AI entry or student AI capability is disabled by admin settings
- **THEN** the H5 app MUST hide or disable the student assistant entry after app-config refresh
- **AND** the backend MUST continue to reject stale student assistant requests.

