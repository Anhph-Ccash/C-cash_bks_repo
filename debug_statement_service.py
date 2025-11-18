#!/usr/bin/env python3
"""
Debug script cho statement_service.py
Hướng dẫn debug các function chính trong statement service
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.statement_service import (
    validate_statement_data,
    _col_to_index,
    _get_dataframe_sheets,
    _find_value_in_df,
    parse_and_store_statement
)
import pandas as pd
import pprint

def debug_col_to_index():
    """Debug function _col_to_index"""
    print("=== DEBUG: _col_to_index ===")

    test_cases = [
        "A",      # Expected: 0
        "B",      # Expected: 1
        "Z",      # Expected: 25
        "AA",     # Expected: 26
        "AB",     # Expected: 27
        "1",      # Expected: 0 (numeric 1-based to 0-based)
        "5",      # Expected: 4
        None,     # Expected: None
        "",       # Expected: None
        "XYZ"     # Expected: complex calculation
    ]

    for test in test_cases:
        result = _col_to_index(test)
        print(f"Input: {test} -> Output: {result}")
        # Thêm breakpoint ở đây để debug step-by-step
        # import pdb; pdb.set_trace()

    print()

def debug_validate_statement_data():
    """Debug function validate_statement_data"""
    print("=== DEBUG: validate_statement_data ===")

    # Test case 1: Valid data
    valid_data = {
        'opening_balance': '1000000',
        'closing_balance': '1500000',
        'currency': 'VND',
        'bank_code': 'VCB',
        'account_number': '12345678',
        'transactions': [
            {
                'transactiondate': '01/11/2023',
                'narrative': 'Transfer from John Doe',
                'credit': '500000',
                'debit': None
            },
            {
                'transactiondate': '02/11/2023',
                'narrative': 'ATM withdrawal',
                'credit': None,
                'debit': '100000'
            }
        ]
    }

    print("Test case 1: Valid data")
    is_valid, errors = validate_statement_data(valid_data)
    print(f"Is Valid: {is_valid}")
    print(f"Errors: {errors}")

    # Thêm breakpoint để debug logic validation
    # import pdb; pdb.set_trace()

    # Test case 2: Missing required fields
    invalid_data = {
        'opening_balance': None,  # Missing
        'closing_balance': '1500000',
        'currency': None,         # Missing
        'bank_code': 'VCB',
        'transactions': []        # Empty transactions
    }

    print("\nTest case 2: Invalid data (missing required fields)")
    is_valid, errors = validate_statement_data(invalid_data)
    print(f"Is Valid: {is_valid}")
    print("Errors:")
    for error in errors:
        print(f"  - {error}")

    print()

def debug_get_dataframe_sheets():
    """Debug function _get_dataframe_sheets"""
    print("=== DEBUG: _get_dataframe_sheets ===")

    # Tạo test files để debug
    # CSV test file
    csv_test_data = """Date,Description,Debit,Credit,Balance
01/11/2023,Initial deposit,,1000000,1000000
02/11/2023,ATM withdrawal,100000,,900000
03/11/2023,Transfer in,,500000,1400000"""

    csv_path = "test_statement.csv"
    with open(csv_path, 'w', encoding='utf-8') as f:
        f.write(csv_test_data)

    try:
        print("Testing CSV file parsing:")
        sheets = _get_dataframe_sheets(csv_path, 'csv')
        print(f"Number of sheets: {len(sheets)}")
        for sheet_name, df in sheets.items():
            print(f"Sheet: {sheet_name}")
            print(f"Shape: {df.shape}")
            print("Data preview:")
            print(df.head())
            print()

            # Thêm breakpoint để debug dataframe content
            # import pdb; pdb.set_trace()

    finally:
        # Cleanup
        if os.path.exists(csv_path):
            os.remove(csv_path)

def debug_find_value_in_df():
    """Debug function _find_value_in_df"""
    print("=== DEBUG: _find_value_in_df ===")

    # Tạo test DataFrame
    test_data = {
        'Field': ['Account Number', 'Opening Balance', 'Currency', 'Transaction Date', 'Description'],
        'Value': ['12345678', '1000000', 'VND', '01/11/2023', 'Sample transaction'],
        'Extra': ['', 'VND', '', '02/11/2023', 'Another transaction']
    }

    df = pd.DataFrame(test_data)
    print("Test DataFrame:")
    print(df)
    print()

    # Test tìm Opening Balance
    print("Test 1: Find Opening Balance")
    keywords = ['opening', 'balance', 'số dư đầu']
    result = _find_value_in_df(df, keywords, 'Field', 'Value', 1, 5)
    print(f"Result: {result}")

    # Thêm breakpoint để debug search logic
    # import pdb; pdb.set_trace()

    # Test tìm Account Number
    print("\nTest 2: Find Account Number")
    keywords = ['account', 'number', 'tài khoản']
    result = _find_value_in_df(df, keywords, 'Field', 'Value', 1, 5)
    print(f"Result: {result}")

    print()

def create_debug_session():
    """Tạo debug session với các tool cần thiết"""
    print("=== STATEMENT SERVICE DEBUG SESSION ===")
    print("Các function có thể debug:")
    print("1. debug_col_to_index() - Test column index conversion")
    print("2. debug_validate_statement_data() - Test data validation")
    print("3. debug_get_dataframe_sheets() - Test file parsing")
    print("4. debug_find_value_in_df() - Test value searching")
    print()

    # Uncomment các dòng dưới để chạy debug
    debug_col_to_index()
    debug_validate_statement_data()
    debug_get_dataframe_sheets()
    debug_find_value_in_df()

if __name__ == "__main__":
    create_debug_session()
