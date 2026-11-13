# 验证与可复跑索引

运行根 `RUN=.runtime/solar-pv/SOLAR-PV-R2-SHARED-INPUT-IMPL-01`。所有执行原命令、输入hash、解释器、时间、退出、stdout/stderr在 `RUN/commands/developer-*.json/.stdout/.stderr`。pytest有独名JUnit；两个超时没有完整JUnit，不能从进度`.`推断最终计数。根现成venv源码测试不是安装验证；conftest显式源码路径，不设置PYTHONPATH或下载依赖。

## 实际批次

| label | 结果 | 含义 |
|---|---|---|
| codec-red | exit1，2失败 | 模块尚不存在，原始失败保留 |
| codec-green | exit0，2通过 | 原两案确定字节含LF回归 |
| lifecycle-red | exit1，2失败 | 新生产动作尚不存在 |
| lifecycle-green | TIMEOUT124，115.812654s | 首次组合生命周期批；无完整JUnit，不计PASS |
| codec-risks | exit0，35通过、2 deselected | 完整两案reseal/QA-F01/语法/资源/预算/no-clobber；后续加入纯构建缓存，不冒称此为最终快照全量结果 |
| upstream-red | exit1，1失败、37 deselected | 已缓存上游没有重验request的真实dispatch缺口；已加公共_request重验 |
| lifecycle-final | TIMEOUT124，115.903809s | 去重仍不足；无完整JUnit，不计PASS |
| lifecycle-bounded | exit0，3通过、35 deselected，78.384028s | 双案全新授权/canonical快照真实生产prepare-r2-shared→publish→accept→core resume→checkpoint；缓存重验dispatch。削减重复开会话与重建，不跳过必经验证 |
| final-small-gates | exit0，12通过、37 deselected，3.321156s | 最终codec/深度缓存/精确预算/空值/上游dispatch/构建缓存防修改及原wrapper隔离回归 |
| freeze-measure | exit0 | 最终源码快照、双案新生产codec视图与manifest/精确还原 |

重复运行不累计为新独立通过数。原失败/超时完整保留。`lifecycle-bounded`后生产仅加了build_view入口bytes类型/长度guard，最终small gates已覆盖；生产生命周期其余实现未变。最终候选仍需独立quality真实源码复核及相关风险复跑。

## 保存测试与需求映射

文件 `tests/solar-pv/test_ai_host_input_view.py`：

- historical_exact_roundtrip：两案完整字段、任务、Schema、状态、数组顺序、原末尾LF；确定生成且变小。
- resealed_full_fidelity_and_qa_f01：两案分别改unknown metric/claim、duplicate source、同来源跨节fact，及删事实/少来源/状态/数字/词法/单位/期间/边界/定位/Schema/六节/风险/上游/表行顺序；重新生成合法view_hash后对固定可信原件拒绝，而非坏hash。
- exact_sentinels_and_noncanonical：null/0/false/空数组对象/大整数/指数/负零和未知假设合成已计算；重复键/非法UTF8/非有限/非确定序列/保留键拒绝。
- view_protocol_reseal_rejections：未知协议/mapping/mode/key，悬空、循环、未用/重复池、坏索引、错案。
- cache_subtree_insertion_depth_counterexample：38层缓存子树先浅插再深插，拒绝展开77层，未放大64上限。
- resource_boundaries_include_keys_utf8_and_punctuation：键/容器/标点/UTF8展开预算、引用/节点预算。
- byte_budget_original_lf_and_no_clobber：旧request预算不计LF；视图阅读封套计LF；no-clobber、缺派生物。
- new_native_lifecycle：双案真实新prepare，NOT_AI协议fixture，仅本地链路，不执行金融计算或Office。
- cached_upstream_must_revalidate_shared_request：最小mock仅断言cache dispatch必须进入公共_request；不是领域权限证明。
- flat_limits_and_cache_defensive_copy：pool/输入限额、缓存对象隔离。
- **source_lifecycle_failure_guards：已保存、developer未执行（预算止损），NOT_TESTED**。真实新授权屋顶生命周期，重新seal view+manifest之后各入口、缺失/半写、锁/模式/预算、accepted过期后恢复、cache变更、取消。quality可独立执行此用例；若失败不得写已通过。

## 独立quality建议（总任务预算不超过900s）

每个命令仍经record_command角色quality，独名label/input/JUnit/--basetemp，timeout<=120s。不要全仓pytest。优先运行未执行的source_lifecycle_failure_guards（单例可能接近120s），再按风险选择codec重seal/资源与原test_ai_host_output_r2的strict拒绝/预算，及既有R2默认路径最小回归。双案正向已有完整JUnit，不需机械重复全部昂贵开会话链。原fixture不跑财务；不选择test_real_native_cli_roundtrip，因为它生成DOCX。

## 仍未完成的开发侧专项

默认legacy完整byte/hash边界生产回归、真实初次派生崩溃及先验证再派生的故障注入、未接受结果过期publish/accept、grant/policy变异的生产复跑，以及完整原R2输出strict专项未在developer剩余预算中执行。本轮不能仅凭源码阅读把这些项判PASS。最终本地提交为wip源码候选，等待quality与manager据实收口；不能当可安装或release-ready。

早期pytest使用系统默认临时目录（原失败保留，不扩大清理未知pytest缓存）；后续均显式--basetemp到本RUN。未删除历史资产。当前run中失败/超时目录保留证据，不当可丢弃缓存清理。
