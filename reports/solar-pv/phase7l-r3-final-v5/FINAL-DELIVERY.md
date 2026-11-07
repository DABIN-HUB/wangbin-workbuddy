# Phase 7L-R3 双案本地审阅交付（非专业验收）

本目录是独立的 R3 报告交付，不覆盖 R2/v7 或封存案例。工商业屋顶与集中式地面沿用已验证的 R2 交易费支付来源 canonical；只修改报告叙述、现金流展示、表格单位及本地渲染。未经授权不推送、不上传、不发布，不启动 Phase 8。

| 项目 | 工商业屋顶 | 集中式地面 |
|---|---|---|
| canonical result_hash | `ca4bdff3f5e89e6770d43f4dad3b4efd57d965aba6c9ba0f1b4299f99295a43f` | `69882cc39020f03fb3ef6cdb1a10b188c324de0f66066392970776b7495ad138` |
| 项目净现值（约，元） | 670,443.03 | 260,918.68 |
| 项目 IRR（约） | 22.8723% | 11.1565% |
| 终期营运资金回收 | 12,000元，已在3D/3E账簿和APP06中 | 同左 |
| 报告版本 | `phase7l-r3-v1-professional-content-and-full-cash-bridge` | 同左 |
| PDF | 本地 WPS 目录刷新后导出，真实PDF | 同左 |

各案例目录包含：经本地 WPS 更新目录缓存后的 DOCX、PDF、测算模型 XLSX、资料来源与假设清单 XLSX、canonical.json、逐文件 manifest.json、126项正文/附录独立读回及42公式组读回、交易费合成支付来源、逐年对账与重放证据、生成前与 WPS 后处理回执。`execution/generator-pre-render-receipt.json` 是目录刷新前的原始生成回执，故其 PDF/TOC 门禁仍为当时的 BLOCKED/待刷新；应以本目录 `manifest.json`、本次审计及最终包清单为准，不混称同一时点的状态。

APP06现在按真实来源分列运营收支、资本支出/更换付款、营运资金增加和回收、终期资产现金，建设至第25年逐期与3E项目净现金流对齐。屋顶自用节费不称作售电到账；项目现金流、股东现金流及 LCOE/盈亏平衡电价保持各自原有状态。合成支付条件不等于已签合同、银行流水或真实付款。

## 已实际完成的机器校核

- 报告生成与本地 WPS 导出双案完成；目录缓存可读，205条目录对应PDF实际文本页的核对由本地归档程序执行。PDF仍需人工逐页视觉审阅，不得将文本页码核对视为视觉合格。
- 双案报告各覆盖100个正文子项、26个附录子项、42个引用公式组。机器检查各标记64项/65项待人工专业审阅；**不是64项/65项已判定错误，也不是126项全部专业通过**。逐项生成正文与机器审阅意见见 `independent-content-review.json`。
- 最后代码快照的限定回归：`PYTHONPATH=services/solar-pv-engine/src python -m pytest tests/solar-pv/test_app06_full_annual_bridge.py tests/solar-pv/test_report_r3_narrative.py tests/solar-pv/test_report_business_semantics.py tests/solar-pv/test_phase7l_r2_v6_display.py tests/solar-pv/test_report_chart_font.py tests/solar-pv/test_phase7l_r2_export.py -q`，退出0：86 passed、2 skipped、1 warning。warning是 anyio/pytest 插件弃用提示。旧版导出测试先因摘要表标题和字段旧断言失败，按新版实际结构修正后重跑通过；该失败过程没有被改写为首次成功。
- `PACKAGE-MANIFEST.json`记录双案包内逐文件大小及SHA-256；每案 `CASE-MANIFEST.json` 仅记录本案成员，便于单案ZIP独立验算。每案ZIP与双案ZIP在归档时逐成员读回核验。ZIP、回执文件自身的SHA-256记录在外部回执中，避免把文件自己的哈希写入自身。

## 尚未开放的门禁

`VISUAL_REVIEW=NOT_TESTED`（未逐页人工检查字体、图表、分页及溢出）；`DOCUMENT_CONTENT_REVIEW=NOT_REVIEWED`、专业内容/42公式适用边界需独立人工审阅；`FOUR_FILE_GATE=NOT_FORMAL_ACCEPTANCE`；`WORKBUDDY_PLATFORM_TEST=NOT_VERIFIED`。PDF真实生成及目录文本页码匹配，不等于这几项通过。请先审阅两份DOCX/PDF与独立126项清单，再决定是否转为正式交付。
