---
name: wangbin-estimate-calculator
display_name: 软件工作量与报价计算器
display_name_en: Software Effort and Quote Calculator
description: 根据有来源的工作包，复核全角色人天、风险缓冲、获准人工费与外部费用。
description_zh: 根据有来源的工作包，复核全角色人天、风险缓冲、获准人工费与外部费用。
description_en: Reconcile sourced work packages, role effort, risk reserves, permitted labor and external costs.
examples_zh:
  - "请按我给出的采购与库存工作包人天，核对每个角色和预算合计。"
  - "财务接口尚未获授权，请比较标准版有无接口时的人天差异。"
  - "我只要工作量，不要人民币报价，请复核完整版的条件范围。"
examples_en:
  - "Check the role totals and labor estimate for my supplied purchasing and inventory tasks."
  - "Compare the standard scope with and without a conditional finance interface."
  - "Recalculate the full scope effort after I remove a work package, without showing a price."
version: 0.2.0
author: 星核实验室 StarCore Lab
---

# 软件工作量与报价计算器

## Preparation / 准备

用户自然语言说明所求范围、实际工作包和分派角色、人天依据、版本、缓冲、费用与许可；不要求用户填写 JSON。依据本次实际加载的包内 Skill 定位根目录，阅读其 @references/input-output-contract.md 中现行 2.0-A/B 完整合同；不得把其他同名 Skill 或仓库预设路径当作该包。新咨询使用显式 `schema_version="2.0"`；无版本字段旧输入仅兼容原四档/五档，不能冒称旧回执覆盖增强项或用旧路径遮盖新输入错误。保留全部实际适用角色及唯一任务 ID；独立基准有据才录。真实未知、明确不适用、明确零及示意分别标状态；按实际加载的 2.0-A/B 语法记录有效数值来源和权限依据；核实范围和费用是否穷尽。每目标 coverage 仅 work/external 使用 COMPLETE/PARTIAL/NOT_APPLICABLE，source 是可定位的覆盖证据或缺口说明而非状态枚举。COMPLETE 要有已穷尽依据，未知或有缺项为 PARTIAL；确认无适用工作或无需独立外费分别明确有据 NOT_APPLICABLE，不以 COMPLETE 空表代替，不把未知或有据零当 N/A。运行依赖获授权的 Bash 工具及 Python 3 标准库，本文件不授权限。

## Usage / 使用

模型按当前话轮实际范围、报价版和来源整理一个 UTF-8 JSON 快照：`request.mode` 选择 full/tiers/scope，`money` 明确 none/labor/external/all，填实际 role_catalog、work_packages/assignments、逐目标 coverage、buffers、pricing、fees；从账本映射实际 ID，不虚构范围、缓冲、单价、角色、外费或档位。先核实本次实际加载的包内 Skill 根目录及同根 `scripts/estimator.py`；不假定调用端 cwd 是根目录，不使用仓库或开发机预设绝对路径。仅在环境明确允许执行、文件和输出目录均已获授权且新输出文件不存在时，通过 Bash 从已核实的 Skill 根目录调用 `python scripts/estimator.py <明确的输入.json> -o <新的回执.json>`，或将实际解析出的同一脚本路径作为独立参数调用（Windows 可用经验证的 `py -3`）；输入/输出路径必须明确解析到获授权位置，不因改变 cwd 而错读错写，所有路径作为独立参数安全引用，不将用户文本插入命令。不能确认加载根目录、脚本身份或权限时不调用、不猜路径、不换同名 Skill。只读明确指定文件，禁止覆盖旧回执。调用后核退出码、回执 SHA、输入 SHA 与脚本 SHA；拒绝/无权限不绕过或模拟成功。

## Processing / 处理

完整五档沿用 M/S/F/I 独立成员，I 只属 StandardB/FullB；指定档或局部按实际所求，不造其他档。按唯一分派→角色与包→各情景 B/R/E→逐角色 C；各档可有据覆盖默认缓冲，同档角色共用率。金额计算与展示按当前所求和最新 money 许可，优先于任何 Agent 场景/历史算例或人工复核：只要人天/不要金额用 money=none，禁止任何人工/外费、预算原数或差额、参考价/历史金额、TCO 与 token 等金额计算或回显；labor 只人工，external 只外费，all 仍须实际所求和来源许可。拒参考人工价且无有效价用 refused；明确需外费仍可按 external/all 实际许可计算依旧不编人工。统一固定价、角色固定/区间价和显式授权混合补价（权限来源符合实际加载的 2.0-A/B 语法）优先，只有 R5 允许时才用参考价且保留原声明；缺价或基准不擅补。外费按实际费用 ID/账户/目标、来源、直接金额或数量×单价、周期和税基归类，已含人工或排除的不二计；不自动换汇、推税率、把周期费混入一次性价。合法未知产生部分/阻断指标；结构/版本/冲突/非法值非零拒绝，无成功回执。接口条件估算不证明已获授权或已实现。

## Outputs / 输出

有效 2.0 回执核 schema/范围/报价版本、实际 request/目标、唯一包与分派、角色/缓冲、逐情景结果及来源，逐值对应 `COMPLETE/PARTIAL/BLOCKED/NOT_APPLICABLE/NOT_REQUESTED`；`known_subtotal` 不冒称完整 `value`。0 退出是回执写成，不等于完整业务报价。按自然语言交所求 B/R/E/C、明确参考价声明、有据费用分组及待核缺口；只有同币种已知一致税基及必要一次性费用完整才给对应一次性金额，局部金额不称全项目。外费、明确期数费用和人工许可各自保留。核 `input_sha256`、`script_sha256` 对应实际输入字节及已核实包内脚本字节，保留实际回执字节和回执 SHA；不凭工具名称认证未覆盖的数值。旧输入回执仅按旧合同核四角色等实际覆盖派生项。

## Limits / 限制

只验证实际输入结构及可核算的算术，不提取客户文件、不证明包完整、估时合理或接口可用；不自动排程、生成市场价格、兑换货币、推税率、签约/支付、推断真实财务结算或构建 TCO 引擎。无权限或无有效回执只能明确人工复核及缺口，不模拟执行或绕过拒绝。0.2.0 是 Expert 1.2.0 内的 Skill 分发身份，2.0 是现行计算合同；旧无版本输入兼容保留。本地有限合成输入回执不证明 WorkBuddy 加载、模型遵从、平台安装或发布。用户成果始终为文字/Markdown。
