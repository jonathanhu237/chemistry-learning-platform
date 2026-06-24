## Why

Students currently have two assessment entry points, but the learning flow still has two gaps: first-time students are not guided to establish a smart-assessment baseline, and the point detail page's "测一测" action starts a full smart assessment instead of checking the point the student just studied.

This change makes baseline assessment guidance explicit and adds a point-scoped assessment mode so post-learning checks produce evidence for the specific catalog point.

## What Changes

- Add a third assessment mode, `point`, for point-scoped post-learning checks.
- Add a student assessment status API that reports smart-baseline completion, open assessment session state, and baseline prompt dismissal state.
- Add a backend dismissal action for the smart-baseline prompt.
- Change the point detail "测一测" flow to start a point-scoped assessment when no other assessment is open.
- Keep the existing one-open-assessment-per-student invariant; if any assessment is already in progress, point assessment entry reuses that open session and the UI explains that the existing assessment is being continued.
- Add a first-login baseline prompt that appears when the student has not completed a `smart` assessment and has not permanently dismissed the prompt.
- Preserve existing smart and custom assessment behavior and reports while allowing point assessment reports to reuse the shared session/report shell.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `student-h5-assessment-flow`: Adds point-scoped assessment sessions and smart-baseline onboarding prompts to the student assessment flow.

## Impact

- Backend student assessment APIs and schemas.
- Student smart assessment session domain logic and session metadata.
- Student H5 runtime shell and point detail route behavior.
- Student H5 e2e tests for baseline prompting and point assessment entry.
