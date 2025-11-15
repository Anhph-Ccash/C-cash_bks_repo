import re
from pathlib import Path
p = Path('translations/en/LC_MESSAGES/messages.po')
s = p.read_text(encoding='utf-8')
entries = re.split(r"\n\n(?=#|$)", s)
empty = []
for e in entries:
    if 'msgid' in e and 'msgstr' in e:
        mid = re.search(r"msgid\s+""(.*?)""", e, re.S)
        mstr = re.search(r"msgstr\s+""(.*?)""", e, re.S)
        if mid and mstr and mstr.group(1).strip() == '':
            empty.append(mid.group(1))

print('Untranslated msgids (count={}):'.format(len(empty)))
for m in empty:
    print(repr(m))
