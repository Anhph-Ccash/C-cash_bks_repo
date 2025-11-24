#!/usr/bin/env python
"""
Migration script để đưa dữ liệu bảng users từ local PostgreSQL lên Render Database
Cách sử dụng:
  python migrate_users_to_render.py --preview    # Xem dữ liệu sẽ migrate
  python migrate_users_to_render.py --execute    # Thực hiện migration
  python migrate_users_to_render.py --backup     # Backup dữ liệu hiện tại trước khi migrate
"""

import os
import sys
import json
import argparse
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

# Thêm workspace vào Python path
sys.path.insert(0, os.path.dirname(__file__))

# Local database configuration
LOCAL_DB_URL = 'postgresql://postgres:11223344@localhost:5432/FlaskWebPostgreSQL'

# Render database configuration - THAY ĐỔI BẰNG URL THỰC TẾ CỦA BẠN
RENDER_DB_URL = os.environ.get(
    'RENDER_DATABASE_URL',
    'postgresql://flaskwebpostgresql_user:nrDeXdaJQ2GA9Bv04ISC2rdNpI7EKhYr@dpg-d47l9824d50c7388ofsg-a.singapore-postgres.render.com/flaskwebpostgresql'
)

class UserMigration:
    def __init__(self, local_url, render_url):
        self.local_url = local_url
        self.render_url = render_url
        self.local_engine = None
        self.render_engine = None
        self.users_data = []

    def connect_databases(self):
        """Kết nối đến cả hai database"""
        try:
            print(f"[*] Kết nối đến Local Database...")
            self.local_engine = create_engine(
                self.local_url,
                poolclass=NullPool,
                connect_args={'connect_timeout': 10}
            )
            # Test connection
            with self.local_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("[✓] Local Database: OK")

            print(f"[*] Kết nối đến Render Database...")
            self.render_engine = create_engine(
                self.render_url,
                poolclass=NullPool,
                connect_args={'connect_timeout': 10}
            )
            # Test connection
            with self.render_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("[✓] Render Database: OK")

            return True
        except Exception as e:
            print(f"[✗] Lỗi kết nối database: {e}")
            return False

    def get_users_from_local(self):
        """Lấy tất cả users từ local database"""
        try:
            with self.local_engine.connect() as conn:
                # Thực hiện query SQL để lấy users
                query = text("SELECT id, username, email, password_hash, role FROM users ORDER BY id")
                result = conn.execute(query)
                self.users_data = [dict(row._mapping) for row in result]

            print(f"[✓] Lấy được {len(self.users_data)} users từ Local Database")
            return True
        except Exception as e:
            print(f"[✗] Lỗi khi lấy dữ liệu users: {e}")
            return False

    def preview_users(self):
        """Hiển thị preview dữ liệu sẽ migrate"""
        if not self.users_data:
            print("[!] Không có users để hiển thị")
            return

        print("\n" + "="*80)
        print("PREVIEW: Dữ liệu Users sẽ được migrate")
        print("="*80)
        print(f"Tổng số users: {len(self.users_data)}\n")

        for user in self.users_data:
            print(f"ID: {user['id']}")
            print(f"  Username: {user['username']}")
            print(f"  Email: {user['email']}")
            print(f"  Role: {user['role']}")
            print(f"  Password Hash: {user['password_hash'][:50]}...")
            print()

        print("="*80)

    def backup_users(self):
        """Backup dữ liệu users trước khi migrate"""
        try:
            backup_dir = os.path.join(os.path.dirname(__file__), 'backups')
            os.makedirs(backup_dir, exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(backup_dir, f'users_backup_{timestamp}.json')

            with open(backup_file, 'w', encoding='utf-8') as f:
                # Convert datetime objects để JSON serializable
                backup_data = [
                    {
                        **user,
                        'id': int(user['id'])
                    }
                    for user in self.users_data
                ]
                json.dump(backup_data, f, indent=2, ensure_ascii=False)

            print(f"[✓] Backup thành công: {backup_file}")
            return True
        except Exception as e:
            print(f"[✗] Lỗi backup dữ liệu: {e}")
            return False

    def clear_existing_users_on_render(self):
        """Xóa dữ liệu users hiện tại trên Render Database"""
        try:
            with self.render_engine.begin() as conn:
                # Xóa foreign key references trước
                conn.execute(text("DELETE FROM user_companies WHERE user_id IN (SELECT id FROM users)"))
                # Sau đó xóa users
                result = conn.execute(text("DELETE FROM users"))
                deleted_count = result.rowcount
                conn.commit()

            print(f"[✓] Xóa {deleted_count} users cũ trên Render Database")
            return True
        except Exception as e:
            print(f"[✗] Lỗi khi xóa dữ liệu: {e}")
            return False

    def migrate_users_to_render(self):
        """Migrate users từ local lên Render Database"""
        try:
            if not self.users_data:
                print("[!] Không có users để migrate")
                return False

            with self.render_engine.begin() as conn:
                # Disable foreign key checks tạm thời
                conn.execute(text("SET session_replication_role = REPLICA"))

                # Insert users
                for user in self.users_data:
                    insert_query = text("""
                        INSERT INTO users (id, username, email, password_hash, role)
                        VALUES (:id, :username, :email, :password_hash, :role)
                        ON CONFLICT (id) DO UPDATE SET
                            username = EXCLUDED.username,
                            email = EXCLUDED.email,
                            password_hash = EXCLUDED.password_hash,
                            role = EXCLUDED.role
                    """)
                    conn.execute(insert_query, user)

                # Enable foreign key checks
                conn.execute(text("SET session_replication_role = DEFAULT"))
                conn.commit()

            print(f"[✓] Migrate thành công {len(self.users_data)} users lên Render Database")
            return True
        except Exception as e:
            print(f"[✗] Lỗi khi migrate dữ liệu: {e}")
            return False

    def verify_migration(self):
        """Xác minh dữ liệu sau migration"""
        try:
            with self.render_engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) as count FROM users"))
                count = dict(result.first()._mapping)['count']

            if count == len(self.users_data):
                print(f"[✓] Xác minh thành công: {count} users trên Render Database")
                return True
            else:
                print(f"[✗] Số users không khớp! Local: {len(self.users_data)}, Render: {count}")
                return False
        except Exception as e:
            print(f"[✗] Lỗi xác minh: {e}")
            return False

    def close_connections(self):
        """Đóng kết nối"""
        if self.local_engine:
            self.local_engine.dispose()
        if self.render_engine:
            self.render_engine.dispose()


def main():
    parser = argparse.ArgumentParser(
        description='Migration script cho bảng users từ Local DB lên Render Database'
    )
    parser.add_argument(
        '--preview',
        action='store_true',
        help='Xem preview dữ liệu sẽ migrate'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Thực hiện migration (cần sự xác nhận)'
    )
    parser.add_argument(
        '--backup',
        action='store_true',
        help='Chỉ backup dữ liệu mà không migrate'
    )
    parser.add_argument(
        '--local-url',
        default=LOCAL_DB_URL,
        help='URL Local Database (default: LOCAL_DB_URL)'
    )
    parser.add_argument(
        '--render-url',
        default=RENDER_DB_URL,
        help='URL Render Database (default: từ environment hoặc hardcoded)'
    )

    args = parser.parse_args()

    # Kiểm tra ít nhất một action được chỉ định
    if not (args.preview or args.execute or args.backup):
        parser.print_help()
        return

    # Tạo migration object
    migration = UserMigration(args.local_url, args.render_url)

    # Kết nối databases
    if not migration.connect_databases():
        return

    # Lấy dữ liệu users từ local
    if not migration.get_users_from_local():
        migration.close_connections()
        return

    # Preview mode
    if args.preview:
        migration.preview_users()

    # Backup mode
    if args.backup:
        migration.backup_users()

    # Execute migration
    if args.execute:
        print("\n" + "="*80)
        print("⚠️  CẢNH BÁO: Bạn sắp migrate dữ liệu users lên Render Database")
        print("="*80)
        print(f"Số users sẽ migrate: {len(migration.users_data)}")
        print("\nDữ liệu cũ trên Render Database sẽ bị XÓA!")
        print("\nBackup được tạo tại: backups/users_backup_TIMESTAMP.json")

        confirmation = input("\nBạn có chắc chắn? (yes/no): ").strip().lower()

        if confirmation == 'yes':
            print("\n[*] Bắt đầu migration...")

            # Backup trước
            if migration.backup_users():
                # Xóa users cũ
                migration.clear_existing_users_on_render()

                # Migrate users
                if migration.migrate_users_to_render():
                    # Xác minh
                    migration.verify_migration()
                    print("\n[✓] Migration hoàn thành!")
            else:
                print("[✗] Backup thất bại, hủy migration")
        else:
            print("[*] Migration bị hủy")

    # Đóng kết nối
    migration.close_connections()


if __name__ == '__main__':
    main()
