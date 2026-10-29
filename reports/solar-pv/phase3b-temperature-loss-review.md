# Phase 3B 温度与损失专项复核

**状态：PARTIAL；温度与损失原子模块专项通过，不代表Phase 3B总体通过。**

## 子任务结果

温度/损失子任务`deleg_82a81330`因上游API慢响应/空响应重试失败，未提供可采纳的完成总结。父任务对其已落盘的生产代码和专项测试逐文件读取，并自行完成失败复现、根因定位和修正验证；不采用子任务未核实的运行统计。

涉及生产模块：

- `services/solar-pv-engine/src/wangbin_solar_pv/calculation/temperature.py`
- `services/solar-pv-engine/src/wangbin_solar_pv/calculation/losses.py`

涉及专项测试：

- `tests/solar-pv/test_energy_temperature_losses.py`

## 实际验证

首次父复现为 **20 tests / 19 passed / 1 failed**。失败根因不是温度生产公式错误，而是测试同时混用了两种状态：`SYNTHETIC` 参数必须是明确的`ASSUMED`，而未验证外部方法参数应使用非SYNTHETIC来源；测试先把来源/状态建模为不可能的组合，触发`SYNTHETIC_IS_NOT_VERIFIED`，未到达预期的温域断言。

修正专项测试使以下事实分别可验证：

- 合成配置：`data_mode=SYNTHETIC`、`source_kind=SYNTHETIC`、`status=ASSUMED`，可以执行受控算例。
- 方法来源未验证：使用`DOCUMENT_EXTRACTED`、`status=UNVERIFIED`，配置可保存但执行被`BLOCKED_METHOD_REVIEW`阻断。
- 方法参数错误仍进入真实温域校验并返回`THERMAL_MODEL_TEMPERATURE_DOMAIN`。

最终父命令（Python 3.12，独占scratch basetemp）：

```text
pytest tests/solar-pv/test_energy_temperature_losses.py -q
```

结果：**20 passed / 0 failed / 0 errors / 0 skipped**，JUnit：`solar-pv-phase3b/thermal-parent-green3.xml`。

## 已核实能力

- Sandia两步模型：先模块温度，再电池温度；`Decimal.exp`受显式精度上下文控制，未把环境温度静默当作电池温度。
- 零辐照使用明确夜间分支，温度返回环境温度但保留方法血缘；负辐照、负风速、绝对零以下、浮点输入拒绝。
- `CELL_TEMPERATURE_SUPPLIED`必须提供显式电池温度；`NOT_REQUIRED_PR`返回`NOT_APPLICABLE`，不当作时序温度模型执行。
- 方法配置在准备边界重新验证；`PreparedTemperature`不持有可变`MethodConfig`，可复用在逐行时序调用；结果details含方法、版本、参数ID、来源ID、来源引用和模块温度。
- 损失账簿按显式DC/AC/GRID边界执行，保留冻结`kind`、稳定ID、原sequence、来源和`included_in_source`；每项使用乘法保留率，输出before/lost/after，独立校验物理守恒。
- 重复ID、错误边界、上游已扣、已含来源、缺来源、非法损失率、非法预算精度均被阻断；零能量可合法计算且不会把未知转成零。

## 尚未闭合

该模块尚未接入完整Phase2输入适配、逐时发电、逐年衰减/更换、设备异构时序、统一结果契约或两类项目入口。Sandia公开方法来源在`reports/solar-pv/phase3-method-access.json`中标记`REQUIRES_REVIEW`；本轮合成配置仅用于算法闭环，不代表真实站址方法已获专业/许可验收。当前Phase3B总体仍为PARTIAL。

未push、未部署、未上传、未发布；未形成3B commit。
