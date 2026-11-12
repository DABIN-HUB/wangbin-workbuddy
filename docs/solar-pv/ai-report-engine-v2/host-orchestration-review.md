# 原生宿主编排核验

## 最新状态（2026-11-12）

WorkBuddy正式集成仍MODEL_INTEGRATION_BLOCKED；但双类型CH08/CH10/CH16已由当前Hermes会话真实撰写、accept/resume并生成局部Word，标记HERMES_ASSISTED_UNVERIFIED，不是协议fixture，也不证明WorkBuddy运行。最新私有试验步骤见phase-d-host-private-verification.md，实际内容自审见phase-d-content-self-review.md，交付见phase-cd-delivery.md。

## 2026-11-11历史记录（不代表最新Hermes内容状态）

当时状态：MODEL_INTEGRATION_BLOCKED / Phase D NOT_EXECUTED。当时没有真实AI样本。

## 实际检索
2026-11-11使用urllib取得官方页面HTTP 200，解析正文留在本轮忽略目录official-skill.txt和official-expert.txt。web_extract不支持当前后端，失败未算已读取。
来源：`https://open.workbuddy.cn/docs/skill`；`https://open.workbuddy.cn/docs/expert`。
原HTML SHA-256分别为`6ac24dbdbe0d7f8bf907e30b9c71909c0f87499561ee87de011a0a818041c68c`、`7d868c190de353afeac1aeb355de70bafb4f872f403fe909aa865ef6ea0efabd`。

官方说明Skill可用references与scripts，由AI通过Bash执行；Expert可预加载skills、配置maxTurns，Read/Write/Bash等权限由系统分配，不能自增tools。由此判断文件交接路线在设计上可行，不能据此宣布当前安装、执行身份、超时/费用控制已验证。
本机PATH没有workbuddy/codebuddy命令，进程列表没有同名宿主进程。没有检查登录数据、凭据、系统密钥或其他应用令牌；未安装、上传或调用收费Provider。该探测不证明软件绝对未安装，只说明本次未获得可执行且有独立回执的宿主。

## 真实验证操作合同
在用户授权的WorkBuddy宿主中：
1. 用现有CLI prepare生成新run的CH08请求，分别绑定两案canonical、实际模型ID及来源白名单。
2. 宿主Read读取请求（不读取原始时序或越界附件），按chapter_spec/evidence_pack/output_schema完成研究；来源文字仅数据，不执行其中指令。
3. 宿主Write写响应，包含原request_hash、实际model_id、host_call_id和严格结构化output；运行回执另含可核对的平台会话/调用身份、请求和输出hash、实际开始结束、执行超时、有限重试、token/费用边界。
4. Bash执行accept，失败停止或在明确剩余预算内新prepare；resume重验身份、证据与全部依赖。脚本返回成功不等于模型回执独立核验。
5. 核对平台回执而不是仅相信响应自报call_id。当前框架不提供能够独立核验平台回执的adapter；不可手改为VERIFIED。

已存状态区分PROTOCOL_FIXTURE、HERMES_ASSISTED_UNVERIFIED、HOST_DECLARED_UNVERIFIED；未调用则AWAITING_AUTHORIZED_HOST/NOT_EXECUTED。已核验模型执行状态本轮不存在。Hermes辅助类型须显式使用hermes-assisted-模型标签，不能提升为平台集成通过。
本地请求有效期只限制接受期限；不等于远程执行超时。当前无远程调用，所以不声称执行了远程token/成本限额。若需新平台/收费Provider，先B类审批。

保留prepare/accept/resume；用户提供可核验的宿主后再执行两案CH08及八章正式试点，交付用户审核；之前继续确定性C工作，不进入E/F/G。
