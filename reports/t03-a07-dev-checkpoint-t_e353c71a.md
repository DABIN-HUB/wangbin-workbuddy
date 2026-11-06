# A07 开发检查点（直接 wb-developer Profile，非 Kanban Worker）

- product_id: `wangbin-purchase-threeway-match`; task_id: `t_e353c71a`（复用原授权缺陷卡，无新任务）；workspace: `F:/ideaWorkSpace/wangbin-workbuddy-purchase-threeway-match`; branch: `skill/purchase-threeway-match`; base_commit: `a71cf0a08ca6061e2b916976ac1b70784acf7c8b`; result_commit: 以本报告提交后的 `git rev-parse HEAD` 为准（提交不可自含哈希）。
- 初始 tracked 工作树及 index 无 diff，原有五份 QA 未跟踪报告和 `uv.lock` 保留。`git worktree list --porcelain` 仅本产品 worktree 占用此分支；进程检查 `ps -ef` 未见其它产品写者，不能声称 NTFS 独占强隔离；`wangbin-workbuddy-dev` 仅在 worktree 登记中见到，未读业务内容。
- 已读冻结 A07、requirements §4.1–4.2、IO §3/§5、QA 报告末段和独立 QA scratch `qa013-gap-t37643c38-independent-b/evidence.json`。旧 ZIP SHA-256 `e2c3b6cf0fa0d506a91a9ec6096514af0808c2ee4434044cb5bdba92e5ddde90`，提取脚本 SHA-256 `fd1a681eb8ace9d0190284aceb6a873b39268a507302113d357824778c25334f`；没有修改旧 ZIP。
- changed_files: `packages/skills/wangbin-purchase-threeway-match/scripts/threeway_match.py`, `tests/test_purchase_threeway_acceptance.py`, `reports/t03-a07-dev-checkpoint-t_e353c71a.md`。artifacts: 本报告、开发 scratch `C:/Users/wangbin/AppData/Local/hermes/profiles/wb-developer/cache/scratch/a07-oldzip-repro/` 和 `a07-qa-replay/`（非候选，非永久交付）。

## verification_commands / verification_results（在上述产品工作树执行）

| 命令 | exit | 实测内容 |
|---|---:|---|
| `git rev-parse HEAD && git branch --show-current && git status --porcelain=v1 && git worktree list --porcelain && git log -1 --format='%H %s'` | 0 | HEAD 与预期一致，产品分支，六项旧未跟踪；主仓库 worktree 仅登记未读业务。 |
| `git status --porcelain=v1 --untracked-files=no && git diff --quiet && git diff --cached --quiet && git rev-parse --show-toplevel && git ls-files ... && ps -ef` | 0 | tracked/index 干净；进程无其他产品写者。 |
| `sha256sum dist/wangbin-purchase-threeway-match-0.1.3-skill-candidate.zip; .venv/Scripts/python.exe --version` | 0 | ZIP SHA 如上，Python 3.11.15。 |
| `.venv/Scripts/python.exe C:/Users/wangbin/AppData/Local/hermes/profiles/wb-developer/cache/scratch/a07_reproduce.py` | 0 | 解旧 ZIP 脚本、以 QA 两份原始 manifest/输入分别重跑；两个 CLI exit0，但各 `po_keys=0, matched=0, exceptions=3`，MISSING_REQUIRED_FIELD + 两个伪孤儿；line_results 均空，确认缺陷。 |
| `.venv/Scripts/python.exe -m pytest tests/test_purchase_threeway_acceptance.py -q -k a07_complete_po_key_with_missing_operand --basetemp=.../a07-red --tb=short` | 1 | 环境中没有 pytest，`No module named pytest`；非业务红灯。 |
| `uv run --no-sync --offline --with pytest python -m pytest tests/test_purchase_threeway_acceptance.py -q -k a07_complete_po_key_with_missing_operand --basetemp=.../a07-red-uv --tb=short` | 1 | 修复前 2 FAILED、34 deselected：各期望 po_keys=1/exceptions=2，实得 po_keys=0/exceptions=3。 |
| 相同 uv 命令，`--basetemp=.../a07-green-uv` | 0 | 修复后 2 passed, 34 deselected。 |
| `.venv/Scripts/python.exe C:/Users/wangbin/AppData/Local/hermes/profiles/wb-developer/cache/scratch/a07_qa_replay.py` | 0 | QA 原始缺 qty/price CSV/manifest 分别独立重跑：各 CLI exit0，PO key=1、matched=0，异常恰为 MISSING_REQUIRED_FIELD、NOT_COMPARABLE，expected_amount=NOT_AVAILABLE，来源 po.csv:2；Excel 两结果表均一行，收货/发票非孤儿，来源三行，输入前后哈希不变并与 QA evidence 对齐。额外 no-receipt、invoice-partial、invoice-over 三组原输入逐一重跑，与 QA 既有 totals/异常码一致，输入 SHA 不变。输出在新开发 scratch，不覆写 QA。 |
| `uv run --no-sync --offline --with pytest python -m pytest tests/test_purchase_threeway_acceptance.py tests/test_purchase_threeway_match.py -q --basetemp=.../a07-full --tb=short` | 0 | 44 passed, 1 skipped in 36.76s；skip 为 Windows symlink privilege unavailable。覆盖既有 A01–A19 聚焦回归及新增两个 A07 断言。 |
| `uv run --no-sync --offline --with pytest python -m tooling.products test --id wangbin-purchase-threeway-match` | 0 | PASS，returncode 0，9 passed in 1.95s。 |
| `.venv/Scripts/python.exe -m tooling.products validate --id wangbin-purchase-threeway-match` | 0 | PASS，findings=[]。 |

实现仅对完整显式 PO key 且仅缺 ordered_quantity/po_unit_price、没有其它非法数值的 PO 行保留键与缺失标记；同键收货和发票仍按原键参与可用维度，缺 PO 操作数不作零、不作聚合伪值，缺额不得推导。已有 key 缺失、发票/收货无效、重复行、币种和安全检查路径保持不变。回归验证不是独立 QA 或新 ZIP 验收。

blocked_reason: 无本地开发阻碍；候选发布仍由独立 QA FAIL、许可及平台门禁阻断。residual_risks: Windows symlink SKIP、真实 200MiB 聚合边界 NOT_TESTED、真实 Office 宏/网络监听 NOT_TESTED、其他 OS 与平台安装/审核/发布 NOT_TESTED。未变版本、未重打 0.1.3、未生成正式 ZIP、未 push、未平台操作。