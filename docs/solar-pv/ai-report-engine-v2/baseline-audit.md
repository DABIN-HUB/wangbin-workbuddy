# 2.0 R13基线与模块审计

## 已执行事实

原工作区实际根目录 `F:/ideaWorkSpace/wangbin-workbuddy`，分支main；HEAD和 `git ls-remote origin refs/heads/main` 均为 `ecaac498e3d14dbae4874e7fa46e63d74c5da2df`，remote为用户指定GitHub仓库；status及diff为空。未reset/rebase/merge/stash/清理。第二附件所述R11远端并非本次实际基线。

目标路径不存在、分支未存在后创建 `refactor/solar-pv-ai-report-engine-v2` 工作树；初始HEAD仍R13且status为空。其他现有工作树不触碰。

R12→R13只有 `report_claims.py` 的读者预览W/V空格、`report_export.py` 的公式说明尾标点，以及39号说明文档；3文件32增3删。计算未变。原PDF公式复制搜索、完整数学语义、真实资料和平台发布阻断均继承为未关闭事项，不继承旧报告视觉PASS。

Python实际3.14.9，当前解释器有docx/jsonschema/pytest/openpyxl，但document engine未安装。源码执行显式将两个src加入PYTHONPATH（Windows以分号分隔）；不混用pip→Python3.11。未安装或改动依赖。

Catalog实际加载校验冻结文件及effective definition：469字段、89公式、281映射；词典文件169+20=189；源码18章100节13附录26节。公式主表77与扩展12不能漏算；冻结文档历史NOT_IMPLEMENTED不能直接作为R13运行状态。

## 真实调用链及处置

以下路径均相对于 `services/solar-pv-engine/src/wangbin_solar_pv/`。

| 模块 | 判定 | 依据与边界 |
|---|---|---|
| `report_export.py` | 保留但封装 | `ReportModel.from_result`先validate_result；`_export_report`→`_write_docx`；复用格式表图/Excel/PDF，不本轮替换完整入口 |
| `report_narrative.py` | 需要重构，旧代码暂保留 | ITEM_QUESTIONS由guidance供_item_evidence消费；部分规则先验写“合成/尚未形成”，不得直接用作新项目结论；新规格独立研究任务替代其生产正文作用 |
| `report_claims.py` | 分离职责，保留来源封装 | CHAPTER_FIELDS/METRICS、category_fields及_source_value可复用；build_claim同时拼接判断、_project_narrative/_research_finding/_settlement_narrative，AI证据包不得调用这些正文函数 |
| `report_equations.py` | 保留直接复用，本轮不改 | convert_equations要求89式；DISPLAY_LATEX仅显示映射；F-UNIT-COST-WP-KWP原始冲突仍待裁定 |
| `report_word_styles.py` | 保留直接复用 | WORD_FORMAT、configure、borders、equation_paragraph；不改字体/版式 |
| `report_display_numbers.py` | 保留直接复用 | 受控显示精度，canonical值不改；IRR根集必须用原专用显示入口 |
| `report_numbering.py` | 保留直接复用 | 稳定ID到Heading和书签；完整检查与局部章节结构检查分开 |
| `calculation/financial_metrics.py` | 当前不允许修改 | 有NPV/IRR根集/静动态回本/CFADS等明确边界；阶段C如需补充必须独立验证 |
| `calculation/financial_ledger.py` | 保留封装读取，本轮不改 | financial-ledger annual保存现金税、更换、应计/实付与营运资金；taxable_income_project不是独立会计净利润 |
| `calculation/scenario_runner.py` | 保留封装，Phase C审查 | prepare→run→seal真实重算；PR替代路径及折现率终期绑定存在显式阻断；不可用基准缩放生成候选 |
| `catalog.py/result_contract.py/serialization.py` | 保留直接复用 | 严格JSON、Decimal、定义锁、result_hash及source/formula/metric引用检查 |
| Skill/Connector/现有report与ground-report CLI | 当前不修改 | 不让新框架未经试点替代现有四文件生产链；平台安装不在本轮 |

**固定正文的实际入口**：`_write_docx:2723 → _item_evidence:2337 → build_claim → _project_narrative → _research_finding`，然后 `_add_professional_narrative`写入。`_professional_narrative`目前只有定义，内部调用`_r4_special_narrative`；`_chapter_intro`也只有定义。不能仅编辑这些旧函数宣称新正文生效。摘要`_project_summary`、附录`_appendix_content`/`appendix_finding`、图解`_chart_interpretation`、READER_APPENDIX_LEADS亦是固定写作面。Phase G逐调用点验收后才可删，不在A/B删除。

## 平台与模型边界核验

官方页面已通过Python urllib实际读取：`https://open.workbuddy.cn/docs/skill`，支持Skill资源与AI通过Bash执行脚本；`https://open.workbuddy.cn/en/docs/connector`描述托管Python及CLI自行管理授权；`https://open.workbuddy.cn/docs/openapi`列出OAuth2.1、开发者应用、clientId/clientSecret及云端任务/ACP等能力。此前web_extract后端不支持内容提取，三次均失败，未将失败计为页面已读；随后urllib实际取得三份HTML，原始副本位于Hermes scratch的solar-v2-platform目录。

官方有API不代表本仓库已实现模型provider。当前solar源码没有厂商SDK、chat/completions或llm_provider入口；Connector cli.json只做依赖安装和import状态检查，没有模型会话授权。未读取任何凭据文件，没有用户提供的开发者应用/已授权模型适配配置。本轮不向第三方应用发起新授权、不复用Hermes令牌，不凭文档宣称平台调用成功。

采用受控章节文件交接接口：prepare生成最小请求，宿主模型在其已授权环境执行，accept严格验证身份和结果。本地没有实际宿主调用回执时保持 `MODEL_INTEGRATION_BLOCKED`。未来自动provider适配必须固定支持方式并获得授权，不将通用shell执行器当成模型实现。

## 保护与运行约束

原始样例canonical只读使用 `tests/fixtures/solar-pv/phase7l-r2-delivery/{type}/canonical.json`，先用Catalog/validate_result校验；不复制或修改封存案例。测试输出到独立worktree的忽略`.runtime/solar-pv/ai-report-engine-v2/`，不在原`.runtime`写入。不启动全仓回归。旧候选dist只读验证，当前不构建2.0平台候选。
