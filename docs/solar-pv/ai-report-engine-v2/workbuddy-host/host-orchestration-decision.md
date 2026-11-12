# 原生宿主编排裁定与执行计划（H1）

版本保持 SOLAR-PV-AI-REPORT-ENGINE-2.0.0；冻结规格/公式/canonical不变。基线与官方依据见workbuddy-platform-compatibility.md。

## 路线

复用现有Skill作为研究流程真源，增加受控宿主会话入口，不新建Python模型SDK或第二个计算器。原report/ground-report保留且标明legacy；AI路径停在待审局部Word，不接正式四文件。

```text
用户授权项目/目录/来源及当前WorkBuddy宿主处理
  → Expert/Skill调用原确定性计算链取得合法canonical
  → 受控宿主入口prepare（复用Registry/build_pack/chapter_writer）
  → 当前WorkBuddy宿主Read新request，独立研究并Write新response
  → 记录实际可见provenance；未暴露项用NOT_EXPOSED_BY_HOST
  → accept（原fact/claim检查 + 结构化高风险断言约束）
  → checkpoint/resume重验身份、来源、配置、上游与输出
  → 原assemble_chapter生成局部待审Word
```

宿主模型研究这一步不是Python调用，不能由脚本从authored/旧Word/历史draft补齐。程序只形成研究任务、校验输出及装配。

## 最小实施清单

1. 在现有reporting边界新增宿主会话适配入口，复用Workspace和核心prepare/accept/resume，不改旧入口行为。显式授权文件绑定canonical字节摘要、类型、来源白名单和当前宿主处理同意；只允许授权目录内文件。
2. 宿主来源单独保存，绑定request/output/model；区分WORKBUDDY_HOST声明、USER_SUPPLIED及PROTOCOL_REPLAY。不生成“服务端call_id”；未知统一明确标识。所有类别都不自动产生独立认证PASS。
3. 增加有界checkpoint、同一输出幂等接受及取消标记；已接受结果只重验，变化拒绝。命令硬超时与宿主模型超时分开；取消仅停止本地继续处理，不声称远程模型已被杀死。
4. 新宿主入口本轮只开放CH08；CH10/CH16在双案真实宿主CH08通过前不启用。过长上下文拒绝而不截掉关键证据；安全切片与宿主上限未验证时保持阻断，不编造已实现。
5. 复用Skill，增加原生研究和恢复指引及安装态入口脚本；不内置完整段落。若尚不能提供合规安装Expert候选，则将Agent角色作为明确的本地集成材料，不能宣称已安装Expert。
6. 修Connector缺失unAuth，无凭据场景明确无凭据可撤销；不创建假登录令牌。增强就绪检查以识别实际AI入口，不将仅导入旧包当AI2.0就绪。未批准索引时不执行真实安装。
7. 在原claim协议增加可选结构化风险断言校验，不改变已有必需字段。将残值/处置现金、应计/付款、预测/实收、项目/股东、DSCR无定义、UNKNOWN/零明确隔离；自由文本仍PROFESSIONAL_REVIEW_REQUIRED，绝不以机器检查升级专业状态。
8. 用户已明确授权专项测试：覆盖两案CH08无响应、协议fixture、身份/来源/规格/配置/超时/预算/路径/恢复/幂等/取消/高风险反例。fixture永不当新AI样稿。
9. 在隔离构建目录生成本地候选，验证wheel内容及独立运行；不改全局安装、不覆盖旧dist、不发布。普通安装者依赖分发仍独立BLOCKED。

## 阶段与STOP

- H0：实际Git/官方规则/安装与分发检查。已知客户端5.5.2、PyPI两版本404、平台资产安装未验证。允许本地候选，不授权平台安装。
- H1：本裁定及V2-EXC-004记录后进入本地实现；不改冻结需求正文。
- H2：仅列出的代码/指引/合同与测试。若必须新厂商API、企业托管账号、付费服务或更改计算方法，立即停止。
- H3第一层：双案CH08本地合同/负向测试，可独立执行；第二层：只有实际授权已安装专家/技能/连接器环境才能试验。当前不能用Hermes或fixture替代，未通过不进CH10/16。
- H4：独立QA须披露worker身份；没有真正wb-quality环境则INDEPENDENT_QA_NOT_RUN，隔离同模型审查只是补充。按真实门禁交付恢复包和本地提交，不进入Phase E。

## 不变与未承诺

不改89公式、财务算法/边界、canonical、原Word整体设计、原PDF引擎；不生成新候选经济排名。保留全部历史审阅资产和旧dist。没有OS级沙箱或可核验服务端模型身份时必须如实报告。Skill/Expert提示词约束不是主机级防读保证。

最终要证明的是普通用户在实际宿主中无旧稿研究，不是本地测试数量。未取得该证据就继续MODEL_INTEGRATION_BLOCKED。
