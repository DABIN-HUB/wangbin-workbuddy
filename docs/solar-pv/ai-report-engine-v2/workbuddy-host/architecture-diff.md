# H2 架构增量与验证范围

状态：本地协议候选已实现并完成专项验证；安装分发与真实WorkBuddy生成仍阻断。冻结版本保持SOLAR-PV-AI-REPORT-ENGINE-2.0.0。本轮不升级财务、内容质量、专业签审或Phase E。

## 调用链与接口

```text
用户明确授权 / 当前WorkBuddy宿主（实际权限尚待验证）
  → 既有Skill的host-orchestration研究指引
  → run_ai_chapter.py（当前已装解释器 -I；有限命令超时）
  → host_session（CH08-only；grant / canonical SHA / 来源 / 模型绑定）
  → 原prepare：冻结规格 + 确定性结果 → 新request
  → 当前宿主自主Read/研究/Write新response与provenance【本轮未运行】
  → 固定host-intent → 原accept（事实/来源/结构及可选风险断言）
  → host-record → checkpoint/resume → 原局部Word装配
```

Python没有新增LLM SDK/API、固定答案、旧draft加载或第二计算器。新入口不是“已接通的WorkBuddy Provider”。旧report/ground-report保留原行为，在Skill中明确legacy。现有prompt-only Expert验证profile没有放宽，本轮没有新增或安装光伏Expert；专属召唤体验仍不具备验收证据。

## 实际文件与影响

| 文件（服务路径相对services/solar-pv-engine/src/wangbin_solar_pv） | 增量 |
|---|---|
| reporting/host_session.py | 授权、CH08门控、来源记录、幂等accept、检查点、取消、局部装配入口 |
| reporting/host_workspace.py | 仅原生会话使用进程退出自动释放的内核锁；保留锁文件，不删除未知legacy锁 |
| reporting/chapter_writer.py | prepare沿用传入Workspace子类；普通Workspace行为不变 |
| reporting/semantic_risks.py | 对主动声明的预测/实绩、残值/处置、费用付款、回款、股东/项目、DSCR/零值进行机械边界核查 |
| reporting/chapter_result_schema.py、claim_validator.py | 可选risk_assertions；旧必需字段、原事实槽校验及自由文本NOT_VERIFIED不变 |
| reporting/connector_runtime.py | 无账号ready/disconnect；校验本地包版本与协议入口，不伪造登录或宿主权限 |
| packages/skills/wangbin-solar-pv-prestudy/scripts/run_ai_chapter.py | 不注入PYTHONPATH；先固定用户workspace，再改变子进程cwd；最长180秒命令超时 |
| 同Skill的SKILL.md、references/runtime.md、references/host-orchestration.md | 当前宿主新研究、禁止旧稿、用户授权、CLI步骤、预算及独立门禁 |
| packages/connectors/wangbin-solar-pv-cli/cli.json、README.md | auth/status只检本地能力，unAuth不删除用户数据；平台生命周期解释仍待私有验证 |
| tests/solar-pv/test_ai_report_host_session.py、test_ai_host_workspace.py | 用户授权的双类型本地协议与崩溃/路径/风险负测；不作为AI正文证据 |

## 隔离只读审查发现与修复

原始审查记录：本轮运行目录h0/h2-read-only-review-transcript.log。审查者是隔离技术子代理，不是wb-quality，不是工程/财务签审。

1. 原文件独占锁只在正常finally中删除，强制退出会阻断恢复。原生会话改用HostWorkspace内核锁；四个实际子进程取得授权/操作/状态/结果锁后被3秒硬超时终止，父进程均重新获得锁。活动锁不能抢占。未知legacy .lock不自动删除，返回HOST_LEGACY_LOCK_REQUIRES_REVIEW。旧Workspace没有全仓替换；不在同一run并发使用legacy CLI。Windows已实测，Linux/macOS分支未实测。宿主自己重启、网络文件系统和恶意OS用户不在本地锁证明范围。
2. 接受结果后、host-record前的崩溃窗口允许更改来源声明。新增不可变host-intent在accept之前固定request/output/provenance摘要；恢复逐项比较，修改origin即阻断，不能把回放重标成宿主。两个项目的针对性反例通过。摘要仍不是服务端签名。
3. Skill子进程cwd切换会改变相对workspace含义。现在在调用者cwd解析根路径，同时先拒绝..，不通过规范化吞掉越界输入；含空格相对路径专项通过。

以上修复由主执行者完成并复验；原审查报告保持不改写，不把主执行者复验称为wb-quality独立签审。

## 本地验证与失败记录

最终选定JUnit去重258项PASS、0失败、0错误、0跳过：58项host_session、9项锁/Skill包装器、71项原章节协议、18项原依赖、102项冻结规格。原始命令、时间、硬超时、stdout/stderr摘要、JUnit摘要与用例ID在h2-final-test-summary.json及h0对应JSON。分组的deselected仅是分片选择，最终去重覆盖所列文件；不是全仓回归。

实际失败保留：初次解释器无pytest；整体新协议、预算组合和依赖组合各180秒超时，后拆分全覆盖执行，不把超时改成PASS。anyio插件存在CallSpec2弃用警告，未修改依赖规避。构建解释器没有pip，改用现有setuptools后端离线构建两个wheel成功；没有下载构建工具。

两个wheel的ZIP CRC、RECORD及新增模块字节已验证，哈希见candidate-wheels/manifest.json。全新venv的uv离线安装实际失败：Pillow>=10,<13所需包不在本地缓存。未放宽依赖、未联网安装、未配置私有索引、未全局安装。两个内部固定版本的公共PyPI 404记录仍在H0；本地产生wheel不等于受信索引分发或平台安装。

## 未实现或未证明的边界

- 无真实WorkBuddy模型调用、实际专家召唤、Read/Write/Bash授权及托管解释器继承证据；无双案新AI Word/JSON。
- 不做自动证据切片；完整请求超过字节预算就阻断。宿主上下文/token/积分/费用/远程超时未暴露，标NOT_EXPOSED_BY_HOST；命令硬超时不替代模型超时。
- 取消只阻止本地后续动作；授权变化本身会阻断打开run。遗留旧锁必须人工确认所有者后另行处理，不自动清除。
- risk_assertions可选，未声明风险的自由文本仍无法全面机械判定。ACTUAL当前一律阻断；没有处置现金证据适配，不将残值当回款。专业审核必须独立进行。
- 原有财务、候选比较、完整四文件、PDF公式、全仓回归及发布阻断保持；CH10/16仍锁定。

## 追溯

运行目录：`.runtime/solar-pv/ai-v2-host-20261112-144349/`。H0/H1提交为7a2a896a927574800dcf521e82c66192655c9121；本文件及H2源码的实际提交SHA以后续h2-commit.json为准。最终门禁以final-gate-verdict.md及final-state.json为准，不用文档自引用未来提交SHA。
