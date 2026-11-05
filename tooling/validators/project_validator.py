"""Project and platform-candidate structure validation."""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

import yaml

from . import Finding, ValidationReport
from .secret_scanner import scan_for_secrets

SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-[0-9A-Za-z.-]+)?$")
_PLACEHOLDER = re.compile(r"(?i)(?:\b(?:todo|tbd|placeholder|sample|example)\b|待补充|待完善|占位|示例)")
_INTERNAL = re.compile(r"(?i)(?:\b(?:api|json|yaml|yml|cli|sdk|regex|stack trace|traceback|exception|bash|powershell|python|pip|git)\b|http\s*\d{3}|error\s*code|[A-Za-z]:[\\/]|/(?:home|usr|tmp|var)/)")
_ABSOLUTE_GUARANTEE = re.compile(r"(?i)(?:guarantee|always|never fail|100%|绝对|保证|必然|一定(?:能|会)|完全准确)")
_PLATFORM_CLAIM = re.compile(r"(?i)(?:适用于所有|支持所有|all platforms|any platform|guaranteed? on)")
_END_PUNCT = "。.!！?？;；:：,，、…"
CANONICAL_SECTIONS = (("Preparation", "准备"), ("Usage", "使用"), ("Processing", "处理"),
                      ("Outputs", "输出"), ("Limits", "边界"))


def _normalized_user_text(value: str) -> str:
    value = unicodedata.normalize("NFC", value).strip()
    value = re.sub(r"\s+", " ", value).casefold()
    return value.rstrip(_END_PUNCT).strip()


def _user_text_error(value: Any, *, language: str) -> str | None:
    if not isinstance(value, str) or not value.strip():
        return "must be a non-empty string"
    text = value.strip()
    length = len(text)
    if language == "zh" and not 8 <= length <= 120:
        return "Chinese user goal length must be 8-120 characters"
    if language == "en" and not 12 <= length <= 180:
        return "English user goal length must be 12-180 characters"
    if _PLACEHOLDER.search(text):
        return "placeholder text is not allowed"
    if _INTERNAL.search(text):
        return "internal technical terms, commands, paths or error codes are not allowed"
    if _ABSOLUTE_GUARANTEE.search(text) or _PLATFORM_CLAIM.search(text):
        return "unverified platform or absolute capability claim is not allowed"
    return None


def validate_user_facing_standard(front: dict[str, Any], skill_path: Path,
                                  checks: list[dict[str, Any]], findings: list[Finding], *,
                                  enforce: bool = False) -> None:
    """Validate Skill-only user copy; legacy packages opt in via the migration marker."""
    enabled = enforce or not isinstance(front, dict) or front.get("user_facing_standard") == "v1"
    if not enabled:
        # Existing assets remain structurally valid during migration, but their
        # user-facing claims are not silently treated as having passed v1.
        for name in ("skill.USER_DESCRIPTION_PASS", "skill.USER_EXAMPLES_PASS", "skill.USER_SECTIONS_PASS"):
            checks.append({"name": name, "status": "NOT_TESTED",
                           "message": "历史 Skill 未声明 user_facing_standard=v1，需显式迁移后检查"})
        checks.append({"name": "skill.capability_boundary_review", "status": "NOT_TESTED",
                       "message": "历史 Skill 的能力边界需要人工复核"})
        return
    if not isinstance(front, dict):
        findings.append(Finding("USER_DESCRIPTION_PASS", str(skill_path), "frontmatter must be a YAML mapping"))
        _check(checks, "skill.USER_DESCRIPTION_PASS", False, "frontmatter must be a YAML mapping")
        _check(checks, "skill.USER_EXAMPLES_PASS", False, "frontmatter must be a YAML mapping")
        _check(checks, "skill.USER_SECTIONS_PASS", False, "frontmatter must be a YAML mapping")
        return
    name_ok = True
    for key in ("display_name", "display_name_en"):
        value = front.get(key)
        error = _user_text_error(value, language="zh" if key == "display_name" else "en")
        if error and "length" not in error:
            findings.append(Finding("USER_DESCRIPTION_PASS", str(skill_path), f"{key}: {error}"))
            name_ok = False
    description_zh = front.get("description_zh", front.get("description"))
    if (isinstance(front.get("description"), str) and isinstance(front.get("description_zh"), str)
            and _normalized_user_text(front["description"]) != _normalized_user_text(front["description_zh"])):
        findings.append(Finding("USER_DESCRIPTION_PASS", str(skill_path), "description and description_zh must agree"))
        name_ok = False
    desc_ok = (isinstance(description_zh, str) and bool(description_zh.strip()) and
               isinstance(front.get("description_en"), str) and bool(front["description_en"].strip()))
    desc_errors = []
    for value, lang in ((description_zh, "zh"), (front.get("description_en"), "en")):
        if isinstance(value, str):
            error = _user_text_error(value, language=lang)
            if error and "length" not in error:
                desc_errors.append(error)
    desc_ok = desc_ok and not desc_errors
    _check(checks, "skill.USER_DESCRIPTION_PASS", name_ok and desc_ok,
           "双语名称与描述完整" if name_ok and desc_ok else "双语名称或描述缺失")
    if not name_ok or not desc_ok:
        findings.append(Finding("USER_DESCRIPTION_PASS", str(skill_path), "双语名称与描述必须非空"))
    examples_ok = True
    normalized: set[str] = set()
    for key, lang in (("examples_zh", "zh"), ("examples_en", "en")):
        values = front.get(key)
        if not isinstance(values, list) or len(values) != 3:
            findings.append(Finding("USER_EXAMPLES_PASS", str(skill_path), f"{key} 必须恰好包含 3 条"))
            examples_ok = False
            continue
        for index, value in enumerate(values):
            error = _user_text_error(value, language=lang)
            normalized_value = _normalized_user_text(value) if isinstance(value, str) else ""
            if error or normalized_value in normalized:
                findings.append(Finding("USER_EXAMPLES_PASS", str(skill_path),
                                        f"{key}[{index}]: {error or 'normalized duplicate'}"))
                examples_ok = False
            normalized.add(normalized_value)
    _check(checks, "skill.USER_EXAMPLES_PASS", examples_ok,
           "双语用户目标通过" if examples_ok else "双语用户目标不符合门禁")
    body = skill_path.read_text(encoding="utf-8")
    heading_pattern = re.compile(r"(?m)^##\s+(.+?)\s*$")
    headings = list(heading_pattern.finditer(body))
    expected = {f"{english} / {chinese}" for english, chinese in CANONICAL_SECTIONS}
    expected |= {f"{chinese} / {english}" for english, chinese in CANONICAL_SECTIONS}
    # The section sequence is deliberately exact: accepting a later matching
    # heading would allow duplicate/extra sections to hide a missing section.
    section_matches = [match for match in headings if match.group(1) in expected]
    sections_ok = (len(headings) == len(CANONICAL_SECTIONS) and
                   [match.group(1) for match in headings] ==
                   [f"{english} / {chinese}" for english, chinese in CANONICAL_SECTIONS])
    if sections_ok:
        for index, match in enumerate(section_matches):
            end = section_matches[index + 1].start() if index + 1 < len(section_matches) else len(body)
            if not body[match.end():end].strip():
                sections_ok = False
        limits = section_matches[-1]
        if not re.search(r"(?i)(?:不能|不支持|限制|仅限|无法|does not|not support|limit|cannot)", body[limits.end():]):
            sections_ok = False
    _check(checks, "skill.USER_SECTIONS_PASS", sections_ok,
           "五段双语说明按序且非空" if sections_ok else "五段双语说明缺失、空段、乱序或缺少边界")
    if not sections_ok:
        findings.append(Finding("USER_SECTIONS_PASS", str(skill_path), "五段 Preparation/Usage/Processing/Outputs/Limits 门禁失败"))
    checks.append({"name": "skill.capability_boundary_review", "status": "NOT_TESTED",
                   "message": "静态检查不能证明全部能力；需人工核对 capability boundary 证据"})


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
    # description is retained as a compatibility alias for description_zh.
    if not front.get("description_zh") and front.get("description"):
        front["description_zh"] = front["description"]
    required = ["name", "display_name", "display_name_en", "description_zh", "description_en", "version", "author"]
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
    validate_user_facing_standard(front, skill, checks, findings)
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
