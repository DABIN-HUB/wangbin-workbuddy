# Phase D：既有双案证据只读核对（2026-11-16）

本记录仅核对**既有合成资料**，不重新生成/替换原件，不构成四文件、平台、专业或客户项目验收。原件仍保留在主工作树的 `tests/fixtures/solar-pv/phase7l-r2-delivery/{industrial_rooftop,utility_scale_ground}/`，CH08/10/16 对照及局部渲染件仍保留在 `.runtime/solar-pv/ai-v2-d-quality-20261112/`；R2/R4 历史受保护原件不得据此删除。不要把这批 R2 基准与其他 R13、R4 或新现金事件示例混成一个运行身份。

| 案例 | 冻结 input_hash | 冻结 result_hash | F01 DOCX SHA-256 | F03 测算 XLSX SHA-256 | F04 来源假设 XLSX SHA-256 |
| --- | --- | --- | --- | --- | --- |
| 工商业屋顶 | `656f694764e2afc1437cb6db603ecc23a9072fa5bea28495c9b036d540624556` | `398474aff972dee9f0a34bf85380a348bb27f8d4b102d7337ca0478ae0d34fe4` | `6a5b199721bf03615028d40e64e277720e18659ba33f7de27c0825840bd0e806` | `e7c703af58f32d6f3c482d1bdd589ca43ca45587bec06d00df5bbbba918859ee` | `645c2cabc5004003bd2bf675f608cf8d4feab23b39fc8a801eb9677787572435` |
| 集中式地面 | `41ffe63a77738f275dc6fefa3ad9bed6f6ce953098924eb2d27d84d3e1e025d3` | `cd4fca1268dea37283a65680512774053d8e3008cd268375e7dd9f7e9abb2b46` | `d3503491668625fb686a45db995b9144bf642deb9db995f634eb9b54bfb2c19a` | `8c767728c8af0097538447749f154b498a08a9af0e456de23ca6074003444a24` | `e026f888cde8d7dbeda584fa4eff1a8875b4071332d7ee6820524879804d37ab` |

只读复核使用 `python -c` + `json`/`hashlib`/`zipfile`/`openpyxl`/`docx`/`pymupdf`：两案 canonical、manifest 和对照收据的 5 项计算身份一致；6 个 F01/F03/F04 文件的实际 SHA-256 与 manifest 一致、ZIP CRC 正常。来源假设工作簿的输入台账等工作表和测算工作簿的项目参数/财务指标工作表实际含上述 `result_hash`。逐项把两案 `project_npv`、`project_irr`、静态/动态回收期的 canonical 数值与 F03 财务指标单元格核对（Excel 已按有限十进制数存储，金额容差 `1e-9`、其余 `1e-12`；**非逐位精确相等**），再把四个结果的读者展示值对照 CH16 DOCX 与局部 PDF 文本：共 16 项交叉检查通过、0 失败。屋顶展示为 679,602 元、23.08%、4.14/5.16 年，地面为 321,668 元、11.95%、6.7/10.33 年，均仅是原合成基准的显示精度。

`content-review-matrix.json` 包含两案 CH08/10/16 共 40 个条目（按案例各 20，其中 CH08/10 各 6、CH16 各 8），**40 个 `user_review` 均为 `PENDING`**；旧版与 AI 文本对照收据的计算身份一致；`rendered-v2/render-receipt.json` 中六个局部章节 DOCX/PDF 的文件哈希逐件读回一致。**这六份 PDF 只覆盖局部章节而不是正式 F02**，且实际提取仍有 U+FFFD（屋顶 CH08/10/16 分别 120/153/119；地面分别 120/107/119），不能当作全文可复制检索的交付 PDF。两案原 R2 manifest 的 F02 都是 `BLOCKED`，F04 都是 `DRAFT_PARTIAL`。静态 XLSX 不是经表格引擎重新计算的证明；摘要核对不等于全文逐页目视、数学公式语义或独立专业签审。

**未闭合门禁**：同一冻结输入的完整四件套（尤其全文真实 F02）未取得；公式 PDF 文字层、逐页视觉、专业内容仍待独立审阅；现有合成两案的日期现金事件、实际项目证明与 IRR 新控制不能凭空补入旧 canonical；Windows Skill 和 Connector 的各自解释器、依赖安装与真正调用/文件回传均未见本次运行回执（PATH 中未发现 `WorkBuddy.exe`，并不证明未安装），状态为 `NOT_TESTED`。现存 `dist` 两个旧候选的 ZIP CRC/sidecar/manifest SHA/许可证与 Git 忽略本机核对通过，**并非本次源码打包版本**；未经新的明确授权不安装、替换、上传或发布，也不推进 E/F/G。

本次专项代码验证与此旧 R2 证据属不同快照：`PYTHONPATH=services/solar-pv-engine/src python -m pytest -q tests/solar-pv/test_phase3e_dated_cash_events.py tests/solar-pv/test_phase3e_sourced_irr_controls.py tests/solar-pv/test_phase3e_irr_roots.py` → `31 passed, 0 failed, 0 skipped`；`python -m compileall -q` 指定两个受影响生产文件 → exit 0。未重跑此前已验证的长链，故新日期来源在整条 25 年项目编排/普通 CLI 中的运行状态仍为 **NOT_TESTED**；合成短表测试不能抹掉这一限制。
