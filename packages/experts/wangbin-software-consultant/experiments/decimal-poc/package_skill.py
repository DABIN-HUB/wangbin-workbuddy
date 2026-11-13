"""Build an immutable local-only test ZIP from the exact experimental Skill source."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

HERE = Path(__file__).resolve().parent
SKILL = HERE / "skill-preview" / "wangbin-estimate-calculator"
MEMBERS = ("SKILL.md", "scripts/estimator.py", "references/input-output-contract.md")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build(dist):
    if (SKILL / "scripts/estimator.py").read_bytes() != (HERE / "estimator.py").read_bytes():
        raise ValueError("Skill script differs from authoritative estimator.py")
    dist.mkdir(parents=True, exist_ok=True)
    archive = dist / "wangbin-estimate-calculator-0.1.0-technical-candidate.zip"
    manifest = dist / "wangbin-estimate-calculator-0.1.0-technical-candidate.manifest.json"
    sidecar = dist / "wangbin-estimate-calculator-0.1.0-technical-candidate.sha256"
    guide = dist / "wangbin-estimate-calculator-0.1.0-technical-candidate-USE.txt"
    expected = {"wangbin-estimate-calculator/" + name: (SKILL / name).read_bytes() for name in MEMBERS}
    if not archive.exists():
        with archive.open("xb") as target:
            with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED) as z:
                for name, data in expected.items():
                    z.writestr(name, data)
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None or set(z.namelist()) != set(expected):
            raise ValueError("ZIP CRC or member list mismatch")
        hashes = {}
        for name, data in expected.items():
            info = z.getinfo(name)
            actual = z.read(name)
            if actual != data:
                raise ValueError("archive member/source mismatch: " + name)
            hashes[name] = {"sha256": sha(actual), "source_sha256": sha(data),
                            "crc32": format(info.CRC, "08x"), "bytes": len(actual),
                            "source": str(SKILL / name.removeprefix("wangbin-estimate-calculator/"))}
    facts = {"type": "local technical Skill candidate; no WorkBuddy installation or QA PASS",
             "archive": str(archive), "archive_sha256": sha(archive.read_bytes()),
             "members": hashes, "crc": "PASS", "script_authority_sha256": sha((HERE / "estimator.py").read_bytes())}
    payloads = {manifest: json.dumps(facts, ensure_ascii=False, indent=2) + "\n",
                sidecar: facts["archive_sha256"] + "  " + archive.name + "\n",
                guide: "Local: unzip to a fresh controlled directory; run python wangbin-estimate-calculator/scripts/estimator.py <authorized-input.json> -o <new-output.json>.\n"
                       "Manual WorkBuddy test: sign into your own account, upload this exact ZIP using the Skill creation UI; verify parser, permissions, installation and tool execution yourself before any release. No platform status is claimed.\n"}
    for path, text in payloads.items():
        if path.exists():
            if path.read_text(encoding="utf-8") != text:
                raise ValueError("existing sidecar differs: " + path.name)
        else:
            with path.open("x", encoding="utf-8") as stream:
                stream.write(text)
    return facts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dist", type=Path, required=True)
    print(json.dumps(build(parser.parse_args().dist), ensure_ascii=False, indent=2))
