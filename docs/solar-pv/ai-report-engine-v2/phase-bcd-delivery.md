# AI Report Engine 2.0 — 本轮交付与恢复说明

## 结论

**PARTIAL / MODEL_INTEGRATION_BLOCKED。不是完整2.0、Phase C或Phase D验收通过。**

本地main已安全快进整合A/B，随后完成规格补充、结构化证据、章节依赖与主张、确定性财务评价/候选验证适配。实际运行暴露的财务生产者和现金来源集成缺口保持显式；没有用协议Fixture冒充真实模型。没有push、平台上传、发布、部署；没有进入E/F/G。

## 本地阶段提交

| 阶段 | 完整SHA |
| --- | --- |
| Phase A冻结 | 2723d7a04b8f43a3b3aeac78e5b5ded21c2103a1 |
| Phase B初始框架 | 95577c63c9044fe2ec9d3acf6be8bafde833568d |
| EXC-003必要规格补充 | 51bfadfd97abe98c996c8822d366c7d3bec7cdbe |
| 结构化证据 | 233de7680e0c55d5a0af38646777b4674115544d |
| 依赖、主张与术语 | 2dbc7822dbfe322fa4f89062a2895dc41abe8a26 |
| 财务评价与已执行情景校验 | fe366da865770d313450a110bce907ebb1165653 |

本说明另行本地提交；最终HEAD和工作区状态由归档中的 `evidence/final-state.json` 读回记录，避免在提交内循环引用自己的SHA。原隔离树仍在 `refactor/solar-pv-ai-report-engine-v2` 的 Phase B 提交，未删除。

## 规格与框架

原规格 SHA-256：`885b92420ee3bbfd9b6ce473ed764584a224d9c246e0d294be638a549fd85f91`，实测64位并与Phase A的UTF-8/LF内容一致。

EXC-003后：`59e379906f6b83d91a76179f14fdc00e5c0dc9346ef5d272bbcf04da90df7532`。冻结40号原文未改；18章100正文节、13附录26节及原469字段/89公式/281映射/189术语保持。100个独立研究目标的字段/指标/公式/表格/判断作用清单在 `section-research-audit.json`，结构审核不是AI内容质量验收。

新实现包括：重复行/原子身份溯源、原生产者月度/年度结果投影、受控计划与风险表；来源白名单与默认原始时序不外传；上游已accept内容重验与变更失效；七类claim、段落证据关系及受控公式/单位term；保留旧报告工具的compat接口。CH01/CH18在专业审阅前仍限制为DEFER，不自动裁定建设或投资通过。未知结构缺适配器仍明确阻断。

旧 `report`、`ground-report`、report_export.py和calculation目录相对R13未变；没有删除旧正文或重设Word样式。

## 财务与真实运行

详见 `phase-c-financial-contract.md`。两案基准项目NPV/IRR/静动态回收来自原canonical；会计净利润、独立经营现金和股东回收不可计算的原因独立列示。

屋顶、地面分别真实运行一个显式合成运维压力候选。两案候选项目现金流都缺同身份的 `finance.project_terminal_cash`、`transaction_cost_cash_paid`，上游阻断导致候选NPV/IRR/回收期不能比较；排名为空。当前通用runner与来源路径的集成缺口不能包装成用户缺资料，更不能借用基准数值或填零。有效多候选排名的正向验收尚未完成。

两案CH17 prepare/accept/resume、缓存篡改拒绝、受控表及现有样式DOCX已执行。文件名明确包含 `NOT-AI`；正文是协议Fixture，不是AI试点，不交作Phase D内容验收。

## 专项结果

最终选定JUnit共251个不同用例通过，零失败、错误、跳过：规格104、结构化22、依赖18、财务评价13、框架屋顶36/地面35、原财务kernel17、旧Word兼容屋顶3/地面3。每个pytest进程上限180秒；各自命令、退出码、JUnit及日志保留。原197项及本轮中途重复运行不叠加计数。

另有两案实际情景运行、协议DOCX、无授权/伪造回执负例及公开CLI回执，不伪造为额外pytest数量。失败尝试也在归档内：执行输入重建身份、来源白名单、阈值表检查误判及重复缺口schema错误均有原始退出记录。不得把整个历史运行目录描述为从未失败。

全仓未重跑；R12已终止的全仓门禁没有被关闭。Word结构/表格/公式专项不等于新的PDF视觉审核或公式复制/搜索通过。

## 真实模型及审核状态

官方宿主研究及本机有限探测见 `host-orchestration-review.md`。本轮没有独立可核验的真实模型回执；未读取Hermes/浏览器/其他应用凭据，也未开通收费Provider。文件有效期不代表远程调用超时。

没有真实八章AI样本、R13对真实AI的内容对照或Phase D审阅DOCX。当前会话做了独立入口检查及自审，但**不是第三方独立专业QA**。用户内容审核门禁尚未具备样本条件，不能视作已到达或通过。

### 仍属于2.0的未闭合项（不转移成2.1）

1. 取得可独立核对的授权宿主调用、超时/重试/费用边界证据；先做双类型CH08。
2. 专业裁定会计净利润、独立经营现金与股东回收边界后再补生产者，不能由报告层擅定会计方法。
3. 将终期及交易费现金来源合法重绑定到候选身份，形成同口径有效多候选正向比较；目前不能宣称优化完成。
4. 完成高风险主张语义、跨章一致性、两类型差异与真实内容独立QA。
5. 有真实样本后交用户审阅；未经确认不进入E。正式四文件、PDF和平台发布另有门禁。

AFTER_V2：本轮没有新增业务扩展；上述缺口继续属于2.0，不以新版本名绕过。

## 恢复说明

证据在 `.runtime/solar-pv/ai-v2-bcd-20261111/`，该目录被Git忽略，**不是远端备份**。审阅ZIP是本地源码/证据备份，不是可安装WorkBuddy发布包。

1. 保留原仓库、原隔离树、全部历史候选。恢复前先读agent.md并检查Git现场，不覆盖已有修改。
2. 归档 `recovery/ai-report-engine-v2.bundle` 保存R13之后的本地提交；它以 `ecaac498e3d14dbae4874e7fa46e63d74c5da2df` 为前置历史。在已有该基线的仓库中先运行 `git bundle verify <bundle路径>`。不要向当前main自动fetch/merge/reset；需要重建时在新的隔离副本按清单恢复。
3. 核对 `MANIFEST.json` 的每个成员SHA-256与ZIP sidecar。`source/` 为最终源文件快照；`evidence/` 为运行证据；`recovery/` 为有界脚本与Git bundle。不要把negative-cache当作有效运行。
4. 使用回执中实际成功的Python解释器；Windows设置 `PYTHONPATH=services/solar-pv-engine/src;services/document-engine/src`。需现有docx/jsonschema等依赖，不用pip/python不同版本混装。
5. 在仓库根执行 `python -m wangbin_solar_pv.reporting spec-check`；然后执行 `evaluate --canonical tests/fixtures/solar-pv/phase7l-r2-delivery/<类型>/canonical.json`。
6. 执行 `compare` 时再加 `--scenario-bundle .runtime/solar-pv/ai-v2-bcd-20261111/phase-c-executed-v2/<类型>/scenario-evidence.json`。这只重新核验证据，不会把原阻断结果变成有效候选。
7. 本地协议恢复使用相同canonical、workspace、`--run protocol-verified --request-id CH17-1 --model protocol-fixture-only --timeout-seconds 900`。实际执行回执包含完整参数。改变模型、规格、授权或scenario bundle须新建run；不手改旧cache hash。
8. 需要重新计算或重跑专项时，先为归档脚本指定新的输出根/运行名，保留180秒进程边界和失败回执。默认脚本拒绝已存在的输出，不能用删除旧证据来消除OUTPUT_EXISTS。
9. 正式模型任务另行使用真实宿主及实际模型标识；不得把协议响应的host_call_id改名后宣称真实调用。

## 卫生与发布门禁

3671个预先保护文件已逐一核对未改；两套原dist候选保留、Git忽略、ZIP/manifest/sidecar分别验证。没有删除受保护历史资产或其他产品；净删除0文件/0字节，不虚构释放空间。新增正式文件只含授权源码、测试和必要说明；本轮失败/成功运行证据按用户要求留在受控忽略目录。

最终Git清洁状态、文件/字节清单、受保护核验和最终源码hash见 `final-state.json`。无用跟踪生成物新增为0；旧候选有效性不代表2.0发布通过。最终判定仍是 **本轮部分成果保存与交付，完整任务未通过验收**。
