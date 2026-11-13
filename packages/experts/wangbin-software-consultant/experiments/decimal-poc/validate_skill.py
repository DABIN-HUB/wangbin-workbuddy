"""Development-time Skill metadata and package boundary checks (PyYAML required only here)."""
import hashlib
from pathlib import Path
import re
import subprocess
import unicodedata

import yaml

HERE = Path(__file__).resolve().parent
SKILL = HERE / "skill-preview" / "wangbin-estimate-calculator"
source = (SKILL / "SKILL.md").read_text(encoding="utf-8")
assert source.startswith("---\n")
front, body = source[4:].split("\n---\n", 1)
metadata = yaml.safe_load(front)
assert isinstance(metadata, dict)
for field in ("name", "display_name", "display_name_en", "description", "description_zh",
              "description_en", "version", "author"):
    assert isinstance(metadata.get(field), str) and metadata[field].strip(), field
assert metadata["name"] == "wangbin-estimate-calculator"
assert metadata["version"] == "0.1.0"
assert metadata["description"] == metadata["description_zh"]
assert metadata["author"] == "星核实验室 StarCore Lab"
normalized = []
for field, low, high in (("examples_zh", 8, 120), ("examples_en", 12, 180)):
    examples = metadata[field]
    assert isinstance(examples, list) and len(examples) == 3, field
    for index, example in enumerate(examples):
        assert isinstance(example, str) and low <= len(example) <= high, (field, index)
        norm = re.sub(r"\s+", " ", unicodedata.normalize("NFC", example).strip()).casefold().rstrip("。.!?？！")
        assert norm and norm not in normalized, (field, index)
        assert not any(t in norm for t in (".py", ".json", "--output", "python ", "git ", "shell ")), (field, index)
        normalized.append(norm)
assert re.findall(r"^## .+$", body, re.M) == [
    "## Preparation / 准备", "## Usage / 使用", "## Processing / 处理",
    "## Outputs / 输出", "## Limits / 限制"]
assert "@references/input-output-contract.md" in body
assert "scripts/estimator.py" in body
script = SKILL / "scripts" / "estimator.py"
assert script.read_bytes() == (HERE / "estimator.py").read_bytes()
committed_license = subprocess.run(
    ["git", "show", "HEAD:packages/experts/wangbin-software-consultant/LICENSE"],
    cwd=HERE, capture_output=True, check=True).stdout
assert committed_license and (SKILL / "LICENSE").read_bytes().replace(b"\r\n", b"\n") == committed_license
assert (HERE.parent.parent / "LICENSE").read_bytes().replace(b"\r\n", b"\n") == committed_license
assert not any(token in script.read_text(encoding="utf-8") for token in (
    "requests", "urllib", "socket", "subprocess", "eval(", "exec(", "os.system", "shell=True"))
print("SKILL_SOURCE_VALIDATION PASS; YAML safe_load; 6 normalized examples; 5 headings; script SHA256=" +
      hashlib.sha256(script.read_bytes()).hexdigest())
