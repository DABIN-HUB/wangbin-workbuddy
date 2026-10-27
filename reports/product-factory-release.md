# 产品工厂本地候选验收与发布门禁

2026-10-27，本报告基于本仓库实际运行结果；**只认本地验收，不代表 WorkBuddy 平台安装、调用、审批或发布通过。发布就绪：BLOCKED。** 原有 Expert 提交状态依用户陈述记为 `USER_REPORTED_SUBMITTED`，没有审核通过回执。

## 交付和保护边界

- 新候选：`dist/wangbin-tender-analyzer-0.1.0-skill-candidate.zip`，SHA-256 `2e68809033301c97b02ec7c7fd59f7b477fcd2f1f86d515d69b5fc7b20146bc7`。`dist/` 忽略于 Git；随同产出的 `.sha256` 和 `.manifest.json` 保留在本地，不进入提交。ZIP 内包含 Skill、分析脚本、虚构示例/预期结果和人工清单模板。
- 既有软件顾问 Expert 候选 `dist/wangbin-software-consultant-1.0.0-expert-candidate.zip`：本轮最终实测 SHA-256 `577f3089d2f4707178f44ba1e5c395a99853bb9558f3e8c0e752a0e6ba2e30de`，等于受保护基线；未重打包该 Expert、未修改其产品源或审核候选。
- 文档助手和 CLI Connector 源/包未修改。原有 `python -m tooling` 四个命令仍通过隔离副本运行，不把其阶段性发布检查误当成本轮平台审核结论。

## 实际验收

| 检查 | 实际结果与证据范围 |
|---|---|
| 完整项目单测 | V1 历史基线为 `.venv/Scripts/python.exe -m pytest -q`：64 passed, 4 skipped；本轮第二批完成后的同一命令：**103 passed, 5 skipped**。跳过项均为当前 Windows 运行器无符号链接创建权限，不能据此声称运行过 symlink 攻击测试。 |
| 严格 Expert 规则 | `.venv/Scripts/python.exe -m pytest -q packages/experts/wangbin-software-consultant/tests/test_expert_candidate.py`：**36 passed**；既有受保护 ZIP 哈希不变。 |
| 原有 CLI | 在独立临时仓库副本运行 `python -m tooling validate`、`test`、`package`、`release-check`，四项退出码均为 0；隔离处理避免覆盖正式仓已有 `reports/validate.*`。 |
| 产品目录与版本 | `python -m tooling.products validate`：PASS；当前台账登记 10 个产品，四个第二批财务 Skill 的 0.1.0 候选已写入相对路径和 SHA-256；版本历史仍通过 active version 选择，不把平台状态升级为审核通过。 |
| 产品级能力 | `validate --id wangbin-tender-analyzer`、`test --id wangbin-tender-analyzer`、`package --id wangbin-tender-analyzer`、`verify --id wangbin-tender-analyzer` 均退出 0。独立脚手架、产品路径冲突与缺失指标场景已由完整单测覆盖；模板和真实服务仍需按产品补全。 |
| 样例与结构 | 本地脚本对 `fictional-tender.txt` 返回退出码 0，解析 JSON 与 `fictional-tender.expected.json` 一致；包括有证据的资格、评分、技术、日期、响应检查项与风险。该样例为虚构文本，不可替代真实招标文件验收。 |
| 确定性与归档 | 主仓重建及独立临时副本从相同源码重新打包均得 `2e68809033301c97b02ec7c7fd59f7b477fcd2f1f86d515d69b5fc7b20146bc7`；两处 `verify` PASS。候选哈希持久化于版本台账，归档证据路径为相对路径。 |
| 发布检查 | `release-check --id wangbin-tender-analyzer`：进程退出非零，状态 `BLOCKED`；归档完整性本地 PASS，平台安装/调用 `BLOCKED`，许可和依赖须人工复核。未制造虚假的 `PASS` 或审核数据。无源码的待开发候选亦为 `BLOCKED`，不能发布。 |
| 组合数据 | `portfolio` 退出 0，十个产品缺失的曝光、安装、使用、反馈、开发成本、维护成本及商业潜力均输出 `UNKNOWN`。详情见 `reports/product-factory-portfolio.md`。 |

## 第二批财务 Skill 候选

| 产品 | 本地专项测试 | 候选 SHA-256 | release-check |
|---|---:|---|---|
| `wangbin-receivable-analyzer` | 6 passed | `229b302ae5109639e3379be61cd259549197f9b22e90a8ffbcf43539dfec1929` | `BLOCKED`，local candidate PASS，platform BLOCKED |
| `wangbin-inventory-analyzer` | 7 passed, 1 skipped（symlink capability） | `b2b7d51998243d819d11237aa2652c486640133bda66a3e75fd6736691b09fdf` | `BLOCKED`，local candidate PASS，platform BLOCKED |
| `wangbin-purchase-analyzer` | 9 passed | `00aaac8d7104151c1ea06e4f709234b94145ea4fca4972d3b866540814453571` | `BLOCKED`，local candidate PASS，platform BLOCKED |
| `wangbin-sales-analyzer` | 8 passed | `571664ec2652a917ac1ea06a3b59b97e271d725f03843529228935b910cf62ab` | `BLOCKED`，local candidate PASS，platform BLOCKED |

新增的可选本地 `tooling/financial_xlsx.py` 及其专项测试为 **8 passed**；该工具复用 document-engine 安全边界，不表示普通 Skill 或 WorkBuddy 平台提供 XLSX/Python 运行时。

## 限制与人工下一步

1. 确认本 Skill 自身的许可及 ZIP 内依赖/第三方材料权利；现有门禁明确阻塞，不能因校验通过宣布可发布。
2. 在官方 WorkBuddy 环境上传**相同 SHA-256** 的候选，人工记录解析、安装、真实调用、审核结果及回执；之前只验证过其它资产，不可外推本 Skill 的平台兼容性。若审核流程不提供非公开测试路径，先取得用户对平台副作用的单独确认。
3. 使用已获授权的非敏感测试文本验证资格、评分、技术、日期、递交/签章条款；对扫描件、表格、附件、冲突日期进行人工复核，脚本不产生页码、实际得分或法律结论。短摘录可能截断/脱敏，不可替代原件。
4. 当前 Windows 无法创建符号链接，需在允许创建链接的独立环境中复核相应安全场景。
5. 取得平台授权的真实曝光、安装、调用、脱敏反馈以及开发/维护工时成本，再按版本登记证据；未取得前继续使用 `UNKNOWN`/`NOT_AVAILABLE`，不得推断商业成功。

**结论：本地产品工厂和首个文本候选可供继续人工验收；平台发布就绪 = BLOCKED，不能宣称已经通过审核或上市。**
