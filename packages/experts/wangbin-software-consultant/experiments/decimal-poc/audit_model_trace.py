"""Reduce raw Hermes JSONL to provenance facts without copying private traces into Git."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(path):
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    calls = {e.get("tool_call_id"): e for e in events if e.get("type") == "tool_use"}
    tools = []
    for event in events:
        if event.get("type") != "tool_result":
            continue
        use = calls.get(event.get("tool_call_id"), {})
        if use.get("name") != "terminal":
            continue
        raw = event.get("output", "")
        try:
            result = json.loads(raw)
        except (ValueError, TypeError):
            result = {"output": str(raw)}
        tools.append({"command": use.get("input", {}).get("command"),
                      "rc": result.get("exit_code"), "stdout_or_error": str(result.get("output", ""))[:1000],
                      "blocked": result.get("status") == "blocked"})
    result = next((e for e in reversed(events) if e.get("type") == "result"), {})
    return {"trace": str(path), "trace_sha256": sha(path), "session_id": result.get("session_id"),
            "model_rc": result.get("exit_code"), "model_error": result.get("error"),
            "tool_selections": [e.get("name") for e in events if e.get("type") == "tool_use"],
            "terminal_calls": tools, "final_answer": result.get("text", ""),
            "response_sha256": hashlib.sha256(result.get("text", "").encode("utf-8")).hexdigest()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("traces", type=Path, nargs="+")
    args = parser.parse_args()
    for trace in args.traces:
        print(json.dumps(audit(trace), ensure_ascii=False))
