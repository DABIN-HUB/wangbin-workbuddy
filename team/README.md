# 星核实验室 · WorkBuddy Skill / Expert 产品研发团队

Board: `wb-skill-factory`；四个永久 Profile：`wb-manager`、`wb-analyst`、`wb-developer`、`wb-quality`。统一执行规范只有仓库根 [`agent.md`](../agent.md)；本目录只说明角色和流程，不复制产品规则。Skill 工厂以 `python -m tooling.products` 和 `docs/product-factory.md` 为权威；Expert 先核对当前 WorkBuddy 官方规范、`tooling/expert_rules.py` 与现有 `packages/experts/wangbin-software-consultant/`，不得把固定产品的 `tooling/phase5_expert_packager.py` 当通用打包器。

经理只接用户明确指定的产品目标；先核现有看板及唯一正式目录，再按 `product_type = Skill | Expert` 建带产品 ID、固定路径、幂等键和 T00→T05 依赖的卡。Skill 与 Expert 使用不同的构建及独立 QA 合同，详见 [`workflows/skill-development.md`](workflows/skill-development.md)。Manager 的阶段 Checkpoint 写入现有交付目录，依 [`workflows/task-handoff.md`](workflows/task-handoff.md) 进行分阶段新会话交接；Checkpoint 是索引，实时 Kanban/Git 才是事实。当前初始化状态见 `reports/initialization.md`，未验证的自动唤醒或自动交接不得宣称通过。WorkBuddy 平台上传、安装、审核与发布由用户另行负责。
