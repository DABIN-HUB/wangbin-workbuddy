# 依赖来源审核结果（独立候选 QA 通过；最终 payload 待限定复审）

结论：**SOURCE_RESEARCH_COMPLETE / ARTIFACT_ACQUISITION_NOT_AUTHORIZED / DEPENDENCY_CLOSURE_BLOCKED**。
数据完整性自检与可分发性是两个门禁；来源已研究不意味着可安装或许可放行。

- 十二旧图各 42 个第三方名称，合并 42 名称 / 43 精确版本；tzdata 在 Windows 为 2026.5，其余目标为 2026.6。
- 43/43 官方精确版本 JSON HTTP 200；另列 2 个 backend，不混入 runtime42。
- 官方记录 926 个 runtime wheel 文件摘要；本提案选择 115 唯一非撤回候选（34 pure、81 平台专属），486 个目标分配、18 缺口。
- 第三方实际 wheel 取得 0，实际 wheel SHA 验证 0；121 个 `.whl.metadata` 是元数据，不是 wheel，PEP658 索引期望摘要未核。
- 许可证工程初审 42 名称/43版本；39名称/40版本取得精确 tag 许可文本，但 tag-to-wheel 未证。所有 42 名称再分发仍 BLOCKED。
- pypdfium2 5.15.1 全部目标撤回拒绝；macOS x86_64 另缺 cryptography 50.0.2、onnxruntime 1.31.1。没有自动升级或允许 yanked。
- 正式首目标 UNCONFIRMED；建议仅条件研究 Windows AMD64 / 标准 GIL CPython 3.12，41 候选 + 1 缺口 + 两个 internal，尚非可安装集合。
- document-cli 1.2.0 双 SHA 不能自动择一；12 外置 baseline、11 可选 fixture、历史五回执/四输入不完整重放问题保留。

## 文件导航

`CANDIDATE_LOCK.json`、`DEPENDENCY_RESOLUTION.json` 是小型正式身份清单，精确绑定 RUN/candidate 内完整机器锁/图/下载计划；大 JSON、raw、日志、输入胶囊只留忽略目录，不入 Git。
完整锁包含 43 节点/12 targets/全部声明边及 marker/extras/115 文件/URL/SHA/tags/许可状态/所属父链和取得状态，不是空占位。
首目标逐项文件表见 WHEELHOUSE_AND_INSTALL_PLAN.md；504 行跨平台表见 DEPENDENCY_SOURCE_MATRIX.csv。

原开发自检/冻结实数保留在 RUN/developer-final-state.json 和 RUN/developer-freeze-index.json，不改写历史。此次文档提交和新payload身份另见 RUN/final-docs-state.json、RUN/final-payload-index.json；文档不嵌入自身未来commit/hash。

## 真正独立的候选 QA（仅原冻结范围）

QUALITY_REPORT.md 为独立审查员原文，8635 B，SHA-256 `5b15278cf0149a7247ed8dd93201b17ab74f839039778b9e329b2675f621ef79`，未附加作者说明。独立 provenance SHA `3fd2943670dbffbcad3e5ca61abb748c16b0e9ab745e1471c3a71cb52ec73a01`；candidate-quality-confirmation SHA `00510622d4bb0a71ce6d3a16aceabd39712f8d96f734d42224c20e8ea911dd6c`。

- 裁定 PASS_LIMITED_DEPENDENCY_SOURCE_CANDIDATE_QA_WITH_LIMITATIONS；只对应原451件/19381431 B、原index SHA `58dece4fc2903572776786076f70388273ec85bf8c601c265befe789588f5bab`、原tree SHA `35f9d78d3305462c02f6249691f8f27bf6514954f5cbac3f416bf11ad66f4afd`，不是未来payload批准。
- 独立12图×44节点，2496 declared/754 active边；4360主要predicate、313支持predicate、504 CSV行有交叉覆盖，不相加当唯一测试数。
- 16互异负向全部实际exit1拒绝，1正常接受；负向17次调用含同版本不同SHA案例8秒超时后同输入retry，另支持wrapper35秒超时后完整重算通过，全部原件保留。QA-OBS-01的21行specifier字面顺序/空格差异语义等价，CLOSED且CSV不改；QA-EXEC-01/02为CLOSED_WITH_RETAINED_TIMEOUT，产品缺陷0。
- 仍OPEN：18文件分配缺口、beautifulsoup4/cobble/protobuf三项精确许可文本关联、42名称再分发及wheel内NOTICE、document双SHA、WorkBuddy解释器UNKNOWN、PEP658期望摘要和所有旧门禁；未以QA提升这些状态。

本轮仅原字节纳入候选QA并冻结新的文档/分享payload，最终payload QA为PENDING_INDEPENDENT_LIMITED_REVIEW。新allowlist逐项扫描来源与分享字节；发现的home路径只做另外标记的分享派生，原stdout/stderr/输入/失败证据保留本地。胶囊及commands/inputs中的原胶囊、raw官方元数据/联系人和历史wheel绝不入包，不能声称全部原始执行输入都包含在未来ZIP。分享索引逐件记录原/新size/SHA。最终独立复审、manager保护/封包/独立读回/总预算接口见DELIVERY.md；作者没有封ZIP、未代签最终QA。

## 43 精确发行来源

| 包 | 版本 | 官方来源 | 许可文本 scope | 再分发 |
|---|---|---|---|---|
| attrs | 26.1.0 | https://pypi.org/pypi/attrs/26.1.0/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| beautifulsoup4 | 4.15.0 | https://pypi.org/pypi/beautifulsoup4/4.15.0/json | UNKNOWN_OR_DIFFERENT_SCOPE | BLOCKED |
| certifi | 2026.10.23 | https://pypi.org/pypi/certifi/2026.10.23/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| cffi | 2.1.1 | https://pypi.org/pypi/cffi/2.1.1/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| charset-normalizer | 3.5.2 | https://pypi.org/pypi/charset-normalizer/3.5.2/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| click | 8.5.1 | https://pypi.org/pypi/click/8.5.1/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| cobble | 0.1.4 | https://pypi.org/pypi/cobble/0.1.4/json | UNKNOWN_OR_DIFFERENT_SCOPE | BLOCKED |
| cryptography | 50.0.2 | https://pypi.org/pypi/cryptography/50.0.2/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| defusedxml | 0.7.1 | https://pypi.org/pypi/defusedxml/0.7.1/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| et-xmlfile | 2.0.0 | https://pypi.org/pypi/et-xmlfile/2.0.0/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| flatbuffers | 25.12.19 | https://pypi.org/pypi/flatbuffers/25.12.19/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| idna | 3.20 | https://pypi.org/pypi/idna/3.20/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| jsonschema-specifications | 2025.9.1 | https://pypi.org/pypi/jsonschema-specifications/2025.9.1/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| jsonschema | 4.26.0 | https://pypi.org/pypi/jsonschema/4.26.0/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| lxml | 6.1.3 | https://pypi.org/pypi/lxml/6.1.3/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| magika | 1.0.3 | https://pypi.org/pypi/magika/1.0.3/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| mammoth | 1.13.0 | https://pypi.org/pypi/mammoth/1.13.0/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| markdownify | 1.2.3 | https://pypi.org/pypi/markdownify/1.2.3/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| markitdown | 0.1.9 | https://pypi.org/pypi/markitdown/0.1.9/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| numpy | 2.5.4 | https://pypi.org/pypi/numpy/2.5.4/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| onnxruntime | 1.31.1 | https://pypi.org/pypi/onnxruntime/1.31.1/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| openpyxl | 3.1.5 | https://pypi.org/pypi/openpyxl/3.1.5/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| packaging | 26.3 | https://pypi.org/pypi/packaging/26.3/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| pandas | 3.1.1 | https://pypi.org/pypi/pandas/3.1.1/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| pdfminer-six | 20260107 | https://pypi.org/pypi/pdfminer-six/20260107/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| pdfplumber | 0.11.10 | https://pypi.org/pypi/pdfplumber/0.11.10/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| pillow | 12.3.0 | https://pypi.org/pypi/pillow/12.3.0/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| protobuf | 7.36.2 | https://pypi.org/pypi/protobuf/7.36.2/json | UNKNOWN_OR_DIFFERENT_SCOPE | BLOCKED |
| pycparser | 3.12 | https://pypi.org/pypi/pycparser/3.12/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| pypdfium2 | 5.15.1 | https://pypi.org/pypi/pypdfium2/5.15.1/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| python-dateutil | 4.0.0 | https://pypi.org/pypi/python-dateutil/4.0.0/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| python-docx | 1.2.0 | https://pypi.org/pypi/python-docx/1.2.0/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| python-pptx | 1.0.2 | https://pypi.org/pypi/python-pptx/1.0.2/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| referencing | 0.37.0 | https://pypi.org/pypi/referencing/0.37.0/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| requests | 2.34.2 | https://pypi.org/pypi/requests/2.34.2/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| rpds-py | 2026.9.1 | https://pypi.org/pypi/rpds-py/2026.9.1/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| six | 1.17.0 | https://pypi.org/pypi/six/1.17.0/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| soupsieve | 4.0.1 | https://pypi.org/pypi/soupsieve/4.0.1/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| typing-extensions | 4.16.0 | https://pypi.org/pypi/typing-extensions/4.16.0/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| tzdata | 2026.5 | https://pypi.org/pypi/tzdata/2026.5/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| tzdata | 2026.6 | https://pypi.org/pypi/tzdata/2026.6/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| urllib3 | 2.8.0 | https://pypi.org/pypi/urllib3/2.8.0/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |
| xlsxwriter | 3.3.1 | https://pypi.org/pypi/xlsxwriter/3.3.1/json | EXACT_TAG_TEXT_CAPTURED_NOT_WHEEL_BOUND | BLOCKED |

来源原证：`.runtime/solar-pv/SOLAR-PV-R2-DEPENDENCY-SOURCE-APPROVAL-01/source-research/sharing-index.final.json` (59623 B, SHA-256 `78cf8573d71f979b31f0d305800ddd934b238317582231c1be27719cc63b85d5`)
