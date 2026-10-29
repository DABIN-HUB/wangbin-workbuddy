"""SYNTHETIC contract-only regressions for independent Phase 3A review findings."""
from copy import deepcopy
from decimal import Decimal

import pytest
from wangbin_solar_pv.catalog import Catalog
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.calculation.result_contract import empty_result, seal_result, validate_result, serialize_result, deserialize_result
from wangbin_solar_pv.calculation.execution_registry import execution_inventory, run_formula
from wangbin_solar_pv.calculation.method_config import MethodConfig, make_parameter
from wangbin_solar_pv.serialization import digest


def result_with_metric(catalog):
    result = empty_result(project_id='SYNTHETIC-SCHEMA-ONLY', pv_type='industrial_rooftop', evaluation_date='2026-01-01', currency='CNY', scenario_id='SYNTHETIC', input_hash='SYNTHETIC-NONEXECUTED', source_snapshot_id='SYNTHETIC-NONEXECUTED', baseline_hashes=catalog.baseline_hashes, definition_version=catalog.definition_version, definition_hash=catalog.definition_hash)
    result['status'] = 'PARTIAL'
    result['maturity']['calculation'] = 'PARTIAL'
    result['boundaries'] = {'SYNTHETIC-BOUNDARY': {'meaning': 'SYNTHETIC contract fixture only'}}
    result['source_snapshot'] = {'phase2': {'records': [{'source_id': 'SYNTHETIC-SOURCE'}]}, 'methods': {'parameters': {}}}
    result['source_snapshot_id'] = digest(result['source_snapshot'])
    identity = {'source_snapshot_id': result['source_snapshot_id']}
    result['inputs']['identity_payload'] = identity
    result['input_hash'] = digest(identity)
    result['evidence'] = {'SYNTHETIC-EVIDENCE': {'scope': 'SCHEMA ONLY NOT NUMERICAL VERIFICATION'}}
    result['results']['metrics'] = [{'metric_id': 'SYNTHETIC-METRIC', 'value': Decimal(1), 'unit': 'm2', 'status': 'CALCULATED', 'reason': None, 'boundary_id': 'SYNTHETIC-BOUNDARY', 'period': 'SYNTHETIC', 'scenario_id': 'SYNTHETIC', 'input_field_ids': [], 'source_ids': ['SYNTHETIC-SOURCE'], 'formula_id': 'F-USABLE-AREA', 'formula_version': catalog.definition_version, 'evidence_ids': ['SYNTHETIC-EVIDENCE'], 'report_locations': [], 'workbook_locations': [], 'rounding_rule': 'SYNTHETIC schema-only fixture'}]
    return seal_result(result)


def test_partial_numeric_result_must_validate_source_and_input_identity():
    catalog = Catalog()
    result = result_with_metric(catalog)
    result['source_snapshot_id'] = 'SYNTHETIC-FORGED'
    with pytest.raises(ContractError, match='RESULT_SOURCE_IDENTITY'):
        validate_result(seal_result(result), catalog)


@pytest.mark.parametrize('key,value', [('source_ids', ['SYNTHETIC-ABSENT']), ('evidence_ids', ['SYNTHETIC-ABSENT']), ('boundary_id', 'SYNTHETIC-ABSENT'), ('method_parameter_ids', ['SYNTHETIC-ABSENT'])])
def test_result_rejects_dangling_metric_trace_references(key, value):
    catalog = Catalog()
    result = result_with_metric(catalog)
    result['results']['metrics'][0][key] = value
    with pytest.raises(ContractError, match='METRIC_.*REFERENCE'):
        validate_result(seal_result(result), catalog)


@pytest.mark.parametrize('entry', ['inventory', 'run', 'result'])
def test_all_formula_consumers_reject_catalog_definition_drift(entry):
    catalog = Catalog()
    result = result_with_metric(catalog)
    catalog.formulas['F-USABLE-AREA']['text_equation'] += ' SYNTHETIC-TAMPER'
    with pytest.raises(ContractError, match='DEFINITION_IDENTITY_DRIFT'):
        if entry == 'inventory':
            execution_inventory(catalog)
        elif entry == 'run':
            run_formula('F-USABLE-AREA', {}, catalog=catalog)
        else:
            validate_result(result, catalog)


def test_new_method_contract_rejects_binary_float_before_hashing():
    p = make_parameter('precision.abs_tolerance', 1e-5, source_id='SYNTHETIC', source_reference='SYNTHETIC', status='ASSUMED', source_kind='SYNTHETIC')
    with pytest.raises(ContractError, match='EXACT_JSON_NUMBER_REQUIRED'):
        MethodConfig.from_dict({'schema_version': 'solar-pv-method-config/1.0.0', 'config_id': 'SYNTHETIC', 'data_mode': 'SYNTHETIC', 'pv_types': ['industrial_rooftop'], 'parameters': {'precision.abs_tolerance': p}})


def test_new_result_contract_rejects_binary_float_before_hashing():
    result = result_with_metric(Catalog())
    result['results']['metrics'][0]['value'] = 1e-5
    with pytest.raises(ContractError, match='EXACT_JSON_NUMBER_REQUIRED'):
        seal_result(result)


def test_declared_trace_references_are_accepted_for_schema_only_partial_result():
    catalog = Catalog()
    result = result_with_metric(catalog)
    assert validate_result(result, catalog) == result


@pytest.mark.parametrize('entry', ['method', 'result'])
def test_integer_token_negative_zero_is_explicitly_rejected(entry):
    if entry == 'method':
        parameter = make_parameter('energy.pr', Decimal('-0'), source_id='SYNTHETIC', source_reference='SYNTHETIC', status='ASSUMED', source_kind='SYNTHETIC')
        with pytest.raises(ContractError, match='NONCANONICAL_NEGATIVE_ZERO'):
            MethodConfig.from_dict({'schema_version': 'solar-pv-method-config/1.0.0', 'config_id': 'SYNTHETIC', 'data_mode': 'SYNTHETIC', 'pv_types': ['industrial_rooftop'], 'parameters': {'energy.pr': parameter}})
    else:
        result = result_with_metric(Catalog())
        result['results']['metrics'][0]['value'] = Decimal('-0')
        with pytest.raises(ContractError, match='NONCANONICAL_NEGATIVE_ZERO'):
            seal_result(result)


@pytest.mark.parametrize('token', ['0', '0.0', '-0.0', '-0E+3', '1E-5', '1.00'])
def test_accepted_exact_numeric_tokens_preserve_result_hash_after_json_roundtrip(token):
    catalog = Catalog()
    result = result_with_metric(catalog)
    result['results']['metrics'][0]['value'] = Decimal(token)
    result = seal_result(result)
    reread = deserialize_result(serialize_result(result, catalog), catalog)
    assert reread['result_hash'] == result['result_hash']


@pytest.mark.parametrize('fault,code', [('input_hash', 'RESULT_INPUT_IDENTITY'), ('input_source', 'RESULT_INPUT_SOURCE_IDENTITY')])
def test_partial_numeric_result_also_checks_input_hash_and_input_source_link(fault, code):
    catalog = Catalog()
    result = result_with_metric(catalog)
    if fault == 'input_hash':
        result['input_hash'] = 'SYNTHETIC-FORGED'
    else:
        result['inputs']['identity_payload']['source_snapshot_id'] = 'SYNTHETIC-FORGED'
        result['input_hash'] = digest(result['inputs']['identity_payload'])
    with pytest.raises(ContractError, match=code):
        validate_result(seal_result(result), catalog)
