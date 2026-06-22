# 实验三要素规范化中间稿

用途：供下一步生成后端 seed 或通过点位内容保存接口导入前审阅。本文不直接入库。

来源：
- `docs/30点位例子.txt`
- `docs/实验描述1.docx`
- `docs/实验描述2.docx`

说明：旧的 `point_content_examples.json` 只生成 30 条文本化示例，无法保留化学方程式结构，已被 `point_content_seed.json` 取代。本文作为 76 条正式内容 seed 的人工审阅中间稿。

## 导入前字段约定

每条规范记录使用以下字段：

- `record_id`：本中间稿内稳定编号。
- `canonical_title`：建议用于点位内容的规范标题。
- `target_path_hint`：按现有章节目录语义推断的路径。若存在同名或跨章节复用，后续导入时再用 catalog seed key 精确绑定。
- `sources`：来源文件与来源序号。多个来源表示重复或近重复实验。
- `principle_mode`：`equation` 或 `text`，对应后端 `experiment_catalog_point_content.principle_mode`。
- `reaction_equations_text`：仅在 `principle_mode=equation` 时使用。一行一个反应；条件、用量、介质、说明写在同一行 `//` 后。
- `principle_text`：仅在 `principle_mode=text` 时使用。
- `phenomenon_explanation`：规范化现象解释。
- `safety_note`：规范化安全提示。
- `normalization_notes`：导入或 AI 校对关注点。

## 总体规范化规则

1. 化学方程式原理尽量转为 `principle_mode=equation`。
2. 多个反应式必须拆成多行；源文档中粘连的反应式在本稿中已按语义拆开。
3. 括号中的条件、过量、酸性、碱性、光照、催化等说明，放入同一行 `//` 后，避免被当作第二条反应。
4. 无法稳定解析为化学反应式的原理，例如焰色反应、品红漂白、通用 `AgX` 或 `M²⁺` 泛化反应，优先使用 `principle_mode=text`，但正文保留关键化学式，便于 ES 检索。
5. 重复实验优先采用信息更完整、分行更清楚的版本；来源较短版本作为 `sources` 保留。
6. 含明显粘连或公式疑点的条目保留 `needs_ai_review` 或 `needs_catalog_mapping` 标记。

## 重复与近重复关系

- `30点位例子.txt` 的 1, 2, 3, 4, 5, 6 与 `实验描述2.docx` 的 27, 18, 21, 22, 24, 26 分别重复。
- `30点位例子.txt` 的 7, 8, 9, 10, 11, 12, 13, 14, 15, 16 与 `实验描述1.docx`/`实验描述2.docx` 中同名或同反应点位重复。
- `30点位例子.txt` 的 17, 18, 19 与 `实验描述1.docx` 的 8, 9, 10 重复。
- `30点位例子.txt` 的 20, 21, 22, 23, 24, 25, 26, 27, 28 与 `实验描述1.docx` 的 11-21 重复。
- `30点位例子.txt` 的 29, 30 与 `实验描述1.docx` 的 25, 26 重复。
- `实验描述1.docx` 的 42 与 `30点位例子.txt` 的 7 重复。

## 规范记录

### norm-ch13-001

record_id: `norm-ch13-001`
canonical_title: 氯水 + KBr + CCl4
target_path_hint: 第13章 卤族元素 / 二、卤素的氧化性 / 氯水、溴水、碘水氧化性差异的比较 / 氯水 + KBr + CCl4
sources: `实验描述1.docx#1`
principle_mode: equation
reaction_equations_text:

```text
Cl2 + 2KBr -> 2KCl + Br2
```

phenomenon_explanation: 向 KBr 溶液中加入氯水，振荡后加入 CCl4，CCl4 层呈橙红色，说明 Cl2 将 Br- 氧化为 Br2，氧化性 Cl2 > Br2。
safety_note: Cl2 和 Br2 有毒，实验在通风橱中操作；Br2 具腐蚀性，避免皮肤接触；CCl4 有毒，废液回收处理。
normalization_notes: needs_catalog_mapping；CCl4 写作 ASCII 便于公式解析，展示层可再渲染为 CCl₄。

### norm-ch13-002

record_id: `norm-ch13-002`
canonical_title: 氯水 + KI + CCl4
target_path_hint: 第13章 卤族元素 / 二、卤素的氧化性 / 氯水、溴水、碘水氧化性差异的比较 / 氯水 + KI + CCl4
sources: `实验描述1.docx#2`
principle_mode: equation
reaction_equations_text:

```text
Cl2 + 2KI -> 2KCl + I2
```

phenomenon_explanation: 向 KI 溶液中加入氯水，振荡后加入 CCl4，CCl4 层呈紫红色，说明 Cl2 将 I- 氧化为 I2，氧化性 Cl2 > I2。
safety_note: Cl2 有毒，实验在通风橱中操作；CCl4 有毒，废液回收处理。
normalization_notes: needs_catalog_mapping。

### norm-ch13-003

record_id: `norm-ch13-003`
canonical_title: 溴水 + KI + CCl4
target_path_hint: 第13章 卤族元素 / 二、卤素的氧化性 / 氯水、溴水、碘水氧化性差异的比较 / 溴水 + KI + CCl4
sources: `实验描述1.docx#3`
principle_mode: equation
reaction_equations_text:

```text
Br2 + 2KI -> 2KBr + I2
```

phenomenon_explanation: 向 KI 溶液中加入溴水，振荡后加入 CCl4，CCl4 层呈紫红色，说明 Br2 将 I- 氧化为 I2。结论：氧化性 Cl2 > Br2 > I2，还原性 I- > Br- > Cl-。
safety_note: Br2 有毒且具腐蚀性，实验在通风橱中操作；CCl4 有毒，废液回收处理。
normalization_notes: needs_catalog_mapping。

### norm-ch13-004

record_id: `norm-ch13-004`
canonical_title: 氯水对溴离子、碘离子混合溶液的氧化顺序
target_path_hint: 第13章 卤族元素 / 二、卤素的氧化性 / 氯水对溴离子、碘离子混合溶液的氧化顺序
sources: `实验描述1.docx#7`
principle_mode: equation
reaction_equations_text:

```text
Cl2 + 2I- -> 2Cl- + I2 // 优先氧化 I-
Cl2 + 2Br- -> 2Cl- + Br2 // I- 基本反应完后再氧化 Br-
I2 + 5Cl2 + 6H2O -> 2HIO3 + 10HCl // 氯水过量时 I2 进一步被氧化
```

phenomenon_explanation: 逐滴加入氯水初期 CCl4 层先呈紫红色，说明 Cl2 优先氧化 I-；继续滴加后出现橙红色，说明 Br- 被氧化为 Br2；氯水过量时紫红色消失，I2 被进一步氧化为无色碘酸。
safety_note: Cl2 有毒，在通风橱中操作；CCl4 有毒，废液回收处理。
normalization_notes: source_has_glued_equations；已拆分三条反应。

### norm-ch13-005

record_id: `norm-ch13-005`
canonical_title: KI + 浓硫酸 | 湿的醋酸铅试纸
target_path_hint: 第13章 卤族元素 / 三、卤素离子的还原性（通风橱内进行） / 利用浓硫酸比较卤素离子的还原性 / KI + 浓硫酸 | 湿的醋酸铅试纸
sources: `30点位例子.txt#17`, `实验描述1.docx#8`
principle_mode: equation
reaction_equations_text:

```text
8KI + 9H2SO4 -> 4I2 + 8KHSO4 + H2S + 4H2O // 浓硫酸条件
Pb(CH3COO)2 + H2S -> PbS + 2CH3COOH // 湿醋酸铅试纸变黑
```

phenomenon_explanation: 生成紫黑色 I2 和臭鸡蛋气味 H2S，湿醋酸铅试纸变黑，KI-淀粉试纸变蓝，pH 试纸变红。
safety_note: H2S 和 I2 蒸气有毒，必须在通风橱中操作；浓硫酸强腐蚀且反应放热，试管口勿对人。
normalization_notes: duplicate_merged；将 Pb(Ac)2 规范为 Pb(CH3COO)2，HAc 规范为 CH3COOH。

### norm-ch13-006

record_id: `norm-ch13-006`
canonical_title: KBr + 浓硫酸 | 湿的 KI-淀粉试纸
target_path_hint: 第13章 卤族元素 / 三、卤素离子的还原性（通风橱内进行） / 利用浓硫酸比较卤素离子的还原性 / KBr + 浓硫酸 | 湿的KI-淀粉试纸
sources: `30点位例子.txt#18`, `实验描述1.docx#9`
principle_mode: equation
reaction_equations_text:

```text
2KBr + 3H2SO4 -> Br2 + 2KHSO4 + SO2 + 2H2O // 浓硫酸条件
Br2 + 2I- -> 2Br- + I2 // 湿 KI-淀粉试纸变蓝的主要原因
SO2 + I2 + 2H2O -> H2SO4 + 2HI // SO2 具还原性，属于伴随说明
```

phenomenon_explanation: 生成棕色 Br2 和刺激性 SO2，KI-淀粉试纸变蓝，pH 试纸变红。
safety_note: Br2 蒸气和 SO2 有毒，在通风橱中操作；浓硫酸和 Br2 均有腐蚀性。
normalization_notes: duplicate_merged；源 30 中 SO2 与 I2 反应解释容易误导，导入时保留为补充反应而非主现象原因。

### norm-ch13-007

record_id: `norm-ch13-007`
canonical_title: KCl + 浓硫酸 | 湿的 pH 试纸
target_path_hint: 第13章 卤族元素 / 三、卤素离子的还原性（通风橱内进行） / 利用浓硫酸比较卤素离子的还原性 / KCl + 浓硫酸 | 湿的pH试纸
sources: `30点位例子.txt#19`, `实验描述1.docx#10`
principle_mode: equation
reaction_equations_text:

```text
KCl + H2SO4 -> KHSO4 + HCl // 浓硫酸条件，HCl 逸出
```

phenomenon_explanation: 产生刺激性 HCl 气体，湿 pH 试纸变红；醋酸铅试纸和 KI-淀粉试纸无明显变化。
safety_note: HCl 气体有刺激性，在通风橱中操作；浓硫酸具腐蚀性，避免皮肤接触。
normalization_notes: duplicate_merged。

### norm-ch13-008

record_id: `norm-ch13-008`
canonical_title: NaClO + MnSO4
target_path_hint: 第13章 卤族元素 / 五、卤素含氧酸盐的氧化性 / 次氯酸盐的氧化性 / NaClO + MnSO4
sources: `30点位例子.txt#20`, `实验描述1.docx#11`
principle_mode: equation
reaction_equations_text:

```text
Mn^2+ + ClO- + 2OH- -> MnO2 + Cl- + H2O // NaClO 溶液本身呈碱性，提供 OH-
```

phenomenon_explanation: 溶液中迅速产生棕黑色 MnO2 沉淀，并可能伴有少量 O2 气泡。
safety_note: NaClO 具有腐蚀性和漂白性，避免皮肤接触；含 Mn 的废液应回收处理。
normalization_notes: duplicate_merged；`//` 用于保留碱性来源说明，避免污染反应物解析。

### norm-ch13-009

record_id: `norm-ch13-009`
canonical_title: NaClO + 品红溶液
target_path_hint: 第13章 卤族元素 / 五、卤素含氧酸盐的氧化性 / 次氯酸盐的氧化性 / NaClO + 品红溶液
sources: `30点位例子.txt#21`, `实验描述1.docx#12`
principle_mode: text
principle_text: NaClO 具有强氧化性，能氧化破坏品红分子的发色基团，使红色品红溶液褪为无色。
phenomenon_explanation: 品红溶液红色立即褪去，体现 NaClO 的氧化漂白性。
safety_note: NaClO 具有腐蚀性和漂白性，避免接触皮肤和衣物。
normalization_notes: duplicate_merged；含有“品红/无色产物”等非结构化有机物名称，暂不进入 equation 模式。

### norm-ch13-010

record_id: `norm-ch13-010`
canonical_title: NaClO + KI-淀粉 | 酸性体系
target_path_hint: 第13章 卤族元素 / 五、卤素含氧酸盐的氧化性 / 次氯酸盐的氧化性 / NaClO + KI-淀粉 | 酸性体系
sources: `30点位例子.txt#22`, `实验描述1.docx#13`
principle_mode: equation
reaction_equations_text:

```text
2I- + ClO- + 2H+ -> I2 + Cl- + H2O
I2 + 5ClO- + H2O -> 2IO3- + 5Cl- + 2H+ // ClO- 过量时
```

phenomenon_explanation: 溶液立即变蓝，说明 I2 与淀粉作用；继续滴加 NaClO 后蓝色褪去，I2 被过量 ClO- 进一步氧化为无色 IO3-。
safety_note: NaClO 和 H2SO4 具有腐蚀性，避免皮肤接触。
normalization_notes: duplicate_merged；源 DOCX 粘连处已拆为两行。

### norm-ch13-011

record_id: `norm-ch13-011`
canonical_title: KClO3 + 浓盐酸 | 湿 KI-淀粉试纸
target_path_hint: 第13章 卤族元素 / 五、卤素含氧酸盐的氧化性 / 氯酸盐的氧化性 / KClO3 + 浓盐酸 | 湿 KI-淀粉试纸
sources: `30点位例子.txt#23`, `实验描述1.docx#16`
principle_mode: equation
reaction_equations_text:

```text
KClO3 + 6HCl -> 3Cl2 + KCl + 3H2O // 浓盐酸条件
Cl2 + 2I- -> 2Cl- + I2 // 湿 KI-淀粉试纸变蓝
```

phenomenon_explanation: 产生黄绿色、有刺激性气味的 Cl2，湿润 KI-淀粉试纸变蓝。
safety_note: Cl2 有毒，必须在通风橱中操作；浓盐酸具腐蚀性；KClO3 与还原剂混合加热可能爆炸，避免混入有机物。
normalization_notes: duplicate_merged。

### norm-ch13-012

record_id: `norm-ch13-012`
canonical_title: KClO3 + Na2SO3 + AgNO3
target_path_hint: 第13章 卤族元素 / 五、卤素含氧酸盐的氧化性 / 氯酸盐的氧化性 / KClO3 + Na2SO3 + AgNO3
sources: `30点位例子.txt#24`, `实验描述1.docx#17`
principle_mode: equation
reaction_equations_text:

```text
ClO3- + 3SO3^2- -> Cl- + 3SO4^2- // 酸性条件促进反应；净离子式中 H+ 和 H2O 抵消
Ag+ + Cl- -> AgCl // 白色沉淀检验 Cl-
```

phenomenon_explanation: 中性条件下无明显现象；酸化后反应发生，再用 AgNO3 检验生成 Cl-，出现白色 AgCl 沉淀。
safety_note: H2SO4 具有腐蚀性，避免皮肤接触；含 Ag+ 废液应回收处理。
normalization_notes: duplicate_merged；源 30 的主反应更完整，DOCX 的 Ag+ 检验反应作为第二行；reviewed_redox_balanced。

### norm-ch13-013

record_id: `norm-ch13-013`
canonical_title: KClO3 + KI + CCl4
target_path_hint: 第13章 卤族元素 / 五、卤素含氧酸盐的氧化性 / 氯酸盐的氧化性 / KClO3 + KI + CCl4
sources: `30点位例子.txt#25`, `实验描述1.docx#18`
principle_mode: equation
reaction_equations_text:

```text
6I- + ClO3- + 6H+ -> 3I2 + Cl- + 3H2O
3I2 + 5ClO3- + 3H2O -> 5Cl- + 6IO3- + 6H+ // ClO3- 过量时，已配平
5Cl- + ClO3- + 6H+ -> 3Cl2 + 3H2O
```

phenomenon_explanation: 中性条件下 CCl4 层无色；酸性条件下 CCl4 层逐渐呈紫红色，继续反应可能颜色变浅并产生黄绿色气体。
safety_note: 反应可能产生 Cl2，在通风橱中操作；H2SO4 具腐蚀性；CCl4 有毒，废液回收处理。
normalization_notes: source_has_glued_equations；源 DOCX 粘连三条反应，已拆分；第二条已按氧化还原配平补入 6H+。

### norm-ch13-014

record_id: `norm-ch13-014`
canonical_title: KClO3 + KI-淀粉 | 酸性体系
target_path_hint: 第13章 卤族元素 / 五、卤素含氧酸盐的氧化性 / 氯酸盐的氧化性 / KClO3 + KI-淀粉 | 酸性体系
sources: `30点位例子.txt#26`, `实验描述1.docx#19`
principle_mode: equation
reaction_equations_text:

```text
ClO3- + 6I- + 6H+ -> 3I2 + Cl- + 3H2O
```

phenomenon_explanation: 中性条件下无明显现象；酸化后溶液变蓝，说明酸性条件下 ClO3- 氧化性增强并氧化 I- 为 I2。
safety_note: H2SO4 具腐蚀性，避免皮肤接触。
normalization_notes: duplicate_merged。

### norm-ch13-015

record_id: `norm-ch13-015`
canonical_title: 高氯酸盐的氧化性
target_path_hint: 第13章 卤族元素 / 五、卤素含氧酸盐的氧化性 / 高氯酸盐的氧化性
sources: `30点位例子.txt#27`, `实验描述1.docx#20`
principle_mode: equation
reaction_equations_text:

```text
ClO4- + 8I- + 8H+ -> 4I2 + Cl- + 4H2O // 强酸并加热时
```

phenomenon_explanation: 中性及冷稀酸条件下无明显现象；在强酸并加热条件下，高氯酸根可氧化 I- 生成 I2，使 KI-淀粉体系变蓝。氧化性比较按教学口径保留：ClO-（中性）> ClO3-（酸性）> ClO4-（强酸加热）。
safety_note: 强酸具腐蚀性；高氯酸盐/强酸加热体系有强氧化风险，应微量、通风橱操作，避免接触有机物和可燃物。
normalization_notes: researched_update；高氯酸根在冷稀水溶液中动力学惰性，已补入“强酸并加热”条件，避免把单纯酸化写成稳定阳性。

### norm-ch13-016

record_id: `norm-ch13-016`
canonical_title: 卤化银的感光性
target_path_hint: 第13章 卤族元素 / 七、金属卤化物的性质 / 卤化银的感光性
sources: `30点位例子.txt#28`, `实验描述1.docx#21`
principle_mode: equation
reaction_equations_text:

```text
2AgCl -> 2Ag + Cl2 // 光照分解
2AgBr -> 2Ag + Br2 // 光照分解
2AgI -> 2Ag + I2 // 光照分解
```

phenomenon_explanation: 制备 AgCl、AgBr、AgI 悬浊液并部分遮光，光照后可见阴影轮廓；卤化银见光分解生成黑色 Ag，未照光部分保持原色。AgCl、AgBr、AgI 均具感光性，实际分解快慢受晶粒、缺陷/敏化点和光照条件影响，本条不写固定速率顺序。
safety_note: 含 Ag+ 废液应回收处理。
normalization_notes: researched_update；将泛化 `AgX` 改为三条代表反应以利于 ES 公式检索；调研后不写固定 AgCl/AgBr/AgI 速率顺序。

### norm-ch13-017

record_id: `norm-ch13-017`
canonical_title: 氯的歧化反应 | 氯水 + NaOH + HCl
target_path_hint: 第13章 卤族元素 / 四、氯的歧化反应（通风橱内进行） / 氯水 + NaOH + HCl
sources: `实验描述1.docx#14`
principle_mode: equation
reaction_equations_text:

```text
Cl2 + 2OH- -> ClO- + Cl- + H2O // 碱性条件下歧化
ClO- + Cl- + 2H+ -> Cl2 + H2O // 酸化后重新放出氯气
Cl2 + 2I- -> 2Cl- + I2 // 湿 KI-淀粉试纸变蓝
```

phenomenon_explanation: 酸化后产生黄绿色 Cl2，湿润 KI-淀粉试纸变蓝。
safety_note: 反应产生 Cl2，有毒，必须在通风橱中操作；浓盐酸和 NaClO/碱液具腐蚀性，避免皮肤接触。
normalization_notes: source_has_glued_equations；已将粘连的歧化和酸化反应拆分。

### norm-ch13-018

record_id: `norm-ch13-018`
canonical_title: 氯水 + KOH
target_path_hint: 第13章 卤族元素 / 四、氯的歧化反应（通风橱内进行） / 氯水 + KOH
sources: `实验描述1.docx#15`
principle_mode: equation
reaction_equations_text:

```text
Cl2 + 2KOH -> KCl + KClO + H2O // 冷稀碱条件下歧化
3Cl2 + 6KOH -> 5KCl + KClO3 + 3H2O // 加热时进一步歧化
```

phenomenon_explanation: 氯水黄绿色逐渐褪去，溶液变为无色；若加热则进一步生成 KCl 和 KClO3。
safety_note: Cl2 有毒，在通风橱中操作；KOH 具强腐蚀性，避免皮肤接触。
normalization_notes: second_equation_added_from_phenomenon；加热反应由源文档现象说明补成标准方程式，非源实验原理原句。

### norm-ch14-001

record_id: `norm-ch14-001`
canonical_title: Na2S2O3 + 氯水
target_path_hint: 第14章 氧族元素 / 六、硫代硫酸钠的制备与性质 / 硫代硫酸钠的性质 / 硫代硫酸钠的还原性 / Na2S2O3 + 氯水
sources: `实验描述1.docx#4`
principle_mode: equation
reaction_equations_text:

```text
Na2S2O3 + 4Cl2 + 5H2O -> Na2SO4 + H2SO4 + 8HCl
```

phenomenon_explanation: 向 Na2S2O3 溶液中加入氯水，氯水黄绿色褪去。
safety_note: Cl2 有毒，在通风橱中操作；废液应回收处理。
normalization_notes: target_path_duplicate_allowed；目录中也有“氯水、溴水、碘水分别与 Na2S2O3 反应”；按系统智能指针设计允许同一实验关联不同目录，本记录映射以现有目录为准。

### norm-ch14-002

record_id: `norm-ch14-002`
canonical_title: Na2S2O3 + 碘水
target_path_hint: 第14章 氧族元素 / 六、硫代硫酸钠的制备与性质 / 硫代硫酸钠的性质 / 硫代硫酸钠的还原性 / Na2S2O3 + 碘水
sources: `实验描述1.docx#6`
principle_mode: equation
reaction_equations_text:

```text
I2 + 2Na2S2O3 -> Na2S4O6 + 2NaI
```

phenomenon_explanation: 向 Na2S2O3 溶液中加入碘水，溶液由棕黄色变为无色，无沉淀生成，S2O3^2- 被氧化为 S4O6^2-。
safety_note: 废液应回收处理。
normalization_notes: target_path_duplicate_allowed；与卤素氧化性比较也可关联；按系统智能指针设计允许同一实验关联不同目录，本记录映射以现有目录为准。

### norm-ch14-003

record_id: `norm-ch14-003`
canonical_title: 臭氧的制备与性质 | BaO2·2H2O + 浓硫酸
target_path_hint: 第14章 氧族元素 / 二、臭氧的制备与性质 / BaO2·2H2O + 浓硫酸 | KI-淀粉试纸
sources: `实验描述1.docx#22`
principle_mode: equation
reaction_equations_text:

```text
BaO2 + H2SO4 -> BaSO4 + H2O2 // 可能的中间/副产物
3BaO2 + 3H2SO4 -> 3BaSO4 + O3 + 3H2O // 教学制臭氧总反应
O3 + 2I- + H2O -> I2 + O2 + 2OH- // KI-淀粉试纸变蓝
```

phenomenon_explanation: BaO2·2H2O 与浓硫酸反应并冰水冷却，用 KI-淀粉试纸检验逸出气体，试纸变蓝，说明有 O3 等强氧化性气体生成。
safety_note: 浓硫酸强腐蚀；反应放热，需冰水冷却防止喷溅；O3/氧化性气体有刺激性，实验在通风橱中操作。
normalization_notes: researched_update；不再把 `3H2O2 -> O3 + 3H2O` 写成一般 H2O2 分解，改为 BaO2 与浓 H2SO4 教学制臭氧总反应；H2O2 作为可能中间/副产物保留。

### norm-ch14-004

record_id: `norm-ch14-004`
canonical_title: 过氧化氢的制备
target_path_hint: 第14章 氧族元素 / 三、过氧化氢的制备与性质 / 过氧化氢的制备
sources: `实验描述1.docx#23`, `30点位例子.txt#2`
principle_mode: equation
reaction_equations_text:

```text
Na2O2 + 2H2O -> 2NaOH + H2O2
2H2O2 -> 2H2O + O2
2Na2O2 + 2H2O -> 4NaOH + O2 // 总反应
```

phenomenon_explanation: Na2O2 溶于冰水中迅速溶解并产生大量无色 O2，溶液呈强碱性；滴加冷却的稀 H2SO4 至酸性后，溶液由碱性变为酸性。
safety_note: Na2O2 具有强氧化性和腐蚀性；反应放热剧烈，必须冰水冷却；H2SO4 具腐蚀性。
normalization_notes: duplicate_related_to_sodium_combustion；源 30 的钠燃烧产物加水段可作为本记录的重复/关联来源。

### norm-ch14-005

record_id: `norm-ch14-005`
canonical_title: 过氧化氢的鉴定
target_path_hint: 第14章 氧族元素 / 三、过氧化氢的制备与性质 / 过氧化氢的鉴定
sources: `实验描述1.docx#24`
principle_mode: equation
reaction_equations_text:

```text
2CrO4^2- + 2H+ -> Cr2O7^2- + H2O
Cr2O7^2- + 4H2O2 + 2H+ -> 2CrO5 + 5H2O
```

phenomenon_explanation: 水层酸化后由黄色变橙色，加入 H2O2 后生成蓝色 CrO5；振荡后乙醚层呈亮蓝色，静置分层。
safety_note: 乙醚易挥发且易燃，远离火源并在通风橱中操作；H2SO4 和 Cr(VI) 化合物具腐蚀性和毒性；含铬和乙醚废液回收。
normalization_notes: source_has_glued_equations；已拆分铬酸根酸化和过氧铬生成反应。

### norm-ch14-006

record_id: `norm-ch14-006`
canonical_title: 过氧化氢的酸性
target_path_hint: 第14章 氧族元素 / 三、过氧化氢的制备与性质 / 过氧化氢的性质 / 过氧化氢的酸性
sources: `30点位例子.txt#29`, `实验描述1.docx#25`
principle_mode: equation
reaction_equations_text:

```text
2H2O2 -> 2H2O + O2 // 碱性条件下催化分解
```

phenomenon_explanation: 向 NaOH 和乙醇体系中加入 H2O2，剧烈产生无色 O2 气泡，溶液迅速冒泡并可能轻微放热。
safety_note: 高浓度 H2O2 与浓碱混合分解剧烈，可能喷溅，应小量、通风橱操作；40% NaOH 强腐蚀。
normalization_notes: user_kept_source；用户要求保留；标题称“酸性”但实验正文源内容体现碱性条件下 H2O2 不稳定，暂不补写弱酸电离/成盐口径。

### norm-ch14-007

record_id: `norm-ch14-007`
canonical_title: H2O2 + KI | 酸性体系
target_path_hint: 第14章 氧族元素 / 三、过氧化氢的制备与性质 / 过氧化氢的性质 / 过氧化氢的氧化性 / H2O2 + KI | 酸性体系
sources: `30点位例子.txt#30`, `实验描述1.docx#26`
principle_mode: equation
reaction_equations_text:

```text
H2O2 + 2I- + 2H+ -> I2 + 2H2O
```

phenomenon_explanation: 酸化后的 H2O2 中滴加 KI，溶液由无色逐渐变为棕黄色；加入淀粉立即变蓝，说明生成 I2。
safety_note: H2SO4 具腐蚀性，避免皮肤接触；含 I2 废液应回收处理。
normalization_notes: duplicate_merged。

### norm-ch14-008

record_id: `norm-ch14-008`
canonical_title: PbS + H2O2
target_path_hint: 第14章 氧族元素 / 三、过氧化氢的制备与性质 / 过氧化氢的性质 / 过氧化氢的氧化性 / Pb(NO3)2 + Na2S + H2O2
sources: `实验描述1.docx#27`
principle_mode: equation
reaction_equations_text:

```text
PbS + 4H2O2 -> PbSO4 + 4H2O
```

phenomenon_explanation: 黑色 PbS 沉淀逐渐转化为白色 PbSO4，同时可能产生少量 O2 气泡。
safety_note: PbS 和 PbSO4 含重金属铅，避免皮肤接触，废液回收；H2O2 具氧化性和腐蚀性。
normalization_notes: source_title_uses_reagents；主反应以实际黑色沉淀 PbS 被氧化为 PbSO4 表示。

### norm-ch14-009

record_id: `norm-ch14-009`
canonical_title: H2O2 + KMnO4 | 酸性体系
target_path_hint: 第14章 氧族元素 / 三、过氧化氢的制备与性质 / 过氧化氢的性质 / 过氧化氢的还原性 / H2O2 + KMnO4 | 酸性体系
sources: `实验描述1.docx#28`, `30点位例子.txt#2`
principle_mode: equation
reaction_equations_text:

```text
2KMnO4 + 5H2O2 + 3H2SO4 -> K2SO4 + 2MnSO4 + 5O2 + 8H2O
```

phenomenon_explanation: 酸化后的 H2O2 中滴加 KMnO4，紫红色迅速褪去，生成无色 Mn2+，并产生大量无色 O2 气泡。
safety_note: H2SO4 具腐蚀性；KMnO4 具氧化性和刺激性，避免皮肤接触。
normalization_notes: duplicate_related；源 30 中作为钠燃烧产物检验的一部分出现，本文作为独立 H2O2 还原性点位。

### norm-ch14-010

record_id: `norm-ch14-010`
canonical_title: AgNO3 + H2O2 | 碱性及中性体系
target_path_hint: 第14章 氧族元素 / 三、过氧化氢的制备与性质 / 过氧化氢的性质 / 过氧化氢的还原性 / AgNO3 + H2O2 | 碱性及中性体系
sources: `实验描述1.docx#29`
principle_mode: equation
reaction_equations_text:

```text
Ag2O + H2O2 -> 2Ag + O2 + H2O // 碱性条件
2Ag+ + H2O2 -> 2Ag + O2 + 2H+ // 中性或酸性条件，反应较慢
```

phenomenon_explanation: 碱性条件下先生成棕色 Ag2O，再加入 H2O2，沉淀转为黑色银粉并产生 O2；中性/酸性条件下反应缓慢，可能较久后析出黑色银沉淀。
safety_note: NaOH 和 AgNO3 具腐蚀性；含 Ag 废液应回收处理。
normalization_notes: source_has_glued_equations；已拆为碱性与中性/酸性两行。

### norm-ch14-011

record_id: `norm-ch14-011`
canonical_title: H2O2 | 加热
target_path_hint: 第14章 氧族元素 / 三、过氧化氢的制备与性质 / 过氧化氢的性质 / 过氧化氢的分解 / H2O2 | 加热
sources: `实验描述1.docx#31`
principle_mode: equation
reaction_equations_text:

```text
2H2O2 -> 2H2O + O2 // 加热分解
```

phenomenon_explanation: 加热 3% H2O2 溶液，产生大量无色 O2 气泡。
safety_note: 加热时试管口勿对人，防止热液喷溅。
normalization_notes: new_from_docx1。

### norm-ch14-012

record_id: `norm-ch14-012`
canonical_title: H2O2 + MnO2
target_path_hint: 第14章 氧族元素 / 三、过氧化氢的制备与性质 / 过氧化氢的性质 / 过氧化氢的分解 / H2O2 + MnO2
sources: `实验描述1.docx#32`
principle_mode: equation
reaction_equations_text:

```text
2H2O2 -> 2H2O + O2 // MnO2 催化
```

phenomenon_explanation: 向 H2O2 中加入 MnO2 固体，立即产生大量 O2 气泡，黑色 MnO2 悬浮但反应后性状基本不变。
safety_note: 反应剧烈，试管口勿对人。
normalization_notes: new_from_docx1；催化剂写入 `//` 注释。

### norm-ch14-013

record_id: `norm-ch14-013`
canonical_title: H2O2 + 铁粉
target_path_hint: 第14章 氧族元素 / 三、过氧化氢的制备与性质 / 过氧化氢的性质 / 过氧化氢的分解 / H2O2 + 铁粉
sources: `实验描述1.docx#33`
principle_mode: equation
reaction_equations_text:

```text
2H2O2 -> 2H2O + O2 // Fe 催化分解
2Fe + 3H2O2 -> 2Fe^3+ + 6OH- // 源文档副反应，已配平但介质依赖
```

phenomenon_explanation: 铁粉表面迅速产生 O2 气泡，铁粉逐渐溶解，溶液由无色变为浅黄色或浅绿色，反应放热。
safety_note: 反应可能放热，试管口勿对人。
normalization_notes: user_kept_source；用户要求保留；第二条源反应已确认配平，介质表达依源文档暂不外改。

### norm-ch14-014

record_id: `norm-ch14-014`
canonical_title: 二氧化硫的制备
target_path_hint: 第14章 氧族元素 / 二氧化硫的制备与性质 / 二氧化硫的制备
sources: `实验描述1.docx#34`
principle_mode: equation
reaction_equations_text:

```text
Na2SO3 + H2SO4 -> Na2SO4 + SO2 + H2O // 浓硫酸条件
```

phenomenon_explanation: 向 Na2SO3 固体中缓慢滴加浓硫酸，立即产生大量无色、有刺激性气味的 SO2，加热时气体产生速率加快。
safety_note: SO2 有毒，必须在通风橱中操作；浓硫酸具强腐蚀性。
normalization_notes: needs_catalog_mapping。

### norm-ch14-015

record_id: `norm-ch14-015`
canonical_title: 二氧化硫的还原性
target_path_hint: 第14章 氧族元素 / 二氧化硫的性质 / 二氧化硫的还原性
sources: `实验描述1.docx#35`
principle_mode: equation
reaction_equations_text:

```text
2KMnO4 + 5SO2 + 2H2O -> K2SO4 + 2MnSO4 + 2H2SO4
```

phenomenon_explanation: 向酸化 KMnO4 溶液中通入 SO2，紫红色逐渐褪去，溶液变为无色或浅粉色。
safety_note: SO2 有毒，在通风橱中操作；H2SO4 具腐蚀性。
normalization_notes: new_from_docx1。

### norm-ch14-016

record_id: `norm-ch14-016`
canonical_title: 二氧化硫的氧化性
target_path_hint: 第14章 氧族元素 / 二氧化硫的性质 / 二氧化硫的氧化性
sources: `实验描述1.docx#36`
principle_mode: equation
reaction_equations_text:

```text
SO2 + 2H2S -> 3S + 2H2O
```

phenomenon_explanation: 向 H2S 溶液中通入 SO2，溶液变浑浊，生成乳白色或淡黄色 S 沉淀。
safety_note: SO2 和 H2S 均有毒，在通风橱中操作；废液回收处理。
normalization_notes: new_from_docx1。

### norm-ch14-017

record_id: `norm-ch14-017`
canonical_title: 二氧化硫的漂白作用
target_path_hint: 第14章 氧族元素 / 二氧化硫的性质 / 二氧化硫的漂白作用
sources: `实验描述1.docx#37`
principle_mode: text
principle_text: SO2 可与品红等有色物质形成不稳定的无色加成化合物，表现为可逆漂白；加热后无色加成物分解，颜色恢复。
phenomenon_explanation: 向品红溶液中通入 SO2，红色逐渐褪为无色；加热后无色溶液又恢复红色。
safety_note: SO2 有毒，在通风橱中操作。
normalization_notes: non_formula_organic_dye；暂用 text 模式。

### norm-ch14-018

record_id: `norm-ch14-018`
canonical_title: 硫代硫酸钠的歧化分解
target_path_hint: 第14章 氧族元素 / 六、硫代硫酸钠的制备与性质 / 硫代硫酸钠的歧化分解
sources: `实验描述1.docx#38`
principle_mode: equation
reaction_equations_text:

```text
Na2S2O3 + 2HCl -> 2NaCl + S + SO2 + H2O
```

phenomenon_explanation: 向 Na2S2O3 溶液中滴加 HCl，立即产生乳白色浑浊并放出有刺激性气味的 SO2。
safety_note: SO2 有毒，在通风橱中操作；HCl 具腐蚀性。
normalization_notes: new_from_docx1。

### norm-ch14-019

record_id: `norm-ch14-019`
canonical_title: 硫代硫酸钠的配位性
target_path_hint: 第14章 氧族元素 / 六、硫代硫酸钠的制备与性质 / 硫代硫酸钠的配位性
sources: `实验描述1.docx#39`
principle_mode: equation
reaction_equations_text:

```text
2Ag+ + S2O3^2- -> Ag2S2O3 // 白色沉淀
Ag2S2O3 + H2O -> Ag2S + H2SO4 // 沉淀转黑
Ag2S2O3 + 3S2O3^2- -> 2[Ag(S2O3)2]^3- // Na2S2O3 过量时络合溶解
```

phenomenon_explanation: 滴加 Na2S2O3 先生成白色沉淀，迅速变黄、棕并最终变黑；Na2S2O3 过量时，未转化或新生成的 Ag(I) 以 [Ag(S2O3)2]^3- 形式进入溶液，沉淀减少或溶解；已完全转黑的 Ag2S 不宜用该络合式直接表示。
safety_note: AgNO3 具腐蚀性和毒性；含重金属银废液应回收。
normalization_notes: researched_update；已拆分沉淀、转化、络合溶解三步；第三步改为守恒的 Ag2S2O3 与过量 S2O3^2- 络合溶解式，不再写 Ag2S 直接生成单个配离子。

### norm-ch14-020

record_id: `norm-ch14-020`
canonical_title: MnSO4 + K2S2O8（+ AgNO3）| 酸性体系
target_path_hint: 第14章 氧族元素 / 七、过二硫酸盐的氧化性 / MnSO4 + K2S2O8（+ AgNO3） | 酸性体系
sources: `实验描述1.docx#40`
principle_mode: equation
reaction_equations_text:

```text
2Mn^2+ + 5S2O8^2- + 8H2O -> 2MnO4- + 10SO4^2- + 16H+ // Ag+ 催化
```

phenomenon_explanation: MnSO4 溶液中加入 H2SO4、AgNO3 和 K2S2O8 后水浴加热，溶液由无色逐渐变为紫红色；不加 AgNO3 对照无明显现象。
safety_note: H2SO4 具腐蚀性；AgNO3 具毒性；含重金属废液回收处理。
normalization_notes: new_from_docx1；催化剂保留为 `//` 注释。

### norm-ch14-021

record_id: `norm-ch14-021`
canonical_title: KI + K2S2O8 | 酸性体系
target_path_hint: 第14章 氧族元素 / 七、过二硫酸盐的氧化性 / KI + K2S2O8 | 酸性体系
sources: `实验描述1.docx#41`
principle_mode: equation
reaction_equations_text:

```text
S2O8^2- + 2I- -> 2SO4^2- + I2
```

phenomenon_explanation: 向酸化 KI 溶液中加入 K2S2O8，溶液由无色变为棕黄色，说明生成 I2。
safety_note: H2SO4 具腐蚀性；含 I2 废液应回收。
normalization_notes: new_from_docx1。

### norm-ch15-001

record_id: `norm-ch15-001`
canonical_title: 亚硝酸的生成与分解
target_path_hint: 第15章 氮族元素 / 二、亚硝酸及其盐的性质 / 亚硝酸的生成与分解
sources: `30点位例子.txt#7`, `实验描述1.docx#42`
principle_mode: equation
reaction_equations_text:

```text
2NaNO2 + H2SO4 -> 2HNO2 + Na2SO4
2HNO2 -> N2O3 + H2O // 淡蓝色
N2O3 -> NO + NO2 // 红棕色气体来自 NO2
2HNO2 -> NO + NO2 + H2O
3NO2 + H2O -> NO + 2HNO3
```

phenomenon_explanation: 冰水冷却的饱和 NaNO2 溶液与稀 H2SO4 混合后，溶液由无色变蓝，同时产生红棕色 NO2；放置后蓝色褪去，溶液变无色，红棕色气体逐渐消失。
safety_note: NO 和 NO2 有毒，必须在通风橱中操作；H2SO4 和生成的 HNO3 具腐蚀性；低温操作注意防冻；含亚硝酸盐/硝酸盐废液回收。
normalization_notes: duplicate_merged；源 DOCX 粘连反应已拆分。

### norm-ch15-002

record_id: `norm-ch15-002`
canonical_title: 亚硝酸的氧化性
target_path_hint: 第15章 氮族元素 / 二、亚硝酸及其盐的性质 / 亚硝酸的氧化性
sources: `30点位例子.txt#8`, `实验描述2.docx#1`
principle_mode: equation
reaction_equations_text:

```text
2NO2- + 2I- + 4H+ -> 2NO + I2 + 2H2O
2NO + O2 -> 2NO2
2HNO2 -> NO + NO2 + H2O // 加热或不稳定分解
```

phenomenon_explanation: 常温下酸化 KI 中加入 NaNO2 后溶液变棕黄色，试管口有红棕色 NO2；加热时棕黄色加深，随后因 I2 升华颜色变浅，并出现紫红色碘蒸气和红棕色气体。
safety_note: NO 和 NO2 有毒，必须在通风橱中操作；H2SO4 具腐蚀性；微热时用试管夹，废液回收。
normalization_notes: duplicate_merged；DOCX2 粘连的 NO 氧化反应已拆分。

### norm-ch15-003

record_id: `norm-ch15-003`
canonical_title: 亚硝酸的还原性
target_path_hint: 第15章 氮族元素 / 二、亚硝酸及其盐的性质 / 亚硝酸的还原性
sources: `30点位例子.txt#9`, `实验描述2.docx#3`
principle_mode: equation
reaction_equations_text:

```text
5NO2- + 2MnO4- + 6H+ -> 5NO3- + 2Mn^2+ + 3H2O
```

phenomenon_explanation: 未酸化时 KMnO4 紫红色无明显变化；酸化后紫红色迅速褪去，变为无色或极浅粉红色，同时可能因 HNO2 分解产生少量气泡。
safety_note: H2SO4 具腐蚀性；含 KMnO4 和亚硝酸盐废液应回收处理。
normalization_notes: duplicate_merged。

### norm-ch15-004

record_id: `norm-ch15-004`
canonical_title: NaNO2 + 对氨基苯磺酸 + 萘胺 | HAc 酸性体系
target_path_hint: 第15章 氮族元素 / 二、亚硝酸及其盐的性质 / 亚硝酸根的检验方法 / NaNO2 + 对氨基苯磺酸 + 萘胺 | HAc酸性体系
sources: `30点位例子.txt#10`, `实验描述2.docx#5`
principle_mode: text
principle_text: 在 HAc 酸性条件下，NO2- 与对氨基苯磺酸、萘胺发生重氮化-偶合反应，生成粉红色偶氮化合物，可灵敏检验 NO2-。
phenomenon_explanation: 点滴板上用 HAc 酸化 NaNO2 后加入对氨基苯磺酸和萘胺，溶液显粉红色。
safety_note: HAc 具腐蚀性；对氨基苯磺酸和萘胺有一定毒性，避免吸入或皮肤接触，实验后洗手；含有机试剂和亚硝酸盐废液回收。
normalization_notes: duplicate_merged；有机偶氮反应用 text 模式更稳。

### norm-ch15-005

record_id: `norm-ch15-005`
canonical_title: NaNO2 + KI + CCl4 | H2SO4 酸性体系
target_path_hint: 第15章 氮族元素 / 二、亚硝酸及其盐的性质 / 亚硝酸根的检验方法 / NaNO2 + KI + CCl4 | H2SO4酸性体系
sources: `30点位例子.txt#11`, `实验描述2.docx#6`
principle_mode: equation
reaction_equations_text:

```text
2NO2- + 2I- + 4H+ -> I2 + 2NO + 2H2O
```

phenomenon_explanation: NaNO2 溶液中加入 KI 和 CCl4，并酸化振荡后，CCl4 层显紫色，说明 I- 被 NO2- 氧化为 I2。
safety_note: NO 有毒，应在通风处或通风橱操作；H2SO4 具腐蚀性；CCl4 有毒，废液回收。
normalization_notes: duplicate_merged。

### norm-ch15-006

record_id: `norm-ch15-006`
canonical_title: 浓硝酸 + 硫粉
target_path_hint: 第15章 氮族元素 / 三、硝酸及其盐的性质 / 硝酸的氧化性 / 浓硝酸 + 硫粉
sources: `30点位例子.txt#12`, `实验描述2.docx#7`
principle_mode: equation
reaction_equations_text:

```text
S + 6HNO3 -> H2SO4 + 6NO2 + 2H2O // 浓硝酸，加热
```

phenomenon_explanation: 加热条件下硫粉溶解，产生大量红棕色 NO2，溶液可能变浑浊。
safety_note: NO2 有毒，必须在通风橱中操作；浓硝酸强腐蚀；加热时用试管夹。
normalization_notes: duplicate_merged。

### norm-ch15-007

record_id: `norm-ch15-007`
canonical_title: 浓硝酸 + Na2S
target_path_hint: 第15章 氮族元素 / 三、硝酸及其盐的性质 / 硝酸的氧化性 / 浓硝酸 + Na2S
sources: `30点位例子.txt#13`, `实验描述2.docx#8`
principle_mode: equation
reaction_equations_text:

```text
Na2S + 4HNO3 -> S + 2NaNO3 + 2NO2 + 2H2O // 浓硝酸条件
S + 6HNO3 -> H2SO4 + 6NO2 + 2H2O // 硝酸过量时，S 可继续被氧化为 SO4^2-
```

phenomenon_explanation: 剧烈反应，产生大量红棕色 NO2，析出淡黄色 S 沉淀。
safety_note: NO2 有毒，通风橱操作；浓硝酸强腐蚀；反应剧烈，试管口勿对人。
normalization_notes: duplicate_merged；过量硝酸进一步氧化写作注释/补充反应。

### norm-ch15-008

record_id: `norm-ch15-008`
canonical_title: 浓硝酸/稀硝酸 + 铜
target_path_hint: 第15章 氮族元素 / 三、硝酸及其盐的性质 / 硝酸的氧化性 / 浓硝酸/稀硝酸 + 铜
sources: `30点位例子.txt#14`, `实验描述2.docx#9`
principle_mode: equation
reaction_equations_text:

```text
Cu + 4HNO3 -> Cu(NO3)2 + 2NO2 + 2H2O // 浓硝酸
3Cu + 8HNO3 -> 3Cu(NO3)2 + 2NO + 4H2O // 稀硝酸
2NO + O2 -> 2NO2
```

phenomenon_explanation: 浓硝酸中铜片溶解，溶液变蓝绿色并产生大量红棕色 NO2；稀硝酸中铜片溶解，溶液变蓝，产生无色 NO，试管口遇空气变红棕色。
safety_note: NO2 有毒，通风橱操作；浓硝酸强腐蚀；含 Cu2+ 废液回收。
normalization_notes: duplicate_merged；DOCX2 粘连的 NO 氧化反应已拆分。

### norm-ch15-009

record_id: `norm-ch15-009`
canonical_title: KNO3 | 加热
target_path_hint: 第15章 氮族元素 / 三、硝酸及其盐的性质 / 硝酸盐的热分解 / KNO3 | 加热
sources: `实验描述2.docx#12`
principle_mode: equation
reaction_equations_text:

```text
2KNO3 -> 2KNO2 + O2 // 加热
```

phenomenon_explanation: 加热 KNO3 固体，产生能使带火星木条复燃的 O2，固体熔化后冷却凝固。
safety_note: 加热时试管口勿对人；高温下硝酸盐与有机物接触可能爆炸。
normalization_notes: new_from_docx2。

### norm-ch15-010

record_id: `norm-ch15-010`
canonical_title: Cu(NO3)2 | 加热
target_path_hint: 第15章 氮族元素 / 三、硝酸及其盐的性质 / 硝酸盐的热分解 / Cu(NO3)2 | 加热
sources: `实验描述2.docx#13`
principle_mode: equation
reaction_equations_text:

```text
2Cu(NO3)2 -> 2CuO + 4NO2 + O2 // 加热
```

phenomenon_explanation: 加热 Cu(NO3)2 固体，产生红棕色 NO2 和能使带火星木条复燃的 O2，固体由蓝色变黑色 CuO。
safety_note: NO2 有毒，通风橱操作；加热时试管口勿对人；含 Cu 废液回收。
normalization_notes: new_from_docx2。

### norm-ch15-011

record_id: `norm-ch15-011`
canonical_title: AgNO3 | 加热
target_path_hint: 第15章 氮族元素 / 三、硝酸及其盐的性质 / 硝酸盐的热分解 / AgNO3 | 加热
sources: `实验描述2.docx#14`
principle_mode: equation
reaction_equations_text:

```text
2AgNO3 -> 2Ag + 2NO2 + O2 // 加热
```

phenomenon_explanation: 加热 AgNO3 固体，产生红棕色 NO2 和 O2，固体由白色变黑色 Ag。
safety_note: NO2 有毒，通风橱操作；加热时试管口勿对人；含 Ag 废液回收。
normalization_notes: new_from_docx2。

### norm-ch15-012

record_id: `norm-ch15-012`
canonical_title: NaNO3 + NaOH + 铝屑 | pH 试纸
target_path_hint: 第15章 氮族元素 / 三、硝酸及其盐的性质 / 硝酸根的检验 / NaNO3 + NaOH + 铝屑 | pH试纸
sources: `实验描述2.docx#15`
principle_mode: equation
reaction_equations_text:

```text
NO3- + 4Al + 7OH- + 6H2O -> NH3 + 4[Al(OH)4]-
```

phenomenon_explanation: NaNO3 溶液中加入 NaOH 和铝屑后加热，湿润红色石蕊试纸变蓝，说明 NO3- 被还原为 NH3。
safety_note: NaOH 具腐蚀性；加热时试管口勿对人；NH3 有刺激性气味，在通风橱中操作。
normalization_notes: new_from_docx2。

### norm-ch15-013

record_id: `norm-ch15-013`
canonical_title: FeSO4·7H2O + NaNO3 + 浓硫酸
target_path_hint: 第15章 氮族元素 / 三、硝酸及其盐的性质 / 硝酸根的检验 / FeSO4·7H2O + NaNO3 + 浓硫酸
sources: `30点位例子.txt#15`, `实验描述2.docx#16`
principle_mode: equation
reaction_equations_text:

```text
3Fe^2+ + NO3- + 4H+ -> 3Fe^3+ + NO + 2H2O
Fe^2+ + NO + SO4^2- -> [Fe(NO)]SO4 // 棕色环配合物，按源文档保留
```

phenomenon_explanation: 斜持试管，沿管壁缓慢加入浓 H2SO4 后，两液面交界处出现棕色环，说明生成亚硝酸合铁(II)配合物，可用于检验 NO3-。
safety_note: 浓 H2SO4 强腐蚀，应缓慢沿管壁加入并防飞溅；含重金属铁废液回收。
normalization_notes: duplicate_merged；user_kept_source；源 30 中第二式系数写作 `3Fe2+ + NO + SO4^2-`，本稿按源 DOCX 语义保留一分子 Fe(II) 参与；按用户要求保留源式 `[Fe(NO)]SO4` 表达。

### norm-ch17-001

record_id: `norm-ch17-001`
canonical_title: 难溶性硅酸盐的生成 - 水中花园
target_path_hint: 第17章 硼族元素 / 一、硼、硅的相似相异性 / 难溶性硅酸盐的生成——“水中花园”
sources: `30点位例子.txt#16`, `实验描述2.docx#17`
principle_mode: text
principle_text: Na2SiO3 溶液与 Ca2+、Cu2+、Co2+、Ni2+、Mn2+、Zn2+、Fe2+/Fe3+ 等金属离子反应，生成难溶、有色金属硅酸盐胶体或沉淀；沉淀膜的半透性与渗透压作用造成枝状或芽状生长。
phenomenon_explanation: 金属盐与硅酸钠接触处形成不同颜色的金属硅酸盐胶体和半透膜，水不断渗入并胀破膜层，反复生成树枝状或花园状结构。
safety_note: 水玻璃呈碱性并具腐蚀性；Co、Ni、Mn、Cu 等重金属盐有毒，避免接触和吸入；含重金属废液回收。
normalization_notes: duplicate_merged；泛化 `M2+` 不利于方程式解析，采用 text 模式。

### norm-ch18-001

record_id: `norm-ch18-001`
canonical_title: 锂、钠、钾、钙、锶、钡盐的焰色反应
target_path_hint: 第18章 碱金属和碱土金属 / 五、焰色反应 / 锂、钠、钾、钙、锶、钡盐的焰色反应
sources: `30点位例子.txt#1`, `实验描述2.docx#27`
principle_mode: text
principle_text: 金属原子受热时，外层价电子吸收能量由基态跃迁至激发态，随后以辐射形式回到较低能级并释放特征频率光子。不同元素原子能级差不同，因此呈现特征焰色；观察 K+ 的紫色需用钴玻璃滤除 Na+ 黄光干扰。
phenomenon_explanation: Li+ 呈洋红/紫红色，Na+ 呈明亮黄色，K+ 呈紫色且需透过钴玻璃观察，Ca2+ 呈砖红/橙红色，Sr2+ 呈猩红/洋红色，Ba2+ 呈黄绿色。
safety_note: 灼烧后的镍丝温度高，冷却前勿触碰；浓盐酸具腐蚀性，蘸取时避免接触皮肤；若用酒精灯，应防止高温镍丝接触酒精蒸气；含金属离子废液回收。
normalization_notes: duplicate_merged；非反应方程式原理，使用 text 模式。

### norm-ch18-002

record_id: `norm-ch18-002`
canonical_title: 钠加热燃烧实验
target_path_hint: 第18章 碱金属和碱土金属 / 一、碱金属、碱土金属单质活泼性的比较 / 钠加热燃烧实验
sources: `30点位例子.txt#2`, `实验描述2.docx#18`
principle_mode: equation
reaction_equations_text:

```text
2Na + O2 -> Na2O2 // 主要产物
Na2O2 + 2H2O -> 2NaOH + H2O2
2Na2O2 + 2H2O -> 4NaOH + O2
2H2O2 -> 2H2O + O2
2KMnO4 + 5H2O2 + 3H2SO4 -> K2SO4 + 2MnSO4 + 5O2 + 8H2O // 酸化后用 KMnO4 验证 H2O2
```

phenomenon_explanation: 钠受热先熔成银白色小球，随后剧烈燃烧并发出黄色火焰，生成淡黄色 Na2O2；产物遇水剧烈反应，放出 O2，溶液呈强碱性；酸化后加 KMnO4，紫色迅速褪去并可能产生气泡。
safety_note: 钠燃烧剧烈，勿近距离直视，移除易燃物；Na2O2 强氧化、腐蚀，勿直接接触；产物加水放热，防喷溅；H2SO4 和 KMnO4 操作需戴防护。
normalization_notes: duplicate_merged；与过氧化氢制备/还原性点位存在内容交叉，导入时可建立相关实验关系。

### norm-ch18-003

record_id: `norm-ch18-003`
canonical_title: 镁条燃烧实验
target_path_hint: 第18章 碱金属和碱土金属 / 一、碱金属、碱土金属单质活泼性的比较 / 镁条燃烧实验
sources: `30点位例子.txt#3`, `实验描述2.docx#21`
principle_mode: equation
reaction_equations_text:

```text
2Mg + O2 -> 2MgO
3Mg + N2 -> Mg3N2
2Mg + CO2 -> 2MgO + C
Mg3N2 + 6H2O -> 3Mg(OH)2 + 2NH3
```

phenomenon_explanation: 镁条剧烈燃烧，发出耀眼白光并放热，生成白色 MgO，伴有白烟；空气中燃烧产物还可能含少量淡黄色 Mg3N2 和黑色碳。
safety_note: 镁燃烧强光含紫外线，严禁长时间直视；温度极高，下方垫石棉网或沙土并远离易燃物；不可用 CO2 灭火，应用干沙覆盖。
normalization_notes: duplicate_merged。

### norm-ch18-004

record_id: `norm-ch18-004`
canonical_title: 钠与水反应
target_path_hint: 第18章 碱金属和碱土金属 / 一、碱金属、碱土金属单质活泼性的比较 / 钠与水反应
sources: `30点位例子.txt#4`, `实验描述2.docx#22`
principle_mode: equation
reaction_equations_text:

```text
2Na + 2H2O -> 2NaOH + H2
```

phenomenon_explanation: 钠浮在水面，熔成银白色小球，在水面迅速游动并发出嘶嘶声，逐渐消失；有 H2 放出，滴加酚酞后溶液变红。同主族从上到下金属性增强，与水反应更剧烈。
safety_note: 反应放热并产生易燃 H2，应远离火源并用漏斗盖住烧杯口；反应后 NaOH 溶液具腐蚀性；未反应钠必须放回煤油保存。
normalization_notes: duplicate_merged；源 30 中 `AI` 应为 `Al`，现象解释已语义修正。

### norm-ch18-005

record_id: `norm-ch18-005`
canonical_title: 钾与水反应
target_path_hint: 第18章 碱金属和碱土金属 / 一、碱金属、碱土金属单质活泼性的比较 / 钾与水反应
sources: `实验描述2.docx#23`
principle_mode: equation
reaction_equations_text:

```text
2K + 2H2O -> 2KOH + H2
```

phenomenon_explanation: 钾浮在水面，熔成银白色小球并迅速燃烧，发出紫色火焰，急速游动并发出嘶嘶声；放出 H2，滴加酚酞后溶液变红。
safety_note: 钾与水反应极其剧烈，必须用漏斗盖住烧杯口，远离火源并保持观察距离；KOH 强腐蚀；未反应钾必须放回煤油。
normalization_notes: new_from_docx2；建议关联钠与水、镁/钙与水作活泼性比较。

### norm-ch18-006

record_id: `norm-ch18-006`
canonical_title: 镁与冷/热水反应
target_path_hint: 第18章 碱金属和碱土金属 / 一、碱金属、碱土金属单质活泼性的比较 / 镁与冷/热水反应
sources: `30点位例子.txt#5`, `实验描述2.docx#24`
principle_mode: equation
reaction_equations_text:

```text
Mg + 2H2O -> Mg(OH)2 + H2
```

phenomenon_explanation: 冷水中反应极慢，几乎无气泡，酚酞不变红；热水中镁表面产生大量 H2 气泡，溶液变浑浊，酚酞变红。Mg(OH)2 难溶并覆盖镁表面，加热可加快反应。
safety_note: 热水试管温度高，用试管夹夹持；反应释放 H2，远离明火，试管口勿对人；打磨镁条防划伤。
normalization_notes: duplicate_merged。

### norm-ch18-007

record_id: `norm-ch18-007`
canonical_title: 钙与水反应
target_path_hint: 第18章 碱金属和碱土金属 / 一、碱金属、碱土金属单质活泼性的比较 / 钙与水反应
sources: `30点位例子.txt#6`, `实验描述2.docx#26`
principle_mode: equation
reaction_equations_text:

```text
Ca + 2H2O -> Ca(OH)2 + H2
```

phenomenon_explanation: 钙块沉入水底，表面产生大量 H2 气泡并逐渐溶解，溶液变浑浊，滴加酚酞变红；反应比钠温和但明显比镁剧烈。
safety_note: 生成 Ca(OH)2 具腐蚀性；反应释放 H2，远离火源，试管口勿对人；反应放热，试管夹持。
normalization_notes: duplicate_merged。

### norm-ch15-014

record_id: `norm-ch15-014`
canonical_title: Sb(OH)3 + 2 mol/L HCl
target_path_hint: 第15章 氮族元素 / 六、砷、锑、铋 / 氢氧化物的性质 / Sb(OH)3的生成与性质 / SbCl3 + NaOH + 2mol/L HCl
sources: `实验描述2.docx#40`
principle_mode: equation
reaction_equations_text:

```text
Sb^3+ + 3OH- -> Sb(OH)3
Sb(OH)3 + 3H+ -> Sb^3+ + 3H2O
```

phenomenon_explanation: SbCl3 溶液中滴加适量 NaOH 生成白色 Sb(OH)3；加入 HCl 后沉淀溶解，说明 Sb(OH)3 可表现碱性。
safety_note: HCl 具腐蚀性；SbCl3 易水解，配制需盐酸酸化；废液回收处理。
normalization_notes: source_has_glued_equations；已拆分生成和酸溶反应。

### norm-ch15-015

record_id: `norm-ch15-015`
canonical_title: Sb(OH)3 + 2 mol/L NaOH
target_path_hint: 第15章 氮族元素 / 六、砷、锑、铋 / 氢氧化物的性质 / Sb(OH)3的生成与性质 / SbCl3 + NaOH + 2 mol/L NaOH
sources: `实验描述2.docx#41`
principle_mode: equation
reaction_equations_text:

```text
Sb^3+ + 3OH- -> Sb(OH)3
Sb(OH)3 + OH- -> [Sb(OH)4]- // 2 mol/L NaOH 中仅微溶，平衡偏弱
```

phenomenon_explanation: 适量 NaOH 生成白色 Sb(OH)3；加入 2 mol/L NaOH 后沉淀不溶或仅微溶，说明 Sb(OH)3 可两性溶解但该浓度下平衡偏弱。
safety_note: NaOH 具腐蚀性，避免皮肤接触。
normalization_notes: researched_update；按常见定性分析口径改为 `[Sb(OH)4]-`，保留 2 mol/L NaOH 中仅微溶现象。

### norm-ch15-016

record_id: `norm-ch15-016`
canonical_title: Sb(OH)3 + 6 mol/L NaOH
target_path_hint: 第15章 氮族元素 / 六、砷、锑、铋 / 氢氧化物的性质 / Sb(OH)3的生成与性质 / SbCl3 + NaOH + 6 mol/L NaOH
sources: `实验描述2.docx#42`
principle_mode: equation
reaction_equations_text:

```text
Sb^3+ + 3OH- -> Sb(OH)3
Sb(OH)3 + OH- -> [Sb(OH)4]- // 6 mol/L NaOH 中溶解
```

phenomenon_explanation: 适量 NaOH 生成白色 Sb(OH)3；加入 6 mol/L NaOH 后沉淀溶解，说明较高浓度碱可使 Sb(OH)3 表现酸性并形成 [Sb(OH)4]- 等可溶羟基配合物。
safety_note: 6 mol/L NaOH 强腐蚀，避免皮肤接触。
normalization_notes: researched_update；按常见定性分析口径改为 `[Sb(OH)4]-`，保留 6 mol/L NaOH 中溶解现象。

### norm-ch15-017

record_id: `norm-ch15-017`
canonical_title: Bi(OH)3 + 2 mol/L HCl
target_path_hint: 第15章 氮族元素 / 六、砷、锑、铋 / 氢氧化物的性质 / Bi(OH)3的生成与性质 / Bi(NO3)3 + NaOH + 2mol/L HCl
sources: `实验描述2.docx#44`
principle_mode: equation
reaction_equations_text:

```text
Bi^3+ + 3OH- -> Bi(OH)3
Bi(OH)3 + 3H+ -> Bi^3+ + 3H2O
```

phenomenon_explanation: Bi(NO3)3 溶液中加 NaOH 生成白色 Bi(OH)3，加入 HCl 后沉淀溶解，说明 Bi(OH)3 显碱性。
safety_note: HCl 具腐蚀性；废液回收处理。
normalization_notes: source_has_glued_equations；已拆分。

### norm-ch15-018a

record_id: `norm-ch15-018a`
canonical_title: Bi(OH)3 + 6 mol/L NaOH
target_path_hint: 第15章 氮族元素 / 六、砷、锑、铋 / 氢氧化物的性质 / Bi(OH)3的生成与性质 / Bi(NO3)3 + NaOH + 6 mol/L NaOH
sources: `实验描述2.docx#45`
principle_mode: equation
reaction_equations_text:

```text
Bi^3+ + 3OH- -> Bi(OH)3 // 生成白色沉淀
```

phenomenon_explanation: Bi(OH)3 白色沉淀中加入 6 mol/L NaOH 溶液，沉淀不溶解，说明 Bi(OH)3 为碱性氢氧化物，不具有明显两性。
safety_note: 6 mol/L NaOH 具强腐蚀性，避免皮肤接触。
normalization_notes: split_from_merged_close_variants；与 `norm-ch15-018b` 原理相同，但碱浓度、现象描述和安全提示不同；导入时绑定 6 mol/L NaOH 点位。

### norm-ch15-018b

record_id: `norm-ch15-018b`
canonical_title: Bi(OH)3 + 40% NaOH
target_path_hint: 第15章 氮族元素 / 六、砷、锑、铋 / 氢氧化物的性质 / Bi(OH)3的生成与性质 / Bi(NO3)3 + NaOH + 40% NaOH
sources: `实验描述2.docx#46`
principle_mode: equation
reaction_equations_text:

```text
Bi^3+ + 3OH- -> Bi(OH)3 // 生成白色沉淀
```

phenomenon_explanation: Bi(OH)3 白色沉淀中加入 40% NaOH 溶液，沉淀不溶解或仅微溶，说明 Bi(OH)3 为碱性氢氧化物，不具有明显两性。
safety_note: 40% NaOH 具强腐蚀性，避免皮肤接触。
normalization_notes: split_from_merged_close_variants；与 `norm-ch15-018a` 原理相同，但碱浓度、现象描述和安全提示不同；导入时绑定 40% NaOH 点位。

### norm-ch16-001

record_id: `norm-ch16-001`
canonical_title: Pb(OH)2 + HNO3
target_path_hint: 第16章 碳族元素 / 五、锡、铅 / 氢氧化物的性质 / Pb(OH)2的生成与性质 / Pb(NO3)2 + NaOH + 2 mol/L HNO3
sources: `实验描述2.docx#33`, `实验描述2.docx#34`
principle_mode: equation
reaction_equations_text:

```text
Pb^2+ + 2OH- -> Pb(OH)2
Pb(OH)2 + 2H+ -> Pb^2+ + 2H2O
```

phenomenon_explanation: Pb(NO3)2 溶液中滴加适量 NaOH 生成白色 Pb(OH)2；加入 HNO3 后沉淀溶解，说明 Pb(OH)2 可表现碱性。
safety_note: NaOH 和 HNO3 具腐蚀性；Pb2+ 为重金属离子，废液回收处理。
normalization_notes: source_split_generation_and_acid_dissolution；导入目录若有独立“生成”和“酸溶”点位，可拆分。

### norm-ch16-002

record_id: `norm-ch16-002`
canonical_title: Pb(OH)2 + 过量 NaOH
target_path_hint: 第16章 碳族元素 / 五、锡、铅 / 氢氧化物的性质 / Pb(OH)2的生成与性质 / Pb(NO3)2 + NaOH + 2 mol/L NaOH
sources: `实验描述2.docx#35`
principle_mode: equation
reaction_equations_text:

```text
Pb(OH)2 + 2OH- -> [Pb(OH)4]^2- // 过量 NaOH
```

phenomenon_explanation: Pb(OH)2 白色沉淀中加入过量 NaOH，沉淀溶解，说明 Pb(OH)2 具有两性。
safety_note: NaOH 具腐蚀性；含 Pb2+ 废液回收处理。
normalization_notes: new_from_docx2。

### norm-ch16-003

record_id: `norm-ch16-003`
canonical_title: Sn(OH)2 + 过量 NaOH
target_path_hint: 第16章 碳族元素 / 五、锡、铅 / 氢氧化物的性质 / Sn(OH)2的生成与性质 / SnCl2 + NaOH + 2 mol/L NaOH
sources: `实验描述2.docx#36`
principle_mode: equation
reaction_equations_text:

```text
Sn^2+ + 2OH- -> Sn(OH)2
Sn(OH)2 + 2OH- -> [Sn(OH)4]^2-
```

phenomenon_explanation: SnCl2 溶液中滴加适量 NaOH 生成白色 Sn(OH)2；加入过量 NaOH 后沉淀溶解，说明 Sn(OH)2 具有两性。
safety_note: NaOH 具腐蚀性；SnCl2 溶液需现配现用，防止 Sn2+ 被氧化。
normalization_notes: new_from_docx2。

### norm-ch16-004

record_id: `norm-ch16-004`
canonical_title: Sn(OH)2 + HCl
target_path_hint: 第16章 碳族元素 / 五、锡、铅 / 氢氧化物的性质 / Sn(OH)2的生成与性质 / SnCl2 + NaOH + 2 mol/L HCl
sources: `实验描述2.docx#37`
principle_mode: equation
reaction_equations_text:

```text
Sn^2+ + 2OH- -> Sn(OH)2
Sn(OH)2 + 2H+ -> Sn^2+ + 2H2O
```

phenomenon_explanation: Sn(OH)2 白色沉淀中加入 HCl，沉淀溶解，说明 Sn(OH)2 可表现碱性。
safety_note: HCl 具腐蚀性；废液回收处理。
normalization_notes: source_title_duplicate_with_36；原题名疑似误写，应按酸溶语义映射。

### norm-ch16-005

record_id: `norm-ch16-005`
canonical_title: FeCl3 + SnCl2
target_path_hint: 第16章 碳族元素 / 五、锡、铅 / Sn(II)的还原性 / FeCl3 + SnCl2
sources: `实验描述2.docx#47`
principle_mode: equation
reaction_equations_text:

```text
2Fe^3+ + Sn^2+ -> 2Fe^2+ + Sn^4+
```

phenomenon_explanation: 黄色 FeCl3 溶液中滴加 SnCl2 并沸水浴加热后，溶液变浅绿色；用 KSCN 检验不变红，说明 Fe3+ 已被还原。
safety_note: FeCl3 和 SnCl2 有腐蚀性；沸水浴加热防烫伤。
normalization_notes: new_from_docx2。

### norm-ch16-006

record_id: `norm-ch16-006`
canonical_title: HgCl2 + SnCl2
target_path_hint: 第16章 碳族元素 / 五、锡、铅 / Sn(II)的还原性 / HgCl2 + SnCl2
sources: `实验描述2.docx#48`
principle_mode: equation
reaction_equations_text:

```text
SnCl2 + 2HgCl2 -> Hg2Cl2 + SnCl4
SnCl2 + Hg2Cl2 -> 2Hg + SnCl4 // SnCl2 过量时
```

phenomenon_explanation: 少量 SnCl2 使 HgCl2 生成白色 Hg2Cl2 沉淀；继续滴加过量 SnCl2，白色沉淀变黑，生成 Hg，体现 Sn2+ 的还原性。
safety_note: HgCl2 剧毒，戴手套并避免皮肤接触；含汞废液必须回收处理。
normalization_notes: new_from_docx2。

### norm-ch16-007

record_id: `norm-ch16-007`
canonical_title: PbO2 + 浓盐酸
target_path_hint: 第16章 碳族元素 / 五、锡、铅 / Pb(IV)的氧化性 / PbO2 + 浓盐酸
sources: `实验描述2.docx#50`
principle_mode: equation
reaction_equations_text:

```text
PbO2 + 4HCl -> PbCl2 + Cl2 + 2H2O // 浓盐酸条件
```

phenomenon_explanation: PbO2 棕黑色固体加入浓盐酸后逐渐溶解，产生大量黄绿色 Cl2，溶液可能因 PbCl2 微溶而变浑浊。
safety_note: Cl2 有毒，在通风橱中操作；浓盐酸具腐蚀性；PbO2 含重金属铅，废液回收。
normalization_notes: new_from_docx2。

### norm-ch16-008

record_id: `norm-ch16-008`
canonical_title: PbO2 + MnSO4 | 酸性体系
target_path_hint: 第16章 碳族元素 / 五、锡、铅 / Pb(IV)的氧化性 / PbO2 + MnSO4 | 酸性体系
sources: `实验描述2.docx#51`
principle_mode: equation
reaction_equations_text:

```text
5PbO2 + 2Mn^2+ + 5SO4^2- + 4H+ -> 2MnO4- + 5PbSO4 + 2H2O
```

phenomenon_explanation: PbO2 中加入 H2SO4 酸化的 MnSO4 并水浴加热，溶液由无色逐渐变紫红色，同时生成白色 PbSO4 沉淀。
safety_note: H2SO4 具腐蚀性；含 Pb 和 Mn 的废液应回收处理。
normalization_notes: new_from_docx2。

### norm-ch15-019

record_id: `norm-ch15-019`
canonical_title: Bi(NO3)3 + NaOH + 氯水
target_path_hint: 第15章 氮族元素 / 六、砷、锑、铋 / As(III)、Sb(III)、Bi(III)的还原性 / 与卤水反应 / Bi(NO3)3 + NaOH + 氯水
sources: `实验描述2.docx#52`
principle_mode: equation
reaction_equations_text:

```text
Bi^3+ + Na+ + 6OH- + Cl2 -> NaBiO3 + 2Cl- + 3H2O
```

phenomenon_explanation: Bi(NO3)3 溶液中加入 NaOH 和氯水并水浴加热，生成黄色 NaBiO3 沉淀，说明 Bi(III) 被 Cl2 氧化为 Bi(V)。
safety_note: Cl2 有毒，在通风橱中操作；NaOH 强腐蚀；含 Bi 重金属废液回收。
normalization_notes: new_from_docx2；reviewed_redox_charge_balanced。

### norm-ch15-020

record_id: `norm-ch15-020`
canonical_title: NaBiO3 + KI + CCl4 | 酸性体系
target_path_hint: 第15章 氮族元素 / 六、砷、锑、铋 / As(V)、Sb(V)、Bi(V)的氧化性 / 与KI的反应 / NaBiO3 + KI + 四氯化碳 | 酸性体系
sources: `实验描述2.docx#53`
principle_mode: equation
reaction_equations_text:

```text
BiO3- + 2I- + 6H+ -> Bi^3+ + I2 + 3H2O // 酸性体系直接氧化 I-，CCl4 层显紫色
BiO3- + 2Cl- + 6H+ -> Bi^3+ + Cl2 + 3H2O // 浓 HCl 条件下可生成 Cl2
Cl2 + 2I- -> 2Cl- + I2 // 间接氧化路径
```

phenomenon_explanation: 黄色 NaBiO3 在酸性 KI/CCl4 体系中可将 I- 氧化成 I2，CCl4 层呈紫色；若使用浓 HCl，黄色沉淀消失并可能产生刺激性 Cl2，Cl2 也可使 KI-淀粉试纸变蓝或使 CCl4 层显紫。
safety_note: NaBiO3 为强氧化剂；浓 HCl 具腐蚀性，若使用浓 HCl 可能产生 Cl2，必须通风橱操作；CCl4 有毒，含 Bi 重金属废液回收。
normalization_notes: researched_update；标题为 KI + CCl4，已把直接 Bi(V) 氧化 I- 净离子式置前；保留浓 HCl 产 Cl2 的源文档间接路径作为条件性路径。
