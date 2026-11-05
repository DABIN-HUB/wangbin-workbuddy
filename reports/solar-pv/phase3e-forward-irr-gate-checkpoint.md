# Phase 3E 开发检查点：项目 IRR 缺来源时准确阻断

基线：独立工作树 `solar/phase3e-forward` 的 `6719de800190bddce46b37abcb614797e4ba0b0e`。本检查点不更改冻结公式、469 原始字段、89 条 Catalog、正式结果 Schema、两个封存项目、原 `main` 或正在运行的 P2-5 L3。

## 实际代码

- `phase3e.py` 的 `calculate_sourced_project_npv()` 已在 P2-5B 接通 `F-PROJECT-CASH-FLOW`、`F-PROJECT-PRETAX-CASH-FLOW`、`F-NPV`、`F-CUMULATIVE-CASH-FLOW`、`F-DISCOUNTED-CUMULATIVE-CASH`、`F-STATIC-PAYBACK`、`F-DYNAMIC-PAYBACK`。累计与两类回收期四项是**既有提交的生产代码**，本轮不重复实现或计算新增数量。
- 本轮完善既有 `F-IRR-PROJECT` 条件式入口：`_record_sourced_project_irr()` 仅在五项 D2 搜索方法来源完整、已授权且多项式次数预算允许时使用同项目选定税前/税后现金向量调用已有冻结 IRR 内核。完全缺失或部分缺失的情况一律保留 `BLOCKED_MISSING_INPUT` 和 `value=null`，未审核为 `BLOCKED_METHOD_REVIEW`；不再将缺方法的运行结果错报为产品尚未实现。无默认搜索域/容差、无跨项目或跨候选价格共享。多根仍 `UNDEFINED`，根集保存在已有 details；不改正式输出结构。
- 既有昂贵 E2E 的一处旧断言改为更严格地检查缺来源状态、空值及五个确切缺项，**不删除或放宽**用例；该 E2E 本轮不运行。新增独立轻量契约检查直接复核缺项、未审核、次数预算、唯一根、多根与 canonical 结果结构，没有伪造真实项目证明。

## 本分支检查与未测试

- 生产和相关检查源码编译成功、`git diff --check` 通过；已执行既有数学/IRR/契约测试及新增 IRR 快速检查：**73 passed、0 failed、0 skipped**，31.55 秒；JUnit：`C:/Users/wangbin/AppData/Local/hermes/cache/scratch/solar-irr-gate-e41e6cd9ff/junit.xml`。
- 新条件式 IRR 的真实 Phase 2→D3→3B→3C→3D→3E 全链数值 E2E、被强化断言所在的慢 E2E、当前分支完整 L2/L3、两个封存项目实测：均 **NOT_TESTED**。快速契约测试不能替代它们；原 `main` 的 P2-5 L3 无论结果如何均不能证明本提交。

## 硬依赖（不得用零或旧来源解锁）

- `F-NOMINAL-REAL-RATE` 已有带输入门禁的生产入口，但没有同税/风险/币种一般通胀与真实利率来源；`F-WORST-CASH-YEAR` 缺事前比较范围、含建设/运营双范围及获准的正式数值表示；`F-INVESTMENT-HURDLE-GAP` 缺用户目标及比较方向。均不得以年账现有值推定缺失来源。
- 股东可分配与已付收款、现金余额、权益 IRR、CFADS/DSCR、生命周期成本/LCOE、DATED-NPV 仍受各自现金事件/范围/口径证据阻断；EVENTS 缺交易级排重及税务依据。正式 `F-BREAK-EVEN-PRICE` 继续 `BLOCKED_MISSING_INPUT`、`value=null`，不重新做根集数学探索。Phase 3E 整体仍 **PARTIAL**，不得宣布发布就绪。
- 以上已穷尽本批无需新增专业假设、来源、结果表示或范围勘误即可接通的 Phase 3E 项；其他独立可开发路径在既定后续阶段推进，受限功能不绕过。Phase 7 后须交付用户上传 WorkBuddy 实测，确认前不开展 Phase 8A–8G。
