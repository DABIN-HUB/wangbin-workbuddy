# 基线、构件与保护身份

源/文档基线 HEAD：`177951690bab2f0a11a75be15e2204be4820409c`，main；manager 的 remote main 只读结果与之相同，未 fetch/pull/push。
接管时 tracked diff/cached 均空，仅本任务 PLAN 未跟踪。

旧 solar wheel：.runtime/solar-pv/SOLAR-PV-R2-ENGINE-ARTIFACT-01/candidate-wheels/wangbin_solar_pv_input-0.3.2-py3-none-any.whl，557392 B，SHA `cd7be44ca5350da87c4760898ddeb46b8a73646d8f2f8de6be61e48cca9f7808`；保持不重建、不覆盖。
旧 SOURCE-REVIEW-ONLY.zip：2621668 B，SHA `fd4d52d6b6725902439779956c49b0fa8560839c562fa5ffaba605798198ae4c`。
旧 final-payload-index.json：304435 B，SHA `122400a048e9c94f84688c62f5f4a477566923c42f92bbf901f14d4b223e1c79`。

manager 已逐件绑定 129 源文件、十份旧正式文档及八核心；本轮用 manager-reused-source-document-binding.json 复用，不重做历史 wheel 审计。
保护账本 3458 文件需要末次逐 SHA 比对；installed Skill 22 文件需成员全集与逐 SHA 不变；R8–R13 的 2638 历史文件仅 size/mtime 元信息保护，不夸大为全文哈希复核。

## 12 外置必需 baseline

保持 EXTERNAL_BASELINE_RESOURCES=NOT_SELF_CONTAINED。未来经审批从批准 source commit/可信渠道只导出以下十二件，manifest 同绑 engine wheel SHA、baseline-lock raw SHA、各件 raw 与 UTF-8-sig/BOM/CRLF 规范化内容 SHA。
Catalog 构造会校验每一 lock 项；使用显式 baseline-dir，不能靠开发 checkout 静默兜底，不能修改 canonical。

| 源路径 | B | raw SHA256 | 未来相对路径 |
|---|---|---|---|
| docs/solar-pv/00-original-user-baseline.md | 35790 | 4af609040ca4e800b16d561b86a8a33c54226d175581b54aa00110158c5d09f2 | baseline/00-original-user-baseline.md |
| docs/solar-pv/00-baseline-manifest.json | 977 | 33845de976ec13345320b79ff7045e86a39bf2194a427b5cd28169238d1defec | baseline/00-baseline-manifest.json |
| docs/solar-pv/01-product-requirements.md | 9273 | 2bbda5ab6d34e2b21c8b8806335986522d75de3a90e8c2e677d4c2ae8075357c | baseline/01-product-requirements.md |
| docs/solar-pv/03-input-data-dictionary.md | 215547 | fcc1eac5641f941adbd6fd4fab216050344b2ae4e0590d8e9549682117ab8148 | baseline/03-input-data-dictionary.md |
| docs/solar-pv/03-input-fields.json | 593148 | 393140cc57b5934041c3fece2c9c185c03c7876afaa3403ce317d795d6112a1b | baseline/03-input-fields.json |
| docs/solar-pv/05-formulas.json | 490989 | d9d601c2cb2b1d6e18e552261c8cdbf9669ddbd8825addad2fa9c6f405c1a331 | baseline/05-formulas.json |
| docs/solar-pv/05-formula-extensions.json | 40985 | 14bb789c908f4f883910fd517fd2cf55cf0719739f9fdd84e4dc61b111252007 | baseline/05-formula-extensions.json |
| docs/solar-pv/05-field-bindings.json | 222309 | 4ef6171f063f402963d61edc9647c7565c9ec9338099f62424a77e3507521533 | baseline/05-field-bindings.json |
| docs/solar-pv/06-glossary.json | 157126 | fa29129d43f54a9b84ef6915e7bca99baa7a2a9a16ddab16beb3edec2e4d3ea5 | baseline/06-glossary.json |
| docs/solar-pv/06-glossary-extensions.json | 14387 | 108f2a0fc11e07286a571bdf4a9a1c2ba63e1e9deae81558c4407bb1f9b85b61 | baseline/06-glossary-extensions.json |
| docs/solar-pv/07-category-boundaries.md | 31298 | ee935418c0a7ef55544f6f97fddf71bcb62f6b906d0c19256b871f8d02b086a8 | baseline/07-category-boundaries.md |
| docs/solar-pv/08-baseline-contract.json | 11331 | b3616e8ca7deab31b41118f0ffd0a8202c763c54371a9a6949e5d97bdecb140c | baseline/08-baseline-contract.json |

## 11 可选 fixture

OPTIONAL_DEMO_FIXTURES=NOT_BUNDLED。属于既有 synthetic/editorial/regression 数据，不是授权真实输入；正式运行不依赖这些示例。
默认 editorial fixture 在 wheel 缺失的历史问题继续披露；若后续需要，单独申请演示包和分发权，不与 required baseline 混包。

| 源路径 | B | SHA256 | 性质 |
|---|---|---|---|
| services/solar-pv-engine/src/wangbin_solar_pv/fixtures/solar_pv_calculation/industrial_rooftop.json | 3188 | 146a1cf8ec92b035746ffcfd9c02b9dbb59103440a46d58b8ad05bbc06b78b00 | 非正式运行必要；SYNTHETIC；未打包 |
| services/solar-pv-engine/src/wangbin_solar_pv/fixtures/solar_pv_calculation/method_values.json | 3105 | 65fdaa53fd7c1cca4203d1c46649e832a4395cdf5cf3e8a35cd0f39e501d64b0 | 非正式运行必要；SYNTHETIC；未打包 |
| services/solar-pv-engine/src/wangbin_solar_pv/fixtures/solar_pv_calculation/utility_scale_ground.json | 2613 | 02ab1af30b4e2835a142c17c3f2f0673e92fb93a2f5d3812ffa67b83308215da | 非正式运行必要；SYNTHETIC；未打包 |
| services/solar-pv-engine/src/wangbin_solar_pv/fixtures/solar_pv_editorial/industrial_rooftop.json | 7285 | c5303d5658920f8d9c812550149591ce9f48bcb5b26731b09b5b808822edd0e8 | 非正式运行必要；SYNTHETIC；未打包 |
| services/solar-pv-engine/src/wangbin_solar_pv/fixtures/solar_pv_editorial/phase7l/industrial_rooftop.json | 8197 | 1584deab6dd11fc7d15379433590c7e81bc56840ec390293f2cd76efaa0fa6f4 | 非正式运行必要；SYNTHETIC；未打包 |
| services/solar-pv-engine/src/wangbin_solar_pv/fixtures/solar_pv_editorial/phase7l/utility_scale_ground.json | 8167 | acb08d4b680b4d35d50a25bbef771f6e04cfaeda4bc8a8f446510a47bae90c70 | 非正式运行必要；SYNTHETIC；未打包 |
| services/solar-pv-engine/src/wangbin_solar_pv/fixtures/solar_pv_editorial/utility_scale_ground.json | 7326 | 6f57fe9c2d977c269aa8d2351f865d1c1d45f1bf12471a1ed48a66da751c1bd8 | 非正式运行必要；SYNTHETIC；未打包 |
| services/solar-pv-engine/src/wangbin_solar_pv/fixtures/solar_pv_phase7l_full_cases/industrial_rooftop.json | 1692 | 8e5574ab17d37124121b1fd8eb84b12b7881b3ce583358111539673f22cf9d28 | 非正式运行必要；SYNTHETIC；未打包 |
| services/solar-pv-engine/src/wangbin_solar_pv/fixtures/solar_pv_phase7l_full_cases/utility_scale_ground.json | 1749 | 9b4a482e3446622f11d0ab6078388585d24eb8b52ef6dbab0ab31c7f495e01d5 | 非正式运行必要；SYNTHETIC；未打包 |
| services/solar-pv-engine/src/wangbin_solar_pv/fixtures/solar_pv_phase7l_r2_inputs/industrial_rooftop.json | 3111 | 2296279f98d96d83ae61eeb9a385d7ac4f9dcf411d26bf5a3fc4c071962ef682 | 非正式运行必要；SYNTHETIC；未打包 |
| services/solar-pv-engine/src/wangbin_solar_pv/fixtures/solar_pv_phase7l_r2_inputs/utility_scale_ground.json | 3120 | 6b50abecf88347462f6694ca73b3c3ce55df8918880b881335cee7ef4e68dadc | 非正式运行必要；SYNTHETIC；未打包 |

## 历史不可重放

HISTORICAL_RECEIPTS=PARTIALLY_NOT_REPLAYABLE：五条成功回执引用的四原输入不完整，不能用同名/其他版本或新值填补。原 HTTP raw 缺口也不能补造。
证据：license-identity/historical-input-identities.json；external-resource-plan.json 保存逐项 raw 与 normalized 比对及调用链。

`.runtime/solar-pv/SOLAR-PV-R2-DEPENDENCY-SOURCE-APPROVAL-01/license-identity/external-resource-plan.json` (30437 B, SHA-256 `39765e6f63c07bc02a878a914b093f3b053e57b15cd2cdf7e4b01642661d10da`)
