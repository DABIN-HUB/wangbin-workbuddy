# Phase 7 — `wangbin-software-consultant` 1.0.0 发布前最后检查与发布说明

核验时间：2026-10-26（UTC+08:00）
项目：`F:/ideaWorkSpace/wangbin-workbuddy`
基线提交：`90a938bc8f499e627ae11dd2dd64f29c3da50b12`
本阶段范围：只修正发布身份资料、Expert 授权声明、候选包和发布说明；不增加专家功能，不上传 WorkBuddy，不提交审核，不公开发布，不开启收费。

## 1. 本阶段变更

1. `packages/experts/wangbin-software-consultant/.codebuddy-plugin/plugin.json`
   - 将作者邮箱从占位值替换为用户本轮明确提供的真实工作邮箱。
   - 报告不重复展示该个人联系值；候选 `plugin.json` 内已使用用户提供的值。
   - 未修改 Expert 名称、版本、分类、提示词、标签或运行时声明。
2. `packages/experts/wangbin-software-consultant/LICENSE`
   - 新增标准 MIT License 文本，版权声明为 `2026 wangbin`。
   - 内容与仓库现有 `services/document-engine/LICENSE` 按去除末尾换行后的文本一致。
3. `packages/experts/wangbin-software-consultant/README.md`
   - 明确说明 MIT 授权只覆盖本 Expert 候选包中的资产，不扩展到仓库其他目录、历史文档引擎或未随包分发的专有代码。
   - 更新包结构说明，将 `LICENSE` 列为授权声明文件。
4. `tooling/phase5_expert_packager.py`
   - 将 `LICENSE` 纳入候选包成员清单；打包器仍只读取本 Expert 目录。

本阶段没有修改测试代码，也没有改变 Agent 的需求分析、估算、报价或隐私行为。

## 2. 授权与许可证结论

当前 `plugin.json` 已有 `license: MIT`，仓库根 `pyproject.toml` 也已有 MIT 元数据，仓库已有 MIT 文本文件。基于现有工程声明，本阶段保留 Expert 的 MIT 授权，并将完整许可证文本放入 Expert 根目录及候选 ZIP。

许可证范围被明确限制为：

```text
packages/experts/wangbin-software-consultant/ 下随 Expert 候选包分发的资产
```

这不是对整个仓库、旧文档助手、文档引擎、未打包源码或其他专有代码的重新授权。若实际权利人不希望 Expert 提示词、文档或头像采用 MIT，应在正式发布前由权利人将 `plugin.json` 的许可证声明和 `LICENSE` 一并改为符合其真实意图的方案；本阶段没有擅自作出专有代码开源承诺。

状态：`LICENSE_SCOPE = PASS_WITH_RIGHTHOLDER_CONFIRMATION`

## 3. Expert 结构、市场资料与头像

| 检查项 | 实际结果 | 状态 |
|---|---|---|
| name/version | `wangbin-software-consultant` / `1.0.0` | PASS |
| expertType/agentName | `agent` / `wangbin-software-consultant` | PASS |
| Agent 路径 | `./agents/wangbin-software-consultant.md`，与 agentName 一致 | PASS |
| 双语字段 | `displayName`、`profession`、`displayDescription`、`defaultInitPrompt` 均有 `zh`/`en` | PASS |
| 中文市场描述 | `displayDescription.zh` 长度 49，处于打包器要求的 40–50 字范围 | PASS |
| 标签/快捷提示 | 3 个双语 tags、3 个双语 quickPrompts；默认提示与第一条 quick prompt 一致 | PASS |
| 分类 | `12-IndustryConsultant` | PASS（账号最终可选类目仍需平台页面确认） |
| Agent frontmatter | 身份、描述、双语展示名和职业与 `plugin.json` 一致；没有 `skills`、`dependencies`、`tools` | PASS |
| 头像 | PNG，512×512，3786 bytes，低于 500 KB；SHA-256 `0834624d4c36a00f97e7634e1fe1ff3537cca2e63757871004f9f04d8d035114` | PASS |
| ZIP 根层级 | 唯一根目录 `wangbin-software-consultant/`，成员均位于其下 | PASS |

官方 Expert 文档说明了 Expert 创建入口、基本目录和配置规则；本地结构校验以当前仓库打包器和现有测试为准。[1] 官方类目文档可帮助核对行业顾问类目，但不能证明当前账号已经取得该类目或发布权限。[5]

## 4. 定价、市场文案与隐私合规

### 4.1 定价与商业声明

- `plugin.json` 没有 `price`、`pricing`、`payment` 或付款链接字段。
- README 和 Agent 明确写明：报价是用户输入或演示假设，不是市场验证价、正式合同、利润保证或固定工期。
- Expert 中出现的 URL 仅为 WorkBuddy 官方文档引用，不是付款、外链成交或个人联系方式。
- 未设置真实售价、一次性买断金额、月费、付款链接或收费开关。
- 未修改现有“仅在用户明确需要时简短说明合作”的限制，未增加强制广告或站外支付引导。

官方变现文档描述了资料审核、签约和付费资产发布流程；本候选未进入该流程，也没有开启收费。[4]

### 4.2 隐私与平台合规

- Agent 只处理用户在当前对话中主动提供的、为分析所需的文字。
- 明确禁止索取客户名单、业务密钥、账号密码、手机号、微信或无关文件。
- 明确要求敏感资料先脱敏，不把用户资料用于推广或虚构案例。
- 不声称访问市场报价、外部系统、第三方服务、真实接口或既有交付经验。
- 不承诺 Word/PDF 下载、真实市场价格、固定工期或模型准确率。
- 用户提供的工作邮箱只作为 `plugin.json` 发布者元数据，不写入 Agent 提示词，不作为对话中强制索取的联系方式。

开发者公约要求提交版本的功能说明、运行条件、测试方式、依赖、收费、权限和数据用途与实际一致；需审核资产在审核通过前不得公开发布。[2] 当前市场描述和 Agent 行为与本地实现一致，正式发布仍受账号审核与平台权限约束。

## 5. 自动化检查

### 5.1 全量项目测试

```text
.venv/Scripts/python.exe -m pytest -q
31 passed, 1 skipped in 61.29s
```

唯一跳过：`tests/test_security.py:38`，当前 Windows 环境不允许创建符号链接。该跳过来自既有文档引擎安全测试，不是 Expert 功能失败。

全量测试会通过 CLI 校验步骤重写 `reports/validate.json` 和 `reports/validate.md`；本阶段已检查并移除该测试副作用产生的重复校验条目，未将其作为本阶段变更提交。

### 5.2 Expert 独立测试

在旧的 4 成员候选 ZIP 尚未重建时，首次运行独立测试得到 `35 passed, 1 failed`；唯一失败是候选 ZIP 尚未包含新增 `LICENSE`，属于预期的旧包与新源清单不一致。随后重新打包并重新执行：

```text
.venv/Scripts/python.exe -m pytest -q packages/experts/wangbin-software-consultant/tests/test_expert_candidate.py
36 passed in 0.23s
```

该测试覆盖 `validate_source`、Expert 必填字段、Agent/提示词一致性、头像约束、ZIP 成员与源文件一致性、报价算术基线和 32 个静态场景目录。

### 5.3 安全扫描

项目 secret scanner 实际结果：

```text
secret_findings=0
```

本阶段没有把个人邮箱以外的账号凭据、Token、密码、私钥或连接字符串写入候选包、报告或提交信息。

## 6. 最终候选包

候选包已在源文件和打包器变更后重新生成，不能复用 Phase 6 的旧哈希。

### 6.1 上传文件

```text
F:/ideaWorkSpace/wangbin-workbuddy/dist/wangbin-software-consultant-1.0.0-expert-candidate.zip
```

### 6.2 配套文件

```text
F:/ideaWorkSpace/wangbin-workbuddy/dist/wangbin-software-consultant-1.0.0-expert-candidate.zip.sha256
F:/ideaWorkSpace/wangbin-workbuddy/dist/wangbin-software-consultant-1.0.0-expert-manifest.json
```

### 6.3 当前 SHA-256

```text
a1055a86b829c7bc774a4c47f8b2fd4462f567a77545b527d6ca500a1641c720
```

### 6.4 ZIP 成员

```text
wangbin-software-consultant/.codebuddy-plugin/plugin.json
wangbin-software-consultant/LICENSE
wangbin-software-consultant/README.md
wangbin-software-consultant/agents/wangbin-software-consultant.md
wangbin-software-consultant/avatars/expert.png
```

实际校验结果：

```text
sha256sum -c ...zip.sha256 -> OK
unzip -t ...zip -> No errors detected in compressed data
成员数 -> 5
```

## 7. 平台门禁与剩余阻断

| 门禁 | 当前状态 | 说明 |
|---|---|---|
| `SOURCE_AUDIT` | PASS | 变更文件已审查；secret scanner 为 0；未加入缓存和凭据 |
| `METADATA` | PASS | 用户提供的工作邮箱已替换占位值；Expert 结构、头像和市场字段通过本地检查 |
| `LICENSE_SCOPE` | PASS_WITH_RIGHTSHOLDER_CONFIRMATION | Expert 内含 MIT LICENSE，并明确不覆盖仓库其他专有代码；正式发布前权利人需确认授权意图 |
| `MARKET_PRICING_PRIVACY` | PASS | 无真实价格、付款链接或强制联系方式；文案和 Agent 保持隐私边界 |
| `PACKAGE` | PASS | 5 成员 ZIP、侧车 SHA-256、manifest 和 `unzip -t` 均通过 |
| `PRIVATE_PLATFORM_PATH` | UNKNOWN | 官方公开文档没有证明当前账号存在可用的私有 Expert 预览权限；未使用正式审核入口测试 |
| `WORKBUDDY_INSTALL` | BLOCKED | 本阶段未上传，未观察到解析/安装/召唤结果 |
| `WORKBUDDY_DIALOGUE` | BLOCKED | ERP、MES、OA、AI Agent、需求模糊、预算不足六类真实平台对话未执行 |
| `PUBLISH_READY` | BLOCKED | 缺少真实平台安装、召唤和对话证据；未确认账号发布资格 |

官方入驻页面要求在官方页面完成个人主体相关身份步骤；本阶段没有要求用户发送身份证、手机号、验证码或任何账号凭据。[3] 官方公约要求审核通过前不得公开发布。[2]

## 8. 人工上传前步骤

1. 由账号所有者在自己的浏览器中打开 WorkBuddy 官方开放平台并完成必要的账号/主体验证；不要把凭据或身份证明发到聊天。
2. 进入“我的专家 → 创建专家”或平台当前显示的 Expert 创建入口，确认页面是否提供草稿、预览、私有或仅自己可见的测试状态。[1]
3. 仅在明确的非公开入口导入：
   `F:/ideaWorkSpace/wangbin-workbuddy/dist/wangbin-software-consultant-1.0.0-expert-candidate.zip`
4. 读回页面显示的名称、版本、分类、头像、描述和解析结果；安装并召唤后执行 ERP、MES、OA、AI Agent、需求模糊和预算不足六类多轮对话。
5. 保存脱敏输入、输出、计算明细、轮次和平台错误提示；不要保存身份证、客户资料、生产数据或登录信息。
6. 如果页面只提供“提交审核”“发布上线”或会进入公开市场的按钮，立即停止，不点击；当前 `WORKBUDDY_INSTALL`、`WORKBUDDY_DIALOGUE` 和 `PUBLISH_READY` 继续保持 `BLOCKED`。
7. 不设置价格、不进入收入变现、不签约、不自动正式发布。

## 9. 本阶段发布状态

```text
LOCAL_CANDIDATE = PASS
CONTACT_PLACEHOLDER_IN_PLUGIN = RESOLVED
LICENSE_FILE_IN_CANDIDATE = PASS
PACKAGE_HASH = a1055a86b829c7bc774a4c47f8b2fd4462f567a77545b527d6ca500a1641c720
WORKBUDDY_INSTALL = BLOCKED
WORKBUDDY_DIALOGUE = BLOCKED
PUBLISH_READY = BLOCKED
```

## Sources

[1] https://open.workbuddy.cn/docs/expert
[2] https://open.workbuddy.cn/docs/developer-agreement
[3] https://open.workbuddy.cn/docs/onboarding
[4] https://open.workbuddy.cn/docs/monetization
[5] https://open.workbuddy.cn/docs/service-categories-individual
