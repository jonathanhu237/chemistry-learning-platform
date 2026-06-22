## Context

The current `AI/RAG/ES 监控` route is already split into route-local modules under `apps/web-teacher/src/features/ai-config`. The previous refactor intentionally replaced the long dashboard with compact module tabs, but the safety guardrail tab regressed further than intended: `GuardrailModule.tsx` now uses generic metric tiles while the old dedicated `.ai-guardrail-*` and `.ai-policy-rail-*` styles still remain in `ai-config.css`.

The prior QA set captured overview, ES, dictionary/outbox, and RAG screens. It did not capture `安全护栏` or `调用趋势`, which left the guardrail visual regression invisible.

## Goals / Non-Goals

**Goals:**

- Restore the safety guardrail module's dedicated radar, policy flow, metric, layer, and outcome presentation.
- Preserve the modular monitoring architecture and tab navigation introduced by the refactor.
- Keep the restored module compact enough for the current monitoring page and responsive at narrow laptop widths.
- Add verification for the previously uncovered guardrail and trend tabs.

**Non-Goals:**

- Do not revert the full AI/RAG/ES monitoring refactor.
- Do not restore the old single-page dashboard layout.
- Do not change AI, RAG, ES, dictionary, outbox, or student guardrail backend behavior.
- Do not reintroduce provider credential or feature-switch editing into the monitoring page.

## Decisions

### 1. Reuse the existing guardrail CSS instead of inventing a new visual system

`ai-config.css` still contains the radar scan, policy pipeline, risk metrics, and policy rail styles. The implementation should reconnect `GuardrailModule.tsx` to those classes and only add small compatibility or responsive fixes where the module shell changed.

Alternative considered: redesign the guardrail module using the generic monitoring cards. That is the current regression and loses the strong visual distinction the user noticed.

### 2. Keep the module shell from the refactor

The restored guardrail content should remain inside the current `ai-monitor-module` tab content so navigation, loading behavior, and page spacing stay consistent with the refactored console.

Alternative considered: bring back the old Ant Design `Card` wrapper. That would fight the current route-local module layout and risk nested-card styling.

### 3. Treat other modules as QA targets, not restoration targets

OpenAI, RAG, ES, dictionary/outbox, and usage trend modules are intentionally using the new compact monitoring language. Only the guardrail module has strong evidence of a lost dedicated style path. The trend tab should be screenshot-checked because it was absent from prior QA, but no restoration is planned unless verification reveals a concrete issue.

Alternative considered: restore old OpenAI/RAG/usage panels. That would undo the spec-driven compact monitoring refactor without evidence that those areas are broken.

## Risks / Trade-offs

- [Risk] The old guardrail visual block may become too tall inside the tabbed module. -> Keep the module shell spacing compact and verify desktop and narrow laptop screenshots.
- [Risk] Restoring animated radar effects could be distracting. -> Preserve the existing `prefers-reduced-motion` guard already present in CSS.
- [Risk] Reusing old CSS may include stale responsive assumptions. -> Add module-scoped media rules for guardrail command, pipeline, metrics, layers, and radar sizes.
- [Risk] QA may require a running teacher console with backend data. -> Prefer existing dev/container setup if available, and fall back to typecheck plus documented screenshot limitations if runtime is unavailable.

## Migration Plan

1. Update `GuardrailModule.tsx` to render the dedicated guardrail visual structure using current policy data.
2. Add or adjust responsive CSS for the restored guardrail module inside the current monitoring page.
3. Run frontend typecheck and focused ai-config tests.
4. Capture or verify guardrail and trend tabs at desktop width, and guardrail at narrow width where possible.
5. Rollback is limited to reverting the guarded frontend files and this OpenSpec change.
