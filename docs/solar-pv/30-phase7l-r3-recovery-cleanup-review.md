# Phase 7L-R3 收尾核查：历史恢复、定界清理与专业审阅

## 结论与范围

本次仅在 `main` 工作；不重算两套25年模型，不修改冻结469字段、89公式、正式算法或 R3-final-v5 的字节。**历史文件消失机制已查明，但触发者/具体命令仍未确定**；R3专业内容、真正的逐页视觉以及平台验收仍不通过。本记录不改变最终交付包的既有门禁状态。

## A. 历史文件调查及恢复

- 2026-11-07 22:05:54.471–22:05:56.197（北京时间），`F:\$RECYCLE.BIN\S-1-5-21-3134441471-2368069193-2402695265-1001\` 的 `$I` 元数据记录421个文件集中移入回收站；其中410个原路径位于本仓库 `reports/solar-pv/`。同名 `$R` 载荷存在且大小匹配。**仅能证明移入回收站，不能据此归责于某个 Bot、Git 命令、测试或外部程序。** 当前未找到能证明发起者的执行日志，因此删除原因未确定。
- 回收站中的 `phase7l-r2-delivery/` 包含原有25个文件。两份原始清单 SHA-256：屋顶 `cec094082957fb10e1f9f12628e5be58eb75d7dc703423f21edf1a9c0319914f`，地面 `8f05ef9f112bc5c469a43243e5ff3c77cdbc975da2ab7b88f825798c80ca11bc`。两份旧案例 `result_hash` 分别为 `398474aff972dee9f0a34bf85380a348bb27f8d4b102d7337ca0478ae0d34fe4` 和 `cd4fca1268dea37283a65680512774053d8e3008cd268375e7dd9f7e9abb2b46`，**不是** R3-final-v5 的 canonical，不能以 R3 清单冒充旧证据。
- 根据每个 `$I` 原路径、原大小和同名 `$R` SHA-256，逐文件复制回原处并重新读取比较：**365个缺失文件恢复（270,983,768 B），43个现有文件与回收载荷同字节，2个同名但字节不同的 R3 v5 回执未覆盖**。冲突仅为 `phase7l-r3-final-v5/ARCHIVE-RECEIPT.json` 与 `CASE-ZIP-RECEIPT.json`；保留工作区当前已提交版本和回收站原件，等待版本链路判断。恢复脚本/逐文件回执位于 Hermes scratch 的 `restore_solar_pv_recycle.py` 与 `r3-recycle-restore-receipt.json`；没有清空回收站。
- `phase7l-r2-delivery/{industrial_rooftop,utility_scale_ground}/manifest.json` 与回收站原载荷的 SHA-256 一致；清单 F01/F03/F04/F05/F06 的哈希均与恢复的原文件一致。该旧版本仍有独立价值：它与后续 fee-v4/R3 的计算及展示状态不同，适合追溯历史 R2 交付身份和回归语义，因此不作为“过时中间件”删除。

## B. 两项回归失败与受控输入

原失败的两项参数化用例同属 `test_delivered_r2_word_workbooks_and_canonical_keep_project_metric_identity`：其目的在于验证**原 R2 DOCX／19表 XLSX／10表来源 XLSX／canonical／manifest** 的项目身份、四个项目回报指标、文字及 XLSX 原始值；原用例从未跟踪的 `reports/solar-pv/phase7l-r2-delivery/` 取文件，导致 checkout 无法独立复验。

已从上述回收的原字节中选取每案 manifest、F01 DOCX、F03/F04 XLSX 与 F06 canonical，共10个文件／10,089,579 B，纳入 `tests/fixtures/solar-pv/phase7l-r2-delivery/` 的本地受控版本；清单 SHA-256 固定在测试中，文件逐项与清单比对，并保留原用例的业务断言。新增的 R3 交付用例还将 R3 canonical 与独立归档的 R2 fee-v4 canonical 对比，并核验 R3 DOCX、两 XLSX、canonical 的清单哈希和 IRR 的百分号单位。fixture 是**真实恢复的原始历史文件**，不是合成替代件；`.gitattributes` 对该受控目录设 `-text`，避免换行规范化改变哈希。

完整原聚焦命令（六个现有测试文件，新增受控 R3 用例，未 deselect）实际结果：**88 passed、2 skipped、1 warning，退出0**。两项原失败用例均执行并通过；2项既有 skip 标明 roof-only，warning 为 anyio/pytest 弃用提示。回执：Hermes scratch `phase7l-r3-recovery-full-focus-output.txt`。未执行六小时 L3，也未将此前的失败回执改写成通过。

## C. 限定范围的清理与保留

清理前快照（`reports/solar-pv/`、`services/solar-pv-engine/`、`tests/solar-pv/`、`tooling/solar_pv_*`、`dist/` 中 PV 文件）：**1,458 文件，723,632,886 B**；这发生在原历史文件尚缺失时，不能作为“恢复后清理前”空间基数。恢复原件后仅对经检查的引擎、测试和 tooling 目录中未跟踪且已忽略的 `__pycache__/*.pyc` 和 `wangbin_solar_pv_input.egg-info/` 逐文件计算 SHA-256 并删除：**328个、7,925,249 B**。删除前路径、大小、哈希在 Hermes scratch `r3-scoped-cache-cleanup-receipt.json`；本次**Git 跟踪文件删除数为0，废弃生产代码删除数为0**。缓存本身不承担关键审计证据；未删除已跟踪 `phase2d-parsers-red.txt`、R1/R2封存案例、v7、R3-final-v5、回收原件、其他产品或用户材料。

恢复及缓存清理后的同范围快照：**1,495文件，986,717,437 B**，其中报告范围1,261个（894跟踪、365恢复的未跟踪历史文件、2个已忽略且与既有回执哈希相符的日志）。另外本次受控 fixture 共10文件／10,089,579 B，属于 `tests/fixtures/solar-pv/`，不在上述前后统计范围。该段是本次大范围清理前的历史快照，后续实际删除见下节。

### C.1 受授权的历史产物清理（2026-11-08）

依据本轮授权，先以 Hermes scratch 中的 `solar-pv-cleanup-plan-20261108.json` 固定删除前逐文件大小和 SHA-256，再执行显式路径删除；没有使用 `git clean -fdx`、`reset --hard`、无差别递归删除或历史重写。删除前确认五个 Git 目录在源码、测试和文档之外无引用，并保留测试仍读取的两个封存25年案例、R2 fee-v4、R3-final-v5、诊断 v7、Phase 7I 审计记录和其他证据。

- 从当前 Git 版本删除 **188 个文件／118,489,925 B（Git blob 原始字节；本地删除前文件字节为118,583,778 B）**：`phase7l-r1-delivery`、`phase7l-r2-delivery-final-v4`、`phase7l-r2-delivery-final-v5`、`phase7l-r2-delivery-final-v6` 和已被 fee-v4 取代的 `phase7l-r2-delivery-final-fee-v3`。这些是无当前源码/测试引用的旧报告快照；R1/R2 原始计算树没有删除。
- 从恢复的365个未跟踪文件中删除 **316 个／226,581,158 B**：旧 R2 fee-v1/v2/v3、旧 R2/R3 delivery/final-v1/v2/v3/v4、Phase 7I chain partial review 和 Phase 5 synthetic rooftop 等重复或中间导出。
- 保留恢复未跟踪文件 **49 个／44,402,610 B**：原始 `phase7l-r2-delivery/` 25个文件作为回收站事件和旧R2独立身份的原字节证据；`phase7l-r2-delivery-final-v7/` 24个文件作为受保护 v7 历史包。两组都没有改写成新的 Git fixture，也没有将其哈希冒充当前 R3。
- 本次实际删除 **504 个文件／345,164,936 B 本地文件字节**（其中未跟踪恢复件226,581,158 B；Git删除项按本地字节计118,583,778 B）。Git 当前版本为 **1,215 个文件／613,730,231 B（blob 原始字节）**，报告范围为 **706 个／591,066,553 B**；本地仍有上述49个受保护未跟踪文件，因此工作区不会宣称为完全 clean。`phase7l-synthetic-review`、Phase 3B/3C/3D/3E 证据、Phase 7I upload review、dist 候选、`.venv` 和用途仍不确定的证据未删。

## D. R3 正文专业内容审阅：不通过

两案各有18章／100子项、13附录／26子项及42条本报告引用公式；DOCX和清单哈希吻合。独立机器审阅按规则标记屋顶64项、地面65项需进一步人工审阅；**其余子项并未因此得到专业批准**。实际正文抽读的 NPV、IRR、建设期/第1/第13/第25年 APP06 数值与 canonical 一致，但并非逐格重算。以下是独立专业复读发现的明确问题，不应将“126项非空”视为内容合格：

1. **CH05、CH08、APP02.01 资源口径**：两案12个月表按月出现 `GHI = DNI + DHI`（示例1月117.8＝86.8＋31.0 kWh/㎡），DNI 法向直射量不能未经太阳高度投影直接和水平散射量相加。屋顶月气温/风速全年固定24°C／1.5 m/s，地面固定28°C／2 m/s；合成来源虽有声明，但资源数据代表性、DNI定义及转置边界未闭合。应先核对原始合成时序和输入定义，不能擅自改冻结算法或重算 canonical；资源论证不能据此签收。
2. **CH04、CH09、CH11、CH12、CH14、APP04 工程与造价**：屋顶未取得具名结构、锚固、防水及消防复核，地面缺测绘、地勘、道路排水及桩基依据。4%预备费被录入但未在 CAPEX 单列；接网工程敞口未核量。项目 CAPEX 屋顶539,000元、地面1,085,000元，建设期付款分别467,000元、950,000元；不能将当前估算视作覆盖未核专项费用的工程报价。
3. **CH01、CH16、CH18 财务判断**：项目 NPV 约670,443.03／260,918.68元、IRR 约22.8723%／11.1565%有数值来源，但股东现金流、LCOE、保本价仍阻断，总状态 PARTIAL。地面 APP06 第13年项目净流出约31,954.21元，CH18未明确将更换年度资金缺口列为推进条件。不能由项目 IRR 推出股东回报。
4. **CH02、CH06、CH09、CH11、CH12、CH17、APP08**：若干小节以“待核”为主；屋顶64个、地面65个子项短于70字仅是提示，不是错误计数。缺具名政策条款、同口径设备方案比选、扰动情景和阈值分析；不能用延长免责声明替代专业论证。
5. **APP01、APP11、APP13**：APP01“本次有1个来源标识”仅针对输入登记，易被误读为整份报告唯一来源；APP11.01称“全部公式注册”但报告仅列冻结89式中的42条引用式，APP11.02约40式复用“同量纲才能相加”的模板校核，对乘法/除法/折现等不充分；APP13.01“同源版本与哈希”正文未完整列出可复核身份。需分别限定范围、逐式校核并补身份链。

这些涉及输入资源定义、工程第三方证据和冻结公式适用性，不能靠自动增补文字宣称解决；本轮不改变已签字节的 R3-v5 报告，也不伪造外部资料。上述问题及逐项专业签审是后续报告改版的明确阻断。

提交后读回补充：`HEAD:` 中 R3 包清单的39个成员与工作区原始字节及清单 SHA-256 均相同。历史 R2 fee-v4 的两个 `canonical.json` 在本机 `core.autocrlf=true` 下，Git blob 末尾为 LF、工作区末尾为 CRLF，因而**Git blob SHA-256 不等于工作区原始字节 SHA-256**；本轮提交的父提交中已有同一 Git blob，解析后的 JSON 内容相同。本轮未改该受保护文件，也不把 blob SHA 冒充其交付包字节哈希。

## E. 双案 PDF：逐页机器检查完成，真实视觉未完成

从各案 manifest、DOCX、PDF 逐字节读回 SHA-256；各案 DOCX 与 PDF 均匹配各自 F01/F02 清单，模型19表、资料10表通过本地文件读回。两份 PDF 均55页、A4、共110页以150 dpi本地渲染在 Hermes scratch `r3-pdf-audit/`；每页有可检索中文文本、连续页脚1–55、55/55页眉一致；没有空白、明显的文字坐标越界、页面边缘像素异常或检测到的孤立标题。目录2–7页各205条条目在目标正文页由完整标题或章节代码定位；P13各有2幅图，图框在页面内部；P55哈希分行需核验阅读观感。屋顶P8、P20–22、P24–26、P28和地面P8、P20–26、P29、P54为表格较密集的重点视觉页。`render_evidence.original_docx_sha256` 是 WPS 刷新前的原版 DOCX，与刷新后 F01 不同，版本链应以 WPS 回执/当前 F01 而非“同字节”解释。

**尚无对110张图片逐张进行主观人工视觉确认的能力与回执**；文字可检索、页码和边缘像素不证明细字、图例、表格跨页或字体观感合格。因此 `VISUAL_REVIEW=NOT_TESTED`、`FOUR_FILE_GATE=NOT_FORMAL_ACCEPTANCE` 维持不变。WPS 本地渲染成功不等于无人值守 WorkBuddy PDF 转换能力。

## F. 逐项门禁

| 门禁 | 本次状态 | 依据 |
|---|---|---|
| `WORKSPACE_CLEANUP` | `PARTIAL_SCOPED` | 已实际删除504个文件／345,164,936 B 本地文件字节，其中 Git 旧交付188个、恢复重复导出316个；仍保留49个受保护未跟踪历史文件及用途不确定证据，故不宣称完全 clean。 |
| `HISTORICAL_FILE_RECOVERY` | `PARTIAL` | 365个原字节恢复；43个相同，2个不同版本回执未覆盖；触发者未确定。 |
| `REGRESSION_TESTS` | `PASS_FOCUSED` | 88 passed、2 skipped、1 warning；不宣称全库或六小时 L3。 |
| `PROFESSIONAL_CONTENT_REVIEW` | `BLOCKED` | 存在资源口径、工程依据、公式校核和结论边界问题；未专业签审。 |
| `PDF_VISUAL_REVIEW` | `NOT_PERFORMED` | 110页机器渲染和异常扫描完成，人工全页视觉未完成。 |
| `FOUR_FILE_GATE` | `NOT_FORMAL_ACCEPTANCE` | 字节和机器读回通过，但内容/视觉门禁未关闭。 |
| `WORKBUDDY_PLATFORM_TEST` | `NOT_VERIFIED` | 未安装、上传、发布或运行平台验收。 |

本轮不 push、不发布、不启动 Phase 8。
