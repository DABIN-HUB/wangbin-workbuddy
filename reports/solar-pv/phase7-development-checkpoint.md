# Phase 7 WorkBuddy 光伏预可研 Skill 候选检查点

## 结论

- 阶段：Phase 7A–7G，本地 Skill 候选封装与报告导出链验证
- 产品：`wangbin-solar-pv-prestudy`
- 版本：`0.1.0`
- 开发者：`星核实验室 StarCore Lab`
- 本地候选状态：`PACKAGE_VALIDATION_PASS`
- WorkBuddy 平台安装/调用/审核：`NOT_TESTED`
- 发布状态：`BLOCKED`
- 本轮没有上传、登录、提交审核、发布或启动 Phase 8。
- 上游光伏计算和报告仍为 `PARTIAL` / `DRAFT_PARTIAL`；本 Skill 不把结果包装为正式投资决策报告。

执行时间：2026-11-05（中国标准时间）。

## 基线

- 仓库：`F:/ideaWorkSpace/wangbin-workbuddy`
- 分支：`main`
- 开发前 HEAD：`da8520f2a16a02f2fac6006717252d870fdef39b`
- 当前代码入口：`services/solar-pv-engine/src/wangbin_solar_pv/cli.py`
- 当前报告入口：`services/solar-pv-engine/src/wangbin_solar_pv/report_export.py`
- Skill 目录：`packages/skills/wangbin-solar-pv-prestudy/`
- 产品目录登记：`products/catalog.json`

本阶段未触碰旧的财务 Skill、Connector、Expert、封存的 25 年项目或用户已有屋顶样件文件。

## 7A WorkBuddy 规范核对

已核对官方页面：

- https://open.workbuddy.cn/docs/skill

截至本轮读取到的规范，Skill 采用：

```text
<skill-name>/
  SKILL.md
  references/       可选
  scripts/          可选
  templates/        可选
```

`SKILL.md` 使用 YAML frontmatter + Markdown 正文；官方页面列出的必填字段包括 `name`、`description`、`version`、`author`，并展示了中英文名称、描述和示例字段。本候选保留了现有仓库约定的完整中英文字段以及 `allowed-tools`。

官方页面未明确包大小上限、WorkBuddy 是否提供 Python 3.12–3.14、是否提供本地光伏引擎依赖、是否提供 LibreOffice/中文字体、是否提供私有 Skill 试运行入口；这些能力保持 `UNKNOWN` / `NOT_TESTED`，没有从本地 ZIP 验证结果推定平台能力。

## 7B Skill 实现

实现文件：

- `packages/skills/wangbin-solar-pv-prestudy/SKILL.md`
- `packages/skills/wangbin-solar-pv-prestudy/manifest.json`
- `packages/skills/wangbin-solar-pv-prestudy/README.md`
- `packages/skills/wangbin-solar-pv-prestudy/LICENSE`
- `packages/skills/wangbin-solar-pv-prestudy/references/input-contract.md`
- `packages/skills/wangbin-solar-pv-prestudy/references/runtime.md`
- `packages/skills/wangbin-solar-pv-prestudy/scripts/run_solar_pv.py`

Skill 能力边界：

1. 识别 `industrial_rooftop` 和 `utility_scale_ground`；类型不明时询问。
2. 提示屋顶/地面项目各自的直接资料和授权缺口。
3. 复用既有 Phase 2–4 输入契约、来源校验和 Phase 3G `project` 入口。
4. 复用既有 `report` / `ground-report` 导出器，不复制计算算法。
5. 对 `UNKNOWN`、`BLOCKED`、`NOT_IMPLEMENTED`、`NOT_TESTED` 保持原状态。
6. 防止工作区路径穿越、输出覆盖和类型反串用。
7. 返回稳定 JSON 状态和错误码。
8. 不自动联网取数、不上传用户附件、不自动审核/发布。

许可证暂按候选包声明 `PROPRIETARY`，权利、平台协议和分发范围仍需人工确认；没有把本候选标记为可正式发布。

## 7C PDF 能力

本机探测结果：

- `soffice`：未发现
- `libreoffice`：未发现
- PDF 状态：`PDF_RENDERER_UNAVAILABLE`

Skill 和引擎均禁止通过修改扩展名或截图拼接伪造 PDF。实际运行时若没有合法转换器，只返回真实 `BLOCKED`，保留已生成的 DOCX/XLSX 和 manifest 状态。

Windows 本机未来若安装并配置转换器，也不代表 WorkBuddy 平台环境具备同一转换器、字体或沙箱权限。

## 7D 稳定执行入口

脚本：

```text
packages/skills/wangbin-solar-pv-prestudy/scripts/run_solar_pv.py
```

支持：

```text
report
project-report
```

`report` 直接消费已验证 canonical；`project-report` 调用既有 `project`，再定位唯一 canonical 并调用类别对应报告导出器。引擎路径通过 `--engine-root` 或 `SOLAR_PV_ENGINE_ROOT` 显式提供，不依赖开发者个人固定路径。

脚本自身只使用 Python 标准库；既有引擎仍需要其 `pyproject.toml` 声明的运行时和依赖。输出目录必须不存在，输入参数相对工作区解析，`..`、绝对路径、符号链接工作区和类型不匹配会被拒绝。

## 7E 候选 ZIP

使用既有 `tooling.products` / `tooling.product_factory`，没有新建通用打包器。

候选 ZIP：

```text
dist/wangbin-solar-pv-prestudy-0.1.0-skill-candidate.zip
```

- 大小：`11,655` bytes
- SHA-256：`71a9eb25a63620b2fdc4d2a7217cba100bcd255a740779c0fe5d86b0544964ef`
- ZIP `unzip -t`：通过
- `tooling.products verify`：`PASS`
- 包结构验证：`PASS`
- 独立复制 source/catalog 后重建：`PASS`
- 独立重建大小：`11,655` bytes
- 独立重建 SHA-256：`71a9eb25a63620b2fdc4d2a7217cba100bcd255a740779c0fe5d86b0544964ef`
- 两次归档哈希一致：`true`

ZIP 成员：

```text
wangbin-solar-pv-prestudy/LICENSE
wangbin-solar-pv-prestudy/README.md
wangbin-solar-pv-prestudy/SKILL.md
wangbin-solar-pv-prestudy/manifest.json
wangbin-solar-pv-prestudy/references/input-contract.md
wangbin-solar-pv-prestudy/references/runtime.md
wangbin-solar-pv-prestudy/scripts/run_solar_pv.py
```

包内没有测试缓存、个人绝对路径、项目 canonical、报告样件、用户附件、密钥或访问令牌。

## 7F 本地短流程

### 工商业屋顶

- 输入：既有一年期 `SYNTHETIC-industrial_rooftop` canonical
- `run_id`：`d86a4e81-e432-4199-b194-bbf93dd15b01`
- Skill wrapper：实际执行成功
- wrapper 运行耗时：`5.183302s`
- 结果：18 章、100 子项、13 附录、26 附录子项、19 测算 sheet、10 来源 sheet
- PDF：`BLOCKED`
- 报告：`DRAFT_PARTIAL`
- 测试范围：canonical → report export，不冒称完整输入到计算 E2E

### 集中式地面

- 输入：既有一年期 `SYNTHETIC-utility_scale_ground` canonical
- `run_id`：`72bd0d6e-e466-46ab-87de-7c3fbc2017a9`
- Skill wrapper：实际执行成功
- wrapper 运行耗时：`5.039550s`
- 结果：18 章、100 子项、13 附录、26 附录子项、19 测算 sheet、10 来源 sheet
- PDF：`BLOCKED`
- 报告：`DRAFT_PARTIAL`
- M08 保持集中式地面项目不适用屋顶自用模型

专项失败检查：

- 屋顶 canonical 传给地面类型：返回 `REPORT_CATEGORY_MISMATCH`。
- `../canonical.json`：返回 `PATH_BOUNDARY`。
- 显式不存在的引擎路径：返回 `ENGINE_UNAVAILABLE`。
- 失败时不创建报告输出目录。

该短流程证明 Skill wrapper 到既有报告导出器的本地调用链，不证明 WorkBuddy 平台安装、Python 依赖解析、平台对话或完整计算链已通过。

## 7G 平台试运行准备

### 用户手动操作

1. 用户在自己的 WorkBuddy 官方账号和浏览器中打开官方 Skill 管理/上传入口。
2. 选择本地候选 ZIP：
   `dist/wangbin-solar-pv-prestudy-0.1.0-skill-candidate.zip`
3. 上传前核对文件名和 SHA-256；不要上传项目 canonical、原始附件或报告样件。
4. 如果界面仅提供正式审核、公开发布或收费发布，不要继续点击；保持平台状态 `BLOCKED`。
5. 如果账号显示草稿、预览、私有或自测入口，用户可在官方页面完成导入和安装，并记录页面显示的解析结果、版本和 Skill 名称。
6. 安装后用以下触发语进行人工试运行：
   - “根据我提供的项目资料，生成一份工商业屋顶光伏预可研报告。”
   - “为这个集中式地面光伏项目生成预可研报告。”
7. 检查输出是否保留 `DRAFT_PARTIAL`、PDF 阻断、同一 run identity 和来源缺口；不接受模型直接编造电价、土地、地勘、结构、并网或财务结果。
8. 只有用户在官方页面实际观察到安装和对话后，才能更新平台 `INSTALL` / `DIALOGUE` 证据；本地 ZIP 验证不能替代。

本轮没有自动登录、上传、安装、调用、提交审核或发布 WorkBuddy。

## 依赖和阻断

引擎依赖来自 `services/solar-pv-engine/pyproject.toml`：

- Python `>=3.12,<3.15`
- `jsonschema==4.26.0`
- `wangbin-document-cli==1.2.0`
- `openpyxl==3.1.5`
- `python-docx==1.2.0`
- `pdfminer.six==20260107`
- `defusedxml==0.7.1`
- Windows：`tzdata==2026.5`
- 可选 PDF：合法可调用的 `soffice`/`libreoffice` 和可用中文字体

当前阻断：

- PDF 转换器不可用；
- WorkBuddy 平台运行时依赖未验证；
- Skill 安装、实际调用和平台对话未测试；
- 平台协议、分发权利和 `PROPRIETARY` 候选许可证仍需人工审核；
- 上游真实土地、地勘、接入、交易和财务资料门禁仍未关闭；
- 完整 L2/L3 未测试。

## 验证清单

- `tooling.products validate --id wangbin-solar-pv-prestudy`：`PASS`
- `tooling.products package --id wangbin-solar-pv-prestudy`：`PASS`
- `tooling.products verify --id wangbin-solar-pv-prestudy`：`PASS`
- `unzip -t`：通过
- 独立复制重建及哈希比较：通过
- `py_compile`：通过
- `git diff --check`：通过
- 屋顶/地面 wrapper 短流程：均成功，均 `DRAFT_PARTIAL` / PDF `BLOCKED`
- 反串用、路径穿越、显式引擎缺失错误：通过
- `tooling.products release-check`：整体 `BLOCKED`；本地包门禁 `PASS`，产品测试 `NOT_TESTED`，许可证需人工复核，WorkBuddy 平台门禁 `NOT_TESTED`
- 完整 L2/L3、平台安装/对话/审核/发布：`NOT_TESTED`

## Git 与停止点

本轮生产代码、产品注册、Skill 资源、候选包和本检查点完成后停止；不启动 Phase 8。当前应在提交前仅暂存本阶段明确文件，不执行 `git add -A`，并保留既有未跟踪屋顶样件不变。

## Phase 7H 独立运行与交付依赖收口

### 7H.1 交付结论

- 版本从 `0.1.0` 升为 `0.1.1`，因为本轮改变了运行依赖、包内冻结基线和安全边界。
- 普通 Skill ZIP **不包含** `services/solar-pv-engine` 的实际计算源码，也不自动安装 Python 依赖；它携带 12 份受控冻结基线和标准库 wrapper。
- 当前最小候选交付为普通 Skill + `wangbin-solar-pv-cli` CLI Connector：Connector 负责隔离 Python runtime 和固定依赖，Skill 负责输入契约、类型路由、输出安全和真实状态保留。
- Connector 仍需权利人将两个内部 wheel 发布到 WorkBuddy 可访问的可信索引，或由用户提供经审核的私有索引；本轮没有上传 wheel、写入凭据或登录 WorkBuddy。
- 因此当前结论是 `LOCAL_CANDIDATE_ONLY`，不是平台安装成功或正式发布就绪。

### 7H.2 无原仓库隔离验证

验证目录为 Hermes scratch 下的新解压目录，运行时使用独立 venv；没有把仓库根目录加入 `PYTHONPATH`，也没有通过 `--engine-root` 指向开发仓库。0.1.1 ZIP 解压后可定位包内 baseline；已安装的 wheel 提供 `wangbin_solar_pv` 和 `wangbin_document_engine`。

实际 runtime 结果：

```text
Python 3.14.7
No broken requirements found.
imports=PASS wangbin_solar_pv wangbin_document_engine
wangbin-solar-pv-input 0.3.0
wangbin-document-cli 1.2.0
markitdown 0.1.9
```

同时确认 ZIP 不含个人绝对路径、`.env`、`__pycache__`、canonical、密码、token 或 secret 成员；Skill 19 个成员、Connector 5 个成员，`unzip -t` 均通过。使用 `project-report` 调用既有 `project` 入口时，屋顶和地面均实际进入引擎并因提供的 `resource-manifest.json` 不是完整 bundle 返回 `BUNDLE_INVALID`，没有创建输出目录；这证明入口和阻断边界可调用，但不冒称缺失专业资源时的完整 `project` 成功。

### 7H.3 两类 SYNTHETIC 实际导出

从最终 0.1.1 ZIP 解压出的 wrapper，在独立 wheel runtime 中对已归档 canonical 真实执行：

| 类型 | 身份 | 状态 | F01/F03/F04 | PDF | 文件证据 |
|---|---|---|---|---|---|
| `industrial_rooftop` | `SYNTHETIC-industrial_rooftop` | `DRAFT_PARTIAL` | DOCX/XLSX/XLSX 已生成 | `PDF_RENDERER_UNAVAILABLE` / `BLOCKED` | `reports/solar-pv/phase7h-isolated-rooftop/` |
| `utility_scale_ground` | `SYNTHETIC-utility_scale_ground` | `DRAFT_PARTIAL` | DOCX/XLSX/XLSX 已生成 | `PDF_RENDERER_UNAVAILABLE` / `BLOCKED` | `reports/solar-pv/phase7h-isolated-ground/` |

两类 manifest 均保留 `four_file_gate=BLOCKED`、`not_decision_ready=true`。导出结构复核为每类 DOCX 404 段落、测算模型 19 sheets、来源台账 10 sheets；这不是 PDF，也不是投资决策结论。最终证据文件的 SHA-256 已写入对应目录文件及本仓库检查记录：

- 屋顶：manifest `184421e1c55d96009c61398f72170d4a86639a17d454cd2a79a121594364cd36`；DOCX `83311843a21b2019614c081c50882d19369131ec38b997628b92a95ea519aaaa`；测算 XLSX `13e58fb297e6cd167a7404b4147f8a763ec30f1a13c79fbf76e68b80cca0246d`；来源 XLSX `2ff1cf1df70d19b22e6487ead1449f5b1453967bb94e2909579b34abc8ff0b8e`。
- 地面：manifest `4b44b36d0c15059c8172e0309dd575a6391d533ab5814ef5d5e6bf1cab7f93a9`；DOCX `cbd00083e14e91c0f99bcc7b2bdcf8a2162062cce7fa5d660de9d7cbf63ee826`；测算 XLSX `e282eaba6698148b34422cdc8bbbdd498f42c7c913970103f5d68abf95b46fa8`；来源 XLSX `8c402f293db3e7807edfb39b0e4c2a8d3b8787ae125adc83b0a5e153cb8705ca`。

### 7H.4 安全和边界专项

- 屋顶 canonical 请求地面报告：`REPORT_CATEGORY_MISMATCH`。
- `../canonical.json`：`PATH_BOUNDARY`。
- 显式不存在引擎：`ENGINE_UNAVAILABLE`。
- 已有输出目录：`OUTPUT_EXISTS`，不覆盖既有结果。
- Windows junction / reparse-point workspace：`WORKSPACE_SYMLINK`，不创建输出；wrapper 现在同时拒绝普通 symlink 和 Windows junction。
- 真实 Windows symlink 创建因当前账号缺少 `SeCreateSymbolicLinkPrivilege` 未执行；junction 复核已实际执行。该平台能力不被误报为已测试。

### 7H.5 PDF 和依赖状态

本机 `soffice`、`libreoffice`、`pandoc`、`wkhtmltopdf` 均未发现；`docx2pdf`/`comtypes` 不可用；Word COM 启动探测超时（exit code 124）。没有可控合法转换器和可复核中文字体/许可证，因此没有生成 PDF，没有改后缀，也没有截图伪造。四文件门禁继续保持 `BLOCKED`。

Connector `cli.json` 和 Skill manifest 现在显式固定：Python `>=3.12,<3.15`、`jsonschema==4.26.0`、`wangbin-document-cli==1.2.0`、`wangbin-solar-pv-input==0.3.0`、`openpyxl==3.1.5`、`python-docx==1.2.0`、`pdfminer.six==20260107`、`defusedxml==0.7.1`、`tzdata==2026.5`、`markitdown[pdf,docx,xlsx,pptx]==0.1.9`。本地 venv `pip check` 通过；WorkBuddy 平台安装、依赖解析、权限和实际对话仍为 `NOT_TESTED`/`UNKNOWN`。

### 7H.6 最终候选归档

- Skill：`dist/wangbin-solar-pv-prestudy-0.1.1-skill-candidate.zip`，203,100 bytes，SHA-256 `e839aa16eac479d70d518890f948508ffb0bbefdfca08669780a3dfc93960002`。
- Connector：`dist/wangbin-solar-pv-cli-0.1.0-connector-candidate.zip`，3,168 bytes，SHA-256 `023dbcd64b09032d850017a5804090afa1837bb6e448f2e7b8783389eeb94c55`。
- 两个归档均由独立 scratch source/catalog 重建；`validate`、`verify`、`unzip -t` 通过，独立重建哈希与原归档分别一致。
- 产品目录已登记上述 Skill 0.1.1 和 Connector 0.1.0 哈希；WorkBuddy 平台证据仍为 `NOT_TESTED`，许可证/权利和可信索引仍需人工审核。

### 7H.7 未关闭事项与停止点

- 屋顶/地面真实项目所需土地、地勘、结构、接入、升压站、交易、合同、报价、授权和财务依据仍缺失；不得用模型估算偷写正式结果。
- 完整真实输入到计算 E2E、完整 L2/L3、Excel 重新计算、PDF 页面/检索/中文视觉复核、WorkBuddy 私有安装/实际调用/权限和平台审核仍为 `NOT_TESTED`。
- 本阶段没有自动上传、登录、发布或发起审核，不启动 Phase 8A–8G；用户完成 WorkBuddy 私有试运行并确认结果前，不宣布正式发布就绪。

## Phase 7I：上传前完整报告内容验收（2026-11-05）

### 7I.1 产品说明和候选版本

- Skill 已升级为 `0.1.2`，Connector 已升级为 `0.1.1`；旧的 0.1.1/0.1.0 候选保留，未覆盖。
- 支持范围在 `SKILL.md`、`README.md`、`manifest.json` 和产品目录中明确限定为工商业屋顶（`industrial_rooftop`）和集中式地面（`utility_scale_ground`）。农光互补、渔光互补、光储、户用、车棚/BIPV 等均明确为不支持。
- 产品说明明确 18 章/100 个章节子项、13 个附录/26 个附录子项和 DOCX/PDF/测算 XLSX/来源 XLSX 目标交付；未取得合法依据的结论保持 `UNKNOWN`/`BLOCKED`。平台安装、平台调用、PDF 和许可证仍未闭合，不能宣称完全可用。

### 7I.2 两类审阅包的真实导出结果

本轮对既有身份可复核的 Phase 3G SYNTHETIC canonical 做了新的导出层验收；这是“canonical → 文件导出”，**不是**新的完整 Phase 2→3G 计算回执。两个独立审阅包位于 `reports/solar-pv/phase7i-upload-review/`，每包包含 DOCX、两个 XLSX、manifest、canonical、公式执行证据、内容清单、质量检查和范围说明。

- 屋顶包：`industrial_rooftop-review-package.zip`，287,034 bytes，SHA-256 `661ad3355a637f65f26e96e62be3c2bc1f24eaa8cda83ee9686e0f12437a521b`。
- 地面包：`utility_scale_ground-review-package.zip`，285,072 bytes，SHA-256 `73d18d4be264c1949644cf09c75722fd614b0481fde8404bd738f1ee2beb9721`。
- 两类导出均为 `DRAFT_PARTIAL`；DOCX 生成耗时分别约 3.77 s / 3.60 s，不代表完整 Skill 计算耗时。
- 两类均真实记录：18/18 章、100/100 章节子项、13/13 附录、26/26 附录子项；DOCX 可编辑文本结构检查通过，但实际页面视觉状态为 `NOT_TESTED`。
- 两类均生成 126 条机器可读逐项检查记录；检查记录含主题摘要、字段/指标、来源、专业内容状态、重复模板标记、错误绑定标记、排版状态、资料缺口和结论。结构存在与专业内容、合法证据和视觉排版状态分开记录。
- 两类均生成 19 张测算工作表和 10 张来源/假设工作表；内容检查确认 `STATIC_SNAPSHOT`，未宣称 `VERIFIED_RECALCULABLE`。

### 7I.3 完整输入链路结论

- 本轮实际尝试以独立 SYNTHETIC Bundle 运行项目入口，保留在 scratch 证据中；该尝试未在时限内完成到 canonical，不能用它替代完整链路证据。
- 运行首先暴露旧 Phase 3D 合成输入中 replacement rows 与单条 illustrative replacement rule 的契约不一致（`ENERGY_REPLACEMENT_RULES`）；在临时独立副本中补齐显式事件绑定后，3B 已生成，但完整 3C→3G 运行仍未在本轮收口，故完整输入到计算链状态保持 `NOT_COMPLETED_IN_THIS_PHASE7I_RUN`。
- 未修改两个封存的 25 年案例，也未将完整链路阻断改成忽略校验或伪造成功；最终审阅包的 `review-scope.json` 明确其 canonical 导出来源和边界。

### 7I.4 PDF、平台和停止点

- `soffice`、`libreoffice`、`pandoc`、`wkhtmltopdf`、`docx2pdf`/`comtypes` 仍不可用；两个审阅包都不含假 PDF，manifest 保持 `PDF_RENDERER_UNAVAILABLE` / `BLOCKED`。
- WorkBuddy 私有安装、Connector `init`、可信 wheel 索引、平台 Python runtime、Skill 对话调用、平台输出权限、平台 PDF/字体和许可证仍为 `NOT_TESTED`/`UNKNOWN`/`REQUIRES_MANUAL_REVIEW`。
- 新候选归档：Skill `dist/wangbin-solar-pv-prestudy-0.1.2-skill-candidate.zip`，221,231 bytes，SHA-256 `42e66522bb923dd9cdf18180ff38dfca69b24a9ae09e49c6efe5ed935293fca7`；Connector `dist/wangbin-solar-pv-cli-0.1.1-connector-candidate.zip`，3,212 bytes，SHA-256 `766a3e7b24527373d46b56aa56bf33de8e7890f788358d7ef39c24e1b9b76d31`。两个 ZIP 的 `unzip -t` 通过。
- 快速契约检查：`pytest -q tests/solar-pv/test_calculation_contract_cli.py`，3 passed，9.83 s；未运行完整 L2/L3。
- 本轮未上传 WorkBuddy、未 push、未提交审核、未发布、未启动 Phase 8A–8G。用户确认报告内容、计算结果、Word 页面视觉和平台试运行前，不进入上传阶段。
