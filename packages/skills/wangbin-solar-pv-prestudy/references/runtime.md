# 运行依赖与边界

## 交付模式

普通 Skill ZIP 可以携带 `scripts/` 和冻结定义，但官方 Skill 结构本身没有依赖安装声明；不能假设 WorkBuddy 会自动执行 pip，也不能假设宿主 Python、全局包或本地 `PYTHONPATH` 存在。因此本候选采用官方 Connector + Skill 组合：Skill 保留用户对话、输入契约和输出边界，CLI Connector 负责 WorkBuddy 托管 Python、隔离虚拟环境和版本化安装命令。

官方 Connector 文档说明：CLI + Skill 适用于已有成熟命令行工具；Python runtime 从 WorkBuddy 5.0.0 起可声明，平台准备托管 Python、隔离 pip/cache。该文档不证明本项目两个内部 wheel 已可从目标索引获取，也不证明 WorkBuddy 账号有私有试运行权限。

## Skill 包自身

- `SKILL.md`、references 和 `scripts/run_solar_pv.py` 使用 Python 标准库；不包含密钥，不自动联网。
- 脚本参数中的工作区内路径必须是相对路径，不能包含 `..`、空路径或绝对路径；工作区根目录由用户显式授权。
- `references/baseline/` 携带运行所需的 12 个冻结基线文件；其哈希仍由引擎 `baseline-lock.json` 校验。
- `--engine-root` 可以是包含 `src/wangbin_solar_pv` 的引擎目录，也可以是仓库根目录。也可使用环境变量 `SOLAR_PV_ENGINE_ROOT`；WorkBuddy 运行优先发现已安装的 `wangbin_solar_pv` 包，不依赖开发仓库。
- 未找到引擎时返回 `ENGINE_UNAVAILABLE`，不把脚本导入成功当作引擎可用。

## 计算引擎

当前仓库的 `services/solar-pv-engine/pyproject.toml` 声明 Python `>=3.12,<3.15`，以及：

- `jsonschema==4.26.0`
- `wangbin-document-cli==1.2.0`
- `openpyxl==3.1.5`
- `python-docx==1.2.0`
- `pdfminer.six==20260107`
- `defusedxml==0.7.1`
- Windows 上的 `tzdata==2026.5`
- `markitdown[pdf,docx,xlsx,pptx]==0.1.9`

WorkBuddy 平台是否能从授权可信索引取得这两个内部 wheel 不是本地 Skill ZIP 可以证明的事项；平台安装、调用和依赖解析保持 `NOT_TESTED` 或 `UNKNOWN`。当前仓库没有自动上传、发布或写入索引凭据。

配套 Connector 的 `cli.json` 安装命令（仅在用户授权的可信索引已经提供包时可用）固定为：

```text
python -m pip install --no-input --disable-pip-version-check --only-binary=:all: jsonschema==4.26.0 wangbin-document-cli==1.2.0 wangbin-solar-pv-input==0.3.1 openpyxl==3.1.5 python-docx==1.2.0 pdfminer.six==20260107 defusedxml==0.7.1 tzdata==2026.5 "markitdown[pdf,docx,xlsx,pptx]==0.1.9"
```

该命令不能在没有包源的环境中成功；失败必须保留为安装阻断，不改成源码路径或个人绝对路径。

## 引擎入口

- `python -m wangbin_solar_pv.cli ... project`：Phase 3G 统一项目计算。
- `python -m wangbin_solar_pv.cli ... report`：工商业屋顶报告导出。
- `python -m wangbin_solar_pv.cli ... ground-report`：集中式地面报告导出。

计算和报告都要求显式 workspace、baseline 和输入/输出路径；输出目录必须不存在，避免覆盖既有 run。建议在真实平台运行前由平台适配层提供私有临时工作区和隔离的 Connector-managed engine installation。

## PDF

报告导出器只在运行环境探测到合法 `soffice`/`libreoffice` 时生成真实 PDF。缺少转换器返回 `PDF_RENDERER_UNAVAILABLE`，不创建假 PDF。Windows 本地存在转换器也不证明 WorkBuddy 云端/沙箱环境具备同一组件或中文字体。

## 运行结果

脚本 stdout 为 JSON，至少包含 `status`、`project_type` 和 `report`；错误为 `FAILED` 或 `BLOCKED`，并给出稳定 `error_code` 与补充方向。不要把 `DRAFT_PARTIAL` 当作正式投资结论。
