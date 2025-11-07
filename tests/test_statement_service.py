import pytest
from services.statement_service import build_mt940_strict

class DummyStmt:
    def __init__(self, id, accountno=None, currency=None, opening_balance=None, closing_balance=None, details=None, bank_code=None):
        self.id = id
        self.accountno = accountno
        self.currency = currency
        self.opening_balance = opening_balance
        self.closing_balance = closing_balance
        self.details = details
        self.bank_code = bank_code


def test_build_mt940_basic():
    details = [
        {'transactiondate': '2025-11-05', 'narrative': 'Test payment', 'debit': '1000.50', 'credit': ''},
        {'transactiondate': '2025-11-06', 'narrative': 'Received', 'debit': '', 'credit': '200.00'},
    ]
    stmt = DummyStmt(123, accountno='12345678', currency='VND', opening_balance='5000', closing_balance='4200.5', details=details, bank_code='VCB')
    mt = build_mt940_strict(stmt)
    assert ':20:VCBXXX' in mt
    assert ':25:12345678' in mt
    # opening balance formatted with comma
    assert ':60F:C' in mt
    # check transaction lines
    assert ':61:' in mt
    assert ':86:Test payment' in mt
    assert ':86:Received' in mt
    assert ':62F:C' in mt