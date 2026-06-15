## Why

The imported default question bank is now fully point-aware, evidence-audited, and option-linked, but the admin console still presents the bank primarily as a theory-chapter list. Teachers need a release-ready interface that matches the new experiment point model and exposes the diagnostic value without showing internal rebuild metadata.

## What Changes

- Make the question bank management page experiment-first, with point-aware counts, point filters, evidence status, and readable question detail.
- Preserve the existing admin console style, modal workflow, and read-only question browsing model.
- Surface canonical/source evidence and option-level diagnostic links in question detail.
- Update weak-point analytics presentation to prioritize experiment video points and selected wrong-option diagnostics.
- Fix the backend weak-point endpoint so point-aware analytics data can be returned reliably.
- Keep the old chapter-first endpoints available for compatibility, but move the primary UI path to the point-aware experiment/question APIs.

## Capabilities

### New Capabilities

### Modified Capabilities
- `experiment-question-bank-management`: Teacher browsing SHALL support the imported point-aware default bank as an experiment and point oriented workspace.
- `class-learning-analytics`: Teacher analytics SHALL present point-aware weak experiment points and option diagnostics in a readable interface.

## Impact

- `server/app/experiment_admin.py` analytics endpoint.
- `apps/admin-web/src/api.ts` question/analytics typing.
- `apps/admin-web/src/App.tsx` question bank and analytics pages.
- Existing Ant Design layout and styling classes in the admin web app.
