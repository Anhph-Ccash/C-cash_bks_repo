import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from factory import create_app

app = create_app()

routes = [
    '/',
    '/admin/admin-users',
    '/admin/admin-view-logs',
    '/admin/admin-upload',
    '/admin/manage-bank-configs',
    '/admin/manage-companies',
    '/user/user-upload-page',
    '/user/user-logs'
]

# Vietnamese tokens to search for (common UI tokens)
vi_tokens = [
    'Quản lý', 'Tải lên', 'Nhật ký', 'Tải sổ phụ', 'Tải tệp', 'Người dùng', 'Công ty',
    'Chọn ngôn ngữ', 'Đăng xuất', 'Tải MT940', 'Tải tệp Excel gốc', 'Chưa có', 'Thêm',
    'Hiển thị', 'Thời gian', 'Trạng thái', 'Tìm kiếm', 'Xóa', 'Chi tiết'
]

results = {}

with app.test_client() as c:
    with c.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['user_id'] = 1
        sess['username'] = 'admin'
        sess['lang'] = 'en'

    for r in routes:
        try:
            rv = c.get(r)
            body = rv.get_data(as_text=True)
        except Exception as e:
            results[r] = {'error': str(e)}
            continue
        found = []
        for t in vi_tokens:
            if t in body:
                found.append(t)
        results[r] = {'found': found, 'snippet': body[:400]}

# Print concise report
for r, info in results.items():
    print('---')
    print('Route:', r)
    if 'error' in info:
        print('Error:', info['error'])
        continue
    if info['found']:
        print('Vietnamese tokens found:', info['found'])
    else:
        print('No Vietnamese tokens detected')

print('\nSummary: pages with Vietnamese tokens:')
for r, info in results.items():
    if 'found' in info and info['found']:
        print('-', r, '->', ', '.join(info['found']))
