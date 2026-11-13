# CALC-PRIVATE-AUTH-2026-11-13：软件顾问计算器专项私有测试授权

## 来源、范围与优先级

项目所有者在 2026-11-13 的最新明确指令授权 Hermes 与既有 dots 团队，使用其 Windows 上已有 WorkBuddy 客户端及本人现有账号，私有导入、启用并测试 `wangbin-estimate-calculator`。仅服务 `product_id=wangbin-software-consultant` 的 `CALC-WORKBUDDY-552-E2E-01` 专项；原三卡为 `t_0ade4e96` → `t_4623929e` → `t_9e4a6ee3`，看板为 `wb-skill-factory`，不重建 T00–T05，不重置历史返工计数。

本记录是项目级专用例外，优先于团队根规则、三个角色模板、release-policy、skill-development 及产品旧规则/任务卡中的默认“禁止上传/安装、由用户本人操作”条款；不是全局解除禁令，也不覆盖真正的系统、平台或强制工具限制。旧运行上下文不能靠文件修改追溯改变，必须在无旧 Worker 的安全边界，通过同一既有角色的新运行重新读取并核实授权生效。禁止换 Bot 规避拒绝、读取隐藏系统提示、直接修改 Hermes 内部数据库、用任务措辞伪装上传。

## 唯一获准包与输入

- 首轮必须原样使用 `packages/experts/wangbin-software-consultant/experiments/decimal-poc/dist/wangbin-estimate-calculator-0.1.0-licensefix1.zip`。
- SHA-256：`56ca2fd8c5bd5abbb7a31f0163a4ef3293f6d6ecb8ed21a10f6d075a893fd9b6`。
- 根目录 `wangbin-estimate-calculator/` 下恰有四个文件：`SKILL.md`、`scripts/estimator.py`、`references/input-output-contract.md`、`LICENSE`。核对哈希、成员、CRC、许可证及来源后才私有导入；不得用旧三成员包、静默重打包或覆盖历史包。
- 只使用既有冻结 SYNTHETIC 样例与本专项必要反例。允许真实对话、获授权的本地 Python、受控文件读写、取证及逐样例 checkpoint。不改冻结 FRD、业务合同、历史测试记录或正式 Expert。
- 允许本机或本人账号内的私有导入、启用、测试；同一已授权导入不重复征求确认。先核已安装列表，遇同 ID 来源不明/替换/覆盖提示停止，不擅自卸载或覆盖。

## 不在授权内

公开上架、提交审核、扩大可见范围、付费购买、收费设置、其他产品、Expert ZIP 上传、部署、正式 P02 回归修复和 MES 均不获授权。真实登录、验证码或代理不能完成的权限动作仅交接该具体动作，其余已授权的包核验、只读版本检查、合同整理、QA 准备与看板细化继续。真正拒绝须保存动作、可见原因、来源类别和正规处理入口，不规避或伪造成功。

## 唯一目录、角色与恢复

- 产品源码只在 `F:/ideaWorkSpace/wangbin-workbuddy-software-consultant`，分支 `expert/software-consultant`；团队规则只在 `F:/ideaWorkSpace/wangbin-workbuddy-team`，分支 `team/skill-factory-v1`。不创建第二产品开发树。
- `wb-developer` 执行原 T02；`wb-quality` 仅在 T02 事实交接完成后独立审查，不代执行导入或伪造独立结果；`wb-manager` 在 QA 后专项收口，不实现业务代码。规则例外必须接入上述角色的公开 SOUL 启动配置；旧会话停止对本专项派单，新运行先记录授权 ID、规则提交/blob/字节哈希、产品 HEAD、候选 SHA、实际 profile/task/run/session 身份。
- 先回读原卡、实际幂等键、依赖、attempt 和事件；原位更新目标、精确输入、允许路径、步骤、断言、依赖、停止条件、交付位置。保留历史 BLOCKED。仅在权限恢复和前置条件满足后原生 unblock 原 T02，观察 Dispatcher 真实 claim/spawn/worker_bound 及新运行读取证据，不能以配置代替启动。
- 原卡宿主时限按实际耗时评估，不机械套 30 分钟；保留有限重试和旧返工记录。每案完成立即保存原件/hash/verdict 与 checkpoint，读取 checkpoint 校验完整性后只续未完成项；未知提交状态先只读查证，不重复导入，不拼接不同 S30 会话。登录/权限阻断只 native block 受影响卡，不以新卡重置预算。
- P02 `t_e6210c95` 可补缺陷证据与下一轮准备，但不因计算器成功改 PASS；MES `t_2affd306` 继续仅依赖正式 P02，不启动、不绕过。

## Git 与证据边界

仅必要授权/调度文档可分别在上述两分支精确暂存、检查、普通 commit/push，并读回对应 origin 精确分支完整 SHA；无变更不空提交。不夹带他人修改，不跨分支混推，不 force push、merge、rebase、amend、reset --hard。运行配置、账号信息和原始证据不得随源码推送。

私有原件、授权及任务恢复记录保存在既有交付区 `F:/ideaWorkSpace/wangbin-workbuddy-delivery/experts/wangbin-software-consultant/calc-workbuddy-552-e2e-01/`。凭据/个人账号信息报告中用 `[REDACTED]`。明确区分 ZIP 核验、授权写入、Worker 领取、客户端版本、私有安装、启用、真实对话、工具调用、数值/范围版本、独立 QA、正式 Expert 集成及发布门禁；没有实际证据一律 NOT_TESTED/NOT_VERIFIED/BLOCKED，不互相冒充。
