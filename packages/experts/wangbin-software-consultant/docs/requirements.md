# 软件需求与报价专家｜FRD-1.0 需求工程映射

> 产品类型 Expert；产品 ID `wangbin-software-consultant`；外显名「软件需求与报价专家」；唯一工作树 `F:/ideaWorkSpace/wangbin-workbuddy-software-consultant`；分支 `expert/software-consultant`；T01 基线 `67d0fe8cfa5d71b53cc46d79bbaec620638dd1e0`。本文是冻结要求的实施映射，**不改写 FRD**。逐 ID 机器矩阵见 [`traceability.csv`](traceability.csv)，输入输出见 [`input-output-contract.md`](input-output-contract.md)，86 条案例见 [`acceptance-cases.md`](acceptance-cases.md)。所有实施/独立模型 QA 当前 `PENDING`，平台能力未验证。

## 权威来源与读入顺序

1. 团队 `F:/ideaWorkSpace/wangbin-workbuddy-team/agent.md`（全文 129 行）→ `team/workflows/skill-development.md`（全文 30 行）→ `team/policies/git-policy.md`（全文 17 行）和 `workspace-policy.md`（全文 3 行）；团队本地 HEAD/精确远端 `6f6040e879be57d5de008d5a410e63c5d50edb79`，前两文件已提交 blob 分别 `53901555742563bb843b94546edda429e029c2bc` / `737925a31da9ae5c92090d13b7607cfc0dea9236`，工作树 SHA-256 分别 `67b77d2cdadd80e93386325171e2a9eae16169efe87e3c4186f9ea3825a4b72b` / `5390c3ee68df2ee6cd925705f71fdcbe34be1d42ddad690e258ed3eec6019a75`。
2. 产品唯一工作树根 `AGENTS.md`（12 行）→ `agent.md`（136 行）→ `docs/development-task-template.md`（35 行）：均存在且全文读取。根旧模板默认禁推，与本轮用户明确允许当前独立产品分支在安全核验后普通 push 不同；分析师仍**无 commit/push 权限**，由授权开发/质量角色执行。主仓仅用于 Git worktree 登记；受保护 `wangbin-workbuddy-dev` 业务内容未读。
3. 冻结原文 `F:/ideaWorkSpace/wangbin-workbuddy-delivery/experts/wangbin-software-consultant/WorkBuddy-Expert-FRD-v1.0.md`，FRD-1.0，1396 行、139382 字节、SHA-256 `bf1821da43f23e372d8782775617054d39163ac630be3f40c11f4a429cbb682d`；执行补充 `C:/Users/wangbin/AppData/Local/hermes/profiles/wb-manager/attachments/pasted_content_2026-11-09_08-44-26-065_abcc06.txt`，1215 行，SHA-256 `59e9071aa74521d43f05aca67fca27c168db827d39434ad9aed1a65237b02497`。原 `agents/wangbin-software-consultant.md`、`tests/scenarios.json`、`tests/test_expert_candidate.py` 和 `reports/phase5-software-consultant.md` 全文读取；T00 原始 Kanban handoff `t_0be91674` 已核对实时基线。

## 现有产品与独立业务价值（先差异、后实现）

| 既有 1.0.0 行为/证据 | FRD-1.0 增量及独立价值 | 防回归/验收 |
|---|---|---|
| 纯对话中文咨询；四态；每轮最多三问；用户只要报价/文档先交付 | 会话内项目版本、需求↔页面↔表↔API↔WBS↔测试↔成本可追踪；指定十四类任一成果且变更传播 | S02/S12/S13/S14/S27/S28/S30；N-X-07；不可声称跨会话自动记忆 |
| MVP/标准/完整；模块人天、缓冲、未知第三方费用；单体/分布式条件判断 | 成品 SaaS/开源二开/定制三路径及三年 TCO；细分功能点×真实角色、前后端分列、报价新参数；不同范围不按比例放大 | S10/S17/S23/S29/S31/S32；N-X-11/12；不得重复计价 |
| ERP/MES 等场景关键词、概略功能表；32 条旧场景仅静态数据收集 | 七领域各十二环节的流程异常/页面规格/数据关系/接口/角色任务/资源/上线验收；工业 MES 与遥测及 AI 与 SaaS 分层 | 七域 42 新案及 12 跨域案；以相同输入、统一五维标准对比旧版和通用 AI，不靠名字/提示词更长声称差异 |
| 1.0.0 `plugin.json` / Agent/头像/README/LICENSE/场景/测试七项资产；旧校验器 prompt-only，旧打包器固定五成员 | 一个原生 Expert，领域规则/模板需要验证**实际**加载和打包；不得直接假定 skills/相对引用可用 | 旧 32 不删；静态、确定性、真实模型、WorkBuddy 分层；正式文件下载需实际打开验证 |

旧静态测试 `test_expert_candidate.py` 共收集 36 项（其中 32 项只检查场景数据，不验证模型回复）；历史报告站外模拟 9 案、S12 有条件通过，不能继承为当前模型 PASS。历史报告声称旧 ZIP 四成员与旧 packager 五成员矛盾；报告 SHA `4813386b...` 与 catalog SHA `577f3089...` 不一致，当前唯一工作树缺实际旧 ZIP/sidecar/manifest，均待后续来源/复建核验。官方公开规范仅能支持配置格式参考，不证明本账号加载、工具权限或下载能力。

## 完整性与实施路由

矩阵覆盖 G-01~13（13）、S-01~08（8）、L-01~12（12）、D01~D07 各01~10（70）、E-01~10（10）、O-01~14（14）、A-01~09（9）、Q-01~12（12）、P-00~06（7）；各行有原文来源、具体工作包/职责、验收案例、待补证据、状态，开发不得将 PENDING 改成不在范围。P-00 基线→P-01 通用/选型/生命周期→P-02 ERP/OA/CRM→P-03 MES/IoT/WMS→P-04 电商/AI SaaS→P-05 工程/14 成果→P-06 独立 QA/包/Git。映射矩阵的 `implementation_task` 使用 FRD 的 `Pxx-Txx` 子任务 ID，不把 Kanban 卡号当业务实现证据；下游按实际卡对应填入精确结果。

## 七领域 × 十二环节覆盖

每域 `Dxx-01` 立项/调研/三路径，`02` 角色/流程/异常，`03` 模块/验收，`04` 页面/原型评审，`05` 实体/关系/事务/DDL，`06` API/技术/集成，`07` 前后端/专项/QA 的 WBS，`08` 容量/资源/部署，`09` 领域测试/上线/验收，`10` L01~L12 的逐域完整映射。七域各自的 `Dxx-10` 原文须保留全部十二项，不把 `-10` 的一句话当作行为测试通过。

| 领域 | 主流程与核心反例 | 页面/数据/API/任务/资源/上线重点 | 主要验收 |
|---|---|---|---|
| D01 ERP | P2P/O2C/库存/往来；部分收货、重复发货、并发扣减 | 单据/库台账与余额/财务边界；期初核对 | N-ERP-01~06 |
| D02 OA/BPM | 分支/会签/代理/离职/旧实例 | 表单/引擎表分离、流程版本和待办审计 | N-OA-01~06 |
| D03 CRM | 线索→客户→商机→报价/合同/售后；查重和交接 | 客户 360°、阶段历史/归属、ERP 订单边界 | N-CRM-01~06 |
| D04 MES/IoT | 工单质检追溯 vs 设备点值；离线/坏质量/关联歧义 | 工位/遥测时序、OT 安全与真实现场验证 | N-MES-01~06 |
| D05 WMS | 收货上架拣货复核；错扫/冻结/弱网 | Web/PDA、库存流水与 ERP 主责、设备采购 | N-WMS-01~06 |
| D06 电商 | 展示/预约/交易按需；重复回调和退款 | 客户端与商家双端、支付可信证据/资质 | N-ECOM-01~06 |
| D07 AI/SaaS | AI 与 SaaS 独立；无授权资料/租户越权 | 引用/检索、用量计费、隔离/成本/限额 | N-AI-01~06 |

## 范围和独立门禁

Expert 交付的是咨询、规格和计划，不是七套真实系统、可执行 SQL、实际部署或设备写控。未获核实的价格、许可证、软件能力、用户事实、平台能力均标待核；没有实际 Office/图输出工具时保留完整 Markdown，文件型能力 `BLOCKED`，平台运行 `NOT_TESTED`。不增加后台服务、其他行业或其他产品。需求变更需用户明确批准；已批准的本轮实施授权和报价参数见执行补充，不是重定义 FRD。发布及 WorkBuddy 上传只能用户本人操作。
