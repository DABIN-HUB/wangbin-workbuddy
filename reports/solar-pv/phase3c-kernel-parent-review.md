# Phase 3C 原子公式子阶段父审与提交边界

## 当前结论

仅九条冻结消纳/收入原子公式数值子阶段通过；**Phase 3C 整体仍 PARTIAL**。项目级电价、负荷及两个独立业务入口、大时序、完整回归和正式报告仍须联合验收。不得使用本文件放行 Phase 3C、Phase 3 整体、财务、正式四文件、真实工程或平台发布。

初始 HEAD 为 `abc39dc21789ca4564301a809248e5850632e751`。本子阶段本地提交 SHA 在提交后读回至独立提交回执，不制造报告自引用 SHA。保护状态见 `phase3c-startup-state.json`；四个用户文件及全部 288 个保护文件在提交前后另核验。

## 独立数值及专项

父任务重新执行：

`python -B -m pytest tests/solar-pv/test_consumption_kernels.py -q --basetemp=<本轮独占scratch>/kernels-stage-final --junitxml=<本轮独占scratch>/kernels-stage-final.xml`

实际结果：**497 passed，0 failed，0 errors，0 skipped**。数值证据为 `phase3c-formula-numerical-verification.json`，含每条完整有效定义、变量/下标/集合/单位、原字段绑定、独立期望、实际输出与误差及源码哈希；九个独立锚均通过。整数/Decimal（十进制精确数值）及 Fraction（有理数）参考在测试中先独立声明，不用生产输出生成期望。

| 冻结公式 | 独立锚 |
|---|---|
| F-SELF-CONSUMPTION | min(100,60)=60 kWh |
| F-EXPORTED-ENERGY | min(100−60,30)=30 kWh |
| F-CURTAILED-ENERGY | 100−60−30=10 kWh |
| F-ENERGY-BALANCE | 100−60−30−10=0 kWh；非零残差保留符号用于诊断 |
| F-DELIVERED-ENERGY | 60+20+30+0=110 kWh |
| F-SELF-CONSUMPTION-RATIO | (60+20)/110=8/11，无量纲；分母是交付电量 |
| F-LOAD-COVERAGE-RATIO | (60+20)/(80+80)=1/2，无量纲 |
| F-ENERGY-REVENUE | 60×0.8+20×1.2+30×0.4+5=89 CNY |
| F-PPA-REVENUE | 60×0.5+20×0.6+30×0.4+5=59 CNY，不加用电方避免支出 |

其中 kWh（kilowatt-hour，千瓦时），CNY（Chinese Yuan，人民币元），PPA（Power Purchase Agreement，购电协议）。上表单价单位 CNY/kWh，各电量为对应同计量边界、同区间的 kWh；年度公式的集合为明确时段 ID（identifier，标识符）及精确同键映射。完整每一符号定义以数值 JSON（JavaScript Object Notation，JavaScript 对象表示法）中的冻结有效定义为准，不创建第二套公式。

## 父审发现与处理

1. 自用率分母严格保留 `E_delivered = E_self + E_export`，不改为限发前电量；零分母 UNDEFINED，不填零。
2. 电量及上网上限非负，自用/上网/弃电过量拒绝；集合缺项/多项/错配拒绝，缺失值 BLOCKED_MISSING_INPUT；负电价不截零，不提前按分舍入。
3. 初稿对 `revenue.other_benefit` 擅加非负限制。原始 `revenue.other_items.amount` 没有 minimum，原公式也未规定这一限制。父任务先执行独立负额调整例复现拒绝，再修正**新增实现**使用有符号金额，与冻结输入域一致；未改原字段或公式含义。独立例为其他收益 −5 时自持 79 CNY、购电协议 49 CNY。新测试中电量非负断言保持，错误施加于其他金额的限制按原定义纠正，不放宽电量条件或数值容差。
4. 项目编排层另有审查发现的夏令时跳变价变与新增资源相容性问题，已复现并处理，仍须纳入项目级/最终候选回归，不能以本原子核证明闭环。

本子阶段提交只涉及本核、专项测试、计划/启动保护/本数值证据与状态说明；不暂存未联合验收的项目编排代码，不修改旧产品、四个用户文件或原始冻结计算文件。
