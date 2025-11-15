import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from factory import create_app

app = create_app()

with app.test_client() as c:
    with c.session_transaction() as sess:
        sess['role'] = 'admin'
        sess['user_id'] = 1
        sess['username'] = 'admin'
        sess['lang'] = 'en'

    rv = c.get('/admin/admin-users')
    body = rv.get_data(as_text=True)
    # Look for English text we expect
    checks = ['Admin Panel', 'User Management', 'Users', 'Company']
    found = [t for t in checks if t in body]
    print('Found tokens:', found)
    print('\n--- snippet start ---\n')
    print(body[:800])
    print('\n--- snippet end ---\n')
