# `legacy` / `main` 产品统一技术设计

## 1. 设计目标

在 `main` 上完成一次可审计的语义合并，最终只保留：

- `apps/web-student`：当前绿色五栏学生 H5；
- `apps/web-teacher`：当前模块化教师端；
- `server`：两端共同使用的 API、任务和数据层；
- 一套在线教材处理与 RAG 向量投影。

`legacy` 是行为、修复和回归用例的来源，不是最终 UI 或运行时。最终删除 `apps/web-student-old`、`apps/web-teacher-old`、`apps/web-admin` 及其独立服务、路由、配置和运维文档。

## 2. Git 合并策略

### 2.1 为什么不能直接接受 Git 的自动结果

只读 `git merge-tree` 预演发现 21 个显式冲突，但自动合并树会在没有冲突标记的情况下：

- 把学生入口从当前 `App` 切换到 `LegacyStudentApp`；
- 把教师入口从当前 `AdminApp` 切换到 `LegacyTeacherApp`；
- 删除当前 3D 原子、RAG 助手、现代路由、教师模块和大量测试；
- 降级两个前端的依赖、构建脚本和端口配置。

因此“没有冲突”不能被视为可接受。所有自动删除、入口切换、包依赖变化和 API 重命名都必须与功能矩阵逐项核对。

### 2.2 直接在 `main` 上工作的安全方式

不创建额外功能分支。执行时按以下顺序工作：

1. 记录并验证 `main`、`origin/main`、`legacy` 和 merge-base；为开工前 `main` 创建明确的安全标签。
2. 将用户已有的 `artifacts/catalog_outline_seed_validation_report.json` 修改保存为仓库外补丁并记录校验值；所有任务提交均显式排除该文件。
3. 在 `main` 上按本设计逐批移植已批准的 legacy 行为，每批完成测试并使用 Conventional Commits 留下可回滚检查点。
4. 所有产品行为和清理通过后，执行最终双亲 merge，把 `legacy` 纳入 `main` 的 ancestry。最终 merge 的树必须保持已经验证的统一产品，不接受 legacy 自动合并树对受保护运行时的改写。
5. 验证 `git merge-base --is-ancestor legacy main` 成功，并对最终 merge 前后的产品树做语义差异检查。
6. 恢复并重新校验用户原有 artifact 修改；它不进入本任务提交。

最终 ancestry merge 不是用来重新选择产品实现，而是记录“legacy 的已批准内容已经被人工语义吸收”。产品变更在之前的可测试提交中完成，merge commit 只闭合历史。

## 3. 最终运行时边界

```text
Student browser
  -> apps/web-student (five-tab green H5)
  -> /api/student/*

Teacher browser
  -> apps/web-teacher (current modular console)
  -> /api/admin/* (internal API namespace retained)

FastAPI server
  -> PostgreSQL canonical facts
  -> media/textbook workers
  -> Elasticsearch
       - textbook RAG hybrid/vector projection (retained)
       - teacher catalog authoring search (retained)
       - student video-library projection (removed)
```

`/api/admin/*` remains an internal compatibility-neutral namespace for the current teacher console; the user-facing product is still called “教师端”. Renaming every current API and frontend client to `/api/teacher/*` provides no approved user capability and would add avoidable migration risk. The legacy duplicate `/api/teacher/*` surface and `/api/web-admin/*` surface are not retained.

## 4. Identity and authorization

### 4.1 Role model

Keep the existing internal roles:

| Internal role | User-facing meaning | Access |
| --- | --- | --- |
| `admin` | 主管教师 | All ordinary teacher workflows plus peer teacher-account management |
| `teacher` | 普通教师 | Teaching workflows and self-service account security |
| `student` | 学生 | Student H5 only |

Retire `platform_admin`. Existing `platform_admin` identities, if present, migrate to `admin` so access is not silently lost. Do not apply legacy's `041_collapse_teacher_student_roles.sql`, because converting `admin` to `teacher` would erase the approved supervisor boundary.

### 4.2 Teacher-account ownership

Move the approved account actions into the current teacher Settings surface:

- every teacher: view own identity and change own password;
- supervisor teacher only: list, create, reset password, enable and disable peer teachers;
- newly created accounts are ordinary `teacher` accounts with `must_change_password=true`;
- no role editor and no account deletion;
- no self-disable or supervisor reset of their own password through peer-management actions;
- disabling and resetting increment/rely on password versioning and revoke active sessions;
- prevent disabling the last active supervisor.

The existing `teacher_accounts` domain can be reduced and moved behind an authenticated supervisor-only `/api/admin/...` router. Remove platform-token authentication and the web-admin-specific API layer.

### 4.3 First-login password gate

`must_change_password` applies to teachers as well as students. An authenticated user with the flag may access only identity/session endpoints needed to inspect the session, change the password or log out. Teacher and student shells route to their current-style password panels; successful change increments `password_version`, clears the flag and revokes other sessions.

## 5. Student H5 design

### 5.1 Navigation and visual system

Keep the current route shell and exactly five root tabs: Home, Learn, Atom, Assessment and Profile. Legacy behavior is implemented with current green tokens, mobile primitives, route stack and active-viewport conventions. `LegacyStudentApp`, red assets and four-tab navigation never become production entrypoints.

### 5.2 Home feed, search and recommendations

Use one read model and one route:

```http
GET /api/student/home-video-feed?q=<optional>&limit=<1..30>&cursor=<optional>
```

Contract:

- source rows are published point placements whose full ancestor path and canonical point are published, with published point content and at least one playable published media binding;
- `q` is trimmed, length-bounded and split on the same simple separators as latest legacy; every normalized token must match the searchable point/catalog/content fields;
- default browse and query results share the same item schema and card UI;
- explicit recommendations sort first by configured order and update time, then remaining rows sort by chapter/catalog order and stable IDs;
- `reason="recommended"` and the recommendation badge appear only for explicit recommendation records;
- discovery is finite and cursor-paginated; it does not cycle repeated cards indefinitely;
- the cursor contains version, normalized-query digest, pool revision/hash and offset, so a cursor cannot be reused with a different search;
- only the active/main viewport card receives muted preview playback; opening the card navigates to the owning point.

Add a canonical recommendation table through a numbered migration. If `legacy_recommended_video_points` exists, copy valid rows once and then retire it. Recommendation toggle/order is owned by the current teacher catalog point editor, not a restored legacy page or operations app.

Remove:

- `/video-library`, unified `/search` behavior that only fronts the video library, and `/api/student/video-library/search`;
- phenomenon topic rail and `topic`-based Home discovery modes;
- watch-later UI/API/data writes while preserving `favorite` saves and the Profile favorites feed;
- like, not-interested, share and fake Home feedback controls; the real Profile feedback form remains.

### 5.3 Student video-search projection cleanup

Delete the student-only index mapping, index state, indexing jobs, configuration, rebuild/validation scripts and production-readiness requirements. Before deleting the current `video_library` package, move its genuinely shared HTTP/hash/analyzer helpers to a neutral Elasticsearch/search module because teacher catalog search still consumes those helpers.

Do not remove:

- teacher catalog search's own index, mapping, projection state and readiness checks;
- textbook RAG's hybrid/vector index and online ingestion workflow;
- shared chemistry dictionaries still referenced by retained indexes.

This leaves one vector-management path: textbook RAG. The Home feed search is relational/catalog search and creates no second vector store.

### 5.4 Authentication and one baseline

After login and any required password change:

1. load smart-baseline readiness;
2. if no completed baseline exists, create/resume exactly one baseline session and enter it automatically;
3. otherwise enter the five-tab application.

Remove the separate pretest gate, temporary skip copy and active pretest routes. Existing pretest records are retained as historical data rather than destructively dropped, but no production route writes or gates on them.

### 5.5 Assessments

Keep current route rendering and report placement, but use latest legacy behavior:

- smart assessment remains the primary entry;
- custom assessment presents a searchable chapter → directory → point tree;
- selected chapters/directories expand to their published usable leaf points;
- `questions_per_point` is one of 1, 2 or 3;
- reject empty, stale, unpublished or questionless scope explicitly;
- random-practice and all-range entry modes are absent;
- preserve multi-blank normalization, submit waiting/error behavior, BKT/mastery updates and report lineage.

Assessment history remains under Profile, not a sixth tab.

### 5.6 Retained current capabilities

- Keep the Zdog atom/orbital experience.
- Keep the Atom assistant and bind it to the current configurable online textbook RAG path.
- Keep persisted favorites.
- Keep teacher device/catalog preview and its mutation suppression.
- Keep browser-local AI history but label it as current-device history.
- Keep the current protected media delivery contract during this task; signed-URL redesign is a separate security change.

## 6. Teacher console design

### 6.1 Current console remains canonical

Restore/keep the current `AdminApp` implementation, Ant Design shell, routes, dependencies and tests. The legacy monolith supplies behavior and test cases only. No legacy red page or duplicate service remains.

### 6.2 Existing owners stay in place

- Global smart-paper strategy stays in System Settings.
- Per-class override and preview stay in Class Settings.
- Online textbooks, AI/OCR/embedding/rerank configuration and ingestion monitoring stay in current modules.
- Video processing stays in the current video-resource page and catalog binding workflow.
- Student preview remains current and self-provisions/repairs its hidden preview student/class.

Do not restore legacy `/paper`, legacy AI-settings pages or web-admin preview maintenance.

### 6.3 Question withdrawal lifecycle

Port latest legacy's reversible workflow into the current evidence-aware workbench:

1. only a `published` question can be withdrawn;
2. withdrawal creates a normal editable draft containing `revoked_from_question_id`, actor and timestamp, and removes the source question from active assessment selection without deleting its row;
3. the draft passes current payload, duplicate-risk and evidence-lineage validation;
4. republishing updates the original question ID, restores `published` status and records publisher/time, preserving historical assessment references;
5. disabling remains a distinct action and does not create an editable draft.

The current RAG evidence and duplicate gates are authoritative; legacy may not bypass them.

### 6.4 Analytics

Use the latest legacy chapter-to-element-family mapping as the primary score matrix. Keep current experiment/point/attempt/evidence drawers, report center, AI summaries and exports. Unknown or newly added chapters fall into an explicit unmapped bucket instead of silently receiving an incorrect family.

### 6.5 Catalog and roster regression contracts

Port or verify the legacy fixes without restoring destructive UI:

- staged video binding changes and visibility remain consistent;
- deleting the final placement of a canonical point follows current data-integrity rules;
- roster import validates initial passwords and reports explicit student-ID conflicts;
- archiving/deleting a class cannot leave active roster identities that still authenticate;
- report dialogs remain usable at constrained viewport heights.

## 7. Data migrations

`main` already owns migrations through `045`. Legacy migrations named `041` and `042` must not be copied under those numbers. New migrations start above the actual `main` head and are ordered by dependency.

Expected migration responsibilities:

1. map any `platform_admin` identities to internal supervisor `admin` and retain the `admin`/`teacher`/`student` constraint;
2. create canonical Home recommendation facts and copy valid legacy recommendation rows if that table exists;
3. remove watch-later rows and narrow the retained save contract to favorites without deleting favorites;
4. apply the verified archived-class roster cleanup under a new migration number;
5. retire/drop student-video-library projection state only after all queue hooks and consumers are removed.

Migrations are tested from both a clean database and a representative pre-merge schema. Destructive data cleanup requires a database backup and row-count assertions. Historical assessment/question ownership rows are never deleted merely to simplify the UI.

## 8. Deletion boundary

After migrations and behavior checks, remove all no-longer-owned surfaces:

- `apps/web-student-old`, `apps/web-teacher-old`, `apps/web-admin`;
- legacy entry components/styles/assets inside canonical app directories;
- `/api/student/legacy/*`, `/api/admin/legacy/*`, `/api/teacher/*` duplicates and `/api/web-admin/*`;
- `server.app.domains.student_legacy` and `teacher_legacy` after callers are migrated;
- old Compose services, `docker-compose.old.yml`, platform-admin token settings and readiness checks;
- standalone student video-library routes, projection, scripts, settings and tests;
- active pretest runtime and watch-later contracts;
- obsolete documentation that advertises multiple apps, OpenSpec, operations admin or removed features.

Deletion is validated through route inventory, import-boundary checks, repository search and production Compose/readiness tests.

## 9. Compatibility, rollout and rollback

### Compatibility

- Existing student favorites, reports, mastery and question IDs remain stable.
- Withdrawn questions retain their original ID on republish.
- Current textbook ingestion settings, secrets, jobs, documents, chunks and active ES projection are unchanged.
- No API key or uploaded textbook file enters Git.
- Internal `/api/admin/*` stays stable for the current teacher UI; deleted legacy namespaces receive no permanent compatibility wrappers.

### Rollout gates

1. identity/migration gate;
2. Home/feed/search gate;
3. student auth/assessment gate;
4. teacher workflow gate;
5. runtime/config/docs deletion gate;
6. final full-stack and ancestry gate.

### Rollback

- The pre-work tag restores the code baseline.
- Each functional slice is a separate verified commit on `main`, so a failing slice can be reverted without losing later evidence.
- Database backup plus migration row-count reports protect destructive cleanup; irreversible drops happen only after code no longer reads the table.
- Elasticsearch student projection can be left inert until the relational Home search passes; deletion follows validation rather than preceding it.
- The user's unrelated artifact patch is restored from the repository-external backup if any Git operation touches it.

## 10. Key trade-offs

- Keeping `/api/admin/*` internally avoids a repository-wide rename with no product benefit, while the UI and documentation consistently say “教师端/主管教师”.
- Relational Home search is intentionally simpler than Elasticsearch. The expected corpus is the published experiment-point catalog, and deterministic token matching plus catalog ordering satisfies the approved focused-search scope without maintaining another projection.
- Retaining the internal `admin` role is less semantically elegant than introducing a new role value, but it preserves current authorization and migrations while presenting the correct user-facing supervisor concept.
- Porting legacy behavior before the final ancestry merge produces reviewable commits and prevents Git's non-conflicting deletions from deciding the product.
