# Q03-SAFE FIX-R1 开发修复与有界回放（待独立 QA）

- product_id=`wangbin-contract-return-check`; task_id=`t_10d1ec97`; workspace=`F:/ideaWorkSpace/wangbin-workbuddy-contract-return-check-export`; branch=`skill/contract-return-check-safe-export`; base_commit=`755e7d3f782e38aaa1710918bb10b027ef9b33e3`（安全空根 `e4548cf38ad18d0d371bfdb49c7f0629560212f0`）；冻结 expected commit=`d2ca02acb4f9052f87747a845f14e669f89b6c11`，generator/test commit=`e11ef20de9c17b9b0bdd03ad754500ec678ad78a`。本报告最终 result_commit 见卡片 handoff / `git rev-parse HEAD`。
- 本卡范围仅行尾配置及新增虚构输入、事先冻结预期、聚焦开发者测试、报告。无业务脚本/正式三合同/产品 manifest/SKILL/旧候选改动；无 push、上传、发布；**开发者自测不是独立 QA PASS，远端推送仍 DENY 等待 QA-R1**。

## 1. 行尾根因、前后可复现证据

Windows 全局 `core.autocrlf=true`（`git config --show-origin --get core.autocrlf` → `file:C:/Users/wangbin/.gitconfig true`），原导出无适用于业务脚本的属性；Git blob `a59d9588395553f4d1503433f97c543e27f53085` 保存 LF，但 Windows `checkout` 把工作文件变为 CRLF。`git archive` 直接输出 blob 的 LF；**archive 自身不会变 CRLF**，真正的失败链是 Windows checkout/platform 写入工作文件后 packager `Path.read_bytes()` 取实际 CRLF；之前 QA 的 archive 观察值和这个机理不能混为一谈。只增加 `.gitattributes` 单一业务脚本 `text eol=lf`，仍使用原透明原字节打包器（无改写业务源码/旧ZIP）。`git check-attr text eol -- packages/.../compare_contracts.py` → `set / lf`。

| 独立对象 | 修复前 QA T03（rc） | 本卡修复后实测（rc） |
|---|---|---|
| 原 HEAD 工作脚本 SHA-256 | `6d98f24a2bde5848fdab547ed91e2e4bb9dbbc300177f4269f6b234524477a0e` | `sha256sum F:/ideaWorkSpace/wangbin-workbuddy-contract-return-check/packages/skills/wangbin-contract-return-check/scripts/compare_contracts.py` → 同 SHA，rc0 |
| 清洁工作文件脚本 | QA checkout `634d3ee71596bdaf893162bf483264f9128752f767f488c496ba96ae64cb45bf`（454 CRLF；当时 package rc0 却与冻结不符） | `git -c core.autocrlf=true checkout-index --all --prefix=<scratch>/checkout/` rc0；文件 SHA `6d98f24a2bde5848fdab547ed91e2e4bb9dbbc300177f4269f6b234524477a0e` |
| Git archive 解包工作文件 | QA 报告 archive/clean 链最终偏差见上 | `git archive e11ef20... | tar -xf - -C <scratch>/archive` 两端 rc0；脚本 SHA 同 `6d98f24...` |
| ZIP 成员 SKILL.md / manifest.json / 脚本 | QA 重建脚本 `634d3ee...`，其余两个一致；旧包脚本 `6d98f24...` | `package` 和 `verify` 均 rc0；成员依次 `d0cfb4cedbe87021cb81d938a9fe4dc2a78e2d01fe933cab4b7c50536fcb9456` / `3edd098fc0d2b1604c6726891141fe5e16493d5375c8c51bbf22a5449b844c12` / `6d98f24a2bde5848fdab547ed91e2e4bb9dbbc300177f4269f6b234524477a0e`；checkout/另一次 archive 重建都相同 |
| ZIP SHA-256 | QA `5a87431ee76e00d53e1bb90f28d9b649fde8e994c7deaa1894fa95f552a2b5d6`，旧0.1.3 `dcf93fcdca8684316975ac4254cdfe381966af1ede133d943e356b3e53ea55ee` | 两种 clean 输入均 `dcf93fcdca8684316975ac4254cdfe381966af1ede133d943e356b3e53ea55ee`，分别 package rc0，checkout verify rc0 |

复现命令：在该导出树 `git -c core.autocrlf=true checkout-index --all --prefix=C:/Users/wangbin/AppData/Local/hermes/profiles/wb-developer/cache/scratch/q03-safe-fix-r1/checkout/`，再运行 `.venv/Scripts/python.exe <checkout>/tooling/package_contract_return.py package --output <scratch>/rebuilt.zip` 与 `verify --output <scratch>/rebuilt.zip`；archive 路径 `<scratch>/archive`、`archive-rebuilt.zip` 另独立重包。`validate` 本导出 rc0，`package --output dist/qa-synthetic/fix-r1-before-commit.zip` rc0 ZIP 同冻结；已存在输出绝不覆盖。旧 ZIP 对象未改。

## 2. 事前冻结的合成输入/期望与开发者实际范围

`tests/fixtures/contract-return.matrix.json` 在 `d2ca02ac...` **先于** generator/test 实测冻结 41 个新 case（旧 `contract-return.expected.json` 5案未改），记录每案段落、可变表格、受控 OOXML 修订/绘图/文本框、损坏/穿越/限额、命令情形及 expected；`tests/generate_contract_fixtures.py` 只创建新目录中的虚构 DOCX、记录每侧 SHA，禁止覆盖。`tests/test_fictional_matrix.py` 调当前真实源码 CLI、成功时重开四表 XLSX 和可编辑 DOCX、复核源哈希及匹配的类型/状态/定位/候选等；**没有**用 actual 回填/修改 expected。聚焦命令 `.venv/Scripts/python.exe -m pytest tests/test_fictional_matrix.py -q -rs --basetemp=dist/qa-synthetic/fix-r1-pytest-v2` 实际 rc0，**36 passed, 5 skipped（1480.58 s）**，不是 41/41。首次同命令 `--basetemp=.../fix-r1-pytest` 终端被 420s 截断且没有最终结果，NOT_TESTED，不计 PASS。原 27 项的 QA 证据是 **26 passed + 1 skipped (WinError1314)**，本轮未重跑原27，非27/27。

以下逐案 `expected → 本轮开发自测 actual`；详细精确原文、各选项及预期在已冻结 JSON；`P` 仅表示有界断言通过，绝非独立 QA/完整业务合格：

| 案例 | 冻结预期摘要 | 本轮实际 |
|---|---|---|
| CON01_negation_date | 不含税→含税、2026-12-01→2027-01-01 原词保留，无虚构法律推断 | P（原词断言） |
| A02_identical | COMPLETE、0 ID、同表格、四表 | P |
| A03_add / A03_delete | 只 ADD / 只 DELETE，另一侧 N/A | P / P |
| A04_move | MOVE 一条，正文段落1→3 | P |
| A05_number | NUMBER 一条，金额无改动 | P（类型断言） |
| A06_table | 两条 MODIFY，表格1行2列 | P |
| A07_candidates | PARTIAL；重复付款保留候选，独立交付 MODIFY | P |
| A08_reverse_add / A08_reverse_core | DELETE 与 60→30 缩短30天、NUMBER | P / P |
| A09_obligation | 可以→必须、含税→不含税保留 | P |
| A10_revision | NEEDS_INPUT / REVISION_STATE | P |
| A11_drawing / A11_textbox | PARTIAL 未支持载体，不能报无变化 | P / P |
| A12_draft / A12_ambiguous_draft | 仅确定 ID 草稿且未发送 / 纯歧义无编造 | P / P |
| A13_source_sha | 正向 SHA 不变 | P |
| A14_three_ids | MODIFY、NUMBER、ADD 各一，3 ID | P |
| E01_missing_role / E01_same_file | NEEDS_INPUT ROLE_AMBIGUOUS | P / P |
| E02_bad_bytes / E02_zip_traversal | ERROR INVALID_DOCX，无成功成果/越界写 | P / P（仅状态与无 XLSX 断言） |
| E03_oversize / E03_many_units / E03_long_text | ERROR LIMIT_EXCEEDED | P / P / P |
| E03_xml_entity | ERROR INVALID_DOCX | P |
| E04_formula_literal / E04_negative_amount / E04_at_literal | 工作表原文为字符串、非公式 | P / P / P |
| E05_collision / E05_output_is_file | 新名保留旧成果 / ERROR IO_FAILURE | P / P |
| F01_unrelated / F01_anchored / F01_same_number | PARTIAL 保留双方候选；付款锚仍确定 | P / P / P |
| F02_positive / F02_new_directory | 无链接授权路径两成果 / 新目录创建 | P / P |
| F02_input_symlink / F02_parent_symlink / F02_output_symlink | ERROR UNSAFE_PATH，原目标不变 | **NOT_TESTED**，创建符号链接 `WinError 5` |
| F02_parent_junction / F02_output_junction | ERROR UNSAFE_PATH，目标不读写 | **NOT_TESTED**，`cmd /c mklink /J` rc1 Access denied |

`F01-P1/P2/B1/A1` 由 A04/A07/A08/核心几案的虚构素材组合涵盖，但**组合路径本身未单独独立验收**；`F01-B2/P3` 由同号歧义、A03 独立增删素材覆盖，组合增删与歧义同案 NOT_TESTED。`F02-B1` 的竞态替换、`E02` 加密包/旧 DOC、`E03` ZIP 炸弹、`E05` ACL 不可写目录、`C01` 宿主对话仍 NOT_TESTED，已列 `limits_not_represented`；焦点筛选、多轮问法、图片 OCR/真实授权、第三方 wheel 及传递许可证、WorkBuddy 平台/发布亦 NOT_TESTED。固定预期的部分细粒度字段（法律推断、无金额变更、ID 全跨表一致、边界以下正例）尚未实现自动强断言，QA 须另行审阅，不以 36 passing 代替完全覆盖。旧五案本轮未逐案重新运行，仍仅沿用前次 QA 的局部事实。

## 3. 安全边界与残余

`git rev-list --objects e4548cf...HEAD` 与旧 `e4548cf..2003e5d...` 精确 OID 交集只有 5 白名单 blob `51c9e214,6edcb488,7635c83d,7e3522d,a59d9588`（此处简写，见 `git rev-list`），加 2 个只含白名单成员的安全子树 `84cee2020e8d02ec55f6f0edadb8cb309e85fc3a` / `93306df6b35273ed3a3f6c1c822fe7cdb4a00277`；旧 HEAD 不是本分支祖先（`merge-base --is-ancestor old HEAD` rc1）。`git ls-tree` 这两树仅含 SKILL、manifest、脚本；`git ls-tree -r --name-only HEAD | rg -i '(^|/)(qa|dist|.*\.(docx|zip|xlsx))($|/)'` rc1，无拒绝 DOCX/旧 QA/ZIP 路径；新增差异的常见 token/凭证及本机绝对路径模式 `rg` rc1。未直接列出 T00 所有拒绝 OID 的逐个读回，交独立 QA 复核。原 worktree `skill/contract-return-check` HEAD `2003e5d0bf4fb645e37e0b41298da7de97642822`、status 空；导出分支以精确路径暂存并 `git diff --cached --check` rc0，本地提交之后 status 空。报告提交前再次核 staged 差异与安全扫描。

**blocked_reason**：无实现阻碍；独立 QA 尚未给结论，symlink/junction 环境无授权能力。`SOURCE_SAFE_EXPORT` 开发者观察满足修复条件，不自判安全/QA 总门禁 PASS；普通 push 在本卡明确禁止。
