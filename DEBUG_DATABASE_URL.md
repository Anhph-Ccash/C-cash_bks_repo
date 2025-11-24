# 🔧 Cách Fix Lỗi Database Connection trên Render

## 📋 Vấn Đề

Application trên Render.com đang cố kết nối đến `localhost:5432` (PostgreSQL local) nhưng Render là cloud service và không thể kết nối đến máy local.

**Error:**
```
(psycopg2.OperationalError) connection to server at "localhost" failed: Connection refused
```

## ✅ Giải Pháp

### Bước 1: Kiểm Tra Render Database URL

Lấy connection string từ **Render Dashboard**:

1. Vào https://dashboard.render.com
2. Chọn project `c-cash-bks-mgmt`
3. Chọn **PostgreSQL** database
4. Copy **Internal Database URL** từ mục "Connections"
   - Format: `postgresql://user:password@host/database`

### Bước 2: Set Environment Variable trên Render

**Cách 1: Via Render Dashboard (Nên làm)**

1. Vào project **c-cash-bks-mgmt**
2. Click **Settings** → **Environment**
3. Thêm/Update variable:
   ```
   DATABASE_URL = postgresql://flaskwebpostgresql_user:nrDeXdaJQ2GA9Bv04ISC2rdNpI7EKhYr@dpg-d47l9824d50c7388ofsg-a.singapore-postgres.render.com/flaskwebpostgresql
   ```
4. Click **Save** → **Redeploy**

**Cách 2: Update `render.yaml` (Production Deploy)**

Thêm vào `render.yaml`:
```yaml
services:
  - type: web
    name: c-cash-bks-mgmt
    envVars:
      - key: DATABASE_URL
        scope: run
        value: postgresql://flaskwebpostgresql_user:nrDeXdaJQ2GA9Bv04ISC2rdNpI7EKhYr@dpg-d47l9824d50c7388ofsg-a.singapore-postgres.render.com/flaskwebpostgresql
```

### Bước 3: Redeploy Application

Render sẽ tự động redeploy khi:
- Environment variables được thay đổi
- Code được push lên GitHub (nếu auto-deploy được enable)

Hoặc trigger manual redeploy:
1. Vào project
2. Click **Deployments**
3. Click **Deploy latest commit**

### Bước 4: Xác Minh Connection

Check logs để xác nhận:
1. Vào project → **Logs**
2. Tìm message "Database: OK" hoặc tương tự
3. Không nên có lỗi `Connection refused`

---

## 📝 Cấu Hình Hiện Tại

**`config.py`** (Updated):
```python
SQLALCHEMY_DATABASE_URI = os.environ.get(
    'DATABASE_URL',
    'postgresql://postgres:11223344@localhost:5432/FlaskWebPostgreSQL'
)
```

- ✅ Lấy `DATABASE_URL` từ environment variable
- ✅ Fallback đến localhost cho local development
- ✅ Raise error nếu không có database

## 🎯 Environment Variables Cần Set Trên Render

| Variable | Value | Khu Vực |
|----------|-------|---------|
| `DATABASE_URL` | `postgresql://...@dpg-xxx.postgres.render.com/...` | Settings → Environment |
| `SECRET_KEY` | Giống value local hoặc tạo mới | Settings → Environment |

---

## 🚀 Bước Tiếp Theo

1. **Copy Render Database URL** từ Render Dashboard
2. **Set DATABASE_URL** environment variable trên Render
3. **Commit code** (đã cập nhật `config.py`)
4. **Push lên GitHub**
5. **Render auto-redeploy** hoặc trigger manual redeploy
6. **Check logs** để xác nhận connection OK

---

## 🔗 Links Hữu Ích

- Render Dashboard: https://dashboard.render.com
- Project: https://dashboard.render.com/d/cjgj0q3e9d9000jnv2g0
- PostgreSQL Database Details: Render Dashboard → PostgreSQL → Info

---

**Ghi chú**: Khi mọi thứ hoạt động, bạn có thể safely disable local development database connection trong `config.py` nếu không cần.
