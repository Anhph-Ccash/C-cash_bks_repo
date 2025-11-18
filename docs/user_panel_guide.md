# User Panel Guide — C-cash_bks_repo

<!-- ===== Vietnamese (FIRST) ===== -->
## Mục tiêu (Tiếng Việt)
Mô tả các module chính dành cho người dùng nghiệp vụ, luồng thao tác và wireframe cho từng màn hình.

## Modules (Người dùng)
1. Upload
   - Chức năng: chọn file (Excel/CSV/ZIP/MT940/TXT), validate client-side, submit.
   - Quy tắc: secure_filename(), validate extension, giới hạn kích thước, thông báo tiến trình.
2. Lịch sử Upload
   - Danh sách các bản ghi đã upload (PENDING/SUCCESS/FAILED), filter theo ngày/ngân hàng/trạng thái.
   - Hành động: xem chi tiết, tải MT940, xóa (chỉ owner).
3. Chi tiết Sổ phụ (view/edit)
   - Header: account number (có thể chỉnh), currency, opening/closing balance.
   - Transactions: chỉnh narrative, đánh dấu ignore, lưu thay đổi.
   - Hành động: Save, Regenerate MT940, Reprocess.
4. Hồ sơ người dùng (Profile)
   - Cập nhật thông tin, đổi mật khẩu, logout.
5. Trợ giúp / Hướng dẫn lỗi
   - Hiển thị lỗi parse với ví dụ mẫu, liên kết file mẫu.

## Luồng nghiệp vụ chính
- Upload file đơn:
  1. Upload → hiển thị progress.
  2. Server trả PENDING → xử lý background (detection/parse/validate).
  3. SUCCESS: show MT940 + details.
  4. INVALID: show lỗi chi tiết, user sửa & reupload.
- Upload ZIP: extract → xử lý từng file → tổng hợp kết quả.

## Wireframe (Tiếng Việt)
1. Dashboard:
   - Header: chọn ngôn ngữ, menu user
   - Thống kê: recent uploads, quick upload
   - Bảng log: [Ngày, File, Ngân hàng, Trạng thái, Hành động]
2. Trang Upload:
   - Chọn file, chọn công ty, nút Upload, link file mẫu, progress bar
3. Trang Chi tiết:
   - Trái: form header (editable)
   - Phải: bảng transactions với inline edit
   - Footer: [Save] [Generate MT940] [Send to Admin]

## UX notes (Tiếng Việt)
- Hiển thị ví dụ khi validation lỗi (ví dụ format date).
- Cho phép tải tệp gốc & file MT940.
- Thông báo được localize theo ngôn ngữ đã chọn.

## Hình minh họa (Tiếng Việt)
- Dashboard: ![User Dashboard VI](images/user_dashboard_vi.png)
- Upload: ![Upload VI](images/upload_vi.png)
- Statement Detail: ![Statement Detail VI](images/statement_detail_vi.png)

---

<!-- ===== English (SECOND) ===== -->
## Purpose (English)
Describe user modules, business flows and text wireframes for screens.

## Modules (User)
1. Upload
   - Function: select file (Excel/CSV/ZIP/MT940/TXT), client-side validation, submit.
   - Rules: secure_filename(), extension check, file size limit, notify processing start.
2. Upload History
   - Show upload records (PENDING/SUCCESS/FAILED), filters (date, bank_code, status).
   - Actions: view details, download MT940, delete (owner only).
3. Statement Detail (view/edit)
   - Header: editable account number, currency, opening/closing balance.
   - Transactions: parsed rows, inline edit narrative, mark ignore.
   - Buttons: Save, Regenerate MT940, Reprocess.
4. Profile
   - Update info, change password, logout.
5. Help / Error Guidance
   - Present parsing errors with sample files.

## Key Flows (English)
- Single-file upload:
  1. User uploads → UI shows "Uploading..."
  2. Server returns PENDING, background processing (detection/parse/validate).
  3. On SUCCESS: display MT940 link + details.
  4. On INVALID: list errors; user may reupload.
- ZIP batch upload: extract → process each file → summary.

## Wireframe (English)
- Dashboard: header, stats, quick upload, recent logs.
- Upload page/modal: file selector, company select, sample link, progress.
- Statement Detail: editable header, transactions table, actions.

## UX & Testing (English)
- Show friendly examples on validation failure (date formats).
- Allow download of original file and generated MT940.
- Localize messages according to language selector.
- Test: fee-only transactions, missing-account flow, balance mismatch.

<!-- Note: add image files into docs/images -->
