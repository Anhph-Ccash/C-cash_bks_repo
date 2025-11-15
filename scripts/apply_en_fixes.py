from pathlib import Path
import re
p = Path('translations/en/LC_MESSAGES/messages.po')
s = p.read_text(encoding='utf-8')

def set_msgstr(msgid, newstr):
    pattern = re.compile(r'(msgid\s+"' + re.escape(msgid) + r'"\s*\nmsgstr\s+")([\s\S]*?)(\")', re.M)
    if pattern.search(s):
        return pattern.sub(r'\1' + newstr.replace('"','\\"') + r'\3', s)
    return s

s2 = set_msgstr('Quản lý', 'Admin Panel')
if s2 != s:
    p.write_text(s2, encoding='utf-8')
    print('Updated en PO for "Quản lý" -> "Admin Panel"')
else:
    print('No change made')
