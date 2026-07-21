# 在线教材摄取与 RAG 运维

## 数据边界

- PostgreSQL 是事实源：保存教材版本、原文 chunk、页级解析结果、任务、质量报告和发布审计。
- Elasticsearch 是唯一向量存储，同时提供关键词和向量召回。在线流程不会写入 `chunk_embeddings`。
- `data/textbooks/originals/<document_id>/source.pdf` 保存上传原件；backend 和 `textbook-ingestion-worker` 必须挂载同一个持久化目录。
- 只有 `source_documents.publication_status = 'published'` 的版本可被检索。在线版本按 `document_id` 过滤，旧 canonical seed 按 `source_collection` 过滤；无活动版本时检索 fail closed。

## 必要配置

以 `.env.example` 为模板，凭据只放部署环境或密钥管理系统，不要写入数据库、仓库或 Compose 文件。

```dotenv
DATA_BACKEND=postgres
TEXTBOOK_INGESTION_ENABLED=true
TEXTBOOK_STORAGE_ROOT=/app/data/textbooks

TEXTBOOK_OCR_ENABLED=true
TEXTBOOK_OCR_BASE_URL=https://aigw.sysu.edu.cn/v1
TEXTBOOK_OCR_API_KEY=<environment-secret>
TEXTBOOK_OCR_MODEL=mineru

TEXTBOOK_RAG_ENABLED=true
TEXTBOOK_RAG_ELASTICSEARCH_URL=http://elasticsearch:9200
TEXTBOOK_RAG_ELASTICSEARCH_INDEX=canonical-rag-chunks-qwen-v1
TEXTBOOK_RAG_EMBEDDING_BASE_URL=<embedding-provider-url>
TEXTBOOK_RAG_EMBEDDING_API_KEY=<environment-secret>
TEXTBOOK_RAG_EMBEDDING_MODEL=<embedding-model>
TEXTBOOK_RAG_EMBEDDING_DIMENSION=1024
TEXTBOOK_RAG_RERANK_BASE_URL=<rerank-provider-url>
TEXTBOOK_RAG_RERANK_API_KEY=<environment-secret>
TEXTBOOK_RAG_RERANK_MODEL=<rerank-model>
```

校内 MinerU 负责 PDF 低质量页的文字/版面识别，不等同于 Embedding 或 Rerank 服务；三者必须分别确认模型、权限和配额。`CATALOG_POINT_EVIDENCE_AUTO_REFRESH=true` 会在教材语料发布或停用后，为已有点位证据自动排队刷新；默认只标记 stale，由管理员择机刷新。

## 启动

```bash
docker compose up -d postgres elasticsearch backend textbook-ingestion-worker web-teacher
```

应用启动会按顺序应用迁移。确认服务状态：

```bash
docker compose ps
docker compose logs -f textbook-ingestion-worker
```

教师后台入口为 `/textbooks`。上传请求只负责校验和落盘并立即返回 document/job；长任务由 worker 依次执行：

`uploaded -> extracting -> [awaiting_ocr | ocr] -> structuring -> chunking -> embedding -> indexing -> review_ready`

人工确认质量和预览后发布，job 才进入 `ready`，document 才进入 `published`。

## 发布、替换和回滚

- 发布前必须同时通过页/chunk 质量门、Embedding 数量、ES bulk 结果、模型维度和 ES count 校验。
- 同一 `logical_textbook_key` 只允许一个已发布版本。发布新版本的事务会先停用旧版本，再激活新版本，并递增 `textbook_corpus_state.revision`。
- 每次发布或停用都会使现有目录点位教材证据和 binding 过期。stale binding 不会再被助教或出题链路消费。
- 旧版本事实和 ES projection 默认保留，因此可直接对 inactive 版本执行“回滚/重新发布”，不需要重新导入或重新 Embedding。

## 重试和故障恢复

| 状态/错误 | 处理 |
| --- | --- |
| `awaiting_ocr` | 配置并验证 MinerU 凭据后点击重试。不可在缺 OCR 的情况下发布。 |
| OCR/Embedding 临时超时 | worker 按最大次数和退避策略重试；任务事件记录阶段和错误。 |
| `failed` / `cancelled` | 修复配置后重试；重试索引前会先删除该未发布 document 的旧 ES projection，避免孤儿 chunk。 |
| `review_ready` 但不能发布 | 检查 blocking issues、chunk/Embedding/index count 和 `index_verified`。 |
| ES 模型或维度不匹配 | 不要强行发布；使用正确模型重建目标索引或调整配置后重新处理。 |
| 发布后召回异常 | 先停用新版本或回滚旧版本；corpus revision 会立即切换检索 allow-list。 |

worker 使用 PostgreSQL lease 和 fencing token。进程崩溃后，lease 到期的任务可由另一 worker 重新领取；旧 worker 的迟到写入会被拒绝。

## 删除边界

- “停用”可恢复，只改变活动语料和 chunk 发布状态，不删除原件或 ES projection。
- 显式“删除”只允许未发布的在线版本；已发布版本必须先停用，canonical seed 禁止删除。
- 删除会物理移除原 PDF 和该 `document_id` 的 ES projection，但保留 PostgreSQL document/chunk/job 和 lifecycle event 作为审计墓碑。

## 验证

```bash
python -m pytest server/tests/test_textbook_ingestion_postgres.py -q
python -m pytest server/tests/test_textbook_active_corpus.py server/tests/test_textbook_lifecycle.py -q
python scripts/validate_backend_architecture.py

cd apps/web-teacher
npm run validate:boundaries
npm run typecheck
npm test
npm run build
```

全书验收应在测试环境使用真实的 OCR、Embedding、Rerank 和 ES 配置执行，并抽检章节标题、实验目的、实验步骤、思考题、公式、表格降级标记、页码引用及旧 seed 排除。不要把教材页图、OCR 原响应或任何 provider key 提交到仓库。
