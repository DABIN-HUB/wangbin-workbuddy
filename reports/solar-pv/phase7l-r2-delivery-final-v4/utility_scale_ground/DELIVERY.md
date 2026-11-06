# Phase 7L-R2 C 批交付说明（合成案例，受控审阅）

本目录**唯一选定的最终报告版本**为 `phase7l-r2-v4` 下的 `industrial_rooftop/` 与 `utility_scale_ground/`。早期 `phase7l-r2-delivery/`、本轮独立保留的 `phase7l-r2-delivery-final/` 和 `phase7l-r2-delivery-final-v3/` 均非当前交付版本，不得混装或将其回执当作 v4 验收。每类的可下载 ZIP 仅包含自身报告、封存结果副本、完整输入及来源证明、逐件回执；ZIP 本身不是 PDF 或专业审批。

## 计算、生成与测试快照

- R2 A `e04e9634054dded1731a0a95230664e62de2219e` 和 B `009163810bd63ca9d4f845778abebe7e692a6ba5` 原样保留。两类 25 年合成输入及其 `result_hash` 来自 B 的现有封存计算。本轮只修改报告来源绑定与展示，**未重算**计算引擎，也未篡改封存 canonical。
- 限定生产修复提交 `4436576`（任务字段与 IRR）、`418cc96`（CH05/APP02 月度核验）及 `cbb610735413ab46fb1dad975ada21dc68537c24`（Word APP02 月度逐行表及内容版本）。使用最后一版生产代码，经真实 `tooling.solar_pv_phase7l_delivery` 普通入口在本独立目录重新导出。
- 最终源代码快照聚焦运行：`python -m pytest tests/solar-pv/test_phase7l_r2_source_binding.py tests/solar-pv/test_phase7l_r2_monthly_binding.py tests/solar-pv/test_phase7l_r2_irr_presentation.py tests/solar-pv/test_phase7l_r2_narrative.py tests/solar-pv/test_phase7l_r2_export.py tests/solar-pv/test_report_resource_monthly.py tests/solar-pv/test_report_business_semantics.py tests/solar-pv/test_phase7l_r2_inputs.py::test_r2_does_not_overwrite_preexisting_case tests/solar-pv/test_phase7l_r1_project_finance.py tests/solar-pv/test_phase3e_financial_metrics.py -q --disable-warnings`：**123 passed in 36.45s**（Python `.venv/Scripts/python.exe`；basetemp 位于 Hermes scratch；退出 0）。旧快照的 `62 passed`、`3 passed in 252.48s`、`19 passed` 单独保留，不与本轮相加；历史超时不算通过。此次未重复运行完整 L2/L3 或 25 年重新计算。
- 封存两类项目的 `verify_delivery` 只读重放均退出 0，计算状态均为 `PARTIAL`。屋顶 `result_hash=398474aff972dee9f0a34bf85380a348bb27f8d4b102d7337ca0478ae0d34fe4`，地面 `result_hash=cd4fca1268dea37283a65680512774053d8e3008cd268375e7dd9f7e9abb2b46`；逐项运行身份见各 `manifest.json`。

## 审计快照对照

| 审计项 | 较早只读审计快照 | 当前 v4 证明文件 | 对应聚焦验证 |
| --- | --- | --- | --- |
| 尚无 R2 报告 | 审计时确无报告，已过时 | 两类真实 DOCX、双 XLSX、`manifest.json`、`INDEPENDENT-READBACK.json` | 报告导出与实际文件回读 |
| CH13 无任务 | 当时源嵌套不匹配，已过时 | 两类 `CONTENT-READBACK.json`：各 5 项任务、5 处依赖说明 | `test_phase7l_r2_source_binding.py`、叙事测试 |
| 子字段来源身份 | 当时有效缺陷 | `report_claims.py` 按 row_id、flat atom 实例、来源登记、单位/状态/授权绑定；绑定失败不声明来源可靠 | 来源正反例 12 passed（纳入 123） |
| 月度资源错绑 | 当时有效缺陷 | 两类 `INDEPENDENT-READBACK.json`：DOCX APP02 与 XLSX M04 各 12 个月、逐变量 84 值、逐行来源与封存 Phase 2 原子对照；CH05 同一报告来源校验 | 月度对照/重排/缺月/错源/时区测试及跨消费路径测试 |
| 多根 IRR 被单根化 | 当时有效缺陷 | 单根项目的 `FINANCIAL-READBACK.json`；多根仅在隔离的报告表达测试中验证，未伪造正式案例 | `test_phase7l_r2_irr_presentation.py` 的多根、无根、未核验与舍入冲突用例 |

42 是报告**引用的公式定义/组数**，不表示 42 组都实际执行。`CONTENT-READBACK.json` 读回每类 42 个公式索引与 42 个包含边界、符号、当前状态的独立公式段。两个模型各 19 页签，来源清单各 10 页签。财务净现值和单根 IRR 从 DOCX 正文及财务 XLSX 与 canonical 对照，结果见 `FINANCIAL-READBACK.json`。

## 失败补丁的独立核实

`tooling/solar_pv_phase7l_r2_inputs.py` 的那次 `hunk 3 not found` **未成功修改文件**。从历史补丁调用恢复的原意是新增 `seal_delivery`：只给首封 R2 案例无损归档 D3 和区间文件，先校验 ZIP 条目及逐字节哈希，再删原重文件，写扩展清单/当前清单并只读重放。现有独立模块 `tooling/solar_pv_phase7l_r2_seal.py:18-95` 已实现同一功能；输入模块维持 B 版本，`prepare` 在 `tooling/solar_pv_phase7l_r2_inputs.py:245`、`verify_delivery` 在 `:444`。对 B 版本及当前文件的 diff 为空；本轮两类封存重放退出 0。因此归类为 **“目标行为已存在，失败补丁属于重复修改”**，不是该失败编辑成功。旧 `3 passed in 252.48s` 属于 B 周期独立运行的 R2 输入测试（其测试文件当时未纳入提交）；现有输入代码未变，但旧测试回执并非本轮最终代码快照证明。本轮只运行其不覆盖旧案例的轻量用例和封存重放。

## 文件与门禁

每类的 `manifest.json` 对实际 DOCX、测算 XLSX、来源 XLSX、清单及 canonical 保留文件大小、SHA-256 和运行身份；`INDEPENDENT-READBACK.json` 再从磁盘逐件重算哈希，并登记额外拷贝的 `input.json`、`methods.json`、来源文件、两层清单及计算回执的哈希。`* -text` 仅施加于本目录，避免签入后平台换行归一化破坏证据字节。

- **PDF**：本机未找到 `soffice/libreoffice` 等真实渲染器；F02=`BLOCKED`，未生成伪 PDF，四文件门禁不是 PASS。
- **目录页码/视觉**：DOCX 目录字段需要真实渲染刷新；页数、末页、NO_OVERFLOW 和逐页视觉审查均未知/未通过。静态 DOCX 检查不证明版式可读性。
- **专业与现实**：计算 `PARTIAL`，编辑/专业全篇审阅未签署；本案是假设性合成案例，不是现场勘察、第三方检测、真实审批或投资许可。WorkBuddy 平台未验证。没有推送、平台上传或发布。
- 历史材料曾包含凭据；本交付说明不复写任何凭据值；如须表示此类值，统一 `[REDACTED]`。

旧 `docs/solar-pv/00-protected-artifacts.json` 是 2026-10-28 采样的旧基线，并非 B 的快照：本轮重算其中 288 项，281 项仍与旧哈希一致，7 项与旧哈希不同（`README.md`、应收分析 Skill 的 SKILL/manifest、`products/catalog.json`、`reports/validate.json`、`reports/validate.md`、`reports/workbuddy-upload-list.md`）。对这 7 项相对于 R2 B 提交的 `git diff` 与工作区状态均为空；它们的旧基线不一致不得伪报“288/288 通过”，也不能归咎于本轮。本轮没有更改这些文件或原有两个未跟踪历史目录。
