# Q06 FIX-6 R1 0.2.13 独立 ZIP QA：LOCAL_QA_PASS（本地限定范围）

- product_id `wangbin-tender-analyzer`；task_id `q06-fix6-evidence-first/R1-Q` / `t_5bdd90bf`；workspace `F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check`；branch `skill/tender-response-check`；验前 HEAD `18b1b6f48e9277ced14af110a7a579e43ea294c7`；QA 基线 `7f4c20c6182bcd4699d01b55bdec5dae6b2869b6`。预冻结 expected 提交 `f70a1278533ded8db3e180bfbe776600f54e1554` 先于修复源码 `3b2e117004f36731395c3bc7fa01873404135b29`（`git merge-base --is-ancestor` exit 0）；未改冻结预期。
- 不可变候选 `dist/wangbin-tender-analyzer-0.2.13-skill-candidate.zip` SHA-256 `3cb421197398c93cfed512d171a1ac2bdea7b413c44685f5a172b24348c5f781`；sidecar 与 manifest 版本/哈希一致；ZIP CRC、11 个唯一安全成员每字节与当前提交产品源码、清单 size/SHA 一致；SKILL frontmatter 匹配。仅干净解压至 `C:/Users/wangbin/AppData/Local/hermes/profiles/wb-quality/cache/scratch/q06_fix6_independent_0213_r1/extract` 后执行包内 CLI，所有子进程删除 `PYTHONPATH`。旧 0.2.12 SHA `7230540fb7c4bf01dbe7deab546ff7ba1a0d5b3224027fcfbe11aa1c1c2e15a8` 的 V14 失败历史未修改。
- 冻结来源：原94逐案结果 JSON SHA `a7886ea08aba45199332a8477f24ed9f5bc518af6db48de138d1fa4a56e90656`；旧输入 ZIP SHA `a791979b9e6d83b36b8e533cde7f65ab1ac3267ced9a909512827413dbc3c986`；Q0 15 案输入/expected JSON 和输入逐文件哈希锁逐案验证，锁 SHA `0ed79b688e2b631d8c7d4d177df43a85e90e0a2c7b6d3cb491cd6903a722e74e`。逐案均核对四维 expected/actual、来源、缺口/待确认/MD 分区、五表打开顺序、概览四维守恒、XLSX 无公式与输出 SHA。

## 实测

命令 `python docs/products/wangbin-tender-analyzer/qa-fix6-0213-independent.py`，exit **0**；原冻结 53/53 + FIX-3 13/13 + FIX-4 16/16 + FIX-5 12/12 = **94/94**；Q0 **15/15**；错误五个均 exit2 且无输出、正控 exit0 且有 XLSX/MD，**6/6**；旧包内 `analyze_tender.py --input` JSON 快照 **1/1**。旧五失败 F01/F02/F04/F05/F08 均在 FIX-5 12/12 内实际回放通过。CLI exit0 单独并非业务 PASS，此结论依赖内容断言。

V14 真实三文件输入 SHA、实际命令/cwd/exit/stdout/stderr 和全行见逐案 JSON。其四维 expected=actual 为 `已定位 / 待确认 / 已提供（可读文本） / 待确认`；`营业执照.txt:1` 肯定原句“营业执照正文：名称为虚构云泽公司；统一社会信用代码为虚构示例编号。”与 `:2` 否定原句“该营业执照当前只有封面，证照正文并未随文件附入。”分别连同行号，均在真实附件核对、矩阵建议理由、待确认事项、MD 四面出现；证据位置同时含两条来源，不误认真实法律效力。XLSX SHA `0a0d02a6362873abfd3f718c942c03fcc2c156e3c5f7b2eb690e8321c283a948`；MD SHA `1d2cbeb2f4e9916f29bc6798a6f3a3fd4aabe2eb68a3a41e4d68542807c40773`；issues `[]`。

完整命令、每案原始输入/输出 SHA、expected/actual、五表行、stdout/stderr、issues：`qa-fix6-0213-independent-results.json` SHA `75b29be2b44113ac4fa42c65dc95cfd8aa4b193fabdad182a4bac34446de415c`。全部109案原始输入和实际 XLSX/MD、错误输入及正控双输出：`qa-fix6-0213-raw-evidence.zip` SHA `8a876a4de81fa1dc8a27318e40122be17f1c53ae5da6f844ca20c28cea8a4dbb`，`unzip -t` exit0。脚本基于先前独立 QA 探针仅更新新版本、隔离 scratch 与 V14 四面双句断言，并扩充全量原始证据；未执行开发 PRE-QA 代替独立验收。

此为本地限定范围 LOCAL_QA_PASS，**不是** WorkBuddy 平台运行/审核、许可证合规、相似性、实物证件合法性或正式发布通过；这些均 NOT_TESTED。QA 不复制至 `qa-passed`、不制作六包总归档、不部署/上传/PR/merge/rebase/force push；由经理独立终验与条件性归档。普通 push 与远端 HEAD 的实测结果另由本任务卡记录，不能将本地 PASS 等同远端同步。
