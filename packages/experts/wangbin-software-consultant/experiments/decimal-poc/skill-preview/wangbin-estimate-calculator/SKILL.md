---
name: wangbin-estimate-calculator
display_name: 软件工作量与报价计算器
display_name_en: Software Effort and Quote Calculator
description: 根据已确认或明确标为示意的工作包，复核软件项目分角色人天、条件方案缓冲及人工费。
description_zh: 根据已确认或明确标为示意的工作包，复核软件项目分角色人天、条件方案缓冲及人工费。
description_en: Reconcile sourced software work packages into role effort, conditional scope alternatives, risk buffers and labor-only estimates.
examples_zh:
  - "请按我给出的采购与库存工作包人天，核对每个角色和预算合计。"
  - "财务接口尚未获授权，请比较标准版有无接口时的人天差异。"
  - "我只要工作量，不要人民币报价，请复核完整版的条件范围。"
examples_en:
  - "Check the role totals and labor estimate for my supplied purchasing and inventory tasks."
  - "Compare the standard scope with and without a conditional finance interface."
  - "Recalculate the full scope effort after I remove a work package, without showing a price."
version: 0.1.0
author: 星核实验室 StarCore Lab
---

# 软件工作量与报价计算器

## Preparation / 准备

用户用自然语言说明范围、逐包角色 FE/BE/DB/QA 的低高人天、依据、版本、缓冲来源及价格意向；不要求用户填写 JSON。先核实工作包是否完整、冲突/撤销是否已处理；未确认的工时只可标 `ASSUMED`，不能将模型建议认作已确认。阅读 @references/input-output-contract.md 的完整受限输入输出定义。运行依赖获授权的 Bash 工具及 Python 3 标准库；本文件不授予工具权限。

## Usage / 使用

模型整理当前会话最新有效范围为一个 UTF-8 JSON 快照，记录每个包的用户话轮定位或明示假设；需要缓冲、角色数时不得擅填未知为零。仅在环境明确允许执行、文件和输出目录均已获授权且新输出文件不存在时，通过 Bash 调用 `python scripts/estimator.py <明确的输入.json> -o <新的回执.json>`（Windows 可用经验证的 `py -3`）；路径作为独立参数安全引用，不将用户文本插入命令。不要读取未指定资料；调用后核对退出码、回执 SHA、输入 SHA 与脚本 SHA。试试这样问：按这些工作包复核标准版有无财务接口的角色人天。

## Processing / 处理

把 `membership` 明确填写为五方案集合：MVP、StandardA、StandardB、FullA、FullB；接口仅属于 StandardB/FullB，FullA 不含接口，FullB 共享包只算一次。按每行 FE/BE/DB/QA→方案 B→R→E→人工费依次核算；报告冲突、缺项、版本混用、非法数值时工具退出 2，停止报告数值，要求澄清后新建快照。固定单价优先；用户拒价或只要人天时选 `refused`，不显示人民币。接口没有授权时 B 档仅为条件示意，不视为已经打通。

## Outputs / 输出

取得有效回执后，以自然语言列逐包来源及五方案唯一 ID、逐角色人天和 B/R/E，必要时列条件人工费、示意参考价声明及缓冲来源；输出单位为人天、人民币仅为人工费。回执包含 `input_sha256`、`script_sha256`、范围版本及 `complete_project_total_rmb=null`；第三方费未知必须另列待询价。核对答复每个数字与回执相符；失败不输出伪造总价。候选 ZIP 供用户自行手动测试，并非平台安装回执。

## Limits / 限制

只验证已输入的结构与算术，不提取客户文件、不证明包完整或估时合理；角色分价、已知外费/总价、真实接口条件、税费及维护费不在本技术候选计算范围。无 Bash/Python 或文件权限时明确说未完成工具核算，不模拟执行；本地测试不等于 WorkBuddy 安装、原 Expert 集成或正式报价。待业务方核查全部假设与来源，平台运行和上传由用户另行确认。
