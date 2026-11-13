# 下一步与恢复（作者冻结快照）

本轮只是输入审计与离线方案。当前待办：manager 官方资料摘录/适用范围、独立 quality 复核、必要截图隐私裁剪，然后同一唯一 writer 第二阶段收尾。**尚未生成最终审计 ZIP**，也未改生产。

## 1. 精确路径与输入身份

仓库：`F:/ideaWorkSpace/wangbin-workbuddy`，source baseline `71ba9b8b2ed6ba7d96ad6619a29a44875d2a6c9a`，分支 main。文档/脚本只在本目录；runtime 根：`.runtime/solar-pv/SOLAR-PV-R2-HOST-INPUT-AUDIT-01/`（以下称 RUN）。

原件根 `OLD=.runtime/solar-pv/r2-client-552-20261113-132354`：

- 屋顶 `OLD/workspaces/industrial_rooftop/roof-primary/CH08-1-request.json`，SHA `d48b0bfad84b303d7f7978d6c9e53f78aba424541992f509240df8a09928bae1`，request_hash `6fe43c192678ffcaad656378a180b5aa6a8d8aea898b2432817c110becef3dd3`。
- 地面 `OLD/workspaces/utility_scale_ground/ground-primary/CH08-1-request.json`，SHA `976ce58137f5aee380de765584df59d78d4777e993cc9f1ddd7dc912d616df6a`，request_hash `a459085535f3dd633f55ad5a6c1915f176fb3087ad51b1f59628cfccd91d57b8`。
- 两案可读副本分别为各类型目录 `CH08-request-readable.json`，原 bytes/hash 见 REQUEST_PROFILE。
- 原 canonical、authorization、state、RESULT、ZIP/sidecar/安装读回均在 BASELINE 及 RUN 精确索引；只读，不执行旧包脚本。

两个请求均已过期：屋顶原 expires_at `2026-11-13T06:32:14.577476+00:00`，地面 `2026-11-13T06:43:26.397208+00:00`。保留这些精确值，不刷新为当前可用请求。文件 SHA 与 request_hash 是不同身份，绝不能互换。

## 2. 可运行离线命令

所有命令从仓库根执行，现有 Python 标准库，无安装。每条分析硬上限120秒；建议使用已有录制器单项115秒子进程上限，累计900秒含 QA。不要再跑历史pytest或财务。

作者产生当前保留视图的实际命令（已执行，目标存在，**不要原样重跑覆盖**）：

```text
python -B docs/solar-pv/ai-report-engine-v2/host-input-audit/SOLAR-PV-R2-HOST-INPUT-AUDIT-01/offline_view_audit.py run --original-root .runtime/solar-pv/r2-client-552-20261113-132354 --out .runtime/solar-pv/SOLAR-PV-R2-HOST-INPUT-AUDIT-01/experiment-final
```

### 独立 QA：纯只读、内存重算（推荐，不写文件）

```text
python -B docs/solar-pv/ai-report-engine-v2/host-input-audit/SOLAR-PV-R2-HOST-INPUT-AUDIT-01/offline_view_audit.py readonly --original-root .runtime/solar-pv/r2-client-552-20261113-132354
```

该命令逐案重算两种视图、每字节/每数字词法、request/evidence hash、六节权限闭包、可读副本及全部负例；stdout 含实际 executable、版本、脚本SHA、每案度量、负例结果和耗时。`writes=false`；`-B` 不写 bytecode。quality 用外部 terminal 120秒上限保存实际开始结束/退出/stdout/stderr，并将原结果交唯一 writer，不覆盖作者报告。脚本状态不自称“独立”，独立性来自真正另一 quality 执行与职责，不是函数名。作者已运行同入口验证新增入口，但这仍只是作者自检。

按已保存视图只读解码（屋顶共享模式示例；地面/类型行应各自复核）：

```text
python -B docs/solar-pv/ai-report-engine-v2/host-input-audit/SOLAR-PV-R2-HOST-INPUT-AUDIT-01/offline_view_audit.py verify --request .runtime/solar-pv/r2-client-552-20261113-132354/workspaces/industrial_rooftop/roof-primary/CH08-1-request.json --view .runtime/solar-pv/SOLAR-PV-R2-HOST-INPUT-AUDIT-01/experiment-final/industrial_rooftop-shared-objects.json
```

错案 replay 应非零退出，不能把错误改回原件。`selfcheck` 只验精确数字/非法JSON/合成sentinel，不替代 readonly 的真实两案完整实验。

若质量角色获准写 QA 生成证据，可在同一 RUN 中使用独名 `qa-experiment-01` 的 `run --out`；不得覆盖作者目录。用户当前分工以纯只读入口为优先。超时保留原输出和124状态，至多按屋顶/地面合理拆一次，不扩大累计预算。

## 3. 冻结与证据索引

- `RUN/author-snapshot.json`：本目录所有冻结文件、关键实验/命令/输入索引的原字节 SHA 和大小；无需在已提交文件中自引用自己的最终提交 SHA。
- `RUN/author-final-state.json`：提交后实际 HEAD、状态、diff、保护比对、计数/字节和累计验证时间。它才是本地 commit 的最终读回，文档不预填未来 SHA。
- `RUN/commands/*.json` 与同前缀 stdout/stderr：真实录制命令、开始结束、输入 hash、解释器、退出码；RED 预期 exit1 保留，其余作者验证以实际回执为准。没有 JUnit，因为未运行pytest。
- `RUN/experiment-final/`：四个 whole-chapter view；每案 leaf bytes、重复结构、每个共享点和类型列映射、完整源定位/周期/边界/状态覆盖明细。core CSV 是精简任务索引，完整明细仍在本RUN，不删语义。
- `RUN/protected-tracked-before.json`：1242个旧 tracked 文件、613683280 B，全部逐字节hash；原件/dist另表，R8–R13单列元信息索引2638项（不是全内容hash证明）。旧隔离worktree只列路径，未遍历/操作。
- `RUN/manager-ui-index.json`：manager 六张原截图hash；仅三张必要图私下保留为 ignored 原件，尚未获准入最终包，需裁剪/隐私复核。无全量 UI 树或全量审计导出。
- `experiment-01/02` 是作者早期实现的真实结果/回执阶段，不作为当前冻结源码结果，也不累加通过数；后续若移除重复 payload 必须先列SHA与保留回执，仅清本任务所有权明确的内容。

这不是独立全仓备份。旧 ZIP、canonical 和大型历史资产继续在其原位置；只依赖 Git 文档或本地忽略目录不能冒充云备份。

## 4. 交还 manager/quality 的核对清单

1. 核验本地 commit 与 snapshot；只允许本审计目录新增，生产/冻结/原件/候选/安装成员原hash不变。
2. quality 独立执行只读命令并核对两案343018/343904 B、267事实、11公式、4表、22术语、12075行；共享228621/229291 B，类型行143143/143289 B；两种模式都完整还原本次原字节（含末尾LF），不是推广到任意JSON序列化。
3. 复核每案45个负向结果（含风险覆盖不足），以及风险自然语言本来未被证明的范围。全字段相等不是专业结论相等；formula许可不代表强制全部使用。
4. 核对 manager 官方资料原文/时间/准确URL/版本范围并补入本目录。已转交现场说明只证明5.5.2有审计UI、两搜索零匹配；provider覆盖及根因UNKNOWN。
5. 同一 writer 保存 QA 原文（不得改写结论）、更新状态/必要简要索引、第二阶段本地 commit，最后才按真实文件集合生成独名审计ZIP + Manifest + SHA，并逐成员CRC/hash/readback。不能拿它当Skill安装包或发布物。

## 5. 后续动作分项审批与停止条件（均未执行）

| 后续项 | 必要条件 | 停止条件 |
|---|---|---|
| 生产整章共享视图接口 | EXC006显式批准、独立QA、当前源码专项计划、旧R2兼容与双身份cache设计 | 未批、未知映射、丢字段/风险/权限或试图刷新旧期限即停止 |
| 新引擎/依赖安装 | 唯一wheel版本/SHA/源码与完整依赖受信来源、隔离解释器批准 | 缺wheel、解析失败、版本不符、找不到R2入口、需注入开发PYTHONPATH即停止 |
| Skill替换 | 新独名候选SHA/manifest、用户单独批准、原安装保护、工具授权 | 相同ID覆盖未经批准、安装内容hash不符或依赖不明即停止 |
| 单次新屋顶CH08 | 官方支持的输入路径/安全边界、新canonical授权和全新request、明确一次新会话预算、依赖是否所需分项证明 | 输入不完整、敏感返回、压缩后内容不能持有、无draft、任何严格校验失败即保留原件停止，不自动换模式重试 |
| 地面CH08 | 屋顶停止门解除且地面独立授权；不可凭离线结果跳过 | 屋顶仍BLOCKED则地面仍NOT_TESTED_BLOCKED_BY_STOP_GATE |

不解锁CH10/16。Phase D完整试点仍是双案CH05/08/10/14/15/16/17/18；历史六章Hermes辅助样稿不证明宿主自主生成。publish/accept/resume→Word、专业审核、PDF、正式四文件、真实资料、全仓回归、Expert和发布均独立保留。
