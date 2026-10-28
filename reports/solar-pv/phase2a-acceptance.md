# Phase 2A 输入契约与Schema验收

日期2026-10-28。起点main/b475c5e5b3d107625acb8e531a623d142060a194，工作区初始干净，保护288文件均未变。任务原文及其哈希已在13-phase2-user-task.md / task-manifest归档，未改写Phase1目录。

- 真实读取所有用户指定冻结文档/JSON/CSV及现有document-engine、financial_xlsx、factory、validators。实际469字段/89公式/281域绑定/九分类与上轮一致；没有结构差异需要覆盖。
- 新增独立包services/solar-pv-engine；Catalog从12份锁定文件读定义，使用LF规范化SHA-256防漂移。metadata包含15项字段契约、技术标识与公式交叉引用。所有计算仍NOT_IMPLEMENTED。
- 完整运行时JSON Schema在services/solar-pv-engine/schemas/project-input.schema.json，支持全部469字段，22对象数组和1嵌套标量数组，逐原子信封、可空未知、禁止额外属性与类型隐式强转。
- ProjectData及严格JSON序列化可运行：Decimal保持原数值精度，拒绝重复JSON键、NaN/Infinity、超大/过深输入、未来版本和目录哈希不符。
- RED：pytest tests/solar-pv/test_catalog_schema.py，11 failed，原因均为未实现包；GREEN：相同11项，11 passed / 0 failed / 0 skipped，JUnit留存。并非19209项文档检查替代功能测试。
- 既有回归在scratch快照真实执行：tests + packages/experts/wangbin-software-consultant/tests，145 passed / 0 failed / 5 skipped（Windows符号链接能力未开放）。未修改旧测试。
- 解释器：scratch/solar-pv-phase2-20261028/verify-venv/Scripts/python.exe，Python3.12.0；依赖在隔离环境安装，指定官方PyPI index及已哈希保护的历史CLI wheel。没有改用户现有venv。
- 本阶段不声称来源语义、归一化、成熟度或解析完成；这些按2B—2E执行。六类产品门禁、四文件、光伏/财务数值与平台仍未通过。

提交前按实际执行git diff --check、增量文本凭据模式扫描、288保护哈希复算、只暂存本阶段新增路径。提交SHA以git log -- reports/solar-pv/phase2a-acceptance.md读回，不预写自引用SHA。默认不push。
