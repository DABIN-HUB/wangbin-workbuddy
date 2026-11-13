# SOURCE/REVIEW ONLY — 非 Skill 安装包

## 本地成果与精确接口

这是批准的EXC006共享对象子集，不批准整份历史草案；旧EXC006仍PROPOSED_NOT_APPROVED且不改。实现/测试候选a7dbe7cbf4e289f361f9e2ae03229ad873bcc52d，八文件原字节集合SHA256 `3b41751eb36a632e38c0aab123e25eb66a271e84d2de1ee42d0b06a5f92993c4`。后续提交只有本轮交付文档，不改变被审生产/测试。最终HEAD/完整保护及ZIP身份外置于RUN/final-state.json和RUN/final-delivery.json，避免自引用。

- CLI：`python -m wangbin_solar_pv.reporting.host_session prepare-r2-shared --workspace <授权根> --grant <新授权.json> --run <全新run>`。仓库Skill wrapper对应 `python scripts/run_ai_chapter.py prepare-r2-shared ...`，仅源码候选，现已安装Skill未改变，不是本轮执行客户端的授权。
- 新授权严格扩展键：`input_view_policy = {"mode":"shared-objects","version":"host-input-shared/1","mapping":"flat-exact-containers/1"}`。只有旧完整required keys或旧required+该精确policy组合；未知键/值拒绝。同一run不改模式。
- `chapter_writer.prepare(..., *, host_delivery=None, input_view_policy=None)`；默认None不改变旧字段/request_hash。新模式需原R2 delivery；真正授信仍经native open_session/canonical/grant/规格/模型验证。
- 纯表示API：`build_view(request_bytes)`、`decode_view(view, trusted_request_bytes)`、`expand(view)`、`manifest(request_bytes, view)`；文件API `create_files(store, request, max_request_bytes)`、`verify_files(store, request, max_request_bytes=None)`。expand单独不证明权限；生产入口使用重建原pack后的公共_request/verify_files，不能相信模型交来的原件路径或自报hash。
- 文件为同run `<request_id>-input-view.json`、`<request_id>-input-manifest.json`；宿主完整读取input_view_file（已含570 B reading），manifest是程序验证材料，不要求模型读取。原四键draft和严格章节Schema、事实槽/claims/风险规则不变。

完整阅读语法、绑定顺序和资源边界见PROTOCOL；不支持任意JSON空白/转义形式，支持引擎确定序列和两个冻结历史请求的原字节含LF。平坦共享池无链式引用；数字以显式$number保留词法；不是压缩/隐藏内容或按节模型调用。原request仍先受原预算，视图阅读封套按实际UTF8含LF计量，不把模型输入变小当成本/容量或安全返回证明。

## 真实验证和剩余边界

- 独立R1：134不同pytest用例和保存的边界诊断；R2：两条正式过期用例首跑通过；manager按四件JUnit去重为136个通过身份。不是一次全跑136、全仓回归、安装验证或新章节通过数。两案正向新授权本地链路来自developer的真实JUnit，不冒称quality重新全跑双案。
- 两份过期历史request只作纯codec回归：屋顶343018→236999 B（减少30.907707%），地面343904→237669 B（减少30.890888%），均含末尾LF，全部原字节还原。平坦池各36项；较旧递归原型稍大，因为无共享链、数字词法包装和完整reading封套。原件期限/hash不刷新。
- 原开发RED、两次115s生命周期TIMEOUT、R1 32s组合probe TIMEOUT及整改预检TIMEOUT完整保留，不以成功拆批掩盖；重复执行不累加。原始命令、输入/源码hash、解释器、开始结束/耗时/退出码、完整stdout/stderr和真实JUnit见VALIDATION/QA_INDEX所指RUN/commands。
- 本地QA不保证所有崩溃点/竞态/组合输入穷举、OS沙箱、来源许可有效期、专业语义、模型持续完整持有、宿主容量、provider安全事件根因、远端超时/费用。QAI-R1-02将独立诊断提炼正式回归是非阻断建议，原实证程序仍保留可复跑。
- 用户要求的原四键、原strict、节权限、取消/过期/缓存、no-clobber/崩溃、原request与新view双预算已在所列真实专项/独立诊断范围验证，不宣传为任意输入的完整领域授权系统。

## 固定共享payload与复核

RUN = `.runtime/solar-pv/SOLAR-PV-R2-SHARED-INPUT-IMPL-01/`。文件集合固定在source-review-payload，逐件SHA/大小在fixed-payload-index.json。quality实际审核固定payload及脱敏后直接写payload-quality-confirmation.json；仅该记录实际PASS且绑定索引SHA时允许seal。确认本身、随后确定生成的MANIFEST/ZIP/sidecar/归档身份排除自引用，manager只能核对已审payload字节未变及包完整性，不改quality原文或结论。

包包含实际源码diff、必要源码/专项及最小支持测试、两份新生产codec view/manifest和原过期请求、独立QA原文/provenance/命令/JUnit、关键新NOT_AI lifecycle工件。命令回执如需脱敏另存衍生并分别记录原/新SHA，原证不覆盖。原始完整会话trace、用户秘密、无关UI不入包。

**不是自包含仓库备份**：其余未改引擎、受信canonical测试快照和历史大原件需匹配基线仓库；EXTERNAL-ORIGINALS.json列外置canonical的精确路径/大小/SHA。两案历史codec输入可随包复核，但运行完整生产pytest仍需原仓库和现成依赖。不得在现有运行目录直接解压覆盖，更不得把此包导入WorkBuddy为Skill。新审阅ZIP的SHA/大小/逐成员CRC/SHA/集合以final-delivery实际读回为准；不存在的wheel或Skill候选不填身份。

## 后续分别审批（本轮全部未执行）

| 后续对象 | 必要条件 | 继续阻断条件 |
|---|---|---|
| 唯一受信R2引擎构件及依赖 | 本轮源码审阅通过后另批构建；具体wheel版本/SHA/成员对应批准源码、受信分发来源及完整依赖约束/目标解释器；普通隔离环境安装和实际prepare/publish/accept/resume验证 | 旧0.3.1名称不证明R2；缺host_output/共享模块/入口、依赖或Skill Bash解释器未知仍阻断；不得PYTHONPATH冒充安装 |
| 精确Skill候选/替换 | 另批从批准源码生成独名候选ZIP，给精确SHA/Manifest、授权版本及替换/回退条件；保护旧21载荷和元信息 | 本轮未打包/导入/替换；未批准覆盖、内容不符或解释器/依赖不明即停止 |
| 一次全新屋顶CH08宿主试验 | 官方支持输入通道及安全边界；用户针对具体canonical/新授权/新run/精确模型配置及一次会话明确批准；所需依赖能力分项证明 | 旧过期request不可复用；缺段、敏感返回、压缩后不能完整持有、无draft或strict失败即停，不换工具/编码/模式重投，不新增请求或预算 |
| 地面CH08 | 屋顶停止门真实解除且另有地面授权 | 仍NOT_TESTED_BLOCKED_BY_STOP_GATE；本地QA不能解锁 |

不解锁CH10/16、Phase E/F/G、财务未决/正式四文件/专业签审/全仓回归/Expert或平台发布。产品目标仍是普通用户提供真实资料，由WorkBuddy宿主自主分析和成稿；程序负责确定性事实/计算/校验，测试fixture不能补齐宿主未成功证据。
