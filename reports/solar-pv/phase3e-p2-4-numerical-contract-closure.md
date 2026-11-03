# Phase 3E-P2-4 数值验收契约收口（只限定本轮）

**结论：PARTIAL。**独立草案已固化为 `docs/solar-pv/19-phase3e-p2-4-numerical-acceptance-draft.md`（`solar-pv-break-even-numerical-acceptance/draft-0.2`）；**尚不是已批准的数值通过规则，也没有当前提交的 L3 覆盖证书。**正式 `F-BREAK-EVEN-PRICE` 保留 `BLOCKED_MISSING_INPUT / BLOCKED_ROOT_SET_COMPLETENESS_UNPROVEN` 且 `value=null`；整个已归档结果为 `PARTIAL`。不改冻结公式、D2/D3、正式结果 Schema、两个封存项目和任何金融计算生产者。[`phase3e-p2-4-numerical-contract-evidence/evidence.json`; `phase3e-p2-4b-c-root-certification-evidence/formal-blocked-result.json`]

## A/B/C：工程数值事实与隔离

- **已批准：**D2 来源的连续闭区间、两端参与；负价必须满足已有来源及合法性门禁；`break_even.price_tolerance` 只表示价格隔离宽度，独立 SYNTHETIC 继续用 `0.000001 元/kWh`；全域和全分支可审计证明是完整根集认证的前提，不能认证时阻断；无根、多根、零平台与证明缺口分别如实诊断；有限小数近似与冻结的精确根集不同。
- **待单独批准：**`1 元` 仅用于这份 SYNTHETIC 案例的 NPV 残差候选、比较/舍入口径；真实项目须独立设定；怎样证明实算误差和全分支覆盖；如何将数学精确集合、区间代表价、无根及零平台映射到既有正式结构（若需变更冻结语义／Schema 则另案）。所有待批项目当前**不得**作为正式 PASS 判据或默认方法参数。
- **可复核的独立证据：**事前声明（SHA-256 `331fff8b0f2945eadfb493db111068fd13899f42294c0624c2f7415729234c66`）导出理想 `F(p)=-1330+(65700p+140160-180000+200)/(11/10)`，闭区间 `[0,2]` 理想斜率 `657000/11>0`、两端 `-411030/11` 与 `902970/11` 元、理想唯一根 `4567/7300` 元/kWh。归档十进制参考价和有理根差值 `|δ|<10^-100 元/kWh`，故**仅对理想式**的 NPV 偏差 `<(657000/11)×10^-100 元`。`1e-6` 宽度对应理想 NPV 最大变化 `657/11000 元`；`1 元` 理想残差反推价差 `11/657000 元/kWh` 大于隔离宽度，二者不能相互替代。真实全链在**一个点**记录 `0E-22 元`；执行链的统一误差界及全域实算根集**均未证明**。源哈希、100 位 Decimal 参考价、形式化差值上界见 `evidence.json`；没有重新运行昂贵回放。
- **正式/诊断隔离：**生产入口 `calculation/break_even_certification.py:16-85` 对独立项目固定封存非数值阻断记录；历史正式结果原文件 SHA-256 `1d7e29e53f755683b8f2bf84f2509362f4329aa21af716730f6f7a74fd5d18a4`，经读取与证据记录核对，根指标 `value=null`。独立回放价和 `0E-22` 只保存在单独诊断证据，**不复制为正式指标**；本轮未修改计算链，隔离沿用现有运行门禁并在契约中明确，不宣称新增全域证明。

## D：测试编排的真实校验

只改进既有 `tooling/solar_pv_regression.py` 的 `verify`：除三份 receipt 两两身份一致外，现在要求**逐份与调用时实际检出的 HEAD、受控代码/测试/配置字节哈希以及规范化执行条件一致**；不同直接 `BLOCKED: HISTORICAL_ONLY`（exit 2）。旧 `audit-archive` 仍只给 `HISTORICAL_ID_MATCH_ONLY`。对 JUnit 原始 SHA-256、测试选择、逐项参数化 node ID、skip/失败、运行日志及执行命令的原有检查不降低。[`docs/solar-pv/18-phase3e-regression-orchestration.md`; `tooling/solar_pv_regression.py:232-318`]

**本轮实际运行（代码改动未涉及财务生产者；无重型 E2E／独立 L2／最终 L3）：**

| 操作 | 实际退出/结果 | 原始证据 |
|---|---|---|
| `python -m tooling.solar_pv_regression run --tier fast --out <新建仓库外目录>` | exit 0；64 passed、0 skipped/failure/error，2.384s | `fast/{receipt.json,output.log,junit.xml}`；JUnit SHA-256 `304c7b058c6142c32816f86e4da0063746e8e3d1c7841137e0792146a3119fb9` |
| `python -m tooling.solar_pv_regression run --tier affected --select tests/solar-pv/test_calculation_contracts.py --out <新建仓库外目录>` | exit 0；35 passed、0 skipped/failure/error，23.547s | `contract/{receipt.json,output.log,junit.xml}`；JUnit SHA-256 `a3f3e7f7f5d5b64aa62303ed8a317403c87b8beb33d75cbee4036da782a9b8c9` |
| `python -m tooling.solar_pv_regression run --tier collect-l2 --out <新建仓库外目录>` | exit 0；60 ID，其中 24 个参数化 ID；**只收集** | `collection/{receipt.json,output.log}`；完整 ID 和执行命令均在 receipt |
| `python -m tooling.solar_pv_regression audit-archive --out <新建仓库外 JSON>` | exit 0；60/60 历史匹配，其中相关旧 L3 有 1 skip，`HISTORICAL_ID_MATCH_ONLY` | 旧 JUnit 及 SHA 校验；当前收集的 60 ID 也与旧 L3 逐 ID 比过，仍只属历史包含性 |
| `python -m tooling.solar_pv_regression verify --collection <旧 collection receipt> --solar <旧 fast receipt> --workbuddy <旧 affected receipt>` | **exit 2，按预期阻断**：`HISTORICAL_ONLY: receipt source/test/config/HEAD differs from current checkout`，未输出覆盖证书 | 本轮只读负向调用；历史 receipt 的受控输入哈希与当前哈希不同 |
| `python -m tooling.solar_pv_regression verify --collection <本轮 collection receipt> --solar <本轮 fast receipt> --workbuddy <本轮 contract receipt>` | **exit 2，按预期阻断**：`incorrect receipt tiers`，未把仅快速／契约测试错判为完整 L3 | 三份 receipt 的本轮身份一致，仍不能绕过 tier 和真实 JUnit 的范围检查 |

三份新运行的身份哈希均为 `90b4b66cb00d497d421d8444ce46cb6845e16e2080419e74983b3be926eb4e12`，运行前后相等，执行条件和合约 JUnit 文件 SHA 已实际读取核对。新结果的详细命令、退出码和原始小型 JUnit/日志均随 receipt 保存。它们属于本轮**提交前**快照；本地提交后 HEAD 变化时，必须在该最终 HEAD 上重收集/运行最终 L3 才能签发 L2-from-L3 证书，不能复用这批 receipt。没有借旧数据冒充新 L3，也不把旧 L2 的历史耗时说成本轮实际加速。[`phase3e-p2-4-numerical-contract-evidence/evidence.json`]

该门禁是对可信本地运行回执的字节、执行环境与工作树身份自校验，**不是**抗拥有回执／JUnit／日志全量写权限的攻击者的加密签名；若需防恶意重写，应另引入独立受信执行与签名见证，不以本轮自校验冒称安全证明。

## P2-4 状态及 P2-5 依赖

| 工作项 | 结论 | 明确边界 |
|---|---|---|
| P2-4A 全链候选重算；P2-4B 原价会话复用 | **已完成（沿用既有证据）** | 不在本轮重跑大包或修改生产算法。 |
| P2-4C 独立 SYNTHETIC 根见证、理想有理模型；本轮数值草案 | **PARTIAL** | 理想唯一根及有限精度单点有界事实可复核；实算模型全域根集与执行误差没有证书，1 元未获批准。 |
| 本轮分级编排与历史防冒认校验 | **已完成（局部门禁）** | 快速 64/64、契约 35/35、L2 收集 60；旧 60/60 仅 ID 包含；没有当前最终 L3。 |
| 正式 F-BREAK-EVEN-PRICE | **BLOCKED** | 原正式根值仍为 `null`；不能发 PASS、NO_ROOT 或近似价。 |
| 完整 Phase 3E 财务验收／两个封存项目 | **PARTIAL／封存** | 不以单一 SYNTHETIC 回放代替真实项目指标与全域证明。 |

**P2-5 依赖评估：**如果提议把 P2-5 限定为“已证的部分财务指标验收”，技术上可以先单独定义每个指标/项目的来源身份、通过/跳过/阻断清单、正式字段禁止近似根的规则及明确的 partial acceptance 口径；**须用户批准该阶段范围和门禁后才能启动**。若 P2-5 的接受准则要求正式完整盈亏平衡价格或全部 Phase 3E 指标，本轮的 BLOCKED 就是硬依赖，不能以理想模型或候选阈值绕开。当前未取得可将此评估解释为“已获准启动 P2-5”的具体批准；本轮停止，不进入 P2-5/Phase 3F。
