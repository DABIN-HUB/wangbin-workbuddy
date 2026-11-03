# Phase 3E P2-4B/C：分级回归与证据复用规则

状态：仅批准**同一最终候选**的完整 L3 JUnit 覆盖同条件关联 L2；不改变任何测试、断言、冻结计算或正式结果结构。正式 `F-BREAK-EVEN-PRICE` 继续 `BLOCKED_MISSING_INPUT`。本规则不授权 P2-5、Phase 3F、push 或发布。

## 可执行入口

从仓库根目录使用 `python -m tooling.solar_pv_regression`。所有 `--out` 均须为**不同且全新的仓库外私有目录**，例如在 Hermes scratch 根下创建一个运行专属目录；工具在该目录内分离 `workspace-tmp`（TMPDIR/TMP/TEMP）与 `pytest-basetemp`，不能令两者重合。工具把命令、退出码、已列入输入身份的服务源码／测试／工具／产品／配置字节 SHA-256、Python／pytest／依赖及相关环境指纹、JUnit SHA-256、跳过原因及原始日志保存在各自 `receipt.json`、`junit.xml`、`output.log`；运行前后源码身份必须相同。报告文件和其他历史输出不参与可执行输入身份；若有未纳入清单的生成代码／外部动态数据，先把它纳入受控输入或停止复用。证据目录应在收口后按项目归档政策保存，不要把测试临时目录作为可信共享缓存。

```bash
# 开发中的快速数学、方法配置检查；此集合不包含完整财务链。
python -m tooling.solar_pv_regression run --tier fast --out 'C:/Users/wangbin/AppData/Local/hermes/cache/scratch/<candidate>-fast'

# 仅运行改动影响的现有用例：可重复 --select 指定精确 pytest node ID 或文件。
python -m tooling.solar_pv_regression run --tier affected --select 'tests/solar-pv/test_phase3e_price_selector.py' --out 'C:/Users/wangbin/AppData/Local/hermes/cache/scratch/<candidate>-affected'

# 只有确需全链诊断时才运行所选真实 E2E；不把该执行当作最终完整 L3。
python -m tooling.solar_pv_regression run --tier e2e --select 'tests/solar-pv/test_phase3e_break_even_project_session.py::test_declared_independent_project_has_real_full_chain_root_witness' --out 'C:/Users/wangbin/AppData/Local/hermes/cache/scratch/<candidate>-e2e'
```

最终候选冻结后，先在**同一代码／测试／配置身份**上收集现有关联 L2 的精确 node ID（仅收集，不执行），再各运行一次完整光伏和 WorkBuddy/Expert L3；将每份输出独立归档。完整 L3 是昂贵门禁，开发阶段不得用它取代必要的小范围反馈，也不得为证明 L2 再启动一次相同范围的重型 L2。除工具内置固定选项外，不使用 `-k`、`-x`、`--ignore` 额外选项或跳过／失败过滤以制造覆盖。

```bash
python -m tooling.solar_pv_regression run --tier collect-l2 --out 'C:/Users/wangbin/AppData/Local/hermes/cache/scratch/<candidate>-l2-collection'
python -m tooling.solar_pv_regression run --tier l3-solar --out 'C:/Users/wangbin/AppData/Local/hermes/cache/scratch/<candidate>-solar-l3'
python -m tooling.solar_pv_regression run --tier l3-workbuddy --out 'C:/Users/wangbin/AppData/Local/hermes/cache/scratch/<candidate>-workbuddy-l3'
python -m tooling.solar_pv_regression verify --collection 'C:/Users/wangbin/AppData/Local/hermes/cache/scratch/<candidate>-l2-collection/receipt.json' --solar 'C:/Users/wangbin/AppData/Local/hermes/cache/scratch/<candidate>-solar-l3/receipt.json' --workbuddy 'C:/Users/wangbin/AppData/Local/hermes/cache/scratch/<candidate>-workbuddy-l3/receipt.json' --out 'C:/Users/wangbin/AppData/Local/hermes/cache/scratch/<candidate>-coverage.json'
```

`verify` 只有在三份记录均 exit=0、执行前后身份不漂移、三者身份与规范化执行条件完全一致、命令和日志匹配、JUnit 原始字节校验通过、两个 L3 无失败／错误、L2 收集数量和 node ID／参数后缀逐项包含于光伏 L3 时才能输出覆盖结论。跳过逐项列出理由，**只能说已执行覆盖，不能说跳过的断言通过**；有差异即非零阻断，不使用旧快照的 L3 覆盖新代码。`verify` 同时读取历史 P2-4B/C L2 的已保存证据与 JUnit 校验其哈希，将其 **15332.98 秒**列为“本轮若重复运行独立 L2 将产生的历史对照耗时”，不是新测得的运行加速。

若只需核对已归档的旧 L2／L3 重叠，执行 `python -m tooling.solar_pv_regression audit-archive --out 'C:/Users/wangbin/AppData/Local/hermes/cache/scratch/<candidate>-historical-overlap.json'`。它读取原始 JUnit、核对归档 SHA-256 并逐 ID 比对，明确返回 `HISTORICAL_ID_MATCH_ONLY`，**绝不**把旧 JUnit 当成当前候选的 L3 或执行条件证明。

当前 L2 的 7 个模块仍全部保留在测试树中；如关联范围扩展到其他模块，先审查调用链并更新工具内的 L2 模块清单，重新收集并核对，不得拿旧清单的 60 个 ID 宣称覆盖新范围。受影响回归依据调用链选择，来源篡改、独立生产、隔离边界以及失败／跳过测试不得因共享原始物理资源而删除或降级。跨模块只读夹具复用**本轮不实施**：后续如需实施，仅在同一 pytest 进程内对完整哈希和来源均已核验、无共享可变状态的物理／原始资源使用；每个消费者复核字节，候选输出私有；篡改及独立生产测试仍须独立执行，收益另行实测，不从旧 profiler 相加估算。

## 工程数值验收：单独审批事项（尚未实施）

拟议独立外部契约版本标识：`solar-pv-break-even-numerical-acceptance/draft-0.1`（**草案，尚未批准／执行**）。保持冻结定义 `P*={p∈P | NPV_b(CF_b(p),r_b)=0}`，不将参考点 `NPV=0E-22 元` 解释为完整根集。以下各项是该草案所需**待用户决定**的业务／数值语义，不预设任何默认值：

1. **价格域：**连续价格区间，还是有来源的业务报价网格；是否允许负价、端点及报价步长？将连续域改为网格域需要单独批准，不能偷换冻结根集。
2. **价格误差：**根隔离区间 `[a,b]` 的最大允许宽度（元/kWh）和所报告代表价的误差定义；既有 D2 `break_even.price_tolerance` 是否仅约束区间宽度？不得拿它替代货币残差。
3. **货币残差：**独立的 `|NPV|` 门限（元）、舍入／计算误差界及使用的现金流口径；已有 `precision.abs_tolerance` 不是自动获批的元单位阈值。
4. **完整性：**允许认证的项目类型、税费／结算分支与价格域、对精确函数和 Decimal 实际执行模型分别要求何种全域根集证明，如何处理多根／零平台／无根；有限网格扫描只有在网格域获批且穷尽时才可能证明**该网格**完整性。
5. **结果语义：**是否允许已证明区间内的近似报价写入既有正式数值 `value`？这与精确集合可能不同，**须另行批准**；在未批准或不能证明全部根时，维持既有非数值 `BLOCKED_MISSING_INPUT`，不宣布 `NO_ROOT`，不调整冻结公式、D2/D3 或正式结果 Schema。

最小实施顺序：批准价格域和两类独立容差／完整性适用范围之后，先形成**独立的版本化证书数据及审核器**，再由现有正式入口按来源和全域证明核验它；任何证明缺口保持阻断。若审批发现必须改变冻结定义、D2/D3 或结果表示，先单列差异报审，本轮不实施。

历史性能和 L1/L2/L3 JUnit 见 `reports/solar-pv/phase3e-p2-4b-c-root-certification-evidence.json`；本文件不是新一轮正式盈亏平衡售价证明。
