# Hướng dẫn sử dụng Scan Ranges trong Cấu hình Ngân hàng

## Tổng quan

Tính năng **Scan Ranges** cho phép định nghĩa các vùng quét dữ liệu cụ thể trong file statement của từng ngân hàng. Điều này giúp hệ thống đọc và phân tích dữ liệu một cách chính xác hơn.

## Cấu trúc JSON của Scan Ranges

```json
[
    {
        "name": "Tên vùng quét",
        "description": "Mô tả chi tiết",
        "start_row": 1,
        "end_row": 15,
        "fields": ["field1", "field2", "field3"],
        "columns": {
            "account_number": "B",
            "balance": "C"
        }
    }
]
```

## Các trường trong Scan Range

### Bắt buộc:
- **name**: Tên định danh cho vùng quét
- **start_row**: Dòng bắt đầu quét (bắt đầu từ 1)
- **end_row**: Dòng kết thúc quét

### Tùy chọn:
- **description**: Mô tả chi tiết về vùng quét
- **fields**: Danh sách các field sẽ được trích xuất
- **columns**: Mapping giữa field và cột Excel (A, B, C, ...)
- **keywords**: Từ khóa để nhận diện vùng quét
- **validation**: Quy tắc validation cho dữ liệu

## Ví dụ cấu hình cho các ngân hàng

### 1. Vietcombank (VCB)

```json
[
    {
        "name": "Header Information",
        "description": "Thông tin header của VCB statement",
        "start_row": 1,
        "end_row": 12,
        "fields": ["account_number", "account_name", "opening_balance", "closing_balance", "currency"],
        "columns": {
            "account_number": "C",
            "account_name": "C",
            "opening_balance": "C",
            "closing_balance": "C",
            "currency": "C"
        },
        "keywords": ["số tài khoản", "tên tài khoản", "số dư đầu kỳ", "số dư cuối kỳ"]
    },
    {
        "name": "Transaction Data",
        "description": "Dữ liệu giao dịch VCB",
        "start_row": 15,
        "end_row": 500,
        "fields": ["transaction_date", "description", "debit", "credit", "balance"],
        "columns": {
            "transaction_date": "B",
            "description": "C",
            "debit": "E",
            "credit": "D",
            "balance": "F"
        }
    }
]
```

### 2. Techcombank (TCB)

```json
[
    {
        "name": "Account Info",
        "description": "Thông tin tài khoản TCB",
        "start_row": 1,
        "end_row": 10,
        "fields": ["account_number", "opening_balance", "closing_balance"],
        "keywords": ["account", "opening", "closing"]
    },
    {
        "name": "Transactions",
        "description": "Giao dịch TCB",
        "start_row": 12,
        "end_row": 1000,
        "fields": ["date", "narrative", "amount", "balance"]
    }
]
```

### 3. Bidv

```json
[
    {
        "name": "Header",
        "start_row": 1,
        "end_row": 8,
        "fields": ["account_info", "balance_info"]
    },
    {
        "name": "Data",
        "start_row": 10,
        "end_row": 800,
        "fields": ["transaction_details"]
    }
]
```

## Cách sử dụng trong Admin Panel

1. **Thêm cấu hình mới:**
   - Vào trang "Cấu hình Ngân hàng"
   - Nhấn "➕ Thêm mới"
   - Nhập thông tin cơ bản (Mã ngân hàng, Tên, Từ khóa)
   - Trong trường "Scan Ranges", nhập JSON theo định dạng trên

2. **Sửa cấu hình có sẵn:**
   - Nhấn nút "✏️" bên cạnh cấu hình cần sửa
   - Cập nhật trường "Scan Ranges" với JSON mới
   - Nhấn "Cập nhật"

## Validation Rules

- JSON phải có định dạng hợp lệ
- `start_row` và `end_row` phải là số nguyên dương
- `start_row` phải nhỏ hơn hoặc bằng `end_row`
- `name` là bắt buộc cho mỗi scan range

## Lưu ý khi sử dụng

1. **Số dòng bắt đầu từ 1** (không phải 0)
2. **Cột Excel**: A=1, B=2, C=3, ... hoặc có thể dùng chữ A, B, C
3. **Test cấu hình** trước khi áp dụng với file thực tế
4. **Backup** cấu hình cũ trước khi thay đổi
5. **Kiểm tra log** nếu có lỗi khi xử lý file

## Troubleshooting

### Lỗi JSON không hợp lệ:
- Kiểm tra dấu ngoặc kép và phẩy
- Sử dụng JSON validator online
- Copy từ ví dụ và chỉnh sửa

### Không đọc được dữ liệu:
- Kiểm tra `start_row` và `end_row`
- Xác nhận mapping cột
- Kiểm tra từ khóa nhận diện

### Performance issues:
- Giới hạn `end_row` phù hợp
- Không quét toàn bộ file nếu không cần thiết
- Sử dụng keywords để tối ưu tìm kiếm
