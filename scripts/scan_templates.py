import os, re, json

ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'templates')
keywords = [
    'Đăng','Nhật','Tải','Ngân hàng','Thời gian','Thành công','Lỗi','Tất cả',
    'Xóa','Hủy','Hiển thị','Trang','Tệp','Mã Ngân hàng','Trạng thái','Hành động',
    'Thông báo','Từ khóa','Quản lý','Công ty','Tải lên','Nhật ký','Đăng nhập'
]
pattern = re.compile('|'.join(re.escape(k) for k in keywords))

results = []
for dirpath, dirnames, filenames in os.walk(ROOT):
    for fn in filenames:
        if not fn.endswith('.html'):
            continue
        path = os.path.join(dirpath, fn)
        with open(path, 'r', encoding='utf-8') as f:
            text = f.read()
        matches = pattern.findall(text)
        count = len(matches)
        # Also count number ofgettext usages
        gettext_count = text.count("{{ _('") + text.count("{% trans %}")
        results.append({'file': os.path.relpath(path), 'matches': count, 'gettext_count': gettext_count, 'sample_matches': list(set(matches))[:10]})

# Sort by matches desc
results_sorted = sorted(results, key=lambda x: x['matches'], reverse=True)
print(json.dumps(results_sorted, indent=2, ensure_ascii=False))
