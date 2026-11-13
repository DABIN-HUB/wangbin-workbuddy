# 审阅交付导航（非发布、不可安装）

**SOURCE_RESEARCH_COMPLETE / ARTIFACT_ACQUISITION_NOT_AUTHORIZED / DEPENDENCY_CLOSURE_BLOCKED**。
首正式目标仍UNCONFIRMED；Windows AMD64 / 标准GIL CPython3.12仅conditional建议。许可、构件取得、安装、宿主、专业审查及全部旧门禁不升级。

`RUN` 指 `.runtime/solar-pv/SOLAR-PV-R2-DEPENDENCY-SOURCE-APPROVAL-01/`。

## 已有独立结论与新范围

- 本目录 QUALITY_REPORT.md 原字节复制自 RUN/independent-qa/QUALITY_REPORT.md，8635 B，SHA-256 `5b15278cf0149a7247ed8dd93201b17ab74f839039778b9e329b2675f621ef79`；作者说明只在RESULT/本导航，不附加进独立原文。
- PASS_LIMITED_DEPENDENCY_SOURCE_CANDIDATE_QA_WITH_LIMITATIONS 只覆盖原451件冻结集合。冻结原index、原候选与原文档中的PENDING历史状态保持原字节；CANDIDATE_LOCK.json的历史qa字段及原三脚本也不改写为新批准。
- 新正式文档及 RUN/final-review-payload/ 的限定独立复审仍PENDING_INDEPENDENT_LIMITED_REVIEW；作者不生成最终QA报告/confirmation，不封ZIP。RUN/FINAL-CLOSURE-CONTRACT.md 是manager交付接口合同，不是QA裁定。

## 精确证据接口

|记录|责任与使用|
|---|---|
|RUN/final-docs-state.json|此次正常本地文档提交后的实际HEAD、精确scope/blob、clean/index状态；不覆盖developer-final-state.json|
|RUN/final-payload-index.json|绑定最终实际HEAD的新allowlist；逐件path/type/size/SHA/source/原新身份/redaction，含原451 frozen-candidate与必要独立QA证据|
|RUN/independent-final-qa/QUALITY_REPORT.md、provenance.json|未来独立角色的最终payload限定报告；不是本目录候选QA报告的替代/延伸|
|RUN/final-payload-quality-confirmation.json|未来独立角色按合同绑定确切index/tree/HEAD/报告；未产生前禁止封包|
|RUN/manager-final-protection-readback.json|最终QA完成后manager重核3458保护SHA、installed22 exactset/SHA、history2638仅元信息及Git状态|
|RUN/manager-archive-readback.json|manager实际封包后另用独立脚本核全集、安全路径、类型、CRC、size/SHA和451 lineage|
|RUN/FINAL-COMMAND-BUDGET.json|外置最终所有实际wrapper时长（含失败/超时）与prestart保守额度，不能用委托walltime替代|

新payload显式收录manager的 seal_review.py、manager_archive_readback.py、aggregate_budget.py 和合同作为delivery-tools，仅做静态/接口审查，尚未由writer封包执行。最终QA及post-QA保护原证不提前放入index，避免自引用；sealer仅按合同固定audit名称追加，后续封包/读回/预算回执外置。

## 分享与不自包含边界

原stdout/stderr、失败/超时输入和胶囊全部保留本地。仅逐项审核的必要原件可分享；含本机home/联系字段的证据另做明确派生，索引同时保留原新size/SHA，派生不能冒称原件或可重放的完整环境。

frozen-inputs.json及commands/inputs内胶囊base64原件LOCAL_ONLY；raw官方元数据、无关联系人、凭据、venv/cache、wheel/sdist/安装器与历史release资产不入包。未来审阅包不是Skill安装包、完整wheelhouse、可部署构件、正式发布或完整历史备份，也不包含全部原始执行输入。外置12 baseline、optional11及历史5回执/4输入不完整重放限制不变。
