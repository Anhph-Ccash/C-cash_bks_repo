# 🎯 Migration Scripts - Tổng Quan Nhanh

## ✨ Các Scripts Vừa Tạo

| Script | Mục Đích | Command |
|--------|----------|---------|
| **migrate_users_to_render.py** | Migrate users từ local → Render | `python migrate_users_to_render.py --execute` |
| **restore_users_from_backup.py** | Restore từ backup JSON | `python restore_users_from_backup.py FILE.json --execute` |
| **check_databases.py** | Kiểm tra 2 databases | `python check_databases.py --all` |
| **manage_backups.py** | Quản lý backup files | `python manage_backups.py list` |

---

## 🚀 Cách Sử Dụng Nhanh (Tuần Tự)

### 1️⃣ Kiểm Tra Local Database
```bash
cd e:\C-cash_bks_repo
python check_databases.py --local
```
✅ Kết quả: Có 11 users sẵn sàng migrate

### 2️⃣ Xem Preview
```bash
python migrate_users_to_render.py --preview
```
✅ Xem trước 11 users sẽ được migrate

### 3️⃣ Tạo Backup
```bash
python migrate_users_to_render.py --backup
```
✅ Backup file được lưu ở: `backups/users_backup_TIMESTAMP.json`

### 4️⃣ Thực Hiện Migration
```bash
python migrate_users_to_render.py --execute
```
⚠️ **Nhập `yes` khi được hỏi để xác nhận**

### 5️⃣ Kiểm Tra Kết Quả
```bash
python check_databases.py --render
```
✅ Verify 11 users đã được migrate lên Render

---

## 📊 Dữ Liệu Hiện Tại

### Local Database - **11 Users Ready**
```
3  - admin (admin@example.com) [ADMIN]
5  - user21 (user2@gmail.com)
6  - user3 (user3@gmail.com)
7  - user4 (user4@gmail.com)
8  - user5 (user5@gmail.com)
9  - user33 (anh.33@gmail.com)
10 - user32 (user32@gmail.com)
11 - Tri01 (tri01@gmail.com)
12 - testuser (test@test.com)
13 - anhph9 (anhph9@gmail.com) [ADMIN]
14 - anh.pham (anh.pham@c-cashglobal.com) [ADMIN]
```

---

## 📁 File Structure

```
C-cash_bks_repo/
├── migrate_users_to_render.py        ← Main migration script
├── restore_users_from_backup.py      ← Restore script
├── check_databases.py                ← Database check script
├── manage_backups.py                 ← Backup management
├── MIGRATION_README.md               ← Full documentation
├── MIGRATION_GUIDE.md                ← Step by step guide
├── .env.migration.example            ← Environment variables template
└── backups/                          ← Backup files (auto-created)
    └── users_backup_20241124_*.json
```

---

## ⚙️ Configuration

### Option 1: Environment Variable (Recommended)
```powershell
$env:RENDER_DATABASE_URL = "postgresql://user:password@host/database"
python migrate_users_to_render.py --execute
```

### Option 2: Command Line
```bash
python migrate_users_to_render.py --execute --render-url "postgresql://user:password@host/database"
```

### Option 3: Edit Script
Edit `migrate_users_to_render.py` line 18:
```python
RENDER_DB_URL = 'your-actual-render-db-url'
```

---

## ✅ Migration Checklist

- [ ] PostgreSQL Local đang chạy? → `python check_databases.py --local`
- [ ] Render Database URL sẵn sàng? → Có từ Render Dashboard
- [ ] Preview dữ liệu? → `python migrate_users_to_render.py --preview`
- [ ] Backup tạo thành công? → Check `backups/` folder
- [ ] Migration hoàn thành? → Xác nhận yes/no prompt
- [ ] Verify kết quả? → `python check_databases.py --render`

---

## 🔄 Common Scenarios

### Migration Lần Đầu Tiên
```bash
python migrate_users_to_render.py --preview
python migrate_users_to_render.py --backup
python migrate_users_to_render.py --execute  # Nhập: yes
python check_databases.py --render
```

### Update Dữ Liệu Thêm (có dữ liệu cũ)
```bash
# Script tự động xóa dữ liệu cũ
python migrate_users_to_render.py --execute
```

### Hoàn Tác (Rollback)
```bash
python restore_users_from_backup.py backups/users_backup_TIMESTAMP.json --execute
```

---

## 📞 Troubleshooting

### ❌ Lỗi: "could not translate host name"
**Nguyên nhân**: PostgreSQL local không chạy
```bash
# Khởi động PostgreSQL (Windows)
# Services → PostgreSQL → Start
```

### ❌ Lỗi: "password authentication failed"
**Nguyên nhân**: Username/password sai
```bash
# Default credentials: postgres / 11223344
python check_databases.py --local  # Test kết nối
```

### ❌ Lỗi: "connection refused" (Render)
**Nguyên nhân**: URL Render không chính xác
```bash
# Copy lại từ Render Dashboard → PostgreSQL → Info
python check_databases.py --render --render-url "correct-url"
```

---

## 💾 Backup Management

### Liệt kê tất cả backups
```bash
python manage_backups.py list
```

### Xem backup mới nhất
```bash
python manage_backups.py latest
```

### Xóa backup cũ (giữ lại 5 cái mới nhất)
```bash
python manage_backups.py cleanup --keep 5
```

### Xóa một backup cụ thể
```bash
python manage_backups.py delete users_backup_20241124_143022.json
```

---

## 🔐 Security Notes

✅ **An toàn**:
- Password hashes được bảo vệ (PBKDF2:SHA256)
- Backup files không được commit vào Git
- Database URLs nên sử dụng env variables
- Confirmation yêu cầu trước mỗi migration

⚠️ **Lưu ý**:
- Giữ backup files an toàn
- Không share credentials qua chat/email
- Review preview trước khi migrate
- Test trên staging trước production

---

## 📚 Documents

Để biết thêm chi tiết:
- **MIGRATION_README.md** - Hướng dẫn chi tiết (20 trang)
- **MIGRATION_GUIDE.md** - Step-by-step guide
- **README.md** - Project overview

---

**Last Updated**: November 24, 2024
**Status**: ✅ Ready to Use
**Python**: 3.7+
**Database**: PostgreSQL 12+
