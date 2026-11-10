# Phase 7L-R6 决策型报告内容整改回执

本轮仅修改报告写作、显示及受用户要求的相关回归；以本地受保护 R2 25 年合成 canonical 导出两案 Word，未修改冻结输入、公式、映射、计算、来源或两份 canonical。依据：`AGENTS.md`、`agent.md`、`02-report-outline-18-chapters.md`、`10-four-file-acceptance.md`、`12-canonical-result-contract.md`。原 R5 编号版仅用于对照；当前唯一 R6 审阅候选保存在 Git 忽略目录 `.runtime/solar-pv/phase7l-r6-current/`。

## 真实生成链与模式

正式 Skill `packages/skills/wangbin-solar-pv-prestudy/SKILL.md` 的 `scripts/run_solar_pv.py` 将用户授权输入交给既有解析与 `project` 计算入口，或读取既有 canonical，再经 `report`/`ground-report` 调用 `report_export.py:_export_report`。`ReportModel` 只读 canonical，`report_claims.py:build_claim` 组织指标、输入、来源与项目类型判断；`_item_evidence`、`_professional_narrative`、`_r4_special_narrative`、`_project_summary` 等按规则和固定文案组织段落，`_write_docx` 写入 Word。编辑性 fixture 需按项目类别和 `result_hash` 绑定，仅为演示文案背景，不进计算。当前报告导出路径**没有 LLM 调用**：`NARRATIVE_GENERATION_MODE=DETERMINISTIC_RULES_AND_BOUND_EVIDENCE`，不可宣传为 AI 逐章撰写；没有验证通过的 WorkBuddy 模型写作接口，本轮没有新增外部模型、密钥或付费依赖。Skill ZIP 与本地源码并非同一个发布构建，当前源码修复不等于平台已装载。

## 当前本地候选与追溯

| 类型 | 实际 DOCX | SHA-256 | canonical `result_hash` |
| --- | --- | --- | --- |
| 工商业屋顶 | `.runtime/solar-pv/phase7l-r6-current/工商业屋顶-R6-光伏预可研报告.docx` | `c606969b616c58e72578828f26d25859fc358202958a380f341901aa3086628d` | `ca4bdff3f5e89e6770d43f4dad3b4efd57d965aba6c9ba0f1b4299f99295a43f` |
| 集中式地面 | `.runtime/solar-pv/phase7l-r6-current/集中式地面-R6-光伏预可研报告.docx` | `1ed90435c73584652573aa4c697c577cc3e5ecea333e994382df4fbe1caea89e` | `69882cc39020f03fb3ef6cdb1a10b188c324de0f66066392970776b7495ad138` |

同目录 `generation-receipt.json` 绑定原 canonical 文件摘要、报告版本、Word 版本及计数；`before-after.md` 逐段引用实际 R5/R6 Word，不冒充所有章节均有变化。两份 `*-qa.md` 为实际 DOCX 的独立逐项复核，包含各 100 正文与 26 附录子项的语言、事实及材料证据三轴判定。屋顶语言 120 PASS/6 PARTIAL，事实 85 PASS/41 PARTIAL，材料 5 PASS/43 PARTIAL/78 FAIL；地面语言 92 PASS/34 PARTIAL，事实 79 PASS/47 PARTIAL，材料 7 PASS/47 PARTIAL/72 FAIL。`PASS` 仅限合成 canonical 的内部一致性，不表示真实工程材料齐备。最终小修只改变两案 CH03.02，独立 QA 按实际 Word 验证其余 125 子项文本与上一候选相同后重新审阅改变项。两案实物均有 18 章、100 子项、13 附录、26 子项、89 公式、157 标题身份与 111 张表；附录词典保留 189 条受控词条。此计数不代替逐项内容审阅。

## 已处理与未关闭

- 摘要使用项目概况、主要结果、假设风险与下一步的自然段落；指标表改为统一说明来源成熟度，不再逐行拼接免责。CH06 三小节分开叙述基准、选择依据、专项；CH17/18 提供按项目类型的影响路径与推进事项，不虚构负责人、具体日期或敏感性结果。
- `CH04.03` 只更换读者标题，稳定章节 ID 与书签不变；CH13 表格与正文共享任务名称映射，标明来源预排早于评价日但**不称已施工/付款**；全期含更换的单位投资与首建计划支出分开表述；APP12 历史词句前有上下文声明，未篡改冻结词典。两案 CH03.02 不再共用屋顶/地面研究路径句。
- 当前 CH03.02 仍有相邻句重复、屋面/屋顶称谓差异；多处主报告仍偏模板化、数值精度和空格未全文统一。APP11 的逐式量纲说明重复；APP12 受控词典保留历史方法句与机械边界句，单凭总说明尚不够理想。这些不能据结构计数宣称语言完全通过。
- 合成输入中计划与预计付款日期早于或贴近评价日，当前仅解释日期矛盾，**未获得实际完成或付款证据**，不得平移或以呈现文字修复计算时序；正式时序调整必须取得资料、更新来源并以新身份重算。独立备选、股东流、LCOE、保本电价、敏感性均不得编造；权属、结构、土地/地勘、负荷、接网、交易合同、报价、税务及实际审批未闭合，投资建议仍为暂缓。
- DOCX 可读文本和三线表/字体/书签专项回归已执行，但未进行两份完整 PDF 全页视觉复核、目录刷新或实际 Word/WPS 页面签审；平台安装、对话调用、平台文件回传及发布门禁均未测。旧版 QA 只作差异依据，不是本件的直接签核。

## 验证与卫生边界

受影响报告专项回归命令：`PYTHONPATH=services/solar-pv-engine/src .venv/Scripts/python.exe -m pytest tests/solar-pv/test_phase7l_r2_export.py tests/solar-pv/test_phase7l_r2_v6_display.py tests/solar-pv/test_report_word_styles.py tests/solar-pv/test_report_business_semantics.py tests/solar-pv/test_report_claims_analysis.py tests/solar-pv/test_report_r3_narrative.py tests/solar-pv/test_phase7l_r2_narrative.py tests/solar-pv/test_phase7l_r2_irr_presentation.py -q`；最后一次 **143 passed、6 skipped**。未运行完整25年重算或六小时 L3，保持 `NOT_TESTED`。

卫生工具 `tooling/solar_pv_workspace_hygiene.py --check` 在清理前读到未跟踪 0；仅清理本轮生成且被标记为可重建的 R6 中间目录 `phase7l-r6-review`（8 文件/563576 字节）和 `phase7l-r6-final`（7 文件/531093 字节），合计 15 文件/1094669 字节，回执在被忽略的 `hygiene-receipts/`。未清理受保护 R5/R4/R2 或别的产品历史物。此次**已跟踪净删除 0**；旧的已跟踪生成日志涉及冻结追溯，未在无逐文件证据时盲删。对该光伏产品，`dist/` 现保留 Skill 0.1.3 与 Connector 0.1.2 本地候选，它们可解压且外部 manifest 的 SHA 与文件一致，并被 Git 忽略；其他产品的 `dist` 文件未触碰。**这些 ZIP 未因本次源码修改重打包，不能称为含 R6 修改的平台交付包**。无 push、merge、WorkBuddy 上传或发布。

## 独立门禁

`NARRATIVE_GENERATION_MODE=DETERMINISTIC_RULES_AND_BOUND_EVIDENCE`；`EXECUTIVE_SUMMARY_READABILITY=PARTIAL`；`MAIN_REPORT_INFORMATION_LAYERING=PARTIAL`；`BODY_100_LANGUAGE_QA=PARTIAL`；`APPENDIX_26_LANGUAGE_QA=PARTIAL`；`FACTUAL_ALIGNMENT_QA=PARTIAL`；`PROJECT_TYPE_DIFFERENTIATION=PARTIAL`；`SOURCE_TRACEABILITY=PASS_WITH_SYNTHETIC_BOUNDARY`；`MATERIAL_EVIDENCE_QA=BLOCKED`；`FORMULA_AND_GLOSSARY_PRESERVATION=PASS_WITH_READABILITY_DEBT`；`CANONICAL_INTEGRITY=PASS_FOR_UNCHANGED_IDENTITIES`；`REGRESSION_TESTS=PASS_FOR_LISTED_SUITE`；`WORKSPACE_HYGIENE=PASS_FOR_THIS_R6_RUN`；`DIST_PRESERVATION=PASS_FOR_OLD_LOCAL_ZIPS_NOT_REBUILT`；`PDF_FULL_VISUAL_REVIEW=NOT_TESTED`；`WORKBUDDY_PLATFORM_TEST=NOT_TESTED`；`RELEASE_READY=BLOCKED`。本轮止于 R6 本地审阅，不启动 Phase 8。
