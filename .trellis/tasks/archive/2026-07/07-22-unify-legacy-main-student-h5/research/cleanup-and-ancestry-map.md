# Phase 5 清理范围与 legacy 血缘落地策略

调研日期：2026-07-22  
调研方式：只读检查当前工作区、`prd.md`、`design.md`、`implement.md`、功能裁剪矩阵、Compose/CI/运行时路由与实际 import/调用关系。本文件只描述范围和安全顺序，不执行删除、合并、提交或推送。

## 1. 结论先行

Phase 5 可以按“删三个前端运行时 + 删四组后端兼容面 + 收口部署/文档/测试”实施：

1. 整体删除 `apps/web-student-old`、`apps/web-teacher-old`、`apps/web-admin`。
2. 删除 `/api/student/legacy/*`、`/api/admin/legacy/*`、`/api/web-admin/*` 及其专属 domain/schema/test；当前树没有实际 `/api/teacher/*` 路由，但应保留一次负向搜索/路由守卫。
3. 删除主动 pretest 的启动/提交能力，但保留历史 pretest 数据、报告读取和迁移链；先把 smart/posttest 仍从 `pretest.py` 借用的学生上下文 helper 迁到中立 assessment owner。
4. 删除旧前端专用的 `legacy-point-generate` 创建入口；保留读取/校验历史 legacy evidence lineage 的兼容代码，除非数据库审计证明不再存在历史 draft。
5. 从默认 Compose、部署脚本、CI、readiness、环境变量和 CORS 中移除三个旧前端；保留 PostgreSQL、Elasticsearch/IK、canonical student/teacher、视频 worker、tusd 和在线教材 ingestion worker。
6. 删除纯旧产品文档，重写仍作为当前入口的 README/部署/架构文档。
7. 最终 ancestry 只用 Git 的 **`ours` merge strategy (`-s ours`)** 创建双亲 merge commit；绝不能用 `-X ours`，后者仍会引入所有“无冲突”的 legacy 删除/入口替换。

## 2. 当前基线（调研时）

- 当前分支：`main`
- 当前已提交 HEAD：`1f81e2e3e8751a03e67f13422078bd41bf2160d1`
- `origin/main`：`e113b2ed0b122f96c28b8b421ceb5441c236f84e`
- `legacy`：`9a3d3559d23d062e353a914a49e86aa2f0206536`
- merge-base：`3096f82d6b282d6a637910960c3123a2c7963d20`
- 当前已提交 ahead 数（`main`, `legacy`）：`13`, `117`
- 已有安全标签：`pre-legacy-reconciliation-20260722-e113b2e`，peel 后指向 `e113b2e`
- 用户文件：`artifacts/catalog_outline_seed_validation_report.json`
- 用户文件及仓库外备份当前 SHA-256 均为 `8e6d89e5f3ca6facf2f1118de3e5add2e476f4e3eb9a4726e5a3a91205cd8b85`，二者字节一致。
- 仓库外备份：`/tmp/chemistry-learning-platform-pre-legacy-artifact-20260722-e113b2e.json`

当前工作区有大量正在进行的 Phase 2–4 修改；Phase 5 不应在这些修改未分别验证/提交时开始，也不应 broad-stage。

## 3. 应整体删除的前端运行时

以下三个目录都是完整运行时边界，批准行为已迁入 canonical app 后应整体删除，包括 package manifest、lockfile、Vite 配置、入口、样式、测试和旧校徽资产：

| 删除目录 | 当前 tracked 内容概况 | 删除理由 |
| --- | --- | --- |
| `apps/web-student-old/` | `LegacyStudentApp*`、旧 `api.ts`、旧 learning/periodic helpers、Vite/package/asset | 旧竞赛学生端；其保留行为已进入绿色五栏 `apps/web-student` |
| `apps/web-teacher-old/` | `LegacyTeacherApp*`、旧 `api.ts`、Vite/package/asset | 旧红色教师端 monolith；当前模块化 `apps/web-teacher` 是唯一 owner |
| `apps/web-admin/` | `PlatformAdminApp.tsx`、token API、role-boundary script、Vite/package | 独立平台运维产品已取消；教师账号能力迁到当前教师 Settings，预览改为教师自助 |

本机 `apps/web-student-old` 还存在 ignored 的 `node_modules/` 和 `dist/`。`git rm` 只保证 tracked 文件消失；完成 Git 删除后需要对这三个**精确目录**做一次本地残留检查，不能用仓库根目录级的 `git clean -fdx`。

Canonical 前端明确保留：

- `apps/web-student/`：绿色五栏 H5、3D 原子/轨道、Atom 助手、收藏、报告和 Home 视频流。
- `apps/web-teacher/`：Ant Design 教师端、在线教材、AI 配置、目录、视频、题库、分析、班级、预览等。
- `apps/shared/`（若有调用）：不能因旧 app 删除而顺带删除。

## 4. 后端删除图

### 4.1 legacy student/teacher adapter：整组删除

删除文件/目录：

```text
server/app/api/student/student_legacy.py
server/app/api/admin/admin_legacy.py
server/app/domains/student_legacy/
server/app/domains/teacher_legacy/
server/app/student_legacy_schemas.py
server/app/teacher_legacy_schemas.py
server/tests/test_student_legacy_video_points.py
server/tests/test_teacher_legacy_demo.py
```

并从 `server/app/app_runtime/main.py` 删除 `admin_legacy_router`、`student_legacy_router` 的 import/include。

应从 route inventory 删除并加入“不得恢复”守卫的实际路由：

```text
GET  /api/student/legacy/video-points
GET  /api/student/legacy/reports
GET  /api/student/legacy/reports/{report_id}
POST /api/student/legacy/smart-assessment/submit

GET  /api/admin/legacy/video-points
PUT  /api/admin/legacy/video-points/{node_id}/recommendation
GET  /api/admin/legacy/teacher-demo/overview
GET  /api/admin/legacy/teacher-demo/video-resources
GET  /api/admin/legacy/teacher-demo/question-resources
GET  /api/admin/legacy/teacher-demo/classes
GET  /api/admin/legacy/teacher-demo/classes/{class_id}/analytics
GET  /api/admin/legacy/teacher-demo/classes/{class_id}/weak-points
GET  /api/admin/legacy/teacher-demo/evaluation-system
```

注意：旧前端也调用了 `/api/auth/*`、当前 smart/custom/point assessment、`/api/admin/classes*`、`/api/admin/catalog/nodes*`、当前 draft/publish 等接口。这些路径有 canonical app 消费者，不能因为旧 app 调用过就删除。

### 4.2 standalone web-admin：路由整组删除，domain 选择性保留

删除整个路由 package：

```text
server/app/api/web_admin/__init__.py
server/app/api/web_admin/auth.py
server/app/api/web_admin/student_preview.py
server/app/api/web_admin/teacher_accounts.py
```

并从 `server/app/app_runtime/main.py` 删除 `web_admin_student_preview_router` 的 import/include。`web_admin/teacher_accounts.py` 在当前树已经没有注册，但仍是会被误导性 import 的死文件，也应删除。

退役路由守卫应覆盖：

```text
GET    /api/web-admin/session
GET    /api/web-admin/teacher-accounts
POST   /api/web-admin/teacher-accounts
PATCH  /api/web-admin/teacher-accounts/{account_id}
DELETE /api/web-admin/teacher-accounts/{account_id}
POST   /api/web-admin/teacher-accounts/{account_id}/reset-password
POST   /api/web-admin/teacher-accounts/{account_id}/disable
POST   /api/web-admin/teacher-accounts/{account_id}/enable
GET    /api/web-admin/student-preview/classes
POST   /api/web-admin/student-preview/classes/{teacher_user_id}/ensure
POST   /api/web-admin/student-preview/classes/{teacher_user_id}/reset
POST   /api/web-admin/student-preview/classes/{teacher_user_id}/disable
POST   /api/web-admin/student-preview/classes/{teacher_user_id}/restore
```

账号 domain **不能删除**：

```text
server/app/domains/platform/teacher_accounts.py
server/app/api/admin/admin_teacher_accounts.py
```

它们已经是当前教师端“主管教师”账号管理 owner，保留 list/create/reset/enable/disable 和 session revocation。

学生预览 domain 只能裁剪运维专属函数，不能整文件删除：

```text
server/app/domains/preview/student_device_preview.py
```

当前教师端仍依赖 `create_teacher_preview_session -> ensure_teacher_preview_student -> get_preview_infrastructure_for_teacher` 以及 ticket exchange。可删除的仅是 web-admin 独占的批量运维/维护函数：

- `_load_teacher_user`
- `ensure_teacher_preview_student_by_teacher_id`
- `list_preview_infrastructure`
- `reset_preview_student`
- `disable_preview_student`
- `restore_preview_student`

删除前应以实际调用搜索为准；`PreviewInfrastructureResponse`、`_preview_item_from_row`、`ensure_teacher_preview_student` 和 `get_preview_infrastructure_for_teacher` 仍被自助预览流程使用。

### 4.3 主动 pretest：删除写入口，保留历史兼容

删除/退役：

```text
server/app/api/student/student_pretest.py
POST /api/student/pretest/start
POST /api/student/pretest/submit
server/app/student_pretest_schemas.py              # 在无剩余 import 后
server/tests/test_student_pretest.py               # 改为负向路由/历史报告回归更合适
```

从 `server/app/app_runtime/main.py` 删除 pretest router。删除教师 Settings 中 `pretest_enabled`、`pretest_question_count` 可编辑控件及对应主动策略字段，避免继续广告一个不可启动的流程。

`server/app/domains/assessments/pretest.py` 目前不能直接整文件删：

- `posttest.py` import `_ensure_student_row`、`_load_student_context`；
- `smart_assessment.py` 也 import 同一组 helper。

先将通用 student assessment context/helper 移到中立模块（例如 `assessments/student_context.py`），改完两个 caller 并测试后，才删除 `pretest.py` 中主动组题/提交/mastery 写入代码。

以下历史兼容应保留：

- `server/migrations/015_student_pretest_sessions.sql`；
- `student_pretest_sessions` 历史表和数据库备份；
- `server/migrations/038_student_assessment_reports.sql` 中 `pretest` report type；
- 历史报告读取、Profile/教师分析的 pretest 标签与展示；
- preview reset/数据维护若仍需清理旧 pretest 行，可保留相应表引用；
- 旧 pretest 对已有学生推荐的历史影响如要取消，应作为明确数据/产品迁移，不能靠删表实现。

### 4.4 旧教师端专属 question generation：建议删除创建入口，保留历史 lineage reader

当前 canonical `apps/web-teacher` 没有调用：

```text
POST /api/admin/question-banks/legacy-point-generate
```

它只由 `apps/web-teacher-old` 调用。删除旧教师端后，建议同时：

- 从 `server/app/api/admin/admin_question_generation.py` 删除该 route 和专属 import；
- 删除 `generate_legacy_point_content_question_drafts` 及仅用于创建新 legacy-point draft 的 helper；
- 更新 `server/tests/test_question_generation_router.py` 和 route inventory。

但不要机械删除所有 `legacy_point_content` / `LEGACY_QUESTION_WITHDRAWAL_MODE` 判断。当前题库 withdrawal/republication 和 evidence 校验可能需要读取旧 draft/generation 的 lineage；应先查生产库历史行，再决定是否移除 reader/validator。新 withdrawal 实现中的 legacy provenance 兼容测试属于数据兼容，不是旧 runtime。

### 4.5 当前树中没有 `/api/teacher/*`

调研只发现设计文档中的 `/api/teacher/*` 字样，没有实际 FastAPI router。Phase 5 仍应保留：

```bash
rg -n 'prefix="/api/teacher|/api/teacher/' server apps scripts
```

作为负向检查；不要为了“改名”把 canonical `/api/admin/*` 全量重命名。

## 5. 配置、Compose、CI 与部署脚本清理

### 5.1 `docker-compose.yml`

删除服务：

```text
web-admin
web-student-old
web-teacher-old
```

删除 backend 环境：

```text
WEB_ADMIN_ACCESS_TOKEN
```

从 `FRONTEND_ALLOWED_ORIGINS` 默认值删除 web-admin/old app 的 15175/15176/15177（以及对应 localhost/127.0.0.1）来源；保留 canonical student/teacher 和教师预览所需来源。

保留服务：

```text
postgres
elasticsearch
backend
web-student
web-teacher
tusd
video-worker
textbook-ingestion-worker
```

`server/Dockerfile.frontend` 和 `server/nginx/frontend.conf.template` 是 canonical 两个前端共用基础设施，不能随旧 app 删除。

### 5.2 整体删除 `docker-compose.old.yml`

它只定义 `backend-old`、`web-student-old`、`web-teacher-old` 的旧竞赛 profile，并包含旧 token/origin/port；无剩余 owner。

### 5.3 `.env.example` 与 settings

删除：

```text
WEB_ADMIN_HOST_BIND
WEB_ADMIN_HOST_PORT
WEB_ADMIN_ACCESS_TOKEN
WEB_STUDENT_OLD_HOST_BIND
WEB_STUDENT_OLD_HOST_PORT
WEB_TEACHER_OLD_HOST_BIND
WEB_TEACHER_OLD_HOST_PORT
```

同时收窄 `FRONTEND_ALLOWED_ORIGINS` 的旧 5175/5176/5177/15176/15177 来源。

从 `server/app/infrastructure/settings.py` 删除：

- `Settings.web_admin_access_token`；
- production 对 `WEB_ADMIN_ACCESS_TOKEN` 的强制校验；
- `get_settings()` 的 token 装载。

不要删除同一 Settings 中 `TEXTBOOK_*`、`TEXTBOOK_RAG_*`、`TEACHER_CATALOG_SEARCH_*`、student preview、video processing 配置。

### 5.4 ignore 文件

- `.gitignore`：删除 `apps/web-admin/.env.local`、`apps/web-admin/dist/` 和对两个 old app 的显式反忽略/旧依赖目录规则。
- 可保留通用 `apps/*-old/` ignore 作为“防止旧 runtime 被误加回”的护栏；它不是运行时配置。
- `.dockerignore`：删除 `apps/web-admin/node_modules`；canonical student/teacher node_modules ignore 保留。

### 5.5 脚本和 CI

修改而不是删除：

| 文件 | 改动 |
| --- | --- |
| `scripts/deploy_compose_stack.py` | `DEFAULT_SERVICES` 去掉 web-admin；删除 `LEGACY_SERVICES`、`--include-legacy` 和分支逻辑 |
| `scripts/validate_compose_stack.py` | required services 去掉 web-admin；删除 legacy 选项、端口解析和 smoke；保留 ES/IK、teacher catalog rebuild、两 canonical frontend/API proxy smoke |
| `scripts/validate_production_readiness.py` | FRONTENDS 仅 teacher/student；删除 web-admin dependency/typecheck/build stage；保留 backend、教材、teacher/student gates |
| `.github/workflows/production-readiness.yml` | cache dependency 和 `npm ci` 步骤删除 `apps/web-admin` |

Phase 2 已删除且应保持删除：

```text
scripts/rebuild_video_library_index.py
scripts/validate_video_library_search.py
```

应保留：

```text
scripts/rebuild_teacher_catalog_search_index.py
scripts/validate_teacher_catalog_search.py
scripts/rebuild_online_textbook_projections.py
scripts/index_textbook_rag_chunks.py
scripts/import_precomputed_textbook_rag.py
scripts/bootstrap_admin.py
scripts/validate_backend_architecture.py
scripts/validate_production_resources.py
scripts/cleanup_legacy_artifacts.py
```

其中 `bootstrap_admin.py` 的 `admin` 是主管教师内部角色；`cleanup_legacy_artifacts.py` 是受 protected manifest 保护的历史 seed/artifact 清理工具，不是旧产品 runtime。

## 6. 文档动作图

### 6.1 整体删除

```text
docs/admin-only-repository.md
docs/legacy-competition-profile.md
```

前者仍以独立 platform operations 产品为中心，后者只描述两个 old frontend 的部署。

### 6.2 必须更新

| 文档 | 必须移除/改写的内容 |
| --- | --- |
| `README.md` | 三 frontend、old app 安装/启动、5175/5176/5177、`--include-legacy`、web-admin token、旧 video-library rebuild；改成一个 student H5 + 一个 teacher console + 在线教材 RAG |
| `docs/production-operations.md` | web-admin/old services/token/ports、student video-library ES 运维、旧 rebuild/diagnostic/rollback；保留 teacher catalog ES 与 textbook RAG/ingestion 运维 |
| `docs/application-engineering-structure.md` | surfaces 去掉 web-admin，student second-level route 去掉 video library，Compose gate 改为两前端，ES 描述改成 teacher authoring + textbook RAG |
| `docs/backend-slim-architecture.md` | 删除 `video_library/`、student search events/index owner、active pretest owner；增加 relational Home owner、neutral `search_index.py`、teacher search/textbook ingestion owner |
| `docs/catalog-tree-architecture.md` | student search 改为 Home relational published/playable read model；job/state 只保留 teacher search 与 RAG evidence；删除 student projection state 的当前式描述 |
| `docs/productionization-final-notes.md` | restore path 删除 `rebuild_video_library_index.py`；补 teacher catalog/textbook projection restore |
| `docs/local_video_processing.md` | 若“video library”只是在描述重复检测范围，改成 current media/catalog video terminology；视频处理能力本身保留 |
| `docs/student-product-learning-model.md` | 五栏名称与当前 `Atom` 对齐；Home 明确有限分页、聚焦搜索、显式推荐、静音单活跃预览、收藏，无独立视频库/社交动作 |
| `data/seed/README.md` | 删除 `WEB_ADMIN_ACCESS_TOKEN` 配置清单；保留教材和 API secrets 外部配置说明 |

### 6.3 名称像旧内容但不要盲删

- `docs/refactor/admin-platform-split-map.md` 实际记录的是当前模块化 `apps/web-teacher` 和 canonical `/api/admin/*` 拆分过程；可修正文案/路径，但不能只因标题有 `admin-platform` 就删除。
- `docs/online-textbook-ingestion.md` 是本任务明确保护的在线教材流程。
- `docs/production-media-cleanup.md` 中 `legacy media_bindings` 描述数据库历史引用与安全清理，不代表旧前端 runtime。
- 当前仓库已无 OpenSpec 引用；无需创建新的“OpenSpec 删除”动作，也不能误删 Trellis `.trellis/`。

## 7. 测试与 route inventory 动作图

### 7.1 随 runtime 删除

```text
apps/web-student-old/src/LegacyStudentApp.test.tsx
apps/web-teacher-old/src/LegacyTeacherApp.test.tsx
apps/web-admin/scripts/role-boundary-contract.mjs
server/tests/test_student_legacy_video_points.py
server/tests/test_teacher_legacy_demo.py
server/tests/test_student_pretest.py               # 主动 pretest 测试
```

若删除 `legacy-point-generate`，同步删除/改写 `server/tests/test_question_generation_router.py` 中对应 route 断言。

### 7.2 保留并调整

- `server/tests/contracts/backend_route_inventory.json`：重新生成 canonical routes，并把旧 namespace/pretest route 作为 removed aliases 或独立负向契约。
- `server/tests/test_admin_teacher_accounts.py`：保留主管教师账号测试；把 `/api/web-admin/student-preview/classes` 由“存在”改为“不存在”。
- `server/tests/test_student_device_preview.py`：保留 current session/exchange/self-provision/preview isolation 测试；删除 web-admin route 和 reset/disable/restore 运维测试。
- `apps/web-student/src/roleBoundaries.test.ts`：保留“不引用 `/api/web-admin`”的负向守卫。
- `apps/web-teacher/src/app/roleBoundaries.test.ts`：保留 platform_admin 不进入当前 UI 的负向守卫。
- `server/tests/test_identity_role_migration.py`：保留历史角色迁移与 runtime taxonomy 保护。
- `server/tests/test_student_assessment_reports.py`：保留历史 pretest 报告可读性测试；不再测试创建新 pretest。
- `server/tests/test_student_video_saves.py`：保留，它现在是 favorite-only canonical owner。
- `server/tests/test_student_video_library.py`：当前内容已经是“旧 route/modules/scripts 必须不存在”的负向测试；建议改名为 `test_removed_student_video_library_contract.py`，不要误删守卫。
- `server/tests/test_remove_student_video_library_projection_migration.py`：保留 upgrade contract。
- 全部 textbook ingestion/RAG、teacher catalog search 测试保留。

建议新增一个聚合的 retired surface contract，至少断言：

```text
三个旧 app 目录不存在
docker-compose.old.yml 不存在
main.py 未注册 legacy/web-admin/pretest 路由
settings 不包含 web_admin_access_token
Compose services 不包含三个旧 service
canonical teacher/student 入口、3D Atom、textbook APIs 仍存在
```

## 8. 看似旧/像管理员代码，但当前仍依赖，不能删

### 8.1 `/api/admin/*` 与 `server/app/api/admin/*`

它们是当前教师端的内部 API namespace，不是 standalone `web-admin`。在线教材、目录、媒体、题库、班级、分析、反馈、设置、AI、教师账号、学生预览全部仍在使用。只删明确的 `admin_legacy.py` 和 `api/web_admin/`，不能批量删 `admin_*`。

### 8.2 `server/app/domains/platform/*` 与 `admin_platform.py`

`domains/platform/settings.py` 被 assessment、assistant、question workbench、catalog RAG jobs、textbook ingestion 等大量 canonical owner 引用；`teacher_accounts.py` 已是主管教师账号 owner。只能删除 pretest 字段/web-admin token，不删 package。

### 8.3 历史 migration 不能删除

即使名字含 old capability，也保留完整 migration chain：

```text
server/migrations/015_student_pretest_sessions.sql
server/migrations/022_platform_admin_role.sql
server/migrations/033_student_video_saves.sql
server/migrations/046_retire_platform_admin_role.sql
server/migrations/047_home_video_recommendations_and_favorite_saves.sql
server/migrations/048_remove_student_video_library_projection.sql
```

022 + 046 是 clean install/upgrade 的角色迁移链；033 + 047 保证 favorite 数据保留并清掉 watch_later；048 只删 student projection，明确保护 teacher/RAG state。不能通过删除旧 migration “清理历史”。

### 8.4 Elasticsearch/IK、neutral search 与两套保留消费者

删除的是 **student video-library projection**，不是 Elasticsearch：

- 保留 `elasticsearch` Compose service 和 IK analyzer assets；
- 保留 `server/app/search_index.py`；
- 保留 `server/app/domains/catalog_tree/teacher_search.py`、teacher search state/jobs/config/scripts；
- 保留 `server/app/domains/textbook_ingestion/`、`server/app/domains/textbook_rag/`、`server/app/workers/textbook_ingestion_worker.py`；
- 保留 `TEXTBOOK_RAG_*`、`TEACHER_CATALOG_SEARCH_*` 与教材 API/UI/tests；
- 保留 `data/seed/textbook_rag_precomputed/` 和 canonical textbook chunks。

### 8.5 catalog 的 `legacy_*` identity 字段

`experiment_catalog_legacy_identity_map`、`legacy_point_key`、`legacy_identity` 仍被 canonical seed migration、teacher authoring search、question lineage/point-aware mapping和校验工具使用。它们是历史 ID 到 canonical point 的数据兼容层，不是旧 app runtime。只有在独立数据迁移证明所有 caller/历史数据都已转换后才能删。

### 8.6 preview、favorite、历史报告

- `server/app/domains/preview/student_device_preview.py`：保留自助预览核心。
- `server/app/api/admin/admin_student_preview.py` 和 `server/app/api/preview/student_session.py`：保留。
- `server/app/domains/student_video_saves.py` / `student_video_save_schemas.py`：保留 favorite-only。
- student/teacher 的 `pretest` report/attempt label：保留历史可读性，不代表主动 pretest 仍开放。

### 8.7 其它“legacy”字样

- `scripts/validate_experiment_points.py` 中 legacy 计数是数据完整性守卫。
- `scripts/cleanup_legacy_artifacts.py` 是 guarded artifact 清理工具。
- `validate_backend_architecture.py` 的 legacy path 检查是防止兼容 wrapper 回归。
- question withdrawal 的 `LEGACY_QUESTION_WITHDRAWAL_MODE` 是历史 lineage 兼容。
- `principle_equation` 等 legacy summary 若仍被 canonical data/render/RAG consumer 读取，不能只按字段名删除。

## 9. 建议的 Phase 5 实施顺序

1. **最后一次 consumer inventory**：对三个 app 的 API path、`api/web_admin`、`student_legacy`、`teacher_legacy`、pretest、legacy-point-generate 做 `rg` 与 route table 快照。
2. **后端先解除注册和 caller**：迁走 assessment helper，删除旧 router include，裁剪 preview ops 和旧 generation creator。
3. **删三个 frontend + backend 专属文件**。
4. **收口 settings/Compose/scripts/CI**，保证 `docker compose config --services` 只列保留服务。
5. **route inventory 和负向测试**，确保旧 surface 不会因 wrapper 被重新加入。
6. **文档重写/删除**，最后 `rg` 不再广告 web-admin、old services、student video-library ES、active pretest。
7. **完整验证并提交 Phase 5**，用户 artifact 显式排除。
8. Phase 6 全量 gate 通过后，才做 ancestry merge。

建议的删除验证搜索（允许 migration/历史兼容白名单）：

```bash
rg -n 'web-admin|web_admin|WEB_ADMIN|web-student-old|web-teacher-old|WEB_STUDENT_OLD|WEB_TEACHER_OLD|docker-compose\.old' . \
  -g '!**/node_modules/**' -g '!**/dist/**' -g '!.git/**' -g '!.trellis/tasks/**'

rg -n '/api/student/legacy|/api/admin/legacy|/api/web-admin|prefix="/api/teacher' server apps scripts
rg -n '/api/student/pretest|student_pretest_router|start_student_pretest|submit_student_pretest_stage' server apps
docker compose config --services
```

## 10. 最安全的 ancestry merge 命令序列（只给方案，不执行）

### 10.1 原则

- 必须等所有产品/清理 commit 和 full gate 完成。
- merge 前除用户 artifact 外不允许任何 staged/unstaged/untracked task 文件。
- 暂存用户 artifact 到单文件 stash，并保留仓库外字节备份；不 broad-stash。
- 使用 `git merge -s ours`，让 merge commit 的 tree 与已验证的 reconciled `main` 完全相同。
- 不使用 `git merge -X ours legacy`；`-X ours` 只偏向冲突选择，仍会应用 legacy 的无冲突入口切换、依赖降级和删除。
- 不 force push，不用 `reset --hard`，remote main 前进时停止。

### 10.2 前置确认与用户 artifact 隔离

以下为建议的非交互 happy-path 命令；其中最终 `main` SHA/安全标签会在实施时动态记录：

```bash
cd /Users/jonathanhu237/code/chemistry-learning-platform
set -euo pipefail

test "$(git branch --show-current)" = "main"
git fetch origin --prune

legacy_sha="$(git rev-parse refs/heads/legacy)"
reconciled_sha="$(git rev-parse HEAD)"
origin_main_sha="$(git rev-parse origin/main)"

test "$legacy_sha" = "9a3d3559d23d062e353a914a49e86aa2f0206536"
test "$(git merge-base main legacy)" = "3096f82d6b282d6a637910960c3123a2c7963d20"
git merge-base --is-ancestor "$origin_main_sha" "$reconciled_sha"
if git merge-base --is-ancestor "$legacy_sha" "$reconciled_sha"; then
  echo "legacy is already an ancestor; stop and inspect"
  exit 1
fi

git diff --cached --quiet
test "$(git status --porcelain=v1 --untracked-files=all)" = " M artifacts/catalog_outline_seed_validation_report.json"

artifact_path="artifacts/catalog_outline_seed_validation_report.json"
artifact_backup="/tmp/chemistry-learning-platform-pre-legacy-ancestry.json"
artifact_sha="$(shasum -a 256 "$artifact_path" | awk '{print $1}')"
test "$artifact_sha" = "8e6d89e5f3ca6facf2f1118de3e5add2e476f4e3eb9a4726e5a3a91205cd8b85"
cp "$artifact_path" "$artifact_backup"
cmp -s "$artifact_path" "$artifact_backup"

git stash push -m "preserve-user-artifact-before-legacy-ancestry" -- "$artifact_path"
artifact_stash="$(git rev-parse refs/stash)"
test -z "$(git status --porcelain=v1 --untracked-files=all)"

reconciled_short="$(git rev-parse --short=12 "$reconciled_sha")"
safety_tag="pre-legacy-ancestry-20260722-$reconciled_short"
git tag -a "$safety_tag" "$reconciled_sha" -m "Safety point before legacy ancestry merge"
```

如果用户 artifact 的预期 checksum 在此前被用户有意更新，应先重新确认和记录新 checksum，而不是为了通过命令硬改回旧值。

### 10.3 创建 tree 不变的双亲 merge commit

```bash
GIT_MERGE_AUTOEDIT=no git merge --no-ff --no-commit -s ours refs/heads/legacy

test "$(git rev-parse MERGE_HEAD)" = "$legacy_sha"
git diff --cached --quiet

git commit -m "chore(git): reconcile legacy history into main"

test "$(git rev-parse HEAD^1)" = "$reconciled_sha"
test "$(git rev-parse HEAD^2)" = "$legacy_sha"
git diff --exit-code "$reconciled_sha" HEAD -- .
git merge-base --is-ancestor "$legacy_sha" HEAD
test "$(git rev-list --parents -n 1 HEAD | wc -w | tr -d ' ')" = "3"
```

这里 `git diff "$reconciled_sha" HEAD` 必须为空：merge commit 只闭合历史，不再做任何产品选择。

### 10.4 恢复并验证用户 artifact

```bash
test "$(git rev-parse stash@{0})" = "$artifact_stash"
git stash apply --index stash@{0}
cmp -s "$artifact_path" "$artifact_backup"
test "$(shasum -a 256 "$artifact_path" | awk '{print $1}')" = "$artifact_sha"
git stash drop stash@{0}

git diff --cached --quiet
test "$(git status --porcelain=v1 --untracked-files=all)" = " M artifacts/catalog_outline_seed_validation_report.json"
```

若 stash apply 失败，不 drop stash；先保留 `/tmp` 备份和 stash，再人工处理。若 merge 在 commit 前失败，使用 `git merge --abort`，不要 `reset --hard`。

### 10.5 merge 后 gate 与非强推

先执行 Phase 6 完整 gate，再执行：

```bash
git diff --check
git merge-base --is-ancestor legacy main

git fetch origin main
git merge-base --is-ancestor origin/main HEAD
git push origin main

test "$(git ls-remote --heads origin main | awk '{print $1}')" = "$(git rev-parse HEAD)"
```

若第二次 fetch 后 `origin/main` 不是 HEAD 的 ancestor，立即停止；重新审计远端新增提交，不使用 `--force`/`--force-with-lease` 绕过。

## 11. ancestry merge 后的语义检查

除 full test/build 外，至少确认：

- `git merge-base --is-ancestor legacy main` 返回 0；
- merge commit 恰好两个 parent，第二 parent 为批准的 `9a3d355...`；
- merge commit 相对第一 parent tree diff 为 0；
- `apps/web-student/src/main.tsx`、`App.tsx` 未切换到 `LegacyStudentApp`；
- `apps/web-teacher` 仍是当前 modular/Ant Design 入口；
- 三个旧 app、`docker-compose.old.yml`、旧 route package 不存在；
- current 3D Atom、favorites、Home feed、question withdrawal、teacher analytics、online textbooks 和 MinerU/Embedding/Rerank 配置仍存在；
- ES 仍服务 teacher catalog authoring 与 textbook RAG，但没有 student video-library projection；
- `artifacts/catalog_outline_seed_validation_report.json` 仍保持用户修改且未进任何 task commit；
- Git diff/历史里没有 API key、上传 PDF、教材 runtime blob 或本地 `.env`。

