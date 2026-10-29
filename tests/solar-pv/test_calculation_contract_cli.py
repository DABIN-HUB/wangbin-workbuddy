"""SYNTHETIC local CLI coverage for actual Phase3A contract artifacts."""
from pathlib import Path

import pytest

from wangbin_solar_pv.cli import main
from wangbin_solar_pv.serialization import loads


@pytest.mark.parametrize("command,version", [("calculation-schema", "solar-pv-calculation-result/1.0.0"), ("method-schema", "solar-pv-method-config/1.0.0")])
def test_contract_cli_writes_real_private_schema_without_numeric_success_claim(tmp_path, capsys, command, version):
    assert main(["--workspace", str(tmp_path), command, "--output", "schema.json"]) == 0
    schema = loads((tmp_path / "schema.json").read_bytes())
    assert schema["$id"] == version
    summary = loads(capsys.readouterr().out)
    assert summary["status"] == "CONTRACT_EXPORTED"
    assert summary["numerical_validation"] == "NOT_PERFORMED_BY_THIS_COMMAND"
    assert main(["--workspace", str(tmp_path), command, "--output", "schema.json"]) == 2


def test_execution_inventory_cli_keeps_storage_unimplemented_and_reports_real_status(tmp_path, capsys):
    assert main(["--workspace", str(tmp_path), "calculation-formulas", "--output", "inventory.json"]) == 0
    data = loads((tmp_path / "inventory.json").read_bytes())
    assert len(data["formulas"]) == 89
    assert sum(row["phase3_applicable"] for row in data["formulas"]) == 82
    assert all(row["executor"] is None and row["status"] == "NOT_IMPLEMENTED" for row in data["formulas"] if not row["phase3_applicable"])
    summary = loads(capsys.readouterr().out)
    assert summary["formula_count"] == 89
    assert summary["scope"] == "EVIDENCE_BACKED_REGISTRY_NOT_PROJECT_COMPUTATION"
