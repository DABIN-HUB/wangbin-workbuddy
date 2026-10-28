# wangbin 光伏预可研产品：长期冻结需求基线

基线版本 `SOLAR-PV-1.0.0`，冻结日期2026-10-28。**Phase0审计和Phase1研究/需求冻结已完成；光伏计算、四文件产品和平台调用尚未实现/验收，Phase2未启动。** Phase0本地提交 `f55cba2bc0e40aa009d48e49b9eed8b6e094e19b`；Phase1为`BASELINE_FROZEN_WITH_OPEN_RESEARCH_ITEMS`，独立审阅4项契约问题已修订，标准全文/许可/方法细节等未决不删除。证据以 `reports/solar-pv/phase1-review-and-acceptance.md` 与实际校验JSON为准，基线完成不等于产品完成。

## 后续会话必须先读

1. `00-original-user-baseline.md`：用户完整总提示词第0–11节逐字冻结；`00-baseline-manifest.json`记录来源/哈希，不因上下文压缩删减功能。
2. `01-product-requirements.md`：产品边界、L1/L2/L3、四态结论、数值诚实和不可删减范围。
3. `08-requirement-traceability.csv`、`08-baseline-contract.json`：逐需求与真实状态；`FROZEN`不等于实现PASS。
4. `11-phased-roadmap.md`及最新 `reports/solar-pv/` 阶段记录，重新运行git status/HEAD与保护校验后才继续。

本轮不进入Phase2，不创建空壳Skill/Expert，不改旧工厂/产品/catalog/许可/历史归档，不上传、不部署、不push。后续逐Phase按真实前置门禁推进；用户完整任务中已要求数值/单元/隔离/文件/安全测试，不得以默认不写测试为由删除长期明确测试要求。

## 文档导航

| 文件 | 作用 |
|---|---|
| `00-repo-audit.md`、`00-reuse-matrix.md` | 实际HEAD、源码定义/调用链、复用与禁止边界、既有安全问题 |
| `00-protected-artifacts.json` | 288个旧文件、25历史归档、22版本保护基线；新文件不在此历史集合中 |
| `00-platform-recheck.md`、`00-official-access.json` | 当期WorkBuddy官方能力、政策/更新索引的实际访问；不等于平台试验 |
| `02-report-outline-18-chapters.md` | 18章100子项、13附录26子项、18×9分类适用矩阵 |
| `03-input-data-dictionary.md`、`03-input-fields.json` | 469字段记录（446标量、22对象数组组和1前置ID标量数组），完整来源信封与分级条件；不是已实现JSON Schema |
| `04-source-registry.md`、`04-sources.json`、`04-source-chapter-comparison.csv` | 37项专业研究cohort；实际来源类型/访问/结构/许可与横向对照；不是37份工程全文 |
| `05-formula-registry.md`、`05-formulas.json` | 最低16组展开77条方法定义，未通过数值验收 |
| `05-extension-formulas.md`、`05-formula-extensions.json` | 另12条光储/布局/年均/减排/工程核对方法，仍未实现 |
| `05-field-bindings.json` | 281个公式域字段显式关联03输入、常量或计算账簿；不是运行时转换器 |
| `06-glossary-zh-en.md`、`06-glossary.json`及`06-glossary-extensions.*` | 合并189个术语，含22个最低必需缩写及全部公式名称 |
| `07-category-boundaries.md` | 九类独立schemas/config/methodology/templates/tests设计及54项专项验收；当前全NOT_IMPLEMENTED |
| `08-acceptance-design.md`、`08-acceptance-cases.json`、`08-derived-acceptance-cases.json` | 数值/缺数/边界/属性/安全/平台、章节/字段/公式/术语/工作表的具体未来验收定义；PLANNED非测试通过 |
| `08-baseline-contract.json` | 六种产品门禁、四文件ID、29sheet、集合与机器引用契约 |
| `09-risk-and-compliance.md` | 站址/并网/价格/政策/税/隐私/授权/解析与平台风险 |
| `10-four-file-acceptance.md` | DOCX/PDF/两个XLSX的真实格式、同源hash、19+10工作表、视觉/编辑/重算、整集事务发布与六门禁 |
| `12-canonical-result-contract.md` | 单一确定性结果JSON、指标及跨文件引用/重算契约 |
| `00-source-index.json`、`05-additional-sources.json` | 合并专业、政策、平台与公式帮助来源；来源ID与实际项目输入证据分开 |

## 可执行检查

```text
python docs/solar-pv/verify_baseline.py
python docs/solar-pv/verify_baseline.py --release
```

默认只读校验原文哈希、文档/目录、字段/公式/词表、来源统计、分类、四文件sheet、逐需求引用与证据状态、旧资产哈希；**不是计算/报告/平台测试**。默认exit0仅表示冻结文档机器完整性通过。`--release`还要求全部产品需求及六门禁真实PASS；当前必须非零BLOCKED，不得通过删需求/改门禁绕过。

矩阵`source_line`对原文全部非空正文行完整覆盖；章节、字段、公式、术语、分类、工作表和反向验收追加独立行。`data_source_ids`在此阶段是规范/研究参考，不代表已经获取本站实际气象/电价/并网证据；每个项目的U/D值必须另带真实provenance。公式域中间账簿不应被当成首轮问用户的长表单。

`变量/术语词典`保留为原始逻辑sheet名，实际Excel禁止斜杠，因此物理名映射为`变量-术语词典`；映射明确登记，不偷删此表。

## 待核验不等于删需求

标准全文与合法授权、部分WAF/JS资料、税制与融资/设备细则、真实资源适配器、温度子模型、可靠PDF转换器/字体和平台安装依赖均留命名风险/阻断。工具环境未提供web.run，实际用公开检索＋原站匿名HTTP/HTTPS＋PDF解析留真实访问证据，不声称使用过未提供工具。研究索引只保存有限摘要/定位，不把第三方整本报告打入仓库/商用包。

本地回归通过、光伏真实报告可用、平台安装成功、平台审核通过必须分别判定。即使下一Phase文档/单元测试通过，九类任何未实现能力仍NOT_IMPLEMENTED。任何范围变更需保留原条款ID和用户批准记录，不能因换会话而缩减。
