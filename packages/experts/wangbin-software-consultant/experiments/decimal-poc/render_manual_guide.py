"""Render a user guide only from frozen and executed Decimal receipts."""
import hashlib
import json
from pathlib import Path

ROOT = Path('F:/ideaWorkSpace/wangbin-workbuddy-delivery/experts/wangbin-software-consultant/calc-integration-01')
MANIFEST = ROOT / 'frozen-before-model.json'
ZIP = 'F:/ideaWorkSpace/wangbin-workbuddy-software-consultant/packages/experts/wangbin-software-consultant/experiments/decimal-poc/dist/wangbin-estimate-calculator-0.1.0-licensefix1.zip'
TITLES = ('简单工作包', '五档与条件接口', '仅改人工单价', '拒绝人民币', '删除工作包与版本变更', '工具错误与未知费用')


def main():
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
    out = ROOT / 'workbuddy-manual-test-guide.md'
    if out.exists():
        raise SystemExit('guide exists: refuse overwrite')
    lines = ['# WorkBuddy Skill 手动试用指南｜CALC-INTEGRATION-01', '',
             '**SYNTHETIC 虚构数据；本指南已准备，平台安装/执行 NOT_TESTED。** 此为独立 Skill，并非原 Expert 正式集成。', '',
             '## 用户本人操作：上传前与证据边界', '',
             f'- **唯一新包**：`{ZIP}`；SHA-256 `56ca2fd8c5bd5abbb7a31f0163a4ef3293f6d6ecb8ed21a10f6d075a893fd9b6`。根目录恰有 SKILL.md、scripts/estimator.py、references/input-output-contract.md、原 MIT LICENSE。旧三成员 technical-candidate.zip 缺许可证，历史 FAIL，禁止上传/使用。',
             '- 官方客户端入口（https://www.workbuddy.cn/docs/workbuddy/From-Beginner-to-Expert-Guide/Function-Description/Skills-Market，“查看技能/上传技能”）：左侧「专家·技能·连接器」→「技能」→「添加技能」→「上传技能」→拖拽或选择文件。自行上传不可用“对话安装市场技能”替代；在「已安装」列表核对该技能和开关。上传前另核 https://open.workbuddy.cn/docs/skill 当时有效的 Skill 结构、ZIP 格式、解析提示与第三方脚本风险，确认 Bash/Python 权限、安装/激活状态与安全提示；有权限才由用户本人操作。本文不代替登录/上传/安装/审核/发布，不上传 Expert ZIP。',
             '- 保存入口及版本、ZIP 文件和哈希、安装/启用/权限截图、完整会话与失败原文；遮挡账号、令牌和个人信息。仅用下面 SYNTHETIC 工作包。用户无需掌握 JSON 命令：可上传对应虚构输入文件或复制文件内容给助手。若文件/工具访问无授权，停止并记 BLOCKED_PERMISSION。',
             '- **证明真实工具调用**：要有同一轮 `tool_use` 及配对 `tool_result` 原始事件、命令参数、输入 JSON/脚本 SHA-256、计算器内层 rc 与 shell 外层 rc、回执字节/哈希及最终回答逐字段对账。回答自称“已调用”或仅有截图不能证明执行；日志缺失记 NOT_TESTED_TOOL_EVENT，绝不判工具 PASS。不要把本地算出的预期冒充客户端实测。',
             '', '## 冻结输入与预期的再现', '',
             f'- 本目录 `frozen-before-model.json` SHA-256 `{hashlib.sha256(MANIFEST.read_bytes()).hexdigest()}`；每案 `{ROOT.name}/WB-xx-input.json` 是全部角色低高、缓冲、单价与版本的冻结虚构数据；`WB-xx-expected.json` 是现有 Decimal 脚本实际执行的完整回执，WB-06 故意拒算无输出。旧 S30 场景用于业务来源，而不是把历史模型结果当正确预期。',
             '- 以下每案列的 B 为基础人天、R 为缓冲人天、E 为含缓冲人天；C 仅为条件人工人民币，外部费用 UNKNOWN，完整项目总额始终 null。`低 / 高`；角色 FE/BE/DB/QA 与每行、成员、条件接口增量逐字段以对应完整回执检查。',
             '- 平台实测证据放在用户有权私有位置 `WB-xx/<session-id>/{question.txt,input.json,tool-events,receipt.json,answer.txt,screenshots,verdict.md}`，不得存储真实客户资料到源码库。当前六案均未在 WorkBuddy 执行，状态 NOT_TESTED。', '',
             '## WB-01 ～ WB-06', '']
    for (case, record), title in zip(manifest['cases'].items(), TITLES):
        if hashlib.sha256((ROOT / record['input']).read_bytes()).hexdigest() != record['input_sha256']:
            raise SystemExit(case + ': frozen input changed')
        if record['output'] and hashlib.sha256((ROOT / record['output']).read_bytes()).hexdigest() != record['output_sha256']:
            raise SystemExit(case + ': frozen receipt changed')
        lines += [f'### {case}：{title}', '', f'**直接复制提问**（附上或复制 `{case}-input.json` 中虚构工作包）：', '',
                  '> ' + record['prompt'], '',
                  f'- 来源：`fixture_branches_synthetic.json` → 冻结输入 `{record["input"]}`；全为 SYNTHETIC/ASSUMED，非真实客户估时。',
                  '- 预期动作：按当前范围和版本辨明已知/示意/未知；用计算器真实验证行与角色列、方案 B/R/E 和许可下的 C；读取真实事件、错误码、回执。工作包估时合理性仍需人工评审。',
                  f'- 冻结命令（在开发环境**已实际运行**；平台用户无需执行）：`{" ".join(record["command"])}`；计算器 rc `{record["calculator_rc"]}`；输入 SHA-256 `{record["input_sha256"]}`；输出 SHA-256 `{record["output_sha256"] or "NOT_APPLICABLE（拒算，无回执）"}`；stderr SHA-256 `{record["stderr_sha256"]}`。']
        if record['expected']:
            lines += ['- **实跑 Decimal 预期**（B / R / E / C，低/高；不是平台已通过）：', '',
                      '| 方案 | 唯一包 ID | B 人天 | R 人天 | E 人天 | C 人工人民币 |', '|---|---|---|---|---|---|']
            for plan, value in record['expected'].items():
                fmt = lambda key: ' / '.join(value[key][side] for side in ('low', 'high')) if value[key] is not None else 'null（拒价）'
                lines.append(f'| {plan} | {", ".join(value["ids"])} | {fmt("B")} | {fmt("R")} | {fmt("E")} | {fmt("labor_rmb")} |')
            lines += ['', '- 同时比对原始回执 `rows` 每个角色 FE/BE/DB/QA 低高与逐行和、`tiers.*.roles` 列和、`delta_roles` 增量；StandardA/FullA 不含 I1，StandardB/FullB 各含一次 I1。']
        else:
            lines += ['- **实跑 Decimal 预期**：脚本输入错误 rc2，原始诊断见 `WB-06-stderr.bin`，不存在成功回执；缺角色/无效数值不能用零补足，未获回执不得称已复核。']
        special = {'WB-03': '工时 B/R/E 必须与 WB-02 不变，只改 C。',
                   'WB-04': '回答不能出现人民币金额，仍必须核算 B/R/E。',
                   'WB-05': '保留 v1 原件，当前 v2 各档不得包含已删除 S2；不可把历史报价混入当前。',
                   'WB-06': '无法执行脚本时不得说已复核；未知接口/许可费不能填零。'}.get(case, '')
        lines += ['- 必须拒绝：' + record['prohibited'] + ' ' + special,
                  '- 工具事件证据：该轮原始用户文字、Skill 权限/身份、实际 tool_use 参数↔tool_result、计算器内层与外层 rc、输入/脚本/回执字节 SHA 和最终回答差异；无事件标 NOT_TESTED_TOOL_EVENT。',
                  f'- 结果记录位置：用户私有 `WB-{case[-2:]}/<session-id>/`；平台 verdict：**NOT_TESTED**。', '']
    lines += ['## 判定与结束', '',
              '平台逐案 PASS 需真实安装与权限回执、模型工具事件、输入/输出与角色和/条件分支/拒价/变更逐字段一致；不符 FAIL。没有事件、权限或截图分别按证据缺口标 NOT_TESTED_TOOL_EVENT / BLOCKED_PERMISSION / NOT_TESTED，不以本地预期替代平台。用户本人保留每次安装报错、权限拒绝、答复与工具差异及原始会话，不覆盖失败原件。', '']
    with out.open('x', encoding='utf-8', newline='\n') as file:
        file.write('\n'.join(lines))
    print(out, 'sha256', hashlib.sha256(out.read_bytes()).hexdigest())


if __name__ == '__main__':
    main()
