# Phase 3B 发电计算运行与 Phase 3C 输入交接

本文件仅描述已落地的离线能源入口及后续消费者约束，不实现Phase3C，不改变原18章、四文件、九分类或89公式。正式验收状态以phase3b-review-and-acceptance.md及实际Git/JUnit证据为准。

## 1. 公开入口

Python API：`wangbin_solar_pv.calculation.energy_yield.calculate_rooftop`、`calculate_ground`。

两者参数为：完整Phase2导出、严格D2方法配置，以及命名参数`catalog/output_dir/budget/bundle`。bundle可为已由D3 `read_bundle`完整校验的句柄；没有bundle时只从Phase2导出消费原小JSON输入。公开入口重新验证项目、分类、来源、定义和方法身份，结果发布前重新遍历全部数据集校验canonical内容摘要。

CLI（目录均在显式授权的已存在私有workspace内，结果目录不得存在）：

```text
python services/solar-pv-engine/solar_pv.py --workspace <private-workspace> energy --input input.json --methods methods.json --budget budget.json --bundle resource --output generation
```

`input.json`是既有完整导出；`methods.json`是既有D2 schema；budget JSON显式给D3的输入bytes/磁盘bytes/行数/秒/进程内存预算（CLI示例使用整数秒）。不更改32MiB默认JSON限制。原子资源信封通过D3有界块保存，不能把大表塞回小JSON或偷换为空数组。

## 2. 输出与计量边界

- `result.json`：既有`solar-pv-calculation-result/1.0.0`，完整数值和身份；最后发布，未完成目录没有可用的完整结果标记。
- `interval-*.jsonl`：有界中间证据。每条保留原row_id、UTC半开起止、实际小时、POA、原子实例/来源及各运营年的DC/温度/逆变器组/损耗/限额结果。更换年有正常与停运两种独立重算状态及等效时长权重。
- `receipt.json`：输入行数、物理计算数、真实资源采样、块文件hash及result_hash。测量终点与磁盘自计量范围明确，逻辑预算不是OS隔离。阶段外验收另量完整调用耗时和实际文件字节。

根status保持PARTIAL，因为消纳/财务未实现；这不抹掉已计算的能源metric。maturity.calculation区分合成或条件性计算，real_project/four_files/platform独立不放行。

指标：`dc_capacity`（kWp）、`ac_capacity`（kWac）、`dc_ac_ratio`、`energy.monthly.year.<y>`（12元素kWh数组）、`energy.year.<y>`、`energy.annual_array`、`energy.lifecycle`、`energy.mean_annual`、等效小时、容量因子、实测口径PR、逆变器与系统可用电量。

- 屋顶最终能源边界：`AVAILABLE_PRE_CONSUMPTION`。不拿上网限额限制全部可供自用的电量；变压器/送出/限发不适用段必须显式为零情景，不能隐含缺数补零。
- 地面最终边界：`GRID_DELIVERABLE`，逐时执行共享变压器有功上限、送出损失、可用率、明确并网/可用容量上限与限发；不代表电网已许可。
- 中间指标分别为`INVERTER_AC`、`SYSTEM_AVAILABLE`；不可把限额前电量当成交付量。
- 月度POA_PR只接受明确的`SYSTEM_AVAILABLE_AFTER_AUXILIARY_AVAILABILITY_PRE_CURTAILMENT`计量边界及已包含损失台账。它是固定PR条件情景，不产生逐时削峰、真实交付或精准停机结果；缺时序但需要停机瓶颈重算时阻断。

## 3. 生命周期与方法适用性

原`project.evaluation_years`决定1—100完整运营年数量。首年初衰只应用一次；年度或无重叠分段率更新DC性能，每年重新执行逆变器及后续瓶颈，不缩放已经限幅的年度输出。

同规格设备事实来自原字段。`energy.dc_allocation`是D2显式分配比例，和必须为1，逐台数量与原设备一致，分配后的组串必须为整数且满足逐台电流约束。不能从异构设备自由文本或未知分配猜出均匀分配；原始资料不能承载时明确阻断，不新建原始输入合同。

更换规则通过`replacement.rules`关联原事件ID，原事件给设备ID、年和停机天数；明确恢复目标及容量比例，不从performance_ceiling推导恢复量。逆变器停运另指定设备ID集合且校验容量范围；组件更换按各组均匀比例假设。日期未知时只接受年初恢复/均匀等效停机场景，且两个状态各自重算限幅后再按时长加权，不是实际年内停机窗口。多件同时/范围重叠且没有无歧义规则的事件保持BLOCKED。

STC组串电气数值检查与带来源的冷/热设计复核引用分开，缺失温度电压系数不捏造。面积按原可利用面积、真实组件尺寸及显式GCR核验，不使用固定W/m²；不是结构或消防审批。跟踪支架未知方法保持方法阻断。

## 4. Phase 3C 消费协议（尚未实现）

1. 先用既有validate_result验证唯一结果、定义、input_hash/source_snapshot_id/method_config_hash/result_hash；验证receipt所列中间文件摘要和逐条canonical内容身份。
2. 使用区间实际UTC起止、时区、粒度、来源和运营年索引对齐负荷及价格，不按数组行号直接配对。代表年重复明确是同一物理资源年情景，不伪装未来实际日历年；YEAR_SPECIFIC保留真实资源年映射。
3. 屋顶使用每条`available_kw × hours`作为待分配可用电量，之后才执行原冻结自用/上网/弃光平衡。地面使用GRID_DELIVERABLE边界，不套屋顶负荷或租赁规则。
4. 年度数组为后续成本/财务的同边界能源输入，不是收入/现金流。当前`consumption/revenue/npv`均null+NOT_IMPLEMENTED，不能当0消费。
5. 来源失效、块篡改、数据缺失、期间/粒度不齐或方法不足时明确阻断；不填零、不创造小时曲线或新接口。Phase3C必须另获当前阶段指令后才开发。

## 5. 明确保留的门禁

真实资源接口仍Phase4；不加入HTTP气象客户端。Sandia公开方法/设备参数适用与商用来源授权仍需真实项目另核。四份正式报告、18章内容、财务指标、其他七类完整业务、WorkBuddy及发布门禁均未由本阶段放行；所有原要求继续保留。
