from pathlib import Path
import re

p = Path('translations/vi/LC_MESSAGES/messages.po')
s = p.read_text(encoding='utf-8')

# find msgid lines that contain 'Admin Panel' or 'User Panel' etc.
changed = 0

def replace_for_mid(mid):
    new = mid.replace('Admin Panel', 'Bảng quản trị')
    new = new.replace('User Panel', 'Bảng người dùng')
    # some templates use 'Admin Users' or similar
    new = new.replace('Admin Users', 'Người dùng (Admin)')
    return new

pattern = re.compile(r'(msgid\s+"([\s\S]*?Admin Panel[\s\S]*?)"\s*\nmsgstr\s+")([\s\S]*?)(\")', re.MULTILINE)

def repl(m):
    global changed
    full_mid = m.group(2)
    new_mid = replace_for_mid(full_mid)
    changed += 1
    # return msgid line unchanged but set msgstr to new_mid
    return 'msgid "' + full_mid + '"\nmsgstr "' + new_mid.replace('"','\\"') + '"'

s2, n = pattern.subn(repl, s)
if n > 0:
    p.write_text(s2, encoding='utf-8')
    print(f'Updated {n} msgstr entries (Admin Panel matches)')
else:
    print('No Admin Panel matches found')
