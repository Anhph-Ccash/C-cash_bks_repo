# 👨‍💼 Hướng Dẫn Tạo User Admin

## 📋 Tính Năng Quản Lý Người Dùng

Application đã hỗ trợ tạo user với vai trò **Admin** hoặc **Người dùng thường**.

---

## ✅ Cách Tạo User Admin

### **Bước 1: Đăng Nhập với Admin Account**

- URL: `https://c-cash-bks-mgmt.onrender.com/login`
- Tài khoản admin (mặc định):
  - Username: `admin`
  - Password: `admin`

### **Bước 2: Vào Trang Quản Lý Người Dùng**

1. Từ **Dashboard**, click menu: **Quản lý** → **Người dùng**
2. Hoặc vào trực tiếp: `/admin/admin-users`

### **Bước 3: Nhấn "➕ Thêm" Button**

- Modal **"Thêm người dùng mới"** sẽ hiện lên

### **Bước 4: Điền Thông Tin**

Điền các trường bắt buộc:

| Field | Giá Trị | Ghi Chú |
|-------|--------|--------|
| **Tên đăng nhập** | `admin_user_1` | Duy nhất, không được trùng |
| **Email** | `admin_user_1@example.com` | Duy nhất, không được trùng |
| **Mật khẩu** | `password123` | Min 8 ký tự, khuyến nghị mạnh |
| **Vai trò** | `Quản trị viên` | **Đây là chính điểm để set admin** |
| **Công ty** | Chọn 1 hoặc nhiều | Giữ Ctrl/Cmd để chọn nhiều |

**QUAN TRỌNG**: Dropdown **Vai trò** có 2 option:
- ✅ **Người dùng** - User thường (default)
- ✅ **Quản trị viên** - Admin user (có quyền cao)

### **Bước 5: Nhấn "Thêm người dùng"**

- User sẽ được tạo ngay lập tức
- Flash message thành công sẽ hiển thị
- User mới sẽ xuất hiện trong bảng danh sách

---

## 📝 Ví Dụ Cụ Thể

### Tạo User Admin Mới:

```
Tên đăng nhập:    quang.admin
Email:            quang.admin@example.com
Mật khẩu:         MySecurePassword2024!
Vai trò:          Quản trị viên ← QUAN TRỌNG
Công ty:          Ngân hàng A, Ngân hàng B
```

### Sau khi Tạo:

User này có thể:
- ✅ Đăng nhập vào dashboard
- ✅ Quản lý các users khác
- ✅ Quản lý các công ty
- ✅ Quản lý cấu hình ngân hàng
- ✅ Xem logs toàn hệ thống

---

## 🔐 Quyền Của Admin User

Người dùng với role **admin** có thể:

1. **Quản lý Người dùng** (`/admin/admin-users`)
   - Thêm user mới
   - Chỉnh sửa user
   - Xóa user
   - Gán công ty cho user

2. **Quản lý Công ty** (`/admin/admin-companies`)
   - Xem danh sách công ty
   - Cấu hình SFTP cho công ty

3. **Quản lý Cấu hình Ngân hàng** (`/admin/admin-bank-configs`)
   - Thêm/chỉnh sửa cấu hình ngân hàng
   - Quản lý template file

4. **Xem Logs**
   - Toàn bộ logs của hệ thống
   - Logs upload, xử lý statements

---

## ✏️ Cách Sửa User (Đổi Role)

Nếu muốn đổi một user từ **Người dùng** thành **Admin**:

### **Bước 1**: Vào `/admin/admin-users`

### **Bước 2**: Click nút **✏️ Sửa** trên user cần đổi

### **Bước 3**: Trong modal:
- Đổi dropdown **Vai trò** từ `Người dùng` → `Quản trị viên`
- Click **Cập nhật**

### **Kết quả**: User sẽ trở thành Admin ngay lập tức

---

## 🗑️ Cách Xóa User

Nếu cần xóa một user admin:

1. Click nút **🗑️ Xóa** trên user
2. Confirm popup sẽ hỏi xác nhận
3. Click **OK** để xóa

**Lưu ý**: Xóa không thể hoàn tác!

---

## 🔍 Xác Minh Role Đã Set Đúng

### Cách 1: Xem Bảng Users
- Cột **Vai trò** sẽ hiển thị badge:
  - 🔴 **Quản trị viên** (Admin) - Badge đỏ
  - ⚫ **Người dùng** (User) - Badge xám

### Cách 2: Đăng Nhập với User Admin
- Nếu có quyền vào `/admin/admin-users` → Là Admin ✓
- Nếu không thấy menu Admin → Là User thường ✗

### Cách 3: Kiểm tra Database
```sql
SELECT username, role FROM users WHERE role = 'admin';
```

---

## 🎯 Common Issues

| Vấn Đề | Nguyên Nhân | Cách Fix |
|--------|-----------|---------|
| Không thấy Vai trò dropdown | JavaScript chưa load | F5 refresh page |
| Không thể chọn "Quản trị viên" | Permission issue | Logout + login lại |
| User được tạo nhưng role sai | Lỗi submit form | Check console logs |
| Không thể xem admin users | Not admin account | Đăng nhập bằng admin |

---

## 💡 Best Practices

1. **Tạo 2-3 Admin Users**
   - Tránh trường hợp 1 account bị khóa/quên mật khẩu
   - Chia sẻ quyền quản lý

2. **Mật Khẩu Mạnh**
   - Nên dùng mật khẩu dài (12+ ký tự)
   - Mix: UPPERCASE + lowercase + numbers + symbols

3. **Gán Công Ty Đúng**
   - Mỗi admin nên được gán công ty cụ thể
   - Giới hạn quyền truy cập vào dữ liệu công ty

4. **Audit Log**
   - Kiểm tra logs khi có thay đổi quan trọng
   - Xem ai tạo/xóa users

---

## 📊 Database Schema

Bảng `users`:
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'user',  -- 'admin' or 'user'
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Role Values**:
- `'admin'` - Quản trị viên
- `'user'` - Người dùng thường

---

## 🔗 Related Files

- **Backend**: `routes/routes_admin.py` (function `add_user()`)
- **Frontend**: `templates/admin_users.html` (modal "Add User")
- **Model**: `models/user.py` (User model with role field)

---

## ✨ Recap

| Bước | Chi Tiết |
|------|---------|
| 1 | Đăng nhập với admin account |
| 2 | Vào **Quản lý → Người dùng** |
| 3 | Click **➕ Thêm** |
| 4 | Điền thông tin, **Vai trò: Quản trị viên** |
| 5 | Click **Thêm người dùng** |
| ✅ | User admin được tạo thành công! |

---

**Cập nhật**: 24/11/2025
**Status**: ✅ Feature đã được support
