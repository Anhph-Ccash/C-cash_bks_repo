# Database Configuration Guide

## Lỗi Database Connection

Nếu gặp lỗi `OperationalError: server closed the connection unexpectedly`, có thể do:

1. **Database server không chạy** (nếu dùng local)
2. **Connection timeout** (nếu dùng remote database)
3. **Network issues** (đối với remote database)

## Giải pháp đã áp dụng:

### 1. Connection Pool Settings (config.py)
```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_pre_ping': True,    # Kiểm tra connection trước khi dùng
    'pool_recycle': 300,      # Làm mới connection mỗi 5 phút
    'pool_size': 10,          # Số connection tối đa
    'max_overflow': 20,       # Connection overflow
    'pool_timeout': 30,       # Timeout khi lấy connection
}
```

### 2. Error Handlers (factory.py)
- Xử lý lỗi `OperationalError`
- Hiển thị trang lỗi thân thiện
- Tự động rollback transaction

### 3. Template Error (templates/error.html)
- Trang hiển thị lỗi đẹp mắt
- Nút quay lại và về trang chủ

## Chuyển đổi Database:

### Sử dụng Local Database:

1. Mở file `config.py`
2. Comment dòng remote database:
```python
# SQLALCHEMY_DATABASE_URI = os.environ.get(
#     'DATABASE_URL',
#     'postgresql://flaskwebpostgresql_user:...'
# )
```

3. Uncomment dòng local database:
```python
SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:11223344@localhost:5432/FlaskWebPostgreSQL'
```

4. Đảm bảo PostgreSQL đang chạy:
```powershell
# Kiểm tra service
Get-Service postgresql*

# Start service nếu cần
Start-Service postgresql-x64-16
```

### Sử dụng Remote Database (Render):

1. Giữ nguyên cấu hình hiện tại trong `config.py`
2. Đảm bảo có kết nối internet ổn định
3. Connection sẽ tự động retry với pool settings

## Kiểm tra kết nối:

```powershell
# Test local database
psql -U postgres -d FlaskWebPostgreSQL -c "SELECT 1;"

# Test remote database (nếu có psql)
psql "postgresql://flaskwebpostgresql_user:nrDeXdaJQ2GA9Bv04ISC2rdNpI7EKhYr@dpg-d47l9824d50c7388ofsg-a.singapore-postgres.render.com/flaskwebpostgresql" -c "SELECT 1;"
```

## Tips:

1. **Development**: Dùng local database để phát triển nhanh hơn
2. **Production**: Dùng remote database (Render)
3. **Testing**: Có thể tạo database riêng cho test
4. **Backup**: Thường xuyên backup database

## Troubleshooting:

### Lỗi: "connection refused"
- PostgreSQL chưa chạy
- Sai port (mặc định: 5432)
- Firewall chặn

### Lỗi: "password authentication failed"
- Sai username/password
- Kiểm tra lại credentials trong config.py

### Lỗi: "database does not exist"
- Tạo database: `createdb -U postgres FlaskWebPostgreSQL`
- Hoặc dùng pgAdmin để tạo database mới
