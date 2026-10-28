# 光伏 Phase 0 仓库审计验收报告

日期：2026-10-28。范围：只读仓库、复用、官方能力和既有回归基线；不是光伏功能、产品发行或平台验收。本文以真实日志/JSON为准，不用子代理自报作为最终证据。

## 结论

`PHASE0_AUDIT=PASS_WITH_RECORDED_LIMITATIONS`：审计、保护清单、复用/缺口和真实回归已完成；Windows符号链接5项未执行、旧安全风险、发行环境前置及平台未测均独立保留。允许冻结Phase1需求，不允许从本结论推导数值引擎/四文件/平台通过。

## 仓库身份与保护

- 初始分支main，HEAD `c9b73291200e904a875ec2e2642f7492bd311036`，初始git status --short无输出。
- 实际 `git ls-remote origin refs/heads/main`：`5407d86b990633753ae577a9e799640da93f4c54`；本地领先1提交，不是与GitHub main完全一致。未pull/reset/checkout/切分支。
- `docs/solar-pv/00-protected-artifacts.json`：288个既有文件、25归档（23 ZIP、2 wheel）、22个catalog版本。父任务初始独立采样216跟踪文件+72 dist文件，与子任务逐文件采样完全一致。
- 实际复算：288个保护文件变化0、子清单与父初始清单不符0；详见 `phase0-protection-verification.json`。保留旧Skill/Expert/Connector、模板/许可/catalog/metrics与全部历史ZIP；没有重新打包或改受保护归档。

## 复用审阅与发现

定义/调用链/行号见 `00-repo-audit.md` 与 `00-reuse-matrix.md`。现有工厂可作唯一台账/版本/隔离打包框架，旧文档服务只读/去重，financial_xlsx只作XLSX转CSV，不是光伏报告/财务引擎。共用旧代码已知ZIP穿越段判断静态缺陷、Windows硬隔离/后代清理、XLSX主进程/快照/日志等风险不因本次回归消失；本轮不修旧代码、不冒充安全沙箱。

官方Skill/Expert/Connector/公约四页直连HTTP200，访问摘要及hash见 `00-official-access.json` / `00-platform-recheck.md`。官方可选skills与依赖不能被旧prompt-only validator解释为平台禁止；保留旧规则，Phase7如需集成另建隔离产品校验profile并真机验。普通Skill依赖自动安装及本项目平台路径未实测。

## 真实回归命令与结果

为避免旧CLI测试重写reports/validate.*或旧包，在Hermes scratch复制全部216个跟踪文件及72个dist文件后运行**未修改的既有测试**，而非在原树运行有副作用的CLI。副本不含.git，不产生新候选上传动作。已有fixture齐全，没有新增测试代码或生成脚本。

工作目录：`C:/Users/wangbin/AppData/Local/hermes/cache/scratch/solar-pv-audit-20261028/repo-baseline`。

首轮：

```text
F:/ideaWorkSpace/wangbin-workbuddy/.venv/Scripts/python.exe -m pytest tests packages/experts/wangbin-software-consultant/tests -ra --basetemp=C:/Users/wangbin/AppData/Local/hermes/cache/scratch/solar-pv-audit-20261028/pytest-baseline --junitxml=C:/Users/wangbin/AppData/Local/hermes/cache/scratch/solar-pv-audit-20261028/baseline-junit.xml
exit=1; 144 passed, 1 failed, 5 skipped; 150 collected
```

失败：`test_capacity_is_enforced_across_cli_processes`，CLI _health返回78而非预期1，报wangbin-document-cli NOT_INSTALLED。当前开发venv有源码路径但无独立发行包元数据；不能忽略首轮或修改断言来通过。

独立环境补齐：

```text
uv venv --python F:/ideaWorkSpace/wangbin-workbuddy/.venv/Scripts/python.exe C:/Users/wangbin/AppData/Local/hermes/cache/scratch/solar-pv-audit-20261028/verify-venv
uv pip install --python C:/Users/wangbin/AppData/Local/hermes/cache/scratch/solar-pv-audit-20261028/verify-venv/Scripts/python.exe -r requirements-dev.txt C:/Users/wangbin/AppData/Local/hermes/cache/scratch/solar-pv-audit-20261028/repo-baseline/dist/wangbin_document_cli-1.2.0-py3-none-any.whl
```

exit0；仅scratch venv安装44包，不修改项目依赖/锁文件或原venv。归档wheel实测SHA-256 `999251868e5d9679860eb8f0c753fc3358dccf0b96dce05edea01a2501cae4aa`。实际Python3.12.0、pytest8.4.2。

补齐后：

```text
C:/Users/wangbin/AppData/Local/hermes/cache/scratch/solar-pv-audit-20261028/verify-venv/Scripts/python.exe -m pytest tests packages/experts/wangbin-software-consultant/tests -ra --basetemp=C:/Users/wangbin/AppData/Local/hermes/cache/scratch/solar-pv-audit-20261028/pytest-equipped --junitxml=C:/Users/wangbin/AppData/Local/hermes/cache/scratch/solar-pv-audit-20261028/equipped-junit.xml
exit=0; 145 passed, 0 failed, 5 skipped; 150 collected
```

5项跳过：inventory symlink、product_factory两项symlink、security symlink、tender symlink；Windows未允许创建符号链接，不标这些安全用例通过。源码回归通过与环境健康检查前置分开，Windows结果不扩推Linux/macOS或WorkBuddy。

持久证据：`phase0-baseline-pytest.txt` / `phase0-baseline-junit.xml`、`phase0-equipped-pytest.txt` / `phase0-equipped-junit.xml`、`phase0-environment-install.txt`。回归日志及首轮失败完整保留。

## 环境发现与产品状态

`soffice`/`libreoffice`未在PATH及两个常见Program Files路径找到；`pdftotext`可发现，但不是DOCX→PDF转换器。本轮未安装转换器或生成报告，Phase5需可靠转换路径及字体/许可/视觉实测，不预判所有可能转换器均不存在。

| 维度 | 状态 |
|---|---|
| 审计/保护/复用基线 | PASS_WITH_RECORDED_LIMITATIONS |
| 既有完整收集回归 | 145通过、0失败、5跳过（独立发行环境） |
| 光伏计算/真实数据生产适配 | NOT_IMPLEMENTED |
| DOCX/PDF/测算XLSX/来源XLSX | NOT_STARTED，实物0，不适用本阶段产出但长期要求不删除 |
| 光伏产品本地测试 | NOT_TESTED（不借旧150项作光伏测试） |
| WorkBuddy安装/实际调用 | NOT_TESTED |
| 平台审核/发布 | NOT_TESTED / BLOCKED |
| 源码安全/商业许可 | 新产品待审；旧风险保留，不以回归推PASS |

## 变更与提交边界

仅新增solar-pv审计/证据文档；没有改旧产品、共用factory、catalog或台账。使用显式allowlist暂存、git diff --cached --check及敏感扫描后本地Phase0提交；提交SHA以Git读回及Phase1收口报告为准（本文件不能包含自己的未来commit SHA）。不push、不发布、不上传、不部署。Phase1新文档可能已在工作区但不会混入Phase0提交。下一阶段依赖：全部需求冻结与可执行追踪矩阵、专业研究缺口登记及跨文档复核。
