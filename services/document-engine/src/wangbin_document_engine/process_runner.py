"""Run document parsers in a disposable child process.

The parent process owns the timeout and always joins/terminates the child. On
POSIX, the child additionally receives CPU and virtual-memory rlimits. Windows
has reliable wall-clock termination here, but does not claim OS-level CPU or
memory enforcement.
"""
from __future__ import annotations

import json
import multiprocessing
import os
import time
from dataclasses import asdict
from multiprocessing.connection import Connection
from pathlib import Path


from .errors import EngineError
from .markitdown_adapter import MarkItDownAdapter
from .models import ParsedDocument

_MAX_RESULT_BYTES = 32 * 1024 * 1024
_ERROR_MESSAGES = {
    "PARSER_RESOURCE_LIMIT": "文档解析超过内存限制",
    "PARSER_OUTPUT_TOO_LARGE": "文档解析结果超过大小限制",
    "PARSER_ERROR": "文档解析失败，详细异常已脱敏",
}


def _send_result(sender: Connection, result: dict[str, object]) -> None:
    payload = json.dumps(result, ensure_ascii=False, default=str).encode("utf-8")
    if len(payload) > _MAX_RESULT_BYTES:
        payload = json.dumps({"status": "error", "code": "PARSER_OUTPUT_TOO_LARGE"}).encode("utf-8")
    sender.send_bytes(payload)


def _apply_posix_limits(max_cpu_seconds: int, max_memory_bytes: int) -> None:
    if os.name == "nt":
        return
    try:
        import resource
    except ImportError:
        return
    cpu_limit = max(1, int(max_cpu_seconds))
    current_cpu = resource.getrlimit(resource.RLIMIT_CPU)
    hard_cpu = current_cpu[1]
    if hard_cpu == resource.RLIM_INFINITY or cpu_limit < hard_cpu:
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, min(cpu_limit + 1, hard_cpu) if hard_cpu != resource.RLIM_INFINITY else cpu_limit + 1))
    current_memory = resource.getrlimit(resource.RLIMIT_AS)
    hard_memory = current_memory[1]
    if hard_memory == resource.RLIM_INFINITY or max_memory_bytes < hard_memory:
        resource.setrlimit(resource.RLIMIT_AS, (max_memory_bytes, min(max_memory_bytes, hard_memory) if hard_memory != resource.RLIM_INFINITY else max_memory_bytes))


def _worker(path: str, sender: Connection, max_cpu_seconds: int, max_memory_bytes: int) -> None:
    try:
        _apply_posix_limits(max_cpu_seconds, max_memory_bytes)
        parsed = MarkItDownAdapter().convert(Path(path))
        _send_result(sender, {"status": "ok", "value": asdict(parsed)})
    except MemoryError:
        _send_result(sender, {"status": "error", "code": "PARSER_RESOURCE_LIMIT"})
    except Exception:
        _send_result(sender, {"status": "error", "code": "PARSER_ERROR"})
    finally:
        sender.close()


def convert_in_process(path: Path, timeout_seconds: float, max_cpu_seconds: int, max_memory_bytes: int) -> ParsedDocument:
    """Convert one document and enforce a real parent-side wall-clock limit."""
    context = multiprocessing.get_context("spawn")
    receiver, sender = context.Pipe(duplex=False)
    process = context.Process(target=_worker, args=(str(path), sender, max_cpu_seconds, max_memory_bytes), daemon=True)
    try:
        process.start()
    except (OSError, RuntimeError) as exc:
        receiver.close()
        sender.close()
        raise EngineError("PARSER_PROCESS_FAILED", "文档解析子进程无法启动") from exc
    sender.close()
    try:
        deadline = time.monotonic() + timeout_seconds
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                process.terminate()
                process.join(timeout=5)
                if process.is_alive():
                    process.kill()
                    process.join(timeout=5)
                raise EngineError("PARSER_TIMEOUT", "文档解析超过时间限制，解析进程已终止")
            if receiver.poll(min(0.1, remaining)):
                result = json.loads(receiver.recv_bytes(maxlength=_MAX_RESULT_BYTES).decode("utf-8"))
                break
            if not process.is_alive():
                process.join(timeout=5)
                raise EngineError("PARSER_RESOURCE_LIMIT", "文档解析子进程被系统资源限制终止")
    except (EOFError, OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        process.join(timeout=5)
        code = "PARSER_RESOURCE_LIMIT" if process.exitcode not in (0, None) else "PARSER_PROCESS_FAILED"
        raise EngineError(code, "文档解析子进程异常退出") from exc
    finally:
        receiver.close()
        if process.is_alive():
            process.join(timeout=5)
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
    if not isinstance(result, dict):
        raise EngineError("PARSER_PROCESS_FAILED", "文档解析子进程返回无效结果")
    if result.get("status") == "ok":
        value = result.get("value")
        if (not isinstance(value, dict) or not isinstance(value.get("text"), str)
                or value.get("title") is not None and not isinstance(value.get("title"), str)
                or not isinstance(value.get("metadata"), dict)
                or not isinstance(value.get("quality_notes"), list)
                or not all(isinstance(note, str) for note in value["quality_notes"])):
            raise EngineError("PARSER_PROCESS_FAILED", "文档解析子进程返回无效结果")
        return ParsedDocument(value["text"], value.get("title"), value["metadata"], value["quality_notes"])
    code = result.get("code")
    if result.get("status") != "error" or code not in _ERROR_MESSAGES:
        raise EngineError("PARSER_PROCESS_FAILED", "文档解析子进程返回无效结果")
    raise EngineError(code, _ERROR_MESSAGES[code])
