# Phase 7L-R2 C 批最终报告：合成案例 v5（待专业审阅）

**唯一当前交付版本**是本目录 `industrial_rooftop` 与 `utility_scale_ground`，写作版本 `phase7l-r2-v5`。旧的 R2 报告目录，以及曾归档的 `phase7l-r2-delivery-final-v4` 均保留为历史/中间快照，不再作为当前报告。`*-R2-C-v5-final.zip` 是分别供审阅上传的完整包；内有真实 DOCX、测算和来源两份 XLSX、canonical、manifest、输入/来源材料及逐项回读证据。

## 版本与执行

- 原始 R2 A/B 提交 `e04e9634054dded1731a0a95230664e62de2219e`、`009163810bd63ca9d4f845778abebe7e692a6ba5` 不变。本次后续仅报告层生产修复：`4436576`、`418cc96`、`cbb6107`、`76276146f78e3c1b4b52a733821245706555e34a`（最终 v5 代码）。没有更改计算引擎、输入、冻结公式、469 字段或封存 canonical；**未重算** 25 年项目。
- 使用当前代码和原合法封存 canonical，分别通过 `python -m tooling.solar_pv_phase7l_delivery <sealed-case> <new-output-root> <category>` 在新目录生成两类报告。B 版项目的 `verify_delivery` 对两类封存项目只读重放退出 0；两类计算整体状态均为 `PARTIAL`，非实际项目批准。
- 最终代码快照聚焦命令 `python -m pytest tests/solar-pv/test_phase7l_r2_source_binding.py tests/solar-pv/test_phase7l_r2_monthly_binding.py tests/solar-pv/test_phase7l_r2_irr_presentation.py tests/solar-pv/test_phase7l_r2_narrative.py tests/solar-pv/test_phase7l_r2_export.py tests/solar-pv/test_report_resource_monthly.py tests/solar-pv/test_report_business_semantics.py tests/solar-pv/test_phase7l_r2_inputs.py::test_r2_does_not_overwrite_preexisting_case tests/solar-pv/test_phase7l_r1_project_finance.py tests/solar-pv/test_phase3e_financial_metrics.py -q --disable-warnings`：Python `.venv/Scripts/python.exe`，Hermes scratch basetemp，**125 passed in 36.42s，exit 0**。此前 62/3/19 passed 属旧快照；`3 passed in 252.48s` 是 B 周期 R2 输入回执，并非修改后的全部测试。本轮未重复 L2/L3 或长时间项目重算，历史超时不计成功。

## 审计问题对照与文件读回

| 较早审计 | 当前 v5 证据 | 局限 |
| --- | --- | --- |
| “尚无 R2 报告” | 两个实际 DOCX、两套双 XLSX、manifest 和两套 ZIP，`INDEPENDENT-READBACK.json` | 旧快照结论已过时，PDF 仍阻断 |
| “CH13 没有任务” | 两类 `CONTENT-READBACK.json` 均从实际 DOCX 读回 5 项本项目任务与 5 处依赖 | 旧快照结论已过时，非真实施工批准 |
| `schedule.tasks` 子字段引用错源 | `report_claims.py` 按 row_id、field_instance_id、flat atom、来源定位、授权、状态和值验证子字段与前置任务；来源测试包含跨任务/跨项目/相同值错源/重排 | 整体封存真实性由原 Phase 2/D3/项目只读门禁支持，单条报告校验不替代其自身证据 |
| M04/CH05/APP02 月度错绑 | 从两类 DOCX APP02 和 XLSX M04 分别读回每类 12 个月 × 7 变量 = 84 个源绑定值，逐个与封存 Phase 2 原子、单位、时区、月份、数据集和来源 ID 核对；元数据同值异项目来源与错误单位负例均拒绝 | 月度输入是合成已登记汇总，不是实测 8760 小时事实 |
| 多根 IRR 被正文单根化 | 隔离小案例 `[-100,230,-132]`、15% 折现率与无根/未核验/舍入碰撞均在报告表达测试中；两类正式单根结果从 DOCX、财务表与 canonical 读回见 `FINANCIAL-READBACK.json` | 两类封存案例本身均是单根，多根仅为隔离测试，未伪造项目结果 |

DOCX 均读回 **18 章/100 子项/13 附录/26 附录子项**、CH13 五项任务及来源，以及 **42 个被引用公式段**的符号/边界/当前执行状态；42 是被引用定义数，**不等于全部实际执行**。测算 XLSX 各 19 工作表、资料 XLSX 各 10 工作表。原结果哈希分别为屋顶 `398474aff972dee9f0a34bf85380a348bb27f8d4b102d7337ca0478ae0d34fe4`、地面 `cd4fca1268dea37283a65680512774053d8e3008cd268375e7dd9f7e9abb2b46`。各 `manifest.json`、`INDEPENDENT-READBACK.json` 和 `PACKAGE-MANIFEST-final.json` 提供实际大小、SHA-256 与项目/run/input/source 身份；包内原始 `input.json`、`methods.json`、`source-material.md`、计算/封存回执逐件哈希。

## 失败补丁核实

已恢复失败 hunk 原意：给 `tooling/solar_pv_phase7l_r2_inputs.py` 加 `seal_delivery`，仅对首次封存的 R2 输入把 D3 和区间文件无损 ZIP 归档，先逐字节校验再删原重文件，写扩展/现有清单并只读复核。那次 `hunk 3 not found` **确实未修改文件**。B 版输入模块 `prepare:245`、`verify_delivery:444` 与现文件 diff 为空；相同封存能力已在独立 `tooling/solar_pv_phase7l_r2_seal.py:18-95` 实现。两类已有封存项目的只读重放 exit 0。因此归类：**目标行为已存在，失败补丁属于重复修改**；不把失败编辑说成成功。旧的 `3 passed in 252.48s` 是此期间独立输入测试回执，不能证明最终展示修复。

## 未通过门禁及保护

F02 PDF 为 `BLOCKED/PDF_RENDERER_UNAVAILABLE`：本机无 `soffice/libreoffice`，未构造伪 PDF；`FOUR_FILE_GATE=BLOCKED`。未刷新真实目录页码，未取得实际页数或逐页渲染，`NO_OVERFLOW`/`VISUAL_REVIEW` 不通过。全篇专业内容、现场勘查、权属、签章、真实审批、WorkBuddy 平台安装与审核均未验证；静态结构/主张绑定 PASS **不是专业验收**。XLSX 为 `STATIC_SNAPSHOT`，没有声称 Excel 引擎重算。没有 push/上传/发布。

旧 `docs/solar-pv/00-protected-artifacts.json` 是 2026-10-28 基线，不是 B 版快照：对其 288 项重算，281 项与旧 SHA 一致，7 项与旧基线不同（`README.md`、应收分析 Skill 的两个文件、`products/catalog.json`、`reports/validate.json`、`reports/validate.md`、`reports/workbuddy-upload-list.md`）。这 7 项相对 B 的 Git diff 和当前工作区均为空，不属于本轮改动；不伪报旧基线全数通过。历史未跟踪目录与旧报告保留。历史材料中存在凭据的事实可记录，任何具体值均应写作 `[REDACTED]`，本说明不传播其值。
