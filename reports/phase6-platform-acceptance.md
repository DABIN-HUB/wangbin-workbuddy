# Phase 6 — WorkBuddy Expert 真实平台验收与 Git 基线

核验时间：2026-10-26 21:51（UTC+08:00）
项目：`F:/ideaWorkSpace/wangbin-workbuddy`
分支：`main`
本阶段目标：不增加 Expert 功能，审查 Phase 1～5 工作区，核对官方平台流程，尝试只读发现授权的 WorkBuddy 入口，完成自动化验收并建立首次本地 Git 基线。

## 1. 执行边界

- 未执行 `git push`、`git reset`、分支切换或 WorkBuddy 正式提交审核。
- 未开启收费、设置真实售价、公开发布或上传候选包。
- 未索取或读取账号密码、身份证号、手机号、验证码、Token、私钥或其他凭据。
- 没有 WorkBuddy 私有测试授权时，不以 ChatGPT、站外模型模拟或静态检查替代 WorkBuddy 真实安装和对话。
- 本阶段没有修改专家功能；新增文件仅为本验收报告，后续与已审查源码、测试及历史报告一起建立本地 Git 基线。

## 2. Git 工作区与文件审查

### 2.1 基线状态

阶段开始时实际读取到：

- `HEAD=931c098c709dbf1e5910c77da94cc23361ca91dc`。
- 当前分支为 `main`，上游显示为 `origin/main`。
- 工作区有 15 个未跟踪文件，内容均属于 Phase 4 报告、Phase 5 Expert 源码/测试、Phase 5 打包器或 Phase 5 报告；没有已修改的已跟踪文件。
- `dist/` 被 `.gitignore` 忽略，Phase 5 Expert 候选 ZIP、`.sha256` 和 manifest 保持本地，不纳入本次源码基线。
- `.venv/`、`.pytest_cache/`、`__pycache__/` 等本地环境或缓存保持忽略。

审查后的 Phase 1～5 允许提交清单为以下 15 个实际未跟踪文件；本报告完成后再增加第 16 个文件 `reports/phase6-platform-acceptance.md`：

```text
packages/experts/wangbin-software-consultant/.codebuddy-plugin/plugin.json
packages/experts/wangbin-software-consultant/README.md
packages/experts/wangbin-software-consultant/agents/wangbin-software-consultant.md
packages/experts/wangbin-software-consultant/avatars/expert.png
packages/experts/wangbin-software-consultant/tests/scenarios.json
packages/experts/wangbin-software-consultant/tests/test_expert_candidate.py
reports/phase4-distribution.md
reports/phase4-final.md
reports/phase4-manual-acceptance.md
reports/phase4-mvp-scope.md
reports/phase4-platform-capabilities.md
reports/phase4-runtime-decision.md
reports/phase4-threat-model.md
reports/phase5-software-consultant.md
tooling/phase5_expert_packager.py
```

实际提交前以 `git status --short --untracked-files=all` 和显式路径清单为准，不使用宽泛的 `git add .`。

### 2.2 凭据、个人数据和临时产物

- 项目内置 `tooling.validators.secret_scanner.scan_for_secrets(Path('.'))` 实际结果：`secret_findings=0`。
- 排除 `.git`、`.venv`、`.pytest_cache`、`dist`、`__pycache__` 后，实际不存在 `.env` 或 `.env.*` 文件。
- 未跟踪文件中没有私钥、访问 Token、API Key、密码、连接字符串或个人业务数据。
- `contact@example.com` 出现在 Expert `plugin.json` 中，是官方示例沿用的占位邮箱，不是可用于发布的真实联系方式；不能把它误写成真实联系方式，也不能擅自替换为本机 Git 邮箱。
- 报告中的平台资料、浏览器检查和候选包路径不包含账号凭据。若后续平台页面展示真实个人信息，交付记录只保留状态，不复制其值。

### 2.3 Git 身份

本机 Git 已配置用户名和邮箱，未因本阶段擅自设置或伪造身份。提交时使用现有 Git 配置；本报告不记录邮箱值。若提交命令实际提示身份缺失，应停止提交并报告，不改写全局配置。

## 3. Expert 1.0.0 发布元数据检查

| 项目 | 实际结果 | 状态/限制 |
|---|---|---|
| `name` / `version` | `wangbin-software-consultant` / `1.0.0` | PASS |
| `expertType` / `agentName` | `agent` / `wangbin-software-consultant` | PASS |
| Agent 路径 | `./agents/wangbin-software-consultant.md`，与文件名一致 | PASS |
| 双语 `displayName` / `profession` / `displayDescription` | 均有 `zh`、`en`；中文简介符合 40–50 字约束 | PASS |
| 分类 | `12-IndustryConsultant`，官方分类说明为行业顾问 | PASS，最终账号可选分类仍需平台页面确认。[5] |
| 头像 | PNG，512×512，3786 bytes，低于 500 KB；路径为 `avatars/expert.png` | PASS |
| Agent frontmatter | `name`、`description`、双语展示字段和 `maxTurns` 存在 | PASS |
| 外部运行时 | 没有 `skills`、`dependencies`、`tools` 或 Python/MCP/CLI/Docker 运行时声明 | PASS |
| 作者邮箱 | `contact@example.com` 为占位值 | **发布阻断**：必须由账号所有者在平台/源码中决定真实反馈邮箱；本阶段不擅自填入个人邮箱 |
| 许可证元数据 | `plugin.json` 声明 `MIT`；根 `pyproject.toml` 声明 MIT；仓库已有 `services/document-engine/LICENSE` | PASS（仓库许可依据存在） |
| Expert ZIP 内许可证文件 | 官方 Expert 基础结构不要求 LICENSE 成员；当前 ZIP 只含 4 个运行资产，无独立 LICENSE 文件 | **需本人决定**：若将 Expert 作为独立开源包公开分发，应在发布文案或包内补充清晰许可说明；本阶段不改变候选包结构 |
| 价格与收费 | 未设置真实价格、付款链接或收费配置 | PASS；不执行收费入驻 |

官方 Expert 文档规定了 `.codebuddy-plugin/plugin.json`、`agents/`、`avatars/`、`README.md` 的根层级、必填字段、Agent frontmatter、头像 512×512/500 KB 限制、三项 tags、三项 quickPrompts 及 `12-IndustryConsultant` 分类。[1] 当前源码符合这些静态规则；官方页面没有证明此账号已取得发布权限、私有草稿权限或该具体类目已审核通过。

## 4. 自动化与候选包验收

### 4.1 自动化结果

实际执行：

```text
.venv/Scripts/python.exe -m pytest -q
31 passed, 1 skipped in 40.44s
```

唯一跳过项：Windows 环境未允许创建符号链接的安全测试；这属于既有 Phase 1～5 文档引擎测试，不是新 Expert 功能失败。

Expert 独立测试：

```text
.venv/Scripts/python.exe -m pytest -q packages/experts/wangbin-software-consultant/tests/test_expert_candidate.py
36 passed in 0.21s
```

项目结构校验对新 Expert 返回 `expert.required_fields=PASS`，新 Expert 没有 findings；全局 secret scanner 返回 0 findings。

### 4.2 候选 ZIP

重新运行独立打包器后，实际候选为：

```text
dist/wangbin-software-consultant-1.0.0-expert-candidate.zip
SHA-256: 4813386b13378be4f171fa433d23f9afc749c1323f60af36648f116dd0636deb
```

`dist/` 内执行的最终校验：

```text
sha256sum -c wangbin-software-consultant-1.0.0-expert-candidate.zip.sha256
-> wangbin-software-consultant-1.0.0-expert-candidate.zip: OK

unzip -t wangbin-software-consultant-1.0.0-expert-candidate.zip
-> No errors detected in compressed data
```

ZIP 成员共 4 项，唯一根目录为 `wangbin-software-consultant/`：

```text
wangbin-software-consultant/.codebuddy-plugin/plugin.json
wangbin-software-consultant/README.md
wangbin-software-consultant/agents/wangbin-software-consultant.md
wangbin-software-consultant/avatars/expert.png
```

以上只是本地源码、结构、完整性和哈希证据，不是 WorkBuddy 上传器解析、安装或召唤成功证据。

## 5. 官方流程与私有测试可行性

### 5.1 官方 Expert 流程

当前官方 Expert 文档显示：

1. Expert 展示在 WorkBuddy 客户端的专家市场。
2. 用户进入专家详情后点击“召唤专家”进入对话。
3. 开发者可从“我的专家 → 创建专家/创建专家团”进入创建流程。
4. ZIP 结构、配置字段、Agent 定义和头像规则有明确说明；解析失败时按文档结构检查并联系平台运营。[1]

官方入驻页面说明个人主体认证需要中国大陆二代居民身份证、实名手机号、可接收验证码的邮箱和人脸识别手机，并要求真实姓名、身份证、手机号和邮箱等信息。[3] 本阶段不代用户提交这些信息，也不要求用户在聊天中发送这些信息。

开发者公约要求提交版本的功能说明、运行条件、测试方式、依赖、收费、权限和数据用途与实际一致；需审核的资产在审核通过前不得公开发布。[2] 因此本阶段即使发现上传入口，也不会自动提交正式审核或公开发布。

### 5.2 草稿、非公开安装与真实入口

本次通过 HTTPS 读取的 Expert、入驻、开发者公约和收入变现官方页面，说明了创建、市场展示、召唤、审核和发布约束，但没有给出可由未登录用户确认的“Expert 私有草稿安装/非公开召唤”入口，也没有给出本账号的实际权限。页面所称“WorkBuddy 私有”字段属于 MCP 展示元信息，不是 Expert 私有测试权限。[1][2]

因此当前结论是：

```text
WORKBUDDY_PRIVATE_DRAFT_ACCESS = UNKNOWN
WORKBUDDY_INSTALL_PASS = BLOCKED
WORKBUDDY_DIALOGUE_PASS = BLOCKED
```

不能把官方文档存在、专家 ZIP 已构建或普通“创建专家”文案解释成已获得私有测试权限。

### 5.3 浏览器会话检查

优先进行了只读桌面/窗口检查：

- 本机没有可连接的 `127.0.0.1:9336` 浏览器 CDP 端点。
- 当前 Chrome 窗口中名为 `workbuddy` 的页面实际显示为 ChatGPT 对话，不是 WorkBuddy 开放平台页面；未导航、未点击提交、未上传文件，也未读取登录凭据。
- WorkBuddy AI 桌面进程当前未运行。

所以本阶段没有可授权的 WorkBuddy Expert 私有入口可供真实安装和对话验收。上述只读观察不代表 WorkBuddy 平台不可用，只代表当前会话没有可验证的目标入口。

## 6. 六类真实对话验收矩阵

下表是必须在 WorkBuddy 私有安装成功后执行的真实模型验收，不以站外模拟结果代替。由于当前缺少私有入口，六项均保持 `BLOCKED`，没有伪造回复或评分。

| 编号 | 实际对话输入方向 | 应核对的真实结果 | 当前状态 |
|---|---|---|---|
| D01 ERP | 描述采购、销售、库存、财务接口和角色规模 | 只把用户原话列为已确认；模块有输入/处理/输出/异常、依赖和验收；MVP/标准/完整范围可追溯 | BLOCKED |
| D02 MES | 工单、报工、质检、设备状态、操作员规模 | 不把设备协议或“支持所有设备”当事实；要求型号/版本/点位/网络证据；模块和工业联调边界可验收 | BLOCKED |
| D03 OA | 只说“想做 OA”，信息很少 | 首轮先给可用的最小流程草案，每轮不超过 3 个高影响问题，不编造人数、审批规则或价格 | BLOCKED |
| D04 AI Agent | 描述知识库、模型、自动化和人工复核需求 | 模型提供方、数据授权、推理费用、评测和准确率保持待确认；不保证效果，不隐藏第三方费用 | BLOCKED |
| D05 需求模糊 | 仅描述痛点，拒绝一次回答大量问题 | 明确已确认/合理假设/待确认，先交付有用初稿，问题最多 3 个且按成本影响排序 | BLOCKED |
| D06 预算不足 | 用户预算明显低于需求范围 | 计算过程可复核，指出预算与范围缺口，提出删减模块/分阶段验收，不保证原范围和原工期 | BLOCKED |

真实验收至少应保存：平台页面/会话标识、脱敏输入、完整输出、轮次、计算明细、平台错误提示和安装/卸载结果。不得保存或提交身份证、手机号、邮箱验证码、Token、客户名单或生产数据。

## 7. 本人可执行的人工步骤

仅在账号所有者自行完成登录和授权后执行，勿把凭据发到聊天：

1. 在浏览器打开 `https://open.workbuddy.cn`，使用账号所有者自己的登录会话。
2. 在“入驻开放平台”确认个人主体认证状态；若未认证，按官方页面在平台内完成认证。认证信息只在官方页面填写，不复制到本报告或聊天。
3. 进入“我的专家”或官方提供的 Expert 创建入口，先确认页面是否提供明确的草稿、预览、私有测试或仅自己可见状态。
4. 如果有非公开入口，只导入本地候选 `dist/wangbin-software-consultant-1.0.0-expert-candidate.zip`，确认 ZIP 能解析，核对名称、版本、分类、头像和简介。
5. 在不公开发布的前提下安装/预览并“召唤专家”，依次执行 D01～D06；保存脱敏结果，逐项检查需求状态标注、问题数量、模块验收标准、报价公式和未知费用边界。
6. 若页面只提供“提交审核”“发布上线”或任何会进入公开审核/市场分发的按钮，立即停止，不点击该按钮；把状态保留为 `BLOCKED`。
7. 不进入收入变现、不设置价格、不签约、不创建收费资产。官方收入变现流程需要资料审核和微信签约，发布时才设置免费、一次性或按月付费。[4]
8. 将平台解析、安装、召唤和六类对话的脱敏证据交回后，才能重新评估 `WORKBUDDY_INSTALL_PASS`、`WORKBUDDY_DIALOGUE_PASS` 和 `PUBLISH_READY`。

## 8. Phase 6 门禁

| 门禁 | 状态 | 证据范围 |
|---|---|---|
| SOURCE_AUDIT_PASS | PASS | 15 个 Phase 1～5 未跟踪文件逐项审查；secret scanner 0；无 `.env` 文件；dist/venv/cache 未提交 |
| GIT_IDENTITY_PASS | PASS | 当前 Git 用户名和邮箱配置存在；未伪造或擅自修改身份 |
| AUTOMATED_TEST_PASS | PASS | 全量 `31 passed, 1 skipped`；Expert 独立 `36 passed` |
| EXPERT_METADATA_PASS | PASS（发布限制） | 字段、路径、类别、头像和 license 元数据符合静态规则；作者邮箱仍为占位值 |
| PACKAGE_VALIDATION_PASS | PASS | 独立打包器 PASS；4 成员 ZIP；sidecar OK；`unzip -t` 无错误 |
| OFFICIAL_FLOW_REVIEW_PASS | PASS | 已读取 Expert、入驻、公约、收入变现官方页面；未把文档推断成账号权限 |
| WORKBUDDY_PRIVATE_DRAFT_ACCESS | UNKNOWN | 官方公开页面没有给出本账号私有草稿权限；当前浏览器没有目标入口 |
| WORKBUDDY_INSTALL_PASS | BLOCKED | 未获得可验证私有安装入口；未上传 |
| WORKBUDDY_DIALOGUE_PASS | BLOCKED | D01～D06 六类真实平台对话均未执行 |
| PUBLISH_READY | BLOCKED | 真实安装、真实对话、账号资格、占位邮箱和公开审核边界均未闭环 |

特别地，`PUBLISH_READY` 不得因本地测试、ZIP 哈希、站外模型模拟或官方文档阅读而变为 PASS。

## 9. Git 提交计划

本报告完成后，在再次执行 `git status --short --untracked-files=all`、`git diff --check`、候选包哈希和自动化测试确认没有新增未审查文件后，显式 `git add` 以下 16 个允许提交文件：15 个 Phase 1～5 文件加本报告。不得加入 `dist/`、`.venv/`、`.pytest_cache/`、`__pycache__/` 或其他个人/临时文件。

随后执行一次本地提交，不 push：

```text
git add <逐项审查后的 16 个路径>
git diff --cached --check
git commit -m "feat: add software consultant expert baseline"
```

提交完成后重新读取 `git status --short --untracked-files=all`、`git rev-parse HEAD`、`git show --stat --oneline --summary HEAD`，把真实 commit hash 追加到最终汇报；若 Git hook 或身份校验失败，不伪造 hash，保持未提交并报告实际错误。

## Sources

[1] https://open.workbuddy.cn/docs/expert
[2] https://open.workbuddy.cn/docs/developer-agreement
[3] https://open.workbuddy.cn/docs/onboarding
[4] https://open.workbuddy.cn/docs/monetization
[5] https://open.workbuddy.cn/docs/service-categories-individual
