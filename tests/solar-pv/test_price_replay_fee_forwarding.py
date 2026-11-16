"""Bounded wiring/real source-validator tests; not a full candidate replay.

Settlement and publishing stages are doubles. Payment source validation is real;
changed-role identities below are explicitly synthetic test identities.
"""
from copy import deepcopy
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from wangbin_solar_pv.calculation import break_even_financial_replay as replay
from wangbin_solar_pv.calculation.method_config import MethodConfig
from wangbin_solar_pv.calculation.trading_fee_payment import validate_trading_fee_payment
from wangbin_solar_pv.errors import ContractError
from wangbin_solar_pv.serialization import loads, dumps

ROOT = Path(__file__).resolve().parents[2]


class PriceReplayFeeForwarding(unittest.TestCase):
    def setUp(self):
        case = ROOT / 'reports/solar-pv/phase7l-r2-full-cases/industrial_rooftop'
        self.original = loads((case / 'input.json').read_bytes())
        self.methods = MethodConfig.from_dict(loads((case / 'methods.json').read_bytes()))
        self.settlement = loads((case / 'project/3c/result.json').read_bytes())
        source = ROOT / 'reports/solar-pv/phase7l-r2-trading-fee-synthetic-source-v1/industrial_rooftop/trading-fee-payment.json'
        self.raw = source.read_bytes()
        self.candidate = deepcopy(self.original)
        self.candidate.update(input_hash='a' * 64, source_snapshot_id='sources-' + 'b' * 64)
        self.candidate_settlement = deepcopy(self.settlement)
        self.candidate_settlement['result_hash'] = 'c' * 64
        self.candidate_settlement['source_snapshot']['datasets']['content_hash'] = 'd' * 64
        separate = loads(self.raw)
        separate['source']['source_id'] = 'SYNTHETIC-INDEPENDENT-CANDIDATE-FEE'
        separate['binding'].update(phase2_input_hash=self.candidate['input_hash'],
            phase2_source_snapshot_id=self.candidate['source_snapshot_id'],
            phase3c_result_hash=self.candidate_settlement['result_hash'], d3_content_hash='d' * 64)
        self.candidate_raw = dumps(separate).encode()

    def invoke(self, original=None, candidate=None):
        seen = []
        def ledger(exported, methods, settlement, *, catalog, trading_fee_source_bytes):
            seen.append(trading_fee_source_bytes)
            if trading_fee_source_bytes is not None:
                validate_trading_fee_payment(trading_fee_source_bytes, exported=exported,
                                            methods=methods, settlement=settlement)
            return {'result_hash': str(len(seen)), 'evidence': {'financial-ledger': {'annual': [len(seen)]}}}
        value = SimpleNamespace(original_revenue=self.settlement, candidate_revenue=self.candidate_settlement,
            candidate_export=self.candidate, original_bundle_hash='original', candidate_bundle_hash='candidate',
            generation_result_hash='generation', original_input_hash=self.original['input_hash'])
        with TemporaryDirectory() as folder:
            root = Path(folder) / 'run'; root.mkdir()
            workspace = SimpleNamespace(path=lambda *a, **k: root)
            with patch.object(replay, '_replay_price_candidate', return_value=value), \
                 patch.object(replay, '_check_settlement', side_effect=lambda result, *a: result['result_hash']), \
                 patch.object(replay, '_check_financial'), patch.object(replay, '_remove_owned'), \
                 patch.object(replay, 'write_financial_bundle'), \
                 patch.object(replay, 'calculate_financial_ledger', side_effect=ledger):
                replay.replay_financial_candidate({}, self.original, self.methods, None, None, 0,
                    catalog=None, budget=None, workspace=workspace, run_name='run',
                    original_trading_fee_source_bytes=original,
                    candidate_trading_fee_source_bytes=candidate)
        return seen

    def test_separate_raw_bytes_reach_correct_role_unchanged(self):
        self.assertEqual(self.invoke(self.raw, self.candidate_raw), [self.raw, self.candidate_raw])

    def test_defaults_do_not_synthesize_sources(self):
        self.assertEqual(self.invoke(), [None, None])

    def test_one_source_does_not_fill_other_role(self):
        self.assertEqual(self.invoke(self.raw), [self.raw, None])

    def test_candidate_source_does_not_fill_original_role(self):
        self.assertEqual(self.invoke(candidate=self.candidate_raw), [None, self.candidate_raw])

    def test_original_source_rejected_for_candidate(self):
        with self.assertRaisesRegex(ContractError, 'TRADING_FEE_SOURCE_BINDING_MISMATCH'):
            self.invoke(self.raw, self.raw)

    def test_candidate_source_rejected_for_original(self):
        with self.assertRaisesRegex(ContractError, 'TRADING_FEE_SOURCE_BINDING_MISMATCH'):
            self.invoke(self.candidate_raw, self.candidate_raw)

    def test_wrong_scenario_and_empty_bytes_rejected(self):
        bad = loads(self.candidate_raw); bad['binding']['scenario_id'] = 'OTHER'
        for raw in (dumps(bad).encode(), b''):
            with self.subTest(raw=bool(raw)), self.assertRaises(ContractError):
                self.invoke(self.raw, raw)

    def test_cached_original_does_not_silently_ignore_new_source(self):
        with self.assertRaisesRegex(ContractError, 'BREAK_EVEN_CACHED_FEE_SOURCE_UNSUPPORTED'):
            replay._replay_financial_candidate({}, {}, None, None, None, 0, catalog=None,
                budget=None, workspace=None, run_name='run', original_revenue={},
                original_financial={}, original_trading_fee_source_bytes=self.raw)


class RealLedgerFeeBoundary(unittest.TestCase):
    def test_nonzero_sourced_payment_and_missing_payment_stay_distinct(self):
        from wangbin_solar_pv.calculation.financial_ledger import calculate_financial_ledger
        from wangbin_solar_pv.calculation.phase3e import _ledger_vectors
        for kind in ('industrial_rooftop', 'utility_scale_ground'):
            with self.subTest(kind=kind):
                case = ROOT / 'reports/solar-pv/phase7l-r2-full-cases' / kind
                exported = loads((case / 'input.json').read_bytes())
                methods = loads((case / 'methods.json').read_bytes())
                settlement = loads((case / 'project/3c/result.json').read_bytes())
                raw = (ROOT / 'reports/solar-pv/phase7l-r2-trading-fee-synthetic-source-v1' / kind / 'trading-fee-payment.json').read_bytes()
                absent = calculate_financial_ledger(exported, methods, settlement)
                self.assertIsNone(absent['evidence']['financial-ledger']['annual'][1]['transaction_cost_cash_paid'])
                self.assertIn('transaction_cost_cash_paid', _ledger_vectors(absent['evidence']['financial-ledger']['annual'])['missing'])
                supplied = calculate_financial_ledger(exported, methods, settlement, trading_fee_source_bytes=raw)
                row = supplied['evidence']['financial-ledger']['annual'][1]
                self.assertGreater(row['transaction_cost_cash_paid'], 0)
                self.assertEqual(row['transaction_cost_cash_paid'], row['transaction_cost_accrued'])
                self.assertEqual(row['transaction_cost_payment_status'], 'SYNTHETIC_ASSUMED_SAME_YEAR')
                self.assertNotIn('transaction_cost_cash_paid', _ledger_vectors(supplied['evidence']['financial-ledger']['annual'])['missing'])


if __name__ == '__main__':
    unittest.main()
