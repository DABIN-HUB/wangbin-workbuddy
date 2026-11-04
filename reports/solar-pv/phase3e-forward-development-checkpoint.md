# Phase 3E 前进开发检查点：条件式项目 IRR

## 实施范围

在独立工作树 `F:/ideaWorkSpace/wangbin-workbuddy-dev`、分支 `solar/phase3e-forward`，从 P2-5B 提交 `ba3c40b76b90ef92151d25e6b054e7738e2fa674` 开始开发；原工作树与其正在执行的 P2-5 光伏 L3 不变。此检查点只接通**有来源的 SYNTHETIC、年末、同一项目税前或税后向量**下的 `F-IRR-PROJECT` 已有内核，不更改冻结公式、输入字典、财务口径、正式状态枚举、两个封存项目或已有测试。

- 复用 D2 现有 `irr.method`、上下界、`irr.root_tolerance`、`irr.maximum_degree` 的配置、来源和方法哈希；不选择默认域、精度或上限。缺项、未审核、未获授权或超出次数预算的路径保持非数值状态，不推出 IRR 数字。
- 内核的多根、无根和不收敛原有状态及根集 details 不改；候选价与原项目仍各自按其选定的财务流计算，不能跨价复用结果。没有整套 IRR 控制的既有案例保持旧行为；部分配置明确阻断。
- `F-BREAK-EVEN-PRICE` 仍 `value=null` / `BLOCKED_MISSING_INPUT`；EVENTS、股东收付、CFADS/DSCR、DATED-NPV、LCOE、最差现金年等未合法闭合，不能升级为 PASS。

## 当前候选已执行检查与延期清单

- 本工作树 `phase3e.py` 编译：成功；`git diff --check`：通过。
- 已有快速/契约专项：`test_phase3e_financial_metrics.py`、`test_phase3e_irr_roots.py`、`test_calculation_contracts.py`，**69 passed / 0 failed / 0 skipped**，29.73 秒；当前工作树、独立私有临时目录的 JUnit：`C:/Users/wangbin/AppData/Local/hermes/cache/scratch/solar-forward-fast-6da65f6e9c/junit.xml`。该集合验证内核与旧契约，不包含新条件接线的全链数值验收。
- 有来源 IRR 的生产编排全链 E2E：**NOT_TESTED**；两个封存项目：**NOT_TESTED**；本工作树完整光伏 L3、WorkBuddy/Expert L3、L2 全量：均 **NOT_TESTED**。原工作树运行中的 P2-5 L3即使完成，也仅覆盖旧身份，绝不计为本分支新代码验收。
- Phase 3F/3G、4、5、6、7：本检查点**尚未实施/NOT_TESTED**。依赖有源且已批准的场景控制、真实项目专业事实或上游通过证明的路径继续阻断；可独立实现的后续路径不受普通子阶段全 L3 等待阻塞。

## 风险与后续门禁

来源绑定与结构由已有 `MethodConfig`、终期绑定和 `validate_result()` 检查；新增的条件分支尚未取得独立数值的全链回执，不能宣称 Phase 3E PASS。重大集成/最终候选须冻结同一代码、测试、配置字节，集中运行不缩水的 L3、必要真实 E2E 与性能/WorkBuddy 验收，保留每项失败和跳过。Phase 7 后只交付用户自行上传平台实测；用户确认前不进入 Phase 8A–8G，不 push 或发布。
