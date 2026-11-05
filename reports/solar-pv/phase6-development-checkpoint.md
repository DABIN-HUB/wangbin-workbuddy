# Phase 6 集中式地面光伏四文件开发检查点

## 状态与边界

- 阶段：Phase 6 集中式地面光伏独立报告开发
- 当前状态：`PARTIAL`
- 样件状态：`DRAFT_PARTIAL`
- 四文件门禁：`BLOCKED`
- 决策状态：`not_decision_ready=true`
- 本检查点不代表 Phase 5、Phase 3E/3F/3G 或 Phase 4 正式通过，不代表正式准入、验收或投资决策就绪。
- 未修改或解锁封存的 25 年项目；本样件使用独立一年期 `SYNTHETIC` 集中式地面 canonical 结果。

## 生产入口与实现

- 工作树：`F:/ideaWorkSpace/wangbin-workbuddy`
- 分支：`main`
- 地面报告入口：`services/solar-pv-engine/src/wangbin_solar_pv/report_export.py:export_ground_report`
- CLI：`python -m wangbin_solar_pv.cli --workspace <workspace> ground-report --result <canonical.json> --output <new-dir>`
- 公共来源工作簿：复用 `source_xlsx.create_source_workbook`，没有新建第二套来源管理框架。
- 测算工作簿：复用 19 个核心工作表，模式为 `STATIC_SNAPSHOT`，没有声明 `VERIFIED_RECALCULABLE`。
- PDF：仅使用已存在的 `soffice`/`libreoffice`；本机两者均未发现，回执为 `PDF_RENDERER_UNAVAILABLE`，没有创建假 PDF。

## 地面专属内容隔离

地面 profile 绑定 `pv_type=utility_scale_ground`，并在报告和工作簿中保留以下独立边界：

- 土地权属、用地性质、用地面积及合规期限；
- 地形、坡度、地质勘察、地基/桩基；
- 地面支架、场区道路、排水、施工运输；
- 集电线路、升压站、送出工程、接入系统意见和调度约束；
- 集中并网、限发、市场化售电和交易结算依据；
- 地面电站 CAPEX/OPEX 边界。

缺少上述直接字段、来源授权、合同或专业审查时，章节保持 `UNKNOWN`、`PENDING_VERIFICATION` 或 `NOT_APPLICABLE`，不生成土地、地质、并网或市场价格结论。M08 明确标记集中式地面项目不采用工商业屋顶自用节省模型，不把 `consumption=0` 解释为屋顶负荷证据。报告的章节状态改为按子项专属证据映射，不再由无关年度发电量或 CAPEX 总额推断气象、现金流、设备、并网或政策证据。

## 样件身份

- 项目：`SYNTHETIC-utility_scale_ground`
- 场景：`BASE`
- `model_version`：`solar-pv-engine/0.3.0`
- `run_id`：`72bd0d6e-e466-46ab-87de-7c3fbc2017a9`
- `input_hash`：`9ddebec31b4d918c8c94b27c3051866a0a2574bb19d88f96cc19d1b3bf2464bf`
- `source_snapshot_id`：`2fd7fd549a7a47b9428811bd54859d4313e1d0a6e5aba8bd0eef86621286c35c`
- `result_hash`：`269c29a114a0d85f6914b96d383dab46fd1a0c8620014da6f7d915440ab86488`

## 地面实际样件

输出目录：`reports/solar-pv/phase6-synthetic-ground/`

| 文件 | 状态 | 字节数 | SHA-256 |
|---|---|---:|---|
| `SYNTHETIC-utility_scale_ground-光伏预可研报告.docx` | GENERATED | 49,024 | `1b577617dc0753d5c95ebe76c54b7ad00165865b59ab466982189b2031bbae65` |
| `SYNTHETIC-utility_scale_ground-光伏预可研报告.pdf` | BLOCKED (`PDF_RENDERER_UNAVAILABLE`) | — | — |
| `SYNTHETIC-utility_scale_ground-测算模型.xlsx` | GENERATED, `STATIC_SNAPSHOT` | 58,355 | `4cff69ad8449324e61f6612ca0a4d6c799d860323d5c73bfaee90f328acfcb08` |
| `SYNTHETIC-utility_scale_ground-资料来源与假设清单.xlsx` | GENERATED, `DRAFT_PARTIAL` | 由 manifest 登记 | `2bd113c2dc1e937119b7450be989e2f15405bec63afeb44fefb4d9f5a43f4e19` |
| `manifest.json` | GENERATED | 4,058 | 见目录内 manifest `manifest` 字段 |

F01/F03/F04 均绑定上方同一组五项身份；F04 含 10 个来源工作表；F03 含 19 个测算工作表。PDF 缺失，所以四文件门禁保持 `BLOCKED`。

## Phase 5 最小修正同步验证

同时重新生成了 `reports/solar-pv/phase5-synthetic-rooftop-v2/` 屋顶样件。修正包括：

1. 章节子项按项目类型、章节标题和直接 metric/input field 映射状态；气象章节不再从年度发电量推断资源分量，投资现金流不再从 CAPEX 总额推断闭合，财务阻断指标不写成有效值。
2. DOCX 增加项目类型专属 canonical 输入表、直接指标表和针对性缺口提示；地面章节不复制屋顶自用收益/屋顶结构结论。
3. 19-sheet 测算 XLSX 保留 `canonical_raw` 追溯列；合法标量写入 Excel 数值单元格并设置数字格式，状态/ID/哈希/UNKNOWN 等保留文本；M08 对地面项目标记 `NOT_APPLICABLE`。

屋顶样件身份仍为原独立 `SYNTHETIC-industrial_rooftop` 运行；其目录 manifest 登记完整路径、长度和哈希。

## 结构与快速验证

- `python -m compileall -q services/solar-pv-engine/src/wangbin_solar_pv`：通过。
- `python -m wangbin_solar_pv.cli ... ground-report ...`：实际返回 `exit_code=0`，输出 `PHASE6_UTILITY_SCALE_GROUND_REPORT_EXPORT`，`DRAFT_PARTIAL`，F01/F03/F04 GENERATED，F02 BLOCKED。
- DOCX：`python-docx` 可读，18 章、100 子项、13 附录、26 附录子项，正文可编辑；地面标题和地面工程缺口存在，未从屋顶结果复制自用收益。
- 测算 XLSX：`openpyxl` 可读，19 个工作表；抽查得到真实 numeric cells（如容量和比例），并保留 `canonical_raw` 精度追溯文本列。
- 来源 XLSX：`openpyxl` 可读，10 个工作表，复用 Phase 4 生成器。
- PDF 转换、PDF 中文检索/页数/视觉复核、Excel 实际重算、完整 L2/L3、真实来源接入、WorkBuddy 平台验收：`NOT_TESTED` 或 `BLOCKED`，未用历史结果替代本轮证据。

## 后续停止点

完成本阶段可合法实施的地面生产代码和开发样件后停止，不自动进入 Phase 7；待合法 PDF 环境、真实土地/地勘/接入/交易资料和上游计算门禁具备后，再集中进行正式验收。