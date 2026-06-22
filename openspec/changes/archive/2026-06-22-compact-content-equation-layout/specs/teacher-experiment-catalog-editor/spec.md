## ADDED Requirements

### Requirement: Point content form uses compact grouped authoring layout
The teacher catalog editor SHALL present point knowledge content as a compact grouped form while preserving existing chemical-equation authoring behavior.

#### Scenario: Teacher opens point knowledge content
- **WHEN** a teacher opens the `知识内容` panel for a point node
- **THEN** the form MUST visually group teacher-only note, experiment principle, and student-facing content as related authoring sections
- **AND** the teacher-only note MUST remain visibly secondary to student-facing point knowledge.

#### Scenario: Teacher edits equation principle mode
- **WHEN** the point principle mode is `化学方程式`
- **THEN** the editor MUST keep the existing natural multiline reaction input, debounced backend preview, AI assistance, suggestion adoption, inline annotation display, and autosave behavior
- **AND** the visible equation area MUST be compact enough that phenomenon explanation and safety note remain easy to reach in the same form.

#### Scenario: Principle controls render
- **WHEN** the experiment principle section is visible
- **THEN** the `化学方程式` / `文字描述` mode selector MUST be placed with the experiment-principle section heading or equivalent section controls
- **AND** the AI equation action MUST be placed with that same section control area when chemical-equation mode is active.

#### Scenario: Equation preview contains many rows
- **WHEN** backend preview returns multiple normalized reaction rows or AI candidates
- **THEN** the editor MUST keep row order visible and preserve per-row candidate adoption actions
- **AND** the preview area MUST use bounded scrolling or an equivalent compact treatment instead of expanding without limit and pushing the student-facing prose fields far down the page.

#### Scenario: Teacher edits student-facing prose
- **WHEN** the teacher edits `现象解释` or `安全提示`
- **THEN** both fields MUST remain textarea controls suitable for longer prose
- **AND** the fields MUST be presented as a coherent student-facing content group that can use two columns on wide surfaces and stack on constrained surfaces.

#### Scenario: Edit-content modal reuses the form
- **WHEN** the teacher opens the reused `编辑内容` modal
- **THEN** the modal MUST use the same content editing behavior as the main `知识内容` panel
- **AND** the layout MUST adapt without relying on sticky equation panes or oversized workbench spacing that would crowd the modal viewport.

### Requirement: Principle mode switching protects existing content
The teacher catalog editor SHALL require explicit confirmation before switching experiment principle mode when the current mode already contains authored content.

#### Scenario: Teacher switches away from equation content
- **WHEN** the current principle mode is `化学方程式`
- **AND** the reaction equation input contains non-empty content
- **AND** the teacher attempts to switch to `文字描述`
- **THEN** the editor MUST show a confirmation dialog explaining that current chemical-equation content will be cleared and only the selected mode will be saved
- **AND** it MUST NOT change the principle mode or autosave the mode switch unless the teacher confirms.
- **AND** the confirmation action MUST be visually marked as dangerous with the label `确认切换`, while the cancel action MUST use the label `放弃切换`.

#### Scenario: Teacher switches away from text principle content
- **WHEN** the current principle mode is `文字描述`
- **AND** the text principle field contains non-empty content
- **AND** the teacher attempts to switch to `化学方程式`
- **THEN** the editor MUST show a confirmation dialog explaining that current text content will be cleared and only the selected mode will be saved
- **AND** it MUST NOT change the principle mode or autosave the mode switch unless the teacher confirms.
- **AND** the confirmation action MUST be visually marked as dangerous with the label `确认切换`, while the cancel action MUST use the label `放弃切换`.

#### Scenario: Teacher switches from an empty mode
- **WHEN** the current principle mode has no authored content
- **AND** the teacher switches to the other principle mode
- **THEN** the editor MAY switch immediately without confirmation
- **AND** it MUST continue to save only the active principle mode.
