# C-cash_bks_repo — User & Admin Panel Guide

## Mục đích
Tài liệu mô tả các chức năng chính và quy trình sử dụng cho:
- User Panel: người dùng nghiệp vụ upload và quản lý file.
- Admin Panel: quản trị hệ thống, quản lý người dùng và cấu hình ngân hàng.

---

## Tổng quan truy cập
- Đăng nhập:
  - Cách đăng nhập: sử dụng tài khoản đã đăng ký (hệ thống dùng Flask-Login). Phân quyền theo role (user / admin).
  - Quy tắc mật khẩu:
    - Mật khẩu lưu an toàn bằng hashing (bcrypt / werkzeug.security).
    - Cấm dùng mật khẩu mặc định hoặc các mật khẩu phổ biến.
- Bảo mật: mật khẩu băm, session quản lý, chỉ admin mới truy cập admin panel.

### Cảnh báo validation logic (tổng quan)
- Mọi upload đều qua pipeline: Upload -> Detection -> Parse -> Validate -> Store/Reject.
- Validation có hai mức:
  - ERROR (critical): dừng xử lý, file có thể bị xóa, trả về INVALID. Ví dụ: thiếu Currency, Opening/Closing Balance, không có giao dịch hợp lệ, balance mismatch.
  - WARNING (non-critical): vẫn tạo StatementLog nhưng hiển thị cảnh báo. Ví dụ: thiếu Account Number (redirect để nhập), vài giao dịch thiếu narrative/date/amount.
- UI behavior:
  - ERROR → flash danger + liệt kê lỗi (hiển thị tối đa 5 lỗi), không tạo StatementLog (ngoại trừ chỉ thiếu account).
  - WARNING → flash warning, vẫn tạo StatementLog.

### Chi tiết cảnh báo cần lưu ý (ngắn gọn)
1. Header (ERROR nếu thiếu)
   - Currency: "❌ Thiếu thông tin Loại tiền (Currency)"
   - Opening Balance: "❌ Thiếu thông tin Số dư đầu kỳ (Opening Balance)"
   - Closing Balance: "❌ Thiếu thông tin Số dư cuối kỳ (Closing Balance)"
   - Bank Code: "❌ Thiếu thông tin Tên ngân hàng (Bank Code)"
   - Account Number: optional — nếu thiếu, hệ thống redirect user để nhập.

2. Transaction (mỗi row)
   - Mỗi giao dịch hợp lệ phải có: Transaction Date (parseable), Narrative (non-empty), và ít nhất một trong Credit / Debit / TransactionFee / TransactionVAT.
   - Nếu không có giao dịch hợp lệ: ERROR "❌ Không có giao dịch hợp lệ nào..."
   - Thống kê cảnh báo:
     - Missing amount fields → "⚠️ Thiếu thông tin Credit/Debit/Fee/VAT cho X/Y giao dịch"
     - Missing narrative → "⚠️ Thiếu thông tin Narrative (Diễn giải) cho X/Y giao dịch"
     - Missing date → "⚠️ Thiếu thông tin Transaction Date (Ngày giao dịch) cho X/Y giao dịch"

3. Balance validation
   - Công thức: Expected_closing = Opening + (ΣCredit - ΣDebit - ΣFee - ΣVAT)
   - Tolerance: ±0.01
   - Nếu vượt tolerance → ERROR, xóa file, xóa BankLog liên quan, trả về detailed breakdown.

### Lời khuyên cho user / admin
- Nếu gặp balance mismatch: kiểm tra dấu thập phân, ký hiệu tiền tệ, hàng ẩn, mapping cột (col_keyword/col_value), row range.
- Fee-only transactions hợp lệ nếu có date + narrative — đảm bảo các trường này không rỗng.
- Admin có thể reprocess sau khi chỉnh cấu hình; luôn kiểm tra logs để xác định nguyên nhân.

---

## User Panel (Người dùng)

### 1. Dashboard
- Hiển thị thống kê tải lên gần nhất, trạng thái xử lý, thông báo lỗi.
- Nút nhanh để Upload file mới.

### 2. Upload file
- Hỗ trợ các định dạng: xls, xlsx, csv, mt940, txt.
- Quy trình:
  1. Chọn file -> tên file được secure_filename().
  2. Validate extension.
  3. Lưu tạm vào `uploads/`.
  4. Gọi File Service -> Detection Service -> lưu kết quả vào DB.
  5. Gọi cleanup_file() để xóa file tạm.
- Nếu lỗi: hiện thông báo chi tiết và lưu log.

### 6. Validation rules (chi tiết, quan trọng)

Mục tiêu: đảm bảo dữ liệu trích xuất từ file đủ tin cậy để tính toán số dư và tạo MT940. Các rule dưới đây được áp dụng trong services/statement_service.py (validate_statement_data và parse_and_store_statement).

1) Phân loại lỗi
- ERROR (critical): file không thể tiếp tục xử lý → xóa file và trả về trạng thái INVALID.
  - Thiếu Currency
  - Thiếu Opening Balance
  - Thiếu Closing Balance
  - Không có bất kỳ giao dịch hợp lệ nào (xem định nghĩa giao dịch hợp lệ)
  - Closing Balance không khớp với công thức (tùy theo tolerance)
- WARNING (non-critical): vẫn cho phép tạo StatementLog nhưng cần thông báo/điều chỉnh bởi user/admin.
  - Thiếu Account Number (được cho phép; redirect để user nhập thủ công)
  - Một vài giao dịch thiếu Narrative hoặc Transaction Date hoặc thiếu amount fields — số lượng nhỏ không chặn xử lý nhưng cần cảnh báo.

2) Header validation (ERROR nếu thiếu)
- Currency:
  - Message: "❌ Thiếu thông tin Loại tiền (Currency)"
- Opening Balance:
  - Message: "❌ Thiếu thông tin Số dư đầu kỳ (Opening Balance)"
- Closing Balance:
  - Message: "❌ Thiếu thông tin Số dư cuối kỳ (Closing Balance)"
- Bank Code:
  - Message: "❌ Thiếu thông tin Tên ngân hàng (Bank Code)"
- Account Number:
  - Optional. Nếu thiếu: tạo StatementLog thành công nhưng redirect tới trang chỉnh sửa để user nhập.

3) Transaction validation (mỗi giao dịch)
- Yêu cầu bắt buộc cho một giao dịch hợp lệ:
  1. Transaction Date (non-empty, parseable)
  2. Narrative / Diễn giải (non-empty)
  3. Ít nhất một trong các trường sau có giá trị: Credit OR Debit OR TransactionFee OR TransactionVAT
- Nếu không tìm thấy giao dịch nào trong file:
  - Message (ERROR): "❌ Không tìm thấy giao dịch nào trong file. Phải có tối thiểu 1 giao dịch hợp lệ."
- Nếu không có giao dịch hợp lệ nào:
  - Message (ERROR): "❌ Không có giao dịch hợp lệ nào. Mỗi giao dịch phải có: Transaction Date, Narrative, và ít nhất một trong Credit/Debit/Transaction Fee/Transaction VAT"
- Tính số giao dịch có vấn đề:
  - Missing amount fields → "⚠️ Thiếu thông tin Credit/Debit/Fee/VAT cho X/Y giao dịch"
  - Missing narrative → "⚠️ Thiếu thông tin Narrative (Diễn giải) cho X/Y giao dịch"
  - Missing date → "⚠️ Thiếu thông tin Transaction Date (Ngày giao dịch) cho X/Y giao dịch"

4) Parsing & Acceptable formats
- Transaction Date: hỗ trợ nhiều định dạng; ưu tiên parse với dayfirst=True. Sau parse nội bộ chuyển về 'ddmmyyyy' cho lưu trữ và sau đó sang YYMMDD cho MT940.
- Amount fields: chấp nhận chuỗi có dấu phẩy/thập phân, ký hiệu tiền tệ ($, €, £) hoặc ngoặc () cho số âm. Hàm float_safe thực hiện chuẩn hóa.
- Nếu một trường không parse được thành số nhưng không rỗng → coi là "present" (đánh dấu có value) nhưng trong balance calculation sẽ coi là 0.0 nếu không parse được.

5) Eligibility cho balance calculation
- Chỉ dùng các giao dịch "eligible" để tính tổng: phải có transactiondate, narrative non-empty, và ít nhất một trong credit/debit/fee/vat khác 0 (sau float_safe).
- Tổng:
  - total_credit = Σ abs(credit) trên các eligible rows
  - total_debit = Σ abs(debit) trên các eligible rows
  - total_fee = Σ abs(transactionfee) trên các eligible rows
  - total_vat = Σ abs(transactionvat) trên các eligible rows

6) Balance validation (ERROR nếu không khớp)
- Công thức:
  - Số dư phát sinh = total_credit - total_debit - total_fee - total_vat
  - Expected_closing = Opening_balance + Số dư phát sinh
- Tolerance: ±0.01 (đơn vị tiền tệ nhỏ nhất)
- Nếu |Expected_closing - Closing_balance| > 0.01:
  - Hành động: xóa file upload nếu có, xóa BankLog liên quan, trả về:
    - status: "INVALID"
    - message: "Số dư cuối kỳ khác Số dư phát sinh + Số dư đầu kỳ"
    - errors: detailed breakdown (Opening, Total Credit, Total Debit, Total Fee, Total VAT, computed expected, file closing, chênh lệch)
  - Ví dụ hiển thị (đã dùng trong code):
    - "❌ Số dư cuối kỳ <> Số dư phát sinh + Số dư đầu kỳ"
    - Sau đó list chi tiết với định dạng tiền: {value:,.2f}

7) Severity & UI handling
- ERROR → show flash danger + list errors (first up to 5), không tạo StatementLog (ngoại trừ trường hợp chỉ thiếu account).
- WARNING → show flash warning, vẫn tạo StatementLog nếu không có ERROR.

8) Logging & audit
- Tất cả validation errors/warnings phải được log (current_app.logger.warning/info) cùng payload file name, bank_code, user_id để dễ debug.
- BankLog/StatementLog nên ghi đủ trace để admin xem lại nguyên nhân (vd: raw parse preview, missing fields count).

9) Recommendations cho người dùng/admin
- Nếu gặp lỗi balance mismatch: kiểm tra file nguồn (định dạng số, dấu thập phân, hàng ẩn), kiểm tra mapping cấu hình bank (col_keyword/col_value, row range).
- Đối với các giao dịch fee-only: đảm bảo narrative + date tồn tại để tránh bị loại.
- Unit tests: cover các trường hợp
  - file thiếu header bắt buộc
  - file có transaction fee-only
  - file có giao dịch parse lỗi amount
  - balance mismatch case

10) Messages (tổng hợp để hiển thị)
- Critical errors (sample):
  - "❌ Thiếu thông tin Loại tiền (Currency)"
  - "❌ Thiếu thông tin Số dư đầu kỳ (Opening Balance)"
  - "❌ Thiếu thông tin Số dư cuối kỳ (Closing Balance)"
  - "❌ Không tìm thấy giao dịch nào trong file. Phải có tối thiểu 1 giao dịch hợp lệ."
  - "❌ Không có giao dịch hợp lệ nào. Mỗi giao dịch phải có: Transaction Date, Narrative, và ít nhất một trong Credit/Debit/Transaction Fee/Transaction VAT"
  - "❌ Số dư cuối kỳ <> Số dư phát sinh + Số dư đầu kỳ"
- Warnings:
  - "⚠️ Thiếu thông tin Credit/Debit/Fee/VAT cho {missing}/{total} giao dịch"
  - "⚠️ Thiếu thông tin Narrative (Diễn giải) cho {missing}/{total} giao dịch"
  - "⚠️ Thiếu thông tin Transaction Date (Ngày giao dịch) cho {missing}/{total} giao dịch"

---

## Admin Panel (Quản trị viên)

### 1. Dashboard Admin
- Tổng quan hệ thống: số file chờ xử lý, lỗi, trạng thái worker, logs gần nhất.

### 2. User Management
- Tạo / Sửa / Xóa tài khoản.
- Gán role (user / admin).
- Reset mật khẩu, disable/enable tài khoản.
- Lịch sử hoạt động (audit) cơ bản.

### 3. Bank Configuration (Cấu hình ngân hàng)
- Thêm/sửa cấu hình mapping cho từng ngân hàng (app/models/bank_config.py).
- Kích hoạt/deactivate các cấu hình.
- Kiểm tra và test cấu hình với tệp mẫu.

### 4. Bank Logs & Audit
- Xem log import, lỗi nhận diện, chi tiết transaction.
- Lọc theo ngày, ngân hàng, trạng thái.

### 5. File Review & Reprocess
- Xem danh sách file đã upload, xem chi tiết mapping và kết quả detection.
- Cho phép admin reprocess, override mapping hoặc xóa entry.

### 6. System Settings
- Cấu hình global (ALLOWED_EXTENSIONS, upload path, DB connection string).
- Thay đổi cấu hình chạy ứng dụng (port, debug) nếu cần.

---

## Quy trình vận hành (ví dụ: upload -> xử lý)
1. User upload file -> lưu tạm.
2. Detection Service phân tích, xác định cấu hình ngân hàng.
3. Kết quả được lưu vào DB, thông báo trạng thái người dùng.
4. Admin kiểm tra logs nếu có lỗi, điều chỉnh config và reprocess.

---

## Quy tắc lỗi và rollback
- Tất cả commit DB phải theo mẫu:
  try:
      db.session.commit()
  except Exception as e:
      db.session.rollback()
      return jsonify({"status": "FAILED", "message": str(e)}), 500

---

## Bảo mật & vận hành
- Luôn dùng secure_filename() khi lưu file.
- Xác thực và phân quyền chặt chẽ cho các endpoint admin.
- Xác thực đầu vào file, giới hạn kích thước và loại file.

---

## FAQ ngắn
- Làm sao thêm định dạng file mới?
  1. Cập nhật ALLOWED_EXTENSIONS trong config.py
  2. Thêm reader trong app/readers/
  3. Cập nhật detection service để nhận diện

- Làm sao tạo blueprint mới?
  1. Tạo thư mục app/blueprints/<name>
  2. Thêm __init__.py và routes.py
  3. Đăng ký blueprint trong app.py

---

## Chuyển sang Word (.docx)
- Dùng script tools/generate_user_guide.py (đã có) để chuyển Markdown trong docs/ sang .docx:
  python tools\generate_user_guide.py

---

## 🧪 Testing (ghi chú cập nhật)
- Thêm test unit để kiểm tra trường hợp "giao dịch chỉ có transactionfee/transactionvat" được chấp nhận:
  - Input: transaction có transactiondate + narrative + chỉ transactionfee (credit/debit rỗng).
  - Expected: giao dịch được coi là hợp lệ và xuất ra dòng :61/:86 trong MT940.
- Cập nhật test tổng số dòng giao dịch tương ứng khi thêm trường hợp fee-only.
