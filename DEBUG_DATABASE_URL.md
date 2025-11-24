# 🔧 Cách Fix Lỗi Database Connection trên Render

## 📋 Vấn Đề

Application trên Render.com đang cố kết nối đến `localhost:5432` (PostgreSQL local) nhưng Render là cloud service và không thể kết nối đến máy local.

**Error:**
```
(psycopg2.OperationalError) connection to server at "localhost" failed: Connection refused
```

## ✅ Giải Pháp Nhanh (3 Cách)

### 🚀 Cách 1: Tự Động Setup (Nên Làm)

Chạy script Python để tự động set DATABASE_URL:

```bash
# Bước 1: Cài đặt requests library
pip install requests

# Bước 2: Lấy Render API token
# - Vào https://dashboard.render.com/account/api-tokens
# - Tạo token mới
# - Copy token

# Bước 3: Run script
python setup_render_database_url.py --token YOUR_API_TOKEN

# Script sẽ:
# 1. Liệt kê các services
# 2. Tự động chọn c-cash-bks service
# 3. Set DATABASE_URL environment variable
# 4. Trigger redeploy tự động
```

### 📋 Cách 2: Manual qua Render Dashboard

**Bước 1: Lấy Database URL**

1. Vào https://dashboard.render.com
2. Chọn **PostgreSQL** database (flaskwebpostgresql)
3. Click tab **Connections**
4. Copy **Internal Database URL**:
   ```
   postgresql://flaskwebpostgresql_user:nrDeXdaJQ2GA9Bv04ISC2rdNpI7EKhYr@dpg-d47l9824d50c7388ofsg-a.singapore-postgres.render.com/flaskwebpostgresql
   ```

**Bước 2: Set Environment Variable**

1. Vào project `c-cash-bks-mgmt` (web service)
2. Click **Settings** → **Environment**
3. Thêm variable mới:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | `postgresql://flaskwebpostgresql_user:...@dpg-....postgres.render.com/flaskwebpostgresql` |
| `SECRET_KEY` | `admin@123` (hoặc tạo key mới) |

4. Click **Save**
5. Render sẽ tự động **Redeploy**

### 📄 Cách 3: Update render.yaml (Tự động cho deployment kế tiếp)

File `render.yaml` đã được cập nhật với:

```yaml
services:
  - type: web
    name: C-cash_BKS_CMS
    env: python
    envVars:
      - key: DATABASE_URL
        value: postgresql://flaskwebpostgresql_user:...@dpg-....postgres.render.com/flaskwebpostgresql
      - key: SECRET_KEY
        value: admin@123
```

Lần deployment tiếp theo, Render sẽ tự động set các environment variables này.

---

## 🔍 Xác Minh Kết Nối

Sau khi set DATABASE_URL, kiểm tra logs:

```bash
# Cách 1: Via Render Dashboard
1. Vào project → Logs
2. Tìm các message:
   ✓ "Database: OK" hoặc "Successfully connected"
   ✗ KHÔNG nên có "Connection refused"

# Cách 2: Xem full logs
curl https://api.render.com/v1/services/YOUR_SERVICE_ID/logs \
  -H "Authorization: Bearer YOUR_API_TOKEN"
```

**Nếu OK:**
```
[✓] Database connection successful
[✓] Admin user created
[✓] Your service is live 🎉
```

**Nếu Still Error:**
```
[✗] connection to server at "localhost" failed: Connection refused
→ DATABASE_URL environment variable chưa được set hoặc sai
→ Thử lại từ Bước 1 hoặc 2
```

---

## 📝 Cấu Hình Hiện Tại

### config.py
```python
SQLALCHEMY_DATABASE_URI = os.environ.get(
    'DATABASE_URL',
    'postgresql://postgres:11223344@localhost:5432/FlaskWebPostgreSQL'
)
```
- ✅ Lấy `DATABASE_URL` từ environment
- ✅ Fallback đến localhost cho local dev

### render.yaml
```yaml
envVars:
  - key: DATABASE_URL
    value: postgresql://...@dpg-....postgres.render.com/flaskwebpostgresql
  - key: SECRET_KEY
    value: admin@123
```
- ✅ Tự động set cho deployment

---

## 🆘 Troubleshooting

| Lỗi | Nguyên Nhân | Cách Fix |
|-----|-----------|---------|
| "localhost" Connection refused | DATABASE_URL không set | Set DATABASE_URL (Cách 1, 2, hoặc 3) |
| psycopg2.OperationalError | Connection string sai | Copy đúng URL từ Render Dashboard |
| "Could not create default admin" | Database chưa sẵn sàng | Đợi ~30 giây, redeploy lại |
| Environment variable không nhận | Cache Render | Force redeploy: Dashboard → Deploy latest |

---

## 🎯 Checklist Deployment

- [ ] PostgreSQL database tạo thành công trên Render
- [ ] DATABASE_URL environment variable được set
- [ ] Redeploy application
- [ ] Logs không có "Connection refused"
- [ ] `/login` page load thành công
- [ ] Có thể login với user credentials

---

## 🔗 Links & Resources

- Render Dashboard: https://dashboard.render.com
- Render API Docs: https://render.com/docs/api-reference
- Project Web Service: https://dashboard.render.com/d/cjgj0q3e9d9000jnv2g0
- PostgreSQL Database: Render Dashboard → PostgreSQL → Info

---

## 💡 Pro Tips

1. **Luôn check logs** - Logs sẽ cho biết exact problem
2. **Redeploy bây giờ** - Không cần chờ git push
3. **Test locally trước** - Set `DATABASE_URL` env var locally để test
4. **Keep credentials safe** - DATABASE_URL chứa password, không commit vào Git
5. **Use script** - Script `setup_render_database_url.py` tiện hơn manual

---

**Updated**: 24/11/2025
