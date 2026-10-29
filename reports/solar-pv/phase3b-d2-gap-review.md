# Phase 3B D2 接入缺口审查：站用功率与更换事件

**审查状态：结论已形成；本报告不代表真实项目数据已具备，也不代表Phase3B总体通过。**

## 站用功率

静态审查确认：`energy.auxiliary_kw`在`docs/solar-pv/05-field-bindings.json`中定义为尚未扣除的站用功率（kW），但原始支持域只列`system.losses`和`system.topology`；`system.losses.value`是0到1比例，不能承载kW，`system.topology`是自由文本，也不能藏数值。

依据`docs/solar-pv/19-phase3-approved-implementation-contract.md`第8行及`docs/solar-pv/18-phase3-preimplementation-review.md`第55—67行，已批准的D2范围允许独立版本化、严格Schema化的方法/数值策略/显式假设配置；新增参数必须有类型、单位、来源、状态、版本、分类、边界并纳入方法hash和计算身份。当前67个参数不是冻结数量上限，因此本缺口属于已批准D2内的最小typed扩展，不是对469原始字段的修改，也不是新的实质数学审批项。

本轮新增`energy.auxiliary_kw`方法控制：

- number，单位kW，非负；
- 语义为选定期间和计量边界内尚未扣除的显式站用功率情景；
- 不提供数值默认，缺少时`MethodConfig.require`返回`BLOCKED_METHOD_REVIEW`；
- 配置内容及来源进入既有方法hash；不改Phase2 input_hash、原始字段含义或旧输入；
- 仍需适配层核查上游是否已经包含站用功率，避免重复扣除；时变站用曲线不由该恒定参数伪造。

这保持当前`solar-pv-method-config/1.0.0`的严格结构和明确内容身份；后续若要把配置格式发布为独立兼容版本，必须保留旧配置/hash并显式迁移，不能重写旧身份。

## 更换恢复与停机

`assets.replacements.performance_reset`仍是字符串事实，不能从自由文本任意抽取恢复量；`degradation.performance_ceiling`仅是更换后的性能上限，不能单独推导每次恢复量。只有规则明确指定恢复目标、适用资产和容量范围时，才能使用该上限；否则阻断。

已有`downtime_days`可用于明确的等效可利用率情景，但没有精确年内更换日期时，不能声称重建真实逐时停机窗口。可选的明确情景必须声明年边界恢复或年度等效停机，并披露日期未知、恢复生效时点是假设、停机不是实际窗口；每年仍需重新计算DC、逐组逆变器限幅和后续损失，不能整体缩放已限幅的年度电量。真实逐时事件要求若缺证据，继续`BLOCKED`。

## 验证

新增方法控制专项及既有计算契约回归：**86 passed / 0 failed / 0 errors / 0 skipped**（`test_method_configuration.py`、`test_calculation_contracts.py`、`test_calculation_review_regressions.py`，最终JUnit `auxiliary-method-final2.xml`）。

本报告只记录D2接入决策和边界。温度/损失/工程原子核此前专项通过，但项目级发电链、年度重算、两分类入口、完整时序和最终结果契约仍未闭合；Phase3B保持`PARTIAL`。不push、不部署、不上传、不发布。
