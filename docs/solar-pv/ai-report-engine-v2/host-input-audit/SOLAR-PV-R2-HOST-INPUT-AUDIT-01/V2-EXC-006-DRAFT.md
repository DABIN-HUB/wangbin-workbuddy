# V2-EXC-006-DRAFT — 整章宿主输入视图与原请求绑定

状态：**PROPOSED_NOT_APPROVED**。仅审批草案，**未应用任何生产补丁**。所属版本 `SOLAR-PV-AI-REPORT-ENGINE-2.0.0`，不解锁 Phase E/F/G、CH10/16 或发布。编号按当前 `ai-report-engine-v2` 中已有 EXC001–005 后下一可用编号；EXC002 的冻结文字保留，不重编号历史。

## 1. 缺口与推荐

同一事实血缘五身份、数组周期/来源与专业任务有大量重复表示。当前真实请求已低于原 2MiB 限制，继续放大本地预算没有依据。旧现场只见输入未完整可用、上下文压缩及宿主自述敏感返回，后台原因 UNKNOWN。

**建议审批主方案：透明的整章共享对象视图**，完全相同的对象/数组共享一次，其余仍保留原 JSON 字段。实测屋顶 228621 B、地面 229291 B（含实验封套与末尾 LF），较原件减少 33.3501%/33.3270%。每个共享点保留原 JSON pointer、索引、理由；原ID、事实/Schema/六节研究任务不删除。

**独立更小备选：类型化事实行表示**，实测 143143/143289 B，减少 58.2695%/58.3346%。完整列名用字段路径，明确类型；组内常量在列头明示，变量逐行保留，缺失字段按不同形状分组，数组不重排。该方案需要额外阅读映射能力验证，不能仅因更小就认定模型能正确研究，因此本草案不自动把它升级为主路径。

两种表示均 NOT_FOR_HOST / NOT_AI / PROPOSED，只在本地运行，不发送宿主，不以改名、编码、移动受阻片段规避防护。不创建小节调用、摘要事实、隐藏二进制、base64 或新恢复协议。若官方证据不能确认透明输入通道可用，继续停在输入审计结果；不自行重投。

## 2. 拟改真实生产接口（全部待批）

路径均以仓库根为准；当前签名/行号由 runtime `exact-original-verification.json#/source_symbols` 验证。新名字在下表明确标“拟新增”，不能当已有能力。

| 文件/当前真实符号 | 待批最小接口变化 | 不允许变化 |
|---|---|---|
| `services/solar-pv-engine/src/wangbin_solar_pv/reporting/chapter_writer.py`：`prepare(..., *, host_delivery=None)`、`_request`、`accept`、`resume` | `prepare` 拟加显式可选 input-view policy；只影响新 run/request。新请求先绑定版本/映射/模式 policy，再计算 request_hash；后生成独立 view 及 manifest。`_request` 对选择新 policy 的请求重建原 pack、验证派生视图/manifest；accept/resume 不得绕过。 | 不改既有请求、hash、expires_at、配置、canonical 或 validator；默认 None 仍走原协议。 |
| `.../reporting/host_session.py`：`open_session`、`execute`、`checkpoint`、`main` | 拟增独立 opt-in 新准备动作/参数，进入原 host-operation 锁；授权 binding 加 view policy，checkpoint 检验新 manifest 身份。旧 prepare/prepare-r2 不被静默升级。 | CH08 gate、取消、来源授权、预算预留、provenance 与无 draft 停止门不放松。 |
| `.../reporting/host_output.py`：`publish_response`、`verify_publication`、`_intent`、`_receipt` | 只对新 policy 请求额外验证原请求—view manifest 的固定绑定；发布回执可选记录 view_hash/decoder/version 作为输入呈现溯源。仍验证原四键 draft 和原严格 output。 | 不为旧请求补回执、不改正文、claim、source、数字槽或 Schema，不把视图 hash 当模型读取认证。 |
| `.../reporting/llm_provider.py`：`ModelConfig.to_dict()` | **建议不改数值配置**；保留现有所有上限。新视图先受原完整请求预算检查，再检查自身不超过同一请求字节限制；不能用视图更小绕过原证据预算。 | max_request_bytes、max_output_bytes、timeout_seconds、max_attempts_per_chapter、max_requests 全不加大。 |
| `.../reporting/evidence_pack_builder.py`：`build_pack()` | **建议不改**事实生产/来源选择。拟新增的表示层纯函数只能消费已经构建验证的整章 request/pack；源数据所有者仍是现有 build_pack。 | 禁止把授权来源池扩为节级来源，不能只因共享而丢定位/状态/期间/单位/许可/缺证。 |
| 拟新增 `.../reporting/host_input_view.py`（当前不存在） | 待审批的纯表示模块，拟接口 `build_view(request_bytes, mode)`、`decode_view(view, trusted_request_bytes)`；正式实现必须复核这次标准库原型，不直接复制为生产补丁。 | 不执行来源中的命令；不生成报告正文、计算事实或读取任意路径。 |
| `packages/skills/wangbin-solar-pv-prestudy/SKILL.md`、`references/host-orchestration.md`、`scripts/run_ai_chapter.py:main()` | 仅待批准的新 Skill 候选中增加明确 opt-in view 的阅读/停止边界及 wrapper 参数透传；仍使用已安装隔离引擎。正式输出使用原 fact/source/formula ID。 | 本轮不重打/替换 Skill、不安装引擎；不能让模型写 manifest 或自行选择不受信 decoder。 |
| `packages/connectors/wangbin-solar-pv-cli/cli.json`、`connector-meta.json`；`.../reporting/connector_runtime.py:main()` | 分发任务另批：绑定唯一受信 R2 wheel 及 SHA，明确 readiness 对必要 R2 模块/入口的验证，不仅同版本协议字符串。 | 不声称 Skill Bash 与 Connector 共用解释器；不将本次本地审计当安装或 init 成功。 |

## 3. 哈希设计：避免循环与冒用

- 原证据真源永远是不可变原 request + canonical/授权/规格；原五身份、evidence_hash、dependency_hash 不改变。
- **不采用** request 包含 view_hash、view 又包含 request_hash 的循环定义。
- 拟议新请求仅包含确定的 view policy（表示版本、mapping 版本、mode），其后计算一次 request_hash。视图封套绑定 request_hash/file_sha256、五身份、规格、证据、generation_run_id、request_id、model_id、expires_at；`view_hash` 对除自身外的完整封套做精确规范序列化 SHA。
- detached manifest 在同一授权 run 中独占创建，绑定两份文件 SHA、view_hash、request_hash、版本/映射/policy。manifest 不回写原 request，不自含自己的 SHA。
- 请求/证据/授权/model/规格/上游/policy/映射变化必须新 run，不能复用旧视图、publication 或 cache。将旧视图重新算 hash 也不能冒用新原件，因为 decoder 还需可信原件精确树比较。
- 恢复只读重建并比对派生物。缺 manifest/视图、未知版本、未知键、重复/悬空/循环索引、错误列、跨节授权变化、任何事实状态/表行/风险/Schema 损失一律失败。不要自动补字段或降级原模式。
- 保留原取消检查和预算预留；派生文件写入崩溃按既有预留/中断状态显式报告。只有相同原请求、相同确定派生字节的 no-clobber 幂等恢复可另行设计并测试；**本轮不实现新恢复机制**。
- 原模型响应四键和 `chapter-result/2.0` 不变。来源共享索引/列号不是新的正式 ID；专业、平台、调用认证都不升级。

## 4. 待批验收要求

1. 独立 QA 已完成冻结作者快照的测量、可逆性与当前双案权限另查，**总裁定 PARTIAL**；原文见 QA_INDEX.md。QA-F01/F02仅由 developer 实施文档边界/共享隐私整改，不是 quality 重新验收。审计脚本和实验快照不改；未来生产验收仍须独立执行。
2. 生产专项后续另批：兼容旧 prepare/prepare-r2 与历史请求；新模式授权、两案、错身份/旧视图、取消/并发/no-clobber/崩溃、unknown key、引用/列映射、原 request 与 view 双预算、期限和缓存失效。严格 validator/risk_assertions 原规则不得削弱。
3. 全部用户列举负例已在离线原型覆盖：删事实/少来源/换状态/数字单位期间/错项目/跨节/重复悬空索引/缺表行/未知键/篡改/错误版本映射/风险不足/旧视图冒用；其中无风险覆盖明确返回 COVERAGE_INSUFFICIENT，不伪装专业审核。
4. 独立证明受信 wheel、依赖、普通 Skill Bash/Connector 的各自环境；当前旧 wheel 不含 R2，文档/版本名不替代实物。
5. 用户分别批准生产接口、依赖安装、精确 Skill 替换、一次新 CH08 宿主试验；保留官方支持安全边界与停止门。若原敏感返回重现，保存证据即停止，不用备选模式自动重试绕过。

补充权限验收边界：原型 `closure()` 只是部分引用一致性 helper，不能独立识别 UNKNOWN metric/claim、duplicate source 或同来源跨节事实，不能将其 VALID 标签当完整授权 PASS。当前两案权限有独立 QA 另查；decoder 依赖受信原件全树精确比较拒绝被重seal的篡改。未来拟议生产接口必须另验完整 metric/claim/source 唯一性与节级事实权限，不能直接照搬 helper 作为完整权限门禁。本轮不应用这一生产补丁。

## 5. 不解决事项与审批问题

不解决 provider 错误根因、模型实际 token/上下文完整持有、专业因果/工程批准、真实资料、候选终期现金/有效排名、基准付款/会计经营股东口径、PDF 公式复制搜索、正式四文件、全仓回归、Expert 安装或平台发布。财务缺口仍是 2.0 未闭合需求，不移入 AFTER_V2。

需要用户决定：是否批准主方案接口范围；是否允许将类型化行作为后续独立阅读能力验证备选；何人提供并批准唯一 wheel 与依赖；官方询证/必要脱敏日志范围；满足这些条件后是否批准一案一次新 CH08 试验。当前**没有执行任何一项**。
