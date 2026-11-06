# Phase 7L 冻结字段基线复核与既有 partial 项目差距

> 本目录目前是**旧 Phase 7I partial 项目的审计基线**，不是 Phase 7L 新的高覆盖度项目，也不是 126 子项专业内容验收。

## 冻结合同核对

- `docs/solar-pv/03-input-fields.json`：469 个唯一 `field_id`。屋顶适用 386，地面适用 375；L2 屋顶 REQUIRED/CONDITIONAL/OPTIONAL = 292/85/9，地面 = 281/85/9。
- 该字典在 Git 历史中仅由 `b475c5e` 引入：当时也是 469 个定义，与当前版本的 `field_id` 集合差集为空。检索原始用户基线、冻结字典和项目历史未发现一份可核对的 486 个 `field_id` 定义；因此**不能捏造 17 个增加/合并/遗漏字段**，也不能断言历史记忆的来源已经查明。若用户提供历史 486 字段清单，可逐 ID 做差集审计。

## 既有项目实例覆盖（冻结定义数 ≠ 提供数）

| 项目 | 类型适用/不适用 | L2 REQUIRED 已提供/未提供 | L2 CONDITIONAL 已提供/未提供 | L2 OPTIONAL 已提供/未提供 | Phase 2/D3 | 计算状态 |
|---|---:|---:|---:|---:|---|---|
| Phase 7I 屋顶 partial | 386/83 | 139/153 | 42/43 | 0/9 | Phase 2 export 完整性通过；D3 所有行与原子通过读取校验 | PARTIAL |
| Phase 7I 地面 partial | 375/94 | 134/147 | 36/49 | 0/9 | Phase 2 export 完整性通过；D3 所有行与原子通过读取校验 | PARTIAL |

统计依据是 `industrial_rooftop-partial.json` 和 `utility_scale_ground-partial.json` 的各 469 条实例记录。L2 `CONDITIONAL` 的“未提供”不能一律算缺失：要用每条 `effective.L2.requirement` 判定是否触发、未触发或条件尚待确定。重复子字段在母数组不存在时不应按 184 个独立记录强制补齐。上表中 D3 字段的时序行数已作为实有实例计入；单字段的行数和原子数见矩阵中的 `d3_dataset_rows`、`d3_atom_count` 和 `instance_count`。`calculation_consumed_reported` 仅指 canonical 的 `used_fields` 记录，`report_binding_ids` 仅指内容 checklist 的输入绑定，不宣称已证明每一个数值在 Word 中被正确使用。

- 既有 partial 屋顶：类型适用字段已出现 181，D3 时序覆盖 18 个字段；地面：已出现 170，D3 覆盖 17 个字段。两者仍有大量未提供的 L2 REQUIRED，均不能称作完整案例。
- 矩阵中的 `source_ids`、`source_statuses` 及 `provenance_kinds` 表示已提交的来源身份，不代表真实性或授权审计已经关闭；所有旧案例合成资料仍为测试数据，不是实际审批、合同、测量或专业签章资料。
- 原子校验走 `read_bundle` 的实际内容读取；这不等于时序资源数据具有场址代表性，也不等于有权据此批准设计。
- 对旧 canonical 的 3G 校验仅证明合同和身份可验证；财务指标仍存在 `BLOCKED_MISSING_INPUT`、`NOT_IMPLEMENTED`、`UNDEFINED`，不能因为流程运行成功而把财务评价判为通过。

## 复核命令

```text
PYTHONPATH=. .venv/Scripts/python.exe -m tooling.solar_pv_input_audit INPUT_JSON BUNDLE_MANIFEST CANONICAL_JSON CONTENT_CHECKLIST OUTPUT_JSON --bundle-dir BUNDLE_DIR
```

输入分别使用历史 Phase 7I 两类项目的 `input.json`、`bundle-manifest.json`、`project/canonical.json` 和 Phase 7K 对应的 `content-checklist.json`；输出是审计快照，不改动历史项目。后续如获得真正的新计算输入和新 canonical，须用**新身份**重新运行，而非复制此基线。
