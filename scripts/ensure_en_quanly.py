from pathlib import Path
import re

p = Path('translations/en/LC_MESSAGES/messages.po')
if not p.exists():
    print('EN PO not found:', p)
    raise SystemExit(1)

s = p.read_text(encoding='utf-8')
changed = 0

# Map various msgid variants containing 'Quản lý' to desired English strings
mapping = {
    'Quản lý': 'Admin Panel',
    'Quản lý - Admin Panel': 'Admin Panel',
    'Quản lý - User Panel': 'User Panel',
    'Quản lý Users': 'Manage Users',
    'Quản lý Companies': 'Manage Companies',
    'Quản lý - Admin Users': 'Admin Users',
}

for mid, mstr in mapping.items():
    pattern = re.compile(r'(msgid\s+"' + re.escape(mid) + r'"\s*\nmsgstr\s+")([\s\S]*?)(\")', re.M)
    if pattern.search(s):
        s = pattern.sub(r'\1' + mstr.replace('"','\\"') + r'\3', s)
        changed += 1

# Also handle cases where msgid contains the phrase inside a longer string (substring)
# Example: msgid "Quản lý Công ty - Admin Panel"
pattern_sub = re.compile(r'msgid\s+"([\s\S]*Quản lý[\s\S]*)"\s*\nmsgstr\s+"([\s\S]*?)"', re.M)
for m in pattern_sub.finditer(s):
    full = m.group(1)
    # if current msgstr empty, set a reasonable english replacement using a simple rule
    current_msgstr = m.group(2)
    if current_msgstr.strip() == '':
        # build english by replacing 'Quản lý' with 'Manage' (simple heuristic)
        eng = full.replace('Quản lý', 'Manage').strip()
        # remove trailing ' - Admin Panel' if present (avoid doubling)
        eng = eng.replace(' - Admin Panel', '')
        # write back
        esc_full = re.escape(full)
        pat = re.compile(r'(msgid\s+"' + esc_full + r'"\s*\nmsgstr\s+")([\s\S]*?)(\")', re.M)
        s = pat.sub(r'\1' + eng.replace('"','\\"') + r'\3', s, count=1)
        changed += 1

if changed:
    p.write_text(s, encoding='utf-8')
    print(f'Updated {changed} en msgstr entries for "Quản lý" variants')
else:
    print('No en msgstr entries updated')
