from pathlib import Path
p = Path('translations/en/LC_MESSAGES/messages.po')
s = p.read_text(encoding='utf-8')
new_lines = []
changed = False
for line in s.splitlines():
    if line.strip() == '#, fuzzy':
        changed = True
        continue
    new_lines.append(line)
if changed:
    p.write_text('\n'.join(new_lines) + '\n', encoding='utf-8')
    print('Removed fuzzy flags from en PO')
else:
    print('No fuzzy flags found in en PO')
