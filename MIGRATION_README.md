# 📊 Migration Scripts - Hướng Dẫn Sử Dụng

## 📁 Các Scripts Có Sẵn

Bạn vừa tạo 3 scripts để quản lý migration dữ liệu users:

### 1. `migrate_users_to_render.py` - Script Migration Chính
**Chức năng**: Migrate dữ liệu users từ Local PostgreSQL → Render Database

**Tính năng**:
- ✅ Preview dữ liệu trước khi migrate
- ✅ Backup tự động trước migration
- ✅ Xóa dữ liệu cũ trên Render DB
- ✅ Xác minh dữ liệu sau migration
- ⚠️ Yêu cầu xác nhận trước thực hiện

### 2. `restore_users_from_backup.py` - Script Restore
**Chức năng**: Phục hồi dữ liệu từ backup JSON

**Tính năng**:
- ✅ Restore từ backup JSON file
- ✅ Preview dữ liệu trước restore
- ✅ Xác minh dữ liệu sau restore
- ⚠️ Yêu cầu xác nhận trước thực hiện

### 3. `check_databases.py` - Script Kiểm Tra
**Chức năng**: Kiểm tra kết nối và dữ liệu trong cả 2 databases

**Tính năng**:
- ✅ Test kết nối đến databases
- ✅ Hiển thị schema bảng users
- ✅ Liệt kê tất cả users
- ✅ Kiểm tra bảng user_companies

---

## 🚀 Quick Start - Các Bước Migration

### Bước 1: Kiểm Tra Dữ Liệu Hiện Tại (5 phút)

```bash
cd e:\C-cash_bks_repo
python check_databases.py --all
```

**Output sẽ cho thấy:**
- ✓ Local Database: 11 users
- ? Render Database: (sẽ hiển thị số users hiện tại)

### Bước 2: Preview Dữ Liệu Sẽ Migrate (2 phút)

```bash
python migrate_users_to_render.py --preview
```

**Output:**
```
[✓] Lấy được 11 users từ Local Database

================================================================================
PREVIEW: Dữ liệu Users sẽ được migrate
================================================================================
Tổng số users: 11

ID: 3
  Username: admin
  Email: anh.pham@c-cashglobal.com
  Role: admin
  ...
```

### Bước 3: Tạo Backup (2 phút)

```bash
python migrate_users_to_render.py --backup
```

**Output:**
```
[✓] Backup thành công: backups/users_backup_20241124_143022.json
```

Backup file được lưu ở thư mục `backups/` (có thể restore nếu cần)

### Bước 4: Thực Hiện Migration (5 phút)

```bash
python migrate_users_to_render.py --execute
```

**Quá trình:**
1. Yêu cầu xác nhận (nhập `yes`)
2. Backup dữ liệu
3. Xóa dữ liệu cũ trên Render DB
4. Migrate 11 users lên Render DB
5. Xác minh dữ liệu

**Output cuối:**
```
[✓] Migration hoàn thành!
```

### Bước 5: Xác Minh Kết Quả (2 phút)

```bash
python check_databases.py --render
```

Kiểm tra:
- Render Database: 11 users ✓
- Tất cả users có đúng dữ liệu ✓

---

## 📝 Chi Tiết Các Commands

### Migration Script

```bash
# Chỉ preview
python migrate_users_to_render.py --preview

# Chỉ backup
python migrate_users_to_render.py --backup

# Preview + Backup
python migrate_users_to_render.py --preview --backup

# Thực hiện migration (yêu cầu xác nhận)
python migrate_users_to_render.py --execute

# Sử dụng custom database URLs
python migrate_users_to_render.py --execute \
  --local-url "postgresql://user:pass@localhost/dbname" \
  --render-url "postgresql://user:pass@host/dbname"
```

### Restore Script

```bash
# Preview backup trước khi restore
python restore_users_from_backup.py backups/users_backup_20241124_143022.json --preview

# Restore từ backup (yêu cầu xác nhận)
python restore_users_from_backup.py backups/users_backup_20241124_143022.json --execute

# Backup file mới nhất (bash/powershell)
python restore_users_from_backup.py (Get-ChildItem backups | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName --preview
```

### Check Databases Script

```bash
# Kiểm tra cả 2 databases
python check_databases.py --all

# Chỉ kiểm tra Local DB
python check_databases.py --local

# Chỉ kiểm tra Render DB
python check_databases.py --render
```

---

## 📊 Dữ Liệu Hiện Tại (Ngày 24/11/2024)

### Local Database
```
Tổng users: 11
├── ID: 3 - admin (anh.pham@c-cashglobal.com) - Role: admin
├── ID: 5 - user21 (user2@gmail.com) - Role: user
├── ID: 6 - user3 (user3@gmail.com) - Role: user
├── ID: 7 - user4 (user4@gmail.com) - Role: user
├── ID: 8 - user5 (user5@gmail.com) - Role: user
├── ID: 9 - user33 (anh.33@gmail.com) - Role: user
├── ID: 10 - user32 (user32@gmail.com) - Role: user
├── ID: 11 - Tri01 (tri01@gmail.com) - Role: user
├── ID: 12 - testuser (test@test.com) - Role: user
├── ID: 13 - anhph9 (anhph9@gmail.com) - Role: admin
└── ID: 14 - anh.pham (anh.pham@c-cashglobal.com) - Role: admin
```

### Render Database
(Sẽ được cập nhật sau migration)

---

## ⚠️ Lưu Ý Quan Trọng

### Trước Migration
- [ ] Backup Local Database (tự động bởi script)
- [ ] Kiểm tra Render Database URL có chính xác?
- [ ] PostgreSQL Local có đang chạy?
- [ ] Có đủ disk space trên cả 2 servers?

### Trong Migration
- ❌ **KHÔNG** ngắt quá trình migration
- ❌ **KHÔNG** đóng terminal
- ❌ **KHÔNG** thay đổi database khi migration đang chạy

### Sau Migration
- ✅ Verify dữ liệu bằng `check_databases.py --render`
- ✅ Test application trên Render Database
- ✅ Giữ backup files an toàn (trong thư mục `backups/`)

---

## 🔄 Các Scenario Khác Nhau

### Scenario 1: Migration Lần Đầu
```bash
# 1. Check current state
python check_databases.py --all

# 2. Preview migration
python migrate_users_to_render.py --preview

# 3. Create backup
python migrate_users_to_render.py --backup

# 4. Execute migration
python migrate_users_to_render.py --execute

# 5. Verify result
python check_databases.py --render
```

### Scenario 2: Migration Lần Thứ 2 (có dữ liệu cũ trên Render)
```bash
# Script tự động xóa dữ liệu cũ, vì vậy chỉ cần:
python migrate_users_to_render.py --execute
```

### Scenario 3: Phục Hồi Từ Backup
```bash
# Nếu migration không thành công, restore từ backup
python restore_users_from_backup.py backups/users_backup_20241124_143022.json --execute
```

### Scenario 4: So Sánh 2 Database
```bash
# Mở 2 terminals
# Terminal 1: Local DB
python check_databases.py --local

# Terminal 2: Render DB
python check_databases.py --render

# So sánh kết quả
```

---

## 🔐 Bảo Mật

### Database URLs
- ✅ Không commit credentials vào Git
- ✅ Sử dụng environment variables: `RENDER_DATABASE_URL`
- ✅ Hoặc truyền via command line: `--render-url "..."`

### Password Hashes
- ✅ Password hashes từ local sẽ được giữ nguyên (không thay đổi)
- ✅ Không có password text nào được lưu trữ

### Backup Files
- ✅ Backup được lưu ở thư mục `backups/` (ignored in .gitignore)
- ✅ Chứa tất cả dữ liệu users (bao gồm password hashes)
- ✅ Giữ backup an toàn hoặc xóa sau khi verify thành công

---

## 🐛 Troubleshooting

### Q: Lỗi "could not translate host name "localhost""
**A:** PostgreSQL local không chạy
```bash
# Windows: Khởi động PostgreSQL Services
# Linux: sudo systemctl start postgresql
# macOS: brew services start postgresql
```

### Q: Lỗi "password authentication failed"
**A:** Username hoặc password sai
```bash
# Kiểm tra LOCAL_DB_URL trong config.py
# Default: postgres / 11223344
python check_databases.py --local
```

### Q: Lỗi kết nối Render Database
**A:** URL không chính xác hoặc network bị chặn
```bash
# 1. Copy đúng URL từ Render Dashboard
# 2. Test kết nối: python check_databases.py --render
# 3. Kiểm tra firewall
```

### Q: Migration bị interrupt
**A:** Có thể data không đầy đủ, khôi phục từ backup
```bash
python restore_users_from_backup.py backups/users_backup_TIMESTAMP.json --execute
```

### Q: Backup file bị mất
**A:** Không thể khôi phục, nhưng có thể migrate lại từ Local
```bash
python migrate_users_to_render.py --execute
# Lưu ý: Dữ liệu trên Render sẽ bị xóa
```

---

## 📞 Support

Nếu gặp vấn đề:
1. Chạy `python check_databases.py --all` để xem tình trạng
2. Xem logs trong terminal output
3. Kiểm tra backup files trong thư mục `backups/`
4. Liên hệ team dev với thông tin:
   - Error message (full text)
   - Database URLs (không bao gồm password)
   - Step đang thực hiện

---

**Last Updated**: 2024-11-24
**Python Version**: 3.7+
**Database**: PostgreSQL
