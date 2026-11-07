# Phase 7L-R2 用户审阅整改：报告内容 v6

当前供用户审阅的报告内容版本为 `phase7l-r2-v6`，由原封存的 R2 两案 canonical 经正常交付入口重新导出。v5 与所有历史报告均保留原样；v6 不表示新的业务阶段或新的计算结果。两类计算状态仍为 `PARTIAL`，真实项目资料未核验；本报告是合成测试材料，不构成真实审批、投资依据或专业签章。

## 直接修复及读回

- APP02 将 12 个月的辐照与气象拆成两张可读表，列内只用本项目、本月的短索引；索引须与变量列配对，在测算 XLSX 的 M04 查逐字段原值、单位、row_id、field_instance_id 和来源。公共数据集、版本、时区及完整来源路径/哈希仅在说明中列一次。月度发电量没有放入资源字段。两案各 84 个来源原子分别从实际 DOCX 与 M04 读回对照；未知/重复/错源不能生成有效索引。实际页面是否因此消除跨页仍需渲染核验。
- CH10 屋顶分别说明自用节费、余电销售、逐时配对得到的自用比例和负荷覆盖；地面明确采用已绑定的逐时市场价格时序，并分开发电链损失和结算截弃。CH08 对照月度/年度曲线，说明合成曲线的月天数特征和第 13 年更换/停机边界。CH13.02 以五项任务表列时间、持续自然日、前置任务与计划属性，CH13.03 只分析依赖链与输入标记，不冒称关键路径算法验算。
- Word APP04 列示已有五个 CAPEX 分项及付款期间，单列初始资本支出、营运资金和第 13 年更换；APP06.01 列示已有建设期加 25 个运营年项目税后现金流，APP06.02 独立保留尚无资本金逐年现金流的缺口。测算/来源 XLSX 分别保持 19/10 工作表，42 个被引用公式段与逐符号边界保留；引用不等于全部执行。
- 预备费率输入为 4%，代码的 CAPEX 分项汇总/账簿没有按该费率再次单列费用；无法从现有材料证明已含在报价内。v6 只解释，不在 Word 另加 4%，不改财务计算。`roof.age=5 year` 是屋面**已使用年限**，`roof.remaining_life=30 year` 为剩余年限，25 年是项目评价期，权利期限另审。无债务时 DSCR 原状态为 `UNDEFINED/ZERO_DEBT_SERVICE`，不是 0 倍；F-NPV 的 `npv` 为未实现实例，`financial.phase3e.project_npv` 为已计算的年度项目实例，不互相覆盖。

## 执行与门禁

- 与来源、正文、财务表达和导出直接相关的聚焦命令：`PYTHONPATH=services/solar-pv-engine/src python -m pytest -q --disable-warnings --tb=short tests/solar-pv/test_phase7l_r2_source_binding.py tests/solar-pv/test_phase7l_r2_monthly_binding.py tests/solar-pv/test_phase7l_r2_irr_presentation.py tests/solar-pv/test_phase7l_r2_narrative.py tests/solar-pv/test_phase7l_r2_export.py tests/solar-pv/test_report_resource_monthly.py tests/solar-pv/test_report_business_semantics.py tests/solar-pv/test_report_claims_analysis.py tests/solar-pv/test_phase7l_r2_v6_display.py tests/solar-pv/test_phase7l_r2_inputs.py::test_r2_does_not_overwrite_preexisting_case tests/solar-pv/test_phase7l_r1_project_finance.py tests/solar-pv/test_phase3e_financial_metrics.py`，**149 passed、4 skipped、1 warning、exit 0**（同一代码快照）。未运行完整 L3。
- 新目录双案例经正常交付入口导出，`INDEPENDENT-READBACK-v6.json` 记录对实际 DOCX、两份 XLSX、来源原子、任务、费用和 26 期项目现金流的独立文件读回。原屋顶 `result_hash=398474aff972dee9f0a34bf85380a348bb27f8d4b102d7337ca0478ae0d34fe4`、地面 `result_hash=cd4fca1268dea37283a65680512774053d8e3008cd268375e7dd9f7e9abb2b46` 均保持不变；未改输入、方法或封存 canonical，**未重算**项目。
- F02 PDF `BLOCKED/PDF_RENDERER_UNAVAILABLE`，四文件门禁 `BLOCKED`。未刷新目录真实页码，**未获得 v6 实际页数**，`NO_OVERFLOW`/逐页 `VISUAL_REVIEW` 未通过；用户所述 v5 附件 52 页不能当成 v6 本机页面结果。专业全篇审阅、真实审批与 WorkBuddy 门禁亦未通过。静态读回不等于专业或视觉批准。
- 仅限本地提交；不 push、不部署、不上传或发布。旧保护清单 288 项中 7 项与更早基线 SHA 不同、但相对 R2 B 无改动的历史差异保留披露；本轮不伪报 288/288 通过。历史凭据如被引用，其值始终写作 `[REDACTED]`。

每案附正常出口的 manifest、canonical 副本、输入/来源封存材料和逐件 SHA-256；根目录的 `PACKAGE-MANIFEST-v6.json` 记录两份独立审阅 ZIP 的内容哈希及包哈希。
