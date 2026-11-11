# V2-EXC-001：无已验证模型adapter时的宿主交接边界

分类：A类必要技术补充；不变更冻结计算、项目类型、正式公式、PDF或四文件合同。

## 缺口与阻断

现有Skill/Connector负责脚本与运行环境，不提供本产品已验证的逐章模型接口。仓库没有授权provider配置或可核验调用回执。当前Hermes能对话，不等于未来安装的Python引擎能调用同一模型；不能复用会话凭据或伪造provider。

## 最小接口

`python -m wangbin_solar_pv.reporting prepare`输出绑定规格、canonical、来源授权和期限的request；授权宿主读取其中的章节任务与最小证据后返回JSON；`accept`校验并独立存储，`resume`重建证据验证缓存；可用`--docx`生成局部待审稿。模型、思考等级、请求/输出字节、期限、重试次数及总请求数可配置。

**此协议不是自动模型适配器，也不伪装为已成功调用。** 当前CLI `status`退出码3，状态 `MODEL_INTEGRATION_BLOCKED`。接受宿主声明的model_id/call_id不能证明实际供应商执行，结果保留 `HOST_DECLARED_NOT_INDEPENDENTLY_VERIFIED`。期限控制的是本地请求接受时间；没有宿主就不存在可声称已经强制的远程超时或token费用控制。

生产接入仍需：用户批准的正式宿主方式、模型可用性及身份回执、资料授权、远程超时/上下文/token或费用上限、有限重试、真实双类型试点调用。若接入方式构成用户定义的B类变化，先请用户批准，不自行切换供应商。

## 稳定事实引用补充

正文数字采用 `[[fact:<程序提供的fact_id>]]`；程序绑定原值与受控显示，禁止裸阿拉伯数字及未分配引用。所有正文字段统一验证。Schema增加 `fact_refs/source_refs`，不改变用户原有必需字段。中文数字、否定、因果及审批结论仍需独立专业审核，不将引用合法冒充全文事实成立。

Phase B只消费可校验标量、计算指标及有限数值数组。数组按原序列位置展开，不伪造日历年度；未经typed adapter处理的嵌套来源明确 `STRUCTURED_SOURCE_REQUIRES_TYPED_ADAPTER`，不是用户没提供资料。图表授权集合为空，不能引用虚构图表。上述限制是当前实现未闭合能力，**不缩减Phase C—F的冻结要求**。

## 新增验收及实际结果

- 两类canonical先通过既有validate_result；原文件与五项身份不变。
- 未授权来源不进入事实包；未知/不可用不补零；负值保留。
- 错章节、非法schema、跨范围引用、裸数字、XML、伪来源均拒绝。
- 更换配置/证据、过期、预算耗尽、输出篡改拒绝，失败独立记录；成功不覆盖。
- 双类型实际CLI prepare→accept→resume→DOCX已运行，使用显式 `PROTOCOL_FIXTURE_NOT_LLM`，仅证明本地接口和Word装配。每案六小节、四表、十二个可编辑数学对象；未渲染PDF。
- 不存在真实AI正文样本，`LLM_INTEGRATION_VERIFIED`、`PILOT_CONTENT_REVIEWED`均未通过。

对应源码：`reporting/llm_provider.py`、`chapter_writer.py`、`chapter_result_schema.py`、`claim_validator.py`、`__main__.py`。测试与回执见本目录 `phase-ab-delivery.md`，不修改Phase A冻结文件和哈希。
