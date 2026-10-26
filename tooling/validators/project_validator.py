"""Project and platform-candidate structure validation."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import yaml

from . import Finding, ValidationReport
from .secret_scanner import scan_for_secrets

SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?$")


def _read_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError("缺少 YAML frontmatter")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError("frontmatter 未闭合")
    value = yaml.safe_load(parts[1])
    if not isinstance(value, dict):
        raise ValueError("frontmatter 必须是对象")
    return value


def _check(checks: list[dict[str, Any]], name: str, passed: bool, message: str) -> None:
    checks.append({"name": name, "status": "PASS" if passed else "FAIL", "message": message})


def validate_skill(skill_dir: Path, checks: list[dict[str, Any]], findings: list[Finding]) -> None:
    skill = skill_dir / "SKILL.md"
    if not skill.exists():
        findings.append(Finding("SKILL_REQUIRED", str(skill), "SKILL.md 是 WorkBuddy Skill 必填文件"))
        return
    try:
        front = _read_frontmatter(skill)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        findings.append(Finding("SKILL_FRONTMATTER", str(skill), f"无法读取 frontmatter: {exc}"))
        return
    required = ["name", "display_name", "display_name_en", "description", "description_zh", "description_en", "version", "author"]
    missing = [key for key in required if not front.get(key)]
    _check(checks, "skill.required_frontmatter", not missing, "必填字段完整" if not missing else f"缺少字段: {', '.join(missing)}")
    if missing:
        findings.append(Finding("SKILL_FIELDS", str(skill), f"缺少字段: {', '.join(missing)}"))
    version = str(front.get("version", ""))
    _check(checks, "skill.semver", bool(SEMVER.match(version)), f"version={version}")
    if not SEMVER.match(version):
        findings.append(Finding("SKILL_VERSION", str(skill), "version 不是语义化版本"))
    if not re.match(r"^[a-z0-9][a-z0-9-]*$", str(front.get("name", ""))):
        findings.append(Finding("SKILL_NAME", str(skill), "name 必须是小写字母、数字和连字符"))
    for referenced in re.findall(r"@((?:references|scripts|templates)/[A-Za-z0-9_./-]+)", skill.read_text(encoding="utf-8")):
        if not (skill_dir / referenced).is_file():
            findings.append(Finding("RESOURCE_MISSING", str(skill_dir / referenced), "SKILL.md 引用的资源不存在"))


def validate_expert(expert_dir: Path, checks: list[dict[str, Any]], findings: list[Finding]) -> None:
    plugin_path = expert_dir / ".codebuddy-plugin" / "plugin.json"
    if not plugin_path.exists():
        findings.append(Finding("EXPERT_PLUGIN_REQUIRED", str(plugin_path), "Expert 的 plugin.json 不存在"))
        return
    try:
        data = json.loads(plugin_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(Finding("EXPERT_JSON", str(plugin_path), f"plugin.json 无法解析: {exc}"))
        return
    required = ["name", "expertType", "version", "description", "author", "agents", "agentName", "displayName", "profession", "displayDescription", "avatar", "categoryId", "defaultInitPrompt", "plugin", "tags", "quickPrompts"]
    missing = [key for key in required if not data.get(key)]
    _check(checks, "expert.required_fields", not missing, "必填字段完整" if not missing else f"缺少字段: {', '.join(missing)}")
    if missing:
        findings.append(Finding("EXPERT_FIELDS", str(plugin_path), f"缺少字段: {', '.join(missing)}"))
    if data.get("expertType") not in {"agent", "team"}:
        findings.append(Finding("EXPERT_TYPE", str(plugin_path), "expertType 必须是 agent 或 team"))
    if not SEMVER.match(str(data.get("version", ""))):
        findings.append(Finding("EXPERT_VERSION", str(plugin_path), "version 不是语义化版本"))
    if len(data.get("tags", [])) != 3:
        findings.append(Finding("EXPERT_TAGS", str(plugin_path), "tags 必须固定为 3 个"))
    if len(data.get("quickPrompts", [])) != 3:
        findings.append(Finding("EXPERT_PROMPTS", str(plugin_path), "quickPrompts 必须固定为 3 个"))
    for agent in data.get("agents", []):
        if not (expert_dir / agent.lstrip("./")).is_file():
            findings.append(Finding("RESOURCE_MISSING", str(expert_dir / agent.lstrip("./")), "Expert agent 文件不存在"))


def validate_connector(connector_dir: Path, checks: list[dict[str, Any]], findings: list[Finding]) -> None:
    meta_path = connector_dir / "connector-meta.json"
    if not meta_path.exists():
        findings.append(Finding("CONNECTOR_META_REQUIRED", str(meta_path), "connector-meta.json 不存在"))
        return
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        findings.append(Finding("CONNECTOR_JSON", str(meta_path), f"connector-meta.json 无法解析: {exc}"))
        return
    for key in ("name", "description", "source", "version", "examples_zh", "examples_en"):
        if not meta.get(key):
            findings.append(Finding("CONNECTOR_FIELD", str(meta_path), f"缺少字段: {key}"))
    if not re.match(r"^[a-z0-9][a-z0-9-]*$", str(meta.get("source", ""))):
        findings.append(Finding("CONNECTOR_SOURCE", str(meta_path), "source 必须是 kebab-case"))
    kind = meta.get("type", "mcp")
    if kind == "mcp":
        config_path = connector_dir / "mcp.json"
        if not config_path.exists():
            findings.append(Finding("MCP_CONFIG_REQUIRED", str(config_path), "MCP 连接器必须包含 mcp.json"))
        else:
            try:
                config = json.loads(config_path.read_text(encoding="utf-8"))
                servers = config.get("mcpServers", {})
                if not isinstance(servers, dict) or len(servers) != 1:
                    findings.append(Finding("MCP_SERVER_COUNT", str(config_path), "必须配置且只能配置一个 MCP Server"))
            except (OSError, json.JSONDecodeError) as exc:
                findings.append(Finding("MCP_JSON", str(config_path), f"mcp.json 无法解析: {exc}"))
        if not (connector_dir / "icon.svg").exists():
            findings.append(Finding("CONNECTOR_ICON_REQUIRED", str(connector_dir / "icon.svg"), "MCP 连接器必须包含 icon.svg"))
    elif kind == "cli":
        config_path = connector_dir / "cli.json"
        if not config_path.exists():
            findings.append(Finding("CLI_CONFIG_REQUIRED", str(config_path), "CLI 连接器必须包含 cli.json"))
        else:
            try:
                config = json.loads(config_path.read_text(encoding="utf-8"))
                required_commands = ("init", "status") + (("auth", "unAuth") if "auth" in config else ())
                if "unAuth" in config and "auth" not in config:
                    findings.append(Finding("CLI_AUTH_PAIR", str(config_path), "无认证模式不应单独声明 unAuth"))
                for key in required_commands:
                    commands = config.get(key, {})
                    if not isinstance(commands, dict) or any(not isinstance(commands.get(os_name), str) or not commands[os_name].strip() for os_name in ("darwin", "linux", "win32")):
                        findings.append(Finding("CLI_COMMAND", str(config_path), f"{key} 缺少跨平台非交互式命令"))
                if not config.get("statusMatch") and not config.get("statusMatchJson"):
                    findings.append(Finding("CLI_STATUS_MATCH", str(config_path), "缺少 statusMatch 或 statusMatchJson"))
                if config.get("runtime", {}).get("type") == "python" and meta.get("minWorkbuddyVersion") != "5.0.0":
                    findings.append(Finding("CLI_PYTHON_VERSION", str(meta_path), "Python runtime 要求最低 WorkBuddy 5.0.0"))
            except (OSError, json.JSONDecodeError) as exc:
                findings.append(Finding("CLI_JSON", str(config_path), f"cli.json 无法解析: {exc}"))
        if not (connector_dir / "icon.svg").exists():
            findings.append(Finding("CONNECTOR_ICON_REQUIRED", str(connector_dir / "icon.svg"), "CLI 连接器必须包含 icon.svg"))
    elif kind != "skill-only":
        findings.append(Finding("CONNECTOR_TYPE", str(meta_path), "type 必须是 mcp、cli 或 skill-only"))


def validate_project(root: Path) -> ValidationReport:
    checks: list[dict[str, Any]] = []
    findings: list[Finding] = []
    required = ["README.md", "pyproject.toml", "docs/workbuddy-platform-spec.md", "docs/third-party-notices.md", "services/document-engine", "packages/skills", "tooling", "tests"]
    for rel in required:
        exists = (root / rel).exists()
        _check(checks, f"path.{rel}", exists, "存在" if exists else "缺失")
        if not exists:
            findings.append(Finding("REQUIRED_PATH", str(root / rel), "项目必需路径缺失"))
    for path in (root / "packages" / "skills").glob("*/") if (root / "packages" / "skills").exists() else []:
        validate_skill(path, checks, findings)
    for path in (root / "packages" / "experts").glob("*/") if (root / "packages" / "experts").exists() else []:
        validate_expert(path, checks, findings)
    for path in (root / "packages" / "connectors").glob("*/") if (root / "packages" / "connectors").exists() else []:
        validate_connector(path, checks, findings)
    findings.extend(scan_for_secrets(root))
    _check(checks, "security.secrets", not any(f.code == "SECRET_PATTERN" for f in findings), "未发现高置信度凭证" if not any(f.code == "SECRET_PATTERN" for f in findings) else "发现疑似凭证")
    return ValidationReport("PASS" if not findings else "FAIL", checks, findings)
