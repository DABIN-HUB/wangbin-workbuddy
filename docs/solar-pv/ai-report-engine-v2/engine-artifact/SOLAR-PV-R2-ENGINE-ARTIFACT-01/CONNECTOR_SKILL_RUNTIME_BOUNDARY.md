# Connector / Skill / engine 的实际边界

**本轮只改engine分发版本；Connector、Skill、已安装资产全部只读。** 不是Skill包，也不触发安装/替换。

## 当前源码路径

| 层 | 可核实事实 | 不代表 |
|---|---|---|
| 新engine wheel | 0.3.2；含新host_input_view/chapter_writer/host_session/host_output及正式specs原字节 | 依赖已闭合/已安装 |
| cli.json | Connector0.1.2，minWorkbuddyVersion5.0.0，runtime python3.12；darwin/linux/win32三个init仍固定solar0.3.1 | 自动指向本轮wheel |
| init依赖 | 三OS均显式tzdata==2026.5、markitdown[pdf,docx,xlsx,pptx]==0.1.9；无完整传递hash lock | --only-binary等于来源/完整性锁 |
| ready/status | auth/status均运行reporting.connector_runtime ready；statusMatch为^LOCAL_READY$ | 外部服务连接或普通Skill可运行 |
| engine内部ready | reporting/connector_runtime.py仍要求solar0.3.1 | 安装0.3.2就会READY |
| input_module_version | __init__.__version__0.3.0被intake输出；与分发版本不同，保持原合同 | 应顺便改成0.3.2 |
| Skill wrapper | standalone资产/依赖说明、run_ai_chapter路由、外置baseline-dir链原样保留 | ZIP含engine或已安装依赖 |
| ordinary Skill Bash | 与Connector Python身份未建立实际绑定 | 托管环境自动共享 |

Connector/Skill逐件source SHA、三个init原命令、auth/unAuth/status及timezone真实边，完整见RUN/analyst/connector-skill-runtime-boundary.json。engine内ready静态入口见冻结source与WHEEL_CONTENT_MANIFEST；没有执行ready或返回LOCAL_READY。

solar的direct tzdata仅win32，而现有init在三个OS都固定它。非Windows实际观察传递链为markitdown[xlsx]→pandas3.1.1→python-dateutil4.0.0→tzdata；不能只看solar direct marker就删其他平台tzdata。

## 官方能力与现场证据

官方Connector文档声明Python runtime版本字段起点5.0.0，WorkBuddy准备托管运行时；英文文档描述managed virtualenv与pip cache隔离。[1][2] 官方Skill结构列出必需SKILL.md与可选scripts。[3] 不能由Skill脚本/资产声明推断它实际使用Connector环境。

| 项目 | 本轮判定 |
|---|---|
| CLI托管Python设计能力 | DOCUMENTED；不等于5.5.2实部署 |
| 当前客户端托管exe/patch/依赖 | NOT_TESTED |
| ordinary Skill Bash与Connector同解释器 | UNKNOWN_NOT_TESTED |
| OS沙箱、CPU/内存cap | UNKNOWN；venv不是OS沙箱 |
| 业务timeout/进程树清理 | UNKNOWN；生命周期timeout表不外推 |
| 实际安装/卸载清理 | NOT_TESTED |
| publisher/private-test权限 | UNKNOWN_NOT_INSPECTED |
| source/installation/download产物交付 | 只核对本地字节；无平台运行 |

## 未来最小方案（未批准、未应用）

1. 先由独立QA核对最终source+wheel+payload；再另批真实可信不可变分发源、42第三方wheel、target-specific完整传递version+SHA锁及license/notice审查。不得使用开发机路径、假公共URL或仅文件名固定作为解决方案。
2. 另批将三个Connector init的solar固定版本与已批准新构件对齐；同时审查engine内部ready的0.3.1固定检查及其契约。不能只改init就宣称READY，也不能借本次版本号变更修改运行协议。
3. 同一另批任务同步Connector README、Skill依赖说明与必要发布元数据；复核非Windows tzdata实际完整链。保留input_module_version原有意义，除非另有批准的合同迁移。
4. 只有获授权才在新隔离环境装明确构件并核查真实exe/依赖/业务入口；随后独立证明Skill Bash到Connector环境的绑定。禁止PYTHONPATH伪装、安装到现有venv或不明rollback。
5. 只有明确私有平台入口与独立授权后，才进行客户端安装/真实对话/输出下载重开；正式审核、发布、替换已安装21成员Skill和Phase E/F/G仍禁行。

本轮没有apply上述方案。旧R2 Skill导入PASS保持；屋顶BLOCKED_NO_DRAFT、地面NOT_TESTED_BLOCKED_BY_STOP_GATE、两案Schema/strict NOT_TESTED_NO_DRAFT、E2E/专业/财务/PDF/正式四文件/发布等门禁不变。

## Sources

[1] https://open.workbuddy.cn/docs/connector — official-connector-zh
[2] https://open.workbuddy.cn/en/docs/connector — official-connector-en
[3] https://open.workbuddy.cn/docs/skill — official-skill-zh
