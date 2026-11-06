# Phase 7L-R2 集中式地面 25 年合成计算案例

本案例是独立版本的 SYNTHETIC 输入和普通 project 计算，非真实项目批复、签署地勘或投资批准；R1 封存案例不受影响。计算仍为 `PARTIAL`，真实工程证据为 `NOT_VERIFIED`。

从仓库根目录只读核验：

`python -c "from pathlib import Path; from tooling.solar_pv_phase7l_r2_inputs import verify_delivery; print(verify_delivery(Path('reports/solar-pv/phase7l-r2-full-cases/utility_scale_ground')))"`

`archived-d3-and-intervals.zip` 无损保留 D3 全部时序块和 3B/3C 区间记录；`expanded-file-manifest.json` 保存归档前逐件 SHA-256 与字节数。先将案例复制到独立工作目录，解压归档并按扩展清单校验，再以普通 project CLI 读取 `input.json`、`methods.json`、`budget.json`、`bundle/`、`terminal.json` 和 `terminal.txt` 重新计算。新运行会产生新 run ID，不得将旧计算哈希冒充新运行身份。`file-manifest.json` 与 `verification.json` 是本案例只读交付校验回执。

本轮新增合成任务及前置依赖；来源与字段真值见 `documents/source-material.md`、`category-effective-obligations.json`。这些输入用于模型和报告，不代表真实土地权利、接网或地勘签章。
