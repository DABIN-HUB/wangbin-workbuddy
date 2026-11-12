# Decimal 算术 POC（独立实验，非 Expert 工具）

`fixture_synthetic.json` 全部是 **SYNTHETIC/FICTITIOUS 虚构演示**；并非真实客户项目、R5 原始回答或行情。四个文件是独立的 Python 标准库实验；没有接入 Agent、manifest、WorkBuddy、数据库或网络服务，也不进入既有五成员 Expert ZIP。输入只接受结构化 JSON，不解析自然语言。

## Windows 复现

在本目录执行（把输出放入已有受控交付区，不放源码目录）：

```text
py -3 estimator.py fixture_synthetic.json -o F:/ideaWorkSpace/wangbin-workbuddy-delivery/experts/wangbin-software-consultant/decimal-poc-t_3268574a/synthetic-output.json
```

测试时设 `POC_SCRATCH` 为现有、可写的 Hermes profile scratch 目录；要运行**原件复算测试**，还须设 `S30_POC_INPUT` 为受控交付区的 `decimal-poc-t_3268574a/s30-transcribed-input.json`，`S30_POC_RAW` 为既有 R5 `preqa-p02-r5-t_f55d0c99/raw/S30-MULTI-turn3/1/stdout.bin` 原件，然后：

```text
py -3 -m unittest discover -s . -p "test_*.py" -v
```

无法使用 `py -3` 时可用实际检查过的 `python`。测试只在 `POC_SCRATCH` 创建并自动清理由自身产生的临时文件。缺少 `S30_POC_INPUT` 时原件用例 SKIP，不得声称 S30 已复算。CLI 成功退出 0；JSON/字段/来源文件错误退出 2；`-o` 必填，缺失属于 argparse 错误退出 2。失败不覆盖旧项目证据；输出目标应为独立的新文件。

## JSON 合同

顶层必填 `scope_version,work_packages,buffers,pricing,outside_fees`。每包必须有非空 `id,function,source`，`tier` 在 `MVP/Standard/FullA/FullB` 中，布尔 `new`，同一 `scope_version`，`roles` 下 FE/BE/DB/QA 各有非负有限 Decimal 字符串 `low/high` 且低不大于高。确实不适用的角色明确填 `"0"`，未知或缺失不得填零。相同 ID 完全相同的重放只计一次，冲突拒绝。每个档位取之前档位唯一 ID 的并集，计算行/角色/档位及逐角色增量；`reported` 可选，形如 `{"Standard":{"roles":{"FE":{"low":"...","high":"..."},"BE":...,"DB":...,"QA":...},"B":{"low":"...","high":"..."}}}`，报告数与独立计算不一致会报错。结构化输入是已确定数值，不推断估时合理性。

`buffers.low/high` 为单独小数比率（0～1），且必须有来源；`B=Σ唯一行角色人天`，`R_low=B_low×r_low`、`R_high=B_high×r_high`，`E=B+R`；小数无浮点、无中途四舍五入。缓冲没有可信来源时不要喂入虚构值。`pricing.mode=fixed` 需用户定价字符串及来源，覆盖参考价；`reference` 使用用户批准的示意 1000/1500 元每人天（不是市场价）；`refused` 不输出 RMB。输出 `labor_rmb` 只表示有条件的人工费，不表示报价或项目总价。`outside_fees.status=unknown` 必填，完整项目金额始终为 `null`，不能把未知的接口/许可/云/部署/维护/税费当零。范围变更应复制出新输入快照、修改每包版本，并设 `scope_changed=true,previous_scope_version=旧版`；同版不能静默改变旧范围。POC 不负责不可变存档/事实认证，版本历史须另行保全。

## R5 原件与边界

原 `raw/S30-MULTI-turn3/1/stdout.bin` 留在交付目录，SHA-256 `18949697dbff9a62cfaf46f31e39f4e569b81b34adb5766fb2d3027e2d6f81fb`。受控目录中的 `s30-transcribed-input.json` 是**人工逐项转录**、每工作包 source 指原字节解码后行号，不是自然语言自动解析，也不是仓库 fixture。那里另存重算结果和逐项差异；原回答、用户输入、冻结 QA 原件保持不变。R5 模型输出 Standard A 角色列低 26/高 45，对比原 M1/M2/S1/S2/F1 真实行的 B 30/52，既有失败不改判。无授权的接口是否开放、工作量假设是否真实、费用是否可询、模型是否会采纳程序、平台是否能原生调用，均非 Decimal 可证明。

若将来**另行授权** Skill 集成，需要审核 Skill `SKILL.md` 自然语言入口、必要 `scripts/estimator.py` 与资源/schema、Skill 单测/契约与失败例、Expert manifest/Agent 的实际工具调用合同、打包器成员和平台运行；现有 `tooling/expert_rules.py` 是 prompt-only 校验，旧 packager 固定五成员，不可把本 POC 直接当成已安装可调用的工具。需独立测试工具调用、打包、平台权限/加载和正式 QA，本轮均未做。
