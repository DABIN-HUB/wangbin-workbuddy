"""Bounded authorized local files, not an OS sandbox (notably on Windows).

No openat/mandatory OS isolation is available here: a hostile process able to
rename directories can still race path operations. Keep this a private local
workspace, with OS ACLs managed by the caller. File modes are best effort on NTFS.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import stat
import tempfile

from .errors import ContractError
from .serialization import MAX_JSON_BYTES, dumps, loads


def _unlinked(path):
    for part in (path, *path.parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, "st_file_attributes", 0) & 0x400:
            raise ContractError("UNSAFE_LINK")
        if hasattr(part, "is_junction") and part.is_junction():
            raise ContractError("UNSAFE_LINK")


def _identity(info):
    # Windows stat/fstat ctime semantics differ across Python releases.
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns


def _regular(info):
    if not stat.S_ISREG(info.st_mode):
        raise ContractError("NOT_REGULAR_FILE")
    if info.st_nlink != 1:
        raise ContractError("HARDLINK_FILE")
    if info.st_size > MAX_JSON_BYTES:
        raise ContractError("JSON_SIZE_LIMIT")


class Workspace:
    """Existing explicit authorization root; paths are relative to this root."""

    def __init__(self, root):
        if ".." in Path(root).parts:
            raise ContractError("PATH_TRAVERSAL")
        self.root = Path(os.path.abspath(root))
        _unlinked(self.root)
        if not self.root.is_dir():
            raise ContractError("WORKSPACE_REQUIRED")

    def path(self, supplied, *, json_only=True):
        raw = Path(supplied)
        if ".." in raw.parts:
            raise ContractError("PATH_TRAVERSAL")
        for part in raw.parts:
            if part != raw.anchor and (":" in part or part.endswith((".", " ")) or part.split(".")[0].rstrip().upper() in {
                "CON", "PRN", "AUX", "NUL", *(f"COM{n}" for n in range(1, 10)), *(f"LPT{n}" for n in range(1, 10))
            }):
                raise ContractError("INVALID_LOCAL_PATH")
        if raw.drive and not raw.is_absolute():
            raise ContractError("INVALID_LOCAL_PATH")
        path = Path(os.path.abspath(self.root / raw))
        if not path.is_relative_to(self.root) or path == self.root:
            raise ContractError("PATH_OUTSIDE_WORKSPACE")
        # Reject Windows ADS, reserved aliases and trailing dot/space aliases.
        for part in path.relative_to(self.root).parts:
            if ":" in part or part.endswith((".", " ")) or part.split(".")[0].upper() in {
                "CON", "PRN", "AUX", "NUL", *(f"COM{n}" for n in range(1, 10)), *(f"LPT{n}" for n in range(1, 10))
            }:
                raise ContractError("INVALID_LOCAL_PATH")
        if json_only and path.suffix.lower() != ".json":
            raise ContractError("JSON_PATH_REQUIRED")
        _unlinked(path)
        if not path.parent.is_dir():
            raise ContractError("PARENT_DIRECTORY_REQUIRED")
        return path

    def read(self, supplied):
        path = self.path(supplied)
        before = path.lstat()
        _regular(before)
        flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
        with os.fdopen(os.open(path, flags), "rb") as stream:
            initial = os.fstat(stream.fileno())
            _regular(initial)
            if _identity(initial) != _identity(before):
                raise ContractError("FILE_CHANGED")
            _unlinked(path)
            payload = stream.read(MAX_JSON_BYTES + 1)
            finished = os.fstat(stream.fileno())
            _regular(finished)
            if (len(payload) > MAX_JSON_BYTES or _identity(initial) != _identity(finished)
                    or initial.st_ctime_ns != finished.st_ctime_ns or len(payload) != initial.st_size
                    or _identity(initial) != _identity(path.lstat())):
                raise ContractError("FILE_CHANGED")
        self.path(path)
        return loads(payload), hashlib.sha256(payload).hexdigest()

    @contextmanager
    def lock(self, supplied):
        target = self.path(supplied)
        lock = self.path(str(target) + ".lock", json_only=False)
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_BINARY", 0), 0o600)
        except FileExistsError:
            raise ContractError("STATE_LOCKED") from None
        owned = os.fstat(fd)
        try:
            os.close(fd)
            self.path(target)
            yield
        finally:
            # Never unlink another writer's replacement lock.
            try:
                current = lock.lstat()
                if not stat.S_ISLNK(current.st_mode) and (current.st_dev, current.st_ino) == (owned.st_dev, owned.st_ino):
                    lock.unlink()
            except FileNotFoundError:
                pass

    def create(self, supplied, data):
        with self.lock(supplied):
            self._write(supplied, data)

    def replace(self, supplied, data, expected_digest):
        """Caller holds the exclusive lock; compare exact prior bytes before CAS."""
        self._write(supplied, data, expected_digest=expected_digest)

    def _write(self, supplied, data, *, expected_digest=None):
        path = self.path(supplied)
        if expected_digest is None and path.exists():
            raise ContractError("OUTPUT_EXISTS")
        payload = (dumps(data) + "\n").encode("utf-8")
        if len(payload) > MAX_JSON_BYTES:
            raise ContractError("JSON_SIZE_LIMIT")
        fd, name = tempfile.mkstemp(prefix=".solar-pv-", suffix=".tmp", dir=path.parent)
        temp = Path(name)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            self.path(path)
            if expected_digest is not None:
                _, current_digest = self.read(path)
                if current_digest != expected_digest:
                    raise ContractError("STATE_CHANGED")
                self.path(path)
                os.replace(temp, path)
            else:
                try:
                    # Atomic no-clobber publication on NTFS/POSIX; never overwrite.
                    os.link(temp, path)
                except FileExistsError:
                    raise ContractError("OUTPUT_EXISTS") from None
        finally:
            temp.unlink(missing_ok=True)
        self._sync_directory(path.parent)

    @staticmethod
    def _sync_directory(path):
        if os.name != "nt":
            fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(fd)
            finally:
                os.close(fd)
