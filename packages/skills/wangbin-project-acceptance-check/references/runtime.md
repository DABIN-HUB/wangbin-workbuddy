# 运行协议（本地开发候选，WorkBuddy 未实测）

运行时：Python 3.11+；需 `python-docx==1.2.0` 与 `openpyxl>=3.1,<4`。本地隔离运行可用 `uv run --no-project --with python-docx==1.2.0 --with 'openpyxl>=3.1,<4' python scripts/check_acceptance.py --help`（在解压 Skill 目录）；平台是否预装这些包 `NOT_TESTED`。不联网、不运行输入文件代码。根目录与输出目录均由有权用户提供；输出目录必须已存在且位于授权根目录下。参数：`--project-name`、`--authorized-input-root`、`--output-dir`，每份附件明确角色用重复 `--scope-source` / `--delivery-source` / `--evidence-source` / `--change-source`，相对授权根目录；`--effective-version-ref` 为现有授权文件**相对路径**，不是自由声称；增量传 `--previous-snapshot`（同根下的旧快照相对路径）。在没有快照时不能回答“哪些缺口已经补上”，不能推断旧结果。

示例：`python scripts/check_acceptance.py --project-name 星桥演示平台 --authorized-input-root ./authorized --output-dir ./authorized/out --scope-source scope.md --delivery-source interface.md --delivery-source deploy.md --effective-version-ref scope.md`。注意 scope.md 只是本地虚构范围来源；实际项目应验证生效依据，未经证实不能把覆盖率解释为正式验收率。输出目录中依次生成 `星桥演示平台-验收资料核对.xlsx`、`星桥演示平台-验收准备报告.docx`、`星桥演示平台-核查快照.json`；已有同名文件不覆盖。返回 0 完整、3 局部读取失败、2 输入或格式失败、4 输出失败；终端输出摘要，不含输入文档全文。

上限（拒绝而不是截断）：每份原件 4,000,000 字节；至多 40 个显式文件；清单至多 2,000 数据行；每份 OOXML 至多 500 个 ZIP 成员及 12,000,000 字节解压总量。TXT/MD/CSV 仅 UTF-8 (BOM 可)，DOCX 普通正文与表格；XLSX 单工作表（公式视为不可靠并拒绝）。不自动展开压缩包、不执行宏、不跟随符号链接、不从内容指定网址抓取。CSV/XLSX 必须带有“要求原文/证据原文/内容/原文/需求/text”等显式列（交付清单允许“名称”），缺少的列标诊断；目录只有名称显示 LISTED_ONLY。正式验收、法律判断、模型对话行为都不能由本地脚本保证。

来源位置：文本物理行号、DOCX 段号/表号行列、表格工作表行列；工具内部 ID 是源标识+定位哈希，快照只用于同项目的显式增量。修改旧文件时先进行人工身份复核；不要把旧快照当签名安全载体，不能输入不可信的旧快照。保守词面判定只针对简单的端点/请求参数/返回字段、部署说明与培训记录；任何更复杂的语义、版本确认和签字必须人工复核，不应把词面命中升为客户确认。
