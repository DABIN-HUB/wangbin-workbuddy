# Phase 3C 正式审查与验收

**PHASE3C_CONSUMPTION_REVENUE_PASS**：只放行本轮离线电力消纳和售电收益计算，不放行 Phase 3 整体、财务、实际工程、正式四文件、WorkBuddy 或发布。证据生成时间 `2026-10-30T04:38:55.792922+00:00`。最终本地提交和提交后哈希保护由本报告第 2–3 节的独立 Git 回执闭环；不制造未来提交 SHA 或报告自引用。

## 1. 本轮实际业务模块

- `calculation/consumption.py`：九条冻结原子公式。
- `generation_evidence.py`：消费既有 3B 唯一结果、固定上游结果哈希、完整 receipt/分块/规范内容/月年合计及物理输入/方法相容验证。
- `tariffs.py`：严格同轴负荷/市场价格、单位和经济口径、单一/分时/合同/PPA/市场、有效期、带符号价格及费用。
- `revenue.py`：`calculate_rooftop` 与 `calculate_ground` 两条独立业务入口、逐时分配、月年/生命周期账簿、守恒及唯一结果。
- `cli.py consumption`：真实命令行入口。D2 仅扩展有来源且无数值默认的执行控制，不改 469 原始字段和冻结公式。
- 未修改 3B 发电模型；未实现 3D 或后续功能；未增加依赖、平台发布或外部数据适配器。

## 2. 原始与最终 Git HEAD

原始 HEAD：`abc39dc21789ca4564301a809248e5850632e751`。最终候选冻结时 HEAD：`7ae2d8885157334342c42f7cc994805b0542778e`，其允许清单生产/测试 SHA-256 在运行前后核对无漂移。

本报告随最终代码提交，不能在自身提交前写入自身未知 SHA。**最终 HEAD 的规范值是 `C:\Users\wangbin\AppData\Local\hermes\attachments\solar-pv-phase3c-evidence-20261030\git-commit-receipt.json` 的 `final_head`**；该提交后回执必须真实读取 Git 提交、索引、文件集合及四文件/288 哈希后生成。最终用户完成消息同时列出该完整 SHA；在回执未生成前不声称已完成提交。

## 3. 本轮所有本地提交

1. `7ae2d8885157334342c42f7cc994805b0542778e`：九原子核、专项及启动/数值证据，共七条明确路径；已校验四用户文件、288 启动哈希及提交后空索引。原始回执保存在持久证据目录 `kernel-commit-receipt.json`。
2. 最终项目链/验收提交：其完整 SHA、父提交、文件清单及最终分支见上述提交后回执 `commits` / `final_head`，不猜填未来值。不 push、不上传、不部署、不自动进入 3D。

## 4. 消纳、电价公式与冻结口径

九条公式为 `F-SELF-CONSUMPTION`、`F-EXPORTED-ENERGY`、`F-CURTAILED-ENERGY`、`F-ENERGY-BALANCE`、`F-DELIVERED-ENERGY`、`F-SELF-CONSUMPTION-RATIO`、`F-LOAD-COVERAGE-RATIO`、`F-ENERGY-REVENUE`、`F-PPA-REVENUE`。

完整冻结定义、变量/符号/上下标/集合/单位、原字段绑定、适用条件与精确数值锚见 `phase3c-formula-numerical-verification.json`；项目结果也携带 `formula_snapshot.consumption_definitions`。所有九个独立锚真实通过，父专项 497 passed/0 failed/0 errors/0 skipped。自用率分母是交付量（自用＋上网），零分母 UNDEFINED；不能换成可用发电或负荷。收入自持/投资方视角互斥，PPA 不叠加用电方避免支出。费用单列及净价已含费标记不重扣。带符号其他金额按原域保留，不擅增非负限制。

执行登记 `{'IMPLEMENTED_TESTED': 36, 'NOT_IMPLEMENTED': 53}`；原 89 公式、469 原始字段、281 绑定域、189 术语和九类范围未变。矩阵 1208 行，当前状态 `{'NOT_IMPLEMENTED': 693, 'PASS': 515}`；只升级九条原子数值行，不把章节/四文件/平台或其他类别标记为完成。价格匹配及费用桥定义和符号单位见 `docs/solar-pv/27-phase3c-runtime-and-phase3d-handoff.md` 第 3–4 节，不创建第二套冻结公式。

## 5. 独立参考验收（20 类）

参考算法只把固定 3B 的逐时电量当本轮输入，使用 Fraction 精确有理数独立执行分配、合同价、费用及月年累计，不调用 3C 原子核、价格匹配或项目输出构造期望。逐月/年/生命周期每个分项误差限为 1e−9（kWh 或 CNY）；非零比率参考误差限 1e−20。每案实际最大误差见机器证据；不提前分币舍入。

| 序号 | 验收类别 | 结论 | 实际证据 |
|---|---|---|---|
| 1 | 逐时负荷匹配 | PASS | 两类 25 年案例与 load-8760；独立 Fraction 逐区间参考 |
| 2 | 15 分钟匹配 | PASS | load-35040、load-35136 完整三年数值与月度汇总 |
| 3 | 时间区间/时区 | PASS | test_series_header_misalignment_or_incomplete_coverage_is_blocked；春季跳时/秋季重复小时 |
| 4 | 自用及余电上网 | PASS | F-SELF-CONSUMPTION、F-EXPORTED-ENERGY；案例 A |
| 5 | 上限与弃光 | PASS | F-CURTAILED-ENERGY；所有真实案例商业上限 |
| 6 | 分时电价 | PASS | test_tou_prices_follow_same_local_settlement_interval；案例 A 三时段 |
| 7 | 合同/PPA 电价 | PASS | test_single_contract_price_and_explicit_fee；固定/折扣购电协议及完整项目 PPA |
| 8 | 负价与零价 | PASS | 原子核负/零价；test_market_signed_price_and_fee_are_time_matched；案例 B |
| 9 | 自用节省 | PASS | 案例 A 分月/年度/生命周期独立参考 |
| 10 | 地面售电收入 | PASS | 案例 B 独立入口、负价市场及交易费参考 |
| 11 | 月/年聚合 | PASS | 两生命周期案例每年 12 月所有数量/金额分项核对 |
| 12 | 生命周期汇总 | PASS | 全部运营年有理数参考与独立累计 |
| 13 | 单位/金额精度 | PASS | test_original_watts_are_normalized_once_before_quarter_hour_energy；497 项精确核 |
| 14 | 缺负荷/价/结算条件 | PASS | test_empty_or_missing_load_is_not_zero；test_missing_settlement_conditions_are_not_defaulted；价格缺档 |
| 15 | 错误边界 | PASS | 完整项目 wrong load.meter_boundary；ground/roof source 边界拒绝 |
| 16 | 不重复损耗 | PASS | test_repeated_electrical_losses_or_wrong_pinned_source_are_rejected；3B energy.year 数值逐年保留 |
| 17 | 业务隔离 | PASS | test_changed_load_recalculates_rooftop_and_cannot_enter_ground_model；两个独立入口 |
| 18 | 来源失效/冲突 | PASS | test_expired_or_conflicting_price_sources_are_blocked；内联资源及同 header 同行数 D3 内容冲突反例 |
| 19 | 哈希/血缘 | PASS | 真实 CLI JSON 往返；固定上游 hash/块篡改拒绝；持久副本逐块/规范数组读回 |
| 20 | 负荷/价格重算 | PASS | test_price_recalculation_does_not_change_physical_energy_or_allocation；test_changed_load_recalculates_rooftop_and_cannot_enter_ground_model |

## 6. 案例 A：工商业屋顶完整合成消纳

SYNTHETIC（合成），原 3B 1 MWp、25 年情景，消费 `AVAILABLE_PRE_CONSUMPTION`；不重算另一套发电。负荷 400 kW，商业上限 200 kW；购电可避免价 00–08 时 0.5、08–18 时 1.0、18–24 时 0.6 CNY/kWh，外售价 0.4、外售交易费 0.01 CNY/kWh。均为显式受控假设，非地方政策或真实企业负荷。共同价格增长显式为零，非内置默认。

3B 结果哈希 `d693f292ab886b9d175b44d083e0f9517e599437c171389f5dba617b0fa371dc`；3C `7eee9f80f9633a4e93905f2df7bafa9896658020c67069b5276e16f259534a50`。真实 API/CLI 结果哈希相同。

| 项目 | 首运营年 | 25 年累计 | 单位 |
|---|---:|---:|---|
| 进入 C 的边界电量 | 3425598.0000 | 43420022.9522111451649045594923057121594242955301786308387673 | kWh |
| 同区间负荷 | 3504000 | 87600000 | kWh |
| 自用 | 1752000.00 | 35570614.0361530519613629098092344643391355710483182378116400 | kWh |
| 上网 | 876000.00 | 6010119.42845034955210299288365208242643375029502067550278177 | kWh |
| 另增商业弃电 | 797598.0000 | 1839289.48760774365143865679941916539385497418683971752434319 | kWh |
| 消纳交付 | 2628000.00 | 41580733.4646034015134659026928865467655693213433389133144385 | kWh |
| 自持避免购电价值 | 1606000.0 | 32606396.1998069642979160006584649256442076067942917179939996 | CNY |
| 外售收入 | 350400.0 | 2404047.77138013982084119715346083297057350011800827020111331 | CNY |
| 另扣交易费 | 8760.0000 | 60101.1942845034955210299288365208242643375029502067550278177 | CNY |
| 冻结电量总收益 | 1956400.0 | 35010443.9711871041187571978119257586147811069122999881951042 | CNY |
| 扣上述交易费后电量收益桥 | 1947640.0000 | 34950342.7769026006232361678830892377905167694093497814400681 | CNY |
| 守恒残差 | 0.0000 | 0.000000000000000000000000000000000000000000000000000000000000000 | kWh |

首年自用率 `0.6666666666666666666666666667`，分母为自用＋上网；上网占比是相同分母下互补分项。完整每年分项/参考/误差见 `phase3c-cases/industrial_rooftop/acceptance.json` 与持久原始块。

| 月 | 可用 kWh | 自用 kWh | 上网 kWh | 商业弃电 kWh | 节省 CNY | 售电 CNY | 另扣交易费 CNY |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 290941.2000 | 148800.00 | 74400.00 | 67741.2000 | 136400.0 | 29760.0 | 744.0000 |
| 2 | 262785.6000 | 134400.00 | 67200.00 | 61185.6000 | 123200.0 | 26880.0 | 672.0000 |
| 3 | 290941.2000 | 148800.00 | 74400.00 | 67741.2000 | 136400.0 | 29760.0 | 744.0000 |
| 4 | 281556.0000 | 144000.00 | 72000.00 | 65556.0000 | 132000.0 | 28800.0 | 720.0000 |
| 5 | 290941.2000 | 148800.00 | 74400.00 | 67741.2000 | 136400.0 | 29760.0 | 744.0000 |
| 6 | 281556.0000 | 144000.00 | 72000.00 | 65556.0000 | 132000.0 | 28800.0 | 720.0000 |
| 7 | 290941.2000 | 148800.00 | 74400.00 | 67741.2000 | 136400.0 | 29760.0 | 744.0000 |
| 8 | 290941.2000 | 148800.00 | 74400.00 | 67741.2000 | 136400.0 | 29760.0 | 744.0000 |
| 9 | 281556.0000 | 144000.00 | 72000.00 | 65556.0000 | 132000.0 | 28800.0 | 720.0000 |
| 10 | 290941.2000 | 148800.00 | 74400.00 | 67741.2000 | 136400.0 | 29760.0 | 744.0000 |
| 11 | 281556.0000 | 144000.00 | 72000.00 | 65556.0000 | 132000.0 | 28800.0 | 720.0000 |
| 12 | 290941.2000 | 148800.00 | 74400.00 | 67741.2000 | 136400.0 | 29760.0 | 744.0000 |

## 7. 案例 B：集中式地面完整合成售电

SYNTHETIC，原 3B 1 MWp、25 年情景，独立消费 `GRID_DELIVERABLE`；负荷不适用，不把缺负荷补零。商业销售上限 500 kW，市场价 12–14 时 −0.1、其他时段 0.45 CNY/kWh；单位交易费 0.015 CNY/kWh。明确合同允许负价，按实际带符号价格结算，不新增经济弃光策略。

3B 已有电气/送出/站用等损耗及物理限发留在原指标，不再次扣；下面弃电只新增商业约束。3B `c36bdf22097be277e00433d06583ea5ef8ac1467aa86edc0c7a1be06dd1078f5`；3C `6f070c327912973efd79f5cb50a705d4422990132aa28701b1e6fe2a5e6ae616`，真实 API/CLI 哈希相同。

| 项目 | 首运营年 | 25 年累计 | 单位 |
|---|---:|---:|---|
| 进入 C 的边界电量 | 2601720.0000000000 | 40535082.2639562239686459259301394000369923760647323144972845 | kWh |
| 同区间负荷 | 不适用 | 不适用 | kWh |
| 自用 | 0 | 0 | kWh |
| 上网 | 2190000.0000 | 38654745.9788129997119674615240821248888517355430585278745463 | kWh |
| 另增商业弃电 | 411720.0000000000 | 1880336.28514322425667846440605727514814064052167378662274145 | kWh |
| 消纳交付 | 2190000.0000 | 38654745.9788129997119674615240821248888517355430585278745463 | kWh |
| 自持避免购电价值 | 0 | 0 | CNY |
| 外售收入 | 784750.00 | 13851283.9757413248967883403794627614185052052362626391550585 | CNY |
| 另扣交易费 | 32850.0000000 | 579821.189682194995679511922861231873332776033145877918118235 | CNY |
| 冻结电量总收益 | 784750.00 | 13851283.9757413248967883403794627614185052052362626391550585 | CNY |
| 扣上述交易费后电量收益桥 | 751900.0000000 | 13271462.7860591299011088284566015295451724292031167612369394 | CNY |
| 守恒残差 | 0.0000000000 | 0.00000000000000000000000000000000000000000000000000000000000000000 | kWh |

| 月 | 入 C 交付 kWh | 自用 kWh | 销售 kWh | 商业弃电 kWh | 屋顶节省 CNY（不适用业务结构零） | 售电 CNY | 另扣交易费 CNY |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | 220968.0000000000 | 0 | 186000.0000 | 34968.0000000000 | 0 | 66650.00 | 2790.0000000 |
| 2 | 199584.0000000000 | 0 | 168000.0000 | 31584.0000000000 | 0 | 60200.00 | 2520.0000000 |
| 3 | 220968.0000000000 | 0 | 186000.0000 | 34968.0000000000 | 0 | 66650.00 | 2790.0000000 |
| 4 | 213840.0000000000 | 0 | 180000.0000 | 33840.0000000000 | 0 | 64500.00 | 2700.0000000 |
| 5 | 220968.0000000000 | 0 | 186000.0000 | 34968.0000000000 | 0 | 66650.00 | 2790.0000000 |
| 6 | 213840.0000000000 | 0 | 180000.0000 | 33840.0000000000 | 0 | 64500.00 | 2700.0000000 |
| 7 | 220968.0000000000 | 0 | 186000.0000 | 34968.0000000000 | 0 | 66650.00 | 2790.0000000 |
| 8 | 220968.0000000000 | 0 | 186000.0000 | 34968.0000000000 | 0 | 66650.00 | 2790.0000000 |
| 9 | 213840.0000000000 | 0 | 180000.0000 | 33840.0000000000 | 0 | 64500.00 | 2700.0000000 |
| 10 | 220968.0000000000 | 0 | 186000.0000 | 34968.0000000000 | 0 | 66650.00 | 2790.0000000 |
| 11 | 213840.0000000000 | 0 | 180000.0000 | 33840.0000000000 | 0 | 64500.00 | 2700.0000000 |
| 12 | 220968.0000000000 | 0 | 186000.0000 | 34968.0000000000 | 0 | 66650.00 | 2790.0000000 |

## 8. 电量守恒及结算一致性

同节点、同 UTC 半开区间：可用＝自用＋上网＋商业弃电；自用不超该时段负荷，上网不超明确适用上限。每个年度所有分项均按 12 月独立累计核对，再核年度与生命周期；两案例逐时源指标 `energy.year.*` 与原 3B 逐年完全一致。所有案例残差为零；不将负残差截零掩盖过量分配。合同生效/日历覆盖必须唯一，跨价变化且没有子区间电量时阻断。内含交易费只披露，不重复扣。

## 9. 大时序完整数值与资源实测

四个完整小时/15 分钟消纳案例各覆盖三运营年；不是仅打开文件或求和探针。另有两案例各 25 年。原 32 MiB 小 JSON 限制保留，负荷与市场大表走 D3。每案完整调用数为原区间数乘运营年，不能与输入行数或 3B 内部设备运算数混称。

| 案例 | 单表区间行 | 分钟 | 运营年 | 实际引用数据输入 bytes | API 输出 bytes | 完整读取及 API 秒 | OS 进程历史峰值 bytes | receipt 逻辑磁盘 bytes |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| lifecycle-industrial_rooftop | 8760 | 60 | 25 | 350198492 | 150805241 | 243.46899999980815 | 103165952 | 501003733 |
| lifecycle-utility_scale_ground | 8760 | 60 | 25 | 373107296 | 141896830 | 267.469000000041 | 123858944 | 515004126 |
| load-8760 | 8760 | 60 | 3 | 81921604 | 26065242 | 122.28100000019185 | 101339136 | 107986846 |
| load-8784 | 8784 | 60 | 3 | 82141861 | 26133992 | 106.95299999997951 | 106373120 | 108275853 |
| load-35040 | 35040 | 15 | 3 | 323767002 | 103327945 | 366.625 | 106512384 | 427094947 |
| load-35136 | 35136 | 15 | 3 | 324650526 | 103608553 | 337.2029999999795 | 106872832 | 428259079 |

实际输入 bytes 是持久 `generation/settlement` 全部文件的字节和；独立调用方 input/method/budget JSON 副本、CLI 输出镜像另在机器证据计量。API receipt 覆盖其实际引用包/源结果/输出，时间/内存采样截至 receipt 自身 fsync 前；磁盘包含 receipt 最终字节。完整外层读取、API、写入与端到端时间分别保留，不混为同一窗口。输入行有发电、负荷/市场两角色；`input_rows_by_role` 与 `year_interval_settlements` 给出精确口径。预算为合作式应用检查，绝非 Windows OS 硬隔离；私有目录权限前提保留。

## 10. 唯一结果契约和哈希

仍为 `solar-pv-calculation-result/1.0.0`；保留项目/类别、输入、场景、方法、有效公式定义、来源快照及完整 3B 祖先。真实 API/CLI 经过 JSON 文件往返后内容哈希相同；块原字节哈希和规范数组哈希分别核对。持久副本已重新读回 exact membership（精确文件集合）、字节、块哈希及规范数组身份。NPV/IRR/LCOE 等仍是 NOT_IMPLEMENTED/null，根状态 PARTIAL 表示完整项目未完，不与本轮子阶段 PASS 混淆。

## 11. 来源追踪和审查闭环

来源记录保留原信封/实例/元数据、原 3B 结果与行、负荷/市场 header、价格合同/规则及 D2 来源。固定上游哈希不替代来源真实性、授权、方法/新物理输入相容性。审查的两个 P1 已真实复现并修复：夏令时跳时漏价变；新增/替换资源与旧 3B 冲突。后者进一步通过同 header、同 8,760 行、改一条有效合成辐照的真实公开 API 反例，明确返回 `GENERATION_RESOURCE_INPUT_CONFLICT`，无结果发布且失败目录清理。详见 `phase3c-independent-review.md`。

原失败日志/red 证据保留；首次集成输入错误修复的是合成地面 fixture 中误带屋顶字段，未放松生产分类验证。旧测试与冻结断言不修改，不以改 expected 绕过验收。

## 12. 最终完整光伏测试

同一冻结候选最终一次 `pytest tests/solar-pv`：`{'errors': 0, 'failed': 0, 'passed': 4059, 'skipped': 6, 'total': 4065}`，耗时 `6119.120` 秒。计数由本次完整 JUnit 解析，不与早期专项相加。

跳过项及原始原因：
- `tests.solar-pv.test_cli.test_real_symlinks_are_rejected_in_all_path_positions[file]`：Windows symlink privilege unavailable: 22
- `tests.solar-pv.test_cli.test_real_symlinks_are_rejected_in_all_path_positions[ancestor]`：Windows symlink privilege unavailable: 22
- `tests.solar-pv.test_cli.test_real_symlinks_are_rejected_in_all_path_positions[workspace]`：Windows symlink privilege unavailable: 22
- `tests.solar-pv.test_parser_security.test_symlinks_and_linked_root_are_rejected_or_explicitly_skipped[file]`：Windows symlink privilege unavailable: OSError
- `tests.solar-pv.test_parser_security.test_symlinks_and_linked_root_are_rejected_or_explicitly_skipped[root]`：Windows symlink privilege unavailable: OSError
- `tests.solar-pv.test_timeseries_bundle_security.test_symlink_bundle_rejected_when_privileged`：Windows symlink privilege unavailable; junction separately exercised

跳过不是权限边界已运行通过；已执行的其他链接/篡改/路径用例与未执行权限项分开陈述。当前 45 个生产 Python 模块实际编译；源码、测试与静态方法 Schema 对同一候选无漂移。

## 13. Phase 2/3A/3B 完整回归覆盖

以下是最终同一次 JUnit 按对应历史提交测试文件归组的**重叠子集**，不是独立运行数，绝不能相加扩大全量总数：

| 子集 | 历史成员基准 | 测试文件数 | 本轮实际结果 |
|---|---|---:|---|
| phase2 | 6c7081ba32959c3b633f452e43a8826740e79158 | 24 | {'passed': 3014, 'skipped': 5, 'total': 3019} |
| phase3a | a84451fa0a09ce65c6e1e8c67c853d65c4e8c1ca | 35 | {'passed': 3279, 'skipped': 6, 'total': 3285} |
| phase3b | abc39dc21789ca4564301a809248e5850632e751 | 40 | {'passed': 3506, 'skipped': 6, 'total': 3512} |

原始 Phase 2/3A/3B 历史通过数保留原报告，不冒称本轮数字。全部当前光伏测试已在上述单次完整调用覆盖。

## 14. 旧产品含 Expert 回归

同一隔离候选 `pytest tests --ignore=tests/solar-pv packages/experts/wangbin-software-consultant/tests`：`{'errors': 0, 'failed': 0, 'passed': 145, 'skipped': 5, 'total': 150}`；包含默认测试根之外的 Expert 目录。不是仅跑默认 tests 或省略 Expert。

## 15. 保护文件、差异与提交检查

全部 288 个文件与本轮启动原字节哈希相同。候选使用用户已授权的四文件历史字节，隔离 baseline 实测 exit 0、20,235 checks 全部通过。实时工作区 baseline 实测 exit 1，恰有四项授权保留的历史差异，不能改称全局 PASS 或 clean；这不是本轮代码损坏。提交前后 SHA-256 与索引/文件清单由最终回执核验。

四文件只哈希，不编辑、不覆盖、不暂存、不提交：
- `packages/skills/wangbin-receivable-analyzer/SKILL.md`：`8a5ee4eb54a4f6a08d3ab7cccf792c12d5f01ab3fb4ab0de8dc926149087a945`
- `packages/skills/wangbin-receivable-analyzer/manifest.json`：`0a9459ab33f0f3bbc1c538535b994218e6ad92792901a39c3e4e94eaf777762b`
- `products/catalog.json`：`d74f3fa9f00184ee64f8452862958c3ef11f7848378ed42657e4b5fbc91def27`
- `reports/workbuddy-upload-list.md`：`6d0df16f21a4cf7a3a87eef1b90fb2f7d26fd1457f124066707281f9ff0ec586`

Git diff/敏感扫描对最终显式允许清单执行，结果保存在 `quality-and-scope.json` 与提交后回执；不存在回执时不得声称已完成该门。不使用 add-all、reset/restore/clean/stash，不触碰无关改动。

## 16. 未关闭问题及限制

没有剩余**已知且已复现未处理的本轮电量/结算核心缺陷**；不是保证不存在任何缺陷。当前全部来源及价格是合成/受控假设，不能当真实工程、有效地方政策、认证负荷或完整商业使用授权。Sandia 等历史方法许可仍有 REQUIRES_REVIEW 的既有边界，产品发布不因本轮数值通过放行。

代表年重复和 3B 更换年份均保持其明确等效情景；本轮是同区间电量均值匹配，不证明区间内真实瞬时同时性或未知更换日期。未知日历文本、不同网格、缺价格/负荷/条件、混合经济口径均阻断；不新增节假日推断、费用、税额、汇率、储能或净计量。非阻断细化留后续批准，不扩展本版。

## 17. Phase 3D 只读接口交接

交接文档 `docs/solar-pv/27-phase3c-runtime-and-phase3d-handoff.md`：3D 将来可消费收入分项、明确单列/内含交易费标记、实际交付电量及不可变原发电边界。不能把自用节省再加到账收入，不能在净桥之外重复扣同笔费，不能无条件把 3B 入 C 电量当实际售电分母。投资/折旧/运维/税/融资/现金流、净现值 NPV（Net Present Value）、内部收益率 IRR（Internal Rate of Return）、平准化度电成本 LCOE（Levelized Cost of Energy）均未实施；不自动执行 3D。

## 18. 独立发布门禁与停止

`verify_baseline.py --release` 实测 exit 1、BLOCKED，隔离文档完整性 PASS 不代替发布。真实项目/真实资源政策/四文件、WorkBuddy 安装调用和平台审核等仍独立 BLOCKED/NOT_TESTED。18 章、13 附录、189 术语、DOCX（Office Open XML Word Document）、PDF（Portable Document Format）、两个 XLSX（Office Open XML Spreadsheet）完整范围不删减，本轮不提前生成它们。

原始持久证据：`C:\Users\wangbin\AppData\Local\hermes\attachments\solar-pv-phase3c-evidence-20261030`；汇总 `phase3c-final-execution-evidence.json`。API（Application Programming Interface，应用程序编程接口）、CLI（Command-Line Interface，命令行接口）、UTC（Coordinated Universal Time，协调世界时）、D3（有界本地时序包）、OS（Operating System，操作系统）、CNY（Chinese Yuan，人民币元）、kW（kilowatt，千瓦）、kWh（kilowatt-hour，千瓦时）、MWp（megawatt-peak，兆瓦峰值）、SHA-256（Secure Hash Algorithm 256-bit，256 位安全散列算法）。其余原公式英文符号/术语以有效定义及 189 词表为准。

**最终本地提交及提交后回执完成后立即停止；不 push、上传、发布、部署或进入 Phase 3D。**
