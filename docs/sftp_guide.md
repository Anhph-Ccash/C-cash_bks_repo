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
