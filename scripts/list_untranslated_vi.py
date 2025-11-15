import re
from pathlib import Path
p = Path('translations/vi/LC_MESSAGES/messages.po')
if not p.exists():
    print('File not found:', p)
    raise SystemExit(1)
s = p.read_text(encoding='utf-8')
# Find all msgid/msgstr pairs
pairs = re.findall(r'msgid\s+"([\s\S]*?)"\s*\nmsgstr\s+"([\s\S]*?)"', s)
empty = []
for mid, mstr in pairs:
    # treat empty or identical as untranslated
    if mstr.strip() == '' or mstr.strip() == mid.strip():
        empty.append((mid, mstr))
print(f'Untranslated or identical translations (vi): {len(empty)}')
for mid, mstr in empty[:200]:
    print('---')
    print('msgid:', repr(mid))
    print('msgstr:', repr(mstr))
