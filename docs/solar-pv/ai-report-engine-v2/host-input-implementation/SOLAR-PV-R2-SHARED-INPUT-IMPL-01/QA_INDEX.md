# 独立QA原文与整改索引

`RUN=.runtime/solar-pv/SOLAR-PV-R2-SHARED-INPUT-IMPL-01`。此文件仅索引，不代写或修改QA原文。

## R1完整独立原证（只读）

- `RUN/independent-qa/QUALITY_REPORT.md`：完整直接作者原文；SHA256 `37d30f66eed67652f103870e78c8707c5352b7c6a3a4668b37cc5cac9cf7068f`。
- `RUN/independent-qa/provenance.json`：被审commit、八文件集合/逐文件身份、原报告和完整COMMANDS/JUnit身份。
- `RUN/independent-qa/COMMANDS.json`：原命令、stdout/stderr与QA原样副本索引、134唯一pytest通过集合；closing recorder单独列明避免自引用。
- `RUN/commands/quality-independent-*.{json,stdout,stderr}`：完整原始回执；R1未接受过期probe为TIMEOUT/124，不能改判。
- `RUN/independent-qa/unaccepted_expiry_r1.py`：原超时probe保留；其他独立边界诊断与结果按provenance定位，非正式pytest。

R1裁定 `PARTIAL_NOT_AI_NOT_HOST_E2E`；被审commit `44c26c972ca1a23eab6f56888d9ed014e8df5367`，八文件集合 `c5fe505dcd32b6d18d2553dc8d8d4dde419d1d7abce1ad9345b308e1722bc22f`。旧审计PARTIAL及全部历史门禁逐值不变。

## R2测试整改候选与独立复验

仅QAI-R1-01：两个正式屋顶新NOT_AI授权过期case，nodeid与断言范围见VALIDATION。生产与Skill不改；QAI-R1-02为建议，不扩源码。`RUN/developer-source-snapshot-r2.json`冻结新八文件，`RUN/developer-fix-r2.diff`只含相对R1测试增量，`RUN/developer-fix-report-r2.md`为作者交接，实际本地wip commit读回在 `RUN/developer-final-state-r2.json`。

作者未执行pytest的冻结记录不变；随后quality两例分别首跑通过，完整原文 `RUN/independent-qa-r2/QUALITY_REPORT.md`、身份 `provenance.json`、命令/JUnit `COMMANDS.json`。R2判定 `PASS_LOCAL_QA_NOT_AI_NOT_HOST_E2E`，QAI-R1-01 CLOSED；七非测试文件与R1原字节一致，八文件集合 `3b41751eb36a632e38c0aab123e25eb66a271e84d2de1ee42d0b06a5f92993c4`。R1原报告PARTIAL及所有旧TIMEOUT不改。

## 固定payload共享审核与封装

manager将SOURCE/REVIEW ONLY实际文件固定到RUN/source-review-payload，逐件身份为RUN/fixed-payload-index.json。最终共享quality原样确认保存为RUN/payload-quality-confirmation.json；只有该记录实际PASS且绑定索引SHA时，才允许封装。它审的是固定payload/隐私，不是改写旧QA，不是审未来ZIP外层hash。其确认自身与后续确定生成的Manifest/ZIP/sidecar/归档身份排除自引用；manager只核对已审字节不变和包完整性。未脱敏原回执不覆盖，任何派生脱敏在包内REDACTED-DERIVATIVES.json分别记原/新SHA。最终HEAD与ZIP身份以RUN/final-state.json、RUN/final-delivery.json为准，不预填未来提交hash。
