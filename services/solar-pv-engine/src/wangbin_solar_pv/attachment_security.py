"""Private Phase2 attachment boundary, not an OS sandbox.

Reuse SecurityPolicy's public path/signature/container checks on the private
snapshot. CSV has its own bounded path/read because the legacy allowlist excludes
CSV. The original is opened once; no safety scanner reopens the original path.
No change to legacy security guarantees is implied.
"""
from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import stat
import tempfile
import time

from wangbin_document_engine.security import SecurityPolicy


class AttachmentError(Exception):
    def __init__(self, code, status="BLOCKED"):
        self.code = code
        self.status = status
        super().__init__(code)


def reject(code, status="BLOCKED"):
    raise AttachmentError(code, status)


def _unlinked(path):
    for part in (path, *path.parents):
        if part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()):
            reject("LINK_INPUT")
        try:
            if getattr(part.lstat(), "st_file_attributes", 0) & 0x400:
                reject("REPARSE_INPUT")
        except FileNotFoundError:
            pass


def _identity(info):
    # Windows Python 3.12 exposes different ctime semantics for stat/fstat;
    # compare inode/device/size/mtime across APIs, ctime only fd-to-fd below.
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns)


@contextmanager
def stable_snapshot(path, input_root, work_root, policy):
    """Bounded single-handle copy, including hardlink and root-link rejection.

    Uses an explicit work_root, otherwise TMPDIR (Hermes scratch), never the
    operating system's implicit temporary-directory fallback.
    """
    root = Path(os.path.abspath(Path(input_root).expanduser()))
    source = Path(os.path.abspath(Path(path).expanduser()))
    if ".." in Path(path).parts or ".." in Path(input_root).parts:
        reject("PATH_TRAVERSAL")
    _unlinked(root)
    _unlinked(source)
    if not root.is_dir():
        reject("INPUT_ROOT_MISSING")
    if not source.is_relative_to(root) or not source.resolve().is_relative_to(root.resolve()):
        reject("PATH_OUTSIDE_ROOT")
    if source.suffix.lower() not in {".txt", ".md", ".csv", ".xlsx", ".docx", ".pdf"}:
        reject("UNSUPPORTED_FORMAT")
    before = source.lstat()
    if not stat.S_ISREG(before.st_mode):
        reject("NOT_REGULAR_FILE")
    if before.st_nlink != 1:
        reject("HARDLINK_INPUT")
    if before.st_size > policy.max_file_bytes:
        reject("FILE_TOO_LARGE")
    workspace = work_root or os.environ.get("TMPDIR")
    if not workspace:
        reject("WORK_ROOT_REQUIRED")
    workspace = Path(os.path.abspath(workspace))
    _unlinked(workspace)
    workspace.mkdir(parents=True, exist_ok=True)
    _unlinked(workspace)
    deadline = time.monotonic() + policy.timeout_seconds
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    with os.fdopen(os.open(source, flags), "rb") as stream:
        initial = os.fstat(stream.fileno())
        if _identity(initial) != _identity(before) or initial.st_nlink != 1:
            reject("INPUT_CHANGED")
        _unlinked(root)
        _unlinked(source)
        with tempfile.TemporaryDirectory(prefix="solar-pv-attachment-", dir=workspace) as private:
            staged = Path(private) / ("attachment" + source.suffix.lower())
            total = 0
            with staged.open("xb") as output:
                while chunk := stream.read(1024 * 1024):
                    total += len(chunk)
                    if total > policy.max_file_bytes:
                        reject("FILE_TOO_LARGE")
                    if time.monotonic() >= deadline:
                        reject("PARSER_TIMEOUT")
                    output.write(chunk)
            finished = os.fstat(stream.fileno())
            if (_identity(initial) != _identity(finished) or initial.st_ctime_ns != finished.st_ctime_ns
                    or _identity(initial) != _identity(source.lstat()) or finished.st_nlink != 1 or total != initial.st_size):
                reject("INPUT_CHANGED")
            _unlinked(root)
            _unlinked(source)
            yield staged


def inspect_snapshot(path, policy):
    """Apply public legacy checks, then private active-content checks to one copy."""
    if path.suffix != ".csv":
        policy.validate_input(path, path.parent)
    if path.suffix in {".docx", ".xlsx"}:
        _inspect_office(path, policy)
    elif path.suffix == ".pdf":
        _inspect_pdf(path, policy)


def formula_text(value):
    import re
    if not isinstance(value,str) or not value.lstrip().startswith(("=", "+", "-", "@")):
        return False
    # A bounded signed numeric literal is data, not a spreadsheet expression.
    return len(value.strip())>128 or re.fullmatch(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]{1,3})?",value.strip()) is None


def _inspect_office(path, policy):
    import zipfile
    from defusedxml import ElementTree
    from defusedxml.common import DefusedXmlException
    with zipfile.ZipFile(path) as archive:
        names = set()
        for info in archive.infolist():
            name = info.filename.replace("\\", "/").casefold()
            if name in names:
                reject("ZIP_DUPLICATE_MEMBER")
            names.add(name)
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode) or (mode and stat.S_IFMT(mode) not in {0, stat.S_IFREG, stat.S_IFDIR}):
                reject("ZIP_SPECIAL_MEMBER")
            if any(token in name for token in ("vbaproject", "vbadata", "/macrosheets/", "/embeddings/", "activex", "attachedtemplate")):
                reject("OFFICE_ACTIVE_CONTENT")
            if not (name.endswith(".xml") or name.endswith(".rels")):
                continue
            try:
                root = ElementTree.fromstring(archive.read(info), forbid_dtd=True, forbid_entities=True, forbid_external=True)
            except (DefusedXmlException, ElementTree.ParseError):
                reject("OFFICE_UNSAFE_XML")
            for node in root.iter():
                local = node.tag.rsplit("}", 1)[-1].casefold()
                if local in {"oleobject", "object", "attachedtemplate", "altchunk", "control", "instrtext", "fldsimple", "ddelink", "ddelinks", "olelink", "externalreference", "externalreferences"}:
                    reject("OFFICE_ACTIVE_CONTENT")
                if local == "relationship" and any(key.rsplit("}", 1)[-1].casefold() == "targetmode" and value.casefold() == "external" for key, value in node.attrib.items()):
                    reject("OFFICE_EXTERNAL_RELATIONSHIP")
                if any(token in value.casefold() for value in node.attrib.values() for token in ("macroenabled", "vbaproject", "macrosheet", "oleobject", "attachedtemplate")):
                    reject("OFFICE_ACTIVE_CONTENT")
                if path.suffix == ".xlsx":
                    if local == "f":
                        reject("FORMULA_INPUT")
                    if local == "c" and node.attrib.get("t") == "str":
                        if formula_text("".join(child.text or "" for child in node if child.tag.rsplit("}", 1)[-1] == "v")):
                            reject("FORMULA_INPUT")
                    if local in {"si", "is"}:
                        value = "".join(t.text or "" for t in node.iter() if t.tag.rsplit("}", 1)[-1] == "t")
                        if formula_text(value):
                            reject("FORMULA_INPUT")


def _inspect_pdf(path, policy):
    """Inspect decoded PDF objects/names, including compressed object streams.

    Byte substring checks are insufficient: literal strings are not actions,
    and name hex escapes/object compression must not hide active dictionaries.
    """
    import re
    from pdfminer.pdfparser import PDFParser
    from pdfminer.pdfdocument import PDFDocument, PDFObjectNotFound
    from pdfminer.pdftypes import PDFObjRef, PDFStream
    from pdfminer.psparser import PSLiteral

    def name(value):
        text = value.name if isinstance(value, PSLiteral) else value
        if isinstance(text, bytes):
            text = text.decode("latin1")
        if not isinstance(text, str):
            return ""
        return re.sub(r"#([0-9a-fA-F]{2})", lambda m: chr(int(m[1], 16)), text).casefold()

    forbidden = {"javascript", "js", "launch", "openaction", "aa", "embeddedfiles", "embeddedfile",
                 "filespec", "richmedia", "rendition", "submitform", "importdata", "gotor", "gotoe", "uri", "xfa"}
    with path.open("rb") as stream:
        document = PDFDocument(PDFParser(stream))
        if document.encryption:
            reject("PDF_ENCRYPTED")
        seen_refs, seen_objects = set(), set()
        stack = [(document.catalog, 0)]
        for xref in document.xrefs:
            for objid in xref.get_objids():
                if objid == 0 or objid in seen_refs:
                    continue
                seen_refs.add(objid)
                if len(seen_refs) > min(policy.max_zip_entries, 20000):
                    reject("PDF_OBJECT_LIMIT")
                try:
                    stack.append((document.getobj(objid), 0))
                except PDFObjectNotFound:
                    reject("PDF_BROKEN_REFERENCE", "FAILED")
        count = 0
        while stack:
            value, depth = stack.pop()
            count += 1
            if count > min(policy.max_spreadsheet_cells, 100000) or depth > 64:
                reject("PDF_STRUCTURE_LIMIT")
            if isinstance(value, PDFObjRef):
                if value.objid not in seen_refs:
                    seen_refs.add(value.objid)
                    stack.append((value.resolve(), depth + 1))
                continue
            if isinstance(value, PSLiteral):
                if name(value) in forbidden:
                    reject("PDF_ACTIVE_CONTENT")
                continue
            if not isinstance(value, (dict, list, tuple, PDFStream)):
                continue
            if id(value) in seen_objects:
                continue
            seen_objects.add(id(value))
            if isinstance(value, PDFStream):
                value = value.attrs
            if isinstance(value, dict):
                if any(name(key) in forbidden for key in value):
                    reject("PDF_ACTIVE_CONTENT")
                stack.extend((item, depth + 1) for item in value.values())
            else:
                stack.extend((item, depth + 1) for item in value)
