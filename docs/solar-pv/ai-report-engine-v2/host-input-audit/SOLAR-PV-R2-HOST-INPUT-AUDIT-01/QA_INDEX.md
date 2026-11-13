# 本轮独立 QA 及整改证据索引

**THIS_AUDIT_INDEPENDENT_QA = PARTIAL。** 历史17门禁逐值保留，不能用本轮状态替换历史INDEPENDENT_QA。QA原文裁定永不改为PASS。

- 原文：`.runtime/solar-pv/SOLAR-PV-R2-HOST-INPUT-AUDIT-01/independent-qa/QUALITY_REPORT.verbatim.md`。这是manager收到并转交的delegation完成返回正文，UTF8/LF原样保存，不含START/END包装，不是provider传输字节；确切字节/SHA在同目录provenance.json。
- QA对象：提交 `25e79e84c0177321ff8088624b91ddce5882c2e1`；author-snapshot SHA `51019eb32e0b3ed46bdf5c7c141abccfdac0bb248ff6f3b354820bdcf66ea043`，脚本SHA `5e0bbba4bd87338e2e229752add86c2987f1ecff3fd203f4f4f5e93af27ce7bc`。原snapshot、脚本及experiment-final不变。后改core仅授权文档/机器回执及隐私收尾；QA没有验收新core字节或最终ZIP。
- live transcript实际可得文本是工具/长消息截断预览。保存脱敏衍生及原SHA/新SHA，不改写成完整trace或完整内存程序。QA报告记录readonly stdout48106B、SHA `192966e1655d146fed1c3b40820c4364d470ce6ef7a74074c0941bdb3f513f31`；本轮没有该完整stdout实物，不按数字/hash合成。作者同大小stdout的不同hash不冒充QA。

## 两项落实（developer，不是 quality 重新验收）

| 项目 | 实际落实与证据 | 未声称 |
|---|---|---|
| QA-F01 | 仅补RESULT/HOST/NEXT/EXC/机器OFFLINE_VALIDATION及REQUEST_PROFILE的边界；closure()仅部分引用一致性helper，UNKNOWN metric/claim、duplicate source、同源跨节事实不能由它独立识别。CSV/历史实验中的REFERENCE_CLOSURE_VALID仅原helper标签，不是完整授权PASS | 不改审计脚本/实验/原validator；不将总裁定转PASS |
| QA-F02 | share-preparation/redacted-receipts/author-final-state.json与相关共享回执独立脱敏；原件不覆写，redacted-receipts-index.json含原/新SHA与替换计数；三件最小crop另记源/新SHA及坐标；最终allowlist排除未脱敏原/原全图/AX树 | 不称quality验收最终隐私或ZIP |

当前双案完整权限由独立QA另查支持；decoder另以可信原件完整树精确比较和规范重编码拒绝视图篡改，不能把helperVALID单独当完整授权结论。QA132项重seal拒绝属于内存自造离线负向，不是产品tests、pytest或新增章节通过数。结构/引用/清单存在不等于专业语义已审。

QA实记82.545415秒；无尾计时shell解析失败精确耗时UNKNOWN，另列该工具timeout120秒保守上界，不把上界写实测。最终角色账本、最终commit/保护与归档分别见runtime final-state.json/final-delivery.json。所有拟议生产动作仍PROPOSED_NOT_APPROVED；官方询证DRAFT_NOT_SENT。
