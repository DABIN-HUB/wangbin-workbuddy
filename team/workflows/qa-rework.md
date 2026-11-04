# 独立 QA 返工
T02 正常 complete，不对同卡 request-review；T03 独立 QA。失败时记录输入、预期、实际、复现命令及任务 ID，kanban_block T03，通知经理。经理以 `产品ID:fix:轮次` 幂等键创建 wb-developer 修复卡，指定目录与验收条件；修复真实运行专项验证并本地 commit。经理检查提交与证据后才 unblock T03；QA 重跑，最多两轮。通知能否主动唤醒经理必须通过真实事件联调核验，不能以“订阅成功”代替。两轮仍失败保持 BLOCKED。
