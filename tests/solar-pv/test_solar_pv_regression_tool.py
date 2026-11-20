"""Focused evidence-tool contracts; no production financial calculation changes."""
from pathlib import Path

import pytest

from tooling.solar_pv_regression import GateError, _junit
from tooling.solar_pv_l3_sharded import _collect_ids, _select


def _xml(path: Path, cases: str, *, tests: int, failures: int = 0,
         errors: int = 0, skipped: int = 0) -> Path:
    path.write_text(
        f'<testsuites tests="{tests}" failures="{failures}" errors="{errors}" skipped="{skipped}">'
        f'<testsuite tests="{tests}" failures="{failures}" errors="{errors}" skipped="{skipped}">'
        f'{cases}</testsuite></testsuites>', encoding='utf-8')
    return path


def test_multiple_same_kind_failures_keep_each_trace_and_one_case(tmp_path):
    xml = _xml(tmp_path / 'result.xml',
               '<testcase classname="tests.solar-pv.test_x" name="test_multi">'
               '<failure message="first" type="AssertionError">first trace</failure>'
               '<failure message="second" type="AssertionError">second trace</failure>'
               '</testcase>', tests=2, failures=2)
    parsed = _junit(xml)
    assert parsed['counts'] == {'passed': 0, 'skipped': 0, 'failure': 1, 'error': 0}
    assert parsed['element_counts'] == {'failure': 2, 'error': 0, 'skipped': 0}
    assert parsed['unrepresented_tests'] == 1
    assert parsed['cases']['tests.solar-pv.test_x::test_multi']['outcomes'] == [
        {'tag': 'failure', 'message': 'first', 'type': 'AssertionError', 'text': 'first trace'},
        {'tag': 'failure', 'message': 'second', 'type': 'AssertionError', 'text': 'second trace'},
    ]


@pytest.mark.parametrize('children,failures,errors,skipped', [
    ('<failure/><error/>', 1, 1, 0),
    ('<failure/><skipped/>', 1, 0, 1),
    ('<error/><error/>', 0, 2, 0),
])
def test_incompatible_outcome_combinations_rejected(tmp_path, children, failures, errors, skipped):
    xml = _xml(tmp_path / 'mixed.xml',
               f'<testcase classname="tests.solar-pv.test_x" name="test_case">{children}</testcase>',
               tests=2, failures=failures, errors=errors, skipped=skipped)
    with pytest.raises(GateError, match='incompatible JUnit outcomes'):
        _junit(xml)


def test_wrong_element_total_and_duplicate_normalized_ids_rejected(tmp_path):
    xml = _xml(tmp_path / 'wrong.xml',
               '<testcase classname="tests.solar-pv.test_x" name="test_case">'
               '<failure/><failure/></testcase>', tests=2, failures=1)
    with pytest.raises(GateError, match='failures count mismatch'):
        _junit(xml)
    xml = _xml(tmp_path / 'collision.xml',
               '<testcase classname="tests.solar-pv.test_x.Case" name="test_a"/>'
               '<testcase classname="tests.solar-pv.test_x" name="Case::test_a"/>', tests=2)
    with pytest.raises(GateError, match='duplicate normalized JUnit node'):
        _junit(xml)


def test_unknown_testcase_child_and_nested_property_fail_closed(tmp_path):
    xml = _xml(tmp_path / 'unknown.xml',
               '<testcase classname="tests.solar-pv.test_x" name="test_unknown">'
               '<unexpected/></testcase>', tests=1)
    with pytest.raises(GateError, match='unexpected JUnit testcase child'):
        _junit(xml)
    xml = _xml(tmp_path / 'unknown-property.xml',
               '<testcase classname="tests.solar-pv.test_x" name="test_unknown">'
               '<properties><unexpected/></properties></testcase>', tests=1)
    with pytest.raises(GateError, match='unexpected JUnit testcase property'):
        _junit(xml)
    xml = _xml(tmp_path / 'hidden-failure.xml',
               '<testcase classname="tests.solar-pv.test_x" name="test_unknown">'
               '<properties><property name="a" value="b">'
               '<failure>hidden failure</failure></property></properties></testcase>', tests=1)
    with pytest.raises(GateError, match='unexpected JUnit testcase property'):
        _junit(xml)
    xml = _xml(tmp_path / 'hidden-system-failure.xml',
               '<testcase classname="tests.solar-pv.test_x" name="test_unknown">'
               '<system-out><failure>hidden failure</failure></system-out></testcase>', tests=1)
    with pytest.raises(GateError, match='unexpected nested JUnit testcase element'):
        _junit(xml)


def test_prototype_collection_must_be_exact_unique_and_scoped(tmp_path):
    selected = _select(['tests/solar-pv/test_phase3e_irr_roots.py',
                        'tests/solar-pv/test_method_configuration.py'])
    good = [f'{name}::test_one' for name in selected]
    log = tmp_path / 'collect.log'
    log.write_text('\n'.join([*good, '2 tests collected in 0.01s']), encoding='utf-8')
    assert _collect_ids(log, selected) == good
    log.write_text('\n'.join([good[0], good[0], '2 tests collected in 0.01s']), encoding='utf-8')
    with pytest.raises(GateError, match='duplicate'):
        _collect_ids(log, selected)
    with pytest.raises(GateError, match='2-3 distinct'):
        _select(['tests/solar-pv/test_phase3e_irr_roots.py'] * 2)
    with pytest.raises(GateError, match='invalid prototype selection'):
        _select(['tests/solar-pv/test_phase3e_irr_roots.py',
                 'tests/solar-pv/test_report_r9_equations.py'])
