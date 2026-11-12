# WorkBuddy 原生宿主兼容性（H0）

核查日：2026-11-12；产品 `wangbin-solar-pv-prestudy`，冻结2.0，不代表发布。

## 现场

- main：`d6b4043e19d391ce6055747ef058e46af1ffd3c0`；初始工作区与暂存区干净，与上轮审计HEAD无差异。
- 初次 `ls-remote` 35秒超时；禁交互、有界重试取得远端main同一SHA。未同步Git。
- 本机卸载注册项与 `D:/ProgramFiles/WorkBuddyAI/WorkBuddyAI.exe` 文件版本均为5.5.2；没有观察到活动WorkBuddy进程。**客户端已安装，不等于光伏Expert/Skill/Connector已经安装或获得测试授权。** 未读取Token/Cookie/models.json/私有会话，未启动、安装或上传资产。
- 当前包源：官方PyPI两个精确版本 `wangbin-solar-pv-input/0.3.1`、`wangbin-document-cli/1.2.0` JSON接口均HTTP404；没有用户授权私有索引。只证明公开版本不可取得，不能断言所有私有索引均无包。`DEPENDENCY_DISTRIBUTION_BLOCKED`。
- 当前仓库没有光伏Expert定义；既有Skill仅路由旧report/ground-report，不能宣称AI2.0原生生成。Connector已有Python runtime及init/status，但缺文档必填unAuth。

## 官方依据与裁定

以下页面本轮均实际HTTP200，原文文本、读取时间、HTML/text SHA在 `.runtime/solar-pv/ai-v2-host-20261112-144349/h0/official-sources.json`。行号指该目录相应txt，不是动态网页行号。

| 项 | 官方URL / 段落 | 文档裁定 | 本机/运行裁定 |
|---|---|---|---|
| A Expert | https://open.workbuddy.cn/docs/expert — Agent定义/字段/工具；txt209–281 | 支持角色正文、skills预加载；maxTurns默认50。禁止自加tools，工具由系统分配 | DOCUMENTED_SUPPORTED；尚未验证本产品实际权限 |
| B Skill | https://open.workbuddy.cn/docs/skill — 目录/SKILL.md | 支持references/scripts及宿主工具流程 | DOCUMENTED_SUPPORTED；allowed-tools不是已授权证明 |
| C 依赖 | expert — 内置MCP与连接器依赖；txt290–312 | dependencies.connectors引用平台已有ID；MCP配置独立 | DOCUMENTED_SUPPORTED；本地connector目录名不自动成为平台ID，解析未验 |
| D CLI | https://open.workbuddy.cn/docs/connector — CLI字段；txt1716–1789 | MCP或CLI二选一；Python托管需5.0.0；auth可选，unAuth必填 | 本机版本满足文档最低值；无凭据CLI不伪造登录，当前缺unAuth需修。真实连接RUNTIME_BLOCKED |
| E 分发 | connector — 托管运行时与安装位置；本地cli.json | 平台托管环境不保证内部wheel存在 | 两固定包公开版本404，无批准索引；RUNTIME_BLOCKED |
| F 其他API | https://open.workbuddy.cn/docs/openapi — 准备工作；https://open.workbuddy.cn/docs/third-party-app — 应用注册与授权 | 开放API有第三方应用注册、OAuth等独立前提，不能等同普通Expert内部模型SDK | REQUIRES_APPROVAL；本轮不使用。企业托管/计费具体权限UNKNOWN，不猜测免费可用 |
| G 资源限制 | expert maxTurns；connector托管运行时说明 | 轮数配置与脚本/模型时间、上下文、费用不是同一限制 | 真实宿主token/费用/签名调用ID/模型超时NOT_EXPOSED或UNKNOWN，未经试验不宣称强制 |
| H 真实性与数据 | https://open.workbuddy.cn/docs/developer-agreement — 2.3、2.7、2.8 | 应披露必要依赖、限制和费用，不伪造功能/回执，不秘密读凭据或外发资料 | 本轮只处理授权合成资料，未开新服务/账号/付费Provider |

## H0决策门

原生宿主Read请求、进行研究、Write输出、Bash执行校验的组合有文档依据；**不是Python内部LLM API**。未发现必须改财务方法或另购Provider才能编制本地候选的依据。因此允许H1/H2本地最小整改；H3真实宿主不能因本机安装了5.5.2就PASS。

平台私有安装/上传没有本轮授权，且未取得已安装光伏专家的可观察证据；分发和连接链也未闭合。实际平台解析、召唤、权限提示、双案CH08新内容及中断恢复均须保持阻断。若需要这些动作，先取得具体私有测试授权，不转用公开发布或另一个模型服务。

这份文档只作工程兼容性核验，不构成法律意见或正式平台认证。六章旧稿、审计ZIP及R13仅为保护/对照资产，不能作为新宿主写作输入。
