#!/usr/bin/env python
"""
Script đổi tên bảng từ user_company -> user_companies trong database FlaskWebPostgreSQL.
An toàn: chỉ chạy nếu bảng cũ tồn tại và bảng mới chưa tồn tại.
Không tạo lại index/constraints trừ unique hiện có.

Cách dùng:
  python rename_user_company_table.py                # dùng DATABASE_URL hoặc local mặc định
  python rename_user_company_table.py --local       # ép dùng local DB
  python rename_user_company_table.py --dry-run     # chỉ hiển thị trạng thái, không đổi tên

Sau khi chạy:
  - Cập nhật model đã được thực hiện (__tablename__ = 'user_companies').
  - Nên chạy lại: python check_databases.py --local để kiểm tra.
"""
import os
import argparse
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

LOCAL_DB_URL = 'postgresql://postgres:11223344@localhost:5432/FlaskWebPostgreSQL'
DB_URL = os.environ.get('DATABASE_URL')

CHECK_TABLE_SQL = """
SELECT table_name FROM information_schema.tables
WHERE table_schema='public' AND table_name IN ('user_company','user_companies');
"""

RENAME_SQL = "ALTER TABLE user_company RENAME TO user_companies;"

COPY_CONSTRAINT_SQL = """
DO $$
BEGIN
    -- Đảm bảo constraint unique tồn tại dưới tên mong muốn (nếu chưa có)
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint c
        JOIN pg_class t ON c.conrelid = t.oid
        WHERE t.relname = 'user_companies' AND c.conname = 'unique_user_company'
    ) THEN
        BEGIN
            ALTER TABLE user_companies ADD CONSTRAINT unique_user_company UNIQUE(user_id, company_id);
        EXCEPTION WHEN others THEN
            -- ignore
        END;
    END IF;
END$$;
"""

def main():
    parser = argparse.ArgumentParser(description='Đổi tên bảng user_company -> user_companies')
    parser.add_argument('--local', action='store_true', help='Dùng local DB URL thay vì DATABASE_URL env')
    parser.add_argument('--dry-run', action='store_true', help='Chỉ kiểm tra, không thực thi rename')
    args = parser.parse_args()

    db_url = LOCAL_DB_URL if args.local else DB_URL or LOCAL_DB_URL
    print(f'[*] Sử dụng database: {db_url}')

    engine = create_engine(db_url, poolclass=NullPool, connect_args={'connect_timeout': 10})

    try:
        with engine.begin() as conn:
            existing = {r[0] for r in conn.execute(text(CHECK_TABLE_SQL))}
            print(f'[✓] Các bảng hiện diện: {", ".join(sorted(existing)) or "(none)"}')

            has_old = 'user_company' in existing
            has_new = 'user_companies' in existing

            if not has_old and has_new:
                print('[✓] Bảng đã ở dạng mới (user_companies). Không cần đổi tên.')
                return
            if not has_old and not has_new:
                print('[!] Không có bảng user_company hoặc user_companies. Có thể chưa migrate model.')
                return
            if has_old and has_new:
                print('[!] Cả hai bảng tồn tại. Cần xử lý thủ công hợp nhất dữ liệu trước khi xóa bảng cũ.')
                return

            if args.dry_run:
                print('[*] DRY-RUN: Sẽ thực thi ALTER TABLE user_company RENAME TO user_companies')
                return

            # Thực hiện rename
            print('[*] Đổi tên bảng ...')
            conn.execute(text(RENAME_SQL))
            print('[✓] Đã đổi tên bảng thành công.')

            # Đảm bảo unique constraint tồn tại
            print('[*] Kiểm tra/đảm bảo unique constraint ...')
            conn.execute(text(COPY_CONSTRAINT_SQL))
            print('[✓] Đã xác nhận unique constraint.')

    except Exception as e:
        print(f'[✗] Lỗi: {e}')
    finally:
        engine.dispose()

if __name__ == '__main__':
    main()
