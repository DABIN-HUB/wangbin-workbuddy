# Phase 2B 来源、单位、类型与输入一致性验收

2026-10-28。前置Phase2A=936428fa28ee2fb783f2800d80b2c9df4e6c7c5b。状态：PHASE2B_LOCAL_PASS，不代表整个Phase2完成。

## 实际实现

- units.py：显式注册功率/直流铭牌/交流铭牌三维度、电量、面积、比例、金额/单位容量价格、时间、温度/风速及全部冻结单位；Fraction因子及上下文独立Decimal，非终止十进制要求显式舍入，原单位/值及规则可复算。八种ROUND规则、绝对零度、真实日期/UTC offset/IANA键均有数值/边界/反向测试。
- provenance.py：六类source_kind、U/D/C映射、原始/规范值、证据/授权/敏感级/假设；不把用户陈述自动核实；冲突保留候选且value=null，需要人工有理由选取；选择来源不等于VERIFIED。未知保留null。
- validation.py/consistency.py：469字段类型/范围/枚举等、逐原子来源、数组/实例ID、金额同明细血缘、价格基年/税含/币种不兼容、合法日内价格表、时序/闰日、前置任务引用/循环（含1100逆序任务链）、报价算术及年度边界；只核验给定数据，不估算发电/收入/NPV或生成结果。
- NORMALIZATION_REPLAY_MISMATCH阻止单位只改标签，confidence_basis不能只有数字概率；格式校验不依赖jsonschema可选RFC3339扩展。Windows IANA依赖在新包显式声明tzdata==2026.5，实际隔离环境读取同版本，不更改旧项目依赖。
- 完整Schema产物同步到新的normalization信封结构，与运行时生成器经严格Decimal解码比较完全一致，冻结469目录未变。

## 实际测试和证据

解释器：C:/Users/wangbin/AppData/Local/hermes/cache/scratch/solar-pv-phase2-20261028/verify-venv/Scripts/python.exe。

```text
-m pytest tests/solar-pv -q --tb=short --basetemp=.../pytest-phase2b-accepted --junitxml=.../phase2b-accepted-junit.xml
exit=0；1768 passed / 0 failed / 0 skipped
```

完整命令的固定前缀/根目录见13实施计划和原始日志；最终日志phase2b-accepted.txt、JUnit同名xml，单位独立最终348 passed。每类转换正常/反向/边界/异常，以及469字段合法记录/错误类型/所有已冻结标量约束都有真实断言，不用文档检查数替代。

RED资料：phase2b-red.txt、consistency-red、boundaries-red、metadata-red及phase2b-units-red1..6.log；GREEN及单位逐轮说明同目录。父任务额外增强后一次回归1 failed/1767 passed：未知面积0首先触发范围错误，影响UNKNOWN专用原因；修复错误路径同时保留FIELD_SCHEMA及UNKNOWN_MUST_BE_NULL，未改原断言，最终全绿。日志副本仅去除行末空白以通过git diff --check，scratch原始原文仍保留。

独立契约审计：phase2-contract-clarifications.md。97条件字段/九类型/L1-L3尚按2C实现，不把2B当分类/成熟度PASS。四文件、全部计算、真实站址数据、WorkBuddy/审核仍未实现或未测；发布BLOCKED。单位纯函数的大数测试不是OS资源隔离证明，旧Windows硬限制仍未解决。

提交前复核288保护hash、阶段范围、凭据模式、git diff --check；只暂存Phase2新包/新测试/本项目证据，本地提交不push。SHA由git log --本报告读回，最终报告汇总。
