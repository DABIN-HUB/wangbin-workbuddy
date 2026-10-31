# Phase 3E-P2 来源链预检与暂停门禁（仅 SYNTHETIC）

## 裁决

**PARTIAL / BLOCKED_MISSING_INPUT。** 本轮真实运行证明：独立合成屋顶案例的单个分时售电价原子可经 Phase 2 重新导出校验，完整 D3 资源／负荷数据可绑定候选导出重新封包，原 3B 物理发电结果不变并供新 3C 收益计算使用。**这不证明正式项目现金流、3D→3E NPV、根的完整性或 P2-1 至 P2-5 完成。** 受影响的盈亏平衡正式求值暂停；没有引入替代现金流承载方式、结果 Schema 或伪造终期现金。

- 原工作区：`main` / `14c87699e0bcd18cb60084e499ca072469d640be`；原有六处用户修改不属于本任务。
- 隔离预检：`python C:/Users/wangbin/AppData/Local/hermes/cache/scratch/phase3e_p2_preflight.py`，退出码 0，约 825 秒。实际终端 `TMPDIR` 意外指向系统 Temp；程序以唯一目录 `phase3e-p2-gate-0c726945-2561-44d2-bb04-7098b39ad3ed` 隔离临时原始和派生 D3、3B 与 3C 输出。结果读回后按确切路径、成员清单和非链接条件安全清理，复核目录不存在。只保存本报告的最小哈希／结果摘要；原始未发布块未留在系统 Temp。所有价格和时序均由既有测试支持模块生成，明确为 **SYNTHETIC**，不是封存项目、真实市场数据或正式回归。
- 候选价格：屋顶 `tariff.periods` 第一条的 `sale_price` 从合成 `0.4` 调整为合成 `0.6` 元/kWh；此处用原子实例 ID 而不是最终受控选择器。该预检是可行性演练，**没有实现或认证 P1 所要求的独立选择器、完整来源审核与求根**。
- 运行后重新读取 `generation`、原始 3C 和候选 3C 的结果 JSON，均可读取，根状态为 `PARTIAL`；这些状态不得升级为项目 PASS。

| 身份／结果 | 实际输出 |
|---|---|
| 原 3B result_hash（两次 3C 均固定引用） | `e142a2098063cc8993a2b17f756336eb15bec45dbec5df7872c19955a0acbdad` |
| 原 Phase 2 input_hash | `b233a66d44d2f326306c2afba830c07fbf5879e3724c9aaba379a2b36e6b0975` |
| 候选 Phase 2 input_hash | `3f9ef59ff08630fa7bb39d863365aa06ffd989cd9174c3f091015f34383b6e1c` |
| 原 D3 content_hash | `475c1f3df66eaf3cb09a10898c87f26e49fc34b053bf5c986a253c10a482ffa7` |
| 候选 D3 content_hash | `ee2024c623a87d2c1e458c81f0ee2f0cafbe924f4e1e00ffa1bde566e951de3e` |
| 两包资源数据集相同 canonical_array_hash | `2f0034a9ec349672305315601d663cb4fcb759c827ddc1a9a6e1edc1cd25259e` |
| 原 3C result_hash | `b1d9dd2a6990bddb73881fd4c2dd1898998065a215dc2700e95b7b35114d9d92` |
| 候选 3C result_hash | `f9b71578926ed93d6a76b257352c82ad04f07529bd7d0ee66ada3e296e49e6da` |
| 原／候选首年外售收入（合成 CNY） | `35040.0` / `52560.0` |

独立 Decimal 差额检查：`52560.0 − 35040.0 = 17520.0`，与 `87600 × (0.6 − 0.4) = 17520.0` 相等。此项只是合成样本的收益差额算术校核，**不是**全链 NPV 的独立数值参考。

## 缺失来源与最小差异

1. P1 草案要求 `basis` 严格等于已有可验证的 `finance.cash_flow_basis` 来源；该 ID 在冻结公式内作为计算期操作数出现，但不在 469 个 Phase 2 输入字段或 D2 参数中。两份封存案例不能仅凭执行控制自报值获得一条经验证的现金流口径来源。不能编造枚举、默认口径或把控制元数据当做财务事实。
2. `phase3e.py:134-149` 将缺少独立终期处置现金来源的 `finance.project_terminal_cash` 设为 `None`，逐级阻断项目现金流和 F-NPV。账面残值不是现金，3D 账簿没有项目终期处置现金事件。既有项目维持 `BLOCKED_MISSING_INPUT`；不增现金事件业务字段或任意现金流注入接口。
3. 仓库内地面项目只有 manifest、结果等缩略材料，**但独立持久证据目录中的原始 SYNTHETIC 数据块存在且可读取**：本轮调用现有 `read_bundle` 后再完整遍历数据集，实际校验 `C:/Users/wangbin/AppData/Local/hermes/attachments/solar-pv-phase3c-evidence-20261030/cases/lifecycle-utility_scale_ground/settlement` 的 `tariff.market_series` 共 8760 行、规范内容 SHA-256 `ff9c21d4584cb59b741d875954d1d757f23a9cfff6ca336f284809c8eaadb19b`；同目录屋顶 `load.series` 8760 行、规范内容 SHA-256 `39f6196d4f5a495a7ad8922613a78200947fea69f90d8b50d1ca59552abe969f`。另完整读取 3B 持久目录 `C:/Users/wangbin/AppData/Local/hermes/attachments/solar-pv-phase3b-evidence-20261029/lifecycle-25-{industrial_rooftop,utility_scale_ground}/resource`，两包各 8760 行，资源数据集规范 SHA-256 均为 `2f0034a9ec349672305315601d663cb4fcb759c827ddc1a9a6e1edc1cd25259e`。上述 `canonical_array_hash(bundle.rows(fid))` 均与各自 manifest 相等。**这证明原始块实际可读，不是仅有 manifest；仍没有建立这两套封存案例的派生 D3→3C→3D→3E 完整候选链，也不把合成价格冒充真实市场价。**
4. `financial_metrics.py:381-412` 的旧样本插值没有 3C/3D 调用与全根证明，只能作为内部诊断。原 `phase3e` 项目编排仍阻断正式结果；本轮不改它，也不将旧插值的 `CALCULATED` 用作正式 F-BREAK-EVEN-PRICE。

最小待批准／补齐内容：在已有冻结边界内，提供合法且可验证的完整终期现金来源以及指定现金流基准的来源绑定；若必须新增业务现金事件承载或改变 D2/D3/冻结 Schema，应另行审批。**本报告没有提出未经批准的新契约。** P2-1 至 P2-5 无一完成、无阶段 commit；不进行全链求根、不宣称价格残差、货币 NPV 残差或根集合完整性。

## 其他实证及保护状态

- 对原封存屋顶 Phase 3D 结果使用项目 Decimal-preserving JSON loader 调用当前 `calculate_phase3e`，实际 `F-BREAK-EVEN-PRICE` 的 `metric.unit` 等于 Catalog 的 `集合（元素元/kWh）`，状态 `BLOCKED_MISSING_INPUT`。故不修改单位逻辑。
- 本轮 288 个保护文件校验：286 项匹配历史基线、`reports/validate.json` 和 `reports/validate.md` 为历史已有差异、0 项缺失；四个历史单列用户保护文件 SHA-256 匹配。六个用户差异文件未暂存／恢复／覆盖。光伏与 WorkBuddy/Expert 完整回归、完整 NPV 独立 Decimal 校核、P2 阶段关联测试及 P2 阶段提交**均未执行**；前轮计数不得冒充本轮结果。
- 本轮未修改 D2 Schema、D3 协议、469 字段、89 公式、281 绑定、封存项目、正式结果 Schema 或生产代码；未 push、发布、部署、进入 3F/3G。
