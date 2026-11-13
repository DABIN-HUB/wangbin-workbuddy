# 独立QA原文与整改索引

`RUN=.runtime/solar-pv/SOLAR-PV-R2-SHARED-INPUT-IMPL-01`。此文件仅索引，不代写或修改QA原文。

## R1完整独立原证（只读）

- `RUN/independent-qa/QUALITY_REPORT.md`：完整直接作者原文；SHA256 `37d30f66eed67652f103870e78c8707c5352b7c6a3a4668b37cc5cac9cf7068f`。
- `RUN/independent-qa/provenance.json`：被审commit、八文件集合/逐文件身份、原报告和完整COMMANDS/JUnit身份。
- `RUN/independent-qa/COMMANDS.json`：原命令、stdout/stderr与QA原样副本索引、134唯一pytest通过集合；closing recorder单独列明避免自引用。
- `RUN/commands/quality-independent-*.{json,stdout,stderr}`：完整原始回执；R1未接受过期probe为TIMEOUT/124，不能改判。
- `RUN/independent-qa/unaccepted_expiry_r1.py`：原超时probe保留；其他独立边界诊断与结果按provenance定位，非正式pytest。

R1裁定 `PARTIAL_NOT_AI_NOT_HOST_E2E`；被审commit `44c26c972ca1a23eab6f56888d9ed014e8df5367`，八文件集合 `c5fe505dcd32b6d18d2553dc8d8d4dde419d1d7abce1ad9345b308e1722bc22f`。旧审计PARTIAL及全部历史门禁逐值不变。

## 本次r2测试整改候选（待独立首跑）

仅QAI-R1-01：两个正式屋顶新NOT_AI授权过期case，nodeid与断言范围见VALIDATION。生产与Skill不改；QAI-R1-02为建议，不扩源码。`RUN/developer-source-snapshot-r2.json`冻结新八文件，`RUN/developer-fix-r2.diff`只含相对R1测试增量，`RUN/developer-fix-report-r2.md`为作者交接，实际本地wip commit读回在 `RUN/developer-final-state-r2.json`。

两新case状态 `NOT_TESTED_PENDING_INDEPENDENT_QA`。作者未执行pytest，不签本轮QA PASS、不签最终payload/脱敏/ZIP；quality后续报告另存，不覆盖R1。封装与最终payload不属于本次writer动作。
