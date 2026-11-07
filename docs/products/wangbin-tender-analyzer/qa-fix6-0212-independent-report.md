# Q06 FIX-6 0.2.12 独立实物 ZIP 验收：LOCAL_QA_FAIL

- `product_id=wangbin-tender-analyzer`；`task_id=q06-fix6-evidence-first/Q1`；workspace `F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check`；branch `skill/tender-response-check`；base `4fe1e9cd4bc88fc608c6af19e3b788fc4f42fed5`；验前 HEAD `59d25aaec64541c1a1ab9a21e32a1c26ec70eb42`。
- Q0 测试合同提交 `4d2cb6c1023096937bb06bbfccdc714338d97e4f`，逐案输入及 expected 提交 `f70a1278533ded8db3e180bfbe776600f54e1554`，均在业务修复 `1b2e4890e1453e5ef58e30242a489d274d793fb3` 之前（实际 `git merge-base --is-ancestor` 返回 0）。本轮没有改动任何旧冻结原件/expected。
- 目标 ZIP `dist/wangbin-tender-analyzer-0.2.12-skill-candidate.zip` SHA-256 `7230540fb7c4bf01dbe7deab546ff7ba1a0d5b3224027fcfbe11aa1c1c2e15a8`；sidecar SHA、manifest 版本/成员11项、CRC、各成员 SHA/size 和工作树产品文件字节一致。干净解压至 `wb-quality/cache/scratch/q06_fix6_independent_0212_final/extract`，全部 CLI 子进程只引用解压脚本，环境移除 PYTHONPATH。**0.2.11 失败中间包未验收。**
- 冻结来源：FIX-5 原94案逐案 JSON SHA `a7886ea08aba45199332a8477f24ed9f5bc518af6db48de138d1fa4a56e90656`、旧 fixture ZIP SHA `a791979b9e6d83b36b8e533cde7f65ab1ac3267ced9a909512827413dbc3c986`；Q0 15案 JSON SHA `1b5163a58173b2382b9020b569d8526c7232814b84c0cba35372ee8707448109` 和 36 输入 SHA 清单 SHA `0ed79b688e2b631d8c7d4d177df43a85e90e0a2c7b6d3cb491cd6903a722e74e`。逐案校验文件字节 SHA 后运行。

## 独立逐案核验结果

命令：`python docs/products/wangbin-tender-analyzer/qa-fix6-0212-independent.py`；实际 exit **1**（业务 FAIL，脚本正确阻断）。原53 **53/53**；FIX-3 13 **13/13**；FIX-4 16 **16/16**；FIX-5 12 **12/12**，包含既有五失败 F01/F02/F04/F05/F08 关闭；Q0 预冻结 15 **14/15**。错误输入五种各预期 exit2 且没有成功工件、正控 exit0 双工件，均 6/6；旧 `analyze_tender.py --input` JSON 精确快照通过 1/1。每案输入 SHA、完整命令/cwd/exit/stdout/stderr、四维 expected/actual、矩阵全行、五表重开数据、概览逐维计数守恒、输出 SHA、issues 见 `qa-fix6-0212-independent-results.json`；20 组关键原始输入和真实 XLSX/MD 在 `qa-fix6-0212-raw-evidence.zip`（含 V01–V15、旧五失败）。本地 CLI exit0 与业务 PASS 不等价。

**唯一阻断反例 V14-positive-negative-body-conflict**：输入 `tender.txt` 一行“必须提供营业执照”，`response.md` 一行“营业执照见附件”，`营业执照.txt:1` 为“营业执照正文：名称为虚构云泽公司；统一社会信用代码为虚构示例编号。”，`:2` 为“该营业执照当前只有封面，证照正文并未随文件附入。”；三输入 SHA 分别 `e15882d7f3447a02d456f4f078005fc5a4146b83cfbbdba4ca9077455bb1a00f`、`3e46c6db2bb24a72db41847c5f5087d56d8be975e9a8e2727e4a1ae6eeeed898`、`1df352f50ac6bbffd0a26eb7698b0453b63086a926589a5214e38c73f48323b2`。命令/路径/exit 见结果 JSON：CLI exit **0**，真实 XLSX SHA `85bcd98bed227fd74d8ffd7e150e54cf6a8a5f549fa3c30aa3647db52e4b3097`，MD SHA `4131c2ad1e87c69bcea1eea882e06b8e5d5e00af596f659cac85ac65682dd4f2`。四维 expected=actual=`已定位 / 待确认 / 已提供（可读文本） / 待确认`，证据位置也含两行；但**附件核对、矩阵判定理由、待确认事项和 MD 均只有“同一材料有正文正反冲突，须核对”加两个行号，没有肯定和否定原句或可审计摘录**。Q0 冻结报告第10行明确要求冲突双方原句或可审计摘录与两条真实来源，不能把两个行号等价为双侧事实摘录。此为可定位的业务证据缺口，非四维状态失败。

源码根因建议（只读定位）：`packages/skills/wangbin-tender-analyzer/scripts/check_response.py:481-483` 的 `negatives and positives` 分支只把 `loc()` 拼到理由，没把各自 `line` 做有限脱敏 `quote()` 摘录；同函数否定单侧分支 485–488 已有 `quote(line)` 可参考。修复需限定两侧正文的安全摘录/真实行来源传播到附件核对、矩阵理由、待确认与 MD，不能丢双行且不能以证照真实有效性冒充文本核查。质量角色不改业务源码，不放宽冻结预期。失败案 ZIP 内的实物输入/输出已保留，可原样复现。

## 边界与后续

这是 **LOCAL_QA_FAIL**，ZIP 不得加入 `qa-passed`，不建议本轮候选，下一轮由唯一经理后继 `t_05e6dc19` 查重并按额度路由。WorkBuddy 平台执行/审核、物理许可证、相似性、实体证照法律效力、部署上传发布均 `NOT_TESTED`。本 QA 卡未进行 PR/merge/rebase/force-push/部署/上传/发布。远端状态及普通 push 的实测读回另见卡片 metadata，不因本地完整性标记远端成功。
