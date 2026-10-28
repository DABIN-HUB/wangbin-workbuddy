# Phase 0 — 复用与禁止复用矩阵

## 0. 适用范围与判定

- 仓库 `F:/ideaWorkSpace/wangbin-workbuddy`，源码基线 `c9b73291200e904a875ec2e2642f7492bd311036`（main）。行号为此基线实际定义行，不是文档猜测。
- 本轮只新建本矩阵及另两份审计文档；**不执行**产品 test/package/release-check，不调用会写旧报告的 upload-list/legacy validate；不修改旧源码/模板/许可/catalog/metrics/历史 ZIP。
- `直接保留`：后续在原工程框架中按原契约使用，不复制另建一套；`有条件复用`：必须新增领域适配、授权、边界与测试，不等于本轮已实现；`只参考结构`：不得拷贝行业业务与未验证能力；`禁止作为安全/业务结论复用`：可以留存历史代码，但不将其当新产品门禁依据。
- 此处“待验证”是明确未完成事项；本子代理未跑任何测试。父代理 scratch 回归复跑 exit0，最终计数/日志尚待父代理整合。历史报告与当前实测严格分开。

## 1. 产品工厂与 CLI（不另建注册中心）

| ID | 实际源码/定义行号 | 已实现功能 | 复用判定与方式 | 禁止复用/必须保留的边界 |
|---|---|---|---|---|
| RF01 | `tooling/product_factory.py:89 load_catalog`、`:93 validate_catalog`、`:171 get_product` | schema/type/status/review/version/相对路径与身份校验；读取真实 JSON | 直接保留 catalog 为唯一现有产品台账；光伏未来增量注册 | 不能覆盖旧22版本记录或把 BACKLOG/未知 SHA 当候选；不能凭 enum 写 APPROVED |
| RF02 | `:40 _safe_relative`、`:58 _relative` | 拒绝绝对/`..`/symlink、约束仓库证据路径 | 有条件借鉴相对路径契约 | 未显式检查 Windows junction，非 OS 权限边界；不能替代附件受限根目录检查 |
| RF03 | `:65 _atomic_bytes` | 同目录临时写、flush/fsync、os.replace | 有条件复用单文件台账写模式 | 会替换目标；不是四文件整体事务，也不是不可覆盖用户输出 API；本轮不调用 |
| RF04 | `:79 _version_entry`、`:181 _source`、`:185 _version` | active 版选择及源码定位 | 直接保留版本选择；新产品必须不同 ID/源码路径/候选路径 | 当前 source 非每版本独立快照；不能用当前源证明历史包字节相同 |
| RF05 | `:189 init_product` | 登记后初始化类型目录；未登记模板/元数据名称也纳入碰撞检查 | 后续授权后只初始化新光伏产品 | 未完成 TODO 骨架不是发行成品；保留旧模板，不绕过身份碰撞 |
| RF06 | `:268 _files` | 按 Skill/Expert/Connector 顶层白名单、后缀、链接/私有缓存过滤；排序 | 直接保留既有产品静态打包隔离 | 当前不接受 DOCX/PDF/XLSX 等二进制输出；不扩大旧产品打包面以容纳客户附件；不能当运行时文件沙箱 |
| RF07 | `:296 validate_product` | 类型校验、产品/manifest身份、TODO、源码凭据模式检查 | 有条件复用通用本地源码门禁；新产品按真实能力声明 | 不验证 PV 公式、输入成熟度、18章/四文件、真实来源或平台调用；不把未发现凭据当完整隐私认证 |
| RF08 | `:340 test_product` | 从登记路径调用同解释器 pytest，缺测试 NOT_TESTED | 保留产品级测试入口；未来注册光伏独立测试 | **会运行测试**；本轮不调用。不以包内测试/静态场景替代 WorkBuddy 实机 |
| RF09 | `:357 _paths` | 由 ID/version/type 派生新式 zip/sidecar/manifest 路径 | 新产品可沿用命名契约 | 老文档 Skill 与软件顾问 manifest 路径有历史命名；不能派生路径取代 catalog 精确历史路径 |
| RF10 | `:367 register_version` | 拒绝重复版本，追加 immutable 元数据并可激活 | 后续新增光伏发行版本的入口 | 不是注册全新产品 API；会写 catalog；本轮不补旧 UNKNOWN，不重写历史或改 active |
| RF11 | `:397 package_product` | 单次内存 payload、排序/固定时间/权限 ZIP、readback、拒不同同名产物、同步 catalog | 未来独立光伏 Skill/Expert 按产品打包；不新建并行工厂 | **会写 dist/catalog**；三件 archive/sidecar/manifest 和 catalog 并非跨文件事务；无授权不调用 |
| RF12 | `:463 verify_package` | 同时比较 active 版源码、成员、大小、sidecar、manifest、catalog/hash | 未来新式候选的本地完整性校验 | 不是任意历史归档检查；不同历史 manifest 命名/源码升版不能强行套用；不代表平台解析 |
| RF13 | `:494 record_metric` | 有证据字段、非负有限值、版本绑定、用户提供未核验 scope，拒本地造平台 APPROVED | 直接保留真实经营指标录入合同 | UNKNOWN 不转零；工程发电/成本 provenance 不能借经营指标台账代替；本轮不写 metrics |
| RF14 | `:519 portfolio_report` | 按 active 版提取指标、真实分母安装率/成本；缺数 UNKNOWN | 直接保留组合观察模式 | 无成功率/商业潜力证据保持 UNKNOWN；不能预测光伏项目成功概率 |
| RF15 | `:552 _license_dependency_gate` | 产品 LICENSE/声明/rights/dependencies/platform agreement 分开核验 | 复用独立许可门禁模型，新光伏产品自行决定许可 | 根 MIT 元数据不扩展覆盖四专有 Skill；文件名 LICENSE/PROPRIETARY 不证明分发权；不能沿用旧 PASS 到新包 |
| RF16 | `:603 release_check` | validation、package、tests、license、similarity 分层，平台/发布 BLOCKED | 后续可扩展新产品 profile 中的工程门禁；保留 legacy | 会跑测试；尚无18章/来源/数值/四文件校验，不能直接称 PV 发布就绪 |
| RF17 | `:643 _archive_inventory` | 依 catalog 精确候选路径读取大小/hash/ZIP目录/CRC | 有条件参考只读归档盘点实现 | 本轮独立只读盘点只读中央目录/hash，不调用其 CRC；已登记 UNKNOWN 不凭存在性自动变 PASS |
| RF18 | `:685 _dependency_inventory`、`:707 _upload_state`、`:729 upload_list` | 依赖声明、人工试传状态和组合清单 | 参考“本地包/平台/许可独立”证据模式 | `:773` 写旧 `reports/workbuddy-upload-list.md`，非文件系统纯只读；旧提交/发布状态逻辑不能当新的独立平台证据 |
| RF19 | `tooling/products.py:12 main` | 独立 `python -m tooling.products` CLI 分派与退出码 | 直接保留入口，新光伏命令优先增量接现有体系 | `list/portfolio` 与 `init/record/register-version/package/test/release-check/upload-list` 副作用不同，不能混称审计只读命令 |
| RF20 | `tooling/generators.py:10 generate_skill` | Skill frontmatter/manifest 与 refs/scripts/templates 骨架 | 只参考/复用结构生成；调用前由 factory 冲突防护 | 函数自身 `exist_ok=True` 且直接写目标，不应绕过 factory 对旧目录调用；默认办公文案不是光伏业务 |

## 2. 校验器、旧命令与模板

| ID | 实际源码/定义行号 | 已实现功能 | 复用判定 | 禁止复用/新增前提 |
|---|---|---|---|---|
| RV01 | `tooling/validators/project_validator.py:17 _read_frontmatter`、`:34 validate_skill` | safe_load 对象、必填双语字段/semver/name/资源引用 | 有条件复用 Skill 本地结构检查 | 不证明脚本依赖自动托管、公式与站址数据真实；资源路径最终还需安全边界 |
| RV02 | `:60 validate_expert` | 基础 plugin 字段、类型、三tags/quick prompts、agents 文件存在 | 只做结构基础层 | 不替代 strict prompt-only 元数据/头像/一致性/长度校验；不能为了新功能降低旧门禁 |
| RV03 | `:88 validate_connector` | CLI/MCP/skill-only 分支、配置/图标、跨平台命令、status/认证配对、Python最小版本 | 有条件复用 Connector 基础结构 | 声明 Python 运行时不等于包可分发/依赖可安装/真实调用通过；仅本地结构规则，不冒充最新平台规范 |
| RV04 | `:144 validate_project` | 全仓库目录/产品结构及凭据扫描 | 继续保留回归能力 | 顶层 CLI 会写报告；扫描不是隐私完备性证明；只读审计不执行 |
| RV05 | `tooling/expert_rules.py:16 validate_prompt_expert`（`:41-62`） | prompt-only Expert：中文简介40–50字、名称≤15字、双语字段、默认prompt一致、头像512×512/大小、禁止front.skills/front.tools及meta.dependencies/meta.skills | 直接保留旧产品严格 profile | **不是“官方禁止 skills/dependencies”**。父代理2026-10-28已确认官方可选能力；Phase7新隔离profile+实机验证，不改旧规则来假通过 |
| RV06 | `packages/experts/wangbin-expert-template/agents/wangbin-document-expert.md:11` | 旧模板有 skills 列表；软件顾问候选无此依赖 | 只参考目录/frontmatter；明确模板与纯提示产品不同 | 不能把复制模板误称已集成已注册 Skill；不能在现有 prompt-only 校验路径下偷偷保留 skills |
| RV07 | `tooling/phase5_expert_packager.py:24 validate_source`、`:34 build` | 固定软件顾问身份 wrapper；旧 ZIP 路径打包与读回 | 只参考 wrapper 保持旧 API/身份的方式 | `build`直接 `ZipFile(...,"w")`覆盖同名受保护包；本轮及未来新产品不得调用来打光伏包 |
| RV08 | `tooling/cli.py:31 main`、`tooling/packager.py:22 build_candidate_zip`、`tooling/release_check.py:21 run_release_check` | 原工程CLI/固定1.0.0文档候选、报告写入/测试聚合 | 保留兼容性，隔离副本中验证 | 原路径固定，运行可改旧 dist/reports；release-check 的文档存在/本地测试推安全PASS不适合作新产品完整门禁 |
| RV09 | `tooling/validators/zip_validator.py:12 sha256`、`:20 validate_zip` | 文件SHA-256、遍历成员读内容并报告 | hash流式做法可参考；**禁止直接作为新安全门禁** | `:27 "../" in name.split("/")`未正确检测`..`段；缺显式展开预算；本轮未修，后续需专门修复与用例 |
| RV10 | `tooling/similarity.py:26 _profile`、`:84 _pair`、`:123 similarity_check` | AST/输入输出/元数据配对；人工REVIEW_REQUIRED | 参考全产品反同质化证据模式 | 内部分类与形状分数不是平台阈值/法律结论；覆盖不完整时不能宣称功能同/不同已获认证 |

## 3. 附件引擎：有限读取，不是报告生成器

下表 `src/` 均指 `services/document-engine/src/wangbin_document_engine/`；实际生产源码已逐一阅读，不引用 build/lib 缓存副本。

| ID | 实际源码/定义行号 | 现有功能 | 可复用部分 | 禁止宣称/后续条件 |
|---|---|---|---|---|
| RD01 | `src/security.py:23 _has_link_component`、`:30 SecurityPolicy`、`:43 validate_input` | 后缀/大小/受限根、symlink/junction/签名/Office容器 | 有条件复用附件输入白名单与可配置预算 | 正常代码路径检查不约束被攻陷解析器的OS权限；根目录授权仍须用户提供 |
| RD02 | `:70 snapshot_input` | FD身份/普通文件/大小/mtime验证、私有快照、重验、finally清理 | 有条件复用单次受控快照的思路 | 不保证全部TOCTOU/同用户敌对目录竞态已解决；不默认真实商业附件可安全解析 |
| RD03 | `:104 validate_batch`、`:111 validate_output_dir` | 数量/累计体积、输出在输入根外、禁止链接、创建输出目录 | 参考分离输入输出的职责 | 方法会mkdir，不是纯路径查询；允许输出根非用户授权的任意系统位置问题需新产品明示范围 |
| RD04 | `:128 validate_signature`、`:141 validate_container`、`:169 is_within` | PDF头尾、Office入口、压缩条数/比率/体积/穿越/加密预检 | 有条件复用容器预检 | 不等价完整格式有效/OCR/漏洞防护；通用入口没有与 financial_xlsx 相同的全宏拒绝 |
| RD05 | `src/engine.py:17 DocumentEngine`、`:24 parse_file`、`:75 parse_many`、`:115 _sections` | 单/批文本提取、错误隔离、Markdown标题/文本行号 | 可为资料解析适配层提供有质量提示的原始文本 | 非18章生成、页码定位、可靠表格坐标、发电/财务或事实核验；`adapter`注入在主进程可绕过子进程资源边界 |
| RD06 | `src/markitdown_adapter.py:11 MarkItDownAdapter`、`:17 convert` | `enable_plugins=False`调用转换器；文本/元数据/复杂布局提示 | 仅有条件复用受支持格式文本抽取 | 关闭插件≠网络/权限沙箱；扫描/OCR/复杂表格不保证；质量提示不能丢弃 |
| RD07 | `src/process_runner.py:31 _send_result`、`:38 _apply_posix_limits`、`:56 _worker`、`:69 convert_in_process` | spawn子进程、JSON IPC32MiB、壁钟超时/直接子进程回收、POSIX rlimits | 借鉴明确错误码、有限IPC、受控进程执行 | Windows无硬CPU/内存、无OS降权/网络封锁/完整后代回收；不得复用“强安全沙箱”声明 |
| RD08 | `src/resource_slots.py:22 _slot_dir`、`:37 hold_resource_slot` | 同用户临时目录OS文件锁，两槽并发 | 有条件借鉴合作式容量管理 | 非每机器/跨用户/多租户硬配额；单任务仍可能超限；调用会写锁文件 |
| RD09 | `src/models.py:9 ParsedDocument`、`:17 DocumentResult`、`:34 BatchResult`、`:52 SpreadsheetSummary`、`:64 ExportResult` | 稳定dataclass结果、文本/质量/错误/计数 | 只复用结果分层与错误模式 | 不含新需求完整provenance、单位、input/result_hash/模型版本、U/D/C/AI；不要硬塞PV领域结果替代新契约 |
| RD10 | `src/errors.py:4 EngineError`、`:11 SecurityViolation`、`:15 ParseFailure`、`:19 ExportFailure` | 稳定错误码/公开消息类型 | 有条件复用统一错误公开层 | 报错脱敏并不证明所有日志/输入标识不泄漏 |
| RD11 | `src/metadata.py:11 file_metadata` | 文件名/扩展名/MIME/大小/mtime | 参考本地资料元数据层 | 没有输入内容哈希、许可、获取时间/有效期、地理适用性、来源位置/版本；不能冒充来源注册表 |
| RD12 | `:22 safe_output_path`、`:35 publish_new_file` | 清理文件stem、冲突后缀、同目录硬链接无覆盖发布 | 有条件复用安全命名/不覆盖语义 | 不是四文件整体事务；需补Windows保留名/长度/并发边界与新四文件命名合同；硬链接依赖文件系统支持 |
| RD13 | `src/spreadsheets.py:20 SpreadsheetService`、`:24 inspect`、`:57 deduplicate` | read_only检查、去重、CSV/XLSX写入重开、临时清理 | inspect可作为有限输入预检；写后重开和无覆盖模式可参考 | **不得把deduplicate用于负荷/气象数据预处理**而删合法重复时段或业务行；非财务工作簿/公式重算服务 |
| RD14 | `:165 _bounded_rows`、`:183 _safe_value`、`:189 _validate_export` | 行/单元格/文本/迭代deadline、危险前缀加引号、重开验证 | 有条件借鉴预算与输出注入防御 | 加载/保存不受强制中断；只保证局部前缀策略，不能宣称任意Excel外链/宏/公式恶意样式都被拒绝 |
| RD15 | `src/serialization.py:9 write_json`、`:14 result_markdown`、`:41 write_markdown` | JSON/Markdown直接输出/写文件 | 只参考序列化分层 | 默认可含全文且可覆盖文件；**不直接复用为商业附件审计日志或原子四文件输出**；无PDF/DOCX生成能力 |
| RD16 | `src/__init__.py:2-5` | 引擎公共API导出 | 保持旧API不变；新领域模块以适配方式依赖 | 不修改公共名称破坏老CLI/Skill；不据import成功宣称发行元数据就绪 |
| RD17 | `services/document-engine/src/wangbin_document_cli/main.py:19 _health`、`:41 _parser`、`:62 main` | 发行版本/依赖检查、version/doctor/status/parse/batch/deduplicate；失败非零 | 参考本地CLI健康检查与真实错误返回模式 | 只加PYTHONPATH不能满足importlib.metadata；会将原文结果发stdout，外部日志/远端模型需额外授权 |
| RD18 | `services/document-engine/pyproject.toml:6-19`、`packages/connectors/wangbin-document-cli/cli.json:2-13` | CLI发行1.2.0、Python>=3.12<3.15、固定依赖；Connector安装声明 | 只参考独立wheel/CLI+Skill架构选择，不擅自选远端微服务 | 现有归档wheel不证明公共索引可获取/WorkBuddy已安装；此轮不运行联网安装，不复制旧文档服务的产品身份 |

## 4. XLSX 预处理、招标证据与纯提示专家

| ID | 实际源码/定义行号 | 已有功能 | 可复用 | 禁止复用与必要新增 |
|---|---|---|---|---|
| RX01 | `tooling/financial_xlsx.py:36 _reject_macros` | ZIP成员/Content_Types识别宏载荷并拒绝 | 有条件复用宏拒绝策略 | 当前在source而非后续统一staged快照上检查；需保持同一受限快照，不能泛称所有Office主动内容已拒绝 |
| RX02 | `:58 _formula_cell`、`:67 _scan_rows`、`:85 _scan_workbook` | 公式/以`=+-@`开头的字符串拒绝，全工作簿扫描，所选sheet取行 | 参考“输入值/公式明确隔离”安全约定 | 拒绝负数字符串但保留数值负数；不能不经域校验把它当全场景财务输入规范；非公式求值 |
| RX03 | `:100 _write_csv`、`:116 convert_xlsx_to_csv`、`:185 main` | 显式input/root/output/sheet、保序保重、CSV≤1MiB、无覆盖发布、错误不输出路径/原文 | 有条件复用安全读取/保留重复/脱敏CLI模式 | 不是NPV/IRR/DSCR引擎、不是测算XLSX输出；多快照/重复扫描不自带硬资源隔离；keep_links=False不是全面显式拒外链 |
| RT01 | `packages/skills/wangbin-tender-analyzer/scripts/analyze_tender.py:56 _redact_sensitive`、`:65 _evidence`、`:77 _item` | 限长120字符、常见敏感值脱敏、basename/1起文本行、待核实 | 只参考最小证据与未核实表达 | 脱敏是启发式，不是完整隐私检测；excerpt并非原始字节逐字证据；不能冒充PDF页码 |
| RT02 | `:200 analyze`、`:374 _read_authorized_utf8`、`:399 main` | 单文件UTF-8 TXT/MD≤1MiB、资格/技术/评分/日期/checklist；拒普通类型/编码错误 | 只参考小MVP输入/稳定错误/fictional样例模式 | 不复制招标正则为工程资料理解；authorization_verified=false；父目录链接/竞态不是这里闭环的安全边界 |
| RT03 | `packages/skills/wangbin-tender-analyzer/SKILL.md:22-64`、`templates/tender-checklist.md:3-18` | 明确本地/平台、缺数、摘录、人工核对 | 可参考“能力契约与限制一致”的写作/测试原则 | 该模板不是18章PV预可研、L1/L2/L3、字段字典/公式表；不得标题替换直接当已实现 |
| RE01 | `packages/experts/wangbin-software-consultant/agents/wangbin-software-consultant.md:18,20,24` | 已确认/假设/待确认/变更；逐轮至多三问、输入→处理→输出/验收 | 只借鉴多轮交互与资料补齐模式 | 软件模块/设备协议不等于PV场址/结构/电价/并网核实；旧Expert及模板不改 |
| RE02 | 同文件`:32-38` | 人天/缓冲/单价/第三方费用边界及预算缺口 | 只参考“不倒推迎合预算”的方法论 | 禁止移植人天成本/演示单价为工程造价；提示词算术不能替代确定性PV引擎/数值测试 |
| RE03 | 同文件`:42,46`；README`:3,15,17,33` | 只交付实际写出的Markdown，不承诺Word/PDF；数据最小化、MIT范围 | 参考真实交付声明与隐私边界 | 不把旧Expert宣称为光伏四文件生成器；保留MIT与现有身份/ZIP不变 |
| RL01 | 四经营 Skill 的独立`LICENSE:1-12`、catalog各产品`license_policy`；软件顾问`LICENSE:1-21`；service`LICENSE:1-21` | 独立PROPRIETARY与MIT并存 | 逐产品保留许可，新增产品先单独权利/依赖/协议审查 | 不批量MIT、不撤销旧许可；不因为同作者/同仓库就复制专有产品代码到新开源包；未知许可证REQUIRES_REVIEW |

## 5. 真正需要新增的能力与验收，不得拿“复用”填空

| 能力 | 当前证据/缺口 | 新增隔离边界与验收依赖 |
|---|---|---|
| canonical result / provenance / units | 引擎只读文本/文件元数据；无PV canonical JSON及完整来源账本 | 新建版本化输入/结果/公式/来源契约，U/D/C/AI、输入/结果哈希、run_id/source_snapshot_id，不能依赖LLM补数 |
| L1/L2/L3 与缺数降级 | 招标/软件顾问有待核实/假设模式，但没有PV成熟度 | 新增资料成熟度、冲突与门槛；所有草稿醒目标注，不把目标IRR作为反推参数 |
| P0工程分类 | 旧产品均非PV | `industrial_rooftop`与`utility_scale_ground`各自schema/methodology/template/scenario tests；屋顶荷载/负荷消纳和地面土地/送出/全额售电不可互串 |
| P1/P2 | 未实现农光/渔光/储能/公共/户用/车棚BIPV/荒漠矿区 | 单独路线与NOT_IMPLEMENTED；不把同一模型换标题视为新分类已支持 |
| 资源/发电/消纳 | 无GHI/DNI/DHI/POA/PR、逐时能量守恒确定性引擎 | 单位与AC/DC边界、损失避免重复扣除、同期负荷、电价合同、限发/ExportLimit与闰年专测 |
| CAPEX/OPEX/税折旧/融资/财务 | 四经营CSV产品不计算投资项目全周期现金流 | 项目/股东两套现金流、折旧非现金不重扣、税制来源、IRR无根/多根、NPV/LCOE/DSCR独立参考校验 |
| 数据源适配 | 无本项目许可核实/真实站址来源 | 父代理先做真实官方/数据文档研究；新增授权/超时/配额/缓存/失败降级，不伪造“真实气象/工程造价” |
| 18章DOCX+PDF | 附件提取不是报告生成；测试fixture会生成简单PDF/DOCX但无生产18章模板 | 新增渲染器/中文样式/目录域/图表/公式逐符号/词汇表/附录；PDF转换器不可用明确BLOCKED；肉眼抽样 |
| 测算XLSX+资料XLSX | 旧xlsx功能为inspect/deduplicate/CSV输出 | 新增sheet contracts、静态快照或经验证重算缓存声明、数值同源、注入/外链/宏门禁、重开校验；不伪称openpyxl自动求值 |
| 四文件一致性与原子发布 | 单文件硬链接/临时写不构成四文件事务 | 全部来自同版本同result_hash JSON，关键指标/图表/附录一致，部分失败不返回总体成功，不覆盖用户已有文件 |
| Expert调用链与运行时 | strict prompt-only现有规则收窄；父代理当前官方确认可选skills/dependencies | Phase7新增隔离profile与新的产品资产，保留旧validator；真实ZIP解析/安装/调用/依赖/文件导出逐项证据；普通Skill依赖自动安装仍UNKNOWN |
| 平台、商业与许可 | UNKNOWN/NOT_TESTED/USER_REPORTED_SUBMITTED不等于审批/发布 | 本地数值/源码/包、许可、平台运行、审核、公开发布分门禁；默认不push/上传/收费/部署 |

## 6. 测试与证据模式复用的限制

- 已实际阅读根 `tests/` 所有 Python 测试与夹具生成源码、包内软件顾问静态测试；逐套测试定义见 `00-repo-audit.md` 第3节。此处不使用 AST 函数个数冒充 pytest 用例数/通过数。
- 保留 `tmp_path`、实际CLI退出码/JSON、fictional fixture/expected、格式重开、边界错误码与不泄露原文的模式；未来PV必须增加数值/能量/现金流/单位/分类隔离/属性变形/四文件一致性测试，而不只断言字符串存在。
- `tests/conftest.py:10-12` 在夹具缺失时会写入 fixtures；`tests/test_tooling.py:20-24` 调旧CLI validate会写 `reports/validate.*`。父代理回归后需审查这些副作用并保留保护基线。
- 根 `pyproject.toml:29-31` 只默认收集 `tests`，不会把包内Expert tests自然等价为全量覆盖。父代理应分别说明执行范围/通过/失败/跳过、命令、解释器发行元数据与日志。
- `packages/experts/wangbin-software-consultant/tests/test_expert_candidate.py:66` 仅验证scenarios静态字段；报价算术固定例子也不证明真实模型每次计算正确。不要把本地PASS变为WorkBuddy实机PASS。
- 历史报告中的“已测试”只代表对应时间/候选/环境。父代理2026-10-28首轮144pass/1fail/5skip后已用scratch归档wheel环境复跑exit0，最终计数尚待整合；本子任务不执行/重复测试。

## 7. 逐定义位置索引（静态解析，不执行模块）

以下用 Python AST 仅读源码取得定义起止行，便于复查表格。索引覆盖本轮实际语义阅读的核心 Python 模块；它不表示额外模块已通过测试或完成安全认证。数据类/类方法的未限定名称以所属文件和行号区分。

### `tooling/product_factory.py`

`_json:32-33`；`_dump:36-37`；`_safe_relative:40-55`；`_relative:58-62`；`_atomic_bytes:65-76`；`_version_entry:79-86`；`load_catalog:89-90`；`validate_catalog:93-168`；`get_product:171-178`；`_source:181-182`；`_version:185-186`；`init_product:189-265`；`_files:268-293`；`validate_product:296-337`；`test_product:340-354`；`_paths:357-360`；`_hash:363-364`；`register_version:367-394`；`package_product:397-460`；`verify_package:463-491`；`record_metric:494-516`；`portfolio_report:519-549`；`_license_dependency_gate:552-600`；`release_check:603-635`；`_absolute_display_path:638-640`；`_archive_inventory:643-682`；`_dependency_inventory:685-704`；`_upload_state:707-726`；`upload_list:729-774`；`_markdown_cell:777-778`；`_render_upload_report:781-838`。

### `tooling/products.py`

`main:12-68`。

### `tooling/validators/project_validator.py`

`_read_frontmatter:17-27`；`_check:30-31`；`validate_skill:34-57`；`validate_expert:60-85`；`validate_connector:88-141`；`validate_project:144-161`。

### `tooling/expert_rules.py`

`validate_prompt_expert:16-68`。

### `tooling/generators.py`

`generate_skill:10-31`。

### `tooling/financial_xlsx.py`

`_reject_macros:36-55`；`_formula_cell:58-64`；`_scan_rows:67-82`；`_scan_workbook:85-93`；`_selected_sheet_names:96-97`；`_write_csv:100-113`；`convert_xlsx_to_csv:116-171`；`_parser:174-182`；`main:185-198`。

### `tooling/cli.py`

`_parser:17-21`；`_dump:24-28`；`main:31-54`。

### `tooling/packager.py`

`build_candidate_zip:22-46`；`write_manifest:49-50`。

### `tooling/release_check.py`

`_write_json:16-18`；`run_release_check:21-67`。

### `tooling/test_runner.py`

`run_tests:12-24`；`write_test_report:27-41`。

### `tooling/phase5_expert_packager.py`

`digest:20-21`；`validate_source:24-31`；`build:34-70`。

### `tooling/validators/zip_validator.py`

`sha256:12-17`；`validate_zip:20-37`。

### `tooling/similarity.py`

`_literal_columns:20-23`；`_profile:26-81`；`_pair:84-120`；`similarity_check:123-146`。

### `services/document-engine/src/wangbin_document_cli/main.py`

`_health:19-34`；`_emit:37-38`；`_parser:41-59`；`main:62-108`。

### `services/document-engine/src/wangbin_document_engine/engine.py`

`DocumentEngine:17-124`；`__init__:18-22`；`parse_file:24-73`；`parse_many:75-112`；`_sections:115-124`。

### `services/document-engine/src/wangbin_document_engine/errors.py`

`EngineError:4-8`；`SecurityViolation:11-12`；`ParseFailure:15-16`；`ExportFailure:19-20`；`__init__:5-8`。

### `services/document-engine/src/wangbin_document_engine/markitdown_adapter.py`

`MarkItDownAdapter:11-29`；`__init__:12-15`；`convert:17-29`。

### `services/document-engine/src/wangbin_document_engine/metadata.py`

`file_metadata:11-19`；`safe_output_path:22-32`；`publish_new_file:35-40`。

### `services/document-engine/src/wangbin_document_engine/models.py`

`ParsedDocument:9-13`；`DocumentResult:17-30`；`BatchResult:34-48`；`SpreadsheetSummary:52-60`；`ExportResult:64-74`；`to_dict:29-30`；`to_dict:41-48`；`to_dict:59-60`；`to_dict:73-74`。

### `services/document-engine/src/wangbin_document_engine/process_runner.py`

`_send_result:31-35`；`_apply_posix_limits:38-53`；`_worker:56-66`；`convert_in_process:69-123`。

### `services/document-engine/src/wangbin_document_engine/resource_slots.py`

`_slot_dir:22-33`；`hold_resource_slot:37-72`。

### `services/document-engine/src/wangbin_document_engine/security.py`

`_has_link_component:23-26`；`SecurityPolicy:30-166`；`is_within:169-174`；`validate_input:43-67`；`snapshot_input:70-102`；`validate_batch:104-109`；`validate_output_dir:111-126`；`validate_signature:128-139`；`validate_container:141-166`。

### `services/document-engine/src/wangbin_document_engine/serialization.py`

`write_json:9-11`；`result_markdown:14-38`；`write_markdown:41-43`。

### `services/document-engine/src/wangbin_document_engine/spreadsheets.py`

`SpreadsheetService:20-197`；`__init__:21-22`；`inspect:24-55`；`deduplicate:57-163`；`_bounded_rows:165-180`；`_safe_value:183-186`；`_validate_export:189-197`。

### `packages/skills/wangbin-tender-analyzer/scripts/analyze_tender.py`

`_basename:52-53`；`_redact_sensitive:56-62`；`_evidence:65-74`；`_item:77-91`；`_is_scoring:94-95`；`_is_eligibility:98-104`；`_is_technical:107-113`；`_score_value:116-121`；`_date_value:124-126`；`_date_name:129-149`；`_contains_ambiguity:152-153`；`_line_texts:156-157`；`_evidence_values:160-165`；`_checklist_item:168-173`；`_response_checklist:176-197`；`analyze:200-371`；`_read_authorized_utf8:374-396`；`main:399-413`。


## 8. 保护与整合约定

逐文件 SHA-256、全部历史ZIP/wheel/sidecar及全部catalog版本候选见 `00-protected-artifacts.json`；重要哈希和静态安全阻断见 `00-repo-audit.md`。旧财务产品、软件顾问、模板、许可证、catalog/metrics以及全部dist历史文件均只读。后续如需增量注册或修复共用代码须另有阶段授权和回归证据，不以这份矩阵自动取得修改旧资产的许可。

本轮Phase0子任务结束状态：只读审计文档已写；保护哈希最终复算、官方快照/链接与当前回归最终计数**尚待父代理整合**。光伏数值引擎、四文件实物及真实平台调用均未实现/未验证，保持对应NOT_IMPLEMENTED/NOT_TESTED/BLOCKED。
