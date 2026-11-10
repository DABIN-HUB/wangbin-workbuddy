# Phase 7L-R8 报告读者排版整改：非发布候选

## 根因与边界

- R7 的指定页眉错字和乱码，原 WPS 保存的 DOCX 页眉 XML、逐页 PDF 文本层均未复现；前置 8 页使印刷页码与 PDF 物理页差 8。未有可归因于长期页眉生成器的错字，不作关键词替换。R7 屋顶物理第 18/20/41/42/97/102 页、地面第 60/72/79/103/105/106 页及对应偏移页，文本层均为标准名称；**截图级视觉误判与真实损字仍未最终判别**。
- R7 的“十一”漏字、十六章漏“（三）”及目录 `#`，在 WPS 刷新后的两案各 157 个 Heading/目录条目与 PDF 中均未复现；R8 重新更新字段而非复用旧缓存。
- 实际表格问题来自固定纵向版心内 7/8 列缩放、英文原始状态码与长编号列，而非财务计算。R8 长期生成器添加六类表用途、明确宽度和自动分配、数字右对齐/不拆行、重复表头/防拆行；月度电量、损失原子链、运维、税费、年度现金事件和财务摘要均按业务边界拆分。原 111 张**逻辑表**映射为两案各 120 张物理表，未删除期别或更改 canonical。APP10 读者表改中文状态；精确机器 ID 留在受控资料与测算记录。
- APP11 原先是普通文本而非 OMML 数学对象；WPS PDF 提取对集合符号 `𝒪` 的缺失是实际渲染/字体问题，不是冻结公式 `η_inv,t` 被改成 `n_inv,t`。尝试仅将公式文本西文字体指定为 Cambria Math，未证明 WPS 解决该字形缺失；**FORMULA_RENDERING 仍 PARTIAL**。89 条全部正式定义和逐式符号按冻结合同继续留在 Word，不为约 5 页目标静默删掉注册字段。完整公式字段另外放入现有 S09 工作表 `FORMULA_SPEC` 记录；这是技术索引，不替代 Word 验收。
- APP12 189 条冻结词典全部保留在 Word 和 S09（`GLOSSARY`），另有两案各 24 条本项目常用术语速览；后者仅为导航，非完整释义索引，尚不能判“20–30 条读者词典”验收完成。底层发电、税费与财务计算、交易费来源、469 字段、281 映射和受控原始案例未改。

## 当前受控候选与身份

路径 `.runtime/solar-pv/phase7l-r8-final-v3/`（Git 忽略），文件分别为各案 `*-R8-光伏预可研报告.docx/.pdf`、`*-R8-测算模型.xlsx` 与 `*-R8-资料来源与假设清单.xlsx`。WPS 安装实装版本 `12.1.0.29161`；刷新生成的 DOCX 副本再转 PDF，不覆盖首次生成的源文件。

| 案例 | WPS DOCX SHA-256 | PDF SHA-256 | canonical result_hash | 页数 |
| --- | --- | --- | --- | ---: |
| 屋顶 | `1aec40ed4955204894523854d19f3dd41037a7a552c3578fff3b802b9bdbb584` | `25da2f2d146e9345fdfd9e7827152745548540e26691a3e009822db8466b6508` | `ca4bdff3f5e89e6770d43f4dad3b4efd57d965aba6c9ba0f1b4299f99295a43f` | 143 |
| 地面 | `d8efb91c5c92267f418e41e29c970634d764a16eeca8b13dec5b28c92a47fce8` | `68fe8f1d5ec17df98b03c2ee2e99fbdf0a9ff043a3a0d60e6660da3df10671b2` | `69882cc39020f03fb3ef6cdb1a10b188c324de0f66066392970776b7495ad138` | 142 |

最终候选的各 157 目录项逐标题/页码与对应 PDF 匹配，均 0 不一致；正文从物理第 9 页开始。独立 QA 对早期 R8 v1 的结论**不继承到 v3**；针对上述确切哈希的 v3 独立回执为 `.runtime/solar-pv/phase7l-r8-final-v3/independent-qa.md`，总体 **PARTIAL**：逐页页眉、目录、指定表号数值和三个单行哈希通过机器核对；屋顶物理第 64 页、地面第 63 页的 `𝒪` 在 PDF 中提取为 `�`，且 OMML 对象为 0。附录 K 各 58 页、附录 L 各 28 页，读者化排版未通过。

## 验证与待闭合项

已运行专项回归 `PYTHONPATH=services/solar-pv-engine/src .venv/Scripts/python.exe -m pytest tests/solar-pv/test_phase7l_r2_export.py tests/solar-pv/test_phase7l_r2_v6_display.py tests/solar-pv/test_report_word_styles.py tests/solar-pv/test_report_business_semantics.py tests/solar-pv/test_report_claims_analysis.py tests/solar-pv/test_report_r3_narrative.py tests/solar-pv/test_phase7l_r2_narrative.py tests/solar-pv/test_phase7l_r2_irr_presentation.py tests/solar-pv/test_phase4_data_adaptation.py -q`：148 passed、6 skipped。初次同套回归曾因 CH18.01 新读者标题与旧校验标题不一致产生 6 个失败，已在生产编号验证器保留冻结身份同时允许该显示名称，最终整套重新运行如上；一次误填不存在的 `test_source_xlsx.py` 路径退出码 4，随后改用现有 `test_phase4_data_adaptation.py`，不将失败命令伪报为通过。未新增或修改任何测试代码。

| 门禁 | 状态 | 实际依据或阻断 |
| --- | --- | --- |
| HEADER_TEXT_INTEGRITY | PASS（PDF文本层） | v3 屋顶135/135、地面134/134正文页独立逐页核对，R7指定异常页文本未复现；视觉另列 |
| TOC_NUMBERING | PASS（机器） | 两案157个标题和TOC同名，无指定的漏字或`#` |
| TOC_PAGE_MATCH | PASS（机器） | 刷新后TOC均逐项与本版PDF物理页一致，0不匹配 |
| TABLE_READABILITY | PARTIAL | 原111张逻辑表分组为120张物理表，未全部逐格视觉签审 |
| NUMERIC_COLUMN_INTEGRITY | PASS（指定表机器抽查） | v3表3/4/12/14/18及末页身份哈希核对，不能外推至全部表 |
| HEADING_DUPLICATION | PARTIAL | 157身份保留并修复CH18读者标题；未对全部126子项作语言签审 |
| FORMULA_RENDERING | PARTIAL | 89文本式、0个OMML；PDF中`𝒪`变为`�` |
| FORMULA_89_REGISTRY | PASS（静态） | 冻结89条不变；Word式数89、S09 FORMULA_SPEC数89 |
| FORMULA_SOURCE_IDENTITY | PASS（静态） | S09保存完整原定义，未改公式注册文件；视觉数学语义另为PARTIAL |
| APP11_READER_READABILITY | PARTIAL | K各58页，非约5页，仍有未修长式与重复说明 |
| GLOSSARY_189_REGISTRY | PASS（静态） | S09 GLOSSARY数189、Word完整词条189 |
| APP12_READER_READABILITY | PARTIAL | 24项速览缺简明释义；全量189条表格仍28页且列窄 |
| PROJECT_TYPE_DIFFERENTIATION | PARTIAL | 指定财务/工程事实独立抽核通过，未获两案全部子项内容签收 |
| NUMERIC_PRECISION_CONSISTENCY | PARTIAL | 明细与来源精度保留，决策摘要/正文口径未全量逐字段核对 |
| CANONICAL_INTEGRITY | PASS（身份） | 两案原result_hash不变，不等于真实项目审核 |
| SOURCE_TRACEABILITY | PASS（受控合成来源） | 两案工作簿同源、公式/词典可索引；真实工程证据缺口单列 |
| CONTENT_LANGUAGE_QA | PARTIAL | 既往R7审阅及v3指定页抽核；无全部126子项独立重评 |
| REGRESSION_TESTS | PASS（本专项） | 148 passed、6 skipped；非全仓 |
| WORKSPACE_HYGIENE | PASS（本轮清理） | 卫生工具按标记删除5个过期R8目录、24个文件含标记、6,242,390字节；保护原始案例，已跟踪净删0 |
| DIST_PRESERVATION | PASS（旧候选保留） | 原Skill 0.1.3、Connector 0.1.2 ZIP均可读取，sidecar哈希一致且Git忽略；未重打R8包 |
| LOCAL_GIT_COMMIT | 待最终Git读回 | 仅在专项通过后本地非发布WIP提交；SHA以提交后实际HEAD为准 |
| MATERIAL_EVIDENCE_QA | BLOCKED | 无真实屋顶/地勘、接网及交易工程材料签收 |
| PDF_FULL_VISUAL_REVIEW | PARTIAL | 已机器逐页页眉/目录及重点页复核，未做全页人工像素签审 |
| FOUR_FILE_GATE | PARTIAL | 每案四文件存在且同源，但公式和材料/视觉门禁未闭 |
| WORKBUDDY_PLATFORM_TEST | NOT_TESTED | 未安装/上传/运行平台 |
| RELEASE_READY | BLOCKED | 严禁把局部排版改进称为合格或已发布候选 |

当前目录仅保留 `.runtime/solar-pv/phase7l-r8-final-v3/` 一套 R8 审阅候选；原R6/R7、R4/R2受保护材料未删除。上述5份清理回执位于 `.runtime/solar-pv/hygiene-receipts/phase7l-r8-*-cleanup.json`。当前Git未跟踪的必要文档只显式暂存本文件，旧`dist`非R8构建且不可冒充新版。该文档不把PDF可打开、目录正确或合成财务数值对齐视为专业内容完成。
