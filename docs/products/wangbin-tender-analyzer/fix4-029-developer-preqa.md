# Q06 FIX-4 · 0.2.9 开发 PRE-QA（非独立验收）

- product_id: `wangbin-tender-analyzer`; task_id: `t_352cbd48`; workspace: `F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check`; branch: `skill/tender-response-check`; base_commit: `a279517598a36765441fe98e596e3554e4e5d764`；result_commit: 见任务交接（提交后记录）。
- 候选 `F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check/dist/wangbin-tender-analyzer-0.2.9-skill-candidate.zip` SHA-256 `d5ed3fd8e06c92046dee6ce6db01a53120be65883d3e6e807b8e3f408fde83ce`。工厂 manifest 和 `.sha256` 同目录。历史 0.2.8 SHA-256 `8eddf4883c35da2eb645ef97acaf1b6f8d77e8384b01e4256382d26b1ea282be`，前后不变；未覆盖旧 ZIP。
- 根因：`uncertain_capability` 未识别同对象“是否已上线尚待核实”，于是近似动作/关键词将状态当正控；材料判定将含“营业执照”字面直接当正文正证，`compare` 再将支持提升为覆盖。修复以同要求对象及当前状态判断明确否定/未来计划、真实未知、当前正控；以实际关联文件及段落区分占位、缺失、明确否定、未核实和实质正证，未知不升格，否定不降格；五表与旧入口不变。限确定性规则，非外部证照真实性认证。

## 原 FIX-3 → 开发 PRE-QA 的四维（响应/条件/附件/内容）

| ID | 冻结预期 | 旧 0.2.8 实际 | 新 0.2.9 实际 |
|---|---|---|---|
| Z04 | 已定位 / 待确认 / 不适用 / 不适用 | 已定位 / 已覆盖（文本层面） / 不适用 / 不适用 | 已定位 / 待确认 / 不适用 / 不适用 |
| Z10 | 已定位 / 待确认 / 已提供（可读文本） / 待确认 | 已定位 / 已覆盖（文本层面） / 已提供（可读文本） / 支持（文本层面） | 已定位 / 待确认 / 已提供（可读文本） / 待确认 |

Z04 `tender.txt:1` / `response.md:1`；Z10 `tender.txt:1` / `response.md:1` / `营业执照.txt:1`。两案新 XLSX `要求响应矩阵` 与 `附件核对`、`待确认事项` 均重新打开核对；MD 不在已覆盖分段、均在人工确认分段。真实前后 XLSX/MD：旧案保留 `qa-fix3-028-examples/` 和 `qa-fix3-028-independent-results.json`，新案存 `qa-fix4-029-preqa-examples/`，新输入与原 QA 的 `input_sha` 三项/两项相同。新 Z04 XLSX/MD SHA `2957abc738fc16da2e0d8fc6f30c70b6903a2153f42d639f9b4c308fd2c8f57c` / `1b5c3bf0312521e44460f1cd601fb563a7f60a819695433bd14107a6035942c0`；Z10 为 `d87d5aeefd3f7b8371059558073d3ea220248de8387344942464d420d3b84c10` / `a24d65f8bde6d85527ec6a31bd58e5268c4f6994bd11f6fed68b1114effb13be`。

## 实际开发验证（非独立 QA）

- `python -m pytest -q tests/test_tender_fix4.py tests/test_tender_fix3.py tests/test_tender_response_audit.py tests/test_tender_evidence_linkage.py tests/test_tender_bid_response.py tests/test_tender_analyzer.py`：最终 exit 0，**103 passed / 1 skipped**（Windows symlink 不可创建），1 pytest 插件弃用警告。开发过程中第一次同命令 exit 1、101 passed / 2 failed / 1 skipped；随后补上“备份不支持”对象后置否定及空正文无虚假行号的测试断言，最终重跑通过。
- `python -m tooling.products validate --id wangbin-tender-analyzer`：exit 0 PASS；`python -m tooling.products test --id wangbin-tender-analyzer`：exit 0，11 passed / 1 skipped；`python -m tooling.products package --id wangbin-tender-analyzer` 与 `verify`：exit 0 PASS。工厂为本产品登记 0.2.9 并选择本地 active_version，非平台激活。
- `python C:/Users/wangbin/AppData/Local/hermes/profiles/wb-developer/cache/scratch/q06_fix4_developer_replay.py`：exit 0，开发者将冻结独立 QA 脚本**仅复制至本人 scratch**，仅改 ZIP/哈希/输出位置，未修改冻结原脚本/expected，使用原 0.2.7 证据 ZIP 输入逐字节对比；从新 ZIP 干净解压：原53/53、新13/13、错误探针6/6、旧 JSON 入口 snapshot PASS；保存全部逐案 CLI/exits/XLSX 五表/MD/输入输出 SHA 于本人 scratch `q06_fix4_developer_029_replay/results.json`。程序 exit 0 不是业务验收，逐案 `issues=[]` 才算开发 PRE-QA 通过。
- ZIP 11 个成员经 `zipfile.testzip()` CRC、manifest SHA/size 和源码同路径字节逐一相等；无重复/非法路径；frontmatter 及 catalog version 0.2.9 已比对。归档本地完整性与独立产品 QA 是不同门禁。

残余风险：独立质量卡 `t_c1690b2a` 尚须另行在新 ZIP 干净解压执行 53+13 和自主变体；WorkBuddy 宿主自然语言/权限、平台审核、权利许可、Windows 物理 symlink 均 NOT_TESTED 或 NOT_VERIFIED。禁止将此 PRE-QA 记为 LOCAL_QA_PASS；未 push、未上传、未发布。
