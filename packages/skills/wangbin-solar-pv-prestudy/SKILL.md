---
name: wangbin-solar-pv-prestudy
display_name: 光伏预可研报告
display_name_en: Solar PV Preliminary Feasibility Report
description: 根据用户授权的项目资料生成有来源边界的工商业屋顶或集中式地面光伏预可研报告。
description_zh: 复用既有光伏输入契约、计算引擎和报告导出器，生成可追溯的开发样件或报告文件。
description_en: Reuses the approved solar-PV contracts, calculation engine, and exporters to produce traceable draft or report files.
examples_zh:
  - "根据这些资料生成一份工商业屋顶光伏预可研报告"
  - "为这个集中式地面光伏项目生成预可研报告"
  - "检查这份光伏项目资料缺少哪些报告输入"
examples_en:
  - "Generate a preliminary feasibility report for this industrial rooftop PV project"
  - "Generate a preliminary feasibility report for this utility-scale ground PV project"
  - "Check which inputs are missing from this solar PV project package"
version: 0.1.3
author: 星核实验室 StarCore Lab
allowed-tools: Read, Bash, Write
license_type: PROPRIETARY
license_status: REQUIRES_MANUAL_REVIEW
---

# 光伏预可研报告

## 运行方式和依赖边界

### AI Report Engine 2.0：原生宿主研究试点

用户明确请求AI2.0章节研究时，先读 `@references/host-orchestration.md`。你（当前WorkBuddy宿主模型）负责读取本次请求、研究证据并撰写新的结构化章节；Python不调用隐藏LLM、不替你从旧稿拼出正文。本轮只开放CH08；真实宿主双案CH08通过前不得扩展CH10/CH16或Phase E。

本轮区分两条路径：用户显式选择“手动文件交接的宿主写作试验”时，当前WorkBuddy模型仅依据用户上传或授权读取的新CH08 request开展研究并返回符合其中Schema的新章节JSON；这一步不依赖Python或Connector，不因缺少它们而拒绝写作。无法实际读取完整请求时停止，不猜测被截断的事实或Schema。此路径只观察宿主写作，不代表CLI、Word或自动工具编排通过。

完整CLI路径通过 `@scripts/run_ai_chapter.py` 调用已安装引擎的授权/prepare-r2/publish/accept/checkpoint/resume协议；缺正确解释器、内部wheel或工具授权时仅阻断这条路径，不暗中切换开发源码。两条路径均不得读取authored、历史draft、旧Word或过去的完整章节作为新写作输入，不能用Hermes作者会话、协议fixture或本地UUID替代。来源、数值和专业边界不因手动交接而放宽。

R2先保持完整六节Schema：claims的许可ID不是必须填满的配额，每条claim覆盖所指段落全部事实及真实来源；假设不能标SUPPORTED；技术ID留元数据，正文用读者语言和合法槽。模型只写本请求的全新draft，引擎严格校验后原子发布response/完成回执，禁止修补旧失败JSON。具体边界见上述指引。新版Skill不含或安装引擎，动作不可用仍须停止CLI，不能将开发机验证冒充宿主成功。

源码候选另提供显式 `prepare-r2-shared`（不是已安装能力或本轮试验授权）。它需要新授权的严格 `input_view_policy`，仅返回同run完整共享视图供阅读；先读host-orchestration的共享阅读语法。pool/tree必须完整持有，数字词法包装与内部共享索引不能充当正式引用；缺段、未知版本、过期或不能完整读取即停止，不自动切换旧模式或追加调用。本轮不打包、安装、替换Skill或投递客户端。

下文report/project-report是保留的**legacy确定性报告导出**，不代表AI2.0运行时生成。不要将旧入口外层SUCCESS转述成模型研究或四文件通过。当前原生路径仍是本地候选，实际WorkBuddy专家安装、连接器环境继承和无旧稿生成均未验证。

本 Skill ZIP 是提示词、契约、冻结定义和路由脚本包，不会自动安装 Python、pip 依赖或光伏计算引擎。推荐在 WorkBuddy 中同时安装配套 CLI Connector `wangbin-solar-pv-cli`；Connector 使用 WorkBuddy 托管的 Python runtime 和隔离虚拟环境安装已审阅的 `wangbin-solar-pv-input==0.3.1` 与 `wangbin-document-cli==1.2.0`。如果 Connector 未安装或状态不是 `LOCAL_READY`，不得声称已完成计算。

普通 Skill 独立运行只在宿主环境已经提供 `wangbin_solar_pv`、`wangbin_document_engine` 及下述依赖时成立；Skill 不依赖开发者 Git 仓库、IDE 或本地 `PYTHONPATH`。WorkBuddy 平台安装、依赖解析和 Connector 获取来源在本候选中仍为 `NOT_TESTED`。

当用户要求根据项目资料生成工商业屋顶或集中式地面光伏预可研报告时，按本技能执行。此技能只负责路由、资料边界、运行入口和结果交付；**不在大模型提示词中重新实现发电、消纳、收益、财务或敏感性计算**。

## 当前支持范围（0.1.3 平台测试前候选）

本候选只支持以下两类独立报告，项目类型必须在输入中明确并由引擎校验：

1. **工商业屋顶光伏预可研报告（`industrial_rooftop`）**：覆盖屋顶边界和可利用面积、结构/防水与荷载资料、组件及逆变器、逐月发电、负荷消纳、自用/上网/限发、购售电价格、CAPEX/OPEX、税费、融资、现金流、敏感性和资料缺口。输入至少包括项目身份、屋顶与结构证据、负荷计量、合同/电价、并网、设备、成本和来源授权。
2. **集中式地面光伏预可研报告（`utility_scale_ground`）**：覆盖土地及建设边界、地形坡度和地质、支架基础、道路排水、集电线路、升压站与送出、集中并网与限发、市场化售电、发电预测、CAPEX/OPEX、税费、融资、项目财务、情景和地面项目资料缺口。输入至少包括土地权属/用地性质、测绘地勘、工程边界、接入系统、送出、交易、设备和成本来源授权。

报告固定结构为 **18章、100个章节子项、13个附录、26个附录子项**。目标交付为 DOCX、真实转换得到的 PDF、测算 XLSX 和来源/假设 XLSX；当前另生成 `canonical.json` 与逐项 `content-checklist.json` 供审阅。未取得合法依据的工程、政策、资源、合同或财务结论会保持 `UNKNOWN`/`BLOCKED`，不会由模型补写。

当前明确**不支持**农光互补、渔光互补、光储、户用、车棚/BIPV 或其他未列出的项目类型；不得仅替换标题后套用上述两类模型。0.1.3 仍是平台测试前本地候选：WorkBuddy 私有安装、依赖解析、平台运行、平台文件输出和真实对话调用尚未验证；PDF 转换器缺失时保持 `PDF_RENDERER_UNAVAILABLE`，不得宣称完全可用或上传就绪。

## 1. 先确认项目类型和授权范围

- 识别 `industrial_rooftop`（工商业屋顶）或 `utility_scale_ground`（集中式地面）。项目类型不明确时先询问，不根据标题猜测。
- 只读取用户明确选择或授权的输入目录；不扫描无关目录，不向第三方自动发送附件。
- 先列出资料状态：已提供、缺失、冲突、待授权、待专业复核。
- 真实项目资料不足时保留 `UNKNOWN`、`BLOCKED`、`NOT_IMPLEMENTED`、`NOT_TESTED`；不得用默认零值、经验数或模型臆测补齐。
- `SYNTHETIC` 仅可用于开发验证，不能描述成实测、真实项目、正式准入或投资决策依据。

## 2. 输入资料门槛

### 工商业屋顶

至少需要明确项目身份、屋顶边界/面积、结构或承载资料、负荷曲线及计量边界、合同/电价口径、并网资料、设备和成本依据、评价情景及来源授权。缺少负荷或合同依据时，不得伪造自用率或可避免购电费用。

### 集中式地面

至少需要明确项目身份、土地权属/用地性质/期限、面积和可建设边界、地形地质、基础和支架、道路排水运输、集电线路、升压站/送出、接入系统意见、限发/调度约束、市场化交易和成本依据。不得把屋顶结构、业主负荷或自用节省模型替换标题后用于地面项目。

详细输入和状态说明见 `@references/input-contract.md`。

## 3. 稳定执行链

1. 将用户资料交给既有 Phase 2 解析、归一化、来源和授权校验；不开发第二套解析或计算逻辑。
2. 使用既有 `project` 入口运行统一项目计算。计算失败、超时或资料阻断时，返回真实错误和待补资料，不生成看似完整的结果。
3. 使用同一份已验证 canonical result 调用 `report`（屋顶）或 `ground-report`（地面）。四个输出必须共享 `model_version`、`run_id`、`input_hash`、`source_snapshot_id` 和 `result_hash`。
4. 检查输出文件和 manifest；明确每个文件是 `GENERATED`、`BLOCKED` 还是 `NOT_TESTED`。
5. 只交付实际存在且重新读取验证过的文件。PDF 缺失时不得把 DOCX 改后缀或声明四文件完成。

稳定包装脚本为 `@scripts/run_solar_pv.py`。脚本只使用 Python 标准库；它调用已安装的 `wangbin_solar_pv` 引擎，不复制算法，并优先使用包内冻结基线副本或已安装引擎提供的基线。

### 已有 canonical 的导出调用

```bash
python scripts/run_solar_pv.py report \
  --project-type industrial_rooftop \
  --workspace "<授权私有工作区>" \
  --result "<workspace 内 canonical.json>" \
  --output "<新的输出目录>"
```

地面项目仅将 `--project-type` 改为 `utility_scale_ground`；脚本会调用 `ground-report`。

### 从项目输入运行计算再导出

```bash
python scripts/run_solar_pv.py project-report \
  --project-type industrial_rooftop \
  --workspace "<授权私有工作区>" \
  --input "<Phase 2 input.json>" \
  --methods "<methods.json>" \
  --bundle "<D3 bundle 目录>" \
  --budget "<bundle budget.json>" \
  --project-output "<新的计算目录>" \
  --report-output "<新的报告目录>"
```

完整参数和运行前提见 `@references/runtime.md`。开发者本地源码调试可以显式传 `--engine-root`，普通用户和 WorkBuddy 运行不应依赖该参数。如果运行环境找不到引擎、Python 依赖或合法 PDF 转换器，脚本必须返回稳定阻断状态，不能假装成功。

## 4. 报告交付规则

标准输出集为：

1. 光伏预可研报告 DOCX；
2. 光伏预可研报告 PDF（仅真实转换成功时）；
3. 测算模型 XLSX（当前为 `STATIC_SNAPSHOT`，不是已验证可重算模型）；
4. 资料来源与假设清单 XLSX；
5. `canonical.json` 和 126 条逐项 `content-checklist.json`（审阅追溯材料，不改变四文件门禁）。

资料不足时输出应显著标记“草稿，资料不足，未决策就绪”，状态保持 `DRAFT_PARTIAL`。如果生成三件而 PDF 阻断，整体门禁保持 `BLOCKED`。不要把本地脚本可执行、ZIP 可解析或历史样件通过解释成 WorkBuddy 平台已安装、已调用、已审核或已发布。

## 5. 安全和隐私

- 所有输入路径必须位于用户授权的工作区；拒绝绝对路径混入相对参数、`..` 路径穿越、输出覆盖和符号链接边界。
- 日志只输出稳定错误码、状态和必要的脱敏路径；不打印原始账单、负荷、合同、报价、令牌或完整附件内容。
- 每次运行使用新的计算/报告目录；不要覆盖旧 run。
- 不自动联网取数、不自动上传资料、不自动提交 WorkBuddy 审核或发布。
- 许可证、平台协议、真实数据来源和专业审查状态未闭合时，保持 `REQUIRES_MANUAL_REVIEW` 或 `BLOCKED`。
