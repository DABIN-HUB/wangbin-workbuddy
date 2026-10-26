"""Freeze truthful Phase 2 local and platform release gates."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

PHASE1_SHA256 = "12544dbd203c3bed5cf6f0094ffc752b17d3fcc852377a6ff09113cb31b5c5b3"
GATE_NAMES = (
    "DOCUMENT_ENGINE_PASS", "CLEAN_INSTALL_PASS", "CLI_RUNTIME_PASS",
    "SKILL_INTEGRATION_PASS", "SECURITY_PASS", "PACKAGE_VALIDATION_PASS",
    "WORKBUDDY_INSTALL_PASS", "WORKBUDDY_E2E_PASS", "PUBLISH_READY",
)


def _hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate(root: Path) -> dict[str, object]:
    root = root.resolve()
    test = json.loads((root / "reports/phase2-clean-install.json").read_text(encoding="utf-8"))
    package = json.loads((root / "dist/wangbin-document-cli-1.1.0-candidate-manifest.json").read_text(encoding="utf-8"))
    expected = test["counts"]
    if sum(expected.values()) != len(test["cases"]):
        raise ValueError("case total disagrees with reported counts")
    if any(expected[key] != sum(item["status"] == key for item in test["cases"]) for key in ("PASS", "FAIL", "SKIP")):
        raise ValueError("case count disagrees with individual results")
    for artifact in [package["wheel"], *package["archives"].values()]:
        path = Path(artifact["path"])
        if not path.is_file() or _hash(path) != artifact["sha256"] or path.stat().st_size != artifact["size_bytes"]:
            raise ValueError(f"current artifact differs from manifest: {path}")
        checksum = path.with_name(path.name + ".sha256")
        if not checksum.is_file() or checksum.read_text(encoding="utf-8").strip() != f"{artifact['sha256']}  {path.name}":
            raise ValueError(f"artifact checksum sidecar differs: {checksum}")
    old_zip = root / "dist/wangbin-document-assistant-1.0.0-candidate.zip"
    old_kept = old_zip.is_file() and _hash(old_zip) == PHASE1_SHA256
    checked = {item["id"]: item["status"] for item in test["cases"]}
    local_ok = test["status"] == "PASS" and expected["FAIL"] == 0 and checked["C19_isolated_install_paths"] == "PASS"
    seven_formats = all(checked[f"C06_{fmt}"] == "PASS" for fmt in ("pdf", "docx", "xlsx", "pptx", "html", "txt", "markdown"))
    zip_ok = package["status"] == "PASS" and old_kept
    gates = {
        "DOCUMENT_ENGINE_PASS": "PASS" if local_ok and seven_formats else "FAIL",
        "CLEAN_INSTALL_PASS": "PASS" if local_ok else "FAIL",
        "CLI_RUNTIME_PASS": "PASS" if local_ok and checked["C03_status"] == "PASS" and checked["C17_missing_dependencies"] == "PASS" else "FAIL",
        "SKILL_INTEGRATION_PASS": "BLOCKED" if checked["C18_platform_metadata_and_skill_commands"] == "PASS" else "FAIL",
        "SECURITY_PASS": "BLOCKED" if checked["C15_windows_junction"] == "PASS" and checked["C16_windows_symlink"] in {"PASS", "SKIP"} else "FAIL",
        "PACKAGE_VALIDATION_PASS": "PASS" if zip_ok else "FAIL",
        "WORKBUDDY_INSTALL_PASS": "BLOCKED",
        "WORKBUDDY_E2E_PASS": "BLOCKED",
        "PUBLISH_READY": "BLOCKED",
    }
    if set(gates) != set(GATE_NAMES):
        raise ValueError("gate set missing a required state")
    counts = {status: sum(value == status for value in gates.values()) for status in ("PASS", "FAIL", "BLOCKED", "NOT_TESTED")}
    report = {
        "version": "1.1.0", "scope": "Windows local clean install + WorkBuddy platform pending",
        "gates": gates, "gate_totals": counts, "test_totals": expected,
        "test_report": "reports/phase2-clean-install.json",
        "artifacts": package,
        "phase1_zip_preserved": old_kept,
        "platform_facts": {"pypi_package_query": "HTTP 404 on 2026-10-26 (pypi.org/pypi/wangbin-document-cli/json)", "developer_account": "not accessed", "workbuddy_install": "not executed", "chat_e2e": "not executed", "submission": "not executed"},
        "limits": [
            "C16 Windows symlink creation denied by current OS token; C15 real junction rejection passed.",
            "SecurityPolicy timeout is checked after conversion, not a hard parser kill; adversarial memory/TOCTOU limits remain unproven.",
            "Skill-to-CLI use in WorkBuddy is not tested; local Skill command and metadata checks do not replace it.",
            "The Python CLI wheel is only local; package index and macOS/Linux runtime are not tested.",
            "Third-party installed license metadata is inventoried, but detailed redistribution legal review is pending.",
            "Generic conversion T15 remains SKIP; no OCR or model summary is claimed."
        ],
    }
    (root / "reports/phase2-acceptance.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = ["# Phase 2 验收报告（本地候选，未平台发布）", "", "- 版本：1.1.0；路线：Python CLI Connector + 配套 Skill；独立 Skill 不含引擎。", f"- 干净环境真实用例：PASS {expected['PASS']} / FAIL {expected['FAIL']} / SKIP {expected['SKIP']}；Windows 3.12 本地 wheel + 从 PyPI 下载依赖。", "- Python CLI 入口、`doctor`/`status`、七种格式解析、批处理、Excel 去重 XLSX/CSV 重读、路径与损坏文件失败、Windows junction 均在隔离 venv 实际执行；符号链接创建权限不足，保持 SKIP。", "- 原 Phase 1 ZIP 校验：" + ("原始 SHA-256 保持不变" if old_kept else "与原始 SHA-256 不一致"), "", "## 门禁", "", "| 门禁 | 状态 |", "|---|---|"]
    for name, status in gates.items():
        lines.append(f"| `{name}` | **{status}** |")
    lines.extend(["", f"门禁计数：PASS {counts['PASS']} / FAIL {counts['FAIL']} / BLOCKED {counts['BLOCKED']} / NOT_TESTED {counts['NOT_TESTED']}。", "", "## 关键阻断", "", "- 候选 `init` 命令使用固定版本的包索引安装，但 2026-10-26 查询公开 PyPI 为 HTTP 404；没有授权发布 wheel，不能将 Connector ZIP 称为普通 WorkBuddy 用户可运行产品。", "- 尚未登录 WorkBuddy、未验证 ZIP 根解析/托管 Python、未安装、未通过对话执行文档任务或接受平台审核。个人主体认证仍需用户本人进行。", "- 本地 `SKILL.md`/CLI 命令静态匹配和干净 CLI 实测均成功，但平台 Skill→CLI 调用未执行，`SKILL_INTEGRATION_PASS` 仍为 BLOCKED。", "- 安全检查覆盖路径、容器、大小和 junction；符号链接直接试验 SKIP，解析器缺乏硬隔离超时与资源限额，不把局部验证外推成完整安全 PASS。", "- macOS/Linux 实机：NOT_TESTED；依赖许可证逐项法律审查：BLOCKED；通用转换 T15：SKIP。", "", "## 证据与人工步骤", "", "- 干净环境逐命令、退出码、结果哈希：`reports/phase2-clean-install.json`、`.md`。", "- 构建物及哈希：`dist/wangbin-document-cli-1.1.0-candidate-manifest.json`、两个 ZIP 与 wheel 各自的 `.sha256`。", "- 实际依赖：`reports/phase2-windows-py312-resolved.txt`、`reports/phase2-dependencies.json`，另见 `docs/third-party-notices.md`。", "- 详细安装/卸载：`docs/phase2-runtime-install.md`；人工平台试传/安装/对话验收：`docs/phase2-platform-acceptance.md`。", "- 本轮未运行 git commit、push、reset 或切换分支，也未自动上传/正式发布。", ""])
    (root / "reports/phase2-acceptance.md").write_text("\n".join(lines), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    report = generate(args.root)
    print(json.dumps({"gates": report["gates"], "gate_totals": report["gate_totals"], "test_totals": report["test_totals"]}, ensure_ascii=False, indent=2))
    return 0 if report["gate_totals"]["FAIL"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
