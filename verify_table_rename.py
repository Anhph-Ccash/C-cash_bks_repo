#!/usr/bin/env python
"""Verify user_companies table exists"""
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

LOCAL_DB_URL = 'postgresql://postgres:11223344@localhost:5432/FlaskWebPostgreSQL'

engine = create_engine(LOCAL_DB_URL, poolclass=NullPool)

try:
    with engine.connect() as conn:
        # Check tables
        result = conn.execute(text("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema='public' AND table_name LIKE 'user_%'
        """))
        tables = [row[0] for row in result]
        print(f"[✓] Tables found: {tables}")

        # Check user_companies specifically
        result = conn.execute(text("""
            SELECT COUNT(*) FROM information_schema.tables
            WHERE table_name = 'user_companies'
        """))
        exists = result.scalar() > 0
        if exists:
            print("[✅] user_companies table EXISTS")
            # Get row count
            result = conn.execute(text("SELECT COUNT(*) FROM user_companies"))
            count = result.scalar()
            print(f"[ℹ️] Total records: {count}")
        else:
            print("[❌] user_companies table NOT FOUND")

except Exception as e:
    print(f"[✗] Error: {e}")
finally:
    engine.dispose()
