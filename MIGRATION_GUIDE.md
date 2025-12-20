# Hướng Dẫn Migration Dữ Liệu Bảng Users Lên Render Database

## 📋 Yêu Cầu Tiên Quyết

1. **Local PostgreSQL Database** phải đang chạy
2. **Render Database** đã được tạo
3. **Python 3.7+** và các package cần thiết: `sqlalchemy`, `psycopg2-binary`

## 🔧 Chuẩn Bị

### 1. Cài Đặt Dependencies
```bash
pip install sqlalchemy psycopg2-binary
```

### 2. Xác Nhận Render Database URL

Truy cập vào Render Dashboard:
1. Vào project PostgreSQL của bạn
2. Copy connection string từ mục "Connections"
3. URL sẽ có dạng: `postgresql://user:password@host/database`

### 3. Cập Nhật Script (Nếu Cần)

Mở file `migrate_users_to_render.py` và cập nhật:
```python
# Tùy chọn A: Cài đặt Environment Variable (Khuyến nghị)
export RENDER_DATABASE_URL="postgresql://user:password@host/database"

# Tùy chọn B: Truyền vào command line
python migrate_users_to_render.py --execute --render-url "postgresql://user:password@host/database"
```

## 📝 Cách Sử Dụng

### Step 1: Preview Dữ Liệu (Xem trước)
```bash
cd e:\C-cash_bks_repo
python migrate_users_to_render.py --preview
```

**Output:**
```
[✓] Local Database: OK
[✓] Render Database: OK
[✓] Lấy được 5 users từ Local Database

================================================================================
PREVIEW: Dữ liệu Users sẽ được migrate
================================================================================
Tổng số users: 5

ID: 1
  Username: admin
  Email: anh.pham@c-cashglobal.com
  Role: admin
  Password Hash: pbkdf2:sha256:600000$...

...
```

### Step 2: Backup Dữ Liệu (Tạo backup)
```bash
python migrate_users_to_render.py --backup
```

**Output:**
```
[✓] Lấy được 5 users từ Local Database
[✓] Backup thành công: backups/users_backup_20241124_143022.json
```

Backup file được lưu ở: `backups/users_backup_TIMESTAMP.json`

### Step 3: Thực Hiện Migration (Migrate dữ liệu)
```bash
python migrate_users_to_render.py --execute
```

**Interactive Confirmation:**
```
================================================================================
⚠️  CẢNH BÁO: Bạn sắp migrate dữ liệu users lên Render Database
================================================================================
Số users sẽ migrate: 5

Dữ liệu cũ trên Render Database sẽ bị XÓA!

Backup được tạo tại: backups/users_backup_TIMESTAMP.json

Bạn có chắc chắn? (yes/no): yes

[*] Bắt đầu migration...
[✓] Backup thành công: backups/users_backup_20241124_143022.json
[✓] Xóa 0 users cũ trên Render Database
[✓] Migrate thành công 5 users lên Render Database
[✓] Xác minh thành công: 5 users trên Render Database

[✓] Migration hoàn thành!
```

## 🔗 Các Lệnh Kết Hợp

### Xem preview + Backup trong 1 lần
```bash
python migrate_users_to_render.py --preview --backup
```

### Toàn bộ quy trình an toàn (Khuyến nghị)
```bash
# 1. Preview dữ liệu
python migrate_users_to_render.py --preview

# 2. Backup dữ liệu
python migrate_users_to_render.py --backup

# 3. Verify backup
ls -la backups/

# 4. Migrate dữ liệu
python migrate_users_to_render.py --execute
```

## ⚙️ Options Chi Tiết

| Option | Mô Tả |
|--------|-------|
| `--preview` | Hiển thị dữ liệu sẽ được migrate (không thay đổi gì) |
| `--execute` | Thực hiện migration (yêu cầu xác nhận) |
| `--backup` | Tạo backup file JSON của dữ liệu |
| `--local-url URL` | URL Local Database (default: `postgresql://postgres:11223344@localhost:5432/FlaskWebPostgreSQL`) |
| `--render-url URL` | URL Render Database (default: từ `RENDER_DATABASE_URL` env var) |

## 🔄 Điều Gì Xảy Ra Trong Quá Trình Migration

1. **Kết nối** cả 2 database
2. **Lấy dữ liệu** từ local database (bảng `users`)
3. **Tạo backup** JSON file (để có thể phục hồi nếu cần)
4. **Xóa dữ liệu** cũ trên Render Database (cả bảng `users` và liên kết trong `user_companies`)
5. **Insert dữ liệu** từ local vào Render Database
6. **Xác minh** dữ liệu sau migration

## ⚠️ Lưu Ý Quan Trọng

1. **Backup Trước**: Script tự động tạo backup, nhưng hãy kiểm tra file backup được tạo
2. **Foreign Keys**: Script tự động xử lý foreign key constraints
3. **Password Hashes**: Password hashes từ local sẽ được giữ nguyên
4. **Connection Timeout**: Nếu kết nối bị timeout, kiểm tra:
   - Local PostgreSQL có đang chạy?
   - URL database có chính xác?
   - Firewall có chặn kết nối?

## 🔍 Troubleshooting

### Lỗi: "could not translate host name "localhost" to address"
```bash
# Kiểm tra PostgreSQL local có đang chạy
# Windows: Services > PostgreSQL > restart
# Linux: sudo systemctl restart postgresql
```

### Lỗi: "password authentication failed"
```bash
# Kiểm tra username và password trong LOCAL_DB_URL
# Mặc định: postgres / 11223344
python migrate_users_to_render.py --preview --local-url "postgresql://postgres:YOUR_PASSWORD@localhost:5432/FlaskWebPostgreSQL"
```

### Lỗi: "connect to Render database"
```bash
# Kiểm tra RENDER_DATABASE_URL
# Đảm bảo copy đúng URL từ Render Dashboard
export RENDER_DATABASE_URL="postgresql://user:password@host/database"
python migrate_users_to_render.py --preview
```

### Muốn hoàn tác (undo) migration
```bash
# Restore từ backup JSON
python restore_users_from_backup.py backups/users_backup_20241124_143022.json
```

## 📊 Kiểm Tra Kết Quả

Sau khi migration hoàn thành, bạn có thể kiểm tra:

### Cách 1: Dùng SQL trực tiếp
```bash
# Trên Render Database
psql "postgresql://user:password@host/database"
SELECT COUNT(*) as total_users FROM users;
```

### Cách 2: Dùng application
```bash
# Deploy lên Render
# Truy cập admin panel -> check users
```

### Cách 3: Kiểm tra backup
```bash
# Xem file backup
cat backups/users_backup_TIMESTAMP.json
```

## 💾 Recovery (Nếu có vấn đề)

Nếu cần phục hồi dữ liệu từ backup:

```bash
python restore_users_from_backup.py backups/users_backup_20241124_143022.json --execute
```

---

**Hỗ trợ**: Nếu gặp vấn đề, hãy kiểm tra logs hoặc liên hệ team dev.
