import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from factory import create_app

app = create_app()

with app.test_client() as c:
    # Set session values
    with c.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['user_id'] = 1
        sess['username'] = 'admin'
        sess['lang'] = 'vi'

    rv = c.get('/user/user-upload-page')
    body = rv.get_data(as_text=True)
    # check for Vietnamese tokens
    checks = ['Tải lên', 'Nhật ký', 'Tải sổ phụ', 'Nhật ký tải lên', 'Tải tệp', 'Quản lý']
    found = [t for t in checks if t in body]
    if found:
        print('Vietnamese tokens found:', found)
    else:
        print('No Vietnamese tokens detected')
    print('\n--- snippet start ---\n')
    print(body[:800])
    print('\n--- snippet end ---\n')
