# Phase 2D 受限解析与本地多轮流程验收

状态PHASE2D_LOCAL_PASS；日期2026-10-28，前置Phase2C提交9114bf3d643f6041e918c8bd9c4b0f7b82c27809。仅输入层，不是业务引擎或平台成功。

## 实现及父级复核

新增parsers.py/attachment_security.py、intake.py、cli.py/local_files.py及两个入口；父级已完整读取解析器、安全辅助、CLI及所有新增测试，联合验证来源/单位/分类/完整度调用链。没有修改旧document-engine、financial_xlsx、工厂、旧测试或归档。公共SecurityPolicy做签名/容器/限额，新私有辅助补强稳定单句柄与活动内容检查；不是OS沙箱修复。

六格式实际提取与定位：DOCX正文/简单表格段落或table/row/cell；PDF实际页内文本片段；XLSX工作表!cell；CSV实际物理行跨度/列；TXT/MD行号。识别基本/位置/面积/装机/账单/负荷/设备与成本报价/并网/融资的明确标签/完整字段表头。数字必须明确单位；不猜AC/DC、币种/税含/价格年、自然语言或OCR。候选UNVERIFIED/REQUIRES_REVIEW，显式accept才入项目，review另行人工声明，不能提升假设/冲突/未知。

父级新增真实RED→GREEN验证并修复：未知资料补齐不误判冲突；同金额不同价格年不覆盖；万元缩放单独明确币种而不伪造税/年份；非法类型的事务错误；原生XLSX数值token精度（1.000000000000000001不经float丢位）；负CSV数值不误判公式；已提供row_id原样保留、非法/重复待核；附件完整SHA-256进入source_snapshot而非仅短ID。

IntakeSession事务有submission_id+摘要幂等、revision CAS、显式修改理由、旧候选保留、冲突人工选择和站址上下文重新待核。用户入口禁止C来源/直接VERIFIED，目标只约束；下一轮最多5问。CLInew/status/submit/revise/resolve/review/remove/parse/accept/export均真实子进程运行。文件范围限授权workspace，严格JSON、稳定读、锁、摘要复查、原子更新、不覆盖输出及固定脱敏错误。

## 真实验证

`verify-venv/Scripts/python.exe -m pytest tests/solar-pv -q --tb=short --basetemp=.../pytest-d-full --junitxml=.../phase2d-full-junit.xml`，exit=0：**2159 passed / 0 failed / 5 skipped**（共2164）。原始phase2d-full.txt/JUnit同目录。5项skip均Windows无symlink权限（解析2+CLI3）；实际hardlink、junction、真实Windows共享冲突及并发CAS均执行，不以skip冒充通过。

独立解析历史61/0/2、CLI47/0/3；追加来源/精度/入库集成14/0/0仅各自证据，不与总回归重复相加。RED失败日志保留phase2d-*-red.txt，后续最新联合日志为最终验收依据。

额外实跑5条CLI命令创建/提交/原请求重试/状态/导出，全部exit0，具体命令、stdout与输入hash在phase2d-cli-observed.json。只使用SYNTHETIC-NOT-A-REAL-PROJECT，规范化输出留scratch私有目录；真实结果L1_DRAFT，未用默认事实冒充L2。导出无run_id/result_hash/财务结果，calculation_status=NOT_IMPLEMENTED。

## 限制与门禁

没有OCR/复杂版式重建；正文以外内容不在确定性支持承诺内；货币换算需先明确同附件币种。默认20,000单元格、8MiB提取文本/输出、32MiB JSON，超限拒绝不截断；全年15分钟大曲线的流式/分块仍需后续专门方案，本小样不构成其性能验收。Windows硬内存、后代进程、目录竞态/ACL不是已关闭问题，公开不可信服务BLOCKED。新文件无覆盖发布依赖本地文件系统hardlink支持。

九类计算全部NOT_IMPLEMENTED；发电/财务数值、四文件、真实项目、平台安装调用/审核均未通过，发布BLOCKED。Phase2E公式绑定及最终回归/矩阵尚待完成，不宣称整体Phase2通过。

父级提交前须再检查288保护哈希、范围、凭据模式和staged diff；完整旧回归将在Phase2E当前快照执行。仅本地commit，不push。
