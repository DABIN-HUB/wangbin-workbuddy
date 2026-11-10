# Phase 7L-R7 预可研报告语言收口：本地交付与未闭合门禁

本轮按 `AGENTS.md`、`agent.md` 和已冻结的光伏合同，在 `main` 上修改长期 `report_claims.py`、`report_export.py`，用原两案合成 canonical 重新生成 Word；没有改 469 输入、89 公式原文、281 映射、计算算法、交易费独立来源、25 年结果或 R5 编号。R6 的真实 Word、QA 与 `32-phase7l-r6-decision-report.md` 作为对照基线。**没有引入运行时 AI：正式导出仍是 `DETERMINISTIC_RULES_AND_BOUND_EVIDENCE`；开发期编辑样稿不是 WorkBuddy Skill 的 AI 创作能力。**

## 可读性改动与真实局限

- 原文本来源分为：章节专用 `report_claims.py:_project_narrative` / `_specific_project_judgment`，`build_claim` 的输入及计算指标绑定，`report_export.py` 的图说/公式/术语显示，以及与类别、result_hash 绑定的编辑 fixture；缺证据提示仍只陈述实际缺口。并未将全部 100 项伪称为逐章 AI 撰写。
- CH03.02 分别说明 165 kWp 屋面自用余电与地面集中送出，不重复“本项目拟按/本项目按”；地面 CH03.04 只写上网销售毛额，不虚构厂区自用。CH09.01/09.04 分离合成接入电压、未批准接入点、计量边界、真实接网与交易意见。CH15.03/15.04 绑定更换停机和计划付款、模型现金税费，并与实际付款/缴税区分；屋顶 CH17.01 不再把负荷下降等同于两项收入都下降。CH13.02 解释 2026-11-06 起的合成预排与 2026-12-31 评价日的区别，不认定实际进度，也不顺延原日期。日期列定点加宽并设置 Word 不断行属性。
- CH08 两幅图说明来自 12 月/25 年实际合成序列：月合计峰谷与月份天数，逐年衰减、第 13 年逆变器更换停机及次年回升的解释；不推断真实所在地的季节辐照，也不把回升当组件性能恢复。图说位于章首、**不在 CH08.01–CH08.06 子项比较块内**。
- APP11 89 式原定义、单位、符号与适用边界保持；重复的原量纲完整文本移入共通索引，逐式引用组号并保留公式各自的运算类型提示。机器重复扫描仍有 9 个精确组/7 个相似模板组，集中于 APP11.02 的下标、边界和运算提示；不能宣称重复彻底清零或全部公式专业审定。APP12 保留 189 个受控术语，显示层拆开通用边界与条目解释，并单独标注历史编制语义，不覆写冻结 JSON；术语可读性仍有部分保留意见。
- 原 R6 到最终 R7 的正文/表格子项全文差异：屋顶 10/126、地面 7/126，其他子项未改；这不是宣称 18 章全部重写。CH01、CH02、CH04、CH05、CH07、CH08 子项、CH10–CH12、CH14、CH16、CH18 沿用 R6，经逐项三轴 QA 保留其材料与语言问题。具体逐章及旧新真实段落见被忽略的 `.runtime/solar-pv/phase7l-r7-final/before-after.md`，不在 Git 放重复的大型 DOCX。

## 两案候选、目录及 QA

| 案例 | WPS 刷新后的 DOCX SHA-256 | PDF 页数 | canonical `result_hash` |
| --- | --- | ---: | --- |
| 工商业屋顶 | `5745bc0a9835ecf9d39323347be46e1c215a9d684da1cca51abbdeecc463b3bb` | 137 | `ca4bdff3f5e89e6770d43f4dad3b4efd57d965aba6c9ba0f1b4299f99295a43f` |
| 集中式地面 | `613c356c59a24fdd68f9927c9c45413e0dee2bd62f607452b721a4bacfe829ff` | 135 | `69882cc39020f03fb3ef6cdb1a10b188c324de0f66066392970776b7495ad138` |

最终两份 DOCX/PDF、`delivery-receipt.json`、生成回执、两份 126 行三轴 QA 和对照均保存在 `.runtime/solar-pv/phase7l-r7-final/`。原 R6 Word 不覆盖。WPS 实装 **12.1.0.29161**（不误称为字面 12.0）；仅对副本执行 COM 目录更新和 PDF 转换。每案 `Heading 1=31`、`Heading 2=126`、TOC 缓存数字页码条目 `157`；逐条与对应标题核对并按 PDF 打印页码偏移 `7` 匹配可检索标题，**0 条不匹配**。R7 当前 `TOC_REFRESH=MACHINE_CHECKED`，非全页人工视觉签审；实施计划表的 XML 不断行和列宽已核对，尚无完整人工页面签核。

屋顶 QA：语言 `116 PASS/10 PARTIAL`，事实 `84 PASS/42 PARTIAL`，材料 `5 PASS/42 PARTIAL/79 FAIL`；其中 116 项正文/表格与已审 R6 全文相同，10 项改动重评，另对未改的 APP08/09 保守调整评级。地面 QA：语言 `99 PASS/27 PARTIAL`，事实 `82 PASS/44 PARTIAL`，材料 `6 PASS/46 PARTIAL/74 FAIL`；以独立 R7 初版 126 项三轴审阅为基线，119 项与之全文相同，7 项改动重评。两份 QA 中分别标明未改变文本的评级沿用，不冒充全部 252 项重新获得人工签审；语言好不消除真实屋面、地勘、接网、交易、报价及税务凭证缺口。对抗性样例为审阅判定标准，未伪称全部已运行自动化变形测试。

## 验证、保留及交付边界

- 报告专项实际命令：`PYTHONPATH=services/solar-pv-engine/src .venv/Scripts/python.exe -m pytest tests/solar-pv/test_phase7l_r2_export.py tests/solar-pv/test_phase7l_r2_v6_display.py tests/solar-pv/test_report_word_styles.py tests/solar-pv/test_report_business_semantics.py tests/solar-pv/test_report_claims_analysis.py tests/solar-pv/test_report_r3_narrative.py tests/solar-pv/test_phase7l_r2_narrative.py tests/solar-pv/test_phase7l_r2_irr_presentation.py -q`：**143 passed，6 skipped**；未重跑六小时 L3 或全量 25 年计算。用户要求下定点更新了受影响的一个原有导出断言，未删除有效断言。
- 最终生成回执与 R6 的 canonical `result_hash`、canonical 文件 SHA-256 逐案相等；DOCX ZIP 可解压；冻结计数 18章、100 正文子项、13附录、26附录子项、89公式、157标题身份、111表及两幅图；89 式/189 词仍在显示层。冻结数据/词典/公式/映射原文件本轮未改；不以只读身份比对冒充真实工程复核。
- 清理本轮可重建的 4 个中间 Word 生成目录和 1 个目录刷新审阅目录，共 17 文件；生成回执与逐项审阅结论已移到最终目录。原 R6、R4、R2 及其他产品资料未删；本轮已跟踪净删除 `0`。`git` 未跟踪 `0`；现有已跟踪历史日志有冻结引用及跨阶段来源，未经逐文件用途判断不盲删。`dist/` 中 Skill 0.1.3、Connector 0.1.2 仍在、ZIP 可读、含 manifest/license 且 Git 忽略；**均未按 R7 源码重打包**。
- `NARRATIVE_QUALITY=PARTIAL`；`MAIN_REPORT_READABILITY=PARTIAL`；`ADJACENT_DUPLICATION=PARTIAL`；`CHAPTER_SPECIFIC_ANALYSIS=PARTIAL`；`ROOFTOP_GROUND_DIFFERENTIATION=PARTIAL`；`CHART_INTERPRETATION=PASS_FOR_BOUND_SYNTHETIC_SERIES`；`APP11_FORMULA_READABILITY=PARTIAL`；`APP12_GLOSSARY_READABILITY=PARTIAL`；`TOC_REFRESH=MACHINE_CHECKED`；`FACTUAL_ALIGNMENT=PARTIAL`；`SOURCE_TRACEABILITY=PASS_WITH_SYNTHETIC_BOUNDARY`；`CANONICAL_INTEGRITY=PASS_FOR_UNCHANGED_IDENTITIES`；`REGRESSION_TESTS=PASS_FOR_LISTED_SUITE`；`WORKSPACE_HYGIENE=PASS_FOR_THIS_RUN`；`DIST_PRESERVATION=PASS_FOR_OLD_ZIPS`；`LOCAL_GIT_COMMIT` 以最终 Git 读回为准；`MATERIAL_EVIDENCE_QA=BLOCKED`；`WORKBUDDY_PLATFORM_TEST=NOT_TESTED`；`RELEASE_READY=BLOCKED`。不上传、不发布、不进入 Phase 8。
