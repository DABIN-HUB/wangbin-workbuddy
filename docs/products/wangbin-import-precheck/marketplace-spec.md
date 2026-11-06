# Skill 平台/市场配置合同

依据权威 V2 §14.1、§14.9、§25–26、§28–29、§33、§39；此为拟配置字段，不是平台审核回执。技术名 `wangbin-import-precheck`；类型 Skill，拟用版本 `0.1.0`，未注册须核实；展示名 zh `数据导入前检查` / en `Data Import Precheck`。简介 zh `对照导入模板检查必填、重复、格式和关联值，输出问题明细与变更记录。` en `Check import data for missing fields, duplicate keys, format issues, and invalid reference values, with traceable findings and changes.` 仅承诺已知规则与本次参考快照，缺模板为有限检查，不保证导入成功；不接入 ERP/CRM。

SKILL.md YAML 使用 `name, display_name, display_name_en, description, description_zh, description_en, version, author, examples_zh, examples_en`；`author` 使用核实过的 `StarCore Lab` 或一致品牌值，不编邮箱；`description` 应说明用户何时触发预检。下列三条分别填入 examples_zh/examples_en，**不是 Expert quickPrompts**，逐字按 §14.9：

|序号|examples_zh|examples_en|能力/验收|
|---|---|---|---|
|1|这是客户资料和系统导入模板，帮我检查必填项、重复编码和格式问题，先不要修改原文件。|Check these customer records against the import template for missing fields, duplicate codes, and format issues. Do not modify the original.|完整预检 A01、CHAT-I01|
|2|客户编码不能重复，地区按我上传的地区表核对，帮我列出需要处理的记录。|Customer codes must be unique. Validate regions against the uploaded reference table and list records needing attention.|参考表/唯一性 A01/A05、CHAT-I02|
|3|按刚才确认的字段对应关系生成候选导入文件，并保留每一项修改记录。|Generate a candidate import file using the confirmed field mapping and record every change.|前置映射与授权/阻断分流 IMP-07/08、CHAT-I03；评测必须有真实前置回合|

逻辑根目录 `{skill-name}/SKILL.md`，需要时带 `scripts/` 真正入口与确定性检查/输出，`references/` 字段/规则/定位约定、`templates/` 仅真实使用者；不可仅靠 YAML 宣称支持流程。正文涵盖适用场景、用户原始 CSV/XLSX 和可选模板/参考表、原始资料转结构、确认门槛、真实执行入口、结果/错误/部分结果、多轮重跑、安全/未覆盖范围与文件列表、禁止越权。内部 rule_id 等不自创平台配置字段。包独立 ZIP `{技术名}-{版本}-skill-candidate.zip` 按实际工厂和官方打包层级核验，记录源码/冻结合同、依赖及许可、包外 SHA-256/清单；从干净目录解压后验证元数据、资源、A01–A14、三问/多轮、真实输出、错误。不包含 .git、缓存、密钥、真实客户资料、工作机绝对路径；未独立 QA 合格不得称可发布。评测材料 `cases.jsonl, header.json, workspace/` 与安装 ZIP 分开，字段以官方现行模板核实；本轮不登录、上传、提审或上架。

官方核查 URL：`https://open.workbuddy.cn/docs/skill`、`https://open.workbuddy.cn/docs/evaluation`（T00 已检索，实施与 QA 需复核现行规范/日期）；Expert 文档仅区分 Expert 非本产品类型。平台真实运行、评测、审核、上架：NOT_TESTED。第三方许可证及作者品牌发布可用性：待开发核验，NOT_TESTED；不可擅改现有许可证。§25–29、§33、§39。
