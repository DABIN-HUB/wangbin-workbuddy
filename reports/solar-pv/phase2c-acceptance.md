# Phase 2C 九类输入、条件与证据完整度验收

日期2026-10-28；前置Phase2B a30dcd37912ffdce3e636732c3892f8f6cf07a15。状态PHASE2C_LOCAL_PASS，仅输入层，不是光伏业务/E2E。

## 模块与闭环

- categories.py + 九类scenarios/<pv_type>/contract.json：独立输入边界，94专属字段跨类拒绝；工商业与地面销售/负荷/加固屋租收入成本反向隔离；storage组合8个合法非递归基座、保留基座未知，其他七类独立类型/专属字段与子型边界；所有计算/E2E仍NOT_IMPLEMENTED。
- conditions.py：从469目录匹配97条件字段，所有13个IN-C规则与父容器继承，三值T/F/U；无债务和纯售电不索要无关资料，未知不豁免，价格表/市场时序择一。精确已知方法名需要显式提供，不从自然语言猜月度/逐时算法。
- applicability.py：受控、不递归的专项适用性复核；与5种证据状态分离，必须有来源/复核者/理由和时间，不能豁免安全/权属/资源。可选元数据不改变469字段ID或新增第六证据状态。
- completeness.py：九输入证据轴、逐字段/逐行/标量元素义务与来源、分级及假设上限；L1_DRAFT接受不足数据，下一问最多5项。不按填写率升级；缺正式接入材料不能输出已确认资格，无曲线自用率UNKNOWN。
- quality.py：给定容量/视在容量/功率因数、声明装机清单、荷载、有效期、年度/月度与观测时间边界、单环闭合/自交和风险；不估算发电/电价/现金流。复杂拓扑/大型几何及代表性负荷映射显式要求专项复核，没有截断或伪称完整校核。
- docs/solar-pv/14-phase2-architecture.md记录接口、证据级别与真实报告/执行门禁分离；完整Schema产物已与运行时生成器一致性读回。

## 真实测试

独立分类223 passed；主任务联合命令：

```text
C:/Users/wangbin/AppData/Local/hermes/cache/scratch/solar-pv-phase2-20261028/verify-venv/Scripts/python.exe -m pytest tests/solar-pv -q --tb=short --basetemp=.../pytest-phase2c-full --junitxml=.../phase2c-full-junit.xml
exit=0；2023 passed / 0 failed / 0 skipped
```

真实日志phase2c-full.txt/JUnit；条件/NA/质量/完整度各自RED及分类RED/GREEN留同目录。一次联合失败2 failed/8 passed：把分类“计算NOT_IMPLEMENTED”提示误当输入质量缺口，导致所有正向L2/L3都被卡到L1。修复后将能力提示保留在validation_issues与执行阻断，不用于输入成熟度；can_execute_calculation仍false，没有删断言或放行未实现计算。

测试用例全部明确SYNTHETIC，包括声明型L2/L3输入证据，绝不是实际站址/真实项目/已审批报告。current_level scope=INPUT_EVIDENCE_ONLY，report_maturity=NOT_EVALUATED；可移交未来计算不表示引擎可执行。分类业务、四文件、真实数据、WorkBuddy与审核仍未通过，发布BLOCKED。

旧产品源码/测试/归档未修改；旧回归基线145/0/5已留2A证据，最终Phase2E再跑当前快照全回归。提交前仍核对288保护文件、凭据模式与diff；仅本地提交，不push。
