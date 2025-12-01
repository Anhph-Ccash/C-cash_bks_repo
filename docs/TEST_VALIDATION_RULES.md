# Validation Rules cho Upload Admin Panel

## ✅ Đã triển khai đầy đủ các validation rules:

### 1. Số tài khoản (Account Number)
- **Rule**: Nếu không tìm thấy số tài khoản trong file, hệ thống vẫn cho phép tạo StatementLog
- **Hành động**: Tự động redirect đến trang chi tiết để user nhập thủ công
- **Code**: `blueprints/upload/routes.py` lines 172-178
```python
if stmt and not (stmt.accountno and str(stmt.accountno).strip()):
    cleanup_file(saved_path)
    return redirect(url_for('main.view_statement_detail', log_id=sid))
```

### 2. Loại tiền (Currency)
- **Rule**: BẮT BUỘC phải có thông tin loại tiền
- **Lỗi nếu thiếu**: ❌ Thiếu thông tin Loại tiền (Currency)
- **Code**: `services/statement_service.py` line 22
```python
if not parsed_data.get('currency'):
    errors.append("❌ Thiếu thông tin Loại tiền (Currency)")
```

### 3. Số dư đầu kỳ (Opening Balance)
- **Rule**: BẮT BUỘC phải có thông tin số dư đầu kỳ
- **Lỗi nếu thiếu**: ❌ Thiếu thông tin Số dư đầu kỳ (Opening Balance)
- **Code**: `services/statement_service.py` line 16
```python
if not parsed_data.get('opening_balance'):
    errors.append("❌ Thiếu thông tin Số dư đầu kỳ (Opening Balance)")
```

### 4. Số dư cuối kỳ (Closing Balance)
- **Rule**: BẮT BUỘC phải có thông tin số dư cuối kỳ
- **Lỗi nếu thiếu**: ❌ Thiếu thông tin Số dư cuối kỳ (Closing Balance)
- **Code**: `services/statement_service.py` line 19
```python
if not parsed_data.get('closing_balance'):
    errors.append("❌ Thiếu thông tin Số dư cuối kỳ (Closing Balance)")
```

### 4.1. Validation Công thức Số dư cuối kỳ ✅
- **Rule**: Số dư cuối kỳ = Số dư đầu kỳ + Số dư phát sinh
- **Công thức chi tiết**:
  - Số dư phát sinh = Credit - Debit - Fee - VAT
  - Số dư cuối kỳ = Opening Balance + (Credit - Debit - Fee - VAT)
- **Tolerance**: Cho phép sai số ±0.01 (do làm tròn số thực)
- **Lỗi nếu không khớp**: ❌ Số dư cuối kỳ <> Số dư phát sinh + Số dư đầu kỳ
- **Chi tiết lỗi hiển thị**:
  - Số dư đầu kỳ (Opening Balance)
  - Tổng Credit
  - Tổng Debit
  - Tổng Fee
  - Tổng VAT
  - Số dư phát sinh = Credit - Debit - Fee - VAT
  - Số dư cuối kỳ TÍNH ĐƯỢC = Opening + Số dư phát sinh
  - Số dư cuối kỳ TRONG FILE (Closing Balance)
  - Chênh lệch
- **Code**: `services/statement_service.py` lines 408-455

### 5. Giao dịch (Transactions)
- **Rule**: BẮT BUỘC phải có tối thiểu 1 giao dịch hợp lệ
- **Giao dịch hợp lệ phải có**:
  1. **Transaction Date** (Ngày giao dịch) - BẮT BUỘC
  2. **Narrative** (Diễn giải) - BẮT BUỘC
  3. **Credit HOẶC Debit** - BẮT BUỘC (ít nhất một trong hai)

#### 5.1. Không có giao dịch nào
- **Lỗi**: ❌ Không tìm thấy giao dịch nào trong file. Phải có tối thiểu 1 giao dịch hợp lệ.
- **Code**: `services/statement_service.py` lines 37-38

#### 5.2. Không có giao dịch hợp lệ
- **Lỗi**: ❌ Không có giao dịch hợp lệ nào. Mỗi giao dịch phải có: Transaction Date, Narrative, và Credit/Debit
- **Code**: `services/statement_service.py` lines 72-73

#### 5.3. Thiếu Credit/Debit
- **Lỗi**: ⚠️ Thiếu thông tin Credit/Debit cho X/Y giao dịch
- **Code**: `services/statement_service.py` lines 75-76

#### 5.4. Thiếu Narrative
- **Lỗi**: ⚠️ Thiếu thông tin Narrative (Diễn giải) cho X/Y giao dịch
- **Code**: `services/statement_service.py` lines 78-79

#### 5.5. Thiếu Transaction Date
- **Lỗi**: ⚠️ Thiếu thông tin Transaction Date (Ngày giao dịch) cho X/Y giao dịch
- **Code**: `services/statement_service.py` lines 81-82

## 📋 Workflow Upload & Validation

### Upload File đơn (Excel/CSV):
1. User upload file qua Admin Panel
2. Hệ thống detect bank code
3. Hệ thống parse statement config
4. **VALIDATION** - Kiểm tra:
   - ✅ Currency có tồn tại?
   - ✅ Opening Balance có tồn tại?
   - ✅ Closing Balance có tồn tại?
   - ✅ Có ít nhất 1 giao dịch hợp lệ?
5. Nếu validation **FAIL** (thiếu thông tin quan trọng):
   - Xóa file đã upload
   - Xóa BankLog liên quan
   - Hiển thị danh sách lỗi chi tiết
6. Nếu validation **PASS**:
   - Tạo StatementLog
   - Tạo file MT940
   - Kiểm tra số tài khoản:
     - Nếu thiếu → Redirect đến trang edit để nhập
     - Nếu có → Hoàn tất

### Upload File ZIP:
1. Extract tất cả files trong ZIP
2. Xử lý từng file một theo quy trình trên
3. Tổng hợp kết quả:
   - Số file processed
   - Số file success
   - Số file failed (kèm lý do)
4. Hiển thị summary và top 5 failures

## 🔧 Code References

### Main Validation Function
- File: `services/statement_service.py`
- Function: `validate_statement_data(parsed_data)`
- Lines: 11-84

### Validation Call
- File: `services/statement_service.py`
- Function: `parse_and_store_statement(...)`
- Lines: 303-343

### Error Display
- File: `blueprints/upload/routes.py`
- Function: `process_upload()`
- Lines: 162-169
```python
if parse_result.get('status') == 'INVALID':
    errors = parse_result.get('errors', [])
    error_msg = parse_result.get('message', 'Mẫu sao kê không tồn tài và phải cấu hình thêm')
    flash(error_msg, 'danger')
    for err in errors[:5]:  # Show first 5 errors
        flash(f"• {err}", 'warning')
```

## 🧪 Testing

### Test Case 1: File thiếu Currency
- **Input**: Excel file không có trường Currency
- **Expected**: Báo lỗi "❌ Thiếu thông tin Loại tiền (Currency)"
- **File không được tạo StatementLog**

### Test Case 2: File thiếu Opening Balance
- **Input**: Excel file không có Số dư đầu kỳ
- **Expected**: Báo lỗi "❌ Thiếu thông tin Số dư đầu kỳ (Opening Balance)"
- **File không được tạo StatementLog**

### Test Case 3: File thiếu Closing Balance
- **Input**: Excel file không có Số dư cuối kỳ
- **Expected**: Báo lỗi "❌ Thiếu thông tin Số dư cuối kỳ (Closing Balance)"
- **File không được tạo StatementLog**

### Test Case 3.1: File có Closing Balance không khớp công thức
- **Input**: Excel file có đầy đủ thông tin nhưng Closing Balance ≠ Opening + (Credit - Debit - Fee - VAT)
- **Expected**:
  - Báo lỗi "❌ Số dư cuối kỳ <> Số dư phát sinh + Số dư đầu kỳ"
  - Hiển thị chi tiết:
    - Số dư đầu kỳ
    - Tổng Credit, Debit, Fee, VAT
    - Số dư phát sinh được tính
    - Số dư cuối kỳ tính được
    - Số dư cuối kỳ trong file
    - Chênh lệch
  - File không được tạo StatementLog
  - File bị xóa khỏi hệ thống

### Test Case 4: File không có giao dịch
- **Input**: Excel file không có dòng transaction nào
- **Expected**: Báo lỗi "❌ Không tìm thấy giao dịch nào trong file..."
- **File không được tạo StatementLog**

### Test Case 5: File thiếu Account Number
- **Input**: Excel file đầy đủ thông tin EXCEPT Account Number
- **Expected**:
  - Tạo StatementLog thành công
  - Redirect đến trang edit
  - User có thể nhập Account Number thủ công

### Test Case 6: Giao dịch thiếu Narrative
- **Input**: File có giao dịch nhưng thiếu Narrative
- **Expected**: Báo lỗi "⚠️ Thiếu thông tin Narrative (Diễn giải) cho X/Y giao dịch"

### Test Case 7: Giao dịch thiếu Credit và Debit
- **Input**: File có giao dịch nhưng cả Credit và Debit đều rỗng
- **Expected**: Báo lỗi "⚠️ Thiếu thông tin Credit/Debit cho X/Y giao dịch"

## ✅ Summary

Tất cả các validation rules đã được triển khai đầy đủ:
- ✅ Số tài khoản: Cho phép nhập thủ công nếu thiếu
- ✅ Loại tiền: BẮT BUỘC, báo lỗi nếu thiếu
- ✅ Số dư đầu kỳ: BẮT BUỘC, báo lỗi nếu thiếu
- ✅ Số dư cuối kỳ: BẮT BUỘC, báo lỗi nếu thiếu
- ✅ **Công thức số dư cuối kỳ: BẮT BUỘC phải khớp với (Số dư đầu kỳ + Số dư phát sinh)**
  - **Số dư phát sinh = Credit - Debit - Fee - VAT**
  - **Sai số cho phép: ±0.01**
  - **Hiển thị chi tiết đầy đủ khi có lỗi**
- ✅ Giao dịch: Tối thiểu 1 giao dịch với đầy đủ Date, Narrative, Credit/Debit

## 📐 Công thức Validation Số dư

```
Số dư phát sinh = Σ(Credit) - Σ(Debit) - Σ(TransactionFee) - Σ(TransactionVAT)

Số dư cuối kỳ (Expected) = Số dư đầu kỳ + Số dư phát sinh

Validation: |Số dư cuối kỳ Expected - Số dư cuối kỳ File| ≤ 0.01
```

### Ví dụ tính toán:

```
Opening Balance:        1,000,000.00
Total Credit:             500,000.00
Total Debit:              200,000.00
Total Fee:                  5,000.00
Total VAT:                  1,000.00

→ Số dư phát sinh = 500,000 - 200,000 - 5,000 - 1,000 = 294,000.00
→ Closing Balance Expected = 1,000,000 + 294,000 = 1,294,000.00

Nếu Closing Balance trong file = 1,294,000.00 → ✅ PASS
Nếu Closing Balance trong file = 1,300,000.00 → ❌ FAIL (chênh lệch 6,000.00)
```
