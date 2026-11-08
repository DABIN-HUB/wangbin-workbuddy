# Q03 冻结用例预期 — 安全重建副本

所有内容为虚构合同；两份明确 original → returned 的独立 DOCX 在每案新建。下表是冻结 **expected**，并非新导出版本的 actual。原开发测试仅覆盖其明示子集，新合成脚本仅生成有限例；未逐案复测的 actual=`NOT_TESTED`。按实际 CLI JSON 状态、真实四表 XLSX/可编辑 DOCX 回读、双侧源 SHA 前后、结果 change_id/type/topic/定位、命令退出码记录 actual；失败不修改预期。不得沿用旧独立 QA 统计。

| ID | 虚构原稿 → 回传稿 / 操作 | 冻结预期 | 新完整验收 actual |
|---|---|---|---|
| CORE / CON-01/03/05 | `第六条，验收后30天付款，金额100000元。` → `第七条，验收后60天付款，金额100000元。` | COMPLETE；付款 MODIFY 恰 1（延长30天），NUMBER 恰 1；金额不变；确认 ID 恰 2；无额外增删、损失/法律推断；四表与 DOCX 的 ID/双侧逐字原文和位置一致 | NOT_TESTED |
| CON-01 | 核心另加 `不含税`→`含税` 与 `应于2026-12-01前`→`应于2027-01-01前` | 保留否定、金额/日期，不能归一化遗漏 | NOT_TESTED |
| CON-02/A04 | `服务期12个月。` 从首段移至末段，中间其他段保持不变 | 仅 MOVE 1，两侧位置正确，不产生该段增删改 | NOT_TESTED |
| CON-03/A05 | `第六条 质保一年。`→`第七条 质保一年。` | 只 NUMBER 1，无实质/金额变更 | NOT_TESTED |
| CON-04/A06 | 普通表格同唯一键 `SKU-X`，单价10元/付款比例30%→单价12元/付款比例40% | 单价与比例两条确定 MODIFY，含表号/行/列，无 NUMBER | NOT_TESTED |
| CON-04/06/A07 | 两组重复的付款条件各有近似候选；另有唯一 `交付7天`→`交付9天` | PARTIAL，付款竞争候选逐一保留定位与双侧原文、不强配对；独立确定交付变化仍可交付，不算候选 | NOT_TESTED |
| CON-07 | `付款30天。交付到A地。`→`付款60天。交付到B地。`，只筛选付款 | 明细仅付款，另说明未显示交付；全量/筛后分别计数 | NOT_TESTED |
| CON-08/A12 | 核心启用 draft_message；歧义无确定差异时也尝试草稿 | 只引用已证实 ID/原文的礼貌问题，不代为接受/自动发送；纯歧义不得写成确定修改 | NOT_TESTED |
| A02 | 两独立文件同 `交付后10天验收。`，同普通表格 `项目A / 100元` | COMPLETE、确认 0、四表真实存在、差异无记录、DOCX 表述已检查范围无变化 | NOT_TESTED |
| A03 | `交付到A地。` 不变，回传追加 `验收7日内书面反馈。`；另案删去 `附录培训一次。` | 分别仅 ADD 1 / DELETE 1；不存在一侧明示 N/A，不补数值 0 | NOT_TESTED |
| A08 | 对调 A03 的文件角色；另对调核心 30/60 角色 | ADD→DELETE 且定位反转；核心 60→30 缩短30天，NUMBER 七→六，金额不变 | NOT_TESTED |
| A09 | `可以延期，价格含税。`→`必须延期，价格不含税。` | 义务词与否定均保留，不降为普通润色 | NOT_TESTED |
| A10 | original 含 Word 未接受插入/删除 OOXML，returned 正常 | NEEDS_INPUT: REVISION_STATE，停止完整结论，要求已接受修订副本 | NOT_TESTED |
| A11 | 文字段相同，但一侧含文本框 `付款90天` 或图片条款 | PARTIAL，列载体和位置/影响；不对图片 OCR，不报整份无变化 | NOT_TESTED |
| A13 | 成功及错误案均量取两源 SHA | 前后字节哈希相同，ERROR 不改源 | NOT_TESTED |
| A14 | 核心再加一个确定 ADD，重开成果 | 确定 ID 3：MODIFY/NUMBER/ADD 各 1，概览/两输出交叉引用唯一 ID，不重复付款 | NOT_TESTED |
| E01 | 两 DOCX 未明示角色，或对话/参数冲突 | NEEDS_INPUT: ROLE_AMBIGUOUS，先追问不猜方向 | NOT_TESTED |
| E02 | 假 DOCX/损坏 ZIP/旧 DOC/加密包 | ERROR: INVALID_DOCX，不生成空白成功成果 | NOT_TESTED |
| E03 | 单份 >10 MiB / >2000 单元 / >100000 字或 ZIP 穿越/炸弹/XML 外部实体 | ERROR: LIMIT_EXCEEDED 或 INVALID_DOCX，无截断成功/路径外写出 | NOT_TESTED |
| E04 | 源 `-100元`、`=1+1`、`@SUM(A1)` 或空白/控制字符前缀 | XLSX 重开为文字单元且原意不变，无公式执行 | NOT_TESTED |
| E05 | 输出不可写/与现有成果或源路径冲突 | ERROR: IO_FAILURE 或唯一安全新名，不覆盖，原哈希不变 | NOT_TESTED |
| F01-N1/N2 | 单句 `双方不得泄露商业秘密。`→`发生地震时由双方协商履行。`；再加相同前后锚点 | 两侧原文/位置保留，不判确定 MODIFY；候选 PARTIAL 或有独立单边证据才可增删；候选不入草稿 | NOT_TESTED |
| F01-P1/P2/B1/A1 | 核心正/反、纯移动、重复付款与明确交付并存 | 方向性 30↔60、NUMBER、MOVE 与歧义分离，不能把正常情况全部降级 | NOT_TESTED |
| F01-B2/P3 | 两边同号第八条但保密→地震，另有唯一付款锚；单独新增验收句/删去附录 | 同号不能确定 MODIFY；付款锚可确定；独立 ADD/DELETE 不一律 PENDING | NOT_TESTED |
| F02-P1/N1/N2/N3 | 普通无链接授权路径 / 输入文件 symlink / 输入父目录 symlink / 输出 symlink | 正向两成果；链接均 ERROR: UNSAFE_PATH 且目标原样。若 Windows 无 symlink 权限如实 NOT_TESTED | NOT_TESTED |
| F02-N4/N5/B1 | 输入父目录真实 Windows junction / 输出目录 junction / 新建目录与替换竞态 | junction 均 ERROR: UNSAFE_PATH，目标不读写；无替换正常创建，无法可靠防竞态失败关闭 | NOT_TESTED |
| F02-B2 | 同一文件、坏 DOCX、缺角色、限额上下边界、不可写目录 | 各对应 ROLE_AMBIGUOUS/INVALID_DOCX/LIMIT_EXCEEDED/IO_FAILURE，普通可控输入不被一律拒绝 | NOT_TESTED |
| C01 | 以双语三句推荐问法依序起问/筛选/草稿，缺上下文另试 | 同一来源角色及确定 ID 贯通；缺信息 NEEDS_INPUT，不产生虚构发送 | NOT_TESTED |

从新安全包干净解压的真实 CLI、真实输入 SHA 前后、XLSX 四表和说明 DOCX 回读属于独立 QA 范围；本地开发者测试不等于宿主/平台验收。新虚构生成仅复现已明确的合同词句，不使用历史 DOCX、原有 QA JSON 或旧评测草案。
