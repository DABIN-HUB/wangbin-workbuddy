# AUDIT-R1 Q02 0.1.3 开发预 QA 证据（独立 QA 尚未运行）

- 产品 `wangbin-project-acceptance-check`；任务 `t_b7ca196e`；工作树 `F:/ideaWorkSpace/wangbin-workbuddy-project-acceptance-check`；分支 `skill/project-acceptance-check`；基线 `a10589827322a6643511101d449298700bb95ef2`。分析师三份冻结合同先单独提交 `7e8ac7434211d21c34730063b66bf43acc5d2075`；业务源代码/受限工厂/专项测试提交 `a11b7087c20bf8e8561a9e7525c2f2d269218aaf`。本报告与 catalog 仅包外证据提交，不改载荷。
- 原 0.1.2 ZIP `dist/wangbin-project-acceptance-check-0.1.2-skill-candidate.zip`：SHA-256 `5117bd7202cd6a322c3aae8246dad79edeb4cd9a876cbcae800ee78ad2a9df57` 未变；独立基线 t_c08511ed 旧反例 F01/F02/F03 FAIL，F04 部分子项 PASS，历史报告不改写。
- 新 0.1.3 ZIP `dist/wangbin-project-acceptance-check-0.1.3-skill-candidate.zip`：SHA-256 `9b6234744613af39c9d710359c93649044cbc4660aa9805a9bf8e1a8927c797e`；对应 `.sha256`/`.manifest.json` 同名 sidecar。`products/catalog.json` 新版登记为候选，`active_version` 仍是 0.1.2；未提前激活/发布。

## 修复与验证层次

| 缺陷 | 基线反例实际 | 源码改动 | 本机开发结果 / 独立 QA |
|---|---|---|---|
| ACC-F01 | 旧同号 10、9999、无关备份都 `EVIDENCE_FOUND` | `judge` 拆编号绑定和并发指标/比较符/场景/单位；双形态 `R01 `、`R01：` 保留候选编号；7999/8000/8001 等值与严格大于比较 | 新 10/9999 不符合、10000/10001/12000 支持、无关 NO_EVIDENCE_FOUND、不可比待确认；独立 QA NOT_TESTED |
| ACC-F02 | 旧 Ubuntu 说明支持 Windows Server 2022 | 目标系统与版本按实际文本提取、比较；明确仅其他环境且未提供目标文档作为交付不符合，其他环境仅缺目标证据；完整步骤才支持 | 新 Windows Server 2022/2025、Debian 12、Fedora 40 正反用例和缺步骤回归通过；独立 QA NOT_TESTED |
| ACC-F03 | 旧把失败 0 判不符合，未发现失败也误判不符合 | 比较执行/成功/失败计数与测试对象、回归范围；零与未知分开 | 新 100/100/0 与 37/37/0 支持，100/99/1 不符合，未发现失败缺范围待确认；独立 QA NOT_TESTED |
| ACC-F04 | 原复合/自述/冲突受测子项 PASS，增量未覆盖 | 保留逐子条件/冲突；显式旧快照来源允许增量沿用版本引用；新增比较理由随三种输出回读；拒绝跨同前缀不同要求编号错绑 | 专项复合部分→补件支持且不影响 R02、双来源冲突、六表 XLSX/DOCX/JSON 回读通过；独立 QA NOT_TESTED |

- `python -m pytest tests/test_project_acceptance_check.py tests/test_project_acceptance_audit_r1.py tests/test_product_factory.py -q --tb=short` → exit 0；**71 passed、3 skipped**（Windows symlink 不可创建）、1 个 pytest 兼容警告。新专项开发用例共 30 个真实文件测试，出自冻结合同但独立 QA 会另选输入。工厂增加显式 `--version` 的候选校验/打包/验证，而不将尚未独立验收的候选设置 active。原工厂测试中写死 10 产品的断言按真实产品注册数改为 ID 唯一与目标存在；其他产品打包未测。
- `python -m tooling.products test --id wangbin-project-acceptance-check` → exit 0、17 passed/1 skipped（catalog 原注册路径的旧产品测试）；`python -m tooling.products validate --id wangbin-project-acceptance-check --version 0.1.3` → exit 0 PASS；`python -m tooling.products package --id wangbin-project-acceptance-check --version 0.1.3` → exit 0 PASS；`python -m tooling.products verify --id wangbin-project-acceptance-check --version 0.1.3` → exit 0 PASS，核对源码/清单/ZIP 成员；`python -m zipfile -t dist/wangbin-project-acceptance-check-0.1.3-skill-candidate.zip` → exit 0；`(cd dist && sha256sum -c wangbin-project-acceptance-check-0.1.3-skill-candidate.zip.sha256)` → exit 0 OK。
- 隔离 Python 3.11.15，通过 `uv venv`/`uv pip install` 实装 python-docx 1.2.0、openpyxl 3.1.5、lxml 6.1.3、et-xmlfile 2.0.0、typing-extensions 4.16.0（uv 返回 0）；该环境仅本机可执行，第三方许可证文本/商业分发与 WorkBuddy 预装 **NOT_VERIFIED**。`F:/tmp/acc-r1-venv/Scripts/python.exe docs/qa/audit-r1-013-developer-probe.py dist/wangbin-project-acceptance-check-0.1.3-skill-candidate.zip C:/Users/wangbin/AppData/Local/hermes/profiles/wb-developer/cache/scratch/acc013-clean-extract > docs/qa/audit-r1-013-developer-results.json` → exit 0；干净解压仅从包内正式脚本调用，7 个真实 MD CLI 场景，七案退出 0 且业务状态逐案符合 expected；每案重开六表 XLSX、DOCX 与 JSON 核对状态、来源、覆盖数，记录在同名 results.json。ZIP 不含本地虚拟环境，勿依赖其绝对路径。
- 当前目录源码已升 0.1.3，而 active/catalog 原版本仍 0.1.2；故**默认 validate 和显式旧 0.1.2 verify FAIL**（源文件/SKILL 版本与旧归档不同）。这是共享源码目录的已知工厂限制，不是旧 ZIP 损坏。旧 ZIP 原哈希不变；新版须显式 `--version 0.1.3`。原版本厂验收不再声称 PASS。

## 未测/风险

L1 有限源码/敏感信息差异检查、L2 本机专项回归、L3 开发从最终 ZIP 清洁解压为本报告范围；L4 真宿主模型自然语言三回合、L5 WorkBuddy 平台安装/实跑 **NOT_TESTED**，不得以 CLI 模拟。OS/单位/语义仍是局部确定性解析，不证明覆盖所有软件环境、任意措辞、冲突数字、可疑旧快照真实性；无可比值时不得作正式合格结论。依赖许可证与平台协议/分发权 NOT_VERIFIED；无平台上传、发布或 push。新 0.1.3 **独立 QA NOT_TESTED**：由预建子任务 t_8b65f7ea 从精确 ZIP 哈希重新选正反变体并复核，失败则保留此不可变 ZIP 并升级新版本返工。
