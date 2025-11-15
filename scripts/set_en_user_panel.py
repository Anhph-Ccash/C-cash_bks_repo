from pathlib import Path
import re

p = Path('translations/en/LC_MESSAGES/messages.po')
if not p.exists():
    print('EN PO not found:', p)
    raise SystemExit(1)

s = p.read_text(encoding='utf-8')
pattern = re.compile(r'(msgid\s+"Người dùng"\s*\nmsgstr\s+")([\s\S]*?)(\")', re.M)
if pattern.search(s):
    s2 = pattern.sub(r'\1User Panel\3', s)
    p.write_text(s2, encoding='utf-8')
    print('Set "Người dùng" -> "User Panel" in en PO')
else:
    print('msgid "Người dùng" not found in en PO')
