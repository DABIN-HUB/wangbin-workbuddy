# 本地 Skill 宿主试验：准备阶段与确认边界

状态：`H0_H1_PREPARED / CLIENT_CONFIRMATION_REQUIRED`。这是新验证路径的准备交接，不是上一轮真实宿主阻断已经解除。Phase D 仍为 `USER_REVIEW_REQUIRED`，不进入 Phase E。

## 范围和实际基线

- 用户依据：`Hermes_SolarPV_WorkBuddy_LocalSkill_RealModel_Test_20261112.md`，本轮仅授权既有合成资料与独立工作区。
- 实测基线：`main / 168aa93bbf1aff26d0e7a47257f2200853c5f4b1`，开始时暂存、已跟踪差异和未跟踪均为空。2026-11-12 实际 `ls-remote` 返回远端 main 为 `d6b4043e19d391ce6055747ef058e46af1ffd3c0`；未拉取、推送或改写历史。
- 原隔离工作树保留。旧恢复 ZIP 的 SHA-256 与用户给定值一致。
- 新证据根：`.runtime/solar-pv/workbuddy-local-skill-host-proof-20261112-185122/`。本文件之外的最终提交 SHA、文件库存与实际校验回执见该目录，不建立自引用提交。
- 规格有效 SHA：`59e379906f6b83d91a76179f14fdc00e5c0dc9346ef5d272bbcf04da90df7532`。实际 Catalog/Registry 重验为18章100小节、13附录26小节、469字段、89公式、281映射、189术语。

## 最小指引改动

只修改既有 `SKILL.md` 与 `references/host-orchestration.md`：将手动文件交接的宿主写作观察，与已安装解释器及工具授权必需的完整 CLI 路径分开。缺 Python/Connector 不再阻断前一条路径，但不降低事实槽、来源、Schema、请求有效期或专业审核要求。

未改 Python 生产代码、测试、模型 SDK、Connector、产品 ID/版本/工具白名单、冻结规格、canonical 或公式。没有新写或复制任何专业章节正文。未新增个人专家、正式 Expert 包或发布资产。

## 新候选

- 文件：`dist/wangbin-solar-pv-prestudy-0.1.3-local-skill-test-20261112-185122.zip`。
- SHA-256：`9745d7c634a2812f1a36c85d29ebb147af1650ce0519339aeecdc2287dcb981a`。
- 共21成员，单一 `wangbin-solar-pv-prestudy/` 根；含现有 SKILL、许可证、manifest、两个脚本、必需参考及冻结基线。排除缓存、虚拟环境、源码仓库、历史正文、request/response 和原始项目资料。
- 使用现有 `product_factory._files` 选取允许成员，沿用确定性 ZIP 布局；没有直接运行会写固定候选路径和 products/catalog.json 的 `package_product`。新路径独占创建，旧 dist 不覆盖，catalog 不变。
- ZIP CRC、精确成员集合、逐成员字节/哈希、解包后的 Skill 引用与脚本语法均实际验证。SHA 是完整性标识，不是发行者签名；候选未签名，未通过客户端解析或正式审核。
- **产品 ID 和版本未更改。文件名不同不保证已安装 Skill 可以并存。** 导入前先检查“已安装”；发现同名/同ID或替换提示时停止，不覆盖、不卸载，另请用户裁定。

## 双案请求

两案使用原始合成 canonical，未更改字节：

| 类型 | canonical SHA-256 |
|---|---|
| industrial_rooftop | b763dec6bd6d37cea78525c777ccfd8a4133a7a18b6c646385f329019671dca3 |
| utility_scale_ground | c83ae242bc864a6566c83a1b6b3851d33587ca4b9b2d3d51447315ebac73080b |

在各自新工作区通过现有公开 `wangbin_solar_pv.reporting.host_session prepare` 和 `checkpoint` 执行，四条命令退出均为0。两案同一 CH08 六节研究规范和请求配置、不同事实证据；五身份与原 canonical 一致；上游均如实标记未提供。当前没有 response/result/AI Word。

完整定位、请求文件 SHA、协议 request_hash、五身份、来源白名单、期限及退出码见 `two-project-requests.json`。准备命令明确使用开发解释器与受控源码路径，只证明请求制备，不当作用户安装、WorkBuddy Bash 或 Connector 运行证据。

本次模型选择尚未在客户端观察，准备配置显式为 `NOT_EXPOSED_BY_HOST`。开测前必须核对两个会话相同的实际模型及设置；若配置与准备时不同或请求过期，使用新run重新prepare，保留旧请求，不修改hash/期限，不拿旧输出改标。

## 依赖与失败记录

现有本地 Python 3.12.0 环境没有 `wangbin-solar-pv-input`，文档模块来自源码映射，不是已证明的固定 wheel 安装；Pillow 为13.0.0，不满足项目 `>=10,<13`，tzdata为2026.6而声明固定2026.5。新的独立安装尚未执行，需用户批准可信公开源或合法离线 wheelhouse；没有修改现有环境。

从新ZIP解包后，以现有 Python 3.12 在非源码目录、移除 PYTHONPATH/PYTHONHOME 并 `-I` 实际运行包装器 status：退出2，`INSTALLED_ENGINE_UNAVAILABLE_OR_INVALID_RESPONSE`。两个内部精确版本公开 PyPI 接口本次再次返回404。这不阻止先做手动 request 交接的宿主写作观察。

首次只读核验错误地用标准 JSON 浮点解析 canonical，被原校验拒绝 `EXACT_JSON_NUMBER_REQUIRED`；随后使用项目自身 `serialization.loads` 原精度解析，通过 Catalog/Registry/ReportModel 验证。原文件始终未变，失败回执保留。未新增或执行单元/集成测试，未将历史258项专项计入本轮；本轮为结构/语法校验和实际请求CLI执行。

## 官方依据与账号入口边界

查询日：2026-11-12。五页官方HTML/正文、访问时间/HTTP状态/哈希保存在 `h0/official-sources.json` 与相应文件。官方客户端文档中的16张原图另存 `h0/official-images/`，均标记为官方示意图，不是本账号的安装截图。

- Skill 本地导入及启用：`https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market`。文档入口是“专家·技能·连接器 → 技能 → 添加技能 → 上传技能”；自行上传不能用市场对话安装代替。
- 个人专家：`https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Expert-Center`。文档描述“专家 → 我的专家 → 创建专家”，与正式专家包上架区分；本账号入口、私有范围及实际关联Skill尚未观察。
- Skill 包结构：`https://open.workbuddy.cn/docs/skill`。
- 正式 Expert 结构/工具与依赖：`https://open.workbuddy.cn/docs/expert`。
- CLI runtime：`https://open.workbuddy.cn/docs/connector`。不由托管runtime文档推导Skill当前解释器已继承。

只读取客户端可执行文件公开版本元数据：WorkBuddy AI 5.5.2。没有启动或操作客户端，没有读取账号配置、Token、Cookie、模型配置文件或私有会话。

## 当前分项门禁

| 门禁 | 状态 |
|---|---|
| LOCAL_SKILL_ZIP_INTEGRITY | PASS，仅本地结构/字节完整性 |
| WORKBUDDY_SKILL_IMPORTED | NOT_RUN_PENDING_USER_CONFIRMATION |
| WORKBUDDY_HOST_MODEL_NEW_CH08_ROOFTOP | NOT_RUN，等待真实宿主 |
| WORKBUDDY_HOST_MODEL_NEW_CH08_GROUND | NOT_RUN，等待真实宿主 |
| WORKBUDDY_HOST_TOOL_EXECUTED | NOT_RUN |
| LOCAL_CH08_ACCEPT_RESUME_DOCX | BLOCKED，无真实输出且安装未闭合 |
| WORKBUDDY_PERSONAL_EXPERT_CREATED | NOT_RUN，需另外明确确认 |
| FORMAL_EXPERT_ZIP_INSTALLED | NOT_TESTED，不在本轮路径内 |
| CONNECTOR_DEPENDENCY_DISTRIBUTION | BLOCKED |
| SERVER_MODEL_ATTESTATION | UNVERIFIED |
| INDEPENDENT_QA_COMPLETE | NOT_RUN；未冒充wb-quality |
| PHASE_D_CONTENT_REVIEW | USER_REVIEW_REQUIRED |

CH10/16、终期现金、有效多候选排名、专业签审、正式四文件、PDF公式检索、全仓回归和发布门禁均不升级。

## 接续步骤

先请用户确认是否允许操作客户端并导入/启用此精确哈希候选；确认范围不包括替换已安装同ID产品、创建专家、公开上传/审核、购买服务或安装依赖。实际UI需保留脱敏截图和动作时间线；遇身份验证由用户在官方客户端完成。

确认后先记录可见版本、Skill冲突检查、所选模型与工具授权；必要时刷新两个请求。在两个独立新对话仅上传各自的新request，明确启用本Skill。仅由WorkBuddy模型产生原始章节JSON；模型写作、文件工具、CLI运行和Word分别判断。无工具时允许用户保存完整原回复，不伪造自动工具调用；出现完整上下文不可读、次数用尽或真实模型无输出时保留阻断。
