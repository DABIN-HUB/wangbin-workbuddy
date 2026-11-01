# Phase 3E-P2-3A-R1：严格隔离目录回归修复与验收

## 结论

**严格隔离目录的回归阻断已关闭。** `TMPDIR` 与 pytest `--basetemp` 均使用实际不同的私有目录：专项 **17 passed、1 skipped**，光伏全量 **4137 passed、7 skipped**，WorkBuddy/Expert **109 passed、5 skipped**；三次命令退出码均为 **0**。跳过项单独列示，**不算 PASS**；它们是本机未授予符号链接创建权限，并不代表相应符号链接负例已经执行。Windows junction 和硬链接负例实际执行且通过。

本轮仅改变 `tests/solar-pv/test_phase3e_candidate_replay.py` 的测试夹具布局、补充安全断言；**生产代码、目录守卫、Phase 3B/3C/3D 数值算法、冻结 Schema/字段/公式/绑定与封存案例均未修改**。源码修复本地提交：`112f45b2c12378c45ba510b7e9e8d02d605db414`；基线 HEAD：`67d37874c6e402864637ff5a4493cc4baa9ca676`。本报告自身所属的后续文档提交 SHA 以交付时 Git HEAD 为准（不能在同一 Git 提交中自引用）。未 push、部署或发布。

## 两项历史失败的根因

复核原始红色 JUnit `reports/solar-pv/phase3e-p2-3a-evidence/solar-separated-failed.xml`：

1. `test_real_replay_changes_only_one_atom_and_runs_both_3c_calculations` 实际失败于 `BREAK_EVEN_SCRATCH_OUTSIDE_WORKSPACE`，还未进入 3C 数值路径。
2. `test_future_price_row_with_no_settled_energy_does_not_publish_candidate` 期望 `BREAK_EVEN_PRICE_NOT_CONSUMED`，实际先触发同一工作区位置守卫，属于错误发生顺序被测试夹具遮蔽，而非价格未消费守卫失效。

生产 `replay_price_candidate()` 要求 `Path(TMPDIR).resolve() == workspace.root.parent.resolve()`；旧 P2-2 模块级 `original(tmp_path_factory)` 在 pytest `--basetemp` 下创建 `synthetic-p2-replay*`，却将其作为正式候选 Workspace 交给生产入口。两个临时根目录分离时，此布局必然不满足安全契约。前轮把 `TMPDIR`、`--basetemp` 设成同一目录的 **4132 passed、6 skipped** 只证明了该不匹配假设，不能算严格隔离验收；旧红色 XML 未覆盖或删除。

另有一次本轮单测红路径重现尝试因执行工具 420 秒超时而未生成 JUnit，不计为新的失败/通过证据；根因结论由已归档的两项历史失败、源码调用链和本轮真正分离后的绿测共同支持。

## 最小修复与安全负例

夹具在环境 `TMPDIR` 下创建 UUID 唯一私有 `synthetic-p2-replay-*` 子目录，先以现有 `Workspace` 校验授权根；pytest 自己的 `--basetemp` 始终独立。模块结束时调用既有 `_remove_owned`，以父级 Workspace、目录 inode/dev 身份及目录项安全检查限定清理对象；本轮专项和全量运行结束后，这两个 TMPDIR 内各自的 P2-2 私有根均已清除。不使用仓库 scratch、不修改环境变量使两目录重合、不 monkeypatch 守卫，真实 8760 行资源/负荷/市场数据及所有原有项目、价格、金额断言保持不变。

新增/加强的验证：合法私有 Workspace 与 `--basetemp` 路径不相同、未授权 pytest Workspace 拒绝、运行名/相对路径穿越拒绝、现存运行目录不可覆盖且其哨兵不变、真实硬链接与 Windows junction 拒绝、真实符号链接在权限不足时**明确 SKIP**；既有错误来源不发布、无效 3B 哈希失败且仅清理自有运行目录。后者还比对原 D3 manifest 与 3B 结果的 SHA-256，并验证同级其他任务哨兵未被触及；未来未结算价仍必须报 `BREAK_EVEN_PRICE_NOT_CONSUMED`、不能发布候选。原 P2-2 **7 项原有业务测试全部通过**，新增 6 项测试中 5 passed、1 skipped。独立 3A 财务测试 **5 passed**。生产 `break_even_replay.py` 的 TMPDIR 判断、`Workspace` 的穿越/符号链接/junction/硬链接拒绝和输出独占规则未放宽。

## 三轮真实执行证据

三个运行的 `RUN_HEAD` 均为 `67d37874c6e402864637ff5a4493cc4baa9ca676`（测试修复未提交时），修复文件 SHA-256 在三轮中均为 `ab6aa61f8b2017ffead41e1b9fb74b26c5ed94e37d3f58da3952cdc8f0e50376`。下述路径均经 `Path.resolve()` 规范化，分别以 `C:\Users\wangbin\AppData\Local\hermes\cache\scratch\` 为前缀；运行 stdout 原件、JUnit、完整测试 ID、测试数和逐项 SKIP 理由见 `reports/solar-pv/phase3e-p2-3a-r1-evidence/` 及同目录机器证据 JSON。

| 范围 / 实际 pytest 主命令 | TMPDIR 尾段 | `--basetemp` 尾段 | 开始 → 结束（UTC+08:00） | 结果 / 退出码 |
| --- | --- | --- | --- | --- |
| `python -m pytest tests/solar-pv/test_phase3e_candidate_replay.py tests/solar-pv/test_phase3e_financial_candidate_replay.py -q` | `p2-3a-r1-focused-workspace` | `p2-3a-r1-focused-pytest` | 2026-11-01 15:09:57 → 16:25:51 | **17 passed、1 skipped / 0** |
| `python -m pytest tests/solar-pv -q` | `p2-3a-r1-solar-workspace` | `p2-3a-r1-solar-pytest` | 2026-11-01 16:26:09 → 19:14:23 | **4137 passed、7 skipped / 0** |
| `python -m pytest tests --ignore=tests/solar-pv -q` | `p2-3a-r1-legacy-workspace` | `p2-3a-r1-legacy-pytest` | 2026-11-01 16:26:18 → 16:27:15 | **109 passed、5 skipped / 0** |

实际命令均另带对应不同的 `--basetemp=<上表私有根>`、`--junitxml=<独立 JUnit 文件>`，完整原文在机器证据 `runs.*.command` 中。全量 JUnit 收集 **4144 项**、旧产品 **114 项**、专项 **18 项**；没有通过删除/跳过容量锁测试来实现退出码 0。光伏全量的 7 个跳过为旧有 6 个 Windows 符号链接权限跳过，外加本轮新增符号链接负例的 1 个权限跳过；旧产品的 5 个跳过同属符号链接权限限制。Windows junction 另有可执行测试且不包含于上述跳过项。

### 财务数值保持（独立 SYNTHETIC，并非银行已验证收款）

真实 Phase 2 → 完整 D3 → 只读 3B → 原/候选两轮 3C → 原/候选两轮既有 3D，在全量光伏回归中重新执行；独立 Decimal 预期未改。运行年 1：

| 售价 CNY/kWh | 真实开票 CNY | 75% 预测收款 CNY | 25% 期末应收 CNY | 项目税基 | 权益税基 | 项目/权益期末结转亏损 | 权益所得税付现 |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 原价 0.4 | 35040.0 | 26280.000 | 8760.000 | 33940.0 | 33883.50 | 60.0 / 116.50 | 0.000 |
| 候选 0.6 | 52560.0 | 39420.000 | 13140.000 | 51460.0 | 51403.50 | 0 / 0 | 2175.43750 |
| 候选 0.8 | 70080.0 | 52560.000 | 17520.000 | 68980.0 | 68923.50 | 0 / 0 | 4365.43750 |

销项 VAT 分别为 4031.15044247787610619469027、6046.72566371681415929203540、8062.30088495575221238938053；合计现金税分别为 3888.15044247787610619469027、8079.16316371681415929203540、12284.73838495575221238938053。利息付现均为 56.50、本金实付均为 565、营运资金末年回收均为 200。独立 3A 测试还验证了进项 VAT、计提、亏损结转与现金税桥接，0.6 的重复重放 3C/3D 结果哈希一致，而不同价格的候选哈希不同；原和派生的 Phase 2/3C/3D 身份各自保留。不能把这里的**预测**收款称为银行已证实到账，也未补造终期现金。

## 完整性和阶段门禁

仅修复一个测试文件：`tests/solar-pv/test_phase3e_candidate_replay.py`。该文件基线 Git HEAD blob 字节 SHA-256 为 `4bf1d58d67045e39cc6f8b58b8eb7f9033d6735ce72c9b6f19d08d6f68d99d7b`，最终工作树文件 SHA-256 为 `ab6aa61f8b2017ffead41e1b9fb74b26c5ed94e37d3f58da3952cdc8f0e50376`；两个生产接线文件 SHA-256 不变，具体值见机器证据。六个原有用户差异文件开头/结尾 SHA-256 一致；288 文件保护基线 **286 匹配、2 项既有差异（`reports/validate.json`、`reports/validate.md`）、0 缺失**。旧红色 JUnit 的归档 SHA-256 未变。

**门禁区分**：P2-3A 的严格临时目录回归阻断在上述真实分离布局下解除；符号链接权限负例仍是环境性 SKIP，不计通过。项目级 Phase 3E 仍为 **PARTIAL/BLOCKED_MISSING_INPUT**：`finance.cash_flow_basis` 和 `finance.project_terminal_cash` 缺口未由本轮填补。不作 NPV、价格残差或盈亏平衡求根结论，不进入 P2-3B/P2-4/P2-5/3F。不修改两封存 SYNTHETIC 项目，不 push、部署或发布。
