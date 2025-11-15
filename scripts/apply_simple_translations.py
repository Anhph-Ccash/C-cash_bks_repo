from pathlib import Path
import re

p = Path('translations/en/LC_MESSAGES/messages.po')
s = p.read_text(encoding='utf-8')

# mapping from msgid to desired msgstr
mapping = {
    "Xem Logs": "View Logs",
    "Đang chọn": "Selected",
    "Đăng xuất": "Logout",
    "Đổi công ty": "Change Company",
    "Hiển thị": "Display",
    "Trước": "Previous",
    "Không": "No",
    "Chỉ xóa được các bản ghi do bạn tải lên (và thuộc công ty đang\n chọn)": "Can only delete records you uploaded (and belonging to the currently selected company)",
    "Email": "Email",
    "English": "English",
    "Tiếng Việt": "Vietnamese",
    "N/A": "N/A",
    "Xem Logs": "View Logs",
    "Xem Logs": "View Logs",
    "Xem Logs": "View Logs",
    "Upload 11 dòng cho VCB (account_number, currency, opening\n_balance, \"\n\"closing_balance, narrative, transaction_date, debit, credit, flow_code, \"\n\"transaction_fee, transaction_vat)": "Upload 11 lines for VCB (account_number, currency, opening_balance, closing_balance, narrative, transaction_date, debit, credit, flow_code, transaction_fee, transaction_vat)",
    "(Tùy chọn) Loại trường để dễ quản lý (account_number, cur\nrency, \"\n\"opening_balance...)": "(Optional) Field type for easier management (account_number, currency, opening_balance...)",
    "Mỗi dòng = 1 cấu hình cho 1 trường. Có thể có nhiều dòng \ncho cùng 1 \"\n\"bank_code.": "Each line = 1 configuration for 1 field. Multiple lines may belong to the same bank_code.",
}

# Apply mapping for exact msgid matches
for mid, mstr in mapping.items():
    # build pattern to find msgid "..." followed by msgstr "..."
    # Escape mid for regex by escaping double quotes
    escaped_mid = mid.replace('"', '\\"')
    pattern = re.compile(r'(msgid \"' + re.escape(mid) + r'\"\s*\nmsgstr \")([\s\S]*?)(\")', re.MULTILINE)
    if pattern.search(s):
        s = pattern.sub(r'\1' + mstr.replace('"','\\"') + r'\3', s)
    else:
        # fallback: try matching with normalized whitespace (newlines replaced)
        norm_mid = mid.replace('\n','\\n')
        pattern2 = re.compile(r'(msgid \"' + re.escape(norm_mid) + r'\"\s*\nmsgstr \")([\s\S]*?)(\")', re.MULTILINE)
        s = pattern2.sub(r'\1' + mstr.replace('"','\\"') + r'\3', s)

p.write_text(s, encoding='utf-8')
print('Applied simple translations.')
