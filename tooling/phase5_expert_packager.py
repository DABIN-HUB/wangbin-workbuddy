"""Build this Expert from verified Git blobs; platform loading remains unverified."""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import stat
import subprocess
import zipfile
from pathlib import Path

import yaml

NAME = "wangbin-software-consultant"
VERSION = "1.2.0"
SKILL_NAME = "wangbin-estimate-calculator"
SKILL_VERSION = "0.2.0"
SOURCE = f"packages/experts/{NAME}"
# Retain the five base members for historical source replay callers.
MEMBERS = (
    ".codebuddy-plugin/plugin.json",
    "agents/wangbin-software-consultant.md",
    "avatars/expert.png",
    "README.md",
    "LICENSE",
)
CANDIDATE_MEMBERS = MEMBERS + tuple(
    f"skills/{SKILL_NAME}/{rel}"
    for rel in ("SKILL.md", "scripts/estimator.py", "references/input-output-contract.md", "LICENSE")
)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _dump(data: dict) -> bytes:
    return (json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _unlinked(path: Path) -> None:
    """Reject linked ancestors as well as linked files (including Windows junctions)."""
    for part in reversed((path, *path.parents)):
        info = part.lstat()
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT:
            raise ValueError("linked candidate or source path")


def validate_source(source: Path) -> dict[str, object]:
    """Keep strict shared Expert rules and require this version's bundled Skill."""
    try:
        from tooling.expert_rules import validate_prompt_expert
    except ModuleNotFoundError:  # Direct `python tooling/phase5_expert_packager.py` execution.
        from expert_rules import validate_prompt_expert

    source = source.absolute()
    for rel in CANDIDATE_MEMBERS:
        _unlinked(source / rel)
        if not (source / rel).is_file():
            raise ValueError(f"missing or non-regular expert asset: {rel}")
    meta = validate_prompt_expert(source, name=NAME, version=VERSION, category="12-IndustryConsultant")
    if meta.get("skills") != [f"./skills/{SKILL_NAME}"]:
        raise ValueError("required bundled expert skills missing")
    skill = (source / f"skills/{SKILL_NAME}/SKILL.md").read_text(encoding="utf-8")
    match = re.match(r"\A---\s*\n(.*?)\n---\s*\n", skill, re.DOTALL)
    front = yaml.safe_load(match.group(1)) if match else None
    if not isinstance(front, dict) or (front.get("name"), front.get("version")) != (SKILL_NAME, SKILL_VERSION):
        raise ValueError("bundled skill identity/version mismatched")
    return meta


def _git(repo: Path, *args: str) -> bytes:
    # The named repository, not an inherited Git directory/worktree override,
    # determines which original objects are examined.
    env = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}
    # No lazy fetching, even on a partial clone with a protocol-specific allow.
    env.update(GIT_NO_LAZY_FETCH="1", GIT_ALLOW_PROTOCOL="", GIT_TERMINAL_PROMPT="0")
    run = subprocess.run(["git", "--no-replace-objects", "-c", "core.longpaths=true",
                          "-c", "protocol.allow=never", *args],
                         cwd=repo, env=env, capture_output=True)
    if run.returncode != 0:
        raise ValueError(f"cannot verify source repository: git {args[0]} failed")
    return run.stdout


def _historical_blob(repo: Path, commit: str, path: str) -> bytes:
    """Read one exact, locally available regular blob from an explicit repository."""
    repo = repo.resolve(strict=True)
    top = Path(_git(repo, "rev-parse", "--show-toplevel").decode("utf-8").strip()).resolve(strict=True)
    if top != repo or not re.fullmatch(r"[0-9a-f]{40}", commit) or _git(repo, "cat-file", "-t", commit).strip() != b"commit":
        raise ValueError("historical read requires an explicit repository and exact commit")
    entry = _git(repo, "ls-tree", "-z", "--full-tree", commit, "--", path)
    metadata, name = entry.removesuffix(b"\0").split(b"\t", 1)
    mode, kind, oid = metadata.split()
    if name != path.encode("utf-8") or kind != b"blob" or mode not in (b"100644", b"100755"):
        raise ValueError("historical member must be a regular committed blob")
    raw = _git(repo, "cat-file", "blob", oid.decode("ascii"))
    if hashlib.sha1(f"blob {len(raw)}\0".encode("ascii") + raw).hexdigest().encode("ascii") != oid:
        raise ValueError("historical blob identity mismatch")
    return raw


def _verified_payload(root: Path, source_repo: Path | None, source_commit: str | None) -> tuple[str, dict[str, bytes], list[str]]:
    repo = source_repo.absolute() if source_repo is not None else root
    _unlinked(repo)
    repo = repo.resolve(strict=True)
    top = Path(_git(repo, "rev-parse", "--show-toplevel").decode("utf-8").strip()).resolve(strict=True)
    if top != repo:
        raise ValueError("source_repo must be the actual Git repository top level")
    if source_commit is None and root != repo:
        raise ValueError("isolated source snapshot requires an explicit full source_commit")
    if source_commit is not None and not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", source_commit):
        raise ValueError("source_commit must be a full lowercase Git commit hash")
    commit = _git(repo, "rev-parse", "--verify", f"{source_commit or 'HEAD'}^{{commit}}").decode("ascii").strip()
    if source_commit is not None and source_commit != commit:
        raise ValueError("source_commit does not identify the resolved commit object")

    paths = {f"{SOURCE}/{rel}": rel for rel in CANDIDATE_MEMBERS}
    tree = _git(repo, "ls-tree", "-z", "--full-tree", commit, "--", *paths)
    blobs = {}
    for row in tree.split(b"\0"):
        if not row:
            continue
        metadata, path = row.split(b"\t", 1)
        mode, kind, oid = metadata.decode("ascii").split()
        if kind != "blob" or mode not in {"100644", "100755"}:
            raise ValueError("committed candidate member must be a regular Git blob")
        blobs[path.decode("utf-8")] = oid
    if set(blobs) != set(paths):
        raise ValueError("commit does not contain the nine approved candidate members")

    expected = {}
    normalized = []
    for path, rel in sorted(paths.items()):
        local = root / path
        _unlinked(local)
        if not local.is_file():
            raise ValueError(f"missing or non-regular expert asset: {rel}")
        actual = local.read_bytes()
        canonical = _git(repo, "cat-file", "blob", blobs[path])
        if actual != canonical:
            # All eight non-PNG members are text; only checkout CRLF may differ.
            if rel == "avatars/expert.png" or actual.replace(b"\r\n", b"\n") != canonical:
                raise ValueError(f"source differs from committed blob: {rel}")
            normalized.append(rel)
        expected[f"{NAME}/{rel}"] = canonical
    return commit, expected, normalized


def _publish(artifacts: tuple[tuple[Path, bytes], ...]) -> None:
    # lstat also sees dangling symlinks; the exclusive open closes the
    # exists-check/write race. Never complete an existing partial set.
    for path, _ in artifacts:
        try:
            path.lstat()
        except FileNotFoundError:
            continue
        raise FileExistsError("candidate version already exists; preserve immutable release and use an empty dist")
    created = []
    try:
        for path, data in artifacts:
            with path.open("xb") as stream:
                created.append((path, os.fstat(stream.fileno())))
                if stream.write(data) != len(data):
                    raise OSError("incomplete candidate artifact write")
        for path, data in artifacts:
            if path.read_bytes() != data:
                raise ValueError("candidate artifact readback failed")
    except BaseException:
        # Roll back only paths created by this invocation, not another writer's
        # pre-existing or subsequently replaced artifacts.
        for path, identity in reversed(created):
            try:
                if os.path.samestat(path.lstat(), identity):
                    path.unlink()
            except FileNotFoundError:
                pass
        raise


def build(root: Path, *, source_commit: str | None = None, source_repo: Path | None = None) -> dict[str, object]:
    """Build once from a verified commit, optionally in an isolated byte snapshot."""
    root = root.absolute()
    _unlinked(root)
    root = root.resolve(strict=True)
    commit, expected, normalized = _verified_payload(root, source_repo, source_commit)
    validate_source(root / SOURCE)
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for member, data in sorted(expected.items()):
            entry = zipfile.ZipInfo(member, date_time=(1980, 1, 1, 0, 0, 0))
            entry.external_attr = 0o100644 << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    raw = out.getvalue()
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        if archive.testzip() is not None or archive.namelist() != sorted(expected) or any(archive.read(member) != data for member, data in expected.items()):
            raise ValueError("candidate ZIP member mismatch/corruption")

    output = root / "dist"
    output.mkdir(exist_ok=True)
    _unlinked(output)
    destination = output / f"{NAME}-{VERSION}-expert-candidate.zip"
    sidecar = output / f"{destination.name}.sha256"
    manifest = output / f"{destination.name}.manifest.json"
    members = [{"path": name, "size": len(data), "sha256": digest(data)} for name, data in sorted(expected.items())]
    result = {
        "id": NAME,
        "name": NAME,
        "version": VERSION,
        "status": "PASS",
        "status_scope": "local_schema_and_archive_integrity_only",
        "scope": "local archive integrity only",
        "source": SOURCE,
        "source_commit": commit,
        "source_byte_basis": "verified_git_blob_bytes",
        "archive": destination.relative_to(root).as_posix(),
        "platform": "BLOCKED",
        "workbuddy_install": "NOT_TESTED",
        "workbuddy_dialogue": "NOT_TESTED",
        "sha256": digest(raw),
        "members": members,
        "payload_snapshot_sha256": digest(_dump({"members": members})),
    }
    _publish(((destination, raw), (sidecar, f"{result['sha256']}  {destination.name}\n".encode("ascii")),
              (manifest, _dump(result))))
    return {**result, "zip": str(destination), "checkout_crlf_normalized_members": normalized}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--source-repo", type=Path)
    parser.add_argument("--source-commit")
    args = parser.parse_args()
    print(json.dumps(build(args.root, source_repo=args.source_repo, source_commit=args.source_commit), ensure_ascii=False, indent=2))
