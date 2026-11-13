# 验证与可复跑索引

## R1与R2独立QA（当前状态）

完整R1原文/COMMANDS/provenance见QA_INDEX。R1独立134唯一pytest通过、边界探针通过；未接受过期组合probe仍TIMEOUT/124。source_lifecycle_failure_guards、legacy四组byte/hash、strict、grant/policy/canonical变异、首次基础失败与真实派生崩溃已按R1原报告范围实测，不再笼统标为独立QA未执行。

QAI-R1-01仅追加 `tests/solar-pv/test_ai_host_input_view.py` 两例：

1. `test_shared_unaccepted_expiry_rejects_first_native_publish`：屋顶只读canonical快照+新NOT_AI授权，经生产prepare-r2-shared；测试时钟expires_at+1，首次native publish拒MODEL_REQUEST_EXPIRED。断言request原字节和唯一reservation不变，无response/publication-intent/publication/result/host-record，failure明确FAILED及过期码。
2. `test_shared_unaccepted_expiry_rejects_native_and_core_accept`：独立新授权生产prepare、有效期native publish；本例已新建published run原字节复制到受控同test临时分支（不复制历史请求为新授权，不改期限/hash，不删failure），供native/core accept各自经过真实验证链并独立失败封口。时钟过期后两条均须MODEL_REQUEST_EXPIRED；两分支无result/host-record，request/reservation/published response与publication原字节不变，failure明确。

两个新例已由独立quality各首跑 **1 passed**：首次publish 23.475727600045502s，native/core accept 32.80240559997037s（recorder实测）；真实JUnit各1 case、0 failure/error/skipped。作者当时仅静态检查的历史记录保留。两例共用未参数化的roof_native_clock与既有native/make_draft真实fixture，不替换生产验证；生产与Skill原SHA不变。新冻结RUN/developer-source-snapshot-r2.json；独立结论RUN/independent-qa-r2/QUALITY_REPORT.md，判定PASS_LOCAL_QA_NOT_AI_NOT_HOST_E2E、QAI-R1-01 CLOSED。

quality实际使用现成 `.venv/Scripts/python.exe -B -m pytest -q -p no:cacheprovider` 分别首跑上述完整nodeid，各自recorder/input/JUnit/--basetemp。manager将原组合probe合理拆分为两个正式场景，各给55s上限（替代作者建议32s，仍低于120s单批上限），不重跑原失败probe；第二例包含两入口且实际32.802s。完整拆批理由见R2原报告，不隐藏原32s TIMEOUT或根据中途工件推PASS。命令/解释器/代码输入hash/开始结束/完整原stdout/stderr见RUN/independent-qa-r2/COMMANDS.json与RUN/commands/quality-independent-r2-*。

## 开发首轮账本（历史，以下未执行指开发侧当时状态）

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

重复运行不累计为新独立通过数。原失败/超时完整保留。`lifecycle-bounded`后生产仅加了build_view入口bytes类型/长度guard，最终small gates已覆盖；R1完整独立源码审查与专项、R2测试增量复验均已完成，原文和scope分开保留。manager读取四件独立JUnit得到136个不同通过身份（R1 134、R2 2），不是最终快照单次全跑或全仓PASS。

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
- **source_lifecycle_failure_guards：首轮developer未执行，R1独立quality已实测1通过**。真实新授权屋顶生命周期，重新seal view+manifest之后各入口、缺失/半写、锁/模式/预算、accepted过期后恢复、cache变更、取消。保留开发未执行事实及R1独立回执，不重复执行。

## 首轮独立quality建议（历史；已执行结果以上方R1索引为准）

每个命令仍经record_command角色quality，独名label/input/JUnit/--basetemp，timeout<=120s。不要全仓pytest。优先运行未执行的source_lifecycle_failure_guards（单例可能接近120s），再按风险选择codec重seal/资源与原test_ai_host_output_r2的strict拒绝/预算，及既有R2默认路径最小回归。双案正向已有完整JUnit，不需机械重复全部昂贵开会话链。原fixture不跑财务；不选择test_real_native_cli_roundtrip，因为它生成DOCX。

## 首轮开发未执行专项与R1后续状态

默认legacy完整byte/hash、真实初次派生崩溃/先验证、grant/policy变异及strict已由R1独立补验，未接受过期publish/accept由R2两正式用例关闭。具体边界严格以完整QA原文为准，独立probe不是正式pytest；QAI-R1-02正式化为非阻断建议。当前仍是不可安装/非release-ready的源码候选，局部QA不证明所有崩溃点、竞态或专业正确性。

早期pytest使用系统默认临时目录（原失败保留，不扩大清理未知pytest缓存）；后续均显式--basetemp到本RUN。未删除历史资产。当前run中失败/超时目录保留证据，不当可丢弃缓存清理。
