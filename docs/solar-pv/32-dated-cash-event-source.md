# Phase 3E 日期现金事件来源合同（开发候选）

适用范围：仅 `SYNTHETIC`、已经通过终期来源和 3D 账簿绑定的项目基准场景。本文实现 `05-formula-registry.md` 中既有 `F-DATED-NPV`，不修改公式、冻结字段及状态枚举；年末 `F-NPV` 与日期 `F-DATED-NPV` 是两个独立结果。本文不是客户现金事件来源、四件套验收或发布许可。

## 原件与版本化载体

调用方**独立提供** UTF-8 原始 CSV 字节（最大 1 MiB、最多 10000 条事件）与 JSON carrier；计算器不从年末向量、应付账款或交易费计提生成日期。CSV 首行严格为：

```csv
kind,event_id,date,period,amount,source_id
RATE,,,DATED_DISCOUNT_RATE,0.1,SYNTHETIC-dated-rate
EVENT,base-1,2024-12-31,CONSTRUCTION,-100,SYNTHETIC-dated-events
EVENT,year-1,2025-06-30,OPERATING_YEAR_1,30,SYNTHETIC-dated-events
EVENT,year-2,2026-12-31,OPERATING_YEAR_2,90,SYNTHETIC-dated-events
```

上例只是独立合成金额和日期，不是任何项目的现金流或折现率。必须恰有一行 `RATE`，金额为该案例明确的日期折现率；其他行均为 `EVENT`。`amount` 为带符号十进制数；`event_id` 不重复，日期为 ISO 8601 日历日。载体的 `schema_version` 固定为 `solar-pv-dated-cash-events/1.0.0`，其完整机器 Schema 可由 `dated_cash_event_schema()` 获取。

载体必含：

- `source_content_sha256`：针对**CSV 原始字节**的 SHA-256，而非规范化表格的摘要。`event_source` 与 `rate_source` 各自包含同一摘要、独立 `source_id`、`source_reference`、`source_location`、`source_kind`、`status`、`license_status`、`reviewer`；未获授权、未审核、虚称已核实的合成来源拒绝。事件逐行与 CSV 的 ID、日期、期、金额、来源核对。折现率从已哈希原始表中的 `RATE` 行提取并与载体数值核对。
- `binding`：`project_id`、`pv_type`、`scenario_id`、`currency`、`cashflow_basis`（`pre_tax` 或 `post_tax`）、`price_basis`（`nominal` 或 `real`）、`evaluation_date`、`terminal_date`、`phase2_input_hash`、`method_config_hash`、`phase3d_result_hash`、`selected_cash_flow_hash`（对本次终期调节后的、同一税基逐期金额向量作 `digest()`）。变化后须重取原件和载体，不接受跨项目、跨场景、跨口径或旧账簿重放。
- `rate_source.rate_scope`：`PROJECT_<PRE_TAX|POST_TAX>_<NOMINAL|REAL>_<CURRENCY>_DATED`，必须与绑定项目的税基、价格基准和币种一致，不能默默复用 `_YEAR_END` 利率证据。`discount_rate` 须大于 -1，且与 `RATE` 原始行相等。
- `events`：与 CSV 的 `EVENT` 行一一对应。每一年度 `CONSTRUCTION`、`OPERATING_YEAR_1...N` 都有事件并与选定的 3E 项目税前/税后现金流逐期**精确**核对；`CONSTRUCTION` 必须发生于评价基日，至少一条事件发生在已绑定终期日，运营事件须落在并网年度起算的相应日历年且不晚于终期。基日前真实付款不能被伪造为基日事件：本版口径不支持其负年分数，应保持阻断并另行裁定。金额不符、空白期、同名 ID、错日期/错摘要拒绝，不以年末金额伪造事件。

日计数由已声明、可用且获授权的 D2 `time.day_count` 来源给出；支持 `ACT_365F`、`ACT_ACT` 与 `30E_360`，基日到事件日期计算高精度年分数。不提供该参数时原项目日期 NPV 继续阻断。日期结果仍保留 `SYNTHETIC`、`PARTIAL` 和实际未完成的其他指标。

## 接口与门禁

Python：`validate_dated_cash_events(carrier, source_bytes, *, exported, methods, financial, scenario_id, cashflow_basis, selected_cash_flow, terminal_date)`；成功返回原件摘要、载体摘要、事件日期/金额/年分数及折现率。`calculate_sourced_project_npv(..., dated_event_carrier=carrier, dated_source_bytes=source_bytes)` 校验后调用**原有** `evaluate("F-DATED-NPV", ...)`；缺一边必须报错。普通 `project` CLI 加 `--dated-event-carrier` 和 `--dated-source-csv`，仅与已验证终期来源成对使用；多场景日期载体在当前范围内拒绝而非跨场景复用。

验收示例的 `-100 / 30 / 90`、`2024-12-31 / 2025-06-30 / 2026-12-31` 与 `0.1` 全是 `SYNTHETIC/ASSUMED`。`test_phase3e_dated_cash_events.py` 对独立 CSV 做 Decimal 复算，并覆盖缺终期、重复 ID、错摘要、错现金流口径、未审来源、缺日计数和上游账簿变化。源文件/载体还需按项目单独生成并完成全链复算；单元验收不等于真实项目或平台验收。
