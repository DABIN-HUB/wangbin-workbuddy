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

最终候选冻结并在**同一最终 HEAD 和代码／测试／配置字节**上收集现有关联 L2 的精确 node ID（仅收集，不执行），再各运行一次完整光伏和 WorkBuddy/Expert L3；将每份输出独立归档。完整 L3 是昂贵门禁，开发阶段不得用它取代必要的小范围反馈，也不得为证明 L2 再启动一次相同范围的重型 L2。除工具内置固定选项外，不使用 `-k`、`-x`、`--ignore` 额外选项或跳过／失败过滤以制造覆盖。

```bash
python -m tooling.solar_pv_regression run --tier collect-l2 --out 'C:/Users/wangbin/AppData/Local/hermes/cache/scratch/<candidate>-l2-collection'
python -m tooling.solar_pv_regression run --tier l3-solar --out 'C:/Users/wangbin/AppData/Local/hermes/cache/scratch/<candidate>-solar-l3'
python -m tooling.solar_pv_regression run --tier l3-workbuddy --out 'C:/Users/wangbin/AppData/Local/hermes/cache/scratch/<candidate>-workbuddy-l3'
python -m tooling.solar_pv_regression verify --collection 'C:/Users/wangbin/AppData/Local/hermes/cache/scratch/<candidate>-l2-collection/receipt.json' --solar 'C:/Users/wangbin/AppData/Local/hermes/cache/scratch/<candidate>-solar-l3/receipt.json' --workbuddy 'C:/Users/wangbin/AppData/Local/hermes/cache/scratch/<candidate>-workbuddy-l3/receipt.json' --out 'C:/Users/wangbin/AppData/Local/hermes/cache/scratch/<candidate>-coverage.json'
```

`verify` 只有在三份记录均 exit=0、执行前后身份不漂移、三者身份与**当前检出的最终 HEAD／全部受控输入字节／规范化执行条件**完全一致、命令和日志匹配、JUnit 原始字节校验通过、两个 L3 无失败／错误、L2 收集数量和 node ID／参数后缀逐项包含于光伏 L3 时才能输出覆盖结论。跳过逐项列出理由，**只能说已执行覆盖，不能说跳过的断言通过**；有差异即非零阻断，不使用旧快照的 L3 覆盖新代码。提交前收集的 receipt 不能冒充提交后最终 HEAD 的覆盖证书。`verify` 同时读取历史 P2-4B/C L2 的已保存证据与 JUnit 校验其哈希，将其 **15332.98 秒**列为“本轮若重复运行独立 L2 将产生的历史对照耗时”，不是新测得的运行加速。

若只需核对已归档的旧 L2／L3 重叠，执行 `python -m tooling.solar_pv_regression audit-archive --out 'C:/Users/wangbin/AppData/Local/hermes/cache/scratch/<candidate>-historical-overlap.json'`。它读取原始 JUnit、核对归档 SHA-256 并逐 ID 比对，明确返回 `HISTORICAL_ID_MATCH_ONLY`，**绝不**把旧 JUnit 当成当前候选的 L3 或执行条件证明。

当前 L2 的 7 个模块仍全部保留在测试树中；如关联范围扩展到其他模块，先审查调用链并更新工具内的 L2 模块清单，重新收集并核对，不得拿旧清单的 60 个 ID 宣称覆盖新范围。受影响回归依据调用链选择，来源篡改、独立生产、隔离边界以及失败／跳过测试不得因共享原始物理资源而删除或降级。跨模块只读夹具复用**本轮不实施**：后续如需实施，仅在同一 pytest 进程内对完整哈希和来源均已核验、无共享可变状态的物理／原始资源使用；每个消费者复核字节，候选输出私有；篡改及独立生产测试仍须独立执行，收益另行实测，不从旧 profiler 相加估算。

## 工程数值验收（独立草案）

已批准使用原 D2 声明的**连续闭区间、端点参与**，负价受既有来源和合法性门禁约束；`break_even.price_tolerance` 仅表示区间宽度，独立案例沿用 `0.000001 元/kWh`。`1 元` SYNTHETIC NPV 残差只是**待单独批准的候选**，真实项目不继承。完整的版本化草案、来源和未批准差异见 `docs/solar-pv/19-phase3e-p2-4-numerical-acceptance-draft.md`；在价格域全分支的可审计证明和正式表示获批前，正式结果仍非数值 `BLOCKED_MISSING_INPUT`。本轮不修改冻结定义、D2/D3 或正式结果 Schema。

历史性能和 L1/L2/L3 JUnit 见 `reports/solar-pv/phase3e-p2-4b-c-root-certification-evidence.json`；本文件不是新一轮正式盈亏平衡售价证明。
