# Python/runtime 兼容性 — 声明与实际执行分开

## 已执行的唯一构建环境

BUILD_PROVENANCE记录绝对exe `C:/Users/wangbin/AppData/Local/hermes/installs/dff2a7c1aa1d2670/environments/3d191065334546e08496a64b86fa12ed/venv/Scripts/python.exe`，Python3.14.9 AMD64，现有setuptools84.1.0。`setuptools.build_meta.build_wheel`已真实exit0，backend实测1.9162649996578693s；含快照取证的recorded批次11.623812300153077s。仅WHEEL_BUILT_LOCAL，不是开发安装、isolated import或目标runtime PASS。

| 环境 | 实际观察 | 本轮结论 |
|---|---|---|
| 上述Hermes独立现成python | 3.14.9；setuptools84.1.0，packaging26.3；无独立wheel/build分发 | 实际backend构建；不安装 |
| preflight python3对应环境 | 3.14.9，最初无setuptools/wheel/build/packaging；pip26.2.2 | 不能由一个命令的缺包推断整机backend缺失；各exe独立 |
| 根.venv与solar.venv | 各3.12.0；无setuptools/wheel/build/pip，根有packaging26.3 | 只读工具身份；DEV环境不能证明新wheel安装 |
| 已发现全局Python312 | 只读probe确认缺backend，见developer-discovery | 未改动/未补装 |
| ordinary Skill Bash | 实际exe/版本/依赖未观察 | UNKNOWN / NOT_TESTED |
| WorkBuddy Connector托管Python | cli.json只声明3.12 | 声明相交，不是已部署证据 |

后续一次裸 `python` metadata绑定尝试报packaging缺失(exit1)，保留原回执；改用**已构建成功的绝对exe**重跑exit0。不能假定跨工具/调用的PATH恒定，也没有为此安装任何包。每个实际调用exe/参数以command原回执为准。

## 12个目标仅做METADATA/marker矩阵

engine source与新wheel都要求 `>=3.12,<3.15`，新wheel tag `py3-none-any`。analyst逐一评估Windows AMD64、Linux x86_64、macOS x86_64和arm64 × CPython3.12.0/3.13.0/3.14.0；每格44 observed nodes、无选中图Requires-Python或版本约束冲突，最终绑定后每格仍缺42第三方独立wheel。完整表见DEPENDENCY_CLOSURE，明确不是可安装lock。

- 代表patch marker不等于所有patch、OS版本/libc、CPU、ABI和实机验证。py3-none-any只描述solar纯Pythonwheel，不覆盖第三方native依赖。
- cp312-Windows installed/cache WHEEL标识不能证明Linux/macOS或cp313/cp314构件可用；Pillow12.3.0所选元数据来自cp311-Windows解包cache，不是3.12+兼容wheel。
- NumPy/lxml/cryptography/cffi/rpds-py/onnxruntime/Pillow等须未来从真实目标wheel核对tags/ABI/Requires-Python与许可；不能复制现有site-packages当wheelhouse。
- build setuptools>=68与document的额外wheel构建需求单列于analyst/build-dependencies-metadata，不混入44 runtime nodes。setuptools的test/doc/core等extras未请求；现有backend内置bdist_wheel实际成功不意味着所有可选extras已装或dynamic requirements已闭合。

## 平台声明与未知边界

官方Connector页面将Python runtime声明支持起点列为WorkBuddy5.0.0。[1] 官方英文页面描述托管Python/virtualenv及独立pip cache。[2] 仓库Connector0.1.2声明Python3.12，与engine版本范围有交集；不能由此判定WorkBuddy5.5.2实际exe、patch、系统环境或3.13/3.14托管可用。

普通Skill脚本与Connector托管解释器是否相同仍UNKNOWN，必须未来通过获授权的实际身份/入口观察建立绑定；Skill资产存在/导入或Python开关不能取代这个证据。官方Skill结构列出必需SKILL.md和可选scripts；结构本身不证明engine部署。[3] venv/cache隔离不是OS沙箱；CPU/内存、业务命令timeout与进程树清理未知。文档生命周期init/auth/status/unAuth timeout不能外推到业务命令。[2]

本轮ISOLATED_INSTALLATION=NOT_TESTED，WORKBUDDY_SKILL_RUNTIME=NOT_TESTED，HOST_E2E=BLOCKED；无import/help/业务运行或跨OS PASS。离线设置及audit hook只限本地构建进程，未声称操作系统安全隔离。

## Sources

[1] https://open.workbuddy.cn/docs/connector — official-connector-zh
[2] https://open.workbuddy.cn/en/docs/connector — official-connector-en
[3] https://open.workbuddy.cn/docs/skill — official-skill-zh
