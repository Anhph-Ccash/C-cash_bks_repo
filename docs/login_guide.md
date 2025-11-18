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
