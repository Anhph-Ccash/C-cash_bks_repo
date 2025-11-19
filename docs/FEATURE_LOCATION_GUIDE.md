# 📍 Hướng dẫn Tìm Kiếm Các Chức Năng trong Project

## Route: `/admin/upload/logs`

### 📂 Cấu Trúc Thư Mục
```
blueprints/
└── upload/
    └── routes.py              ← Chứa tất cả logic xử lý

templates/
├── admin_logs.html            ← Giao diện admin logs (NEW)
├── logs.html                  ← Giao diện user logs
└── admin_base.html            ← Layout base cho admin

routes/
└── routes_admin.py            ← Route admin (bổ sung)
```

---

## 🔴 Route Định Nghĩa

### 1️⃣ **Route chính: `/upload/logs` → `view_logs()`**
📁 **File**: `blueprints/upload/routes.py` (dòng 203)

```python
@upload_bp.route("/logs")
@login_required
def view_logs():
    """View all logs with filtering and pagination"""
```

**Chức năng**:
- Hiển thị danh sách logs với phân trang
- Lọc theo: Mã ngân hàng, Trạng thái, Thời gian
- Phân trang: 30 logs/trang (có thể tuỳ chỉnh)

**URL**: `http://127.0.0.1:5001/upload/logs`

---

### 2️⃣ **Route admin: `/admin/upload/logs` → `admin_view_logs()`**
📁 **File**: `routes/routes_admin.py` (dòng 855)

```python
@admin_bp.route("/upload/logs")
@login_required
def admin_view_logs():
    """Admin view for logs"""
```

**Chức năng**:
- Hiển thị logs từ góc độ admin
- Có quyền xóa logs
- Sử dụng template `admin_logs.html`

**URL**: `http://127.0.0.1:5001/admin/upload/logs`

---

### 3️⃣ **Route xóa theo bộ lọc: `/upload/logs/delete`**
📁 **File**: `blueprints/upload/routes.py` (dòng 267)

```python
@upload_bp.route("/logs/delete", methods=["POST"])
@login_required
def delete_logs():
    """Delete logs by filter criteria"""
```

**Chức năng**:
- Xóa tất cả logs khớp với bộ lọc (bank_code, status, days)
- Yêu cầu admin role
- Ghi log hành động xóa

---

### 4️⃣ **Route xóa từng dòng: `/upload/logs/delete-selected` (NEW)**
📁 **File**: `blueprints/upload/routes.py` (dòng 325)

```python
@upload_bp.route("/logs/delete-selected", methods=["POST"])
@login_required
def delete_logs_selected():
    """Delete selected logs by their IDs"""
```

**Chức năng**:
- Xóa các logs được chọn (multi-select)
- Xóa từng dòng riêng lẻ
- Yêu cầu admin role

---

## 🎨 Template Files

### `admin_logs.html` (NEW - Enhanced)
📁 **File**: `templates/admin_logs.html`

**Chứa**:
- ✅ Form lọc (Mã ngân hàng, Trạng thái, Thời gian)
- ✅ Checkbox multi-select cho từng dòng
- ✅ Nút "Chọn tất cả" / "Bỏ chọn tất cả"
- ✅ Nút xóa từng dòng (🗑️)
- ✅ Nút xóa theo bộ lọc
- ✅ Nút xóa mục đã chọn
- ✅ Modal xác nhận xóa
- ✅ JavaScript xử lý UI

**Sections**:
```
Dòng 1-50     → Header + Filter Form
Dòng 51-70    → Bulk Actions Buttons
Dòng 71-130   → Table Header + Rows
Dòng 131-170  → Pagination
Dòng 171-220  → Delete Modal
Dòng 221-363  → JavaScript (Event Handlers)
```

---

### `logs.html`
📁 **File**: `templates/logs.html`

**Chứa**: Giao diện logs cho user (không có quyền xóa)

---

## 🧠 Database Models

### `BankLog` Model
📁 **File**: `models/bank_log.py`

**Fields**:
```python
id              # ID duy nhất
bank_code       # Mã ngân hàng (VCB, TCB, ...)
original_filename  # Tên file upload
status          # SUCCESS / ERROR
message         # Thông báo
processed_at    # Thời gian xử lý
filename        # Tên file lưu
detected_keywords  # Từ khóa phát hiện
```

---

## 📋 Database Query

### Lấy Logs Có Lọc
```python
query = BankLog.query

# Lọc theo mã ngân hàng
if bank_code:
    query = query.filter(BankLog.bank_code == bank_code)

# Lọc theo trạng thái
if status:
    query = query.filter(BankLog.status == status)

# Lọc theo thời gian (ngày)
if days > 0:
    since = datetime.utcnow() - timedelta(days=days)
    query = query.filter(BankLog.processed_at >= since)

# Phân trang
paginated = query.paginate(page=page, per_page=per_page)
logs = paginated.items
```

---

## 🔗 Navigation Menu

### Admin Menu
📁 **File**: `templates/admin_base.html` (dòng 35)

```html
<a class="nav-link" href="{{ url_for('admin.admin_view_logs') }}">
  📋 {{ _('Nhật ký') }}
</a>
```

### User Menu
📁 **File**: `templates/base_layout.html` (dòng 38)

```html
<a class="nav-link" href="{{ url_for('upload.view_logs') }}">
  📋 {{ _('Nhật ký') }}
</a>
```

---

## 🎯 Features (Chi Tiết)

### 1. **Xem Logs**
- Hiển thị danh sách logs với thông tin: thời gian, file, bank code, status, message
- Phân trang 30 logs/trang
- URL: `/upload/logs`

### 2. **Lọc Logs** (Filter)
- **Mã Ngân hàng**: Nhập text (VCB, TCB, ...)
- **Trạng thái**: Dropdown (Tất cả, Thành công, Lỗi)
- **Thời gian**: Dropdown (7 ngày, 30 ngày, 90 ngày, Tất cả)
- Nút "🔍 Lọc" để áp dụng

### 3. **Xóa Logs**

#### 3a. **Xóa từng dòng riêng lẻ** (Single Delete) - NEW
- Click nút 🗑️ ở cuối mỗi dòng
- Modal hiển thị tên file sẽ xóa
- Nhấn "🗑️ Xác nhận xóa" để xóa 1 log

#### 3b. **Xóa nhiều dòng** (Multi-Select Delete) - NEW
- ✓ Check các dòng muốn xóa (hoặc check "Chọn tất cả")
- ✓ Nhấn nút "🗑️ Xóa mục đã chọn"
- ✓ Modal hiển thị danh sách logs sẽ xóa
- ✓ Xác nhận xóa

#### 3c. **Xóa theo bộ lọc** (Filter-based Delete)
- Sau khi lọc, nhấn "🗑️ Xóa Nhật ký theo Bộ lọc"
- Modal hiển thị điều kiện lọc + số logs sẽ xóa
- Xác nhận xóa tất cả logs khớp bộ lọc

### 4. **Tải File Logs**
- Click "📥 Tải" để tải file gốc
- Yêu cầu log có file

---

## 🔐 Quyền Hạn (Permissions)

| Chức năng | User | Company | Admin |
|-----------|------|---------|-------|
| Xem logs | ✅ (riêng) | ✅ (công ty) | ✅ (tất cả) |
| Tải file | ✅ | ✅ | ✅ |
| Xóa logs | ❌ | ❌ | ✅ |

**Kiểm tra**:
```python
if session.get('role') != 'admin':
    flash('Chỉ admin được xóa!', 'error')
    return redirect(url_for('upload.view_logs'))
```

---

## 🐛 Debug - Tìm Bug

### 1. Logs không hiển thị?
- ✓ Kiểm tra `BankLog` table có dữ liệu?
- ✓ Kiểm tra filter điều kiện có đúng?
- ✓ Kiểm tra pagination (page, per_page) có hợp lệ?

### 2. Xóa không hoạt động?
- ✓ Kiểm tra role = 'admin'?
- ✓ Kiểm tra log_ids JSON hợp lệ?
- ✓ Kiểm tra CSRF token?

### 3. Modal không hiển thị?
- ✓ Kiểm tra Bootstrap 5 JS loaded?
- ✓ Kiểm tra `#deleteLogsModal` ID tồn tại?
- ✓ Kiểm tra JavaScript không có error (F12)

---

## 📝 Code Examples

### Thêm Một Log Mới
```python
from models.bank_log import BankLog
from extensions import db

log = BankLog(
    bank_code='VCB',
    original_filename='statement.xlsx',
    status='SUCCESS',
    message='Parsed successfully',
    processed_at=datetime.utcnow()
)
db.session.add(log)
db.session.commit()
```

### Lấy Logs của 7 Ngày Qua
```python
from datetime import datetime, timedelta

since = datetime.utcnow() - timedelta(days=7)
recent_logs = BankLog.query.filter(
    BankLog.processed_at >= since
).all()
```

### Xóa Log
```python
log = BankLog.query.get(log_id)
db.session.delete(log)
db.session.commit()
```

---

## 🔍 Quick Reference

| Cần tìm gì? | Tìm ở đâu? |
|-------------|-----------|
| Route logic | `blueprints/upload/routes.py` |
| Admin route | `routes/routes_admin.py` |
| HTML template | `templates/admin_logs.html` |
| Database model | `models/bank_log.py` |
| JavaScript | `templates/admin_logs.html` (dòng 221+) |
| Navigation | `templates/admin_base.html` |
| CSS styles | Bootstrap classes |

---

## 🚀 Testing

### Test Xem Logs
```bash
curl http://127.0.0.1:5001/upload/logs
```

### Test Xóa (POST)
```bash
curl -X POST http://127.0.0.1:5001/upload/logs/delete \
  -d "bank_code=VCB&status=SUCCESS&days=7"
```

---

## 📌 Notes

- Tất cả logs được lưu trong database `BankLog` table
- Files được lưu trong thư mục `uploads/`
- Deletion là hard delete (không soft delete)
- Mỗi lần xóa được log lại trong application logs
- Multi-select dùng JSON array để truyền IDs

---

**Version**: 1.0
**Last Updated**: Nov 19, 2025
