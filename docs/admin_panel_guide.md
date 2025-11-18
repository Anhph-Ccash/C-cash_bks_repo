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
