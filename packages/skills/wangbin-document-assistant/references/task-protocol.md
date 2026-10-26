# wangbin 文档助手任务协议

## parse

输入一个用户明确授权的文件路径。允许扩展名：`.pdf`、`.docx`、`.xlsx`、`.pptx`、`.html`、`.htm`、`.txt`、`.md`、`.markdown`。返回 JSON：

```json
{
  "source_name": "材料.pdf",
  "source_type": "pdf",
  "status": "success",
  "size_bytes": 1234,
  "text": "真实提取文本",
  "metadata": {},
  "sections": [],
  "quality_notes": [],
  "error": null,
  "duration_ms": 20
}
```

## batch

输入文件列表和同一个授权输入根目录。每个文件独立处理；返回 `success`、`failed` 或 `partial_failure`，并保留每个文件的 `error.code` 和脱敏 `error.message`。

## deduplicate

只接受 XLSX。读取第一个工作表的表头和数据，以用户指定列或整行作为去重键，写入输出根目录下的新 XLSX/CSV。输出文件重新打开验证后才能报告成功，公式样式字符串会按文本处理，不执行公式。

## summary input

先完成 parse/batch，再将真实文本和元数据交给后续模型。模型输出必须标记推断，不得把缺失信息补写为原文事实。

## 失败码

`FILE_NOT_FOUND`、`PATH_OUTSIDE_ROOT`、`SYMLINK_INPUT`、`FILE_TOO_LARGE`、`TOO_MANY_FILES`、`BATCH_TOO_LARGE`、`MISMATCHED_EXTENSION`、`CORRUPT_CONTAINER`、`UNSUPPORTED_FORMAT`、`PARSER_ERROR`、`TIMEOUT` 和 `EXPORT_ERROR`。
