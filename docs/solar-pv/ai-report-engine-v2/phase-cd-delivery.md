# SOLAR-PV-AI-REPORT-ENGINE-2.0.0：Phase C/D 本轮交付与恢复

日期：2026-11-12。**有限交付，非2.0完成/非发布：交易费现金链修复；终期候选比较未闭合；六份真实AI章节及双案对照Word交用户审核。** 停在Phase D，不进入E/F/G，不启动2.1。

## 1. Git与冻结资产

- 起始main：`fcf888caa15cadb959d3d551f1d3188111201840`；没有强制回退或重复合并。
- 财务有限修复提交：`f24581709a5e26d420154c046eb77a7d61e9e396`。
- 后续文档交付提交及最终main HEAD：见同包`final-state.json`；该文件在最后一次本地提交后由Git实测生成，避免提交文档自引用自己的SHA。
- 生产变更仅`calculation/scenario_runner.py`、新`scenario_cash_sources.py`；新22项规则边界测试。临时终期接线和测试已撤回，试验原件另存，不作为已验证生产功能。
- 规格按现有Registry的UTF-8-sig/CRLF→LF规则核验为`59e379906f6b83d91a76179f14fdc00e5c0dc9346ef5d272bbcf04da90df7532`，与spec-lock一致。最初raw字节断言失败已定位为归一化口径差异，未重写规格或锁。原raw SHA另存final-chapter-verification.json。
- 实际核对18章100节、13附录26节、469字段89公式、281映射、169+20=189术语；没有更换公式、四文件合同或Word样式，旧report_export.py与R13相同。
- 本轮930个保护清单文件无变；前轮3671个历史保护文件重新核对无变，包括历史审阅资产。两套dist ZIP/sidecar哈希及CRC核验通过，仍忽略，未重打包为本轮版本。原隔离工作树保留。

## 2. 财务实际结果

详细调用链、来源ID、字段实例、支付政策、完整候选身份及首次缺口见`phase-c-cash-source-audit.md`。

| 项目 | 屋顶 | 地面 |
|---|---|---|
| 候选 | 原合成维护费1.05倍 | 原合成维护费1.05倍 |
| 3D/3E及sealed receipt | 实际存在 | 实际存在 |
| 交易费支付 | 已消费原合法合成支付规则，非null | 同左 |
| 现金组成 | 25运营期逐项核对 | 25运营期逐项核对 |
| 终期现金 | 候选未闭合 | 候选未闭合 |
| NPV、IRR、静动态回收比较 | BLOCKED，ranking空 | BLOCKED，ranking空 |

不是来源原本没有：交易费文件和终期NO_DISPOSITION原始声明均存在。交易费缺在runner→3D传递；终期缺在generic 3E未接入候选来源绑定。恢复两案归档各71个D3文件后，屋顶完整路径600秒超时，未取得完整结果；地面未重复启动同一高成本完整路径。未复制基准终期金额、未改比较器放行、未将基准指标填入候选。

会计盈利、独立经营现金转正、股东资金回收继续NOT_CALCULABLE，裁定单见`phase-c-method-adjudication-required.md`，未获方法负责人/用户审批。

## 3. 用户首先阅读什么

运行根：`.runtime/solar-pv/ai-v2-cd-20261112/`。

- `comparison/industrial_rooftop/屋顶-R13与AI重点章节对照.docx`
- `comparison/utility_scale_ground/地面-R13与AI重点章节对照.docx`

两份对照各包含CH08、CH10、CH16共20小节，逐节列旧固定正文与真实AI新文。使用同一canonical重渲染未改的旧R13生成器；不是挪用另一输入身份的历史R13实物。对照正文没有重列所有表图公式，完整旧Word和六份局部AI Word另附。

六份章节JSON、请求、response、accept结果、claims及state位于`<type>-preview/`和`<type>-finance-preview/`。CH08使用CH08-1，CH10最终有效CH10-2，CH16独立run的CH16-1。手写draft及机械封装output保存在`authored/<type>/`。

所有六章已accept并在最终源码下resume重验；最终回执final-chapters-command.json exit0，final-chapter-verification.json绑定文档/请求/结果SHA，共40小节。数字仍由事实槽渲染，不由正文计算器补算。

正文实质差异：屋顶讨论负荷匹配、自用节费与余电，地面讨论送出约束、全额上网与交易；财务明确项目/股东、现金/会计、单年为正/回本的差别。全部是合成示例，未证明真实建设条件、并网许可或收益保障。

## 4. 模型、内容及质量限制

当前会话运行标识gpt-6-astra；交换标签hermes-assisted-gpt-6-astra；实际状态HERMES_ASSISTED_UNVERIFIED。本轮是会话模型实际阅读请求并撰写正文，封装脚本不生成专业分析，不再称NOT-AI。local-session-authoring-*仅本地声明，不是平台执行ID；没有独立服务端模型调用回执。

请求有效期、context/output字节及重试限制由本地协议执行；没有可证明的宿主模型执行超时、token/费用独立回执。请求有效期3600秒不能当作模型调用超时。没有使用第三方API Key或读取其他应用凭据。

逐小节自审见phase-d-content-self-review.md及content-self-review.json。只有同模型自审，没有独立专家签审；正文已逐段读回，未完成Word逐页渲染视觉验收。CH10.01地面小节模式引用、月度差异因果证据和逐时平衡可读摘要仍有具体不足，财务边界文字也需要用户评价重复程度。因此没有为凑八章扩展CH05/14/15/17/18。

WorkBuddy正式宿主保持MODEL_INTEGRATION_BLOCKED。官方资料与本机有限探测、私有验证步骤见phase-d-host-private-verification.md；prepare辅助脚本已真实执行exit0，但这不等于平台调用。未安装、上传或发布。

## 5. 回归与失败证据

| 选定专项 | passed | failed/errors/skipped | 退出码 | 上限 |
|---|---:|---|---:|---:|
| 最终fee规则、财务核、评价、runner | 61 | 0/0/0 | 0 | 180秒 |
| 既有交易费和终期source合同 | 47 | 0/0/0 | 0 | 180秒 |

去重108项；原52/9项重跑不累加。新增规则测试22项包含其中。实际双案bundle又执行重复消费、错误receipt及篡改拒绝，但不计入pytest数量。完整终期绑定专项只有进度输出、180秒exit124，没有完整JUnit，因此最终passed/failed/skipped未知，不能猜成两项通过。

失败记录全部保留：CH10首次CHAPTER_APPLICABILITY_REASON_REQUIRED，补储能不适用说明后新请求通过；CH16首次MODEL_CONTEXT_BUDGET_EXCEEDED，改独立2MiB受控run后通过；初次finance BUNDLE_MISSING_FILE，归档恢复证明不是原件丢失；完整重放工具外层420秒中断（无内部exit receipt），随后600秒exit124；终期专项180秒exit124。后两项未解决，不能用108项抵消。

前轮9组JUnit实际解析去重251项、零失败/错误/跳过，历史失败原件仍在；它们是历史证据。旧回执缺执行时不可变源码树哈希，不能独立补证所有测试当时精确源码状态，也不能移作本轮全仓PASS。R12全仓中止未关闭；本轮未运行4609项全仓。

## 6. 独立门禁

| 门禁 | 本轮结论 |
|---|---|
| PHASE_C_FINANCIAL | PARTIAL：fee闭合，terminal及三项方法未闭合 |
| SCENARIO_COMPARISON | BLOCKED：两案ranking为空，未形成有效多候选比较 |
| HERMES_AI_CONTENT_PREVIEW | GENERATED_AND_VALIDATED / HERMES_ASSISTED_UNVERIFIED |
| WORKBUDDY_MODEL_INTEGRATION | MODEL_INTEGRATION_BLOCKED |
| PHASE_D_CONTENT_REVIEW | USER_REVIEW_REQUIRED；自审PARTIAL |
| FULL_REPOSITORY_REGRESSION | NOT_RUN / 历史ABORTED未关闭 |
| FORMAL_FOUR_FILE_DELIVERY | NOT_EXECUTED；局部Word不是正式四文件 |
| PDF_FORMULA_COPY_SEARCH | BLOCKED；未关闭R13历史问题 |
| PROFESSIONAL_APPROVAL | NOT_APPROVED |
| PLATFORM_RELEASE | NOT_EXECUTED / NOT_AUTHORIZED |

## 7. 恢复与停止点

审阅包含本说明、当前源码差异、Git恢复bundle、恢复脚本、有效JSON/Word、JUnit/退出回执、自审和SHA manifest。精确最终HEAD、Git状态、归档成员数/哈希以final-state.json及包外sidecar为准。先`git bundle verify`核验；增量bundle依赖已保留的R13基线，不自动fetch、merge或reset。新尝试必须使用不存在的run路径，不能覆盖本轮或历史失败。

`recovery/scripts/`保留执行器、fee重算、章节准备/封装、旧Word重渲染、对照及终验脚本。terminal-experiment-not-accepted仅诊断源码，不是最终代码；其恢复脚本不能直接在fee-only最终代码上当作支持的正式入口。大体积恢复D3/原始interval留本地recovered目录，审阅包按归档路径和SHA引用，不重复复制全部分块；原归档仍受Git保护。

卫生：本轮没有确认为无用的已跟踪文件删除，净删除0文件/0字节，释放0字节；当前实验/失败/恢复材料因有恢复证据价值受控留存，不进入Git。新增合同/源码/测试选择性提交；生成Word/JSON/JUnit/ZIP只在忽略目录。未push、pull、merge、rebase、reset或删除旧工作树。

下一步仅等待用户审阅两份对照Word，并对三项财务方法裁定给出意见。终期完整候选链仍需后续限定诊断与验收，不能由内容认可推导通过；用户内容审核前不得进入Phase E。
