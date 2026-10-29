"""Private resource/file primitives for D3. Local ACL-controlled workspaces only.

Checks bound cooperative local operations, not an OS sandbox: an adversarial
iterator/native call cannot be preempted by a Python checkpoint. Windows working
set is observed, not reserved; unrelated threads share the process budget.
"""
from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
import ctypes
import hashlib
import os
from pathlib import Path
import sqlite3
import stat
import tempfile
import time

from .errors import ContractError
from .local_files import _unlinked, _identity


@lru_cache(maxsize=1)
def _windows_reader():
    from ctypes import wintypes
    class Counters(ctypes.Structure):
        _fields_ = [('cb', wintypes.DWORD), ('faults', wintypes.DWORD)] + [
            (name, ctypes.c_size_t) for name in ('peak', 'current', 'paged_peak',
            'paged', 'nonpaged_peak', 'nonpaged', 'pagefile', 'pagefile_peak')]
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi = ctypes.WinDLL('psapi', use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
    def read():
        c = Counters(); c.cb = ctypes.sizeof(c)
        if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(c), c.cb):
            raise ContractError('BUNDLE_MEMORY_UNAVAILABLE')
        return c.current, c.peak
    return read


def memory_usage():
    """Actual resident bytes and OS process lifetime high-water mark."""
    if os.name == 'nt':
        return _windows_reader()()
    try:
        with open('/proc/self/status', encoding='ascii') as f:
            values = dict(line.split(':', 1) for line in f if ':' in line)
        return int(values['VmRSS'].split()[0])*1024, int(values['VmHWM'].split()[0])*1024
    except (OSError, KeyError, ValueError):
        raise ContractError('BUNDLE_MEMORY_UNAVAILABLE') from None


class Meter:
    def __init__(self, budget):
        self.budget = budget
        self.start = time.monotonic()
        self.input = self.disk = self.index = self.rows = self.atoms = 0
        self.peak = self.os_peak = self.peak_disk = 0
        self.check()

    def check(self):
        if time.monotonic() - self.start > self.budget.max_seconds:
            raise ContractError('BUNDLE_TIME_LIMIT')
        current, peak = memory_usage()
        self.peak = max(current, self.peak); self.os_peak = max(peak, self.os_peak)
        if max(current, peak) > self.budget.max_memory_bytes:
            raise ContractError('BUNDLE_MEMORY_LIMIT')
        if self.input > self.budget.max_input_bytes:
            raise ContractError('BUNDLE_INPUT_LIMIT')
        self.peak_disk = max(self.peak_disk, self.disk + self.index)
        if self.disk + self.index > self.budget.max_disk_bytes:
            raise ContractError('BUNDLE_DISK_LIMIT')
        if self.rows > self.budget.max_rows:
            raise ContractError('BUNDLE_ROW_LIMIT')

    def stats(self):
        self.check()
        return {'rows_validated': self.rows, 'atoms_validated': self.atoms,
            'input_bytes': self.input, 'disk_bytes': self.disk, 'peak_disk_reserved_bytes': self.peak_disk,
            'elapsed_seconds': time.monotonic()-self.start,
            'peak_working_set_bytes': self.peak, 'os_peak_working_set_bytes': self.os_peak}


def local_target(supplied):
    raw = os.fspath(supplied)
    if not isinstance(raw, str) or not raw or raw.startswith(('\\\\', '//')):
        raise ContractError('BUNDLE_LOCAL_PATH')
    p = Path(raw)
    if '..' in p.parts or (p.drive and not p.is_absolute()):
        raise ContractError('BUNDLE_LOCAL_PATH')
    for part in p.parts:
        if part == p.anchor:
            continue
        if (':' in part or part.endswith(('.', ' ')) or
                part.split('.')[0].upper() in {'CON','PRN','AUX','NUL',
                *(f'COM{i}' for i in range(1,10)), *(f'LPT{i}' for i in range(1,10))}):
            raise ContractError('BUNDLE_LOCAL_PATH')
    p = Path(os.path.abspath(p))
    _unlinked(p)
    if not p.parent.is_dir():
        raise ContractError('BUNDLE_PARENT_REQUIRED')
    return p


def _regular(info, limit):
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
        raise ContractError('BUNDLE_UNSAFE_FILE')
    if info.st_size > limit:
        raise ContractError('BUNDLE_FILE_LIMIT')


def checked_read(path, limit, meter, *, account=True):
    meter.check(); _unlinked(path)
    before = path.lstat(); _regular(before, limit)
    # Reserve/validate cumulative input and disk before allocating file bytes.
    # Re-reading the same immutable identity for a closing check is not new disk.
    if account:
        meter.input += before.st_size; meter.disk += before.st_size
    meter.check()
    flags = os.O_RDONLY | getattr(os, 'O_BINARY', 0) | getattr(os, 'O_NOFOLLOW', 0)
    with os.fdopen(os.open(path, flags), 'rb') as f:
        initial = os.fstat(f.fileno()); _regular(initial, limit)
        if _identity(before) != _identity(initial):
            raise ContractError('BUNDLE_FILE_CHANGED')
        payload = f.read(limit+1)
        final = os.fstat(f.fileno()); _regular(final, limit)
        current = path.lstat(); _regular(current, limit)
        if (_identity(initial) != _identity(final) or initial.st_ctime_ns != final.st_ctime_ns
                or _identity(final) != _identity(current) or len(payload) != initial.st_size):
            raise ContractError('BUNDLE_FILE_CHANGED')
    _unlinked(path); meter.check()
    return payload


def write_file(path, payload, meter):
    meter.disk += len(payload); meter.check(); _unlinked(path)
    with path.open('xb') as f:
        f.write(payload); f.flush(); os.fsync(f.fileno())
    meter.check()
    return {'file': path.name, 'bytes': len(payload), 'sha256': hashlib.sha256(payload).hexdigest()}


class IdentityIndex:
    """Disk-backed exact uniqueness/lineage index, not an unbounded Python set.

    Scratch contains original identifiers in a caller-private directory; it is
    removed on success or failure and never included in a published bundle.
    """
    def __init__(self, meter):
        root = os.environ.get('TMPDIR')
        if not root:
            raise ContractError('BUNDLE_SCRATCH_REQUIRED')
        root = Path(root); _unlinked(root)
        if not root.is_dir():
            raise ContractError('BUNDLE_SCRATCH_REQUIRED')
        meter.index = 32768; meter.check()  # Reserve initial SQLite pages first.
        fd, name = tempfile.mkstemp(prefix='d3-index-', suffix='.sqlite', dir=root)
        os.close(fd); self.path = Path(name); self.meter = meter
        self.db = None
        try:
            self.db = sqlite3.connect(self.path)
            self.db.execute('PRAGMA page_size=4096')
            self.db.execute('PRAGMA journal_mode=OFF')
            self.db.execute('PRAGMA cache_size=-1024')
            self.db.execute('PRAGMA temp_store=FILE')
            self.db.execute('CREATE TABLE ids(kind TEXT, id TEXT, PRIMARY KEY(kind,id)) WITHOUT ROWID')
            self.db.execute('CREATE TABLE refs(id TEXT PRIMARY KEY) WITHOUT ROWID')
        except Exception:
            if self.db is not None: self.db.close()
            self.path.unlink(missing_ok=True); meter.index = 0
            raise

    def _reserve(self, *values):
        pages = self.db.execute('PRAGMA page_count').fetchone()[0]
        # One bounded B-tree insertion: reserve overflow bytes plus split pages
        # BEFORE sqlite may grow the scratch file. Conservative caps are allowed.
        self.meter.index = pages*4096 + 32768 + sum(len(v.encode('utf-8')) for v in values)*2
        self.meter.check()

    def add(self, kind, value):
        self._reserve(kind, value)
        try:
            self.db.execute('INSERT INTO ids VALUES(?,?)', (kind, value))
        except sqlite3.IntegrityError:
            raise ContractError('BUNDLE_DUPLICATE_ID') from None

    def ref(self, value):
        self._reserve(value)
        self.db.execute('INSERT OR IGNORE INTO refs VALUES(?)', (value,))

    def check(self):
        self.meter.index = max(self.path.stat().st_size, self.db.execute('PRAGMA page_count').fetchone()[0]*4096)
        self.meter.check()

    def finish(self):
        self.check()
        if self.db.execute("SELECT 1 FROM refs r WHERE NOT EXISTS(SELECT 1 FROM ids i WHERE i.kind='atom' AND i.id=r.id) LIMIT 1").fetchone():
            raise ContractError('BUNDLE_UPSTREAM_MISSING')

    def close(self):
        self.db.close(); self.path.unlink(missing_ok=True); self.meter.index = 0


@contextmanager
def identity_index(meter):
    index = IdentityIndex(meter)
    try:
        yield index
    finally:
        index.close()
