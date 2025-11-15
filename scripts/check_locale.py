import time
import urllib.request
import http.cookiejar

base = 'http://127.0.0.1:5001'
set_lang_path = '/i18n/set-lang/en'
target = '/admin/admin-view-logs'

cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# wait for server and set language
for i in range(12):
    try:
        # fetch login page to get csrf token
        login_get = opener.open(base + '/auth/login', timeout=5)
        login_html = login_get.read().decode('utf-8', errors='ignore')
        import re
        m = re.search(r'name="csrf_token" value="([^"]+)"', login_html)
        csrf = m.group(1) if m else ''

        # login as default admin (admin/admin123)
        login_data = urllib.parse.urlencode({'username': 'admin', 'password': 'admin123', 'csrf_token': csrf}).encode()
        req_login = urllib.request.Request(base + '/auth/login', data=login_data)
        opener.open(req_login, timeout=5)

        # set language to EN
        opener.open(base + set_lang_path, timeout=5)

        # fetch target page using same cookie jar
        req2 = urllib.request.Request(base + target)
        with opener.open(req2, timeout=5) as resp:
            body = resp.read().decode('utf-8', errors='ignore')
            if 'Upload History' in body or 'Upload Logs' in body or 'Upload' in body:
                print('English content detected')
            else:
                print('English content not detected — sample check strings missing')
            snippet = body[:800]
            print('\n--- snippet start ---\n')
            print(snippet)
            print('\n--- snippet end ---\n')
        break
    except Exception as e:
        print(f'Attempt {i+1}: server not ready or request failed ({e})')
        time.sleep(1)
else:
    print('Server did not respond in time')
