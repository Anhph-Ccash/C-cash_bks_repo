# Example: Validation Số dư cuối kỳ

## Ví dụ 1: File HỢP LỆ ✅

### Thông tin trong Excel:
```
Opening Balance: 10,000,000
Closing Balance: 10,585,000

Transactions:
ID | Date       | Narrative      | Credit   | Debit    | Fee   | VAT
1  | 01/11/2025 | Nộp tiền       | 1,000,000|          |       |
2  | 02/11/2025 | Rút tiền       |          | 300,000  |       |
3  | 03/11/2025 | Chuyển khoản   |          | 100,000  | 5,000 | 1,000
4  | 04/11/2025 | Nhận lương     | 200,000  |          |       |
5  | 05/11/2025 | Thanh toán     |          | 200,000  | 5,000 | 4,000
```

### Tính toán:
```
Total Credit    = 1,000,000 + 200,000 = 1,200,000
Total Debit     = 300,000 + 100,000 + 200,000 = 600,000
Total Fee       = 5,000 + 5,000 = 10,000
Total VAT       = 1,000 + 4,000 = 5,000

Số dư phát sinh = 1,200,000 - 600,000 - 10,000 - 5,000 = 585,000

Expected Closing = 10,000,000 + 585,000 = 10,585,000

File Closing Balance = 10,585,000

Kết quả: 10,585,000 = 10,585,000 → ✅ HỢP LỆ
```

---

## Ví dụ 2: File KHÔNG HỢP LỆ ❌

### Thông tin trong Excel:
```
Opening Balance: 10,000,000
Closing Balance: 10,700,000  ← SAI!

Transactions:
(Giống như ví dụ 1)
```

### Tính toán:
```
Total Credit    = 1,200,000
Total Debit     = 600,000
Total Fee       = 10,000
Total VAT       = 5,000

Số dư phát sinh = 585,000

Expected Closing = 10,000,000 + 585,000 = 10,585,000

File Closing Balance = 10,700,000

Chênh lệch = |10,585,000 - 10,700,000| = 115,000 > 0.01

Kết quả: ❌ KHÔNG HỢP LỆ
```

### Thông báo lỗi sẽ hiển thị:

```
❌ Số dư cuối kỳ <> Số dư phát sinh + Số dư đầu kỳ

📊 Chi tiết:
   • Số dư đầu kỳ (Opening Balance): 10,000,000.00
   • Tổng Credit: 1,200,000.00
   • Tổng Debit: 600,000.00
   • Tổng Fee: 10,000.00
   • Tổng VAT: 5,000.00
   • Số dư phát sinh = Credit - Debit - Fee - VAT = 585,000.00

🔢 Kết quả:
   • Số dư cuối kỳ TÍNH ĐƯỢC = Số dư đầu kỳ + Số dư phát sinh = 10,000,000.00 + 585,000.00 = 10,585,000.00
   • Số dư cuối kỳ TRONG FILE (Closing Balance) = 10,700,000.00
   • Chênh lệch = 115,000.00
```

---

## Ví dụ 3: Sai số chấp nhận được ✅

### Thông tin trong Excel:
```
Opening Balance: 10,000,000.00
Closing Balance: 10,585,000.01  ← Chênh 0.01 do làm tròn

Transactions:
(Giống như ví dụ 1)
```

### Tính toán:
```
Expected Closing = 10,585,000.00
File Closing Balance = 10,585,000.01

Chênh lệch = |10,585,000.00 - 10,585,000.01| = 0.01 ≤ 0.01

Kết quả: ✅ HỢP LỆ (sai số chấp nhận được)
```

---

## Ví dụ 4: Không có Fee và VAT ✅

### Thông tin trong Excel:
```
Opening Balance: 5,000,000
Closing Balance: 5,300,000

Transactions:
ID | Date       | Narrative      | Credit   | Debit    | Fee | VAT
1  | 01/11/2025 | Nộp tiền       | 500,000  |          |     |
2  | 02/11/2025 | Rút tiền       |          | 200,000  |     |
```

### Tính toán:
```
Total Credit    = 500,000
Total Debit     = 200,000
Total Fee       = 0
Total VAT       = 0

Số dư phát sinh = 500,000 - 200,000 - 0 - 0 = 300,000

Expected Closing = 5,000,000 + 300,000 = 5,300,000

File Closing Balance = 5,300,000

Kết quả: 5,300,000 = 5,300,000 → ✅ HỢP LỆ
```

---

## Lưu ý khi nhập liệu:

1. **Số dư phát sinh** được tính tự động từ các giao dịch
2. **Công thức**: Closing = Opening + (Credit - Debit - Fee - VAT)
3. **Sai số cho phép**: ±0.01 (do làm tròn số thực)
4. **Giao dịch hợp lệ**: Phải có Transaction Date, Narrative, và Credit/Debit
5. **File sẽ bị từ chối** nếu công thức không khớp với chênh lệch > 0.01
