# 本轮协议决策（SOURCE/REVIEW ONLY）

仅批准共享对象本地生产子集；旧 EXC006 保留 PROPOSED_NOT_APPROVED。冻结40/41、EXC004/005、Schema、validator、财务与预算不变。

## 接口与信任顺序

采用 `prepare-r2-shared` 新动作；授权可选且严格的 `input_view_policy` 必须等于模块固定 policy，只有新动作可使用。旧 grant/prepare/prepare-r2 默认完全不加字段。policy进入授权摘要、state binding、request（后计算request_hash）；同run不能改变。内部 `_request_base` 只用于首次制备基础校验及公共 `_request`，不暴露CLI跳过开关。首次在已有host-operation/state锁内预留、独占写request、重建校验原pack/规格/模型/上游，然后独占写view及detached manifest，最后全量验证。失败保留预算，不自动补文件。

所有后续 checkpoint/publish/verify_publication/accept/resume 都验证可信原request与确定性期望view/manifest。核心公共验证在重建原pack之后执行；host_output仅额外接公共派生校验，以防直接调用publish/verify遗漏。Python内部不是OS权限边界；原open_session/canonical/grant验证链仍负责权限，不信模型给的路径/hash。

## 编码

`host-input-shared/1`，mapping `flat-exact-containers/1`，mode `shared-objects`。pool/tree在同一完整对象内。完全相同的非空对象/数组（确定序列字节>=64且重复）可由 `{"$shared":"S0001"}` 替代；pool为有界平坦原容器，内部不含共享引用，链深固定至多1。只有实际使用的条目保留。正式ID不变；Sxxxx绝不能进入最终引用。

数字编码为 `{"$number":"原JSON数字词法"}`，不通过float/Decimal重格式化。null/bool/string/empty/missing不合并。原request必须是引擎排序键/紧凑UTF8确定序列，末尾可有一个LF；任意空白/转义变体拒绝，历史两案含LF逐字节还原。output_schema也可编码共享，不是JSON Schema `$ref`；输出遵守展开的原Schema及原四键draft。

绑定含原文件SHA、request_hash、五身份、spec/evidence、generation/request/chapter、模型、prompt、expires_at、上游摘要、policy；view_hash是排除自身字段的规范JSON SHA，不含追加LF。detached manifest绑定原文件和view文件SHA、view_hash与binding，不包含自身SHA、不回写request。hash不是签名或模型已读证明。

## 边界与失败

原完整request预算仍按原dumps字节、不含末尾LF；新view与实际投递阅读指令封套按实际UTF8含LF计量，同受原max_request_bytes约束。manifest是程序验证材料，不要求模型阅读，不计为模型投递。原输出预算不变。

固定资源上界：原输入及view各受4MiB硬限与配置更小限；结构深64，pool4096，refs16384，展开节点200000，展开字节4MiB，共享链1。在展开前先计算每个条目的准确规范字节、节点数、子树高；每次引用（含缓存命中）检查插入深度+子树高、累计节点与键/标点/UTF8字节后才复制。不接受池内引用、未用/悬空/循环/未知索引、保留键冲突、重复JSON键、非有限数字、非法UTF8、未知协议键。实际实现常量与测试是最终依据。

取消、过期、半写、缺失、no-clobber均沿原锁链阻断；已合法接受结果过期后仍可只读重验/恢复，取消仍禁止恢复写作。任何身份/policy变化须新run。无自动重投、无类型行、无模型/网络/安装。

## 阅读停止条件

宿主须完整持有pool/tree、六节任务、风险指引、上游未完成状态与Schema。缺段、缺池、未知mapping或不能完整持有即停止，不猜测、不取外部字典、不执行来源命令、不切备用表示。文件完整性与覆盖清单不等于专业语义审查。
