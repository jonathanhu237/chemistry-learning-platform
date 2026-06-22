## 1. Guardrail Visual Restoration

- [x] 1.1 Compare the current `GuardrailModule.tsx` with the pre-refactor guardrail section and identify the reusable data mappings.
- [x] 1.2 Restore the guardrail-specific JSX structure inside the current monitoring module shell.
- [x] 1.3 Reconnect policy status, policy version, judgement model, decision counts, handled risk counts, invalid fallback counts, coverage layers, and outcome distribution to the restored structure.

## 2. Responsive Styling

- [x] 2.1 Add or adjust scoped CSS so the restored guardrail command, pipeline, metrics, layers, and radar wrap correctly in the current tabbed monitoring page.
- [x] 2.2 Confirm the restored guardrail module preserves reduced-motion handling and does not affect OpenAI, RAG, ES, dictionary/outbox, or trend module layouts.

## 3. Verification

- [x] 3.1 Run focused frontend checks for the ai-config monitoring code.
- [x] 3.2 Inspect or capture the `安全护栏` module at desktop and narrow laptop widths.
- [x] 3.3 Inspect or capture the `调用趋势` module at desktop width.
- [x] 3.4 Record verification results and mark the OpenSpec tasks complete.
