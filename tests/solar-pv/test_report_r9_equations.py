"""R9 guards for the frozen 89-formula registry and editable OMML structure."""
from __future__ import annotations

from docx.oxml.ns import qn

from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.report_equations import CONFLICT_ID, DISPLAY_LATEX, convert_equations


def test_all_formulas_have_distinct_editable_math_objects():
    catalog = Catalog()
    definitions = [catalog.formulas[fid] for fid in sorted(catalog.formulas)]
    before = [(row["formula_id"], row.get("latex"), row.get("text_equation")) for row in definitions]
    nodes = convert_equations(definitions)
    assert len(nodes) == len(definitions) == 89
    assert set(nodes) == {row["formula_id"] for row in definitions}
    assert all(node.tag == qn("m:oMath") and list(node.iter(qn("m:r"))) for node in nodes.values())
    assert before == [(row["formula_id"], row.get("latex"), row.get("text_equation")) for row in definitions]
    assert len(DISPLAY_LATEX) == 40 and CONFLICT_ID in DISPLAY_LATEX
    assert definitions[[row["formula_id"] for row in definitions].index(CONFLICT_ID)]["latex"] != DISPLAY_LATEX[CONFLICT_ID]

    token_text = lambda fid: "".join((node.text or "") for node in nodes[fid].iter(qn("m:t")))
    assert "η" in token_text("F-AC-INVERTER-POWER")
    assert "δ" in token_text("F-DEBT-INTEREST")
    assert list(nodes["F-DEBT-INTEREST"].iter(qn("m:nary")))
    assert list(nodes["F-ANNUAL-DEGRADATION"].iter(qn("m:sSup")))
    assert len(list(nodes["F-AVAILABLE-ENERGY"].iter(qn("m:sSub")))) >= 5
    assert list(nodes["F-UNIT-COST-WP-KWP"].iter(qn("m:sSub")))
    assert list(nodes["F-STORAGE-CYCLE-COUNT"].iter(qn("m:f")))
    for fid in ("F-NPV", "F-DATED-NPV", "F-DISCOUNTED-CUMULATIVE-CASH", "F-LCOE",
                "F-IRR-PROJECT", "F-IRR-EQUITY"):
        operators = list(nodes[fid].iter(qn("m:nary")))
        assert operators
        assert any(list(op.find(qn("m:e")).iter(qn("m:f"))) for op in operators)
    for fid, expected_operand in (("F-CUMULATIVE-CASH-FLOW", "CFb,y"),
                                  ("F-LOSS-COMPOSITE", "1−lk"),
                                  ("F-OPEX-ESCALATION", "1+πk,a")):
        operator = next(nodes[fid].iter(qn("m:nary")))
        assert "".join((run.text or "") for run in operator.find(qn("m:e")).iter(qn("m:t"))) == expected_operand
    assert len(list(nodes["F-LCOE"].iter(qn("m:f")))) >= 3
