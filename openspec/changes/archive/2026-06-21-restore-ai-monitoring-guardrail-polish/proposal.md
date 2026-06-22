## Why

The `AI/RAG/ES 监控` refactor preserved the modular console, but the `安全护栏` module lost its dedicated visual treatment during component extraction. The old guardrail radar, flow, and layer styles still exist in CSS, yet the current module renders as generic metric cards and was not covered by screenshot QA.

## What Changes

- Restore the safety guardrail module's purpose-built visual structure while keeping the tabbed monitoring architecture.
- Reconnect the existing guardrail radar, policy pipeline, risk metrics, coverage layers, and outcome distribution styles.
- Keep OpenAI, RAG, ES, dictionary/outbox, and trend modules on the new compact monitoring layout unless QA shows a concrete regression.
- Add focused visual QA coverage for `安全护栏`, and include `调用趋势` as a low-risk screenshot check because it was also absent from the previous QA set.
- Preserve existing API contracts, feature-switch behavior, provider settings boundaries, and teacher-only diagnostic access.

## Capabilities

### New Capabilities
- `monitoring-visual-regression-coverage`: Defines visual regression expectations for the AI/RAG/ES monitoring console modules that were not fully covered by the prior refactor QA.

### Modified Capabilities
- None.

## Impact

- Affected frontend code:
  - `apps/web-teacher/src/features/ai-config/GuardrailModule.tsx`
  - `apps/web-teacher/src/features/ai-config/ai-config.css`
- Affected verification artifacts:
  - OpenSpec tasks and screenshot QA for guardrail and trend modules.
- No backend API, database, dependency, or runtime contract changes are expected.
