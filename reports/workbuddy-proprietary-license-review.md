# 四个经营分析 Skill 私有版权与 WorkBuddy 协议审查

范围：`wangbin-receivable-analyzer`、`wangbin-inventory-analyzer`、`wangbin-purchase-analyzer`、`wangbin-sales-analyzer` 的新候选 `0.1.2`。用户已明确选择保留版权、不采用 MIT 或其他开放许可；此决定只适用于这四个产品。仓库根项目、文档引擎、Connector 与已提交审核的软件顾问 Expert 的许可不随之改变。

## 官方文本与逐项结论

检索入口：[开放文档首页](https://open.workbuddy.cn/docs)、[Skill 规范](https://open.workbuddy.cn/docs/skill)、[开发者公约（试行）](https://open.workbuddy.cn/docs/developer-agreement)、[开发者服务协议](https://rule.tencent.com/rule/202608300002)、[收入变现](https://open.workbuddy.cn/docs/monetization)。以下 `NOT_FOUND` 仅指所核查的公开文本中未找到明确规定，不等于平台作出许可承诺。协议实际适用版本、账号签约及上传界面的额外要求尚未核实。本报告是工程合规核查，不代替法律意见。

| 问题 | 结论 | 官方条款及证据边界 |
| --- | --- | --- |
| Skill 是否必须开源 | **NOT_FOUND** | [服务协议 §8.8](https://rule.tencent.com/rule/202608300002) 规定“若您主动选择将创作的开发者能力进一步开源”，用户才依开源协议使用；这是可选择的情形，未发现强制开源。不能反推出任何自拟私有协议都获平台接受。 |
| 开发者能否保留版权 | **CONFIRMED**（有权利人前提） | [服务协议 §8.1、§8.3](https://rule.tencent.com/rule/202608300002) 保留双方既有著作权，并规定接入的开发者能力所有权及知识产权归开发者或相关权利人；第三方权利仍须事先授权。 |
| 平台是否明确接受本项目的私有版权声明 | **AMBIGUOUS** | [服务协议 §8.3、§8.6](https://rule.tencent.com/rule/202608300002) 没有要求版权转让且列出展示与分发，但未规定独立私有声明的审核规则；本账号和该声明均未实际解析/审核。 |
| 是否必须在 ZIP 中提供 LICENSE | **NOT_FOUND** | [Skill 规范：技能基础结构、Frontmatter 字段](https://open.workbuddy.cn/docs/skill) 只标注 `SKILL.md` 必须，列出 `scripts/` 等可选目录，未列出 LICENSE/NOTICE 强制项。本项目主动保留各自 `LICENSE`，不以文件名替代授权审查。 |
| 平台托管、安装、执行和分发所需授权 | **CONFIRMED / AMBIGUOUS** | [服务协议 §3.1、§8.6](https://rule.tencent.com/rule/202608300002) 将内容托管、发布与分发及平台内展示/分发纳入服务；[Skill 规范：技能市场](https://open.workbuddy.cn/docs/skill) 描述安装、对话调用。但具体账号生效协议、执行脚本及独立源码 ZIP 向用户交付方式尚不明确。不能声称获得超出有效协议的许可。 |
| ZIP 内能否放私有版权声明 | **NOT_FOUND** | [Skill 规范：技能基础结构](https://open.workbuddy.cn/docs/skill) 未列明 LICENSE，也未明文禁止附加版权声明；本地打包器支持，平台解析接受性仍为 `NOT_TESTED`。 |
| 平台是否向最终用户发放含源码的 ZIP | **AMBIGUOUS** | [服务协议 §8.6](https://rule.tencent.com/rule/202608300002) 允许展示/分发开发者能力，但未界定是否提供下载原始 ZIP。[收入变现：常见问题](https://open.workbuddy.cn/docs/monetization) 仅称付费资产会加密防护、云端运行，用户不易复制，并非保证技术上无法获取源码；需向平台确认免费/付费各自的源码分发边界。 |
| 付费 Skill 是否有额外代码授权要求 | **NOT_FOUND / AMBIGUOUS** | [收入变现 §2–§3](https://open.workbuddy.cn/docs/monetization) 要求主体入驻、审核和签约，可选一次性或按月付费；[开发者公约 §2.3.2](https://open.workbuddy.cn/docs/developer-agreement) 要求付费前告知费用及核心功能。未找到付费 Skill 必须开源或必须转让代码权利的条款；账号实际补充协议未知。 |
| 用户购买后的复制/使用权 | **CONFIRMED / NOT_FOUND** | [收入变现 §3.2、§3.3](https://open.workbuddy.cn/docs/monetization) 明确一次性购买后永久拥有的是**使用权限**，月订阅仅有效期可用；未找到源代码复制、修改、再分发或转售的独立授予。[开发者公约 §2.7.1](https://open.workbuddy.cn/docs/developer-agreement) 提醒公开可访问不等于允许复制、转售或再分发。 |

[开发者公约 §1.2、§2.1.2](https://open.workbuddy.cn/docs/developer-agreement) 规定公约与主协议同效力，提交时说明真实运行条件、依赖、权限、费用和数据用途；须经审核的资产未经通过不得公开发布。当前公开条款未发现与保留版权直接冲突，**不是**已确认本账号的协议版本或已获平台对该候选许可文本的认可。许可文本不覆盖、撤销或限制任何已生效平台协议。

## 四个产品的本地权利边界

- 仓库提交历史与产品元数据表明代码为项目内开发；脚本仅直接导入 Python 标准库，没有随包分发第三方库、模型或平台代码。该技术核查不证明雇佣、合作、委托或其他法律意义上的权属；上传前应由实际权利人复核。
- 四份 `LICENSE` 都是私有版权声明，声明权利以合法权利人实际拥有的范围为限，不独立授予用户复制、修改、再分发、转售源码的权限；平台必要运营行为依有效协议和适用法律执行。第三方许可证与法定允许行为不受其覆盖。
- 示例 CSV/JSON 标明 `fictional`，本地审查没有发现真实客户数据或凭证。用于实际业务的数据及分析结果仍需获授权处理。
- `license_policy.type=PROPRIETARY`、`decision=USER_CONFIRMED`；仓库内权利与依赖审查记录为 `PASS`，但 `platform_agreement=NOT_VERIFIED`。源 `SKILL.md` 和 `manifest.json` 都标记 `REQUIRES_MANUAL_REVIEW`。因此 `LICENSE_PASS=BLOCKED`，直到账号生效协议、版权声明审核边界与最终分发权限得到核实。

## 仍需账号所有者/平台确认

1. 查看该开发者账号实际同意的最新主协议、补充条款及付费资产协议，确认私有版权声明不与其冲突；留存脱敏条款版本/回执。**当前许可证门禁的直接阻断点。**
2. 问平台免费和付费 Skill 的 ZIP/脚本源码是否会被用户下载、复制或以其他方式访问，私有版权 `LICENSE` 是否允许作为 ZIP 成员；公约未给出确定答案。
3. 在正式提交前验证 ZIP 解析、Python 运行时、文件权限与实际 CSV 调用；涉及账号操作的试传、审核及公开发布均未由本轮执行。
4. 如四个资产涉及雇佣成果、共同作者或第三方文件，实际权利人应提供相应证明或授权；本地技术检查不能代替法律确认。

## 分离的发布状态

| 门禁 | 四个新候选状态 | 理由 |
| --- | --- | --- |
| `LICENSE_PASS` | `BLOCKED` | 私有版权已选，公开协议与账号生效协议/源码分发边界尚待核实 |
| `LOCAL_TEST_PASS` | `PASS` | 既有专项业务测试及解压样例执行通过；跳过项单独列示 |
| `PACKAGE_VALIDATION_PASS` | `PASS` | 本地源码校验、ZIP 完整性及登记哈希对齐 |
| `WORKBUDDY_ZIP_PARSE_PASS` | `NOT_TESTED` | 未向平台上传 |
| `WORKBUDDY_RUNTIME_PASS` | `NOT_TESTED` | WorkBuddy Python 运行时为 `UNKNOWN` |
| `WORKBUDDY_REVIEW_PASS` | `NOT_TESTED` | 无平台审核结果 |
| `PUBLISH_READY` | `BLOCKED` | 上述门禁未满足 |

A 人工平台试传：**当前不放行**（须先确认有效授权/许可文本及试传入口不会自动提交审核）。B 非公开运行验证：**未执行**，待试传放行且确认私有入口。C 正式提交审核：**不放行**。D 公开上架：**不放行**。

## 本轮本地验证记录

- 四产品既有专项测试：`30 passed, 1 skipped`；全仓库回归：`103 passed, 5 skipped`。跳过项全部是当前 Windows 环境无法创建符号链接的能力检查，未跳过业务计算测试。
- `python -m tooling.products validate`：`PASS`；`python -m tooling.products upload-list`：全部十产品报告已更新；四产品各自 `verify`：`PASS`，各自 `release-check`：`BLOCKED`（退出码 1，许可证需人工审查且平台未实测）。
- 四个 `0.1.2` ZIP 在独立 scratch 目录解压；各自脚本使用打包内虚构 UTF-8 CSV 实际运行，JSON 输出与包内 expected JSON 逐项相等；ZIP 完整性、顶层目录、私有声明、manifest 版本及 SHA-256 与台账匹配。
- 仓库凭证扫描为 `0` 项（扫描器排除 `dist/` 与 `reports/`；对本轮报告与 ZIP 成员另行检查）；Windows 原生绝对路径、UTF-8 JSON 和 ZIP 成员读取均经本地校验。旧 `0.1.0`/`0.1.1` 候选及受保护软件顾问 Expert ZIP 哈希未改。
