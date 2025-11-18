# C-cash_bks_repo — User Guide

Phiên bản: 1.0
Mục đích: Hướng dẫn cài đặt, vận hành và sử dụng các chức năng chính của ứng dụng C-cash_bks_repo.

---

## 1. Tổng quan dự án
C-cash_bks_repo là ứng dụng Flask để quản lý upload và xử lý file sổ phụ ngân hàng. Kiến trúc gồm:
- Application factory (app.py)
- Blueprints: upload, bank_config, bank_log
- DB: PostgreSQL + SQLAlchemy
- Auth: Flask-Login (role-based)

---

## 2. Cài đặt môi trường (dev)
1. Kéo mã về máy:
   - git clone <repo-url> e:\C-cash_bks_repo
2. Tạo và kích hoạt virtualenv:
   - python -m venv .venv
   - .venv\Scripts\activate
3. Cài dependencies:
   - pip install -r requirements.txt
   - pip install -r requirements-dev.txt
   - nếu thiếu: pip install flask-babel pandas openpyxl python-docx
4. Thiết lập biến môi trường (ví dụ):
   - set FLASK_ENV=development
   - set DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
5. Khởi tạo DB (nếu có script migration): theo repo hướng dẫn.

---

## 3. Chạy ứng dụng
- Cách nhanh (dev):
  - set FLASK_APP=app.py
  - flask run --port=5001
- Hoặc: python app.py nếu repo có entrypoint.
- Giao diện mặc định: http://localhost:5001

---

## 4. User Panel (Người dùng)
Chức năng chính:
- Dashboard: theo dõi upload gần nhất, trạng thái xử lý.
- Upload file: hỗ trợ xls, xlsx, csv, mt940, txt.
  - Quy trình: secure_filename -> validate extension -> lưu tạm (uploads/) -> gọi service xử lý -> cleanup_file().
- Upload History: xem trạng thái (PENDING, SUCCESS, FAILED), tải file MT940.
- Profile: đổi mật khẩu, thông tin cá nhân.

Lưu ý bảo mật:
- Luôn dùng secure_filename().
- Giới hạn kích thước upload.

---


## 5. Admin Panel (Quản trị viên)
Chức năng chính:
- Quản lý Users: CRUD, gán role, reset password.
- Bank Configuration: tạo/sửa cấu hình nhận diện sổ phụ (bank_statement_config).
  - Từ phiên bản mới, cấu hình hỗ trợ trường `scan_ranges` (JSON): xác định vùng quét dữ liệu trong file (ví dụ: `[{"range": "A1:O5", "sheet_name": "0"}]`).
  - Khi upload, hệ thống chỉ đọc các vùng scan_ranges để phát hiện ngân hàng, tăng tốc độ và độ chính xác.
  - Cấu hình keywords, col_keyword, col_value cho từng trường (accountno, currency, openingbalance, closingbalance, ...).
  - Smart extraction: trường accountno chỉ nhận số 4-20 chữ số liên tục; currency chỉ nhận mã tiền tệ chuẩn ISO 4217 (VND, USD, EUR, ...); opening/closing balance chỉ nhận số và đơn vị tiền tệ phía sau nếu có.
- Statement Logs & Audit: xem logs, filter, download bản gốc.
- Reprocess: admin có thể reprocess file hoặc chỉnh mapping.

---


## 6. Validation rules & Smart Extraction
(Áp dụng trong services/statement_service.py validate_statement_data)

### Header bắt buộc:
- Opening Balance (Số dư đầu kỳ) — bắt buộc
- Closing Balance (Số dư cuối kỳ) — bắt buộc
- Currency — bắt buộc (chỉ nhận mã tiền tệ chuẩn ISO 4217: VND, USD, EUR, GBP, ...)
- Bank Code — bắt buộc

### Account number:
- Không bắt buộc: nếu thiếu sẽ tạo StatementLog và redirect user để nhập thủ công.
- Chỉ nhận số liên tục 4-20 chữ số (không nhận ký tự khác).

### Giao dịch (transaction) hợp lệ:
- Mỗi giao dịch phải có:
  1. Transaction Date (bắt buộc, định dạng ngày hợp lệ)
  2. Narrative (bắt buộc, không rỗng)
  3. Ít nhất một trong: Credit OR Debit OR TransactionFee OR TransactionVAT
- Giao dịch chỉ có transactionfee hoặc transactionvat (với date + narrative) được coi là hợp lệ.

### Balance validation:
- Số dư phát sinh = Σ(Credit) - Σ(Debit) - Σ(TransactionFee) - Σ(TransactionVAT)
- Expected Closing = Opening + Số dư phát sinh
- Tolerance = 0.01
- Nếu mismatch nghiêm trọng: file bị xóa, logs bị xóa, trả về lỗi INVALID (hiển thị chi tiết tổng Credit/Debit/Fee/VAT).

### Smart extraction:
- Trường openingbalance/closingbalance: chỉ nhận số, có thể kèm đơn vị tiền tệ phía sau (ví dụ: `7529778893 VND`).
- Trường currency: chỉ nhận mã tiền tệ chuẩn (VND, USD, EUR, ...).
- Trường accountno: chỉ nhận số liên tục 4-20 chữ số.

### Thông báo lỗi mẫu (được dịch & hiển thị trong UI):
- ❌ Thiếu thông tin Loại tiền (Currency)
- ❌ Thiếu thông tin Số dư đầu kỳ (Opening Balance)
- ❌ Thiếu thông tin Số dư cuối kỳ (Closing Balance)
- ❌ Không tìm thấy giao dịch nào...
- ❌ Không có giao dịch hợp lệ nào...
- ⚠️ Thiếu thông tin Credit/Debit/Fee/VAT cho X/Y giao dịch
- ⚠️ Thiếu thông tin Narrative cho X/Y giao dịch
- ⚠️ Thiếu thông tin Transaction Date cho X/Y giao dịch

---

## 7. Quy trình upload (tóm tắt)
1. User upload -> lưu tạm.
2. Detection Service phân tích, xác định cấu hình ngân hàng (bank_code).
3. Parse header + details theo configs.
4. Chạy validate_statement_data.
   - Nếu FAIL (critical) -> xóa file, xóa bank log, show errors.
   - Nếu PASS -> tạo StatementLog, sinh MT940, ghi file mt940 vào uploads/mt940.
5. Nếu account missing -> redirect user edit để nhập.

---

## 8. MT940 generation (service)
- Hàm: build_mt940_strict(stmt_log)
- Tags chính: :20:, :25:, :28C:, :60F:, :61:/:86:, :62F:
- Ghi chú:
  - Reference :20: sử dụng BANKCODE + "XXX"
  - Amount format: decimal comma (e.g. 1000,50)
  - Fee/VAT được cộng vào phần debit khi quyết định D/C và amount.

---

## 9. Chạy và viết unit tests
- Thư mục tests/ chứa test_*.py
- Cài pytest và pytest-cov (requirements-dev.txt)
- Chạy toàn bộ tests:
  - python tools\run_all_tests.py
  - hoặc: pytest tests/ -v --cov=services --cov-report=html
- Gợi ý: nếu gặp lỗi import, đảm bảo PYTHONPATH chứa project root hoặc dùng tests/conftest.py để set sys.path.

---

## 10. Troubleshooting (thường gặp)
- ModuleNotFoundError (ví dụ flask_babel): cài package bằng pip install flask-babel hoặc cập nhật requirements.txt.
- ScopeMismatch với fixtures (base_url): set fixture scope="session" trong tests/conftest.py hoặc dùng pytest-base-url flag.
- Lỗi validation: kiểm tra file mẫu, cấu hình bank_statement_config.

---

## 11. Tạo file Word từ Markdown
- Script đã có: tools/generate_user_guide.py (sử dụng python-docx).
- Chạy:
  - pip install python-docx
  - python tools\generate_user_guide.py
- Kết quả: file lưu vào docs/C-cash_bks_repo_User_Guide.docx

---


## 12. Thông tin dev / mở rộng
- Thêm định dạng file mới:
  1. Update ALLOWED_EXTENSIONS trong config.py
  2. Thêm reader trong app/readers/
  3. Cập nhật detection service
- Thêm blueprint:
  1. Tạo app/blueprints/<name>/__init__.py và routes.py
  2. Đăng ký blueprint trong app factory
- Cập nhật/bổ sung dịch thuật (translation):
  1. Chạy task `i18n: extract` để cập nhật messages.pot
  2. Chạy task `i18n: update catalogs` để đồng bộ các file .po
  3. Chạy task `i18n: compile` để sinh file .mo cho các ngôn ngữ
  4. Sửa nội dung dịch trong translations/<lang>/LC_MESSAGES/messages.po nếu cần
  5. Khởi động lại app để áp dụng bản dịch mới

---

## 13. Liên hệ & ghi chú
- Ghi chú nội bộ: giữ logging chi tiết cho upload/parse để dễ gỡ lỗi.
- Backup db trước khi thay đổi migration/config quan trọng.

---
Tài liệu ngắn gọn — cần mở rộng phần hướng dẫn sysadmin hoặc chi tiết API, báo tôi biết phần bạn muốn bổ sung (ví dụ: endpoints API, cấu trúc DB, mẫu file Excel).
