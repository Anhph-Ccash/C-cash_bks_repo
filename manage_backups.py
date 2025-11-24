#!/usr/bin/env python
"""
Helper script để liệt kê và quản lý backup files
"""

import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

BACKUPS_DIR = os.path.join(os.path.dirname(__file__), 'backups')

def list_backups():
    """Liệt kê tất cả backup files"""
    if not os.path.exists(BACKUPS_DIR):
        print(f"[!] Thư mục backups không tồn tại: {BACKUPS_DIR}")
        return []

    backup_files = sorted(
        Path(BACKUPS_DIR).glob('users_backup_*.json'),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    if not backup_files:
        print(f"[!] Không tìm thấy backup files trong {BACKUPS_DIR}")
        return []

    print("="*80)
    print("AVAILABLE BACKUPS")
    print("="*80)

    for idx, backup_file in enumerate(backup_files, 1):
        file_size = backup_file.stat().st_size
        file_time = datetime.fromtimestamp(backup_file.stat().st_mtime)

        # Read file to get user count
        try:
            import json
            with open(backup_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                user_count = len(data)
        except:
            user_count = "?"

        marker = "← LATEST" if idx == 1 else ""

        print(f"\n[{idx}] {backup_file.name}")
        print(f"    Size: {file_size:,} bytes")
        print(f"    Time: {file_time}")
        print(f"    Users: {user_count}")
        print(f"    Path: {backup_file}")
        print(f"    {marker}")

    print("\n" + "="*80)
    return [str(f) for f in backup_files]

def get_latest_backup():
    """Lấy backup file mới nhất"""
    backups = list_backups()
    if backups:
        return backups[0]
    return None

def delete_backup(filename):
    """Xóa một backup file"""
    backup_path = os.path.join(BACKUPS_DIR, filename)

    if not os.path.exists(backup_path):
        print(f"[✗] Backup file không tồn tại: {backup_path}")
        return False

    try:
        os.remove(backup_path)
        print(f"[✓] Đã xóa backup: {filename}")
        return True
    except Exception as e:
        print(f"[✗] Lỗi xóa backup: {e}")
        return False

def cleanup_old_backups(keep=5):
    """Xóa các backup cũ, chỉ giữ lại N backup mới nhất"""
    if not os.path.exists(BACKUPS_DIR):
        print(f"[!] Thư mục backups không tồn tại")
        return

    backup_files = sorted(
        Path(BACKUPS_DIR).glob('users_backup_*.json'),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )

    if len(backup_files) <= keep:
        print(f"[!] Chỉ có {len(backup_files)} backups, không cần xóa (giữ lại {keep})")
        return

    files_to_delete = backup_files[keep:]

    print(f"[*] Sẽ xóa {len(files_to_delete)} backup files (giữ lại {keep})")

    for backup_file in files_to_delete:
        try:
            os.remove(backup_file)
            print(f"[✓] Đã xóa: {backup_file.name}")
        except Exception as e:
            print(f"[✗] Lỗi xóa {backup_file.name}: {e}")

def main():
    parser = argparse.ArgumentParser(
        description='Quản lý backup files'
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # List command
    subparsers.add_parser('list', help='Liệt kê tất cả backup files')

    # Latest command
    subparsers.add_parser('latest', help='Hiển thị backup file mới nhất')

    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Xóa một backup file')
    delete_parser.add_argument('filename', help='Tên backup file cần xóa')

    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Xóa các backup cũ')
    cleanup_parser.add_argument(
        '--keep',
        type=int,
        default=5,
        help='Số backup files giữ lại (default: 5)'
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'list':
        list_backups()

    elif args.command == 'latest':
        latest = get_latest_backup()
        if latest:
            print(f"Latest backup: {latest}")
        else:
            print("[!] Không tìm thấy backup files")

    elif args.command == 'delete':
        if delete_backup(args.filename):
            print("\n" + "="*80)
            print("Remaining backups:")
            print("="*80)
            list_backups()

    elif args.command == 'cleanup':
        print(f"[*] Cleanup: Giữ lại {args.keep} backup files mới nhất")
        cleanup_old_backups(keep=args.keep)
        print("\n" + "="*80)
        print("Remaining backups:")
        print("="*80)
        list_backups()

if __name__ == '__main__':
    main()
