# Phase 5 工商业屋顶四文件开发检查点

## 状态

- 阶段：Phase 5 工商业屋顶光伏预可研四文件导出
- 当前状态：`PARTIAL`
- 样件状态：`DRAFT_PARTIAL`
- 四文件门禁：`BLOCKED`
- 决策状态：`not_decision_ready=true`
- 本检查点不代表 Phase 3E/3F/3G 或 Phase 4 正式通过，不代表正式四文件验收、准入或投资决策就绪。

## 基线与实现

- 工作树：`F:/ideaWorkSpace/wangbin-workbuddy`
- 分支：`main`
- 合并后 HEAD（开发开始前）：`12964c0f11b00e5da6bd3ec1b3e76bc421ba77f`
- 统一生产入口：`services/solar-pv-engine/src/wangbin_solar_pv/report_export.py`
- CLI 入口：`wangbin_solar_pv report --result ... --mapping ... --output ...`
- 来源工作簿：复用既有 `source_xlsx.create_source_workbook`，未重建第二套来源管理框架。
- 测算工作簿：`STATIC_SNAPSHOT`；未声明 `VERIFIED_RECALCULABLE`。
- PDF：仅探测真实 `soffice`/`libreoffice`；未找到转换器时不创建伪 PDF。

## 样件输入与统一身份

样件使用既有独立一年期工商业屋顶 `SYNTHETIC` canonical 结果，仅用于开发验证：

- 项目：`SYNTHETIC-industrial_rooftop`
- 场景：`BASE`
- `model_version`：`solar-pv-engine/0.3.0`
- `run_id`：`d86a4e81-e432-4199-b194-bbf93dd15b01`
- `input_hash`：`3074f404bba5f06af0b88a701ff3f91b9690758cdb86022cfd254646b1c4c6fa`
- `source_snapshot_id`：`88902c3b845bacc32759a5d4bc61f743e63b3a5c2862233520e3e0475e210f31`
- `result_hash`：`76ff9ad35e6a08cfad88d8e855a88eb2109c63026e07d225e0a5883eef1842b1`

四个文件（PDF 阻断时为已生成的三件样件）和来源工作簿均由该 canonical 结果驱动；报告层没有重新计算财务指标。`UNKNOWN`、`BLOCKED`、`NOT_IMPLEMENTED`、`NOT_TESTED` 按原状态展示。

## 实际样件

输出目录：`reports/solar-pv/phase5-synthetic-rooftop/`

| 文件 | 状态 | 字节数 | SHA-256 |
|---|---|---:|---|
| `SYNTHETIC-industrial_rooftop-光伏预可研报告.docx` | GENERATED | 46,474 | `1caa2674fdbad4e07f404709c7ea0d2e65f31a218c640c02dda41dd6eadc3dc1` |
| `SYNTHETIC-industrial_rooftop-光伏预可研报告.pdf` | BLOCKED | — | — |
| `SYNTHETIC-industrial_rooftop-测算模型.xlsx` | GENERATED, `STATIC_SNAPSHOT` | 56,318 | `824e88cdc0121f498bff3778246f951f30a9184ca23a3dd94887e7aa5b88798c` |
| `SYNTHETIC-industrial_rooftop-资料来源与假设清单.xlsx` | GENERATED, `DRAFT_PARTIAL` | 77,670 | `93b079a0956c73ca4d593976a954675872b0b5c8b9a8cb00870893e197ead5ae` |
| `manifest.json` | GENERATED | 4,042 | `7e753e759e7b60103d63b7166133ac3b6e64a6674c3701cca30f93b9aa367f79` |

来源 XLSX 的既有 Phase 4 样件此前为 77,673 字节；Phase 5 复用生成器后重新写入时，身份和输出文件保持同一 canonical 绑定，不能用旧哈希替代当前样件哈希。

## 结构检查

- DOCX：OOXML ZIP 可读，`docx_validate.py` 返回 `ok=true`；结构读取为 402 个正文段落、4 个表格，正文内容可编辑。
- DOCX 覆盖：18 章、100 个章节子项、13 个附录、26 个附录子项。
- 测算 XLSX：真实 OOXML，可由 `openpyxl` 读取，19 个冻结核心工作表全部存在。
- 来源 XLSX：真实 OOXML，可由 `openpyxl` 读取，10 个冻结物理工作表全部存在；`变量/术语词典` 映射为合法物理名 `变量-术语词典`。
- DOCX ZIP `testzip()` 返回 `None`，未发现 ZIP CRC 错误。
- 公开样件不包含受保护商业原始附件、凭据或密钥；`sensitive_raw_attachments_included=false`。

## PDF 阻断

当前环境未发现 `soffice` 或 `libreoffice`。因此 F02 回执为：

```json
{"status":"BLOCKED","reason":"PDF_RENDERER_UNAVAILABLE","renderer":null}
```

没有创建空 PDF、改后缀文件或伪造 PDF。F01/F03/F04 继续保留为开发样件；四文件整体不通过。

## 实际验证

- `python -m compileall -q services/solar-pv-engine/src/wangbin_solar_pv`：通过。
- 直接相关快速回归：`tests/solar-pv/test_phase4_data_adaptation.py tests/solar-pv/test_phase3g_project_runner.py`，`9 passed`，约 `33.74s`。
- CLI 单项目导出：成功，报告导出总耗时约 `1.986341s`；其中来源 XLSX 生成约 `1.039194s`。该耗时为本机开发样件实测，不等于完整项目计算耗时或用户 Skill 调用耗时。
- 完整 L2/L3、长时间财务求根回放、真实数据源访问、PDF 转换、电子表格实际重算、全页视觉复核、WorkBuddy 平台验收：`NOT_TESTED` 或 `BLOCKED`，未以历史结果替代本轮证据。

## 后续边界

1. 需要合法、可用的 DOCX→PDF 转换环境后，才能继续 F02 真实转换与 PDF 解析/视觉检查。
2. 需要真实来源、授权和上游阶段关闭后，才能评估正式真实性与四文件门禁。
3. 本轮停止在 Phase 5 可合法实施的报告生产代码和开发样件；不自动进入 Phase 6，不自动 push、部署、上传或发布。
