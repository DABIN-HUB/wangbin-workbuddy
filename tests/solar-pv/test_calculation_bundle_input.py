"""SYNTHETIC D2/D3 integration, not project energy or finance acceptance."""
import pytest

from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.calculation.input_contract import validate_export, calculation_identity
from wangbin_solar_pv.calculation.method_config import MethodConfig
from wangbin_solar_pv.timeseries_bundle import BundleBudget, write_bundle, read_bundle
from test_timeseries_bundle import base, header, rows


def config():
    return MethodConfig.from_dict({"schema_version": "solar-pv-method-config/1.0.0", "config_id": "SYNTHETIC", "data_mode": "SYNTHETIC", "pv_types": ["industrial_rooftop"], "parameters": {}})


def test_dataset_identity_rejects_unvalidated_mapping():
    catalog = Catalog()
    with pytest.raises(ContractError, match="CALCULATION_DATASET_NOT_VALIDATED"):
        calculation_identity(validate_export(base(catalog), catalog), config(), catalog, datasets={"load.series": {"content_hash": "0" * 64}})


def test_bundle_content_and_original_provenance_enter_identity_not_chunk_layout(tmp_path):
    catalog = Catalog()
    exported = base(catalog)
    validated = validate_export(exported, catalog)
    data = {"load.series": {"header": header(catalog), "rows": list(rows(catalog))}}
    budget = BundleBudget()
    identities = []
    for chunk_size in (1, 2):
        target = tmp_path / str(chunk_size)
        write_bundle(target, base_export=exported, datasets=data, catalog=catalog, budget=budget, rows_per_chunk=chunk_size)
        with read_bundle(target, catalog=catalog, budget=budget) as bundle:
            identity = calculation_identity(validated, config(), catalog, datasets=bundle)
            identities.append(identity)
            assert identity["source_snapshot"]["datasets"]["datasets"]["load.series"]["header"] == data["load.series"]["header"]
            assert identity["phase2_input_hash"] == exported["input_hash"]
        with pytest.raises(ContractError):
            calculation_identity(validated, config(), catalog, datasets=bundle)
    assert identities[0] == identities[1]
