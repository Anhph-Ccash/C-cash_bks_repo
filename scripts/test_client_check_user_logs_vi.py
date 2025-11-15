import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from factory import create_app

app = create_app()

with app.test_client() as c:
    with c.session_transaction() as sess:
        sess['role'] = 'user'
        sess['user_id'] = 11
        sess['username'] = 'Tri01'
        sess['lang'] = 'vi'

    rv = c.get('/user/logs')
    body = rv.get_data(as_text=True)
    checks = ['Lọc', 'Nhật ký tải lên', 'Tệp gốc']
    found = [t for t in checks if t in body]
    print('Found tokens:', found)
    print('\n--- snippet start ---\n')
    print(body[:800])
    print('\n--- snippet end ---\n')
