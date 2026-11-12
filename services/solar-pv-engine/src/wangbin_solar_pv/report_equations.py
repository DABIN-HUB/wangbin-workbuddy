"""Convert frozen formula definitions to editable OMML without changing their registry.

Pandoc is an external, deterministic document converter. Missing or malformed
math fails the export closed; plain text and images are never substitutes.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import os
import shutil
import subprocess
import tempfile

from docx import Document
from docx.oxml.ns import qn

from .errors import ContractError

# Per-ID *display* notation where the frozen text uses multi-letter subscripts
# without TeX grouping. Never mutate the catalog's latex/text_equation.
DISPLAY_LATEX = {
    # The n-ary operator must own the *whole* summand/product, not the first
    # glyph of a multi-letter quantity. These are fixed, reviewed display
    # identities, not token-wide regex transformations of the frozen registry.
    "F-AC-CAPACITY": r"P_{AC}=\sum_{j\in\mathcal J}P_{inv,j}",
    "F-POA-IRRADIATION": r"H_{POA,y}=\sum_{t\in\mathcal T_y}\left(G_{POA,t}\Delta t_t\right)",
    "F-LOSS-COMPOSITE": r"K_{loss}=\prod_{k\in\mathcal K}\left(1-l_k\right)",
    "F-ENERGY-AGGREGATION": r"E_{b,p}=\sum_{t\in\mathcal T_p}E_{b,t}",
    "F-DELIVERED-ENERGY": r"E_{delivered,y}=\sum_{t\in\mathcal T_y}\left(E_{self,t}+E_{export,t}\right)",
    "F-SELF-CONSUMPTION-RATIO": r"S_y=\frac{\sum_{t\in\mathcal T_y}E_{self,t}}{E_{delivered,y}}",
    "F-LOAD-COVERAGE-RATIO": r"A_y=\frac{\sum_{t\in\mathcal T_y}E_{self,t}}{\sum_{t\in\mathcal T_y}L_t}",
    "F-ENERGY-REVENUE": r"R_y=\sum_{t\in\mathcal T_y}\left(E_{self,t}p_{avoid,t}+E_{export,t}p_{sell,t}\right)+R_{other,y}",
    "F-PPA-REVENUE": r"R_{PPA,y}=\sum_{t\in\mathcal T_y}\left(E_{host,t}p_{PPA,t}+E_{export,t}p_{sell,t}\right)+R_{other,y}",
    "F-CAPEX-TOTAL": r"\mathrm{CAPEX}=\sum_{i\in\mathcal I}C_i",
    "F-ANNUAL-OPEX": r"O_y=\sum_{k\in\mathcal O_y}O_{k,y}",
    "F-OPEX-ESCALATION": r"O_{k,y}=O_{k,base}\prod_{a=1}^{y}\left(1+\pi_{k,a}\right)",
    "F-OTHER-CASH-TAXES": r"T_{other,b,y}=\sum_{k\in\mathcal Q_{b,y}}T_{k,b,y}",
    "F-DEBT-INTEREST": r"I_y=\sum_{s\in\mathcal S_y}\left(B_{D,s}i_s\delta_s\right)",
    "F-NPV": r"\mathrm{NPV}_b(r_b)=\sum_{y=0}^{N}\frac{CF_{b,y}}{(1+r_b)^y}",
    "F-DATED-NPV": r"\mathrm{NPV}_b=\sum_{k\in\mathcal C}\frac{CF_{b,k}}{(1+r_b)^{\tau_k}}",
    "F-IRR-PROJECT": r"\mathcal R_P=\{r\in\mathcal D:\sum_{y=0}^{N}\frac{CF_{P,y}}{(1+r)^y}=0\}",
    "F-IRR-EQUITY": r"\mathcal R_E=\{r\in\mathcal D:\sum_{y=0}^{N}\frac{CF_{E,y}}{(1+r)^y}=0\}",
    "F-CUMULATIVE-CASH-FLOW": r"A_{b,n}=\sum_{y=0}^{n}\left(CF_{b,y}\right)",
    "F-DISCOUNTED-CUMULATIVE-CASH": r"A^d_{b,n}=\sum_{y=0}^{n}\frac{CF_{b,y}}{(1+r_b)^y}",
    "F-LCOE": r"\mathrm{LCOE}=\frac{\sum_{y=0}^{N}\frac{Cost_{P,y}}{(1+r_L)^y}}{\sum_{y=0}^{N}\frac{E_{delivered,y}}{(1+r_L)^y}}",
    "F-CAPEX-PAYMENT-BALANCE": r"\epsilon_K=\sum_{y\in\mathcal Y_K}K_y+AP_{end}-AP_{start}-CAPEX_{payable}",
    "F-UNIT-KW-MW": r"P_{\mathrm{MW}}=\frac{P_{\mathrm{kW}}}{s}",
    "F-UNIT-KWH-MWH": r"E_{\mathrm{MWh}}=\frac{E_{\mathrm{kWh}}}{s}",
    "F-UNIT-IRRADIANCE-W-KW": r"G_{\mathrm{kW}}=\frac{G_{\mathrm{W}}}{s}",
    "F-UNIT-DC-CAPACITY": r"P_{\mathrm{MWp}}=\frac{P_{\mathrm{kWp}}}{s}",
    "F-UNIT-AC-CAPACITY": r"P_{\mathrm{MWac}}=\frac{P_{\mathrm{kWac}}}{s}",
    "F-STORAGE-ENERGY-UPDATE": r"B_{t+1}=B_t+\eta_{\mathrm{ch}}E_{\mathrm{ch},t}-\frac{E_{\mathrm{dis},t}}{\eta_{\mathrm{dis}}}-E_{\mathrm{sd},t}-E_{\mathrm{aux},t}",
    "F-STORAGE-SOC": r"\mathrm{SOC}_t=\frac{B_t}{C_{\mathrm{use},t}}",
    "F-STORAGE-CHARGE-LIMIT": r"E_{\mathrm{ch,max},t}=P_{\mathrm{ch,max},t}\,\delta_t",
    "F-STORAGE-DISCHARGE-LIMIT": r"E_{\mathrm{dis,max},t}=P_{\mathrm{dis,max},t}\,\delta_t",
    "F-STORAGE-PV-BALANCE": r"E_{\mathrm{pv},t}=E_{\mathrm{direct},t}+E_{\mathrm{pv,ch},t}+E_{\mathrm{pv,exp},t}+E_{\mathrm{curt},t}",
    "F-STORAGE-LOAD-BALANCE": r"L_t=E_{\mathrm{direct},t}+E_{\mathrm{bat,load},t}+E_{\mathrm{grid,load},t}",
    "F-STORAGE-CYCLE-COUNT": r"n_{\mathrm{eq}}=\frac{\sum_{t\in T}E_{\mathrm{dis,internal},t}}{C_{\mathrm{ref}}}",
    "F-USABLE-AREA": r"A_{\mathrm{use}}=A_{\mathrm{total}}-\sum_i A_{\mathrm{excl},i}",
    "F-AVERAGE-ANNUAL-ENERGY": r"E_{\mathrm{mean}}=\frac{\sum_{y=1}^{N}E_y}{N}",
    "F-EMISSIONS-AVOIDED": r"M_{\mathrm{avoided},y}=E_{\mathrm{eligible},y}\,\mathrm{EF}_{\mathrm{grid},y}",
    "F-TRANSFORMER-ACTIVE-LIMIT": r"P_{\mathrm{tr}}=S_{\mathrm{tr}}\,\mathrm{PF}",
    "F-CAPEX-ITEM-AMOUNT": r"C_i=q_i\,u_i",
    # Frozen latex contradicts text_equation and unit definitions. The Word
    # view follows the stated text definition; original *both* forms remain
    # visible below it and FORMULA_MATH_SEMANTICS must remain PARTIAL pending
    # method-owner adjudication, never silently count this as an exact match.
    "F-UNIT-COST-WP-KWP": r"c_{\mathrm{kWp}}=c_{\mathrm{Wp}}\times s",
}
CONFLICT_ID = "F-UNIT-COST-WP-KWP"


def pandoc_executable() -> str:
    executable = os.environ.get("WANGBIN_SOLAR_PV_PANDOC") or shutil.which("pandoc")
    if not executable or not Path(executable).is_file():
        raise ContractError("REPORT_OMML_CONVERTER_UNAVAILABLE")
    return str(executable)


def convert_equations(definitions: list[dict], *, formula_ids=None) -> dict[str, object]:
    """Return one detached OMML node per formal ID; fail closed on any mismatch."""
    ids = [row["formula_id"] for row in definitions]
    if len(ids) != len(set(ids)) or len(ids) != 89:
        raise ContractError("REPORT_OMML_FORMULA_IDENTITY")
    if not set(DISPLAY_LATEX) <= set(ids):
        raise ContractError("REPORT_OMML_DISPLAY_MAPPING_UNKNOWN_ID")
    if formula_ids is not None:
        if not set(formula_ids) <= set(ids):
            raise ContractError("REPORT_OMML_FORMULA_IDENTITY")
        definitions = [row for row in definitions if row['formula_id'] in formula_ids]
        ids = [row['formula_id'] for row in definitions]
        if not ids:
            return {}
    lines: list[str] = []
    for row in definitions:
        expression = DISPLAY_LATEX.get(row["formula_id"], row.get("latex"))
        if not isinstance(expression, str) or not expression.strip() or "$$" in expression:
            raise ContractError("REPORT_OMML_FORMULA_MISSING", row["formula_id"])
        lines.extend((row["formula_id"], "", "$$", expression, "$$", ""))
    with tempfile.TemporaryDirectory(prefix="solar-omml-", dir=os.environ.get("TMPDIR")) as scratch:
        target = Path(scratch) / "math.docx"
        try:
            proc = subprocess.run(
                [pandoc_executable(), "--from=markdown+tex_math_dollars", "--to=docx", "--output", str(target)],
                input="\n".join(lines), text=True, encoding="utf-8", capture_output=True,
                timeout=120, check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ContractError("REPORT_OMML_CONVERTER_FAILED") from exc
        if proc.returncode or not target.is_file() or proc.stderr.strip():
            raise ContractError("REPORT_OMML_CONVERTER_FAILED", proc.stderr[:200])
        paragraphs = Document(target).paragraphs
        if len(paragraphs) != len(ids) * 2:
            raise ContractError("REPORT_OMML_OBJECT_COUNT")
        nodes = {}
        for i, fid in enumerate(ids):
            marker, equation = paragraphs[2 * i : 2 * i + 2]
            math = equation._p.xpath("./m:oMathPara/m:oMath")
            if marker.text != fid or len(math) != 1 or equation.text.strip():
                raise ContractError("REPORT_OMML_FORMULA_IDENTITY", fid)
            node = deepcopy(math[0])
            if not any(token.text for token in node.iter(qn("m:t"))):
                raise ContractError("REPORT_OMML_EMPTY_FORMULA", fid)
            nodes[fid] = node
        return nodes
