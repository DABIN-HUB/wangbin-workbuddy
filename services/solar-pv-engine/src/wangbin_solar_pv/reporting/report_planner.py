"""Deterministic research order, independent of final Word order."""
from ..errors import ContractError


def plan(registry):
    seen, tasks = set(), []
    for cid in registry.spec["generation_order"]:
        ch = registry.chapter(cid)
        if not set(ch["dependencies"]) <= seen or cid in seen:
            raise ContractError("CHAPTER_DEPENDENCY_ORDER")
        tasks.append({"chapter_id": cid, "dependencies": ch["dependencies"],
                      "section_ids": [s["section_id"] for s in ch["sections"]]})
        seen.add(cid)
    if len(tasks) != 18 or tasks[-1]["chapter_id"] != "CH01":
        raise ContractError("CHAPTER_PLAN_COVERAGE")
    return {"tasks": tasks, "execution_gate": "PILOT_USER_REVIEW_REQUIRED_BEFORE_FULL_GENERATION"}
