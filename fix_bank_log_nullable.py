"""Migration to make company_id nullable in bank_log"""
import psycopg2
from config import Config

conn = None
try:
    conn = psycopg2.connect(Config.SQLALCHEMY_DATABASE_URI)
    conn.autocommit = False
    cur = conn.cursor()
    
    print("🔄 Making company_id nullable in bank_log...")
    
    cur.execute("ALTER TABLE bank_log ALTER COLUMN company_id DROP NOT NULL;")
    
    conn.commit()
    print("✅ Migration completed!")
    
    cur.execute("""
        SELECT column_name, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'bank_log' AND column_name = 'company_id';
    """)
    result = cur.fetchone()
    if result:
        print(f"✅ Verified: company_id is_nullable = {result[1]}")
    
    cur.close()
    conn.close()
    
except Exception as e:
    print(f"❌ Error: {e}")
    if conn:
        conn.rollback()
        conn.close()
