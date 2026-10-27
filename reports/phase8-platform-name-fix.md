# Phase 8 — WorkBuddy Expert 名称解析错误针对性修复

核验时间：2026-10-27 08:47（UTC+08:00）
项目：`F:/ideaWorkSpace/wangbin-workbuddy`
修复前提交：`3c7e2e2c8ac826280be0846ef85b8eeb0e6edf99`
范围：只修复 WorkBuddy 真实上传反馈的专家名称长度问题并重新生成候选包；不修改项目 ID、Agent 文件名、目录路径或版本号，不上传、不提交审核、不公开发布。

## 1. 真实平台反馈

本次 WorkBuddy 真实上传测试返回：

```text
专家名称：当前 21 字，上限 15 字。
```

对应验收状态记录为：

```text
ZIP 解析失败：专家名称超长，已执行针对性修复，等待重新上传验证
```

该反馈是当前名称长度门禁的直接平台证据，优先级高于此前仅基于公开文档的静态约束判断。

## 2. 针对性修复

中文专家展示名称已统一为：

```text
软件需求与报价专家
```

实际检查并更新的位置：

| 位置 | 修复结果 |
|---|---|
| `.codebuddy-plugin/plugin.json` → `displayName.zh` | 已统一为 `软件需求与报价专家` |
| Agent Markdown frontmatter → `displayName.zh` | 已统一为 `软件需求与报价专家` |
| Agent Markdown 一级标题 | 已统一为 `软件需求与报价专家` |
| Expert README 市场介绍标题 | 已统一为 `软件需求与报价专家 · 1.0.0` |

当前中文展示名称长度为 9，低于 WorkBuddy 本次反馈的 15 字上限。项目身份保持不变：

```text
name/plugin = wangbin-software-consultant
agentName = wangbin-software-consultant
Agent 文件 = agents/wangbin-software-consultant.md
version = 1.0.0
```

已搜索 Expert 目录，旧中文专家名称不再出现在 `plugin.json`、Agent 或 README 中。`profession.zh` 是职业头衔而不是展示名称，保持原值；没有依据将其强行改成展示名称。

## 3. 英文名称与其他展示字段

当前字段长度检查结果：

| 字段 | 语言 | 当前长度 | 结论 |
|---|---:|---:|---|
| `displayName` | zh | 9 | 按真实平台反馈通过 |
| `displayName` | en | 49 | 未发现官方英文同等 15 字限制，保持不变 |
| `profession` | zh | 11 | 非专家展示名称；未发现长度限制，保持不变 |
| `profession` | en | 54 | 非专家展示名称；未发现长度限制，保持不变 |
| `displayDescription` | zh | 49 | 官方文档要求中文 40–50 字，当前通过。[1] |
| `displayDescription` | en | 157 | 官方资料未给出英文长度上限，保持不变 |
| `defaultInitPrompt` | zh | 22 | 默认提示词，不是展示名称；保持不变 |
| `defaultInitPrompt` | en | 70 | 默认提示词，不是展示名称；保持不变 |

官方 Expert 字段表确认 `displayName` 同时包含 `en`、`zh`，但本次检索到的公开资料只明确给出了中文 `displayDescription` 的 40–50 字要求，没有给出英文 `displayName` 的长度上限。[1] 因此没有猜测英文也必须限制为 15 个字符，也没有擅自缩短英文名称。

开发者公约要求名称、分类、标签和展示信息与实际功能及运营主体一致；当前短名称仍准确描述需求分析与报价服务，没有添加无关品牌、热点或搜索词。[2]

## 4. 新增长度校验

在 `tooling/phase5_expert_packager.py` 中增加：

```text
MAX_ZH_DISPLAY_NAME_LENGTH = 15
```

`validate_source()` 现在会拒绝超过 15 个字符的 `plugin.json.displayName.zh`，并返回明确错误：

```text
Chinese displayName must be at most 15 characters
```

校验关系如下：

- `plugin.json.displayName.zh` 通过长度检查。
- Agent frontmatter 的 `displayName` 仍必须与 `plugin.json` 完全一致。
- Agent 文件名、`agentName`、目录路径和版本号仍由既有校验保护。
- 通过临时内存副本将中文展示名称改为 16 个字符时，验证结果为 `overlong_zh_rejected=True`。

## 5. 本次自动化验证

Expert 独立测试：

```text
.venv/Scripts/python.exe -m pytest -q packages/experts/wangbin-software-consultant/tests/test_expert_candidate.py
36 passed in 0.21s
```

结构校验：

```text
validate_source=PASS
zh_display_name_length=9
zh_limit=15
en_display_name_length=49
overlong_zh_rejected=True
```

安全扫描：

```text
secret_findings=0
```

本轮未修改测试代码；长度校验由生产打包器的 `validate_source()` 执行，并由独立测试调用该校验路径。

## 6. 重新生成的候选包

候选包完整路径：

```text
F:/ideaWorkSpace/wangbin-workbuddy/dist/wangbin-software-consultant-1.0.0-expert-candidate.zip
```

SHA-256：

```text
577f3089d2f4707178f44ba1e5c395a99853bb9558f3e8c0e752a0e6ba2e30de
```

配套文件：

```text
F:/ideaWorkSpace/wangbin-workbuddy/dist/wangbin-software-consultant-1.0.0-expert-candidate.zip.sha256
F:/ideaWorkSpace/wangbin-workbuddy/dist/wangbin-software-consultant-1.0.0-expert-manifest.json
```

最终 ZIP 成员为 5 项：

```text
wangbin-software-consultant/.codebuddy-plugin/plugin.json
wangbin-software-consultant/LICENSE
wangbin-software-consultant/README.md
wangbin-software-consultant/agents/wangbin-software-consultant.md
wangbin-software-consultant/avatars/expert.png
```

完整性结果：

```text
sha256sum -c ...zip.sha256 -> OK
unzip -t ...zip -> No errors detected in compressed data
```

## 7. 当前门禁

| 门禁 | 状态 | 说明 |
|---|---|---|
| `DISPLAY_NAME_ZH_LENGTH` | PASS | 9 ≤ 15；生产校验已加入 |
| `METADATA_CONSISTENCY` | PASS | plugin.json、Agent frontmatter、Agent 标题和 README 标题已统一 |
| `IDENTITY_PRESERVED` | PASS | 项目 ID、Agent 文件名、目录路径、版本号均未变化 |
| `ENGLISH_NAME_LIMIT` | UNKNOWN | 公开资料未确认英文名称是否有相同上限，未猜测、未修改 |
| `EXPERT_STRUCTURE` | PASS | 独立结构测试 36 passed，头像和字段校验通过 |
| `PACKAGE_INTEGRITY` | PASS | 新 ZIP、manifest、sidecar、成员和压缩完整性通过 |
| `WORKBUDDY_REUPLOAD` | BLOCKED | 修复后尚未重新上传到 WorkBuddy |
| `WORKBUDDY_INSTALL` | BLOCKED | 等待平台重新解析和安装结果 |
| `WORKBUDDY_DIALOGUE` | BLOCKED | 真实召唤和六类对话尚未重新执行 |
| `PUBLISH_READY` | BLOCKED | 必须等待修复后真实上传验证，不能由本地检查替代 |

## 8. 后续人工操作

1. 在 WorkBuddy 平台重新上传上述新 ZIP。
2. 先确认平台解析显示的专家名称为 `软件需求与报价专家`，并确认不再出现 15 字超限错误。
3. 仅在允许的测试/草稿入口继续安装和召唤；不要进入正式审核、公开发布或收费流程。
4. 解析通过后再执行 ERP、MES、OA、AI Agent、需求模糊和预算不足六类真实多轮对话。
5. 如果平台仍返回新的字段限制，记录原始错误并按具体字段修复；不要根据未确认的英文限制自行缩短英文名称。

## Sources

[1] https://open.workbuddy.cn/docs/expert
[2] https://open.workbuddy.cn/docs/developer-agreement