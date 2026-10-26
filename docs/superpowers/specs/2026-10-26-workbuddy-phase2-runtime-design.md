# Phase 2 运行时交付设计（2026-10-26）

## 授权范围与门禁

本轮仅交付本地可安装的 Python CLI、官方 CLI Connector 结构和与之绑定的 Skill 工作流。不得自动提交 Git、发布 Python 包、登录平台、设置收费或部署生产环境。Phase 1 的证据与 ZIP 不改写。平台安装、运行和审核状态依实际账号验证，不能由本地证据推断。

## 官方契约

- https://open.workbuddy.cn/docs/skill ：Skill 包的 `SKILL.md` 和可选资源目录已明确；scripts 可由 Bash 工具执行，但 Python/依赖托管机制及 ZIP 上传根层级未明确。
- https://open.workbuddy.cn/docs/connector ：CLI + Skill 连接器须有 `connector-meta.json`、`cli.json`、`icon.svg`，Skill 强烈推荐。CLI 至少支持 macOS/Linux，建议 Windows。`runtime.type=python` 自 WorkBuddy 5.0.0 起受支持，WorkBuddy 提供隔离 Python 环境；建议 `python -m pip install <package>`，不能假设用户预装 Python。认证命令应清晰，`status` 无副作用，`unAuth` 安全。安装/认证/状态分别有超时要求。连接器更新需要重新审核。
- 两个官方页面均未说明「随连接器 ZIP 放置的 wheel 如何从 init 命令定位」，不得猜测工作目录或新增非官方变量。

## 路线评估

A. 独立 Skill：Phase 1 ZIP 仅带适配脚本，不带引擎、Python 或 MarkItDown。没有平台保证的依赖交付机制；只保留为工作流说明，不作为可运行成品。

B. Python CLI Connector（采用）：文档引擎只保留一份源码，独立 Python 发行包从 `services/document-engine/src/` 同时构建引擎和 CLI 入口 `wangbin-document-cli`。锁定直接依赖版本，Windows 干净环境从**实际构建的 wheel**安装并联网安装锁定的 PyPI 依赖；依赖下载是明确的人工安装动作，不在文档处理时触发。交付可审计 wheel + 本地安装命令 + Connector ZIP + Skill ZIP。`cli.json` 使用受 WorkBuddy 托管的 Python runtime、非交互式版本化 `pip install` 命令。安装源需要把对应版本发布到用户环境可达的可信索引；本轮禁止自动发布，因此实际平台可获取性保持 BLOCKED，不把本地 wheel 安装视为平台安装通过。

## CLI 协议

`version`、`doctor`、`auth`、`status`、`logout`、`parse`、`batch`、`deduplicate`。业务输出 JSON；参数错误返回非零；文件错误使用引擎稳定代码；路径由用户明确授权并分别传入输入目录及独立输出目录。纯本地工具无需外部账号：`auth` 表示无认证要求，`status` 基于已安装包/依赖作只读检查并输出 `LOCAL_READY`，`logout` 不删除用户数据或配置；CLI 配置保留相同无账号语义。若平台拒绝无凭证连接，保留 BLOCKED，不制造虚假 OAuth。

## 验证与打包

在 scratch 新建独立 venv，不注入 `WANGBIN_ENGINE_SRC`、`PYTHONPATH` 或开发环境，安装本地 wheel + 依赖，再运行七格式、批量、去重、错误处理、安全路径和导出重读。构建 Skill ZIP 与 Connector ZIP 均使用显式白名单、重读成员/哈希；不修改 Phase 1 候选。平台根层级解析、Connector 安装、聊天实际调用、跨 OS 运行和 Python 包可获取性均保持独立门禁。
