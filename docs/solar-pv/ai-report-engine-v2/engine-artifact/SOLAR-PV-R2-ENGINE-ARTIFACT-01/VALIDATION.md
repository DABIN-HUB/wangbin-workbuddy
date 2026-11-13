# 构建阶段验证 — NOT_INSTALLED / NOT_HOST_E2E

RUN = `.runtime/solar-pv/SOLAR-PV-R2-ENGINE-ARTIFACT-01`。全部实际验证由该 RUN/record_command.py，role=developer 录制；完整命令数组、输入 SHA、解释器、cwd、开始/结束、timeout、退出码及原始 stdout/stderr 在 `RUN/commands/developer-*.{json,stdout,stderr}`。下表不是 pytest 用例统计。

| label | 上限秒 | 实测秒 | 实际结果 |
|---|---:|---:|---|
| discovery |45|1.86333499988541|exit0；实际 HEAD/main/clean、八文件原 SHA、现有解释器/backend|
| build-wheel |90|11.623812300153077|exit0；setuptools.build_meta 真实构建唯一 wheel；backend 内部计时 1.9162649996578693s，前者包含 snapshot/源身份取证|
| wheel-static-audit |60|1.7377778999507427|exit1；审计脚本错误 codec 名 utf8-sig，非产品或 wheel 缺陷；原 stderr 与匹配 input SHA 的 failed-first 脚本保留|
| wheel-static-audit-r2 |60|2.0738353999331594|exit0；完整 ZIP/RECORD/METADATA/源映射/AST 静态验证|
| build-stage-closeout |60|17.33355010021478|exit0；129 源文件对应实际基线 blobs、1929 保护项、22 installed、2638 历史 metadata、现成 secret scanner；修正演示 fixture 的 tracked 分类|
| hygiene-check |45|2.038044299930334|exit0；只读卫生、四个既有太阳能 dist ZIP CRC/结构/忽略读回，无删除|
| final-wheel-binding |60|0.22132789995521307|exit1；裸python缺packaging；未创建metadata目录/无产品写入，保留原证|
| final-wheel-binding-r2 |60|0.98015489988029|exit0；改用实际构建的绝对exe；新wheel实际METADATA与source/原graph相等；12矩阵43→42，50条metadata原SHA复核|

后续本阶段 Git/文档封口的实际时间与结果另以 `developer-precommit*`、`developer-commit`、`developer-postcommit` 原回执为准；尚未发生的命令不预判 PASS。precommit首次因Windows默认GBK解码exit1(0.19396739965304732s)；改显式UTF8后二次strict-citation因重复引用警告exit1(0.785716200247407s)，只更新过一个Sources块，尚未stage。独名citation-diagnostic exit1(0.26307869981974363s)保存实际警告；移除同句重复citation后新批次重跑。早期wrapper保留trace，但其未落盘的嵌套citation stdout不补造；后续每个子命令即时保存原stdout/stderr。两个失败precommit的精确input脚本另存，不丢弃失败或假计PASS。角色累计由最终 `RUN/developer-final-state.json` 从全部本角色 receipt 求和，包含失败；每批 <=120s，本阶段上限260s，不借其他角色时间。

## 构件与静态覆盖

- wheel：`RUN/candidate-wheels/wangbin_solar_pv_input-0.3.2-py3-none-any.whl`；557392 B；SHA-256 `cd7be44ca5350da87c4760898ddeb46b8a73646d8f2f8de6be61e48cca9f7808`。ASCII/LF sidecar 原字节通过。
- 122 唯一、安全、无大小写别名/穿越/链接/加密成员，逐成员读取/size/CRC/SHA-256 与 `ZipFile.testzip()` 通过。
- RECORD 122 唯一行与成员集合完全一致；121 个非自身成员的 URL-safe 无 padding SHA-256 与十进制 size 核对；RECORD 自身 hash/size 空。详见 WHEEL_CONTENT_MANIFEST.json，不以 basename 或版本代替内容验证。
- 117 件 source→snapshot→wheel 原字节映射通过：97 Python 模块 + 20 个声明 data。四个关键 host_input_view/chapter_writer/host_session/host_output 均是批准原字节；两个正式 reporting/specs 全件映射通过。spec-lock LF 合同 SHA 仍 `59e379906f6b83d91a76179f14fdc00e5c0dc9346ef5d272bbcf04da90df7532`，冻结报告版本不变。
- 5 个 .dist-info 是 backend 生成：METADATA、WHEEL、entry_points.txt、top_level.txt、RECORD。METADATA 与新 snapshot egg-info/PKG-INFO 同字节，script/top_level 与其生成源同字节；METADATA Name/Version、Requires-Python、8 项 Requires-Dist 与 pyproject 语义精确相等。仓库历史 egg-info 六文件没有复制或修改。
- 97 Python 文件全部 AST parse；console script `wangbin_solar_pv.cli:main`、package __main__、reporting __main__、host_session main 静态解析到实际函数；新 prepare-r2-shared 动作在 wheel 源码中存在。仅 `AST_STATIC_TARGET_RESOLVED_NOT_EXECUTED`，没有 import/help/runtime/installed PASS；未设置 PYTHONPATH。
- 129 件完整源 snapshot（pyproject + 128 src 文件）逐件 SHA 冻结；129 个基线 Git blobs 实际 readback，除批准分发版本外匹配 Git checkout CRLF/LF。该归一化仅解释 Git 工作区差异；wheel 映射始终原字节。snapshot 集合 SHA `d4662f988413fcfecb7024db3c418887c680239ca51aa2b887f47930d0eb743c`。核心八文件集合 SHA 仍 `3b41751eb36a632e38c0aab123e25eb66a271e84d2de1ee42d0b06a5f92993c4`。

## 明示缺口与边界

1. 11 件既有 **tracked** synthetic/editorial fixture JSON 在完整 source snapshot 内，但未声明 package-data、因此不在 wheel。原审计生成器误标 UNTRACKED，封口通过实际 git ls-files 和 snapshot 成员逐项修正，不改 payload 或旧 receipt。它们不是 R2 自动研究输入；可选 load_editorial_fixture 默认演示目录不可用，不声称全部 demo/legacy 功能完整。
2. Catalog 按既有合同需要显式 `--baseline-dir` 提供 12 件外置冻结基线。静态核实本地真源的原 SHA 和锁定归一化 SHA，但没有装入 wheel；现有 Skill wrapper 单独带基线并传参。wheel 单独不是自包含运行包。本轮不能改这一打包/运行合同。
3. `__version__=0.3.0` 被 intake 用为 input_module_version，仍不改；分发身份以 pyproject/METADATA 为准。引擎内 connector_runtime 仍检查 solar 分发0.3.1，Connector 三 OS init 也固定0.3.1；未来安装0.3.2后 readiness 仍会阻断，不能宣称 LOCAL_READY。另批对齐必要 metadata，并先提供可信分发与依赖，不在本阶段擅改。
4. 只发现一份本地 solar0.3.1 wheel：548537 B / `9c0abf6597c6b444c646eaafc3a802fa2e78cddcfe720633c6b65b2463f8a64b`；其内部无 host_input_view/host_output，不代表本次 R2。document1.2.0 两份 bytes/hash 不同，分别保留并记录，不据版本号认定同一可信源或可互换。无覆盖/改名旧 wheel。
5. 现成 setuptools84.1.0 自带 bdist_wheel；独立 wheel/build 分发缺失不是本次 backend 构建阻断。使用实际 Python3.14.9，符合声明 >=3.12,<3.15，但纯构建不验证3.12/3.13/3.14安装、Linux/macOS或WorkBuddy解释器。
6. PIP_NO_INDEX、PIP_CONFIG_FILE=nul、PIP_NO_BUILD_ISOLATION、PIP_DISABLE_PIP_VERSION_CHECK、UV_OFFLINE、禁 bytecode/user site；直接 backend，不调用安装前端。audit hook 拒绝网络连接/DNS/bind、外部子进程与 setuptools 依赖获取。没有 OS 沙箱宣称。SOURCE_DATE_EPOCH 来自真实基线 Git committer 时间；只构建一次，不宣称可重复构建。

## 保护、卫生与未执行

1929 保护项中1928 原字节相同，唯一变化为批准 pyproject 版本；installed22（21载荷+1metadata）全部原 SHA 不变；R8–R13 2638 项仅元信息不变，不能升级为全内容 hash。旧 dist/历史 wheel/旧QA/原 canonical/request 不修改。现成 secret scanner 限定对完整 snapshot src 与当前正式任务文档运行，发现0；不将其称为全仓秘密完备性证明。

本轮净删除0文件/0B、释放0B；115 历史 tracked logs 因本轮历史保护而留存，不做未授权清理。构建产生 build/egg-info 只在 RUN/build-source 内，作为可追溯唯一构建证据保留；wheel/sidecar/命令/源快照均留忽略 RUN，不入 Git。当前正式材料八项加PLAN共九文件；QUALITY_REPORT保留待独立QA，精确 allowlist 随 Git receipt。

没有新增或改动测试/Mock/fixture，没有 pytest、财务重算、Office/PDF/全仓回归，没有下载/安装、Connector/Skill修改或安装、宿主模型、push、上传或发布。DEPENDENCY_CLOSURE = BLOCKED（最终12矩阵各42第三方独立wheel缺失/来源许可未闭合），本轮独立QA = PENDING；安装 = NOT_TESTED；平台/专业/财务/四文件/发布门禁继承，不用旧136身份或纯静态映射冒充当前 runtime PASS。
