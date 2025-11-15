import re
from pathlib import Path
p = Path('translations/en/LC_MESSAGES/messages.po')
s = p.read_text(encoding='utf-8')
# Find all msgid/msgstr pairs
pairs = re.findall(r'msgid\s+"([\s\S]*?)"\s*\nmsgstr\s+"([\s\S]*?)"', s)
empty = []
for mid, mstr in pairs:
    mid = mid.replace('\n','\\n')
    mstr = mstr.replace('\n','\\n')
    if mstr.strip() == '' or mstr.strip() == mid.strip():
        empty.append((mid, mstr))
print(f'Untranslated or identical translations: {len(empty)}')
for mid, mstr in empty[:200]:
    print('---')
    print('msgid:', repr(mid))
    print('msgstr:', repr(mstr))
