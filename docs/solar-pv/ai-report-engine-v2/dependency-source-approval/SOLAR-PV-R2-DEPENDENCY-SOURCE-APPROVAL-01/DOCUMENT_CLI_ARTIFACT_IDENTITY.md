# document-cli 1.2.0 双构件身份裁定

**DOCUMENT_CLI_ARTIFACT_IDENTITY=BLOCKED**。同名同版本不等于同构件；不得按 mtime/是否含LICENSE/新 generator 自动选。

| 原路径 | B | SHA256 | members | LICENSE |
|---|---|---|---|---|
| .runtime/solar-pv/ai-v2-host-20261112-144349/candidate-wheels/wangbin_document_cli-1.2.0-py3-none-any.whl | 20077 | 8f2ef2ab31c0f058612884ddf36a797b2dded4fc8ffdd5781453901e98a86bbd | 18 | 无 LICENSE |
| dist/wangbin_document_cli-1.2.0-py3-none-any.whl | 20970 | 999251868e5d9679860eb8f0c753fc3358dccf0b96dce05edea01a2501cae4aa | 19 | 含 licenses/LICENSE |

两个 ZIP 安全唯一、CRC/RECORD 静态校验已有真实原证；13模块原字节相同，且当前源码/Git LF一致，但共同 METADATA/WHEEL/RECORD 不同，dist 多 licenses/LICENSE。
候选曾有 No module named pip 的失败，后用 setuptools backend 的成功 JSON；原 build-source copy 现不可得，source commit/environment 绑定不足。dist sidecar 是身份凭据，不是构建来源证明。
当前模块相同不能倒推构建时commit。完整 member SHA、generator、依赖声明、METADATA/license原件与历史streams见 document-identity.json / document-originals。

后续需要两构件各自的原构建输入、精确commit、解释器/工具链、完整命令streams和许可来源链、不可变可获取渠道。若无法补足，另申请新无冲突版本可追溯隔离构建；本轮不重打1.2.0，不择一、不发布。

`.runtime/solar-pv/SOLAR-PV-R2-DEPENDENCY-SOURCE-APPROVAL-01/license-identity/document-identity.json` (52544 B, SHA-256 `529cd1d061e8783058f9af915c886dea410fd65c7315ceb51dba0b462f3b0325`)
