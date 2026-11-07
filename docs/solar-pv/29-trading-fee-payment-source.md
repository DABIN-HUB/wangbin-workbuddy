# Phase 7L R2：合成交易费支付来源合同（v1）

状态：限定实现。只承载工商业屋顶／集中式地面 SYNTHETIC/ASSUMED 年度预测，不是实付、合同或第三方核验。冻结 469 字段、D2、D3 以及经济公式均不改。

## 决策与边界

- 来源是独立的严格 JSON 原始文件 `solar-pv-trading-fee-payment/1.0.0`，载体类型 `TRADING_FEE_PAYMENT_SOURCE`；须由调用者显式传入，不扫描目录、不从运维付现规则推断。
- 只接受 `SEPARATE_LEDGER`：3C 已计提交易费按当年本期费用为基数，同一运营年预计支付 100%；期初应付、建设期费用、历史欠费、预付、退款及其他冲销均须逐项显式声明为零；每个运营年度各有 `OPERATING_YEAR_N` 和数值比例 1。任何延期、部分支付、期初非零、净额内含费用或超范围用途均拒绝，不自动清偿。
- JSON 本身即原始合成假设材料；从 workspace 读取其原始字节并独立计算 SHA-256，文件内部不写自身哈希。严格验证字段、数值、项目稳定 ID、项目类型、币种、场景、评价期、Phase 2 输入和来源快照、D2 方法、D3 内容、3C 结果哈希及 3C 结算费用口径；来源字节哈希与已校验合同进入 3D 的 `source_snapshot`／`input_identity_payload`，由此改变 3D、3E、canonical 及报告身份。Phase 2、D3 和 3C 的历史身份保持不变。
- 3D 单列计提、预计付款、期初及期末应付和来源引用，按 `期末 = 期初 + 本期计提 - 本期预计支付` 逐期核对；3E 只扣一次该预计付款，原所得税税基不因现金付款再次扣减。原始字节 SHA-256 不能证明实际付款或合同真实性。
- 原有无单列交易费路径保持兼容；有正交易费但未提供独立来源时，费用计提和税基可计算，付款及应付未知，3E 项目现金流与回报阻断，绝不继承 `cash.opex_payment_fractions` 或默认零／全额付款。

## 接口和验证

- `calculate_financial_ledger(..., trading_fee_source_bytes=None)` 在已验真的 3C 之后解析并绑定原始字节；`run_project(..., trading_fee_source_bytes=None)` 和普通 CLI `project --trading-fee-payment-source`、`project-report` wrapper 显式透传。
- 来源字段由 `calculation/schema/trading-fee-payment.schema.json` 定义，未知键、重复键、未知版本、非法数值、来源与项目／3C／费用类型或期间不符均拒绝；只允许当前单一合成规则。
- 历史 v6 的正费用没有进入现金支出；原诊断 v7 使用了未获来源证明的运维付现比例，数值只能作历史条件情景，不再是当前有效财务结论。任何新报告只从新 canonical 导出，独立保留旧产物。
- DOCX 原图、中国字形、PDF／目录页码、全篇专业审阅与平台审核分别验收；财务源可闭合不代表其余门禁通过。
