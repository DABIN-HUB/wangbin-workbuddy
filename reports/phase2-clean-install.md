# Phase 2 干净环境验收

- 状态：PASS；PASS 28 / FAIL 0 / SKIP 1
- 实际环境：Windows Python 3.12，scratch 新建 venv；不使用开发机的 WANGBIN_ENGINE_SRC/PYTHONPATH。
- 安装：`python -m pip install --no-input --only-binary=:all: --no-cache-dir dist/wangbin_document_cli-1.1.0-py3-none-any.whl`；`python -m pip check`。
- SKIP 不计为 PASS；平台 WorkBuddy 安装/运行与 macOS/Linux 运行均未验证。

| 用例 | 状态 | 实际退出码/错误码 |
|---|---|---|
| C01_version | PASS | 0  |
| C02_doctor | PASS | 0  |
| C03_status | PASS | 0  |
| C04_auth_no_account | PASS | 0  |
| C05_logout_no_delete | PASS | 0  |
| C06_pdf | PASS | 0  |
| C06_docx | PASS | 0  |
| C06_xlsx | PASS | 0  |
| C06_pptx | PASS | 0  |
| C06_html | PASS | 0  |
| C06_txt | PASS | 0  |
| C06_markdown | PASS | 0  |
| C07_batch_partial | PASS | 1  |
| C08_dedup_xlsx | PASS | 0  |
| C08_dedup_csv | PASS | 0  |
| C09_corrupt_pdf | PASS | 1 CORRUPT_DOCUMENT |
| C10_wrong_extension | PASS | 1 MISMATCHED_EXTENSION |
| C11_missing_file | PASS | 1 FILE_NOT_FOUND |
| C11_missing_root | PASS | 1 INPUT_ROOT_MISSING |
| C12_outside_root | PASS | 1 PATH_OUTSIDE_ROOT |
| C13_output_inside_input | PASS | 1 OUTPUT_EQUALS_INPUT_ROOT |
| C13_output_file_rejected | PASS | 1 OUTPUT_PATH_INVALID |
| C14_oversize | PASS | 1 FILE_TOO_LARGE |
| C15_windows_junction | PASS | 1 SYMLINK_INPUT |
| C16_windows_symlink | SKIP |   |
| C17_missing_dependencies | PASS | 78 ENGINE_RUNTIME_MISSING |
| C17_parse_missing_dependencies | PASS | 78 ENGINE_RUNTIME_MISSING |
| C18_platform_metadata_and_skill_commands | PASS |   |
| C19_isolated_install_paths | PASS |   |

完整命令、输出状态和结果文件 SHA-256 见 `reports/phase2-clean-install.json`。未保存用户文档正文。
