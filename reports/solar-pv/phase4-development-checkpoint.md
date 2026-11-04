# Phase 4 数据适配先行开发检查点（独立模块，不代表正式准入）

**当前判定：PARTIAL / DRAFT_PARTIAL。** `docs/solar-pv/11-phased-roadmap.md` 的正式 Phase 4 入口要求 Phase 3 PASS；当前 3G 仍 PARTIAL。此次仅依据用户独立开发授权，完成不依赖该门禁的离线适配、既有 D3 核验和 F04 来源 XLSX 草稿。未实施实时外部资源 API、生产项目接入或正式四文件发布；未改 469 字段、89 公式、冻结 10 sheet 或正式结果 Schema。开发树仅 `solar/phase3e-forward`，起点 HEAD `67f04a4150cf54afd2e4dff435344c7af9996438`。

## 新增和复用的接口

- `services/solar-pv-engine/src/wangbin_solar_pv/data_adaptation.py`：`adapt_offline_response` 接受显式来源描述与不超过 8 MiB 的固定私有 JSON 字节，返回原始字节 SHA-256、数据集/版本、地理及时段/粒度/时区、授权、过期、缺失/冲突和待审 Phase 2 候选；不执行网络请求、不保存原始私密字节、不把 SYNTHETIC 改为真实。`approve_candidates` 要求人工复核者、证据说明、相同原始字节和描述符；再次核验原始 observation、许可证、项目/来源身份，使用现有 `make_record`、`validate_record`、`register_candidate`、`IntakeSession` 生成**新** Phase 2 导出，不自动选取冲突候选。对同字段的政策/电价/报价，优先复用已有 Phase 2 的候选/人工复核与经济口径字段，不造第二套审核状态机。未经真实核验的 `READY_FOR_REVIEW` 仍不得视作已批准。
- `inspect_resource_bundle`：只读消费既有 `read_bundle` 对 resource.timeseries 的完整 D3 校验，核对项目完整 Phase 2 基座、header 来源/许可、时区、间隔/覆盖、POA/温度/风/质量标记及每行有效标记；只读回 D3 `content_hash` 和行数，不重写资源时序。没有合法逐时数据、站址经纬度或正式权限时不能自动推算资源曲线。历史资源数据与评价日不强制相等，适用性须另核。当前**没有** PVGIS/NASA 原生响应解析或实时 HTTP 客户端，故其真实 API 重试、超时、限流、配额及缓存 **NOT_IMPLEMENTED**，没有隐式线上降级。
- `services/solar-pv-engine/src/wangbin_solar_pv/source_xlsx.py`：`create_source_workbook` 只读正式 canonical、可选同一结果的公式映射，生成 F04 真 XLSX **DRAFT_PARTIAL**；CLI `source-xlsx --result ... --mapping ... --output ...`。精确物理 sheet 顺序为：输入台账、气象与地理来源、政策适用性、设备与成本来源、案例对标、假设清单、冲突与缺口、变更与复核记录、变量-术语词典、资料授权说明。S09 首页写明冻结逻辑名 `变量/术语词典` 与 Excel 合法物理名的显式映射。所有 sheet 带 model/run/input/source/result 五标识，UNKNOWN/BLOCKED 显式可见，原始附件及 URL 不复制到草稿单元格；所有文本写入为非公式单元。未实施 Excel 内自动重算、四文件原子发布或视觉验收。
- Phase 5 可消费：经批准的**新** Phase 2 导出、原有 D3 目录/内容哈希、3G `run_project` 的 `canonical.json`/`formula-execution.json`/`receipt.json`，以及仅作诊断的 F04 私有 XLSX。新输入必须重建并绑定 D3；不得把老 D3 直接配给新导出。无审批的适配输出不能进入正式计算。

## 来源/许可调查与实际状态

- 欧盟 JRC **PVGIS**：官方 Usage Conditions & Data Protection 声明服务信息免费使用，要求注明来源；官方 API 文档描述限流和接口，2026 年更新说明 PVGIS 6 接口/覆盖变动。调查只核了**一般许可和接口说明**，没有选定项目站址、具体资源数据库版本/时段、对应授权证据或验收真实请求；**未接入、REAL_API_NOT_TESTED**，不能凭一般许可把任何用户数据发给服务。参考：JRC「Usage Conditions & Data Protection」「API non-interactive service」「Updates & bug fixes」。
- **NASA POWER**：官方 Referencing Guide 要求服务/数据版本与访问时间的引用，NASA Earthdata 使用指引提示第三方数据需要分别核权。未选定产品数据集/商用情境并复核其许可，未做 API 请求；**未接入、LICENSE_REVIEW_REQUIRED / REAL_API_NOT_TESTED**。参考：NASA POWER「Referencing Guide」、NASA Earthdata「Data Use and Citation Guidance」。
- 政策、售购电/合同价格、设备报价及税务资料：**无本轮经授权的项目专属真实响应或合同原件**，保持 UNKNOWN/BLOCKED；不得根据标题、通用网页或 SYNTHETIC 数值推定适用、税率或商业报价。
- 已实际使用的唯一数据是一期**SYNTHETIC** 离线响应和原 Phase 3G 合成项目/D3；来源标签保持 `SYNTHETIC_ONLY`，没有 `VERIFIED` 真实项目来源。项目资料未上传第三方。

## 可读样件、联调与验证

- 样件：`reports/solar-pv/phase4-synthetic/资料来源与假设清单-DRAFT_PARTIAL.xlsx`，从前阶段 `SYNTHETIC-industrial_rooftop` BASE 的经校验 canonical 和公式映射实际生成。文件 **77,673 字节**、SHA-256 **d2d1fc780c7a209a1b0f31346c5ef49c5d94ca82fb6eb284663b3c166e45e821**；重新解析 ZIP/10 sheet 均成功，未含外部链接或 VBA，未发现公式单元。10 sheet 实际行数依次为 **209/15/10/144/10/10/79/10/567/12**。这是单文件来源草稿，**不是**四文件交付或投资决策依据。
- 固定离线响应专项：明确 SYNTHETIC 的资源标量候选保持 `UNVERIFIED` 与 `SYNTHETIC_ONLY`，人工批准接口拒绝把它改成 REAL；缺失、重复冲突、过期和 DENIED 许可各自拒绝/阻断。既有 **8760 行** SYNTHETIC D3 原始时序只读核验：`SYNTHETIC_ONLY`，D3 内容哈希相等，行数及每行质量/POA/温度/风守卫通过；这不是 PVGIS/NASA 网络可用性测试。
- `run_project` 最小负例联调：将不匹配的有效 Phase 2 导出指向另一个有效 D3，实际返回 **`PROJECT_BUNDLE_BASE_MISMATCH`**，无项目目录发布。原 Phase 3G 的合法 SYNTHETIC 项目链有历史实算，但本轮**未**对经人工批准的真实适配来源重新执行项目，正例保持 **NOT_TESTED**。
- 当前最终代码的编译/导入及直接相关快速测试：`test_phase4_data_adaptation.py + test_phase3g_project_runner.py` **8 passed、0 failed，28.13 秒**。样件 CLI 实际退出 0 并给出 `DRAFT_PARTIAL`，重新打开文件与 SHA-256 均核对。D3 只读资源专项约 **62.53 秒**；不匹配基座的生产入口拒绝约 **50.64 秒**。这些不是 pytest 运行时间，也不是 Phase 3/4 完整计算耗时。
- 暂缓：真实外部接口与许可闭环、资源原生格式解析、真实来源审批正例、完整项目 E2E、19+10 全模型/四文件、Word/PDF、L2/L3、WorkBuddy 安装/上传/审核均 **NOT_TESTED 或 NOT_IMPLEMENTED**；原 Phase 3E/3F/3G 的专业阻断不变。Phase 4 正式入口 Phase 3 PASS、出口真实接口或充分 UNAVAILABLE 证据与 F04 全字段/视觉/安全验收均**未关闭**，不进入 Phase 5。

本轮本地提交 SHA 以 Git 最终读回为准；禁止 push、merge、部署或发布。Phase 7 完成并集中验收前不上传 WorkBuddy；用户确认前不启动 Phase 8A–8G。
