# 下一步与恢复（最终输入审计）

本轮只是输入审计与离线方案。五个官方原文已实际GET并保留完整HTML/时间/SHA；独立quality已完成，总裁定PARTIAL原样保留；截图最小裁剪及Git邮箱脱敏由developer落实，不是quality重新验收。QA原文与索引见QA_INDEX.md。最终commit/保护/预算、审计ZIP/Manifest/外SHA分别以RUN/final-state.json、RUN/final-delivery.json真实读回为准，不以本文预填未来SHA；未改生产。

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

该命令逐案重算两种视图、字节/数字词法、request/evidence hash、部分引用一致性helper、可读副本及负例，`writes=false`、`-B`不写bytecode。**closure()只检查部分关系，UNKNOWN metric/claim、duplicate source、同源跨节事实不能由它独立识别，不能仅凭此命令的VALID标签证明完整六节权限**。当前完整权限结论依赖可信原件完整树精确比较和本次独立QA另查。QA已实际执行并另写独立展开/权限/132项内存负向，原裁定PARTIAL；这些是离线诊断，不是产品tests。原完整stdout未从截断live log恢复，48106B/SHA只记QA报告值，绝不合成stdout或内存程序。源码未变，收尾不重复跑30秒readonly凑通过。

按已保存视图只读解码（屋顶共享模式示例；地面/类型行应各自复核）：

```text
python -B docs/solar-pv/ai-report-engine-v2/host-input-audit/SOLAR-PV-R2-HOST-INPUT-AUDIT-01/offline_view_audit.py verify --request .runtime/solar-pv/r2-client-552-20261113-132354/workspaces/industrial_rooftop/roof-primary/CH08-1-request.json --view .runtime/solar-pv/SOLAR-PV-R2-HOST-INPUT-AUDIT-01/experiment-final/industrial_rooftop-shared-objects.json
```

错案 replay 应非零退出，不能把错误改回原件。`selfcheck` 只验精确数字/非法JSON/合成sentinel，不替代 readonly 的真实两案完整实验。

若质量角色获准写 QA 生成证据，可在同一 RUN 中使用独名 `qa-experiment-01` 的 `run --out`；不得覆盖作者目录。用户当前分工以纯只读入口为优先。超时保留原输出和124状态，至多按屋顶/地面合理拆一次，不扩大累计预算。

## 3. 冻结与证据索引

- `RUN/author-snapshot.json`：本目录所有冻结文件、关键实验/命令/输入索引的原字节 SHA 和大小；无需在已提交文件中自引用自己的最终提交 SHA。
- `RUN/author-final-state.json`：作者冻结提交的原读回，原件含git fuller邮箱不可入共享包；另有redacted-receipts/author-final-state.json及原/新SHA。最终收尾读回是RUN/final-state.json，原作者回执不覆写。
- `RUN/commands/*.json` 与同前缀 stdout/stderr：真实录制命令、开始结束、输入 hash、解释器、退出码；RED 预期 exit1 保留，其余作者验证以实际回执为准。没有 JUnit，因为未运行pytest。
- `RUN/experiment-final/`：四个 whole-chapter view；每案 leaf bytes、重复结构、每个共享点和类型列映射、完整源定位/周期/边界/状态覆盖明细。core CSV 是精简任务索引，完整明细仍在本RUN，不删语义。
- `RUN/protected-tracked-before.json`：1242个旧 tracked 文件、613683280 B，全部逐字节hash；原件/dist另表，R8–R13单列元信息索引2638项（不是全内容hash证明）。旧隔离worktree只列路径，未遍历/操作。
- `RUN/manager-ui-index.json`：六张原截图索引，三张私下原件不变；新share-preparation/cropped-ui仅保留审计标题及两零搜索panel，源/新SHA、坐标和像素对应见cropped-ui-index.json。原图/全量capture/AX树不入包；developer结构裁剪不称quality再验收。
- `experiment-01/02` 是作者早期实现的真实结果/回执阶段，不作为当前冻结源码结果，也不累加通过数；后续若移除重复 payload 必须先列SHA与保留回执，仅清本任务所有权明确的内容。

这不是独立全仓备份。旧 ZIP、canonical 和大型历史资产继续在其原位置；只依赖 Git 文档或本地忽略目录不能冒充云备份。

最终审计包按精确allowlist保留仓库相对路径，可恢复两个精确request、两个readable、四view及完整mapping/coverage用于只读复算；大reviewZIP/wheel/完整官方HTML/canonical外置精确hash，故仅对本次codec输入自包含、对历史全材料非自包含。先验证外SHA/Manifest每成员size/SHA/CRC/唯一性/安全路径，再在独立空目录解压，不覆盖现有run；不执行旧包脚本。author-snapshot与原脚本/experiment-final不变；后改core只为说明/隐私收尾，QA未审最终文档或ZIP。

## 4. 独立复核结果与交还 manager 的核对定位

1. 核验本地 commit 与 snapshot；只允许本审计目录新增，生产/冻结/原件/候选/安装成员原hash不变。
2. quality 独立执行只读命令并核对两案343018/343904 B、267事实、11公式、4表、22术语、12075行；共享228621/229291 B，类型行143143/143289 B；两种模式都完整还原本次原字节（含末尾LF），不是推广到任意JSON序列化。
3. 复核每案45个负向结果（含风险覆盖不足），以及风险自然语言本来未被证明的范围。全字段相等不是专业结论相等；formula许可不代表强制全部使用。
4. 官方原文/时间/准确URL/版本支持边界已由实际GET补齐HOST文档，完整HTML在official/；5.5.2审计UI存在已证，两搜索零匹配不证明无事件，provider覆盖及根因UNKNOWN。
5. QA原文UTF8/LF保存于RUN/independent-qa/QUALITY_REPORT.verbatim.md，来自delegation完成返回，不是provider传输字节。QA-F01仅补边界、F02使用脱敏衍生，落实者为developer，总裁定仍PARTIAL。最终commit及独名审计ZIP以final-state/final-delivery实际回执为准；不能当Skill安装包或发布物，需要重新质量验收由manager另排。

## 5. 后续动作分项审批与停止条件（均未执行）

| 后续项 | 必要条件 | 停止条件 |
|---|---|---|
| 生产整章共享视图接口 | EXC006显式批准、独立QA、当前源码专项计划、旧R2兼容与双身份cache设计 | 未批、未知映射、丢字段/风险/权限或试图刷新旧期限即停止 |
| 新引擎/依赖安装 | 唯一wheel版本/SHA/源码与完整依赖受信来源、隔离解释器批准 | 缺wheel、解析失败、版本不符、找不到R2入口、需注入开发PYTHONPATH即停止 |
| Skill替换 | 新独名候选SHA/manifest、用户单独批准、原安装保护、工具授权 | 相同ID覆盖未经批准、安装内容hash不符或依赖不明即停止 |
| 单次新屋顶CH08 | 官方支持的输入路径/安全边界、新canonical授权和全新request、明确一次新会话预算、依赖是否所需分项证明 | 输入不完整、敏感返回、压缩后内容不能持有、无draft、任何严格校验失败即保留原件停止，不自动换模式重试 |
| 地面CH08 | 屋顶停止门解除且地面独立授权；不可凭离线结果跳过 | 屋顶仍BLOCKED则地面仍NOT_TESTED_BLOCKED_BY_STOP_GATE |

不解锁CH10/16。Phase D完整试点仍是双案CH05/08/10/14/15/16/17/18；历史六章Hermes辅助样稿不证明宿主自主生成。publish/accept/resume→Word、专业审核、PDF、正式四文件、真实资料、全仓回归、Expert和发布均独立保留。
