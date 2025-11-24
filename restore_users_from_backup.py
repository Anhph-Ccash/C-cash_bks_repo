#!/usr/bin/env python
"""
Script để restore dữ liệu users từ backup JSON
Cách sử dụng:
  python restore_users_from_backup.py backups/users_backup_20241124_143022.json --preview
  python restore_users_from_backup.py backups/users_backup_20241124_143022.json --execute
"""

import os
import sys
import json
import argparse
from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool

sys.path.insert(0, os.path.dirname(__file__))

# Render database configuration
RENDER_DB_URL = os.environ.get(
    'RENDER_DATABASE_URL',
    'postgresql://flaskwebpostgresql_user:nrDeXdaJQ2GA9Bv04ISC2rdNpI7EKhYr@dpg-d47l9824d50c7388ofsg-a.singapore-postgres.render.com/flaskwebpostgresql'
)

class UserRestore:
    def __init__(self, backup_file, render_url):
        self.backup_file = backup_file
        self.render_url = render_url
        self.render_engine = None
        self.users_data = []

    def load_backup_file(self):
        """Tải dữ liệu từ backup JSON file"""
        try:
            if not os.path.exists(self.backup_file):
                print(f"[✗] Backup file không tồn tại: {self.backup_file}")
                return False

            with open(self.backup_file, 'r', encoding='utf-8') as f:
                self.users_data = json.load(f)

            print(f"[✓] Đã tải {len(self.users_data)} users từ backup file")
            return True
        except Exception as e:
            print(f"[✗] Lỗi khi tải backup file: {e}")
            return False

    def connect_render_database(self):
        """Kết nối đến Render Database"""
        try:
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
            print(f"[✗] Lỗi kết nối Render Database: {e}")
            return False

    def preview_restore(self):
        """Hiển thị preview dữ liệu sẽ restore"""
        print("\n" + "="*80)
        print("PREVIEW: Dữ liệu Users sẽ được restore từ backup")
        print("="*80)
        print(f"Backup file: {self.backup_file}")
        print(f"Tổng số users: {len(self.users_data)}\n")

        for user in self.users_data:
            print(f"ID: {user.get('id')}")
            print(f"  Username: {user.get('username')}")
            print(f"  Email: {user.get('email')}")
            print(f"  Role: {user.get('role')}")
            print(f"  Password Hash: {str(user.get('password_hash'))[:50]}...")
            print()

        print("="*80)

    def restore_users(self):
        """Restore users từ backup vào Render Database"""
        try:
            with self.render_engine.begin() as conn:
                # Disable foreign key checks tạm thời
                conn.execute(text("SET session_replication_role = REPLICA"))

                # Xóa users cũ
                conn.execute(text("DELETE FROM user_companies"))
                conn.execute(text("DELETE FROM users"))

                # Insert users từ backup
                for user in self.users_data:
                    insert_query = text("""
                        INSERT INTO users (id, username, email, password_hash, role)
                        VALUES (:id, :username, :email, :password_hash, :role)
                    """)
                    conn.execute(insert_query, user)

                # Enable foreign key checks
                conn.execute(text("SET session_replication_role = DEFAULT"))
                conn.commit()

            print(f"[✓] Restore thành công {len(self.users_data)} users từ backup")
            return True
        except Exception as e:
            print(f"[✗] Lỗi khi restore dữ liệu: {e}")
            return False

    def verify_restore(self):
        """Xác minh dữ liệu sau restore"""
        try:
            with self.render_engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) as count FROM users"))
                count = dict(result.first()._mapping)['count']

            if count == len(self.users_data):
                print(f"[✓] Xác minh thành công: {count} users trên Render Database")
                return True
            else:
                print(f"[✗] Số users không khớp! Backup: {len(self.users_data)}, Render: {count}")
                return False
        except Exception as e:
            print(f"[✗] Lỗi xác minh: {e}")
            return False

    def close_connection(self):
        """Đóng kết nối"""
        if self.render_engine:
            self.render_engine.dispose()


def main():
    parser = argparse.ArgumentParser(
        description='Restore dữ liệu users từ backup JSON'
    )
    parser.add_argument(
        'backup_file',
        help='Đường dẫn đến backup JSON file (vd: backups/users_backup_20241124_143022.json)'
    )
    parser.add_argument(
        '--preview',
        action='store_true',
        help='Xem preview dữ liệu sẽ restore'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Thực hiện restore (cần sự xác nhận)'
    )
    parser.add_argument(
        '--render-url',
        default=RENDER_DB_URL,
        help='URL Render Database (default: từ environment hoặc hardcoded)'
    )

    args = parser.parse_args()

    # Kiểm tra ít nhất một action được chỉ định
    if not (args.preview or args.execute):
        parser.print_help()
        return

    # Tạo restore object
    restore = UserRestore(args.backup_file, args.render_url)

    # Tải backup file
    if not restore.load_backup_file():
        return

    # Kết nối Render Database
    if not restore.connect_render_database():
        return

    # Preview mode
    if args.preview:
        restore.preview_restore()

    # Execute restore
    if args.execute:
        print("\n" + "="*80)
        print("⚠️  CẢNH BÁO: Bạn sắp restore dữ liệu users từ backup")
        print("="*80)
        print(f"Backup file: {args.backup_file}")
        print(f"Số users sẽ restore: {len(restore.users_data)}")
        print("\nDữ liệu hiện tại trên Render Database sẽ bị XÓA!")

        confirmation = input("\nBạn có chắc chắn? (yes/no): ").strip().lower()

        if confirmation == 'yes':
            print("\n[*] Bắt đầu restore...")

            if restore.restore_users():
                restore.verify_restore()
                print("\n[✓] Restore hoàn thành!")
            else:
                print("[✗] Restore thất bại")
        else:
            print("[*] Restore bị hủy")

    # Đóng kết nối
    restore.close_connection()


if __name__ == '__main__':
    main()
