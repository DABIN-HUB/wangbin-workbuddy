# WorkBuddy 产品工厂（本地候选）

本工具在现有 `tooling` 和 `packages` 之上增加产品级工作流，不替换已有 `python -m tooling validate|test|package|release-check`。首批登记 3 个既有资产及 5 个新候选；本轮仅实现招标分析 Skill。注册表 `products/catalog.json` 保存产品、版本和审核证据；`products/metrics.json` 保存各版本指标。没有平台证据时使用 `UNKNOWN` 或 `NOT_AVAILABLE`，不要填零或编造审核通过。

## 产品级命令

从仓库根目录运行；也可在命令末尾传 `--root <仓库目录>`：

```bash
python -m tooling.products list
python -m tooling.products validate
python -m tooling.products init --id wangbin-receivable-analyzer
python -m tooling.products register-version --id <已有产品ID> --version <新语义版本>
python -m tooling.products validate --id wangbin-tender-analyzer
python -m tooling.products test --id wangbin-tender-analyzer
python -m tooling.products package --id wangbin-tender-analyzer
python -m tooling.products verify --id wangbin-tender-analyzer
python -m tooling.products release-check --id wangbin-tender-analyzer
python -m tooling.products portfolio
```

`validate` 不带 ID 检查整个注册表，带 ID 检查单个产品。`init` 只对已登记且尚无源目录的产品生效；Connector 还须传 `--connector-mode cli` 或 `mcp`。`register-version` 只附加新版本并选为 active，旧记录不可覆盖；随后须把该产品源码版本字段更新为新版本，并重新校验、测试和打包。已生成的旧 ZIP 不得改写；当前 `verify` 只比对 active 版本与当前源码，历史版本仅保存归档哈希，不能用更新后的源码复验旧包。Expert/Connector 的模板是待完善脚手架：作者、真实服务、授权、头像、说明和许可须人工审查；不能把生成目录视为可发布候选。`test` 只调用该产品登记的测试路径；没有对应测试返回 `NOT_TESTED`，不能偷换为平台运行通过。`package` 只打包指定产品，成员按类型限于受审查目录，稳定排序/时间戳/权限；同名且不同内容的 ZIP/manifest/sidecar 不能覆盖。`verify` 对照当前源码、成员及 SHA-256；产品源变动后必须重新评估是否升版，不要覆盖旧审核版本。`release-check` 的本地候选失败返回非零，但本地通过也不代表平台发布就绪。

记录真实数据时须有可追溯来源：

```bash
python -m tooling.products record --id wangbin-tender-analyzer --field exposures --value <真实曝光整数> --evidence "<真实平台导出记录编号>"
python -m tooling.products portfolio
```

尖括号是待填写的占位符，不是产品实测数据；没有真实导出记录时不得执行或填入台账。指标字段：`exposures`（曝光）、`installs`（安装）、`uses`（使用）、`feedback`（反馈数量）、`review_result`（审核）、`development_cost`（开发成本）、`maintenance_cost`（维护成本）。数字必须是非负、来自真实记录；审查、成本和量纲需要登记者核实。用户自行提供的证据在系统里标记为“user-provided; unverified”，不能自动变成平台核验。组合报告保留缺失项；没有审核/使用证据时审核成功率与商业潜力为 `UNKNOWN`，安装率只在真实曝光和安装均可用且曝光大于零时计算。

## 招标 Skill 使用

```bash
python packages/skills/wangbin-tender-analyzer/scripts/analyze_tender.py --input packages/skills/wangbin-tender-analyzer/examples/fictional-tender.txt
```

该脚本本地分析用户已授权的 UTF-8 文本，不解析 PDF、扫描件或复杂表格。只输出源文本行号和原文引文；投标资格满足与否、实际分数、无法识别的截止时间一律待核实。示例源和预期 JSON 位于该 Skill 的 `examples/`。WorkBuddy 普通 Skill 是否具备执行此脚本的 Python 环境、附件路径、安装与真实对话能力未验证。含投标报价、合同及个人信息的正文不应进入未授权日志/远端模型；本地脚本的输出也包含原文片段，应仅交给授权用户。现有文档引擎针对不可信文件的高风险限制见 `reports/phase4-threat-model.md`，本 Skill 不以复用引擎为平台安全性背书。

## 发行门禁与人工步骤

`release-check` 分开列本地校验、产品测试、包完整性、许可证/依赖审查、平台安装/对话及发布。即使本地候选通过，平台安装、真实调用、账号/审核资格及公开发布仍为 `NOT_TESTED`/`BLOCKED`。需要账号所有者在官方授权入口确认：ZIP 解析目录、元数据、安装、调用和证据引文，在不泄露采购正文的前提下保存脱敏回执；若入口会正式提交审核或公开发布，另行取得授权后再操作。不得用本地 pytest 代替这些步骤。软件顾问 Expert 的 `USER_REPORTED_SUBMITTED` 仅依据用户陈述，不等于 APPROVED；其旧候选包与 SHA-256 基线保持不变。
