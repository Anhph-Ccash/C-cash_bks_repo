"""
Demo validation for statement upload
"""
from services.statement_service import validate_statement_data

print("=" * 60)
print("DEMO: STATEMENT VALIDATION")
print("=" * 60)

# Test Case 1: Valid data
print("\n1. Valid Statement Data:")
valid_data = {
    'opening_balance': '1000000',
    'closing_balance': '500000',
    'bank_code': 'TPB',
    'account_number': '03399686868',
    'transactions': [
        {
            'transactiondate': '10112025',
            'narrative': 'Payment for invoice',
            'credit': '0',
            'debit': '500000'
        }
    ]
}
is_valid, errors = validate_statement_data(valid_data)
print(f"  Valid: {is_valid}")
if errors:
    for err in errors:
        print(f"    - {err}")

# Test Case 2: Missing opening balance
print("\n2. Missing Opening Balance:")
invalid_data1 = {
    'opening_balance': None,
    'closing_balance': '500000',
    'bank_code': 'TPB',
    'account_number': '03399686868',
    'transactions': [
        {
            'transactiondate': '10112025',
            'narrative': 'Payment',
            'credit': '0',
            'debit': '500000'
        }
    ]
}
is_valid, errors = validate_statement_data(invalid_data1)
print(f"  Valid: {is_valid}")
for err in errors:
    print(f"    - {err}")

# Test Case 3: Missing transactions
print("\n3. No Transactions:")
invalid_data2 = {
    'opening_balance': '1000000',
    'closing_balance': '1000000',
    'bank_code': 'TPB',
    'account_number': '03399686868',
    'transactions': []
}
is_valid, errors = validate_statement_data(invalid_data2)
print(f"  Valid: {is_valid}")
for err in errors:
    print(f"    - {err}")

# Test Case 4: Missing transaction fields
print("\n4. Missing Transaction Date and Narrative:")
invalid_data3 = {
    'opening_balance': '1000000',
    'closing_balance': '500000',
    'bank_code': 'TPB',
    'account_number': '03399686868',
    'transactions': [
        {
            'transactiondate': None,
            'narrative': None,
            'credit': '500000',
            'debit': '0'
        },
        {
            'transactiondate': '10112025',
            'narrative': None,
            'credit': '0',
            'debit': '200000'
        }
    ]
}
is_valid, errors = validate_statement_data(invalid_data3)
print(f"  Valid: {is_valid}")
for err in errors:
    print(f"    - {err}")

# Test Case 5: All fields missing
print("\n5. All Required Fields Missing:")
invalid_data4 = {
    'opening_balance': None,
    'closing_balance': None,
    'bank_code': None,
    'account_number': None,
    'transactions': []
}
is_valid, errors = validate_statement_data(invalid_data4)
print(f"  Valid: {is_valid}")
for err in errors:
    print(f"    - {err}")

print("\n" + "=" * 60)
print("VALIDATION SUMMARY:")
print("=" * 60)
print("✓ Kiểm tra Số dư đầu kỳ (Opening Balance)")
print("✓ Kiểm tra Số dư cuối kỳ (Closing Balance)")
print("✓ Kiểm tra Tên ngân hàng (Bank Code)")
print("✓ Kiểm tra Số tài khoản (Account Number)")
print("✓ Kiểm tra có giao dịch (Transactions)")
print("✓ Kiểm tra Credit/Debit cho từng giao dịch")
print("✓ Kiểm tra Narrative (Diễn giải) cho từng giao dịch")
print("✓ Kiểm tra Transaction Date cho từng giao dịch")
