# wangbin-solar-pv-cli

这是 `wangbin-solar-pv-prestudy` Skill 的 CLI Connector 候选，不是第二套光伏计算引擎。

## 运行方式

- WorkBuddy 最低版本：5.0.0。
- WorkBuddy 托管 Python runtime：3.12。
- `init` 使用隔离环境安装固定的 `jsonschema==4.26.0`、`wangbin-document-cli==1.2.0`、`wangbin-solar-pv-input==0.3.1`、`openpyxl==3.1.5`、`python-docx==1.2.0`、`pdfminer.six==20260107`、`defusedxml==0.7.1`、`tzdata==2026.5` 和 `markitdown[pdf,docx,xlsx,pptx]==0.1.9`。
- `status` 只有在两个 Python 包都能导入时返回 `LOCAL_READY`。
- 用户项目资料只在授权的本地工作区处理，不自动上传第三方服务。

## 分发阻断

本仓库不自动发布 wheel，也不写入索引凭据。两个固定版本必须先由权利人发布到 WorkBuddy 托管 Python 可访问的可信索引，或由用户提供经审核的私有索引；否则 `init` 会真实失败，Connector 必须保持未连接。不要把本地源码目录、IDE 路径或个人绝对路径写入 `cli.json`。

请同时安装 `wangbin-solar-pv-prestudy` Skill 0.1.2；本 Connector 仅提供运行时，不替代 Skill 的输入契约和输出安全边界。
