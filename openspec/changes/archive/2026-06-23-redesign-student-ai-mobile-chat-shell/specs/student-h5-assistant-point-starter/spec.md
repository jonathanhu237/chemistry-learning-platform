## REMOVED Requirements

### Requirement: Point starter mode entry
**Reason**: The first-round AI root redesign makes direct composer-first chat the default and moves structured point selection out of the first-screen scope.
**Migration**: Students still ask point-aware questions from point/detail source pages through `/ai/chat`; a later change may reintroduce optional point starter controls without blocking free-form chat.

### Requirement: Student-visible experiment data loading
**Reason**: Loading experiment and point choices inside the AI root is deferred so the root chat shell can remain fast and focused.
**Migration**: Existing student-visible experiment APIs remain available for learning and point detail pages, and future optional starter work can reuse them.

### Requirement: Video point option derivation
**Reason**: The AI root no longer exposes a mandatory point-selection starter in this change.
**Migration**: Point option derivation can be re-added in a later optional starter change if product direction returns to AI-root point selection.

### Requirement: Point starter templates
**Reason**: Structured point templates are prompt/starter work and are not part of this first-round direct chat shell.
**Migration**: Contextual point pages continue to provide point-aware prompts or quick questions where appropriate.

### Requirement: Point starter preview and launch
**Reason**: Preview-and-launch starter behavior is no longer required before a student can chat from the AI root.
**Migration**: If optional starter templates return later, they must remain secondary to the direct composer and must make sent text unambiguous.

### Requirement: Point-aware assistant context construction
**Reason**: Point context construction inside the AI-root starter is deferred; point context now primarily enters chat from source pages.
**Migration**: Source pages that open `/ai/chat` must continue to pass available point, experiment, chapter, and context summary fields.

### Requirement: Point starter transition to normal chat
**Reason**: There is no mandatory AI-root point starter transition in this first-round design.
**Migration**: Normal chat transition behavior remains required for any future optional starter that sends a generated point question.
