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
