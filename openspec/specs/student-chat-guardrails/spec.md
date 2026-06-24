# student-chat-guardrails Specification

## Purpose
Define policy, retrieval, feature-switch, and student-facing presentation guardrails for the student learning assistant across H5 chat surfaces.
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
The student learning assistant SHALL treat RAG and platform evidence as helpful support for ordinary chemistry questions, not as a hard requirement, and SHALL use the retrieval decision layer to determine whether dynamic RAG is needed for each turn.

#### Scenario: Student asks a course-factual question
- **WHEN** the student asks an ordinary inorganic chemistry factual question
- **THEN** the assistant SHALL answer using available chemistry knowledge
- **AND** it SHALL use RAG evidence as supporting context only when the retrieval decision selects dynamic RAG and usable evidence is found.

#### Scenario: Student asks an ordinary explanation question
- **WHEN** the student asks for a concept explanation, mechanism explanation, equation derivation, safe reasoning path, or short follow-up without requesting platform evidence
- **THEN** the assistant SHALL allow the retrieval decision to skip dynamic RAG
- **AND** it SHALL still answer from reliable model chemistry knowledge when a model is configured.

#### Scenario: RAG is disabled or has no match
- **WHEN** RAG lookup is disabled or no suitable evidence is found for an ordinary course-factual question
- **THEN** the assistant SHALL still answer from reliable model chemistry knowledge when a model is configured
- **AND** it SHALL NOT claim that the answer came from platform evidence.

#### Scenario: Explicit evidence request is received
- **WHEN** the student asks for a citation, source, textbook wording, source figure, evidence image, course material reference, or answer according to platform material
- **THEN** the assistant SHALL require evidence through fixed point evidence, dynamic RAG, or strict evidence handling
- **AND** it SHALL NOT provide an unsupported platform-evidence claim when no usable evidence is found.

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
The student learning assistant SHALL fall back to deterministic local policy and deterministic retrieval routing when the optional model policy gate is unavailable or invalid.

#### Scenario: Policy gate is unavailable
- **WHEN** the optional model policy gate raises an error or is not configured
- **THEN** the assistant SHALL continue with the local student policy classification
- **AND** risky requests SHALL still be refused or converted to hints according to local policy
- **AND** retrieval routing SHALL use deterministic local fallback rather than defaulting to dynamic RAG for every turn.

#### Scenario: Policy gate returns invalid structured output
- **WHEN** the optional model policy gate returns malformed JSON, an unknown mode, an unknown retrieval mode, or another invalid policy decision
- **THEN** the assistant SHALL record an invalid policy decision guardrail or diagnostic
- **AND** it SHALL continue with the local student policy classification and deterministic retrieval routing instead of treating the request as a normal always-RAG answer.

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
The student H5 assistant SHALL present a direct mobile chat shell, model answers, optional point context, chat status, history entry, and source summaries in a student-readable form while preserving existing student guardrail enforcement.

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

#### Scenario: Student chat starts from global AI root
- **WHEN** a student opens the assistant from the bottom navigation without a current chapter, experiment, or point handoff
- **THEN** the `/ai` root page MUST render a direct composer-first chat shell using the default `learning_home` context
- **AND** the student MUST be able to type and send a course question without first choosing a prompt, point, model, attachment, or voice option.

#### Scenario: Student chat starts from point or page context
- **WHEN** a student opens the assistant from a property section, experiment point, video result, chapter, or assessment report
- **THEN** the `/ai/chat` detail page MUST include the selected context in the request where available
- **AND** the active context MUST be visible and dismissible rather than trapping the student in that point
- **AND** the page MUST use contextual detail-page chrome instead of the `/ai` root history chrome.

#### Scenario: Unsupported generic AI controls are absent
- **WHEN** the student views either the root AI chat shell or contextual AI chat detail page
- **THEN** the UI MUST NOT show attachment upload, model selection, or voice-input controls
- **AND** all visible controls MUST map to implemented student assistant behavior.

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

### Requirement: Follow-up prompt guardrails
The student learning assistant SHALL apply student-facing safety, assessment, and course-scope guardrails to generated follow-up prompt suggestions.

#### Scenario: Suggestions are generated from in-scope context
- **WHEN** the backend generates follow-up prompt suggestions for a successful student assistant answer
- **THEN** the suggestion-generation context MUST include the active student assistant context, the latest student question, the completed assistant answer, and recent conversation history
- **AND** it MUST NOT include teacher/admin diagnostics, raw retrieval traces, policy internals, or hidden answer keys.

#### Scenario: Suggestions stay within course scope
- **WHEN** follow-up prompt suggestions are attached to the student assistant final response
- **THEN** each suggestion MUST be a student-facing inorganic chemistry experiment learning follow-up or a safe learning-strategy follow-up for the active context
- **AND** suggestions MUST NOT direct the student toward unrelated entertainment, finance, personal advice, or other out-of-course topics.

#### Scenario: Suggestions avoid unsafe experiment operations
- **WHEN** follow-up prompt suggestions relate to experiment practice or safety
- **THEN** they MUST avoid soliciting hazardous unsupervised operation steps
- **AND** they MAY ask about safety principles, observation cues, or teacher-supervised lab precautions.

#### Scenario: Suggestions avoid direct assessment answers
- **WHEN** the active context or recent conversation relates to a quiz, pretest, posttest, exam, or mistake review
- **THEN** generated suggestions MUST NOT ask Atom to directly reveal an answer choice or final answer
- **AND** they SHOULD ask for hints, reasoning steps, misconception analysis, or review priorities.

#### Scenario: Invalid suggestions are removed
- **WHEN** a generated suggestion violates student guardrails, exposes diagnostics, asks for direct answers, or is not student-readable
- **THEN** the backend MUST remove that suggestion before returning `suggested_prompts`
- **AND** the backend MUST NOT replace it with a static frontend fallback prompt.

### Requirement: Retrieval routing remains separate from safety guardrails
The student learning assistant SHALL keep safety, assessment, and course-scope guardrails separate from retrieval routing while allowing retrieval decisions to be recorded for diagnostics.

#### Scenario: Safety refusal is selected
- **WHEN** the student asks for unsafe experiment operation details
- **THEN** the safety guardrail SHALL decide the refusal behavior
- **AND** retrieval routing SHALL NOT run dynamic RAG to produce unsafe operation steps.

#### Scenario: Assessment hint is selected
- **WHEN** the student asks for a direct quiz, test, exam, or assignment answer
- **THEN** the assessment guardrail SHALL convert the turn to learning guidance or hints
- **AND** retrieval routing SHALL NOT override that policy into a direct grounded answer.

#### Scenario: Retrieval decision is diagnostic
- **WHEN** the backend records a retrieval decision for a student assistant turn
- **THEN** diagnostics SHALL include that decision for teacher/operator inspection where assistant turn diagnostics are exposed
- **AND** student-facing chat surfaces MUST NOT display raw retrieval mode names, policy codes, confidence values, or tool internals.

