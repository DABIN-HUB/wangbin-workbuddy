# 产品组合分析（仅已记录证据）

由 `python -m tooling.products portfolio` 的本轮实际输出整理。所有曝光、安装、使用、反馈、开发成本与维护成本目前均为 `UNKNOWN`；这不是数值零。未观察到可核实的平台审核通过记录；审核成功率、安装率和商业潜力均为 `UNKNOWN`，不能对任何产品下商业成功结论。

| 产品 ID | 版本 | 状态 | 审核证据状态 | 曝光 | 安装 | 使用 | 反馈 | 开发成本 | 维护成本 | 商业潜力 |
|---|---|---|---|---|---|---|---|---|---|---|
| wangbin-document-assistant | 1.0.0 | DEVELOPING | NOT_TESTED | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| wangbin-document-cli | 1.2.0 | DEVELOPING | BLOCKED | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| wangbin-software-consultant | 1.0.0 | SUBMITTED | USER_REPORTED_SUBMITTED | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| wangbin-tender-analyzer | 0.1.0 | DEVELOPING | NOT_TESTED | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| wangbin-receivable-analyzer | 0.1.0 | TESTED | NOT_TESTED | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| wangbin-requirement-impact | 0.1.0 | BACKLOG | NOT_TESTED | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| wangbin-inventory-analyzer | 0.1.0 | TESTED | NOT_TESTED | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| wangbin-industry-research | 0.1.0 | BACKLOG | NOT_TESTED | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| wangbin-purchase-analyzer | 0.1.0 | TESTED | NOT_TESTED | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| wangbin-sales-analyzer | 0.1.0 | TESTED | NOT_TESTED | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |

软件顾问的 `USER_REPORTED_SUBMITTED` 仅依据用户陈述，不能算审核成功。应在取得授权平台回执后，按版本填报曝光、安装、真实调用与脱敏反馈证据，再对比开发及维护成本。优先开发已登记的 `wangbin-requirement-impact`（可复用需求分析和证据清单）、`wangbin-receivable-analyzer`（可复用数据读取与待核实判定）、`wangbin-inventory-analyzer`（相同批处理/隐私边界）、`wangbin-industry-research`（可复用来源引用与报告模板）；第五个可选择既有路线图的 Excel 数据清洗专家，但在输入资源隔离、许可证与平台运行验证前不作为可公开发布承诺。
