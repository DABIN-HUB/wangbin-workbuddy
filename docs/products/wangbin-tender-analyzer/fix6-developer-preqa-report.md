# FIX-6 Q06 开发 PRE-QA 交接（NOT_ACCEPTED）

- product_id: `wangbin-tender-analyzer`; task_id: `q06-fix6-evidence-first/D1`; 工作树：`F:/ideaWorkSpace/wangbin-workbuddy-tender-response-check`；分支：`skill/tender-response-check`；基线：`4fe1e9cd4bc88fc608c6af19e3b788fc4f42fed5`。
- Q0 合同/QA 预冻结按顺序已在 `4d2cb6c1023096937bb06bbfccdc714338d97e4f`、`f70a1278533ded8db3e180bfbe776600f54e1554`，修复前源码 blob `468a06be4f50cf45d21940daa3a05c8052d9747c`。预冻结输入/expected SHA 原文件未改。
- 开发源码提交 `1b2e4890e1453e5ef58e30242a489d274d793fb3`：`check_response.py` 同对象聚合当前事实、不同对象隔离、功能覆盖不得 token 回退、缺正文正反归属；单独开发测试/回放脚本和 SKILL.md 版本。catalog 独立提交见 Git 历史。
- 初始不可覆盖 0.2.11 ZIP SHA-256 `571780046b635edb5d11845b8b9fb2d00977c7996eca1ec180830ebbeeaf1d15` 在开发回放时原 94 中 4 例失败，已**保留**原包、不重包覆盖。修复后另选 0.2.12，原 0.2.7–0.2.10 SHA 均不变。
- 最终待独立 QA 的候选是 `dist/wangbin-tender-analyzer-0.2.12-skill-candidate.zip`，SHA-256 `7230540fb7c4bf01dbe7deab546ff7ba1a0d5b3224027fcfbe11aa1c1c2e15a8`，sidecar `.sha256`、manifest `.manifest.json`；11 个 ZIP 成员，manifest 逐成员 SHA/size；factory package/verify 均 exit 0，`status=PASS` **仅包完整性**，不是业务 QA 或发布许可。
- 从该 ZIP 干净解压执行 `python docs/products/wangbin-tender-analyzer/fix6-developer-preqa.py dist/wangbin-tender-analyzer-0.2.12-skill-candidate.zip` exit 0；实际原 53/53 + FIX-3 13/13 + FIX-4 16/16 + FIX-5 12/12 + Q0 15/15；旧 `analyze_tender.py --input` JSON 快照成功；错误探针 5/5 exit 2、正控 1/1 exit 0。每次脚本实际生成并重开 XLSX 五表与 MD，比较四维、来源及概览计数；但开发自测**不等于独立质量门禁**，独立 QA 须自行完整核验行源、负证、MD 分区和逐例输出 SHA。
- `python -m pytest -q --tb=short tests/test_tender_fix6.py tests/test_tender_fix5.py tests/test_tender_fix4.py tests/test_tender_fix3.py tests/test_tender_evidence_linkage.py tests/test_tender_bid_response.py tests/test_tender_analyzer.py` exit 0：101 passed，1 skipped（Windows symlink 生成不可用）；`python -m tooling.products validate/test/package/verify --id wangbin-tender-analyzer` 分别 exit 0（工厂 test：11 passed、1 skipped）。
- 普通 push 前 `git ls-remote --heads origin skill/tender-response-check` 仍为旧基线 `4fe1e9cd...`；一次非交互 push 85s timeout exit 124；重读远端仍旧基线，本地提交保留，不宣称已 push，也不盲目重复相同超时。平台运行、许可证、相似性、物理 symlink、上传和发布 **NOT_TESTED**。

**本文件是开发 PRE-QA 记录，状态 NOT_ACCEPTED；独立质量卡 `t_146b1714` 从精确 0.2.12 ZIP 自行执行，不能复用本开发测试作为 QA 结论。**
