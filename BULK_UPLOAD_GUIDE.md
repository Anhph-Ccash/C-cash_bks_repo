# Hướng dẫn Upload cấu hình Sổ phụ theo lô

## Mục đích
Cho phép upload nhiều cấu hình nhận diện cho cùng một ngân hàng (bank_code) trong một file Excel/CSV.

## Các trường identify_info được hỗ trợ

Mỗi ngân hàng cần có cấu hình cho các trường sau:

1. **accountno** - Số tài khoản
2. **currency** - Loại tiền
3. **openingbalance** - Số dư đầu kỳ
4. **closingbalance** - Số dư cuối kỳ
5. **narrative** - Diễn giải giao dịch
6. **transactiondate** - Ngày giao dịch
7. **debit** - Số tiền ghi nợ
8. **credit** - Số tiền ghi có
9. **flowcode** - Mã luồng tiền
10. **transactionfee** - Phí giao dịch
11. **transactionvat** - VAT
12. **identify_info** - Thông tin định danh khác

## Cấu trúc file Excel/CSV

| bank_code | keywords | col_keyword | col_value | row_start | row_end | identify_info | cell_format |
|-----------|----------|-------------|-----------|-----------|---------|---------------|-------------|
| VCB | Số tài khoản,Account Number | A | B | 1 | 1 | accountno | Text |
| VCB | Loại tiền,Currency | A | B | 2 | 2 | currency | Text |
| VCB | Số dư đầu kỳ,Opening Balance | A | B | 3 | 3 | openingbalance | Number |
| VCB | Số dư cuối kỳ,Closing Balance | A | B | 4 | 4 | closingbalance | Number |
| VCB | Diễn giải,Narrative | A | B | 10 | 100 | narrative | Text |
| VCB | Ngày GD,Date | A | B | 10 | 100 | transactiondate | Date |
| VCB | Ghi nợ,Debit | A | B | 10 | 100 | debit | Number |
| VCB | Ghi có,Credit | A | B | 10 | 100 | credit | Number |
| VCB | Mã luồng,Flow Code | A | B | 10 | 100 | flowcode | Text |
| VCB | Phí,Fee | A | B | 10 | 100 | transactionfee | Number |
| VCB | VAT | A | B | 10 | 100 | transactionvat | Number |
| VCB | Info | A | B | 10 | 100 | identify_info | Text |

## Giải thích các cột

- **bank_code**: Mã ngân hàng (VD: VCB, TCB, ACB) - có thể lặp lại cho nhiều trường
- **keywords**: Từ khóa để tìm kiếm trong file, ngăn cách bằng dấu phẩy
- **col_keyword**: Cột chứa từ khóa trong file Excel (A, B, C...)
- **col_value**: Cột chứa giá trị tương ứng
- **row_start**: Dòng bắt đầu tìm kiếm
- **row_end**: Dòng kết thúc tìm kiếm
- **identify_info**: Loại trường (phải là một trong 12 giá trị trên)
- **cell_format**: Định dạng dữ liệu (Text, Number, Date...)

## Cách sử dụng

1. Truy cập trang "Cấu hình Sổ phụ"
2. Click nút "📤 Upload theo lô"
3. Click "📥 Tải file mẫu với đầy đủ 12 trường" để tải template
4. Điền thông tin vào file template:
   - Giữ nguyên bank_code cho tất cả các dòng (nếu chỉ cấu hình cho 1 ngân hàng)
   - Điều chỉnh keywords phù hợp với file của ngân hàng đó
   - Điều chỉnh col_keyword, col_value, row_start, row_end phù hợp
   - Đảm bảo identify_info đúng cho từng trường
5. Upload file
6. Xem kết quả: số cấu hình thành công / thất bại

## Lưu ý quan trọng

- ✅ Có thể upload nhiều dòng cho cùng một bank_code
- ✅ Mỗi dòng = 1 cấu hình cho 1 trường (identify_info)
- ✅ Nếu cấu hình đã tồn tại (cùng company, bank_code, identify_info) → sẽ cập nhật
- ✅ Nếu chưa tồn tại → sẽ tạo mới
- ⚠️ identify_info phải chính xác (không được viết sai)
- ⚠️ Keywords nên bao gồm cả tiếng Việt và tiếng Anh để nhận diện tốt hơn

## Ví dụ thực tế

**Tình huống**: Cấu hình nhận diện cho ngân hàng VCB

**File upload**: 12 dòng, tất cả có bank_code = "VCB"

**Kết quả**: Hệ thống sẽ có 12 cấu hình riêng biệt cho VCB:
- 1 cấu hình tìm số tài khoản
- 1 cấu hình tìm loại tiền
- 1 cấu hình tìm số dư đầu kỳ
- ... (và 9 cấu hình khác)

Khi xử lý file sao kê VCB, hệ thống sẽ sử dụng cả 12 cấu hình này để trích xuất đầy đủ thông tin.
