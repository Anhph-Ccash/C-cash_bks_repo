#!/usr/bin/env python3
"""
Advanced Debug Script với breakpoints và step-by-step debugging
Sử dụng Python debugger (pdb) để debug từng bước
"""

import sys
import os
import pdb
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.statement_service import validate_statement_data, _col_to_index, _find_value_in_df
import pandas as pd

def step_by_step_validation_debug():
    """
    Debug step-by-step validation logic
    Chạy function này và sử dụng pdb commands:
    - n (next): Chạy dòng kế tiếp
    - s (step): Bước vào function
    - c (continue): Tiếp tục chạy
    - p <variable>: In giá trị biến
    - pp <variable>: Pretty print biến
    - l: Xem code xung quanh
    - q: Thoát debugger
    """
    print("=== STEP BY STEP VALIDATION DEBUG ===")

    # Test data with some missing fields
    test_data = {
        'opening_balance': '1000000',
        'closing_balance': None,  # Missing - sẽ tạo error
        'currency': 'VND',
        'bank_code': 'VCB',
        'account_number': '12345678',
        'transactions': [
            {
                'transactiondate': '01/11/2023',
                'narrative': 'Valid transaction',
                'credit': '500000',
                'debit': None
            },
            {
                'transactiondate': '',  # Missing date - sẽ tạo error
                'narrative': 'Invalid transaction - no date',
                'credit': None,
                'debit': '100000'
            },
            {
                'transactiondate': '03/11/2023',
                'narrative': '',  # Missing narrative - sẽ tạo error
                'credit': '200000',
                'debit': None
            }
        ]
    }

    print("Data to validate:")
    import pprint
    pprint.pprint(test_data)
    print("\n--- Starting validation debug ---")

    # Đặt breakpoint ở đây - sẽ dừng trước khi vào function
    pdb.set_trace()

    # Call validation function
    is_valid, errors = validate_statement_data(test_data)

    print(f"Final result - Is Valid: {is_valid}")
    print("Errors found:")
    for error in errors:
        print(f"  - {error}")

def debug_column_parsing():
    """Debug column parsing logic"""
    print("=== COLUMN PARSING DEBUG ===")

    # Test DataFrame giống như file Excel/CSV thực tế
    test_data = {
        'A': ['Account Info', '12345678', '', 'Transaction 1', 'Transaction 2'],
        'B': ['Balance Info', '1000000', '', '500000', '300000'],
        'C': ['Currency', 'VND', '', 'Credit', 'Debit'],
        'D': ['Date', '01/11/2023', '', '01/11/2023', '02/11/2023'],
        'E': ['Description', 'Opening', '', 'Salary', 'ATM withdrawal']
    }

    df = pd.DataFrame(test_data)
    print("Test DataFrame (giống file Excel):")
    print(df)
    print()

    # Test parsing column A (should be index 0)
    print("Testing column conversion:")
    test_cols = ['A', 'B', 'C', '1', '2', '3']

    for col in test_cols:
        pdb.set_trace()  # Breakpoint để debug từng column
        index = _col_to_index(col)
        print(f"Column '{col}' -> Index: {index}")

        if index is not None and index < len(df.columns):
            actual_col = df.columns[index]
            print(f"  Actual column name: {actual_col}")
            print(f"  Sample values: {df[actual_col].head(3).tolist()}")
        print()

def debug_value_search():
    """Debug value searching in DataFrame"""
    print("=== VALUE SEARCH DEBUG ===")

    # Tạo DataFrame giống cấu trúc file statement thực tế
    bank_statement_data = {
        'Field Name': [
            'Tên tài khoản',
            'Số tài khoản',
            'Số dư đầu kỳ',
            'Số dư cuối kỳ',
            'Loại tiền tệ',
            '',
            'Ngày GD',
            'Diễn giải',
            'Số tiền ghi có',
            'Số tiền ghi nợ'
        ],
        'Value': [
            'JOHN DOE',
            '12345678901',
            '5000000',
            '5500000',
            'VND',
            '',
            '01/11/2023',
            'Chuyển khoản từ ABC',
            '1000000',
            ''
        ],
        'Extra Info': [
            'Customer Name',
            'Account Number',
            'Opening Balance',
            'Closing Balance',
            'Currency',
            '',
            'Transaction Date',
            'Description',
            'Credit Amount',
            'Debit Amount'
        ]
    }

    df = pd.DataFrame(bank_statement_data)
    print("Bank Statement DataFrame:")
    print(df)
    print()

    # Test searches với keywords tiếng Việt
    searches = [
        {
            'name': 'Account Number',
            'keywords': ['số tài khoản', 'account', 'tài khoản'],
            'col_keyword': 'Field Name',
            'col_value': 'Value'
        },
        {
            'name': 'Opening Balance',
            'keywords': ['số dư đầu', 'opening', 'đầu kỳ'],
            'col_keyword': 'Field Name',
            'col_value': 'Value'
        },
        {
            'name': 'Currency',
            'keywords': ['loại tiền', 'currency', 'tiền tệ'],
            'col_keyword': 'Field Name',
            'col_value': 'Value'
        }
    ]

    for search in searches:
        print(f"Searching for: {search['name']}")
        print(f"Keywords: {search['keywords']}")

        pdb.set_trace()  # Breakpoint để debug search logic

        result = _find_value_in_df(
            df,
            search['keywords'],
            search['col_keyword'],
            search['col_value'],
            1, 10  # row range
        )

        print(f"Result: {result}")
        print("-" * 40)

def main():
    """Main debug menu"""
    print("STATEMENT SERVICE ADVANCED DEBUG")
    print("================================")
    print("Chọn debug mode:")
    print("1. Step-by-step validation debug")
    print("2. Column parsing debug")
    print("3. Value search debug")
    print("4. All debug modes")

    choice = input("Nhập lựa chọn (1-4): ").strip()

    if choice == '1':
        step_by_step_validation_debug()
    elif choice == '2':
        debug_column_parsing()
    elif choice == '3':
        debug_value_search()
    elif choice == '4':
        print("Running all debug modes...")
        step_by_step_validation_debug()
        debug_column_parsing()
        debug_value_search()
    else:
        print("Invalid choice!")

if __name__ == "__main__":
    main()
