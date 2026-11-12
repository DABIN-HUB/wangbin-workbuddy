# Phase C 候选现金来源审计与有限修复

范围：SOLAR-PV-AI-REPORT-ENGINE-2.0.0；两种既有合成类型；仅运维维护费压力，不变计算方法。结论：**交易费规则传递已修复并双案重算；候选终期现金与经济比较仍未闭合。**

## 精确调用链

| 层 | 真实输入/输出 | 审计结论 |
|---|---|---|
| 基准 | R2各案input.json、methods.json、3C result及交付canonical | 原身份、字节保留；不是以旧结果冒充候选 |
| 情景控制 | `OPERATING_MAINTENANCE`；`opex.items.base_amount`；实例`opex.items:maintenance:base_amount`；原atom hash及`SYNTHETIC-AI-V2-OPEX-STRESS`授权声明 | 原合成维护费用乘1.05；屋顶候选7560、地面15750；不是市场报价 |
| prepare | 独立prepared-export.json、输入hash、sources-ID；场景PESSIMISTIC、控制run_id=opex-stress | 原样保存，不二次prepare后套旧receipt |
| 3C | 财务专属变更复用经`_trusted_original_settlement`验证的原3C | 不伪造新3C身份；receipt明确reused_settlement_result_hash |
| 交易费来源 | `SYNTHETIC-ROOF-TRADING-FEE-PAYMENT-V1` / `SYNTHETIC-GROUND-TRADING-FEE-PAYMENT-V1` | 原来源存在，原runner未接收/传递该来源；这是接线缺口，不是支付数据原本不存在 |
| 3D | `rebind_opex_fee`保留已验证payment/source，重绑候选Phase2和实际使用的3C；随后生产者重新算台账 | 禁止改变币种、期间、非允许OPEX、资产、方法；保留原/派生bytes哈希与绑定 |
| 3E | `calculate_phase3e`消费本候选3D | 交易费cash不再null；generic入口未消费终期source，project_terminal_cash仍缺，NPV/IRR/回收继续BLOCKED |
| sealed receipt | `seal_scenario_run`验证实际3D/3E及候选prepared身份 | 两案回执真实存在，未伪造数值 |
| compare | 原`compare_scenarios`，未改白名单/税费/折现/IRR根集/重复消费门禁 | 两案均NO_VALID_MULTI_CANDIDATE_COMPARISON，ranking为空 |

支付来源路径：`reports/solar-pv/phase7l-r2-trading-fee-synthetic-source-v1/<type>/trading-fee-payment.json`。该来源明确25运营年、CNY、SEPARATE_LEDGER、预计当年支付比例1及期初无欠款；本轮沿用的是该合成预测规则，**不是本轮假定全部支付，更不是实际付款证明**。来源没有Phase2字段实例，适用位置为payment.annual等载体路径，不编造field_instance_id。

运行实物：`.runtime/solar-pv/ai-v2-cd-20261112/finance-fee/<type>/`；其中control、prepared-export、scenario-evidence、comparison以及opex-stress下3D/3E/receipt/fee-source-rebinding均保留。完整逐层hash与现金组成在`source-and-cash-audit.json`。

## 候选实际计算身份

| 身份 | 工商业屋顶 | 集中式地面 |
|---|---|---|
| model_version | solar-pv-engine/0.3.0 | solar-pv-engine/0.3.0 |
| 3E run_id | c3983c63-b193-4880-bba0-03940f68e6db | 736e1938-3ec9-496f-9922-2bf04403cf04 |
| input_hash | 270b125a3396c463be830f4d1f9de94ae87943b2840b70811576d6020b437430 | 2f6ea28e6ff7350dedaf950c794909b04355812402ce4e6a7a02d29e55db89fa |
| source_snapshot_id | 737fd6f97094996283ba4c448510a6773f29f0eff02df1608e8c4c98dfdc471f | 51a3e9b0b6a23062c1a059495e83b38a60e0b7002b15a0fe67dc071f46a480eb |
| result_hash | 2e79978860cad42df4da9a27e77c1f72f31a4a07c38c98be10f455d7d14170d9 | 0f48accbb5272dfb247f70386b0e19057f04b7ba7df81c17b533b45ccf5f08d4 |

控制run_id与3E计算run_id是不同对象，不能混称。基准与候选的四项运行/hash身份不同，model_version不应人为变更。

## 现金组成及重复计入检查

两案各25运营期均实际校验：交易费应付期初＋计提－支付＝期末；3E benefit由回款＋自用避免支出－独立交易费支付构成，不从已经扣费的净收益再次扣减；OPEX、资本支出、项目现金税及营运资金增加－释放分别与3D对应。各项由既有生产者计算，本轮没有新增现金流公式。

第25年两案台账均已有12000元营运资金释放，不能再次作为额外终期现金加入。未把折旧或账面残值作为处置收入。上述证明覆盖已存在的现金组成与传递，**不是完整项目现金流/终期现金闭合证明**。

## 终期来源与恢复结果

原`terminal.json`与其哈希绑定的`terminal.txt`确实存在：NO_DISPOSITION、2026-12-31评估日、2051-12-31终期、四类资产、LEDGER_ALREADY_RECOVERED。它们是有明确范围的合成“无额外处置”声明，不能直接复制基准终期金额。

最初完整运行因散装D3分块不在原目录而失败。进一步查得两案`archived-d3-and-intervals.zip`，已仅向新`recovered/<type>`恢复；每案71个bundle文件逐一匹配manifest SHA。**原始数据可恢复，缺失目录不是最终数据阻断。** 原审计JSON中“historical D3 files unavailable”仅表示恢复前观察，以本节和`archive-recovery.json`更正。

随后尝试候选D3/3C重放→候选3D→原sourced 3E。第一次被工具外层420秒限制中断，无正式退出回执；改为受控后台600秒进程上限后仍exit124，最后进度为进入run_scenario，未产生完整阶段result。终期绑定专项180秒exit124，无完整JUnit，不能从进度点猜计数。未重复执行全仓测试，也未再将相同高成本链扩展到地面。归档恢复后的地面完整经济重放仍NOT_EXECUTED。

未验收的终期接线及非BASE重算试验已从生产路径撤回，仅留在`recovery/terminal-experiment-not-accepted`供恢复诊断。`terminal_binding.py`与其原测试最终无净改动；所有公式/比较器均未改变。终期接线仍属于2.0未闭合原需求，不转入2.1。

## 验证、负向与审批边界

最终费规则/财务核/评价/runner四模块61 passed，exit0，157.15秒；独立既有交易费/终期source合同47 passed，exit0，112.83秒；去重108项。此前52及9为同组较早回执，不重复累计。完整终期试验的两次超时另计NOT_PASSED，不被108覆盖。

新22项覆盖两类支付规则保留，以及未授权、缺来源、不同期间、身份错误、重复/错误计费口径、货币/税基/折现/容量范围改变；既有核与评价覆盖IRR无根/多根及财务状态。双案实际bundle负检覆盖重复消费、错误receipt和结果篡改。完整有效候选经济比较的正向与完整负向矩阵尚未闭合，故SCENARIO_COMPARISON不得PASS。

会计利润、独立经营现金与股东回收继续按`phase-c-method-adjudication-required.md`待方法负责人及用户裁定。用户目标不得从已有计算结果反推。
