"""Mechanical meaning checks for declared risks, not natural-language approval."""
from ..errors import ContractError

MEANINGS = ('DISPOSAL_CASH', 'PAID_FEE', 'CASH_RECEIPT', 'EQUITY_RETURN', 'DSCR_MULTIPLE', 'ZERO_VALUE')


def validate_risk_assertions(claim, facts):
    for assertion in claim.get('risk_assertions', []):
        refs = assertion['fact_refs']
        if not refs or set(refs) - set(claim['fact_refs']):
            raise ContractError('SEMANTIC_RISK_BLOCKED')
        # Current evidence adapters carry predictions, not certified bank events.
        # No approved standalone disposal-cash fact adapter is present either.
        if assertion['basis'] == 'ACTUAL' or assertion['meaning'] == 'DISPOSAL_CASH':
            raise ContractError('SEMANTIC_RISK_BLOCKED')
        for ref in refs:
            fact = facts[ref]
            if fact['status'] != 'CALCULATED' or fact['value'] is None:
                raise ContractError('SEMANTIC_RISK_BLOCKED')
            meaning = assertion['meaning']
            allowed = False
            if meaning == 'PAID_FEE':
                allowed = fact['kind'] == 'ledger' and ref.startswith('pilot:cash.') and ref.endswith('.transaction_cost_cash_paid')
            elif meaning == 'CASH_RECEIPT':
                allowed = fact['kind'] == 'ledger' and ref.startswith('pilot:cash.') and ref.endswith('.revenue_cash_receipts')
            elif meaning == 'EQUITY_RETURN':
                allowed = fact['kind'] == 'metric' and fact.get('metric_id') == 'financial.phase3e.equity-investor-cash-flow'
            elif meaning == 'DSCR_MULTIPLE':
                allowed = fact['kind'] == 'metric' and fact.get('metric_id') == 'financial.phase3e.dscr'
            elif meaning == 'ZERO_VALUE':
                allowed = not isinstance(fact['value'], bool) and fact['value'] == 0
            if not allowed:
                raise ContractError('SEMANTIC_RISK_BLOCKED')
