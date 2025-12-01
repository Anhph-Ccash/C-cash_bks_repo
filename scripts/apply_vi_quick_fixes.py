from pathlib import Path
import re

p = Path('translations/vi/LC_MESSAGES/messages.po')
s = p.read_text(encoding='utf-8')

# mapping from exact msgid to desired Vietnamese msgstr
mapping = {
    "Quản lý - Admin Panel": "Quản lý - Bảng quản trị",
    "👑 Quản lý - Admin Panel": "👑 Quản lý - Bảng quản trị",
    "Admin Panel": "Bảng quản trị",
    "users": "Người dùng",
    "Users": "Người dùng",
    "Upload file": "Tải tệp",
    "Upload": "Tải lên",
    "Original file": "Tệp gốc",
    "Download original file": "Tải tệp gốc",
    "Are you sure you want to delete?": "Bạn có chắc chắn muốn xóa?",
    "Active": "Đã kích hoạt",
    "Inactive": "Chưa kích hoạt",
    "Choose File": "Chọn tệp",
    "No file chosen": "Chưa chọn tệp",
    "Select Language": "Chọn ngôn ngữ",
    "Upload Logs": "Nhật ký tải lên",
    "Upload Bank Statement": "Tải sổ phụ",
    "Admin Page": "Trang quản trị",
}

for mid, newstr in mapping.items():
    # Try to find exact msgid block
    # Build regex to match msgid "..." followed by msgstr "..." block
    esc = re.escape(mid)
    pattern = re.compile(r'(msgid \"' + esc + r'\"\s*\nmsgstr \")([\s\S]*?)(\")', re.MULTILINE)
    if pattern.search(s):
        s = pattern.sub(r'\1' + newstr.replace('"','\\"') + r'\3', s)
    else:
        # also try matching with possible leading/trailing whitespace variations
        pattern2 = re.compile(r'(msgid \"' + esc + r'\"\s*\nmsgstr \"\")', re.MULTILINE)
        if pattern2.search(s):
            s = pattern2.sub('msgid "' + mid + '"\nmsgstr "' + newstr.replace('"','\\"') + '"', s)

p.write_text(s, encoding='utf-8')
print('Applied quick Vietnamese fixes.')
