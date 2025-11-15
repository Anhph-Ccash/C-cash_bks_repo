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
        sess['lang'] = 'en'

    rv = c.get('/admin/admin-view-logs')
    body = rv.get_data(as_text=True)
    if 'Upload History' in body or 'Upload Logs' in body or 'Upload' in body:
        print('English content detected')
    else:
        print('English content not detected')
    print('\n--- snippet start ---\n')
    print(body[:800])
    print('\n--- snippet end ---\n')
