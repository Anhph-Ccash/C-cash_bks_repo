#!/usr/bin/env python3
"""
Quick script to check the users table schema in the database
"""
import sys
import os
sys.path.append(os.path.dirname(__file__))

from config import Config
import psycopg2

try:
    # Connect directly to database
    conn = psycopg2.connect(Config.SQLALCHEMY_DATABASE_URI)
    cur = conn.cursor()

    # Get table info using raw SQL
    cur.execute("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'users' ORDER BY ordinal_position;")
    columns = cur.fetchall()

    print("Existing users table columns:")
    print("-" * 40)
    for col in columns:
        print(f"  {col[0]} ({col[1]}) - {'NULL' if col[2] == 'YES' else 'NOT NULL'}")

    cur.close()
    conn.close()

except Exception as e:
    print(f"Error checking table schema: {e}")
