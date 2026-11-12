"""Crash-released kernel locks for native host sessions only.

Lock files remain as stable inodes; never delete them while a run can be used.
Legacy lock files are not reclaimed. This is not protection from a hostile OS
user, network filesystem, or concurrent use of the legacy CLI in this run.
"""
from contextlib import contextmanager
import os
import stat

from ..errors import ContractError
from ..local_files import Workspace


class HostWorkspace(Workspace):
    @contextmanager
    def lock(self, supplied):
        target = self.path(supplied)
        if self.path(str(target) + '.lock', json_only=False).exists():
            raise ContractError('HOST_LEGACY_LOCK_REQUIRES_REVIEW')
        path = self.path(str(target) + '.host-lock', json_only=False)
        fd = os.open(path, os.O_CREAT | os.O_RDWR | getattr(os, 'O_BINARY', 0)
                     | getattr(os, 'O_NOFOLLOW', 0), 0o600)
        try:
            info = os.fstat(fd)
            self.path(path, json_only=False)
            current = path.lstat()
            if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                    or (info.st_dev, info.st_ino) != (current.st_dev, current.st_ino)):
                raise ContractError('UNSAFE_LINK')
            try:
                if os.name == 'nt':
                    import msvcrt
                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                raise ContractError('STATE_LOCKED') from None
            self.path(target)
            yield
        finally:
            # close releases the kernel lock, including after process death.
            # Unlinking here would allow competing locks on different inodes.
            os.close(fd)
