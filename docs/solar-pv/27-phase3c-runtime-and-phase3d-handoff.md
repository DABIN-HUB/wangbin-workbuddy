# Phase 3C 运行合同与 Phase 3D 接口交接

本文件描述本轮落地的离线消纳/售电收益接口。最终验收结论以 `reports/solar-pv/phase3c-review-and-acceptance.md` 及其真实运行证据为准；本文本身不是放行。原 18 章、13 附录、89 公式、469 原始字段、189 术语和四份正式文件的范围不变。不实现 Phase 3D。

## 1. 公开入口及输入

Python API（Application Programming Interface，应用程序接口）：

- `wangbin_solar_pv.calculation.revenue.calculate_rooftop`：工商业屋顶。
- `wangbin_solar_pv.calculation.revenue.calculate_ground`：集中式地面。

位置参数：完整 Phase 2 导出、严格 D2 方法配置；命名参数：`generation_dir/generation_result_hash/catalog/output_dir/budget/bundle`。3B 发电入口仍在 `calculation.energy_yield`，没有替换或重构。

CLI（Command Line Interface，命令行接口），所有路径在显式授权的私有 workspace 内：

```text
python services/solar-pv-engine/solar_pv.py --workspace <private-workspace> consumption --input input.json --methods methods.json --budget budget.json --generation generation --generation-hash <pinned-3B-result-SHA256> --bundle settlement --output consumption
```

没有负荷/市场大表时可省略 `--bundle`，例如使用原小 JSON 价格表的地面全售电。目录参数不是 JSON 文件参数；输出不得已存在，目录穿越、链接/不安全别名由原路径合同拒绝。SHA-256（Secure Hash Algorithm 256-bit，256 位安全散列算法）必须按原小写 64 位标识符提供，不自动纠正或改写。

3B 输入目录必须保留 `result.json/receipt.json/interval-*.jsonl` 完整集合。先验证唯一结果、调用方固定的结果 hash、输入/来源/方法/定义身份，再逐块核对 bytes/hash、canonical 数组内容、真实区间、运营年集合及月/年/生命周期汇总。hash 证明内容完整性，不是数字签名或真实现场认证。月度 PR（Performance Ratio，性能比）总量不够支撑精确负荷匹配，不能制造逐时曲线。

C 阶段可以仅提供结算数据，不重复提供辐照资源。如果当前导出或 bundle 再携带资源，必须与 3B 使用的资源逐数据集 canonical 内容、行数及来源 header 一致；**不能比较整个 bundle hash**，因为其中 base_export 会随新增结算事实合理变化。不得新增或替换相矛盾的物理事实/方法，却继续复用旧电量。

## 2. 时间、来源及计量边界

- UTC（Coordinated Universal Time，协调世界时）半开区间 `[start,end)` 为匹配轴；IANA（Internet Assigned Numbers Authority，互联网号码分配机构）时区校验真实偏移和本地日期。DST（Daylight Saving Time，夏令时）重复小时是两个真实区间，虚构的跳时墙钟不合法。
- 负荷与发电必须同起止、粒度、时区和计量点。时段缺失、额外数据、错位、不同粒度明确阻断，不按数组序号假配、不重采样或插值、不补零。
- 原 `load.series.energy` 为 kWh（kilowatt-hour，千瓦时）；`load.series.power` 为 kW（kilowatt，千瓦），只乘一次真实经过小时。两者同时给出必须相容。原单位换算先由 Phase 2 信封完成，C 阶段不重复换算。
- 负荷 `quality_flag` 必须是原枚举 `valid`；缺失、估算、异常不假作精确企业负荷。所有合成资料保留 SYNTHETIC 说明，不能升级 VERIFIED 或真实项目通过。
- 屋顶只使用 `AVAILABLE_PRE_CONSUMPTION`。同段 `load.meter_boundary` 和 `grid.metering_boundary` 必须与该节点相符；先自用，再对剩余量执行原并网功率约束和显式商业外送上限。
- 地面只使用 `GRID_DELIVERABLE`，全额销售，不读取屋顶购电节省或负荷。3B 已扣的电气/变压器/送出/站用/可利用率/物理限发不再扣；C 阶段只施加另行声明的商业接收上限。
- 原 `project.sales_mode=full_export` 明确商业自用为零；负荷是 NOT_APPLICABLE，不是假定未知负荷为零。屋顶全售电必须显式 `NO_LOAD_FULL_EXPORT`，地面为 `NO_LOAD_GROUND`。
- 代表年重复只在 3B 与负荷的显式情景轴相容时执行；逐年轴需要 YEAR_SPECIFIC 输入。同一个代表年在多运营年复用不是未来实际天气、企业实测负荷或真实未来生效电价。

## 3. D2 控制与价格表

保留既有 `solar-pv-method-config/1.0.0` 结构和严格类型；无数值默认，不改旧配置/hash。不新增原始输入字典字段。

| 参数 | 作用 |
|---|---|
| `consumption.load_repetition` | 原代表年/逐年/地面无负荷模式，另有明确屋顶全售电不适用模式 |
| `consumption.commercial_export_limit_kw` | 显式商业外送功率上限，不能从缺失推定无限或零 |
| `settlement.price_source` | `PERIOD_TABLE` 或 `MARKET_SERIES`，显式选择，不混用两套外售价 |
| `settlement.revenue_method` | `OWNER_AVOIDED_COST/PPA_FIXED/PPA_DISCOUNT/EXPORT_ONLY`，收入权属视角互斥 |
| `settlement.currency/price_year/tax_basis/price_basis` | 可相加结算项的币种、基准价年、含税/未税、名义/实际口径；必须与原金额信封一致 |
| `settlement.fee_treatment` | `SEPARATE_LEDGER` 或合同净价已含费的 `ALREADY_IN_PRICE`，不重复扣费 |
| `settlement.negative_price_treatment` | 有原合同及负价规则时按带符号价格结算；不擅加经济弃光策略 |
| `settlement.ppa_discount_factor` | PPA（Power Purchase Agreement，购电协议）结算单价为同段可避免购电价乘显式合同/情景乘数；与原固定 PPA 单价互斥 |
| `settlement.other_benefit_months` | 将原其他收益 row_id 显式对应到月份；不得把仅年度金额自动平均分摊 |
| `prices.escalation_fraction` | 已有的共同合同单价增长情景；对本模型选中单位电价、PPA 价及单位交易费用使用同一显式乘数，来源中必须说明该共同情景，不当作真实未来政策 |

`tariff.periods` 的季节字符串使用 `ALL` 或 `MONTHS:1,2,...`；星期使用 `ALL` 或 `ISO_WEEKDAYS:1,2,...`，1 为星期一、7 为星期日。不把自由文本“节假日”等猜成实际日历。生效起止日期两端均包含，日内时段为半开区间，可用 `24:00` 作结束。

单一价是一条全天记录；分时价是完整、不重叠的多个日内/日期/月份/星期记录。跨午夜/月份按真实本地日历检查；同一计量区间中发生价档切换且无子时段电量证据时阻断，不擅自均匀分摊。跳时跳过不存在的 `02:00` 价格边界时，也检查真实 UTC 偏移转换及区间末端，不能整段沿用跳变前价格。

购电可避免价、固定/折扣购电协议价、外售结算价分别保存。地面不带“可避免购电价”等屋顶专属字段。只有原合同有权确认的边际能源费用可以作为自用节省，不把月账单均价、需量/容量/固定费用自动变成可避免费。

税含、价年、币种或名实口径混合/缺失时阻断；本轮不内置汇率、税率、税额剥离、补贴、销项/抵扣或税款付现。`vat_rate` 为原资料披露，不因此形成完整税模型。

## 4. 冻结公式、派生账簿和单位

九条原公式的完整变量、下标、集合、单位、适用条件及实际绑定见 `phase3c-formula-numerical-verification.json` 和结果 `formula_snapshot.consumption_definitions`，原定义/hash不变。

- 自用：`E_self,t = min(E_available,t,L_t)`。
- 上网：`E_export,t = min(max(E_available,t−E_self,t,0),X_t)`。
- 弃电：`E_curt,t = E_available,t−E_self,t−E_export,t`；残差保留符号，不能把负弃电截零掩盖过量分配。
- 交付：`E_delivered,y = Σ(E_self,t+E_export,t)`。
- 自用率：`S_y = ΣE_self,t/E_delivered,y`；上网占比在**同一交付分母**下为其互补分项。不是限发前发电占比。
- 负荷自给率：`A_y = ΣE_self,t/ΣL_t`。零分母 UNDEFINED，不以零或默认百分比替代。
- 自持收益与 PPA 投资方收益按原两条独立收入公式执行，不叠加投资方合同收入和用电方避免购电收益。原其他收益金额无非负 minimum，有来源的合同负额调整保持符号。

以上 `t` 为同节点计量/结算区间，`y` 为运营年，`Σ` 只汇总对应年明确完整时段集合；`E`、`L`、`X` 均为 kWh，比例无量纲。`X_t=P_limit×h_t`，其中 `P_limit` 是声明的有效外送 kW 上限，`h_t` 是真实经过小时。屋顶取原并网/可用容量与商业上限的共同约束；地面交付量已含原物理上限，只施加新商业上限。

派生结算桥：`V_self,t=E_self,t×p_self,t`，`V_sell,t=E_export,t×p_sell,t`，`C_fee,t=E_export,t×f_fee,t`。`p_self` 为明确自持可避免价或投资方 PPA 价，`p_sell` 为选中外售价，`f_fee` 为原单位交易费；单价/费用率均为项目币种/kWh，乘积为该币种金额。D2 折扣分支 `p_PPA,t=p_avoid,t×d_PPA`，其中 `d_PPA` 是 0—1 的显式合同乘数；不是另一项原始事实。

共同增长情景的 `g_y=(1+e)^(y−1)`，`e` 为原 D2 年增长分数，`g_y` 无量纲；只影响上述已选择的单位结算价/费，不改变光伏物理电量。没有证据不自动增长；本轮案例明确给 `e=0`。已经按年度报价的输入不应再无依据叠加增长。

`gross_benefit` 表示冻结收入公式的结算价合计（自用价值＋外售＋明确其他收益），不是承诺的到账现金、发票税基或完整项目利润。`benefit_after_transaction_cost = gross_benefit − transaction_cost` 只是电量费用桥；若已在合同净价中含费，另扣费用为零并披露 `embedded_transaction_cost`，不把信息性内含费重复扣一次。负价格允许收益为负；“发电下降、收益不增”的单调性校核只适用于非负边际价格，不能拿它覆盖带符号负价公式。

## 5. 唯一结果与费用交接

仍输出 `solar-pv-calculation-result/1.0.0`：

- 原 3B 发电指标保留；`source_snapshot.generation` 保留其结果/输入/来源及逐时证据身份。
- `consumption.year.<y>` 的 `details.ledger/monthly` 包含同边界可用、负荷、自用、上网、额外商业弃电、交付及守恒残差；`consumption.self_ratio.year.<y>` 同时披露上网占比；`consumption.load_coverage.year.<y>` 区分不适用与零分母。
- `revenue.year.<y>` 和 `revenue` 包含月/年/生命周期自用价值、外售收入、交易费用、其他收益及费用桥。`self_value_kind`/结算边界标明自持节省还是 PPA 合同收入，不能误当同一笔真实收款。
- `energy.delivered.year.<y>` 为 C 阶段实际消纳交付量；原 `energy.year.<y>` 是 3B 进入 C 的边界电量。后续 LCOE（Levelized Cost of Energy，平准化度电成本）消费者不能把两者无条件混为一个分母，成本也必须同边界。
- 每条时序证据含 3B 来源行、真实区间、负荷实例/来源、价格/政策行及各运营年分配、单价、费用和收入。来源字段集合有界为原 469 字段，不积累无限行 ID 集合。完整输入表与证据块须持久保留。
- 输入/来源/方法/公式和所有数值内容进入 canonical 结果 hash；运行 ID、生成时刻和私有产物位置仍按既有合同排除。API/CLI 需要同一候选下真实往返校验，不能只比较显示小数。

Phase 3D 可消费**明确的收入分项、已计交易费用、内含费用标记及实际交付电量**作为接口。租金/收益分成、投资、运维、折旧、税金、融资、应收应付、付现与现金流仍未计算。不能把自用节省再加一笔收款，不能既消费净电量收益桥又再扣同笔交易费。NPV（Net Present Value，净现值）、IRR（Internal Rate of Return，内部收益率）和 LCOE 等保持 NOT_IMPLEMENTED/null；本文不启动这些模块。

## 6. 有界执行、失败处理与独立门禁

继续既有 D3 显式预算与硬上限，小 JSON 默认 32 MiB 不变。输入/输出分块、逐次 checkpoint 和 Windows 实测进程工作集为应用合作式约束，**不是 OS（Operating System，操作系统）硬隔离**。结果数据 fsync 后采样，receipt 自身 bytes 计入磁盘；receipt 的时间/内存采样在其自身 fsync 前。完整读取/CLI 外层耗时另记录，不把不同测量窗口混成一个数。

新私有输出目录独占创建，`result.json` 最后发布；任何中途异常删除本次未完成目录，不删除原已存在用户目录。调用方应保持私有 ACL（Access Control List，访问控制列表），不把合作式目录校验当公开不可信服务的强沙箱。

所有案例仍是 SYNTHETIC。真实资源/政策/电价数据仍 Phase 4；真实项目、正式 DOCX（Office Open XML Word Document，Word 文档）、PDF（Portable Document Format，便携文档格式）、两个 XLSX（Office Open XML Spreadsheet，Excel 工作簿）、WorkBuddy 平台和发布门禁独立 BLOCKED。完成本轮验收及本地提交后停止，不自动进入 3D。
