# Teacher workflow reconciliation map

Read-only comparison of current `main` with the approved behavior on `legacy`.

## Question withdrawal

Relevant legacy commits:

- `ea613df` adds published-question withdrawal and its route/UI flow.
- `e92b3d9` fixes republishing a withdrawn draft into the original question row.
- `a729e97` adds draft deletion, which is not required for the retained lifecycle.

Port only the behavior into the current `/api/admin/question-banks` owners and current Ant Design workbench. Keep disable separate.

Required hardening beyond the legacy implementation:

- lock the published source question before withdrawal so concurrent requests cannot create duplicate drafts;
- keep authoritative withdrawal provenance outside user-editable payload metadata, or validate it against generation metadata before republish;
- preserve current evidence-lineage and duplicate-risk gates for withdrawn drafts (legacy bypassed evidence lineage when `revoked_from_question_id` existed);
- republish must update the original question ID, and must verify that the source is still in the withdrawn state;
- draft listing should return active `draft` rows only;
- assessment selection already filters `status='published'`, so withdrawn rows leave the pool without deletion.

Expected current owners:

- `server/app/domains/questions/bank.py`
- `server/app/domains/questions/drafts.py`
- `server/app/api/admin/admin_question_banks.py`
- `apps/web-teacher/src/api/questionBank.ts`
- `apps/web-teacher/src/features/question-bank/QuestionBanksPage.tsx`
- focused question-bank/draft/workbench tests and route inventory.

## Element-family analytics

Relevant legacy commit: `e88bb39`.

Approved family mapping:

| Chapter | Family |
| --- | --- |
| CH13 | 卤族元素 |
| CH14 | 氧族元素 |
| CH15 | 氮族元素 |
| CH16 | 碳族元素 |
| CH17 | 硼族元素 |
| CH18 | 碱金属和碱土金属 |
| CH19 | 铜锌副族元素 |
| CH20 | d 区过渡金属元素 |
| CH21 | 镧系和锕系元素 |
| CH22 | 氢和稀有气体 |

Port the chapter/point-based grouping and point drilldown into current `server/app/domains/analytics/read_models.py`, retaining current `/api/admin` routes, reports, AI summaries and export. Improve on legacy by placing unknown/new chapters into one explicit `unmapped` group rather than silently using arbitrary parent titles. Update the current Analytics UI wording from “实验组” to “元素族” while retaining its drawers and table structure.

## Roster and catalog regression fixes

Relevant legacy commits:

- `af56b90`: report cross-class student-ID conflicts before roster import.
- `a5d7b25`: align initial/shared password validation with six-character seed defaults; current seed default length is six while current API/UI require eight.
- `02fd669`: archiving/deleting a class disables its roster entries, activated users and student mirrors, and revokes sessions. Renumber the legacy `042` migration above the new Home migrations.
- `bb51a85`: permit final placement archival only with explicit `archive_final_placement=true`; add the same confirmation in the current catalog editor.

Do not restore legacy class/catalog pages. Audit staged video-binding visibility against current catalog behavior after the Home recommendation/search changes settle.

## Paper and preview

- Keep System Settings as the global smart/custom strategy owner.
- Keep Class Settings as the per-class override/preview owner; do not add `/paper`.
- Keep the current self-provisioning hidden student preview; only add regression coverage if a legacy edge case is not already represented.
