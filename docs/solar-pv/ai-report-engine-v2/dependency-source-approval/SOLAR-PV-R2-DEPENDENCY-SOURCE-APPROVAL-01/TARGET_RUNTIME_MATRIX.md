# 目标运行环境与兼容性

| 身份 | 实际证据 | 限定结论 |
|---|---|---|
| OS/client | Windows 10 10.0.19045 / AMD64 / 64bit；WorkBuddyAI 文件与真实进程 5.5.2 | 客户端存在，不证明 Python 绑定 |
| DEV | 根 .venv CPython 3.12.0，packaging 26.3 | 本次解析工具；DEV_ENV_ONLY |
| Hermes | CPython 3.14.9 | 不是 WorkBuddy interpreter |
| Skill Bash | 未获得直接解释器绑定 | UNKNOWN |
| Connector | 配置声明 Python 3.12，部署 exe 未观察 | UNKNOWN |
| 首个正式目标 | 未确认 managed interpreter | UNCONFIRMED_BLOCKED_BY_RUNTIME_IDENTITY |

以下 .0 patch 是旧 marker 环境代表值，不是部署观测。未来实际 patch 改变必须重新计算 Requires-Python/marker/tag；不能将 DEV 或声明 runtime 当实际宿主。
仅接受标准 GIL cp312/cp313/cp314 和适用旧 abi3，拒绝 t-GIL/abi3t。Linux 只条件研究 glibc/manylinux，不能混用 musl/未知 linux ABI；macOS 最低版本按每文件保留，arm64 至少 11.0，未知实际最低 OS 仍是条件。

| 原目标 | 候选数 | 缺口 | 活跃边 | 分发闭包 |
|---|---|---|---|---|
| Windows-AMD64-CPython3.12 | 41 | pypdfium2==5.15.1 | 65 | BLOCKED |
| Windows-AMD64-CPython3.13 | 41 | pypdfium2==5.15.1 | 64 | BLOCKED |
| Windows-AMD64-CPython3.14 | 41 | pypdfium2==5.15.1 | 64 | BLOCKED |
| Linux-x86_64-CPython3.12 | 41 | pypdfium2==5.15.1 | 63 | BLOCKED |
| Linux-x86_64-CPython3.13 | 41 | pypdfium2==5.15.1 | 62 | BLOCKED |
| Linux-x86_64-CPython3.14 | 41 | pypdfium2==5.15.1 | 62 | BLOCKED |
| macOS-x86_64-CPython3.12 | 39 | cryptography==50.0.2,onnxruntime==1.31.1,pypdfium2==5.15.1 | 63 | BLOCKED |
| macOS-x86_64-CPython3.13 | 39 | cryptography==50.0.2,onnxruntime==1.31.1,pypdfium2==5.15.1 | 62 | BLOCKED |
| macOS-x86_64-CPython3.14 | 39 | cryptography==50.0.2,onnxruntime==1.31.1,pypdfium2==5.15.1 | 62 | BLOCKED |
| macOS-arm64-CPython3.12 | 41 | pypdfium2==5.15.1 | 63 | BLOCKED |
| macOS-arm64-CPython3.13 | 41 | pypdfium2==5.15.1 | 62 | BLOCKED |
| macOS-arm64-CPython3.14 | 41 | pypdfium2==5.15.1 | 62 | BLOCKED |

十二目标固定点均未发现新增缺失节点、版本冲突、Requires-Python 冲突、未定义 extra 或未知边；这只是元数据闭合，不是实际分发闭包。
官方 magika 使用 python_version，旧 installed 使用 python_full_version（含通配 patch）；声明字符串不同，但在原 12 环境的活跃包/约束求值相同，不能外推所有可能环境逻辑等价。
MARKER_COMPARISON_CLARIFICATION.json 保存澄清；原图、官方 overlay 均未改写。

参见 [官方 wheel tag 规范](https://packaging.python.org/en/latest/specifications/platform-compatibility-tags/)、[PyPI JSON API](https://docs.pypi.org/api/json/)。本地五页官方 docs 全 HTTP200 身份在 manager-official-docs-index.json。
[WorkBuddy Connector](https://open.workbuddy.cn/docs/connector) 的托管环境声明与 [Skill](https://open.workbuddy.cn/docs/skill) Bash 能力需分开；不能从文档推导本机已部署、OS sandbox、资源上限或业务调用 timeout。

运行原证：`.runtime/solar-pv/SOLAR-PV-R2-DEPENDENCY-SOURCE-APPROVAL-01/manager-target-runtime.json` (10688 B, SHA-256 `b8473f93b579e53f46c9dc9f3e33b420101f42d6007cecd80d94b69cc903843d`)
