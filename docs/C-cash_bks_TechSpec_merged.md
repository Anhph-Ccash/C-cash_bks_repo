

<!-- source: login_guide.md -->

# Login Guide — C-cash_bks_repo

<!-- ===== Vietnamese (FIRST) ===== -->
## Đăng nhập (Tiếng Việt)

### Mục tiêu
Hướng dẫn dùng cho giao diện đăng nhập: lựa chọn ngôn ngữ (Vi/En), nhập username/password, xử lý lỗi và cảnh báo bảo mật.

### UI fields
- Trình chọn ngôn ngữ: [Tiếng Việt | English] — lưu lựa chọn vào session/cookie.
- Tên đăng nhập (username)
- Mật khẩu (password)
- Ghi nhớ đăng nhập (Remember me)
- Nút: [Đăng nhập], [Quên mật khẩu?]

### Luồng đăng nhập
1. Chọn ngôn ngữ → UI/Thông báo hiển thị theo ngôn ngữ đã chọn.
2. Nhập username & password → Gửi lên server.
3. Server xác thực:
   - Thành công: tạo session, chuyển tới dashboard theo role.
   - Thất bại: hiển thị thông báo chung (KHÔNG tiết lộ username hay password sai).
4. Quá nhiều lần thất bại → lockout, hiển thị hướng dẫn reset.

### Quy tắc & chính sách
- Password: tối thiểu 8 ký tự; khuyến nghị chữ hoa, chữ thường, số, ký tự đặc biệt.
- Lưu mật khẩu bằng hashing an toàn (bcrypt / werkzeug).
- Lockout & throttling: giới hạn (ví dụ 5 lần) trong window (ví dụ 15 phút).
- Session timeout: cấu hình (ví dụ 15–30 phút idle).
- MFA: khuyến nghị cho admin.
- Reset password: token 1-time, expiry ngắn (ví dụ 1 giờ) gửi qua email.

### Thông báo lỗi mẫu (Tiếng Việt)
- "Tên đăng nhập hoặc mật khẩu không đúng"
- "Tài khoản bị khóa do đăng nhập thất bại nhiều lần"
- "Cần nhập tên đăng nhập và mật khẩu"

### Accessibility & Bảo mật (Tiếng Việt)
- Thứ tự focus: language → username → password → remember → submit.
- Dùng HTTPS production; rate-limit endpoint; log hành vi đăng nhập (IP, user-agent).

### Hình minh họa (Tiếng Việt)
- Wireframe: ![Login VI](images/login_vi.png)

---

<!-- ===== English (SECOND) ===== -->
## Login (English)

### Purpose
Guide for login UI: language selector (VI/EN), username/password, error handling and security warnings.

### UI fields
- Language selector: [Vietnamese | English] — stored in session/cookie.
- Username
- Password
- Remember me (optional)
- Buttons: [Log in], [Forgot password?]

### Login flow
1. User selects language → UI & validation messages shown accordingly.
2. User enters credentials and submits.
3. Server authenticates:
   - Success: create session and redirect based on role.
   - Failure: show generic message (do NOT reveal which field was wrong).
4. Too many failed attempts → account lockout with instructions to reset.

### Policies
- Password: min 8 chars; recommend uppercase, lowercase, digits, symbols.
- Store password hashed (bcrypt / werkzeug).
- Lockout & throttling: e.g., 5 attempts in 15 minutes.
- Session timeout configurable (e.g., 15–30 min).
- Recommend MFA for admin.
- Reset password via tokenized email link (1-time, short expiry).

### Error messages (English)
- "Invalid username or password"
- "Account locked due to multiple failed attempts"
- "Username and password are required"

### Accessibility & Security (English)
- Focus order: language → username → password → remember → submit.
- Use HTTPS, rate-limit the login endpoint, log attempts with IP & user-agent.

### Wireframe (English)
- Wireframe sample: ![Login EN](images/login_en.png)

<!-- Note: add the image files to e:\C-cash_bks_repo\docs\images\login_vi.png and login_en.png -->


<!-- source: user_panel_guide.md -->

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


<!-- source: admin_panel_guide.md -->

# Admin Panel Guide — C-cash_bks_repo

<!-- ===== Vietnamese (FIRST) ===== -->
## Mục tiêu (Tiếng Việt)
Hướng dẫn cho admin: module, quyền, nghiệp vụ quản lý, wireframe cho từng màn hình.

## Modules (Admin)
1. Quản lý Người dùng
   - CRUD, gán role, enable/disable, reset password, audit.
2. Quản lý Công ty
   - Tạo/sửa công ty, cấu hình SFTP, remote paths.
3. Cấu hình Ngân hàng (Bank Config)
   - Quản lý BankStatementConfig (identify_info, keywords, col_keyword/col_value, row ranges).
   - Upload batch, test config với sample file.
4. Nhật ký Sổ phụ (Statement Logs)
   - Xem toàn bộ StatementLog, filter, reprocess, upload MT940 → SFTP.
5. Nhật ký lỗi (Bank Logs)
   - Inspect logs, export investigation data.
6. Cấu hình hệ thống & Job Monitor
   - ALLOWED_EXTENSIONS, UPLOAD_FOLDER, session settings, job queue monitor.

## Luồng admin chính
- Thêm cấu hình ngân hàng:
  - Add -> Fill mappings -> Save -> Test with sample.
- Reprocess:
  - Open statement → Adjust mapping → Re-run → Review result.
- Bulk upload config:
  - Upload Excel -> Validate rows -> Import.

## Wireframe (Tiếng Việt)
- Admin Dashboard: stats, recent errors, quick actions.
- Bank Config page: table + add/edit modal + test area.
- Statement Logs: filters + detail drawer + MT940 generator.

## Bảo mật & vận hành (Tiếng Việt)
- Chỉ admin truy cập endpoints admin.
- Hành động nhạy cảm require confirmation + audit log.
- Backup & test mode trước khi áp dụng thay đổi lớn.

## Hình minh họa (Tiếng Việt)
- Admin Dashboard: ![Admin Dashboard VI](images/admin_dashboard_vi.png)
- Bank Config: ![Bank Config VI](images/bank_config_vi.png)
- Statement Logs: ![Statement Logs VI](images/statement_logs_vi.png)

---

<!-- ===== English (SECOND) ===== -->
## Purpose (English)
Guide for admin: modules, responsibilities, wireframes for each screen.

## Modules (Admin)
1. Users Management
   - CRUD users, assign roles, enable/disable, reset password, audit.
2. Companies Management
   - Create/edit companies, SFTP config, remote paths.
3. Bank Configurations
   - Manage BankStatementConfig entries (identify_info, keywords, col_keyword/col_value, row_start/row_end).
   - Bulk upload configs via Excel; test against sample files.
4. Statement Logs & Processing
   - Central view across companies; filters; actions: view, reprocess, regenerate MT940, upload to SFTP, delete.
5. Bank Logs / Error Audit
   - Inspect detection/parsing errors; export.
6. System Settings & Job Monitor
   - Global settings and background worker monitoring.

## Key Admin Flows (English)
- Create Bank config: add -> fill mapping -> save -> test against sample.
- Reprocess failed statement: adjust mapping -> re-run -> review.
- Bulk import configs: validate rows before storing; show per-row errors.

## Wireframe (English)
- Admin Dashboard: global stats, recent failures, quick actions.
- Bank Config page: list + Edit modal + Test area.
- Statement Logs: filters, result table, detail drawer with MT940 preview.

## Security & Ops (English)
- Admin endpoints restricted to admin role.
- Sensitive actions require confirmation and are audited.
- Backup before bulk changes; test mode for imports.

## Wireframe images (English)
- Admin Dashboard EN: ![Admin Dashboard EN](images/admin_dashboard_en.png)
- Bank Config EN: ![Bank Config EN](images/bank_config_en.png)
- Statement Logs EN: ![Statement Logs EN](images/statement_logs_en.png)

<!-- Note: add images into docs/images -->



<!-- source: sftp_guide.md -->

# SFTP Integration Guide — C-cash_bks_repo

<!-- ===== Vietnamese (FIRST) ===== -->
## Giới thiệu (Tiếng Việt)
Mô tả: upload MT940 lên SFTP (thủ công & tự động), auth bằng key/password. Wireframe modal: ![SFTP Modal VI](images/sftp_modal_vi.png)

## Cấu hình (Tiếng Việt)
- SFTP_HOST, SFTP_PORT, SFTP_USERNAME, SFTP_PASSWORD (secure), SFTP_PRIVATE_KEY_PATH, SFTP_REMOTE_PATH, SFTP_TIMEOUT, SFTP_ALWAYS_OVERWRITE.
- Ưu tiên key-based auth; không lưu mật khẩu plaintext.

## Luồng upload (Tiếng Việt)
- Thủ công: admin → Statement Logs → Upload to SFTP → ghi trạng thái (PENDING/UPLOADED/FAILED).
- Tự động: worker picks PENDING → upload with retry/backoff → update status.

## Xử lý lỗi & Logging (Tiếng Việt)
- Retry transient errors; alert admin on permanent auth errors.
- Lưu SFTP activity vào BankLog/StatementLog (attempts, last_error, sftp_response).
- Wireframe modal: ![SFTP Modal VI](images/sftp_modal_vi.png)

## Bảo mật (Tiếng Việt)
- Key-based auth; private key permission 600; secrets in vault if possible.
- Validate remote path; use secure temp storage; delete temp after upload.

---

<!-- ===== English (SECOND) ===== -->
## Introduction (English)
Overview: upload MT940 files to customer SFTP servers (manual & automated), supports key/password auth. Wireframe modal: ![SFTP Modal EN](images/sftp_modal_en.png)

## Configuration (English)
- Keys: SFTP_HOST, SFTP_PORT, SFTP_USERNAME, SFTP_PASSWORD (secure), SFTP_PRIVATE_KEY_PATH, SFTP_REMOTE_PATH, SFTP_TIMEOUT, SFTP_ALWAYS_OVERWRITE.
- Prefer key-based auth; avoid storing plaintext passwords.

## Upload flows (English)
- Manual: Admin → Statement Logs → Upload to SFTP → update status (PENDING/UPLOADED/FAILED).
- Automated: background worker picks queued entries, retries transient errors with backoff, update status and logs.

## Error handling & logging (English)
- Retry network/timeouts; do not retry persistent auth failures.
- Log timestamp, statement_id, filename, remote_path, attempts, last_error.
- Provide UI to view recent failures and retry manually.

## Security best practices (English)
- Use key-based auth and secure key storage.
- Use SSH/SFTP only, whitelist IPs if possible, sanitize filenames.
- Do not expose secrets in logs.

## Wireframes & Testing (English)
- UI: Upload modal with host/remote path preview, confirm button, masked credentials.
- Tests: mock paramiko transport for unit tests; integration tests against a test SFTP server.
