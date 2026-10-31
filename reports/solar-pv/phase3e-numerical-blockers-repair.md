# Phase 3E 数值阻断专项修复及审批阻断（本轮）

## 范围与版本

启动 HEAD `2a7ad0adcd8182302ab63b9651385d52dc55eb24`，分支 `main`。本轮仅修改 `services/solar-pv-engine/src/wangbin_solar_pv/calculation/financial_metrics.py` 的 IRR 求解过程，新增独立数学测试 `tests/solar-pv/test_phase3e_irr_roots.py`，代码提交 `49faaac4dddf920fc0be7120fddd3c5f11726d72`。本报告、机器证据、两份 JUnit XML 和两份测试 ID 清单为新增文件，未改冻结定义、D2 配置、Phase 3B/3C/3D 结果、两个 SYNTHETIC 案例或前轮审计报告。最终报告提交 SHA 及最终 HEAD 由提交后单独的本地收据记录，避免提交文件引用自身尚未产生的 SHA。

冻结版本 `solar-pv-formula-definitions/1.0.1`，有效定义哈希 `617a2e9d314c095bd2ec893939c930a2323be6fd7805da12bf6d6fdd70274808`。验收分开记录公式数值内核和项目数据闭合；前者成功不代表后者通过。

## IRR_EVEN_MULTIPLICITY_ROOT — PASS（数值专项；非项目级通过）

冻结 `F-IRR-PROJECT`、`F-IRR-EQUITY` 按年度现金流第 0 至 N 期求 NPV 零点；D2 已登记 `EXACT_RATIONAL_POLYNOMIAL_ISOLATION`，搜索域、残差容差、根集合及预算见 `docs/solar-pv/05-formula-registry.md`、`services/solar-pv-engine/src/wangbin_solar_pv/calculation/method_config.py`。旧 `_irr` 在 `financial_metrics.py` 只扫描离散样本点和相邻异号区间；偶重根与未采到的局部接触点没有异号，因而误报 `NO_ROOT`。旧实现还不能证明根集合完整。

修复在已有冻结数值方法内，把有限 Decimal 年度现金流精确表示为有理系数多项式 `P(x)=Σ CF_y·x^(N−y)`（`x=1+r>0`），用多项式 GCD 消除重因子并以 Sturm 符号变差计数、隔离有界域内不同实根；以有界精化取得候选，将候选代入原 Decimal NPV 检查货币残差。不把接近零的极小值当根，也不因利率区间宽度满足容差就忽略高导数场景的残差。根集合多个返回 `UNDEFINED/MULTIPLE_ROOTS` 并保留根证据；无根返回 `UNDEFINED/NO_ROOT`；退化、非法输入和预算耗尽保持各自状态，不造 0% IRR。

独立解析参考：`[-100, 220, -121]` 对应 `-100(x−1.1)^2`，唯一不同实根为 `r=0.1`；实际 `CALCULATED`，返回 `0.10000000000000000000024352197233561134748214271894539706408977508544921875`，NPV 残差 `−4.901070331423657722435204839828813734E−42`。`[-100, 230, -132]` 对应 `-100(x−1.1)(x−1.2)`，实际 `UNDEFINED/MULTIPLE_ROOTS`，不同根约 `0.1` 和 `0.2`，没有擅选一个。`[-100, 220, -121.00000000000000000001]` 在已配置搜索域内无根，实际 `UNDEFINED/NO_ROOT`，不因近零残差产生伪根。测试还覆盖近距离不同根、负根、边界根、退化流、非法域，以及近 `−1` 高导数的独立异号区间。

根集合完整性条件：**多项式次数 ≤100，有限 Decimal 系数，合法 `r>−1` 有界域；有理多项式 GCD 和 Sturm 隔离在计算上限内完成，随后每个根均通过原方程残差验证。**若隔离或精化预算不足，不得从部分根推断唯一性，必须报告不收敛。命令 `python -m pytest tests/solar-pv/test_phase3e_irr_roots.py tests/solar-pv/test_phase3e_financial_metrics.py -q --tb=short`：**34 passed**，退出 0。源码 `compileall`、本轮代码 `git diff --check` 通过；最终候选的完整回归见下文。因此该**已实现的 IRR 数值专项**为 PASS，但两案并无可供实际项目计算的完整现金流。

## BREAK_EVEN_TARIFF_FULL_RECOMPUTATION — BLOCKED，停止改动并申请审批

冻结 `F-BREAK-EVEN-PRICE` 要求事前指定可变结算电价项，固定其余外生输入，对每个候选价重算同口径项目收益、税费、现金流和 NPV，返回批准价格域内的零点集合；见 `docs/solar-pv/05-formula-registry.md:3290-3338`。现有 `financial_metrics.py:374-412` 的 `_break_even` 对价格—现金流样本进行线性插值并求根，**没有**调用 Phase 3C 收益、Phase 3D 税费和收款账簿，也未证明样本之间全根；`phase3e.py:191-203` 目前正确将既有两项目该公式阻断。独立缺陷复现：两个样本价格 0 与 10、一期现金流 `−1e−20` 与 `9e−20`，仿射数学根为 1；旧实现却返回 `CALCULATED` 价格 5，代回样本残差 `4e−20`。这只证明旧求解器容差/插值问题，**不是**完整收益税务链的验收算例。不能把其任一输出称为已验收的全链电价。

可复用的既有依赖：`revenue.py:149-225` 使用经校验的 3B 发电证据、分时/市场价格及负荷重算自用收益、售电收入、交易费；`financial_ledger.py:193-267` 从 3C 年度 ledger 重算收款、税基、VAT、税损及税现金；`phase3e.py:122-212` 组合项目/权益现金流和 NPV。`tariffs.py:123-176` 分别消费 `tariff.periods.sale_price`、`avoidable_price`、PPA 或 8760 行市场报价；改一个价格项不等于改全部电价，更不等于改交易费。3B 发电可以保持不变，但 3C 重放仍须经 D3 bundle 的 `base_export` 和来源身份校验（`generation_evidence.py:123-147`）；不得修改封存件或就地改共享结果。

**审批阻断**：现有 D2 `break_even.minimum_price`/`maximum_price`、`price_tolerance`、`maximum_iterations` 和批准方法已登记，但严格的 D2 Schema (`method_config.py:139-161,164-173`) 以及现有 CLI (`cli.py:49-66,145-195`) 均无带来源、参与结果哈希的「指定价格字段 + 行/序列」选择器。两个封存案例没有声明调屋顶哪一行售电价/自用避免价，地面采用市场逐时价格，不能任选；仓库内两案 D3 manifest 亦不足以重放完整 8760 行数据，不能假设仓库外原数据不存在。此外两案的项目终期现金等必要事件仍缺，不能生成真实 NPV 根。为补选择器而扩 D2 Schema、发明旁路输入或按分时倍率变更输出字段均触及未经批准的关键配置/输入合同。依据用户停止规则，本轮**没有实现价格全链修复，没有新增测试宣称通过，也不更改既有样本求解器或项目阻断状态**。请先批准受控选价身份、合法候选场景重放输入与终期现金来源的处理方式；未获批准前状态保持 `BLOCKED`。

## 最终候选与保护

两个原 SYNTHETIC 案例本轮以同一源码重新运行 CLI/API：各 26 期间、21 项指标，均 `CALCULATED=0 / UNDEFINED=1 / BLOCKED_MISSING_INPUT=20`；`F-DSCR` 为 `UNDEFINED/ZERO_DEBT_SERVICE`，四笔付款 `INDETERMINATE`。CLI/API/侧车结果哈希相符；未补合同 CFADS 调整量、项目终期现金、真实股东收付、日期现金事件、期间非受限现金平衡或投资目标。两个项目仍非 Phase 3E 项目级 PASS。

WorkBuddy/Expert：`python -m pytest tests --ignore=tests/solar-pv -q --junitxml=<独立 scratch 路径>`：114 个唯一测试 ID 全覆盖，**109 passed / 5 skipped / 0 failed / 0 errors**，退出 0；5 个跳过为 Windows 符号链接能力相关。光伏：`python -m pytest tests/solar-pv -q --junitxml=<独立 scratch 路径>`：2026-10-31 13:01:06+0800 至 14:32:36+0800，退出 **0**，4109 个收集 ID 与 4109 个实际执行 ID 完全相同且无重复，**4103 passed / 6 skipped / 0 failed / 0 errors**；6 个跳过为 Windows 符号链接权限相关。完整候选源码 HEAD `49faaac4dddf920fc0be7120fddd3c5f11726d72` 的三项源码 SHA 在运行前与运行后相符；两份原始 JUnit 和完整 ID 清单保存在本报告同名前缀文件，具体命令、SHA、时间及计数见机器证据。前轮 `4086 passed / 6 skipped` 仅为历史比较，不挪用。

六个既有用户差异文件 SHA-256 已与启动记录一致，未暂存、修改或清理；288 文件基线 286 匹配、`reports/validate.json` 和 `.md` 两项既有偏差、零缺失，未新增偏差。哈希明细见机器证据。未引入新业务功能、公式、字段、D2 参数或生产状态枚举；未 push、部署、上传或发布。数值门禁分别为 **IRR_EVEN_MULTIPLICITY_ROOT=PASS**、**BREAK_EVEN_TARIFF_FULL_RECOMPUTATION=BLOCKED**；现阶段 **PHASE3E=PARTIAL/BLOCKED**，Phase 3F/3G 未启动。下一步须对受控电价选择器及完整情景重算数据作审批，绝不以本轮全量测试通过替代仍缺失的真实项目输入或电价全链验收。
