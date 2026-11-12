# V2-EXC-004：原生宿主会话授权与恢复入口

A类必要技术补充；依据用户本轮WorkBuddy宿主H0–H4任务。不是新版本、付费API方案、计算方法变更或平台上传授权。冻结report-spec、稳定小节、89公式及canonical不改。

## 缺口

现有Skill只走legacy报告；章节CLI缺少普通宿主可使用的授权绑定/来源记录/恢复cursor。宿主声明ID不是独立认证。合法事实引用不能证明财务语义。两个内部wheel分发及实际平台工具链尚未验证。

## 最小接口

- 新增 `python -m wangbin_solar_pv.reporting.host_session`，复用原prepare/accept/resume/Workspace/Registry。只开放CH08试点，真实宿主双案通过前不解锁CH10/16。
- `--workspace` 为授权根；`--grant` 为根内JSON，绑定canonical相对路径、SHA-256、项目类型、来源ID白名单及当前宿主处理授权。授权文档不可由模型自行扩大。
- `--run` 为独立目录；授权/模型/规格变化须新run。检查点只列状态、摘要和下一步，不提供旧正文作为新模型输入。取消只禁止后续本地写作提交，不声明终止远程模型。
- provenance记录来源类别（WORKBUDDY_HOST声明/USER_SUPPLIED/PROTOCOL_REPLAY）、模型声明、实际可见会话/调用标识及request/output摘要；未暴露项用NOT_EXPOSED_BY_HOST。不生成伪平台UUID；专业及平台认证始终单列。
- 相同request/output/provenance的重复提交只重验已接受结果；不同提交拒绝。恢复重建证据与上游，不信本地PASS字符串。
- 保留chapter-result/2.0原有必需字段；可选 `claims[].risk_assertions` 表示需要机械核查的事实含义与预测/实绩性质。缺证、不匹配或无法验证的强现金/股东/DSCR/零值断言拒绝；没有结构化声明的自然语言仍NOT_VERIFIED、必须专业复审。旧稿不因新增可选字段而被改写。
- Skill脚本只启动已安装引擎并给出有界命令超时；没有引擎或未确定正确解释器则停止。不偷偷注入开发者仓库或PYTHONPATH。

## 新增验证

双类型CH08授权/路径/规格/身份/来源/模型/有效期/预算、缺响应、重复接受、输出变化、取消、重启后checkpoint、恶意路径与结构化风险反例；原章节协议/依赖/显示检查回归。所有协议正文保持NOT-AI，不能作为宿主生成验收。

## 非承诺

不认证模型自报来源，不实现OS沙箱，不自动切片删证据，不控制未暴露的远程模型超时或费用，不证明Skill已经连到Connector托管环境。Workbench/WorkBuddy私有安装、实际工具调用及普通用户可获得性仍须真实环境证据。新增Expert资产及集成验证profile不在当前最小候选中；现有prompt-only Expert规则不放宽。
