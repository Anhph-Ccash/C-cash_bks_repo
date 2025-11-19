# 🗺️ Project Structure Map - Tìm Chức Năng Logs

```
PROJECT ROOT (e:\C-cash_bks_repo)
│
├── 📁 blueprints/                 ← Blueprint modules
│   └── 📁 upload/
│       └── routes.py              ✅ MAIN ROUTES FOR LOGS
│           ├── Line 203: view_logs()           [GET /upload/logs]
│           ├── Line 267: delete_logs()         [POST /upload/logs/delete]
│           └── Line 325: delete_logs_selected() [POST /upload/logs/delete-selected] (NEW)
│
├── 📁 routes/                     ← Standalone route files
│   └── routes_admin.py            ✅ ADMIN ROUTES
│       └── Line 855: admin_view_logs()  [GET /admin/upload/logs]
│
├── 📁 models/                     ← Database models
│   └── bank_log.py                ✅ BankLog model (database table)
│
├── 📁 templates/                  ← HTML templates
│   ├── admin_logs.html            ✅ ADMIN LOGS UI (NEW - Enhanced)
│   │   ├── Lines 1-50:    Header + Filter Form
│   │   ├── Lines 51-70:   Bulk Actions Buttons
│   │   ├── Lines 71-130:  Table + Rows
│   │   ├── Lines 131-170: Pagination
│   │   ├── Lines 171-220: Delete Modal
│   │   └── Lines 221-363: JavaScript
│   │
│   ├── logs.html                  ← USER LOGS UI (no delete)
│   │
│   ├── admin_base.html            ← Admin layout with nav menu
│   │   └── Line 35: <a href="{{ url_for('admin.admin_view_logs') }}">
│   │
│   └── base_layout.html           ← User layout with nav menu
│       └── Line 38: <a href="{{ url_for('upload.view_logs') }}">
│
└── 📁 extensions.py               ← db, login_manager (imports)
```

---

## 🎯 ROUTES MAP

```
HTTP Request                      Python Function          Template Used
─────────────────────────────────────────────────────────────────────────

GET  /upload/logs                 upload.view_logs()       logs.html
     [User view of their logs]    (blueprints/upload)

GET  /admin/upload/logs           admin.admin_view_logs()  admin_logs.html
     [Admin view of all logs]     (routes/routes_admin)

POST /upload/logs/delete          upload.delete_logs()     -
     [Delete by filter]           (blueprints/upload)

POST /upload/logs/delete-selected upload.delete_logs_selected() -
     [Delete selected IDs] (NEW)  (blueprints/upload)
```

---

## 📊 DATABASE

```
Table: bank_log
┌─────────┬──────────────────────────┐
│ Field   │ Type                     │
├─────────┼──────────────────────────┤
│ id      │ Integer (Primary Key)    │ ← Unique ID
│ bank_code│ String                  │ ← Filter by bank
│ status  │ Enum (SUCCESS/ERROR)     │ ← Filter by status
│ processed_at │ DateTime            │ ← Filter by date
│ original_filename │ String         │ ← Display in list
│ message │ String (500)             │ ← Display status msg
│ filename│ String                   │ ← File path to download
│ detected_keywords │ List           │ ← Show keywords
└─────────┴──────────────────────────┘
```

---

## 🔧 HOW TO FIND CODE

### 1️⃣ **Find Route Handler**
```
WHERE: blueprints/upload/routes.py

SEARCH FOR:
  @upload_bp.route("/logs")
  def view_logs():
```

### 2️⃣ **Find Admin Route**
```
WHERE: routes/routes_admin.py

SEARCH FOR:
  @admin_bp.route("/upload/logs")
  def admin_view_logs():
```

### 3️⃣ **Find Delete Function**
```
WHERE: blueprints/upload/routes.py

SEARCH FOR:
  @upload_bp.route("/logs/delete", methods=["POST"])
  def delete_logs():
```

### 4️⃣ **Find Delete-Selected Function (NEW)**
```
WHERE: blueprints/upload/routes.py

SEARCH FOR:
  @upload_bp.route("/logs/delete-selected", methods=["POST"])
  def delete_logs_selected():
```

### 5️⃣ **Find HTML Template**
```
WHERE: templates/admin_logs.html

LOOK FOR:
  <form class="row g-3 mb-4">           ← Filter form
  <table class="table">                 ← Logs table
  <input type="checkbox">               ← Multi-select checkbox
  <button ... delete-single-btn>        ← Delete button (NEW)
  <div class="modal">                   ← Confirm modal
  <script>                              ← JavaScript
```

### 6️⃣ **Find JavaScript**
```
WHERE: templates/admin_logs.html (Lines 221-363)

LOOK FOR:
  document.addEventListener('DOMContentLoaded', ...)
  .delete-single-btn                    ← Single delete handler (NEW)
  .log-checkbox                         ← Multi-select handler
  .deleteSelectedBtn                    ← Multi-delete handler
  .deleteAllBtn                         ← Filter-delete handler
```

---

## 🎨 COMPONENT BREAKDOWN

### Filter Form (Lines 13-42, admin_logs.html)
```html
├── Mã Ngân hàng (text input)
├── Trạng thái (select: Tất cả, Thành công, Lỗi)
├── Thời gian (select: 7/30/90 ngày, Tất cả)
└── Nút Lọc (submit button)
```

### Bulk Actions Bar (Lines 43-67, admin_logs.html)
```html
├── Đếm logs (Tổng số, Đã chọn)
├── Nút "✓ Chọn tất cả"
├── Nút "✗ Bỏ chọn tất cả"
├── Nút "🗑️ Xóa mục đã chọn"
└── Nút "🗑️ Xóa theo Bộ lọc"
```

### Logs Table (Lines 68-130, admin_logs.html)
```html
├── Checkbox (for multi-select)
├── Thời gian (processed_at)
├── Tệp gốc (original_filename)
├── Mã Ngân hàng (bank_code)
├── Trạng thái (status - SUCCESS/ERROR badge)
├── Từ khóa phát hiện (detected_keywords)
├── Thông báo (message)
└── Hành động
    ├── 📥 Tải (download button)
    └── 🗑️ Delete button (NEW - single delete)
```

### Delete Modal (Lines 171-220, admin_logs.html)
```html
├── Header: "🗑️ Xóa nhật ký"
├── Alert: "⚠️ Cảnh báo: ..."
├── filterDeleteInfo (for filter-based delete)
│   ├── Mã Ngân hàng (selected)
│   ├── Trạng thái (selected)
│   ├── Thời gian (selected)
│   └── Số lượng sẽ xóa
├── selectedItemsInfo (for individual/multi delete)
│   ├── Danh sách logs sẽ xóa
│   └── Số lượng sẽ xóa
└── Buttons: ❌ Hủy | 🗑️ Xác nhận xóa
```

---

## 🔐 SECURITY

```python
# Check 1: Login Required
@login_required
def view_logs():
    ...

# Check 2: Admin Role Required (for delete)
if session.get('role') != 'admin':
    flash('Chỉ admin được phép xóa!', 'error')
    return redirect(...)

# Check 3: CSRF Token Required
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}">

# Check 4: Input Validation
log_ids = json.loads(log_ids_json)  # Parse JSON safely
log_ids = [int(lid) for lid in log_ids]  # Validate integers
```

---

## 📝 FILE SIZES

| File | Lines | Purpose |
|------|-------|---------|
| blueprints/upload/routes.py | 460 | All upload routes including logs |
| routes/routes_admin.py | 913 | Admin specific routes |
| templates/admin_logs.html | 363 | Admin logs UI (NEW - Enhanced) |
| templates/logs.html | ~180 | User logs UI |
| models/bank_log.py | ~50 | Database model |

---

## 🚀 QUICK NAVIGATION COMMANDS

### Find logs-related code
```bash
# Search for "view_logs" function
grep -n "def view_logs" blueprints/upload/routes.py

# Search for "delete_logs" functions
grep -n "def delete_logs" blueprints/upload/routes.py

# Find all @upload_bp.route with "logs"
grep -n "@upload_bp.route.*logs" blueprints/upload/routes.py

# Find delete modal in template
grep -n "deleteLogsModal" templates/admin_logs.html

# Find JavaScript handlers
grep -n "addEventListener" templates/admin_logs.html
```

---

## 💡 QUICK FACTS

✅ **Single Delete** (NEW) - Each row has a 🗑️ button
✅ **Multi-Select** (NEW) - Checkbox to select multiple rows
✅ **Filter Delete** - Delete all matching filter criteria
✅ **Admin Only** - Delete requires admin role
✅ **Modal Confirm** - User must confirm before delete
✅ **JSON IDs** - Selected IDs sent as JSON array
✅ **Hard Delete** - No undo, permanent deletion
✅ **Audit Log** - Each delete logged in application logs

---

## 🎯 COMMON TASKS

### I want to modify the filter form
🔍 **File**: `templates/admin_logs.html` (Lines 13-42)
- Add new filter field in form
- Update Python code in `blueprints/upload/routes.py` to handle filter

### I want to change delete behavior
🔍 **File**: `blueprints/upload/routes.py` (Lines 267, 325)
- Modify `delete_logs()` for filter-based
- Modify `delete_logs_selected()` for individual/multi

### I want to add new column to table
🔍 **File**: `templates/admin_logs.html` (Lines 68-130)
- Add `<th>` header
- Add `<td>` with data in table row

### I want to modify JavaScript
🔍 **File**: `templates/admin_logs.html` (Lines 221-363)
- Find event listener for `.delete-single-btn`
- Modify modal or form data

### I want to change styling
🔍 **File**: `templates/admin_logs.html`
- Use Bootstrap classes (btn, badge, alert, etc.)
- Modify CSS in `<style>` tag or use inline styles

---

## 📞 SUPPORT

For each section above, look at the specified line numbers or search terms to find the exact code location.

**Version**: 2.0
**Last Updated**: Nov 19, 2025
