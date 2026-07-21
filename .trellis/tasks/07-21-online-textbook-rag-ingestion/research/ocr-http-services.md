# OCR HTTP 服务选型调研

调研日期：2026-07-21。价格和活动可能变化，实际开通前以服务商控制台为准。

## 样本约束

- 《无机化学（下册）（第二版）》：299 页、19.3 MB，全部有文本层，默认不需要整本 OCR。
- 《无机化学实验（第四版）》：240 页、36.3 MB，其中 239 页为扫描图片，必须 OCR。
- 首版需要中文正文、标题层级、阅读顺序、公式、表格、实验步骤、思考题、图题和 PDF 页码；不需要理解装置图本身。

## 候选比较

| 方案 | HTTP/文档能力 | 对当前样本的适配 | 成本与限制 | 结论 |
| --- | --- | --- | --- | --- |
| 中大 AIGW MinerU | OpenAI-compatible 页图 VLM；实际模型 `MinerU2.5-Pro-2604-1.2B`；版面、正文、公式、表格分阶段调用 | 无需本地 GPU；服务端可逐页处理两本教材；精确版本适合复杂文档和 RAG | 网关标注 `本地`/`网络中心`；不是整本 PDF API；当前会去除布局特殊 token，需兼容层；留存、日志、并发和 SLA 未公开 | **当前首选**，先做教材代表页门禁 |
| 百度智能云文档解析（PaddleOCR-VL 1.6） | 异步 HTTP；PDF；Markdown/JSON；中文、公式、表格、标题层级、坐标；500 页/100 MB | 两本均在限制内；官方明确覆盖教材、公式和长文档 | 当前公开按量价约 0.09 元/页；个人通常有 200 页测试额度，活动和认证额度会变化 | 校内 MinerU 未过门禁时的外部 fallback |
| MinerU 精准解析 API | 异步 HTTP；签名上传；`vlm`/pipeline；OCR、公式、表格；Markdown/JSON/Zip；面向 RAG 的页级结构化结果 | 科学文献与复杂 PDF 是其核心场景，输出更接近可直接消费的 RAG 中间格式；两本文件大小满足限制 | 官方不同入口目前分别写 200/600 页与每日 1000/2000 页高优额度；云端 `vlm` 未明确等同 MinerU2.5-Pro，需以实际 API 为准 | 强候选；不能凭模型名断言优于最新 PaddleOCR-VL，须同页 A/B |
| 阿里云 Document Mind 大模型版 | 异步 OpenAPI/SDK；PDF；Markdown/版面；中文 VLM OCR；公式增强；15,000 页/150 MB | 两本均在限制内；整本提交余量大 | 官方文档列出每月 3,000 页免费额度；AccessKey/SDK 和结果轮询接入更复杂，结果需及时持久化 | 国内备选，尤其适合已有阿里云账号 |
| Mistral OCR 4 | REST `/v1/ocr`；按页 Markdown；block/bbox；表格和指定页 | 文件接口简洁，成本低；中文教材效果与国内网络需实测 | 官方价约 4 美元/千页，扫描教材约 0.96 美元 | 海外备选，不作为默认首接 |
| Mathpix Convert API | 异步 PDF API；MMD/Markdown/LaTeX；公式、表格、化学图；最大 1 GB | STEM 和公式能力强，适合作为疑难公式对照 | 约 0.005 美元/页，扫描教材约 1.20 美元，另有一次性 19.99 美元开通费；中文需实测 | 公式专项备选，不作为默认全文 OCR |
| 自托管 PaddleOCR-VL | 可部署完整 HTTP API；Markdown/结构化输出；无第三方传输 | 官方已验证 Apple M4 本地推理和手工 API 部署 | Apple Silicon 暂不支持官方 Docker/Compose 路径，需要手工部署并承担性能、模型和运维成本 | 仅在禁止第三方上传时采用 |

## 基准结论与限制

- OmniDocBench v1.6 维护方公布的表格中，MinerU2.5-Pro 为 95.75，PaddleOCR-VL-1.5 为 94.93；这能支持“MinerU 优于旧版 PaddleOCR-VL-1.5”。
- PaddleOCR-VL-1.6 随后在其技术报告中报告 OmniDocBench v1.6 为 96.33，高于 MinerU2.5-Pro 报告的约 95.69/95.75；因此“MinerU 普遍优于 PaddleOCR”对当前版本不成立。
- 上述差距不到 1 个百分点，基准也不是中文无机化学教材专项集；厂商云 API 的实际预处理和后处理还可能改变结果。
- MinerU 是完整 PDF 解析流水线，PaddleOCR-VL 1.6 是文档 VLM/解析服务。MinerU 在清理、结构化和 RAG 中间产物上可能更省工程，PaddleOCR-VL 在当前公开综合精度和百度商业服务稳定性上更明确。

## 中大 AIGW 实测

- `GET /v1/models` 暴露模型别名 `mineru`，但单凭该接口没有版本号。
- AIGW 公开模型目录 `/api/pricing` 的 `mineru` 条目描述为 `【mineru2.5-pro-2604-1.2b】`，供应方为 OpenDataLab，标签为 `本地`、`网络中心`。
- 对无教材内容的合成化学页面调用 `/v1/chat/completions`，响应中的实际 `model` 字段为 `mineru2.5-pro-2604-1.2b`。目录元数据与运行时结果相互印证，版本可以确定。
- 按官方 `mineru-vl-utils` 预处理和请求参数测试，模型返回的页面布局坐标和类别与合成页面一致，普通英文正文也能正确识别。此前不经过官方图像预处理/消息顺序的直接请求出现重复满页框，说明接入必须复用官方调用契约，不能把它当普通聊天模型随意提示。
- AIGW 返回布局时去除了 `<|box_start|>`、`<|box_end|>`、`<|ref_start|>`、`<|ref_end|>` 等特殊 token，即使请求携带官方的 `skip_special_tokens=false`；官方客户端因此解析不到 block。简化结果仍是稳定的四个 0～1000 坐标加 block type，可由 provider adapter 严格归一化，但也应向网络中心反馈部署配置。
- 合成公式可返回 LaTeX，但对用普通字体绘制的 `^` 等字符存在误识；简单合成表格经 stock 后处理后为空。该现象随后已用真实教材代表页进一步定位。

## 两本教材代表页验证

经用户明确许可，2026-07-22 从两本教材各选择 7 页，共 14 页发送至中大校内 MinerU；没有发送整本 PDF，也没有调用百度或 MinerU 官方云。

代表页覆盖：

- 《无机化学（下册）（第二版）》PDF 第 19、25、43、66、91、190、237 页：章首页、学习要求、正文、复杂反应式、电势图、含结构式表格、过渡金属表格和图题。
- 《无机化学实验（第四版）》PDF 第 20、40、70、90、100、130、180 页：教学程序、实验步骤、仪器图、气体收集、有效数字、公式、数据表、思考题和复杂实验装置。

结果：

- 14/14 页请求成功；总处理时间 45.76 秒，平均 3.27 秒/页，单页 2.50～4.31 秒。该数据只代表本次小样本与有限并发，不等同生产 SLA 或整书耗时承诺。
- 章节/小节标题、正文、实验步骤、页码、图题与图注整体可读。扫描页能够识别“实验目的/原理/内容”“注释”“思考题”等层级，装置图本身保留为 image block，图号和部件说明进入文本。
- 13/13 个独立公式块返回非空 LaTeX。大多数化学式、离子电荷、浓度和单位保留；观察到一处液态 `(l)` 被识别为数字 `(1)`、一处弱印刷算式出现 `?` 标记，以及个别 `10^6` 被输出为空格分隔 token，必须由质量门禁标记而非自动猜改。
- 9/9 个表格块的模型原始响应非空，包含表题、行文字、数值和 LaTeX。AIGW 去除表格 HTML/cell special token 后，单元格边界丢失；stock `mineru-vl-utils` 后处理会把这些非 HTML 内容清空。直接保留 raw table text 或改用 Text Recognition 可用于文字检索，但不能承诺精确 Markdown/HTML 表格重建。
- 将第一本书 7 页输出（补回 raw table text）与其原生文本层做归一化顺序相似度 sanity check，平均约 0.915；各页约 0.710～0.997。原生文本层本身不是人工标注真值，因此该指标只用于发现大范围漏页/乱序。
- 当前离线 canonical 数据对《无机化学（下册）》保存了大量结构化 table row chunks，而实验教材主要依赖可读 Markdown 文本。若要求在线结果完全复制第一本书的表格单元格语义，应继续优先使用本地原生表格抽取，并将扫描表格列为单独质量门禁。

结论：校内 MinerU **已通过文字 RAG 的首版代表页门禁**。正文、结构、公式、图题和实验步骤足以作为首选 OCR/VLM；上线前必须实现 AIGW 兼容 parser，并绕过会清空纯文本表格的 stock 后处理。根据首版“文字即可”的产品范围，扫描表格接受“可检索文字、表题和页码，但无精确单元格结构”的降级，并通过 `table_structure_lost` 明示质量，不再以此阻塞 MVP。

## 推荐路径

1. 首版优先实现校内 MinerU adapter，不再先申请百度凭证。
2. 将简化布局 parser、raw table preservation、Text Recognition 表格降级和容器/子块去重做成 provider contract tests。
3. 向网络中心反馈 `skip_special_tokens=false` 未生效导致布局标记及表格 HTML/cell 标记丢失，并确认调用日志/数据留存、并发、限流和 SLA。
4. 首版接受扫描表格的纯文本降级，不等待 AIGW 修复，也不实现百度 adapter；若后续业务确实需要精确表格结构，再用相同页集单独评估修复后的 AIGW 或百度，且不维护双份向量或双份整书解析结果。
5. 全书 OCR 必须由后台显式触发，任务记录 provider、实际模型版本、参数、页数和费用/配额信息。

## 官方资料

- [百度文档解析（PaddleOCR-VL）API](https://cloud.baidu.com/doc/OCR/s/7mh8u7ruk)
- [百度文档解析产品限制与价格入口](https://cloud.baidu.com/product/ocr/doc_parser)
- [百度 OCR 产品价格](https://cloud.baidu.com/doc/OCR/s/tlrzzplc1)
- [MinerU 精准解析 API](https://mineru.net/apiManage/docs)
- [MinerU 开源项目与能力说明](https://github.com/opendatalab/MinerU)
- [中大 AIGW 模型目录](https://aigw.sysu.edu.cn/api/pricing)
- [MinerU2.5-Pro-2604-1.2B 官方模型卡](https://huggingface.co/opendatalab/MinerU2.5-Pro-2604-1.2B)
- [MinerU 官方 VLM HTTP 客户端](https://github.com/opendatalab/mineru-vl-utils)
- [MinerU 轻量 HTTP 客户端接入说明](https://opendatalab.github.io/MinerU/quick_start/extension_modules/)
- [OmniDocBench v1.6 公开评测](https://github.com/opendatalab/OmniDocBench)
- [MinerU2.5-Pro 技术报告](https://arxiv.org/abs/2604.04771)
- [PaddleOCR-VL-1.6 技术报告](https://arxiv.org/abs/2606.03264)
- [阿里云 Document Mind 文档解析（大模型版）](https://help.aliyun.com/zh/document-mind/developer-reference/document-parsing-large-model-version)
- [PaddleOCR 服务化部署](https://www.paddleocr.ai/main/en/version3.x/deployment/serving.html)
- [PaddleOCR-VL Apple Silicon 部署](https://www.paddleocr.ai/main/en/version3.x/pipeline_usage/PaddleOCR-VL-Apple-Silicon.html)
- [Mistral OCR API](https://docs.mistral.ai/api/endpoint/ocr)
- [Mistral API 价格](https://mistral.ai/pricing/api/)
- [Mathpix OCR API](https://docs.mathpix.com/)
- [Mathpix Convert API 价格](https://website.mathpix.com/pricing/api)
