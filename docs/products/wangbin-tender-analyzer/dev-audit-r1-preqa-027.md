# AUDIT-R1 Q06 最后一次退回开发预 QA · 0.2.7

product_id `wangbin-tender-analyzer`；task_id `t_a37f80a9`；workspace `F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check`；branch `skill/tender-response-check`；base_commit `34c3bd780929ee89c01d695fb331a940a95b0e21`。本文件记录开发验证，**不替代**后继 `t_b7703b65` 的独立 QA；历史 0.2.5 29/32 FAIL、0.2.6 36/41 FAIL 原判不改。

## 修复及文本判据

- BID-F02/F04：把当前能力状态谓词和请求的动作对象绑定；相邻分句只有明确指回该对象/同一省略主语时才沿用，`做不到`、`尚未具备该能力`、`尚未启用` 等不因主题共现升为已覆盖，独立另一行离线查询肯定不受连带否定。确认的正向保留已覆盖，双否定匹配照旧。
- BID-F03/F04：显式交付的占位文件仍登记为“已提供（可读文本）”，但“示例占位/并非证书”是证书交付义务的文本反证，保留文件:行与确定缺口，不认证行政真伪。无目录且无直接文件名的多条义务，必须由显式提交的文件名对象和正文对象共同锚定对应要求；甲/乙不能互借，不明的候选不捏造支持。有限乙类证明文本及交付回应可覆盖对应乙类文本义务，甲类仍未提供。

## 精确产物与实跑

- 新不可变 `dist/wangbin-tender-analyzer-0.2.7-skill-candidate.zip`，SHA-256 `12b9ebc2f99a20e4a15dd3e783a2b825bd04adba7edef70a3e0be041002faf09`；旁路 `.sha256` 与 `.manifest.json`，11 个成员。`SKILL.md`/catalog/manifest/包名均 0.2.7；catalog 本地 `active_version` 用于工厂选包，**不代表 WorkBuddy 激活**。包内 `scripts/check_response.py` SHA-256 `100de72a1562162446d925c25f5d499d723f9f0ab60b95bcbccd745b3eb52cc6`。manifest 成员大小/hash 与源码逐件比对由 factory verify 实测 PASS。
- `python -m tooling.products validate/test/package/verify/release-check --id wangbin-tender-analyzer`（各单独执行）：exit `0/0/0/0/1`；validate PASS、test 11 passed/1 Windows symlink skipped、package/verify PASS、release-check BLOCKED（缺许可文件/依赖分发权未核实，人工相似性 REVIEW_REQUIRED，平台 NOT_TESTED）。
- `python docs/products/wangbin-tender-analyzer/dev-audit-r1-preqa-027.py` exit 0：基于原 QA 探针预声明的 41 条真实文件断言，从全新 scratch 解压**新 ZIP**运行包内 CLI，逐例回读 XLSX 五表及 MD、校验四维/缺口/来源/概览/MD 分类，原 32/32、新 N01–N09 9/9，总 41/41 开发 PRE-QA；N01/N02/N04/N05/N08 均从旧失败转为预期结论，N03/N06/N07/N09 正反控制保留。原旧 ZIP 的 frozen JSON expected 与新 ZIP 的 `analyze_tender.py` stdout 解析一致，exit0。完整实际 argv、输入/输出 SHA 和逐行输出在 `dev-audit-r1-preqa-027-results.json`；203 个输入与产出在 `dev-audit-r1-preqa-027-fixtures-outputs.zip`（**证据包，不是 Skill**），SHA-256 `d72008ff4c2494aa5bae4a221e03b38319c09dff9dda2a77e8b0b30380ac21c0`。
- 独立于冻结句子的新增功能测试含“目前无法交付/仍在规划”等改写，否定范围隔离、占位反证、无目录乙类对象对应。`python -m pytest -q tests/test_tender_response_audit.py tests/test_tender_analyzer.py --basetemp=C:/Users/wangbin/AppData/Local/hermes/profiles/wb-developer/cache/scratch/q06_r2_focused_final` exit0：42 passed、1 Windows symlink skipped；该专项也从新 ZIP 清洁解压执行不同日期的正式 CLI 和旧 JSON。
- `python docs/products/wangbin-tender-analyzer/dev-audit-r1-errors-027.py` exit0：5 种错误输入分别 exit2、错误码匹配、无成功产物；正向 exit0/双产物。`python docs/products/wangbin-tender-analyzer/dev-audit-r1-preqa-027-evidence-pack.py` exit0，`python -m zipfile -t docs/products/wangbin-tender-analyzer/dev-audit-r1-preqa-027-fixtures-outputs.zip` exit0。

只做本地开发预 QA；真实 Hermes 模型三轮 L4、WorkBuddy 安装使用 L5、证照真实性、许可及人工相似性 **NOT_TESTED/BLOCKED**。本次未 push、上传或发布；旧 0.1.0 实物未验证，Windows symlink 正向实测跳过。完整旧 A02–A14 独立 L3 本次未逐条重跑。独立后继 QA 若发现新业务失败，本审查阶段返工次数已达 2/2，不得创建第三次自动修复。
