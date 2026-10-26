"""Small cross-process capacity limit for local parsing and spreadsheet work.

The per-user slot files contain no document data. OS file locks release on process
exit, including crashes; a busy slot is never reclaimed by guessing at a PID.
This is a capacity bound, not a sandbox or a per-machine security boundary.
"""
from __future__ import annotations

import getpass
import os
import stat
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .errors import EngineError

_SLOTS = 2


def _slot_dir() -> Path:
    owner = str(os.getuid()) if hasattr(os, "getuid") else getpass.getuser()
    root = Path(tempfile.gettempdir()) / f"wangbin-document-cli-slots-{owner}"
    try:
        root.mkdir(mode=0o700, exist_ok=True)
        if root.is_symlink() or (hasattr(root, "is_junction") and root.is_junction()) or not root.is_dir():
            raise OSError("slot directory is not an ordinary directory")
        if os.name != "nt" and stat.S_IMODE(root.stat().st_mode) & 0o077:
            raise OSError("slot directory permissions are too broad")
    except OSError as exc:
        raise EngineError("RESOURCE_LOCK_UNAVAILABLE", "无法安全建立任务容量锁目录") from exc
    return root


@contextmanager
def hold_resource_slot() -> Iterator[None]:
    """At most two cooperative CLI processes may parse or export concurrently."""
    root = _slot_dir()
    for number in range(_SLOTS):
        flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
        try:
            fd = os.open(root / f"slot-{number}.lock", flags, 0o600)
        except OSError as exc:
            raise EngineError("RESOURCE_LOCK_UNAVAILABLE", "无法安全打开任务容量锁") from exc
        try:
            if not stat.S_ISREG(os.fstat(fd).st_mode):
                raise EngineError("RESOURCE_LOCK_UNAVAILABLE", "任务容量锁不是普通文件")
            if os.fstat(fd).st_size == 0:
                os.write(fd, b"\0")
            os.lseek(fd, 0, os.SEEK_SET)
            try:
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except (BlockingIOError, OSError):
                continue
            try:
                yield
            finally:
                os.lseek(fd, 0, os.SEEK_SET)
                if os.name == "nt":
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(fd, fcntl.LOCK_UN)
            return
        finally:
            os.close(fd)
    raise EngineError("RESOURCE_BUSY", "并发文档任务已达上限，请稍后重试")
