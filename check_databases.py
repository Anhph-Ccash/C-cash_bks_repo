#!/usr/bin/env python
"""
Script test kết nối và kiểm tra dữ liệu trong databases
"""

import os
import sys
import argparse
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

sys.path.insert(0, os.path.dirname(__file__))

LOCAL_DB_URL = 'postgresql://postgres:11223344@localhost:5432/FlaskWebPostgreSQL'
RENDER_DB_URL = os.environ.get(
    'RENDER_DATABASE_URL',
    'postgresql://flaskwebpostgresql_user:nrDeXdaJQ2GA9Bv04ISC2rdNpI7EKhYr@dpg-d47l9824d50c7388ofsg-a.singapore-postgres.render.com/flaskwebpostgresql'
)

def test_connection(db_url, db_name):
    """Test kết nối đến database"""
    try:
        print(f"\n[*] Kết nối đến {db_name}...")
        engine = create_engine(
            db_url,
            poolclass=NullPool,
            connect_args={'connect_timeout': 10}
        )

        with engine.connect() as conn:
            # Test basic query
            result = conn.execute(text("SELECT version()"))
            version = result.first()[0]
            print(f"[✓] {db_name} connected successfully")
            print(f"    PostgreSQL version: {version.split(',')[0]}")

        engine.dispose()
        return engine
    except Exception as e:
        print(f"[✗] Lỗi kết nối {db_name}: {e}")
        return None

def check_users_table(db_url, db_name):
    """Kiểm tra bảng users"""
    try:
        engine = create_engine(db_url, poolclass=NullPool)

        with engine.connect() as conn:
            # Check if table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'users'
                )
            """))

            table_exists = result.first()[0]

            if not table_exists:
                print(f"[✗] {db_name}: Bảng 'users' không tồn tại")
                return

            # Get table info
            result = conn.execute(text("SELECT COUNT(*) FROM users"))
            count = result.first()[0]

            result = conn.execute(text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_name = 'users'
                ORDER BY ordinal_position
            """))
            columns = [dict(row._mapping) for row in result]

            print(f"[✓] {db_name}: Bảng 'users' OK")
            print(f"    Total users: {count}")
            print(f"    Columns:")
            for col in columns:
                print(f"      - {col['column_name']}: {col['data_type']}")

            # List users
            if count > 0:
                result = conn.execute(text("""
                    SELECT id, username, email, role
                    FROM users
                    ORDER BY id
                """))
                users = [dict(row._mapping) for row in result]
                print(f"\n    Users:")
                for user in users:
                    print(f"      [{user['id']}] {user['username']} ({user['email']}) - Role: {user['role']}")

        engine.dispose()
    except Exception as e:
        print(f"[✗] Lỗi kiểm tra bảng users: {e}")

def check_user_companies_table(db_url, db_name):
    """Kiểm tra bảng user_companies"""
    try:
        engine = create_engine(db_url, poolclass=NullPool)

        with engine.connect() as conn:
            # Check if table exists
            result = conn.execute(text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_name = 'user_companies'
                )
            """))

            table_exists = result.first()[0]

            if not table_exists:
                print(f"[!] {db_name}: Bảng 'user_companies' không tồn tại")
                return

            # Get count
            result = conn.execute(text("SELECT COUNT(*) FROM user_companies"))
            count = result.first()[0]

            print(f"[✓] {db_name}: Bảng 'user_companies' OK")
            print(f"    Total user_companies: {count}")

        engine.dispose()
    except Exception as e:
        print(f"[✗] Lỗi kiểm tra bảng user_companies: {e}")

def main():
    parser = argparse.ArgumentParser(
        description='Test kết nối và kiểm tra dữ liệu databases'
    )
    parser.add_argument(
        '--local',
        action='store_true',
        help='Chỉ kiểm tra Local Database'
    )
    parser.add_argument(
        '--render',
        action='store_true',
        help='Chỉ kiểm tra Render Database'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Kiểm tra cả Local và Render Database (default)'
    )

    args = parser.parse_args()

    # Default: check all
    if not (args.local or args.render or args.all):
        args.all = True

    print("="*80)
    print("DATABASE CONNECTION & DATA CHECK")
    print("="*80)

    if args.local or args.all:
        print("\n" + "="*80)
        print("LOCAL DATABASE")
        print("="*80)
        test_connection(LOCAL_DB_URL, "Local DB")
        check_users_table(LOCAL_DB_URL, "Local DB")
        check_user_companies_table(LOCAL_DB_URL, "Local DB")

    if args.render or args.all:
        print("\n" + "="*80)
        print("RENDER DATABASE")
        print("="*80)
        test_connection(RENDER_DB_URL, "Render DB")
        check_users_table(RENDER_DB_URL, "Render DB")
        check_user_companies_table(RENDER_DB_URL, "Render DB")

    print("\n" + "="*80)
    print("CHECK COMPLETED")
    print("="*80)

if __name__ == '__main__':
    main()
