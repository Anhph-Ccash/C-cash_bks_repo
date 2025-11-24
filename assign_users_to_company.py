#!/usr/bin/env python
"""
Script gán tất cả users hiện có vào company_id=1 trong bảng user_companies.
Tạo bảng company và user_companies nếu chưa tồn tại.
Không thay đổi dữ liệu hiện có, chỉ thêm bản ghi còn thiếu.

Cách dùng:
  python assign_users_to_company.py              # chạy trên DATABASE_URL (remote hoặc local)
  python assign_users_to_company.py --dry-run    # hiển thị dự kiến insert mà không ghi
  python assign_users_to_company.py --local      # ép dùng LOCAL_DB_URL

Env:
  DATABASE_URL (được sử dụng mặc định)

Logic:
    1. Đảm bảo tồn tại bảng company, user_companies theo schema đơn giản nếu chưa có.
  2. Đảm bảo tồn tại company id=1 (tạo nếu chưa có).
  3. Lấy toàn bộ users từ bảng users.
    4. Chèn vào user_companies nếu chưa có (user_id, company_id=1), role lấy theo users.role (null -> 'user').
  5. Báo cáo số lượng đã thêm.
"""
import os
import argparse
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

LOCAL_DB_URL = 'postgresql://postgres:11223344@localhost:5432/FlaskWebPostgreSQL'
REMOTE_DB_URL = os.environ.get('DATABASE_URL')

CREATE_COMPANY_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS company (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address TEXT,
    tax_code VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,
    sftp_host VARCHAR(255),
    sftp_port INTEGER DEFAULT 22,
    sftp_username VARCHAR(255),
    sftp_password VARCHAR(255),
    sftp_remote_path VARCHAR(255),
    sftp_private_key_path VARCHAR(255)
);
"""

CREATE_USER_COMPANY_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS user_companies (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_id INTEGER NOT NULL REFERENCES company(id) ON DELETE CASCADE,
    role VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_user_company UNIQUE(user_id, company_id)
);
"""

ENSURE_COMPANY_ID_SQL = """
INSERT INTO company (id, name, is_active)
SELECT 1, 'Default Company', TRUE
WHERE NOT EXISTS (SELECT 1 FROM company WHERE id=1);
"""

SELECT_USERS_SQL = """SELECT id, username, role FROM users ORDER BY id;"""

SELECT_EXISTING_LINKS_SQL = """SELECT user_id FROM user_companies WHERE company_id=1;"""

INSERT_LINK_SQL = """
INSERT INTO user_companies (user_id, company_id, role)
VALUES (:user_id, 1, :role)
ON CONFLICT (user_id, company_id) DO NOTHING;
"""

def main():
    parser = argparse.ArgumentParser(description='Gán tất cả users vào company_id=1')
    parser.add_argument('--dry-run', action='store_true', help='Chỉ hiển thị dự kiến insert, không ghi')
    parser.add_argument('--local', action='store_true', help='Dùng local DB thay vì DATABASE_URL env')
    args = parser.parse_args()

    db_url = LOCAL_DB_URL if args.local else REMOTE_DB_URL or LOCAL_DB_URL
    if not db_url:
        print('[✗] Không tìm thấy DATABASE_URL và LOCAL_DB_URL trống')
        return

    print(f'[*] Kết nối database: {db_url}')
    engine = create_engine(db_url, poolclass=NullPool, connect_args={'connect_timeout': 10})

    try:
        with engine.begin() as conn:
            # Tạo bảng nếu thiếu
            conn.execute(text(CREATE_COMPANY_TABLE_SQL))
            conn.execute(text(CREATE_USER_COMPANY_TABLE_SQL))
            # Đảm bảo company id=1
            conn.execute(text(ENSURE_COMPANY_ID_SQL))

            users = [dict(r._mapping) for r in conn.execute(text(SELECT_USERS_SQL))]
            existing_links = {r[0] for r in conn.execute(text(SELECT_EXISTING_LINKS_SQL))}

            to_insert = []
            for u in users:
                if u['id'] not in existing_links:
                    role = u.get('role') or 'user'
                    to_insert.append({'user_id': u['id'], 'role': role})

            print(f'[✓] Tổng users: {len(users)}; đã có link: {len(existing_links)}; sẽ thêm: {len(to_insert)}')

            if args.dry_run:
                for row in to_insert:
                    print(f"DRY-RUN INSERT -> user_id={row['user_id']} company_id=1 role={row['role']}")
                print('[*] Dry-run hoàn tất, không ghi dữ liệu.')
                return

            for row in to_insert:
                conn.execute(text(INSERT_LINK_SQL), row)

            print(f'[✓] Đã thêm {len(to_insert)} bản ghi mới vào user_companies.')
    except Exception as e:
        print(f'[✗] Lỗi: {e}')
    finally:
        engine.dispose()

if __name__ == '__main__':
    main()
