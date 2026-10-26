# 发布指南（人工操作）

## 当前状态

本项目只生成本地发布候选 ZIP，未登录 WorkBuddy、未上传、未提交审核、未设置售价、未发布上线。`PUBLISH_READY` 在平台运行时和主体资格未确认前保持 `BLOCKED`。

## 上传前本地检查

1. 完成个人或企业主体认证，并确认开发者资料、头像、昵称、简介和联系方式符合官方规则。
2. 执行：

   ```bash
   .venv/Scripts/python.exe -m tooling release-check
   ```

3. 核对 `reports/acceptance-report.md`、`reports/release-check.md`、`dist/wangbin-document-assistant-1.0.0-candidate.zip`、SHA-256 和包内文件清单。
4. 确认产品描述、依赖、运行条件、权限和数据用途与上传版本一致。

## WorkBuddy Skill 操作步骤

根据官方 Skill 页面进入开放平台，创建 Skill 并上传候选 ZIP。官方文档明确 Skill 根资源需要 `SKILL.md`，并支持 `references/`、`scripts/`、`templates/`。平台没有明确本次 ZIP 额外包裹层级，因此上传前应先确认页面解析结果；若解析失败，保存平台错误并对照 `docs/workbuddy-platform-spec.md`，不要用额外文件或猜测字段掩盖问题。

上传后人工验证：安装 Skill、在对话中选择真实七类文档，检查成功/失败/部分失败输出。平台安装验证和实际功能验证必须单独记录，不能由本地 pytest 代替。

## 收费

本轮保持免费，不进入收入变现，不签署微信结算，不设置一次性或按月价格。官方变现页面说明付费 Skill/Expert 需要入驻审核和签约，后续如启用需重新审核文案、交付内容和额外费用。

## 手动门禁

- 账号认证：`BLOCKED`，需要本人提供身份证、实名手机号、邮箱和人脸识别。
- 平台上传：`NOT_TESTED`，需要人工登录和点击上传。
- 平台安装/调用：`NOT_TESTED`，需要人工登录和真实文件。
- 平台审核：`BLOCKED`，只能由 WorkBuddy 平台审核决定。
