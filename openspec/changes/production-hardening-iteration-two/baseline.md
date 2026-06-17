## Baseline: 2026-06-17

Branch and remote:

- Current branch: `codex/productionize-admin-platform`
- Remote branch: `origin/codex/productionize-admin-platform`
- Baseline commit after proposal: `a91d4dc`
- Working tree was clean before baseline validation.

Validation command:

```powershell
python scripts/validate_production_readiness.py --change production-hardening-iteration-two
```

Result:

- PASS: protected resource manifest
- PASS: OpenSpec strict validation for `production-hardening-iteration-two`
- PASS: admin app import smoke
- PASS: backend tests, `44 passed`
- PASS: frontend typecheck
- PASS: frontend tests, `7 passed`
- PASS: frontend build

Known warnings captured by the baseline:

- `server/app/admin_main.py` still emits FastAPI `on_event` deprecation warnings during backend tests.
- `server/app/bge_service.py` also contains an `on_event` startup hook and must be migrated with the admin app.
- Frontend build still reports Vite chunks above 500 KB.

Largest current frontend JavaScript assets:

| Asset | Size |
| --- | ---: |
| `index-CKilTYL0.js` | 1,483,447 bytes |
| `index-D_pOLKV3.js` | 949,886 bytes |
| `index-DffE8MKe.js` | 463,331 bytes |
| `Table-D-2jkno8.js` | 196,414 bytes |
| `index-DFNaWixP.js` | 71,176 bytes |
| `index-Dwh0ALlb.js` | 69,178 bytes |

Initial chunk ownership signals from string scanning:

| Asset | Likely dependency family / owner |
| --- | --- |
| `index-CKilTYL0.js` | Charts / G2 plotting stack |
| `index-D_pOLKV3.js` | Mixed app shell/vendor: Ant Design, React DOM, React Router, dayjs, motion, upload/tus traces |
| `index-DffE8MKe.js` | Markdown/math rendering: KaTeX, remark, react-markdown, plus upload/chart traces |
| `Table-D-2jkno8.js` | Ant Design table-related chunk with motion/upload traces |

Hardening guardrails:

- Do not change core seed resources, question data, knowledge framework data, canonical chunks, embeddings, or point evidence bindings.
- Do not change public API paths, authentication/authorization behavior, or existing request/response contracts.
- Do not delete `data/media` directly; media cleanup must account for `media_assets`, `media_bindings`, derived files, processing rows, and UI/API state.
- Do not rewrite existing migration history; future migrations continue from `014_...`.
