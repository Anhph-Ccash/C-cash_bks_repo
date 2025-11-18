#!/usr/bin/env python3
"""
Debug với data thực tế - tạo test cases giống như file statement thật
"""

import sys
import os
import pandas as pd
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.statement_service import parse_and_store_statement, validate_statement_data
from models.bank_statement_config import BankStatementConfig

def create_test_excel_file():
    """Tạo file Excel test giống như file statement thực tế"""

    # Data giống như file VCB statement
    data = {
        'A': [
            'NGÂN HÀNG TMCP NGOẠI THƯƠNG VIỆT NAM',
            'Số tài khoản',
            '12345678901',
            'Tên tài khoản',
            'NGUYEN VAN A',
            'Số dư đầu kỳ',
            '5,000,000',
            'Số dư cuối kỳ',
            '5,500,000',
            'Loại tiền',
            'VND',
            '',
            'STT',
            '1',
            '2',
            '3'
        ],
        'B': [
            'VIETCOMBANK',
            'Account Number',
            '',
            'Account Name',
            '',
            'Opening Balance',
            'VND',
            'Closing Balance',
            'VND',
            'Currency',
            '',
            '',
            'Ngày GD',
            '01/11/2023',
            '02/11/2023',
            '03/11/2023'
        ],
        'C': [
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            'Diễn giải',
            'Lương tháng 11',
            'Rút tiền ATM',
            'Chuyển khoản đi'
        ],
        'D': [
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            'Ghi có',
            '3,000,000',
            '',
            ''
        ],
        'E': [
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            'Ghi nợ',
            '',
            '500,000',
            '2,000,000'
        ],
        'F': [
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            '',
            'Số dư',
            '8,000,000',
            '7,500,000',
            '5,500,000'
        ]
    }

    df = pd.DataFrame(data)
    filename = 'test_vcb_statement.xlsx'
    df.to_excel(filename, index=False, header=False)

    print(f"Created test file: {filename}")
    print("File structure:")
    print(df.head(16))

    return filename

def debug_real_parsing():
    """Debug parsing với file thực tế"""
    print("=== DEBUG REAL FILE PARSING ===")

    # Tạo test file
    test_file = create_test_excel_file()

    try:
        # Import để test
        from services.statement_service import _get_dataframe_sheets, _find_value_in_df

        # Đọc file
        print("\n1. Reading Excel file:")
        sheets = _get_dataframe_sheets(test_file, 'xlsx')

        for sheet_name, df in sheets.items():
            print(f"Sheet: {sheet_name}")
            print(f"Shape: {df.shape}")
            print("First 10 rows:")
            print(df.head(10))
            print()

            # Test tìm các fields quan trọng
            print("2. Testing field extraction:")

            # Tìm số tài khoản
            account = _find_value_in_df(df, ['số tài khoản', 'account'], 'A', 'C', 1, 15)
            print(f"Account Number: {account}")

            # Tìm số dư đầu kỳ
            opening = _find_value_in_df(df, ['số dư đầu', 'opening'], 'A', 'C', 1, 15)
            print(f"Opening Balance: {opening}")

            # Tìm số dư cuối kỳ
            closing = _find_value_in_df(df, ['số dư cuối', 'closing'], 'A', 'C', 1, 15)
            print(f"Closing Balance: {closing}")

            # Tìm currency
            currency = _find_value_in_df(df, ['loại tiền', 'currency'], 'A', 'C', 1, 15)
            print(f"Currency: {currency}")

            print("\n3. Testing transaction extraction:")
            # Thử extract transactions từ row 14-16 (0-based: 13-15)
            transactions = []
            for row_idx in range(13, 16):
                if row_idx < len(df):
                    row = df.iloc[row_idx]
                    transaction = {
                        'date': row.get('B', ''),
                        'narrative': row.get('C', ''),
                        'credit': row.get('D', ''),
                        'debit': row.get('E', ''),
                        'balance': row.get('F', '')
                    }
                    transactions.append(transaction)
                    print(f"Row {row_idx + 1}: {transaction}")

            # Test validation
            print("\n4. Testing validation:")
            validation_data = {
                'opening_balance': opening,
                'closing_balance': closing,
                'currency': currency,
                'bank_code': 'VCB',
                'account_number': account,
                'transactions': [
                    {
                        'transactiondate': '01112023',
                        'narrative': 'Lương tháng 11',
                        'credit': '3000000',
                        'debit': None
                    },
                    {
                        'transactiondate': '02112023',
                        'narrative': 'Rút tiền ATM',
                        'credit': None,
                        'debit': '500000'
                    }
                ]
            }

            is_valid, errors = validate_statement_data(validation_data)
            print(f"Is Valid: {is_valid}")
            if errors:
                print("Validation Errors:")
                for error in errors:
                    print(f"  - {error}")
            else:
                print("✅ All validation passed!")

    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"\nCleaned up test file: {test_file}")

def debug_step_by_step_parsing():
    """Debug từng bước của parsing process"""
    print("=== STEP BY STEP PARSING DEBUG ===")

    # Tạo simple test case
    test_data = {
        'opening_balance': '1000000',
        'closing_balance': '1500000',
        'currency': 'VND',
        'bank_code': 'VCB',
        'account_number': '12345678',
        'transactions': []
    }

    print("Step 1: Empty transactions test")
    is_valid, errors = validate_statement_data(test_data)
    print(f"Result: Valid={is_valid}, Errors={len(errors)}")
    for error in errors:
        print(f"  - {error}")

    print("\nStep 2: Adding invalid transactions")
    test_data['transactions'] = [
        {
            'transactiondate': '',  # Missing
            'narrative': 'Test transaction',
            'credit': '100000',
            'debit': None
        },
        {
            'transactiondate': '01112023',
            'narrative': '',  # Missing
            'credit': None,
            'debit': '50000'
        }
    ]

    is_valid, errors = validate_statement_data(test_data)
    print(f"Result: Valid={is_valid}, Errors={len(errors)}")
    for error in errors:
        print(f"  - {error}")

    print("\nStep 3: Adding valid transactions")
    test_data['transactions'].append({
        'transactiondate': '02112023',
        'narrative': 'Valid transaction',
        'credit': '200000',
        'debit': None
    })

    is_valid, errors = validate_statement_data(test_data)
    print(f"Result: Valid={is_valid}, Errors={len(errors)}")
    for error in errors:
        print(f"  - {error}")

if __name__ == "__main__":
    print("REAL DATA DEBUG FOR STATEMENT SERVICE")
    print("====================================")

    debug_step_by_step_parsing()
    print("\n" + "="*50 + "\n")
    debug_real_parsing()
