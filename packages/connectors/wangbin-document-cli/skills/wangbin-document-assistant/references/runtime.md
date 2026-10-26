# 本地运行协议

- `version`：报告 CLI 版本；`doctor`：只读检查已安装 Python 依赖；`status`：只读检查并在健康时输出 `LOCAL_READY`。
- `auth`：本产品不要求外部账号，不创建/存储认证资料；`logout`：无外部会话可撤销，不删除输入或输出文件。
- `parse --input <路径> --input-root <目录> [--output-root <目录>]`：单文件 JSON 结果。
- `batch --files <路径1> <路径2> ... --input-root <目录> [--output-root <目录>]`：逐文件 JSON 状态及成功/失败数量。
- `deduplicate --input <xlsx路径> --input-root <目录> --output-root <不同目录> [--format xlsx|csv]`：写入新文件，输出 `output_path` 及去重计数。
- 输入文件名可有中文或空格；每个路径作为单独参数并正确引用。结果可能包含用户文档正文，应只返回给授权用户，不写入公开日志。
- `ENGINE_RUNTIME_MISSING`：依赖缺失或版本不符；需在受控环境重新安装 CLI，不能在解析请求中自动联网安装。
- `FILE_NOT_FOUND`、`INPUT_ROOT_MISSING`、`PATH_OUTSIDE_ROOT`、`SYMLINK_INPUT`、`OUTPUT_EQUALS_INPUT_ROOT`、`OUTPUT_PATH_INVALID`、`OUTPUT_PERMISSION_DENIED`、`FILE_TOO_LARGE`、`MISMATCHED_EXTENSION`、`CORRUPT_DOCUMENT`：请用户更正授权文件、目录、权限或格式；不绕过安全限制。
- 退出码 0 只用于完整成功/已处理但文本为空的成功告警，1 用于文件级或批次部分失败，78 用于运行环境缺失。
- 错误信息不含完整系统异常和凭证；解析质量和原文真实性仍需人工复核。
